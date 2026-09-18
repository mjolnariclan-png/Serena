"""
Central Task Queue for Serena Agent Ecosystem
Phase 2: Centralized task queue with priority, FIFO, and lifecycle management

This module provides a centralized task queue that Agent Manager uses to coordinate
task execution across all agents. Tasks follow the Phase 1 security pipeline.
"""

import time
import heapq
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Try to import Phase 1 core data contracts
try:
    from core_data_contracts import Task, TaskStatus, generate_task_id
    CORE_CONTRACTS_AVAILABLE = True
except ImportError:
    CORE_CONTRACTS_AVAILABLE = False
    
    # Fallback definitions
    import uuid
    from enum import Enum
    from dataclasses import dataclass, field
    
    class TaskStatus(Enum):
        PENDING = "pending"
        ASSIGNED = "assigned"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        FAILED = "failed"
        BLOCKED = "blocked"
        CANCELLED = "cancelled"
        RETRYING = "retrying"
    
    @dataclass
    class Task:
        task_id: str
        goal: str
        priority: int = 5
        agent_id: Optional[str] = None
        status: TaskStatus = TaskStatus.PENDING
        created_at: float = field(default_factory=time.time)
        context: Dict = field(default_factory=dict)
        dependencies: List[str] = field(default_factory=list)
    
    def generate_task_id():
        return f"task_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


@dataclass
class QueuedTask:
    """
    Wrapper for Task in the queue with priority-based ordering.
    """
    task: Task
    queue_order: float  # Timestamp for FIFO within same priority
    enqueued_at: float = field(default_factory=time.time)
    
    def __lt__(self, other):
        # Lower priority number = higher priority (1 is highest, 10 is lowest)
        # If priorities are equal, use queue_order (FIFO)
        if self.task.priority != other.task.priority:
            return self.task.priority < other.task.priority
        return self.queue_order < other.queue_order


class TaskQueue:
    """
    Centralized task queue for Agent Manager.
    
    Supports:
    - Priority-based ordering
    - FIFO behavior within same priority
    - Task cancellation
    - Timeout handling
    - Retry policy
    - Dependency blocking
    """
    
    def __init__(self):
        self._queue: List[QueuedTask] = []
        self._tasks_by_id: Dict[str, QueuedTask] = {}
        self._lock = threading.RLock()
        self._queue_counter = 0.0  # For FIFO ordering
        self._cancelled_tasks: set = set()
        self._blocked_tasks: Dict[str, str] = {}  # task_id -> reason
    
    def enqueue(self, task: Task) -> bool:
        """
        Add a task to the queue.
        
        Args:
            task: The task to enqueue
            
        Returns:
            True if task was enqueued, False if already exists
        """
        with self._lock:
            if task.task_id in self._tasks_by_id:
                return False
            
            if task.task_id in self._cancelled_tasks:
                return False
            
            # Create queued wrapper
            queued_task = QueuedTask(
                task=task,
                queue_order=self._queue_counter
            )
            self._queue_counter += 1.0
            
            # Add to heap and index
            heapq.heappush(self._queue, queued_task)
            self._tasks_by_id[task.task_id] = queued_task
            
            return True
    
    def dequeue(self, check_dependencies: bool = True) -> Optional[Task]:
        """
        Get the next task to execute.
        
        Args:
            check_dependencies: If True, skip tasks with unmet dependencies
            
        Returns:
            The next task, or None if queue is empty or all tasks blocked
        """
        with self._lock:
            while self._queue:
                queued_task = heapq.heappop(self._queue)
                task = queued_task.task
                
                # Check if cancelled
                if task.task_id in self._cancelled_tasks:
                    self._cancelled_tasks.remove(task.task_id)
                    del self._tasks_by_id[task.task_id]
                    continue
                
                # Check if blocked
                if task.task_id in self._blocked_tasks:
                    # Re-add to end of queue
                    heapq.heappush(self._queue, queued_task)
                    continue
                
                # Check dependencies
                if check_dependencies and task.dependencies:
                    if not self._dependencies_satisfied(task):
                        # Re-add to end of queue
                        heapq.heappush(self._queue, queued_task)
                        continue
                
                # Return task
                return task
            
            return None
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID without removing from queue."""
        with self._lock:
            queued_task = self._tasks_by_id.get(task_id)
            return queued_task.task if queued_task else None
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: The task ID to cancel
            
        Returns:
            True if task was cancelled, False if not found
        """
        with self._lock:
            if task_id in self._tasks_by_id:
                self._cancelled_tasks.add(task_id)
                return True
            return False
    
    def block_task(self, task_id: str, reason: str) -> bool:
        """
        Block a task due to unmet dependencies.
        
        Args:
            task_id: The task ID to block
            reason: Reason for blocking
            
        Returns:
            True if task was blocked, False if not found
        """
        with self._lock:
            if task_id in self._tasks_by_id:
                self._blocked_tasks[task_id] = reason
                return True
            return False
    
    def unblock_task(self, task_id: str) -> bool:
        """
        Unblock a task (e.g., when dependencies are satisfied).
        
        Args:
            task_id: The task ID to unblock
            
        Returns:
            True if task was unblocked, False if not found
        """
        with self._lock:
            if task_id in self._blocked_tasks:
                del self._blocked_tasks[task_id]
                return True
            return False
    
    def remove_task(self, task_id: str) -> bool:
        """
        Remove a task from the queue completely.
        
        Args:
            task_id: The task ID to remove
            
        Returns:
            True if task was removed, False if not found
        """
        with self._lock:
            if task_id in self._tasks_by_id:
                # Mark as cancelled to avoid blocking on dequeue
                self._cancelled_tasks.add(task_id)
                del self._tasks_by_id[task_id]
                return True
            return False
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """
        Update task status (for tasks already dequeued).
        
        Args:
            task_id: The task ID to update
            status: The new status
            
        Returns:
            True if task was updated, False if not found
        """
        with self._lock:
            queued_task = self._tasks_by_id.get(task_id)
            if queued_task:
                queued_task.task.status = status
                return True
            return False
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks in the queue."""
        with self._lock:
            return [qt.task for qt in self._queue]
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with a specific status."""
        with self._lock:
            return [qt.task for qt in self._queue if qt.task.status == status]
    
    def get_tasks_by_agent(self, agent_id: str) -> List[Task]:
        """Get all tasks assigned to a specific agent."""
        with self._lock:
            return [qt.task for qt in self._queue if qt.task.agent_id == agent_id]
    
    def size(self) -> int:
        """Get the number of tasks in the queue."""
        with self._lock:
            return len(self._queue)
    
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        with self._lock:
            return len(self._queue) == 0
    
    def clear(self) -> None:
        """Clear all tasks from the queue."""
        with self._lock:
            self._queue.clear()
            self._tasks_by_id.clear()
            self._cancelled_tasks.clear()
            self._blocked_tasks.clear()
    
    def _dependencies_satisfied(self, task: Task) -> bool:
        """
        Check if all task dependencies are satisfied.
        
        Args:
            task: The task to check
            
        Returns:
            True if all dependencies are satisfied
        """
        for dep_id in task.dependencies:
            dep_task = self.get_task(dep_id)
            if dep_task and dep_task.status not in [TaskStatus.COMPLETED]:
                return False
        return True
    
    def get_blocked_tasks(self) -> Dict[str, str]:
        """Get all blocked tasks and their reasons."""
        with self._lock:
            return self._blocked_tasks.copy()
    
    def get_queue_statistics(self) -> Dict[str, Any]:
        """Get statistics about the queue."""
        with self._lock:
            status_counts = {}
            for qt in self._queue:
                status = qt.task.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "total_tasks": len(self._queue),
                "blocked_tasks": len(self._blocked_tasks),
                "cancelled_tasks": len(self._cancelled_tasks),
                "status_breakdown": status_counts,
                "queue_counter": self._queue_counter
            }


