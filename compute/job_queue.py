"""
Job Queue for AFC3 Distributed Compute Engine.

Priority-based job queue with worker dispatch.

Author: AFC3 Distributed Compute
"""

from typing import Dict, Any, List, Optional, Callable
from collections import deque
import asyncio

from compute.job_manager import JobManager, Job, JobStatus, JobType, get_job_manager


class JobQueue:
    """
    Distributed job queue with priority scheduling.
    """
    
    def __init__(self, job_manager: JobManager):
        self.job_manager = job_manager
        
        # Queue per job type
        self._queues: Dict[str, deque] = {}
        
        # Workers
        self._workers: Dict[str, Callable] = {}
        self._worker_types: Dict[str, List[str]] = {}  # worker_id -> [job_types]
        
        # Running
        self._dispatching = False
    
    def register_worker(self, worker_id: str, job_types: List[str]) -> None:
        """Register a worker for job types."""
        self._workers[worker_id] = None
        self._worker_types[worker_id] = job_types
    
    def unregister_worker(self, worker_id: str) -> None:
        """Unregister a worker."""
        if worker_id in self._workers:
            del self._workers[worker_id]
        if worker_id in self._worker_types:
            del self._worker_types[worker_id]
    
    def enqueue_job(self, job_id: str) -> bool:
        """Move job to queue."""
        job = self.job_manager.get_job(job_id)
        
        if not job:
            return False
        
        # Update status
        self.job_manager.update_status(job_id, JobStatus.QUEUED.value)
        
        # Add to queue
        job_type = job.job_type
        if job_type not in self._queues:
            self._queues[job_type] = deque()
        
        self._queues[job_type].append(job_id)
        
        return True
    
    def dequeue_job(self, job_type: str) -> Optional[str]:
        """Get next job from queue."""
        if job_type not in self._queues or not self._queues[job_type]:
            return None
        
        return self._queues[job_type].popleft()
    
    def get_queue_size(self, job_type: Optional[str] = None) -> int:
        """Get queue size."""
        if job_type:
            return len(self._queues.get(job_type, []))
        
        return sum(len(q) for q in self._queues.values())
    
    async def dispatch_jobs(self) -> int:
        """Dispatch jobs to available workers."""
        dispatched = 0
        
        # Get pending jobs sorted by priority
        pending = self.job_manager.get_pending_jobs()
        
        for job in pending:
            # Try to dispatch
            if self.dispatch_job(job.job_id):
                dispatched += 1
        
        return dispatched
    
    def dispatch_job(self, job_id: str) -> bool:
        """Dispatch a single job."""
        job = self.job_manager.get_job(job_id)
        
        if not job or job.status != JobStatus.PENDING.value:
            return False
        
        # Enqueue
        if not self.enqueue_job(job_id):
            return False
        
        # Mark as running
        self.job_manager.update_status(job_id, JobStatus.RUNNING.value)
        
        return True
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        stats = {"total": self.get_queue_size()}
        
        for job_type, queue in self._queues.items():
            stats[job_type] = len(queue)
        
        return stats


# Global queue
_job_queue = None


def get_job_queue() -> JobQueue:
    """Get global job queue."""
    global _job_queue
    if _job_queue is None:
        _job_queue = JobQueue(get_job_manager())
    return _job_queue
