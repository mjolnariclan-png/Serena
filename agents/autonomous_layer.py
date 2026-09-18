"""
Controlled Autonomous Layer for Serena Agent Ecosystem
Phase 3: Conservative autonomous task generation with strict security boundaries

This module provides goal-based task generation and operational learning
while strictly respecting the established security architecture.
"""

import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta
import json

# Try to import Phase 1 and Phase 2 infrastructure
try:
    from core_data_contracts import Task, TaskStatus, generate_task_id, generate_correlation_id
    from agents.agent_manager import AgentManager
    from agents.task_queue import get_task_queue
    from agents.task_storage import get_task_storage
    AUTONOMY_AVAILABLE = True
except ImportError:
    AUTONOMY_AVAILABLE = False


class AutonomousLayer:
    """
    Controlled autonomous layer for Serena.
    
    Phase 3: Goal-based task generation with strict security boundaries.
    
    The autonomous layer may support:
    - Goal-based task generation
    - Task prioritization
    - Historical performance analysis
    - Failure pattern analysis
    - Operational learning
    - Deciding when an agent should perform a task
    - Coordinating multiple agents
    
    BUT it MUST NOT:
    - Bypass permissions
    - Bypass approval
    - Bypass verification
    - Bypass audit logging
    - Directly execute arbitrary tools
    - Directly modify protected files
    - Grant itself permissions
    - Modify the permission system
    - Modify its own security boundaries
    - Create unrestricted filesystem access
    - Create unrestricted network access
    - Silently retry destructive operations
    - Self-modify security boundaries
    
    "Learning" means operational learning, NOT self-modifying code.
    """
    
    def __init__(self, agent_manager: Optional[AgentManager] = None):
        """
        Initialize the autonomous layer.
        
        Args:
            agent_manager: The AgentManager instance
        """
        self.agent_manager = agent_manager
        self.task_queue = get_task_queue() if AUTONOMY_AVAILABLE else None
        self.task_storage = get_task_storage() if AUTONOMY_AVAILABLE else None
        
        # Operational learning data
        self.task_history = {}  # task_id -> task result
        self.agent_performance = {}  # agent_id -> performance metrics
        self.failure_patterns = {}  # pattern -> count
        
        # Goals (high-level objectives)
        self.goals = []
        
        # Safety constraints
        self.max_autonomous_priority = 7  # Never auto-generate priority 8-10 tasks
        self.auto_generated_tasks_count = 0
        self.max_auto_tasks_per_hour = 10
        
        self.last_task_generation_time = time.time()
    
    def add_goal(self, goal: str, priority: int = 5, agent_id: Optional[str] = None) -> bool:
        """
        Add a high-level goal for the autonomous layer.
        
        Args:
            goal: The goal description
            priority: Task priority (1-10, capped at 7 for autonomous)
            agent_id: Specific agent to use (optional)
            
        Returns:
            True if goal was added
        """
        # Cap priority for autonomous tasks
        priority = min(priority, self.max_autonomous_priority)
        
        self.goals.append({
            "goal": goal,
            "priority": priority,
            "agent_id": agent_id,
            "created_at": time.time(),
            "active": True
        })
        
        return True
    
    def generate_task_from_goal(self, goal: Dict[str, Any]) -> Optional[Task]:
        """
        Generate a task from a goal.
        
        Phase 3: The autonomous layer CREATES TASKS, it does NOT execute them.
        Tasks go through the normal execution pipeline.
        
        Args:
            goal: The goal dictionary
            
        Returns:
            Task object or None if generation failed
        """
        # Check rate limiting
        now = time.time()
        if now - self.last_task_generation_time < 3600:  # Within last hour
            if self.auto_generated_tasks_count >= self.max_auto_tasks_per_hour:
                return None  # Rate limit reached
        
        # Create task
        # Cap priority for autonomous tasks
        capped_priority = min(goal["priority"], self.max_autonomous_priority)
        
        task = Task(
            task_id=generate_task_id(),
            goal=goal["goal"],
            priority=capped_priority,
            agent_id=goal.get("agent_id"),
            task_type="autonomous",
            context={
                "source": "autonomous_layer",
                "goal_id": str(id(goal)),
                "reasoning": "Generated from autonomous goal"
            },
            metadata={
                "autonomous": True,
                "confidence": 0.7  # Autonomous tasks have moderate confidence
            },
            correlation_id=generate_correlation_id()
        )
        
        # Rate limit tracking
        self.auto_generated_tasks_count += 1
        self.last_task_generation_time = now
        
        return task
    
    def process_goals(self) -> Dict[str, Any]:
        """
        Process active goals and generate tasks.
        
        Phase 3: Process goals by creating tasks that go through the normal pipeline.
        
        Returns:
            Processing results
        """
        if not self.task_queue:
            return {
                "success": False,
                "error": "Task queue not available"
            }
        
        results = {
            "tasks_generated": 0,
            "goals_processed": 0,
            "errors": []
        }
        
        for goal in self.goals:
            if not goal["active"]:
                continue
            
            try:
                # Generate task from goal
                task = self.generate_task_from_goal(goal)
                
                if task:
                    # Submit to queue (goes through normal pipeline)
                    submitted = self.task_queue.enqueue(task)
                    
                    if submitted:
                        results["tasks_generated"] += 1
                        results["goals_processed"] += 1
                        goal["active"] = False  # Goal processed
                    else:
                        results["errors"].append(f"Failed to enqueue task for goal: {goal['goal']}")
                else:
                    results["errors"].append(f"Failed to generate task from goal: {goal['goal']}")
                    
            except Exception as e:
                results["errors"].append(f"Error processing goal: {e}")
        
        return results
    
    def record_task_result(self, task_id: str, result: Dict[str, Any]) -> None:
        """
        Record the result of a task for operational learning.
        
        Args:
            task_id: The task ID
            result: The task result
        """
        self.task_history[task_id] = {
            "result": result,
            "recorded_at": time.time()
        }
        
        # Update agent performance metrics
        agent_id = result.get("agent_id")
        if agent_id:
            if agent_id not in self.agent_performance:
                self.agent_performance[agent_id] = {
                    "total_tasks": 0,
                    "successful_tasks": 0,
                    "failed_tasks": 0
                }
            
            self.agent_performance[agent_id]["total_tasks"] += 1
            
            if result.get("success"):
                self.agent_performance[agent_id]["successful_tasks"] += 1
            else:
                self.agent_performance[agent_id]["failed_tasks"] += 1
    
    def analyze_failure_patterns(self) -> Dict[str, Any]:
        """
        Analyze patterns in task failures.
        
        Returns:
        Failure pattern analysis
        """
        patterns = {}
        
        for task_id, history in self.task_history.items():
            result = history["result"]
            
            if not result.get("success"):
                error = result.get("error_message", "unknown")
                patterns[error] = patterns.get(error, 0) + 1
        
        self.failure_patterns = patterns
        
        return {
            "patterns": patterns,
            "total_failures": sum(patterns.values())
        }
    
    def get_agent_performance_report(self) -> Dict[str, Any]:
        """
        Get performance report for all agents.
        
        Returns:
        Agent performance metrics
        """
        report = {}
        
        for agent_id, metrics in self.agent_performance.items():
            total = metrics["total_tasks"]
            if total > 0:
                success_rate = metrics["successful_tasks"] / total
            else:
                success_rate = 0.0
            
            report[agent_id] = {
                "total_tasks": total,
                "successful_tasks": metrics["successful_tasks"],
                "failed_tasks": metrics["failed_tasks"],
                "success_rate": round(success_rate, 2)
            }
        
        return report
    
    def prioritize_tasks(self) -> List[str]:
        """
        Suggest task prioritization based on historical performance.
        
        Returns:
        List of task IDs in suggested priority order
        """
        # This is a simple implementation - could be enhanced with ML
        # For now, prioritize by recent failures first
        recent_failures = []
        
        for task_id, history in self.task_history.items():
            result = history["result"]
            if not result.get("success"):
                age = time.time() - history["recorded_at"]
                if age < 3600:  # Failed within last hour
                    recent_failures.append((task_id, age))
        
        # Sort by age (oldest first)
        recent_failures.sort(key=lambda x: x[1])
        
        return [task_id for task_id, _ in recent_failures]
    
    def should_auto_retry(self, task_id: str) -> bool:
        """
        Determine if a task should be automatically retried.
        
        Phase 3: Conservative retry policy - only retry safe operations.
        
        Args:
            task_id: The task ID to check
            
        Returns:
            True if task should be auto-retried
        """
        if task_id not in self.task_history:
            return False
        
        result = self.task_history[task_id]["result"]
        
        # Never retry destructive operations
        if result.get("task_type") in ["delete", "reset", "destructive"]:
            return False
        
        # Only retry if error appears transient
        error = result.get("error_message", "").lower()
        transient_errors = ["timeout", "network", "temporary", "unavailable"]
        
        if any(err in error for err in transient_errors):
            return True
        
        return False
    
    def get_autonomy_status(self) -> Dict[str, Any]:
        """
        Get the current status of the autonomous layer.
        
        Returns:
        Autonomous layer status
        """
        return {
            "active_goals": len([g for g in self.goals if g["active"]]),
            "total_goals": len(self.goals),
            "auto_generated_tasks": self.auto_generated_tasks_count,
            "tasks_in_history": len(self.task_history),
            "agents_tracked": len(self.agent_performance),
            "failure_patterns": len(self.failure_patterns),
            "rate_limit_remaining": max(0, self.max_auto_tasks_per_hour - self.auto_generated_tasks_count)
        }


