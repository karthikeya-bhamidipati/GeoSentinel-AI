"""
===============================================================================
GeoSentinel AI

Package:
    src.recommendation

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from src.recommendation.rules import Rule, RuleLoader, Severity
from src.recommendation.templates import ExplanationRenderer
from src.recommendation.engine import (
    RecommendationEngine,
    RecommendationResult,
    Recommendation,
)

__all__ = [
    "Rule",
    "RuleLoader",
    "Severity",
    "ExplanationRenderer",
    "RecommendationEngine",
    "RecommendationResult",
    "Recommendation",
]
