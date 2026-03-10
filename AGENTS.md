# AFC3 Project Notes

## Project Overview
- **AFIE Control Core (AFC3)**: Multi-agent financial intelligence orchestration system
- **Location**: `/workspace/afc3_project/`

## Running the System

### Main Application
```bash
cd /workspace/afc3_project
python3 main.py
```

### Example Workflows
```bash
cd /workspace/afc3_project
python3 example_workflows_refactored.py
```

### Running Tests
```bash
cd /workspace/afc3_project
pip install pytest pytest-asyncio
pytest tests/integration/test_afc3.py -v
```

### Monitoring Dashboard
Start the API server:
```bash
cd /workspace/afc3_project
pip install fastapi uvicorn
uvicorn monitoring_dashboard.api.main:app --host 0.0.0.0 --port 8000
```

## Key Components

| Component | File | Description |
|-----------|------|-------------|
| Base Agent | `agents/base_agent.py` | Agent lifecycle states, standardized results |
| Task Scheduler | `task_scheduler/scheduler.py` | Full lifecycle (pending→completed/failed) |
| Pipeline Manager | `strategy_pipeline/manager.py` | Result propagation between steps |
| Event Bus | `core/event_bus.py` | Publish/subscribe messaging |
| Short-term Memory | `shared_memory/short_term_memory.py` | Transient data |
| Long-term Memory | `shared_memory/long_term_memory.py` | Persistent experiments |
| Experiment Store | `shared_memory/experiment_store.py` | Pipeline run records |
| Monitoring API | `monitoring_dashboard/api/main.py` | System state endpoints |

## Example Workflows

- **Workflow A**: AlphaDiscovery → SimulationBacktest → experiment store
- **Workflow B**: SimulationBacktest → MacroEvaluation → approval/rejection
- **Workflow C**: Failure handling with rejection recording

## Agent Types

1. **AlphaDiscoveryAgent** - Signal generation
2. **SimulationBacktestingAgent** - Strategy validation
3. **MacroIntelligenceAgent** - Market regime detection
