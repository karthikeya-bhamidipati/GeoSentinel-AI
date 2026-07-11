"""
===============================================================================
GeoSentinel AI

Module:
    src/eo/aoi/__init__.py

Description:
    Earth Observation AOI package.
    Exposes AOI geometry, validation, and boundary utilities.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from src.eo.aoi.geometry import AOI
from src.eo.aoi.validator import AOIValidator
from src.eo.aoi.boundary import get_boundary

__all__ = ["AOI", "AOIValidator", "get_boundary"]
