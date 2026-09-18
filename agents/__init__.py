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
    
    # Import and register agents
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
    
    return manager

# Global agent manager instance
_agent_manager = None

def get_agent_manager():
    """Get the global agent manager instance"""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = initialize_agent_system()
    return _agent_manager