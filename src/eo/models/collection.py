"""
===============================================================================
GeoSentinel AI

Module:
    collection.py

Description:
    Raster Collection Model

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np

from src.eo.models.bands import Band
from src.eo.models.raster import Raster


class RasterCollection:
    """
    Collection of Raster objects.

    Responsible only for managing rasters.
    It does not know anything about Sentinel,
    AOIs, APIs or Machine Learning.
    """

    def __init__(self):

        self._rasters: dict[Band, Raster] = {}

    # ------------------------------------------------------------------
    # Basic Operations
    # ------------------------------------------------------------------

    def add(
        self,
        raster: Raster,
    ) -> None:
        """
        Add a raster to the collection.
        """

        self._rasters[raster.band] = raster

    # ------------------------------------------------------------------

    def remove(
        self,
        band: Band,
    ) -> None:
        """
        Remove a raster.
        """

        self._rasters.pop(band, None)

    # ------------------------------------------------------------------

    def get(
        self,
        band: Band,
    ) -> Raster:
        """
        Retrieve a raster.
        """

        if band not in self._rasters:

            raise KeyError(
                f"{band.code} is not available."
            )

        return self._rasters[band]

    # ------------------------------------------------------------------

    def exists(
        self,
        band: Band,
    ) -> bool:
        """
        Check if a raster exists.
        """

        return band in self._rasters

    # ------------------------------------------------------------------
    # Information
    # ------------------------------------------------------------------

    def available(self) -> list[Band]:
        """
        Return available bands.
        """

        return sorted(
            self._rasters.keys(),
            key=lambda band: band.code,
        )

    # ------------------------------------------------------------------

    def names(self) -> list[str]:
        """
        Return available band names.
        """

        return [

            band.code

            for band in self.available()

        ]

    # ------------------------------------------------------------------

    def stack(
        self,
        bands: list[Band] | tuple[Band, ...],
    ) -> np.ndarray:
        """
        Stack multiple rasters.

        Returns
        -------
        (Bands, Height, Width)
        """

        arrays = [

            self.get(band).array

            for band in bands

        ]

        return np.stack(
            arrays,
            axis=0,
        )

    # ------------------------------------------------------------------

    def unload(self) -> None:
        """
        Clear raster cache.
        """

        for raster in self._rasters.values():

            raster.unload()

    # ------------------------------------------------------------------

    def clear(self) -> None:
        """
        Remove all rasters.
        """

        self._rasters.clear()

    # ------------------------------------------------------------------

    def summary(self) -> dict:
        """
        Collection summary.
        """

        return {

            "count": len(self),

            "bands": self.names(),

        }

    # ------------------------------------------------------------------
    # Magic Methods
    # ------------------------------------------------------------------

    def __contains__(
        self,
        band: Band,
    ) -> bool:

        return band in self._rasters

    # ------------------------------------------------------------------

    def __getitem__(
        self,
        band: Band,
    ) -> Raster:

        return self.get(band)

    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[Raster]:

        return iter(
            self._rasters.values()
        )

    # ------------------------------------------------------------------

    def __len__(self) -> int:

        return len(
            self._rasters
        )

    # ------------------------------------------------------------------

    def __repr__(self):

        return (

            f"RasterCollection("
            f"{len(self)} rasters)"

        )