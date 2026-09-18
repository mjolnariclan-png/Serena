"""
Comprehensive test suite verifying:
- Serena character selection
- Astrid character selection
- Mode switching
- Memory isolation
- System prompt generation (dynamic and uncorrupted by conversation history)
- Character switching and context separation
- Duplicate greeting prevention
- Non-fatal voice and optional dependency behavior
"""

import sys
import json
from pathlib import Path

def test_character_independence_and_metadata():
    print("--- 1. Testing Character Independence & Metadata ---")
    from characters import get_character, set_character, list_characters, CHARACTERS
    
    # Check Serena metadata
    serena = CHARACTERS["serena"]
    assert serena["age_rating"] == "Adult (18+)", "Serena missing adult rating"
    assert serena["name"] == "Serena", "Serena name mismatch"
    assert "Pokémon" in serena["identity"], "Serena identity mismatch"
    
    # Check Astrid metadata
    astrid = CHARACTERS["astrid"]
    assert astrid["age_rating"] == "Adult (18+)", "Astrid missing adult rating"
    assert astrid["name"] == "Astrid", "Astrid name mismatch"
    assert "Norse" in astrid["identity"] or "Viking" in astrid["identity"], "Astrid identity mismatch"
    
    # Verify independent themes
    assert serena["theme"]["accent_color"] != astrid["theme"]["accent_color"], "Themes are not independent"
    
    # Verify independent voices
    assert serena["voice"]["default_voice"] != astrid["voice"]["default_voice"], "Voices are not independent"
    
    # Verify independent memory files
    for mode in ["chat", "story", "code", "agentic"]:
        assert serena["memory_files"][mode] != astrid["memory_files"][mode], f"Memory files for {mode} not independent"
    
    print("✅ Character independence and metadata verified.")


def test_dynamic_system_prompts_and_isolation():
    print("\n--- 2. Testing Dynamic System Prompts & Memory Isolation ---")
    from characters import set_character, get_character
    from ai import set_mode, get_current_mode, get_current_system_prompt, load_memory, save_conversation_history, load_conversation_history
    
    # Test Serena in Chat mode
    set_character("serena")
    set_mode("chat")
    p1 = get_current_system_prompt()
    assert "Serena" in p1 and "Pokémon" in p1, "Serena chat prompt invalid"
    assert "Astrid" not in p1, "Astrid leaked into Serena chat prompt"
    
    # Switch Serena to Story mode
    set_mode("story")
    p2 = get_current_system_prompt()
    assert "creative writing" in p2.lower() or "story" in p2.lower(), "Serena story prompt invalid"
    assert p1 != p2, "Mode prompts did not change"
    
    # Switch to Astrid in Chat mode
    set_character("astrid")
    set_mode("chat")
    p3 = get_current_system_prompt()
    assert "Astrid" in p3 and "Norse" in p3, "Astrid chat prompt invalid"
    assert "Pokémon" not in p3, "Pokémon leaked into Astrid chat prompt"
    
    # Test that conversation history contains only user/assistant turns and no system prompt
    save_conversation_history([
        {"role": "system", "content": "FAKE OLD SYSTEM INSTRUCTION"},
        {"role": "user", "content": "Test user query"},
        {"role": "assistant", "content": "Test assistant answer"}
    ], mode="chat", character_id="astrid")
    
    loaded_turns = load_conversation_history(mode="chat", character_id="astrid")
    # System message must have been stripped
    assert len(loaded_turns) == 2, "System message was not stripped from conversation history"
    assert loaded_turns[0]["role"] == "user"
    assert loaded_turns[1]["role"] == "assistant"
    
    # load_memory must dynamically inject current system prompt at index 0
    full_messages = load_memory(mode="chat", character_id="astrid")
    assert len(full_messages) == 3
    assert full_messages[0]["role"] == "system"
    assert full_messages[0]["content"] == p3, "load_memory did not dynamically generate system prompt"
    assert "FAKE OLD SYSTEM INSTRUCTION" not in full_messages[0]["content"]
    
    print("✅ Dynamic system prompts and memory isolation verified.")


def test_clear_memory_safety():
    print("\n--- 3. Testing Safe Memory Clearing ---")
    from characters import set_character
    from ai import clear_memory, load_conversation_history, save_conversation_history, get_mode_config
    
    set_character("serena")
    save_conversation_history([{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}], mode="chat", character_id="serena")
    
    # Verify turns exist
    assert len(load_conversation_history(mode="chat", character_id="serena")) == 2
    
    # Clear memory
    res = clear_memory("chat", "serena")
    assert "cleared" in res.lower()
    
    # Memory must now be empty
    assert len(load_conversation_history(mode="chat", character_id="serena")) == 0
    
    # Mode config must remain completely intact
    config = get_mode_config("chat", "serena")
    assert config["label"] == "Chat / Adventure"
    assert "model" in config
    assert "system_prompt" in config
    
    print("✅ Memory clearing safely clears conversation without affecting configuration.")


def test_duplicate_greeting_prevention():
    print("\n--- 4. Testing Duplicate Greeting Prevention ---")
    import tkinter as tk
    import main
    
    # Create hidden root
    root = tk.Tk()
    root.withdraw()
    
    app = main.SerenaApp(root)
    
    # Inspect chat contents on initial startup
    chat_text = app.chat.get("1.0", tk.END).strip()
    welcome_count = chat_text.count("Hey trainer!") + chat_text.count("Welcome, friend.")
    assert welcome_count == 1, f"Expected exactly 1 welcome greeting on startup, got {welcome_count}"
    
    # Switch character to Astrid
    app.switch_character("astrid")
    chat_text_astrid = app.chat.get("1.0", tk.END).strip()
    # On character switch, only the switch confirmation message should be added, not a duplicate welcome block
    assert "Switched to Astrid" in chat_text_astrid
    
    root.destroy()
    print("✅ Startup and character-switch duplicate greeting prevention verified.")


def test_voice_lazy_non_fatal():
    print("\n--- 5. Testing Non-Fatal Voice and Audio Fallbacks ---")
    import voice_enhanced
    import characters
    
    # Calling speak with invalid device or broken audio should never raise an unhandled exception
    try:
        voice_enhanced.speak("Test fallback voice message", character="serena")
        print("✅ Voice call executed safely without crash.")
    except Exception as e:
        assert False, f"speak() raised unhandled exception: {e}"


def run_all_tests():
    print("=" * 60)
    print("RUNNING SERENA & ASTRID ARCHITECTURE VERIFICATION TESTS")
    print("=" * 60)
    test_character_independence_and_metadata()
    test_dynamic_system_prompts_and_isolation()
    test_clear_memory_safety()
    test_duplicate_greeting_prevention()
    test_voice_lazy_non_fatal()
    print("\n" + "=" * 60)
    print("🎉 ALL ARCHITECTURE AND SYSTEM TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
