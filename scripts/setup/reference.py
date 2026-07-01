"""
===============================================================================
GeoSentinel AI

Module:
    reference.py

Description:
    Downloads and prepares all reference datasets required by
    GeoSentinel AI.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from pathlib import Path

import requests

from src.utils.logger import logger
from src.utils.paths import paths


class ReferenceManager:
    """
    Downloads and prepares reference datasets.
    """

    def __init__(self):

        self.reference_dir = paths.REFERENCE_DIR

        self.reference_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ------------------------------------------------------------------

    def download_file(
        self,
        url: str,
        destination: Path,
    ):

        if destination.exists():

            logger.info(
                f"{destination.name} already exists."
            )

            return

        logger.info(
            f"Downloading {destination.name}"
        )

        response = requests.get(
            url,
            stream=True,
            timeout=120,
        )

        response.raise_for_status()

        with open(
            destination,
            "wb",
        ) as file:

            for chunk in response.iter_content(8192):

                if chunk:

                    file.write(chunk)

        logger.info(
            f"{destination.name} downloaded."
        )

    # ------------------------------------------------------------------

    def setup(self):

        logger.info(
            "Preparing reference datasets."
        )

        logger.info(
            "Reference setup completed."
        )

    # ------------------------------------------------------------------

    def __repr__(self):

        return "ReferenceManager()"