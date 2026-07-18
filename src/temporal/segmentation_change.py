"""
===============================================================================
GeoSentinel AI

Module:
    segmentation_change.py

Description:
    Segmentation-based change detection between two classified scenes.

    Computes:
    - Transition matrix (from-class → to-class pixel counts)
    - Change map (pixels that changed class)
    - Hotspot detection (spatial clusters of change)

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import ndimage

from src.models.unet import LandCoverClass, LAND_COVER_NAMES, NUM_CLASSES
from src.eo.exceptions import TemporalAnalysisError
from src.utils.logger import logger


@dataclass
class Hotspot:
    """
    A spatial cluster of land cover change.

    Attributes
    ----------
    center_row : int
    center_col : int
    area_pixels : int
    dominant_transition : tuple[int, int]
        (from_class, to_class) most common transition.
    """

    center_row: int
    center_col: int
    area_pixels: int
    dominant_transition: tuple[int, int]
    center_lat: float | None = None
    center_lon: float | None = None

    def to_dict(self) -> dict:

        from_cls, to_cls = self.dominant_transition

        return {
            "center_row": self.center_row,
            "center_col": self.center_col,
            "center_lat": self.center_lat,
            "center_lon": self.center_lon,
            "area_pixels": self.area_pixels,
            "from_class": LAND_COVER_NAMES.get(from_cls, str(from_cls)),
            "to_class": LAND_COVER_NAMES.get(to_cls, str(to_cls)),
        }


@dataclass
class SegmentationChangeResult:
    """
    Result of segmentation-based temporal change analysis.

    Attributes
    ----------
    change_mask : np.ndarray
        Boolean array (H, W): True where class changed.
    change_map : np.ndarray
        (H, W) int array: class of T2 for changed pixels, else 0.
    transition_matrix : np.ndarray
        (num_classes, num_classes) count of T1→T2 transitions.
    hotspots : list[Hotspot]
        Detected spatial change hotspots.
    total_changed_pixels : int
    changed_pct : float
    urban_expansion_pixels : int
    vegetation_loss_pixels : int
    water_loss_pixels : int
    """

    change_mask: np.ndarray
    change_map: np.ndarray
    transition_matrix: np.ndarray
    hotspots: list[Hotspot]
    total_changed_pixels: int
    changed_pct: float
    urban_expansion_pixels: int
    vegetation_loss_pixels: int
    water_loss_pixels: int

    def summary(self) -> dict:

        return {
            "changed_pct": round(self.changed_pct, 2),
            "urban_expansion_pixels": self.urban_expansion_pixels,
            "vegetation_loss_pixels": self.vegetation_loss_pixels,
            "water_loss_pixels": self.water_loss_pixels,
            "num_hotspots": len(self.hotspots),
        }

    def transition_dict(self) -> dict[str, dict[str, int]]:
        """
        Return transition matrix as a nested dict with class names.
        """

        result = {}

        for i in range(NUM_CLASSES):
            from_name = LAND_COVER_NAMES.get(i, str(i))
            result[from_name] = {}

            for j in range(NUM_CLASSES):
                to_name = LAND_COVER_NAMES.get(j, str(j))
                result[from_name][to_name] = int(
                    self.transition_matrix[i, j]
                )

        return result


class SegmentationChangeAnalyzer:
    """
    Detects land cover changes between two segmentation masks.

    Computes transition matrices, change maps, and hotspots.

    Parameters
    ----------
    min_hotspot_pixels : int
        Minimum cluster size to qualify as a hotspot.
    """

    def __init__(
        self,
        min_hotspot_pixels: int = 50,
    ) -> None:

        self.min_hotspot_pixels = min_hotspot_pixels

    # ------------------------------------------------------------------

    def analyze(
        self,
        mask_t1: np.ndarray,
        mask_t2: np.ndarray,
        ml_change_mask: np.ndarray | None = None,
        bbox: list[float] | tuple[float, float, float, float] | None = None,
    ) -> SegmentationChangeResult:
        """
        Analyze segmentation change between two masks.

        Parameters
        ----------
        mask_t1 : np.ndarray
            T1 classification mask (H, W), int32.
        mask_t2 : np.ndarray
            T2 classification mask (H, W), int32.
        ml_change_mask: np.ndarray | None
        bbox: list[float] | tuple | None
            [west, south, east, north] in EPSG:4326

        Returns
        -------
        SegmentationChangeResult

        Raises
        ------
        TemporalAnalysisError
        """

        if mask_t1.shape != mask_t2.shape:
            raise TemporalAnalysisError(
                f"Segmentation masks must have the same shape. "
                f"Got {mask_t1.shape} and {mask_t2.shape}."
            )

        try:
            # ----------------------------------------------------------
            # Change mask
            # ----------------------------------------------------------

            if ml_change_mask is not None:
                # The Siamese U-Net provides a structural change mask (0 or 1).
                # A pixel is "changed" only if the U-Net says it changed AND
                # the DeepLab classification class actually changed.
                # IMPORTANT: Do NOT overwrite mask_t2 — we need the original
                # classification to compute accurate area statistics.
                change_mask_nn = ml_change_mask > 0
                class_changed = mask_t1 != mask_t2
                change_mask = change_mask_nn & class_changed
            else:
                change_mask = mask_t1 != mask_t2
            
            total_pixels = mask_t1.size
            changed_pixels = int(change_mask.sum())
            changed_pct = changed_pixels / total_pixels * 100

            # ----------------------------------------------------------
            # Change map
            # ----------------------------------------------------------

            change_map = np.where(change_mask, mask_t2, 0).astype(np.int32)

            # ----------------------------------------------------------
            # Transition matrix
            # ----------------------------------------------------------

            transition_matrix = np.zeros(
                (NUM_CLASSES, NUM_CLASSES), dtype=np.int64
            )

            for i in range(NUM_CLASSES):
                for j in range(NUM_CLASSES):
                    transition_matrix[i, j] = int(
                        ((mask_t1 == i) & (mask_t2 == j)).sum()
                    )

            # ----------------------------------------------------------
            # Urban expansion (other → Urban)
            # ----------------------------------------------------------

            urban_expansion_pixels = int(
                (change_mask & (mask_t1 != LandCoverClass.URBAN) & (mask_t2 == LandCoverClass.URBAN)).sum()
            )

            # ----------------------------------------------------------
            # Vegetation loss (Vegetation → other)
            # ----------------------------------------------------------

            vegetation_loss_pixels = int(
                (change_mask & (mask_t1 == LandCoverClass.VEGETATION) & (mask_t2 != LandCoverClass.VEGETATION)).sum()
            )

            # ----------------------------------------------------------
            # Water loss (Water → other)
            # ----------------------------------------------------------

            water_loss_pixels = int(
                (change_mask & (mask_t1 == LandCoverClass.WATER) & (mask_t2 != LandCoverClass.WATER)).sum()
            )

            # ----------------------------------------------------------
            # Hotspot detection
            # ----------------------------------------------------------

            hotspots = self._detect_hotspots(
                change_mask, mask_t1, mask_t2, bbox=bbox
            )

        except TemporalAnalysisError:
            raise

        except Exception as exc:
            raise TemporalAnalysisError(
                f"Segmentation change analysis failed: {exc}"
            ) from exc

        logger.info(
            f"Segmentation change: {changed_pct:.1f}% changed, "
            f"{len(hotspots)} hotspots detected"
        )

        return SegmentationChangeResult(
            change_mask=change_mask,
            change_map=change_map,
            transition_matrix=transition_matrix,
            hotspots=hotspots,
            total_changed_pixels=changed_pixels,
            changed_pct=changed_pct,
            urban_expansion_pixels=urban_expansion_pixels,
            vegetation_loss_pixels=vegetation_loss_pixels,
            water_loss_pixels=water_loss_pixels,
        )

    # ------------------------------------------------------------------

    def _detect_hotspots(
        self,
        change_mask: np.ndarray,
        mask_t1: np.ndarray,
        mask_t2: np.ndarray,
        bbox: list[float] | tuple[float, float, float, float] | None = None,
    ) -> list[Hotspot]:
        """
        Detect spatial clusters of change.

        Uses connected component labeling to find clusters,
        then filters by minimum size. If bbox is provided,
        calculates the geographical coordinates of the cluster center.
        """

        labeled, n_components = ndimage.label(change_mask)

        hotspots = []
        H, W = change_mask.shape

        for label_id in range(1, n_components + 1):

            component = labeled == label_id
            area = int(component.sum())

            if area < self.min_hotspot_pixels:
                continue

            rows, cols = np.where(component)
            center_row = int(rows.mean())
            center_col = int(cols.mean())

            lat, lon = None, None
            if bbox is not None:
                west, south, east, north = bbox
                # Interpolate based on the assumption that pixel (0,0) is top-left
                lon = west + (center_col / W) * (east - west)
                lat = north - (center_row / H) * (north - south)

            # Find dominant T1→T2 transition in this hotspot
            t1_values = mask_t1[component]
            t2_values = mask_t2[component]

            transitions = {}
            for t1, t2 in zip(t1_values, t2_values):
                key = (int(t1), int(t2))
                transitions[key] = transitions.get(key, 0) + 1

            dominant = max(transitions, key=transitions.get) if transitions else (0, 0)

            hotspots.append(Hotspot(
                center_row=center_row,
                center_col=center_col,
                center_lat=lat,
                center_lon=lon,
                area_pixels=area,
                dominant_transition=dominant,
            ))

        # Sort by area (largest first)
        hotspots.sort(key=lambda h: h.area_pixels, reverse=True)

        return hotspots

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"SegmentationChangeAnalyzer("
            f"min_hotspot={self.min_hotspot_pixels}px)"
        )
