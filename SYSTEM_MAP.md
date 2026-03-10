# AFC3 System Architecture Map

## Current System Components

### Agent Classes
- **BaseAgent** (`agents/base_agent.py`)
  - Abstract base class with id, name, agent_type, status
  - Abstract methods: process_task(), handle_message()
  - Status: simple "idle" string

- **AlphaDiscoveryAgent** (`agents/alpha_discovery_agent.py`)
  - Actions: generate_candidate_signals, explore_parameter_space, mutate_strategy, score_signals
  - Returns: {"status": "success", ...}

- **SimulationBacktestingAgent** (`agents/simulation_backtesting_agent.py`)
  - Actions: perform_historical_backtest, run_monte_carlo_stress_test, simulate_regime, analyze_drawdown

- **MacroIntelligenceAgent** (`agents/macro_intelligence_agent.py`)
  - Actions: monitor_indicators, detect_regime_changes, generate_regime_probability_scores

### Scheduler Logic
- **TaskScheduler** (`task_scheduler/scheduler.py`)
  - job_queue: List of pending tasks
  - active_tasks: Dict of running tasks
  - Issues: No completed/failed/archived storage, no retry logic, no timeout handling

### Orchestration Manager
- **AgentOrchestrationManager** (`agent_orchestration/manager.py`)
  - Manages agent registry
  - Routes tasks to agents
  - Simple idle/busy status

### Pipeline Manager
- **StrategyPipelineManager** (`strategy_pipeline/manager.py`)
  - Manages pipeline execution
  - Known issue: Results don't propagate correctly between steps

### Memory Layer
- **ShortTermMemory** (`shared_memory/short_term_memory.py`)
  - Simple key-value store with TTL

### Monitoring API
- **FastAPI** (`monitoring_dashboard/api/main.py`)
  - Not connected to actual system components
  - Returns empty/default data

---

## Required Changes (Per Directive 005)

### Phase 2: Task Scheduler Hardening
- Add task states: pending, queued, running, completed, failed, cancelled, archived
- Standard task schema with all required fields
- Implement completed_tasks, failed_tasks, archived_tasks storage
- Add retry logic and timeout handling
- Record execution duration

### Phase 3: Pipeline Manager Repair
- Fix result propagation between steps
- Add pipeline_run_id tracking
- Add step status tracking
- Implement failure detection and retry logic
- Add input/output mapping

### Phase 4: Agent Result Standardization
- Standardize success/failure response envelopes
- Include agent_id, agent_type, action, task_id, timestamp, duration_seconds

### Phase 5: Base Agent Hardening
- Add lifecycle states: idle, busy, running, error, offline
- Add metadata fields
- Add helper methods

### Phase 6: Event Bus Implementation
- Create core/event_bus.py
- Implement publish/subscribe/unsubscribe
- Define event schema

### Phase 7: Shared Memory Layer
- Add long_term_memory.py
- Add experiment_store.py

### Phase 8: Monitoring Dashboard Integration
- Connect endpoints to actual system state
- Add required endpoints

### Phase 9: Structured Logging
- Replace print statements
- Add timestamp, component, task_id, agent_id, pipeline_run_id

### Phase 10-11: Tests and Workflows
- Integration tests
- Example research workflows
