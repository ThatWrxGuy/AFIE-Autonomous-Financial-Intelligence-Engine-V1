"""
Event Bus for AFC3 - Event-driven messaging system.

Provides:
- publish(event)
- subscribe(event_type)
- unsubscribe()

Event schema:
{
    event_id
    event_type
    source
    target
    timestamp
    payload
}

Example events:
- strategy.generated
- simulation.completed
- macro.regime_changed
- task.completed
- task.failed
"""

import uuid
from typing import Callable, Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import asyncio


@dataclass
class Event:
    """Event schema for the event bus."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    source: str = ""
    target: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "target": self.target,
            "timestamp": self.timestamp,
            "payload": self.payload
        }


class EventBus:
    """
    Event-driven messaging system for AFC3.
    
    Allows components to publish and subscribe to events.
    """
    
    # Pre-defined event types
    STRATEGY_GENERATED = "strategy.generated"
    SIMULATION_COMPLETED = "simulation.completed"
    SIMULATION_FAILED = "simulation.failed"
    MACRO_REGIME_CHANGED = "macro.regime_changed"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_STARTED = "task.started"
    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"
    AGENT_REGISTERED = "agent.registered"
    AGENT_STATUS_CHANGED = "agent.status_changed"
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000  # Limit history size
    
    def subscribe(self, event_type: str, callback: Callable) -> str:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Async function to call when event is published
            
        Returns:
            Subscription ID that can be used to unsubscribe
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        subscription_id = str(uuid.uuid4())
        self._subscribers[event_type].append({
            "id": subscription_id,
            "callback": callback
        })
        
        return subscription_id
    
    def unsubscribe(self, event_type: str, subscription_id: str) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            subscription_id: ID returned from subscribe()
            
        Returns:
            True if unsubscribed successfully
        """
        if event_type not in self._subscribers:
            return False
        
        self._subscribers[event_type] = [
            s for s in self._subscribers[event_type] 
            if s["id"] != subscription_id
        ]
        return True
    
    async def publish(self, event: Event) -> List[Any]:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
            
        Returns:
            List of results from all callbacks
        """
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # Get subscribers for this event type
        callbacks = self._subscribers.get(event.event_type, [])
        
        # Also notify wildcard subscribers
        callbacks.extend(self._subscribers.get("*", []))
        
        # Call all subscribers
        results = []
        for subscriber in callbacks:
            try:
                result = await subscriber["callback"](event)
                results.append(result)
            except Exception as e:
                # Log error but don't break other subscribers
                print(f"Error in event subscriber: {e}")
        
        return results
    
    def publish_sync(self, event: Event) -> List[Any]:
        """
        Synchronous version of publish (for non-async contexts).
        """
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # Get subscribers for this event type
        callbacks = self._subscribers.get(event.event_type, [])
        
        # Also notify wildcard subscribers
        callbacks.extend(self._subscribers.get("*", []))
        
        # Call all subscribers synchronously
        results = []
        for subscriber in callbacks:
            try:
                callback = subscriber["callback"]
                # Check if callback is async
                if asyncio.iscoroutinefunction(callback):
                    print("Warning: Using publish_sync with async callback")
                else:
                    result = callback(event)
                    results.append(result)
            except Exception as e:
                print(f"Error in event subscriber: {e}")
        
        return results
    
    def get_event_history(self, event_type: Optional[str] = None, 
                          limit: int = 100) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Optional filter by event type
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        if event_type:
            events = [e for e in self._event_history if e.event_type == event_type]
        else:
            events = self._event_history
        
        return events[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
    
    def get_subscriber_count(self, event_type: str) -> int:
        """Get number of subscribers for an event type."""
        return len(self._subscribers.get(event_type, []))


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create the global event bus."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def publish_event(event_type: str, source: str, 
                        payload: Dict[str, Any] = None,
                        target: Optional[str] = None) -> Event:
    """
    Convenience function to publish an event.
    
    Args:
        event_type: Type of event
        source: Source component
        payload: Event payload
        target: Optional target component
        
    Returns:
        Published event
    """
    event = Event(
        event_type=event_type,
        source=source,
        target=target,
        payload=payload or {}
    )
    
    bus = get_event_bus()
    await bus.publish(event)
    return event
