"""
===============================================================================
GeoSentinel AI

Module:
    normalize.py

Description:
    Band normalization for Sentinel-2 L2A imagery.

    Sentinel-2 L2A products store surface reflectance values as
    unsigned 16-bit integers scaled by a factor of 10,000.
    Dividing by 10,000 converts them to physical reflectance in [0, 1].

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import numpy as np

from src.eo.models.scene import SentinelScene
from src.eo.exceptions import PreprocessingError
from src.utils.logger import logger


# Sentinel-2 L2A quantification value
SENTINEL2_SCALE_FACTOR = 10_000.0

# Valid reflectance range after normalization
REFLECTANCE_MIN = 0.0
REFLECTANCE_MAX = 1.0


class BandNormalizer:
    """
    Normalizes Sentinel-2 L2A band values to physical reflectance [0, 1].

    Applies the standard Sentinel-2 L2A quantification factor:
        reflectance = DN / 10000

    Values are clipped to [0, 1] to handle occasional sensor artifacts
    or atmospheric correction residuals.

    This class operates on SentinelScene raster arrays in-place.
    It does not load or write files.
    """

    def __init__(
        self,
        scale_factor: float = SENTINEL2_SCALE_FACTOR,
    ) -> None:

        self.scale_factor = scale_factor

    # ------------------------------------------------------------------

    def normalize_array(self, array: np.ndarray) -> np.ndarray:
        """
        Normalize a raw DN array to reflectance [0, 1].

        Parameters
        ----------
        array : np.ndarray
            Raw digital number (DN) array from Sentinel-2.

        Returns
        -------
        np.ndarray
            Float32 array of surface reflectance values in [0, 1].
        """

        normalized = array.astype("float32") / self.scale_factor

        return np.clip(normalized, REFLECTANCE_MIN, REFLECTANCE_MAX)

    # ------------------------------------------------------------------

    def normalize_scene(self, scene: SentinelScene) -> SentinelScene:
        """
        Normalize all loaded raster arrays within a SentinelScene.

        This modifies the in-memory arrays of each raster in place.
        The on-disk files are not altered.

        Parameters
        ----------
        scene : SentinelScene

        Returns
        -------
        SentinelScene
            The same scene object with normalized arrays.

        Raises
        ------
        PreprocessingError
            If normalization fails for any band.
        """

        logger.info(
            f"Normalizing {len(scene)} bands "
            f"for scene: {scene.product_name}"
        )

        for raster in scene.rasters:

            try:
                raw = raster.array
                raster._array = self.normalize_array(raw)

            except Exception as exc:
                raise PreprocessingError(
                    f"Normalization failed for band {raster.band.code}: {exc}"
                ) from exc

        logger.info("Band normalization complete.")

        return scene

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"BandNormalizer("
            f"scale_factor={self.scale_factor})"
        )
