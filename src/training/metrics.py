"""
===============================================================================
GeoSentinel AI

Module:
    metrics.py (training)

Description:
    Segmentation evaluation metrics.

    Implements all metrics required by the Master Spec:
    - IoU (Intersection over Union / Jaccard Index)
    - Dice Coefficient (F1 score for binary segmentation)
    - Precision
    - Recall
    - F1 Score
    - Accuracy

    All metrics are computed per-class and averaged (macro average).
    Compatible with both training loops and standalone evaluation.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch
import torch.nn.functional as F


# =============================================================================
# Metric Result
# =============================================================================


@dataclass
class SegmentationMetrics:
    """
    Container for segmentation evaluation metrics.

    Attributes
    ----------
    iou : float
        Mean Intersection over Union (mIoU).
    dice : float
        Mean Dice coefficient.
    precision : float
        Macro-averaged precision.
    recall : float
        Macro-averaged recall.
    f1 : float
        Macro-averaged F1 score.
    accuracy : float
        Pixel accuracy.
    per_class_iou : dict[int, float]
        IoU per class.
    per_class_dice : dict[int, float]
        Dice per class.
    """

    iou: float = 0.0
    dice: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    accuracy: float = 0.0
    per_class_iou: dict[int, float] = field(default_factory=dict)
    per_class_dice: dict[int, float] = field(default_factory=dict)

    def to_dict(self) -> dict:

        return {
            "iou": round(self.iou, 4),
            "dice": round(self.dice, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "accuracy": round(self.accuracy, 4),
            "per_class_iou": {
                str(k): round(v, 4)
                for k, v in self.per_class_iou.items()
            },
            "per_class_dice": {
                str(k): round(v, 4)
                for k, v in self.per_class_dice.items()
            },
        }


# =============================================================================
# Metric Computations
# =============================================================================


class SegmentationMetricCalculator:
    """
    Computes segmentation metrics from predictions and ground truth.

    Supports both numpy arrays and PyTorch tensors.
    All metrics are computed on a confusion matrix basis.
    """

    def __init__(
        self,
        num_classes: int,
        ignore_index: int | None = None,
        smooth: float = 1e-6,
    ) -> None:

        self.num_classes = num_classes
        self.ignore_index = ignore_index
        self.smooth = smooth

    # ------------------------------------------------------------------

    def confusion_matrix(
        self,
        predictions: np.ndarray,
        targets: np.ndarray,
    ) -> np.ndarray:
        """
        Compute a confusion matrix.

        Parameters
        ----------
        predictions : np.ndarray
            Predicted class indices, shape (N,).
        targets : np.ndarray
            Ground truth class indices, shape (N,).

        Returns
        -------
        np.ndarray
            Confusion matrix of shape (num_classes, num_classes).
        """

        predictions = predictions.flatten().astype(int)
        targets = targets.flatten().astype(int)

        if self.ignore_index is not None:
            mask = targets != self.ignore_index
            predictions = predictions[mask]
            targets = targets[mask]

        matrix = np.zeros(
            (self.num_classes, self.num_classes),
            dtype=np.int64,
        )

        for t, p in zip(targets, predictions):
            if 0 <= t < self.num_classes and 0 <= p < self.num_classes:
                matrix[t, p] += 1

        return matrix

    # ------------------------------------------------------------------

    def compute(
        self,
        predictions: np.ndarray | torch.Tensor,
        targets: np.ndarray | torch.Tensor,
    ) -> SegmentationMetrics:
        """
        Compute all metrics from predictions and targets.

        Parameters
        ----------
        predictions : np.ndarray | torch.Tensor
            Shape (H, W) or (B, H, W), predicted class indices.
        targets : np.ndarray | torch.Tensor
            Shape (H, W) or (B, H, W), ground truth class indices.

        Returns
        -------
        SegmentationMetrics
        """

        if isinstance(predictions, torch.Tensor):
            predictions = predictions.cpu().numpy()
        if isinstance(targets, torch.Tensor):
            targets = targets.cpu().numpy()

        cm = self.confusion_matrix(predictions, targets)

        return self._metrics_from_cm(cm)

    # ------------------------------------------------------------------

    def _metrics_from_cm(
        self,
        cm: np.ndarray,
    ) -> SegmentationMetrics:
        """
        Derive all metrics from a confusion matrix.
        """

        tp = np.diag(cm)
        fp = cm.sum(axis=0) - tp
        fn = cm.sum(axis=1) - tp
        total = cm.sum()

        # IoU per class
        iou_per_class = tp / (tp + fp + fn + self.smooth)

        # Dice per class
        dice_per_class = (2 * tp) / (2 * tp + fp + fn + self.smooth)

        # Precision per class
        precision_per_class = tp / (tp + fp + self.smooth)

        # Recall per class
        recall_per_class = tp / (tp + fn + self.smooth)

        # F1 per class
        f1_per_class = (
            2 * precision_per_class * recall_per_class
            / (precision_per_class + recall_per_class + self.smooth)
        )

        # Accuracy
        accuracy = tp.sum() / (total + self.smooth)

        return SegmentationMetrics(
            iou=float(iou_per_class.mean()),
            dice=float(dice_per_class.mean()),
            precision=float(precision_per_class.mean()),
            recall=float(recall_per_class.mean()),
            f1=float(f1_per_class.mean()),
            accuracy=float(accuracy),
            per_class_iou={
                i: float(v) for i, v in enumerate(iou_per_class)
            },
            per_class_dice={
                i: float(v) for i, v in enumerate(dice_per_class)
            },
        )

    # ------------------------------------------------------------------

    def from_logits(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
    ) -> SegmentationMetrics:
        """
        Compute metrics from raw model logits.

        Parameters
        ----------
        logits : torch.Tensor
            Shape (B, num_classes, H, W).
        targets : torch.Tensor
            Shape (B, H, W).

        Returns
        -------
        SegmentationMetrics
        """

        predictions = torch.argmax(logits, dim=1)

        return self.compute(predictions, targets)
