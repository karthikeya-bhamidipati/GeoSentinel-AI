"""
===============================================================================
GeoSentinel AI

Module:
    resample.py

Description:
    Spatial resolution resampling for Sentinel-2 bands.

    Sentinel-2 bands have varying native resolutions:
    - 10m: B02, B03, B04, B08
    - 20m: B05, B06, B07, B8A, B11, B12, SCL
    - 60m: B01, B09, B10

    This module resamples all bands to a target resolution (default 10m)
    so they can be stacked into a unified multi-band array.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_bounds

from src.eo.exceptions import PreprocessingError
from src.utils.logger import logger


# Native Sentinel-2 band resolutions in metres
SENTINEL2_RESOLUTIONS = {
    "B01": 60,
    "B02": 10,
    "B03": 10,
    "B04": 10,
    "B05": 20,
    "B06": 20,
    "B07": 20,
    "B08": 10,
    "B8A": 20,
    "B09": 60,
    "B10": 60,
    "B11": 20,
    "B12": 20,
    "SCL": 20,
    "TCI": 10,
}


class RasterResampler:
    """
    Resamples raster data to a target spatial resolution.

    Uses rasterio's efficient windowed reading and reprojection
    to resample without loading the full array unnecessarily.

    The default target resolution is 10 metres, matching the
    highest-resolution Sentinel-2 bands.
    """

    def __init__(
        self,
        target_resolution_m: float = 10.0,
        resampling: Resampling = Resampling.bilinear,
    ) -> None:

        self.target_resolution_m = target_resolution_m
        self.resampling = resampling

    # ------------------------------------------------------------------

    def resample_file(
        self,
        input_path: Path,
        output_path: Path,
    ) -> Path:
        """
        Resample a raster file to the target resolution.

        Parameters
        ----------
        input_path : Path
        output_path : Path

        Returns
        -------
        Path
            Path to the resampled output file.

        Raises
        ------
        PreprocessingError
        """

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with rasterio.open(input_path) as src:

                src_res_x = abs(src.transform.a)

                if abs(src_res_x - self.target_resolution_m) < 0.5:
                    # Already at target resolution — just copy
                    import shutil
                    shutil.copy2(input_path, output_path)
                    logger.debug(
                        f"No resampling needed: {input_path.name}"
                    )
                    return output_path

                scale = src_res_x / self.target_resolution_m

                new_height = int(src.height * scale)
                new_width = int(src.width * scale)

                profile = src.profile.copy()
                profile.update({
                    "height": new_height,
                    "width": new_width,
                    "transform": src.transform * src.transform.scale(
                        src.width / new_width,
                        src.height / new_height,
                    ),
                    "compress": "lzw",
                })

                data = src.read(
                    out_shape=(
                        src.count,
                        new_height,
                        new_width,
                    ),
                    resampling=self.resampling,
                )

                with rasterio.open(output_path, "w", **profile) as dst:
                    dst.write(data)

        except Exception as exc:
            raise PreprocessingError(
                f"Resampling failed for {input_path.name}: {exc}"
            ) from exc

        logger.debug(
            f"Resampled: {input_path.name} → "
            f"{self.target_resolution_m}m ({new_width}x{new_height})"
        )

        return output_path

    # ------------------------------------------------------------------

    def resample_array(
        self,
        array: np.ndarray,
        src_profile: dict,
    ) -> tuple[np.ndarray, dict]:
        """
        Resample a numpy array to the target resolution.

        Parameters
        ----------
        array : np.ndarray
            Shape (bands, height, width).
        src_profile : dict
            Rasterio profile for the array.

        Returns
        -------
        tuple[np.ndarray, dict]
            (resampled_array, updated_profile)
        """

        import tempfile

        with tempfile.NamedTemporaryFile(
            suffix=".tif", delete=False
        ) as tmp_in, tempfile.NamedTemporaryFile(
            suffix=".tif", delete=False
        ) as tmp_out:

            path_in = Path(tmp_in.name)
            path_out = Path(tmp_out.name)

        with rasterio.open(path_in, "w", **src_profile) as dst:
            dst.write(array)

        self.resample_file(path_in, path_out)

        with rasterio.open(path_out) as src:
            result_array = src.read()
            result_profile = src.profile.copy()

        path_in.unlink(missing_ok=True)
        path_out.unlink(missing_ok=True)

        return result_array, result_profile

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"RasterResampler("
            f"target={self.target_resolution_m}m, "
            f"resampling={self.resampling.name})"
        )
