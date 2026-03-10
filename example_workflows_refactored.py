"""
Example Research Workflows for AFC3.

Workflow A: AlphaDiscovery → SimulationBacktest → results stored in experiment store
Workflow B: SimulationBacktest → MacroEvaluation → strategy approved or rejected
Workflow C: invalid strategy → simulation failure → rejection recorded
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_orchestration.manager import AgentOrchestrationManager
from task_scheduler.scheduler import TaskScheduler
from shared_memory.short_term_memory import ShortTermMemory
from shared_memory.long_term_memory import LongTermMemory
from shared_memory.experiment_store import ExperimentStore
from strategy_pipeline.manager import StrategyPipelineManager
from agents.alpha_discovery_agent import AlphaDiscoveryAgent
from agents.simulation_backtesting_agent import SimulationBacktestingAgent
from agents.macro_intelligence_agent import MacroIntelligenceAgent


class ResearchWorkflows:
    """Example research workflows for AFC3."""
    
    def __init__(self):
        # Initialize system components
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
        self._register_agents()
        
        # Start scheduler
        self.scheduler_task = None
    
    def _register_agents(self):
        """Register all agents."""
        alpha_agent = AlphaDiscoveryAgent("Alpha Discovery Agent")
        sim_agent = SimulationBacktestingAgent("Simulation Agent")
        macro_agent = MacroIntelligenceAgent("Macro Intelligence Agent")
        
        self.orchestration_manager.register_agent(alpha_agent)
        self.orchestration_manager.register_agent(sim_agent)
        self.orchestration_manager.register_agent(macro_agent)
        
        print("Agents registered:")
        for agent in [alpha_agent, sim_agent, macro_agent]:
            print(f"  - {agent.name} ({agent.agent_type})")
    
    async def start(self):
        """Start the workflow system."""
        self.scheduler_task = asyncio.create_task(self.task_scheduler.run_scheduler())
        await asyncio.sleep(0.5)  # Give scheduler time to start
        print("\nWorkflow system started.\n")
    
    async def stop(self):
        """Stop the workflow system."""
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        print("\nWorkflow system stopped.")
    
    async def workflow_a_alpha_to_simulation(self) -> dict:
        """
        Workflow A: AlphaDiscovery → SimulationBacktest → results stored in experiment store
        
        This workflow:
        1. Generates candidate signals via AlphaDiscovery
        2. Runs simulation backtest on the signals
        3. Stores results in experiment store
        
        Returns:
            Workflow result dictionary
        """
        print("=" * 60)
        print("WORKFLOW A: AlphaDiscovery → SimulationBacktest")
        print("=" * 60)
        
        # Create pipeline
        pipeline_name = "workflow_a"
        await self.pipeline_manager.create_pipeline(
            name=pipeline_name,
            steps=[
                {
                    "name": "AlphaDiscovery",
                    "agent_type": "alpha_discovery",
                    "action": "generate_candidate_signals",
                    "input_map": {},
                    "stop_on_failure": True,
                    "max_retries": 1
                },
                {
                    "name": "SimulationBacktest",
                    "agent_type": "simulation_backtesting",
                    "action": "perform_historical_backtest",
                    "input_map": {
                        "strategy": "result"  # Map from AlphaDiscovery result
                    },
                    "stop_on_failure": True,
                    "max_retries": 1
                }
            ]
        )
        
        # Run pipeline
        result = await self.pipeline_manager.run_pipeline(
            name=pipeline_name,
            initial_data={"market": "US_EQUITY", "universe": "TOP500"}
        )
        
        # Store in experiment store
        if result.get("status") == "success":
            pipeline_run_id = result.get("pipeline_run_id")
            self.experiment_store.create_experiment(pipeline_run_id, "workflow_a")
            self.experiment_store.update_experiment(
                pipeline_run_id,
                final_result=result.get("result"),
                execution_duration=result.get("execution_duration")
            )
            
            # Store strategy performance in long-term memory
            strategy_result = result.get("result", {})
            if "sharpe_ratio" in strategy_result:
                self.long_term_memory.store_strategy_performance(
                    f"strategy_{pipeline_run_id[:8]}",
                    strategy_result
                )
            
            # Store signals in short-term memory
            for signal in strategy_result.get("signals", []):
                self.short_term_memory.add_signal(signal)
        
        print(f"\nWorkflow A completed: {result.get('status')}")
        print(f"Pipeline Run ID: {result.get('pipeline_run_id')}")
        print(f"Execution Duration: {result.get('execution_duration')}s")
        
        return result
    
    async def workflow_b_simulation_to_macro(self) -> dict:
        """
        Workflow B: SimulationBacktest → MacroEvaluation → strategy approved or rejected
        
        This workflow:
        1. Runs simulation backtest
        2. Evaluates with macro intelligence
        3. Approves or rejects strategy based on validation
        
        Returns:
            Workflow result dictionary
        """
        print("=" * 60)
        print("WORKFLOW B: SimulationBacktest → MacroEvaluation")
        print("=" * 60)
        
        # Create pipeline
        pipeline_name = "workflow_b"
        await self.pipeline_manager.create_pipeline(
            name=pipeline_name,
            steps=[
                {
                    "name": "SimulationBacktest",
                    "agent_type": "simulation_backtesting",
                    "action": "perform_historical_backtest",
                    "input_map": {},
                    "stop_on_failure": True,
                    "max_retries": 1
                },
                {
                    "name": "MacroEvaluation",
                    "agent_type": "macro_intelligence",
                    "action": "detect_regime_changes",
                    "input_map": {},
                    "stop_on_failure": True,
                    "max_retries": 1
                },
                {
                    "name": "Validation",
                    "agent_type": "macro_intelligence",
                    "action": "generate_regime_probability_scores",
                    "input_map": {},
                    "stop_on_failure": True,
                    "max_retries": 1
                }
            ]
        )
        
        # Run pipeline
        result = await self.pipeline_manager.run_pipeline(
            name=pipeline_name,
            initial_data={
                "strategy": {"id": "test_strategy", "type": "momentum"},
                "market_conditions": "normal"
            }
        )
        
        # Evaluate and approve/reject strategy
        if result.get("status") == "success":
            pipeline_run_id = result.get("pipeline_run_id")
            
            # Create experiment record
            self.experiment_store.create_experiment(pipeline_run_id, "workflow_b")
            
            # Get simulation results
            sim_result = result.get("result", {})
            sharpe = sim_result.get("sharpe_ratio", 0)
            drawdown = sim_result.get("max_drawdown", 1)
            
            # Get macro regime
            regime_result = result.get("result", {})
            regime = regime_result.get("detected_regime", "unknown")
            
            # Validation logic
            validation_metrics = {
                "sharpe_ratio": sharpe,
                "max_drawdown": drawdown,
                "macro_regime": regime,
                "approved": False
            }
            
            # Simple approval criteria
            if sharpe > 1.0 and drawdown < 0.2:
                reason = f"Strategy approved: sharpe={sharpe:.2f}, drawdown={drawdown:.2f}"
                self.experiment_store.approve_strategy(pipeline_run_id, reason)
                validation_metrics["approved"] = True
                print(f"\n✓ Strategy APPROVED: {reason}")
            else:
                reason = f"Strategy rejected: sharpe={sharpe:.2f}, drawdown={drawdown:.2f}"
                self.experiment_store.reject_strategy(pipeline_run_id, reason)
                print(f"\n✗ Strategy REJECTED: {reason}")
            
            # Update experiment with validation
            self.experiment_store.update_experiment(
                pipeline_run_id,
                validation_metrics=validation_metrics,
                final_result=result.get("result"),
                execution_duration=result.get("execution_duration")
            )
        
        print(f"\nWorkflow B completed: {result.get('status')}")
        print(f"Pipeline Run ID: {result.get('pipeline_run_id')}")
        
        return result
    
    async def workflow_c_failure_handling(self) -> dict:
        """
        Workflow C: invalid strategy → simulation failure → rejection recorded
        
        This workflow:
        1. Attempts to run simulation with invalid data
        2. Handles failure gracefully
        3. Records rejection in experiment store
        
        Returns:
            Workflow result dictionary
        """
        print("=" * 60)
        print("WORKFLOW C: Failure Handling (invalid strategy)")
        print("=" * 60)
        
        # Create pipeline
        pipeline_name = "workflow_c"
        await self.pipeline_manager.create_pipeline(
            name=pipeline_name,
            steps=[
                {
                    "name": "AlphaDiscovery",
                    "agent_type": "alpha_discovery",
                    "action": "generate_candidate_signals",
                    "input_map": {},
                    "stop_on_failure": True,
                    "max_retries": 1
                },
                {
                    "name": "SimulationBacktest",
                    "agent_type": "simulation_backtesting",
                    "action": "perform_historical_backtest",
                    "input_map": {
                        "strategy": "result"  # This will fail if result is invalid
                    },
                    "stop_on_failure": True,
                    "max_retries": 1
                }
            ]
        )
        
        # Run pipeline with intentionally invalid initial data
        # (the simulation backtest expects a specific strategy format)
        result = await self.pipeline_manager.run_pipeline(
            name=pipeline_name,
            initial_data={
                "invalid_strategy": True,  # This will cause issues
                "broken_data": "intentionally_broken"
            }
        )
        
        # Record rejection in experiment store
        pipeline_run_id = result.get("pipeline_run_id", "unknown")
        
        if result.get("status") == "failed":
            self.experiment_store.create_experiment(pipeline_run_id, "workflow_c")
            self.experiment_store.reject_strategy(
                pipeline_run_id,
                reason=f"Pipeline failed: {result.get('error', 'Unknown error')}"
            )
            self.experiment_store.update_experiment(
                pipeline_run_id,
                final_result=result,
                execution_duration=result.get("execution_duration", 0),
                error=result.get("error")
            )
            print(f"\n✗ Workflow C FAILED (as expected)")
            print(f"Failure reason: {result.get('error')}")
        else:
            print(f"\n⚠ Workflow C unexpectedly succeeded (should have failed)")
        
        print(f"Pipeline Run ID: {pipeline_run_id}")
        
        return result
    
    async def run_all_workflows(self):
        """Run all example workflows."""
        await self.start()
        
        try:
            # Run Workflow A
            result_a = await self.workflow_a_alpha_to_simulation()
            await asyncio.sleep(1)
            
            # Run Workflow B
            result_b = await self.workflow_b_simulation_to_macro()
            await asyncio.sleep(1)
            
            # Run Workflow C (failure case)
            result_c = await self.workflow_c_failure_handling()
            await asyncio.sleep(1)
            
            # Print summary
            print("\n" + "=" * 60)
            print("WORKFLOW SUMMARY")
            print("=" * 60)
            
            print("\nExperiment Store Statistics:")
            stats = self.experiment_store.get_stats()
            print(f"  Total experiments: {stats['total_experiments']}")
            print(f"  Approved: {stats['approved_count']}")
            print(f"  Rejected: {stats['rejected_count']}")
            
            print("\nApproved Strategies:")
            approved = self.experiment_store.get_approved_strategies()
            for a in approved:
                print(f"  - {a['pipeline_run_id']}: {a.get('validation_metrics', {}).get('approval_reason', '')}")
            
            print("\nRejected Strategies:")
            rejected = self.experiment_store.get_rejected_strategies()
            for r in rejected:
                print(f"  - {r['pipeline_run_id']}: {r.get('validation_metrics', {}).get('rejection_reason', '')}")
            
            print("\nLong-term Memory (Strategy Performance):")
            strategies = self.long_term_memory.list_strategies()
            for s in strategies:
                print(f"  - {s['strategy_id']}: sharpe={s.get('sharpe_ratio', 'N/A')}")
            
            print("\nShort-term Memory (Recent Signals):")
            signals = self.short_term_memory.get_signals()
            for sig in signals:
                print(f"  - {sig.get('id', 'unknown')}: {sig.get('type', 'unknown')}")
            
        finally:
            await self.stop()


async def main():
    """Run example workflows."""
    workflows = ResearchWorkflows()
    await workflows.run_all_workflows()


if __name__ == "__main__":
    asyncio.run(main())
