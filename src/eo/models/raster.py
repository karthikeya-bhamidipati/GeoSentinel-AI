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

        with rasterio.open(self.path) as src:

            return src.profile

    # ------------------------------------------------------------------

    @property
    def transform(self) -> Affine:

        with rasterio.open(self.path) as src:

            return src.transform

    # ------------------------------------------------------------------

    @property
    def crs(self) -> CRS:

        with rasterio.open(self.path) as src:

            return src.crs

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