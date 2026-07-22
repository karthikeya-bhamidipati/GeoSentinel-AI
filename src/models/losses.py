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


# =============================================================================
# Focal Tversky Loss
# =============================================================================


class FocalTverskyLoss(nn.Module):
    """
    Focal Tversky Loss for extreme class imbalance.
    Combines Tversky Index with Focal Loss.
    """
    def __init__(self, alpha=0.3, beta=0.7, gamma=4.0 / 3.0, smooth=1e-6, ignore_index=None, class_weights=None):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.smooth = smooth
        self.ignore_index = ignore_index
        self.class_weights = class_weights

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        num_classes = logits.shape[1]
        probs = F.softmax(logits, dim=1)
        
        targets_one_hot = F.one_hot(targets.long(), num_classes=num_classes).permute(0, 3, 1, 2).float()
        
        if self.ignore_index is not None:
            mask = (targets != self.ignore_index).unsqueeze(1).float()
            probs = probs * mask
            targets_one_hot = targets_one_hot * mask
            
        dims = (0, 2, 3)
        
        # True Positives, False Positives, False Negatives
        TP = (probs * targets_one_hot).sum(dim=dims)
        FP = (probs * (1 - targets_one_hot)).sum(dim=dims)
        FN = ((1 - probs) * targets_one_hot).sum(dim=dims)
        
        Tversky = (TP + self.smooth) / (TP + self.alpha * FP + self.beta * FN + self.smooth)
        FocalTversky = (1 - Tversky) ** self.gamma
        
        if self.class_weights is not None:
            weights = torch.tensor(self.class_weights, device=logits.device, dtype=torch.float32)
            # Ensure weights matches num_classes
            if len(weights) != num_classes:
                raise ValueError(f"class_weights length ({len(weights)}) must match num_classes ({num_classes})")
            return (FocalTversky * weights).sum() / weights.sum()
        
        return FocalTversky.mean()


# =============================================================================
# Boundary Loss (Edge-Aware)
# =============================================================================

class BoundaryLoss(nn.Module):
    """
    Edge-aware Boundary Loss using spatial gradients (Sobel filters).
    Forces the network to produce crisp, sharp cuts that match ground-truth edges.
    """
    def __init__(self, ignore_index=None):
        super().__init__()
        self.ignore_index = ignore_index
        self.register_buffer('sobel_x', torch.tensor([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=torch.float32).view(1, 1, 3, 3))
        self.register_buffer('sobel_y', torch.tensor([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=torch.float32).view(1, 1, 3, 3))

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        probs = F.softmax(logits, dim=1)
        num_classes = probs.shape[1]
        
        targets_one_hot = F.one_hot(targets.long(), num_classes=num_classes).permute(0, 3, 1, 2).float()
        
        if self.ignore_index is not None:
            mask = (targets != self.ignore_index).unsqueeze(1).float()
            probs = probs * mask
            targets_one_hot = targets_one_hot * mask

        b, c, h, w = probs.shape
        probs_flat = probs.view(b * c, 1, h, w)
        targets_flat = targets_one_hot.reshape(b * c, 1, h, w)
        
        grad_x_pred = F.conv2d(probs_flat, self.sobel_x, padding=1)
        grad_y_pred = F.conv2d(probs_flat, self.sobel_y, padding=1)
        edges_pred = torch.sqrt(grad_x_pred**2 + grad_y_pred**2 + 1e-6)
        
        grad_x_target = F.conv2d(targets_flat, self.sobel_x, padding=1)
        grad_y_target = F.conv2d(targets_flat, self.sobel_y, padding=1)
        edges_target = torch.sqrt(grad_x_target**2 + grad_y_target**2 + 1e-6)
        
        return F.l1_loss(edges_pred, edges_target, reduction='mean')


class CombinedFocalBoundaryLoss(nn.Module):
    """
    Combines Focal Tversky Loss (for class imbalance and blobs) 
    with Boundary Loss (for crisp edges and cuts).
    """
    def __init__(self, alpha=0.3, beta=0.7, gamma=4.0/3.0, boundary_weight=0.5, ignore_index=None, class_weights=None):
        super().__init__()
        self.focal_tversky = FocalTverskyLoss(alpha, beta, gamma, ignore_index=ignore_index, class_weights=class_weights)
        self.boundary = BoundaryLoss(ignore_index=ignore_index)
        self.boundary_weight = boundary_weight
        
    def forward(self, logits, targets):
        ft_loss = self.focal_tversky(logits, targets)
        b_loss = self.boundary(logits, targets)
        return ft_loss + self.boundary_weight * b_loss
