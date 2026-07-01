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
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from src.backend.app.schemas import JobStatus
from src.utils.logger import logger


class JobRecord:
    """
    Stores the state of a single analysis job.
    """

    def __init__(self, job_id: str) -> None:

        self.job_id = job_id
        self.status = JobStatus.QUEUED
        self.progress_message = "Queued"
        self.created_at = datetime.utcnow().isoformat()
        self.completed_at: Optional[str] = None
        self.result: Optional[Any] = None
        self.error: Optional[str] = None

    def to_dict(self) -> dict:

        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "progress_message": self.progress_message,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }


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

    # ------------------------------------------------------------------

    def create_job(self) -> str:
        """
        Create a new job record and return its job_id.
        """

        job_id = str(uuid.uuid4())
        self._jobs[job_id] = JobRecord(job_id)

        logger.info(f"Job created: {job_id}")

        return job_id

    # ------------------------------------------------------------------

    def get_status(self, job_id: str) -> Optional[JobRecord]:
        """
        Return the JobRecord for a job_id, or None if not found.
        """

        return self._jobs.get(job_id)

    # ------------------------------------------------------------------

    def get_result(self, job_id: str) -> Optional[Any]:
        """
        Return the result of a completed job, or None.
        """

        record = self._jobs.get(job_id)

        if record and record.status == JobStatus.COMPLETED:
            return record.result

        return None

    # ------------------------------------------------------------------

    async def submit(
        self,
        job_id: str,
        coro,
    ) -> None:
        """
        Submit an async coroutine as a background job.

        Parameters
        ----------
        job_id : str
        coro : coroutine
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
                    record.result = result
                    record.status = JobStatus.COMPLETED
                    record.progress_message = "Completed"
                    record.completed_at = datetime.utcnow().isoformat()
                    logger.info(f"Job completed: {job_id}")

                except Exception as exc:
                    logger.error(f"Job failed: {job_id} — {exc}")
                    record.status = JobStatus.FAILED
                    record.error = str(exc)
                    record.progress_message = f"Failed: {exc}"
                    record.completed_at = datetime.utcnow().isoformat()

        asyncio.create_task(_run())

    # ------------------------------------------------------------------

    def active_count(self) -> int:
        """Return number of currently running jobs."""

        return sum(
            1 for r in self._jobs.values()
            if r.status == JobStatus.RUNNING
        )

    # ------------------------------------------------------------------

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Remove completed jobs older than max_age_hours.

        Returns number of jobs cleaned.
        """

        from datetime import timezone, timedelta

        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        to_remove = []

        for job_id, record in self._jobs.items():
            if record.status in (
                JobStatus.COMPLETED,
                JobStatus.FAILED,
            ):
                if record.completed_at:
                    completed = datetime.fromisoformat(record.completed_at)
                    if completed < cutoff:
                        to_remove.append(job_id)

        for job_id in to_remove:
            del self._jobs[job_id]

        return len(to_remove)


# Module-level singleton
_job_queue: Optional[JobQueue] = None


def get_job_queue() -> JobQueue:
    """Return the module-level JobQueue singleton."""

    global _job_queue

    if _job_queue is None:
        _job_queue = JobQueue(max_concurrent=3)

    return _job_queue
