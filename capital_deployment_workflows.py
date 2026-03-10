"""
Capital Deployment Workflows for AFC3.

This module provides example workflows for the capital deployment layer.

Workflow D: Approved Strategy to Allocation
Workflow E: Allocation to Execution Simulation  
Workflow F: Risk Rejection
Workflow G: Full End-to-End

Author: AFC3 Capital Deployment Layer
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_orchestration.manager import AgentOrchestrationManager
from task_scheduler.scheduler import TaskScheduler
from shared_memory.short_term_memory import ShortTermMemory
from shared_memory.long_term_memory import LongTermMemory
from shared_memory.experiment_store import ExperimentStore
from strategy_pipeline.manager import StrategyPipelineManager
from core.event_bus import EventBus, get_event_bus
from agents.alpha_discovery_agent import AlphaDiscoveryAgent
from agents.simulation_backtesting_agent import SimulationBacktestingAgent
from agents.macro_intelligence_agent import MacroIntelligenceAgent
from agents.portfolio_intelligence_agent import PortfolioIntelligenceAgent
from agents.execution_intelligence_agent import ExecutionIntelligenceAgent


class CapitalDeploymentWorkflows:
    """Example capital deployment workflows for AFC3."""
    
    def __init__(self, initial_capital: float = 100000.0):
        # Initialize system components
        self.orchestration_manager = AgentOrchestrationManager()
        self.task_scheduler = TaskScheduler(self.orchestration_manager)
        self.short_term_memory = ShortTermMemory()
        self.long_term_memory = LongTermMemory()
        self.experiment_store = ExperimentStore()
        self.event_bus = get_event_bus()
        
        # Initialize pipeline manager
        self.pipeline_manager = StrategyPipelineManager(
            self.task_scheduler, 
            self.short_term_memory
        )
        
        # Initialize agents
        self.portfolio_agent = PortfolioIntelligenceAgent(
            "Portfolio Intelligence Agent",
            initial_capital=initial_capital
        )
        self.execution_agent = ExecutionIntelligenceAgent(
            "Execution Intelligence Agent",
            execution_mode="simulation"
        )
        
        # Connect agents to memory and event bus
        self.portfolio_agent.set_experiment_store(self.experiment_store)
        self.portfolio_agent.set_short_term_memory(self.short_term_memory)
        self.portfolio_agent.set_long_term_memory(self.long_term_memory)
        self.portfolio_agent.set_event_bus(self.event_bus)
        
        self.execution_agent.set_short_term_memory(self.short_term_memory)
        self.execution_agent.set_long_term_memory(self.long_term_memory)
        self.execution_agent.set_event_bus(self.event_bus)
        
        # Register agents
        self._register_agents()
        
        # Setup capital deployment pipeline
        self._setup_capital_deployment_pipeline()
        
        # Start scheduler
        self.scheduler_task = None
    
    def _register_agents(self):
        """Register all agents."""
        # Research agents
        alpha_agent = AlphaDiscoveryAgent("Alpha Discovery Agent")
        sim_agent = SimulationBacktestingAgent("Simulation Agent")
        macro_agent = MacroIntelligenceAgent("Macro Intelligence Agent")
        
        # Capital deployment agents
        self.orchestration_manager.register_agent(alpha_agent)
        self.orchestration_manager.register_agent(sim_agent)
        self.orchestration_manager.register_agent(macro_agent)
        self.orchestration_manager.register_agent(self.portfolio_agent)
        self.orchestration_manager.register_agent(self.execution_agent)
        
        print("Agents registered:")
        print("  Research:")
        print(f"    - {alpha_agent.name} ({alpha_agent.agent_type})")
        print(f"    - {sim_agent.name} ({sim_agent.agent_type})")
        print(f"    - {macro_agent.name} ({macro_agent.agent_type})")
        print("  Capital Deployment:")
        print(f"    - {self.portfolio_agent.name} ({self.portfolio_agent.agent_type})")
        print(f"    - {self.execution_agent.name} ({self.execution_agent.agent_type})")
    
    def _setup_capital_deployment_pipeline(self):
        """Setup the capital deployment pipeline."""
        # This pipeline: Research → Portfolio → Execution
        asyncio.create_task(
            self.pipeline_manager.create_pipeline(
                name="approved_strategy_to_execution_simulation",
                steps=[
                    {
                        "name": "PortfolioValidation",
                        "agent_type": "portfolio_intelligence",
                        "action": "validate_strategy_for_allocation",
                        "input_map": {"strategy": "initial_data"},
                        "stop_on_failure": True,
                        "max_retries": 1
                    },
                    {
                        "name": "PortfolioAllocation",
                        "agent_type": "portfolio_intelligence",
                        "action": "generate_order_intents",
                        "input_map": {},
                        "stop_on_failure": True,
                        "max_retries": 1
                    },
                    {
                        "name": "ExecutionValidation",
                        "agent_type": "execution_intelligence",
                        "action": "validate_order_intents",
                        "input_map": {"order_intents": "previous_result.order_intents"},
                        "stop_on_failure": True,
                        "max_retries": 1
                    },
                    {
                        "name": "OrderGeneration",
                        "agent_type": "execution_intelligence",
                        "action": "generate_orders",
                        "input_map": {"order_intents": "previous_result.valid_intents"},
                        "stop_on_failure": True,
                        "max_retries": 1
                    },
                    {
                        "name": "SimulatedExecution",
                        "agent_type": "execution_intelligence",
                        "action": "simulate_execution",
                        "input_map": {"orders": "previous_result.orders"},
                        "stop_on_failure": True,
                        "max_retries": 1
                    }
                ]
            )
        )
    
    async def start(self):
        """Start the workflow system."""
        self.scheduler_task = asyncio.create_task(self.task_scheduler.run_scheduler())
        await asyncio.sleep(0.5)
        print("\nCapital Deployment system started.\n")
    
    async def stop(self):
        """Stop the workflow system."""
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        print("\nCapital Deployment system stopped.")
    
    async def workflow_d_strategy_to_allocation(self, strategy_data: dict = None) -> dict:
        """
        Workflow D: Approved Strategy to Allocation
        
        Steps:
        1. Portfolio Intelligence validates metrics
        2. Position sizing performed
        3. Allocation stored
        """
        print("=" * 60)
        print("WORKFLOW D: Strategy → Allocation")
        print("=" * 60)
        
        # Default strategy data
        if strategy_data is None:
            strategy_data = {
                "strategy_id": f"strategy_{uuid.uuid4().hex[:8]}",
                "pipeline_run_id": f"pipeline_{uuid.uuid4().hex[:8]}",
                "approval_status": "approved",
                "signal_payload": {"asset": "SPY", "signal": "buy"},
                "expected_return": 0.15,
                "sharpe_ratio": 1.2,
                "max_drawdown": 0.12,
                "regime_score": 0.7,
                "confidence": 0.85
            }
        
        print(f"Input Strategy: {strategy_data['strategy_id']}")
        
        # Validate strategy
        validation_result = await self.portfolio_agent.validate_strategy_for_allocation({
            "strategy": strategy_data
        })
        
        print(f"Validation: {'PASSED' if validation_result['is_valid'] else 'FAILED'}")
        
        if not validation_result['is_valid']:
            print(f"Errors: {validation_result['validation_errors']}")
            return {"status": "rejected", "validation": validation_result}
        
        # Score strategy
        score_result = await self.portfolio_agent.score_strategy_for_allocation({
            "strategy": strategy_data
        })
        print(f"Strategy Score: {score_result['composite_score']:.1f}/100")
        
        # Calculate position size
        position_result = await self.portfolio_agent.calculate_position_size({
            "strategy": strategy_data,
            "target_weight": 0.15
        })
        print(f"Position Size: ${position_result['target_notional']:.2f}")
        
        # Generate order intents
        order_intent_result = await self.portfolio_agent.generate_order_intents({
            "allocation_decisions": [{
                "strategy_id": strategy_data["strategy_id"],
                "approved": True,
                "target_weight": position_result["target_weight"],
                "target_notional": position_result["target_notional"]
            }],
            "default_asset": "SPY",
            "order_type": "market"
        })
        
        print(f"Order Intents Generated: {order_intent_result['total_intents']}")
        
        return {
            "status": "success",
            "validation": validation_result,
            "score": score_result,
            "position": position_result,
            "order_intents": order_intent_result
        }
    
    async def workflow_e_allocation_to_execution(self, order_intents: list = None) -> dict:
        """
        Workflow E: Allocation to Execution Simulation
        
        Steps:
        1. Order intents generated
        2. Execution orders created
        3. Simulated fills returned
        4. Execution summary stored
        """
        print("=" * 60)
        print("WORKFLOW E: Allocation → Execution")
        print("=" * 60)
        
        # Default order intents
        if order_intents is None:
            order_intents = [{
                "order_intent_id": f"intent_{uuid.uuid4().hex[:8]}",
                "asset": "SPY",
                "side": "buy",
                "quantity": 100,
                "order_type": "market",
                "urgency": "medium",
                "strategy_id": "test_strategy"
            }]
        
        print(f"Input Order Intents: {len(order_intents)}")
        
        # Validate order intents
        validation_result = await self.execution_agent.validate_order_intents({
            "order_intents": order_intents
        })
        
        print(f"Validation: {validation_result['validated']} valid, {validation_result['rejected']} rejected")
        
        if validation_result['validated'] == 0:
            return {"status": "rejected", "validation": validation_result}
        
        # Generate orders
        orders_result = await self.execution_agent.generate_orders({
            "order_intents": validation_result["valid_intents"]
        })
        
        print(f"Orders Generated: {orders_result['total_orders']}")
        
        # Simulate execution
        execution_result = await self.execution_agent.simulate_execution({
            "orders": orders_result["orders"]
        })
        
        print(f"Orders Executed: {execution_result['orders_executed']}")
        print(f"Fill Reports: {len(execution_result['fill_reports'])}")
        
        # Get execution summary
        if order_intents:
            summary_result = await self.execution_agent.summarize_execution_quality({
                "order_intent_id": order_intents[0]["order_intent_id"]
            })
            print(f"Execution Summary: {summary_result.get('summary_id', 'N/A')}")
        
        return {
            "status": "success",
            "validation": validation_result,
            "orders": orders_result,
            "execution": execution_result
        }
    
    async def workflow_f_risk_rejection(self, strategy_data: dict) -> dict:
        """
        Workflow F: Risk Rejection
        
        Approved strategy candidate arrives
        → Portfolio Intelligence rejects due to drawdown/leverage/concentration issue
        → rejection stored and event emitted
        """
        print("=" * 60)
        print("WORKFLOW F: Risk Rejection")
        print("=" * 60)
        
        print(f"Input Strategy: {strategy_data.get('strategy_id', 'unknown')}")
        
        # Validate - this should fail due to bad metrics
        validation_result = await self.portfolio_agent.validate_strategy_for_allocation({
            "strategy": strategy_data
        })
        
        if validation_result['is_valid']:
            print("⚠️ Strategy unexpectedly passed validation")
            return {"status": "unexpected_pass", "validation": validation_result}
        
        print(f"✗ Strategy REJECTED")
        print(f"Reason: {validation_result['validation_errors']}")
        
        return {
            "status": "rejected",
            "validation": validation_result,
            "rejection_reason": validation_result['validation_errors']
        }
    
    async def workflow_g_full_end_to_end(self, strategy_data: dict = None) -> dict:
        """
        Workflow G: Full End-to-End
        
        Research-approved strategy
        → allocation decision
        → order generation
        → execution simulation
        → portfolio state updated
        → monitoring endpoints reflect changes
        """
        print("=" * 60)
        print("WORKFLOW G: Full End-to-End")
        print("=" * 60)
        
        # Default strategy
        if strategy_data is None:
            strategy_data = {
                "strategy_id": f"strategy_{uuid.uuid4().hex[:8]}",
                "pipeline_run_id": f"pipeline_{uuid.uuid4().hex[:8]}",
                "approval_status": "approved",
                "signal_payload": {"asset": "SPY", "signal": "buy"},
                "expected_return": 0.15,
                "sharpe_ratio": 1.2,
                "max_drawdown": 0.12,
                "regime_score": 0.7,
                "confidence": 0.85
            }
        
        print(f"Starting full pipeline for: {strategy_data['strategy_id']}")
        
        # Step 1: Portfolio validation
        print("\n[1/4] Portfolio Validation...")
        validation_result = await self.portfolio_agent.validate_strategy_for_allocation({
            "strategy": strategy_data
        })
        
        if not validation_result['is_valid']:
            return {"status": "failed_at_validation", "error": validation_result['validation_errors']}
        
        # Step 2: Generate order intents
        print("[2/4] Generating Order Intents...")
        score_result = await self.portfolio_agent.score_strategy_for_allocation({
            "strategy": strategy_data
        })
        
        position_result = await self.portfolio_agent.calculate_position_size({
            "strategy": strategy_data,
            "target_weight": 0.15
        })
        
        order_intent_result = await self.portfolio_agent.generate_order_intents({
            "allocation_decisions": [{
                "strategy_id": strategy_data["strategy_id"],
                "approved": True,
                "target_weight": position_result["target_weight"],
                "target_notional": position_result["target_notional"]
            }],
            "default_asset": "SPY",
            "order_type": "market"
        })
        
        # Step 3: Execute orders
        print("[3/4] Executing Orders...")
        orders_result = await self.execution_agent.generate_orders({
            "order_intents": order_intent_result["order_intents"]
        })
        
        execution_result = await self.execution_agent.simulate_execution({
            "orders": orders_result["orders"]
        })
        
        # Step 4: Update portfolio state
        print("[4/4] Updating Portfolio State...")
        
        # Get current portfolio state
        portfolio_state = self.portfolio_agent.get_portfolio_state()
        
        # Update with fills
        for fill_data in execution_result.get("fill_reports", []):
            self.portfolio_agent.update_portfolio_state({
                "asset": "SPY",
                "filled_quantity": fill_data.get("filled_quantity", 0),
                "average_fill_price": fill_data.get("average_fill_price", 0)
            })
        
        updated_portfolio = self.portfolio_agent.get_portfolio_state()
        
        print(f"\n✓ Full pipeline completed!")
        print(f"Portfolio State:")
        print(f"  Cash Available: ${updated_portfolio['cash_available']:.2f}")
        print(f"  Allocated Capital: ${updated_portfolio['allocated_capital']:.2f}")
        print(f"  Leverage: {updated_portfolio['leverage']:.2f}x")
        
        return {
            "status": "success",
            "validation": validation_result,
            "allocation": position_result,
            "orders": orders_result,
            "execution": execution_result,
            "portfolio_state": updated_portfolio
        }
    
    async def run_all_workflows(self):
        """Run all example workflows."""
        await self.start()
        
        try:
            # Workflow D: Strategy to Allocation
            print("\n" + "=" * 60)
            print("RUNNING WORKFLOW D")
            print("=" * 60)
            result_d = await self.workflow_d_strategy_to_allocation()
            await asyncio.sleep(0.5)
            
            # Workflow E: Allocation to Execution
            print("\n" + "=" * 60)
            print("RUNNING WORKFLOW E")
            print("=" * 60)
            result_e = await self.workflow_e_allocation_to_execution()
            await asyncio.sleep(0.5)
            
            # Workflow F: Risk Rejection (with bad strategy)
            print("\n" + "=" * 60)
            print("RUNNING WORKFLOW F (Risk Rejection)")
            print("=" * 60)
            bad_strategy = {
                "strategy_id": "bad_strategy_001",
                "pipeline_run_id": "pipeline_bad",
                "approval_status": "approved",
                "signal_payload": {},
                "expected_return": 0.05,
                "sharpe_ratio": 0.1,  # Too low
                "max_drawdown": 0.35,  # Too high
                "regime_score": 0.3,
                "confidence": 0.4
            }
            result_f = await self.workflow_f_risk_rejection(bad_strategy)
            await asyncio.sleep(0.5)
            
            # Workflow G: Full End-to-End
            print("\n" + "=" * 60)
            print("RUNNING WORKFLOW G (Full End-to-End)")
            print("=" * 60)
            result_g = await self.workflow_g_full_end_to_end()
            
            # Summary
            print("\n" + "=" * 60)
            print("WORKFLOW SUMMARY")
            print("=" * 60)
            print(f"Workflow D (Strategy→Allocation): {result_d['status']}")
            print(f"Workflow E (Allocation→Execution): {result_e['status']}")
            print(f"Workflow F (Risk Rejection): {result_f['status']}")
            print(f"Workflow G (Full E2E): {result_g['status']}")
            
            print("\n" + "=" * 60)
            print("PORTFOLIO STATE")
            print("=" * 60)
            portfolio = self.portfolio_agent.get_portfolio_state()
            print(f"Cash Available: ${portfolio['cash_available']:.2f}")
            print(f"Allocated Capital: ${portfolio['allocated_capital']:.2f}")
            print(f"Current Positions: {len(portfolio['current_positions'])}")
            print(f"Leverage: {portfolio['leverage']:.2f}x")
            
        finally:
            await self.stop()


async def main():
    """Run capital deployment workflows."""
    workflows = CapitalDeploymentWorkflows(initial_capital=100000.0)
    await workflows.run_all_workflows()


if __name__ == "__main__":
    asyncio.run(main())
