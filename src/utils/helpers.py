"""
===============================================================================
GeoSentinel AI

Module:
    helpers.py

Description:
    General-purpose utility helpers for the GeoSentinel AI platform.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any

from shapely.geometry import box, shape, Polygon


# =============================================================================
# Date Utilities
# =============================================================================


def parse_date(value: str | date | datetime) -> date:
    """
    Parse a date from a string, date, or datetime object.

    Parameters
    ----------
    value : str | date | datetime

    Returns
    -------
    date

    Raises
    ------
    ValueError
        If the string cannot be parsed as a date.
    """

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Cannot parse date: {value!r}")


def date_range_days(start: date, end: date) -> int:
    """
    Return the number of days between two dates.
    """

    return abs((end - start).days)


def format_date_for_cdse(value: date) -> str:
    """
    Format a date as ISO 8601 string for CDSE API queries.
    """

    return value.strftime("%Y-%m-%dT00:00:00.000Z")


# =============================================================================
# Bounding Box Utilities
# =============================================================================


def bbox_to_polygon(
    minx: float,
    miny: float,
    maxx: float,
    maxy: float,
) -> Polygon:
    """
    Create a Shapely Polygon from bounding box coordinates.

    Parameters
    ----------
    minx, miny, maxx, maxy : float
        Bounding box in WGS84 (lon/lat).

    Returns
    -------
    Polygon
    """

    return box(minx, miny, maxx, maxy)


def bbox_from_geojson(geojson: dict) -> tuple[float, float, float, float]:
    """
    Extract bounding box from a GeoJSON geometry.

    Returns
    -------
    tuple (minx, miny, maxx, maxy)
    """

    geometry = shape(geojson)

    return geometry.bounds


def expand_bbox(
    minx: float,
    miny: float,
    maxx: float,
    maxy: float,
    buffer_km: float,
) -> tuple[float, float, float, float]:
    """
    Expand a bounding box by a given distance in km.

    This uses an approximation (1 degree ≈ 111 km).

    Parameters
    ----------
    buffer_km : float
        Buffer distance in kilometres.

    Returns
    -------
    tuple (minx, miny, maxx, maxy)
    """

    deg = buffer_km / 111.0

    return (
        minx - deg,
        miny - deg,
        maxx + deg,
        maxy + deg,
    )


def bbox_to_wkt(
    minx: float,
    miny: float,
    maxx: float,
    maxy: float,
) -> str:
    """
    Convert bounding box to WKT POLYGON string.
    """

    return (
        f"POLYGON(({minx} {miny}, {maxx} {miny}, "
        f"{maxx} {maxy}, {minx} {maxy}, {minx} {miny}))"
    )


# =============================================================================
# Area Utilities
# =============================================================================


def pixel_area_km2(resolution_m: float) -> float:
    """
    Compute the area of a single pixel in km².

    Parameters
    ----------
    resolution_m : float
        Pixel resolution in metres.

    Returns
    -------
    float
        Area in km².
    """

    return (resolution_m ** 2) / 1_000_000


def pixel_count_to_km2(
    pixel_count: int,
    resolution_m: float = 10.0,
) -> float:
    """
    Convert pixel count to area in km².

    Parameters
    ----------
    pixel_count : int
    resolution_m : float
        Default 10m (Sentinel-2 resolution).

    Returns
    -------
    float
    """

    return pixel_count * pixel_area_km2(resolution_m)


# =============================================================================
# Numeric Utilities
# =============================================================================


def safe_divide(
    numerator: float,
    denominator: float,
    fill: float = 0.0,
) -> float:
    """
    Divide two numbers safely, returning fill value on zero division.
    """

    if denominator == 0:
        return fill

    return numerator / denominator


def clamp(
    value: float,
    min_val: float,
    max_val: float,
) -> float:
    """
    Clamp a value to [min_val, max_val].
    """

    return max(min_val, min(max_val, value))


def round_dict(data: dict[str, Any], decimals: int = 4) -> dict[str, Any]:
    """
    Round all float values in a dictionary to a specified number of decimals.
    """

    return {
        key: round(value, decimals) if isinstance(value, float) else value
        for key, value in data.items()
    }


# =============================================================================
# String Utilities
# =============================================================================


def slugify(text: str) -> str:
    """
    Convert a string to a safe filename slug.
    """

    return (
        text.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )


def human_readable_size(size_bytes: int) -> str:
    """
    Convert bytes to a human-readable string.
    """

    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))

    return f"{size_bytes / (1024 ** i):.2f} {units[i]}"
