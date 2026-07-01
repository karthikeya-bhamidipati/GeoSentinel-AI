"""
===============================================================================
GeoSentinel AI

Module:
    local_safe.py

Description:
    Local Sentinel-2 SAFE Provider.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.eo.providers.base import BaseProvider
from src.utils.logger import logger


class LocalSAFEProvider(BaseProvider):
    """
    Local provider for Sentinel-2 SAFE products.
    """

    def __init__(self):

        super().__init__("local_safe")

        self.connected = False

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """
        Initialize the provider.
        """

        logger.info("Initializing Local SAFE Provider...")

        self.connected = True

        logger.info("Local SAFE Provider initialized successfully.")

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, directory: str | Path) -> list[dict]:
        """
        Search a directory for SAFE products.

        Parameters
        ----------
        directory : str | Path

        Returns
        -------
        list[dict]
        """

        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(directory)

        safe_products = []

        for item in directory.iterdir():

            if item.is_dir() and item.suffix.lower() == ".safe":

                safe_products.append(
                    {
                        "name": item.name,
                        "path": item,
                    }
                )

        logger.info(
            f"Found {len(safe_products)} SAFE product(s)."
        )

        return safe_products

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load(self, source: str | Path) -> Path:
        """
        Load a SAFE product.

        Parameters
        ----------
        source : str | Path

        Returns
        -------
        Path
        """

        source = Path(source)

        if not source.exists():
            raise FileNotFoundError(source)

        if source.suffix.lower() != ".safe":
            raise ValueError(
                "Input must be a Sentinel-2 SAFE directory."
            )

        logger.info(f"Loaded SAFE product: {source.name}")

        return source

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def metadata(self, source: str | Path) -> dict:
        """
        Placeholder for metadata extraction.

        Metadata extraction will be implemented
        in src/ingestion/metadata.py
        """

        source = Path(source)

        return {
            "product_name": source.name,
            "provider": self.provider_name,
        }

    # ------------------------------------------------------------------
    # Bands
    # ------------------------------------------------------------------

    def available_bands(
        self,
        source: str | Path,
    ) -> list[str]:
        """
        Placeholder.

        Band discovery will be implemented
        in band_loader.py
        """

        return []

    def load_band(
        self,
        source: str | Path,
        band_name: str,
    ) -> Any:
        """
        Placeholder.

        Band loading will be implemented
        later.
        """

        raise NotImplementedError(
            "Band loading is implemented in band_loader.py"
        )

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------

    def close(self) -> None:

        logger.info("Closing Local SAFE Provider.")

        self.connected = False

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self, source: str | Path) -> bool:
        """
        Validate a SAFE product.

        Parameters
        ----------
        source : str | Path

        Returns
        -------
        bool
        """

        source = Path(source)

        if not source.exists():
            return False

        if source.suffix.lower() != ".safe":
            return False

        if not (source / "GRANULE").exists():
            return False

        if not (source / "MTD_MSIL2A.xml").exists():
            return False

        return True

    # ------------------------------------------------------------------

    def __str__(self):

        return (
            f"LocalSAFEProvider("
            f"connected={self.connected})"
        )