"""
Serena Launcher - Background service for global hotkey startup
Run this script to enable Ctrl+Alt+S to launch/show Serena from anywhere
"""

import keyboard
import subprocess
import sys
import os
import psutil
from pathlib import Path

def is_serena_running():
    """Check if Serena is already running"""
    try:
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                # Check if this is a Python process running main.py
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline and any('main.py' in str(cmd) for cmd in cmdline):
                        return True, proc.pid
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False, None
    except Exception as e:
        print(f"Error checking processes: {e}")
        return False, None

def launch_serena():
    """Launch Serena as a fresh instance or show if already running"""
    try:
        running, pid = is_serena_running()
        
        if running:
            print("Serena is already running, showing window...")
            # Try to bring existing window to front
            # Since we can't directly control the window from launcher,
            # we'll just let the user know
            print("Serena is already running! Check your taskbar or system tray.")
        else:
            # Get the directory where this script is located
            script_dir = Path(__file__).parent
            main_script = script_dir / "main.py"
            
            print("Launching Serena...")
            
            # Launch main.py as a separate process
            if os.name == 'nt':  # Windows
                subprocess.Popen([sys.executable, str(main_script)], 
                              creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:  # Linux/Mac
                subprocess.Popen([sys.executable, str(main_script)], 
                              start_new_session=True)
            
            print("Serena launched successfully!")
        
    except Exception as e:
        print(f"Failed to launch Serena: {e}")

def main():
    print("Serena Launcher Running...")
    print("Press Ctrl+Alt+S to launch/show Serena from anywhere")
    print("Press Ctrl+Alt+Q to quit the launcher")
    
    # Setup hotkeys
    keyboard.add_hotkey('ctrl+alt+s', launch_serena)
    keyboard.add_hotkey('ctrl+alt+q', lambda: sys.exit(0))
    
    print("Launcher active. Waiting for hotkey...")
    
    # Keep the script running
    keyboard.wait()

if __name__ == "__main__":
    main()