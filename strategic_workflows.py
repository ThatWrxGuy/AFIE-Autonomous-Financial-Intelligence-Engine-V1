"""Strategic Intelligence Workflows for AFC3."""
import asyncio
import sys
sys.path.insert(0, '.')

from agents.strategic_intelligence_agent import StrategicIntelligenceAgent
from shared_memory.experiment_store import ExperimentStore
from compute.compute_engine import get_compute_engine

async def workflow_p():
    """Workflow P - Strategy Family Analysis"""
    print("="*50)
    print("WORKFLOW P: Strategy Family Analysis")
    print("="*50)
    
    # Setup
    es = ExperimentStore()
    agent = StrategicIntelligenceAgent()
    agent.set_experiment_store(es)
    
    # Create some experiments
    for i in range(10):
        exp_id = f"exp_{i}"
        es.create_experiment(exp_id, f"experiment_{i}")
        import random
        es.update_experiment(exp_id, validation_metrics={
            "sharpe_ratio": random.uniform(0.5, 1.5),
            "max_drawdown": random.uniform(0.05, 0.20),
            "family": random.choice(["momentum", "mean_reversion", "breakout"])
        })
        if i < 5:
            es.approve_strategy(exp_id, "Approved")
    
    # Run analysis
    print("\n[1/2] Analyzing strategy families...")
    result = await agent.rank_strategy_families({})
    print(f"  Ranked: {result['ranked_families']}")
    
    print("\n[2/2] Performance report...")
    perf = await agent.analyze_system_performance({})
    print(f"  Avg Sharpe: {perf['performance_report']['avg_sharpe']:.2f}")
    
    return {"status": "success", "families": result['ranked_families']}

async def workflow_q():
    """Workflow Q - Research Allocation Update"""
    print("="*50)
    print("WORKFLOW Q: Research Allocation Update")
    print("="*50)
    
    es = ExperimentStore()
    agent = StrategicIntelligenceAgent()
    agent.set_experiment_store(es)
    
    print("\n[1/1] Updating research priorities...")
    result = await agent.update_research_priorities({})
    print("  New allocations:")
    for p in result['priorities']:
        print(f"    {p['family']}: {p['allocation']:.1%}")
    
    return {"status": "success"}

async def workflow_r():
    """Workflow R - Compute Allocation Optimization"""
    print("="*50)
    print("WORKFLOW R: Compute Allocation Optimization")
    print("="*50)
    
    # Create some compute jobs
    engine = get_compute_engine()
    engine.register_worker("backtest", "w1")
    engine.register_worker("backtest", "w2")
    engine.register_worker("simulation", "w3")
    
    jobs = [{"type": "backtest", "payload": {"i": i}} for i in range(5)]
    engine.submit_batch(jobs)
    await asyncio.sleep(0.5)
    
    agent = StrategicIntelligenceAgent()
    
    print("\n[1/1] Optimizing compute allocation...")
    result = await agent.optimize_compute_allocation({})
    print("  New compute allocation:")
    for k, v in result['compute_allocation'].items():
        print(f"    {k}: {v:.1%}")
    
    return {"status": "success"}

async def main():
    print("Strategic Intelligence Workflows")
    print("="*50)
    
    result_p = await workflow_p()
    print(f"\nResult P: {result_p['status']}")
    
    result_q = await workflow_q()
    print(f"\nResult Q: {result_q['status']}")
    
    result_r = await workflow_r()
    print(f"\nResult R: {result_r['status']}")
    
    print("\n" + "="*50)
    print("Strategic workflows complete!")

if __name__ == "__main__":
    asyncio.run(main())
