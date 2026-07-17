"""
===============================================================================
GeoSentinel AI

Module:
    align.py

Description:
    Spatial alignment of two raster datasets to a common grid.

    When comparing scenes from two different dates, minor spatial
    misalignments can occur due to different acquisition geometries.
    This module reprojects and resamples a secondary raster to match
    the reference raster's exact grid (CRS, resolution, origin, extent).

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject

from src.eo.exceptions import PreprocessingError
from src.utils.logger import logger


class RasterAligner:
    """
    Aligns a target raster to a reference raster's spatial grid.

    Given two rasters (e.g., from T1 and T2 acquisitions), this class
    ensures they share an identical CRS, transform, and pixel dimensions
    before any downstream comparison is performed.

    The reference raster is never modified.
    Only the target is reprojected and resampled.
    """

    def __init__(
        self,
        resampling: Resampling = Resampling.bilinear,
    ) -> None:

        self.resampling = resampling

    # ------------------------------------------------------------------

    def align_files(
        self,
        reference_path: "Path",
        target_path: "Path",
        output_path: "Path",
    ) -> "Path":
        """
        Reproject and resample target to match reference grid.

        Parameters
        ----------
        reference_path : Path
            Reference raster file (defines the output grid).
        target_path : Path
            Raster file to align.
        output_path : Path
            Output GeoTIFF path.

        Returns
        -------
        Path
            Path to the aligned output file.

        Raises
        ------
        PreprocessingError
        """

        from pathlib import Path

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with rasterio.open(reference_path) as ref:
                ref_crs = ref.crs
                ref_transform = ref.transform
                ref_height = ref.height
                ref_width = ref.width
                ref_count = ref.count
                ref_dtype = ref.dtypes[0]

            with rasterio.open(target_path) as tgt:

                target_array = tgt.read()
                target_profile = tgt.profile.copy()

                output_array = np.zeros(
                    (tgt.count, ref_height, ref_width),
                    dtype=ref_dtype,
                )

                for band_idx in range(1, tgt.count + 1):

                    reproject(
                        source=rasterio.band(tgt, band_idx),
                        destination=output_array[band_idx - 1],
                        src_transform=tgt.transform,
                        src_crs=tgt.crs,
                        dst_transform=ref_transform,
                        dst_crs=ref_crs,
                        resampling=self.resampling,
                    )

            output_profile = target_profile.copy()
            output_profile.update({
                "crs": ref_crs,
                "transform": ref_transform,
                "width": ref_width,
                "height": ref_height,
                "compress": "lzw",
            })

            with rasterio.open(output_path, "w", **output_profile) as dst:
                dst.write(output_array)

        except Exception as exc:
            raise PreprocessingError(
                f"Alignment failed: {exc}"
            ) from exc

        logger.debug(
            f"Aligned: {target_path.name} → {output_path.name} "
            f"({ref_width}x{ref_height})"
        )

        return output_path

    # ------------------------------------------------------------------

    def align_arrays(
        self,
        reference_array: np.ndarray,
        reference_profile: dict,
        target_array: np.ndarray,
        target_profile: dict,
    ) -> tuple[np.ndarray, dict]:
        """
        Align target array to reference array's grid.

        Parameters
        ----------
        reference_array : np.ndarray
            Reference array (bands, height, width).
        reference_profile : dict
            Rasterio profile of reference array.
        target_array : np.ndarray
            Target array to align.
        target_profile : dict
            Rasterio profile of target array.

        Returns
        -------
        tuple[np.ndarray, dict]
            (aligned_array, updated_profile)
        """

        ref_h = reference_profile["height"]
        ref_w = reference_profile["width"]
        ref_crs = reference_profile["crs"]
        ref_transform = reference_profile["transform"]

        if (
            target_profile["crs"] == ref_crs
            and target_profile["transform"] == ref_transform
            and target_profile["height"] == ref_h
            and target_profile["width"] == ref_w
        ):
            # Already aligned
            return target_array, target_profile

        try:
            from skimage.registration import phase_cross_correlation
            import scipy.ndimage as ndimage

            aligned = np.zeros(
                (target_array.shape[0], ref_h, ref_w),
                dtype=target_array.dtype,
            )

            for i in range(target_array.shape[0]):
                reproject(
                    source=target_array[i],
                    destination=aligned[i],
                    src_transform=target_profile["transform"],
                    src_crs=target_profile["crs"],
                    dst_transform=ref_transform,
                    dst_crs=ref_crs,
                    resampling=self.resampling,
                )

            # Sub-pixel co-registration
            # Use NIR band (index 3) if available, else last available band
            band_idx = min(3, reference_array.shape[0] - 1)
            ref_band = reference_array[band_idx]
            tgt_band = aligned[band_idx]

            # Calculate shift
            shift, error, diffphase = phase_cross_correlation(
                ref_band, tgt_band, upsample_factor=10
            )

            # Apply shift if significant
            if np.any(np.abs(shift) > 0.05):
                logger.debug(f"Applying sub-pixel shift: {shift}")
                for i in range(aligned.shape[0]):
                    aligned[i] = ndimage.shift(
                        aligned[i], shift, order=3, mode='reflect'
                    )

        except Exception as exc:
            raise PreprocessingError(
                f"Array alignment failed: {exc}"
            ) from exc

        updated_profile = target_profile.copy()
        updated_profile.update({
            "crs": ref_crs,
            "transform": ref_transform,
            "height": ref_h,
            "width": ref_w,
        })

        return aligned, updated_profile

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"RasterAligner("
            f"resampling={self.resampling.name})"
        )
