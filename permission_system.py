"""
Permission and Safety System for Serena's Agentic Harness
This module handles approval workflows, safety checks, and dangerous operation management.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum


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

def get_permission_system(config_file: str = "permission_config.json") -> PermissionSystem:
    """Get or create the global PermissionSystem instance."""
    global _permission_system
    if _permission_system is None:
        _permission_system = PermissionSystem(config_file)
    return _permission_system


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