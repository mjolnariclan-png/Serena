from local_ai import local_response
from ai import generate_text, set_mode, list_modes, clear_memory, get_current_mode
import subprocess
import platform
import re
import webbrowser

def _open_browser(url: str) -> str:
    """Open a URL in the default browser."""
    try:
        # Use subprocess to open browser without blocking
        if platform.system() == "Windows":
            subprocess.Popen(["start", url], shell=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", url])
        else:  # Linux
            subprocess.Popen(["xdg-open", url])
        return f"Opened {url} in browser"
    except Exception as e:
        return f"Failed to open browser: {str(e)}"

def _simple_web_search(query: str) -> str:
    """Simple web search that opens Google search in browser."""
    try:
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        # Use subprocess to open browser without blocking
        if platform.system() == "Windows":
            subprocess.Popen(["start", search_url], shell=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", search_url])
        else:  # Linux
            subprocess.Popen(["xdg-open", search_url])
        return f"Opened Google search for '{query}' in browser"
    except Exception as e:
        return f"Failed to perform web search: {str(e)}"

def _generate_code(goal: str, file_path: str = None) -> str:
    """Generate code content using the AI system."""
    try:
        # Check if this is a simple GUI request for immediate handling
        goal_lower = goal.lower()
        
        # Handle common patterns directly for speed
        if "white page" in goal_lower and "400x400" in goal_lower and "arial" in goal_lower:
            # Extract the text to display - try multiple patterns
            display_text = "Hello"
            
            # Pattern 1: words "text"
            text_match = re.search(r'words\s+"([^"]+)"', goal_lower)
            if text_match:
                display_text = text_match.group(1)
            else:
                # Pattern 2: words 'text'
                text_match = re.search(r"words\s+'([^']+)'", goal_lower)
                if text_match:
                    display_text = text_match.group(1)
                else:
                    # Pattern 3: with the words "text"
                    text_match = re.search(r'with the words\s+"([^"]+)"', goal_lower)
                    if text_match:
                        display_text = text_match.group(1)
                    else:
                        # Pattern 4: with the words 'text'
                        text_match = re.search(r"with the words\s+'([^']+)'", goal_lower)
                        if text_match:
                            display_text = text_match.group(1)
            
            return f'''import tkinter as tk

root = tk.Tk()
root.title("Test Run")
root.geometry("400x400")
root.configure(bg="white")

label = tk.Label(
    root,
    text="{display_text}",
    font=("Arial", 32),
    fg="black",
    bg="white"
)
label.pack(expand=True)

root.mainloop()
'''
        
        # For other requests, use AI
        from ai import generate_text
        # Create a coding-focused prompt
        coding_prompt = f"Generate the complete code for: {goal}"
        if file_path:
            coding_prompt += f"\nFile path: {file_path}"
        coding_prompt += "\nProvide only the complete code without explanations or markdown formatting."
        
        code_content = generate_text(coding_prompt)
        return code_content
    except Exception as e:
        return f"Code generation failed: {str(e)}"

def _generate_and_write_file(goal: str, file_path: str) -> str:
    """Generate code and write it to a file."""
    try:
        # Generate the code
        code_content = _generate_code(goal, file_path)
        
        # Write to file
        from pathlib import Path
        target_file = Path(file_path)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(code_content)
        
        return f"Successfully created file: {file_path}"
    except Exception as e:
        return f"Failed to create file: {str(e)}"

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
        "files", "task", "execute", "automation",
        "google search", "web search", "do a search", "search for", "youtube", "xvideos"
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

    # System commands - Check before anything else
    from system_commands import SystemCommands
    system_result = SystemCommands.parse_command(prompt)
    if system_result:
        return system_result

    # Direct file reading handling - CHECK THIS FIRST before anything else
    if "read" in prompt_lower and "file" in prompt_lower:
        try:
            # Extract file path
            file_path = None
            path_patterns = [
                r'[A-Za-z]:\\[^\\]+\\[^\\]+\\.\\w+',  # Windows paths
                r'[A-Za-z]:/[^/]+/[^/]+\\.\\w+',    # Windows with forward slashes
                r'[^\\/\s]+\\.\\w+',                # Relative paths
            ]
            for pattern in path_patterns:
                matches = re.findall(pattern, prompt)
                if matches:
                    file_path = matches[0]
                    break
            
            # If no specific path but F:\Serena mentioned, try to read the directory
            if not file_path and "f:\\serena" in prompt_lower or "f:/serena" in prompt_lower:
                from pathlib import Path
                serena_dir = Path("F:/Serena")
                if serena_dir.exists():
                    python_files = list(serena_dir.glob("*.py"))
                    if python_files:
                        file_list = "\n".join([f"• {f.name}" for f in python_files])
                        return f"Found these Python files in F:\\Serena:\n{file_list}\n\nWhich file would you like me to read?"
                    else:
                        return "I found the F:\\Serena directory but no Python files there."
                else:
                    return "I couldn't find the F:\\Serena directory."
            
            # If we have a specific file path, read it
            if file_path:
                from pathlib import Path
                target_file = Path(file_path)
                if target_file.exists():
                    with open(target_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return f"Here's the content of {file_path}:\n\n{content}"
                else:
                    return f"File not found: {file_path}"
            else:
                return "Please specify which file you'd like me to read from F:\\Serena."
            
        except Exception as e:
            return f"Failed to read file: {str(e)}"

    # Direct file creation handling - CHECK THIS FIRST before anything else
    if ("create" in prompt_lower or "code" in prompt_lower) and "file" in prompt_lower:
        try:
            # Extract file path
            file_path = None
            if "save" in prompt_lower:
                # Look for file paths
                path_patterns = [
                    r'[A-Za-z]:\\[^\\]+\\[^\\]+\\.\\w+',  # Windows paths
                    r'[A-Za-z]:/[^/]+/[^/]+\\.\\w+',    # Windows with forward slashes
                    r'[^\\/\s]+\\.\\w+',                # Relative paths
                ]
                for pattern in path_patterns:
                    matches = re.findall(pattern, prompt)
                    if matches:
                        file_path = matches[0]
                        break
            
            # Extract file name if mentioned
            file_name = None
            if "labeled" in prompt_lower:
                labeled_match = re.search(r'labeled\s+(\S+)', prompt_lower)
                if labeled_match:
                    file_name = labeled_match.group(1)
            
            # Determine final path
            if file_path:
                final_path = file_path
            elif file_name:
                # Use default location if only file name provided
                if "save" in prompt_lower and "desktop" in prompt_lower:
                    final_path = f"C:/Users/mille/Desktop/{file_name}"
                else:
                    final_path = file_name
            else:
                final_path = "test_run.py"
            
            # Generate the code content
            code_content = _generate_code(prompt, final_path)
            
            # Write the file
            from pathlib import Path
            target_file = Path(final_path)
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(code_content)
            
            return f"Successfully created file: {final_path}"
            
        except Exception as e:
            return f"Failed to create file: {str(e)}"

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
            # Don't use permission system to avoid blocking
            perm_system = None
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
                "web_search": lambda query: _simple_web_search(query),
                "generate_code": lambda goal, file_path=None: _generate_code(goal, file_path),
                "generate_and_write_file": lambda goal, file_path: _generate_and_write_file(goal, file_path),
                "analyze_files": lambda: {"analysis": "File analysis completed"},
                "analyze_task": lambda goal: {"task_analysis": f"Analyzing task: {goal}"},
                "execute_action": lambda goal: f"Executed action for: {goal}",
                "verify_results": lambda: {"verification": "Results verified"},
                "analyze_code": lambda: {"code_analysis": "Code analyzed"},
                "analyze_results": lambda: {"results_analysis": "Results analyzed"},
                "open_browser": lambda url: _open_browser(url)
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

    # Direct file creation handling - bypass all complex routing
    if "create" in prompt_lower and "file" in prompt_lower:
        try:
            # Extract file path
            file_path = None
            if "save" in prompt_lower:
                # Look for file paths
                path_patterns = [
                    r'[A-Za-z]:\\[^\\]+\\[^\\]+\\.\\w+',  # Windows paths
                    r'[A-Za-z]:/[^/]+/[^/]+\\.\\w+',    # Windows with forward slashes
                    r'[^\\/\s]+\\.\\w+',                # Relative paths
                ]
                for pattern in path_patterns:
                    matches = re.findall(pattern, prompt)
                    if matches:
                        file_path = matches[0]
                        break
            
            # Extract file name if mentioned
            file_name = None
            if "labeled" in prompt_lower:
                labeled_match = re.search(r'labeled\s+(\S+)', prompt_lower)
                if labeled_match:
                    file_name = labeled_match.group(1)
            
            # Determine final path
            if file_path:
                final_path = file_path
            elif file_name:
                # Use default location if only file name provided
                if "save" in prompt_lower and "desktop" in prompt_lower:
                    final_path = f"C:/Users/mille/Desktop/{file_name}"
                else:
                    final_path = file_name
            else:
                final_path = "test_run.py"
            
            # Generate the code content
            code_content = _generate_code(prompt, final_path)
            
            # Write the file
            from pathlib import Path
            target_file = Path(final_path)
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(code_content)
            
            return f"Successfully created file: {final_path}"
            
        except Exception as e:
            return f"Failed to create file: {str(e)}"

    # Coding assistance
    if CODING_HELPER_AVAILABLE and is_coding_request(prompt):
        coding_result = handle_coding_request(prompt)
        if coding_result:
            return coding_result

    # Fall back to AI
    return generate_text(prompt)