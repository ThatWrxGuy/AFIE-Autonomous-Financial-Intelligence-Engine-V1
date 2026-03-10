"""Base Worker for AFC3 Distributed Compute."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
from compute.job_manager import JobManager, JobStatus, get_job_manager

class BaseWorker(ABC):
    def __init__(self, worker_id: str, job_types: list):
        self.worker_id = worker_id
        self.job_types = job_types
        self.job_manager = get_job_manager()
        self.running = False
        self.current_job = None
    
    @abstractmethod
    async def execute_job(self, job) -> Dict[str, Any]:
        pass
    
    async def run(self):
        self.running = True
        while self.running:
            job = self._fetch_job()
            if job:
                await self._process_job(job)
            await asyncio.sleep(0.5)
    
    def _fetch_job(self):
        for job_type in self.job_types:
            jobs = self.job_manager.get_jobs_by_status(JobStatus.QUEUED.value)
            for job in jobs:
                if job.job_type == job_type:
                    return job
        return None
    
    async def _process_job(self, job):
        self.current_job = job
        try:
            result = await self.execute_job(job)
            self.job_manager.update_status(job.job_id, JobStatus.COMPLETED.value, result=result)
        except Exception as e:
            self.job_manager.update_status(job.job_id, JobStatus.FAILED.value, error=str(e))
        finally:
            self.current_job = None
    
    def stop(self):
        self.running = False

class BacktestWorker(BaseWorker):
    async def execute_job(self, job) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {"status": "completed", "sharpe_ratio": 1.2, "max_drawdown": 0.12}

class SimulationWorker(BaseWorker):
    async def execute_job(self, job) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {"status": "completed", "iterations": 100, "success_rate": 0.65}

class LearningWorker(BaseWorker):
    async def execute_job(self, job) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {"status": "completed", "fitness_score": 75.5}

class PortfolioWorker(BaseWorker):
    async def execute_job(self, job) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {"status": "completed", "approved": True, "risk_score": 0.6}

class FeatureWorker(BaseWorker):
    async def execute_job(self, job) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {"status": "completed", "features_generated": 5}

def create_worker(worker_type: str, worker_id: str) -> BaseWorker:
    workers = {"backtest": BacktestWorker, "simulation": SimulationWorker,
               "learning": LearningWorker, "portfolio": PortfolioWorker, "feature": FeatureWorker}
    job_types = {"backtest": ["backtest"], "simulation": ["simulation"],
                 "learning": ["learning"], "portfolio": ["portfolio"], "feature": ["feature"]}
    return workers.get(worker_type, BaseWorker)(worker_id, job_types.get(worker_type, ["generic"]))
