"""
===============================================================================
GeoSentinel AI

Module:
    services.py

Description:
    Async job queue service.

    Manages background analysis jobs so the API can immediately
    return a job_id and the client can poll for completion.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

from backend.app.schemas import JobStatus
from src.utils.logger import logger


ProgressCallback = Callable[[str, str], None]


from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, job_id: str):
        await ws.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(ws)

    def disconnect(self, ws: WebSocket, job_id: str):
        if job_id in self.active_connections and ws in self.active_connections[job_id]:
            self.active_connections[job_id].remove(ws)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def broadcast(self, job_id: str, payload: dict):
        if job_id in self.active_connections:
            for ws in list(self.active_connections[job_id]):
                try:
                    await ws.send_json(payload)
                except Exception:
                    self.disconnect(ws, job_id)

manager = ConnectionManager()

class JobRecord:
    """
    Stores the state of a single analysis job.
    """

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        self.status = JobStatus.QUEUED
        self.progress_message = "Queued"
        self.progress_steps: list[str] = []
        self.created_at = datetime.now(UTC).isoformat()
        self.completed_at: Optional[str] = None
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the job record for API responses."""

        return {
            "job_id": self.job_id,
            "status": self.status.value if hasattr(self.status, "value") else self.status,
            "progress_message": self.progress_message,
            "progress_steps": self.progress_steps,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }

    def set_progress(self, step_id: str, message: str) -> None:
        """Update the progress message and completed step list."""

        self.progress_message = message

        if step_id and step_id not in self.progress_steps:
            self.progress_steps.append(step_id)
            
        if self._loop and manager.active_connections.get(self.job_id):
            asyncio.run_coroutine_threadsafe(
                manager.broadcast(self.job_id, self.to_dict()), 
                self._loop
            )


