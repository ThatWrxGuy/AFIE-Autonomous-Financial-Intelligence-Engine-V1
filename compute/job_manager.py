"""
Job Manager for AFC3 Distributed Compute Engine.

Centralized job management system.

Author: AFC3 Distributed Compute
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class JobStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(Enum):
    BACKTEST = "backtest"
    SIMULATION = "simulation"
    LEARNING = "learning"
    PORTFOLIO = "portfolio"
    FEATURE = "feature"
    GENERIC = "generic"


@dataclass
class Job:
    """
    Distributed job.
    
    Fields:
    - job_id: Unique identifier
    - job_type: Type of job
    - payload: Job data
    - priority: Job priority (1-10, 10 is highest)
    - status: Job status
    - created_at: Creation timestamp
    - started_at: Start timestamp
    - completed_at: Completion timestamp
    - retries: Retry count
    - result: Job result
    - error: Error message
    """
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_type: str = JobType.GENERIC.value
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5
    status: str = JobStatus.PENDING.value
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retries: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "payload": self.payload,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retries": self.retries,
            "result": self.result,
            "error": self.error
        }


class JobManager:
    """
    Centralized job management system.
    
    Handles job lifecycle, retries, and storage.
    """
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        
        # Job storage
        self._jobs: Dict[str, Job] = {}
        
        # Status indices
        self._by_status: Dict[str, List[str]] = {
            JobStatus.PENDING.value: [],
            JobStatus.QUEUED.value: [],
            JobStatus.RUNNING.value: [],
            JobStatus.COMPLETED.value: [],
            JobStatus.FAILED.value: [],
            JobStatus.CANCELLED.value: []
        }
    
    def submit_job(
        self,
        job_type: str,
        payload: Dict[str, Any],
        priority: int = 5
    ) -> str:
        """Submit a new job."""
        job = Job(
            job_type=job_type,
            payload=payload,
            priority=priority
        )
        
        self._jobs[job.job_id] = job
        self._by_status[JobStatus.PENDING.value].append(job.job_id)
        
        return job.job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self._jobs.get(job_id)
    
    def update_status(
        self,
        job_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> bool:
        """Update job status."""
        job = self._jobs.get(job_id)
        
        if not job:
            return False
        
        # Remove from old status
        old_status = job.status
        if job.job_id in self._by_status[old_status]:
            self._by_status[old_status].remove(job.job_id)
        
        # Update status
        job.status = status
        
        if status == JobStatus.RUNNING.value and not job.started_at:
            job.started_at = datetime.utcnow().isoformat()
        
        if status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
            job.completed_at = datetime.utcnow().isoformat()
        
        if result is not None:
            job.result = result
        
        if error is not None:
            job.error = error
        
        # Add to new status
        self._by_status[status].append(job.job_id)
        
        return True
    
    def get_jobs_by_status(self, status: str) -> List[Job]:
        """Get all jobs with given status."""
        job_ids = self._by_status.get(status, [])
        return [self._jobs[jid] for jid in job_ids if jid in self._jobs]
    
    def get_pending_jobs(self) -> List[Job]:
        """Get pending jobs sorted by priority."""
        pending = self.get_jobs_by_status(JobStatus.PENDING.value)
        return sorted(pending, key=lambda j: j.priority, reverse=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get job statistics."""
        return {
            "total": len(self._jobs),
            "pending": len(self._by_status[JobStatus.PENDING.value]),
            "queued": len(self._by_status[JobStatus.QUEUED.value]),
            "running": len(self._by_status[JobStatus.RUNNING.value]),
            "completed": len(self._by_status[JobStatus.COMPLETED.value]),
            "failed": len(self._by_status[JobStatus.FAILED.value]),
            "cancelled": len(self._by_status[JobStatus.CANCELLED.value])
        }
    
    def retry_job(self, job_id: str) -> bool:
        """Retry a failed job."""
        job = self._jobs.get(job_id)
        
        if not job or job.status != JobStatus.FAILED.value:
            return False
        
        if job.retries >= self.max_retries:
            return False
        
        job.retries += 1
        job.status = JobStatus.PENDING.value
        job.error = None
        
        # Move to pending
        self._by_status[JobStatus.FAILED.value].remove(job_id)
        self._by_status[JobStatus.PENDING.value].append(job_id)
        
        return True
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        job = self._jobs.get(job_id)
        
        if not job or job.status in [JobStatus.COMPLETED.value, JobStatus.CANCELLED.value]:
            return False
        
        job.status = JobStatus.CANCELLED.value
        job.completed_at = datetime.utcnow().isoformat()
        
        # Remove from current status
        if job.job_id in self._by_status.get(job.status, []):
            self._by_status[job.status].remove(job_id)
        
        self._by_status[JobStatus.CANCELLED.value].append(job_id)
        
        return True


# Global job manager
_job_manager = None


def get_job_manager() -> JobManager:
    """Get global job manager."""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager
