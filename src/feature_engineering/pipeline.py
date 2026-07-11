"""
===============================================================================
GeoSentinel AI

Module:
    pipeline.py (feature_engineering)

Description:
    Feature engineering pipeline — computes all spectral indices from a
    SentinelScene and assembles a FeatureStack for AI inference.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from src.eo.models.bands import Band
from src.eo.models.scene import SentinelScene
from src.eo.exceptions import FeatureEngineeringError
from src.feature_engineering.ndvi import NDVICalculator
from src.feature_engineering.ndbi import NDBICalculator
from src.feature_engineering.ndwi import NDWICalculator
from src.feature_engineering.mndwi import MNDWI
from src.feature_engineering.evi import EVICalculator
from src.feature_engineering.savi import SAVICalculator
from src.feature_engineering.msavi import MSAVICalculator
from src.feature_engineering.bsi import BSICalculator
from src.feature_engineering.stack import FeatureStack, FeatureStackBuilder
from src.utils.logger import logger


# Ordered spectral bands included in the feature stack
FEATURE_BANDS: tuple[Band, ...] = (
    Band.BLUE,
    Band.GREEN,
    Band.RED,
    Band.NIR,
    Band.SWIR_1,
)


@dataclass
class FeatureEngineeringResult:
    """
    Output of the feature engineering pipeline.

    Attributes
    ----------
    stack : FeatureStack
        Combined feature array (bands + indices).
    indices : dict[str, np.ndarray]
        Individual index arrays keyed by name.
    bands : dict[str, np.ndarray]
        Spectral band arrays used in the stack.
    """

    stack: FeatureStack
    indices: dict[str, np.ndarray] = field(default_factory=dict)
    bands: dict[str, np.ndarray] = field(default_factory=dict)


class FeatureEngineeringPipeline:
    """
    Computes all spectral indices from a SentinelScene and builds
    a multi-channel FeatureStack.
    """

    def __init__(self) -> None:

        self._ndvi = NDVICalculator()
        self._ndbi = NDBICalculator()
        self._ndwi = NDWICalculator()
        self._mndwi = MNDWI()
        self._evi = EVICalculator()
        self._savi = SAVICalculator()
        self._msavi = MSAVICalculator()
        self._bsi = BSICalculator()
        self._stack_builder = FeatureStackBuilder()

    # ------------------------------------------------------------------

    def run(
        self,
        scene: SentinelScene,
    ) -> FeatureEngineeringResult:
        """
        Compute all indices and build the feature stack.
        """

        logger.info(
            f"Computing spectral features: {scene.product_name}"
        )

        bands: dict[str, np.ndarray] = {}

        for band in FEATURE_BANDS:
            if scene.has_band(band):
                bands[band.code] = scene.band(band)
            else:
                logger.warning(
                    f"Band {band.code} missing from scene. "
                    f"Filling with zeros."
                )
                bands[band.code] = np.zeros((1, 1), dtype="float32")

        indices: dict[str, np.ndarray] = {}

        calculators = [
            ("NDVI", self._ndvi),
            ("NDBI", self._ndbi),
            ("NDWI", self._ndwi),
            ("MNDWI", self._mndwi),
            ("EVI", self._evi),
            ("SAVI", self._savi),
            ("MSAVI", self._msavi),
            ("BSI", self._bsi),
        ]

        for index_name, calculator in calculators:
            try:
                indices[index_name] = calculator.from_scene(scene)
                logger.debug(f"Computed: {index_name}")

            except FeatureEngineeringError as exc:
                logger.warning(
                    f"Could not compute {index_name}: {exc}. "
                    f"Filling with zeros."
                )
                # Determine shape from available array
                ref_band = next(iter(bands.values()))
                indices[index_name] = np.zeros(
                    ref_band.shape, dtype="float32"
                )

        # ----------------------------------------------------------
        # Step 3: Build unified feature stack
        # ----------------------------------------------------------

        stack = self._stack_builder.build(
            bands=bands,
            indices=indices,
        )

        logger.info(
            f"Feature stack built: {stack.n_channels} channels "
            f"({stack.height}x{stack.width})"
        )

        return FeatureEngineeringResult(
            stack=stack,
            indices=indices,
            bands=bands,
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return "FeatureEngineeringPipeline(12 channels)"
