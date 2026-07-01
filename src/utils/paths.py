"""
===============================================================================
GeoSentinel AI

Module:
    paths.py

Description:
    Centralized path management for the GeoSentinel AI platform.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from pathlib import Path


class ProjectPaths:
    """
    Centralized project path manager.

    All project directories should be accessed from this class.
    This avoids hardcoding paths throughout the codebase.
    """

    def __init__(self):

        # ------------------------------------------------------------------
        # Project Root
        # ------------------------------------------------------------------

        self.PROJECT_ROOT = Path(__file__).resolve().parents[2]

        # ------------------------------------------------------------------
        # Configuration
        # ------------------------------------------------------------------

        self.CONFIG_DIR = self.PROJECT_ROOT / "configs"

        # ------------------------------------------------------------------
        # Assets
        # ------------------------------------------------------------------

        self.ASSETS_DIR = self.PROJECT_ROOT / "assets"
        self.LOGO_DIR = self.ASSETS_DIR / "logo"
        self.ICONS_DIR = self.ASSETS_DIR / "icons"
        self.SCREENSHOTS_DIR = self.ASSETS_DIR / "screenshots"

        # ------------------------------------------------------------------
        # Data
        # ------------------------------------------------------------------

        self.DATA_DIR = self.PROJECT_ROOT / "data"

        self.RAW_DATA_DIR = self.DATA_DIR / "raw"
        self.SAFE_DATA_DIR = self.RAW_DATA_DIR / "safe"
        self.CACHE_DIR = self.RAW_DATA_DIR / "cache"
        self.DOWNLOAD_DIR = self.RAW_DATA_DIR / "downloads"
        self.ARCHIVE_DIR = self.RAW_DATA_DIR / "archive"

        self.PROCESSED_DATA_DIR = self.DATA_DIR / "processed"
        self.METADATA_DIR = self.DATA_DIR / "metadata"
        self.LABELS_DIR = self.DATA_DIR / "labels"
        self.PATCHES_DIR = self.DATA_DIR / "patches"

        self.BENCHMARK_DIR = self.DATA_DIR / "benchmark"
        self.OSCD_DIR = self.BENCHMARK_DIR / "oscd"
        self.S2LOOKING_DIR = self.BENCHMARK_DIR / "s2looking"

        self.REFERENCE_DIR = self.DATA_DIR / "reference"

        self.HYDERABAD_BOUNDARY = (
            self.REFERENCE_DIR / "hyderabad_boundary.geojson"
        )

        self.HMR_BOUNDARY = (
            self.REFERENCE_DIR / "hmr_boundary.geojson"
        )

        self.DISTRICT_BOUNDARIES = (
            self.REFERENCE_DIR / "district_boundaries.geojson"
        )

        self.WATER_BODIES = (
            self.REFERENCE_DIR / "water_bodies.geojson"
        )

        self.DATA_OUTPUT_DIR = self.DATA_DIR / "outputs"

        # ------------------------------------------------------------------
        # Source
        # ------------------------------------------------------------------

        self.SRC_DIR = self.PROJECT_ROOT / "src"

        # ------------------------------------------------------------------
        # Backend
        # ------------------------------------------------------------------

        self.BACKEND_DIR = self.PROJECT_ROOT / "backend"

        # ------------------------------------------------------------------
        # Frontend
        # ------------------------------------------------------------------

        self.FRONTEND_DIR = self.PROJECT_ROOT / "frontend"

        # ------------------------------------------------------------------
        # Scripts
        # ------------------------------------------------------------------

        self.SCRIPTS_DIR = self.PROJECT_ROOT / "scripts"

        # ------------------------------------------------------------------
        # Tests
        # ------------------------------------------------------------------

        self.TESTS_DIR = self.PROJECT_ROOT / "tests"

        # ------------------------------------------------------------------
        # Documentation
        # ------------------------------------------------------------------

        self.DOCS_DIR = self.PROJECT_ROOT / "docs"

        # ------------------------------------------------------------------
        # Docker
        # ------------------------------------------------------------------

        self.DOCKER_DIR = self.PROJECT_ROOT / "docker"

        # ------------------------------------------------------------------
        # Outputs
        # ------------------------------------------------------------------

        self.OUTPUT_DIR = self.PROJECT_ROOT / "outputs"

        self.CHECKPOINTS_DIR = self.OUTPUT_DIR / "checkpoints"
        self.PREDICTIONS_DIR = self.OUTPUT_DIR / "predictions"
        self.REPORTS_DIR = self.OUTPUT_DIR / "reports"
        self.LOGS_DIR = self.OUTPUT_DIR / "logs"
        self.FIGURES_DIR = self.OUTPUT_DIR / "figures"

    def create_directories(self) -> None:
        """
        Create all required runtime directories if they do not exist.
        """

        directories = [

            self.CACHE_DIR,
            self.DOWNLOAD_DIR,
            self.PROCESSED_DATA_DIR,
            self.METADATA_DIR,
            self.LABELS_DIR,
            self.PATCHES_DIR,

            self.DATA_OUTPUT_DIR,

            self.CHECKPOINTS_DIR,
            self.PREDICTIONS_DIR,
            self.REPORTS_DIR,
            self.LOGS_DIR,
            self.FIGURES_DIR,

        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------
# Global Instance
# --------------------------------------------------------------------------

paths = ProjectPaths()

# Automatically create runtime directories

paths.create_directories()