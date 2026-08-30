from local_ai import local_response
from ai import generate_text, set_mode, list_modes, clear_memory, get_current_mode

# Import optional features - these will be available if dependencies are installed
try:
    from web_search import search_web, is_search_query, extract_search_query
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False

try:
    from image_gen import generate_image, is_image_request, extract_image_prompt
    IMAGE_GEN_AVAILABLE = True
except ImportError:
    IMAGE_GEN_AVAILABLE = False

try:
    from gif_gen import generate_gif, is_gif_request, extract_gif_prompt
    GIF_GEN_AVAILABLE = True
except ImportError:
    GIF_GEN_AVAILABLE = False

try:
    from coding_helper import is_coding_request, handle_coding_request
    CODING_HELPER_AVAILABLE = True
except ImportError:
    CODING_HELPER_AVAILABLE = False

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

    # GIF generation (check before image generation since it's more specific)
    if GIF_GEN_AVAILABLE and is_gif_request(prompt):
        gif_prompt = extract_gif_prompt(prompt)
        return generate_gif(gif_prompt)
    
    # Image generation
    if IMAGE_GEN_AVAILABLE and is_image_request(prompt):
        from image_gen import extract_quality_settings
        image_prompt = extract_image_prompt(prompt)
        quality_settings = extract_quality_settings(prompt)
        return generate_image(
            image_prompt, 
            width=quality_settings["width"],
            height=quality_settings["height"],
            steps=quality_settings["steps"]
        )

    # Web search
    if WEB_SEARCH_AVAILABLE and is_search_query(prompt):
        search_query = extract_search_query(prompt)
        return search_web(search_query)

    # Coding assistance
    if CODING_HELPER_AVAILABLE and is_coding_request(prompt):
        coding_result = handle_coding_request(prompt)
        if coding_result:
            return coding_result

    # Local commands (exact match only)
    local_result = local_response(prompt)
    if local_result is not None:
        return local_result

    # Fall back to AI
    return generate_text(prompt)