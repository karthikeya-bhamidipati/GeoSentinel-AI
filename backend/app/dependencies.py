"""
===============================================================================
GeoSentinel AI

Module:
    dependencies.py

Description:
    FastAPI dependency injection providers.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from src.orchestration.orchestrator import Orchestrator
from src.utils.logger import logger
from src.utils.config import ProjectConfig


@lru_cache(maxsize=1)
def get_orchestrator() -> Orchestrator:
    """
    Dependency: returns the shared Orchestrator singleton.

    Cached with lru_cache so it is created only once per process.
    """

    config = ProjectConfig()

    checkpoint_path = None

    try:
        model_cfg = config.model_config
        checkpoint_str = model_cfg.get(
            "inference", {}
        ).get("checkpoint_path", None)

        if checkpoint_str:
            checkpoint_path = Path(checkpoint_str)

    except Exception:
        pass

    logger.info("Creating Orchestrator singleton ...")

    return Orchestrator(
        model_checkpoint=checkpoint_path,
        device="cpu",
        max_cloud_cover=10.0,
    )


def get_project_config() -> ProjectConfig:
    """Dependency: returns the ProjectConfig."""
    return ProjectConfig()
