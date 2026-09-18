"""
Agent Manager
Coordinates and manages multiple specialized agents

Phase 1: Enhanced with execution interface for AI → Agent Manager → Agent coordination
"""

import os
import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Try to import Phase 1 core data contracts
try:
    from core_data_contracts import Task, TaskDecision, ExecutionPlan, ExecutionStep, TaskStatus, PermissionLevel, generate_correlation_id, generate_task_id
    CORE_CONTRACTS_AVAILABLE = True
except ImportError:
    CORE_CONTRACTS_AVAILABLE = False
    
    # Fallback definitions
    import uuid
    from enum import Enum
    from dataclasses import dataclass, field
    
    class TaskStatus(Enum):
        PENDING = "pending"
        EXECUTING = "executing"
        COMPLETED = "completed"
        FAILED = "failed"
    
    class PermissionLevel(Enum):
        SAFE = "safe"
        WARNING = "warning"
        DANGEROUS = "dangerous"
        FORBIDDEN = "forbidden"
    
    @dataclass
    class Task:
        task_id: str
        goal: str
        priority: int = 5
        agent_id: Optional[str] = None
        task_type: Optional[str] = None
        created_at: float = field(default_factory=time.time)
        context: Dict = field(default_factory=dict)
        parameters: Dict = field(default_factory=dict)
        metadata: Dict = field(default_factory=dict)
    
    @dataclass
    class TaskDecision:
        decision_id: str
        task: Task
        confidence: float
        reasoning: str
        suggested_agent: Optional[str] = None
        suggested_parameters: Dict = field(default_factory=dict)
        created_at: float = field(default_factory=time.time)
    
    @dataclass
    class ExecutionStep:
        step_id: str
        description: str
        tool: str
        parameters: Dict
        status: TaskStatus = TaskStatus.PENDING
        verification_required: bool = True
        permission_level: PermissionLevel = PermissionLevel.SAFE
    
    @dataclass
    class ExecutionPlan:
        plan_id: str
        task_id: str
        agent_id: str
        steps: List[ExecutionStep]
        estimated_duration: Optional[float] = None
        created_at: float = field(default_factory=time.time)
    
    def generate_correlation_id():
        return str(uuid.uuid4())
    
    def generate_task_id():
        return f"task_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    
    # Fallback definitions
    import uuid
    from enum import Enum
    from dataclasses import dataclass, field
    
    class TaskStatus(Enum):
        PENDING = "pending"
        EXECUTING = "executing"
        COMPLETED = "completed"
        FAILED = "failed"
    
    class PermissionLevel(Enum):
        SAFE = "safe"
        WARNING = "warning"
        DANGEROUS = "dangerous"
        FORBIDDEN = "forbidden"
    
    @dataclass
    class Task:
        task_id: str
        goal: str
        priority: int = 5
        agent_id: Optional[str] = None
        created_at: float = field(default_factory=time.time)
        context: Dict = field(default_factory=dict)
        metadata: Dict = field(default_factory=dict)
    
    @dataclass
    class TaskDecision:
        decision_id: str
        task: Task
        confidence: float
        reasoning: str
        suggested_agent: Optional[str] = None
        suggested_parameters: Dict = field(default_factory=dict)
        created_at: float = field(default_factory=time.time)
    
    @dataclass
    class ExecutionStep:
        step_id: str
        description: str
        tool: str
        parameters: Dict
        status: TaskStatus = TaskStatus.PENDING
        verification_required: bool = True
        permission_level: PermissionLevel = PermissionLevel.SAFE
    
    @dataclass
    class ExecutionPlan:
        plan_id: str
        task_id: str
        agent_id: str
        steps: List[ExecutionStep]
        estimated_duration: Optional[float] = None
        created_at: float = field(default_factory=time.time)
    
    def generate_correlation_id():
        return str(uuid.uuid4())

