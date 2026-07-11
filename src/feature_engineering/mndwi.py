"""
===============================================================================
GeoSentinel AI

Module:
    mndwi.py

Description:
    Modified Normalized Difference Water Index (MNDWI) calculation.
    Formula: (Green - SWIR1) / (Green + SWIR1)
    For Sentinel-2: (B03 - B11) / (B03 + B11)

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

import numpy as np

from src.eo.models.bands import Band
from src.eo.models.scene import SentinelScene
from src.eo.exceptions import FeatureEngineeringError


class MNDWI:
    """
    Computes Modified Normalized Difference Water Index (MNDWI).
    """

    @staticmethod
    def compute(
        green: np.ndarray,
        swir1: np.ndarray,
        epsilon: float = 1e-8,
    ) -> np.ndarray:
        """
        Compute MNDWI from Green and SWIR1 arrays.

        Parameters
        ----------
        green : np.ndarray
        swir1 : np.ndarray
        epsilon : float

        Returns
        -------
        np.ndarray
            MNDWI values in [-1.0, 1.0].
        """

        # Ensure swir1 matches green exactly (handles 20m to 10m discrepancies)
        if green.shape != swir1.shape:
            import cv2
            swir1 = cv2.resize(
                swir1,
                (green.shape[1], green.shape[0]),
                interpolation=cv2.INTER_LINEAR
            )

        numerator = green - swir1
        denominator = green + swir1 + epsilon

        mndwi = np.divide(numerator, denominator, dtype=np.float32)
        return np.clip(mndwi, -1.0, 1.0)

    @classmethod
    def from_scene(cls, scene: SentinelScene) -> np.ndarray:
        """
        Compute MNDWI directly from a SentinelScene.

        Raises
        ------
        FeatureEngineeringError
            If B03 or B11 are missing.
        """

        if not scene.has_band(Band.GREEN):
            raise FeatureEngineeringError("MNDWI requires Green band (B03).")
        if not scene.has_band(Band.SWIR_1):
            raise FeatureEngineeringError("MNDWI requires SWIR1 band (B11).")

        return cls.compute(
            green=scene.band(Band.GREEN),
            swir1=scene.band(Band.SWIR_1),
        )
