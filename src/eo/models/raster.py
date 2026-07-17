"""
===============================================================================
GeoSentinel AI

Module:
    raster.py

Description:
    Raster Model

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import rasterio
from rasterio.coords import BoundingBox
from rasterio.crs import CRS
from rasterio.transform import Affine

from src.eo.models.bands import Band


@dataclass(slots=True)
class Raster:
    """
    Represents a single raster layer.

    A Raster may represent:

    - Sentinel band
    - Spectral index
    - Segmentation mask
    - Probability map
    - Change map

    The Raster class lazily loads data from disk and caches it
    in memory after the first read.
    """

    band: Band

    path: Path

    _array: np.ndarray | None = field(
        default=None,
        init=False,
        repr=False,
    )

    _profile_override: dict | None = field(default=None, init=False, repr=False)
    _transform_override: Affine | None = field(default=None, init=False, repr=False)
    _crs_override: CRS | None = field(default=None, init=False, repr=False)

    # ------------------------------------------------------------------

    @property
    def array(self) -> np.ndarray:

        if self._array is None:

            with rasterio.open(self.path) as src:

                self._array = src.read(1)

        return self._array

    # ------------------------------------------------------------------

    @property
    def profile(self):
        if self._profile_override is not None:
            return self._profile_override

        with rasterio.open(self.path) as src:

            return src.profile

    @profile.setter
    def profile(self, value: dict):
        self._profile_override = value

    # ------------------------------------------------------------------

    @property
    def transform(self) -> Affine:
        if self._transform_override is not None:
            return self._transform_override

        with rasterio.open(self.path) as src:

            return src.transform
            
    @transform.setter
    def transform(self, value: Affine):
        self._transform_override = value

    # ------------------------------------------------------------------

    @property
    def crs(self) -> CRS:
        if self._crs_override is not None:
            return self._crs_override

        with rasterio.open(self.path) as src:

            return src.crs
            
    @crs.setter
    def crs(self, value: CRS):
        self._crs_override = value

    # ------------------------------------------------------------------

    @property
    def bounds(self) -> BoundingBox:

        with rasterio.open(self.path) as src:

            return src.bounds

    # ------------------------------------------------------------------

    @property
    def resolution(self):

        with rasterio.open(self.path) as src:

            return src.res

    # ------------------------------------------------------------------

    @property
    def shape(self):

        return self.array.shape

    # ------------------------------------------------------------------

    @property
    def dtype(self):

        return self.array.dtype

    # ------------------------------------------------------------------

    @property
    def width(self):

        return self.shape[1]

    # ------------------------------------------------------------------

    @property
    def height(self):

        return self.shape[0]

    # ------------------------------------------------------------------

    @property
    def statistics(self):

        image = self.array

        return {

            "min": float(image.min()),

            "max": float(image.max()),

            "mean": float(image.mean()),

            "std": float(image.std()),

        }

    # ------------------------------------------------------------------

    def unload(self):

        """
        Remove raster from memory.
        """

        self._array = None

    # ------------------------------------------------------------------

    def __repr__(self):

        return (

            f"Raster("
            f"{self.band.code}, "
            f"{self.width}x{self.height})"

        )