"""
Long Term Memory for AFC3.

Stores:
- historical experiments
- strategy performance
- model outputs
"""

from typing import Dict, Any, List, Optional
import time
from datetime import datetime
import uuid


class Experiment:
    """Represents a historical experiment."""
    
    def __init__(self, experiment_id: str, name: str, config: Dict[str, Any]):
        self.experiment_id = experiment_id
        self.name = name
        self.config = config
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        self.metrics: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}
        self.tags: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "config": self.config,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metrics": self.metrics,
            "results": self.results,
            "tags": self.tags
        }


class LongTermMemory:
    """
    Long-term memory system for persistent data storage.
    
    Stores:
    - historical experiments
    - strategy performance
    - model outputs
    """
    
    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
        self.strategy_performance: Dict[str, Dict[str, Any]] = {}
        self.model_outputs: Dict[str, Dict[str, Any]] = {}
        self._max_experiments = 1000
        self._max_strategies = 500
        self._max_models = 500
    
    # --- Experiment methods ---
    
    def create_experiment(self, name: str, config: Dict[str, Any], 
                         tags: List[str] = None) -> str:
        """
        Create a new experiment.
        
        Args:
            name: Experiment name
            config: Experiment configuration
            tags: Optional tags
            
        Returns:
            Experiment ID
        """
        experiment_id = str(uuid.uuid4())
        experiment = Experiment(experiment_id, name, config)
        experiment.tags = tags or []
        
        self.experiments[experiment_id] = experiment
        
        # Limit number of experiments
        if len(self.experiments) > self._max_experiments:
            # Remove oldest
            oldest = min(self.experiments.values(), key=lambda e: e.created_at)
            del self.experiments[oldest.experiment_id]
        
        return experiment_id
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """
        Get an experiment by ID.
        
        Args:
            experiment_id: Experiment ID
            
        Returns:
            Experiment or None
        """
        return self.experiments.get(experiment_id)
    
    def update_experiment(self, experiment_id: str, 
                         metrics: Dict[str, Any] = None,
                         results: Dict[str, Any] = None) -> bool:
        """
        Update an experiment with metrics and results.
        
        Args:
            experiment_id: Experiment ID
            metrics: Metrics to update
            results: Results to update
            
        Returns:
            True if updated successfully
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return False
        
        if metrics:
            experiment.metrics.update(metrics)
        if results:
            experiment.results.update(results)
        
        experiment.updated_at = datetime.utcnow().isoformat()
        return True
    
    def list_experiments(self, tags: List[str] = None, 
                        limit: int = 100) -> List[Experiment]:
        """
        List experiments, optionally filtered by tags.
        
        Args:
            tags: Filter by tags
            limit: Maximum number to return
            
        Returns:
            List of experiments
        """
        experiments = list(self.experiments.values())
        
        if tags:
            experiments = [e for e in experiments 
                         if any(tag in e.tags for tag in tags)]
        
        # Sort by updated_at descending
        experiments.sort(key=lambda e: e.updated_at, reverse=True)
        
        return experiments[:limit]
    
    # --- Strategy performance methods ---
    
    def store_strategy_performance(self, strategy_id: str, 
                                    performance: Dict[str, Any]) -> None:
        """
        Store strategy performance data.
        
        Args:
            strategy_id: Strategy ID
            performance: Performance metrics
        """
        performance["stored_at"] = datetime.utcnow().isoformat()
        self.strategy_performance[strategy_id] = performance
        
        # Limit number of strategies
        if len(self.strategy_performance) > self._max_strategies:
            oldest = min(self.strategy_performance.items(), 
                        key=lambda x: x[1].get("stored_at", ""))
            del self.strategy_performance[oldest[0]]
    
    def get_strategy_performance(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """
        Get strategy performance data.
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Performance data or None
        """
        return self.strategy_performance.get(strategy_id)
    
    def list_strategies(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all strategies with performance data.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of strategies with performance
        """
        strategies = [
            {"strategy_id": k, **v} 
            for k, v in self.strategy_performance.items()
        ]
        
        # Sort by stored_at descending
        strategies.sort(key=lambda x: x.get("stored_at", ""), reverse=True)
        
        return strategies[:limit]
    
    # --- Model output methods ---
    
    def store_model_output(self, model_id: str, output: Dict[str, Any]) -> None:
        """
        Store model output.
        
        Args:
            model_id: Model ID
            output: Model output data
        """
        output["stored_at"] = datetime.utcnow().isoformat()
        self.model_outputs[model_id] = output
        
        # Limit number of models
        if len(self.model_outputs) > self._max_models:
            oldest = min(self.model_outputs.items(),
                        key=lambda x: x[1].get("stored_at", ""))
            del self.model_outputs[oldest[0]]
    
    def get_model_output(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get model output.
        
        Args:
            model_id: Model ID
            
        Returns:
            Model output or None
        """
        return self.model_outputs.get(model_id)
    
    def list_models(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all models with outputs.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of models with outputs
        """
        models = [
            {"model_id": k, **v}
            for k, v in self.model_outputs.items()
        ]
        
        # Sort by stored_at descending
        models.sort(key=lambda x: x.get("stored_at", ""), reverse=True)
        
        return models[:limit]
    
    # --- Statistics ---
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_experiments": len(self.experiments),
            "total_strategies": len(self.strategy_performance),
            "total_models": len(self.model_outputs),
            "oldest_experiment": min(
                (e.created_at for e in self.experiments.values()),
                default=None
            ),
            "newest_experiment": max(
                (e.updated_at for e in self.experiments.values()),
                default=None
            )
        }
