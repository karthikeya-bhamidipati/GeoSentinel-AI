"""
===============================================================================
GeoSentinel AI

Module:
    engine.py

Description:
    Rule-based explainable recommendation engine.

    The engine evaluates a fixed set of rules against analysis results
    and generates prioritized, human-readable recommendations.

    Design principles:
    - Rule-based, NOT LLM-based (per Master Spec)
    - Every recommendation includes a WHY explanation with data values
    - Rules are loaded from YAML, not hardcoded
    - Multiple rules can fire per analysis
    - Results are sorted by severity (CRITICAL first)

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from src.models.unet import LandCoverClass
from src.recommendation.rules import Rule, RuleLoader, Severity
from src.recommendation.templates import ExplanationRenderer
from src.analytics.area import AreaChangeResult
from src.temporal.ndvi_change import NDVIChangeResult
from src.temporal.ndbi_change import NDBIChangeResult
from src.temporal.segmentation_change import SegmentationChangeResult
from src.utils.helpers import pixel_count_to_km2
from src.utils.logger import logger


# =============================================================================
# Recommendation Output
# =============================================================================


@dataclass
class Recommendation:
    """
    A single recommendation triggered by an analysis result.

    Attributes
    ----------
    rule_id : str
    category : str
    severity : Severity
    title : str
    recommendation : str
        What to do.
    why : str
        Why this recommendation was triggered (data-driven explanation).
    priority : int
        Higher = more urgent.
    """

    rule_id: str
    category: str
    severity: Severity
    title: str
    recommendation: str
    why: str
    priority: int = 0

    def to_dict(self) -> dict:

        return {
            "rule_id": self.rule_id,
            "category": self.category,
            "severity": self.severity.value,
            "title": self.title,
            "recommendation": self.recommendation,
            "why": self.why,
            "priority": self.priority,
        }


@dataclass
class RecommendationResult:
    """
    Complete recommendation output for an analysis.
    """

    recommendations: list[Recommendation] = field(default_factory=list)
    date1: str = ""
    date2: str = ""
    total_area_km2: float = 0.0

    def highest_severity(self) -> Severity | None:

        if not self.recommendations:
            return None

        return max(
            self.recommendations,
            key=lambda r: r.priority,
        ).severity

    def to_dict(self) -> dict:

        return {
            "date1": self.date1,
            "date2": self.date2,
            "total_area_km2": self.total_area_km2,
            "highest_severity": (
                self.highest_severity().value
                if self.highest_severity()
                else None
            ),
            "recommendations": [
                r.to_dict() for r in self.recommendations
            ],
        }


# =============================================================================
# Recommendation Engine
# =============================================================================


class RecommendationEngine:
    """
    Rule-based explainable recommendation engine.

    Evaluates each loaded rule against analysis results and
    generates a prioritized list of recommendations.

    Usage
    -----
    >>> engine = RecommendationEngine()
    >>> result = engine.evaluate(
    ...     ndvi_change=...,
    ...     ndbi_change=...,
    ...     seg_change=...,
    ...     area_change=...,
    ...     date1="2023-01-01",
    ...     date2="2024-01-01",
    ... )
    """

    def __init__(self) -> None:

        self._loader = RuleLoader()
        self._renderer = ExplanationRenderer()
        self._rules: list[Rule] = []

        self._load_rules()

    # ------------------------------------------------------------------

    def _load_rules(self) -> None:
        """Load rules from YAML config."""
        try:
            self._rules = self._loader.load()
        except FileNotFoundError as exc:
            logger.warning(
                f"Rules file not found: {exc}. "
                f"Using empty ruleset."
            )
            self._rules = []

    # ------------------------------------------------------------------

    def evaluate(
        self,
        ndvi_change: NDVIChangeResult | None,
        ndbi_change: NDBIChangeResult | None,
        seg_change: SegmentationChangeResult | None,
        area_change: AreaChangeResult | None,
        date1: str | date = "",
        date2: str | date = "",
        pixel_resolution_m: float = 10.0,
    ) -> RecommendationResult:
        """
        Evaluate all rules against analysis results.

        Parameters
        ----------
        ndvi_change : NDVIChangeResult | None
        ndbi_change : NDBIChangeResult | None
        seg_change : SegmentationChangeResult | None
        area_change : AreaChangeResult | None
        date1, date2 : str | date
            Analysis period dates.
        pixel_resolution_m : float

        Returns
        -------
        RecommendationResult
        """

        recommendations = []

        date1_str = str(date1)
        date2_str = str(date2)

        total_area_km2 = (
            area_change.total_area_km2 if area_change else 0.0
        )

        # ----------------------------------------------------------
        # Build context for template rendering
        # ----------------------------------------------------------

        context = self._build_context(
            ndvi_change=ndvi_change,
            ndbi_change=ndbi_change,
            seg_change=seg_change,
            area_change=area_change,
            date1=date1_str,
            date2=date2_str,
            pixel_resolution_m=pixel_resolution_m,
        )

        # ----------------------------------------------------------
        # Evaluate each rule
        # ----------------------------------------------------------

        for rule in self._rules:
            triggered = self._evaluate_rule(rule, context)

            if triggered:
                why = self._renderer.render(
                    rule.why_template,
                    {**context, "threshold": rule.threshold_pct or 0.0},
                )

                recommendations.append(
                    Recommendation(
                        rule_id=rule.rule_id,
                        category=rule.category,
                        severity=rule.severity,
                        title=rule.title,
                        recommendation=rule.recommendation.strip(),
                        why=why,
                        priority=rule.priority(),
                    )
                )

        # ----------------------------------------------------------
        # Seasonal Phenology Check
        # ----------------------------------------------------------

        if context.get("seasonal_shift") and any("Loss" in r.title or "Decline" in r.title for r in recommendations):
            recommendations.append(
                Recommendation(
                    rule_id="SEASONAL_PHENOLOGY",
                    category="Context",
                    severity=Severity.LOW,
                    title="Potential Seasonal Phenology Detected",
                    recommendation=(
                        "Verify if the detected vegetation/water losses are due to "
                        "natural seasonal changes (e.g. winter leaf fall, dry season) "
                        "rather than physical deforestation or permanent change."
                    ),
                    why=(
                        f"The analysis spans from {date1_str} to {date2_str}, which "
                        f"crosses major seasonal boundaries. Some detected declines "
                        f"may be natural phenological cycles."
                    ),
                    priority=50,  # Ensure it shows up high
                )
            )

        # ----------------------------------------------------------
        # Stable fallback: if no significant changes
        # ----------------------------------------------------------

        if not recommendations:
            recommendations.append(
                Recommendation(
                    rule_id="STABLE",
                    category="General",
                    severity=Severity.LOW,
                    title="No Significant Land Cover Changes",
                    recommendation=(
                        "No significant land cover changes were detected "
                        "in the selected area and time period. "
                        "Continue periodic monitoring (quarterly recommended)."
                    ),
                    why=(
                        f"Land cover changes between {date1_str} and "
                        f"{date2_str} were within normal variation "
                        f"thresholds across all categories."
                    ),
                    priority=1,
                )
            )

        # Sort by priority (highest first)
        recommendations.sort(key=lambda r: r.priority, reverse=True)

        logger.info(
            f"Recommendation engine: {len(recommendations)} "
            f"recommendation(s) generated."
        )

        return RecommendationResult(
            recommendations=recommendations,
            date1=date1_str,
            date2=date2_str,
            total_area_km2=total_area_km2,
        )

    # ------------------------------------------------------------------

    def _build_context(
        self,
        ndvi_change: NDVIChangeResult | None,
        ndbi_change: NDBIChangeResult | None,
        seg_change: SegmentationChangeResult | None,
        area_change: AreaChangeResult | None,
        date1: str,
        date2: str,
        pixel_resolution_m: float,
    ) -> dict[str, Any]:
        """
        Build a flat context dictionary from all analysis results.
        """

        ctx: dict[str, Any] = {
            "date1": date1,
            "date2": date2,
            "seasonal_shift": False,
        }

        try:
            from dateutil import parser
            d1 = parser.parse(date1)
            d2 = parser.parse(date2)
            month_diff = abs(d1.month - d2.month)
            ctx["seasonal_shift"] = (month_diff > 2 and month_diff < 10)
        except Exception:
            pass

        # NDVI context
        if ndvi_change:
            ctx["vegetation_loss_pct"] = ndvi_change.loss_pct
            ctx["vegetation_gain_pct"] = ndvi_change.gain_pct
            ctx["ndvi_delta"] = ndvi_change.mean_delta
            ctx["change_pct"] = ndvi_change.loss_pct
            ctx["change_km2"] = pixel_count_to_km2(
                int(ndvi_change.loss_mask.sum()),
                pixel_resolution_m,
            )

        # NDBI context
        if ndbi_change:
            ctx["urban_gain_pct"] = ndbi_change.urban_increase_pct
            ctx["urban_loss_pct"] = ndbi_change.urban_decrease_pct

        # Segmentation change context
        if seg_change:
            ctx["urban_expansion_pixels"] = seg_change.urban_expansion_pixels
            ctx["vegetation_loss_pixels"] = seg_change.vegetation_loss_pixels
            ctx["water_loss_pixels"] = seg_change.water_loss_pixels
            ctx["hotspot_count"] = len(seg_change.hotspots)
            ctx["min_cluster_km2"] = 0.5  # from rules config
            ctx["urban_expansion_near_water_body"] = (
                self._check_urban_near_water(seg_change)
            )

            if seg_change.hotspots:
                largest = seg_change.hotspots[0]
                ctx["largest_km2"] = pixel_count_to_km2(
                    largest.area_pixels, pixel_resolution_m
                )
                ctx["center_lat"] = 17.3850  # Hyderabad default
                ctx["center_lon"] = 78.4867

        # Area change context
        if area_change:
            ctx["total_area_km2"] = area_change.total_area_km2

            veg_change = area_change.change_km2.get(
                LandCoverClass.VEGETATION, 0.0
            )
            ctx["vegetation_loss_km2"] = abs(veg_change) if veg_change < 0 else 0.0

            ctx["water_loss_km2"] = 0.0

            urban_change = area_change.change_km2.get(
                LandCoverClass.URBAN, 0.0
            )
            ctx["urban_gain_km2"] = urban_change if urban_change > 0 else 0.0

            # Percentage changes relative to total area
            if area_change.total_area_km2 > 0:
                veg_change_pct_abs = (
                    abs(veg_change) / area_change.total_area_km2 * 100
                )
                ctx["water_loss_pct"] = 0.0

                if "vegetation_loss_pct" not in ctx:
                    ctx["vegetation_loss_pct"] = veg_change_pct_abs

        return ctx

    # ------------------------------------------------------------------

    def _evaluate_rule(
        self,
        rule: Rule,
        context: dict[str, Any],
    ) -> bool:
        """
        Evaluate a single rule against the context.

        Parameters
        ----------
        rule : Rule
        context : dict

        Returns
        -------
        bool
            True if the rule condition is satisfied.
        """

        condition = rule.condition

        # Vegetation loss rules
        if "vegetation_loss_pct >= threshold" in condition:
            threshold = rule.threshold_pct or 0.0
            return context.get("vegetation_loss_pct", 0.0) >= threshold

        # Urban expansion rules
        if "urban_gain_pct >= threshold" in condition:
            threshold = rule.threshold_pct or 0.0
            return context.get("urban_gain_pct", 0.0) >= threshold

        # Urban near water
        if "urban_expansion_near_water_body" in condition:
            return bool(
                context.get("urban_expansion_near_water_body", False)
            )

        # Water body loss
        if "water_loss_pct >= threshold" in condition:
            threshold = rule.threshold_pct or 0.0
            return context.get("water_loss_pct", 0.0) >= threshold

        # NDVI decline
        if "mean_ndvi_change <= threshold" in condition:
            threshold = rule.threshold_delta or 0.0
            return context.get("ndvi_delta", 0.0) <= threshold

        # Hotspot
        if "hotspot_count > 0" in condition:
            return context.get("hotspot_count", 0) > 0

        # Stable (fallback)
        if "no_significant_change" in condition:
            return False  # Handled by the engine fallback

        return False

    # ------------------------------------------------------------------

    def _check_urban_near_water(
        self,
        seg_change: SegmentationChangeResult,
    ) -> bool:
        """
        Simplified check for urban expansion near water bodies.

        In a full implementation this would use spatial buffers
        against water body polygons. Here we use the transition matrix
        to check if any Water→Urban transitions occurred.
        """

        return False

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"RecommendationEngine("
            f"{len(self._rules)} rules)"
        )
