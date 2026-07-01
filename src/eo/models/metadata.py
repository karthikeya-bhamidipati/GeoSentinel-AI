"""
===============================================================================
GeoSentinel AI

Module:
    metadata.py

Description:
    Sentinel-2 Metadata Model

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class SentinelMetadata:
    """
    Metadata associated with a Sentinel-2 scene.

    This class stores metadata independently of the source.
    Whether the scene comes from CDSE, STAC, or a local SAFE
    product, the rest of the application interacts only with
    this model.
    """

    # ------------------------------------------------------------------
    # Product Information
    # ------------------------------------------------------------------

    product_id: str

    product_name: str

    satellite: str

    processing_level: str

    processing_baseline: str

    acquisition_datetime: datetime

    generation_datetime: datetime | None = None

    # ------------------------------------------------------------------
    # Orbit Information
    # ------------------------------------------------------------------

    orbit_number: int | None = None

    relative_orbit: int | None = None

    orbit_direction: str | None = None

    # ------------------------------------------------------------------
    # Tile Information
    # ------------------------------------------------------------------

    tile_id: str | None = None

    utm_zone: str | None = None

    epsg: int | None = None

    # ------------------------------------------------------------------
    # Scene Information
    # ------------------------------------------------------------------

    cloud_cover: float | None = None

    nodata_percentage: float | None = None

    snow_percentage: float | None = None

    water_percentage: float | None = None

    vegetation_percentage: float | None = None

    # ------------------------------------------------------------------
    # Download Information
    # ------------------------------------------------------------------

    source: str = "CDSE"

    local_path: Path | None = None

    download_url: str | None = None

    downloaded: bool = False

    cache_key: str | None = None

    # ------------------------------------------------------------------
    # Additional Metadata
    # ------------------------------------------------------------------

    extra: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------

    @property
    def acquisition_date(self):

        return self.acquisition_datetime.date()

    # ------------------------------------------------------------------

    @property
    def acquisition_time(self):

        return self.acquisition_datetime.time()

    # ------------------------------------------------------------------

    @property
    def is_cached(self):

        return self.local_path is not None

    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """
        Convert metadata into a serializable dictionary.
        """

        return {

            "product_id": self.product_id,

            "product_name": self.product_name,

            "satellite": self.satellite,

            "processing_level": self.processing_level,

            "processing_baseline": self.processing_baseline,

            "acquisition_datetime":
                self.acquisition_datetime.isoformat(),

            "generation_datetime":
                self.generation_datetime.isoformat()
                if self.generation_datetime
                else None,

            "orbit_number": self.orbit_number,

            "relative_orbit": self.relative_orbit,

            "orbit_direction": self.orbit_direction,

            "tile_id": self.tile_id,

            "utm_zone": self.utm_zone,

            "epsg": self.epsg,

            "cloud_cover": self.cloud_cover,

            "nodata_percentage": self.nodata_percentage,

            "snow_percentage": self.snow_percentage,

            "water_percentage": self.water_percentage,

            "vegetation_percentage": self.vegetation_percentage,

            "source": self.source,

            "local_path":
                str(self.local_path)
                if self.local_path
                else None,

            "download_url": self.download_url,

            "downloaded": self.downloaded,

            "cache_key": self.cache_key,

            "extra": self.extra,

        }

    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict):

        data = data.copy()

        data["acquisition_datetime"] = datetime.fromisoformat(
            data["acquisition_datetime"]
        )

        if data.get("generation_datetime"):

            data["generation_datetime"] = datetime.fromisoformat(
                data["generation_datetime"]
            )

        if data.get("local_path"):

            data["local_path"] = Path(
                data["local_path"]
            )

        return cls(**data)

    # ------------------------------------------------------------------

    def __repr__(self):

        return (

            f"SentinelMetadata("
            f"{self.product_name}, "
            f"{self.acquisition_date})"

        )