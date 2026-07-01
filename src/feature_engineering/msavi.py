"""
===============================================================================
GeoSentinel AI

Module:
    msavi.py

Description:
    Modified Soil-Adjusted Vegetation Index (MSAVI).

    MSAVI = [2*NIR + 1 - sqrt((2*NIR + 1)^2 - 8*(NIR - RED))] / 2

    Range: [-1, 1]
    Advantage over SAVI:
    - Self-adjusting soil factor (no need to estimate L)
    - More accurate for sparse vegetation

    Reference:
    Qi et al. (1994). A modified soil adjusted vegetation index.
    Remote Sensing of Environment, 48(2), 119-126.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import numpy as np

from src.eo.models.bands import Band
from src.eo.models.scene import SentinelScene
from src.eo.exceptions import FeatureEngineeringError


class MSAVICalculator:
    """
    Computes the Modified Soil-Adjusted Vegetation Index (MSAVI).

    Formula:
    MSAVI = [2*NIR + 1 - sqrt((2*NIR + 1)^2 - 8*(NIR - RED))] / 2

    Requires:
    - B08 (NIR)
    - B04 (RED)
    """

    INDEX_NAME = "MSAVI"

    def compute(
        self,
        nir: np.ndarray,
        red: np.ndarray,
    ) -> np.ndarray:
        """
        Compute MSAVI.

        Parameters
        ----------
        nir, red : np.ndarray

        Returns
        -------
        np.ndarray
            MSAVI values, dtype float32.
        """

        nir = nir.astype("float32")
        red = red.astype("float32")

        inner = (2.0 * nir + 1.0) ** 2 - 8.0 * (nir - red)

        # Clip to avoid sqrt of negative numbers from floating point errors
        inner = np.clip(inner, 0.0, None)

        msavi = (2.0 * nir + 1.0 - np.sqrt(inner)) / 2.0

        return np.clip(msavi, -1.0, 1.0).astype("float32")

    def from_scene(self, scene: SentinelScene) -> np.ndarray:

        for band in (Band.NIR, Band.RED):
            if not scene.has_band(band):
                raise FeatureEngineeringError(
                    f"Band {band.code} required for MSAVI "
                    f"is missing from scene {scene.product_name}."
                )

        return self.compute(
            nir=scene.band(Band.NIR),
            red=scene.band(Band.RED),
        )

    def __repr__(self) -> str:
        return "MSAVICalculator()"
