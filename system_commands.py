"""
System Commands Module - JARVIS-like system control
Handles application launching, website opening, system control, etc.
"""

import os
import subprocess
import platform
import webbrowser
from pathlib import Path
from datetime import datetime

# Optional pyautogui import
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

class SystemCommands:
    """Centralized system command handling"""
    
    # Application mappings
    APPLICATIONS = {
        'calculator': 'calc.exe',
        'notepad': 'notepad.exe',
        'chrome': 'chrome.exe',
        'edge': 'msedge.exe',
        'firefox': 'firefox.exe',
        'word': 'winword.exe',
        'excel': 'excel.exe',
        'powerpoint': 'powerpnt.exe',
        'vlc': 'vlc.exe',
        'vscode': 'code.exe',
        'visual studio code': 'code.exe',
        'spotify': 'spotify.exe',
        'steam': 'steam.exe',
        'cmd': 'cmd.exe',
        'command prompt': 'cmd.exe',
        'taskmanager': 'taskmgr.exe',
        'task manager': 'taskmgr.exe',
        'explorer': 'explorer.exe',
        'file explorer': 'explorer.exe',
        'paint': 'mspaint.exe',
        'settings': 'ms-settings:',
        'control panel': 'control.exe'
    }
    
    # Website mappings
    WEBSITES = {
        'google': 'https://www.google.com',
        'youtube': 'https://www.youtube.com',
        'wikipedia': 'https://www.wikipedia.org',
        'github': 'https://www.github.com',
        'amazon': 'https://www.amazon.com',
        'instagram': 'https://www.instagram.com',
        'facebook': 'https://www.facebook.com',
        'twitter': 'https://www.twitter.com',
        'linkedin': 'https://www.linkedin.com',
        'netflix': 'https://www.netflix.com',
        'gmail': 'https://mail.google.com',
        'whatsapp': 'https://web.whatsapp.com',
        'whatsapp web': 'https://web.whatsapp.com',
        'reddit': 'https://www.reddit.com',
        'twitch': 'https://www.twitch.tv',
        'discord': 'https://www.discord.com',
        'spotify': 'https://open.spotify.com'
    }
    
    @staticmethod
    def open_application(app_name):
        """Open an application by name"""
        app_lower = app_name.lower()
        
        # Mapping for Linux / generic commands
        linux_apps = {
            'calculator': 'gnome-calculator',
            'notepad': 'gedit',
            'chrome': 'google-chrome',
            'edge': 'microsoft-edge',
            'firefox': 'firefox',
            'vlc': 'vlc',
            'vscode': 'code',
            'visual studio code': 'code',
            'spotify': 'spotify',
            'steam': 'steam',
            'terminal': 'x-terminal-emulator',
            'cmd': 'x-terminal-emulator',
            'command prompt': 'x-terminal-emulator',
            'taskmanager': 'gnome-system-monitor',
            'task manager': 'gnome-system-monitor',
            'explorer': 'nautilus',
            'file explorer': 'nautilus',
        }
        
        system = platform.system()
        
        # Try Windows
        if system == "Windows":
            target = SystemCommands.APPLICATIONS.get(app_lower)
            if not target:
                for app, exe in SystemCommands.APPLICATIONS.items():
                    if app_lower in app or app in app_lower:
                        target = exe
                        break
            if target:
                try:
                    if hasattr(os, 'startfile'):
                        os.startfile(target)
                    else:
                        subprocess.Popen([target], shell=True)
                    return f"Opened {app_name}"
                except Exception as e:
                    return f"Failed to open {app_name}: {str(e)}"
        else:
            # Linux / macOS
            cmd = linux_apps.get(app_lower, app_lower)
            try:
                subprocess.Popen([cmd])
                return f"Opened {app_name}"
            except FileNotFoundError:
                try:
                    subprocess.Popen(["xdg-open", app_name])
                    return f"Opened {app_name}"
                except Exception as e:
                    return f"Failed to open {app_name}: {str(e)}"
            except Exception as e:
                return f"Failed to open {app_name}: {str(e)}"
        
        return f"Application '{app_name}' not recognized"
    
    @staticmethod
    def open_website(site_name):
        """Open a website by name"""
        site_lower = site_name.lower()
        
        # Try exact match first
        if site_lower in SystemCommands.WEBSITES:
            try:
                webbrowser.open(SystemCommands.WEBSITES[site_lower])
                return f"Opened {site_name}"
            except Exception as e:
                return f"Failed to open {site_name}: {str(e)}"
        
        # Try partial match
        for site, url in SystemCommands.WEBSITES.items():
            if site_lower in site or site in site_lower:
                try:
                    webbrowser.open(url)
                    return f"Opened {site}"
                except Exception as e:
                    return f"Failed to open {site}: {str(e)}"
        
        # If it looks like a URL, try opening directly
        if '.' in site_name and not site_name.startswith('http'):
            try:
                webbrowser.open(f"https://{site_name}")
                return f"Opened {site_name}"
            except Exception as e:
                return f"Failed to open {site_name}: {str(e)}"
        
        return f"Website '{site_name}' not recognized"
    
    @staticmethod
    def control_volume(action):
        """Control system volume"""
        if not PYAUTOGUI_AVAILABLE:
            return "Volume control not available (pyautogui not installed)"
        try:
            if action in ['up', 'increase', 'raise']:
                for _ in range(5):  # Press multiple times for noticeable change
                    pyautogui.press('volumeup')
                return "Volume increased"
            elif action in ['down', 'decrease', 'lower']:
                for _ in range(5):
                    pyautogui.press('volumedown')
                return "Volume decreased"
            elif action in ['mute', 'unmute', 'toggle']:
                pyautogui.press('volumemute')
                return "Volume toggled"
            else:
                return "Unknown volume action"
        except Exception as e:
            return f"Volume control error: {str(e)}"
    
    @staticmethod
    def control_brightness(action):
        """Control screen brightness"""
        if not PYAUTOGUI_AVAILABLE:
            return "Brightness control not available (pyautogui not installed)"
        try:
            if action in ['up', 'increase', 'raise']:
                for _ in range(5):
                    pyautogui.press('brightnessup')
                return "Brightness increased"
            elif action in ['down', 'decrease', 'lower']:
                for _ in range(5):
                    pyautogui.press('brightnessdown')
                return "Brightness decreased"
            else:
                return "Unknown brightness action"
        except Exception as e:
            return f"Brightness control error: {str(e)}"
    
    @staticmethod
    def take_screenshot():
        """Take a screenshot"""
        if not PYAUTOGUI_AVAILABLE:
            return "Screenshot not available (pyautogui not installed)"
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = Path.home() / "Desktop" / f"screenshot_{timestamp}.png"
            pyautogui.screenshot(str(screenshot_path))
            return f"Screenshot saved to {screenshot_path}"
        except Exception as e:
            return f"Screenshot error: {str(e)}"
    
    @staticmethod
    def show_desktop():
        """Show desktop (minimize all windows)"""
        if not PYAUTOGUI_AVAILABLE:
            return "Show desktop not available (pyautogui not installed)"
        try:
            pyautogui.hotkey('win', 'd')
            return "Desktop shown"
        except Exception as e:
            return f"Show desktop error: {str(e)}"
    
    @staticmethod
    def minimize_all():
        """Minimize all windows"""
        if not PYAUTOGUI_AVAILABLE:
            return "Minimize all not available (pyautogui not installed)"
        try:
            pyautogui.hotkey('win', 'd')
            return "All windows minimized"
        except Exception as e:
            return f"Minimize error: {str(e)}"
    
    @staticmethod
    def control_power(action):
        """Control system power"""
        system = platform.system()
        try:
            if action in ['shutdown', 'shut down', 'turn off']:
                if system == "Windows":
                    os.system('shutdown /s /t 1')
                else:
                    os.system('systemctl poweroff || shutdown -h now')
                return "Shutting down..."
            elif action in ['restart', 'reboot']:
                if system == "Windows":
                    os.system('shutdown /r /t 1')
                else:
                    os.system('systemctl reboot || reboot')
                return "Restarting..."
            elif action in ['sleep', 'hibernate']:
                if system == "Windows":
                    os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
                else:
                    os.system('systemctl suspend')
                return "Going to sleep..."
            elif action in ['lock', 'lock computer']:
                if system == "Windows":
                    os.system('rundll32.exe user32.dll,LockWorkStation')
                else:
                    os.system('loginctl lock-session || xdg-screensaver lock')
                return "Locking computer..."
            else:
                return "Unknown power action"
        except Exception as e:
            return f"Power control error: {str(e)}"
    
    @staticmethod
    def send_whatsapp(phone_number, message):
        """Send WhatsApp message"""
        try:
            import pywhatkit
            pywhatkit.sendwhatmsg_instantly(phone_number, message)
            return f"WhatsApp message sent to {phone_number}"
        except Exception as e:
            return f"WhatsApp error: {str(e)}"
    
    @staticmethod
    def parse_command(command):
        """Parse natural language command and execute"""
        command_lower = command.lower()
        
        # Application opening
        if 'open' in command_lower:
            # Check for websites
            for site in SystemCommands.WEBSITES:
                if site in command_lower:
                    return SystemCommands.open_website(site)
            
            # Check for applications
            for app in SystemCommands.APPLICATIONS:
                if app in command_lower:
                    return SystemCommands.open_application(app)
        
        # Volume control
        if 'volume' in command_lower:
            if 'up' in command_lower or 'increase' in command_lower:
                return SystemCommands.control_volume('up')
            elif 'down' in command_lower or 'decrease' in command_lower:
                return SystemCommands.control_volume('down')
            elif 'mute' in command_lower:
                return SystemCommands.control_volume('mute')
        
        # Brightness control
        if 'brightness' in command_lower:
            if 'up' in command_lower or 'increase' in command_lower:
                return SystemCommands.control_brightness('up')
            elif 'down' in command_lower or 'decrease' in command_lower:
                return SystemCommands.control_brightness('down')
        
        # Screenshot
        if 'screenshot' in command_lower or 'take screenshot' in command_lower:
            return SystemCommands.take_screenshot()
        
        # Desktop
        if 'show desktop' in command_lower or 'desktop' in command_lower:
            return SystemCommands.show_desktop()
        
        # Minimize
        if 'minimize' in command_lower:
            return SystemCommands.minimize_all()
        
        # Power control
        if 'shutdown' in command_lower or 'shut down' in command_lower:
            return SystemCommands.control_power('shutdown')
        elif 'restart' in command_lower or 'reboot' in command_lower:
            return SystemCommands.control_power('restart')
        elif 'sleep' in command_lower:
            return SystemCommands.control_power('sleep')
        elif 'lock' in command_lower:
            return SystemCommands.control_power('lock')
        
        return None  # Command not recognized