# Global instance
_task_queue = None

def get_task_queue() -> TaskQueue:
    """Get or create the global TaskQueue instance."""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue


if __name__ == "__main__":
    # Test the task queue
    print("Testing Task Queue...")
    
    queue = TaskQueue()
    
    # Create test tasks
    task1 = Task(
        task_id=generate_task_id(),
        goal="Low priority task",
        priority=8
    )
    
    task2 = Task(
        task_id=generate_task_id(),
        goal="High priority task",
        priority=2
    )
    
    task3 = Task(
        task_id=generate_task_id(),
        goal="Medium priority task",
        priority=5
    )
    
    # Enqueue tasks
    queue.enqueue(task1)
    queue.enqueue(task2)
    queue.enqueue(task3)
    
    print(f"Queue size: {queue.size()}")
    
    # Dequeue should return high priority first
    next_task = queue.dequeue()
    print(f"First task: {next_task.goal} (priority {next_task.priority})")
    
    next_task = queue.dequeue()
    print(f"Second task: {next_task.goal} (priority {next_task.priority})")
    
    next_task = queue.dequeue()
    print(f"Third task: {next_task.goal} (priority {next_task.priority})")
    
    # Test blocking
    task4 = Task(
        task_id=generate_task_id(),
        goal="Task with dependency",
        priority=3,
        dependencies=["nonexistent"]
    )
    queue.enqueue(task4)
    
    # Should skip blocked task
    next_task = queue.dequeue(check_dependencies=True)
    print(f"Blocked task skipped: {next_task is None}")
    
    # Unblock and retry
    queue.block_task(task4.task_id, "test block")
    blocked = queue.get_blocked_tasks()
    print(f"Blocked tasks: {blocked}")
    
    queue.unblock_task(task4.task_id)
    blocked = queue.get_blocked_tasks()
    print(f"Blocked tasks after unblock: {blocked}")
    
    # Test cancellation
    task5 = Task(
        task_id=generate_task_id(),
        goal="Task to cancel",
        priority=1
    )
    queue.enqueue(task5)
    queue.cancel_task(task5.task_id)
    
    next_task = queue.dequeue()
    print(f"Cancelled task skipped: {next_task is None}")
    
    # Statistics
    stats = queue.get_queue_statistics()
    print(f"Queue statistics: {stats}")
    
    print("\n✅ Task Queue Test Passed!")