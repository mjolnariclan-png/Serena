"""
Phase 4I Simplified Validation Tests
Tests what can be validated without GUI: agent registration, scheduler, event system availability
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_agent_registration():
    """Verify all agents are auto-registered."""
    print("\n=== Test 1: Agent Registration ===")
    
    try:
        from agents import get_agent_manager
        
        agent_manager = get_agent_manager()
        agents = list(agent_manager.agents.keys())
        
        print(f"Registered agents: {agents}")
        
        # Verify expected agents are registered
        expected_agents = ['MediaAgent', 'ServerAgent', 'PhotoAgent', 'DevelopmentAgent', 'BackupAgent', 'SecurityAgent', 'MonitoringAgent']
        for agent in expected_agents:
            if agent in agents:
                print(f"✅ {agent} registered")
            else:
                print(f"❌ {agent} NOT registered")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scheduler_availability():
    """Verify scheduler is available in Agent Manager."""
    print("\n=== Test 2: Scheduler Availability ===")
    
    try:
        from agents import get_agent_manager
        
        agent_manager = get_agent_manager()
        
        # Verify scheduler methods exist
        assert hasattr(agent_manager, 'schedules')
        assert hasattr(agent_manager, 'schedule_task')
        assert hasattr(agent_manager, 'cancel_schedule')
        
        print("✅ Scheduler methods available")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_event_system_availability():
    """Verify event system is available."""
    print("\n=== Test 3: Event System Availability ===")
    
    try:
        from agents.event_system import EventBus
        
        # Verify event system is accessible
        event_bus = EventBus()
        assert event_bus is not None
        print("✅ Event system available")
        
        # Test event subscription
        event_received = []
        def handler(event):
            event_received.append(event)
        
        event_bus.subscribe("test_event", handler)
        print("✅ Event handler subscribed")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_autonomous_layer_availability():
    """Verify autonomous layer is available."""
    print("\n=== Test 4: Autonomous Layer Availability ===")
    
    try:
        from agents import get_agent_manager
        from agents.autonomous_layer import AutonomousLayer
        
        agent_manager = get_agent_manager()
        autonomous = AutonomousLayer(agent_manager)
        
        print("✅ Autonomous layer created")
        
        # Test goal addition
        autonomous.add_goal("test goal", priority=5)
        print("✅ Goal added")
        
        # Verify autonomous layer respects Agent Manager
        assert autonomous.agent_manager == agent_manager
        print("✅ Autonomous layer uses Agent Manager")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_permission_system_availability():
    """Verify permission system is available."""
    print("\n=== Test 5: Permission System Availability ===")
    
    try:
        from permission_system import get_centralized_permission_system
        
        perm_system = get_centralized_permission_system()
        assert perm_system is not None
        print("✅ Permission system available")
        
        # Verify permission methods exist
        assert hasattr(perm_system, 'agent_permissions')
        print("✅ Permission methods available")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_simplified_tests():
    """Run simplified Phase 4I validation tests."""
    print("=" * 60)
    print("PHASE 4I SIMPLIFIED VALIDATION TESTS")
    print("=" * 60)
    
    tests = [
        ("Agent Registration", test_agent_registration),
        ("Scheduler Availability", test_scheduler_availability),
        ("Event System Availability", test_event_system_availability),
        ("Autonomous Layer Availability", test_autonomous_layer_availability),
        ("Permission System Availability", test_permission_system_availability),
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
        print("\n🎉 ALL PHASE 4I SIMPLIFIED TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED - REVIEW REQUIRED")
        return False

if __name__ == "__main__":
    success = run_simplified_tests()
    sys.exit(0 if success else 1)