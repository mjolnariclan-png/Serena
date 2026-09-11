"""
Hermes Agent Integration for Serena
This module provides a wrapper around Hermes Agent to give Serena agentic capabilities
while preserving all her existing features.
"""

import sys
import os
from pathlib import Path

# Add Hermes Agent to Python path
HERMES_PATH = Path(r"C:\Users\mille\AppData\Local\hermes\hermes-agent")
HERMES_VENV = Path(r"C:\Users\mille\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages")

if HERMES_PATH.exists():
    sys.path.insert(0, str(HERMES_PATH))
    print(f"Added Hermes path: {HERMES_PATH}")
else:
    print(f"Hermes path not found: {HERMES_PATH}")

if HERMES_VENV.exists():
    sys.path.insert(0, str(HERMES_VENV))
    print(f"Added Hermes venv path: {HERMES_VENV}")
else:
    print(f"Hermes venv path not found: {HERMES_VENV}")

try:
    from run_agent import AIAgent
    HERMES_AVAILABLE = True
except ImportError:
    HERMES_AVAILABLE = False
    print("Hermes Agent not available. Install and configure Hermes for advanced agentic features.")


class HermesAgent:
    """
    Wrapper for Hermes Agent that provides agentic capabilities to Serena.
    This allows Serena to perform complex multi-step tasks, use tools, and have
    persistent memory while maintaining her existing personality and features.
    """
    
    def __init__(self, model="llama3.2:latest", quiet_mode=True):
        if not HERMES_AVAILABLE:
            raise RuntimeError("Hermes Agent is not available or not properly installed")
        
        self.model = model
        self.quiet_mode = quiet_mode
        self.agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the Hermes Agent with local Ollama configuration."""
        try:
            self.agent = AIAgent(
                model=self.model,
                quiet_mode=self.quiet_mode,
                # Disable features that Serena already handles
                skip_context_files=True,  # Serena manages her own context
                skip_memory=False,  # Let Hermes handle persistent memory
            )
            print(f"Hermes Agent initialized with model: {self.model}")
        except Exception as e:
            print(f"Failed to initialize Hermes Agent: {e}")
            raise
    
    def chat(self, message, conversation_history=None):
        """
        Send a message to Hermes Agent and get a response.
        
        Args:
            message: The user's message
            conversation_history: Optional conversation history for context
            
        Returns:
            str: The agent's response
        """
        if not self.agent:
            self._initialize_agent()
        
        try:
            response = self.agent.chat(message)
            return response
        except Exception as e:
            print(f"Hermes Agent chat error: {e}")
            return f"I encountered an issue with my agentic capabilities: {str(e)}"
    
    def run_conversation(self, message, conversation_history=None):
        """
        Run a full conversation with Hermes Agent, returning detailed response.
        
        Args:
            message: The user's message
            conversation_history: Optional conversation history for context
            
        Returns:
            dict: Full response with message history and metadata
        """
        if not self.agent:
            self._initialize_agent()
        
        try:
            response = self.agent.run_conversation(message)
            return response
        except Exception as e:
            print(f"Hermes Agent conversation error: {e}")
            return {
                "response": f"I encountered an issue with my agentic capabilities: {str(e)}",
                "messages": [],
                "metadata": {}
            }
    
    def is_available(self):
        """Check if Hermes Agent is available and functioning."""
        return HERMES_AVAILABLE and self.agent is not None
    
    def get_model_info(self):
        """Get information about the current model being used."""
        if self.agent:
            return {
                "model": self.model,
                "available": True,
                "capabilities": ["tool_calling", "file_operations", "web_browsing", "memory"]
            }
        return {
            "model": self.model,
            "available": False,
            "capabilities": []
        }


# Global Hermes instance (lazy loaded)
_hermes_instance = None

def get_hermes_agent():
    """Get or create the global Hermes Agent instance."""
    global _hermes_instance
    if _hermes_instance is None and HERMES_AVAILABLE:
        try:
            _hermes_instance = HermesAgent()
        except Exception as e:
            print(f"Could not initialize Hermes Agent: {e}")
    return _hermes_instance


def is_hermes_available():
    """Check if Hermes Agent is available for use."""
    return HERMES_AVAILABLE


def hermes_chat(message):
    """
    Convenience function to chat with Hermes Agent.
    Returns None if Hermes is not available.
    """
    agent = get_hermes_agent()
    if agent and agent.is_available():
        return agent.chat(message)
    return None


if __name__ == "__main__":
    # Test the Hermes integration
    print("Testing Hermes Agent integration...")
    
    if is_hermes_available():
        print("Hermes Agent is available!")
        agent = get_hermes_agent()
        
        if agent and agent.is_available():
            print("Agent initialized successfully")
            print(f"Model info: {agent.get_model_info()}")
            
            # Test a simple chat
            test_message = "Hello, can you help me organize my files?"
            print(f"\nTesting chat with: '{test_message}'")
            response = agent.chat(test_message)
            print(f"Response: {response}")
        else:
            print("Agent initialization failed")
    else:
        print("Hermes Agent is not available")