"""
===============================================================================
GeoSentinel AI

Module:
    pipeline.py

Description:
    Preprocessing pipeline that chains all preprocessing steps.

    Ordered steps:
    1. Clip to AOI
    2. Cloud masking (SCL)
    3. Resample to target resolution
    4. Spatial alignment (for T2 scenes, align to T1)
    5. Band normalization (DN → reflectance)

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

from src.eo.aoi.geometry import AOI
from src.eo.models.scene import SentinelScene
from src.eo.exceptions import PreprocessingError
from src.preprocessing.clip import RasterClipper
from src.preprocessing.cloudmask import CloudMasker
from src.preprocessing.resample import RasterResampler
from src.preprocessing.align import RasterAligner
from src.preprocessing.normalize import BandNormalizer
from src.utils.logger import logger


@dataclass
class PreprocessingResult:
    """
    Result of the preprocessing pipeline.

    Attributes
    ----------
    scene : SentinelScene
        The fully preprocessed scene.
    cloud_mask : np.ndarray
        Boolean array indicating masked pixels.
    cloud_coverage_pct : float
        Percentage of cloud-contaminated pixels.
    steps_applied : list[str]
        Names of preprocessing steps applied.
    """

    scene: SentinelScene
    cloud_mask: np.ndarray
    cloud_coverage_pct: float
    steps_applied: list[str] = field(default_factory=list)


class PreprocessingPipeline:
    """
    Chains all Sentinel-2 preprocessing steps into a single workflow.

    Steps applied (in order):
    1. Cloud masking (SCL-based)
    2. Resampling to target resolution
    3. Spatial alignment (optional — for T2 scenes vs. T1 reference)
    4. Band normalization (DN / 10000)

    Note: AOI clipping is performed at download time by CDSEProvider,
    so it is not repeated here.

    This class does not perform feature engineering or AI inference.
    """

    def __init__(
        self,
        target_resolution_m: float = 10.0,
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
            Optional reference scene. If provided, the scene is spatially
            aligned to the reference (used for T2 alignment to T1).

        Returns
        -------
        PreprocessingResult

        Raises
        ------
        PreprocessingError
            If any step fails.
        """

        steps_applied = []
        cloud_mask = np.zeros((1, 1), dtype=bool)
        cloud_coverage_pct = 0.0

        logger.info(
            f"Starting preprocessing pipeline: {scene.product_name}"
        )

        # ----------------------------------------------------------
        # Step 1: Cloud Masking
        # ----------------------------------------------------------

        if self.apply_cloud_mask:
            scene, cloud_mask = self._cloud_masker.mask_scene(scene)
            cloud_coverage_pct = float(cloud_mask.mean() * 100)
            steps_applied.append("cloud_masking")

            logger.info(
                f"Cloud mask: {cloud_coverage_pct:.1f}% masked"
            )

        # ----------------------------------------------------------
        # Step 2: Normalization
        # ----------------------------------------------------------

        if self.apply_normalization:
            scene = self._normalizer.normalize_scene(scene)
            steps_applied.append("normalization")

        # ----------------------------------------------------------
        # Step 3: Spatial Alignment (if reference provided)
        # ----------------------------------------------------------

        if reference_scene is not None:
            scene = self._align_to_reference(scene, reference_scene)
            steps_applied.append("spatial_alignment")

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

    def _align_to_reference(
        self,
        scene: SentinelScene,
        reference: SentinelScene,
    ) -> SentinelScene:
        """
        Align scene rasters to the reference scene's grid.

        Parameters
        ----------
        scene : SentinelScene
        reference : SentinelScene

        Returns
        -------
        SentinelScene
        """

        from src.eo.models.bands import AI_BANDS

        for band in AI_BANDS:
            if not scene.has_band(band) or not reference.has_band(band):
                continue

            ref_raster = reference.raster(band)
            tgt_raster = scene.raster(band)

            ref_array = ref_raster.array[np.newaxis, ...]
            tgt_array = tgt_raster.array[np.newaxis, ...]

            ref_profile = ref_raster.profile
            tgt_profile = tgt_raster.profile

            aligned_array, _ = self._aligner.align_arrays(
                reference_array=ref_array,
                reference_profile=ref_profile,
                target_array=tgt_array,
                target_profile=tgt_profile,
            )

            tgt_raster._array = aligned_array[0]

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
