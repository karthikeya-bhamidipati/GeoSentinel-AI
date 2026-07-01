"""
===============================================================================
GeoSentinel AI

Module:
    scheduler.py

Description:
    Learning rate scheduler factory for training.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from enum import Enum

import torch.optim as optim
from torch.optim import lr_scheduler


class SchedulerType(str, Enum):
    """Available LR scheduler types."""
    COSINE = "cosine"
    REDUCE_ON_PLATEAU = "reduce_on_plateau"
    STEP = "step"
    ONE_CYCLE = "one_cycle"


class SchedulerFactory:
    """
    Creates PyTorch learning rate schedulers.
    """

    def create(
        self,
        optimizer: optim.Optimizer,
        scheduler_type: str | SchedulerType = SchedulerType.COSINE,
        num_epochs: int = 100,
        steps_per_epoch: int | None = None,
        patience: int = 10,
        factor: float = 0.5,
        min_lr: float = 1e-7,
        step_size: int = 30,
        max_lr: float = 1e-3,
    ):
        """
        Create a learning rate scheduler.

        Parameters
        ----------
        optimizer : Optimizer
        scheduler_type : str | SchedulerType
        num_epochs : int
        steps_per_epoch : int | None
            Required for one_cycle.
        patience : int
            For reduce_on_plateau.
        factor : float
            LR reduction factor for reduce_on_plateau.
        min_lr : float
        step_size : int
            For step scheduler.
        max_lr : float
            For one_cycle scheduler.

        Returns
        -------
        LR scheduler instance.
        """

        scheduler_type = SchedulerType(scheduler_type)

        if scheduler_type == SchedulerType.COSINE:
            return lr_scheduler.CosineAnnealingLR(
                optimizer,
                T_max=num_epochs,
                eta_min=min_lr,
            )

        elif scheduler_type == SchedulerType.REDUCE_ON_PLATEAU:
            return lr_scheduler.ReduceLROnPlateau(
                optimizer,
                mode="max",
                factor=factor,
                patience=patience,
                min_lr=min_lr,
                verbose=True,
            )

        elif scheduler_type == SchedulerType.STEP:
            return lr_scheduler.StepLR(
                optimizer,
                step_size=step_size,
                gamma=factor,
            )

        elif scheduler_type == SchedulerType.ONE_CYCLE:
            if steps_per_epoch is None:
                raise ValueError(
                    "steps_per_epoch is required for one_cycle scheduler."
                )
            return lr_scheduler.OneCycleLR(
                optimizer,
                max_lr=max_lr,
                epochs=num_epochs,
                steps_per_epoch=steps_per_epoch,
            )

        else:
            raise ValueError(f"Unknown scheduler: {scheduler_type!r}")
