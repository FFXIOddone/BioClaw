from __future__ import annotations

from bioscaffold.types import Job, JobResult


class Ribosome:
    def __init__(self, *, allowed_job_types: set[str]) -> None:
        self._allowed_job_types = set(allowed_job_types)

    def can_execute(self, job: Job) -> bool:
        job_type = str(job.payload.get("type", ""))
        return job_type in self._allowed_job_types

    def execute(self, job: Job) -> JobResult:
        job_type = str(job.payload.get("type", ""))
        if job_type not in self._allowed_job_types:
            return JobResult(
                job_id=job.job_id,
                succeeded=False,
                output={},
                reason=f"job type {job_type} is not allowed",
            )
        if job_type == "echo":
            return JobResult(
                job_id=job.job_id,
                succeeded=True,
                output={"result": job.payload.get("value")},
                reason="completed",
            )
        return JobResult(job.job_id, False, {}, f"job type {job_type} has no executor")
