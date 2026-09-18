"""
Centralized Permission and Safety System for Serena
Phase 1: Single authoritative permission boundary for all operations

This module provides the CentralizedPermissionSystem that enforces the security model:
AI → Router/Planner → Agent Manager → Agent → Permission System → Tool → Execute → Verify → Audit Log → Result
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import uuid

# Try to import Phase 1 core data contracts, provide fallbacks if not available
try:
    from core_data_contracts import (
        PermissionRequest, PermissionDecision, ApprovalRequest, 
        ApprovalStatus, PermissionLevel, generate_correlation_id,
        generate_request_id, generate_approval_id
    )
    CORE_CONTRACTS_AVAILABLE = True
except ImportError:
    CORE_CONTRACTS_AVAILABLE = False
    
    # Fallback definitions for Phase 1 data contracts
    class PermissionLevel(Enum):
        SAFE = "safe"
        WARNING = "warning"
        DANGEROUS = "dangerous"
        FORBIDDEN = "forbidden"
    
    class ApprovalStatus(Enum):
        PENDING = "pending"
        APPROVED = "approved"
        DENIED = "denied"
        EXPIRED = "expired"
        CANCELLED = "cancelled"
    
    @dataclass
    class PermissionRequest:
        request_id: str
        operation: str
        agent_id: str
        parameters: Dict[str, Any]
        context: Dict[str, Any]
        permission_level: PermissionLevel = PermissionLevel.SAFE
        correlation_id: Optional[str] = None
        created_at: float = field(default_factory=time.time)
        
        def to_dict(self) -> Dict:
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
        approval_id: str
        operation: str
        agent_id: str
        details: str
        danger_level: PermissionLevel
        correlation_id: Optional[str] = None
        timeout_seconds: int = 300
        created_at: float = field(default_factory=time.time)
        expires_at: Optional[float] = None
        status: ApprovalStatus = ApprovalStatus.PENDING
        approved_by: Optional[str] = None
        denied_reason: Optional[str] = None
        
        def to_dict(self) -> Dict:
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
            if self.expires_at is None:
                return False
            return time.time() > self.expires_at
        
        def grant(self, user: str) -> None:
            self.status = ApprovalStatus.APPROVED
            self.approved_by = user
        
        def deny(self, reason: str) -> None:
            self.status = ApprovalStatus.DENIED
            self.denied_reason = reason
    
    def generate_correlation_id() -> str:
        return str(uuid.uuid4())
    
    def generate_request_id() -> str:
        return f"perm_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    
    def generate_approval_id() -> str:
        return f"approval_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    
    # Fix type reference
    from typing import Any as AnyType
    Any = AnyType


class DangerLevel(Enum):
    """Classification of operation danger levels."""
    SAFE = "safe"           # No approval needed
    WARNING = "warning"     # Inform user, proceed automatically
    DANGEROUS = "dangerous" # Require explicit approval
    FORBIDDEN = "forbidden" # Never allow


class PermissionRequest:
    """Represents a permission request for a dangerous operation."""
    
    def __init__(self, operation: str, details: str, danger_level: DangerLevel, 
                 timestamp: float = None, auto_approve: bool = False):
        self.operation = operation
        self.details = details
        self.danger_level = danger_level
        self.timestamp = timestamp or time.time()
        self.auto_approve = auto_approve
        self.approved = False
        self.denied = False
        self.response = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "operation": self.operation,
            "details": self.details,
            "danger_level": self.danger_level.value,
            "timestamp": self.timestamp,
            "auto_approve": self.auto_approve,
            "approved": self.approved,
            "denied": self.denied,
            "response": self.response
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PermissionRequest':
        """Create from dictionary."""
        request = cls(
            operation=data["operation"],
            details=data["details"],
            danger_level=DangerLevel(data["danger_level"]),
            timestamp=data["timestamp"],
            auto_approve=data["auto_approve"]
        )
        request.approved = data["approved"]
        request.denied = data["denied"]
        request.response = data["response"]
        return request


class PermissionSystem:
    """
    Manages permissions and safety checks for agentic operations.
    """
    
    def __init__(self, config_file: str = "permission_config.json"):
        """
        Initialize the permission system.
        
        Args:
            config_file: Path to store permission configuration and history
        """
        self.config_file = Path(config_file)
        self.permission_history: List[PermissionRequest] = []
        self.auto_approve_rules: Dict[str, DangerLevel] = {}
        self.load_config()
        
        # Default safety rules
        self._setup_default_rules()
        
        # Add organize_files to the rules
        self.auto_approve_rules["organize_files"] = DangerLevel.WARNING
        
        # Add analysis tools to safe operations
        analysis_tools = ["analyze_files", "analyze_task", "analyze_code", "analyze_results", "verify_results", "execute_action"]
        for tool in analysis_tools:
            self.auto_approve_rules[tool] = DangerLevel.SAFE
    
    def _setup_default_rules(self):
        """Setup default safety rules for common operations."""
        default_rules = {
            # File operations
            "read_file": DangerLevel.SAFE,
            "write_file": DangerLevel.SAFE,
            "list_files": DangerLevel.SAFE,
            "create_directory": DangerLevel.SAFE,
            "rename_file": DangerLevel.WARNING,
            "delete_file": DangerLevel.DANGEROUS,
            
            # System operations
            "get_system_info": DangerLevel.SAFE,
            "run_command": DangerLevel.WARNING,
            
            # Web operations
            "web_search": DangerLevel.SAFE,
            
            # Dangerous patterns
            "rm -rf": DangerLevel.FORBIDDEN,
            "del /f": DangerLevel.FORBIDDEN,
            "format": DangerLevel.FORBIDDEN,
            "shutdown": DangerLevel.FORBIDDEN,
            "reboot": DangerLevel.FORBIDDEN,
            "sudo": DangerLevel.WARNING,
            "administrator": DangerLevel.WARNING,
        }
        
        # Merge with existing rules
        for operation, level in default_rules.items():
            if operation not in self.auto_approve_rules:
                self.auto_approve_rules[operation] = level
    
    def check_permission(self, operation: str, details: str = "") -> Tuple[bool, str, PermissionRequest]:
        """
        Check if an operation requires permission approval.
        
        Args:
            operation: The operation being performed
            details: Additional details about the operation
            
        Returns:
            Tuple of (allowed, message, permission_request)
        """
        # Check for forbidden operations
        for forbidden_pattern, level in self.auto_approve_rules.items():
            if level == DangerLevel.FORBIDDEN and forbidden_pattern.lower() in operation.lower() or forbidden_pattern.lower() in details.lower():
                request = PermissionRequest(operation, details, DangerLevel.FORBIDDEN)
                request.denied = True
                request.response = "Operation is forbidden by safety rules"
                self.permission_history.append(request)
                return False, f"FORBIDDEN: {forbidden_pattern} operations are not allowed", request
        
        # Check for auto-approved safe operations
        if operation in self.auto_approve_rules:
            danger_level = self.auto_approve_rules[operation]
            
            if danger_level == DangerLevel.SAFE:
                request = PermissionRequest(operation, details, DangerLevel.SAFE, auto_approve=True)
                request.approved = True
                self.permission_history.append(request)
                return True, "Operation approved (safe)", request
            
            elif danger_level == DangerLevel.WARNING:
                request = PermissionRequest(operation, details, DangerLevel.WARNING, auto_approve=True)
                request.approved = True
                request.response = "Warning acknowledged, proceeding"
                self.permission_history.append(request)
                return True, f"WARNING: {details} - Proceeding anyway", request
            
            elif danger_level == DangerLevel.DANGEROUS:
                request = PermissionRequest(operation, details, DangerLevel.DANGEROUS)
                self.permission_history.append(request)
                return False, f"APPROVAL REQUIRED: {operation} - {details}", request
        
        # Default to requiring approval for unknown operations
        request = PermissionRequest(operation, details, DangerLevel.DANGEROUS)
        self.permission_history.append(request)
        return False, f"APPROVAL REQUIRED: Unknown operation '{operation}'", request
    
    def approve_request(self, request: PermissionRequest, approved: bool, response: str = ""):
        """
        Approve or deny a permission request.
        
        Args:
            request: The permission request to respond to
            approved: Whether to approve the request
            response: Optional response message
        """
        request.approved = approved
        request.denied = not approved
        request.response = response
        
        if approved:
            # Learn from approval - make similar operations safer in the future
            self._learn_from_approval(request)
        
        self.save_config()
    
    def _learn_from_approval(self, request: PermissionRequest):
        """
        Learn from user approvals to adjust safety rules.
        """
        # If user approved a dangerous operation, consider making it a warning level
        if request.danger_level == DangerLevel.DANGEROUS and request.approved:
            # Check if this operation has been approved multiple times
            similar_approvals = [
                r for r in self.permission_history 
                if r.operation == request.operation and r.approved
            ]
            
            if len(similar_approvals) >= 3:
                # After 3 approvals, downgrade to warning level
                self.auto_approve_rules[request.operation] = DangerLevel.WARNING
                print(f"Learned: Downgraded '{request.operation}' to WARNING level after {len(similar_approvals)} approvals")
    
    def set_rule(self, operation: str, danger_level: DangerLevel):
        """
        Manually set a safety rule for an operation.
        
        Args:
            operation: The operation to set a rule for
            danger_level: The danger level to assign
        """
        self.auto_approve_rules[operation] = danger_level
        self.save_config()
    
    def get_pending_requests(self) -> List[PermissionRequest]:
        """Get all pending permission requests."""
        return [r for r in self.permission_history if not r.approved and not r.denied]
    
    def get_recent_history(self, limit: int = 10) -> List[PermissionRequest]:
        """Get recent permission history."""
        return self.permission_history[-limit:]
    
    def save_config(self):
        """Save configuration and history to file."""
        try:
            config = {
                "auto_approve_rules": {op: level.value for op, level in self.auto_approve_rules.items()},
                "permission_history": [req.to_dict() for req in self.permission_history]
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving permission config: {e}")
    
    def load_config(self):
        """Load configuration and history from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Load rules
                self.auto_approve_rules = {
                    op: DangerLevel(level) 
                    for op, level in config.get("auto_approve_rules", {}).items()
                }
                
                # Load history
                self.permission_history = [
                    PermissionRequest.from_dict(req_data)
                    for req_data in config.get("permission_history", [])
                ]
        except Exception as e:
            print(f"Error loading permission config: {e}")
            # Initialize with defaults if load fails
            self.auto_approve_rules = {}
            self.permission_history = []
    
    def clear_history(self):
        """Clear permission history."""
        self.permission_history = []
        self.save_config()
    
    def get_stats(self) -> Dict:
        """Get statistics about permission usage."""
        total = len(self.permission_history)
        approved = sum(1 for r in self.permission_history if r.approved)
        denied = sum(1 for r in self.permission_history if r.denied)
        pending = sum(1 for r in self.permission_history if not r.approved and not r.denied)
        
        by_level = {}
        for level in DangerLevel:
            by_level[level.value] = sum(
                1 for r in self.permission_history if r.danger_level == level
            )
        
        return {
            "total_requests": total,
            "approved": approved,
            "denied": denied,
            "pending": pending,
            "by_danger_level": by_level,
            "active_rules": len(self.auto_approve_rules)
        }


