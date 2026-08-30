import os
import datetime
import subprocess
import platform
import sys

def local_response(prompt: str):
    p = prompt.lower().strip()

    # Time requests
    if any(x in p for x in ["what time is it", "current time", "tell me the time", "time"]):
        return datetime.datetime.now().strftime("It's %I:%M %p on %B %d, %Y.")
    
    if any(x in p for x in ["what day is it", "what's the date", "today's date"]):
        return datetime.datetime.now().strftime("Today is %A, %B %d, %Y.")

    # System commands
    if p in ["open chrome", "launch chrome", "start chrome"]:
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["start", "chrome"], shell=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", "-a", "Google Chrome"])
            else:  # Linux
                subprocess.Popen(["google-chrome"])
            return "Opening Chrome for you."
        except Exception as e:
            return f"Couldn't open Chrome: {str(e)}"

    if p in ["open code", "launch code", "start vs code", "open vs code"]:
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["code"])
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", "-a", "Visual Studio Code"])
            else:  # Linux
                subprocess.Popen(["code"])
            return "Opening VS Code for you."
        except Exception as e:
            return f"Couldn't open VS Code: {str(e)}"

    # Automation
    if p.startswith("type "):
        try:
            import pyautogui
            pyautogui.write(p[5:])
            return "Typed it out for you."
        except ImportError:
            return "I need the pyautogui library to do that."
        except Exception as e:
            return f"Couldn't type that: {str(e)}"

    # File operations
    if p.startswith("create file "):
        try:
            filename = p[12:].strip()
            with open(filename, 'w') as f:
                f.write("")
            return f"Created empty file: {filename}"
        except Exception as e:
            return f"Couldn't create file: {str(e)}"

    if p.startswith("create folder ") or p.startswith("create directory "):
        try:
            foldername = p[13:].strip() if "folder" in p else p[17:].strip()
            os.makedirs(foldername, exist_ok=True)
            return f"Created folder: {foldername}"
        except Exception as e:
            return f"Couldn't create folder: {str(e)}"

    # System info
    if p in ["system info", "what's my system", "my computer info"]:
        system_info = f"You're running {platform.system()} {platform.release()}"
        if platform.system() == "Windows":
            system_info += f" (Version {platform.version()})"
        return system_info

    # Help
    if p in ["help", "what can you do", "capabilities"]:
        return """I can help you with:
• Web search (just ask me to search for anything)
• Generate images and GIFs using Stable Diffusion
• Coding assistance and debugging
• Creative writing and storytelling
• Open applications (Chrome, VS Code, etc.)
• Type text for you
• Create files and folders
• Tell you the time and date
• Remember our conversations and context
• And much more through AI conversation!

Just ask me anything naturally!"""

    return None