class JobQueue:
    """
    In-memory async job queue for analysis requests.

    Jobs are executed in the background using asyncio.
    The queue supports concurrent job limits to prevent resource exhaustion.

    Parameters
    ----------
    max_concurrent : int
        Maximum number of jobs running simultaneously.
    """

    def __init__(self, max_concurrent: int = 3) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._history_dir = Path("data/jobs")
        self._history_dir.mkdir(parents=True, exist_ok=True)
        self._load_history()

    def _load_history(self) -> None:
        try:
            import json
            for f in self._history_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    job = JobRecord(data["job_id"])
                    
                    # Convert to lowercase to match JobStatus enum ("completed", "failed", etc.)
                    raw_status = data.get("status", "completed")
                    job.status = JobStatus(raw_status.lower() if isinstance(raw_status, str) else "completed")
                    
                    job.progress_message = data.get("progress_message", "")
                    job.progress_steps = data.get("progress_steps", [])
                    job.created_at = data.get("created_at", "")
                    job.completed_at = data.get("completed_at")
                    job.result = data.get("result")
                    job.error = data.get("error")
                    self._jobs[job.job_id] = job
                except Exception as e:
                    logger.error(f"Failed to load job history {f}: {e}")
        except Exception as e:
            logger.error(f"Error reading history dir: {e}")

    async def _save_job(self, record: JobRecord) -> None:
        try:
            import json
            f = self._history_dir / f"{record.job_id}.json"
            data = record.to_dict()
            if record.result:
                data["result"] = record.result.to_dict() if hasattr(record.result, "to_dict") else record.result
            else:
                data["result"] = None
            content = json.dumps(data, indent=2)
            await asyncio.to_thread(f.write_text, content, "utf-8")
        except Exception as e:
            logger.error(f"Failed to save job {record.job_id}: {e}")

    def create_job(self) -> str:
        """
        Create a new job record and return its job_id.
        """

        job_id = str(uuid.uuid4())
        self._jobs[job_id] = JobRecord(job_id)

        logger.info(f"Job created: {job_id}")

        return job_id

    def get_status(self, job_id: str) -> Optional[JobRecord]:
        """
        Return the JobRecord for a job_id, or None if not found.
        """

        return self._jobs.get(job_id)

    def get_result(self, job_id: str) -> Optional[Any]:
        """Retrieve the final result of a job."""
        record = self._jobs.get(job_id)
        if record:
            return record.result
        return None

    def delete_job(self, job_id: str) -> bool:
        """Delete a job from the queue and remove its output files and history from disk."""
        from src.utils.paths import paths

        if job_id in self._jobs:
            del self._jobs[job_id]
        
        # Remove all output files that start with the job_id
        try:
            deleted_count = 0
            for d in [paths.FIGURES_DIR, paths.REPORTS_DIR, paths.OUTPUT_DIR]:
                if not d.exists():
                    continue
                for p in d.rglob(f"{job_id}_*"):
                    if p.is_file():
                        try:
                            p.unlink()
                            deleted_count += 1
                            logger.info(f"Deleted output file: {p}")
                        except Exception as e:
                            logger.warning(f"Failed to delete file {p}: {e}")
            logger.info(f"Deleted {deleted_count} output files for job {job_id}.")
        except Exception as e:
            logger.error(f"Failed to search for job output files for {job_id}: {e}")

        
        # Remove persistent history file
        history_file = self._history_dir / f"{job_id}.json"
        if history_file.exists():
            try:
                history_file.unlink()
            except Exception as e:
                logger.error(f"Failed to delete job history {history_file}: {e}")
                return False
                
        return True

    async def submit(
        self,
        job_id: str,
        coro: Awaitable[Any],
    ) -> None:
        """
        Submit an async coroutine as a background job.

        Parameters
        ----------
        job_id : str
        coro : Awaitable[Any]
            The analysis coroutine to run.
        """

        record = self._jobs.get(job_id)

        if record is None:
            logger.error(f"Job not found: {job_id}")
            return

        async def _run() -> None:
            async with self._semaphore:
                record.status = JobStatus.RUNNING
                record.progress_message = "Analysis running ..."

                logger.info(f"Job started: {job_id}")

                try:
                    result = await coro
                    # Store as dict in result
                    record.result = result.to_dict() if hasattr(result, "to_dict") else result
                    record.completed_at = datetime.now(UTC).isoformat()

                    result_success = getattr(result, "success", True)
                    result_error = getattr(result, "error", None)

                    if result_success:
                        record.status = JobStatus.COMPLETED
                        record.progress_message = "Completed"
                        logger.info(f"Job completed: {job_id}")
                    else:
                        record.status = JobStatus.FAILED
                        record.error = result_error or "Analysis failed."
                        record.progress_message = record.error
                        logger.error(
                            f"Job completed with failure result: {job_id} - "
                            f"{record.error}"
                        )

                except Exception as exc:
                    logger.error(f"Job failed: {job_id} - {exc}")
                    record.status = JobStatus.FAILED
                    record.error = str(exc)
                    record.progress_message = f"Failed: {exc}"
                    record.completed_at = datetime.now(UTC).isoformat()
                
                # Save terminal state
                await self._save_job(record)
                
                # Broadcast final state over WebSockets
                if manager.active_connections.get(job_id):
                    try:
                        await manager.broadcast(job_id, record.to_dict())
                    except Exception as e:
                        logger.error(f"Failed to broadcast final state for {job_id}: {e}")

        asyncio.create_task(_run())

    def active_count(self) -> int:
        """Return number of currently running jobs."""

        return sum(
            1 for record in self._jobs.values()
            if record.status == JobStatus.RUNNING
        )

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Remove completed jobs older than max_age_hours.

        Returns number of jobs cleaned.
        """

        cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
        to_remove: list[str] = []

        for job_id, record in self._jobs.items():
            if record.status not in (JobStatus.COMPLETED, JobStatus.FAILED):
                continue

            if record.completed_at is None:
                continue

            completed = datetime.fromisoformat(record.completed_at)

            if completed < cutoff:
                to_remove.append(job_id)

        for job_id in to_remove:
            self.delete_job(job_id)

        return len(to_remove)


_job_queue: Optional[JobQueue] = None


def get_job_queue() -> JobQueue:
    """Return the module-level JobQueue singleton."""

    global _job_queue

    if _job_queue is None:
        _job_queue = JobQueue(max_concurrent=3)

    return _job_queue


class AnalysisService:
    """
    Application service layer orchestrating the analysis workflow.
    """

    def __init__(self, queue: JobQueue, orchestrator: Any) -> None:
        self.queue = queue
        self.orchestrator = orchestrator

    async def submit_analysis_job(self, request: Any) -> str:
        """
        Create a job and submit it to the background queue.

        Returns
        -------
        str
            The created job ID.
        """

        job_id = self.queue.create_job()
        record = self.queue.get_status(job_id)

        def update_progress(step_id: str, message: str) -> None:
            if record is not None:
                record.set_progress(step_id, message)

        async def _run_analysis() -> Any:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None,
                self.orchestrator.run,
                job_id,
                request.aoi.model_dump(),
                str(request.date1),
                str(request.date2),
                request.max_cloud_cover,
                update_progress,
            )

        await self.queue.submit(job_id, _run_analysis())
        return job_id
