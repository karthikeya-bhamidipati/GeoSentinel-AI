"""
===============================================================================
GeoSentinel AI

Package:
    src.eo

Description:
    Earth Observation Engine package.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from src.eo.aoi.geometry import AOI
from src.eo.aoi.validator import AOIValidator
from src.eo.cache import CacheManager
from src.eo.exceptions import (
    AOIError,
    AOIOutsideBoundaryError,
    AOITooLargeError,
    CDSEError,
    GeoSentinelError,
    InvalidGeometryError,
    SceneNotFoundError,
)
from src.eo.models.bands import AI_BANDS, RGB_BANDS, Band
from src.eo.models.collection import RasterCollection
from src.eo.models.metadata import SentinelMetadata
from src.eo.models.raster import Raster
from src.eo.models.scene import SentinelScene

__all__ = [
    "AOI",
    "AOIValidator",
    "CacheManager",
    "GeoSentinelError",
    "AOIError",
    "AOIOutsideBoundaryError",
    "AOITooLargeError",
    "CDSEError",
    "InvalidGeometryError",
    "SceneNotFoundError",
    "Band",
    "AI_BANDS",
    "RGB_BANDS",
    "Raster",
    "RasterCollection",
    "SentinelMetadata",
    "SentinelScene",
]
