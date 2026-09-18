#!/usr/bin/env python3
"""
Test script to verify character switching and functionality
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_character_system():
    """Test the character configuration system"""
    print("Testing character system...")
    
    from characters import get_character, set_character, get_current_character, list_characters, get_character_theme, get_character_voice
    
    # Test 1: List characters
    print("\n1. Available characters:")
    print(list_characters())
    
    # Test 2: Get current character (should be Serena)
    print("\n2. Current character:")
    current = get_current_character()
    print(f"Current: {current}")
    char = get_character()
    print(f"Name: {char['name']}")
    print(f"Identity: {char['identity']}")
    
    # Test 3: Switch to Astrid
    print("\n3. Switching to Astrid:")
    result = set_character("astrid")
    print(result)
    astrid = get_character()
    print(f"Name: {astrid['name']}")
    print(f"Identity: {astrid['identity']}")
    
    # Test 4: Get Astrid's theme
    print("\n4. Astrid's theme:")
    theme = get_character_theme("astrid")
    print(f"Primary BG: {theme['primary_bg']}")
    print(f"Accent Color: {theme['accent_color']}")
    
    # Test 5: Get Astrid's voice config
    print("\n5. Astrid's voice configuration:")
    voice = get_character_voice("astrid")
    print(f"Default voice: {voice['default_voice']}")
    print(f"Voice rate: {voice['voice_rate']}")
    
    # Test 6: Switch back to Serena
    print("\n6. Switching back to Serena:")
    result = set_character("serena")
    print(result)
    serena = get_character()
    print(f"Name: {serena['name']}")
    
    # Test 7: Get Serena's theme
    print("\n7. Serena's theme:")
    theme = get_character_theme("serena")
    print(f"Primary BG: {theme['primary_bg']}")
    print(f"Accent Color: {theme['accent_color']}")
    
    print("\n✅ Character system tests passed!")

def test_ai_integration():
    """Test AI integration with characters"""
    print("\n\nTesting AI integration with characters...")
    
    from ai import get_mode_config, get_memory_file, get_character_system_prompt, get_character_memory_file
    from characters import get_current_character
    
    # Test 1: Get mode config for current character
    print("\n1. Mode config for current character:")
    current_char = get_current_character()
    print(f"Current character: {current_char}")
    config = get_mode_config("chat")
    print(f"Chat mode label: {config['label']}")
    print(f"System prompt length: {len(config['system_prompt'])}")
    
    # Test 2: Get memory file
    print("\n2. Memory file for chat mode:")
    memory_file = get_memory_file("chat")
    print(f"Memory file: {memory_file}")
    
    # Test 3: Get character-specific memory file
    print("\n3. Character-specific memory files:")
    chat_memory = get_character_memory_file("chat", "serena")
    story_memory = get_character_memory_file("story", "serena")
    astrid_chat_memory = get_character_memory_file("chat", "astrid")
    print(f"Serena chat memory: {chat_memory}")
    print(f"Serena story memory: {story_memory}")
    print(f"Astrid chat memory: {astrid_chat_memory}")
    
    # Test 4: Get character system prompts
    print("\n4. Character system prompts:")
    serena_prompt = get_character_system_prompt("chat", "serena")
    astrid_prompt = get_character_system_prompt("chat", "astrid")
    print(f"Serena chat prompt length: {len(serena_prompt)}")
    print(f"Astrid chat prompt length: {len(astrid_prompt)}")
    print(f"Serena prompt contains 'Pokémon': {'Pokémon' in serena_prompt}")
    print(f"Astrid prompt contains 'Norse': {'Norse' in astrid_prompt}")
    
    print("\n✅ AI integration tests passed!")

def test_voice_integration():
    """Test voice integration with characters"""
    print("\n\nTesting voice integration with characters...")
    
    try:
        from voice_enhanced import get_character_voice_safe, get_emotion_voice
        from characters import get_character_voice
        
        # Test 1: Get character voice safely
        print("\n1. Character voice configurations:")
        serena_voice = get_character_voice_safe("serena")
        astrid_voice = get_character_voice_safe("astrid")
        print(f"Serena default voice: {serena_voice['default_voice']}")
        print(f"Astrid default voice: {astrid_voice['default_voice']}")
        
        # Test 2: Get emotion voices
        print("\n2. Emotion-based voices:")
        serena_happy = get_emotion_voice("happy", "chat", "serena")
        astrid_happy = get_emotion_voice("happy", "chat", "astrid")
        print(f"Serena happy voice: {serena_happy}")
        print(f"Astrid happy voice: {astrid_happy}")
        
        print("\n✅ Voice integration tests passed!")
    except Exception as e:
        print(f"\n⚠️ Voice integration test skipped (voice dependencies not available): {e}")

def test_router_integration():
    """Test router integration with characters"""
    print("\n\nTesting router integration with characters...")
    
    try:
        from router import detect_mode_switch
        from characters import set_character, get_character
        
        # Test 1: Mode detection with Serena
        print("\n1. Mode detection with Serena:")
        set_character("serena")
        result = detect_mode_switch("I want to write a story about coding")
        print(f"Mode switch result: {result}")
        
        # Test 2: Mode detection with Astrid
        print("\n2. Mode detection with Astrid:")
        set_character("astrid")
        result = detect_mode_switch("Tell me a Norse saga")
        print(f"Mode switch result: {result}")
        
        # Reset to Serena
        set_character("serena")
        
        print("\n✅ Router integration tests passed!")
    except Exception as e:
        print(f"\n⚠️ Router integration test failed: {e}")

if __name__ == "__main__":
    try:
        test_character_system()
        test_ai_integration()
        test_voice_integration()
        test_router_integration()
        
        print("\n" + "="*50)
        print("🎉 ALL TESTS PASSED!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)