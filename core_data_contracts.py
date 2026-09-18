"""
Core Data Contracts for Serena Phase 1
Standardized data structures for the secure execution pipeline

This module defines the authoritative data contracts that will be used throughout:
- AI decision-making
- Agent coordination  
- Permission system
- Tool execution
- Verification
- Audit logging

Existing objects from agentic_executor.py (TaskStep, AgenticTask) are adapted here
to maintain compatibility while adding Phase 1 required fields.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime


# ==================== ENUMS ====================

class TaskStatus(Enum):
    """Status of a task in the execution pipeline."""
    PENDING = "pending"
    PLANNING = "planning"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class PermissionLevel(Enum):
    """Permission level for operations."""
    SAFE = "safe"
    WARNING = "warning"
    DANGEROUS = "dangerous"
    FORBIDDEN = "forbidden"


class ApprovalStatus(Enum):
    """Status of approval requests."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class VerificationStatus(Enum):
    """Status of verification checks."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    UNCERTAIN = "uncertain"
    SKIPPED = "skipped"


class RequestType(Enum):
    """Type of user request."""
    CONVERSATION = "conversation"
    CREATIVE_WRITING = "creative_writing"
    BOOK_WRITING = "book_writing"
    CODING_ASSISTANCE = "coding_assistance"
    MEDIA = "media"
    WEB = "web"
    SYSTEM_TASK = "system_task"
    SCHEDULED_TASK = "scheduled_task"
    EVENT_TASK = "event_task"
    AGENT_MANAGEMENT = "agent_management"
    UNKNOWN = "unknown"


class Capability(Enum):
    """Conversational capabilities."""
    CHAT = "chat"
    ROMANTIC = "romantic"
    CODING = "coding"
    BOOK_WRITING = "book_writing"
    CREATIVE_WRITING = "creative_writing"
    MEDIA = "media"
    WEB = "web"
    BACKUP = "backup"
    SECURITY = "security"
    MONITORING = "monitoring"
    DEVELOPMENT = "development"
    AGENT_MANAGEMENT = "agent_management"
    UNKNOWN = "unknown"


class AgentType(Enum):
    """Specialized agent types."""
    DEVELOPMENT = "development"
    BACKUP = "backup"
    SECURITY = "security"
    MONITORING = "monitoring"
    MEDIA = "media"
    SERVER = "server"
    PHOTO = "photo"
    NONE = None


# ==================== TASK OBJECTS ====================

@dataclass
class Task:
    """
    High-level task representing work to be done.
    Created by AI decision-making, consumed by Agent Manager.
    
    Phase 2: Enhanced with full lifecycle support, dependencies, and retry information.
    """
    task_id: str
    goal: str
    priority: int = 5  # 1-10, 10 being highest
    agent_id: Optional[str] = None  # Assigned by Agent Manager
    task_type: Optional[str] = None  # Type of task (media_operation, system_maintenance, etc.)
    created_at: float = field(default_factory=time.time)
    assigned_at: Optional[float] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: TaskStatus = TaskStatus.PENDING
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Task IDs this task depends on
    dependent_tasks: List[str] = field(default_factory=list)  # Task IDs that depend on this task
    parent_task_id: Optional[str] = None  # For multi-agent coordination
    child_task_ids: List[str] = field(default_factory=list)  # For multi-agent coordination
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: Optional[float] = None
    result: Optional[Any] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission."""
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "priority": self.priority,
            "agent_id": self.agent_id,
            "task_type": self.task_type,
            "created_at": self.created_at,
            "assigned_at": self.assigned_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status.value,
            "context": self.context,
            "metadata": self.metadata,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "dependent_tasks": self.dependent_tasks,
            "parent_task_id": self.parent_task_id,
            "child_task_ids": self.child_task_ids,
            "correlation_id": self.correlation_id,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "result": str(self.result) if self.result else None,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        """Create Task from dictionary."""
        return cls(
            task_id=data["task_id"],
            goal=data["goal"],
            priority=data.get("priority", 5),
            agent_id=data.get("agent_id"),
            task_type=data.get("task_type"),
            created_at=data.get("created_at", time.time()),
            assigned_at=data.get("assigned_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            status=TaskStatus(data.get("status", "pending")),
            context=data.get("context", {}),
            metadata=data.get("metadata", {}),
            parameters=data.get("parameters", {}),
            dependencies=data.get("dependencies", []),
            dependent_tasks=data.get("dependent_tasks", []),
            parent_task_id=data.get("parent_task_id"),
            child_task_ids=data.get("child_task_ids", []),
            correlation_id=data.get("correlation_id"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds"),
            result=data.get("result"),
            error_message=data.get("error_message")
        )
    
    def assign(self, agent_id: str) -> None:
        """Assign task to an agent."""
        self.agent_id = agent_id
        self.assigned_at = time.time()
        self.status = TaskStatus.ASSIGNED
    
    def start(self) -> None:
        """Mark task as started."""
        self.started_at = time.time()
        self.status = TaskStatus.IN_PROGRESS
    
    def complete(self, result: Any = None) -> None:
        """Mark task as completed."""
        self.completed_at = time.time()
        self.status = TaskStatus.COMPLETED
        self.result = result
    
    def fail(self, error_message: str) -> None:
        """Mark task as failed."""
        self.completed_at = time.time()
        self.status = TaskStatus.FAILED
        self.error_message = error_message
    
    def block(self, reason: str) -> None:
        """Mark task as blocked."""
        self.status = TaskStatus.BLOCKED
        self.error_message = reason
    
    def cancel(self) -> None:
        """Mark task as cancelled."""
        self.completed_at = time.time()
        self.status = TaskStatus.CANCELLED
    
    def retry(self) -> bool:
        """Increment retry count. Returns True if retries remain."""
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            self.status = TaskStatus.RETRYING
            return True
        return False
    
    def is_expired(self) -> bool:
        """Check if task has exceeded its timeout."""
        if self.timeout_seconds is None:
            return False
        if self.started_at is None:
            return False
        return time.time() - self.started_at > self.timeout_seconds
    
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries


@dataclass
class TaskDecision:
    """
    AI's decision about what should happen.
    Output from AI decision-making, input to Agent Manager.
    
    Phase 4I: This is being replaced by RequestClassification for better separation
    between conversational intent and agent execution.
    """
    decision_id: str
    task: Task
    confidence: float  # 0.0 to 1.0
    reasoning: str
    suggested_agent: Optional[str] = None
    suggested_parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission."""
        return {
            "decision_id": self.decision_id,
            "task": self.task.to_dict(),
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "suggested_agent": self.suggested_agent,
            "suggested_parameters": self.suggested_parameters,
            "created_at": self.created_at
        }


@dataclass
class RequestClassification:
    """
    Formal classification contract for user requests.
    
    This separates conversational intent from agent execution requirements.
    The classifier answers "What is this request?" not "Am I allowed to execute this?"
    
    Fields:
        request_type: Broad category of the request (conversation, system_task, etc.)
        capability: What capability is being requested (chat, coding, media, etc.)
        character: Which character is handling the interaction (serena, astrid, bulma, none)
        requires_agent: Whether this requires specialized-agent execution
        agent_type: Which agent is required (only if requires_agent=True)
        action: What operation is being requested
        target: What the action applies to
        parameters: Structured information for the request
        confidence: Classifier's confidence in the classification
        reason: Explanation of the classification
    """
    request_type: RequestType
    capability: Capability
    character: str  # "serena", "astrid", "bulma", "none"
    requires_agent: bool
    agent_type: Optional[AgentType] = None  # Must be None if requires_agent=False
    action: str = "unknown"
    target: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5  # 0.0 to 1.0
    reason: str = ""
    created_at: float = field(default_factory=time.time)
    
    def validate(self) -> bool:
        """
        Validate the classification invariants.
        
        Invariants:
        1. If requires_agent=False, then agent_type must be None
        2. If request_type=CONVERSATION, then requires_agent should be False
        3. Classification does not grant authorization
        """
        # Invariant 1: requires_agent=False implies agent_type=None
        if not self.requires_agent and self.agent_type is not None:
            return False
        
        # Invariant 2: conversation requests should not require agents by default
        if self.request_type == RequestType.CONVERSATION and self.requires_agent:
            # Allow this only for explicitly documented exceptions
            pass
        
        return True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission."""
        return {
            "request_type": self.request_type.value if isinstance(self.request_type, RequestType) else self.request_type,
            "capability": self.capability.value if isinstance(self.capability, Capability) else self.capability,
            "character": self.character,
            "requires_agent": self.requires_agent,
            "agent_type": self.agent_type.value if self.agent_type and isinstance(self.agent_type, AgentType) else self.agent_type,
            "action": self.action,
            "target": self.target,
            "parameters": self.parameters,
            "confidence": self.confidence,
            "reason": self.reason,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RequestClassification':
        """Create RequestClassification from dictionary."""
        return cls(
            request_type=RequestType(data.get("request_type", "unknown")),
            capability=Capability(data.get("capability", "unknown")),
            character=data.get("character", "none"),
            requires_agent=data.get("requires_agent", False),
            agent_type=AgentType(data["agent_type"]) if data.get("agent_type") else None,
            action=data.get("action", "unknown"),
            target=data.get("target"),
            parameters=data.get("parameters", {}),
            confidence=data.get("confidence", 0.5),
            reason=data.get("reason", ""),
            created_at=data.get("created_at", time.time())
        )


@dataclass
class ExecutionPlan:
    """
    Agent's plan for how to execute a task.
    Created by Agent, consumed by Permission System and Executor.
    """
    plan_id: str
    task_id: str
    agent_id: str
    steps: List['ExecutionStep']
    estimated_duration: Optional[float] = None
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission."""
        return {
            "plan_id": self.plan_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "steps": [step.to_dict() for step in self.steps],
            "estimated_duration": self.estimated_duration,
            "resource_requirements": self.resource_requirements,
            "dependencies": self.dependencies,
            "created_at": self.created_at
        }


@dataclass
class ExecutionStep:
    """
    Single execution step within an ExecutionPlan.
    Adapted from agentic_executor.py TaskStep to maintain compatibility.
    """
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
    estimated_duration: Optional[float] = None
    verification_required: bool = True
    permission_level: PermissionLevel = PermissionLevel.SAFE
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission."""
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
            "dependencies": self.dependencies,
            "estimated_duration": self.estimated_duration,
            "verification_required": self.verification_required,
            "permission_level": self.permission_level.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ExecutionStep':
        """Create ExecutionStep from dictionary."""
        return cls(
            step_id=data["step_id"],
            description=data["description"],
            tool=data["tool"],
            parameters=data["parameters"],
            status=TaskStatus(data.get("status", "pending")),
            result=data.get("result"),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            dependencies=data.get("dependencies", []),
            estimated_duration=data.get("estimated_duration"),
            verification_required=data.get("verification_required", True),
            permission_level=PermissionLevel(data.get("permission_level", "safe"))
        )


# ==================== PERMISSION OBJECTS ====================

@dataclass
class PermissionRequest:
    """
    Request for permission to perform an operation.
    Input to Permission System, output includes PermissionDecision.
    """
    request_id: str
    operation: str
    agent_id: str
    parameters: Dict[str, Any]
    context: Dict[str, Any]
    permission_level: PermissionLevel = PermissionLevel.SAFE
    correlation_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission."""
        return {
            "request_id": self.request_id,
            "operation": self.operation,
            "agent_id": self.agent_id,
            "parameters": self.parameters,
            "context": self.context,
            "permission_level": self.permission_level.value,
            "correlation_id": self.correlation_id,
            "created_at": self.created_at
        }


@dataclass
class PermissionDecision:
    """
    Decision about whether an operation is permitted.
    Output from Permission System.
    """
    request_id: str
    allowed: bool
    reason: str
    permission_level: PermissionLevel
    requires_approval: bool = False
    conditions: List[str] = field(default_factory=list)
    correlation_id: Optional[str] = None
    decided_at: float = field(default_factory=time.time)
    decided_by: str = "CentralizedPermissionSystem"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission."""
        return {
            "request_id": self.request_id,
            "allowed": self.allowed,
            "reason": self.reason,
            "permission_level": self.permission_level.value,
            "requires_approval": self.requires_approval,
            "conditions": self.conditions,
            "correlation_id": self.correlation_id,
            "decided_at": self.decided_at,
            "decided_by": self.decided_by
        }


@dataclass
class ApprovalRequest:
    """
    Request for human approval of dangerous operations.
    Created when PermissionDecision requires approval.
    """
    approval_id: str
    operation: str
    agent_id: str
    details: str
    danger_level: PermissionLevel
    correlation_id: Optional[str] = None
    timeout_seconds: int = 300  # 5 minutes default
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    denied_reason: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission."""
        return {
            "approval_id": self.approval_id,
            "operation": self.operation,
            "agent_id": self.agent_id,
            "details": self.details,
            "danger_level": self.danger_level.value,
            "correlation_id": self.correlation_id,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "status": self.status.value,
            "approved_by": self.approved_by,
            "denied_reason": self.denied_reason
        }
    
    def is_expired(self) -> bool:
        """Check if approval request has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def grant(self, user: str) -> None:
        """Grant approval."""
        self.status = ApprovalStatus.APPROVED
        self.approved_by = user
    
    def deny(self, reason: str) -> None:
        """Deny approval."""
        self.status = ApprovalStatus.DENIED
        self.denied_reason = reason


# ==================== EXECUTION OBJECTS ====================

@dataclass
class ToolResult:
    """
    Result from tool execution.
    Output from tool, input to verification.
    """
    tool: str
    operation: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    executed_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission."""
        return {
            "tool": self.tool,
            "operation": self.operation,
            "success": self.success,
            "result": str(self.result) if self.result else None,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
            "correlation_id": self.correlation_id,
            "executed_at": self.executed_at
        }


@dataclass
class VerificationResult:
    """
    Result of verification check.
    Separate from permission - verifies that operation actually worked.
    """
    verification_id: str
    operation: str
    tool: str
    status: VerificationStatus
    details: str
    verified_at: float = field(default_factory=time.time)
    can_rollback: bool = False
    rollback_action: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission."""
        return {
            "verification_id": self.verification_id,
            "operation": self.operation,
            "tool": self.tool,
            "status": self.status.value,
            "details": self.details,
            "verified_at": self.verified_at,
            "can_rollback": self.can_rollback,
            "rollback_action": self.rollback_action,
            "correlation_id": self.correlation_id
        }


@dataclass
class TaskResult:
    """
    Final result of task execution.
    Aggregates ToolResults and VerificationResults.
    """
    task_id: str
    goal: str
    status: TaskStatus
    success: bool
    final_result: Any
    execution_results: List[ToolResult] = field(default_factory=list)
    verification_results: List[VerificationResult] = field(default_factory=list)
    error_message: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    total_execution_time: float = 0.0
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission."""
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "status": self.status.value,
            "success": self.success,
            "final_result": str(self.final_result) if self.final_result else None,
            "execution_results": [r.to_dict() for r in self.execution_results],
            "verification_results": [r.to_dict() for r in self.verification_results],
            "error_message": self.error_message,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_execution_time": self.total_execution_time,
            "correlation_id": self.correlation_id
        }


# ==================== AUDIT OBJECTS ====================

@dataclass
class AuditEntry:
    """
    Single audit log entry.
    Records lifecycle events with correlation IDs.
    """
    entry_id: str
    event_type: str
    correlation_id: Optional[str]
    task_id: Optional[str]
    agent_id: Optional[str]
    operation: Optional[str]
    details: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    outcome: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission."""
        return {
            "entry_id": self.entry_id,
            "event_type": self.event_type,
            "correlation_id": self.correlation_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "operation": self.operation,
            "details": self.details,
            "timestamp": self.timestamp,
            "outcome": self.outcome,
            "metadata": self.metadata
        }


# ==================== COMPATIBILITY LAYER ====================

# Compatibility layer for existing agentic_executor.py objects
def adapt_task_step_to_execution_step(task_step) -> ExecutionStep:
    """Convert existing TaskStep to ExecutionStep for compatibility."""
    return ExecutionStep(
        step_id=task_step.step_id,
        description=task_step.description,
        tool=task_step.tool,
        parameters=task_step.parameters,
        status=TaskStatus(task_step.status.value),
        result=task_step.result,
        error=task_step.error,
        retry_count=task_step.retry_count,
        max_retries=task_step.max_retries,
        dependencies=task_step.dependencies,
        verification_required=True,  # Phase 1 requirement
        permission_level=PermissionLevel.SAFE  # Default, will be set by permission system
    )


def adapt_agentic_task_to_task(agentic_task) -> Task:
    """Convert existing AgenticTask to Task for compatibility."""
    return Task(
        task_id=agentic_task.task_id,
        goal=agentic_task.goal,
        context=agentic_task.context,
        metadata={"status": agentic_task.status.value}
    )


# ==================== FACTORY FUNCTIONS ====================

def generate_correlation_id() -> str:
    """Generate unique correlation ID for tracking operation lifecycle."""
    return str(uuid.uuid4())


def generate_task_id() -> str:
    """Generate unique task ID."""
    return f"task_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


def generate_request_id() -> str:
    """Generate unique permission request ID."""
    return f"perm_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


def generate_approval_id() -> str:
    """Generate unique approval request ID."""
    return f"approval_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


def generate_verification_id() -> str:
    """Generate unique verification ID."""
    return f"verify_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


def generate_audit_id() -> str:
    """Generate unique audit entry ID."""
    return f"audit_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"