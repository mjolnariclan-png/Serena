"""
Base Agent Framework
Provides the foundation for specialized background agents

Phase 1: Integrated with CentralizedPermissionSystem for single authority
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import shutil

class BaseAgent:
    """Base class for all specialized agents
    
    Phase 1: Uses CentralizedPermissionSystem for authorization
    """
    
    def __init__(self, name: str, workspace: Path, instructions: str = "", permission_system=None):
        self.name = name
        self.workspace = workspace
        self.instructions = instructions
        self.logger = self._setup_logging()
        
        # Phase 1: Use centralized permission system
        self.permission_system = permission_system
        
        # Keep local permissions for defense-in-depth (will be registered with centralized system)
        self.permissions = {
            "read_dirs": [],
            "write_dirs": [],
            "allowed_commands": [],
            "forbidden_operations": []
        }
        
        # Keep safety rules for validation (separate from authorization)
        self.rules = []
        self.activity_log = []
        
        # Register agent permissions with centralized system if available
        if self.permission_system:
            self._register_with_centralized_system()
    
    def _register_with_centralized_system(self):
        """Register this agent's permissions with the centralized permission system."""
        try:
            self.permission_system.set_agent_permissions(self.name, self.permissions)
            self.logger.info(f"Registered {self.name} with centralized permission system")
        except Exception as e:
            self.logger.warning(f"Failed to register with centralized permission system: {e}")
        
    def _setup_logging(self):
        """Setup agent-specific logging"""
        log_dir = self.workspace / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger(self.name)
    
    def add_permission(self, permission_type: str, paths: List[str]):
        """Add permissions for this agent"""
        if permission_type in self.permissions:
            self.permissions[permission_type].extend(paths)
    
    def add_rule(self, rule: str):
        """Add a safety rule for this agent"""
        self.rules.append(rule)
    
    def check_permission(self, operation: str, path: str) -> bool:
        """Check if agent has permission for operation"""
        # Basic permission checking
        if operation in ["read", "list"]:
            return any(Path(path).is_relative_to(allowed) for allowed in self.permissions["read_dirs"])
        elif operation in ["write", "move", "delete"]:
            return any(Path(path).is_relative_to(allowed) for allowed in self.permissions["write_dirs"])
        return False
    
    def check_rules(self, operation: str, details: Dict) -> bool:
        """Check if operation violates any rules"""
        for rule in self.rules:
            if "never delete" in rule.lower() and operation == "delete":
                self.logger.warning(f"Rule violation: {rule}")
                return False
            if "never overwrite" in rule.lower() and operation == "write" and Path(details.get("path", "")).exists():
                self.logger.warning(f"Rule violation: {rule}")
                return False
        return True
    
    def log_activity(self, activity: str, details: Dict = None):
        """Log agent activity"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "activity": activity,
            "details": details or {}
        }
        self.activity_log.append(entry)
        self.logger.info(f"{activity}: {details}")
        
        # Keep log manageable
        if len(self.activity_log) > 1000:
            self.activity_log = self.activity_log[-500:]
    
    def safe_read_file(self, path: str) -> Optional[str]:
        """Safely read a file with permission checking"""
        if not self.check_permission("read", path):
            self.logger.error(f"Permission denied to read {path}")
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading {path}: {e}")
            return None
    
    def safe_write_file(self, path: str, content: str) -> bool:
        """Safely write a file with permission and rule checking"""
        if not self.check_permission("write", path):
            self.logger.error(f"Permission denied to write {path}")
            return False
        
        if not self.check_rules("write", {"path": path}):
            return False
        
        try:
            path_obj = Path(path)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log_activity("write_file", {"path": path, "size": len(content)})
            return True
        except Exception as e:
            self.logger.error(f"Error writing {path}: {e}")
            return False
    
    def safe_move_file(self, source: str, destination: str) -> bool:
        """Safely move a file with permission and rule checking"""
        if not self.check_permission("write", destination):
            self.logger.error(f"Permission denied to move to {destination}")
            return False
        
        if not self.check_rules("move", {"source": source, "destination": destination}):
            return False
        
        try:
            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(source, destination)
            self.log_activity("move_file", {"source": source, "destination": destination})
            return True
        except Exception as e:
            self.logger.error(f"Error moving {source} to {destination}: {e}")
            return False
    
    def safe_run_command(self, command: List[str]) -> Optional[str]:
        """Safely run a command with permission checking"""
        cmd_str = " ".join(command)
        
        # Check if command is allowed
        command_allowed = any(cmd_str.startswith(allowed) for allowed in self.permissions["allowed_commands"])
        if not command_allowed:
            self.logger.error(f"Permission denied to run command: {cmd_str}")
            return None
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.log_activity("run_command", {"command": cmd_str, "success": True})
                return result.stdout
            else:
                self.logger.error(f"Command failed: {cmd_str}. Error: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out: {cmd_str}")
            return None
        except Exception as e:
            self.logger.error(f"Error running command {cmd_str}: {e}")
            return None
    
    def list_files(self, directory: str, pattern: str = "*") -> List[str]:
        """List files in directory with permission checking"""
        if not self.check_permission("read", directory):
            self.logger.error(f"Permission denied to list {directory}")
            return []
        
        try:
            path = Path(directory)
            if not path.exists():
                return []
            
            return [str(f) for f in path.glob(pattern) if f.is_file()]
        except Exception as e:
            self.logger.error(f"Error listing {directory}: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "name": self.name,
            "workspace": str(self.workspace),
            "permissions": self.permissions,
            "rules_count": len(self.rules),
            "recent_activities": self.activity_log[-10:] if self.activity_log else [],
            "status": "active"
        }
    
    def execute_task(self, task: str) -> str:
        """Execute a task - to be overridden by specific agents
        
        Phase 1: Enhanced with permission validation and verification
        """
        self.logger.info(f"Executing task: {task}")
        
        # Phase 1: Check with centralized permission system if available
        if self.permission_system:
            try:
                from core_data_contracts import PermissionLevel
                permission_decision = self.permission_system.validate_operation(
                    operation="execute_task",
                    agent_id=self.name,
                    context={"task": task}
                )
                
                if not permission_decision.allowed:
                    self.logger.error(f"Permission denied for task: {task}. Reason: {permission_decision.reason}")
                    return f"Permission denied: {permission_decision.reason}"
                
                # Check if approval is required
                if permission_decision.requires_approval:
                    self.logger.warning(f"Approval required for task: {task}")
                    # For now, we'll deny approval-required tasks until approval UI is implemented
                    return f"Approval required for task: {task}. Use approval workflow to proceed."
                    
            except Exception as e:
                self.logger.warning(f"Permission check failed, proceeding with caution: {e}")
        
        # Execute the task (to be overridden by specific agents)
        result = self._execute_task_implementation(task)
        
        # Phase 1: Verify the operation
        verification_result = self.verify_operation("execute_task", task, result)
        
        if not verification_result:
            self.logger.warning(f"Verification failed for task: {task}")
            return f"Task executed but verification failed: {result}"
        
        return result
    
    def _execute_task_implementation(self, task: str) -> str:
        """Implementation of task execution - to be overridden by specific agents"""
        return f"Task executed: {task}"
    
    def verify_operation(self, operation: str, context: str, result: str) -> bool:
        """Verify that an operation completed successfully
        
        Phase 1: Basic verification - can be enhanced by specific agents
        
        Args:
            operation: The operation that was performed
            context: Context about the operation
            result: The result of the operation
            
        Returns:
            True if verification passed, False otherwise
        """
        # Basic verification - check if result is not None/empty
        if result is None:
            self.logger.warning(f"Verification failed: empty result for {operation}")
            return False
        
        if isinstance(result, str) and not result.strip():
            self.logger.warning(f"Verification failed: empty result for {operation}")
            return False
        
        # Check for error indicators in result
        if isinstance(result, str):
            error_indicators = ["error", "failed", "denied", "exception"]
            if any(indicator in result.lower() for indicator in error_indicators):
                self.logger.warning(f"Verification failed: error indicators in result for {operation}")
                return False
        
        # Specific verifications for different operations
        if operation == "write_file":
            return self._verify_file_operation(context, "write")
        elif operation == "move_file":
            return self._verify_file_operation(context, "move")
        elif operation == "delete_file":
            return self._verify_file_operation(context, "delete")
        
        # Default verification passes if no explicit error indicators
        return True
    
    def _verify_file_operation(self, context: str, operation: str) -> bool:
        """Verify file operations"""
        try:
            # Parse path from context
            if operation == "delete":
                # For delete, verify file no longer exists
                if Path(context).exists():
                    return False
            else:
                # For write/move, verify file exists
                if not Path(context).exists():
                    return False
            return True
        except Exception as e:
            self.logger.warning(f"File verification failed: {e}")
            return False