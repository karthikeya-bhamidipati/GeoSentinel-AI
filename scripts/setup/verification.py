"""
===============================================================================
GeoSentinel AI

Module:
    verification.py

Description:
    Project verification utilities.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from pathlib import Path

from src.utils.logger import logger
from src.utils.paths import paths


class VerificationManager:
    """
    Verifies that the GeoSentinel AI project
    is correctly initialized.
    """

    REQUIRED_CONFIGS = [

        "config.yaml",
        "model.yaml",
        "api.yaml",
        "logging.yaml",
        "recommendation_rules.yaml",

    ]

    REQUIRED_REFERENCE_FILES = [

        "hmr_boundary.geojson",
        "district_boundaries.geojson",

    ]

    # ------------------------------------------------------------------

    def verify_configs(self):

        """
        Verify configuration files.
        """

        logger.info(
            "Verifying configuration files..."
        )

        missing = []

        for file in self.REQUIRED_CONFIGS:

            path = paths.CONFIG_DIR / file

            if not path.exists():

                missing.append(path)

        return missing

    # ------------------------------------------------------------------

    def verify_reference_data(self):

        """
        Verify downloaded reference datasets.
        """

        logger.info(
            "Verifying reference datasets..."
        )

        missing = []

        for file in self.REQUIRED_REFERENCE_FILES:

            path = paths.REFERENCE_DIR / file

            if not path.exists():

                missing.append(path)

        return missing

    # ------------------------------------------------------------------

    def verify_outputs(self):

        """
        Verify output folders.
        """

        logger.info(
            "Verifying output directories..."
        )

        required = [

            paths.CHECKPOINTS_DIR,

            paths.PREDICTIONS_DIR,

            paths.REPORTS_DIR,

            paths.LOGS_DIR,

            paths.FIGURES_DIR,

        ]

        missing = [

            directory

            for directory in required

            if not directory.exists()

        ]

        return missing

    # ------------------------------------------------------------------

    def verify_data(self):

        """
        Verify data directories.
        """

        logger.info(
            "Verifying data directories..."
        )

        required = [

            paths.RAW_DATA_DIR,

            paths.PROCESSED_DATA_DIR,

            paths.REFERENCE_DIR,

            paths.BENCHMARK_DIR,

        ]

        missing = [

            directory

            for directory in required

            if not directory.exists()

        ]

        return missing

    # ------------------------------------------------------------------

    def verify(self):

        """
        Execute all verification checks.
        """

        report = {

            "configs": self.verify_configs(),

            "reference": self.verify_reference_data(),

            "outputs": self.verify_outputs(),

            "data": self.verify_data(),

        }

        return report

    # ------------------------------------------------------------------

    def print_report(self):

        """
        Print verification report.
        """

        report = self.verify()

        print("\n")

        print("=" * 70)

        print("GeoSentinel AI Verification")

        print("=" * 70)

        for section, items in report.items():

            if len(items) == 0:

                print(f"✓ {section.capitalize():15} OK")

            else:

                print(f"✗ {section.capitalize():15} Missing")

                for item in items:

                    print(f"    - {item}")

        print()

    # ------------------------------------------------------------------

    def passed(self):

        """
        Returns True if all checks pass.
        """

        report = self.verify()

        return all(

            len(items) == 0

            for items in report.values()

        )

    # ------------------------------------------------------------------

    def __repr__(self):

        return "VerificationManager()"