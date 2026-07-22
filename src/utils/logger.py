"""
===============================================================================
GeoSentinel AI

Module:
    logger.py

Description:
    Central logging utility for the GeoSentinel AI platform.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path

import yaml


class ProjectLogger:
    """
    Singleton logger manager.

    Loads logging configuration from configs/logging.yaml.
    Falls back to a default logger if the configuration file
    is unavailable.
    """

    _configured = False

    @classmethod
    def configure(cls) -> None:
        """
        Configure the logging system.
        """

        if cls._configured:
            return

        project_root = Path(__file__).resolve().parents[2]
        config_path = project_root / "configs" / "logging.yaml"

        if config_path.exists():

            with open(config_path, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)

            # Ensure log directory exists so FileHandler doesn't crash on a fresh clone
            log_dir = project_root / "outputs" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)

            logging.config.dictConfig(config)

        else:

            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            )

        cls._configured = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Return a configured logger.

        Parameters
        ----------
        name : str
            Name of the logger.

        Returns
        -------
        logging.Logger
        """

        cls.configure()

        return logging.getLogger(name)


# ---------------------------------------------------------------------
# Global Project Logger
# ---------------------------------------------------------------------

logger = ProjectLogger.get_logger("GeoSentinel")