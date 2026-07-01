"""
===============================================================================
GeoSentinel AI

Module:
    geotiff_export.py

Description:
    GeoTIFF export for segmentation masks and change maps.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import Affine

from src.utils.io import write_raster
from src.utils.paths import paths
from src.utils.logger import logger


class GeoTIFFExporter:
    """
    Exports raster analysis results as GeoTIFF files.
    """

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or paths.REPORTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_mask(
        self,
        mask: np.ndarray,
        crs: CRS,
        transform: Affine,
        filename: str | None = None,
    ) -> Path:
        """
        Export a segmentation mask as GeoTIFF.

        Parameters
        ----------
        mask : np.ndarray
            Shape (H, W), int32.
        crs : CRS
        transform : Affine
        filename : str | None

        Returns
        -------
        Path
        """

        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"segmentation_mask_{ts}.tif"

        output_path = self.output_dir / filename

        write_raster(
            path=output_path,
            array=mask,
            crs=crs,
            transform=transform,
            dtype="int32",
        )

        logger.info(f"GeoTIFF mask exported: {output_path.name}")

        return output_path

    def export_change_raster(
        self,
        change_array: np.ndarray,
        crs: CRS,
        transform: Affine,
        filename: str | None = None,
    ) -> Path:
        """
        Export a change delta raster (NDVI/NDBI) as GeoTIFF.

        Parameters
        ----------
        change_array : np.ndarray
            Shape (H, W), float32.
        crs : CRS
        transform : Affine
        filename : str | None

        Returns
        -------
        Path
        """

        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"change_raster_{ts}.tif"

        output_path = self.output_dir / filename

        write_raster(
            path=output_path,
            array=change_array,
            crs=crs,
            transform=transform,
            dtype="float32",
            nodata=-9999.0,
        )

        logger.info(f"GeoTIFF change raster exported: {output_path.name}")

        return output_path
