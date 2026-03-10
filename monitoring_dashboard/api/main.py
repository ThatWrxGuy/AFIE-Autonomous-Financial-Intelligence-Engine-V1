"""
Monitoring Dashboard API for AFC3.

Provides endpoints for:
- /health - Health check
- /agents - Agent information
- /tasks/active - Active tasks
- /tasks/completed - Completed tasks
- /tasks/failed - Failed tasks
- /pipelines - Pipeline information
- /signals - Recent signals
- /macro_state - Macro regime state
- /strategy_performance - Strategy performance data
"""

from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime

app = FastAPI(title="AFC3 Monitoring Dashboard API")

# Global references to system components (set by main.py)
orchestration_manager = None
task_scheduler = None
shared_memory = None
long_term_memory = None
experiment_store = None
pipeline_manager = None


def set_orchestration_manager(manager):
    """Set the orchestration manager reference."""
    global orchestration_manager
    orchestration_manager = manager


def set_task_scheduler(scheduler):
    """Set the task scheduler reference."""
    global task_scheduler
    task_scheduler = scheduler


def set_shared_memory(memory):
    """Set the shared memory reference."""
    global shared_memory
    shared_memory = memory


def set_long_term_memory(memory):
    """Set the long-term memory reference."""
    global long_term_memory
    long_term_memory = memory


def set_experiment_store(store):
    """Set the experiment store reference."""
    global experiment_store
    experiment_store = store


def set_pipeline_manager(manager):
    """Set the pipeline manager reference."""
    global pipeline_manager
    pipeline_manager = manager


@app.get("/")
async def root():
    return {"message": "Welcome to the AFC3 Monitoring Dashboard API", "version": "1.0.0"}


@app.get("/health")
async def get_health() -> Dict[str, Any]:
    """
    Returns system health status.
    """
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check orchestration manager
    if orchestration_manager:
        agent_count = len(orchestration_manager.agents)
        health["components"]["orchestration"] = {
            "status": "healthy",
            "agents_registered": agent_count
        }
    else:
        health["components"]["orchestration"] = {"status": "not_initialized"}
    
    # Check task scheduler
    if task_scheduler:
        health["components"]["scheduler"] = {
            "status": "healthy",
            "active_tasks": len(task_scheduler.active_tasks),
            "pending_tasks": len(task_scheduler.pending_tasks),
            "completed_tasks": len(task_scheduler.completed_tasks),
            "failed_tasks": len(task_scheduler.failed_tasks)
        }
    else:
        health["components"]["scheduler"] = {"status": "not_initialized"}
    
    # Check memory
    if shared_memory:
        health["components"]["short_term_memory"] = {
            "status": "healthy",
            "keys": len(shared_memory.list_keys())
        }
    else:
        health["components"]["short_term_memory"] = {"status": "not_initialized"}
    
    # Check long-term memory
    if long_term_memory:
        health["components"]["long_term_memory"] = {
            "status": "healthy",
            "experiments": len(long_term_memory.experiments),
            "strategies": len(long_term_memory.strategy_performance)
        }
    else:
        health["components"]["long_term_memory"] = {"status": "not_initialized"}
    
    # Check experiment store
    if experiment_store:
        health["components"]["experiment_store"] = {
            "status": "healthy",
            "experiments": len(experiment_store.experiments)
        }
    else:
        health["components"]["experiment_store"] = {"status": "not_initialized"}
    
    # Check pipeline manager
    if pipeline_manager:
        health["components"]["pipeline_manager"] = {
            "status": "healthy",
            "active_pipelines": len(pipeline_manager.pipeline_runs),
            "completed_pipelines": len(pipeline_manager.completed_pipelines)
        }
    else:
        health["components"]["pipeline_manager"] = {"status": "not_initialized"}
    
    return health


@app.get("/agents")
async def get_agents() -> List[Dict[str, Any]]:
    """
    Returns information about all registered agents.
    """
    if not orchestration_manager:
        return []
    
    agents = []
    for agent in orchestration_manager.agents.values():
        agents.append(agent.get_info())
    
    return agents


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str) -> Dict[str, Any]:
    """Get specific agent information."""
    if not orchestration_manager:
        raise HTTPException(status_code=503, detail="Orchestration manager not initialized")
    
    if agent_id not in orchestration_manager.agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return orchestration_manager.agents[agent_id].get_info()


@app.get("/tasks/active")
async def get_active_tasks() -> List[Dict[str, Any]]:
    """
    Returns currently active tasks.
    """
    if not task_scheduler:
        return []
    
    return list(task_scheduler.active_tasks.values())


@app.get("/tasks/pending")
async def get_pending_tasks() -> List[Dict[str, Any]]:
    """Returns pending tasks."""
    if not task_scheduler:
        return []
    return task_scheduler.pending_tasks


