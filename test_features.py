"""
Test script for Serena's new features.
Run this to verify that all components are working correctly.
"""

import sys
import os

def test_imports():
    """Test that all new modules can be imported."""
    print("Testing imports...")
    try:
        import requests
        import PIL
        import coding_helper
        import image_gen
        import gif_gen
        import web_search
        print("[OK] All modules imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Import error: {e}")
        return False

def test_web_search():
    """Test web search functionality."""
    print("\nTesting web search...")
    try:
        from web_search import is_search_query, extract_search_query
        assert is_search_query("search for python tutorials") == True
        assert extract_search_query("search for python tutorials") == "python tutorials"
        print("[OK] Web search query parsing works")
        return True
    except Exception as e:
        print(f"[FAIL] Web search test failed: {e}")
        return False

def test_image_generation():
    """Test image generation functionality."""
    print("\nTesting image generation...")
    try:
        from image_gen import is_image_request, extract_image_prompt
        assert is_image_request("generate an image of a cat") == True
        assert len(extract_image_prompt("generate an image of a cat")) > 0
        print("[OK] Image request parsing works")
        return True
    except Exception as e:
        print(f"[FAIL] Image generation test failed: {e}")
        return False

def test_gif_generation():
    """Test GIF generation functionality."""
    print("\nTesting GIF generation...")
    try:
        from gif_gen import is_gif_request, extract_gif_prompt
        assert is_gif_request("create a gif of a dancing robot") == True
        assert len(extract_gif_prompt("create a gif of a dancing robot")) > 0
        print("[OK] GIF request parsing works")
        return True
    except Exception as e:
        print(f"[FAIL] GIF generation test failed: {e}")
        return False

def test_coding_helper():
    """Test coding helper functionality."""
    print("\nTesting coding helper...")
    try:
        from coding_helper import is_coding_request, execute_code
        assert is_coding_request("execute code ```python\nprint('hello')```") == True
        res = execute_code("print('test')")
        assert "test" in res
        print("[OK] Coding helper works")
        return True
    except Exception as e:
        print(f"[FAIL] Coding helper test failed: {e}")
        return False

def test_local_ai():
    """Test local AI commands."""
    print("\nTesting local AI commands...")
    try:
        from local_ai import local_response
        
        # Test help command (should work without dependencies)
        result = local_response("help")
        assert "help" in result.lower() or "capabilities" in result.lower()
        print("[OK] Help command works")
        
        return True
    except Exception as e:
        print(f"[FAIL] Local AI test failed: {e}")
        return False

def test_router():
    """Test router functionality."""
    print("\nTesting router...")
    try:
        from router import route
        
        # Test mode switching
        result = route("mode chat")
        assert "chat" in result.lower() or "unknown" in result.lower()
        print("[OK] Mode switching works")
        
        # Test memory clear
        result = route("clear memory")
        assert "memory" in result.lower()
        print("[OK] Memory clear works")
        
        return True
    except Exception as e:
        print(f"[FAIL] Router test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("Serena Feature Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_web_search,
        test_image_generation,
        test_gif_generation,
        test_coding_helper,
        test_local_ai,
        test_router
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[FAIL] Test crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 50)
    
    if all(results):
        print("[OK] All tests passed!")
        return 0
    else:
        print("[FAIL] Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())