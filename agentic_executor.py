"""
Agentic Executor for Serena
This module implements the planning/execution loop for multi-step agentic tasks.
"""

import json
import time
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(Enum):
    """Status of a task in the execution pipeline."""
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    RETRYING = "retrying"


@dataclass
class TaskStep:
    """Represents a single step in a multi-step task."""
    step_id: str
    description: str
    tool: str
    parameters: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = None
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "step_id": self.step_id,
            "description": self.description,
            "tool": self.tool,
            "parameters": self.parameters,
            "status": self.status.value,
            "result": str(self.result) if self.result else None,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "dependencies": self.dependencies
        }


@dataclass
class AgenticTask:
    """Represents a complete agentic task with multiple steps."""
    task_id: str
    goal: str
    steps: List[TaskStep] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    current_step_index: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    started_at: float = None
    completed_at: float = None
    error_message: str = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "steps": [step.to_dict() for step in self.steps],
            "status": self.status.value,
            "current_step_index": self.current_step_index,
            "context": self.context,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message
        }


class AgenticExecutor:
    """
    Executes multi-step agentic tasks with planning, execution, and error recovery.
    """
    
    def __init__(self, tools: Dict[str, Callable] = None, permission_system=None):
        """
        Initialize the agentic executor.
        
        Args:
            tools: Dictionary of available tools (name -> function)
            permission_system: Optional permission system for safety checks
        """
        self.tools = tools or {}
        self.permission_system = permission_system
        self.active_tasks: Dict[str, AgenticTask] = {}
        self.task_history: List[AgenticTask] = []
        self.max_steps_per_task = 50
        self.max_execution_time = 300  # 5 minutes max per task
        
    def create_task(self, goal: str, steps: List[TaskStep] = None) -> AgenticTask:
        """
        Create a new agentic task.
        
        Args:
            goal: The goal of the task
            steps: Optional pre-defined steps (will be planned if not provided)
            
        Returns:
            The created task
        """
        task_id = f"task_{int(time.time() * 1000)}"
        task = AgenticTask(
            task_id=task_id,
            goal=goal,
            steps=steps or []
        )
        self.active_tasks[task_id] = task
        return task
    
    def plan_task(self, task: AgenticTask) -> bool:
        """
        Plan the steps needed to complete a task.
        This is where the AI would break down the goal into executable steps.
        
        Args:
            task: The task to plan
            
        Returns:
            True if planning succeeded, False otherwise
        """
        task.status = TaskStatus.PLANNING
        
        try:
            # For now, use a simple heuristic-based planner
            # In a full implementation, this would use the AI to generate plans
            steps = self._generate_plan(task.goal)
            
            if not steps:
                task.status = TaskStatus.FAILED
                task.error_message = "Could not generate a plan for this task"
                return False
            
            task.steps = steps
            task.status = TaskStatus.PENDING
            return True
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = f"Planning error: {str(e)}"
            return False
    
    def _generate_plan(self, goal: str) -> List[TaskStep]:
        """
        Generate a plan for achieving the goal.
        This is a simplified version - a full implementation would use AI.
        
        Args:
            goal: The goal to achieve
            
        Returns:
            List of steps to execute
        """
        steps = []
        goal_lower = goal.lower()
        
        # Simple heuristic-based planning for common tasks
        if "organize" in goal_lower and "file" in goal_lower:
            steps = [
                TaskStep(
                    step_id="step_1",
                    description="List files in target directory",
                    tool="list_files",
                    parameters={"pattern": "*"}
                ),
                TaskStep(
                    step_id="step_2", 
                    description="Analyze file patterns and naming",
                    tool="analyze_files",
                    parameters={}
                ),
                TaskStep(
                    step_id="step_3",
                    description="Create organized directory structure",
                    tool="create_directory",
                    parameters={"dir_path": "organized"}
                ),
                TaskStep(
                    step_id="step_4",
                    description="Move files to organized structure",
                    tool="organize_files",
                    parameters={}
                )
            ]
        
        elif "search" in goal_lower and "web" in goal_lower:
            steps = [
                TaskStep(
                    step_id="step_1",
                    description="Perform web search",
                    tool="web_search",
                    parameters={"query": goal}
                ),
                TaskStep(
                    step_id="step_2",
                    description="Analyze search results",
                    tool="analyze_results",
                    parameters={}
                )
            ]
        
        elif "code" in goal_lower or "debug" in goal_lower:
            steps = [
                TaskStep(
                    step_id="step_1",
                    description="Analyze code or error",
                    tool="read_file",
                    parameters={}
                ),
                TaskStep(
                    step_id="step_2",
                    description="Identify issues and solutions",
                    tool="analyze_code",
                    parameters={}
                ),
                TaskStep(
                    step_id="step_3",
                    description="Apply fixes",
                    tool="write_file",
                    parameters={}
                )
            ]
        
        else:
            # Generic plan for unknown tasks
            steps = [
                TaskStep(
                    step_id="step_1",
                    description="Analyze task requirements",
                    tool="analyze_task",
                    parameters={"goal": goal}
                ),
                TaskStep(
                    step_id="step_2",
                    description="Execute primary action",
                    tool="execute_action",
                    parameters={"goal": goal}
                ),
                TaskStep(
                    step_id="step_3",
                    description="Verify results",
                    tool="verify_results",
                    parameters={}
                )
            ]
        
        return steps
    
    def execute_task(self, task: AgenticTask) -> Dict[str, Any]:
        """
        Execute a task step by step.
        
        Args:
            task: The task to execute
            
        Returns:
            Execution results
        """
        if not task.steps:
            if not self.plan_task(task):
                return {"success": False, "error": task.error_message}
        
        task.status = TaskStatus.EXECUTING
        task.started_at = time.time()
        
        results = {
            "success": False,
            "steps_completed": 0,
            "steps_failed": 0,
            "final_result": None,
            "error": None
        }
        
        try:
            for i, step in enumerate(task.steps):
                task.current_step_index = i
                
                # Check dependencies
                if not self._check_dependencies(step, task):
                    step.status = TaskStatus.BLOCKED
                    step.error = "Dependencies not met"
                    results["steps_failed"] += 1
                    continue
                
                # Execute step
                step.status = TaskStatus.EXECUTING
                success, result = self._execute_step(step)
                
                if success:
                    step.status = TaskStatus.COMPLETED
                    step.result = result
                    results["steps_completed"] += 1
                    # Update task context with step results
                    task.context[step.step_id] = result
                else:
                    step.status = TaskStatus.FAILED
                    step.error = str(result)
                    results["steps_failed"] += 1
                    
                    # Retry logic
                    if step.retry_count < step.max_retries:
                        step.retry_count += 1
                        step.status = TaskStatus.RETRYING
                        # Move back to retry this step
                        task.current_step_index = i - 1
                        continue
                    else:
                        # Max retries reached, mark task as failed
                        task.status = TaskStatus.FAILED
                        task.error_message = f"Step {step.step_id} failed after {step.max_retries} retries"
                        results["error"] = task.error_message
                        break
                
                # Check timeout
                if time.time() - task.started_at > self.max_execution_time:
                    task.status = TaskStatus.FAILED
                    task.error_message = "Task execution timeout"
                    results["error"] = task.error_message
                    break
            
            # Check if task completed successfully
            if results["steps_failed"] == 0 and results["steps_completed"] == len(task.steps):
                task.status = TaskStatus.COMPLETED
                task.completed_at = time.time()
                results["success"] = True
                results["final_result"] = f"Task completed: {task.goal}"
            elif task.status != TaskStatus.FAILED:
                task.status = TaskStatus.COMPLETED
                task.completed_at = time.time()
                results["success"] = True
                results["final_result"] = f"Task partially completed: {results['steps_completed']}/{len(task.steps)} steps"
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = f"Execution error: {str(e)}"
            results["error"] = str(e)
        
        # Move to history
        self.task_history.append(task)
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]
        
        return results
    
    def _check_dependencies(self, step: TaskStep, task: AgenticTask) -> bool:
        """Check if step dependencies are satisfied."""
        for dep_id in step.dependencies:
            # Find the dependency step
            dep_step = next((s for s in task.steps if s.step_id == dep_id), None)
            if not dep_step or dep_step.status != TaskStatus.COMPLETED:
                return False
        return True
    
    def _execute_step(self, step: TaskStep) -> Tuple[bool, Any]:
        """
        Execute a single step using the appropriate tool.
        
        Args:
            step: The step to execute
            
        Returns:
            Tuple of (success, result)
        """
        tool = self.tools.get(step.tool)
        if not tool:
            return False, f"Tool '{step.tool}' not available"
        
        try:
            # Check permissions if permission system is available
            if self.permission_system:
                allowed, message, request = self.permission_system.check_permission(
                    step.tool, 
                    f"{step.description} with params: {step.parameters}"
                )
                if not allowed:
                    return False, f"Permission denied: {message}"
            
            # Execute the tool
            result = tool(**step.parameters)
            return True, result
            
        except Exception as e:
            return False, f"Tool execution error: {str(e)}"
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get the status of a task."""
        task = self.active_tasks.get(task_id)
        if not task:
            # Check history
            task = next((t for t in self.task_history if t.task_id == task_id), None)
        
        if task:
            return task.to_dict()
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel an active task."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = TaskStatus.FAILED
            task.error_message = "Task cancelled by user"
            self.task_history.append(task)
            del self.active_tasks[task_id]
            return True
        return False
    
    def get_active_tasks(self) -> List[Dict]:
        """Get all currently active tasks."""
        return [task.to_dict() for task in self.active_tasks.values()]


# Global instance
_agentic_executor = None

def get_agentic_executor(tools: Dict[str, Callable] = None, permission_system=None) -> AgenticExecutor:
    """Get or create the global AgenticExecutor instance."""
    global _agentic_executor
    if _agentic_executor is None:
        # Default tools if none provided
        default_tools = {}
        if tools:
            default_tools.update(tools)
        _agentic_executor = AgenticExecutor(default_tools, permission_system)
    return _agentic_executor


if __name__ == "__main__":
    # Test the agentic executor
    print("Testing Agentic Executor...")
    
    # Mock tools
    def mock_list_files(pattern="*"):
        return ["file1.txt", "file2.py", "file3.jpg"]
    
    def mock_analyze_files():
        return {"analysis": "Found 3 files with mixed extensions"}
    
    def mock_create_directory(dir_path):
        return f"Created directory: {dir_path}"
    
    def mock_rename_file(old_path, new_path):
        return f"Renamed {old_path} to {new_path}"
    
    def mock_organize_files():
        return "Files organized successfully"
    
    def mock_analyze_task(goal):
        return {"task_analysis": f"Analyzing task: {goal}"}
    
    def mock_execute_action(goal):
        return f"Executed action for: {goal}"
    
    def mock_verify_results():
        return {"verification": "Results verified"}
    
    def mock_analyze_code():
        return {"code_analysis": "Code analyzed"}
    
    def mock_analyze_results():
        return {"results_analysis": "Results analyzed"}
    
    tools = {
        "list_files": mock_list_files,
        "analyze_files": mock_analyze_files,
        "create_directory": mock_create_directory,
        "rename_file": mock_rename_file,
        "organize_files": mock_organize_files,
        "analyze_task": mock_analyze_task,
        "execute_action": mock_execute_action,
        "verify_results": mock_verify_results,
        "analyze_code": mock_analyze_code,
        "analyze_results": mock_analyze_results
    }
    
    executor = AgenticExecutor(tools)
    
    # Create and execute a task
    task = executor.create_task("Organize files in current directory")
    print(f"Created task: {task.task_id}")
    
    # Plan the task
    if executor.plan_task(task):
        print(f"Planned task with {len(task.steps)} steps")
        for step in task.steps:
            print(f"  - {step.step_id}: {step.description}")
    
    # Execute the task
    results = executor.execute_task(task)
    print(f"\nExecution results: {json.dumps(results, indent=2)}")
    
    # Get task status
    status = executor.get_task_status(task.task_id)
    print(f"\nFinal task status: {json.dumps(status, indent=2)}")