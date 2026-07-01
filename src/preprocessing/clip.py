"""
===============================================================================
GeoSentinel AI

Module:
    clip.py

Description:
    AOI-based raster clipping using rasterio.

    Clips Sentinel-2 band rasters to the user-defined Area of Interest,
    writing the clipped output back to disk as a GeoTIFF.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio
import rasterio.mask
from pyproj import Transformer
from shapely.geometry import Polygon, mapping
from shapely.ops import transform as shapely_transform

from src.eo.aoi.geometry import AOI
from src.eo.exceptions import PreprocessingError
from src.utils.logger import logger


class RasterClipper:
    """
    Clips a raster to an Area of Interest (AOI) polygon.

    The AOI is always provided in WGS84 (EPSG:4326).
    The clipper reprojects it to match the raster's native CRS
    before masking, ensuring spatial accuracy.

    Outputs are written as GeoTIFF files with LZW compression.
    """

    def __init__(self, nodata: float = 0.0) -> None:

        self.nodata = nodata

    # ------------------------------------------------------------------

    def clip_file(
        self,
        input_path: Path,
        aoi: AOI,
        output_path: Path,
    ) -> Path:
        """
        Clip a raster file to the AOI and write to output_path.

        Parameters
        ----------
        input_path : Path
            Source raster file (any rasterio-supported format).
        aoi : AOI
            Area of Interest in WGS84.
        output_path : Path
            Output GeoTIFF path.

        Returns
        -------
        Path
            Path to the clipped output file.

        Raises
        ------
        PreprocessingError
            If clipping fails.
        """

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with rasterio.open(input_path) as src:

                clip_geom = self._reproject_aoi(
                    aoi.geometry, src.crs.to_epsg()
                )

                clipped, transform = rasterio.mask.mask(
                    src,
                    [mapping(clip_geom)],
                    crop=True,
                    nodata=self.nodata,
                )

                profile = src.profile.copy()
                profile.update({
                    "driver": "GTiff",
                    "height": clipped.shape[1],
                    "width": clipped.shape[2],
                    "transform": transform,
                    "nodata": self.nodata,
                    "compress": "lzw",
                })

                with rasterio.open(output_path, "w", **profile) as dst:
                    dst.write(clipped)

        except Exception as exc:
            raise PreprocessingError(
                f"Clipping failed for {input_path.name}: {exc}"
            ) from exc

        logger.debug(f"Clipped: {input_path.name} → {output_path.name}")

        return output_path

    # ------------------------------------------------------------------

    def clip_array(
        self,
        array: np.ndarray,
        src_profile: dict[str, Any],
        aoi: AOI,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """
        Clip a numpy array to the AOI using its rasterio profile.

        Parameters
        ----------
        array : np.ndarray
            Shape (bands, height, width).
        src_profile : dict
            Rasterio profile corresponding to the array.
        aoi : AOI
            Area of Interest in WGS84.

        Returns
        -------
        tuple[np.ndarray, dict]
            (clipped_array, updated_profile)

        Raises
        ------
        PreprocessingError
        """

        import io as _io
        import tempfile

        try:
            # Write to a temporary file and clip
            with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            with rasterio.open(tmp_path, "w", **src_profile) as dst:
                dst.write(array)

            with rasterio.open(tmp_path) as src:
                raster_epsg = src.crs.to_epsg()
                clip_geom = self._reproject_aoi(aoi.geometry, raster_epsg)

                clipped, transform = rasterio.mask.mask(
                    src,
                    [mapping(clip_geom)],
                    crop=True,
                    nodata=self.nodata,
                )

                updated_profile = src.profile.copy()
                updated_profile.update({
                    "height": clipped.shape[1],
                    "width": clipped.shape[2],
                    "transform": transform,
                    "nodata": self.nodata,
                })

            tmp_path.unlink(missing_ok=True)

        except Exception as exc:
            raise PreprocessingError(
                f"Array clipping failed: {exc}"
            ) from exc

        return clipped, updated_profile

    # ------------------------------------------------------------------

    def _reproject_aoi(
        self,
        geometry: Polygon,
        target_epsg: int,
    ) -> Polygon:
        """
        Reproject AOI geometry from WGS84 to the target EPSG.

        Parameters
        ----------
        geometry : Polygon
            WGS84 polygon.
        target_epsg : int
            Target CRS EPSG code.

        Returns
        -------
        Polygon
        """

        if target_epsg == 4326:
            return geometry

        transformer = Transformer.from_crs(
            4326, target_epsg, always_xy=True
        )

        return shapely_transform(transformer.transform, geometry)

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return f"RasterClipper(nodata={self.nodata})"
