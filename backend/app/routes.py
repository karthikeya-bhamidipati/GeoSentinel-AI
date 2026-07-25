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

from datetime import UTC, datetime
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
        timestamp=datetime.now(UTC).isoformat(),
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
    from backend.app.services import AnalysisService

    service = AnalysisService(queue=queue, orchestrator=orchestrator)
    job_id = await service.submit_analysis_job(request)

    logger.info(
        f"Analysis submitted: {job_id} "
        f"({request.date1} -> {request.date2})"
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
# Job History
# =============================================================================

@router.get(
    "/analysis/history",
    summary="Get analysis history",
    tags=["Analysis"],
)
async def get_analysis_history(
    queue: JobQueue = Depends(get_job_queue),
):
    """
    Retrieve all completed and failed jobs from the JobQueue.
    """
    jobs = []
    # queue._jobs is a dict mapping job_id to JobRecord
    for job_id, record in queue._jobs.items():
        data = record.to_dict()
        if data["status"] == "completed" and hasattr(record, "result"):
            data["result"] = record.result.to_dict() if hasattr(record.result, "to_dict") else record.result
        jobs.append(data)
        
    # Sort by created_at descending
    jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
    return JSONResponse(content={"jobs": jobs})

@router.delete(
    "/analysis/{job_id}",
    summary="Delete a job",
    tags=["Analysis"],
)
async def delete_job(
    job_id: str,
    queue: JobQueue = Depends(get_job_queue),
):
    """
    Delete a job from history and remove all associated output files.
    """
    # Return 404 if job is not in queue at all (never existed)
    if queue.get_status(job_id) is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
        )
    success = queue.delete_job(job_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to completely delete job {job_id}",
        )
    return JSONResponse(content={"message": f"Job {job_id} deleted successfully."})

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

from fastapi import WebSocket, WebSocketDisconnect
from backend.app.services import manager

@router.websocket("/analysis/{job_id}/ws")
async def websocket_job_status(
    websocket: WebSocket,
    job_id: str,
    queue: JobQueue = Depends(get_job_queue),
):
    """
    WebSocket endpoint for real-time job status.
    """
    await manager.connect(websocket, job_id)
    try:
        # Send current state immediately
        record = queue.get_status(job_id)
        if record:
            await websocket.send_json(record.to_dict())
            
        while True:
            # Wait for messages (keep connection alive)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)


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

    if record.status == JobStatus.QUEUED:
        raise HTTPException(
            status_code=202,
            detail="Analysis is queued.",
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

    if isinstance(result, dict):
        return AnalysisResultResponse(**result)
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


# =============================================================================
# Benchmark Results
# =============================================================================


@router.get(
    "/benchmark",
    summary="Get model benchmark results",
    tags=["Benchmark"],
)
async def get_benchmark_results():
    """
    Returns pre-computed model benchmark results.

    Compares U-Net (ResNet34) vs DeepLabV3+ on OSCD and S2Looking datasets.
    """

    results = [
        {
            "model": "Siamese U-Net Elite (Linear Attention)",
            "dataset": "OSCD (12-ch)",
            "iou": 0.378,
            "dice": 0.548,
            "f1": 0.5478,
            "precision": 0.561,
            "recall": 0.535,
            "accuracy": 0.892,
            "params": "31.2M",
            "is_best": True,
        },
        {
            "model": "Siamese U-Net Baseline (ResNet34)",
            "dataset": "OSCD (12-ch)",
            "iou": 0.331,
            "dice": 0.498,
            "f1": 0.4981,
            "precision": 0.512,
            "recall": 0.485,
            "accuracy": 0.874,
            "params": "24.4M",
            "is_best": False,
        },
        {
            "model": "DeepLabV3+ (ResNet50) — Semantic",
            "dataset": "OSCD (12-ch)",
            "iou": 0.442,
            "dice": 0.613,
            "f1": 0.613,
            "precision": 0.598,
            "recall": 0.629,
            "accuracy": 0.901,
            "params": "41.1M",
            "is_best": False,
        },
    ]

    return JSONResponse(content={"results": results})


# =============================================================================
# Settings (read-only — credential management is via .env)
# =============================================================================


@router.get(
    "/settings",
    summary="Get platform settings",
    tags=["System"],
)
async def get_settings():
    """
    Returns read-only platform settings for display in the frontend.
    Credentials are never exposed via API.
    """
    from src.utils.config import ProjectConfig

    config = ProjectConfig()

    project_info = config.project if isinstance(config.project, dict) else {}
    version = project_info.get("version", "1.0.0")

    inference_device = config.get("model", "inference", "device", default="cpu")

    return JSONResponse(content={
        "project": project_info,
        "version": version,
        "model_architecture": "deeplabv3plus",
        "device": inference_device,
    })

from pydantic import BaseModel

class CredentialsUpdate(BaseModel):
    cdse_email: str
    cdse_password: str

@router.post(
    "/settings/credentials",
    summary="Update credentials",
    tags=["System"],
)
async def update_credentials(creds: CredentialsUpdate):
    """
    Update the CDSE_USERNAME and CDSE_PASSWORD in the local .env file.
    """
    import dotenv
    import shutil
    from src.utils.paths import paths

    env_path = paths.PROJECT_ROOT / ".env"
    env_example_path = paths.PROJECT_ROOT / ".env.example"
    
    # Copy .env.example if .env doesn't exist
    if not env_path.exists():
        if env_example_path.exists():
            shutil.copy(str(env_example_path), str(env_path))
        else:
            env_path.touch()

    # Update the token
    dotenv.set_key(str(env_path), "CDSE_USERNAME", creds.cdse_email)
    dotenv.set_key(str(env_path), "CDSE_PASSWORD", creds.cdse_password)

    return JSONResponse(content={"message": "Credentials updated successfully."})
