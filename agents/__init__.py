"""
Agent System Package
Integrates specialized background agents with the Serena/Astrid interactive system
"""

from pathlib import Path
import sys

# Add agents directory to path
agents_dir = Path(__file__).parent
sys.path.insert(0, str(agents_dir))

from agent_manager import AgentManager
from base_agent import BaseAgent

# Initialize the agent system
def initialize_agent_system():
    """Initialize the agent system with all agents"""
    workspace = Path(__file__).parent
    
    manager = AgentManager(workspace)
    
    # Import and register original agents
    try:
        from media.agent import MediaAgent
        media_agent = MediaAgent(workspace / "media")
        manager.register_agent(media_agent)
    except ImportError as e:
        print(f"Could not load MediaAgent: {e}")
    
    try:
        from server.agent import ServerAgent
        server_agent = ServerAgent(workspace / "server")
        manager.register_agent(server_agent)
    except ImportError as e:
        print(f"Could not load ServerAgent: {e}")
    
    try:
        from photos.agent import PhotoAgent
        photo_agent = PhotoAgent(workspace / "photos")
        manager.register_agent(photo_agent)
    except ImportError as e:
        print(f"Could not load PhotoAgent: {e}")
    
    # Phase 3: Register specialized agents
    try:
        from development.agent import DevelopmentAgent
        temp_repo = workspace / "temp_repo"
        temp_repo.mkdir(exist_ok=True)
        dev_agent = DevelopmentAgent(workspace, temp_repo)
        manager.register_agent(dev_agent)
    except ImportError as e:
        print(f"Could not load DevelopmentAgent: {e}")
    
    try:
        from backup.agent import BackupAgent
        temp_backup = workspace / "temp_backup"
        temp_backup.mkdir(exist_ok=True)
        backup_agent = BackupAgent(workspace, temp_backup)
        manager.register_agent(backup_agent)
    except ImportError as e:
        print(f"Could not load BackupAgent: {e}")
    
    try:
        from security.agent import SecurityAgent
        security_agent = SecurityAgent(workspace)
        manager.register_agent(security_agent)
    except ImportError as e:
        print(f"Could not load SecurityAgent: {e}")
    
    try:
        from monitoring.agent import MonitoringAgent
        monitoring_agent = MonitoringAgent(workspace)
        manager.register_agent(monitoring_agent)
    except ImportError as e:
        print(f"Could not load MonitoringAgent: {e}")
    
    return manager

# Global agent manager instance
_agent_manager = None

def get_agent_manager():
    """Get the global agent manager instance"""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = initialize_agent_system()
    return _agent_manager