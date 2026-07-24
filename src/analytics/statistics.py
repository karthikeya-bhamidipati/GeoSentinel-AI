"""
===============================================================================
GeoSentinel AI

Module:
    statistics.py

Description:
    Spatial statistics computation for analytics.

    Computes:
    - Index statistics per class (mean NDVI, NDBI, etc.)
    - Hotspot geographic coordinates
    - Trend statistics (before/after comparisons)

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from src.models.unet import LandCoverClass, LAND_COVER_NAMES, NUM_CLASSES
from src.utils.logger import logger


@dataclass
class IndexStatistics:
    """
    Statistics for a spectral index within a specific class.
    """

    index_name: str
    class_id: int
    class_name: str
    mean: float
    std: float
    min_val: float
    max_val: float
    pixel_count: int

    def to_dict(self) -> dict:

        return {
            "index": self.index_name,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "mean": round(self.mean, 4),
            "std": round(self.std, 4),
            "min": round(self.min_val, 4),
            "max": round(self.max_val, 4),
            "pixel_count": self.pixel_count,
        }


@dataclass
class SpatialStatisticsResult:
    """
    Complete spatial statistics for an analysis period.
    """

    index_stats_t1: list[IndexStatistics] = field(default_factory=list)
    index_stats_t2: list[IndexStatistics] = field(default_factory=list)
    trend_summary: dict[str, Any] = field(default_factory=dict)


class SpatialStatisticsCalculator:
    """
    Computes spatial statistics on segmentation masks and index arrays.
    """

    # ------------------------------------------------------------------

    def compute_index_stats(
        self,
        index_array: np.ndarray,
        mask: np.ndarray,
        index_name: str,
    ) -> list[IndexStatistics]:
        """
        Compute per-class statistics for a spectral index.

        Parameters
        ----------
        index_array : np.ndarray
            Shape (H, W), float32.
        mask : np.ndarray
            Shape (H, W), int class indices.
        index_name : str

        Returns
        -------
        list[IndexStatistics]
        """

        stats = []

        for class_id in range(NUM_CLASSES):
            if class_id == LandCoverClass.BACKGROUND:
                continue
            pixels = index_array[mask == class_id]

            # Remove NaN values
            pixels = pixels[~np.isnan(pixels)]

            if len(pixels) == 0:
                continue

            stats.append(IndexStatistics(
                index_name=index_name,
                class_id=class_id,
                class_name=LAND_COVER_NAMES.get(class_id, str(class_id)),
                mean=float(pixels.mean()),
                std=float(pixels.std()),
                min_val=float(pixels.min()),
                max_val=float(pixels.max()),
                pixel_count=len(pixels),
            ))

        return stats

    # ------------------------------------------------------------------

    def compute_trend_summary(
        self,
        indices_t1: dict[str, np.ndarray],
        indices_t2: dict[str, np.ndarray],
        mask_t1: np.ndarray,
        mask_t2: np.ndarray,
    ) -> dict[str, Any]:
        """
        Compute high-level trend statistics.

        Parameters
        ----------
        indices_t1 : dict[str, np.ndarray]
        indices_t2 : dict[str, np.ndarray]
        mask_t1, mask_t2 : np.ndarray

        Returns
        -------
        dict[str, Any]
        """

        trend = {}

        for index_name in indices_t1:

            if index_name not in indices_t2:
                continue

            arr_t1 = indices_t1[index_name]
            arr_t2 = indices_t2[index_name]

            mean_t1 = float(np.nanmean(arr_t1))
            mean_t2 = float(np.nanmean(arr_t2))
            delta = mean_t2 - mean_t1

            trend[index_name] = {
                "t1_mean": round(mean_t1, 4),
                "t2_mean": round(mean_t2, 4),
                "delta": round(delta, 4),
                "direction": "increase" if delta > 0 else (
                    "decrease" if delta < 0 else "stable"
                ),
            }

        # Overall vegetation health
        if "NDVI" in trend:
            ndvi_delta = trend["NDVI"]["delta"]
            trend["vegetation_health"] = (
                "improving" if ndvi_delta > 0.05
                else "degrading" if ndvi_delta < -0.05
                else "stable"
            )

        # Urban pressure
        if "NDBI" in trend:
            ndbi_delta = trend["NDBI"]["delta"]
            trend["urban_pressure"] = (
                "high" if ndbi_delta > 0.05
                else "low" if ndbi_delta < -0.05
                else "moderate"
            )

        return trend

    # ------------------------------------------------------------------

    def compute_full(
        self,
        indices_t1: dict[str, np.ndarray],
        indices_t2: dict[str, np.ndarray],
        mask_t1: np.ndarray,
        mask_t2: np.ndarray,
    ) -> SpatialStatisticsResult:
        """
        Compute full spatial statistics for both time periods.

        Returns
        -------
        SpatialStatisticsResult
        """

        stats_t1 = []
        stats_t2 = []

        for index_name, arr in indices_t1.items():
            stats_t1.extend(
                self.compute_index_stats(arr, mask_t1, index_name)
            )

        for index_name, arr in indices_t2.items():
            stats_t2.extend(
                self.compute_index_stats(arr, mask_t2, index_name)
            )

        trend = self.compute_trend_summary(
            indices_t1, indices_t2, mask_t1, mask_t2
        )

        logger.info(
            f"Spatial statistics computed: "
            f"T1={len(stats_t1)} stats, T2={len(stats_t2)} stats"
        )

        return SpatialStatisticsResult(
            index_stats_t1=stats_t1,
            index_stats_t2=stats_t2,
            trend_summary=trend,
        )