# Global instance
_permission_system = None
_centralized_permission_system = None

def get_permission_system(config_file: str = "permission_config.json") -> PermissionSystem:
    """Get or create the global PermissionSystem instance (legacy)."""
    global _permission_system
    if _permission_system is None:
        _permission_system = PermissionSystem(config_file)
    return _permission_system

def get_centralized_permission_system(config_file: str = "permission_config.json") -> 'CentralizedPermissionSystem':
    """Get or create the global CentralizedPermissionSystem instance (Phase 1)."""
    global _centralized_permission_system
    if _centralized_permission_system is None:
        _centralized_permission_system = CentralizedPermissionSystem(config_file)
    return _centralized_permission_system


class CentralizedPermissionSystem:
    """
    Phase 1: Single authoritative permission boundary for all operations.
    
    This is the centralized authority that enforces:
    - AI → Agent → Permission → Tool pipeline
    - No bypass allowed
    - Consistent permission checking across all components
    - Agent-specific permission profiles
    - Approval workflow for dangerous operations
    - Correlation ID tracking for audit trail
    """
    
    def __init__(self, config_file: str = "permission_config.json"):
        """
        Initialize the centralized permission system.
        
        Args:
            config_file: Path to store permission configuration and history
        """
        self.config_file = Path(config_file)
        self.permission_history: List = []
        self.agent_permissions: Dict[str, Dict] = {}
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.auto_approve_rules: Dict[str, PermissionLevel] = {}
        
        # Load existing configuration
        self.load_config()
        
        # Setup default safety rules
        self._setup_default_rules()
        
        # Setup agent-specific permission profiles
        self._setup_agent_profiles()
    
    def _setup_default_rules(self):
        """Setup default safety rules for common operations."""
        default_rules = {
            # File operations
            "read_file": PermissionLevel.SAFE,
            "write_file": PermissionLevel.SAFE,
            "list_files": PermissionLevel.SAFE,
            "create_directory": PermissionLevel.SAFE,
            "rename_file": PermissionLevel.WARNING,
            "delete_file": PermissionLevel.DANGEROUS,
            
            # System operations
            "get_system_info": PermissionLevel.SAFE,
            "run_command": PermissionLevel.WARNING,
            
            # Web operations
            "web_search": PermissionLevel.SAFE,
            
            # Agent operations
            "execute_task": PermissionLevel.SAFE,
            "plan_execution": PermissionLevel.SAFE,
            
            # Analysis operations
            "analyze_files": PermissionLevel.SAFE,
            "analyze_task": PermissionLevel.SAFE,
            "analyze_code": PermissionLevel.SAFE,
            "analyze_results": PermissionLevel.SAFE,
            "verify_results": PermissionLevel.SAFE,
            "execute_action": PermissionLevel.SAFE,
            
            # Dangerous patterns
            "rm -rf": PermissionLevel.FORBIDDEN,
            "del /f": PermissionLevel.FORBIDDEN,
            "format": PermissionLevel.FORBIDDEN,
            "shutdown": PermissionLevel.FORBIDDEN,
            "reboot": PermissionLevel.FORBIDDEN,
            "sudo": PermissionLevel.WARNING,
            "administrator": PermissionLevel.WARNING,
        }
        
        # Merge with existing rules
        for operation, level in default_rules.items():
            if operation not in self.auto_approve_rules:
                self.auto_approve_rules[operation] = level
    
    def _setup_agent_profiles(self):
        """Setup default permission profiles for known agents."""
        # Media Agent permissions
        self.agent_permissions["MediaAgent"] = {
            "read_dirs": ["/home/eirik17/Media"],
            "write_dirs": ["/home/eirik17/Media"],
            "allowed_commands": ["systemctl", "ffprobe"],
            "forbidden_operations": ["rm -rf", "delete"]
        }
        
        # Server Agent permissions
        self.agent_permissions["ServerAgent"] = {
            "read_dirs": ["/home/eirik17", "/var/lib/jellyfinf"],
            "write_dirs": [],
            "allowed_commands": ["systemctl", "df", "free", "uptime", "apt"],
            "forbidden_operations": ["reboot", "shutdown"]
        }
        
        # Photo Agent permissions
        self.agent_permissions["PhotoAgent"] = {
            "read_dirs": ["/home/eirik17/Pictures"],
            "write_dirs": ["/home/eirik17/Pictures"],
            "allowed_commands": ["exiftool"],
            "forbidden_operations": ["rm -rf", "delete"]
        }
    
    def validate_operation(self, operation: str, agent_id: str, context: Dict) -> PermissionDecision:
        """
        Validate an operation and return permission decision.
        
        This is the main entry point for permission checking in Phase 1.
        
        Args:
            operation: The operation being performed
            agent_id: The agent requesting the operation
            context: Additional context (parameters, paths, etc.)
            
        Returns:
            PermissionDecision with allow/deny result and reason
        """
        # Generate correlation ID for tracking
        correlation_id = generate_correlation_id()
        
        # Check for forbidden operations first
        if self._is_operation_forbidden(operation, context):
            return PermissionDecision(
                request_id=generate_request_id(),
                allowed=False,
                reason=f"Operation '{operation}' is forbidden by safety rules",
                permission_level=PermissionLevel.FORBIDDEN,
                correlation_id=correlation_id
            )
        
        # Get agent-specific permissions
        agent_perms = self.agent_permissions.get(agent_id, {})
        
        # Check if operation is in auto-approve rules
        permission_level = self.auto_approve_rules.get(operation, PermissionLevel.DANGEROUS)
        
        # Check if agent has specific permission for this operation
        # (This would be enhanced in future with path/resource restrictions)
        
        # Determine if approval is required
        requires_approval = (permission_level == PermissionLevel.DANGEROUS)
        
        # Create permission decision
        decision = PermissionDecision(
            request_id=generate_request_id(),
            allowed=not requires_approval,
            reason=f"Operation {operation} classified as {permission_level.value}",
            permission_level=permission_level,
            requires_approval=requires_approval,
            correlation_id=correlation_id
        )
        
        # Log the decision
        self._log_permission_decision(operation, agent_id, decision)
        
        return decision
    
    def _is_operation_forbidden(self, operation: str, context: Dict) -> bool:
        """Check if operation contains forbidden patterns."""
        forbidden_patterns = ["rm -rf", "del /f", "format", "shutdown", "reboot"]
        operation_lower = operation.lower()
        
        for pattern in forbidden_patterns:
            if pattern in operation_lower:
                return True
        
        # Check context for forbidden patterns
        context_str = str(context).lower()
        for pattern in forbidden_patterns:
            if pattern in context_str:
                return True
        
        return False
    
    def request_approval(self, operation: str, details: str, context: Dict = None) -> ApprovalRequest:
        """
        Request approval for a dangerous operation.
        
        Args:
            operation: The operation requiring approval
            details: Human-readable description of the operation
            context: Additional context about the operation
            
        Returns:
            ApprovalRequest that can be tracked for user decision
        """
        context = context or {}
        correlation_id = generate_correlation_id()
        
        # Determine danger level
        permission_level = self.auto_approve_rules.get(operation, PermissionLevel.DANGEROUS)
        
        # Map PermissionLevel to the ApprovalRequest's danger level
        danger_level_mapping = {
            PermissionLevel.SAFE: PermissionLevel.SAFE,
            PermissionLevel.WARNING: PermissionLevel.WARNING,
            PermissionLevel.DANGEROUS: PermissionLevel.DANGEROUS,
            PermissionLevel.FORBIDDEN: PermissionLevel.FORBIDDEN
        }
        
        approval = ApprovalRequest(
            approval_id=generate_approval_id(),
            operation=operation,
            agent_id=context.get("agent_id", "unknown"),
            details=details,
            danger_level=danger_level_mapping.get(permission_level, PermissionLevel.DANGEROUS),
            correlation_id=correlation_id,
            timeout_seconds=300,  # 5 minutes
            expires_at=time.time() + 300
        )
        
        # Store in pending approvals
        self.pending_approvals[approval.approval_id] = approval
        
        # Log the approval request
        self._log_approval_request(approval)
        
        return approval
    
    def check_approval_status(self, request_id: str) -> ApprovalStatus:
        """
        Check the status of an approval request.
        
        Args:
            request_id: The approval request ID to check
            
        Returns:
            Current status of the approval request
        """
        if request_id not in self.pending_approvals:
            return ApprovalStatus.CANCELLED
        
        approval = self.pending_approvals[request_id]
        
        if approval.is_expired():
            approval.status = ApprovalStatus.EXPIRED
            del self.pending_approvals[request_id]
            return ApprovalStatus.EXPIRED
        
        return approval.status
    
    def grant_approval(self, request_id: str, user: str = "user") -> bool:
        """
        Grant approval for a pending request.
        
        Args:
            request_id: The approval request ID to approve
            user: The user granting approval
            
        Returns:
            True if approval was granted successfully
        """
        if request_id not in self.pending_approvals:
            return False
        
        approval = self.pending_approvals[request_id]
        approval.grant(user)
        
        # Remove from pending
        del self.pending_approvals[request_id]
        
        # Log the approval
        self._log_approval_decision(approval, approved=True, user=user)
        
        return True
    
    def deny_approval(self, request_id: str, reason: str) -> bool:
        """
        Deny approval for a pending request.
        
        Args:
            request_id: The approval request ID to deny
            reason: The reason for denial
            
        Returns:
            True if approval was denied successfully
        """
        if request_id not in self.pending_approvals:
            return False
        
        approval = self.pending_approvals[request_id]
        approval.deny(reason)
        
        # Remove from pending
        del self.pending_approvals[request_id]
        
        # Log the denial
        self._log_approval_decision(approval, approved=False, reason=reason)
        
        return True
    
    def get_agent_permissions(self, agent_id: str) -> Dict:
        """
        Get permission profile for a specific agent.
        
        Args:
            agent_id: The agent to get permissions for
            
        Returns:
            Dictionary of agent permissions
        """
        return self.agent_permissions.get(agent_id, {})
    
    def set_agent_permissions(self, agent_id: str, permissions: Dict) -> bool:
        """
        Set permission profile for a specific agent.
        
        Args:
            agent_id: The agent to set permissions for
            permissions: Dictionary of permissions
            
        Returns:
            True if permissions were set successfully
        """
        self.agent_permissions[agent_id] = permissions
        self.save_config()
        return True
    
    def _log_permission_decision(self, operation: str, agent_id: str, decision: PermissionDecision):
        """Log a permission decision for audit trail."""
        self.permission_history.append({
            "timestamp": time.time(),
            "event_type": "permission_decision",
            "operation": operation,
            "agent_id": agent_id,
            "decision": decision.to_dict()
        })
    
    def _log_approval_request(self, approval: ApprovalRequest):
        """Log an approval request for audit trail."""
        self.permission_history.append({
            "timestamp": time.time(),
            "event_type": "approval_request",
            "approval": approval.to_dict()
        })
    
    def _log_approval_decision(self, approval: ApprovalRequest, approved: bool, user: str = None, reason: str = None):
        """Log an approval decision for audit trail."""
        self.permission_history.append({
            "timestamp": time.time(),
            "event_type": "approval_decision",
            "approval": approval.to_dict(),
            "approved": approved,
            "user": user,
            "reason": reason
        })
    
    def save_config(self):
        """Save configuration and history to file."""
        try:
            config = {
                "auto_approve_rules": {op: level.value for op, level in self.auto_approve_rules.items()},
                "agent_permissions": self.agent_permissions,
                "permission_history": self.permission_history
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving permission config: {e}")
    
    def load_config(self):
        """Load configuration and history from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Load rules
                self.auto_approve_rules = {
                    op: PermissionLevel(level) 
                    for op, level in config.get("auto_approve_rules", {}).items()
                }
                
                # Load agent permissions
                self.agent_permissions = config.get("agent_permissions", {})
                
                # Load history
                self.permission_history = config.get("permission_history", [])
        except Exception as e:
            print(f"Error loading permission config: {e}")
            # Initialize with defaults if load fails
            self.auto_approve_rules = {}
            self.agent_permissions = {}
            self.permission_history = []
    
    def get_stats(self) -> Dict:
        """Get statistics about permission usage."""
        total = len(self.permission_history)
        
        # Count decisions by type
        permission_decisions = sum(1 for entry in self.permission_history if entry.get("event_type") == "permission_decision")
        approval_requests = sum(1 for entry in self.permission_history if entry.get("event_type") == "approval_request")
        approval_decisions = sum(1 for entry in self.permission_history if entry.get("event_type") == "approval_decision")
        
        return {
            "total_events": total,
            "permission_decisions": permission_decisions,
            "approval_requests": approval_requests,
            "approval_decisions": approval_decisions,
            "pending_approvals": len(self.pending_approvals),
            "agent_profiles": len(self.agent_permissions),
            "active_rules": len(self.auto_approve_rules)
        }


if __name__ == "__main__":
    # Test the permission system
    print("Testing Permission System...")
    
    perm_system = PermissionSystem("test_permission_config.json")
    
    # Test various operations
    print("\n=== Testing Safe Operations ===")
    allowed, message, request = perm_system.check_permission("read_file", "Reading config.txt")
    print(f"read_file: Allowed={allowed}, Message={message}")
    
    print("\n=== Testing Warning Operations ===")
    allowed, message, request = perm_system.check_permission("rename_file", "Renaming important_file.txt to backup.txt")
    print(f"rename_file: Allowed={allowed}, Message={message}")
    
    print("\n=== Testing Dangerous Operations ===")
    allowed, message, request = perm_system.check_permission("delete_file", "Deleting important_data.txt")
    print(f"delete_file: Allowed={allowed}, Message={message}")
    
    print("\n=== Testing Forbidden Operations ===")
    allowed, message, request = perm_system.check_permission("run_command", "rm -rf /important/data")
    print(f"rm -rf: Allowed={allowed}, Message={message}")
    
    # Test approval workflow
    print("\n=== Testing Approval Workflow ===")
    perm_system.approve_request(request, approved=True, response="User approved deletion")
    print(f"Request approved: {request.approved}")
    
    # Show stats
    print("\n=== Permission Stats ===")
    stats = perm_system.get_stats()
    print(json.dumps(stats, indent=2))
    
    # Cleanup
    perm_system.clear_history()
    if Path("test_permission_config.json").exists():
        Path("test_permission_config.json").unlink()