"""
Agent Manager
Coordinates and manages multiple specialized agents
"""

import os
import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class AgentManager:
    """Manages multiple specialized agents"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.agents = {}
        self.agent_status = {}
        self.running = False
        self.scheduler_thread = None
        
        # Create workspace structure
        self.workspace.mkdir(parents=True, exist_ok=True)
        
    def register_agent(self, agent):
        """Register an agent with the manager"""
        self.agents[agent.name] = agent
        self.agent_status[agent.name] = {
            "status": "idle",
            "last_activity": None,
            "tasks_completed": 0,
            "errors": 0
        }
        print(f"Registered agent: {agent.name}")
    
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