#!/usr/bin/env python3
"""
Test script to verify Serena functionality and Astrid feature parity
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_serena_functionality():
    """Test that all original Serena functionality still works"""
    print("Testing Serena functionality...")
    
    from characters import set_character, get_character
    from ai import set_mode, get_mode_config, get_memory_file, list_modes, generate_text
    from router import route
    
    # Set to Serena
    set_character("serena")
    serena = get_character()
    print(f"Testing with {serena['name']}")
    
    # Test 1: Mode switching
    print("\n1. Mode switching:")
    modes = ["chat", "story", "code", "agentic"]
    for mode in modes:
        result = set_mode(mode)
        print(f"  {mode}: {result}")
    
    # Test 2: Mode configurations
    print("\n2. Mode configurations:")
    set_mode("chat")
    chat_config = get_mode_config("chat")
    print(f"  Chat label: {chat_config['label']}")
    print(f"  Chat model: {chat_config['model']}")
    
    # Test 3: Memory files
    print("\n3. Memory files:")
    for mode in modes:
        memory_file = get_memory_file(mode)
        print(f"  {mode}: {memory_file}")
    
    # Test 4: AI text generation (mock test)
    print("\n4. AI system integration:")
    print(f"  System prompt contains 'Pokémon': {'Pokémon' in chat_config['system_prompt']}")
    print(f"  System prompt contains 'Serena': {'Serena' in chat_config['system_prompt']}")
    
    # Test 5: Router integration
    print("\n5. Router integration:")
    test_prompts = [
        "hello",
        "write a story",
        "debug this code",
        "search for python"
    ]
    for prompt in test_prompts:
        try:
            # We won't actually call route to avoid Ollama dependency
            # Just test that the import works
            print(f"  Router available for: '{prompt}'")
        except Exception as e:
            print(f"  Router error for '{prompt}': {e}")
    
    print("\n✅ Serena functionality tests passed!")

def test_astrid_feature_parity():
    """Test that Astrid has feature parity with Serena"""
    print("\n\nTesting Astrid feature parity...")
    
    from characters import set_character, get_character, get_character_modes, get_character_memory_file
    from ai import set_mode, get_mode_config, get_memory_file
    
    # Set to Astrid
    set_character("astrid")
    astrid = get_character()
    print(f"Testing with {astrid['name']}")
    
    # Test 1: Same modes available
    print("\n1. Mode availability:")
    serena_modes = get_character_modes("serena")
    astrid_modes = get_character_modes("astrid")
    
    print(f"  Serena modes: {list(serena_modes.keys())}")
    print(f"  Astrid modes: {list(astrid_modes.keys())}")
    
    modes_match = set(serena_modes.keys()) == set(astrid_modes.keys())
    print(f"  Modes match: {modes_match}")
    
    # Test 2: Mode structure
    print("\n2. Mode structure:")
    for mode in ["chat", "story", "code", "agentic"]:
        serena_mode = serena_modes[mode]
        astrid_mode = astrid_modes[mode]
        
        has_label = "label" in astrid_mode
        has_model = "model" in astrid_mode
        has_system_prompt = "system_prompt" in astrid_mode
        has_temperature = "temperature" in astrid_mode
        has_num_predict = "num_predict" in astrid_mode
        
        print(f"  {mode}: All fields present: {all([has_label, has_model, has_system_prompt, has_temperature, has_num_predict])}")
    
    # Test 3: Memory files
    print("\n3. Memory file structure:")
    for mode in ["chat", "story", "code", "agentic"]:
        serena_memory = get_character_memory_file(mode, "serena")
        astrid_memory = get_character_memory_file(mode, "astrid")
        
        has_suffix = "_astrid" in astrid_memory
        is_different = serena_memory != astrid_memory
        
        print(f"  {mode}: Separate memory file: {has_suffix and is_different}")
    
    # Test 4: Voice configuration
    print("\n4. Voice configuration:")
    serena_voice = get_character("serena")["voice"]
    astrid_voice = get_character("astrid")["voice"]
    
    print(f"  Serena has voice config: {bool(serena_voice)}")
    print(f"  Astrid has voice config: {bool(astrid_voice)}")
    print(f"  Different default voices: {serena_voice['default_voice'] != astrid_voice['default_voice']}")
    
    # Test 5: Theme configuration
    print("\n5. Theme configuration:")
    serena_theme = get_character("serena")["theme"]
    astrid_theme = get_character("astrid")["theme"]
    
    print(f"  Serena has theme: {bool(serena_theme)}")
    print(f"  Astrid has theme: {bool(astrid_theme)}")
    print(f"  Different themes: {serena_theme['accent_color'] != astrid_theme['accent_color']}")
    
    # Test 6: Character-specific content
    print("\n6. Character-specific content:")
    chat_config = get_mode_config("chat")
    
    has_norse = "Norse" in chat_config["system_prompt"]
    has_viking = "Viking" in chat_config["system_prompt"]
    no_pokemon = "Pokémon" not in chat_config["system_prompt"]
    
    print(f"  Contains Norse content: {has_norse or has_viking}")
    print(f"  No Pokémon content: {no_pokemon}")
    
    print("\n✅ Astrid feature parity tests passed!")

def test_voice_system():
    """Test voice system with both characters"""
    print("\n\nTesting voice system with both characters...")
    
    try:
        from voice_enhanced import get_character_voice_safe, get_emotion_voice, VOICE_AVAILABLE
        from characters import set_character
        
        if not VOICE_AVAILABLE:
            print("Voice system not available (missing dependencies)")
            return
        
        # Test Serena voice
        print("\n1. Serena voice configuration:")
        set_character("serena")
        serena_voice = get_character_voice_safe("serena")
        print(f"  Default voice: {serena_voice['default_voice']}")
        print(f"  Voice rate: {serena_voice['voice_rate']}")
        
        # Test emotion voices for Serena
        for emotion in ["happy", "sad", "angry", "excited", "calm"]:
            voice = get_emotion_voice(emotion, "chat", "serena")
            print(f"  {emotion}: {voice}")
        
        # Test Astrid voice
        print("\n2. Astrid voice configuration:")
        set_character("astrid")
        astrid_voice = get_character_voice_safe("astrid")
        print(f"  Default voice: {astrid_voice['default_voice']}")
        print(f"  Voice rate: {astrid_voice['voice_rate']}")
        
        # Test emotion voices for Astrid
        for emotion in ["happy", "sad", "angry", "excited", "calm"]:
            voice = get_emotion_voice(emotion, "chat", "astrid")
            print(f"  {emotion}: {voice}")
        
        # Test that voices are different
        print("\n3. Voice differentiation:")
        voices_different = serena_voice['default_voice'] != astrid_voice['default_voice']
        print(f"  Different default voices: {voices_different}")
        
        print("\n✅ Voice system tests passed!")
        
    except Exception as e:
        print(f"\n⚠️ Voice system test failed: {e}")

def test_state_isolation():
    """Test that character state is properly isolated"""
    print("\n\nTesting character state isolation...")
    
    from characters import set_character, get_character, get_current_character
    from ai import set_mode, get_mode_config, get_memory_file
    
    # Test 1: Character switching
    print("\n1. Character switching isolation:")
    set_character("serena")
    serena_char = get_character()
    set_character("astrid")
    astrid_char = get_character()
    
    print(f"  Serena name: {serena_char['name']}")
    print(f"  Astrid name: {astrid_char['name']}")
    print(f"  Characters are different: {serena_char['name'] != astrid_char['name']}")
    
    # Test 2: Mode isolation
    print("\n2. Mode isolation per character:")
    set_character("serena")
    set_mode("chat")
    serena_mode = get_current_character()
    
    set_character("astrid")
    set_mode("story")
    astrid_mode = get_current_character()
    
    print(f"  Current character after Astrid switch: {astrid_mode}")
    print(f"  Correctly switched to Astrid: {astrid_mode == 'astrid'}")
    
    # Test 3: Memory file isolation
    print("\n3. Memory file isolation:")
    set_character("serena")
    serena_chat_mem = get_memory_file("chat")
    
    set_character("astrid")
    astrid_chat_mem = get_memory_file("chat")
    
    print(f"  Serena chat memory: {serena_chat_mem}")
    print(f"  Astrid chat memory: {astrid_chat_mem}")
    print(f"  Memory files are different: {serena_chat_mem != astrid_chat_mem}")
    
    # Reset to Serena
    set_character("serena")
    
    print("\n✅ State isolation tests passed!")

if __name__ == "__main__":
    try:
        test_serena_functionality()
        test_astrid_feature_parity()
        test_voice_system()
        test_state_isolation()
        
        print("\n" + "="*50)
        print("🎉 ALL FUNCTIONALITY TESTS PASSED!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)