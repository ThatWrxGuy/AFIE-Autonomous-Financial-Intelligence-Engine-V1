# AFIE Control Core Extension: Agent Architecture and Folder Structure Design

This document outlines the proposed architecture and folder structure for integrating three new AI agents—Alpha Discovery AI, Simulation & Backtesting AI, and Macro Intelligence AI—into the existing AFIE Control Core.

## 1. Agent Architecture Design

Each new agent will inherit from the `BaseAgent` class, ensuring adherence to the core's interaction protocols. This approach facilitates seamless integration with the `AgentOrchestrationManager`, `TaskScheduler`, and `ShortTermMemory` components.

### 1.1. Alpha Discovery AI Agent

**Purpose**: To generate and refine alpha signals for the Strategy Laboratory pipeline.

**Class Name**: `AlphaDiscoveryAgent`

**Agent Type**: `alpha_discovery`

**Capabilities & Methods**:

*   `generate_candidate_signals(self, data: Dict[str, Any]) -> List[Dict[str, Any]]`: Generates new alpha signals based on input market data or research parameters.
*   `explore_parameter_space(self, signal_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]`: Explores different parameter configurations for a given signal to optimize its performance.
*   `mutate_strategy(self, strategy_id: str, mutation_params: Dict[str, Any]) -> Dict[str, Any]`: Modifies existing strategies by introducing variations in their logic or parameters.
*   `score_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]`: Evaluates signals based on statistical edge, returning scored signals.
*   `process_task(self, task: Dict[str, Any]) -> Dict[str, Any]`: Overrides `BaseAgent`'s method to handle specific alpha discovery tasks.
*   `handle_message(self, message: Dict[str, Any]) -> None`: Overrides `BaseAgent`'s method to process messages from other agents or the Control Core.

**Integration Points**:

*   **Task Scheduler**: Receives tasks to generate, explore, mutate, or score signals.
*   **Shared Memory**: Stores intermediate signals, parameter exploration results, and scoring metrics.
*   **Strategy Pipeline Manager**: Feeds scored alpha signals into the Strategy Laboratory pipeline.
*   **System Monitoring Dashboard**: Exposes status, active tasks, and performance metrics related to signal generation.

### 1.2. Simulation & Backtesting AI Agent

**Purpose**: To rigorously test and validate trading strategies through various simulation techniques.

**Class Name**: `SimulationBacktestingAgent`

**Agent Type**: `simulation_backtesting`

**Capabilities & Methods**:

*   `perform_historical_backtest(self, strategy: Dict[str, Any], historical_data: Dict[str, Any]) -> Dict[str, Any]`: Executes a strategy against historical data to evaluate its past performance.
*   `run_monte_carlo_stress_test(self, strategy: Dict[str, Any], market_scenarios: List[Dict[str, Any]]) -> Dict[str, Any]`: Conducts Monte Carlo simulations to assess strategy robustness under various market conditions.
*   `simulate_regime(self, strategy: Dict[str, Any], regime_data: Dict[str, Any]) -> Dict[str, Any]`: Simulates strategy performance within specific market regimes.
*   `analyze_drawdown(self, performance_data: Dict[str, Any]) -> Dict[str, Any]`: Performs detailed drawdown analysis on strategy performance.
*   `process_task(self, task: Dict[str, Any]) -> Dict[str, Any]`: Overrides `BaseAgent`'s method to handle simulation and backtesting tasks.
*   `handle_message(self, message: Dict[str, Any]) -> None`: Overrides `BaseAgent`'s method to process messages.

**Outputs**:

*   Risk metrics (e.g., VaR, CVaR, maximum drawdown).
*   Sharpe distributions.
*   Strategy survival probabilities.

**Integration Points**:

*   **Task Scheduler**: Receives tasks for backtesting, stress testing, regime simulations, and drawdown analysis.
*   **Shared Memory**: Stores simulation results, performance metrics, and strategy survival probabilities.
*   **Strategy Pipeline Manager**: Provides validated strategies and performance reports for further stages.
*   **System Monitoring Dashboard**: Displays simulation progress, key risk metrics, and strategy validation status.

### 1.3. Macro Intelligence AI Agent

**Purpose**: To monitor macroeconomic indicators, detect regime changes, and provide probabilistic scores for market regimes.

**Class Name**: `MacroIntelligenceAgent`

**Agent Type**: `macro_intelligence`

**Capabilities & Methods**:

*   `monitor_indicators(self, indicators: List[str]) -> Dict[str, Any]`: Continuously monitors specified macroeconomic indicators (interest rates, credit spreads, volatility indexes, liquidity metrics).
*   `detect_regime_changes(self, indicator_data: Dict[str, Any]) -> Dict[str, Any]`: Identifies shifts in market regimes based on indicator analysis.
*   `generate_regime_probability_scores(self, current_state: Dict[str, Any]) -> Dict[str, Any]`: Calculates probability scores for different market regimes.
*   `send_alerts_to_risk_system(self, alert_data: Dict[str, Any]) -> None`: Sends alerts regarding significant regime changes or risk events to the portfolio risk system.
*   `process_task(self, task: Dict[str, Any]) -> Dict[str, Any]`: Overrides `BaseAgent`'s method to handle macro intelligence tasks.
*   `handle_message(self, message: Dict[str, Any]) -> None`: Overrides `BaseAgent`'s method to process messages.

**Key Indicators Monitored**:

*   Interest rates
*   Credit spreads
*   Volatility indexes
*   Liquidity metrics

**Integration Points**:

*   **Task Scheduler**: Receives tasks for monitoring, regime detection, and score generation.
*   **Shared Memory**: Stores current macroeconomic indicator values, detected regime states, and probability scores.
*   **Strategy Pipeline Manager**: Informs strategies about current and probable future market regimes.
*   **System Monitoring Dashboard**: Displays real-time macroeconomic indicators, detected regimes, and alerts.

## 2. Folder Structure for New Agents

The new agents will reside within the `AFC3/agents/` directory, following the existing pattern established by `base_agent.py` and `example_agents.py`. Each agent will have its own dedicated Python file.

```
AFC3/
├── agent_orchestration/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── example_agents.py
│   ├── alpha_discovery_agent.py         # New: Alpha Discovery AI Agent
│   ├── simulation_backtesting_agent.py  # New: Simulation & Backtesting AI Agent
│   └── macro_intelligence_agent.py      # New: Macro Intelligence AI Agent
├── communication_protocol/
├── config/
├── monitoring_dashboard/
├── shared_memory/
├── strategy_pipeline/
├── task_scheduler/
├── tests/
└── utils/
```

This structure maintains modularity and organization, making it easy to locate and manage each agent's implementation. The `__init__.py` file in the `agents` directory will be updated to import these new agent classes, making them discoverable by the `AgentOrchestrationManager`.
