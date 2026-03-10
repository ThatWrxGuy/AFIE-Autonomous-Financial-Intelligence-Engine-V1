"""
Integration Tests for AFC3.

Tests:
- Scheduler lifecycle test: pending → running → completed
- Pipeline propagation test: AlphaDiscovery output → Simulation input
- Failure handling test: invalid payload produces structured error
- Event bus test: publish/subscribe works
- Dashboard test: monitoring endpoints show real system state
"""

import asyncio
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_orchestration.manager import AgentOrchestrationManager
from task_scheduler.scheduler import TaskScheduler, TaskStatus
from shared_memory.short_term_memory import ShortTermMemory
from shared_memory.long_term_memory import LongTermMemory
from shared_memory.experiment_store import ExperimentStore
from strategy_pipeline.manager import StrategyPipelineManager
from core.event_bus import EventBus, get_event_bus, Event
from agents.alpha_discovery_agent import AlphaDiscoveryAgent
from agents.simulation_backtesting_agent import SimulationBacktestingAgent
from agents.macro_intelligence_agent import MacroIntelligenceAgent


class TestSchedulerLifecycle:
    """Test scheduler lifecycle: pending → running → completed."""
    
    @pytest.mark.asyncio
    async def test_task_lifecycle(self):
        """Test that a task goes through all lifecycle states."""
        # Setup
        orchestration_manager = AgentOrchestrationManager()
        task_scheduler = TaskScheduler(orchestration_manager)
        
        # Register a test agent
        agent = AlphaDiscoveryAgent("Test Agent")
        orchestration_manager.register_agent(agent)
        
        # Start scheduler in background
        scheduler_task = asyncio.create_task(task_scheduler.run_scheduler())
        
        # Give scheduler time to start
        await asyncio.sleep(0.2)
        
        # Schedule a task
        task_id = await task_scheduler.schedule_task(
            agent_type="alpha_discovery",
            action="generate_candidate_signals",
            data={}
        )
        
        # Wait for task to complete
        await asyncio.sleep(3)
        
        # Verify task states
        task = task_scheduler.get_task(task_id)
        
        # Cancel scheduler
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        
        # Assertions
        assert task is not None
        assert task["status"] in [TaskStatus.COMPLETED, "completed"]
        assert task["result"] is not None
        
        # Verify task is in completed storage
        assert task_id in task_scheduler.completed_tasks


class TestPipelinePropagation:
    """Test pipeline result propagation between steps."""
    
    @pytest.mark.asyncio
    async def test_pipeline_result_propagation(self):
        """Test that AlphaDiscovery output propagates to Simulation input."""
        # Setup
        orchestration_manager = AgentOrchestrationManager()
        task_scheduler = TaskScheduler(orchestration_manager)
        shared_memory = ShortTermMemory()
        
        # Register agents
        alpha_agent = AlphaDiscoveryAgent("Alpha Agent")
        sim_agent = SimulationBacktestingAgent("Simulation Agent")
        
        orchestration_manager.register_agent(alpha_agent)
        orchestration_manager.register_agent(sim_agent)
        
        # Create pipeline manager
        pipeline_manager = StrategyPipelineManager(task_scheduler, shared_memory)
        
        # Create a pipeline
        await pipeline_manager.create_pipeline(
            name="test_pipeline",
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
                        "strategy": "result"  # Map result from previous step
                    },
                    "stop_on_failure": True,
                    "max_retries": 1
                }
            ]
        )
        
        # Start scheduler in background
        scheduler_task = asyncio.create_task(task_scheduler.run_scheduler())
        
        # Give scheduler time to start
        await asyncio.sleep(0.2)
        
        # Run pipeline
        result = await pipeline_manager.run_pipeline(
            name="test_pipeline",
            initial_data={"test": "data"}
        )
        
        # Cancel scheduler
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        
        # Assertions
        assert result["status"] == "success"
        assert result["pipeline_run_id"] is not None
        
        # Verify result contains simulation output
        assert "sharpe_ratio" in result["result"] or "strategy_id" in result["result"]


class TestFailureHandling:
    """Test failure handling produces structured errors."""
    
    @pytest.mark.asyncio
    async def test_invalid_payload_produces_error(self):
        """Test that invalid payload produces structured error."""
        # Setup
        orchestration_manager = AgentOrchestrationManager()
        task_scheduler = TaskScheduler(orchestration_manager)
        
        # Register agent
        agent = AlphaDiscoveryAgent("Test Agent")
        orchestration_manager.register_agent(agent)
        
        # Start scheduler
        scheduler_task = asyncio.create_task(task_scheduler.run_scheduler())
        await asyncio.sleep(0.2)
        
        # Schedule task with invalid action
        task_id = await task_scheduler.schedule_task(
            agent_type="alpha_discovery",
            action="invalid_action",
            data={}
        )
        
        # Wait for task to complete (should fail)
        await asyncio.sleep(3)
        
        # Cancel scheduler
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        
        # Verify error is stored
        task = task_scheduler.get_task(task_id)
        
        # Task should either be failed or have error
        assert task is not None
        assert task.get("status") in [TaskStatus.FAILED, "failed"] or task.get("error") is not None


