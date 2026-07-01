"""
===============================================================================
GeoSentinel AI

Module:
    ndbi_change.py

Description:
    NDBI temporal change analysis for urban expansion detection.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.eo.exceptions import TemporalAnalysisError
from src.utils.logger import logger


@dataclass
class NDBIChangeResult:
    """
    Result of NDBI temporal change analysis.

    Attributes
    ----------
    delta : np.ndarray
        Per-pixel NDBI delta (T2 - T1).
    urban_increase_mask : np.ndarray
        Pixels where NDBI increased (urban expansion).
    urban_decrease_mask : np.ndarray
        Pixels where NDBI decreased.
    stable_mask : np.ndarray
        Unchanged pixels.
    mean_delta : float
    urban_increase_pct : float
    urban_decrease_pct : float
    stable_pct : float
    """

    delta: np.ndarray
    urban_increase_mask: np.ndarray
    urban_decrease_mask: np.ndarray
    stable_mask: np.ndarray
    mean_delta: float
    urban_increase_pct: float
    urban_decrease_pct: float
    stable_pct: float

    def summary(self) -> dict:

        return {
            "mean_delta": round(self.mean_delta, 4),
            "urban_increase_pct": round(self.urban_increase_pct, 2),
            "urban_decrease_pct": round(self.urban_decrease_pct, 2),
            "stable_pct": round(self.stable_pct, 2),
        }


class NDBIChangeAnalyzer:
    """
    Analyzes NDBI change to detect urban expansion.

    Parameters
    ----------
    increase_threshold : float
        Minimum positive delta for urban increase (default: 0.05).
    decrease_threshold : float
        Maximum negative delta for urban decrease (default: -0.05).
    """

    def __init__(
        self,
        increase_threshold: float = 0.05,
        decrease_threshold: float = -0.05,
    ) -> None:

        self.increase_threshold = increase_threshold
        self.decrease_threshold = decrease_threshold

    # ------------------------------------------------------------------

    def analyze(
        self,
        ndbi_t1: np.ndarray,
        ndbi_t2: np.ndarray,
    ) -> NDBIChangeResult:
        """
        Compute NDBI change between two arrays.

        Parameters
        ----------
        ndbi_t1 : np.ndarray
        ndbi_t2 : np.ndarray

        Returns
        -------
        NDBIChangeResult
        """

        if ndbi_t1.shape != ndbi_t2.shape:
            raise TemporalAnalysisError(
                f"NDBI arrays must have the same shape. "
                f"Got {ndbi_t1.shape} and {ndbi_t2.shape}."
            )

        try:
            delta = (ndbi_t2 - ndbi_t1).astype("float32")

            valid = ~(np.isnan(delta))
            urban_increase = valid & (delta > self.increase_threshold)
            urban_decrease = valid & (delta < self.decrease_threshold)
            stable = valid & (~urban_increase) & (~urban_decrease)

            n_valid = valid.sum()

            urban_increase_pct = float(
                urban_increase.sum() / n_valid * 100
            ) if n_valid else 0.0

            urban_decrease_pct = float(
                urban_decrease.sum() / n_valid * 100
            ) if n_valid else 0.0

            stable_pct = float(
                stable.sum() / n_valid * 100
            ) if n_valid else 0.0

            mean_delta = float(np.nanmean(delta))

        except Exception as exc:
            raise TemporalAnalysisError(
                f"NDBI change analysis failed: {exc}"
            ) from exc

        logger.info(
            f"NDBI change: mean_delta={mean_delta:.3f}, "
            f"urban_increase={urban_increase_pct:.1f}%"
        )

        return NDBIChangeResult(
            delta=delta,
            urban_increase_mask=urban_increase,
            urban_decrease_mask=urban_decrease,
            stable_mask=stable,
            mean_delta=mean_delta,
            urban_increase_pct=urban_increase_pct,
            urban_decrease_pct=urban_decrease_pct,
            stable_pct=stable_pct,
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"NDBIChangeAnalyzer("
            f"increase>{self.increase_threshold})"
        )
