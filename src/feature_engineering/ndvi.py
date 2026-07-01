"""
===============================================================================
GeoSentinel AI

Module:
    ndvi.py

Description:
    Normalized Difference Vegetation Index (NDVI).

    NDVI = (NIR - RED) / (NIR + RED)

    Range: [-1, 1]
    High values (> 0.4): Dense vegetation
    Low values (< 0.1): Bare soil, urban, water

    Reference:
    Rouse et al. (1974). Monitoring vegetation systems in the Great Plains
    with ERTS. Proceedings of the Third Earth Resources Technology
    Satellite Symposium, 1, 309-317.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import numpy as np

from src.eo.models.bands import Band
from src.eo.models.scene import SentinelScene
from src.eo.exceptions import FeatureEngineeringError


class NDVICalculator:
    """
    Computes the Normalized Difference Vegetation Index (NDVI).

    NDVI = (NIR - RED) / (NIR + RED)

    Requires Sentinel-2 bands:
    - B08 (NIR)
    - B04 (RED)
    """

    INDEX_NAME = "NDVI"

    # ------------------------------------------------------------------

    def compute(
        self,
        nir: np.ndarray,
        red: np.ndarray,
        epsilon: float = 1e-10,
    ) -> np.ndarray:
        """
        Compute NDVI from NIR and RED arrays.

        Parameters
        ----------
        nir : np.ndarray
            Near-Infrared band array (float32, reflectance [0,1]).
        red : np.ndarray
            Red band array (float32, reflectance [0,1]).
        epsilon : float
            Small constant to prevent division by zero.

        Returns
        -------
        np.ndarray
            NDVI values in [-1, 1], dtype float32.
        """

        nir = nir.astype("float32")
        red = red.astype("float32")

        numerator = nir - red
        denominator = nir + red + epsilon

        ndvi = numerator / denominator

        return np.clip(ndvi, -1.0, 1.0).astype("float32")

    # ------------------------------------------------------------------

    def from_scene(self, scene: SentinelScene) -> np.ndarray:
        """
        Compute NDVI from a SentinelScene.

        Parameters
        ----------
        scene : SentinelScene

        Returns
        -------
        np.ndarray

        Raises
        ------
        FeatureEngineeringError
            If required bands are missing.
        """

        self._check_bands(scene)

        return self.compute(
            nir=scene.band(Band.NIR),
            red=scene.band(Band.RED),
        )

    # ------------------------------------------------------------------

    def _check_bands(self, scene: SentinelScene) -> None:

        for band in (Band.NIR, Band.RED):
            if not scene.has_band(band):
                raise FeatureEngineeringError(
                    f"Band {band.code} required for NDVI "
                    f"is missing from scene {scene.product_name}."
                )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return "NDVICalculator()"
