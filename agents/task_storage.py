"""
Task Storage and Persistence for Serena Agent Ecosystem
Phase 2: Persistent task state for recovery after restart

This module provides task persistence so Serena can recover task state after restart.
IMPORTANT: Do not automatically repeat potentially destructive or non-idempotent operations.
"""

import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# Try to import Phase 1 core data contracts
try:
    from core_data_contracts import Task, TaskStatus, generate_task_id
    CORE_CONTRACTS_AVAILABLE = True
except ImportError:
    CORE_CONTRACTS_AVAILABLE = False
    
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
        assigned_at: Optional[float] = None
        started_at: Optional[float] = None
        completed_at: Optional[float] = None
        result: Optional[Any] = None
        error_message: Optional[str] = None
        
        def to_dict(self) -> Dict:
            return {
                "task_id": self.task_id,
                "goal": self.goal,
                "priority": self.priority,
                "agent_id": self.agent_id,
                "status": self.status.value,
                "created_at": self.created_at,
                "context": self.context,
                "dependencies": self.dependencies,
                "assigned_at": self.assigned_at,
                "started_at": self.started_at,
                "completed_at": self.completed_at,
                "result": str(self.result) if self.result else None,
                "error_message": self.error_message
            }
        
        def assign(self, agent_id: str) -> None:
            self.agent_id = agent_id
            self.assigned_at = time.time()
            self.status = TaskStatus.ASSIGNED
    
    def generate_task_id():
        return f"task_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


@dataclass
class TaskSnapshot:
    """
    Snapshot of task state at a point in time.
    Used for history and recovery.
    """
    snapshot_id: str
    task_id: str
    status: TaskStatus
    timestamp: float
    data: Dict[str, Any]
    change_type: str  # created, assigned, started, completed, failed, blocked, cancelled
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "snapshot_id": self.snapshot_id,
            "task_id": self.task_id,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "change_type": self.change_type
        }


