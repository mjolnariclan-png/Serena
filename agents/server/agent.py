"""
Server Maintenance Agent
Monitors system health, checks services, performs maintenance tasks
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta
import subprocess
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent

class ServerAgent(BaseAgent):
    """Agent for server maintenance and monitoring"""
    
    def __init__(self, workspace: Path):
        instructions = """
        You are the Server Maintenance Agent. Your job is to:
        1. Monitor disk space and storage health
        2. Check critical services (Jellyfin, Samba, Tailscale)
        3. Check for failed systemd services
        4. Install system updates when safe
        5. Reboot only when absolutely necessary
        6. Send comprehensive maintenance reports
        7. Alert on critical issues
        
        Be conservative with system changes. Always verify before acting.
        """
        
        super().__init__("ServerAgent", workspace, instructions)
        
        # Server monitoring paths
        self.monitor_paths = [
            "/home/eirik17/Media",
            "/var/lib/jellyfin",
            "/home/eirik17"
        ]
        
        # Critical services
        self.critical_services = [
            "jellyfin",
            "smbd",
            "tailscaled"
        ]
        
        # Set up permissions
        self.add_permission("read_dirs", self.monitor_paths)
        self.add_permission("allowed_commands", [
            "df",
            "systemctl",
            "apt",
            "uname",
            "free",
            "uptime",
            "journalctl"
        ])
        
        # Add safety rules
        self.add_rule("Never reboot without explicit confirmation")
        self.add_rule("Never install updates during active hours")
        self.add_rule("Always check disk space before operations")
        self.add_rule("Never stop critical services without backup plan")
        self.add_rule("Log all maintenance activities")
    
    def check_disk_space(self) -> Dict[str, Dict]:
        """Check disk space on all mounted filesystems"""
        disk_info = {}
        
        try:
            result = self.safe_run_command(["df", "-h"])
            if result:
                lines = result.split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 6:
                            filesystem = parts[0]
                            size = parts[1]
                            used = parts[2]
                            available = parts[3]
                            use_percent = parts[4]
                            mount_point = parts[5]
                            
                            disk_info[mount_point] = {
                                "filesystem": filesystem,
                                "size": size,
                                "used": used,
                                "available": available,
                                "use_percent": use_percent
                            }
                            
                            # Alert if disk is > 80% full
                            if int(use_percent.rstrip('%')) > 80:
                                self.logger.warning(f"Disk {mount_point} is {use_percent} full")
        
        except Exception as e:
            self.logger.error(f"Error checking disk space: {e}")
        
        return disk_info
    
    def check_service_status(self, service_name: str) -> Dict:
        """Check status of a systemd service"""
        try:
            result = self.safe_run_command(["systemctl", "is-active", service_name])
            if result:
                status = result.strip()
                is_running = status == "active"
                
                # Get more detailed status
                detail_result = self.safe_run_command(["systemctl", "status", service_name])
                
                return {
                    "name": service_name,
                    "status": status,
                    "running": is_running,
                    "details": detail_result if detail_result else ""
                }
        except Exception as e:
            self.logger.error(f"Error checking service {service_name}: {e}")
        
        return {"name": service_name, "status": "unknown", "running": False}
    
    def check_all_services(self) -> Dict[str, Dict]:
        """Check status of all critical services"""
        service_status = {}
        
        for service in self.critical_services:
            service_status[service] = self.check_service_status(service)
        
        return service_status
    
    def check_failed_services(self) -> List[str]:
        """Check for any failed systemd services"""
        failed_services = []
        
        try:
            result = self.safe_run_command(["systemctl", "list-units", "--state=failed"])
            if result and "failed" in result.lower():
                lines = result.split('\n')
                for line in lines:
                    if ".service" in line and "loaded" in line:
                        service_name = line.split()[0]
                        failed_services.append(service_name)
                        self.logger.warning(f"Failed service detected: {service_name}")
        
        except Exception as e:
            self.logger.error(f"Error checking failed services: {e}")
        
        return failed_services
    
    def check_system_updates(self) -> Dict:
        """Check for available system updates"""
        try:
            result = self.safe_run_command(["apt", "list", "--upgradable"])
            if result:
                lines = result.split('\n')
                upgradable = [line for line in lines if line.strip() and not line.startswith("Listing")]
                
                return {
                    "updates_available": len(upgradable),
                    "packages": upgradable[:10]  # First 10 packages
                }
        except Exception as e:
            self.logger.error(f"Error checking updates: {e}")
        
        return {"updates_available": 0, "packages": []}
    
    def get_system_info(self) -> Dict:
        """Get general system information"""
        system_info = {}
        
        try:
            # Uptime
            uptime_result = self.safe_run_command(["uptime", "-p"])
            if uptime_result:
                system_info["uptime"] = uptime_result.strip()
            
            # Memory
            mem_result = self.safe_run_command(["free", "-h"])
            if mem_result:
                system_info["memory"] = mem_result.strip()
            
            # CPU info (basic)
            cpu_result = self.safe_run_command(["uname", "-r"])
            if cpu_result:
                system_info["kernel"] = cpu_result.strip()
        
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
        
        return system_info
    
    def generate_maintenance_report(self) -> str:
        """Generate comprehensive maintenance report"""
        report = []
        report.append("=" * 50)
        report.append("SERVER MAINTENANCE REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 50)
        
        # System info
        system_info = self.get_system_info()
        report.append("\nSYSTEM INFORMATION:")
        for key, value in system_info.items():
            report.append(f"  {key}: {value}")
        
        # Disk space
        disk_info = self.check_disk_space()
        report.append("\nDISK SPACE:")
        for mount, info in disk_info.items():
            report.append(f"  {mount}: {info['used']} / {info['size']} ({info['use_percent']})")
        
        # Service status
        service_status = self.check_all_services()
        report.append("\nCRITICAL SERVICES:")
        for service, status in service_status.items():
            status_symbol = "✓" if status["running"] else "✗"
            report.append(f"  {status_symbol} {service}: {status['status']}")
        
        # Failed services
        failed = self.check_failed_services()
        if failed:
            report.append("\nFAILED SERVICES:")
            for service in failed:
                report.append(f"  ✗ {service}")
        else:
            report.append("\nFAILED SERVICES: None")
        
        # Updates
        updates = self.check_system_updates()
        report.append(f"\nSYSTEM UPDATES: {updates['updates_available']} available")
        if updates['packages']:
            report.append("  Sample packages:")
            for pkg in updates['packages'][:5]:
                report.append(f"    {pkg}")
        
        report.append("=" * 50)
        
        full_report = "\n".join(report)
        self.log_activity("maintenance_report", {"report_lines": len(report)})
        
        return full_report
    
    def execute_task(self, task: str) -> str:
        """Execute server maintenance task"""
        self.logger.info(f"Server task: {task}")
        
        if "report" in task.lower():
            return self.generate_maintenance_report()
        
        elif "check" in task.lower():
            if "disk" in task.lower():
                disk_info = self.check_disk_space()
                return f"Disk check completed. Monitored {len(disk_info)} filesystems."
            elif "services" in task.lower():
                service_status = self.check_all_services()
                running = sum(1 for s in service_status.values() if s["running"])
                return f"Service check completed. {running}/{len(service_status)} services running."
            elif "updates" in task.lower():
                updates = self.check_system_updates()
                return f"Update check completed. {updates['updates_available']} updates available."
        
        elif "failed" in task.lower():
            failed = self.check_failed_services()
            if failed:
                return f"Failed services: {', '.join(failed)}"
            else:
                return "No failed services detected."
        
        else:
            return f"Unknown server task: {task}"