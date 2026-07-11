"""
===============================================================================
GeoSentinel AI

Module:
    rules.py

Description:
    Rule definitions and loader for the recommendation engine.

    Reads recommendation rules from configs/recommendation_rules.yaml.
    Each rule has an ID, category, severity, condition, and templates
    for generating human-readable explanations.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from src.utils.logger import logger
from src.utils.paths import paths


# =============================================================================
# Severity Enum
# =============================================================================


class Severity(str, Enum):
    """Recommendation severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


SEVERITY_PRIORITY = {
    Severity.CRITICAL: 4,
    Severity.HIGH: 3,
    Severity.MEDIUM: 2,
    Severity.LOW: 1,
}


# =============================================================================
# Rule Dataclass
# =============================================================================


@dataclass
class Rule:
    """
    A single recommendation rule.

    Attributes
    ----------
    rule_id : str
    category : str
    severity : Severity
    condition : str
        Textual description of the condition triggering this rule.
    title : str
    recommendation : str
    why_template : str
        Template string with {placeholders} for WHY explanation.
    threshold_pct : float | None
    threshold_delta : float | None
    buffer_m : float | None
    min_cluster_km2 : float | None
    """

    rule_id: str
    category: str
    severity: Severity
    condition: str
    title: str
    recommendation: str
    why_template: str
    threshold_pct: float | None = None
    threshold_delta: float | None = None
    buffer_m: float | None = None
    min_cluster_km2: float | None = None

    def priority(self) -> int:
        """Return numeric priority for sorting."""
        return SEVERITY_PRIORITY.get(self.severity, 0)


# =============================================================================
# Rule Loader
# =============================================================================


class RuleLoader:
    """
    Loads recommendation rules from the YAML config file.

    Parses configs/recommendation_rules.yaml and builds a list of
    Rule objects for use by the RecommendationEngine.
    """

    def __init__(
        self,
        config_path: Path | None = None,
    ) -> None:

        self.config_path = (
            config_path
            or paths.CONFIG_DIR / "recommendation_rules.yaml"
        )

    # ------------------------------------------------------------------

    def load(self) -> list[Rule]:
        """
        Load and parse all rules from the YAML config.

        Returns
        -------
        list[Rule]

        Raises
        ------
        FileNotFoundError
        """

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Rules config not found: {self.config_path}"
            )

        with open(self.config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)

        rules_data = config.get("rules", {})
        rules = []

        for rule_key, rule_data in rules_data.items():
            try:
                rule = Rule(
                    rule_id=rule_data.get("id", rule_key.upper()),
                    category=rule_data.get("category", "General"),
                    severity=Severity(
                        rule_data.get("severity", "LOW")
                    ),
                    condition=rule_data.get("condition", ""),
                    title=rule_data.get("title", ""),
                    recommendation=rule_data.get("recommendation", ""),
                    why_template=rule_data.get("why_template", ""),
                    threshold_pct=rule_data.get("threshold_pct"),
                    threshold_delta=rule_data.get("threshold_delta"),
                    buffer_m=rule_data.get("buffer_m"),
                    min_cluster_km2=rule_data.get("min_cluster_km2"),
                )
                rules.append(rule)

            except Exception as exc:
                logger.warning(
                    f"Failed to parse rule {rule_key!r}: {exc}"
                )

        logger.info(f"Loaded {len(rules)} recommendation rules.")

        return rules
