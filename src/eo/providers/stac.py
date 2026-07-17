"""
===============================================================================
GeoSentinel AI

Module:
    stac.py

Description:
    Copernicus Data Space Ecosystem (CDSE) provider.

    Implements:
    - OpenID Connect authentication against CDSE
    - STAC API search for Sentinel-2 L2A products
    - AOI-windowed band streaming via GDAL /vsicurl/ (never full scene)
    - Scene-level disk caching keyed by (scene_id, band, aoi_hash)

    Streaming strategy:
    The provider builds a /vsicurl/ URL for each JP2 band and uses
    rasterio.DatasetReader.read(window=...) to extract ONLY the pixels
    that fall within the AOI bounding box. This avoids downloading the
    full ~500MB SAFE product and transfers only ~1–5MB per band.

    References:
    - https://documentation.dataspace.copernicus.eu/APIs/STAC.html
    - https://documentation.dataspace.copernicus.eu/APIs/OData.html
    - https://documentation.dataspace.copernicus.eu/APIs/S3.html
    - https://gdal.org/en/stable/user/virtual_file_systems.html#vsicurl

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import numpy as np
import rasterio
import rasterio.mask
import rasterio.warp
import requests
from affine import Affine
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rasterio.transform import from_bounds
from rasterio.windows import from_bounds as window_from_bounds
from shapely.geometry import Polygon, mapping

from src.eo.models.bands import Band
from src.eo.models.metadata import SentinelMetadata
from src.eo.models.scene import SentinelScene
from src.eo.providers.base import BaseProvider
from src.eo.exceptions import (
    AuthenticationError,
    CDSEError,
    DownloadError,
    SceneNotFoundError,
    SearchError,
)
from src.utils.logger import logger
from src.utils.paths import paths


# =============================================================================
# Runtime Environment
# =============================================================================


def _configure_rasterio_environment() -> None:
    """
    Point GDAL/PROJ to Rasterio's bundled data directories.

    This avoids conflicts with unrelated system installations such as
    PostgreSQL/PostGIS shipping an incompatible `proj.db`.
    """

    rasterio_root = Path(rasterio.__file__).resolve().parent
    proj_dir = rasterio_root / "proj_data"
    gdal_dir = rasterio_root / "gdal_data"

    if proj_dir.exists():
        os.environ["PROJ_LIB"] = str(proj_dir)
        os.environ["PROJ_DATA"] = str(proj_dir)

    if gdal_dir.exists():
        os.environ["GDAL_DATA"] = str(gdal_dir)


_configure_rasterio_environment()


# =============================================================================
# Constants
# =============================================================================


CDSE_TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu"
    "/auth/realms/CDSE/protocol/openid-connect/token"
)

CDSE_STAC_URL = (
    "https://catalogue.dataspace.copernicus.eu/stac/search"
)

CDSE_STAC_COLLECTION = "sentinel-2-l2a"

CDSE_ODATA_BASE = (
    "https://catalogue.dataspace.copernicus.eu/odata/v1"
)

CDSE_S3_ENDPOINT = "https://eodata.dataspace.copernicus.eu"

# Sentinel-2 band filename patterns within a SAFE product
BAND_FILENAME_PATTERNS: dict[Band, str] = {
    Band.BLUE:    "B02_10m.jp2",
    Band.GREEN:   "B03_10m.jp2",
    Band.RED:     "B04_10m.jp2",
    Band.NIR:     "B08_10m.jp2",
    Band.SWIR_1:  "B11_20m.jp2",
    Band.SWIR_2:  "B12_20m.jp2",
    Band.SCL:     "SCL_20m.jp2",
}

# Default bands to download for analysis
DEFAULT_DOWNLOAD_BANDS: tuple[Band, ...] = (
    Band.BLUE,
    Band.GREEN,
    Band.RED,
    Band.NIR,
    Band.SWIR_1,
    Band.SWIR_2,
    Band.SCL,
)

# Maximum cloud cover accepted for a scene (%)
DEFAULT_MAX_CLOUD_COVER = 10.0

# GDAL vsicurl environment settings for optimised cloud streaming
_VSICURL_ENV = {
    "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".jp2,.tif,.tiff",
    "GDAL_HTTP_TIMEOUT": "60",
    "GDAL_HTTP_MAX_RETRY": "3",
    "GDAL_HTTP_RETRY_DELAY": "5",
    "VSI_CACHE": "TRUE",
    "VSI_CACHE_SIZE": "52428800",  # 50 MB per-process GDAL cache
    "CPL_VSIL_CURL_CACHE_SIZE": "52428800",
}


# =============================================================================
# Utilities
# =============================================================================


def _aoi_hash(aoi: Polygon) -> str:
    """
    Return a stable 12-character hex hash for an AOI polygon.
    Coordinates are rounded to 4 decimal places (~11m precision) before
    hashing so that visually identical AOIs drawn at slightly different
    floating-point positions produce the same cache key.
    """

    raw = mapping(aoi)
    def _round_coords(obj):
        if isinstance(obj, (list, tuple)):
            return [_round_coords(v) for v in obj]
        if isinstance(obj, float):
            return round(obj, 4)
        return obj
    rounded = {k: _round_coords(v) for k, v in raw.items()}
    geojson = json.dumps(rounded, sort_keys=True)
    return hashlib.sha256(geojson.encode()).hexdigest()[:12]


def _scene_cache_key(scene_id: str, band: Band, aoi: Polygon) -> str:
    """
    Unique cache key for a (scene, band, AOI) combination.
    """

    return f"{scene_id}_{band.code}_{_aoi_hash(aoi)}"


# =============================================================================
# CDSE Provider
# =============================================================================


class CDSEProvider(BaseProvider):
    """
    Copernicus Data Space Ecosystem (CDSE) data provider.

    Responsibilities:
    - Authenticate with CDSE using username/password (OpenID Connect)
    - Search for Sentinel-2 L2A scenes by AOI + date + cloud cover,
      selecting the scene nearest to the target date with the lowest
      cloud cover
    - Stream only the required AOI window from each JP2 band using
      GDAL /vsicurl/ — never the full ~500 MB SAFE product
    - Cache per-band AOI-clipped GeoTIFFs to avoid re-downloading

    Authentication credentials are read from environment variables:
    - CDSE_USERNAME
    - CDSE_PASSWORD
    """

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        max_cloud_cover: float = DEFAULT_MAX_CLOUD_COVER,
        download_bands: tuple[Band, ...] = DEFAULT_DOWNLOAD_BANDS,
    ) -> None:

        super().__init__("cdse")

        self._username = username or os.environ.get("CDSE_USERNAME", "")
        self._password = password or os.environ.get("CDSE_PASSWORD", "")
        self._max_cloud_cover = max_cloud_cover
        self._download_bands = download_bands

        self._access_token: str | None = None
        self._token_expiry: float = 0.0
        self._session: requests.Session = requests.Session()

        self.connected: bool = False

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """
        Authenticate with CDSE and initialize the HTTP session.

        Raises
        ------
        AuthenticationError
            If credentials are missing or authentication fails.
        """

        if not self._username or not self._password:
            raise AuthenticationError(
                "CDSE credentials are not set. "
                "Set CDSE_USERNAME and CDSE_PASSWORD environment variables."
            )

        self._refresh_token()

        self._session.headers.update({
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        })

        self.connected = True

        logger.info("CDSE provider connected.")

    # ------------------------------------------------------------------
    # Token Management
    # ------------------------------------------------------------------

    def _refresh_token(self) -> None:
        """
        Obtain a new access token from CDSE OpenID Connect endpoint.

        Raises
        ------
        AuthenticationError
        """

        payload = {
            "grant_type": "password",
            "client_id": "cdse-public",
            "username": self._username,
            "password": self._password,
        }

        try:
            response = requests.post(
                CDSE_TOKEN_URL,
                data=payload,
                timeout=30,
            )
            response.raise_for_status()

        except requests.RequestException as exc:
            raise AuthenticationError(
                f"CDSE authentication failed: {exc}"
            ) from exc

        token_data = response.json()

        self._access_token = token_data["access_token"]
        self._token_expiry = (
            time.time() + token_data.get("expires_in", 600) - 60
        )

        logger.debug("CDSE access token refreshed.")

    def _ensure_valid_token(self) -> None:
        """
        Refresh token if it is about to expire.
        """

        if time.time() >= self._token_expiry:
            self._refresh_token()
            self._session.headers["Authorization"] = (
                f"Bearer {self._access_token}"
            )

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        aoi: Polygon,
        start_date: date,
        end_date: date,
        max_cloud_cover: float | None = None,
        max_results: int = 10,
        **kwargs: Any,
    ) -> list[dict]:
        """
        Search CDSE STAC API for Sentinel-2 L2A scenes.

        Returns scenes sorted by date proximity to the midpoint of
        [start_date, end_date] first, then by cloud cover ascending.
        This ensures the best available scene nearest the target date
        is ranked first.

        Parameters
        ----------
        aoi : Polygon
            AOI geometry in WGS84 (EPSG:4326).
        start_date : date
        end_date : date
        max_cloud_cover : float | None
            Cloud cover percentage limit (0–100).
        max_results : int
            Maximum number of results to return.

        Returns
        -------
        list[dict]
            STAC feature items, sorted by (date proximity, cloud cover).

        Raises
        ------
        SearchError
            If the STAC API request fails.
        SceneNotFoundError
            If no suitable scenes are found.
        """

        self._ensure_valid_token()

        cloud_limit = max_cloud_cover if max_cloud_cover is not None \
            else self._max_cloud_cover

        # Widen search to at most 30 days each side to maximise hit rate
        bbox = list(aoi.bounds)  # [minx, miny, maxx, maxy]
        payload = {
            "bbox": bbox,
            "datetime": (
                f"{start_date.isoformat()}T00:00:00Z"
                f"/{end_date.isoformat()}T23:59:59Z"
            ),
            "collections": [CDSE_STAC_COLLECTION],
            "filter": {
                "op": "<=",
                "args": [
                    {"property": "eo:cloud_cover"},
                    cloud_limit,
                ],
            },
            "filter-lang": "cql2-json",
            "limit": max_results,
        }

        logger.info(
            f"Searching CDSE STAC: {start_date} to {end_date}, "
            f"cloud < {cloud_limit}%"
        )

        try:
            response = self._session.post(
                CDSE_STAC_URL,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()

        except requests.RequestException as exc:
            raise SearchError(
                f"CDSE STAC search failed: {exc}"
            ) from exc

        data = response.json()
        features = data.get("features", [])

        if not features:
            raise SceneNotFoundError(
                f"No Sentinel-2 L2A scenes found for the given AOI "
                f"between {start_date} and {end_date} "
                f"with cloud cover < {cloud_limit}%."
            )

        # Rank by date proximity (to mid-point) then cloud cover
        from datetime import timedelta

        mid_date = start_date + (end_date - start_date) / 2

        def _rank_key(feature: dict) -> tuple[float, float]:
            props = feature.get("properties", {})
            dt_str = props.get("datetime", "")
            cloud = props.get("eo:cloud_cover", 100.0)

            try:
                from datetime import datetime
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                days_diff = abs((dt.date() - mid_date).days)
            except Exception:
                days_diff = 9999

            return (days_diff, cloud)

        features = sorted(features, key=_rank_key)

        logger.info(
            f"Found {len(features)} scene(s). "
            f"Best (global): {features[0].get('id', '?')} "
            f"(cloud={features[0].get('properties', {}).get('eo:cloud_cover', '?')}%)"
        )

        return features

    # ------------------------------------------------------------------

    def get_local_cloud_cover(self, feature: dict, aoi: Polygon) -> float:
        """
        Calculates exact cloud cover percentage inside the AOI by downloading
        the SCL (Scene Classification) band using /vsicurl/.
        """
        scene_id = feature.get("id")
        if not scene_id:
            return 100.0
            
        assets = feature.get("assets", {})
        scl_asset = assets.get("scl", assets.get("SCL"))
        if not scl_asset:
            return float(feature.get("properties", {}).get("eo:cloud_cover", 100.0))
            
        url = scl_asset.get("href")
        if not url:
            return 100.0

        if url.startswith("s3://"):
            url = url.replace("s3://eodata/", "https://zipper.dataspace.copernicus.eu/odata/v1/Products(")
            # Extract UUID and build stream URL
            # Just fallback to global if S3
            return float(feature.get("properties", {}).get("eo:cloud_cover", 100.0))

        # We must use proper VSI URL if it's HTTPS
        if url.startswith("http"):
            # Try to fetch SCL array directly using GDAL via vsicurl
            try:
                import rasterio
                from rasterio.mask import mask
                from src.utils.logger import logger
                
                vsi_url = f"/vsicurl/{url}"
                
                # We must use token authentication if needed
                env = self._get_vsi_env()
                with rasterio.Env(**env):
                    with rasterio.open(vsi_url) as src:
                        out_image, _ = mask(src, [aoi], crop=True)
                        scl_array = out_image[0]
                        
                        # Sentinel-2 SCL Cloud Classes:
                        # 3: Cloud Shadows
                        # 8: Cloud Medium Probability
                        # 9: Cloud High Probability
                        # 10: Thin Cirrus
                        # 0: No Data
                        
                        valid_pixels = np.sum(scl_array > 0)
                        if valid_pixels == 0:
                            return 100.0
                            
                        cloud_pixels = np.sum(np.isin(scl_array, [3, 8, 9, 10]))
                        return float(cloud_pixels / valid_pixels * 100.0)
                        
            except Exception as exc:
                logger.debug(f"Failed to fetch local SCL for {scene_id}: {exc}")
                
        return float(feature.get("properties", {}).get("eo:cloud_cover", 100.0))

    # ------------------------------------------------------------------
    # Metadata Extraction
    # ------------------------------------------------------------------

    def metadata(self, source: str | Path | dict) -> dict:
        """
        Extract metadata from a STAC feature item.

        Parameters
        ----------
        source : dict
            A STAC feature item returned by search().

        Returns
        -------
        dict
        """

        if isinstance(source, dict):
            feature = source
        else:
            raise TypeError(
                "CDSEProvider.metadata() expects a STAC feature dict."
            )

        props = feature.get("properties", {})

        return {
            "product_id": feature.get("id", ""),
            "product_name": props.get("title", feature.get("id", "")),
            "satellite": props.get("platform", "SENTINEL-2"),
            "processing_level": "L2A",
            "processing_baseline": props.get(
                "s2:processing_baseline", "00.00"
            ),
            "acquisition_datetime": props.get("datetime", ""),
            "cloud_cover": props.get("eo:cloud_cover", None),
            "tile_id": props.get("s2:mgrs_tile", None),
            "orbit_number": props.get("sat:absolute_orbit", None),
            "relative_orbit": props.get("sat:relative_orbit", None),
            "orbit_direction": props.get("sat:orbit_state", None),
            "source": "CDSE",
            "download_url": self._extract_download_url(feature),
        }

    def _extract_download_url(self, feature: dict) -> str | None:
        """
        Extract the product download URL from a STAC feature.
        """

        assets = feature.get("assets", {})

        # Try SAFE archive link
        for key in ("PRODUCT", "product", "safe-zip"):
            if key in assets:
                asset = assets[key]
                alternate_href = (
                    asset.get("alternate", {})
                    .get("https", {})
                    .get("href")
                )
                return alternate_href or asset.get("href", None)

        return None

    # ------------------------------------------------------------------
    # Scene Loading (public entry point)
    # ------------------------------------------------------------------

    def load(
        self,
        source: dict,
        aoi: Polygon,
        output_dir: Path | None = None,
    ) -> SentinelScene:
        """
        Download and load a Sentinel-2 scene clipped to the AOI.

        Uses /vsicurl/ windowed streaming: only pixels that fall within
        the AOI bounding box are transferred from CDSE storage. Results
        are cached on disk keyed by (scene_id, band, aoi_hash) so the
        same request is served from the local cache on subsequent calls.

        Parameters
        ----------
        source : dict
            A STAC feature item returned by search().
        aoi : Polygon
            AOI polygon in WGS84.
        output_dir : Path | None
            Directory to save downloaded band files.
            Defaults to paths.DOWNLOAD_DIR.

        Returns
        -------
        SentinelScene

        Raises
        ------
        DownloadError
        """

        output_dir = output_dir or paths.DOWNLOAD_DIR

        meta_dict = self.metadata(source)

        from datetime import datetime
        meta_dict["acquisition_datetime"] = datetime.fromisoformat(
            meta_dict["acquisition_datetime"].replace("Z", "+00:00")
        )
        meta_dict.setdefault("generation_datetime", None)

        scene_meta = SentinelMetadata(**{
            k: v for k, v in meta_dict.items()
            if k in SentinelMetadata.__dataclass_fields__
        })

        # Cache directory keyed by scene_id + aoi_hash for correctness
        aoi_hash = _aoi_hash(aoi)
        scene_dir = output_dir / f"{scene_meta.product_id}_{aoi_hash}"
        scene_dir.mkdir(parents=True, exist_ok=True)

        scene = SentinelScene(metadata=scene_meta)

        for band in self._download_bands:
            band_path = self._stream_band_windowed(
                feature=source,
                band=band,
                aoi=aoi,
                scene_dir=scene_dir,
            )

            if band_path is not None:
                scene.add_raster(band=band, path=band_path)

        scene_meta.downloaded = True
        scene_meta.local_path = scene_dir

        logger.info(
            f"Scene loaded: {scene_meta.product_name} "
            f"({len(scene)} bands) — AOI-clipped via /vsicurl/"
        )

        return scene

    # ------------------------------------------------------------------
    # AOI-windowed band streaming via /vsicurl/
    # ------------------------------------------------------------------

    def _stream_band_windowed(
        self,
        feature: dict,
        band: Band,
        aoi: Polygon,
        scene_dir: Path,
    ) -> Path | None:
        """
        Stream a single band's AOI window from CDSE via GDAL /vsicurl/.

        Strategy
        --------
        1. Locate the HTTPS asset URL for the JP2 band in the STAC item.
        2. Build a ``/vsicurl/<url>`` path and open it with rasterio using
           the bearer token injected via GDAL_HTTP_HEADER.
        3. Compute the raster window that corresponds to the AOI bounds.
        4. Read only that window (1–5 MB vs ~500 MB for a full scene).
        5. Write the extracted AOI tile as a compressed GeoTIFF.

        Falls back to full-file streaming (HTTP GET + in-memory clip)
        if the /vsicurl/ open fails (e.g., behind a non-virtual-FS
        compatible CDN node).

        Parameters
        ----------
        feature : dict
        band : Band
        aoi : Polygon
            AOI in WGS84.
        scene_dir : Path

        Returns
        -------
        Path | None
        """

        self._ensure_valid_token()

        output_path = scene_dir / f"{band.code}.tif"

        # ---- Cache hit ------------------------------------------------
        if output_path.exists():
            logger.debug(f"Band cached: {output_path.name}")
            return output_path

        # ---- Locate asset URL -----------------------------------------
        band_filename = BAND_FILENAME_PATTERNS.get(band)
        if band_filename is None:
            logger.warning(f"No filename pattern for {band.code}. Skipping.")
            return None

        assets = feature.get("assets", {})
        band_url: str | None = None
        band_asset: dict | None = None

        for asset_val in assets.values():
            href = asset_val.get("href", "")
            alt_href = (
                asset_val.get("alternate", {})
                .get("https", {})
                .get("href", "")
            )
            s3_href = (
                asset_val.get("alternate", {})
                .get("s3", {})
                .get("href", "")
            )

            if (band_filename in unquote(href) or 
                band_filename in unquote(alt_href) or 
                band_filename in unquote(s3_href)):
                
                if s3_href.startswith("s3://eodata/"):
                    band_url = s3_href.replace("s3://eodata/", "https://eodata.dataspace.copernicus.eu/")
                else:
                    band_url = alt_href or href
                band_asset = asset_val
                break

        if band_url is None:
            logger.warning(
                f"No asset URL for band {band.code}. "
                f"Falling back to HTTP download."
            )
            return self._download_band_http_fallback(
                feature=feature,
                band=band,
                aoi=aoi,
                scene_dir=scene_dir,
                band_url=None,
                band_asset=band_asset,
            )

        # ---- Attempt /vsicurl/ windowed read --------------------------
        # Skip vsicurl for OData endpoints as they do not support HTTP Range requests
        if "odata/v1/Products" in band_url:
            logger.info(f"OData endpoint detected for {band.code}. Bypassing /vsicurl/ and streaming via HTTP ...")
            return self._download_band_http_fallback(
                feature=feature,
                band=band,
                aoi=aoi,
                scene_dir=scene_dir,
                band_url=band_url,
                band_asset=band_asset,
            )

        try:
            return self._read_via_vsicurl(
                band_url=band_url,
                band=band,
                band_asset=band_asset,
                aoi=aoi,
                output_path=output_path,
            )

        except Exception as exc:
            logger.warning(
                f"vsicurl failed for {band.code} ({exc}). "
                f"Falling back to HTTP download."
            )
            return self._download_band_http_fallback(
                feature=feature,
                band=band,
                aoi=aoi,
                scene_dir=scene_dir,
                band_url=band_url,
                band_asset=band_asset,
            )

    def _read_via_vsicurl(
        self,
        band_url: str,
        band: Band,
        band_asset: dict | None,
        aoi: Polygon,
        output_path: Path,
    ) -> Path:
        """
        Open a JP2 asset via /vsicurl/ and read only the AOI window.

        GDAL environment variables are set so that the bearer token is
        sent with every HTTP request, enabling authenticated streaming.

        Parameters
        ----------
        band_url : str
        band : Band
        band_asset : dict | None
            STAC asset metadata (carries proj:code, proj:transform, etc.)
        aoi : Polygon
            WGS84 AOI polygon.
        output_path : Path

        Returns
        -------
        Path
        """

        vsicurl_path = f"/vsicurl/{band_url}"

        # Inject auth header into GDAL environment
        gdal_env = {
            **_VSICURL_ENV,
            "GDAL_HTTP_HEADER_FILE": "",  # cleared — we use GDAL_HTTP_HEADERS
            "GDAL_HTTP_HEADERS": f"Authorization: Bearer {self._access_token}",
        }

        logger.info(f"Streaming {band.code} via /vsicurl/ ...")

        with rasterio.Env(**gdal_env):
            with rasterio.open(vsicurl_path, driver="JP2OpenJPEG") as src:
                raster_crs = src.crs

                # Recover CRS from STAC asset metadata if missing in file
                if raster_crs is None and band_asset is not None:
                    proj_code = band_asset.get("proj:code")
                    if proj_code:
                        raster_crs = CRS.from_string(proj_code)

                if raster_crs is None:
                    raise DownloadError(
                        f"Band {band.code} has no CRS metadata."
                    )

                # Reproject AOI into raster's native CRS
                clip_geom = self._reproject_aoi(aoi, raster_crs)
                clip_bounds = clip_geom.bounds  # (minx, miny, maxx, maxy)

                # Compute the pixel window for the AOI
                window = window_from_bounds(
                    *clip_bounds, transform=src.transform
                )
                window = window.intersection(
                    rasterio.windows.Window(0, 0, src.width, src.height)
                )

                if window.width <= 0 or window.height <= 0:
                    raise DownloadError(
                        f"AOI does not intersect band {band.code} raster."
                    )

                # Read ONLY the windowed pixels (bandwidth-efficient)
                clipped_array = src.read(1, window=window)
                clipped_transform = src.window_transform(window)

        # Write windowed AOI tile as compressed GeoTIFF
        self._write_band_geotiff(
            array=clipped_array,
            crs=raster_crs,
            transform=clipped_transform,
            output_path=output_path,
        )

        logger.info(
            f"Band {band.code} streamed via /vsicurl/: "
            f"{clipped_array.shape[1]}×{clipped_array.shape[0]} px"
        )

        return output_path

    # ------------------------------------------------------------------
    # HTTP fallback (full-file download + in-memory clip)
    # ------------------------------------------------------------------

    def _download_band_http_fallback(
        self,
        feature: dict,
        band: Band,
        aoi: Polygon,
        scene_dir: Path,
        band_url: str | None,
        band_asset: dict | None,
    ) -> Path | None:
        """
        Download a band via HTTP GET, clip to AOI in memory, save GeoTIFF.

        This is the fallback when /vsicurl/ is unavailable.
        """

        output_path = scene_dir / f"{band.code}.tif"

        if output_path.exists():
            return output_path

        if band_url is None:
            logger.error(f"No URL for band {band.code}. Cannot download.")
            return None

        raw_scene_dir = scene_dir.parent / feature.get("id", "unknown_scene")
        raw_scene_dir.mkdir(parents=True, exist_ok=True)
        raw_file = raw_scene_dir / f"{band.code}.jp2"

        if raw_file.exists():
            logger.info(f"Using cached raw file for {band.code}")
            band_bytes = raw_file.read_bytes()
        else:
            logger.info(f"HTTP fallback — downloading {band.code} ...")

            try:
                response = self._session.get(
                    band_url,
                    stream=True,
                    timeout=120,
                )
                response.raise_for_status()
                band_bytes = response.content
                raw_file.write_bytes(band_bytes)

            except requests.RequestException as exc:
                raise DownloadError(
                    f"HTTP download failed for {band.code}: {exc}"
                ) from exc

        try:
            with rasterio.open(__import__("io").BytesIO(band_bytes)) as src:
                raster_crs = src.crs

                if raster_crs is None and band_asset is not None:
                    proj_code = band_asset.get("proj:code")
                    proj_transform = band_asset.get("proj:transform")
                    proj_shape = band_asset.get("proj:shape")
                    raster_profile = src.profile.copy()

                    if proj_code:
                        raster_crs = CRS.from_string(proj_code)

                    if proj_transform:
                        raster_transform = Affine(*proj_transform[:6])
                    else:
                        raster_transform = src.transform

                    if proj_shape:
                        raster_profile.update({
                            "height": proj_shape[0],
                            "width": proj_shape[1],
                        })
                else:
                    raster_transform = src.transform
                    raster_profile = src.profile.copy()

                if raster_crs is None:
                    raise DownloadError(
                        f"Band {band.code} is missing CRS metadata."
                    )

                clip_geom = self._reproject_aoi(aoi, raster_crs)

                if src.crs is not None:
                    clipped_array, clipped_transform = rasterio.mask.mask(
                        src,
                        [mapping(clip_geom)],
                        crop=True,
                        nodata=0,
                    )
                    profile = src.profile.copy()
                    clipped_array = clipped_array[0]  # (H, W)
                else:
                    array = src.read()
                    raster_profile.update({
                        "driver": "GTiff",
                        "count": array.shape[0],
                        "dtype": str(array.dtype),
                        "crs": raster_crs,
                        "transform": raster_transform,
                    })

                    with MemoryFile() as memfile:
                        with memfile.open(**raster_profile) as dataset:
                            dataset.write(array)
                            clipped_arr, clipped_transform = rasterio.mask.mask(
                                dataset,
                                [mapping(clip_geom)],
                                crop=True,
                                nodata=0,
                            )
                            profile = dataset.profile.copy()

                    clipped_array = clipped_arr[0]

        except Exception as exc:
            raise DownloadError(
                f"Failed to clip band {band.code}: {exc}"
            ) from exc

        self._write_band_geotiff(
            array=clipped_array,
            crs=raster_crs,
            transform=clipped_transform,
            output_path=output_path,
        )

        logger.info(f"Band {band.code} downloaded (HTTP fallback): {output_path.name}")

        return output_path

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _reproject_aoi(aoi: Polygon, target_crs: CRS) -> Polygon:
        """
        Reproject the AOI polygon from WGS84 to ``target_crs``.

        Parameters
        ----------
        aoi : Polygon
            WGS84 polygon.
        target_crs : CRS

        Returns
        -------
        Polygon
        """

        from pyproj import Transformer
        from shapely.ops import transform as shapely_transform

        target_epsg = target_crs.to_epsg()

        if target_epsg == 4326:
            return aoi

        transformer = Transformer.from_crs(4326, target_crs, always_xy=True)
        return shapely_transform(transformer.transform, aoi)

    @staticmethod
    def _write_band_geotiff(
        array: np.ndarray,
        crs: CRS,
        transform: Affine,
        output_path: Path,
        compress: str = "lzw",
        nodata: int = 0,
    ) -> None:
        """
        Write a 2D numpy array as a single-band compressed GeoTIFF.
        """

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if array.ndim == 3:
            array = array[0]

        profile = {
            "driver": "GTiff",
            "dtype": str(array.dtype),
            "width": array.shape[1],
            "height": array.shape[0],
            "count": 1,
            "crs": crs,
            "transform": transform,
            "compress": compress,
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256,
            "nodata": nodata,
        }

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(array, 1)

    # ------------------------------------------------------------------
    # Available Bands
    # ------------------------------------------------------------------

    def available_bands(self, source: str | Path | dict) -> list[str]:
        """
        Return band names available from this provider.
        """

        return [band.code for band in self._download_bands]

    def load_band(
        self,
        source: str | Path,
        band_name: str,
    ) -> np.ndarray:
        """
        Load a specific band from a local path.
        """

        with rasterio.open(source) as src:
            return src.read(1).astype("float32")

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------

    def close(self) -> None:
        """
        Close the HTTP session.
        """

        self._session.close()
        self.connected = False

        logger.info("CDSE provider closed.")

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"CDSEProvider("
            f"user={self._username!r}, "
            f"connected={self.connected})"
        )
