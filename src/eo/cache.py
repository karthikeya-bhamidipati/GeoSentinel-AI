"""
===============================================================================
GeoSentinel AI

Module:
    cache.py

Description:
    Cache manager for GeoSentinel AI.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.utils.logger import logger
from src.utils.paths import paths


class CacheManager:
    """
    Cache manager for Sentinel products.

    Responsible for

    - SAFE cache
    - Download cache
    - AOI cache
    - Future API cache
    """

    def __init__(self):

        self.cache_directory = paths.CACHE_DIR

        self.cache_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        logger.info(
            f"Cache initialized:\n{self.cache_directory}"
        )

    # ------------------------------------------------------------------

    def generate_key(self, value: str) -> str:
        """
        Generate SHA256 cache key.
        """

        return hashlib.sha256(
            value.encode("utf-8")
        ).hexdigest()

    # ------------------------------------------------------------------

    def cache_file(self, key: str) -> Path:
        """
        Return cache file path.
        """

        return self.cache_directory / f"{key}.json"

    # ------------------------------------------------------------------

    def exists(self, key: str) -> bool:
        """
        Check if cache exists.
        """

        return self.cache_file(key).exists()

    # ------------------------------------------------------------------

    def save(
        self,
        key: str,
        data: dict,
    ) -> None:
        """
        Save cache.
        """

        cache_path = self.cache_file(key)

        with open(
            cache_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
            )

        logger.info(
            f"Cache saved:\n{cache_path.name}"
        )

    # ------------------------------------------------------------------

    def load(self, key: str) -> dict:
        """
        Load cache.
        """

        cache_path = self.cache_file(key)

        if not cache_path.exists():

            raise FileNotFoundError(
                cache_path
            )

        with open(
            cache_path,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        logger.info(
            f"Cache loaded:\n{cache_path.name}"
        )

        return data

    # ------------------------------------------------------------------

    def remove(self, key: str) -> None:
        """
        Delete cache.
        """

        cache_path = self.cache_file(key)

        if cache_path.exists():

            cache_path.unlink()

            logger.info(
                f"Cache removed:\n{cache_path.name}"
            )

    # ------------------------------------------------------------------

    def clear(self) -> None:
        """
        Delete all cache.
        """

        files = list(
            self.cache_directory.glob("*.json")
        )

        for file in files:

            file.unlink()

        logger.info(
            "Cache cleared."
        )

    # ------------------------------------------------------------------

    def list(self) -> list[str]:
        """
        List cache entries.
        """

        files = sorted(
            self.cache_directory.glob("*.json")
        )

        return [

            file.stem

            for file in files

        ]

    # ------------------------------------------------------------------

    def info(self) -> dict:
        """
        Cache statistics.
        """

        files = list(
            self.cache_directory.glob("*.json")
        )

        total_size = sum(

            file.stat().st_size

            for file in files

        )

        return {

            "cache_directory": str(
                self.cache_directory
            ),

            "entries": len(files),

            "size_bytes": total_size,

        }

    # ------------------------------------------------------------------

    def __len__(self):

        return len(self.list())

    # ------------------------------------------------------------------

    def __repr__(self):

        return (

            f"CacheManager("
            f"{len(self)} entries)"

        )