"""
===============================================================================
GeoSentinel AI

Module:
    optimizer.py

Description:
    Optimizer factory for training segmentation models.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from enum import Enum

import torch.nn as nn
import torch.optim as optim


class OptimizerType(str, Enum):
    """Available optimizer types."""
    ADAM = "adam"
    ADAMW = "adamw"
    SGD = "sgd"


class OptimizerFactory:
    """
    Creates PyTorch optimizers by type and configuration.
    """

    def create(
        self,
        model: nn.Module,
        optimizer_type: str | OptimizerType = OptimizerType.ADAM,
        learning_rate: float = 1e-4,
        weight_decay: float = 1e-4,
        momentum: float = 0.9,
    ) -> optim.Optimizer:
        """
        Create an optimizer for the given model.

        Parameters
        ----------
        model : nn.Module
        optimizer_type : str | OptimizerType
        learning_rate : float
        weight_decay : float
        momentum : float
            Only used for SGD.

        Returns
        -------
        optim.Optimizer
        """

        optimizer_type = OptimizerType(optimizer_type)

        params = filter(lambda p: p.requires_grad, model.parameters())

        if optimizer_type == OptimizerType.ADAM:
            return optim.Adam(
                params,
                lr=learning_rate,
                weight_decay=weight_decay,
            )

        elif optimizer_type == OptimizerType.ADAMW:
            return optim.AdamW(
                params,
                lr=learning_rate,
                weight_decay=weight_decay,
            )

        elif optimizer_type == OptimizerType.SGD:
            return optim.SGD(
                params,
                lr=learning_rate,
                momentum=momentum,
                weight_decay=weight_decay,
                nesterov=True,
            )

        else:
            raise ValueError(f"Unknown optimizer: {optimizer_type!r}")
