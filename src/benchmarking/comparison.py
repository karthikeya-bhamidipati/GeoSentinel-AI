"""
===============================================================================
GeoSentinel AI

Module:
    comparison.py

Description:
    Model comparison table — UNet vs DeepLabV3+.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.benchmarking.metrics import BenchmarkResult
from src.utils.logger import logger


@dataclass
class ComparisonTable:
    """
    Side-by-side comparison of multiple benchmark results.
    """

    results: list[BenchmarkResult] = field(default_factory=list)

    def add(self, result: BenchmarkResult) -> None:
        self.results.append(result)

    def to_rows(self) -> list[dict[str, Any]]:
        """Return results as a list of row dicts for CSV export."""
        return [r.to_dict() for r in self.results]

    def best_by(self, metric: str = "iou") -> BenchmarkResult | None:
        """Return the result with the best value for a given metric."""

        if not self.results:
            return None

        return max(
            self.results,
            key=lambda r: getattr(r.metrics, metric, 0.0),
        )

    def summary(self) -> str:
        """Human-readable comparison summary."""

        lines = [
            "=" * 60,
            "Model Comparison Summary",
            "=" * 60,
        ]

        for r in self.results:
            lines.append(
                f"{r.model_name} [{r.dataset_name}]: "
                f"IoU={r.metrics.iou:.4f}, "
                f"Dice={r.metrics.dice:.4f}, "
                f"F1={r.metrics.f1:.4f}, "
                f"Acc={r.metrics.accuracy:.4f}"
            )

        best = self.best_by("iou")
        if best:
            lines.append(
                f"\nBest model by IoU: {best.model_name} "
                f"({best.metrics.iou:.4f})"
            )

        lines.append("=" * 60)

        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"ComparisonTable({len(self.results)} results)"
