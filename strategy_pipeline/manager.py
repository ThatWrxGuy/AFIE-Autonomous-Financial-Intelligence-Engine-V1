"""
Strategy Pipeline Manager for AFC3.

Features:
- pipeline_run_id for each run
- Step status tracking
- Failure detection
- Retry logic
- Step input/output mapping
- Final pipeline result storage

Pipeline step structure:
{
    name
    agent_type
    action
    input_map
    stop_on_failure
    max_retries
}
"""

from typing import List, Dict, Any, Optional, Callable
import asyncio
import uuid
from datetime import datetime
from enum import Enum


class PipelineStatus(str, Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Step execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineStep:
    """Represents a single step in a pipeline."""
    
    def __init__(self, config: Dict[str, Any]):
        self.name = config.get("name", "")
        self.agent_type = config.get("agent_type")
        self.action = config.get("action")
        self.input_map = config.get("input_map", {})
        self.stop_on_failure = config.get("stop_on_failure", True)
        self.max_retries = config.get("max_retries", 3)
        
        # Runtime state
        self.status = StepStatus.PENDING
        self.task_id: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.retry_count = 0
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.execution_duration: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        return {
            "name": self.name,
            "agent_type": self.agent_type,
            "action": self.action,
            "input_map": self.input_map,
            "stop_on_failure": self.stop_on_failure,
            "max_retries": self.max_retries,
            "status": self.status,
            "task_id": self.task_id,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "execution_duration": self.execution_duration
        }


class PipelineRun:
    """Represents a single pipeline execution."""
    
    def __init__(self, pipeline_run_id: str, name: str, steps: List[PipelineStep]):
        self.pipeline_run_id = pipeline_run_id
        self.name = name
        self.steps = steps
        self.status = PipelineStatus.PENDING
        self.initial_data: Dict[str, Any] = {}
        self.final_result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.execution_duration: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline run to dictionary."""
        return {
            "pipeline_run_id": self.pipeline_run_id,
            "name": self.name,
            "status": self.status,
            "steps": [step.to_dict() for step in self.steps],
            "initial_data": self.initial_data,
            "final_result": self.final_result,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "execution_duration": self.execution_duration
        }


class StrategyPipelineManager:
    """
    Manages automated workflows for the entire financial intelligence process.
    
    Features:
    - pipeline_run_id for each run
    - Step status tracking
    - Failure detection
    - Retry logic
    - Step input/output mapping
    - Final pipeline result storage
    """
    
    def __init__(self, task_scheduler, shared_memory):
        self.task_scheduler = task_scheduler
        self.shared_memory = shared_memory
        self.pipelines: Dict[str, List[Dict[str, Any]]] = {}
        self.pipeline_runs: Dict[str, PipelineRun] = {}
        self.completed_pipelines: Dict[str, PipelineRun] = {}
        
        # Set up task completion callback
        self.task_scheduler.set_task_complete_callback(self._on_task_complete)
    
    async def _on_task_complete(self, task_id: str, task: Dict[str, Any]) -> None:
        """Callback for task completion to update pipeline step status."""
        # Find the pipeline run that contains this task
        for pipeline_run in self.pipeline_runs.values():
            for step in pipeline_run.steps:
                if step.task_id == task_id:
                    if task.get("status") == "completed":
                        step.status = StepStatus.COMPLETED
                        step.result = task.get("result")
                        step.completed_at = datetime.utcnow().isoformat()
                        if step.started_at:
                            started = datetime.fromisoformat(step.started_at)
                            completed = datetime.fromisoformat(step.completed_at)
                            step.execution_duration = (completed - started).total_seconds()
                    else:
                        step.status = StepStatus.FAILED
                        step.error = task.get("error")
                        step.completed_at = datetime.utcnow().isoformat()
                    break
    
    async def create_pipeline(self, name: str, steps: List[Dict[str, Any]]) -> str:
        """
        Creates a new strategy pipeline with defined steps.
        
        Args:
            name: Pipeline name
            steps: List of step configurations
            
        Returns:
            Pipeline name
        """
        self.pipelines[name] = steps
        print(f"Pipeline created: {name} with {len(steps)} steps.")
        return name
    
    async def run_pipeline(self, name: str, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs a strategy pipeline with initial data.
        
        Args:
            name: Pipeline name
            initial_data: Initial data for the pipeline
            
        Returns:
            Pipeline execution result
        """
        if name not in self.pipelines:
            raise ValueError(f"Pipeline with name {name} not found.")
        
        # Create pipeline run ID
        pipeline_run_id = str(uuid.uuid4())
        
        # Create pipeline run object
        step_configs = self.pipelines[name]
        pipeline_steps = [PipelineStep(config) for config in step_configs]
        pipeline_run = PipelineRun(pipeline_run_id, name, pipeline_steps)
        pipeline_run.initial_data = initial_data.copy()
        pipeline_run.status = PipelineStatus.RUNNING
        pipeline_run.started_at = datetime.utcnow().isoformat()
        
        # Store pipeline run
        self.pipeline_runs[pipeline_run_id] = pipeline_run
        
        print(f"Starting pipeline: {name} (Run ID: {pipeline_run_id})")
        
        # Execute pipeline steps
        current_data = initial_data.copy()
        
        for i, step in enumerate(pipeline_steps):
            step.status = StepStatus.RUNNING
            step.started_at = datetime.utcnow().isoformat()
            
            # Map input data based on input_map
            mapped_data = self._map_input(step.input_map, current_data)
            
            print(f"Pipeline {name} (Run: {pipeline_run_id}): "
                  f"Step {i+1}/{len(pipeline_steps)} - {step.name} "
                  f"({step.agent_type}.{step.action})")
            
            # Schedule task with retries
            success = False
            for attempt in range(step.max_retries):
                try:
                    step.task_id = await self.task_scheduler.schedule_task(
                        agent_type=step.agent_type,
                        action=step.action,
                        data=mapped_data,
                        priority=10 - i,  # Higher priority for earlier steps
                        max_retries=1,  # We handle retries at pipeline level
                        timeout_seconds=300
                    )
                    
                    # Wait for task completion
                    result = await self._wait_for_step(pipeline_run_id, step)
                    
                    if result.get("status") == "success":
                        step.status = StepStatus.COMPLETED
                        step.result = result.get("result", {})
                        step.completed_at = datetime.utcnow().isoformat()
                        
                        if step.started_at:
                            started = datetime.fromisoformat(step.started_at)
                            completed = datetime.fromisoformat(step.completed_at)
                            step.execution_duration = (completed - started).total_seconds()
                        
                        # Propagate result to next step
                        current_data.update(step.result)
                        success = True
                        break
                    else:
                        step.error = result.get("error", "Unknown error")
                        
                except Exception as e:
                    step.error = str(e)
                    step.retry_count += 1
            
            if not success:
                step.status = StepStatus.FAILED
                step.completed_at = datetime.utcnow().isoformat()
                
                if step.stop_on_failure:
                    pipeline_run.status = PipelineStatus.FAILED
                    pipeline_run.error = f"Step {step.name} failed: {step.error}"
                    pipeline_run.completed_at = datetime.utcnow().isoformat()
                    
                    if pipeline_run.started_at:
                        started = datetime.fromisoformat(pipeline_run.started_at)
                        completed = datetime.fromisoformat(pipeline_run.completed_at)
                        pipeline_run.execution_duration = (completed - started).total_seconds()
                    
                    # Store in completed pipelines
                    self.completed_pipelines[pipeline_run_id] = pipeline_run
                    
                    print(f"Pipeline {name} (Run: {pipeline_run_id}) failed at step {step.name}: {step.error}")
                    return {
                        "status": "failed",
                        "pipeline_run_id": pipeline_run_id,
                        "failed_step": step.name,
                        "error": step.error,
                        "steps_completed": i,
                        "total_steps": len(pipeline_steps)
                    }
            
            # Store intermediate results in shared memory
            self.shared_memory.set(f"pipeline_{name}_step_{i}", step.result or {})
            
            # Update current data with step result for next step
            if step.result:
                current_data.update(step.result)
        
        # Pipeline completed successfully
        pipeline_run.status = PipelineStatus.COMPLETED
        pipeline_run.final_result = current_data.copy()
        pipeline_run.completed_at = datetime.utcnow().isoformat()
        
        if pipeline_run.started_at:
            started = datetime.fromisoformat(pipeline_run.started_at)
            completed = datetime.fromisoformat(pipeline_run.completed_at)
            pipeline_run.execution_duration = (completed - started).total_seconds()
        
        # Store in completed pipelines
        self.completed_pipelines[pipeline_run_id] = pipeline_run
        
        # Remove from active pipeline runs
        del self.pipeline_runs[pipeline_run_id]
        
        print(f"Pipeline {name} (Run: {pipeline_run_id}) completed successfully. "
              f"Duration: {pipeline_run.execution_duration}s")
        
        return {
            "status": "success",
            "pipeline_run_id": pipeline_run_id,
            "result": current_data,
            "execution_duration": pipeline_run.execution_duration
        }
    
    def _map_input(self, input_map: Dict[str, Any], source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map input data based on input_map configuration.
        
        Example input_map:
        {
            "strategy": "AlphaDiscovery.result.strategy",
            "signals": "AlphaDiscovery.result.signals"
        }
        
        This would extract:
        - source_data["AlphaDiscovery"]["result"]["strategy"] -> mapped_data["strategy"]
        """
        mapped_data = {}
        
        for target_key, source_path in input_map.items():
            # Parse the source path (e.g., "AlphaDiscovery.result.strategy")
            value = self._get_nested_value(source_data, source_path)
            mapped_data[target_key] = value
        
        # If no input_map, pass all source data
        if not input_map:
            mapped_data = source_data.copy()
        
        return mapped_data
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """
        Get a nested value from a dictionary using dot notation.
        
        Example: _get_nested_value(data, "a.b.c") returns data["a"]["b"]["c"]
        """
        keys = path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        
        return value
    
    async def _wait_for_step(self, pipeline_run_id: str, step: PipelineStep) -> Dict[str, Any]:
        """
        Waits for a step's task to complete.
        
        Args:
            pipeline_run_id: Pipeline run ID
            step: Pipeline step
            
        Returns:
            Step result
        """
        max_wait = 60  # Max wait time in seconds
        wait_interval = 0.5
        waited = 0
        
        while waited < max_wait:
            # Get task from scheduler
            if step.task_id:
                task = self.task_scheduler.get_task(step.task_id)
                
                if task:
                    if task.get("status") == "completed":
                        return {"status": "success", "result": task.get("result", {})}
                    elif task.get("status") == "failed":
                        return {"status": "failed", "error": task.get("error", "Task failed")}
            
            await asyncio.sleep(wait_interval)
            waited += wait_interval
        
        return {"status": "failed", "error": "Timeout waiting for step completion"}
    
    def get_pipeline_run(self, pipeline_run_id: str) -> Optional[PipelineRun]:
        """Get a pipeline run by ID."""
        if pipeline_run_id in self.pipeline_runs:
            return self.pipeline_runs[pipeline_run_id]
        if pipeline_run_id in self.completed_pipelines:
            return self.completed_pipelines[pipeline_run_id]
        return None
    
    def get_all_pipeline_runs(self) -> List[Dict[str, Any]]:
        """Get all pipeline runs."""
        all_runs = list(self.pipeline_runs.values()) + list(self.completed_pipelines.values())
        return [run.to_dict() for run in all_runs]
    
    def get_active_pipeline_runs(self) -> List[Dict[str, Any]]:
        """Get active pipeline runs."""
        return [run.to_dict() for run in self.pipeline_runs.values()]
    
    def get_completed_pipeline_runs(self) -> List[Dict[str, Any]]:
        """Get completed pipeline runs."""
        return [run.to_dict() for run in self.completed_pipelines.values()]
