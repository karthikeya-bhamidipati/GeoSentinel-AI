"""
===============================================================================
GeoSentinel AI

Module:
    utils.py

Description:
    Common utility functions used throughout the GeoSentinel AI platform.

Author:
    Karthikeya Bhamidipati

===============================================================================
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import yaml


# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)

logger = logging.getLogger("GeoSentinel")


# =============================================================================
# Time Utilities
# =============================================================================

def current_timestamp() -> str:
    """
    Returns the current timestamp.

    Returns
    -------
    str
        Timestamp in YYYY-MM-DD HH:MM:SS format.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =============================================================================
# Directory Utilities
# =============================================================================

def ensure_directory(path: str | Path) -> Path:
    """
    Creates a directory if it does not already exist.

    Parameters
    ----------
    path : str | Path

    Returns
    -------
    Path
    """
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def file_exists(path: str | Path) -> bool:
    """
    Checks whether a file exists.

    Parameters
    ----------
    path : str | Path

    Returns
    -------
    bool
    """
    return Path(path).exists()


# =============================================================================
# JSON Utilities
# =============================================================================

def save_json(data: dict, filepath: str | Path) -> None:
    """
    Save dictionary as JSON.
    """
    filepath = Path(filepath)

    with filepath.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def load_json(filepath: str | Path) -> dict:
    """
    Load JSON file.
    """
    filepath = Path(filepath)

    with filepath.open("r", encoding="utf-8") as file:
        return json.load(file)


# =============================================================================
# YAML Utilities
# =============================================================================

def save_yaml(data: dict, filepath: str | Path) -> None:
    """
    Save dictionary as YAML.
    """
    filepath = Path(filepath)

    with filepath.open("w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, sort_keys=False)


def load_yaml(filepath: str | Path) -> dict:
    """
    Load YAML configuration file.
    """
    filepath = Path(filepath)

    with filepath.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


# =============================================================================
# Timer Decorator
# =============================================================================

def timer(func: Callable) -> Callable:
    """
    Decorator that measures execution time.
    """

    def wrapper(*args, **kwargs):

        start = time.perf_counter()

        result = func(*args, **kwargs)

        end = time.perf_counter()

        logger.info(
            f"{func.__name__} completed in {end - start:.2f} seconds"
        )

        return result

    return wrapper


# =============================================================================
# File Utilities
# =============================================================================

def delete_file(filepath: str | Path) -> None:
    """
    Deletes a file if it exists.
    """
    filepath = Path(filepath)

    if filepath.exists():
        filepath.unlink()


def delete_directory(directory: str | Path) -> None:
    """
    Deletes an entire directory.
    """
    directory = Path(directory)

    if directory.exists():
        shutil.rmtree(directory)


# =============================================================================
# Console Banner
# =============================================================================

def print_banner() -> None:
    """
    Prints the GeoSentinel AI banner.
    """

    banner = r"""

   _____            _____            _   _ _             _
  / ____|          / ____|          | | (_) |           | |
 | |  __  ___  ___| (___   ___ _ __ | |_ _| |_ ___  __ _| |
 | | |_ |/ _ \/ _ \\___ \ / _ \ '_ \| __| | __/ _ \/ _` | |
 | |__| |  __/ (_) |___) |  __/ | | | |_| | ||  __/ (_| | |
  \_____|\___|\___/_____/ \___|_| |_|\__|_|\__\___|\__,_|_|

                    GeoSentinel AI

    """

    print(banner)