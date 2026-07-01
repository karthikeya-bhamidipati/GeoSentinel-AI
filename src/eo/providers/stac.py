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
    - AOI-clipped band download via CDSE S3 / OData endpoint
    - Scene-level caching to avoid repeated downloads

    References:
    - https://documentation.dataspace.copernicus.eu/APIs/STAC.html
    - https://documentation.dataspace.copernicus.eu/APIs/OData.html
    - https://documentation.dataspace.copernicus.eu/APIs/S3.html

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import io
import os
import time
import zipfile
from datetime import date
from pathlib import Path
from typing import Any

import requests
import rasterio
import rasterio.mask
import numpy as np
from rasterio.crs import CRS
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
    TokenExpiredError,
)
from src.utils.logger import logger
from src.utils.paths import paths


# =============================================================================
# Constants
# =============================================================================


CDSE_TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu"
    "/auth/realms/CDSE/protocol/openid-connect/token"
)

CDSE_STAC_URL = (
    "https://catalogue.dataspace.copernicus.eu/stac/collections"
    "/SENTINEL-2/items"
)

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


# =============================================================================
# CDSE Provider
# =============================================================================


class CDSEProvider(BaseProvider):
    """
    Copernicus Data Space Ecosystem (CDSE) data provider.

    Responsibilities:
    - Authenticate with CDSE using username/password (OpenID Connect)
    - Search for Sentinel-2 L2A scenes by AOI + date + cloud cover
    - Download only the required spectral bands clipped to the AOI
    - Cache results to avoid re-downloading

    This class never performs preprocessing or feature engineering.
    Those are handled by dedicated downstream modules.

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
        self._token_expiry = time.time() + token_data.get("expires_in", 600) - 60

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
        max_results: int = 5,
        **kwargs: Any,
    ) -> list[dict]:
        """
        Search CDSE STAC API for Sentinel-2 L2A scenes.

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
            STAC feature items, sorted by cloud cover ascending.

        Raises
        ------
        SearchError
            If the STAC API request fails.
        SceneNotFoundError
            If no suitable scenes are found.
        """

        self._ensure_valid_token()

        cloud_limit = max_cloud_cover or self._max_cloud_cover

        bbox = list(aoi.bounds)  # [minx, miny, maxx, maxy]

        params = {
            "bbox": ",".join(str(c) for c in bbox),
            "datetime": (
                f"{start_date.isoformat()}T00:00:00Z"
                f"/{end_date.isoformat()}T23:59:59Z"
            ),
            "collections": "SENTINEL-2",
            "filter": (
                f"eo:cloud_cover lt {cloud_limit:.1f} "
                f"and s2:processing_baseline ge '00.00'"
            ),
            "filter-lang": "cql2-text",
            "limit": max_results,
            "sortby": "+eo:cloud_cover",
        }

        logger.info(
            f"Searching CDSE STAC: {start_date} to {end_date}, "
            f"cloud < {cloud_limit}%"
        )

        try:
            response = self._session.get(
                CDSE_STAC_URL,
                params=params,
                timeout=60,
            )
            response.raise_for_status()

        except requests.RequestException as exc:
            raise SearchError(
                f"CDSE STAC search failed: {exc}"
            ) from exc

        data = response.json()
        features = data.get("features", [])

        # Filter to L2A only
        features = [
            f for f in features
            if "L2A" in f.get("id", "")
        ]

        if not features:
            raise SceneNotFoundError(
                f"No Sentinel-2 L2A scenes found for the given AOI "
                f"between {start_date} and {end_date} "
                f"with cloud cover < {cloud_limit}%."
            )

        logger.info(f"Found {len(features)} scene(s).")

        return features

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
                return assets[key].get("href", None)

        return None

    # ------------------------------------------------------------------
    # Scene Loading
    # ------------------------------------------------------------------

    def load(
        self,
        source: dict,
        aoi: Polygon,
        output_dir: Path | None = None,
    ) -> SentinelScene:
        """
        Download and load a Sentinel-2 scene clipped to the AOI.

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

        scene_dir = output_dir / scene_meta.product_id
        scene_dir.mkdir(parents=True, exist_ok=True)

        scene = SentinelScene(metadata=scene_meta)

        for band in self._download_bands:
            band_path = self._download_band_clipped(
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
            f"({len(scene)} bands)"
        )

        return scene

    # ------------------------------------------------------------------
    # Band Download
    # ------------------------------------------------------------------

    def _download_band_clipped(
        self,
        feature: dict,
        band: Band,
        aoi: Polygon,
        scene_dir: Path,
    ) -> Path | None:
        """
        Download a single band clipped to the AOI.

        Uses the CDSE OData streaming API to retrieve the JP2 band file,
        then clips it in memory using rasterio.mask.

        Parameters
        ----------
        feature : dict
            STAC feature item.
        band : Band
            Band to download.
        aoi : Polygon
            Clipping polygon (WGS84).
        scene_dir : Path
            Output directory.

        Returns
        -------
        Path | None
            Path to the written GeoTIFF file, or None on failure.
        """

        self._ensure_valid_token()

        output_path = scene_dir / f"{band.code}.tif"

        if output_path.exists():
            logger.debug(f"Band cached: {output_path.name}")
            return output_path

        product_id = feature.get("id", "")

        # Build OData download URL for the specific band file
        band_filename = BAND_FILENAME_PATTERNS.get(band)

        if band_filename is None:
            logger.warning(f"No filename pattern for band {band.code}. Skipping.")
            return None

        # Try to get direct asset URL first
        assets = feature.get("assets", {})
        band_url = None

        for asset_key, asset_val in assets.items():
            href = asset_val.get("href", "")
            if band_filename in href:
                band_url = href
                break

        if band_url is None:
            # Fall back to constructing OData path
            band_url = (
                f"{CDSE_ODATA_BASE}/Products('{product_id}')"
                f"/Nodes('{product_id}.SAFE')"
                f"/Nodes('GRANULE')"
                f"/Nodes('$AUTO')"
                f"/Nodes('IMG_DATA')"
                f"/Nodes('R10m')"
                f"/Nodes('{band_filename}')/$value"
            )

        logger.info(f"Downloading band {band.code} ...")

        try:
            response = self._session.get(
                band_url,
                stream=True,
                timeout=120,
            )
            response.raise_for_status()

        except requests.RequestException as exc:
            logger.error(f"Band download failed ({band.code}): {exc}")
            raise DownloadError(
                f"Failed to download band {band.code}: {exc}"
            ) from exc

        # Load into rasterio and clip to AOI
        try:
            band_bytes = response.content

            with rasterio.open(io.BytesIO(band_bytes)) as src:

                # Reproject AOI to raster CRS if needed
                from pyproj import Transformer
                from shapely.ops import transform as shapely_transform

                raster_crs = src.crs.to_epsg()

                if raster_crs != 4326:
                    transformer = Transformer.from_crs(
                        4326, raster_crs, always_xy=True
                    )
                    clip_geom = shapely_transform(
                        transformer.transform, aoi
                    )
                else:
                    clip_geom = aoi

                clipped_array, clipped_transform = rasterio.mask.mask(
                    src,
                    [mapping(clip_geom)],
                    crop=True,
                    nodata=0,
                )

                profile = src.profile.copy()
                profile.update({
                    "driver": "GTiff",
                    "height": clipped_array.shape[1],
                    "width": clipped_array.shape[2],
                    "transform": clipped_transform,
                    "compress": "lzw",
                })

                with rasterio.open(output_path, "w", **profile) as dst:
                    dst.write(clipped_array)

        except Exception as exc:
            logger.error(f"Band clip/save failed ({band.code}): {exc}")
            raise DownloadError(
                f"Failed to clip and save band {band.code}: {exc}"
            ) from exc

        logger.info(f"Band saved: {output_path.name}")

        return output_path

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
