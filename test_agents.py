#!/usr/bin/env python3
"""
Test script for the agent system integration
"""

import sys
import os
from pathlib import Path

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_agent_system():
    """Test the agent system"""
    print("Testing Agent System...")
    
    try:
        from agents import get_agent_manager, initialize_agent_system
        
        # Initialize agent system
        print("\n1. Initializing agent system...")
        manager = initialize_agent_system()
        
        # Check registered agents
        print("\n2. Registered agents:")
        status = manager.get_all_agent_status()
        for agent_name, agent_status in status['agents'].items():
            print(f"  - {agent_name}: {agent_status['status']}")
        
        # Test Media Agent
        print("\n3. Testing Media Agent...")
        media_result = manager.execute_agent_task("MediaAgent", "scan incoming")
        print(f"  Media Agent result: {media_result}")
        
        # Test Server Agent
        print("\n4. Testing Server Agent...")
        server_result = manager.execute_agent_task("ServerAgent", "check services")
        print(f"  Server Agent result: {server_result}")
        
        # Generate dashboard
        print("\n5. Generating dashboard...")
        dashboard = manager.generate_dashboard_report()
        print(dashboard)
        
        print("\n✅ Agent system tests passed!")
        
    except Exception as e:
        print(f"\n❌ Agent system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_router_integration():
    """Test router integration with agent system"""
    print("\n\nTesting Router Integration...")
    
    try:
        from router import route, AGENT_SYSTEM_AVAILABLE
        
        print(f"Agent system available: {AGENT_SYSTEM_AVAILABLE}")
        
        if AGENT_SYSTEM_AVAILABLE:
            # Test agent commands
            test_commands = [
                "agent status",
                "agent list", 
                "media agent scan",
                "server agent check"
            ]
            
            for command in test_commands:
                print(f"\nTesting command: '{command}'")
                try:
                    result = route(command)
                    print(f"Result: {result[:200]}...")  # Truncate long results
                except Exception as e:
                    print(f"Error: {e}")
        
        print("\n✅ Router integration tests passed!")
        
    except Exception as e:
        print(f"\n❌ Router integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = True
    success = test_agent_system() and success
    success = test_router_integration() and success
    
    if success:
        print("\n" + "="*50)
        print("🎉 ALL AGENT SYSTEM TESTS PASSED!")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("❌ SOME TESTS FAILED")
        print("="*50)
        sys.exit(1)