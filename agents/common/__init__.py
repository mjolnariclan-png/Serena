"""
Common utilities for agents
"""
from pathlib import Path

# Ensure base_agent is accessible
import sys
agents_dir = Path(__file__).parent.parent
sys.path.insert(0, str(agents_dir))