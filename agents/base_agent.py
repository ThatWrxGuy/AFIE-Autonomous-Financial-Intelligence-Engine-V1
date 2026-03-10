"""
Base Agent for AFC3.

Features:
- Agent lifecycle states: idle, busy, running, error, offline
- Metadata fields: current_task_id, tasks_completed, tasks_failed, last_started_at, last_completed_at
- Helper methods: begin_task(), complete_task(), fail_task(), set_status()
- Standardized result envelope
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import uuid
import time
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    """Agent lifecycle states."""
    IDLE = "idle"
    BUSY = "busy"
    RUNNING = "running"
    ERROR = "error"
    OFFLINE = "offline"


class AgentResult:
    """Standardized result envelope for agent responses."""
    
    @staticmethod
    def success(
        agent_id: str,
        agent_type: str,
        action: str,
        task_id: str,
        result: Dict[str, Any],
        duration_seconds: float = 0.0
    ) -> Dict[str, Any]:
        """
        Create a success result envelope.
        
        Args:
            agent_id: Agent ID
            agent_type: Type of agent
            action: Action that was performed
            task_id: Task ID
            result: Result data
            duration_seconds: Execution duration
            
        Returns:
            Standardized success response
        """
        return {
            "status": "success",
            "agent_id": agent_id,
            "agent_type": agent_type,
            "action": action,
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": duration_seconds,
            "result": result
        }
    
    @staticmethod
    def error(
        agent_id: str,
        agent_type: str,
        action: str,
        task_id: str,
        error: str
    ) -> Dict[str, Any]:
        """
        Create an error result envelope.
        
        Args:
            agent_id: Agent ID
            agent_type: Type of agent
            action: Action that was performed
            task_id: Task ID
            error: Error message
            
        Returns:
            Standardized error response
        """
        return {
            "status": "error",
            "agent_id": agent_id,
            "agent_type": agent_type,
            "action": action,
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
            "error": error
        }


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents in the AFC3 system.
    
    Features:
    - Agent lifecycle states: idle, busy, running, error, offline
    - Metadata fields: current_task_id, tasks_completed, tasks_failed, last_started_at, last_completed_at
    - Helper methods: begin_task(), complete_task(), fail_task(), set_status()
    - Standardized result envelope
    """
    
    def __init__(self, name: str, agent_type: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.agent_type = agent_type
        self.status = AgentStatus.IDLE
        
        # Metadata fields
        self.current_task_id: Optional[str] = None
        self.tasks_completed: int = 0
        self.tasks_failed: int = 0
        self.last_started_at: Optional[str] = None
        self.last_completed_at: Optional[str] = None
        
        # Internal state
        self._error_message: Optional[str] = None
    
    def set_status(self, status: str) -> None:
        """
        Set agent status.
        
        Args:
            status: New status (idle, busy, running, error, offline)
        """
        if status in [s.value for s in AgentStatus]:
            self.status = AgentStatus(status)
    
    def begin_task(self, task_id: str) -> None:
        """
        Mark the beginning of a task execution.
        
        Args:
            task_id: ID of the task being started
        """
        self.current_task_id = task_id
        self.status = AgentStatus.BUSY
        self.last_started_at = datetime.utcnow().isoformat()
        self._error_message = None
    
    def complete_task(self, task_id: str) -> None:
        """
        Mark a task as completed.
        
        Args:
            task_id: ID of the completed task
        """
        if self.current_task_id == task_id:
            self.current_task_id = None
        self.tasks_completed += 1
        self.status = AgentStatus.IDLE
        self.last_completed_at = datetime.utcnow().isoformat()
    
    def fail_task(self, task_id: str) -> None:
        """
        Mark a task as failed.
        
        Args:
            task_id: ID of the failed task
        """
        if self.current_task_id == task_id:
            self.current_task_id = None
        self.tasks_failed += 1
        self.status = AgentStatus.IDLE
        self.last_completed_at = datetime.utcnow().isoformat()
    
    def set_error(self, error_message: str) -> None:
        """
        Set agent error state.
        
        Args:
            error_message: Error message
        """
        self._error_message = error_message
        self.status = AgentStatus.ERROR
    
    def clear_error(self) -> None:
        """Clear error state."""
        self._error_message = None
        if self.status == AgentStatus.ERROR:
            self.status = AgentStatus.IDLE
    
    def get_info(self) -> Dict[str, Any]:
        """
        Returns information about the agent.
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.agent_type,
            "status": self.status.value,
            "current_task_id": self.current_task_id,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "last_started_at": self.last_started_at,
            "last_completed_at": self.last_completed_at,
            "error": self._error_message
        }
    
    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a given task and returns the result.
        
        Must return standardized result envelope using AgentResult.success() or AgentResult.error()
        """
        pass

    @abstractmethod
    async def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handles incoming messages from other agents or the Control Core.
        """
        pass
