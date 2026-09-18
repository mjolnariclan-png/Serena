"""
Event-Driven Task Creation for Serena Agent Ecosystem
Phase 3: Event-triggered task creation using Phase 2 infrastructure

This module enables events to trigger tasks that go through the normal execution pipeline.
"""

import time
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

# Try to import Phase 2 infrastructure
try:
    from agents.event_system import EventBus, EventType
    from agents.task_queue import get_task_queue
    from core_data_contracts import Task, generate_task_id
    EVENT_DRIVEN_AVAILABLE = True
except ImportError:
    EVENT_DRIVEN_AVAILABLE = False


class EventDrivenTaskCreator:
    """
    Creates tasks in response to events.
    
    Phase 3: Event-triggered tasks go through the normal execution pipeline.
    No direct tool execution from events - events only create Tasks.
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize event-driven task creator.
        
        Args:
            event_bus: The EventBus to subscribe to
        """
        self.event_bus = event_bus
        self.task_queue = None
        self.event_handlers = {}  # event_type -> list of handlers
        
        if EVENT_DRIVEN_AVAILABLE:
            self.task_queue = get_task_queue()
        
        # Subscribe to events if event bus is provided
        if self.event_bus:
            self._subscribe_to_events()
    
    def _subscribe_to_events(self):
        """Subscribe to relevant event types."""
        if not self.event_bus:
            return
        
        # Subscribe to system events
        self.event_bus.subscribe(EventType.SYSTEM_WARNING, self._handle_system_warning)
        self.event_bus.subscribe(EventType.SYSTEM_FAILURE, self._handle_system_failure)
        
        # Subscribe to agent events
        self.event_bus.subscribe(EventType.AGENT_ERROR, self._handle_agent_error)
        
        # Subscribe to domain-specific events
        self.event_bus.subscribe(EventType.MEDIA_RECEIVED, self._handle_media_received)
        self.event_bus.subscribe(EventType.PHOTO_RECEIVED, self._handle_photo_received)
    
    def register_event_handler(self, event_type: EventType, handler: Callable[[Dict], Optional[Task]]):
        """
        Register a custom event handler.
        
        Args:
            event_type: The event type to handle
            handler: Function that takes event data and returns a Task or None
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def _handle_system_warning(self, event):
        """Handle system warning events."""
        # Example: Create a maintenance task when system warning occurs
        if not self.task_queue:
            return
        
        task = Task(
            task_id=generate_task_id(),
            goal=f"Investigate system warning: {event.data.get('message', 'Unknown')}",
            priority=7,
            task_type="system_maintenance",
            agent_id="ServerAgent",
            context={"event": event.to_dict()},
            metadata={"triggered_by_event": True, "event_type": "system_warning"}
        )
        
        self.task_queue.enqueue(task)
        print(f"Created task from system warning: {task.task_id}")
    
    def _handle_system_failure(self, event):
        """Handle system failure events."""
        if not self.task_queue:
            return
        
        task = Task(
            task_id=generate_task_id(),
            goal=f"Handle system failure: {event.data.get('message', 'Unknown')}",
            priority=9,  # High priority for failures
            task_type="system_maintenance",
            agent_id="ServerAgent",
            context={"event": event.to_dict()},
            metadata={"triggered_by_event": True, "event_type": "system_failure"}
        )
        
        self.task_queue.enqueue(task)
        print(f"Created task from system failure: {task.task_id}")
    
    def _handle_agent_error(self, event):
        """Handle agent error events."""
        if not self.task_queue:
            return
        
        task = Task(
            task_id=generate_task_id(),
            goal=f"Investigate agent error: {event.data.get('error', 'Unknown')}",
            priority=6,
            task_type="system_maintenance",
            agent_id="ServerAgent",
            context={"event": event.to_dict()},
            metadata={"triggered_by_event": True, "event_type": "agent_error"}
        )
        
        self.task_queue.enqueue(task)
        print(f"Created task from agent error: {task.task_id}")
    
    def _handle_media_received(self, event):
        """Handle media received events."""
        if not self.task_queue:
            return
        
        task = Task(
            task_id=generate_task_id(),
            goal="Process new media files",
            priority=5,
            task_type="media_operation",
            agent_id="MediaAgent",
            context={"event": event.to_dict()},
            metadata={"triggered_by_event": True, "event_type": "media_received"}
        )
        
        self.task_queue.enqueue(task)
        print(f"Created task from media received: {task.task_id}")
    
    def _handle_photo_received(self, event):
        """Handle photo received events."""
        if not self.task_queue:
            return
        
        task = Task(
            task_id=generate_task_id(),
            goal="Organize new photos",
            priority=5,
            task_type="photo_organization",
            agent_id="PhotoAgent",
            context={"event": event.to_dict()},
            metadata={"triggered_by_event": True, "event_type": "photo_received"}
        )
        
        self.task_queue.enqueue(task)
        print(f"Created task from photo received: {task.task_id}")
    
    def handle_event(self, event):
        """
        Process an event and potentially create a task.
        
        Args:
            event: The event to process
        """
        # Check for custom handlers
        event_type = event.event_type
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    task = handler(event.data)
                    if task and self.task_queue:
                        self.task_queue.enqueue(task)
                        print(f"Created task from custom handler: {task.task_id}")
                except Exception as e:
                    print(f"Error in event handler: {e}")


# Global instance
_event_driven_creator = None

def get_event_driven_creator(event_bus: Optional[EventBus] = None) -> EventDrivenTaskCreator:
    """Get or create the global EventDrivenTaskCreator instance."""
    global _event_driven_creator
    if _event_driven_creator is None:
        _event_driven_creator = EventDrivenTaskCreator(event_bus)
    return _event_driven_creator


if __name__ == "__main__":
    # Test the event-driven task creator
    print("Testing Event-Driven Task Creator...")
    
    if not EVENT_DRIVEN_AVAILABLE:
        print("Phase 2 infrastructure not available")
    else:
        from agents.event_system import EventBus, EventType
        
        # Create event bus and task creator
        event_bus = EventBus()
        creator = EventDrivenTaskCreator(event_bus)
        
        # Test system warning event
        event_bus.publish_event(
            EventType.SYSTEM_WARNING,
            "System",
            {"message": "Disk space low"}
        )
        
        # Test media received event
        event_bus.publish_event(
            EventType.MEDIA_RECEIVED,
            "MediaScanner",
            {"count": 5}
        )
        
        # Check queue
        queue = get_task_queue()
        print(f"Queue size after events: {queue.size()}")
        
        print("\n✅ Event-Driven Task Creator Test Passed!")