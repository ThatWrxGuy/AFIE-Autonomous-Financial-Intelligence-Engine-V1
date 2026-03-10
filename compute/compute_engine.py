"""
Compute Engine for AFC3 Distributed Compute.

Unified interface for distributed job execution.

Author: AFC3 Distributed Compute
"""

from typing import Dict, Any, List, Optional
import asyncio

from compute.job_manager import JobManager, JobStatus, get_job_manager
from compute.job_queue import JobQueue, get_job_queue
from compute.workers.base_worker import create_worker, BaseWorker


class ComputeEngine:
    """
    Distributed Compute Engine.
    
    Orchestrates workers, jobs, and result aggregation.
    """
    
    def __init__(self):
        self.job_manager = get_job_manager()
        self.job_queue = get_job_queue()
        
        # Workers
        self._workers: Dict[str, BaseWorker] = {}
        self._worker_tasks: Dict[str, asyncio.Task] = {}
        
        # Results storage
        self._results: Dict[str, Dict[str, Any]] = {}
    
    def submit_job(
        self,
        job_type: str,
        payload: Dict[str, Any],
        priority: int = 5
    ) -> str:
        """Submit a job."""
        job_id = self.job_manager.submit_job(job_type, payload, priority)
        
        # Queue for execution
        self.job_queue.enqueue_job(job_id)
        
        return job_id
    
    def submit_batch(
        self,
        jobs: List[Dict[str, Any]]
    ) -> List[str]:
        """Submit multiple jobs."""
        job_ids = []
        
        for job in jobs:
            job_id = self.submit_job(
                job.get("type", "generic"),
                job.get("payload", {}),
                job.get("priority", 5)
            )
            job_ids.append(job_id)
        
        return job_ids
    
    async def wait_for_results(
        self,
        job_ids: List[str],
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """Wait for jobs to complete."""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check if all done
            completed = []
            failed = []
            
            for job_id in job_ids:
                job = self.job_manager.get_job(job_id)
                if not job:
                    continue
                
                if job.status == JobStatus.COMPLETED.value:
                    completed.append(job_id)
                elif job.status == JobStatus.FAILED.value:
                    failed.append(job_id)
            
            # All done?
            if len(completed) + len(failed) >= len(job_ids):
                break
            
            # Timeout?
            if asyncio.get_event_loop().time() - start_time > timeout:
                break
            
            await asyncio.sleep(0.1)
        
        # Collect results
        results = {}
        for job_id in job_ids:
            job = self.job_manager.get_job(job_id)
            if job:
                results[job_id] = {
                    "status": job.status,
                    "result": job.result,
                    "error": job.error
                }
        
        return results
    
    def register_worker(self, worker_type: str, worker_id: str) -> None:
        """Register a worker."""
        if worker_id in self._workers:
            return
        
        worker = create_worker(worker_type, worker_id)
        self._workers[worker_id] = worker
        
        # Start worker
        task = asyncio.create_task(worker.run())
        self._worker_tasks[worker_id] = task
    
    def unregister_worker(self, worker_id: str) -> None:
        """Unregister a worker."""
        if worker_id in self._workers:
            self._workers[worker_id].stop()
            del self._workers[worker_id]
        
        if worker_id in self._worker_tasks:
            self._worker_tasks[worker_id].cancel()
            del self._worker_tasks[worker_id]
    
    def get_worker_status(self) -> Dict[str, Any]:
        """Get worker status."""
        return {
            "total_workers": len(self._workers),
            "workers": {
                wid: {
                    "job_type": w.job_types,
                    "current_job": w.current_job.job_id if w.current_job else None,
                    "running": w.running
                }
                for wid, w in self._workers.items()
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get compute engine stats."""
        return {
            "jobs": self.job_manager.get_stats(),
            "queue": self.job_queue.get_queue_stats(),
            "workers": self.get_worker_status()
        }


# Global compute engine
_compute_engine = None


def get_compute_engine() -> ComputeEngine:
    """Get global compute engine."""
    global _compute_engine
    if _compute_engine is None:
        _compute_engine = ComputeEngine()
    return _compute_engine


# Convenience functions
def submit_backtest(payload: Dict[str, Any]) -> str:
    """Submit backtest job."""
    return get_compute_engine().submit_job("backtest", payload)


def submit_simulation(payload: Dict[str, Any]) -> str:
    """Submit simulation job."""
    return get_compute_engine().submit_job("simulation", payload)


def submit_learning(payload: Dict[str, Any]) -> str:
    """Submit learning job."""
    return get_compute_engine().submit_job("learning", payload)
