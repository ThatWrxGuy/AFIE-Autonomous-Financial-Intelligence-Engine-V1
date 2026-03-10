# AFIE Control Core: Integration Instructions for New AI Agents

This document provides detailed instructions for integrating the Alpha Discovery AI, Simulation & Backtesting AI, and Macro Intelligence AI agents into the AFIE Control Core. It covers agent registration, task scheduling, shared memory usage, strategy pipeline integration, and monitoring dashboard access.

## 1. Agent Registration

To make the new agents discoverable and usable by the AFIE Control Core, they must be registered with the `AgentOrchestrationManager`. This is typically done during the system's initialization phase.

**Steps:**

1.  **Import Agent Classes**: Ensure the new agent classes (`AlphaDiscoveryAgent`, `SimulationBacktestingAgent`, `MacroIntelligenceAgent`) are imported from their respective files within the `AFC3/agents/` directory.
2.  **Instantiate Agents**: Create instances of each agent.
3.  **Register with Manager**: Use the `register_agent` method of the `AgentOrchestrationManager` to add each agent to the system.

**Example Code Snippet (from `main.py` or an initialization script)**:

```python
from agent_orchestration.manager import AgentOrchestrationManager
from task_scheduler.scheduler import TaskScheduler
from shared_memory.short_term_memory import ShortTermMemory
from strategy_pipeline.manager import StrategyPipelineManager

from agents.alpha_discovery_agent import AlphaDiscoveryAgent
from agents.simulation_backtesting_agent import SimulationBacktestingAgent
from agents.macro_intelligence_agent import MacroIntelligenceAgent

# Initialize core components
orchestration_manager = AgentOrchestrationManager()
task_scheduler = TaskScheduler(orchestration_manager)
shared_memory = ShortTermMemory()
strategy_pipeline_manager = StrategyPipelineManager(task_scheduler, shared_memory)

# Register new agents
alpha_agent = AlphaDiscoveryAgent("AlphaDiscovery-1")
sim_backtest_agent = SimulationBacktestingAgent("SimBacktest-1")
macro_agent = MacroIntelligenceAgent("MacroIntel-1")

orchestration_manager.register_agent(alpha_agent)
orchestration_manager.register_agent(sim_backtest_agent)
orchestration_manager.register_agent(macro_agent)

# (Optional) Link pipeline manager to orchestration manager for task completion callbacks
orchestration_manager.pipeline_manager = strategy_pipeline_manager
```

## 2. Task Scheduling

Tasks for the new agents are scheduled using the `TaskScheduler`. Each task specifies the `agent_type`, the `action` to be performed, and any necessary `data`.

**Example Code Snippet**:

```python
import asyncio

async def schedule_example_tasks(task_scheduler):
    # Schedule a task for Alpha Discovery Agent
    alpha_task_id = await task_scheduler.schedule_task({
        "agent_type": "alpha_discovery",
        "action": "generate_candidate_signals",
        "data": {"market_context": "bullish"}
    }, priority=1)
    print(f"Alpha Discovery Task Scheduled: {alpha_task_id}")

    # Schedule a task for Simulation & Backtesting Agent
    sim_backtest_task_id = await task_scheduler.schedule_task({
        "agent_type": "simulation_backtesting",
        "action": "perform_historical_backtest",
        "data": {"strategy": {"id": "momentum_v1"}, "historical_data": {"source": "internal_db"}}
    }, priority=2)
    print(f"Simulation & Backtesting Task Scheduled: {sim_backtest_task_id}")

    # Schedule a task for Macro Intelligence Agent
    macro_task_id = await task_scheduler.schedule_task({
        "agent_type": "macro_intelligence",
        "action": "monitor_indicators",
        "data": {"indicators": ["interest_rates", "volatility_indexes"]}
    }, priority=3)
    print(f"Macro Intelligence Task Scheduled: {macro_task_id}")

# To run this:
# asyncio.run(schedule_example_tasks(task_scheduler))
```

## 3. Shared Memory Usage

The `ShortTermMemory` class provides a mechanism for agents to share transient data. Agents can `set`, `get`, and `delete` data using string keys.

**Example Code Snippet**:

```python
# Storing data
shared_memory.set("latest_alpha_signals", [{
    "id": "signal_1234",
    "type": "momentum",
    "strength": 0.85,
    "score": 92.5
}], ttl=300) # Data expires in 300 seconds

# Retrieving data
signals = shared_memory.get("latest_alpha_signals")
if signals:
    print(f"Retrieved from shared memory: {signals}")

# Deleting data
shared_memory.delete("old_data_key")
```

## 4. Strategy Pipeline Integration

The `StrategyPipelineManager` orchestrates sequences of tasks involving multiple agents. It allows defining a series of steps, where each step is a task for a specific agent. The output of one step can serve as input for the next.

**Example Workflow: Alpha Signal to Backtesting Pipeline**

This pipeline demonstrates generating alpha signals, scoring them, and then backtesting the top-performing signal.

```python
async def run_alpha_to_backtest_pipeline(pipeline_manager):
    pipeline_steps = [
        {
            "agent_type": "alpha_discovery",
            "action": "generate_candidate_signals",
            "data": {"market_focus": "tech_sector"}
        },
        {
            "agent_type": "alpha_discovery",
            "action": "score_signals",
            "data": {} # Data will be passed from previous step
        },
        {
            "agent_type": "simulation_backtesting",
            "action": "perform_historical_backtest",
            "data": {"historical_data": {"source": "internal_db"}} # Strategy will be derived from previous step
        }
    ]

    await pipeline_manager.create_pipeline("AlphaToBacktest", pipeline_steps)
    print("Running AlphaToBacktest pipeline...")
    result = await pipeline_manager.run_pipeline("AlphaToBacktest", {})
    print(f"Pipeline 'AlphaToBacktest' Result: {result}")

# To run this:
# asyncio.run(run_alpha_to_backtest_pipeline(strategy_pipeline_manager))
```

## 5. System Monitoring Dashboard

The `monitoring_dashboard/api/main.py` file has been updated to include new endpoints for accessing data generated by the new agents. These endpoints allow external systems or a frontend dashboard to retrieve relevant information.

**New Endpoints**:

*   `/agents`: Returns information about all registered agents.
*   `/alpha_signals`: Retrieves the latest alpha signals from shared memory.
*   `/backtest_results`: Retrieves the latest backtest results from shared memory.
*   `/macro_indicators`: Retrieves the latest macroeconomic indicators from shared memory.
*   `/regime_scores`: Retrieves the latest regime probability scores from shared memory.

To access these, ensure the FastAPI application is running. For example, if running locally on port 8000, you can access `http://localhost:8000/alpha_signals` to get the latest alpha signals.
