"""Tests for Distributed Compute"""
import pytest
import asyncio
import sys
sys.path.insert(0, '.')

from compute.job_manager import JobManager, Job, JobStatus
from compute.compute_engine import ComputeEngine
from compute.workers.base_worker import create_worker, BacktestWorker

class TestJobManager:
    def test_submit_job(self):
        jm = JobManager()
        job_id = jm.submit_job("backtest", {"test": True})
        assert job_id is not None
        job = jm.get_job(job_id)
        assert job.job_type == "backtest"
    
    def test_job_status_update(self):
        jm = JobManager()
        job_id = jm.submit_job("test", {})
        jm.update_status(job_id, JobStatus.RUNNING.value)
        job = jm.get_job(job_id)
        assert job.status == JobStatus.RUNNING.value
    
    def test_job_stats(self):
        jm = JobManager()
        jm.submit_job("test", {})
        stats = jm.get_stats()
        assert stats["total"] == 1

class TestWorkers:
    @pytest.mark.asyncio
    async def test_create_worker(self):
        w = create_worker("backtest", "test_worker")
        assert w.worker_id == "test_worker"

class TestComputeEngine:
    @pytest.mark.asyncio
    async def test_submit_job(self):
        engine = ComputeEngine()
        job_id = engine.submit_job("backtest", {"test": True})
        assert job_id is not None
    
    @pytest.mark.asyncio
    async def test_submit_batch(self):
        engine = ComputeEngine()
        jobs = [{"type": "backtest", "payload": {"i": i}} for i in range(5)]
        job_ids = engine.submit_batch(jobs)
        assert len(job_ids) == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