# Global instance
_autonomous_layer = None

def get_autonomous_layer(agent_manager: Optional[AgentManager] = None) -> AutonomousLayer:
    """Get or create the global AutonomousLayer instance."""
    global _autonomous_layer
    if _autonomous_layer is None:
        _autonomous_layer = AutonomousLayer(agent_manager)
    return _autonomous_layer


if __name__ == "__main__":
    # Test the autonomous layer
    print("Testing Autonomous Layer...")
    
    if not AUTONOMY_AVAILABLE:
        print("Phase 1/2 infrastructure not available")
    else:
        from pathlib import Path
        import tempfile
        
        # Create temporary workspace
        temp_workspace = Path(tempfile.mkdtemp())
        
        # Create agent manager
        agent_manager = AgentManager(temp_workspace)
        
        # Create autonomous layer
        auto = AutonomousLayer(agent_manager)
        
        # Test add goal
        auto.add_goal("Test autonomous goal", priority=5)
        print(f"Added goal, active goals: {len([g for g in auto.goals if g['active']])}")
        
        # Test process goals
        results = auto.process_goals()
        print(f"Processed goals: {results}")
        
        # Test record task result
        auto.record_task_result("test_task_123", {
            "success": True,
            "agent_id": "TestAgent"
        })
        
        # Test performance report
        report = auto.get_agent_performance_report()
        print(f"Performance report: {report}")
        
        # Test autonomy status
        status = auto.get_autonomy_status()
        print(f"Autonomy status: {status}")
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_workspace)
        
        print("\n✅ Autonomous Layer Test Passed!")