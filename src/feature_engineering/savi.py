"""
===============================================================================
GeoSentinel AI

Module:
    savi.py

Description:
    Soil-Adjusted Vegetation Index (SAVI).

    SAVI = (1 + L) * (NIR - RED) / (NIR + RED + L)

    L = 0.5 (soil correction factor for intermediate vegetation density)

    Range: [-1, 1]
    Advantage: Reduces soil background noise compared to NDVI.

    Reference:
    Huete, A.R. (1988). A soil-adjusted vegetation index (SAVI).
    Remote Sensing of Environment, 25(3), 295-309.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import numpy as np

from src.eo.models.bands import Band
from src.eo.models.scene import SentinelScene
from src.eo.exceptions import FeatureEngineeringError


class SAVICalculator:
    """
    Computes the Soil-Adjusted Vegetation Index (SAVI).

    SAVI = (1 + L) * (NIR - RED) / (NIR + RED + L)

    Requires:
    - B08 (NIR)
    - B04 (RED)
    """

    INDEX_NAME = "SAVI"

    def __init__(self, L: float = 0.5) -> None:
        self.L = L

    def compute(
        self,
        nir: np.ndarray,
        red: np.ndarray,
        epsilon: float = 1e-10,
    ) -> np.ndarray:
        """
        Compute SAVI.

        Parameters
        ----------
        nir, red : np.ndarray
        epsilon : float

        Returns
        -------
        np.ndarray
            SAVI values in [-1, 1], dtype float32.
        """

        nir = nir.astype("float32")
        red = red.astype("float32")

        numerator = (1.0 + self.L) * (nir - red)
        denominator = nir + red + self.L + epsilon

        savi = numerator / denominator

        return np.clip(savi, -1.0, 1.0).astype("float32")

    def from_scene(self, scene: SentinelScene) -> np.ndarray:

        for band in (Band.NIR, Band.RED):
            if not scene.has_band(band):
                raise FeatureEngineeringError(
                    f"Band {band.code} required for SAVI "
                    f"is missing from scene {scene.product_name}."
                )

        return self.compute(
            nir=scene.band(Band.NIR),
            red=scene.band(Band.RED),
        )

    def __repr__(self) -> str:
        return f"SAVICalculator(L={self.L})"