class TaskStorage:
    """
    Persistent task storage for recovery after restart.
    
    Supports:
    - Task state persistence
    - Status change history
    - Pending task recovery
    - Result persistence
    - Error logging
    - Safe recovery (no automatic retry of destructive operations)
    """
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.tasks_file = self.storage_dir / "tasks.json"
        self.history_file = self.storage_dir / "task_history.json"
        self.results_file = self.storage_dir / "task_results.json"
        
        self._lock = threading.RLock()
        
        # Load existing data
        self._load_tasks()
        self._load_history()
        self._load_results()
    
    def _load_tasks(self) -> None:
        """Load tasks from storage."""
        self.tasks: Dict[str, Task] = {}
        
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r') as f:
                    data = json.load(f)
                    for task_id, task_data in data.items():
                        if CORE_CONTRACTS_AVAILABLE:
                            self.tasks[task_id] = Task.from_dict(task_data)
                        else:
                            # Fallback for basic task
                            self.tasks[task_id] = Task(
                                task_id=task_data["task_id"],
                                goal=task_data["goal"],
                                priority=task_data.get("priority", 5),
                                agent_id=task_data.get("agent_id"),
                                status=TaskStatus(task_data.get("status", "pending")),
                                created_at=task_data.get("created_at", time.time()),
                                context=task_data.get("context", {}),
                                dependencies=task_data.get("dependencies", [])
                            )
            except Exception as e:
                print(f"Error loading tasks: {e}")
    
    def _load_history(self) -> None:
        """Load task history from storage."""
        self.history: Dict[str, List[TaskSnapshot]] = {}
        
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    for task_id, snapshots in data.items():
                        self.history[task_id] = []
                        for snap_data in snapshots:
                            snapshot = TaskSnapshot(
                                snapshot_id=snap_data["snapshot_id"],
                                task_id=snap_data["task_id"],
                                status=TaskStatus(snap_data["status"]),
                                timestamp=snap_data["timestamp"],
                                data=snap_data["data"],
                                change_type=snap_data["change_type"]
                            )
                            self.history[task_id].append(snapshot)
            except Exception as e:
                print(f"Error loading history: {e}")
    
    def _load_results(self) -> None:
        """Load task results from storage."""
        self.results: Dict[str, Any] = {}
        
        if self.results_file.exists():
            try:
                with open(self.results_file, 'r') as f:
                    self.results = json.load(f)
            except Exception as e:
                print(f"Error loading results: {e}")
    
    def save_task(self, task: Task, change_type: str = "updated") -> bool:
        """
        Save task state and create history snapshot.
        
        Args:
            task: The task to save
            change_type: Type of change (created, assigned, started, completed, failed, blocked, cancelled)
            
        Returns:
            True if save successful
        """
        with self._lock:
            try:
                # Save task
                self.tasks[task.task_id] = task
                
                # Create history snapshot
                snapshot = TaskSnapshot(
                    snapshot_id=f"snap_{int(time.time() * 1000)}",
                    task_id=task.task_id,
                    status=task.status,
                    timestamp=time.time(),
                    data=task.to_dict(),
                    change_type=change_type
                )
                
                if task.task_id not in self.history:
                    self.history[task.task_id] = []
                self.history[task.task_id].append(snapshot)
                
                # Persist to disk
                self._persist_tasks()
                self._persist_history()
                
                return True
            except Exception as e:
                print(f"Error saving task: {e}")
                return False
    
    def save_result(self, task_id: str, result: Any) -> bool:
        """
        Save task result.
        
        Args:
            task_id: The task ID
            result: The result to save
            
        Returns:
            True if save successful
        """
        with self._lock:
            try:
                self.results[task_id] = str(result) if result else None
                self._persist_results()
                return True
            except Exception as e:
                print(f"Error saving result: {e}")
                return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        with self._lock:
            return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        with self._lock:
            return list(self.tasks.values())
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with a specific status."""
        with self._lock:
            return [task for task in self.tasks.values() if task.status == status]
    
    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks for recovery."""
        with self._lock:
            return [task for task in self.tasks.values() 
                   if task.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.BLOCKED]]
    
    def get_task_history(self, task_id: str) -> List[TaskSnapshot]:
        """Get history for a specific task."""
        with self._lock:
            return self.history.get(task_id, [])
    
    def get_result(self, task_id: str) -> Optional[Any]:
        """Get result for a task."""
        with self._lock:
            return self.results.get(task_id)
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task from storage.
        
        Args:
            task_id: The task ID to delete
            
        Returns:
            True if deletion successful
        """
        with self._lock:
            try:
                if task_id in self.tasks:
                    del self.tasks[task_id]
                if task_id in self.history:
                    del self.history[task_id]
                if task_id in self.results:
                    del self.results[task_id]
                
                self._persist_tasks()
                self._persist_history()
                self._persist_results()
                
                return True
            except Exception as e:
                print(f"Error deleting task: {e}")
                return False
    
    def clear_completed_tasks(self, older_than_hours: int = 24) -> int:
        """
        Clear completed tasks older than specified hours.
        
        Args:
            older_than_hours: Clear tasks completed more than this many hours ago
            
        Returns:
            Number of tasks cleared
        """
        with self._lock:
            cutoff_time = time.time() - (older_than_hours * 3600)
            tasks_to_delete = []
            
            for task_id, task in self.tasks.items():
                if task.status == TaskStatus.COMPLETED:
                    if task.completed_at and task.completed_at < cutoff_time:
                        tasks_to_delete.append(task_id)
            
            for task_id in tasks_to_delete:
                self.delete_task(task_id)
            
            return len(tasks_to_delete)
    
    def _persist_tasks(self) -> None:
        """Persist tasks to disk."""
        with open(self.tasks_file, 'w') as f:
            data = {task_id: task.to_dict() for task_id, task in self.tasks.items()}
            json.dump(data, f, indent=2)
    
    def _persist_history(self) -> None:
        """Persist history to disk."""
        with open(self.history_file, 'w') as f:
            data = {task_id: [snap.to_dict() for snap in snapshots] 
                   for task_id, snapshots in self.history.items()}
            json.dump(data, f, indent=2)
    
    def _persist_results(self) -> None:
        """Persist results to disk."""
        with open(self.results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics."""
        with self._lock:
            status_counts = {}
            for task in self.tasks.values():
                status = task.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "total_tasks": len(self.tasks),
                "status_breakdown": status_counts,
                "total_history_entries": sum(len(snaps) for snaps in self.history.values()),
                "total_results": len(self.results),
                "storage_dir": str(self.storage_dir)
            }


# Global instance
_task_storage = None

def get_task_storage(storage_dir: Path = None) -> TaskStorage:
    """Get or create the global TaskStorage instance."""
    global _task_storage
    if _task_storage is None:
        if storage_dir is None:
            storage_dir = Path.cwd() / "task_storage"
        _task_storage = TaskStorage(storage_dir)
    return _task_storage


if __name__ == "__main__":
    # Test the task storage
    print("Testing Task Storage...")
    
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())
    storage = TaskStorage(temp_dir)
    
    # Test saving tasks
    task1 = Task(
        task_id=generate_task_id(),
        goal="Test task 1",
        priority=5
    )
    
    storage.save_task(task1, "created")
    print(f"Saved task: {task1.task_id}")
    
    # Test status change
    task1.assign("TestAgent")
    storage.save_task(task1, "assigned")
    print(f"Task assigned to: {task1.agent_id}")
    
    # Test retrieval
    retrieved = storage.get_task(task1.task_id)
    print(f"Retrieved task: {retrieved.goal}")
    
    # Test history
    history = storage.get_task_history(task1.task_id)
    print(f"Task history entries: {len(history)}")
    
    # Test result saving
    storage.save_result(task1.task_id, "Task completed successfully")
    result = storage.get_result(task1.task_id)
    print(f"Task result: {result}")
    
    # Test pending tasks
    pending = storage.get_pending_tasks()
    print(f"Pending tasks: {len(pending)}")
    
    # Test statistics
    stats = storage.get_statistics()
    print(f"Statistics: {stats}")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    
    print("\n✅ Task Storage Test Passed!")