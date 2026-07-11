"""
===============================================================================
GeoSentinel AI

Module:
    ndbi.py

Description:
    Normalized Difference Built-up Index (NDBI).

    NDBI = (SWIR1 - NIR) / (SWIR1 + NIR)

    Range: [-1, 1]
    High values (> 0): Built-up areas, urban surfaces
    Low values (< 0): Vegetation, water

    Reference:
    Zha et al. (2003). Use of normalized difference built-up index in
    automatically mapping urban areas from TM imagery. International
    Journal of Remote Sensing, 24(3), 583-594.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import numpy as np

from src.eo.models.bands import Band
from src.eo.models.scene import SentinelScene
from src.eo.exceptions import FeatureEngineeringError


class NDBICalculator:
    """
    Computes the Normalized Difference Built-up Index (NDBI).

    NDBI = (SWIR1 - NIR) / (SWIR1 + NIR)

    Requires Sentinel-2 bands:
    - B11 (SWIR1)
    - B08 (NIR)
    """

    INDEX_NAME = "NDBI"

    def compute(
        self,
        swir1: np.ndarray,
        nir: np.ndarray,
        epsilon: float = 1e-10,
    ) -> np.ndarray:
        """
        Compute NDBI from SWIR1 and NIR arrays.

        Parameters
        ----------
        swir1 : np.ndarray
        nir : np.ndarray
        epsilon : float

        Returns
        -------
        np.ndarray
            NDBI values in [-1, 1], dtype float32.
        """

        swir1 = swir1.astype("float32")
        nir = nir.astype("float32")

        if swir1.shape != nir.shape:
            fy = max(1, round(nir.shape[0] / swir1.shape[0]))
            fx = max(1, round(nir.shape[1] / swir1.shape[1]))
            swir1 = np.repeat(np.repeat(swir1, fy, axis=0), fx, axis=1)
            swir1 = swir1[:nir.shape[0], :nir.shape[1]]

        numerator = swir1 - nir
        denominator = swir1 + nir + epsilon

        ndbi = numerator / denominator

        return np.clip(ndbi, -1.0, 1.0).astype("float32")

    def from_scene(self, scene: SentinelScene) -> np.ndarray:
        """
        Compute NDBI from a SentinelScene.
        """

        for band in (Band.SWIR_1, Band.NIR):
            if not scene.has_band(band):
                raise FeatureEngineeringError(
                    f"Band {band.code} required for NDBI "
                    f"is missing from scene {scene.product_name}."
                )

        return self.compute(
            swir1=scene.band(Band.SWIR_1),
            nir=scene.band(Band.NIR),
        )

    def __repr__(self) -> str:
        return "NDBICalculator()"