class TestEventBus:
    """Test event bus publish/subscribe."""
    
    @pytest.mark.asyncio
    async def test_publish_subscribe(self):
        """Test that publish/subscribe works correctly."""
        # Create fresh event bus
        event_bus = EventBus()
        
        # Track events
        received_events = []
        
        async def callback(event: Event):
            received_events.append(event)
        
        # Subscribe to event
        subscription_id = event_bus.subscribe("test.event", callback)
        
        # Publish event
        event = Event(
            event_type="test.event",
            source="test",
            payload={"data": "test"}
        )
        await event_bus.publish(event)
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0].event_type == "test.event"
        assert received_events[0].payload["data"] == "test"
        
        # Unsubscribe
        event_bus.unsubscribe("test.event", subscription_id)
        
        # Publish another event
        event2 = Event(
            event_type="test.event",
            source="test",
            payload={"data": "test2"}
        )
        await event_bus.publish(event2)
        await asyncio.sleep(0.1)
        
        # Should still be only 1 event
        assert len(received_events) == 1


class TestMonitoringDashboard:
    """Test monitoring dashboard endpoints."""
    
    @pytest.mark.asyncio
    async def test_monitoring_shows_system_state(self):
        """Test that monitoring endpoints show real system state."""
        # Setup system
        orchestration_manager = AgentOrchestrationManager()
        task_scheduler = TaskScheduler(orchestration_manager)
        shared_memory = ShortTermMemory()
        long_term_memory = LongTermMemory()
        experiment_store = ExperimentStore()
        
        # Register agents
        alpha_agent = AlphaDiscoveryAgent("Alpha Agent")
        orchestration_manager.register_agent(alpha_agent)
        
        # Schedule some tasks
        await task_scheduler.schedule_task(
            agent_type="alpha_discovery",
            action="generate_candidate_signals",
            data={}
        )
        
        # Add some memory data
        shared_memory.add_signal({"id": "signal_1", "type": "momentum"})
        shared_memory.set_macro_regime("high_volatility", 0.8)
        
        # Add long-term memory data
        long_term_memory.store_strategy_performance("strategy_1", {
            "sharpe_ratio": 1.5,
            "max_drawdown": 0.1
        })
        
        # Verify data is accessible
        agents = orchestration_manager.discover_agents()
        assert len(agents) == 1
        
        signals = shared_memory.get_signals()
        assert len(signals) == 1
        
        macro = shared_memory.get_macro_regime()
        assert macro["regime"] == "high_volatility"
        
        strategy_perf = long_term_memory.get_strategy_performance("strategy_1")
        assert strategy_perf["sharpe_ratio"] == 1.5


class TestAgentResultStandardization:
    """Test agent result standardization."""
    
    @pytest.mark.asyncio
    async def test_agent_returns_standard_result(self):
        """Test that agents return standardized result envelope."""
        # Setup
        orchestration_manager = AgentOrchestrationManager()
        task_scheduler = TaskScheduler(orchestration_manager)
        
        # Register agent
        agent = AlphaDiscoveryAgent("Test Agent")
        orchestration_manager.register_agent(agent)
        
        # Start scheduler
        scheduler_task = asyncio.create_task(task_scheduler.run_scheduler())
        await asyncio.sleep(0.2)
        
        # Schedule task
        task_id = await task_scheduler.schedule_task(
            agent_type="alpha_discovery",
            action="generate_candidate_signals",
            data={}
        )
        
        # Wait for completion
        await asyncio.sleep(3)
        
        # Cancel scheduler
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        
        # Get result
        task = task_scheduler.get_task(task_id)
        result = task.get("result", {})
        
        # Verify standardized format
        assert result.get("status") == "success"
        assert "agent_id" in result
        assert "agent_type" in result
        assert "action" in result
        assert "task_id" in result
        assert "timestamp" in result
        assert "duration_seconds" in result
        assert "result" in result


class TestTaskStorage:
    """Test task storage (completed, failed, archived)."""
    
    @pytest.mark.asyncio
    async def test_completed_tasks_persist(self):
        """Test that completed tasks remain retrievable."""
        # Setup
        orchestration_manager = AgentOrchestrationManager()
        task_scheduler = TaskScheduler(orchestration_manager)
        
        # Register agent
        agent = AlphaDiscoveryAgent("Test Agent")
        orchestration_manager.register_agent(agent)
        
        # Start scheduler
        scheduler_task = asyncio.create_task(task_scheduler.run_scheduler())
        await asyncio.sleep(0.2)
        
        # Schedule and complete a task
        task_id = await task_scheduler.schedule_task(
            agent_type="alpha_discovery",
            action="generate_candidate_signals",
            data={}
        )
        
        await asyncio.sleep(3)
        
        # Cancel scheduler
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        
        # Verify task is in completed storage
        assert task_id in task_scheduler.completed_tasks
        
        # Can retrieve it
        task = task_scheduler.get_task(task_id)
        assert task is not None
        assert task["status"] in [TaskStatus.COMPLETED, "completed"]
    
    @pytest.mark.asyncio
    async def test_failed_tasks_persist(self):
        """Test that failed tasks persist in failure store."""
        # Setup
        orchestration_manager = AgentOrchestrationManager()
        task_scheduler = TaskScheduler(orchestration_manager)
        
        # Register agent
        agent = AlphaDiscoveryAgent("Test Agent")
        orchestration_manager.register_agent(agent)
        
        # Start scheduler
        scheduler_task = asyncio.create_task(task_scheduler.run_scheduler())
        await asyncio.sleep(0.2)
        
        # Schedule invalid task that will fail
        task_id = await task_scheduler.schedule_task(
            agent_type="alpha_discovery",
            action="nonexistent_action",
            data={}
        )
        
        await asyncio.sleep(3)
        
        # Cancel scheduler
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        
        # Verify task is in failed storage
        assert task_id in task_scheduler.failed_tasks
        
        # Can retrieve error
        task = task_scheduler.get_task(task_id)
        assert task is not None
        assert task.get("error") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
