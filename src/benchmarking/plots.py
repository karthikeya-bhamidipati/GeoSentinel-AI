"""
===============================================================================
GeoSentinel AI

Module:
    plots.py (benchmarking)

Description:
    Visualization utilities for benchmarking results.

    Generates:
    - Confusion matrix heatmaps
    - Per-class metric bar charts
    - Model comparison bar charts

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

from src.utils.logger import logger


class BenchmarkPlotter:
    """
    Generates benchmark visualization plots.

    All plots are saved to disk as PNG files.
    No interactive display is used.
    """

    def __init__(
        self,
        output_dir: Path | None = None,
        dpi: int = 150,
    ) -> None:

        from src.utils.paths import paths

        self.output_dir = output_dir or paths.FIGURES_DIR
        self.dpi = dpi
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------

    def confusion_matrix(
        self,
        matrix: np.ndarray,
        class_names: list[str],
        filename: str = "confusion_matrix.png",
        title: str = "Confusion Matrix",
    ) -> Path:
        """
        Plot and save a confusion matrix heatmap.

        Parameters
        ----------
        matrix : np.ndarray
            Shape (n_classes, n_classes).
        class_names : list[str]
        filename : str
        title : str

        Returns
        -------
        Path
        """

        fig, ax = plt.subplots(figsize=(8, 6))

        im = ax.imshow(matrix, interpolation="nearest", cmap="Blues")
        plt.colorbar(im, ax=ax)

        ticks = np.arange(len(class_names))
        ax.set_xticks(ticks)
        ax.set_yticks(ticks)
        ax.set_xticklabels(class_names, rotation=45, ha="right")
        ax.set_yticklabels(class_names)

        thresh = matrix.max() / 2.0

        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(
                    j, i, str(matrix[i, j]),
                    ha="center", va="center",
                    color="white" if matrix[i, j] > thresh else "black",
                    fontsize=9,
                )

        ax.set_title(title)
        ax.set_ylabel("True Label")
        ax.set_xlabel("Predicted Label")

        plt.tight_layout()

        output_path = self.output_dir / filename
        fig.savefig(output_path, dpi=self.dpi, bbox_inches="tight")
        plt.close(fig)

        logger.info(f"Confusion matrix saved: {output_path.name}")

        return output_path

    # ------------------------------------------------------------------

    def metric_bar_chart(
        self,
        metrics_dict: dict[str, float],
        filename: str = "metrics_bar.png",
        title: str = "Segmentation Metrics",
    ) -> Path:
        """
        Plot a bar chart of metrics.

        Parameters
        ----------
        metrics_dict : dict[str, float]
            Metric name → value.
        filename : str
        title : str

        Returns
        -------
        Path
        """

        names = list(metrics_dict.keys())
        values = list(metrics_dict.values())

        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(names)))

        fig, ax = plt.subplots(figsize=(8, 5))

        bars = ax.bar(names, values, color=colors, edgecolor="white")

        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.01,
                f"{val:.3f}",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        ax.set_ylim(0, 1.1)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_ylabel("Score")
        ax.set_xlabel("Metric")
        ax.grid(axis="y", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        plt.tight_layout()

        output_path = self.output_dir / filename
        fig.savefig(output_path, dpi=self.dpi, bbox_inches="tight")
        plt.close(fig)

        logger.info(f"Metric chart saved: {output_path.name}")

        return output_path

    # ------------------------------------------------------------------

    def model_comparison_chart(
        self,
        comparison_data: list[dict],
        metrics: list[str] | None = None,
        filename: str = "model_comparison.png",
        title: str = "Model Comparison",
    ) -> Path:
        """
        Plot a grouped bar chart comparing multiple models.

        Parameters
        ----------
        comparison_data : list[dict]
            Each dict must have 'model' key and metric values.
        metrics : list[str] | None
            Metrics to plot. Defaults to ['iou', 'dice', 'f1', 'accuracy'].
        filename : str
        title : str

        Returns
        -------
        Path
        """

        if metrics is None:
            metrics = ["iou", "dice", "f1", "accuracy"]

        n_models = len(comparison_data)
        n_metrics = len(metrics)

        x = np.arange(n_metrics)
        width = 0.8 / n_models

        colors = plt.cm.Set2(np.linspace(0, 1, n_models))

        fig, ax = plt.subplots(figsize=(10, 6))

        for i, data in enumerate(comparison_data):
            values = [data.get(m, 0.0) for m in metrics]
            offset = (i - n_models / 2 + 0.5) * width

            bars = ax.bar(
                x + offset,
                values,
                width,
                label=data.get("model", f"Model {i+1}"),
                color=colors[i],
                edgecolor="white",
            )

        ax.set_xticks(x)
        ax.set_xticklabels([m.upper() for m in metrics])
        ax.set_ylim(0, 1.15)
        ax.set_ylabel("Score")
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.legend(loc="upper right")
        ax.grid(axis="y", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        plt.tight_layout()

        output_path = self.output_dir / filename
        fig.savefig(output_path, dpi=self.dpi, bbox_inches="tight")
        plt.close(fig)

        logger.info(f"Model comparison chart saved: {output_path.name}")

        return output_path
