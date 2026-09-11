from local_ai import local_response
from ai import generate_text, set_mode, list_modes, clear_memory, get_current_mode

# Import optional features - these will be available if dependencies are installed
try:
    from web_search import search_web, is_search_query, extract_search_query
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False

# Import Hermes Agent for agentic capabilities
try:
    from hermes_wrapper import is_hermes_available, get_hermes_agent, hermes_chat
    HERMES_AVAILABLE = is_hermes_available()
except ImportError:
    HERMES_AVAILABLE = False

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

def is_agentic_request(prompt: str) -> bool:
    """Detect if a request requires agentic capabilities (multi-step tasks, tool use, etc.)"""
    agentic_keywords = [
        "organize", "rename", "move", "copy", "delete", "create",
        "analyze", "inspect", "check", "scan", "search",
        "download", "upload", "install", "setup", "configure",
        "plan", "execute", "run", "automate", "batch",
        "multiple files", "all files", "directory", "folder",
        "system", "process", "service", "registry",
        "files", "task", "execute", "automation"
    ]
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in agentic_keywords)

def detect_mode_switch(prompt: str) -> str:
    """Automatically detect and switch modes based on conversation context"""
    prompt_lower = prompt.lower()
    
    # Chat/sexual mode detection - explicit, romantic, or sexual keywords
    chat_keywords = [
        "babe", "baby", "hun", "honey", "love", "sexy", "hot", "horny",
        "fuck", "sex", "naughty", "dirty", "kiss", "touch", "pleasure",
        "aroused", "turn on", "wet", "hard", "cock", "dick", "pussy",
        "cum", "orgasm", "intimate", "desire", "lust", "seduce", "flirt",
        "beautiful", "gorgeous", "pretty", "handsome", "miss you", "want you"
    ]
    
    # Writing/story mode detection - check first since it has specific terms
    story_keywords = [
        "write", "story", "book", "chapter", "character", "plot", "novel",
        "creative writing", "fiction", "narrative", "protagonist", "dialogue",
        "scene", "setting", "genre", "draft", "outline", "manuscript",
        "author", "publish", "literary", "poem", "poetry", "tale"
    ]
    
    # Coding mode detection
    code_keywords = [
        "code", "function", "class", "python", "javascript", "programming",
        "debug", "error", "syntax", "variable", "algorithm", "api", "database",
        "implement", "refactor", "compile", "script", "fix",
        "git", "repository", "commit", "pull", "push", "merge", "branch",
        "developer", "software", "app", "application"
    ]
    
    # Check each category - story has priority over code for overlapping terms
    if any(keyword in prompt_lower for keyword in chat_keywords):
        if get_current_mode() != "chat":
            set_mode("chat")
            return "[Auto-switched to Chat mode]"
    
    elif any(keyword in prompt_lower for keyword in story_keywords):
        if get_current_mode() != "story":
            set_mode("story")
            return "[Auto-switched to Writing mode]"
    
    elif any(keyword in prompt_lower for keyword in code_keywords):
        if get_current_mode() != "code":
            set_mode("code")
            return "[Auto-switched to Coding mode]"
    
    return None

def route(prompt: str):
    prompt_lower = prompt.lower().strip()

    # Shutdown
    if any(word in prompt_lower for word in ["turn off", "shutdown", "go to sleep", "goodbye"]):
        return "__SHUTDOWN__"

    # Manual mode switching
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

    # Local commands (check BEFORE mode switching and AI)
    local_result = local_response(prompt)
    if local_result is not None:
        return local_result

    # Automatic mode detection (only if not handled by local commands)
    mode_switch = detect_mode_switch(prompt)
    if mode_switch:
        # Process the prompt with the new mode
        return f"{mode_switch}\n{generate_text(prompt)}"

    # Agentic requests - route to Hermes if available or if in agentic mode
    if HERMES_AVAILABLE and (is_agentic_request(prompt) or get_current_mode() == "agentic"):
        try:
            hermes_response = hermes_chat(prompt)
            if hermes_response:
                return f"[Agentic Mode] {hermes_response}"
            else:
                print("Hermes returned no response, falling back to local agentic")
                # Fall through to local agentic system
        except Exception as e:
            print(f"Hermes error: {e}, falling back to local agentic")
            # Fall through to local agentic system
    
    # Fallback agentic handling when Hermes is not available but we have agentic requests or are in agentic mode
    if is_agentic_request(prompt) or get_current_mode() == "agentic":
        try:
            from agentic_executor import get_agentic_executor
            from agentic_tools import get_agentic_tools
            from permission_system import get_permission_system
            
            # Get the components
            tools_instance = get_agentic_tools()
            perm_system = get_permission_system()
            executor = get_agentic_executor(None, perm_system)
            
            # Map agentic_tools methods to executor tools
            tool_mapping = {
                "list_files": tools_instance.list_files,
                "read_file": tools_instance.read_file,
                "write_file": tools_instance.write_file,
                "rename_file": tools_instance.rename_file,
                "delete_file": tools_instance.delete_file,
                "create_directory": tools_instance.create_directory,
                "organize_files": tools_instance.organize_files,
                "run_command": tools_instance.run_command,
                "get_system_info": tools_instance.get_system_info,
                "web_search": tools_instance.web_search,
                "analyze_files": lambda: {"analysis": "File analysis completed"},
                "analyze_task": lambda goal: {"task_analysis": f"Analyzing task: {goal}"},
                "execute_action": lambda goal: f"Executed action for: {goal}",
                "verify_results": lambda: {"verification": "Results verified"},
                "analyze_code": lambda: {"code_analysis": "Code analyzed"},
                "analyze_results": lambda: {"results_analysis": "Results analyzed"}
            }
            executor.tools = tool_mapping
            
            # For non-agentic requests in agentic mode, just use standard AI
            if not is_agentic_request(prompt):
                return generate_text(prompt)
            
            # Create and execute a simple task for agentic requests
            task = executor.create_task(prompt)
            if executor.plan_task(task):
                results = executor.execute_task(task)
                if results["success"]:
                    return f"[Local Agentic] Task completed: {results['final_result']}"
                else:
                    return f"[Local Agentic] Task encountered issues: {results.get('error', 'Unknown error')}"
            else:
                return f"[Local Agentic] Could not plan task: {task.error_message}"
                
        except Exception as e:
            print(f"Local agentic error: {e}")
            return f"Local agentic system encountered an error: {str(e)}. Using standard mode instead."

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

    # Fall back to AI
    return generate_text(prompt)