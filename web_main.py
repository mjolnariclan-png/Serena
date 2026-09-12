import eel
import json
import sqlite3
import os
from datetime import datetime
import threading
import time
import pyautogui
import psutil
from pathlib import Path
from router import route
from ai import set_mode, get_current_mode, get_mode_config

# Initialize Eel
eel.init('www')

# Command history database
DB_PATH = Path(__file__).parent / "command_history.db"

def init_database():
    """Initialize command history database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT NOT NULL,
            response TEXT,
            mode TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_command(command, response, mode):
    """Log command to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO commands (command, response, mode)
        VALUES (?, ?, ?)
    ''', (command, response, mode))
    conn.commit()
    conn.close()

def get_recent_commands(limit=10):
    """Get recent commands from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT command, timestamp FROM commands 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    commands = cursor.fetchall()
    conn.close()
    return commands

# Initialize database
init_database()

@eel.expose
def process_message(message):
    """Process user message and return response"""
    try:
        response = route(message)
        mode = get_current_mode()
        log_command(message, response, mode)
        
        # Update mode in UI
        mode_config = get_mode_config(mode)
        eel.updateMode(mode_config['label'])(lambda x: None)
        
        return response
    except Exception as e:
        return f"Error processing message: {str(e)}"

@eel.expose
def voice_input():
    """Handle voice input"""
    try:
        from voice_enhanced import listen
        user_input, emotion = listen(duration=6, emotion_detection=True)
        return user_input if user_input else ""
    except Exception as e:
        print(f"Voice input error: {e}")
        return ""

@eel.expose
def get_system_stats():
    """Get system statistics"""
    try:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()
        battery_percent = battery.percent if battery else 0
        
        return {
            'cpu': cpu,
            'memory': memory,
            'battery': battery_percent
        }
    except Exception as e:
        print(f"System stats error: {e}")
        return {'cpu': 0, 'memory': 0, 'battery': 0}

@eel.expose
def execute_command(command):
    """Execute system command"""
    try:
        return route(command)
    except Exception as e:
        return f"Error executing command: {str(e)}"

# Enhanced system control functions
def open_application(app_name):
    """Open an application"""
    apps = {
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
        'spotify': 'spotify.exe',
        'steam': 'steam.exe',
        'cmd': 'cmd.exe',
        'taskmanager': 'taskmgr.exe',
        'explorer': 'explorer.exe',
        'paint': 'mspaint.exe'
    }
    
    if app_name.lower() in apps:
        try:
            os.startfile(apps[app_name.lower()])
            return f"Opened {app_name}"
        except Exception as e:
            return f"Failed to open {app_name}: {str(e)}"
    else:
        return f"Application '{app_name}' not recognized"

def open_website(site_name):
    """Open a website"""
    sites = {
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
        'whatsapp': 'https://web.whatsapp.com'
    }
    
    if site_name.lower() in sites:
        try:
            import webbrowser
            webbrowser.open(sites[site_name.lower()])
            return f"Opened {site_name}"
        except Exception as e:
            return f"Failed to open {site_name}: {str(e)}"
    else:
        return f"Website '{site_name}' not recognized"

def control_volume(action):
    """Control system volume"""
    try:
        if action == 'up':
            pyautogui.press('volumeup')
            return "Volume increased"
        elif action == 'down':
            pyautogui.press('volumedown')
            return "Volume decreased"
        elif action == 'mute':
            pyautogui.press('volumemute')
            return "Volume toggled"
        else:
            return "Unknown volume action"
    except Exception as e:
        return f"Volume control error: {str(e)}"

def control_brightness(action):
    """Control screen brightness"""
    try:
        if action == 'up':
            pyautogui.press('brightnessup')
            return "Brightness increased"
        elif action == 'down':
            pyautogui.press('brightnessdown')
            return "Brightness decreased"
        else:
            return "Unknown brightness action"
    except Exception as e:
        return f"Brightness control error: {str(e)}"

def take_screenshot():
    """Take a screenshot"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = Path.home() / "Desktop" / f"screenshot_{timestamp}.png"
        pyautogui.screenshot(str(screenshot_path))
        return f"Screenshot saved to {screenshot_path}"
    except Exception as e:
        return f"Screenshot error: {str(e)}"

def control_power(action):
    """Control system power"""
    try:
        if action == 'shutdown':
            os.system('shutdown /s /t 1')
            return "Shutting down..."
        elif action == 'restart':
            os.system('shutdown /r /t 1')
            return "Restarting..."
        elif action == 'sleep':
            os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
            return "Going to sleep..."
        elif action == 'lock':
            os.system('rundll32.exe user32.dll,LockWorkStation')
            return "Locking computer..."
        else:
            return "Unknown power action"
    except Exception as e:
        return f"Power control error: {str(e)}"

def send_whatsapp(phone_number, message):
    """Send WhatsApp message"""
    try:
        import pywhatkit
        pywhatkit.sendwhatmsg_instantly(phone_number, message)
        return f"WhatsApp message sent to {phone_number}"
    except Exception as e:
        return f"WhatsApp error: {str(e)}"

# Start in chat mode
set_mode("chat")

if __name__ == "__main__":
    print("Starting Serena Web Interface...")
    print("Open http://localhost:8080 in your browser")
    eel.start('index.html', port=8080, size=(1200, 800))