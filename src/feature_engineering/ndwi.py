"""
===============================================================================
GeoSentinel AI

Module:
    ndwi.py

Description:
    Normalized Difference Water Index (NDWI).

    NDWI = (GREEN - NIR) / (GREEN + NIR)

    Range: [-1, 1]
    Positive values: Water bodies
    Negative values: Vegetation, soil, urban

    Reference:
    McFeeters, S.K. (1996). The use of the Normalized Difference Water
    Index (NDWI) in the delineation of open water features.
    International Journal of Remote Sensing, 17(7), 1425-1432.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import numpy as np

from src.eo.models.bands import Band
from src.eo.models.scene import SentinelScene
from src.eo.exceptions import FeatureEngineeringError


class NDWICalculator:
    """
    Computes the Normalized Difference Water Index (NDWI).

    NDWI = (GREEN - NIR) / (GREEN + NIR)

    Requires:
    - B03 (GREEN)
    - B08 (NIR)
    """

    INDEX_NAME = "NDWI"

    def compute(
        self,
        green: np.ndarray,
        nir: np.ndarray,
        epsilon: float = 1e-10,
    ) -> np.ndarray:
        """
        Compute NDWI.

        Parameters
        ----------
        green : np.ndarray
        nir : np.ndarray
        epsilon : float

        Returns
        -------
        np.ndarray
            NDWI values in [-1, 1], dtype float32.
        """

        green = green.astype("float32")
        nir = nir.astype("float32")

        ndwi = (green - nir) / (green + nir + epsilon)

        return np.clip(ndwi, -1.0, 1.0).astype("float32")

    def from_scene(self, scene: SentinelScene) -> np.ndarray:

        for band in (Band.GREEN, Band.NIR):
            if not scene.has_band(band):
                raise FeatureEngineeringError(
                    f"Band {band.code} required for NDWI "
                    f"is missing from scene {scene.product_name}."
                )

        return self.compute(
            green=scene.band(Band.GREEN),
            nir=scene.band(Band.NIR),
        )

    def __repr__(self) -> str:
        return "NDWICalculator()"
