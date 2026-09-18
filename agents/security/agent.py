"""
Security Agent
Security monitoring and alerting with restricted capabilities

Phase 3: Specialized agent for security operations
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent


class SecurityAgent(BaseAgent):
    """
    Agent for security monitoring and alerting.
    
    Restricted capabilities:
    - READ: System logs, configuration files
    - MONITOR: Security-related metrics
    - ALERT: Generate security alerts
    - NEVER modify security configurations without explicit approval
    - NEVER change firewall rules without authorization
    - All security events logged
    """
    
    def __init__(self, workspace: Path):
        """
        Initialize Security Agent.
        
        Args:
            workspace: Agent workspace for logs and reports
        """
        instructions = """
        You are the Security Agent. Your job is to:
        1. Monitor system security events
        2. Check log files for suspicious activity
        3. Alert on security issues
        4. Report security status
        5. Never modify security configurations without approval
        
        CRITICAL SECURITY RULES:
        - NEVER modify security configurations without explicit approval
        - NEVER change firewall rules without authorization
        - NEVER disable security features
        - ALWAYS report security events
        - NEVER bypass permission system
        """
        
        super().__init__("SecurityAgent", workspace, instructions)
        
        # Security monitoring paths
        self.security_paths = {
            "logs": "/var/log",
            "reports": str(workspace / "security_reports")
        }
        
        # Create reports directory
        Path(self.security_paths["reports"]).mkdir(parents=True, exist_ok=True)
        
        # Set up READ permissions for logs
        self.add_permission("read_dirs", [self.security_paths["logs"]])
        
        # Set up allowed commands (read-only)
        self.add_permission("allowed_commands", [
            "journalctl",  # System logs
            "last",  # Login history
            "who",  # Current users
            "ps",  # Process list
            "netstat",  # Network connections
            "ss",  # Socket statistics
            "ls",  # Listing files
            "cat",  # Reading files
        ])
        
        # Add safety rules
        self.add_rule("NEVER modify security configurations without approval")
        self.add_rule("NEVER change firewall rules without authorization")
        self.add_rule("NEVER disable security features")
        self.add_rule("ALWAYS report security events")
        self.add_rule("NEVER bypass permission system")
    
    def check_failed_logins(self, since_hours: int = 24) -> Dict[str, Any]:
        """
        Check for failed login attempts.
        
        Args:
            since_hours: Check for failures in the last N hours
            
        Returns:
            Failed login information
        """
        try:
            # Use journalctl to check for failed logins
            result = self.safe_run_command([
                "journalctl",
                "--since", f"{since_hours} hours ago",
                "SYSLOG_IDENTIFIER=sshd",
                "MESSAGE=Failed"
            ])
            
            if result is None:
                return {
                    "success": False,
                    "error": "Failed to check logs",
                    "since_hours": since_hours
                }
            
            # Count failures
            failures = result.count('\n') if result else 0
            
            return {
                "success": True,
                "since_hours": since_hours,
                "failed_attempts": failures,
                "recent_failures": result.split('\n')[:10] if result else []
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "since_hours": since_hours
            }
    
    def check_active_sessions(self) -> Dict[str, Any]:
        """
        Check for active user sessions.
        
        Returns:
            Active session information
        """
        try:
            result = self.safe_run_command(["who"])
            
            if result is None:
                return {
                    "success": False,
                    "error": "Failed to check sessions"
                }
            
            sessions = []
            for line in result.split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 5:
                        sessions.append({
                            "user": parts[0],
                            "tty": parts[1],
                            "date": parts[2],
                            "time": parts[3],
                            "host": parts[4]
                        })
            
            return {
                "success": True,
                "active_sessions": len(sessions),
                "sessions": sessions
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_open_ports(self) -> Dict[str, Any]:
        """
        Check for open network ports.
        
        Returns:
            Open port information
        """
        try:
            # Use ss to check listening ports
            result = self.safe_run_command(["ss", "-tln"])
            
            if result is None:
                return {
                    "success": False,
                    "error": "Failed to check ports"
                }
            
            ports = []
            for line in result.split('\n'):
                if line.strip() and not line.startswith("State"):
                    parts = line.split()
                    if len(parts) >= 5:
                        ports.append({
                            "protocol": parts[0],
                            "state": parts[1],
                            "address": parts[3] if len(parts) > 3 else "N/A",
                            "process": parts[5] if len(parts) > 5 else "N/A"
                        })
            
            return {
                "success": True,
                "open_ports": len(ports),
                "ports": ports
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_security_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive security report.
        
        Returns:
            Security report with all checks
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # Check failed logins
        report["checks"]["failed_logins"] = self.check_failed_logins()
        
        # Check active sessions
        report["checks"]["active_sessions"] = self.check_active_sessions()
        
        # Check open ports
        report["checks"]["open_ports"] = self.check_open_ports()
        
        # Overall security status
        failed_logins = report["checks"]["failed_logins"].get("failed_attempts", 0)
        active_sessions = report["checks"]["active_sessions"].get("active_sessions", 0)
        
        report["security_status"] = "OK"
        if failed_logins > 10:
            report["security_status"] = "WARNING"
        if failed_logins > 50:
            report["security_status"] = "CRITICAL"
        
        return report


if __name__ == "__main__":
    # Test the Security Agent
    print("Testing Security Agent...")
    
    import tempfile
    temp_workspace = Path(tempfile.mkdtemp())
    
    agent = SecurityAgent(temp_workspace)
    
    # Test check active sessions
    sessions = agent.check_active_sessions()
    print(f"Active sessions: {sessions}")
    
    # Test generate security report
    report = agent.generate_security_report()
    print(f"Security report status: {report['security_status']}")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_workspace)
    
    print("\n✅ Security Agent Test Passed!")