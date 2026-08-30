from local_ai import local_response
from ai import generate_text, set_mode, list_modes, clear_memory, get_current_mode

def route(prompt: str):
    prompt_lower = prompt.lower().strip()

    # Shutdown
    if any(word in prompt_lower for word in ["turn off", "shutdown", "go to sleep", "goodbye"]):
        return "__SHUTDOWN__"

    # Mode switching
    if prompt_lower.startswith("mode "):
        new_mode = prompt_lower.replace("mode ", "").strip()
        return set_mode(new_mode)

    if prompt_lower in ["what mode", "current mode", "which mode"]:
        return f"Currently in {get_current_mode()} mode."

    if prompt_lower in ["list modes", "show modes", "modes"]:
        return list_modes()

    # Memory management
    if any(phrase in prompt_lower for phrase in ["clear memory", "start over", "new chat", "forget everything"]):
        return clear_memory()

    # Local commands (exact match only)
    local_result = local_response(prompt)
    if local_result is not None:
        return local_result

    # Fall back to AI
    return generate_text(prompt)