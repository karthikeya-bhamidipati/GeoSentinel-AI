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
    change_checkpoint_path = None

    try:
        checkpoint_str = config.get("model", "inference", "checkpoint_path")
        if checkpoint_str:
            checkpoint_path = Path(checkpoint_str)
            
        change_ckpt_str = config.get("model", "inference", "change_checkpoint_path")
        if change_ckpt_str:
            change_checkpoint_path = Path(change_ckpt_str)
    except Exception:
        pass

    # ── Auto-detect trained weights from the training pipeline ────────
    weights_dir = Path(__file__).resolve().parent.parent.parent / "data" / "weights"
    
    if checkpoint_path is None or not checkpoint_path.exists():
        trained_weights = weights_dir / "deeplabv3plus_best.pt"
        if trained_weights.exists():
            checkpoint_path = trained_weights
            logger.info(f"Auto-detected land cover checkpoint: {trained_weights}")
            
    if change_checkpoint_path is None or not change_checkpoint_path.exists():
        change_weights = weights_dir / "change_unet_best.pt"
        if change_weights.exists():
            change_checkpoint_path = change_weights
            logger.info(f"Auto-detected change detection checkpoint: {change_weights}")

    logger.info("Creating Orchestrator singleton ...")

    inference_device = config.get("model", "inference", "device", default="cpu")
    cloud_cover_threshold = config.get(
        "sentinel",
        "cloud_cover_threshold",
        default=10.0,
    )

    return Orchestrator(
        model_checkpoint=checkpoint_path,
        change_model_checkpoint=change_checkpoint_path,
        device=inference_device,
        max_cloud_cover=float(cloud_cover_threshold),
    )


def get_project_config() -> ProjectConfig:
    """Dependency: returns the ProjectConfig."""
    return ProjectConfig()
