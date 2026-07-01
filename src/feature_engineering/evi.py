"""
===============================================================================
GeoSentinel AI

Module:
    evi.py

Description:
    Enhanced Vegetation Index (EVI).

    EVI = G * (NIR - RED) / (NIR + C1*RED - C2*BLUE + L)

    Standard coefficients: G=2.5, C1=6, C2=7.5, L=1

    Range: [-1, 1]
    Advantages over NDVI:
    - Less susceptible to atmospheric influences
    - Better sensitivity in dense canopy conditions
    - Decouples canopy background signal

    Reference:
    Huete et al. (2002). Overview of the radiometric and biophysical
    performance of the MODIS vegetation indices.
    Remote Sensing of Environment, 83(1-2), 195-213.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import numpy as np

from src.eo.models.bands import Band
from src.eo.models.scene import SentinelScene
from src.eo.exceptions import FeatureEngineeringError


class EVICalculator:
    """
    Computes the Enhanced Vegetation Index (EVI).

    EVI = G * (NIR - RED) / (NIR + C1*RED - C2*BLUE + L)

    Standard MOD13 coefficients:
    - G  = 2.5 (gain factor)
    - C1 = 6.0 (aerosol resistance coefficient 1)
    - C2 = 7.5 (aerosol resistance coefficient 2)
    - L  = 1.0 (canopy background adjustment)

    Requires:
    - B08 (NIR)
    - B04 (RED)
    - B02 (BLUE)
    """

    INDEX_NAME = "EVI"

    def __init__(
        self,
        G: float = 2.5,
        C1: float = 6.0,
        C2: float = 7.5,
        L: float = 1.0,
    ) -> None:

        self.G = G
        self.C1 = C1
        self.C2 = C2
        self.L = L

    def compute(
        self,
        nir: np.ndarray,
        red: np.ndarray,
        blue: np.ndarray,
        epsilon: float = 1e-10,
    ) -> np.ndarray:
        """
        Compute EVI.

        Parameters
        ----------
        nir, red, blue : np.ndarray
            Band arrays (float32, reflectance [0,1]).
        epsilon : float

        Returns
        -------
        np.ndarray
            EVI values, clipped to [-1, 1], dtype float32.
        """

        nir = nir.astype("float32")
        red = red.astype("float32")
        blue = blue.astype("float32")

        numerator = self.G * (nir - red)
        denominator = (
            nir + self.C1 * red - self.C2 * blue + self.L + epsilon
        )

        evi = numerator / denominator

        return np.clip(evi, -1.0, 1.0).astype("float32")

    def from_scene(self, scene: SentinelScene) -> np.ndarray:

        for band in (Band.NIR, Band.RED, Band.BLUE):
            if not scene.has_band(band):
                raise FeatureEngineeringError(
                    f"Band {band.code} required for EVI "
                    f"is missing from scene {scene.product_name}."
                )

        return self.compute(
            nir=scene.band(Band.NIR),
            red=scene.band(Band.RED),
            blue=scene.band(Band.BLUE),
        )

    def __repr__(self) -> str:
        return (
            f"EVICalculator("
            f"G={self.G}, C1={self.C1}, "
            f"C2={self.C2}, L={self.L})"
        )
