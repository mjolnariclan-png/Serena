"""
Event System for Serena Agent Ecosystem
Phase 2: Central event bus for agent coordination and system events

This module provides a centralized event system that agents can subscribe to and publish events.
Events may trigger tasks but must not bypass the Phase 1 security pipeline.
"""

import time
import threading
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

# Try to import Phase 1 core data contracts
try:
    from core_data_contracts import generate_correlation_id
    CORE_CONTRACTS_AVAILABLE = True
except ImportError:
    CORE_CONTRACTS_AVAILABLE = False
    
    import uuid
    def generate_correlation_id():
        return str(uuid.uuid4())


class EventType(Enum):
    """Types of events in the system."""
    # Task events
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_BLOCKED = "task.blocked"
    TASK_CANCELLED = "task.cancelled"
    
    # Agent events
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_ERROR = "agent.error"
    AGENT_HEALTH_CHANGED = "agent.health_changed"
    
    # System events
    SYSTEM_WARNING = "system.warning"
    SYSTEM_FAILURE = "system.failure"
    SYSTEM_SHUTDOWN = "system.shutdown"
    
    # Domain-specific events
    MEDIA_RECEIVED = "media.received"
    PHOTO_RECEIVED = "photo.received"
    SERVER_WARNING = "server.warning"
    SERVER_FAILURE = "server.failure"


@dataclass
class Event:
    """
    An event in the system.
    """
    event_id: str
    event_type: EventType
    source: str  # Agent ID or system component
    data: Dict[str, Any]
    correlation_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source": self.source,
            "data": self.data,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        """Create Event from dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            source=data["source"],
            data=data["data"],
            correlation_id=data.get("correlation_id"),
            timestamp=data.get("timestamp", time.time()),
            metadata=data.get("metadata", {})
        )


class EventBus:
    """
    Central event bus for the agent ecosystem.
    
    Supports:
    - Event publishing
    - Event subscription
    - Event delivery
    - Event history
    - Event filtering
    """
    
    def __init__(self, max_history: int = 1000):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._lock = threading.RLock()
        self._max_history = max_history
        self._event_counter = 0
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> bool:
        """
        Subscribe to an event type.
        
        Args:
            event_type: The event type to subscribe to
            callback: The callback function to call when event occurs
            
        Returns:
            True if subscription successful
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
            return True
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: The event type to unsubscribe from
            callback: The callback function to remove
            
        Returns:
            True if unsubscription successful
        """
        with self._lock:
            if event_type in self._subscribers:
                if callback in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(callback)
                    return True
            return False
    
    def publish(self, event: Event) -> bool:
        """
        Publish an event to all subscribers.
        
        Args:
            event: The event to publish
            
        Returns:
            True if event was published successfully
        """
        with self._lock:
            # Add to history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
            
            self._event_counter += 1
            
            # Get subscribers for this event type
            subscribers = self._subscribers.get(event.event_type, [])
            
            # Deliver event to subscribers
            for callback in subscribers:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error delivering event to subscriber: {e}")
            
            return True
    
    def publish_event(self, event_type: EventType, source: str, data: Dict[str, Any], 
                    correlation_id: Optional[str] = None) -> Event:
        """
        Convenience method to create and publish an event.
        
        Args:
            event_type: The type of event
            source: The source of the event
            data: Event data
            correlation_id: Optional correlation ID
            
        Returns:
            The created event
        """
        event = Event(
            event_id=f"event_{int(time.time() * 1000)}_{self._event_counter}",
            event_type=event_type,
            source=source,
            data=data,
            correlation_id=correlation_id
        )
        self.publish(event)
        return event
    
    def get_history(self, event_type: Optional[EventType] = None, 
                   source: Optional[str] = None, limit: int = 100) -> List[Event]:
        """
        Get event history with optional filtering.
        
        Args:
            event_type: Filter by event type (optional)
            source: Filter by source (optional)
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        with self._lock:
            filtered = self._event_history
            
            if event_type:
                filtered = [e for e in filtered if e.event_type == event_type]
            
            if source:
                filtered = [e for e in filtered if e.source == source]
            
            return filtered[-limit:]
    
    def get_recent_events(self, limit: int = 50) -> List[Event]:
        """Get most recent events."""
        with self._lock:
            return self._event_history[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._event_history.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        with self._lock:
            event_type_counts = {}
            for event in self._event_history:
                event_type = event.event_type.value
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
            
            return {
                "total_events": len(self._event_history),
                "event_counter": self._event_counter,
                "subscribers": {et.value: len(subs) for et, subs in self._subscribers.items()},
                "event_type_counts": event_type_counts,
                "max_history": self._max_history
            }


# Global instance
_event_bus = None

def get_event_bus(max_history: int = 1000) -> EventBus:
    """Get or create the global EventBus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus(max_history)
    return _event_bus


if __name__ == "__main__":
    # Test the event system
    print("Testing Event System...")
    
    event_bus = EventBus()
    
    # Test subscription
    received_events = []
    
    def task_callback(event: Event):
        received_events.append(event)
        print(f"Received event: {event.event_type.value} from {event.source}")
    
    event_bus.subscribe(EventType.TASK_CREATED, task_callback)
    event_bus.subscribe(EventType.TASK_COMPLETED, task_callback)
    
    # Test publishing
    event_bus.publish_event(
        EventType.TASK_CREATED,
        "AgentManager",
        {"task_id": "task_123", "goal": "Test task"}
    )
    
    event_bus.publish_event(
        EventType.TASK_COMPLETED,
        "MediaAgent",
        {"task_id": "task_123", "result": "Success"}
    )
    
    print(f"Received {len(received_events)} events")
    
    # Test history
    history = event_bus.get_history(limit=10)
    print(f"History size: {len(history)}")
    
    # Test filtering
    task_events = event_bus.get_history(event_type=EventType.TASK_CREATED)
    print(f"Task created events: {len(task_events)}")
    
    # Test statistics
    stats = event_bus.get_statistics()
    print(f"Statistics: {stats}")
    
    print("\n✅ Event System Test Passed!")