"""
===============================================================================
GeoSentinel AI

Module:
    cloudmask.py

Description:
    Cloud and cloud shadow masking using Sentinel-2 Scene Classification
    Layer (SCL).

    The SCL band is produced by the Sen2Cor processor during L2A
    atmospheric correction. Each pixel is classified into one of 12
    classes. This module sets cloud and shadow pixels to NaN, allowing
    downstream modules to handle them as no-data.

    SCL Class Codes:
        0  = No Data
        1  = Saturated / Defective
        2  = Dark Area Pixels
        3  = Cloud Shadows
        4  = Vegetation
        5  = Not Vegetated
        6  = Water
        7  = Unclassified
        8  = Cloud medium probability
        9  = Cloud high probability
        10 = Thin Cirrus
        11 = Snow / Ice

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from enum import IntEnum

import numpy as np

from src.eo.models.bands import Band
from src.eo.models.scene import SentinelScene
from src.eo.exceptions import PreprocessingError
from src.utils.logger import logger


class SCLClass(IntEnum):
    """Sentinel-2 Scene Classification Layer class codes."""

    NO_DATA = 0
    SATURATED = 1
    DARK_AREA = 2
    CLOUD_SHADOW = 3
    VEGETATION = 4
    NOT_VEGETATED = 5
    WATER = 6
    UNCLASSIFIED = 7
    CLOUD_MEDIUM = 8
    CLOUD_HIGH = 9
    THIN_CIRRUS = 10
    SNOW_ICE = 11


# Pixel classes to mask out (cloud, shadow, saturated, no-data)
DEFAULT_INVALID_CLASSES: tuple[SCLClass, ...] = (
    SCLClass.NO_DATA,
    SCLClass.SATURATED,
    SCLClass.CLOUD_SHADOW,
    SCLClass.CLOUD_MEDIUM,
    SCLClass.CLOUD_HIGH,
    SCLClass.THIN_CIRRUS,
)


class CloudMasker:
    """
    Masks cloud-contaminated pixels using the Sentinel-2 SCL band.

    Applies a boolean mask to all spectral bands in a SentinelScene,
    setting invalid pixels (clouds, shadows, no-data) to NaN.

    Requires the SCL band to be present in the scene.
    If the SCL band is absent, a warning is logged and no masking
    is applied.
    """

    def __init__(
        self,
        invalid_classes: tuple[SCLClass, ...] = DEFAULT_INVALID_CLASSES,
        nodata_value: float = np.nan,
    ) -> None:

        self.invalid_classes = invalid_classes
        self.nodata_value = nodata_value

    # ------------------------------------------------------------------

    def build_cloud_mask(
        self,
        scl_array: np.ndarray,
    ) -> np.ndarray:
        """
        Build a boolean cloud mask from an SCL array.

        Parameters
        ----------
        scl_array : np.ndarray
            2D SCL array with integer class codes.

        Returns
        -------
        np.ndarray
            Boolean array (True = invalid / masked pixel).
        """

        mask = np.zeros(scl_array.shape, dtype=bool)

        for cls in self.invalid_classes:
            mask |= scl_array == int(cls)

        return mask

    # ------------------------------------------------------------------

    def apply_mask(
        self,
        data_array: np.ndarray,
        cloud_mask: np.ndarray,
    ) -> np.ndarray:
        """
        Apply a cloud mask to a data array.

        Parameters
        ----------
        data_array : np.ndarray
            2D or 3D (bands, height, width) array.
        cloud_mask : np.ndarray
            2D boolean mask.

        Returns
        -------
        np.ndarray
            Float32 array with masked pixels set to nodata_value.
        """

        result = data_array.astype("float32")

        if result.ndim == 2:
            result[cloud_mask] = self.nodata_value

        else:
            for i in range(result.shape[0]):
                result[i][cloud_mask] = self.nodata_value

        return result

    # ------------------------------------------------------------------

    def mask_scene(
        self,
        scene: SentinelScene,
    ) -> tuple[SentinelScene, np.ndarray]:
        """
        Apply cloud masking to all spectral bands in a scene.

        Parameters
        ----------
        scene : SentinelScene

        Returns
        -------
        tuple[SentinelScene, np.ndarray]
            (masked_scene, cloud_mask) where cloud_mask is the 2D
            boolean array of invalid pixels.

        Raises
        ------
        PreprocessingError
            If mask application fails.
        """

        if not scene.has_band(Band.SCL):
            logger.warning(
                f"SCL band not found in scene {scene.product_name}. "
                f"Cloud masking skipped."
            )
            empty_mask = np.zeros((1, 1), dtype=bool)
            return scene, empty_mask

        try:
            scl_array = scene.raster(Band.SCL).array

            cloud_mask = self.build_cloud_mask(scl_array)

            masked_pct = cloud_mask.mean() * 100

            logger.info(
                f"Cloud mask applied: {masked_pct:.1f}% pixels masked "
                f"({scene.product_name})"
            )

            # Apply mask to all non-SCL bands
            for raster in scene.rasters:

                if raster.band == Band.SCL:
                    continue

                raster._array = self.apply_mask(
                    raster.array, cloud_mask
                )

        except Exception as exc:
            raise PreprocessingError(
                f"Cloud masking failed: {exc}"
            ) from exc

        return scene, cloud_mask

    # ------------------------------------------------------------------

    def cloud_coverage_pct(
        self,
        scl_array: np.ndarray,
    ) -> float:
        """
        Compute the percentage of cloud-contaminated pixels.

        Parameters
        ----------
        scl_array : np.ndarray

        Returns
        -------
        float
            Percentage in [0, 100].
        """

        mask = self.build_cloud_mask(scl_array)

        return float(mask.mean() * 100)

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        classes = [c.name for c in self.invalid_classes]

        return (
            f"CloudMasker("
            f"invalid_classes={classes})"
        )
