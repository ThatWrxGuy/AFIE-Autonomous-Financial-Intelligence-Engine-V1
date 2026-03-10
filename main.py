"""
AFIE Control Core (AFC3) - Main Entry Point

Initializes all system components:
- Agent Orchestration Manager
- Task Scheduler (hardened)
- Shared Memory (short-term, long-term)
- Experiment Store
- Strategy Pipeline Manager
- Monitoring Dashboard API
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_orchestration.manager import AgentOrchestrationManager
from task_scheduler.scheduler import TaskScheduler
from shared_memory.short_term_memory import ShortTermMemory
from shared_memory.long_term_memory import LongTermMemory
from shared_memory.experiment_store import ExperimentStore
from strategy_pipeline.manager import StrategyPipelineManager
from monitoring_dashboard.api.main import (
    set_orchestration_manager,
    set_task_scheduler,
    set_shared_memory,
    set_long_term_memory,
    set_experiment_store,
    set_pipeline_manager
)
from agents.alpha_discovery_agent import AlphaDiscoveryAgent
from agents.simulation_backtesting_agent import SimulationBacktestingAgent
from agents.macro_intelligence_agent import MacroIntelligenceAgent


class AFC3:
    """
    AFIE Control Core - Main application class.
    """
    
    def __init__(self):
        # Initialize core components
        self.orchestration_manager = AgentOrchestrationManager()
        self.task_scheduler = TaskScheduler(self.orchestration_manager)
        self.short_term_memory = ShortTermMemory()
        self.long_term_memory = LongTermMemory()
        self.experiment_store = ExperimentStore()
        self.pipeline_manager = StrategyPipelineManager(
            self.task_scheduler,
            self.short_term_memory
        )
        
        # Register agents
        self._register_default_agents()
        
        # Connect monitoring dashboard
        self._connect_monitoring()
        
        # Background tasks
        self.scheduler_task = None
    
    def _register_default_agents(self):
        """Register default system agents."""
        agents = [
            AlphaDiscoveryAgent("Alpha Discovery Agent"),
            SimulationBacktestingAgent("Simulation Agent"),
            MacroIntelligenceAgent("Macro Intelligence Agent")
        ]
        
        for agent in agents:
            self.orchestration_manager.register_agent(agent)
        
        print(f"Registered {len(agents)} agents")
    
    def _connect_monitoring(self):
        """Connect monitoring dashboard to system components."""
        set_orchestration_manager(self.orchestration_manager)
        set_task_scheduler(self.task_scheduler)
        set_shared_memory(self.short_term_memory)
        set_long_term_memory(self.long_term_memory)
        set_experiment_store(self.experiment_store)
        set_pipeline_manager(self.pipeline_manager)
    
    async def start(self):
        """Start the AFC3 system."""
        print("Starting AFIE Control Core (AFC3)...")
        
        # Start task scheduler
        self.scheduler_task = asyncio.create_task(self.task_scheduler.run_scheduler())
        
        # Give scheduler time to start
        await asyncio.sleep(0.5)
        
        print("AFC3 started successfully.")
        
        # Keep running
        try:
            await asyncio.Event().wait()  # Wait forever
        except asyncio.CancelledError:
            print("AFC3 shutting down...")
    
    async def stop(self):
        """Stop the AFC3 system."""
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        print("AFC3 stopped.")
    
    def get_status(self) -> dict:
        """Get system status."""
        return {
            "agents": len(self.orchestration_manager.agents),
            "active_tasks": len(self.task_scheduler.active_tasks),
            "completed_tasks": len(self.task_scheduler.completed_tasks),
            "failed_tasks": len(self.task_scheduler.failed_tasks),
            "pipelines": len(self.pipeline_manager.pipelines),
            "experiments": len(self.experiment_store.experiments)
        }


async def main():
    """Main entry point."""
    afc3 = AFC3()
    
    # Handle shutdown
    def signal_handler():
        print("\nReceived shutdown signal...")
        asyncio.create_task(afc3.stop())
    
    try:
        await afc3.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        await afc3.stop()


if __name__ == "__main__":
    asyncio.run(main())
