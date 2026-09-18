"""
Base Agent Framework
Provides the foundation for specialized background agents
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
    """Base class for all specialized agents"""
    
    def __init__(self, name: str, workspace: Path, instructions: str = ""):
        self.name = name
        self.workspace = workspace
        self.instructions = instructions
        self.logger = self._setup_logging()
        self.permissions = {
            "read_dirs": [],
            "write_dirs": [],
            "allowed_commands": [],
            "forbidden_operations": []
        }
        self.rules = []
        self.activity_log = []
        
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
        """Execute a task - to be overridden by specific agents"""
        self.logger.info(f"Executing task: {task}")
        return f"Task executed: {task}"