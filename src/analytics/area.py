"""
===============================================================================
GeoSentinel AI

Module:
    area.py

Description:
    Area calculations and land cover statistics.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from src.models.unet import LandCoverClass, LAND_COVER_NAMES, NUM_CLASSES
from src.utils.helpers import pixel_count_to_km2
from src.utils.logger import logger


@dataclass
class ClassArea:
    """
    Area information for a single land cover class.
    """

    class_id: int
    class_name: str
    pixel_count: int
    area_km2: float
    coverage_pct: float

    def to_dict(self) -> dict:

        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "pixel_count": self.pixel_count,
            "area_km2": round(self.area_km2, 4),
            "coverage_pct": round(self.coverage_pct, 2),
        }


@dataclass
class AreaChangeResult:
    """
    Area change statistics between T1 and T2.
    """

    t1_areas: list[ClassArea] = field(default_factory=list)
    t2_areas: list[ClassArea] = field(default_factory=list)
    change_km2: dict[int, float] = field(default_factory=dict)
    change_pct: dict[int, float] = field(default_factory=dict)
    total_area_km2: float = 0.0

    def get_change(self, class_id: int) -> dict:

        return {
            "class_id": class_id,
            "class_name": LAND_COVER_NAMES.get(class_id, str(class_id)),
            "change_km2": round(self.change_km2.get(class_id, 0.0), 4),
            "change_pct": round(self.change_pct.get(class_id, 0.0), 2),
        }

    def to_rows(self) -> list[dict]:
        """Export as list of dicts for CSV."""

        rows = []

        t1_map = {a.class_id: a for a in self.t1_areas}
        t2_map = {a.class_id: a for a in self.t2_areas}

        for class_id in range(NUM_CLASSES):
            t1 = t1_map.get(class_id)
            t2 = t2_map.get(class_id)

            rows.append({
                "class_id": class_id,
                "class_name": LAND_COVER_NAMES.get(class_id, str(class_id)),
                "t1_area_km2": round(t1.area_km2, 4) if t1 else 0.0,
                "t2_area_km2": round(t2.area_km2, 4) if t2 else 0.0,
                "t1_pct": round(t1.coverage_pct, 2) if t1 else 0.0,
                "t2_pct": round(t2.coverage_pct, 2) if t2 else 0.0,
                "change_km2": round(
                    self.change_km2.get(class_id, 0.0), 4
                ),
                "change_pct": round(
                    self.change_pct.get(class_id, 0.0), 2
                ),
            })

        return rows


class AreaCalculator:
    """
    Computes per-class area statistics from segmentation masks.

    Parameters
    ----------
    pixel_resolution_m : float
        Spatial resolution in metres (default: 10m for Sentinel-2).
    """

    def __init__(
        self,
        pixel_resolution_m: float = 10.0,
    ) -> None:

        self.pixel_resolution_m = pixel_resolution_m

    # ------------------------------------------------------------------

    def compute_areas(
        self,
        mask: np.ndarray,
    ) -> list[ClassArea]:
        """
        Compute area statistics for each land cover class.

        Parameters
        ----------
        mask : np.ndarray
            Shape (H, W), int class indices.

        Returns
        -------
        list[ClassArea]
        """

        total_pixels = mask.size
        areas = []

        for class_id in range(NUM_CLASSES):

            pixel_count = int((mask == class_id).sum())
            area_km2 = pixel_count_to_km2(
                pixel_count, self.pixel_resolution_m
            )
            coverage_pct = pixel_count / total_pixels * 100

            areas.append(ClassArea(
                class_id=class_id,
                class_name=LAND_COVER_NAMES.get(class_id, str(class_id)),
                pixel_count=pixel_count,
                area_km2=area_km2,
                coverage_pct=coverage_pct,
            ))

        return areas

    # ------------------------------------------------------------------

    def compute_change(
        self,
        mask_t1: np.ndarray,
        mask_t2: np.ndarray,
    ) -> AreaChangeResult:
        """
        Compute area change between two segmentation masks.

        Parameters
        ----------
        mask_t1 : np.ndarray
        mask_t2 : np.ndarray

        Returns
        -------
        AreaChangeResult
        """

        t1_areas = self.compute_areas(mask_t1)
        t2_areas = self.compute_areas(mask_t2)

        t1_map = {a.class_id: a for a in t1_areas}
        t2_map = {a.class_id: a for a in t2_areas}

        change_km2 = {}
        change_pct = {}

        total_area_km2 = pixel_count_to_km2(
            mask_t1.size, self.pixel_resolution_m
        )

        for class_id in range(NUM_CLASSES):
            t1_km2 = t1_map.get(class_id, ClassArea(class_id, "", 0, 0.0, 0.0)).area_km2
            t2_km2 = t2_map.get(class_id, ClassArea(class_id, "", 0, 0.0, 0.0)).area_km2

            delta_km2 = t2_km2 - t1_km2
            delta_pct = (delta_km2 / total_area_km2 * 100) if total_area_km2 > 0 else 0.0

            change_km2[class_id] = delta_km2
            change_pct[class_id] = delta_pct

        logger.info(
            f"Area change computed: "
            f"total={total_area_km2:.2f} km²"
        )

        return AreaChangeResult(
            t1_areas=t1_areas,
            t2_areas=t2_areas,
            change_km2=change_km2,
            change_pct=change_pct,
            total_area_km2=total_area_km2,
        )
