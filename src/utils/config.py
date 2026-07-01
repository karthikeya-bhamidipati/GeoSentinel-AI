"""
===============================================================================
GeoSentinel AI

Module:
    config.py

Description:
    Configuration manager for the GeoSentinel AI platform.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ProjectConfig:
    """
    Singleton configuration manager.

    Loads the project's YAML configuration file once and provides
    easy attribute-based access throughout the application.
    """

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProjectConfig, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Load configuration from YAML."""

        project_root = Path(__file__).resolve().parents[2]
        config_path = project_root / "configs" / "config.yaml"

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found:\n{config_path}"
            )

        with open(config_path, "r", encoding="utf-8") as file:
            self._config = yaml.safe_load(file)

    def reload(self) -> None:
        """Reload configuration from disk."""
        self._load_config()

    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Retrieve nested configuration values.

        Example:
            config.get("training", "epochs")
        """

        value = self._config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    @property
    def project(self):
        return self._config.get("project", {})

    @property
    def study_area(self):
        return self._config.get("study_area", {})

    @property
    def coordinate_system(self):
        return self._config.get("coordinate_system", {})

    @property
    def data(self):
        return self._config.get("data", {})

    @property
    def sentinel(self):
        return self._config.get("sentinel", {})

    @property
    def bands(self):
        return self._config.get("bands", {})

    @property
    def indices(self):
        return self._config.get("indices", {})

    @property
    def preprocessing(self):
        return self._config.get("preprocessing", {})

    @property
    def dataset(self):
        return self._config.get("dataset", {})

    @property
    def training(self):
        return self._config.get("training", {})

    @property
    def benchmark(self):
        return self._config.get("benchmark", {})

    @property
    def output(self):
        return self._config.get("output", {})

    @property
    def logging(self):
        return self._config.get("logging", {})

    @property
    def docker(self):
        return self._config.get("docker", {})


config = ProjectConfig()