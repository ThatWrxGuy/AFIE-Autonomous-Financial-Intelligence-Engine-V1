"""Learning Workflows for AFC3."""
import asyncio
import sys
sys.path.insert(0, '.')

from agent_orchestration.manager import AgentOrchestrationManager
from task_scheduler.scheduler import TaskScheduler
from shared_memory.short_term_memory import ShortTermMemory
from shared_memory.long_term_memory import LongTermMemory
from shared_memory.experiment_store import ExperimentStore
from core.event_bus import get_event_bus
from agents.alpha_discovery_agent import AlphaDiscoveryAgent
from agents.strategy_evolution_agent import StrategyEvolutionAgent
from core.strategy_genome import StrategyGenome

class LearningWorkflows:
    def __init__(self):
        self.om = AgentOrchestrationManager()
        self.ts = TaskScheduler(self.om)
        self.stm = ShortTermMemory()
        self.ltm = LongTermMemory()
        self.es = ExperimentStore()
        self.ev = get_event_bus()
        
        self.alpha = AlphaDiscoveryAgent("Alpha")
        self.evo = StrategyEvolutionAgent("Evolution")
        self.evo.set_experiment_store(self.es)
        self.evo.set_long_term_memory(self.ltm)
        
        for a in [self.alpha, self.evo]:
            self.om.register_agent(a)
        
        self.st = None
    
    async def start(self):
        self.st = asyncio.create_task(self.ts.run_scheduler())
        await asyncio.sleep(0.3)
    
    async def stop(self):
        if self.st:
            self.st.cancel()
            try: await self.st
            except: pass

async def workflow_h():
    """Strategy Evolution"""
    wf = LearningWorkflows()
    await wf.start()
    
    # Create seed experiments
    for i in range(3):
        eid = f"exp_{i}"
        wf.es.create_experiment(eid, f"exp_{i}")
        wf.es.update_experiment(eid, validation_metrics={"sharpe_ratio": 0.5 + i*0.3})
    
    # Run evolution
    result = await wf.evo.run_evolution_cycle({})
    print(f"Workflow H: {result.get('status', 'done')}")
    
    await wf.stop()
    return result

async def workflow_i():
    """Full Learning Loop"""
    wf = LearningWorkflows()
    await wf.start()
    
    # Create genome and mutate
    seed = StrategyGenome.create_seed("momentum")
    result = await wf.evo.mutate_strategy_parameters({"genome": seed.to_dict(), "num_variants": 2})
    print(f"Workflow I: Generated {result['variants_generated']} variants")
    
    await wf.stop()
    return result

async def main():
    print("="*50)
    print("WORKFLOW H: Strategy Evolution")
    print("="*50)
    await workflow_h()
    
    print("\n" + "="*50)
    print("WORKFLOW I: Full Learning Loop")
    print("="*50)
    await workflow_i()
    
    print("\nLearning workflows complete!")

if __name__ == "__main__":
    asyncio.run(main())
