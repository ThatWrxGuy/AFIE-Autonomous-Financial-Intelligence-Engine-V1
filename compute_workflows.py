"""Distributed Compute Workflows for AFC3."""
import asyncio
import sys
sys.path.insert(0, '.')

from compute.compute_engine import get_compute_engine

async def workflow_m():
    """Workflow M - Distributed Backtesting"""
    print("="*50)
    print("WORKFLOW M: Distributed Backtesting")
    print("="*50)
    
    engine = get_compute_engine()
    
    # Register workers
    print("\n[1/4] Registering workers...")
    engine.register_worker("backtest", "worker_1")
    engine.register_worker("backtest", "worker_2")
    engine.register_worker("backtest", "worker_3")
    print("  3 workers registered")
    
    # Submit batch jobs
    print("\n[2/4] Submitting 10 backtest jobs...")
    jobs = [{"type": "backtest", "payload": {"strategy": f"s_{i}"}} for i in range(10)]
    job_ids = engine.submit_batch(jobs)
    print(f"  Submitted {len(job_ids)} jobs")
    
    # Wait for completion
    print("\n[3/4] Waiting for completion...")
    results = await engine.wait_for_results(job_ids, timeout=10.0)
    completed = sum(1 for r in results.values() if r["status"] == "completed")
    print(f"  Completed: {completed}/{len(job_ids)}")
    
    # Get stats
    print("\n[4/4] Engine stats:")
    stats = engine.get_stats()
    print(f"  Jobs: {stats['jobs']}")
    
    return {"status": "success", "completed": completed}

async def workflow_n():
    """Workflow N - Mutation Batch Evaluation"""
    print("="*50)
    print("WORKFLOW N: Mutation Batch Evaluation")
    print("="*50)
    
    engine = get_compute_engine()
    
    # Register workers
    print("\n[1/3] Registering learning workers...")
    engine.register_worker("learning", "learn_worker_1")
    engine.register_worker("learning", "learn_worker_2")
    
    # Submit mutations
    print("\n[2/3] Submitting 20 mutation evaluations...")
    jobs = [{"type": "learning", "payload": {"mutation": f"m_{i}"}} for i in range(20)]
    job_ids = engine.submit_batch(jobs)
    print(f"  Submitted {len(job_ids)} jobs")
    
    # Wait
    print("\n[3/3] Waiting for evaluation...")
    results = await engine.wait_for_results(job_ids, timeout=10.0)
    completed = sum(1 for r in results.values() if r["status"] == "completed")
    
    return {"status": "success", "completed": completed}

async def workflow_o():
    """Workflow O - Portfolio Scenario Testing"""
    print("="*50)
    print("WORKFLOW O: Portfolio Scenario Testing")
    print("="*50)
    
    engine = get_compute_engine()
    
    # Register workers
    print("\n[1/3] Registering portfolio workers...")
    engine.register_worker("portfolio", "port_worker_1")
    engine.register_worker("portfolio", "port_worker_2")
    
    # Submit scenarios
    print("\n[2/3] Submitting 15 portfolio scenarios...")
    jobs = [{"type": "portfolio", "payload": {"scenario": f"s_{i}"}} for i in range(15)]
    job_ids = engine.submit_batch(jobs)
    print(f"  Submitted {len(job_ids)} jobs")
    
    # Wait
    print("\n[3/3] Waiting for results...")
    results = await engine.wait_for_results(job_ids, timeout=10.0)
    completed = sum(1 for r in results.values() if r["status"] == "completed")
    
    return {"status": "success", "completed": completed}

async def main():
    print("="*50)
    print("Distributed Compute Workflows")
    print("="*50)
    
    result_m = await workflow_m()
    print(f"\nResult M: {result_m['status']}")
    
    result_n = await workflow_n()
    print(f"\nResult N: {result_n['status']}")
    
    result_o = await workflow_o()
    print(f"\nResult O: {result_o['status']}")
    
    print("\n" + "="*50)
    print("Compute workflows complete!")

if __name__ == "__main__":
    asyncio.run(main())
