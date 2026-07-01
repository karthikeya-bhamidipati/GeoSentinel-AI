"""
===============================================================================
GeoSentinel AI

Module:
    directories.py

Description:
    Creates and verifies the GeoSentinel AI directory structure.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from pathlib import Path

from src.utils.logger import logger
from src.utils.paths import paths


class DirectoryManager:
    """
    Creates and verifies all required runtime directories.
    """

    def __init__(self):

        self.directories = [

            # ------------------------------------------------------------------
            # Data
            # ------------------------------------------------------------------

            paths.RAW_DATA_DIR,
            paths.SAFE_DATA_DIR,
            paths.CACHE_DIR,
            paths.DOWNLOAD_DIR,
            paths.ARCHIVE_DIR,

            paths.PROCESSED_DATA_DIR,
            paths.METADATA_DIR,
            paths.LABELS_DIR,
            paths.PATCHES_DIR,

            paths.BENCHMARK_DIR,
            paths.OSCD_DIR,
            paths.S2LOOKING_DIR,

            paths.REFERENCE_DIR,

            paths.DATA_OUTPUT_DIR,

            # ------------------------------------------------------------------
            # Outputs
            # ------------------------------------------------------------------

            paths.OUTPUT_DIR,
            paths.CHECKPOINTS_DIR,
            paths.PREDICTIONS_DIR,
            paths.REPORTS_DIR,
            paths.LOGS_DIR,
            paths.FIGURES_DIR,

        ]

    # ------------------------------------------------------------------

    def create(self):

        """
        Create missing directories.
        """

        logger.info("Creating project directories...")

        created = 0

        for directory in self.directories:

            if not directory.exists():

                directory.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                created += 1

                logger.info(f"Created: {directory}")

        logger.info(
            f"{created} new directories created."
        )

    # ------------------------------------------------------------------

    def verify(self):

        """
        Verify all required directories exist.
        """

        missing = []

        for directory in self.directories:

            if not directory.exists():

                missing.append(directory)

        return missing

    # ------------------------------------------------------------------

    def setup(self):

        self.create()

        missing = self.verify()

        if len(missing) == 0:

            logger.info(
                "Directory verification successful."
            )

        else:

            raise RuntimeError(

                f"Missing directories:\n{missing}"

            )

    # ------------------------------------------------------------------

    def __repr__(self):

        return (

            f"DirectoryManager("

            f"{len(self.directories)} directories)"

        )