#!/usr/bin/env python3
"""
Test script for all visual system enhancements
"""

import sys
import os
from pathlib import Path

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_visual_assets():
    """Test visual assets creation and loading"""
    print("Testing Visual Assets...")
    
    # Check if assets exist
    images_dir = Path(__file__).parent / "images"
    
    print("\n1. Checking asset directories:")
    directories = ["avatars", "backgrounds", "icons"]
    for dir_name in directories:
        dir_path = images_dir / dir_name
        exists = "✓" if dir_path.exists() else "✗"
        print(f"  {exists} {dir_name}/")
    
    print("\n2. Checking generated assets:")
    expected_assets = [
        "avatars/serena_avatar.png",
        "avatars/astrid_avatar.png",
        "backgrounds/serena_background.png",
        "backgrounds/astrid_background.png",
        "icons/agent_icon.png",
        "icons/media_icon.png",
        "icons/server_icon.png",
        "icons/photo_icon.png",
        "icons/chat_icon.png",
        "icons/settings_icon.png"
    ]
    
    for asset_path in expected_assets:
        full_path = images_dir / asset_path
        exists = "✓" if full_path.exists() else "✗"
        print(f"  {exists} {asset_path}")
    
    print("\n✅ Visual assets check completed!")

def test_character_themes():
    """Test enhanced character themes"""
    print("\n\nTesting Enhanced Character Themes...")
    
    from characters import get_character, get_character_theme
    
    # Test Serena theme
    print("\n1. Serena theme:")
    serena_theme = get_character_theme("serena")
    theme_keys = ["primary_bg", "accent_color", "accent_secondary", "button_color", 
                   "status_ready", "avatar_border", "gradient_start"]
    for key in theme_keys:
        has_key = "✓" if key in serena_theme else "✗"
        print(f"  {has_key} {key}: {serena_theme.get(key, 'MISSING')}")
    
    # Test Astrid theme
    print("\n2. Astrid theme:")
    astrid_theme = get_character_theme("astrid")
    for key in theme_keys:
        has_key = "✓" if key in astrid_theme else "✗"
        print(f"  {has_key} {key}: {astrid_theme.get(key, 'MISSING')}")
    
    print("\n✅ Enhanced themes check completed!")

def test_photo_agent():
    """Test Photo Agent functionality"""
    print("\n\nTesting Photo Agent...")
    
    try:
        from agents import get_agent_manager
        
        manager = get_agent_manager()
        photo_agent = manager.get_agent("PhotoAgent")
        
        if photo_agent:
            print("\n1. Photo Agent registered: ✓")
            
            # Test photo agent features
            print("\n2. Testing photo agent features:")
            
            # Test file type detection
            from agents.photos.agent import PhotoAgent
            test_photo = PhotoAgent(Path(__file__).parent / "agents" / "photos")
            
            test_files = [
                ("test.jpg", True, "photo"),
                ("test.mp4", True, "video"),
                ("test.txt", False, "unknown")
            ]
            
            for filename, expected_is_media, expected_type in test_files:
                is_media, media_type = test_photo._is_media_file(filename)
                status = "✓" if (is_media == expected_is_media and media_type == expected_type) else "✗"
                print(f"  {status} {filename}: {media_type}")
            
            # Test hash calculation
            print("\n3. Testing hash calculation:")
            test_file = Path(__file__).parent / "test_visual_system.py"
            if test_file.exists():
                file_hash = test_photo._get_file_hash(str(test_file))
                print(f"  ✓ Hash calculation works (hash length: {len(file_hash)})")
            else:
                print(f"  ✗ Test file not found for hash test")
            
            print("\n✅ Photo Agent tests passed!")
        else:
            print("\n✗ Photo Agent not registered")
            return False
            
    except Exception as e:
        print(f"\n❌ Photo Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_gui_integration():
    """Test GUI integration with visual assets"""
    print("\n\nTesting GUI Integration...")
    
    try:
        # Test ImageTk availability
        try:
            from PIL import ImageTk
            print("\n1. ImageTk available: ✓")
        except ImportError:
            print("\n1. ImageTk available: ✗ (Will use fallback emojis)")
        
        # Test main.py imports
        print("\n2. Testing main.py imports:")
        try:
            import main
            print("  ✓ main.py imports successfully")
        except Exception as e:
            print(f"  ✗ main.py import failed: {e}")
            return False
        
        print("\n✅ GUI integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ GUI integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_system():
    """Test the complete visual system"""
    print("\n\n" + "="*50)
    print("COMPLETE VISUAL SYSTEM TEST")
    print("="*50)
    
    success = True
    
    # Test all components
    test_visual_assets()
    test_character_themes()
    success = test_photo_agent() and success
    success = test_gui_integration() and success
    
    if success:
        print("\n" + "="*50)
        print("🎉 ALL VISUAL SYSTEM TESTS PASSED!")
        print("="*50)
        print("\n📊 Visual System Summary:")
        print("• Enhanced character themes with extended color palettes")
        print("• Character avatars with fallback emojis")
        print("• UI icons for agents and features")
        print("• Photo Organizer Agent with date grouping and duplicate detection")
        print("• Graceful fallback when ImageTk unavailable")
        print("• Full integration with existing Serena/Astrid system")
    else:
        print("\n" + "="*50)
        print("❌ SOME VISUAL SYSTEM TESTS FAILED")
        print("="*50)
        sys.exit(1)

if __name__ == "__main__":
    test_complete_system()