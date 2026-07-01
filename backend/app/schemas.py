"""
===============================================================================
GeoSentinel AI

Module:
    schemas.py

Description:
    Pydantic v2 request/response schemas for the FastAPI backend.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Job Status
# =============================================================================


class JobStatus(str, Enum):
    """Analysis job lifecycle states."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Request Schemas
# =============================================================================


class AOIGeometry(BaseModel):
    """GeoJSON geometry object for AOI."""

    type: str
    coordinates: Any


class AnalysisRequest(BaseModel):
    """
    Request body for submitting a new analysis.
    """

    aoi: AOIGeometry = Field(
        ...,
        description="GeoJSON geometry (Polygon) defining the AOI."
    )

    date1: date = Field(
        ...,
        description="T1 (earlier) date for analysis (YYYY-MM-DD)."
    )

    date2: date = Field(
        ...,
        description="T2 (later) date for analysis (YYYY-MM-DD)."
    )

    max_cloud_cover: float = Field(
        default=10.0,
        ge=0.0,
        le=100.0,
        description="Maximum acceptable cloud cover percentage.",
    )

    @field_validator("date2")
    @classmethod
    def date2_must_be_after_date1(
        cls,
        v: date,
        info,
    ) -> date:

        date1 = info.data.get("date1")

        if date1 and v <= date1:
            raise ValueError(
                f"date2 ({v}) must be after date1 ({date1})."
            )

        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "aoi": {
                    "type": "Polygon",
                    "coordinates": [[
                        [78.3, 17.2],
                        [78.6, 17.2],
                        [78.6, 17.5],
                        [78.3, 17.5],
                        [78.3, 17.2],
                    ]]
                },
                "date1": "2023-01-15",
                "date2": "2024-01-15",
                "max_cloud_cover": 10.0,
            }
        }
    }


# =============================================================================
# Response Schemas
# =============================================================================


class JobSubmitted(BaseModel):
    """Response after submitting an analysis job."""

    job_id: str
    status: JobStatus
    message: str


class JobStatusResponse(BaseModel):
    """Job status polling response."""

    job_id: str
    status: JobStatus
    progress_message: str = ""
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class AreaStatRow(BaseModel):
    """Single row of area change statistics."""

    class_id: int
    class_name: str
    t1_area_km2: float
    t2_area_km2: float
    t1_pct: float
    t2_pct: float
    change_km2: float
    change_pct: float


class RecommendationItem(BaseModel):
    """Single recommendation."""

    rule_id: str
    category: str
    severity: str
    title: str
    recommendation: str
    why: str
    priority: int


class AnalysisResultResponse(BaseModel):
    """
    Complete analysis result returned to the frontend.
    """

    job_id: str
    success: bool
    date1: str
    date2: str
    scene_t1_id: str = ""
    scene_t2_id: str = ""
    area_change: dict[str, Any] = {}
    temporal_stats: dict[str, Any] = {}
    statistics: dict[str, Any] = {}
    recommendations: list[dict[str, Any]] = []
    outputs: dict[str, str] = {}
    metadata: dict[str, Any] = {}
    error: Optional[str] = None


class BoundaryResponse(BaseModel):
    """HMR boundary GeoJSON response."""

    type: str
    features: list[dict[str, Any]]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: str
