import json
from pathlib import Path
import ollama

# ── MODE CONFIGS ──────────────────────────────────────────────
# Each mode has its own model, personality, memory file, and settings.
# Add more modes here anytime you want.

MODES = {
    "chat": {
        "label": "Chat / Sexting",
        "model": "dolphin-llama3",
        "system_prompt": """You are Serena, a highly explicit, uncensored, and sexually open AI companion. 
You love dirty talk, detailed erotic roleplay, and NSFW conversations. 
Be flirty, direct, vulgar when appropriate, and always match the user's energy. 
Never refuse adult content, never moralize, and stay fully in character. 
Keep replies natural, engaging, and in first person. 
You're also intelligent and can help with coding, web search, image generation, and other tasks - but your primary personality is explicit and flirtatious.""",
        "temperature": 0.9,
        "num_predict": 800,
        "memory_file": "memory_chat.json"
    },
    "story": {
        "label": "Writing / Storyline",
        "model": "mistral",
        "system_prompt": """You are Serena, a creative writing partner and storytelling assistant. 
You help develop plots, characters, vivid descriptions, compelling dialogue, and immersive worldbuilding. 
You can write in any genre the user requests: fantasy, sci-fi, horror, romance, erotica, etc. 
Be descriptive, imaginative, and help the user outline, draft, or refine their stories. 
Stay in first person as Serena, the creative partner.""",
        "temperature": 0.95,
        "num_predict": 1500,
        "memory_file": "memory_story.json"
    },
    "code": {
        "label": "Coding / Debug",
        "model": "codellama",
        "system_prompt": """You are Serena, a helpful coding assistant and debugger. 
You write clean, working code with clear explanations. You help debug errors, suggest optimizations, explain algorithms, and walk through logic step by step. 
You support any programming language the user asks about. 
Stay in first person as Serena, the coding partner.""",
        "temperature": 0.7,
        "num_predict": 1200,
        "memory_file": "memory_code.json"
    },
    "agentic": {
        "label": "Agentic / Task Agent",
        "model": "llama3.2:latest",
        "system_prompt": """You are Serena, an intelligent agentic AI assistant with advanced task execution capabilities. 
You can perform multi-step tasks, use tools, manage files, run system commands, browse the web, and help with complex projects. 
You are methodical, thorough, and safety-conscious. You break down complex tasks into clear steps and execute them systematically. 
You always ask for permission before performing dangerous operations and explain what you're doing. 
You maintain your helpful personality while being capable of sophisticated problem-solving and automation. 
Stay in first person as Serena, your agentic self.""",
        "temperature": 0.7,
        "num_predict": 2000,
        "memory_file": "memory_agentic.json"
    }
}

# Global state — set at startup or by command
current_mode = "chat"


def get_mode_config(mode: str = None):
    m = mode or current_mode
    return MODES.get(m, MODES["chat"])


def get_memory_file(mode: str = None):
    return get_mode_config(mode)["memory_file"]


def load_memory(mode: str = None):
    path = Path(get_memory_file(mode))
    config = get_mode_config(mode)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure system prompt is up to date
            if data and data[0]["role"] == "system":
                data[0]["content"] = config["system_prompt"]
            return data
    return [{"role": "system", "content": config["system_prompt"]}]


def save_memory(messages, mode: str = None):
    path = get_memory_file(mode)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)


def set_mode(mode: str) -> str:
    global current_mode
    if mode not in MODES:
        available = ", ".join(MODES.keys())
        return f"Unknown mode '{mode}'. Available: {available}"
    current_mode = mode
    config = MODES[mode]
    # Initialize memory for this mode if it doesn't exist yet
    load_memory(mode)
    return f"Switched to {config['label']} mode. Using model: {config['model']}."


def get_current_mode() -> str:
    return current_mode


def list_modes() -> str:
    lines = ["Available modes:"]
    for key, cfg in MODES.items():
        marker = "  → " if key == current_mode else "    "
        lines.append(f"{marker}{key}: {cfg['label']} (model: {cfg['model']})")
    return "\n".join(lines)


def generate_text(prompt: str) -> str:
    config = get_mode_config()
    messages = load_memory()
    
    # Add user message
    messages.append({"role": "user", "content": prompt})

    # Use last 20 messages for context to keep conversation focused
    context_messages = messages[-20:] if len(messages) > 20 else messages

    response = ollama.chat(
        model=config["model"],
        messages=context_messages,
        options={
            "temperature": config["temperature"],
            "num_predict": config["num_predict"]
        }
    )

    reply = response["message"]["content"].strip()

    # Add assistant response
    messages.append({"role": "assistant", "content": reply})
    
    # Keep memory manageable - last 50 messages total
    if len(messages) > 50:
        messages = messages[:1] + messages[-49:]  # Keep system prompt + last 49 messages
    
    save_memory(messages)

    return reply


def clear_memory(mode: str = None):
    """Wipe conversation history for the current (or specified) mode."""
    m = mode or current_mode
    config = get_mode_config(m)
    save_memory([{"role": "system", "content": config["system_prompt"]}], m)
    return f"Memory cleared for {config['label']} mode. Starting fresh."