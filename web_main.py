#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import eel
import json
import sqlite3
from datetime import datetime
import threading
import time
import pyautogui
import psutil
from router import route
from ai import set_mode, get_current_mode, get_mode_config
from system_commands import SystemCommands

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
def process_message(message, voice_enabled=True):
    """Process user message and return response"""
    try:
        response = route(message)
        mode = get_current_mode()
        log_command(message, response, mode)
        
        # Update mode in UI
        mode_config = get_mode_config(mode)
        eel.updateMode(mode_config['label'])(lambda x: None)
        
        # Speak the response if voice is enabled
        if voice_enabled:
            speak_response(response, mode)
        
        return response
    except Exception as e:
        return f"Error processing message: {str(e)}"

def speak_response(text, mode="chat"):
    """Speak the response using TTS"""
    try:
        from voice_enhanced import speak, detect_emotion
        emotion = detect_emotion(text)
        speak(text, emotion=emotion, context=mode)
    except Exception as e:
        print(f"Voice synthesis error: {e}")

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
    return SystemCommands.open_application(app_name)

def open_website(site_name):
    """Open a website"""
    return SystemCommands.open_website(site_name)

def control_volume(action):
    """Control system volume"""
    return SystemCommands.control_volume(action)

def control_brightness(action):
    """Control screen brightness"""
    return SystemCommands.control_brightness(action)

def take_screenshot():
    """Take a screenshot"""
    return SystemCommands.take_screenshot()

def control_power(action):
    """Control system power"""
    return SystemCommands.control_power(action)

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