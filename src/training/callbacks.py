"""
===============================================================================
GeoSentinel AI

Module:
    callbacks.py

Description:
    Training callbacks: model checkpointing and early stopping.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from pathlib import Path

import torch
import torch.nn as nn

from src.utils.logger import logger
from src.utils.paths import paths


class ModelCheckpoint:
    """
    Saves the best model checkpoint during training.

    Monitors a given metric and saves the model weights
    whenever the metric improves.

    Parameters
    ----------
    monitor : str
        Metric name to monitor (e.g., 'dice', 'iou').
    mode : str
        'max' for metrics where higher is better (IoU, Dice).
        'min' for metrics where lower is better (loss).
    save_dir : Path | None
        Directory to save checkpoints.
    filename : str
        Checkpoint filename.
    """

    def __init__(
        self,
        monitor: str = "dice",
        mode: str = "max",
        save_dir: Path | None = None,
        filename: str = "best_model.pt",
    ) -> None:

        self.monitor = monitor
        self.mode = mode
        self.save_dir = save_dir or paths.CHECKPOINTS_DIR
        self.filename = filename
        self.best_value = float("-inf") if mode == "max" else float("inf")

        self.save_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------

    def __call__(
        self,
        model: nn.Module,
        current_value: float,
        epoch: int,
    ) -> bool:
        """
        Check metric and save checkpoint if improved.

        Parameters
        ----------
        model : nn.Module
        current_value : float
            Current value of the monitored metric.
        epoch : int

        Returns
        -------
        bool
            True if the model was saved.
        """

        improved = (
            (self.mode == "max" and current_value > self.best_value)
            or (self.mode == "min" and current_value < self.best_value)
        )

        if improved:
            self.best_value = current_value
            save_path = self.save_dir / self.filename

            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    f"best_{self.monitor}": self.best_value,
                },
                save_path,
            )

            logger.info(
                f"Checkpoint saved: epoch={epoch}, "
                f"{self.monitor}={current_value:.4f}"
            )

            return True

        return False


class EarlyStopping:
    """
    Stops training when a metric stops improving.

    Parameters
    ----------
    monitor : str
        Metric name to monitor.
    patience : int
        Number of epochs to wait without improvement.
    mode : str
        'max' or 'min'.
    min_delta : float
        Minimum change to qualify as improvement.
    """

    def __init__(
        self,
        monitor: str = "dice",
        patience: int = 15,
        mode: str = "max",
        min_delta: float = 1e-4,
    ) -> None:

        self.monitor = monitor
        self.patience = patience
        self.mode = mode
        self.min_delta = min_delta

        self.best_value = float("-inf") if mode == "max" else float("inf")
        self.counter = 0
        self.should_stop = False

    # ------------------------------------------------------------------

    def __call__(self, current_value: float) -> bool:
        """
        Update state and check for early stopping.

        Parameters
        ----------
        current_value : float

        Returns
        -------
        bool
            True if training should stop.
        """

        if self.mode == "max":
            improved = current_value > self.best_value + self.min_delta
        else:
            improved = current_value < self.best_value - self.min_delta

        if improved:
            self.best_value = current_value
            self.counter = 0
        else:
            self.counter += 1

        if self.counter >= self.patience:
            self.should_stop = True
            logger.info(
                f"Early stopping triggered after {self.counter} epochs "
                f"without improvement. Best {self.monitor}: "
                f"{self.best_value:.4f}"
            )

        return self.should_stop
