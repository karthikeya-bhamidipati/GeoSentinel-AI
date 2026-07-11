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
from src.utils.config import ProjectConfig
from src.utils.logger import logger


@lru_cache(maxsize=1)
def get_orchestrator() -> Orchestrator:
    """
    Dependency: returns the shared Orchestrator singleton.

    Cached with lru_cache so it is created only once per process.
    """

    config = ProjectConfig()

    checkpoint_path = None

    try:
        checkpoint_str = config.get("model", "inference", "checkpoint_path")

        if checkpoint_str:
            checkpoint_path = Path(checkpoint_str)

    except Exception:
        pass

    # ── Auto-detect trained weights from the training pipeline ────────
    if checkpoint_path is None or not checkpoint_path.exists():
        trained_weights = (
            Path(__file__).resolve().parent.parent.parent
            / "data" / "weights" / "unet_best.pt"
        )
        if trained_weights.exists():
            checkpoint_path = trained_weights
            logger.info(
                f"Auto-detected trained checkpoint: {trained_weights}"
            )

    logger.info("Creating Orchestrator singleton ...")

    inference_device = config.get("model", "inference", "device", default="cpu")
    cloud_cover_threshold = config.get(
        "sentinel",
        "cloud_cover_threshold",
        default=10.0,
    )

    return Orchestrator(
        model_checkpoint=checkpoint_path,
        device=inference_device,
        max_cloud_cover=float(cloud_cover_threshold),
    )


def get_project_config() -> ProjectConfig:
    """Dependency: returns the ProjectConfig."""
    return ProjectConfig()
