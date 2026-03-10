import asyncio
from agent_orchestration.manager import AgentOrchestrationManager
from task_scheduler.scheduler import TaskScheduler
from shared_memory.short_term_memory import ShortTermMemory
from strategy_pipeline.manager import StrategyPipelineManager

from agents.alpha_discovery_agent import AlphaDiscoveryAgent
from agents.simulation_backtesting_agent import SimulationBacktestingAgent
from agents.macro_intelligence_agent import MacroIntelligenceAgent
from agents.example_agents import QuantResearchAgent, ExecutionAgent

async def main():
    print("Initializing AFIE Control Core components...")
    # Initialize core components
    orchestration_manager = AgentOrchestrationManager()
    task_scheduler = TaskScheduler(orchestration_manager)
    shared_memory = ShortTermMemory()
    strategy_pipeline_manager = StrategyPipelineManager(task_scheduler, shared_memory)

    # Link pipeline manager to orchestration manager for task completion callbacks
    orchestration_manager.pipeline_manager = strategy_pipeline_manager

    # Register agents
    alpha_agent = AlphaDiscoveryAgent("AlphaDiscovery-1")
    sim_backtest_agent = SimulationBacktestingAgent("SimBacktest-1")
    macro_agent = MacroIntelligenceAgent("MacroIntel-1")
    quant_research_agent = QuantResearchAgent("QuantResearch-1")
    execution_agent = ExecutionAgent("Execution-1")

    orchestration_manager.register_agent(alpha_agent)
    orchestration_manager.register_agent(sim_backtest_agent)
    orchestration_manager.register_agent(macro_agent)
    orchestration_manager.register_agent(quant_research_agent)
    orchestration_manager.register_agent(execution_agent)

    # Start the task scheduler in the background
    scheduler_task = asyncio.create_task(task_scheduler.run_scheduler())

    print("\n--- Example Workflow 1: Alpha Signal Generation to Backtesting ---")
    # Define a pipeline that goes from alpha signal generation to backtesting
    alpha_to_backtest_pipeline_steps = [
        {
            "agent_type": "alpha_discovery",
            "action": "generate_candidate_signals",
            "data": {"market_focus": "tech_sector", "lookback_period": "3M"}
        },
        {
            "agent_type": "alpha_discovery",
            "action": "score_signals",
            "data": {} # Data will be passed from previous step (signals)
        },
        {
            "agent_type": "simulation_backtesting",
            "action": "perform_historical_backtest",
            "data": {"historical_data": {"source": "internal_db", "period": "5Y"}} # Strategy will be derived from previous step (top signal)
        }
    ]

    await strategy_pipeline_manager.create_pipeline("AlphaToBacktest", alpha_to_backtest_pipeline_steps)
    print("Running AlphaToBacktest pipeline...")
    pipeline_result_1 = await strategy_pipeline_manager.run_pipeline("AlphaToBacktest", {})
    print(f"Pipeline 'AlphaToBacktest' Result: {pipeline_result_1}")
    
    # Retrieve intermediate results from shared memory
    signals_from_memory = shared_memory.get("pipeline_AlphaToBacktest_step_0")
    if signals_from_memory:
        print(f"Latest signals from shared memory after step 0: {signals_from_memory.get('signals')[:2]}...")
    scored_signals_from_memory = shared_memory.get("pipeline_AlphaToBacktest_step_1")
    if scored_signals_from_memory:
        print(f"Top scored signal from shared memory after step 1: {scored_signals_from_memory.get('scored_signals')[0]}")

    print("\n--- Example Workflow 2: Macro-driven Strategy Adjustment ---")
    # Define a pipeline that monitors macro indicators and adjusts a strategy based on regime change
    macro_strategy_adjust_pipeline_steps = [
        {
            "agent_type": "macro_intelligence",
            "action": "monitor_indicators",
            "data": {"indicators": ["interest_rates", "credit_spreads", "volatility_indexes"]}
        },
        {
            "agent_type": "macro_intelligence",
            "action": "detect_regime_changes",
            "data": {} # Data will be passed from previous step (indicator_values)
        },
        {
            "agent_type": "alpha_discovery",
            "action": "mutate_strategy",
            "data": {"strategy_id": "existing_momentum_strategy"} # Mutation params will be based on detected regime
        }
    ]

    await strategy_pipeline_manager.create_pipeline("MacroStrategyAdjust", macro_strategy_adjust_pipeline_steps)
    print("Running MacroStrategyAdjust pipeline...")
    pipeline_result_2 = await strategy_pipeline_manager.run_pipeline("MacroStrategyAdjust", {})
    print(f"Pipeline 'MacroStrategyAdjust' Result: {pipeline_result_2}")

    print("\n--- Example Workflow 3: Stress Testing a Strategy ---")
    # Define a pipeline to stress test a specific strategy
    stress_test_pipeline_steps = [
        {
            "agent_type": "simulation_backtesting",
            "action": "run_monte_carlo_stress_test",
            "data": {"strategy": {"id": "value_investing_strategy"}, "market_scenarios": ["bear_market", "high_inflation"]}
        },
        {
            "agent_type": "simulation_backtesting",
            "action": "analyze_drawdown",
            "data": {} # Data will be passed from previous step (stress test results)
        }
    ]

    await strategy_pipeline_manager.create_pipeline("StressTestStrategy", stress_test_pipeline_steps)
    print("Running StressTestStrategy pipeline...")
    pipeline_result_3 = await strategy_pipeline_manager.run_pipeline("StressTestStrategy", {})
    print(f"Pipeline 'StressTestStrategy' Result: {pipeline_result_3}")

    # Clean up scheduler task
    scheduler_task.cancel()
    print("\nExample workflows completed.")

if __name__ == "__main__":
    asyncio.run(main())
