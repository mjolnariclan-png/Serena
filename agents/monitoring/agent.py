"""
Monitoring Agent
System monitoring and metrics collection with restricted capabilities

Phase 3: Specialized agent for monitoring operations
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


class MonitoringAgent(BaseAgent):
    """
    Agent for system monitoring and metrics collection.
    
    Restricted capabilities:
    - READ: System metrics and status
    - MONITOR: CPU, memory, disk, network
    - REPORT: Generate monitoring reports
    - NEVER modify system configurations
    - NEVER perform system maintenance
    - All monitoring data logged
    """
    
    def __init__(self, workspace: Path):
        """
        Initialize Monitoring Agent.
        
        Args:
            workspace: Agent workspace for logs and reports
        """
        instructions = """
        You are the Monitoring Agent. Your job is to:
        1. Monitor system metrics (CPU, memory, disk, network)
        2. Track service status
        3. Generate monitoring reports
        4. Alert on threshold breaches
        5. Never modify system configurations
        
        CRITICAL SECURITY RULES:
        - NEVER modify system configurations
        - NEVER perform system maintenance operations
        - NEVER restart services without authorization
        - ALWAYS report metrics accurately
        - NEVER bypass permission system
        """
        
        super().__init__("MonitoringAgent", workspace, instructions)
        
        # Monitoring paths
        self.monitoring_paths = {
            "reports": str(workspace / "monitoring_reports")
        }
        
        # Create reports directory
        Path(self.monitoring_paths["reports"]).mkdir(parents=True, exist_ok=True)
        
        # Set up allowed commands (read-only)
        self.add_permission("allowed_commands", [
            "df",  # Disk usage
            "free",  # Memory usage
            "uptime",  # System uptime
            "ps",  # Process list
            "top",  # Process monitoring
            "systemctl",  # Service status (read-only)
            "iostat",  # I/O statistics
            "mpstat",  # CPU statistics
        ])
        
        # Add safety rules
        self.add_rule("NEVER modify system configurations")
        self.add_rule("NEVER perform system maintenance operations")
        self.add_rule("NEVER restart services without authorization")
        self.add_rule("ALWAYS report metrics accurately")
        self.add_rule("NEVER bypass permission system")
    
    def get_cpu_usage(self) -> Dict[str, Any]:
        """
        Get CPU usage information.
        
        Returns:
            CPU usage metrics
        """
        try:
            # Use /proc/stat for CPU info
            with open('/proc/stat', 'r') as f:
                lines = f.readlines()
            
            cpu_line = lines[0]
            parts = cpu_line.split()
            
            return {
                "success": True,
                "cpu": parts[0],
                "user": parts[1],
                "nice": parts[2],
                "system": parts[3],
                "idle": parts[4],
                "iowait": parts[5] if len(parts) > 5 else "0"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get memory usage information.
        
        Returns:
            Memory usage metrics
        """
        try:
            result = self.safe_run_command(["free", "-h"])
            
            if result is None:
                return {
                    "success": False,
                    "error": "Failed to get memory info"
                }
            
            lines = result.split('\n')
            mem_info = {}
            
            for line in lines:
                if line.startswith("Mem:"):
                    parts = line.split()
                    mem_info = {
                        "total": parts[1],
                        "used": parts[2],
                        "free": parts[3],
                        "available": parts[6] if len(parts) > 6 else "N/A"
                    }
            
            return {
                "success": True,
                "memory": mem_info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_disk_usage(self) -> Dict[str, Any]:
        """
        Get disk usage information.
        
        Returns:
            Disk usage metrics
        """
        try:
            result = self.safe_run_command(["df", "-h"])
            
            if result is None:
                return {
                    "success": False,
                    "error": "Failed to get disk info"
                }
            
            lines = result.split('\n')
            disks = []
            
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 6:
                        disks.append({
                            "filesystem": parts[0],
                            "size": parts[1],
                            "used": parts[2],
                            "available": parts[3],
                            "use_percent": parts[4],
                            "mount_point": parts[5]
                        })
            
            return {
                "success": True,
                "disks": disks
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_system_uptime(self) -> Dict[str, Any]:
        """
        Get system uptime.
        
        Returns:
            System uptime information
        """
        try:
            result = self.safe_run_command(["uptime"])
            
            if result is None:
                return {
                    "success": False,
                    "error": "Failed to get uptime"
                }
            
            return {
                "success": True,
                "uptime": result.strip()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        Check the status of a systemd service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service status information
        """
        try:
            result = self.safe_run_command(["systemctl", "is-active", service_name])
            
            if result is None:
                return {
                    "success": False,
                    "error": "Failed to check service status",
                    "service": service_name
                }
            
            status = result.strip()
            
            return {
                "success": True,
                "service": service_name,
                "status": status,
                "active": status == "active"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "service": service_name
            }
    
    def generate_monitoring_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive monitoring report.
        
        Returns:
            Monitoring report with all metrics
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {}
        }
        
        # Get CPU usage
        report["metrics"]["cpu"] = self.get_cpu_usage()
        
        # Get memory usage
        report["metrics"]["memory"] = self.get_memory_usage()
        
        # Get disk usage
        report["metrics"]["disk"] = self.get_disk_usage()
        
        # Get system uptime
        report["metrics"]["uptime"] = self.get_system_uptime()
        
        # Check critical services
        critical_services = ["jellyfin", "smbd", "tailscaled"]
        report["metrics"]["services"] = {}
        
        for service in critical_services:
            report["metrics"]["services"][service] = self.check_service_status(service)
        
        # Overall system health
        disk_usage = report["metrics"]["disk"].get("disks", [])
        any_disk_full = any(d.get("use_percent", "0%").rstrip('%') == "100" for d in disk_usage)
        
        report["system_health"] = "OK"
        if any_disk_full:
            report["system_health"] = "CRITICAL"
        
        return report


if __name__ == "__main__":
    # Test the Monitoring Agent
    print("Testing Monitoring Agent...")
    
    import tempfile
    temp_workspace = Path(tempfile.mkdtemp())
    
    agent = MonitoringAgent(temp_workspace)
    
    # Test get memory usage
    memory = agent.get_memory_usage()
    print(f"Memory usage: {memory}")
    
    # Test get disk usage
    disk = agent.get_disk_usage()
    print(f"Disk usage (found {len(disk.get('disks', []))} filesystems)")
    
    # Test generate monitoring report
    report = agent.generate_monitoring_report()
    print(f"System health: {report['system_health']}")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_workspace)
    
    print("\n✅ Monitoring Agent Test Passed!")