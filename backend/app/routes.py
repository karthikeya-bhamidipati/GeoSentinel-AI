"""
===============================================================================
GeoSentinel AI

Module:
    routes.py

Description:
    FastAPI API router with all endpoint definitions.

    Endpoints:
    GET  /health              — Health check
    POST /analysis            — Submit analysis job
    GET  /analysis/{job_id}   — Poll job status
    GET  /analysis/{job_id}/result — Fetch completed results
    GET  /boundary            — HMR boundary GeoJSON
    GET  /download/{job_id}/{file_type} — Download report files

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from backend.app.schemas import (
    AnalysisRequest,
    AnalysisResultResponse,
    BoundaryResponse,
    HealthResponse,
    JobStatus,
    JobStatusResponse,
    JobSubmitted,
)
from backend.app.dependencies import get_orchestrator
from backend.app.services import get_job_queue, JobQueue
from src.orchestration.orchestrator import Orchestrator
from src.utils.io import read_geojson
from src.utils.logger import logger
from src.utils.paths import paths


router = APIRouter()


# =============================================================================
# Health
# =============================================================================


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"],
)
async def health_check() -> HealthResponse:
    """
    Returns API health status.
    """

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
    )


# =============================================================================
# HMR Boundary
# =============================================================================


@router.get(
    "/boundary",
    summary="Get HMR boundary GeoJSON",
    tags=["Geospatial"],
)
async def get_hmr_boundary():
    """
    Returns the Hyderabad Metropolitan Region boundary as GeoJSON.
    This boundary is used to validate AOI inputs.
    """

    boundary_path = (
        paths.PROJECT_ROOT
        / "data"
        / "reference"
        / "hmr_boundary.geojson"
    )

    if not boundary_path.exists():
        raise HTTPException(
            status_code=404,
            detail="HMR boundary file not found.",
        )

    data = read_geojson(boundary_path)

    return JSONResponse(content=data)


# =============================================================================
# Submit Analysis
# =============================================================================


@router.post(
    "/analysis",
    response_model=JobSubmitted,
    status_code=202,
    summary="Submit analysis job",
    tags=["Analysis"],
)
async def submit_analysis(
    request: AnalysisRequest,
    queue: JobQueue = Depends(get_job_queue),
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> JobSubmitted:
    """
    Submit a new land cover analysis job.

    Returns immediately with a job_id.
    Poll GET /analysis/{job_id} for status.
    """

    job_id = queue.create_job()

    # Build async wrapper around the synchronous orchestrator.run()
    async def _run_analysis():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            orchestrator.run,
            job_id,
            request.aoi.model_dump(),
            str(request.date1),
            str(request.date2),
        )

    await queue.submit(job_id, _run_analysis())

    logger.info(
        f"Analysis submitted: {job_id} "
        f"({request.date1} → {request.date2})"
    )

    return JobSubmitted(
        job_id=job_id,
        status=JobStatus.QUEUED,
        message=(
            f"Analysis job {job_id} submitted. "
            f"Poll GET /api/v1/analysis/{job_id} for status."
        ),
    )


# =============================================================================
# Job Status
# =============================================================================


@router.get(
    "/analysis/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
    tags=["Analysis"],
)
async def get_job_status(
    job_id: str,
    queue: JobQueue = Depends(get_job_queue),
) -> JobStatusResponse:
    """
    Poll the status of a submitted analysis job.
    """

    record = queue.get_status(job_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
        )

    return JobStatusResponse(**record.to_dict())


# =============================================================================
# Analysis Result
# =============================================================================


@router.get(
    "/analysis/{job_id}/result",
    response_model=AnalysisResultResponse,
    summary="Get analysis result",
    tags=["Analysis"],
)
async def get_analysis_result(
    job_id: str,
    queue: JobQueue = Depends(get_job_queue),
) -> AnalysisResultResponse:
    """
    Retrieve the full result of a completed analysis.
    Returns 404 if job not found or 202 if still running.
    """

    record = queue.get_status(job_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
        )

    if record.status == JobStatus.RUNNING:
        raise HTTPException(
            status_code=202,
            detail="Analysis still running.",
        )

    if record.status == JobStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {record.error}",
        )

    result = queue.get_result(job_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Result not available.",
        )

    return AnalysisResultResponse(**result.to_dict())


# =============================================================================
# File Download
# =============================================================================


@router.get(
    "/download/{job_id}/{file_type}",
    summary="Download report file",
    tags=["Download"],
)
async def download_report(
    job_id: str,
    file_type: str,
    queue: JobQueue = Depends(get_job_queue),
) -> FileResponse:
    """
    Download a report file for a completed analysis.

    file_type options: 'pdf', 'csv', 'mask_png', 'ndvi_delta_png'
    """

    result = queue.get_result(job_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No result for job {job_id}",
        )

    outputs = result.outputs if hasattr(result, "outputs") else {}

    if isinstance(result, dict):
        outputs = result.get("outputs", {})

    file_path_str = outputs.get(file_type)

    if not file_path_str:
        raise HTTPException(
            status_code=404,
            detail=f"File type '{file_type}' not found for job {job_id}",
        )

    file_path = Path(file_path_str)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Report file not found on disk.",
        )

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
    )
