"""
===============================================================================
GeoSentinel AI

Module:
    losses.py

Description:
    Loss functions for semantic segmentation training.

    Implements:
    - Dice Loss — handles class imbalance, pixel-overlap based
    - BCE + Dice Loss — combined loss for stable training
    - Focal Loss — downweights easy examples, focuses on hard pixels

    All losses accept raw logits and handle multi-class segmentation.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


# =============================================================================
# Dice Loss
# =============================================================================


class DiceLoss(nn.Module):
    """
    Soft Dice Loss for multi-class segmentation.

    Computes the Dice coefficient per class and averages across all classes.
    Handles class imbalance better than cross-entropy by focusing on
    the overlap between prediction and ground truth.

    Parameters
    ----------
    smooth : float
        Laplace smoothing to prevent division by zero.
    ignore_index : int | None
        Class index to ignore (e.g., background).
    """

    def __init__(
        self,
        smooth: float = 1.0,
        ignore_index: int | None = None,
    ) -> None:

        super().__init__()

        self.smooth = smooth
        self.ignore_index = ignore_index

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        """
        Compute Dice loss.

        Parameters
        ----------
        logits : torch.Tensor
            Shape (batch, num_classes, H, W), raw logits.
        targets : torch.Tensor
            Shape (batch, H, W), integer class indices.

        Returns
        -------
        torch.Tensor
            Scalar Dice loss.
        """

        num_classes = logits.shape[1]

        probabilities = F.softmax(logits, dim=1)

        targets_one_hot = F.one_hot(
            targets.long(), num_classes=num_classes
        ).permute(0, 3, 1, 2).float()

        # Mask ignore_index
        if self.ignore_index is not None:
            mask = (targets != self.ignore_index).unsqueeze(1).float()
            probabilities = probabilities * mask
            targets_one_hot = targets_one_hot * mask

        dims = (0, 2, 3)

        intersection = (probabilities * targets_one_hot).sum(dim=dims)
        cardinality = (probabilities + targets_one_hot).sum(dim=dims)

        dice_score = (2.0 * intersection + self.smooth) / (
            cardinality + self.smooth
        )

        return 1.0 - dice_score.mean()


# =============================================================================
# BCE + Dice Loss (Combined)
# =============================================================================


class BCEDiceLoss(nn.Module):
    """
    Combined Binary Cross-Entropy and Dice Loss.

    loss = alpha * BCE + (1 - alpha) * Dice

    BCE provides stable gradient signals during early training.
    Dice handles class imbalance and optimizes overlap metrics.

    Parameters
    ----------
    alpha : float
        Weight for BCE component (default: 0.5).
    smooth : float
        Dice smoothing factor.
    ignore_index : int | None
        Class index to ignore.
    """

    def __init__(
        self,
        alpha: float = 0.5,
        smooth: float = 1.0,
        ignore_index: int | None = None,
    ) -> None:

        super().__init__()

        self.alpha = alpha
        self.dice_loss = DiceLoss(
            smooth=smooth,
            ignore_index=ignore_index,
        )
        self.ce_loss = nn.CrossEntropyLoss(
            ignore_index=ignore_index if ignore_index is not None else -100
        )

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        """
        Compute BCE + Dice loss.

        Parameters
        ----------
        logits : torch.Tensor
            Shape (batch, num_classes, H, W).
        targets : torch.Tensor
            Shape (batch, H, W).

        Returns
        -------
        torch.Tensor
            Scalar combined loss.
        """

        bce = self.ce_loss(logits, targets.long())
        dice = self.dice_loss(logits, targets)

        return self.alpha * bce + (1.0 - self.alpha) * dice


# =============================================================================
# Focal Loss
# =============================================================================


class FocalLoss(nn.Module):
    """
    Focal Loss for addressing class imbalance.

    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)

    Focuses training on hard, misclassified examples by down-weighting
    the loss contribution of well-classified pixels.

    Reference:
    Lin et al. (2017). Focal Loss for Dense Object Detection. ICCV 2017.

    Parameters
    ----------
    gamma : float
        Focusing parameter (default: 2.0).
    alpha : float | None
        Class balancing weight.
    ignore_index : int | None
        Class index to ignore.
    """

    def __init__(
        self,
        gamma: float = 2.0,
        alpha: float | None = None,
        ignore_index: int | None = None,
    ) -> None:

        super().__init__()

        self.gamma = gamma
        self.alpha = alpha
        self.ignore_index = ignore_index

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        """
        Compute Focal loss.

        Parameters
        ----------
        logits : torch.Tensor
            Shape (batch, num_classes, H, W).
        targets : torch.Tensor
            Shape (batch, H, W).

        Returns
        -------
        torch.Tensor
            Scalar focal loss.
        """

        ce_loss = F.cross_entropy(
            logits,
            targets.long(),
            reduction="none",
            ignore_index=(
                self.ignore_index
                if self.ignore_index is not None
                else -100
            ),
        )

        pt = torch.exp(-ce_loss)
        focal = (1 - pt) ** self.gamma * ce_loss

        if self.alpha is not None:
            focal = self.alpha * focal

        return focal.mean()
