"""
===============================================================================
GeoSentinel AI

Module:
    templates.py

Description:
    Template rendering for recommendation WHY explanations.

    Each recommendation includes a human-readable explanation of WHY
    the rule was triggered, with specific numerical values inserted
    from the analysis results.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from datetime import date
from typing import Any


class ExplanationRenderer:
    """
    Renders WHY explanation templates with analysis data.

    The template system uses Python string format() with keyword
    arguments corresponding to analysis result fields.

    No LLM is used. All explanations are deterministic and
    fully traceable to specific data values.
    """

    def render(
        self,
        template: str,
        context: dict[str, Any],
    ) -> str:
        """
        Render a template with the given context.

        Parameters
        ----------
        template : str
            Template string with {placeholder} syntax.
        context : dict[str, Any]
            Values to substitute into the template.

        Returns
        -------
        str
            Rendered explanation text.
        """

        # Provide safe defaults for any missing keys
        safe_context = self._safe_context(context)

        try:
            return template.strip().format(**safe_context)

        except (KeyError, ValueError) as exc:
            # If rendering fails, return the template as-is
            return template.strip()

    # ------------------------------------------------------------------

    def _safe_context(
        self,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build a context dict with safe defaults for all known placeholders.
        """

        today = date.today().isoformat()

        defaults = {
            "change_pct": 0.0,
            "change_km2": 0.0,
            "date1": today,
            "date2": today,
            "threshold": 0.0,
            "ndvi_delta": 0.0,
            "hotspot_count": 0,
            "min_cluster_km2": 0.0,
            "largest_km2": 0.0,
            "center_lat": 17.385,
            "center_lon": 78.486,
            "distance_m": 0.0,
            "area_km2": 0.0,
        }

        return {**defaults, **context}
