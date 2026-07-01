"""
===============================================================================
GeoSentinel AI

Module:
    bsi.py

Description:
    Bare Soil Index (BSI).

    BSI = [(SWIR1 + RED) - (NIR + BLUE)] / [(SWIR1 + RED) + (NIR + BLUE)]

    Range: [-1, 1]
    High values: Bare soil, disturbed land, construction
    Low values: Vegetation, water

    Reference:
    Rikimaru et al. (2002). Tropical forest cover density mapping.
    Tropical Ecology, 43(1), 39-47.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import numpy as np

from src.eo.models.bands import Band
from src.eo.models.scene import SentinelScene
from src.eo.exceptions import FeatureEngineeringError


class BSICalculator:
    """
    Computes the Bare Soil Index (BSI).

    BSI = [(SWIR1 + RED) - (NIR + BLUE)] / [(SWIR1 + RED) + (NIR + BLUE)]

    Requires:
    - B11 (SWIR1)
    - B04 (RED)
    - B08 (NIR)
    - B02 (BLUE)
    """

    INDEX_NAME = "BSI"

    def compute(
        self,
        swir1: np.ndarray,
        red: np.ndarray,
        nir: np.ndarray,
        blue: np.ndarray,
        epsilon: float = 1e-10,
    ) -> np.ndarray:
        """
        Compute BSI.

        Parameters
        ----------
        swir1, red, nir, blue : np.ndarray
        epsilon : float

        Returns
        -------
        np.ndarray
            BSI values in [-1, 1], dtype float32.
        """

        swir1 = swir1.astype("float32")
        red = red.astype("float32")
        nir = nir.astype("float32")
        blue = blue.astype("float32")

        numerator = (swir1 + red) - (nir + blue)
        denominator = (swir1 + red) + (nir + blue) + epsilon

        bsi = numerator / denominator

        return np.clip(bsi, -1.0, 1.0).astype("float32")

    def from_scene(self, scene: SentinelScene) -> np.ndarray:

        for band in (Band.SWIR_1, Band.RED, Band.NIR, Band.BLUE):
            if not scene.has_band(band):
                raise FeatureEngineeringError(
                    f"Band {band.code} required for BSI "
                    f"is missing from scene {scene.product_name}."
                )

        return self.compute(
            swir1=scene.band(Band.SWIR_1),
            red=scene.band(Band.RED),
            nir=scene.band(Band.NIR),
            blue=scene.band(Band.BLUE),
        )

    def __repr__(self) -> str:
        return "BSICalculator()"