class AgentManager:
    """
    Manages multiple specialized agents
    
    Phase 2: Upgraded from basic registry to coordinator with task queue and lifecycle management
    """
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.agents = {}
        self.agent_status = {}
        self.agent_capabilities = {}  # Phase 2: Agent capability registry
        self.running = False
        self.scheduler_thread = None
        self.task_queue = None  # Phase 2: Central task queue
        self.task_queue_thread = None  # Phase 2: Task queue processor thread
        
        # Phase 3: Enhanced scheduling
        self.scheduled_tasks = {}  # task_id -> schedule config
        self.schedules = []  # List of schedule definitions
        
        # Create workspace structure
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        # Phase 2: Initialize task queue
        self._initialize_task_queue()
    
    def _initialize_task_queue(self):
        """Initialize the central task queue."""
        try:
            from task_queue import get_task_queue
            self.task_queue = get_task_queue()
            print("Task queue initialized")
        except ImportError:
            print("Warning: task_queue module not available, queue features disabled")
            self.task_queue = None
        
    def register_agent(self, agent):
        """
        Register an agent with the manager.
        
        Phase 2: Also register agent capabilities.
        """
        self.agents[agent.name] = agent
        self.agent_status[agent.name] = {
            "status": "idle",
            "last_activity": None,
            "tasks_completed": 0,
            "errors": 0,
            "health": "healthy",  # Phase 2: Health tracking
            "started_at": datetime.now().isoformat()  # Phase 2: Start time
        }
        
        # Phase 2: Register agent capabilities
        self.agent_capabilities[agent.name] = self._extract_agent_capabilities(agent)
        
        print(f"Registered agent: {agent.name}")
    
    def _extract_agent_capabilities(self, agent) -> Dict[str, Any]:
        """
        Extract capabilities from an agent.
        
        Phase 2: Build capability registry for agent selection.
        """
        capabilities = {
            "agent_id": agent.name,
            "agent_type": agent.__class__.__name__,
            "status": "idle",
            "supported_task_types": [],
            "permissions": getattr(agent, "permissions", {}),
            "rules": getattr(agent, "rules", []),
            "workspace": str(agent.workspace),
            "registered_at": datetime.now().isoformat()
        }
        
        # Extract task types based on agent type
        if agent.__class__.__name__ == "MediaAgent":
            capabilities["supported_task_types"] = ["media_operation", "media_scan", "media_organize"]
            capabilities["description"] = "Manages media files and Jellyfin integration"
        elif agent.__class__.__name__ == "PhotoAgent":
            capabilities["supported_task_types"] = ["photo_operation", "photo_organize", "photo_duplicate_detection"]
            capabilities["description"] = "Organizes photos by date and detects duplicates"
        elif agent.__class__.__name__ == "ServerAgent":
            capabilities["supported_task_types"] = ["system_maintenance", "system_monitoring", "disk_check"]
            capabilities["description"] = "Monitors system health and performs maintenance"
        else:
            capabilities["supported_task_types"] = ["general"]
            capabilities["description"] = "General purpose agent"
        
        return capabilities
    
    def get_agent(self, name: str):
        """Get an agent by name"""
        return self.agents.get(name)
    
    def execute_agent_task(self, agent_name: str, task: str) -> str:
        """Execute a task on a specific agent"""
        agent = self.get_agent(agent_name)
        if not agent:
            return f"Agent '{agent_name}' not found"
        
        try:
            self.agent_status[agent_name]["status"] = "working"
            result = agent.execute_task(task)
            self.agent_status[agent_name]["status"] = "idle"
            self.agent_status[agent_name]["last_activity"] = datetime.now().isoformat()
            self.agent_status[agent_name]["tasks_completed"] += 1
            return result
        except Exception as e:
            self.agent_status[agent_name]["status"] = "error"
            self.agent_status[agent_name]["errors"] += 1
            return f"Error executing task: {str(e)}"
    
    def get_all_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            "agents": self.agent_status,
            "total_agents": len(self.agents),
            "active_agents": sum(1 for s in self.agent_status.values() if s["status"] == "working"),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_recent_activity(self, limit: int = 20) -> List[Dict]:
        """Get recent activity from all agents"""
        all_activity = []
        
        for agent_name, agent in self.agents.items():
            for activity in agent.activity_log[-limit:]:
                activity_copy = activity.copy()
                activity_copy["agent"] = agent_name
                all_activity.append(activity_copy)
        
        # Sort by timestamp and limit
        all_activity.sort(key=lambda x: x["timestamp"], reverse=True)
        return all_activity[:limit]
    
    def start_scheduler(self):
        """Start the background scheduler for periodic tasks"""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        print("Agent scheduler started")
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("Agent scheduler stopped")
    
    def _scheduler_loop(self):
        """Background loop for scheduled tasks"""
        while self.running:
            try:
                # Run periodic tasks
                current_hour = datetime.now().hour
                
                # Server maintenance check every hour
                if current_hour % 1 == 0:  # Every hour
                    server_agent = self.get_agent("ServerAgent")
                    if server_agent:
                        self.execute_agent_task("ServerAgent", "check services")
                
                # Media scan every 30 minutes
                if current_hour % 0.5 == 0:  # Every 30 minutes
                    media_agent = self.get_agent("MediaAgent")
                    if media_agent:
                        self.execute_agent_task("MediaAgent", "scan incoming")
                
                # Sleep for 5 minutes
                time.sleep(300)
                
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(60)
    
    def generate_dashboard_report(self) -> str:
        """Generate a dashboard-style report"""
        status = self.get_all_agent_status()
        recent_activity = self.get_recent_activity(10)
        
        report = []
        report.append("AGENT HUB DASHBOARD")
        report.append("=" * 40)
        report.append(f"Total Agents: {status['total_agents']}")
        report.append(f"Active Agents: {status['active_agents']}")
        report.append(f"Last Updated: {status['timestamp']}")
        report.append("")
        
        report.append("AGENT STATUS:")
        for agent_name, agent_status in status['agents'].items():
            status_symbol = "●" if agent_status['status'] == "working" else "○"
            report.append(f"  {status_symbol} {agent_name}: {agent_status['status']}")
            report.append(f"      Tasks completed: {agent_status['tasks_completed']}")
            report.append(f"      Errors: {agent_status['errors']}")
            if agent_status['last_activity']:
                report.append(f"      Last activity: {agent_status['last_activity']}")
        
        report.append("")
        report.append("RECENT ACTIVITY:")
        for activity in recent_activity:
            report.append(f"  {activity['timestamp']} - {activity['agent']}: {activity['activity']}")
        
        return "\n".join(report)
    
    # ==================== PHASE 2 TASK QUEUE MANAGEMENT ====================
    
    def submit_task(self, task: Task) -> bool:
        """
        Submit a task to the central queue.
        
        Phase 2: Task submission through Agent Manager.
        
        Args:
            task: The task to submit
            
        Returns:
            True if task was enqueued, False otherwise
        """
        if not self.task_queue:
            print("Task queue not available")
            return False
        
        # Assign agent if not already assigned
        if not task.agent_id:
            agent_id = self._select_agent_for_task(task)
            if agent_id:
                task.agent_id = agent_id
                task.assign(agent_id)
        
        return self.task_queue.enqueue(task)
    
    def _select_agent_for_task(self, task: Task) -> Optional[str]:
        """
        Select the best agent for a task based on capabilities.
        
        Phase 2: Agent selection with capability matching.
        
        Args:
            task: The task to assign
            
        Returns:
            Agent ID or None if no suitable agent found
        """
        # Check task type
        task_type = task.task_type or task.context.get("task_type", "general")
        
        # Find agents that support this task type
        suitable_agents = []
        for agent_id, capabilities in self.agent_capabilities.items():
            if task_type in capabilities.get("supported_task_types", []):
                # Check if agent is available
                if self.agent_status[agent_id]["status"] == "idle":
                    suitable_agents.append(agent_id)
        
        # Select agent with least workload
        if suitable_agents:
            # Simple selection: first available
            # In a more sophisticated version, would consider workload, health, etc.
            return suitable_agents[0]
        
        # Fallback: first registered agent
        if self.agents:
            return list(self.agents.keys())[0]
        
        return None
    
    def start_task_queue_processor(self):
        """
        Start the background task queue processor.
        
        Phase 2: Background thread to process queued tasks.
        """
        if not self.task_queue:
            print("Task queue not available")
            return
        
        if self.task_queue_thread and self.task_queue_thread.is_alive():
            print("Task queue processor already running")
            return
        
        self.running = True
        self.task_queue_thread = threading.Thread(target=self._task_queue_loop, daemon=True)
        self.task_queue_thread.start()
        print("Task queue processor started")
    
    def stop_task_queue_processor(self):
        """Stop the task queue processor."""
        self.running = False
        if self.task_queue_thread:
            self.task_queue_thread.join(timeout=5)
        print("Task queue processor stopped")
    
    def _task_queue_loop(self):
        """
        Background loop to process queued tasks.
        
        Phase 2: Continuously dequeue and execute tasks.
        """
        while self.running:
            try:
                # Get next task
                task = self.task_queue.dequeue(check_dependencies=True)
                
                if task:
                    # Execute task
                    self._execute_queued_task(task)
                else:
                    # No tasks available, sleep briefly
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Task queue processor error: {e}")
                time.sleep(5)
    
    def _execute_queued_task(self, task: Task):
        """
        Execute a queued task.
        
        Phase 2: Execute task through Agent Manager coordination.
        
        Args:
            task: The task to execute
        """
        agent = self.get_agent(task.agent_id)
        if not agent:
            print(f"Agent not found: {task.agent_id}")
            task.fail(f"Agent not found: {task.agent_id}")
            return
        
        try:
            # Update agent status
            self.agent_status[agent.name]["status"] = "working"
            
            # Mark task as started
            task.start()
            
            # Execute task (Phase 1: goes through permission system)
            result = agent.execute_task(task.goal)
            
            # Mark task as completed
            task.complete(result)
            
            # Update agent status
            self.agent_status[agent.name]["status"] = "idle"
            self.agent_status[agent.name]["last_activity"] = datetime.now().isoformat()
            self.agent_status[agent.name]["tasks_completed"] += 1
            
            print(f"Task {task.task_id} completed by {agent.name}")
            
        except Exception as e:
            # Mark task as failed
            task.fail(str(e))
            
            # Update agent status
            self.agent_status[agent.name]["status"] = "error"
            self.agent_status[agent.name]["errors"] += 1
            
            print(f"Task {task.task_id} failed: {e}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get status of the task queue.
        
        Phase 2: Queue monitoring interface.
        
        Returns:
            Queue status information
        """
        if not self.task_queue:
            return {"available": False}
        
        stats = self.task_queue.get_queue_statistics()
        return {
            "available": True,
            "queue_size": self.task_queue.size(),
            "is_empty": self.task_queue.is_empty(),
            "statistics": stats,
            "blocked_tasks": self.task_queue.get_blocked_tasks()
        }
    
    def get_agent_capabilities(self, agent_id: str = None) -> Dict[str, Any]:
        """
        Get agent capabilities.
        
        Phase 2: Capability registry interface.
        
        Args:
            agent_id: Specific agent ID, or None for all agents
            
        Returns:
            Agent capabilities
        """
        if agent_id:
            return self.agent_capabilities.get(agent_id, {})
        return self.agent_capabilities
    
    # ==================== PHASE 3: SCHEDULED AND EVENT-DRIVEN WORK ====================
    
    def schedule_task(self, task: Task, schedule_type: str, schedule_config: Dict[str, Any]) -> bool:
        """
        Schedule a task for later execution.
        
        Phase 3: Enhanced scheduling using existing Phase 2 infrastructure.
        
        Args:
            task: The task to schedule
            schedule_type: Type of schedule (interval, datetime, cron)
            schedule_config: Schedule configuration (depends on type)
                - interval: seconds between executions
                - datetime: specific execution time (ISO format)
                - cron: cron-like schedule pattern
                
        Returns:
            True if task was scheduled
        """
        if not self.task_queue:
            print("Task queue not available for scheduling")
            return False
        
        # Add to scheduled tasks
        self.scheduled_tasks[task.task_id] = {
            "task": task,
            "schedule_type": schedule_type,
            "schedule_config": schedule_config,
            "next_run": self._calculate_next_run(schedule_type, schedule_config),
            "last_run": None,
            "active": True
        }
        
        # Also add to schedules list for the scheduler loop
        self.schedules.append(task.task_id)
        
        print(f"Scheduled task {task.task_id} with {schedule_type} schedule")
        return True
    
    def _calculate_next_run(self, schedule_type: str, schedule_config: Dict[str, Any]) -> float:
        """
        Calculate the next run time for a scheduled task.
        
        Args:
            schedule_type: Type of schedule
            schedule_config: Schedule configuration
            
        Returns:
            Unix timestamp of next run
        """
        import time
        now = time.time()
        
        if schedule_type == "interval":
            interval = schedule_config.get("interval", 3600)  # Default 1 hour
            return now + interval
        elif schedule_type == "datetime":
            datetime_str = schedule_config.get("datetime")
            if datetime_str:
                from datetime import datetime
                dt = datetime.fromisoformat(datetime_str)
                return dt.timestamp()
            return now + 3600
        else:
            # Default to 1 hour from now
            return now + 3600
    
    def _scheduler_loop(self):
        """
        Background loop for scheduled tasks.
        
        Phase 3: Enhanced to support multiple schedule types and event-driven tasks.
        All scheduled work creates Tasks that go through the normal execution pipeline.
        """
        while self.running:
            try:
                now = time.time()
                
                # Check scheduled tasks
                for task_id in list(self.schedules):
                    if task_id not in self.scheduled_tasks:
                        continue
                    
                    schedule = self.scheduled_tasks[task_id]
                    
                    if not schedule["active"]:
                        continue
                    
                    # Check if it's time to run
                    if now >= schedule["next_run"]:
                        # Submit task to queue (goes through normal pipeline)
                        task = schedule["task"]
                        
                        # Create a new task instance for this execution
                        if CORE_CONTRACTS_AVAILABLE:
                            new_task = Task(
                                task_id=generate_task_id(),
                                goal=task.goal,
                                priority=task.priority,
                                agent_id=task.agent_id,
                                task_type=task.task_type,
                                context=task.context.copy(),
                                parameters=task.parameters.copy(),
                                metadata={"scheduled": True, "parent_task_id": task.task_id}
                            )
                        else:
                            new_task = task
                        
                        # Submit to queue (goes through Agent Manager → Permission → Tool pipeline)
                        if self.task_queue:
                            self.task_queue.enqueue(new_task)
                            print(f"Submitted scheduled task: {new_task.task_id}")
                        
                        # Update schedule
                        schedule["last_run"] = now
                        schedule["next_run"] = self._calculate_next_run(
                            schedule["schedule_type"],
                            schedule["schedule_config"]
                        )
                
                # Sleep for 10 seconds
                time.sleep(10)
                
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(30)
    
    def cancel_schedule(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: The task ID to cancel
            
        Returns:
            True if schedule was cancelled
        """
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id]["active"] = False
            if task_id in self.schedules:
                self.schedules.remove(task_id)
            print(f"Cancelled schedule for task: {task_id}")
            return True
        return False
    
    def get_scheduled_tasks(self) -> Dict[str, Any]:
        """
        Get information about all scheduled tasks.
        
        Returns:
            Dictionary of scheduled task information
        """
        scheduled_info = {}
        for task_id, schedule in self.scheduled_tasks.items():
            scheduled_info[task_id] = {
                "task_id": task_id,
                "goal": schedule["task"].goal,
                "schedule_type": schedule["schedule_type"],
                "schedule_config": schedule["schedule_config"],
                "next_run": schedule["next_run"],
                "last_run": schedule["last_run"],
                "active": schedule["active"]
            }
        return scheduled_info
    
    # ==================== PHASE 1 EXECUTION INTERFACE ====================
    
    def get_agent_for_task(self, task_decision: TaskDecision) -> Optional[str]:
        """
        Select the appropriate agent for a task based on AI decision.
        
        Phase 1: Agent selection interface for AI → Agent Manager coordination.
        
        Args:
            task_decision: The AI's task decision with suggested agent
            
        Returns:
            Agent ID or None if no suitable agent found
        """
        # If AI suggested an agent, check if it's available
        if task_decision.suggested_agent:
            agent = self.get_agent(task_decision.suggested_agent)
            if agent:
                return task_decision.suggested_agent
        
        # Fall back to task type-based selection
        task_type = task_decision.task.context.get("task_type", "unknown")
        
        if task_type == "media_operation":
            return "MediaAgent" if self.get_agent("MediaAgent") else None
        elif task_type == "system_maintenance":
            return "ServerAgent" if self.get_agent("ServerAgent") else None
        elif task_type == "photo_organization":
            return "PhotoAgent" if self.get_agent("PhotoAgent") else None
        elif task_type == "development":
            return "DevelopmentAgent" if self.get_agent("DevelopmentAgent") else None
        
        # No suitable agent found
        return None
    
    def plan_execution(self, agent_id: str, task: Task) -> Optional[ExecutionPlan]:
        """
        Get execution plan from an agent for a task.
        
        Phase 1: Execution planning interface for Agent → Agent Manager coordination.
        
        Args:
            agent_id: The agent to plan execution
            task: The task to plan execution for
            
        Returns:
            ExecutionPlan or None if planning failed
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        
        try:
            # For now, create a simple execution plan
            # In a full implementation, the agent would create the plan
            
            if CORE_CONTRACTS_AVAILABLE:
                correlation_id = generate_correlation_id()
            else:
                correlation_id = None
            
            # Create a simple single-step plan
            step = ExecutionStep(
                step_id=f"step_1",
                description=f"Execute task: {task.goal}",
                tool="execute_task",
                parameters={"task": task.goal},
                status=TaskStatus.PENDING,
                verification_required=True,
                permission_level=PermissionLevel.SAFE
            )
            
            plan = ExecutionPlan(
                plan_id=f"plan_{task.task_id}",
                task_id=task.task_id,
                agent_id=agent_id,
                steps=[step],
                estimated_duration=60.0,
                created_at=time.time()
            )
            
            return plan
            
        except Exception as e:
            print(f"Error planning execution: {e}")
            return None
    
    def execute_agent_task_with_plan(self, agent_id: str, plan: ExecutionPlan) -> Dict:
        """
        Execute a task using an execution plan.
        
        Phase 1: Enhanced execution with planning support.
        
        Args:
            agent_id: The agent to execute the task
            plan: The execution plan to follow
            
        Returns:
            Execution results
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return {"success": False, "error": f"Agent '{agent_id}' not found"}
        
        try:
            # Execute the plan step by step
            results = {
                "success": False,
                "steps_completed": 0,
                "steps_failed": 0,
                "final_result": None,
                "error": None
            }
            
            for step in plan.steps:
                # For now, just use the basic execute_task
                # In a full implementation, this would use the tool system
                result = agent.execute_task(step.parameters.get("task", plan.task_id))
                
                if result and "error" not in result.lower():
                    results["steps_completed"] += 1
                else:
                    results["steps_failed"] += 1
            
            results["success"] = results["steps_failed"] == 0
            results["final_result"] = f"Plan executed: {results['steps_completed']}/{len(plan.steps)} steps completed"
            
            return results
            
        except Exception as e:
            return {"success": False, "error": f"Execution error: {str(e)}"}