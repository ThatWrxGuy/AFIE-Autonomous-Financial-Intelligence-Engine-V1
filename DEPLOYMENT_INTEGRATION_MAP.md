# AFC3 Capital Deployment Layer - Integration Map

## Current AFC3 Modules (from Directive 005)

### Core Components
| Module | Location | Purpose |
|--------|----------|---------|
| Event Bus | `core/event_bus.py` | Publish/subscribe messaging |
| Task Scheduler | `task_scheduler/scheduler.py` | Task lifecycle management |
| Pipeline Manager | `strategy_pipeline/manager.py` | Multi-step pipeline execution |
| Short-term Memory | `shared_memory/short_term_memory.py` | Transient data storage |
| Long-term Memory | `shared_memory/long_term_memory.py` | Persistent data storage |
| Experiment Store | `shared_memory/experiment_store.py` | Experiment records |
| Monitoring API | `monitoring_dashboard/api/main.py` | System state endpoints |

### Agent Types
| Agent | Location | Purpose |
|-------|----------|---------|
| BaseAgent | `agents/base_agent.py` | Agent base class |
| AlphaDiscoveryAgent | `agents/alpha_discovery_agent.py` | Signal generation |
| SimulationBacktestingAgent | `agents/simulation_backtesting_agent.py` | Strategy validation |
| MacroIntelligenceAgent | `agents/macro_intelligence_agent.py` | Regime detection |

---

## New Components for Capital Deployment Layer

### Phase 2: Portfolio Intelligence AI
- **File**: `agents/portfolio_intelligence_agent.py`
- **Purpose**: Convert approved strategies to capital allocation decisions
- **Integrates with**: 
  - Experiment Store (read approved strategies)
  - Short-term Memory (read/write portfolio state)
  - Long-term Memory (read historical allocations)
  - Event Bus (publish allocation events)

### Phase 3: Execution Intelligence AI
- **File**: `agents/execution_intelligence_agent.py`
- **Purpose**: Convert allocations to executable orders (paper/simulated)
- **Integrates with**:
  - Short-term Memory (read/write orders, fills)
  - Long-term Memory (read/write execution summaries)
  - Event Bus (publish execution events)

### Phase 5: Portfolio Constraint Engine
- **File**: `core/portfolio_constraints.py`
- **Purpose**: Risk control and constraint validation
- **Integrates with**: Portfolio Intelligence Agent

### Phase 11: Execution Adapter
- **Files**: `execution/base_execution_adapter.py`, `execution/simulated_adapter.py`
- **Purpose**: Safe order execution abstraction
- **Integrates with**: Execution Intelligence Agent

### Phase 12: Portfolio State
- **File**: `core/portfolio_state.py`
- **Purpose**: Track portfolio positions and state
- **Integrates with**: Memory layers

---

## Data Flow

```
Research Pipeline (from Directive 005)
         ↓
   Approved Strategy
         ↓
   [Portfolio Intelligence AI]
         ↓ (validate_strategy_for_allocation)
   Validation Gate
         ↓ (if approved)
   Score & Size Positions
         ↓
   Allocation Decision
         ↓
   [Execution Intelligence AI]
         ↓ (generate_order_intents)
   Order Intents
         ↓
   Validation Gate
         ↓ (if valid)
   Execution Orders
         ↓
   [Execution Adapter]
         ↓ (simulate_execution)
   Fill Reports
         ↓
   Portfolio State Update
         ↓
   Monitoring Dashboard
```

---

## Event Flow

| Event | Source | Target |
|-------|--------|--------|
| `strategy.approved_for_allocation` | Research Workflow | Portfolio Intelligence |
| `allocation.created` | Portfolio Intelligence | Event Bus |
| `allocation.rejected` | Portfolio Intelligence | Event Bus |
| `order_intent.created` | Portfolio Intelligence | Event Bus |
| `order.generated` | Execution Intelligence | Event Bus |
| `order.executed` | Execution Adapter | Event Bus |
| `execution.summary_generated` | Execution Intelligence | Event Bus |
| `portfolio.rebalanced` | Portfolio State | Event Bus |

---

## Monitoring Endpoints to Add

| Endpoint | Description |
|----------|-------------|
| GET /portfolio/state | Current portfolio state |
| GET /portfolio/allocations | Allocation history |
| GET /portfolio/constraints | Active constraints |
| GET /portfolio/rejections | Rejected allocations |
| GET /execution/orders | Active orders |
| GET /execution/fills | Fill history |
| GET /execution/summaries | Execution summaries |
| GET /risk/current_exposure | Current exposure |
| GET /risk/leverage | Current leverage |
| GET /risk/kill_switch_status | Kill switch state |
