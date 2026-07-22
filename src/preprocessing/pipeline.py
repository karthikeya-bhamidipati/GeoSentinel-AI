"""
===============================================================================
GeoSentinel AI

Module:
    pipeline.py

Description:
    Preprocessing pipeline that chains all preprocessing steps.

    Ordered steps:
    1. Cloud masking (SCL-based)
    2. Resample all bands to target resolution (10 m)
       - 10m bands: B02, B03, B04, B08  → no-op
       - 20m bands: B11, B12, SCL       → 2× upsampled via bilinear
    3. Spatial alignment (for T2 scenes, co-register pixel grid to T1)
    4. Band normalization (DN / 10 000 → [0, 1] surface reflectance)

    Note: AOI clipping is performed at download time by CDSEProvider
    via windowed /vsicurl/ streaming, so it is NOT repeated here.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

from src.eo.models.bands import AI_BANDS, Band
from src.eo.models.scene import SentinelScene
from src.eo.exceptions import PreprocessingError
from src.preprocessing.clip import RasterClipper
from src.preprocessing.cloudmask import CloudMasker
from src.preprocessing.resample import RasterResampler
from src.preprocessing.align import RasterAligner
from src.preprocessing.normalize import BandNormalizer
from src.utils.logger import logger


# Target output resolution for all bands
TARGET_RESOLUTION_M: float = 10.0


@dataclass
class PreprocessingResult:
    """
    Result of the preprocessing pipeline.

    Attributes
    ----------
    scene : SentinelScene
        The fully preprocessed scene (cloud-masked, 10m, aligned, normalised).
    cloud_mask : np.ndarray
        Boolean array indicating masked pixels (True = cloud/shadow).
    cloud_coverage_pct : float
        Percentage of cloud-contaminated pixels in the AOI.
    steps_applied : list[str]
        Names of preprocessing steps applied in order.
    """

    scene: SentinelScene
    cloud_mask: np.ndarray
    cloud_coverage_pct: float
    steps_applied: list[str] = field(default_factory=list)


class PreprocessingPipeline:
    """
    Chains all Sentinel-2 preprocessing steps into a single workflow.

    Steps applied (in order):
    1. Cloud masking  — SCL-based pixel masking
    2. Resampling     — all bands upsampled / downsampled to 10 m
    3. Alignment      — (optional) pixel-grid co-registration to T1 reference
    4. Normalization  — DN / 10 000 → [0, 1] surface reflectance

    Note: AOI clipping is performed upstream by CDSEProvider
    (windowed /vsicurl/ streaming), so it is NOT repeated here.

    This class does not perform feature engineering or AI inference.
    """

    def __init__(
        self,
        target_resolution_m: float = TARGET_RESOLUTION_M,
        apply_cloud_mask: bool = True,
        apply_normalization: bool = True,
    ) -> None:

        self.target_resolution_m = target_resolution_m
        self.apply_cloud_mask = apply_cloud_mask
        self.apply_normalization = apply_normalization

        self._cloud_masker = CloudMasker()
        self._resampler = RasterResampler(
            target_resolution_m=target_resolution_m
        )
        self._aligner = RasterAligner()
        self._normalizer = BandNormalizer()

    # ------------------------------------------------------------------

    def run(
        self,
        scene: SentinelScene,
        reference_scene: Optional[SentinelScene] = None,
    ) -> PreprocessingResult:
        """
        Run the full preprocessing pipeline on a scene.

        Parameters
        ----------
        scene : SentinelScene
            The scene to preprocess.
        reference_scene : SentinelScene | None
            Optional reference scene for spatial alignment.
            When provided (T2 processing) the scene is co-registered
            to the reference scene's pixel grid so both scenes are
            spatially aligned before feature engineering.

        Returns
        -------
        PreprocessingResult

        Raises
        ------
        PreprocessingError
            If any step fails.
        """

        steps_applied: list[str] = []
        cloud_mask = np.zeros((1, 1), dtype=bool)
        cloud_coverage_pct = 0.0

        logger.info(
            f"Starting preprocessing pipeline: {scene.product_name}"
        )

        # ----------------------------------------------------------
        # Step 1: Cloud Masking (SCL-based)
        # ----------------------------------------------------------

        if self.apply_cloud_mask:
            try:
                scene, cloud_mask = self._cloud_masker.mask_scene(scene)
                cloud_coverage_pct = float(cloud_mask.mean() * 100)
                steps_applied.append("cloud_masking")

                logger.info(
                    f"Cloud mask applied: {cloud_coverage_pct:.1f}% masked"
                )

            except Exception as exc:
                logger.warning(
                    f"Cloud masking failed: {exc}. Continuing without mask."
                )

        # ----------------------------------------------------------
        # Step 2: Resampling — harmonise all bands to TARGET_RESOLUTION_M
        # ----------------------------------------------------------

        try:
            scene = self._resample_scene(scene)
            steps_applied.append("resampling")

        except Exception as exc:
            logger.warning(
                f"Resampling failed: {exc}. Using native resolutions."
            )

        # ----------------------------------------------------------
        # Step 3: Spatial Alignment (T2 → T1 co-registration)
        # ----------------------------------------------------------

        if reference_scene is not None:
            try:
                scene = self._align_to_reference(scene, reference_scene)
                steps_applied.append("spatial_alignment")
            except Exception as exc:
                logger.warning(
                    f"Spatial alignment failed: {exc}. "
                    f"Continuing without alignment."
                )

        # ----------------------------------------------------------
        # Step 4: Normalization (DN → reflectance)
        # ----------------------------------------------------------

        if self.apply_normalization:
            try:
                scene = self._normalizer.normalize_scene(scene)
                steps_applied.append("normalization")
            except Exception as exc:
                logger.warning(
                    f"Normalization failed: {exc}. Using raw DN values."
                )

        logger.info(
            f"Preprocessing complete: "
            f"{scene.product_name} "
            f"[{', '.join(steps_applied)}]"
        )

        return PreprocessingResult(
            scene=scene,
            cloud_mask=cloud_mask,
            cloud_coverage_pct=cloud_coverage_pct,
            steps_applied=steps_applied,
        )

    # ------------------------------------------------------------------

    def _resample_scene(
        self,
        scene: SentinelScene,
    ) -> SentinelScene:
        """
        Resample every band raster in the scene to target_resolution_m.

        Sentinel-2 native resolutions:
        - 10 m: B02, B03, B04, B08   → no-op (skip)
        - 20 m: B11, B12, SCL        → 2× bilinear upsample to 10 m

        The resampled array is written directly into the cached Raster
        object so downstream code sees consistent 10 m data.

        Parameters
        ----------
        scene : SentinelScene

        Returns
        -------
        SentinelScene
        """

        for band in AI_BANDS:
            if not scene.has_band(band):
                continue

            raster = scene.raster(band)

            # Check current resolution — skip if already at target
            try:
                current_res = abs(raster.transform.a)
            except Exception:
                continue

            if abs(current_res - self.target_resolution_m) < 0.5:
                continue  # Already 10 m

            # Resample in-place via array resampling
            try:
                src_profile = raster.profile
                # Ensure it has a valid driver for in-memory resampling
                src_profile.setdefault("driver", "GTiff")

                array_2d = raster.array  # (H, W)
                array_3d = array_2d[np.newaxis, ...]  # (1, H, W)

                resampled_array, updated_profile = self._resampler.resample_array(
                    array=array_3d,
                    src_profile=src_profile,
                )
                raster._array = resampled_array[0].astype("float32")
                
                # Update raster profile and transform in memory
                raster.profile = updated_profile
                raster.transform = updated_profile["transform"]

                logger.debug(
                    f"Resampled {band.code}: "
                    f"{current_res:.0f}m → {self.target_resolution_m:.0f}m "
                    f"({resampled_array.shape[2]}×{resampled_array.shape[1]})"
                )

            except Exception as exc:
                logger.warning(
                    f"Could not resample {band.code}: {exc}. "
                    f"Keeping native resolution."
                )

        return scene

    # ------------------------------------------------------------------

    def _align_to_reference(
        self,
        scene: SentinelScene,
        reference: SentinelScene,
    ) -> SentinelScene:
        """
        Align scene rasters to the reference scene's pixel grid.

        Called when preprocessing T2 to co-register it to T1 so that
        the same pixel coordinates refer to the same ground location
        in both epochs.

        Parameters
        ----------
        scene : SentinelScene
        reference : SentinelScene

        Returns
        -------
        SentinelScene
        """

        bands_to_align = []
        for band in AI_BANDS:
            if scene.has_band(band) and reference.has_band(band):
                bands_to_align.append(band)
                
        if not bands_to_align:
            return scene
            
        ref_arrays = []
        tgt_arrays = []
        
        for band in bands_to_align:
            ref_arrays.append(reference.raster(band).array)
            tgt_arrays.append(scene.raster(band).array)
            
        # Stack into multi-band arrays (N, H, W)
        ref_stacked = np.stack(ref_arrays)
        tgt_stacked = np.stack(tgt_arrays)
        
        # All rasters share the same profile post-resampling
        ref_profile = reference.raster(bands_to_align[0]).profile
        tgt_profile = scene.raster(bands_to_align[0]).profile
        
        # Align all bands simultaneously
        aligned_array, aligned_profile = self._aligner.align_arrays(
            reference_array=ref_stacked,
            reference_profile=ref_profile,
            target_array=tgt_stacked,
            target_profile=tgt_profile,
        )
        
        # Unstack and assign back to individual rasters
        for i, band in enumerate(bands_to_align):
            tgt_raster = scene.raster(band)
            tgt_raster._array = aligned_array[i].astype("float32")
            tgt_raster.profile = aligned_profile
            tgt_raster.transform = aligned_profile["transform"]
            tgt_raster.crs = aligned_profile["crs"]

        logger.debug(
            f"Aligned {scene.product_name} → {reference.product_name}"
        )

        return scene

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"PreprocessingPipeline("
            f"resolution={self.target_resolution_m}m, "
            f"cloud_mask={self.apply_cloud_mask}, "
            f"normalize={self.apply_normalization})"
        )
