"""
===============================================================================
GeoSentinel AI

Module:
    metrics.py (benchmarking)

Description:
    Benchmarking metric computation for model evaluation on
    OSCD and S2Looking datasets.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch

from src.training.metrics import SegmentationMetricCalculator, SegmentationMetrics
from src.models.unet import NUM_CLASSES
from src.utils.logger import logger


@dataclass
class BenchmarkResult:
    """
    Benchmark evaluation result for a single model on a dataset.

    Attributes
    ----------
    model_name : str
    dataset_name : str
    metrics : SegmentationMetrics
    num_samples : int
    """

    model_name: str
    dataset_name: str
    metrics: SegmentationMetrics
    num_samples: int

    def to_dict(self) -> dict:

        return {
            "model": self.model_name,
            "dataset": self.dataset_name,
            "num_samples": self.num_samples,
            **self.metrics.to_dict(),
        }


class BenchmarkEvaluator:
    """
    Evaluates a model on a benchmark dataset and computes all metrics.

    Parameters
    ----------
    num_classes : int
    device : str
        'cuda' or 'cpu'.
    """

    def __init__(
        self,
        num_classes: int = NUM_CLASSES,
        device: str = "cpu",
    ) -> None:

        self.num_classes = num_classes
        self.device = torch.device(device)
        self._metric_calc = SegmentationMetricCalculator(num_classes)

    # ------------------------------------------------------------------

    def evaluate(
        self,
        model: torch.nn.Module,
        dataloader: "DataLoader",
        model_name: str = "model",
        dataset_name: str = "dataset",
    ) -> BenchmarkResult:
        """
        Evaluate a model on a dataloader and return metrics.

        Parameters
        ----------
        model : nn.Module
        dataloader : DataLoader
        model_name : str
        dataset_name : str

        Returns
        -------
        BenchmarkResult
        """

        model.eval()
        model = model.to(self.device)

        all_preds = []
        all_targets = []
        n_samples = 0

        with torch.no_grad():
            for images, masks in dataloader:

                images = images.to(self.device)
                logits = model(images)
                preds = torch.argmax(logits, dim=1)

                all_preds.append(preds.cpu().numpy())
                all_targets.append(masks.numpy())
                n_samples += images.shape[0]

        preds_array = np.concatenate(all_preds, axis=0)
        targets_array = np.concatenate(all_targets, axis=0)

        metrics = self._metric_calc.compute(preds_array, targets_array)

        logger.info(
            f"Benchmark [{dataset_name}] {model_name}: "
            f"IoU={metrics.iou:.4f}, Dice={metrics.dice:.4f}"
        )

        return BenchmarkResult(
            model_name=model_name,
            dataset_name=dataset_name,
            metrics=metrics,
            num_samples=n_samples,
        )
