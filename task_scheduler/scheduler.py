"""
Hardened Task Scheduler for AFC3.

Features:
- Complete task lifecycle (pending, queued, running, completed, failed, cancelled, archived)
- Standard task schema with all required fields
- Completed/failed/archived task storage
- Retry logic with max_retries
- Timeout handling
- Execution duration tracking
- Agent status management (busy when executing, idle when finished)
"""

from typing import List, Dict, Any, Optional, Callable
import asyncio
import uuid
import time
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Task lifecycle states."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class TaskSchema:
    """Standard task schema."""
    
    @staticmethod
    def create(
        agent_type: str,
        action: str,
        data: Dict[str, Any],
        priority: int = 0,
        max_retries: int = 3,
        timeout_seconds: int = 300
    ) -> Dict[str, Any]:
        """Create a new task with standard schema."""
        return {
            "id": str(uuid.uuid4()),
            "agent_type": agent_type,
            "action": action,
            "data": data,
            "priority": priority,
            "status": TaskStatus.PENDING,
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "retry_count": 0,
            "max_retries": max_retries,
            "timeout_seconds": timeout_seconds,
            "result": None,
            "error": None,
            "execution_duration_seconds": None
        }


class TaskScheduler:
    """
    Distributed task scheduling system for assigning workloads to agents.
    
    Features:
    - Complete task lifecycle management
    - Completed, failed, and archived task storage
    - Retry logic with configurable max retries
    - Timeout handling
    - Execution duration tracking
    - Agent status management
    """
    
    def __init__(self, orchestration_manager):
        self.orchestration_manager = orchestration_manager
        self.pending_tasks: List[Dict[str, Any]] = []
        self.queued_tasks: List[Dict[str, Any]] = []
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: Dict[str, Dict[str, Any]] = {}
        self.failed_tasks: Dict[str, Dict[str, Any]] = {}
        self.archived_tasks: Dict[str, Dict[str, Any]] = {}
        
        # Callback for pipeline manager to be notified of task completion
        self.on_task_complete: Optional[Callable] = None
        
    def set_task_complete_callback(self, callback: Callable) -> None:
        """Set callback for task completion notifications."""
        self.on_task_complete = callback
    
    async def schedule_task(
        self,
        agent_type: str,
        action: str,
        data: Dict[str, Any],
        priority: int = 0,
        max_retries: int = 3,
        timeout_seconds: int = 300
    ) -> str:
        """
        Schedules a task for execution with standard schema.
        """
        task = TaskSchema.create(
            agent_type=agent_type,
            action=action,
            data=data,
            priority=priority,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds
        )
        
        # Add to pending queue
        self.pending_tasks.append(task)
        
        # Sort by priority (higher priority first)
        self.pending_tasks.sort(key=lambda x: x["priority"], reverse=True)
        
        self._log("INFO", "TaskScheduler", None, None, None,
                  f"Task scheduled: {task['id']} (Priority: {priority}, Agent: {agent_type}, Action: {action})")
        
        return task["id"]
    
    async def queue_task(self, task: Dict[str, Any]) -> None:
        """
        Move a task to the queued state.
        """
        task["status"] = TaskStatus.QUEUED
        task["queued_at"] = datetime.utcnow().isoformat()
        self.queued_tasks.append(task)
        self.queued_tasks.sort(key=lambda x: x["priority"], reverse=True)
        
    async def run_scheduler(self) -> None:
        """
        Continuously monitors the queues and assigns tasks to available agents.
        """
        while True:
            await self._process_pending_tasks()
            await self._check_timeouts()
            await asyncio.sleep(0.5)
    
    async def _process_pending_tasks(self) -> None:
        """Process pending tasks and assign to available agents."""
        while self.pending_tasks:
            task = self.pending_tasks.pop(0)
            await self.queue_task(task)
        
        # Process queued tasks
        while self.queued_tasks:
            task = self.queued_tasks.pop(0)
            agent_type = task.get("agent_type")
            available_agents = self.orchestration_manager.discover_agents(agent_type)
            
            # Find idle agents
            idle_agents = [a for a in available_agents if a.get("status") == "idle"]
            
            if idle_agents:
                agent_id = idle_agents[0]["id"]
                await self._start_task(agent_id, task)
            else:
                # Re-queue task if no agents are available
                self.queued_tasks.insert(0, task)
                break
    
    async def _start_task(self, agent_id: str, task: Dict[str, Any]) -> None:
        """
        Starts executing a task on a specific agent.
        """
        task_id = task["id"]
        task["status"] = TaskStatus.RUNNING
        task["started_at"] = datetime.utcnow().isoformat()
        task["agent_id"] = agent_id
        
        # Update agent status to busy
        if agent_id in self.orchestration_manager.agents:
            agent = self.orchestration_manager.agents[agent_id]
            agent.set_status("busy")
            agent.begin_task(task_id)
        
        # Add to active tasks
        self.active_tasks[task_id] = task
        
        self._log("INFO", "TaskScheduler", task_id, agent_id, None,
                  f"Task started: {task_id} on agent {agent_id}")
        
        # Execute task with timeout
        asyncio.create_task(self._execute_task_with_timeout(agent_id, task))
    
    async def _execute_task_with_timeout(self, agent_id: str, task: Dict[str, Any]) -> None:
        """
        Executes a task with timeout handling.
        """
        task_id = task["id"]
        timeout_seconds = task.get("timeout_seconds", 300)
        
        try:
            result = await asyncio.wait_for(
                self.orchestration_manager.route_task(agent_id, task),
                timeout=timeout_seconds
            )
            await self._complete_task(task_id, result)
        except asyncio.TimeoutError:
            await self._fail_task(task_id, f"Task timed out after {timeout_seconds} seconds")
        except Exception as e:
            await self._handle_task_error(task_id, agent_id, str(e))
    
    async def _complete_task(self, task_id: str, result: Dict[str, Any]) -> None:
        """
        Marks a task as completed successfully.
        """
        if task_id not in self.active_tasks:
            return
            
        task = self.active_tasks[task_id]
        completed_at = datetime.utcnow().isoformat()
        
        # Calculate execution duration
        if task.get("started_at"):
            started = datetime.fromisoformat(task["started_at"])
            completed = datetime.fromisoformat(completed_at)
            duration = (completed - started).total_seconds()
            task["execution_duration_seconds"] = duration
        
        task["status"] = TaskStatus.COMPLETED
        task["completed_at"] = completed_at
        task["result"] = result
        
        # Store in completed tasks
        self.completed_tasks[task_id] = task.copy()
        
        # Update agent status
        agent_id = task.get("agent_id")
        if agent_id and agent_id in self.orchestration_manager.agents:
            agent = self.orchestration_manager.agents[agent_id]
            agent.set_status("idle")
            agent.complete_task(task_id)
        
        # Remove from active tasks
        del self.active_tasks[task_id]
        
        self._log("INFO", "TaskScheduler", task_id, agent_id, task.get("pipeline_run_id"),
                  f"Task completed: {task_id} (Duration: {task.get('execution_duration_seconds')}s)")
        
        # Notify pipeline manager if callback is set
        if self.on_task_complete:
            await self.on_task_complete(task_id, task)
    
    async def _fail_task(self, task_id: str, error: str) -> None:
        """
        Marks a task as failed.
        """
        if task_id not in self.active_tasks:
            return
            
        task = self.active_tasks[task_id]
        agent_id = task.get("agent_id")
        
        # Check if we should retry
        if task.get("retry_count", 0) < task.get("max_retries", 3):
            task["retry_count"] += 1
            self._log("WARNING", "TaskScheduler", task_id, agent_id, task.get("pipeline_run_id"),
                      f"Task failed, retrying ({task['retry_count']}/{task['max_retries']}): {error}")
            
            # Re-queue the task
            task["status"] = TaskStatus.PENDING
            task["last_error"] = error
            self.pending_tasks.append(task)
            
            # Update agent status
            if agent_id and agent_id in self.orchestration_manager.agents:
                agent = self.orchestration_manager.agents[agent_id]
                agent.set_status("idle")
            
            del self.active_tasks[task_id]
            return
        
        # Max retries reached - mark as failed
        completed_at = datetime.utcnow().isoformat()
        
        if task.get("started_at"):
            started = datetime.fromisoformat(task["started_at"])
            completed = datetime.fromisoformat(completed_at)
            duration = (completed - started).total_seconds()
            task["execution_duration_seconds"] = duration
        
        task["status"] = TaskStatus.FAILED
        task["completed_at"] = completed_at
        task["error"] = error
        
        # Store in failed tasks
        self.failed_tasks[task_id] = task.copy()
        
        # Update agent status
        if agent_id and agent_id in self.orchestration_manager.agents:
            agent = self.orchestration_manager.agents[agent_id]
            agent.set_status("idle")
            agent.fail_task(task_id)
        
        # Remove from active tasks
        del self.active_tasks[task_id]
        
        self._log("ERROR", "TaskScheduler", task_id, agent_id, task.get("pipeline_run_id"),
                  f"Task failed permanently: {task_id} - {error}")
        
        # Notify pipeline manager if callback is set
        if self.on_task_complete:
            await self.on_task_complete(task_id, task)
    
    async def _handle_task_error(self, task_id: str, agent_id: str, error: str) -> None:
        """
        Handles task execution errors with retry logic.
        """
        await self._fail_task(task_id, error)
    
    async def _check_timeouts(self) -> None:
        """
        Checks for timed out tasks.
        """
        current_time = datetime.utcnow()
        
        for task_id, task in list(self.active_tasks.items()):
            if task.get("started_at"):
                started = datetime.fromisoformat(task["started_at"])
                elapsed = (current_time - started).total_seconds()
                timeout = task.get("timeout_seconds", 300)
                
                if elapsed > timeout:
                    await self._fail_task(task_id, f"Task timed out after {elapsed:.1f} seconds")
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancels a task if it hasn't started yet.
        """
        # Check pending tasks
        for i, task in enumerate(self.pending_tasks):
            if task["id"] == task_id:
                task["status"] = TaskStatus.CANCELLED
                task["cancelled_at"] = datetime.utcnow().isoformat()
                self.archived_tasks[task_id] = task.copy()
                self.pending_tasks.pop(i)
                self._log("INFO", "TaskScheduler", task_id, None, None,
                          f"Task cancelled: {task_id}")
                return True
        
        # Check queued tasks
        for i, task in enumerate(self.queued_tasks):
            if task["id"] == task_id:
                task["status"] = TaskStatus.CANCELLED
                task["cancelled_at"] = datetime.utcnow().isoformat()
                self.archived_tasks[task_id] = task.copy()
                self.queued_tasks.pop(i)
                self._log("INFO", "TaskScheduler", task_id, None, None,
                          f"Task cancelled: {task_id}")
                return True
        
        return False
    
    def archive_task(self, task_id: str) -> bool:
        """
        Archives a completed or failed task.
        """
        task = None
        
        if task_id in self.completed_tasks:
            task = self.completed_tasks.pop(task_id)
        elif task_id in self.failed_tasks:
            task = self.failed_tasks.pop(task_id)
        
        if task:
            task["status"] = TaskStatus.ARCHIVED
            task["archived_at"] = datetime.utcnow().isoformat()
            self.archived_tasks[task_id] = task
            self._log("INFO", "TaskScheduler", task_id, task.get("agent_id"), None,
                      f"Task archived: {task_id}")
            return True
        
        return False
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a task from any storage.
        """
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        if task_id in self.failed_tasks:
            return self.failed_tasks[task_id]
        if task_id in self.archived_tasks:
            return self.archived_tasks[task_id]
        for task in self.pending_tasks:
            if task["id"] == task_id:
                return task
        for task in self.queued_tasks:
            if task["id"] == task_id:
                return task
        return None
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Dict[str, Any]]:
        """
        Returns all tasks with a specific status.
        """
        if status == TaskStatus.PENDING:
            return self.pending_tasks.copy()
        elif status == TaskStatus.QUEUED:
            return self.queued_tasks.copy()
        elif status == TaskStatus.RUNNING:
            return list(self.active_tasks.values())
        elif status == TaskStatus.COMPLETED:
            return list(self.completed_tasks.values())
        elif status == TaskStatus.FAILED:
            return list(self.failed_tasks.values())
        elif status == TaskStatus.CANCELLED:
            return [t for t in self.archived_tasks.values() if t.get("status") == TaskStatus.CANCELLED]
        elif status == TaskStatus.ARCHIVED:
            return list(self.archived_tasks.values())
        return []
    
    def _log(self, level: str, component: str, task_id: Optional[str], 
             agent_id: Optional[str], pipeline_run_id: Optional[str], message: str) -> None:
        """
        Structured logging (simplified).
        """
        # Use simple print for now to avoid logging issues
        print(f"[{level}] {component}: {message}")
