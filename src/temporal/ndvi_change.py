"""
===============================================================================
GeoSentinel AI

Module:
    ndvi_change.py

Description:
    NDVI temporal change analysis.

    Computes per-pixel NDVI delta between two dates and classifies
    each pixel into gain, loss, or stable categories.

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
class NDVIChangeResult:
    """
    Result of NDVI temporal change analysis.

    Attributes
    ----------
    delta : np.ndarray
        Per-pixel NDVI delta (T2 - T1), shape (H, W).
    gain_mask : np.ndarray
        Boolean mask: pixels with vegetation gain.
    loss_mask : np.ndarray
        Boolean mask: pixels with vegetation loss.
    stable_mask : np.ndarray
        Boolean mask: unchanged pixels.
    mean_delta : float
        Spatial mean NDVI change.
    gain_pct : float
        Percentage of pixels with gain.
    loss_pct : float
        Percentage of pixels with loss.
    stable_pct : float
        Percentage of stable pixels.
    """

    delta: np.ndarray
    gain_mask: np.ndarray
    loss_mask: np.ndarray
    stable_mask: np.ndarray
    mean_delta: float
    gain_pct: float
    loss_pct: float
    stable_pct: float

    def summary(self) -> dict:

        return {
            "mean_delta": round(self.mean_delta, 4),
            "gain_pct": round(self.gain_pct, 2),
            "loss_pct": round(self.loss_pct, 2),
            "stable_pct": round(self.stable_pct, 2),
        }


class NDVIChangeAnalyzer:
    """
    Analyzes NDVI change between two time periods.

    Classifies each pixel based on delta thresholds:
    - Gain: delta > +threshold (greening / revegetation)
    - Loss: delta < -threshold (deforestation / die-off)
    - Stable: |delta| <= threshold

    Parameters
    ----------
    gain_threshold : float
        Minimum positive delta to classify as gain (default: 0.1).
    loss_threshold : float
        Maximum negative delta to classify as loss (default: -0.1).
    """

    def __init__(
        self,
        gain_threshold: float = 0.1,
        loss_threshold: float = -0.1,
    ) -> None:

        self.gain_threshold = gain_threshold
        self.loss_threshold = loss_threshold

    # ------------------------------------------------------------------

    def analyze(
        self,
        ndvi_t1: np.ndarray,
        ndvi_t2: np.ndarray,
    ) -> NDVIChangeResult:
        """
        Compute NDVI change between two arrays.

        Parameters
        ----------
        ndvi_t1 : np.ndarray
            NDVI at time 1 (H, W), float32.
        ndvi_t2 : np.ndarray
            NDVI at time 2 (H, W), float32.

        Returns
        -------
        NDVIChangeResult

        Raises
        ------
        TemporalAnalysisError
        """

        if ndvi_t1.shape != ndvi_t2.shape:
            raise TemporalAnalysisError(
                f"NDVI arrays must have the same shape. "
                f"Got {ndvi_t1.shape} and {ndvi_t2.shape}."
            )

        try:
            delta = (ndvi_t2 - ndvi_t1).astype("float32")

            valid = ~(np.isnan(delta))
            gain_mask = valid & (delta > self.gain_threshold)
            loss_mask = valid & (delta < self.loss_threshold)
            stable_mask = valid & (~gain_mask) & (~loss_mask)

            n_valid = valid.sum()

            gain_pct = float(gain_mask.sum() / n_valid * 100) if n_valid else 0.0
            loss_pct = float(loss_mask.sum() / n_valid * 100) if n_valid else 0.0
            stable_pct = float(stable_mask.sum() / n_valid * 100) if n_valid else 0.0

            mean_delta = float(np.nanmean(delta))

        except Exception as exc:
            raise TemporalAnalysisError(
                f"NDVI change analysis failed: {exc}"
            ) from exc

        logger.info(
            f"NDVI change: mean_delta={mean_delta:.3f}, "
            f"gain={gain_pct:.1f}%, loss={loss_pct:.1f}%"
        )

        return NDVIChangeResult(
            delta=delta,
            gain_mask=gain_mask,
            loss_mask=loss_mask,
            stable_mask=stable_mask,
            mean_delta=mean_delta,
            gain_pct=gain_pct,
            loss_pct=loss_pct,
            stable_pct=stable_pct,
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"NDVIChangeAnalyzer("
            f"gain>{self.gain_threshold}, "
            f"loss<{self.loss_threshold})"
        )
