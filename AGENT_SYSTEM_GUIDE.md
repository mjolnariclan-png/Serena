# Agent System Integration Guide

## Overview

The Serena & Astrid application now includes a specialized background agent system that works alongside your interactive AI companions. This allows you to have dedicated agents for specific tasks while keeping Serena and Astrid for conversation and interaction.

## Architecture

```
Desktop AI System
├── Interactive Layer (Serena & Astrid)
│   ├── GUI Application (main.py)
│   ├── Character Management (characters.py)
│   └── AI Processing (ai.py, router.py)
│
└── Agent Hub (Background System)
    ├── Agent Manager (agents/agent_manager.py)
    ├── Media Agent (agents/media/agent.py)
    ├── Server Agent (agents/server/agent.py)
    ├── Base Agent Framework (agents/base_agent.py)
    └── Common Tools (agents/common/)
```

## Current Agents

### 🎬 Media Agent
- **Purpose**: Organize media files and manage Jellyfin library
- **Capabilities**:
  - Scan incoming directories for new media
  - Identify file types (movies vs TV shows)
  - Rename files to standard format
  - Sort into correct library folders
  - Trigger Jellyfin refresh
  - Safe file operations with logging

### 🔧 Server Agent  
- **Purpose**: Monitor system health and perform maintenance
- **Capabilities**:
  - Check disk space across filesystems
  - Monitor critical services (Jellyfin, Samba, Tailscale)
  - Detect failed systemd services
  - Check for system updates
  - Generate maintenance reports
  - Safe command execution with permissions

## How to Use

### Through Chat Interface

You can interact with agents through Serena or Astrid using natural language commands:

**Agent Status:**
```
"agent status"
"agent dashboard" 
"show agents"
```

**Media Agent:**
```
"media agent scan"
"media agent refresh jellyfin"
"check for new media"
```

**Server Agent:**
```
"server agent report"
"server agent check services"
"check system health"
```

### Through Hotkeys

- **Ctrl+Shift+A**: Show agent system status

### Programmatic Access

```python
from agents import get_agent_manager

manager = get_agent_manager()

# Execute agent tasks
result = manager.execute_agent_task("MediaAgent", "scan incoming")
result = manager.execute_agent_task("ServerAgent", "check services")

# Get status
status = manager.get_all_agent_status()
dashboard = manager.generate_dashboard_report()
```

## Agent Features

### Safety & Permissions

Each agent has:
- **Restricted permissions**: Only access to specific directories
- **Safety rules**: Never delete, never overwrite, verify operations
- **Activity logging**: Every operation is logged
- **Error handling**: Graceful failure without system crashes

### Rule-Based Behavior

Agents follow explicit rules like:
- "Never permanently delete a file"
- "Never overwrite an existing file" 
- "If uncertain, move to Unsorted and report"
- "Verify every file operation"
- "Keep a log of every operation"

## Creating New Agents

### Step 1: Create Agent Directory

```bash
mkdir -p agents/newagent
```

### Step 2: Create Agent File

```python
# agents/newagent/agent.py
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent

class NewAgent(BaseAgent):
    def __init__(self, workspace: Path):
        instructions = """
        Your agent's purpose and instructions here
        """
        super().__init__("NewAgent", workspace, instructions)
        
        # Set permissions
        self.add_permission("read_dirs", ["/path/to/allowed/dirs"])
        self.add_permission("write_dirs", ["/path/to/write/dirs"])
        self.add_permission("allowed_commands", ["safe-command"])
        
        # Add safety rules
        self.add_rule("Never delete files")
        self.add_rule("Always verify operations")
    
    def execute_task(self, task: str) -> str:
        # Implement your agent's specific tasks
        return f"Task completed: {task}"
```

### Step 3: Register Agent

```python
# In agents/__init__.py
try:
    from newagent.agent import NewAgent
    new_agent = NewAgent(workspace / "newagent")
    manager.register_agent(new_agent)
except ImportError:
    pass
```

### Step 4: Add Router Commands

```python
# In router.py
elif "newagent" in prompt_lower:
    manager = get_agent_manager()
    result = manager.execute_agent_task("NewAgent", task)
    return f"New Agent: {result}"
```

## Agent Scheduling

The Agent Manager includes a scheduler for periodic tasks:

```python
# Start the scheduler
manager.start_scheduler()

# The scheduler runs tasks like:
# - Server maintenance checks every hour
# - Media scans every 30 minutes
# - Custom intervals based on your needs
```

## System Integration

### systemd Services

You can create systemd services for background agent execution:

```ini
# /etc/systemd/system/serena-agents.service
[Unit]
Description=Serena Agent System
After=network.target

[Service]
Type=simple
User=eirik17
WorkingDirectory=/home/eirik17/Desktop/Serena
ExecStart=/usr/bin/python3 /home/eirik17/Desktop/Serena/agents/agent_daemon.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Cron Jobs

Alternative scheduling with cron:

```bash
# Media scan every 30 minutes
*/30 * * * * cd /home/eirik17/Desktop/Serena && python -c "from agents import get_agent_manager; manager = get_agent_manager(); manager.execute_agent_task('MediaAgent', 'scan incoming')"

# Server check every hour
0 * * * * cd /home/eirik17/Desktop/Serena && python -c "from agents import get_agent_manager; manager = get_agent_manager(); manager.execute_agent_task('ServerAgent', 'check services')"
```

## Future Agents You Could Build

### 📸 Photo Organizer Agent
- Watch incoming photo directories
- Group by date/event
- Detect duplicates
- Organize into album structure
- Handle uncertain cases with Unsorted folder

### 👨‍💻 Development Agent
- Monitor project directories
- Run tests automatically
- Create git commits
- Generate code summaries
- Assist with refactoring

### 💾 Backup Agent
- Monitor critical directories
- Perform scheduled backups
- Verify backup integrity
- Report backup status
- Handle backup failures

### 📚 Librarian Agent
- Organize documents and ebooks
- Extract metadata
- Create library structure
- Index content for search
- Maintain reading lists

## Advantages of This Architecture

1. **Separation of Concerns**: Interactive AI vs. Background automation
2. **Safety**: Permission-based access prevents accidental damage
3. **Reliability**: Each agent operates independently
4. **Scalability**: Easy to add new specialized agents
5. **Transparency**: Full logging and activity tracking
6. **Flexibility**: Use different AI backends per agent
7. **Maintenance**: Individual agents can be updated without affecting others

## Integration with Serena & Astrid

The agent system enhances rather than replaces your AI companions:

- **Serena & Astrid**: Handle conversation, creativity, complex reasoning
- **Agents**: Handle repetitive, maintenance, and organizational tasks
- **Coordination**: You can ask Serena/Astrid to trigger agent tasks
- **Reporting**: Agents report back through the chat interface

This gives you the best of both worlds - intelligent conversation plus reliable automation.