@app.get("/tasks/queued")
async def get_queued_tasks() -> List[Dict[str, Any]]:
    """Returns queued tasks."""
    if not task_scheduler:
        return []
    return task_scheduler.queued_tasks


@app.get("/tasks/completed")
async def get_completed_tasks(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Returns completed tasks.
    """
    if not task_scheduler:
        return []
    
    tasks = list(task_scheduler.completed_tasks.values())
    return tasks[-limit:]


@app.get("/tasks/failed")
async def get_failed_tasks(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Returns failed tasks.
    """
    if not task_scheduler:
        return []
    
    tasks = list(task_scheduler.failed_tasks.values())
    return tasks[-limit:]


@app.get("/tasks/archived")
async def get_archived_tasks(limit: int = 100) -> List[Dict[str, Any]]:
    """Returns archived tasks."""
    if not task_scheduler:
        return []
    
    tasks = list(task_scheduler.archived_tasks.values())
    return tasks[-limit:]


@app.get("/tasks/{task_id}")
async def get_task(task_id: str) -> Dict[str, Any]:
    """Get specific task information."""
    if not task_scheduler:
        raise HTTPException(status_code=503, detail="Task scheduler not initialized")
    
    task = task_scheduler.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return task


@app.get("/pipelines")
async def get_pipelines() -> Dict[str, Any]:
    """
    Returns pipeline information.
    """
    result = {
        "defined_pipelines": [],
        "active_runs": [],
        "completed_runs": []
    }
    
    # Get defined pipelines
    if pipeline_manager:
        result["defined_pipelines"] = list(pipeline_manager.pipelines.keys())
        result["active_runs"] = pipeline_manager.get_active_pipeline_runs()
        result["completed_runs"] = pipeline_manager.get_completed_pipeline_runs()
    
    return result


@app.get("/pipelines/{pipeline_run_id}")
async def get_pipeline_run(pipeline_run_id: str) -> Dict[str, Any]:
    """Get specific pipeline run information."""
    if not pipeline_manager:
        raise HTTPException(status_code=503, detail="Pipeline manager not initialized")
    
    run = pipeline_manager.get_pipeline_run(pipeline_run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Pipeline run {pipeline_run_id} not found")
    
    return run.to_dict()


@app.get("/signals")
async def get_signals(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Returns recent signals.
    """
    if not shared_memory:
        return []
    
    return shared_memory.get_signals(limit)


@app.get("/macro_state")
async def get_macro_state() -> Dict[str, Any]:
    """
    Returns macro regime state.
    """
    if not shared_memory:
        return {"regime": None, "confidence": None}
    
    regime_data = shared_memory.get_macro_regime()
    if not regime_data:
        return {"regime": None, "confidence": None}
    
    return regime_data


@app.get("/strategy_performance")
async def get_strategy_performance(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Returns strategy performance data.
    """
    if not long_term_memory:
        return []
    
    return long_term_memory.list_strategies(limit)


@app.get("/strategy_performance/{strategy_id}")
async def get_strategy_performance_by_id(strategy_id: str) -> Dict[str, Any]:
    """Get specific strategy performance."""
    if not long_term_memory:
        raise HTTPException(status_code=503, detail="Long-term memory not initialized")
    
    performance = long_term_memory.get_strategy_performance(strategy_id)
    if not performance:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    
    return performance


@app.get("/experiments")
async def get_experiments(status: str = None, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Returns experiments from the experiment store.
    """
    if not experiment_store:
        return []
    
    return experiment_store.list_experiments(status, limit)


@app.get("/experiments/approved")
async def get_approved_strategies(limit: int = 100) -> List[Dict[str, Any]]:
    """Returns approved strategies."""
    if not experiment_store:
        return []
    
    return experiment_store.get_approved_strategies(limit)


@app.get("/experiments/rejected")
async def get_rejected_strategies(limit: int = 100) -> List[Dict[str, Any]]:
    """Returns rejected strategies."""
    if not experiment_store:
        return []
    
    return experiment_store.get_rejected_strategies(limit)


@app.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Returns overall system statistics."""
    stats = {
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if orchestration_manager:
        stats["agents"] = {
            "total": len(orchestration_manager.agents),
            "by_type": {}
        }
        for agent_type in orchestration_manager.agent_types:
            stats["agents"]["by_type"][agent_type] = len(
                orchestration_manager.agent_types[agent_type]
            )
    
    if task_scheduler:
        stats["tasks"] = {
            "active": len(task_scheduler.active_tasks),
            "pending": len(task_scheduler.pending_tasks),
            "queued": len(task_scheduler.queued_tasks),
            "completed": len(task_scheduler.completed_tasks),
            "failed": len(task_scheduler.failed_tasks),
            "archived": len(task_scheduler.archived_tasks)
        }
    
    if long_term_memory:
        stats["long_term_memory"] = long_term_memory.get_stats()
    
    if experiment_store:
        stats["experiments"] = experiment_store.get_stats()
    
    return stats
