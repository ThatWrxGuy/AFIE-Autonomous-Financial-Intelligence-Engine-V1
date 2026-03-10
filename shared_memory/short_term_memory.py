"""
Short Term Memory for AFC3.

Stores:
- signals
- pipeline state
- macro regime
- recent task results
"""

from typing import Dict, Any, List, Optional
import time


class ShortTermMemory:
    """
    Persistent shared memory system for transient, real-time data.
    
    Stores:
    - signals
    - pipeline state
    - macro regime
    - recent task results
    """
    def __init__(self):
        self.memory: Dict[str, Dict[str, Any]] = {}
        
        # Predefined categories for structured storage
        self._signals: List[Dict[str, Any]] = []
        self._pipeline_state: Dict[str, Any] = {}
        self._macro_regime: Optional[str] = None
        self._recent_tasks: List[Dict[str, Any]] = []
        self._max_recent_tasks = 100

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Sets a value in the short-term memory with an optional TTL.
        """
        self.memory[key] = {
            "value": value,
            "timestamp": time.time(),
            "ttl": ttl
        }

    def get(self, key: str) -> Any:
        """
        Retrieves a value from the short-term memory.
        """
        if key in self.memory:
            item = self.memory[key]
            if time.time() - item["timestamp"] < item["ttl"]:
                return item["value"]
            else:
                del self.memory[key]
        return None

    def delete(self, key: str) -> None:
        """
        Deletes a value from the short-term memory.
        """
        if key in self.memory:
            del self.memory[key]

    def list_keys(self) -> List[str]:
        """
        Lists all keys in the short-term memory.
        """
        return list(self.memory.keys())
    
    # --- Structured storage methods ---
    
    def add_signal(self, signal: Dict[str, Any]) -> None:
        """
        Add a signal to short-term memory.
        
        Args:
            signal: Signal data to store
        """
        signal["timestamp"] = time.time()
        self._signals.append(signal)
        
        # Keep only recent signals (last 100)
        if len(self._signals) > 100:
            self._signals = self._signals[-100:]
        
        # Also store in key-value memory
        self.set(f"signal_{signal.get('id', len(self._signals))}", signal, ttl=3600)
    
    def get_signals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent signals.
        
        Args:
            limit: Maximum number of signals to return
            
        Returns:
            List of recent signals
        """
        return self._signals[-limit:]
    
    def set_pipeline_state(self, state: Dict[str, Any]) -> None:
        """
        Store pipeline state.
        
        Args:
            state: Pipeline state data
        """
        self._pipeline_state = state
        self.set("pipeline_state", state, ttl=3600)
    
    def get_pipeline_state(self) -> Dict[str, Any]:
        """
        Get pipeline state.
        
        Returns:
            Pipeline state data
        """
        return self._pipeline_state
    
    def set_macro_regime(self, regime: str, confidence: float = 1.0) -> None:
        """
        Store macro regime.
        
        Args:
            regime: Current macro regime
            confidence: Confidence level
        """
        self._macro_regime = regime
        self.set("macro_regime", {"regime": regime, "confidence": confidence}, ttl=3600)
    
    def get_macro_regime(self) -> Optional[Dict[str, Any]]:
        """
        Get macro regime.
        
        Returns:
            Macro regime data
        """
        return self.get("macro_regime")
    
    def add_task_result(self, task_result: Dict[str, Any]) -> None:
        """
        Add a task result to recent tasks.
        
        Args:
            task_result: Task result data
        """
        task_result["timestamp"] = time.time()
        self._recent_tasks.append(task_result)
        
        # Keep only recent tasks
        if len(self._recent_tasks) > self._max_recent_tasks:
            self._recent_tasks = self._recent_tasks[-self._max_recent_tasks:]
        
        # Also store in key-value memory
        task_id = task_result.get("task_id", f"task_{len(self._recent_tasks)}")
        self.set(f"task_{task_id}", task_result, ttl=3600)
    
    def get_recent_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent task results.
        
        Args:
            limit: Maximum number of tasks to return
            
        Returns:
            List of recent task results
        """
        return self._recent_tasks[-limit:]
    
    def clear_expired(self) -> int:
        """
        Clear expired entries from memory.
        
        Returns:
            Number of entries cleared
        """
        cleared = 0
        current_time = time.time()
        
        expired_keys = [
            key for key, item in self.memory.items()
            if current_time - item["timestamp"] >= item["ttl"]
        ]
        
        for key in expired_keys:
            del self.memory[key]
            cleared += 1
        
        return cleared
