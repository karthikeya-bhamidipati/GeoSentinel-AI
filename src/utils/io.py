"""
===============================================================================
GeoSentinel AI

Module:
    io.py

Description:
    Raster and vector I/O utilities for the GeoSentinel AI platform.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import Affine

from src.utils.logger import logger


# =============================================================================
# Raster I/O
# =============================================================================


def read_raster(path: str | Path) -> tuple[np.ndarray, dict]:
    """
    Read a raster file and return the array and profile.

    Parameters
    ----------
    path : str | Path

    Returns
    -------
    tuple[np.ndarray, dict]
        (array, rasterio profile)

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Raster not found: {path}")

    with rasterio.open(path) as src:
        array = src.read()
        profile = src.profile.copy()

    logger.debug(f"Read raster: {path.name} {array.shape}")

    return array, profile


def write_raster(
    path: str | Path,
    array: np.ndarray,
    crs: CRS,
    transform: Affine,
    dtype: str = "float32",
    nodata: float | None = None,
) -> None:
    """
    Write a numpy array as a GeoTIFF.

    Parameters
    ----------
    path : str | Path
    array : np.ndarray
        Shape (bands, height, width) or (height, width).
    crs : rasterio.crs.CRS
    transform : Affine
    dtype : str
    nodata : float | None
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if array.ndim == 2:
        array = array[np.newaxis, ...]

    bands, height, width = array.shape

    profile = {
        "driver": "GTiff",
        "dtype": dtype,
        "width": width,
        "height": height,
        "count": bands,
        "crs": crs,
        "transform": transform,
        "compress": "lzw",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }

    if nodata is not None:
        profile["nodata"] = nodata

    with rasterio.open(path, "w", **profile) as dst:
        dst.write(array.astype(dtype))

    logger.debug(f"Written raster: {path.name} {array.shape}")


def read_band(
    path: str | Path,
    band_index: int = 1,
) -> tuple[np.ndarray, dict]:
    """
    Read a single band from a raster file.

    Parameters
    ----------
    path : str | Path
    band_index : int
        1-indexed band number.

    Returns
    -------
    tuple[np.ndarray, dict]
    """

    path = Path(path)

    with rasterio.open(path) as src:
        array = src.read(band_index).astype("float32")
        profile = src.profile.copy()

    return array, profile


# =============================================================================
# GeoJSON I/O
# =============================================================================


def read_geojson(path: str | Path) -> dict:
    """
    Read a GeoJSON file.

    Parameters
    ----------
    path : str | Path

    Returns
    -------
    dict
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"GeoJSON not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    logger.debug(f"Read GeoJSON: {path.name}")

    return data


def write_geojson(
    path: str | Path,
    data: dict,
) -> None:
    """
    Write a GeoJSON file.

    Parameters
    ----------
    path : str | Path
    data : dict
        GeoJSON-compliant dictionary.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    logger.debug(f"Written GeoJSON: {path.name}")


# =============================================================================
# CSV I/O
# =============================================================================


def write_csv(
    path: str | Path,
    rows: list[dict[str, Any]],
    fieldnames: list[str] | None = None,
) -> None:
    """
    Write a list of dicts as a CSV file.

    Parameters
    ----------
    path : str | Path
    rows : list[dict]
    fieldnames : list[str] | None
        Column names. If None, derived from the first row.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        logger.warning("write_csv called with empty rows.")
        return

    if fieldnames is None:
        fieldnames = list(rows[0].keys())

    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.debug(f"Written CSV: {path.name} ({len(rows)} rows)")


def read_csv(path: str | Path) -> list[dict[str, Any]]:
    """
    Read a CSV file as a list of dicts.

    Parameters
    ----------
    path : str | Path

    Returns
    -------
    list[dict]
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    logger.debug(f"Read CSV: {path.name} ({len(rows)} rows)")

    return rows


# =============================================================================
# JSON I/O
# =============================================================================


def read_json(path: str | Path) -> dict | list:
    """
    Read a JSON file.
    """

    path = Path(path)

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_json(
    path: str | Path,
    data: dict | list,
    indent: int = 2,
) -> None:
    """
    Write a dictionary or list as JSON.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=indent, default=str)
