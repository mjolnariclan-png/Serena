import json
from pathlib import Path
from typing import List, Dict, Optional
import ollama
from characters import get_character, get_current_character, get_character_modes, get_character_memory_file, get_character_system_prompt

# Global state — set at startup or by command
current_mode = "chat"


def get_mode_config(mode: str = None, character_id: str = None) -> Dict:
    """Get mode configuration for specified or current character and mode."""
    m = mode or current_mode
    char_modes = get_character_modes(character_id)
    return char_modes.get(m, char_modes.get("chat", {}))


def get_memory_file(mode: str = None, character_id: str = None) -> str:
    """Get memory file path for specified or current character and mode."""
    m = mode or current_mode
    return get_character_memory_file(m, character_id)


def get_current_system_prompt(mode: str = None, character_id: str = None) -> str:
    """
    Generate the authoritative system prompt dynamically from the current
    character and mode configuration.
    """
    m = mode or current_mode
    return get_character_system_prompt(m, character_id)


def load_conversation_history(mode: str = None, character_id: str = None) -> List[Dict[str, str]]:
    """
    Load ONLY actual conversation turns (user and assistant messages) from disk.
    System messages from disk are filtered out so that old system prompts or
    stale character configurations never override dynamic configuration.
    """
    file_name = get_memory_file(mode, character_id)
    path = Path(file_name)
    turns: List[Dict[str, str]] = []

    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for msg in data:
                        if isinstance(msg, dict) and msg.get("role") in ["user", "assistant"]:
                            # Prevent corrupt or non-string content
                            content = str(msg.get("content", "")).strip()
                            if content:
                                turns.append({"role": msg["role"], "content": content})
        except Exception as e:
            print(f"Warning: Failed to load conversation history from {file_name}: {e}")
            turns = []

    return turns


def save_conversation_history(turns: List[Dict[str, str]], mode: str = None, character_id: str = None) -> None:
    """
    Save ONLY user and assistant conversation turns to disk.
    Filters out any system prompts to keep the memory clean.
    """
    file_name = get_memory_file(mode, character_id)
    filtered_turns = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in turns
        if isinstance(msg, dict) and msg.get("role") in ["user", "assistant"]
    ]
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(filtered_turns, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Failed to save conversation history to {file_name}: {e}")


def load_memory(mode: str = None, character_id: str = None) -> List[Dict[str, str]]:
    """
    Construct the full message list for Ollama:
    Index 0 is ALWAYS the dynamically generated current system prompt,
    followed by the filtered conversation turns.
    """
    system_prompt = get_current_system_prompt(mode, character_id)
    turns = load_conversation_history(mode, character_id)
    return [{"role": "system", "content": system_prompt}] + turns


def save_memory(messages: List[Dict[str, str]], mode: str = None, character_id: str = None) -> None:
    """Save conversation messages by persisting only the actual conversation turns."""
    save_conversation_history(messages, mode, character_id)


def set_mode(mode: str) -> str:
    """Set mode for current character."""
    global current_mode
    character_modes = get_character_modes()
    if mode not in character_modes:
        available = ", ".join(character_modes.keys())
        return f"Unknown mode '{mode}'. Available: {available}"
    current_mode = mode
    config = character_modes[mode]
    char_name = get_character()["name"]
    return f"Switched to {config['label']} mode. Using model: {config['model']}."


def get_current_mode() -> str:
    return current_mode


def list_modes() -> str:
    """List available modes for current character."""
    character_modes = get_character_modes()
    char_name = get_character()["name"]
    lines = [f"Available modes for {char_name}:"]
    for key, cfg in character_modes.items():
        marker = "  → " if key == current_mode else "    "
        lines.append(f"{marker}{key}: {cfg['label']} (model: {cfg['model']})")
    return "\n".join(lines)


def generate_text(prompt: str) -> str:
    """
    Generate text using current character's dynamic mode configuration
    and isolated conversation memory.
    """
    config = get_mode_config()
    current_char = get_character()
    system_prompt = get_current_system_prompt()
    
    # Load actual conversation history
    turns = load_conversation_history()
    
    # Add new user message
    turns.append({"role": "user", "content": prompt})

    # Keep conversation context focused: last 20 turns
    recent_turns = turns[-20:] if len(turns) > 20 else turns

    # Construct clean payload for Ollama with dynamic system prompt at top
    context_messages = [{"role": "system", "content": system_prompt}] + recent_turns

    try:
        response = ollama.chat(
            model=config["model"],
            messages=context_messages,
            options={
                "temperature": config.get("temperature", 0.7),
                "num_predict": config.get("num_predict", 800),
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        )
        reply = response["message"]["content"].strip()
    except Exception as e:
        reply = f"AI error ({type(e).__name__}): {str(e)}\n(Make sure Ollama is running with model '{config['model']}')"

    # Add assistant response to history
    turns.append({"role": "assistant", "content": reply})
    
    # Keep total stored history manageable (last 50 turns)
    if len(turns) > 50:
        turns = turns[-50:]
    
    save_conversation_history(turns)

    return reply


def clear_memory(mode: str = None, character_id: str = None) -> str:
    """
    Wipe conversation history for the specified (or current) character and mode
    without deleting configuration or affecting other characters/modes.
    """
    m = mode or current_mode
    char = get_character(character_id)
    config = get_mode_config(m, character_id)
    save_conversation_history([], m, character_id)
    return f"Memory cleared for {char['name']}'s {config['label']} mode. Starting fresh."


def clear_all_character_memory(character_id: str = None) -> str:
    """Clear conversation history for all modes of a given character."""
    char = get_character(character_id)
    char_id = character_id or get_current_character()
    for mode in char.get("modes", {}).keys():
        save_conversation_history([], mode, char_id)
    return f"All conversation memories cleared for {char['name']}."