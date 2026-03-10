"""
Experiment Store for AFC3.

Records:
- pipeline_run_id
- step results
- validation metrics
- strategy acceptance or rejection
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid


class ExperimentRecord:
    """Represents a single experiment/pipeline run record."""
    
    def __init__(self, pipeline_run_id: str, name: str):
        self.pipeline_run_id = pipeline_run_id
        self.name = name
        self.created_at = datetime.utcnow().isoformat()
        self.step_results: List[Dict[str, Any]] = []
        self.validation_metrics: Dict[str, Any] = {}
        self.status: str = "running"  # running, approved, rejected
        self.final_result: Optional[Dict[str, Any]] = None
        self.execution_duration: Optional[float] = None
        self.error: Optional[str] = None
    
    def add_step_result(self, step_name: str, agent_type: str, 
                       result: Dict[str, Any], status: str) -> None:
        """Add a step result to the experiment."""
        self.step_results.append({
            "step_name": step_name,
            "agent_type": agent_type,
            "result": result,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def set_validation_metrics(self, metrics: Dict[str, Any]) -> None:
        """Set validation metrics."""
        self.validation_metrics = metrics
    
    def approve_strategy(self, reason: str = "") -> None:
        """Mark strategy as approved."""
        self.status = "approved"
        self.validation_metrics["approval_reason"] = reason
        self.validation_metrics["approved_at"] = datetime.utcnow().isoformat()
    
    def reject_strategy(self, reason: str) -> None:
        """Mark strategy as rejected."""
        self.status = "rejected"
        self.validation_metrics["rejection_reason"] = reason
        self.validation_metrics["rejected_at"] = datetime.utcnow().isoformat()
    
    def complete(self, final_result: Dict[str, Any], 
                 duration: float, error: Optional[str] = None) -> None:
        """Complete the experiment record."""
        self.final_result = final_result
        self.execution_duration = duration
        self.error = error
        if error:
            self.status = "failed"
        elif self.status == "running":
            self.status = "completed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pipeline_run_id": self.pipeline_run_id,
            "name": self.name,
            "created_at": self.created_at,
            "step_results": self.step_results,
            "validation_metrics": self.validation_metrics,
            "status": self.status,
            "final_result": self.final_result,
            "execution_duration": self.execution_duration,
            "error": self.error
        }


class ExperimentStore:
    """
    Experiment store for recording pipeline runs.
    
    Records:
    - pipeline_run_id
    - step results
    - validation metrics
    - strategy acceptance or rejection
    """
    
    def __init__(self):
        self.experiments: Dict[str, ExperimentRecord] = {}
        self._max_experiments = 1000
    
    def create_experiment(self, pipeline_run_id: str, name: str) -> ExperimentRecord:
        """
        Create a new experiment record.
        
        Args:
            pipeline_run_id: Pipeline run ID
            name: Experiment name
            
        Returns:
            ExperimentRecord
        """
        experiment = ExperimentRecord(pipeline_run_id, name)
        self.experiments[pipeline_run_id] = experiment
        return experiment
    
    def get_experiment(self, pipeline_run_id: str) -> Optional[ExperimentRecord]:
        """
        Get an experiment by pipeline run ID.
        
        Args:
            pipeline_run_id: Pipeline run ID
            
        Returns:
            ExperimentRecord or None
        """
        return self.experiments.get(pipeline_run_id)
    
    def update_experiment(self, pipeline_run_id: str,
                         step_name: str = None,
                         agent_type: str = None,
                         result: Dict[str, Any] = None,
                         status: str = None,
                         validation_metrics: Dict[str, Any] = None,
                         final_result: Dict[str, Any] = None,
                         execution_duration: float = None,
                         error: str = None) -> bool:
        """
        Update an experiment record.
        
        Args:
            pipeline_run_id: Pipeline run ID
            step_name: Step name (optional)
            agent_type: Agent type (optional)
            result: Step result (optional)
            status: Step status (optional)
            validation_metrics: Validation metrics (optional)
            final_result: Final result (optional)
            execution_duration: Execution duration (optional)
            error: Error message (optional)
            
        Returns:
            True if updated successfully
        """
        experiment = self.experiments.get(pipeline_run_id)
        if not experiment:
            return False
        
        if step_name and agent_type and result and status:
            experiment.add_step_result(step_name, agent_type, result, status)
        
        if validation_metrics:
            experiment.set_validation_metrics(validation_metrics)
        
        if final_result is not None or execution_duration is not None:
            experiment.complete(
                final_result or {},
                execution_duration or 0,
                error
            )
        
        return True
    
    def approve_strategy(self, pipeline_run_id: str, reason: str = "") -> bool:
        """
        Approve a strategy.
        
        Args:
            pipeline_run_id: Pipeline run ID
            reason: Approval reason
            
        Returns:
            True if approved successfully
        """
        experiment = self.experiments.get(pipeline_run_id)
        if not experiment:
            return False
        
        experiment.approve_strategy(reason)
        return True
    
    def reject_strategy(self, pipeline_run_id: str, reason: str) -> bool:
        """
        Reject a strategy.
        
        Args:
            pipeline_run_id: Pipeline run ID
            reason: Rejection reason
            
        Returns:
            True if rejected successfully
        """
        experiment = self.experiments.get(pipeline_run_id)
        if not experiment:
            return False
        
        experiment.reject_strategy(reason)
        return True
    
    def list_experiments(self, status: str = None, 
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        List experiments, optionally filtered by status.
        
        Args:
            status: Filter by status (running, approved, rejected, completed, failed)
            limit: Maximum number to return
            
        Returns:
            List of experiments
        """
        experiments = list(self.experiments.values())
        
        if status:
            experiments = [e for e in experiments if e.status == status]
        
        # Sort by created_at descending
        experiments.sort(key=lambda e: e.created_at, reverse=True)
        
        return [e.to_dict() for e in experiments[:limit]]
    
    def get_approved_strategies(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all approved strategies.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of approved strategies
        """
        approved = [
            e for e in self.experiments.values() 
            if e.status == "approved"
        ]
        approved.sort(key=lambda e: e.created_at, reverse=True)
        return [e.to_dict() for e in approved[:limit]]
    
    def get_rejected_strategies(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all rejected strategies.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of rejected strategies
        """
        rejected = [
            e for e in self.experiments.values()
            if e.status == "rejected"
        ]
        rejected.sort(key=lambda e: e.created_at, reverse=True)
        return [e.to_dict() for e in rejected[:limit]]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get experiment store statistics.
        
        Returns:
            Statistics dictionary
        """
        statuses = {}
        for experiment in self.experiments.values():
            statuses[experiment.status] = statuses.get(experiment.status, 0) + 1
        
        return {
            "total_experiments": len(self.experiments),
            "by_status": statuses,
            "approved_count": statuses.get("approved", 0),
            "rejected_count": statuses.get("rejected", 0)
        }
