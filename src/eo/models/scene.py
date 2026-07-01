"""
===============================================================================
GeoSentinel AI

Module:
    scene.py

Description:
    Sentinel-2 Scene Domain Model

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.eo.models.bands import AI_BANDS, RGB_BANDS, Band
from src.eo.models.collection import RasterCollection
from src.eo.models.metadata import SentinelMetadata
from src.eo.models.raster import Raster


@dataclass(slots=True)
class SentinelScene:
    """
    Represents a complete Sentinel-2 scene.

    This is the primary domain object used throughout the
    GeoSentinel AI platform.

    A SentinelScene contains:

    - Scene metadata
    - Raster collection
    - Scene location
    - Helper methods

    The scene itself performs no processing.
    Processing is delegated to dedicated services.
    """

    metadata: SentinelMetadata

    rasters: RasterCollection = field(
        default_factory=RasterCollection
    )

    # ------------------------------------------------------------------
    # Raster Management
    # ------------------------------------------------------------------

    def add_raster(
        self,
        band: Band,
        path: str | Path,
    ) -> Raster:
        """
        Register a raster with the scene.
        """

        raster = Raster(
            band=band,
            path=Path(path),
        )

        self.rasters.add(raster)

        return raster

    # ------------------------------------------------------------------

    def raster(
        self,
        band: Band,
    ) -> Raster:
        """
        Return Raster object.
        """

        return self.rasters.get(band)

    # ------------------------------------------------------------------

    def band(
        self,
        band: Band,
    ):
        """
        Return raster array.
        """

        return self.raster(band).array

    # ------------------------------------------------------------------

    def has_band(
        self,
        band: Band,
    ) -> bool:

        return self.rasters.exists(band)

    # ------------------------------------------------------------------

    @property
    def available_bands(self):

        return self.rasters.available()

    # ------------------------------------------------------------------

    @property
    def rgb(self):

        return self.rasters.stack(RGB_BANDS)

    # ------------------------------------------------------------------

    @property
    def ai_stack(self):

        return self.rasters.stack(AI_BANDS)

    # ------------------------------------------------------------------
    # Metadata Shortcuts
    # ------------------------------------------------------------------

    @property
    def acquisition_date(self):

        return self.metadata.acquisition_date

    # ------------------------------------------------------------------

    @property
    def acquisition_datetime(self):

        return self.metadata.acquisition_datetime

    # ------------------------------------------------------------------

    @property
    def cloud_cover(self):

        return self.metadata.cloud_cover

    # ------------------------------------------------------------------

    @property
    def satellite(self):

        return self.metadata.satellite

    # ------------------------------------------------------------------

    @property
    def tile_id(self):

        return self.metadata.tile_id

    # ------------------------------------------------------------------

    @property
    def epsg(self):

        return self.metadata.epsg

    # ------------------------------------------------------------------

    @property
    def cached(self):

        return self.metadata.is_cached

    # ------------------------------------------------------------------

    @property
    def downloaded(self):

        return self.metadata.downloaded

    # ------------------------------------------------------------------

    @property
    def product_name(self):

        return self.metadata.product_name

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def unload(self):
        """
        Release all raster arrays from memory.
        """

        self.rasters.unload()

    # ------------------------------------------------------------------

    def summary(self) -> dict:
        """
        Scene summary.
        """

        return {

            "product_name": self.product_name,

            "satellite": self.satellite,

            "date": str(
                self.acquisition_date
            ),

            "tile": self.tile_id,

            "epsg": self.epsg,

            "cloud_cover": self.cloud_cover,

            "bands": self.rasters.names(),

            "number_of_bands": len(
                self.rasters
            ),

            "cached": self.cached,

            "downloaded": self.downloaded,

        }

    # ------------------------------------------------------------------

    def __len__(self):

        return len(
            self.rasters
        )

    # ------------------------------------------------------------------

    def __contains__(
        self,
        band: Band,
    ):

        return band in self.rasters

    # ------------------------------------------------------------------

    def __repr__(self):

        return (

            f"SentinelScene("
            f"{self.product_name}, "
            f"{len(self)} bands)"

        )