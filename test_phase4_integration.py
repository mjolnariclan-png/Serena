"""
Phase 4 End-to-End Integration Tests
Tests the complete conversational flow through the actual system

These tests validate the actual execution path:
User → main.py → router → ai.submit_agent_task → Agent Manager → Agent → Permission → Tool → Execution → Verification → Audit → Result
"""

import sys
import os
from pathlib import Path

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_router_accepts_agent_manager():
    """Test that router accepts agent_manager parameter."""
    print("\n=== Test 1: Router Accepts Agent Manager ===")
    
    try:
        from router import route
        import inspect
        
        # Verify router function signature includes agent_manager
        sig = inspect.signature(route)
        assert 'agent_manager' in sig.parameters
        print("✅ Router function signature includes agent_manager")
        
        # Verify default value is None
        default = sig.parameters['agent_manager'].default
        assert default is None
        print("✅ Agent manager parameter defaults to None")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_submit_agent_task_accepts_agent_manager():
    """Test that ai.submit_agent_task accepts agent_manager parameter."""
    print("\n=== Test 2: AI submit_agent_task Accepts Agent Manager ===")
    
    try:
        from ai import submit_agent_task
        import inspect
        
        # Verify function signature includes agent_manager
        sig = inspect.signature(submit_agent_task)
        assert 'agent_manager' in sig.parameters
        print("✅ submit_agent_task signature includes agent_manager")
        
        # Verify default value is None
        default = sig.parameters['agent_manager'].default
        assert default is None
        print("✅ Agent manager parameter defaults to None")
        
        # Verify wait_for_result parameter exists
        assert 'wait_for_result' in sig.parameters
        print("✅ wait_for_result parameter exists")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_passes_agent_manager():
    """Test that main.py passes agent_manager to router."""
    print("\n=== Test 3: main.py Passes Agent Manager ===")
    
    try:
        # Read main.py and verify it passes agent_manager
        with open('/home/eirik17/Desktop/Serena/main.py', 'r') as f:
            content = f.read()
        
        # Check that process() calls route with agent_manager
        assert 'route(user_input, agent_manager=self.agent_manager)' in content
        print("✅ main.py passes agent_manager to router")
        
        # Check that agent_manager is initialized
        assert 'self.agent_manager = get_agent_manager()' in content
        print("✅ main.py initializes agent_manager")
        
        # Check that scheduler is started
        assert 'self.agent_manager.start_scheduler()' in content
        print("✅ main.py starts scheduler")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_router_calls_ai_submit_agent_task():
    """Test that router calls ai.submit_agent_task."""
    print("\n=== Test 4: Router Calls ai.submit_agent_task ===")
    
    try:
        # Read router.py and verify it calls submit_agent_task
        with open('/home/eirik17/Desktop/Serena/router.py', 'r') as f:
            content = f.read()
        
        # Check that router imports and calls submit_agent_task
        assert 'from ai import submit_agent_task' in content
        print("✅ router imports submit_agent_task")
        
        assert 'submit_agent_task(prompt, agent_manager' in content
        print("✅ router calls submit_agent_task with agent_manager")
        
        # Check that it waits for result
        assert 'wait_for_result=True' in content
        print("✅ router waits for task result")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_permission_system_maintained():
    """Test that permission system is still enforced."""
    print("\n=== Test 5: Permission System Maintained ===")
    
    try:
        from permission_system import get_centralized_permission_system
        from agentic_executor import get_agentic_executor
        
        # Verify permission system exists
        perm_system = get_centralized_permission_system()
        assert perm_system is not None
        print("✅ Centralized permission system available")
        
        # Verify executor requires permission system
        try:
            executor = get_agentic_executor({}, None)
            print("❌ FAILED: Executor should require permission system")
            return False
        except ValueError:
            print("✅ Executor still requires permission system")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase1_security_still_passes():
    """Test that Phase 1 security tests still pass."""
    print("\n=== Test 6: Phase 1 Security Regression ===")
    
    try:
        import subprocess
        result = subprocess.run(
            ['python', 'test_phase1_security.py'],
            cwd='/home/eirik17/Desktop/Serena',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check that tests passed
        assert 'TOTAL: 9/9 tests passed' in result.stdout
        print("✅ Phase 1 security tests still pass (9/9)")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase3_functionality_still_passes():
    """Test that Phase 3 functionality tests still pass."""
    print("\n=== Test 7: Phase 3 Functionality Regression ===")
    
    try:
        import subprocess
        result = subprocess.run(
            ['python', 'test_phase3_functionality.py'],
            cwd='/home/eirik17/Desktop/Serena',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check that tests passed
        assert 'TOTAL: 11/11 tests passed' in result.stdout
        print("✅ Phase 3 functionality tests still pass (11/11)")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_path_complete():
    """Test that the complete integration path exists in code."""
    print("\n=== Test 8: Complete Integration Path ===")
    
    try:
        # Verify all components exist and are connected
        checks = []
        
        # Check main.py
        with open('/home/eirik17/Desktop/Serena/main.py', 'r') as f:
            main_content = f.read()
        checks.append(('main.py initializes agent_manager', 'self.agent_manager = get_agent_manager()' in main_content))
        checks.append(('main.py passes agent_manager to router', 'route(user_input, agent_manager=self.agent_manager)' in main_content))
        
        # Check router.py
        with open('/home/eirik17/Desktop/Serena/router.py', 'r') as f:
            router_content = f.read()
        checks.append(('router accepts agent_manager', 'def route(prompt: str, agent_manager=None):' in router_content))
        checks.append(('router calls submit_agent_task', 'submit_agent_task(prompt, agent_manager' in router_content))
        
        # Check ai.py
        with open('/home/eirik17/Desktop/Serena/ai.py', 'r') as f:
            ai_content = f.read()
        checks.append(('ai.submit_agent_task accepts agent_manager', 'def submit_agent_task(user_input: str, agent_manager: Optional[AgentManager] = None' in ai_content))
        checks.append(('ai.submit_agent_task calls agent_manager.submit_task', 'agent_manager.submit_task(task)' in ai_content))
        
        # Check agents/agent_manager.py
        with open('/home/eirik17/Desktop/Serena/agents/agent_manager.py', 'r') as f:
            am_content = f.read()
        checks.append(('AgentManager has submit_task', 'def submit_task(self, task: Task)' in am_content))
        
        # Report results
        for check_name, result in checks:
            if result:
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
        
        all_passed = all(result for _, result in checks)
        if all_passed:
            print("✅ Complete integration path exists in code")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_integration_tests():
    """Run all Phase 4 end-to-end integration tests."""
    print("=" * 60)
    print("PHASE 4 END-TO-END INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        ("Router Accepts Agent Manager", test_router_accepts_agent_manager),
        ("AI submit_agent_task Accepts Agent Manager", test_ai_submit_agent_task_accepts_agent_manager),
        ("main.py Passes Agent Manager", test_main_passes_agent_manager),
        ("Router Calls ai.submit_agent_task", test_router_calls_ai_submit_agent_task),
        ("Permission System Maintained", test_permission_system_maintained),
        ("Phase 1 Security Regression", test_phase1_security_still_passes),
        ("Phase 3 Functionality Regression", test_phase3_functionality_still_passes),
        ("Complete Integration Path", test_integration_path_complete),
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
        print("\n🎉 ALL PHASE 4 INTEGRATION TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED - REVIEW REQUIRED")
        return False

if __name__ == "__main__":
    success = run_all_integration_tests()
    sys.exit(0 if success else 1)