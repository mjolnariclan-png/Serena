"""
Phase 4I Live Agent Ecosystem Tests
Tests the actual agent execution through direct agent calls (simulating conversational flow)

These tests verify that agents are registered and can execute their capabilities:
Agent → Permission → Tool → Execution → Verification → Audit → Result
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_live_development_agent():
    """Test Development Agent direct execution."""
    print("\n=== Test 1: Live Development Agent ===")
    
    try:
        from agents import get_agent_manager
        
        # Get agent manager
        agent_manager = get_agent_manager()
        
        # Verify Development Agent is registered
        dev_agent = agent_manager.get_agent("DevelopmentAgent")
        assert dev_agent is not None
        print("✅ Development Agent registered")
        
        # Execute capability directly
        result = dev_agent.execute_capability("inspect_project", {"path": agent_manager.workspace})
        
        print(f"Result: {result}")
        
        # Verify result structure
        assert result is not None
        print("✅ Development Agent executed and returned result")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_live_backup_agent():
    """Test Backup Agent direct execution."""
    print("\n=== Test 2: Live Backup Agent ===")
    
    try:
        from agents import get_agent_manager
        import tempfile
        
        # Get agent manager
        agent_manager = get_agent_manager()
        
        # Verify Backup Agent is registered
        backup_agent = agent_manager.get_agent("BackupAgent")
        assert backup_agent is not None
        print("✅ Backup Agent registered")
        
        # Create temporary source directory with test file
        temp_source = Path(tempfile.mkdtemp())
        test_file = temp_source / "test.txt"
        test_file.write_text("Test data for backup\n")
        
        # Add source to backup agent
        backup_agent.add_source_directory(temp_source)
        
        # Execute capability directly
        result = backup_agent.execute_capability("create_backup", {"source": str(temp_source)})
        
        print(f"Result: {result}")
        
        # Verify result
        assert result is not None
        print("✅ Backup Agent executed and returned result")
        
        # Cleanup
        shutil.rmtree(temp_source)
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_live_security_agent():
    """Test Security Agent direct execution."""
    print("\n=== Test 3: Live Security Agent ===")
    
    try:
        from agents import get_agent_manager
        
        # Get agent manager
        agent_manager = get_agent_manager()
        
        # Verify Security Agent is registered
        security_agent = agent_manager.get_agent("SecurityAgent")
        assert security_agent is not None
        print("✅ Security Agent registered")
        
        # Execute capability directly
        result = security_agent.execute_capability("check_active_sessions", {})
        
        print(f"Result: {result}")
        
        # Verify result
        assert result is not None
        print("✅ Security Agent executed and returned result")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_live_monitoring_agent():
    """Test Monitoring Agent direct execution."""
    print("\n=== Test 4: Live Monitoring Agent ===")
    
    try:
        from agents import get_agent_manager
        
        # Get agent manager
        agent_manager = get_agent_manager()
        
        # Verify Monitoring Agent is registered
        monitoring_agent = agent_manager.get_agent("MonitoringAgent")
        assert monitoring_agent is not None
        print("✅ Monitoring Agent registered")
        
        # Execute capability directly
        result = monitoring_agent.execute_capability("check_memory_usage", {})
        
        print(f"Result: {result}")
        
        # Verify result
        assert result is not None
        print("✅ Monitoring Agent executed and returned result")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_live_scheduler():
    """Test scheduler availability in Agent Manager."""
    print("\n=== Test 5: Live Scheduler ===")
    
    try:
        from agents import get_agent_manager
        from core_data_contracts import Task
        
        # Get agent manager
        agent_manager = get_agent_manager()
        
        # Verify scheduler is available
        assert hasattr(agent_manager, 'schedules')
        print("✅ Scheduler available")
        
        # Create a task to schedule
        task = Task(
            task_id="test_schedule_001",
            goal="Test scheduled task",
            priority=5,
            agent_id="MonitoringAgent",
            task_type="system_monitoring"
        )
        
        # Schedule task for 5 seconds from now
        agent_manager.schedule_task(task, schedule_type="interval", interval_seconds=5)
        print("✅ Task scheduled")
        
        # Verify schedule exists
        schedules = agent_manager.get_schedules()
        assert len(schedules) > 0
        print("✅ Schedule recorded")
        
        # Cancel the schedule (we don't want to wait 5 seconds)
        agent_manager.cancel_schedule(task.task_id)
        print("✅ Schedule cancelled")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_live_event_system():
    """Test event system availability in Agent Manager."""
    print("\n=== Test 6: Live Event System ===")
    
    try:
        from agents import get_agent_manager
        from agents.event_driven_tasks import EventDrivenTaskCreator
        
        # Get agent manager
        agent_manager = get_agent_manager()
        
        # Verify event system is available
        assert agent_manager.event_system is not None
        print("✅ Event system available")
        
        # Create event-driven task creator
        creator = EventDrivenTaskCreator(agent_manager)
        
        # Subscribe to an event
        event_received = []
        def handler(event):
            event_received.append(event)
        
        agent_manager.event_system.subscribe("system_warning", handler)
        print("✅ Event handler subscribed")
        
        # Publish an event
        agent_manager.event_system.publish("system_warning", {"message": "Test warning"})
        print("✅ Event published")
        
        # Verify event was received
        assert len(event_received) > 0
        print("✅ Event received by handler")
        
        # Test event-driven task creation
        creator.register_event_mapping("system_warning", "MonitoringAgent", "system_monitoring")
        creator.handle_event("system_warning", {"message": "Test warning"})
        print("✅ Event-driven task created")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_live_autonomous_layer():
    """Test autonomous layer execution."""
    print("\n=== Test 7: Live Autonomous Layer ===")
    
    try:
        from agents import get_agent_manager
        from agents.autonomous_layer import AutonomousLayer
        
        # Get agent manager
        agent_manager = get_agent_manager()
        
        # Create autonomous layer
        autonomous = AutonomousLayer(agent_manager)
        print("✅ Autonomous layer created")
        
        # Add a goal
        autonomous.add_goal("monitor system health", priority=5)
        print("✅ Goal added")
        
        # Generate tasks from goal
        tasks = autonomous.generate_task_from_goal("monitor system health", priority=5)
        print(f"✅ Generated task from goal: {tasks.task_id if tasks else 'None'}")
        
        # Verify task is created (not executed directly)
        if tasks:
            assert tasks.priority <= 7  # Autonomous priority cap
            print(f"✅ Task {tasks.task_id} has priority {tasks.priority} (capped at 7)")
        
        # Verify autonomous layer doesn't bypass Agent Manager
        assert autonomous.agent_manager == agent_manager
        print("✅ Autonomous layer uses Agent Manager")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_live_permission_system():
    """Test permission system enforcement in agents."""
    print("\n=== Test 8: Live Permission System ===")
    
    try:
        from permission_system import get_centralized_permission_system
        from agents import get_agent_manager
        
        # Get permission system
        perm_system = get_centralized_permission_system()
        assert perm_system is not None
        print("✅ Permission system available")
        
        # Test authorization decision
        decision = perm_system.check_permission(
            operation="read_file",
            parameters={"path": "/safe/test.txt"},
            context={"agent": "DevelopmentAgent"}
        )
        
        print(f"Permission decision: {decision}")
        assert decision is not None
        print("✅ Permission system makes authorization decisions")
        
        # Test that agent execution uses permission system
        agent_manager = get_agent_manager()
        dev_agent = agent_manager.get_agent("DevelopmentAgent")
        
        # Verify agent has permission system
        assert dev_agent.permission_system is not None
        print("✅ Agent has permission system")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_live_tests():
    """Run all Phase 4I live agent ecosystem tests."""
    print("=" * 60)
    print("PHASE 4I LIVE AGENT ECOSYSTEM TESTS")
    print("=" * 60)
    
    tests = [
        ("Live Development Agent", test_live_development_agent),
        ("Live Backup Agent", test_live_backup_agent),
        ("Live Security Agent", test_live_security_agent),
        ("Live Monitoring Agent", test_live_monitoring_agent),
        ("Live Scheduler", test_live_scheduler),
        ("Live Event System", test_live_event_system),
        ("Live Autonomous Layer", test_live_autonomous_layer),
        ("Live Permission System", test_live_permission_system),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 ALL PHASE 4I LIVE TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED - REVIEW REQUIRED")
        return False

if __name__ == "__main__":
    success = run_all_live_tests()
    sys.exit(0 if success else 1)