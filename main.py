#!/usr/bin/env python3
# main.py
import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import scrolledtext, ttk
from ai import set_mode, list_modes
from characters import get_character, set_character, get_current_character, get_character_theme, list_characters
import threading
import keyboard
import time
from PIL import Image, ImageDraw
try:
    from PIL import ImageTk
    IMAGETK_AVAILABLE = True
except ImportError:
    IMAGETK_AVAILABLE = False

# Optional system tray import - use lazy import to avoid crashes
PYSTRAY_AVAILABLE = False
def _try_import_pystray():
    global PYSTRAY_AVAILABLE
    try:
        import pystray
        PYSTRAY_AVAILABLE = True
        return pystray
    except Exception:
        PYSTRAY_AVAILABLE = False
        return None


class SerenaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Serena & Astrid")
        self.root.geometry("800x700")
        
        # ── CHARACTER STATE ─────────────────────────────────
        self.current_character = get_current_character()
        self.current_theme = get_character_theme(self.current_character)
        self.apply_theme()
        
        # ── LAZY VOICE IMPORTS ───────────────────────────────
        self.voice_loaded = False
        self.listen = None
        self.speak = None
        self.voice_available = True  # Track if voice system is available

        # ── HOTKEY SYSTEM ─────────────────────────────────────
        self.hotkeys_enabled = True
        self.setup_hotkeys()

        # ── CONTINUOUS CONVERSATION ─────────────────────────
        self.continuous_conversation = None
        self.continuous_active = False

        # ── VOICE SETTINGS ─────────────────────────────────
        self.voice_output_enabled = True  # Voice enabled by default

        # ── SYSTEM TRAY ───────────────────────────────────
        self.setup_system_tray()
        
        # ── AGENT SYSTEM ───────────────────────────────────
        self.setup_agent_system()
        
        # ── VISUAL ASSETS ───────────────────────────────────
        self.setup_visual_assets()

        # ── BUILD UI WITH CHARACTER TABS ────────────────────
        self.build_main_ui()
        
        # ── START DIRECTLY IN CHAT MODE ───────────────────────
        set_mode("chat")
        self.build_chat_ui("Chat / Adventure mode", is_startup=True)
    
    def apply_theme(self):
        """Apply current character's theme to the application"""
        self.current_theme = get_character_theme(self.current_character)
        self.root.configure(bg=self.current_theme["primary_bg"])
    
    def switch_character(self, character_id):
        """Switch to a different character"""
        if character_id == self.current_character and hasattr(self, 'chat_frame'):
            return
        result = set_character(character_id)
        self.current_character = get_current_character()
        self.apply_theme()
        
        # Update tab appearance
        self.update_tab_appearance()
        
        # Update character info label
        char_info = get_character()
        self.info_label.config(text=f"{char_info['name']} - {char_info['identity']}", 
                               fg=self.current_theme["accent_color"],
                               bg=self.current_theme["primary_bg"])
        
        # Update avatars
        if IMAGETK_AVAILABLE and hasattr(self, 'visual_assets') and "serena_avatar" in self.visual_assets and "astrid_avatar" in self.visual_assets:
            if character_id == "serena":
                self.serena_avatar_label.config(image=self.visual_assets["serena_avatar"])
            else:
                self.astrid_avatar_label.config(image=self.visual_assets["astrid_avatar"])
        
        # Rebuild UI with new theme
        self.chat_frame.destroy()
        self.chat_frame = tk.Frame(self.root, bg=self.current_theme["primary_bg"])
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.build_chat_ui(f"Switched to {get_character()['name']}", is_startup=False)
        
        # Update voice configuration
        if self.voice_loaded:
            try:
                from voice_enhanced import set_voice
                voice_config = get_character()["voice"]
                set_voice(voice_config["default_voice"])
            except Exception as e:
                print(f"Voice switch notice: {e}")
        
        # Update tray icon
        pystray = _try_import_pystray()
        if pystray and hasattr(self, 'tray_icon'):
            try:
                new_icon = self.create_tray_icon()
                self.tray_icon.icon = new_icon
            except:
                pass
        
        self.add_message(get_character()["name"], result)
        self._speak(result)
    
    def update_tab_appearance(self):
        """Update tab button appearances based on current character"""
        theme = self.current_theme
        
        if self.current_character == "serena":
            self.serena_tab.config(bg=theme["button_color"], relief=tk.RAISED)
            self.astrid_tab.config(bg=theme["secondary_bg"], relief=tk.FLAT)
        else:
            self.serena_tab.config(bg=theme["secondary_bg"], relief=tk.FLAT)
            self.astrid_tab.config(bg=theme["button_color"], relief=tk.RAISED)

    def build_main_ui(self):
        """Build the main UI with character tabs and visual assets"""
        # Character selection tabs with avatars
        tab_frame = tk.Frame(self.root, bg=self.current_theme["primary_bg"])
        tab_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Serena tab with avatar
        serena_frame = tk.Frame(tab_frame, bg=self.current_theme["primary_bg"])
        serena_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.serena_avatar_label = tk.Label(serena_frame, bg=self.current_theme["primary_bg"])
        if IMAGETK_AVAILABLE and "serena_avatar" in self.visual_assets:
            self.serena_avatar_label.config(image=self.visual_assets["serena_avatar"])
        else:
            self.serena_avatar_label.config(text="⚡", font=("Segoe UI", 16))
        self.serena_avatar_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.serena_tab = tk.Button(
            serena_frame,
            text="⚡ Serena",
            command=lambda: self.switch_character("serena"),
            bg=self.current_theme["button_color"] if self.current_character == "serena" else self.current_theme["secondary_bg"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.RAISED if self.current_character == "serena" else tk.FLAT
        )
        self.serena_tab.pack(side=tk.LEFT)
        
        # Astrid tab with avatar
        astrid_frame = tk.Frame(tab_frame, bg=self.current_theme["primary_bg"])
        astrid_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.astrid_avatar_label = tk.Label(astrid_frame, bg=self.current_theme["primary_bg"])
        if IMAGETK_AVAILABLE and "astrid_avatar" in self.visual_assets:
            self.astrid_avatar_label.config(image=self.visual_assets["astrid_avatar"])
        else:
            self.astrid_avatar_label.config(text="🛡️", font=("Segoe UI", 16))
        self.astrid_avatar_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.astrid_tab = tk.Button(
            astrid_frame,
            text="🛡️ Astrid",
            command=lambda: self.switch_character("astrid"),
            bg=self.current_theme["button_color"] if self.current_character == "astrid" else self.current_theme["secondary_bg"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.RAISED if self.current_character == "astrid" else tk.FLAT
        )
        self.astrid_tab.pack(side=tk.LEFT)
        
        # Character info label
        char_info = get_character()
        self.info_label = tk.Label(
            tab_frame,
            text=f"{char_info['name']} - {char_info['identity']}",
            fg=self.current_theme["accent_color"],
            bg=self.current_theme["primary_bg"],
            font=("Segoe UI", 9, "italic")
        )
        self.info_label.pack(side=tk.RIGHT, padx=10)
        
        # Chat frame container
        self.chat_frame = tk.Frame(self.root, bg=self.current_theme["primary_bg"])
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def setup_hotkeys(self):
        """Setup global hotkeys for common actions"""
        try:
            # Hotkey combinations (Ctrl+Alt+S is handled by launcher)
            self.hotkeys = {
                'ctrl+shift+s': self.toggle_voice_mode,
                'ctrl+shift+c': self.clear_chat,
                'ctrl+shift+m': self.cycle_modes,
                'ctrl+shift+q': self.quick_exit,
                'ctrl+shift+v': self.voice_input,
                'ctrl+shift+h': self.show_hotkeys,
                'ctrl+shift+t': self.toggle_continuous_conversation,
                'ctrl+shift+a': self.show_agent_status
            }
            
            # Register hotkeys
            for hotkey, callback in self.hotkeys.items():
                keyboard.add_hotkey(hotkey, callback)
            
            print("Hotkeys enabled:")
            print("  Ctrl+Shift+S: Toggle voice mode")
            print("  Ctrl+Shift+C: Clear chat")
            print("  Ctrl+Shift+M: Cycle modes")
            print("  Ctrl+Shift+Q: Quick exit")
            print("  Ctrl+Shift+V: Voice input")
            print("  Ctrl+Shift+H: Show hotkeys")
            print("  Ctrl+Shift+T: Toggle continuous conversation")
            print("  Ctrl+Shift+A: Show agent status")
            print("  (Run launcher.py for Ctrl+Alt+S global startup)")
            
        except Exception as e:
            print(f"Could not setup hotkeys: {e}")
            print("Hotkeys require root/sudo access on Linux. Running without hotkeys.")
            self.hotkeys_enabled = False

    def toggle_voice_mode(self):
        """Toggle between text and voice input mode"""
        if hasattr(self, 'input_method'):
            current = self.input_method.get()
            new_mode = "voice" if current == "text" else "text"
            self.input_method.set(new_mode)
            self.toggle_input()
            char_name = get_character()["name"]
            self.add_message(char_name, f"Switched to {new_mode} mode")

    def clear_chat(self):
        """Clear the chat display"""
        if hasattr(self, 'chat'):
            self.chat.configure(state="normal")
            self.chat.delete(1.0, tk.END)
            self.chat.configure(state="disabled")
            char_name = get_character()["name"]
            self.add_message(char_name, "Chat cleared. Ready for new conversation.")

    def cycle_modes(self):
        """Cycle through available modes"""
        from ai import get_current_mode, set_mode
        from characters import get_character_modes
        character_modes = get_character_modes()
        modes = list(character_modes.keys())
        current = get_current_mode()
        current_index = modes.index(current) if current in modes else 0
        next_index = (current_index + 1) % len(modes)
        next_mode = modes[next_index]
        result = set_mode(next_mode)
        char_name = get_character()["name"]
        self.add_message(char_name, result)
        if hasattr(self, 'mode_label'):
            from ai import get_mode_config
            mode_config = get_mode_config(next_mode)
            self.mode_label.config(text=f"Mode: {mode_config['label']}")

    def quick_exit(self):
        """Quick exit with confirmation"""
        char_name = get_character()["name"]
        self.add_message(char_name, "Goodnight! Shutting down...")
        self._speak("Goodnight! Shutting down.")
        self.root.after(1000, self.root.destroy)

    def voice_input(self):
        """Trigger voice input immediately"""
        if hasattr(self, 'send_voice'):
            self.send_voice()

    def show_hotkeys(self):
        """Display available hotkeys in chat"""
        hotkey_info = """Available Hotkeys:
• Ctrl+Shift+S: Toggle voice mode
• Ctrl+Shift+C: Clear chat
• Ctrl+Shift+M: Cycle modes
• Ctrl+Shift+Q: Quick exit
• Ctrl+Shift+V: Voice input
• Ctrl+Shift+H: Show this help
• Ctrl+Shift+T: Toggle continuous conversation
• Ctrl+Shift+A: Show agent status
• (Run launcher.py for Ctrl+Alt+S global startup)"""
        char_name = get_character()["name"]
        self.add_message(char_name, hotkey_info)
    
    def show_agent_status(self):
        """Display agent system status in chat"""
        if not hasattr(self, 'agent_manager') or not self.agent_manager:
            self.add_message(get_character()["name"], "Agent system not available")
            return
        
        try:
            # Phase 3: Enhanced agent dashboard
            status = self.get_comprehensive_agent_status()
            
            self.add_message(get_character()["name"], f"🤖 Agent Ecosystem Status:\n{status}")
            
        except Exception as e:
            self.add_message(get_character()["name"], f"Error getting agent status: {e}")
    
    def get_comprehensive_agent_status(self) -> str:
        """
        Get comprehensive agent ecosystem status for display.
        
        Phase 3: Enhanced dashboard with queue, events, and tasks.
        
        Returns:
        Formatted status string
        """
        if not hasattr(self, 'agent_manager') or not self.agent_manager:
            return "Agent system not available"
        
        try:
            lines = []
            
            # Agent status
            agent_status = self.agent_manager.get_all_agent_status()
            lines.append("AGENTS:")
            for agent_name, status in agent_status.get("agents", {}).items():
                status_symbol = "●" if status["status"] == "working" else "○"
                lines.append(f"  {status_symbol} {agent_name}: {status['status']}")
                lines.append(f"      Tasks: {status['tasks_completed']}, Errors: {status['errors']}")
            
            # Queue status
            queue_status = self.agent_manager.get_queue_status()
            if queue_status.get("available"):
                lines.append(f"\nTASK QUEUE:")
                lines.append(f"  Queued tasks: {queue_status.get('queue_size', 0)}")
                lines.append(f"  Blocked tasks: {len(queue_status.get('blocked_tasks', {}))}")
                stats = queue_status.get("statistics", {})
                lines.append(f"  Status breakdown: {stats.get('status_breakdown', {})}")
            
            # Agent capabilities
            capabilities = self.agent_manager.get_agent_capabilities()
            lines.append(f"\nAGENT CAPABILITIES:")
            for agent_id, caps in capabilities.items():
                lines.append(f"  {agent_id}:")
                lines.append(f"    Type: {caps.get('agent_type', 'Unknown')}")
                lines.append(f"    Tasks: {', '.join(caps.get('supported_task_types', []))}")
            
            # Scheduled tasks
            scheduled = self.agent_manager.get_scheduled_tasks()
            if scheduled:
                lines.append(f"\nSCHEDULED TASKS:")
                for task_id, schedule in scheduled.items():
                    if schedule["active"]:
                        lines.append(f"  {task_id}: {schedule['goal']}")
                        lines.append(f"    Type: {schedule['schedule_type']}, Next run: {schedule['next_run']}")
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def show_agent_dashboard(self):
        """
        Show a dedicated agent dashboard window.
        
        Phase 3: Comprehensive GUI dashboard for agent ecosystem.
        """
        if not hasattr(self, 'agent_manager') or not self.agent_manager:
            self.add_message(get_character()["name"], "Agent system not available")
            return
        
        # Create dashboard window
        dashboard = tk.Toplevel(self.root)
        dashboard.title("Agent Ecosystem Dashboard")
        dashboard.geometry("900x600")
        dashboard.configure(bg=self.current_theme["primary_bg"])
        
        # Create notebook for tabs
        notebook = ttk.Notebook(dashboard)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Agents tab
        agents_frame = tk.Frame(notebook, bg=self.current_theme["primary_bg"])
        notebook.add(agents_frame, text="Agents")
        
        agents_text = scrolledtext.ScrolledText(agents_frame, bg=self.current_theme["secondary_bg"], 
                                                  fg=self.current_theme["text_color"])
        agents_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        agent_status = self.agent_manager.get_all_agent_status()
        agents_text.insert(tk.END, "AGENT STATUS\n" + "="*50 + "\n")
        for agent_name, status in agent_status.get("agents", {}).items():
            agents_text.insert(tk.END, f"\n{agent_name}:\n")
            agents_text.insert(tk.END, f"  Status: {status['status']}\n")
            agents_text.insert(tk.END, f"  Tasks completed: {status['tasks_completed']}\n")
            agents_text.insert(tk.END, f"  Errors: {status['errors']}\n")
            if status.get("last_activity"):
                agents_text.insert(tk.END, f"  Last activity: {status['last_activity']}\n")
        
        # Tasks tab
        tasks_frame = tk.Frame(notebook, bg=self.current_theme["primary_bg"])
        notebook.add(tasks_frame, text="Tasks")
        
        tasks_text = scrolledtext.ScrolledText(tasks_frame, bg=self.current_theme["secondary_bg"],
                                                fg=self.current_theme["text_color"])
        tasks_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        queue_status = self.agent_manager.get_queue_status()
        tasks_text.insert(tk.END, "TASK QUEUE\n" + "="*50 + "\n")
        if queue_status.get("available"):
            tasks_text.insert(tk.END, f"\nQueue size: {queue_status.get('queue_size', 0)}\n")
            tasks_text.insert(tk.END, f"Blocked tasks: {len(queue_status.get('blocked_tasks', {}))}\n")
            stats = queue_status.get("statistics", {})
            tasks_text.insert(tk.END, f"\nStatus breakdown:\n")
            for status, count in stats.get("status_breakdown", {}).items():
                tasks_text.insert(tk.END, f"  {status}: {count}\n")
        
        # Capabilities tab
        caps_frame = tk.Frame(notebook, bg=self.current_theme["primary_bg"])
        notebook.add(caps_frame, text="Capabilities")
        
        caps_text = scrolledtext.ScrolledText(caps_frame, bg=self.current_theme["secondary_bg"],
                                               fg=self.current_theme["text_color"])
        caps_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        capabilities = self.agent_manager.get_agent_capabilities()
        caps_text.insert(tk.END, "AGENT CAPABILITIES\n" + "="*50 + "\n")
        for agent_id, caps in capabilities.items():
            caps_text.insert(tk.END, f"\n{agent_id}:\n")
            caps_text.insert(tk.END, f"  Type: {caps.get('agent_type', 'Unknown')}\n")
            caps_text.insert(tk.END, f"  Description: {caps.get('description', 'No description')}\n")
            caps_text.insert(tk.END, f"  Supported tasks: {', '.join(caps.get('supported_task_types', []))}\n")
        
        # Refresh button
        refresh_btn = tk.Button(dashboard, text="Refresh", command=lambda: self._refresh_dashboard(agents_text, tasks_text, caps_text),
                               bg=self.current_theme["button_color"], fg="white")
        refresh_btn.pack(pady=5)
        
        # Update hotkey to use dashboard
        self.hotkeys['ctrl+shift+a'] = self.show_agent_dashboard
    
    def _refresh_dashboard(self, agents_text, tasks_text, caps_text):
        """Refresh the dashboard content"""
        # Clear and reload agents
        agents_text.delete(1.0, tk.END)
        agent_status = self.agent_manager.get_all_agent_status()
        agents_text.insert(tk.END, "AGENT STATUS\n" + "="*50 + "\n")
        for agent_name, status in agent_status.get("agents", {}).items():
            agents_text.insert(tk.END, f"\n{agent_name}:\n")
            agents_text.insert(tk.END, f"  Status: {status['status']}\n")
            agents_text.insert(tk.END, f"  Tasks completed: {status['tasks_completed']}\n")
            agents_text.insert(tk.END, f"  Errors: {status['errors']}\n")
            if status.get("last_activity"):
                agents_text.insert(tk.END, f"  Last activity: {status['last_activity']}\n")
        
        # Clear and reload tasks
        tasks_text.delete(1.0, tk.END)
        queue_status = self.agent_manager.get_queue_status()
        tasks_text.insert(tk.END, "TASK QUEUE\n" + "="*50 + "\n")
        if queue_status.get("available"):
            tasks_text.insert(tk.END, f"\nQueue size: {queue_status.get('queue_size', 0)}\n")
            tasks_text.insert(tk.END, f"Blocked tasks: {len(queue_status.get('blocked_tasks', {}))}\n")
            stats = queue_status.get("statistics", {})
            tasks_text.insert(tk.END, f"\nStatus breakdown:\n")
            for status, count in stats.get("status_breakdown", {}).items():
                tasks_text.insert(tk.END, f"  {status}: {count}\n")
        
        # Clear and reload capabilities
        caps_text.delete(1.0, tk.END)
        capabilities = self.agent_manager.get_agent_capabilities()
        caps_text.insert(tk.END, "AGENT CAPABILITIES\n" + "="*50 + "\n")
        for agent_id, caps in capabilities.items():
            caps_text.insert(tk.END, f"\n{agent_id}:\n")
            caps_text.insert(tk.END, f"  Type: {caps.get('agent_type', 'Unknown')}\n")
            caps_text.insert(tk.END, f"  Description: {caps.get('description', 'No description')}\n")
            caps_text.insert(tk.END, f"  Supported tasks: {', '.join(caps.get('supported_task_types', []))}\n")

    def toggle_continuous_conversation(self):
        """Toggle continuous voice conversation mode"""
        if not self.voice_available:
            self.add_message(get_character()["name"], "Voice system not available. Please install audio dependencies.")
            return
            
        if not self.voice_loaded:
            self._load_voice()
        
        if not self.voice_loaded or not hasattr(self, 'ContinuousConversation'):
            self.add_message(get_character()["name"], "Voice module not available for continuous conversation.")
            return
            
        if self.continuous_active:
            # Stop continuous conversation
            if self.continuous_conversation:
                self.continuous_conversation.stop()
            self.continuous_active = False
            self.conv_label.config(text="")
            self.add_message(get_character()["name"], "Continuous conversation stopped. Use text input or Ctrl+Shift+V for voice.")
        else:
            # Start continuous conversation
            self.continuous_conversation = self.ContinuousConversation(self.process)
            self.continuous_conversation.start()
            self.continuous_active = True
            self.conv_label.config(text="🎙️ Continuous")
            self.add_message(get_character()["name"], "Continuous conversation started. Just start talking! Press Ctrl+Shift+T to stop.")

    def setup_system_tray(self):
        """Setup system tray icon"""
        pystray = _try_import_pystray()
        if not pystray:
            print("System tray not available (missing dependencies)")
            return
            
        try:
            # Create a simple icon
            icon_image = self.create_tray_icon()
            
            # Create menu items
            menu_items = [
                pystray.MenuItem("Show", self.show_window),
                pystray.MenuItem("Hide", self.hide_window),
                pystray.MenuItem("Hotkeys", self.show_hotkeys_tray),
                pystray.MenuItem("Start Launcher", self.start_launcher),
                pystray.MenuItem("Exit", self.quit_app)
            ]
            
            # Create tray icon
            self.tray_icon = pystray.Icon("Serena", icon_image, "Serena AI", menu_items)
            
            # Start tray icon in separate thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            print("System tray enabled")
            
        except Exception as e:
            print(f"Could not setup system tray: {e}")
    
    def setup_agent_system(self):
        """Setup the background agent system"""
        try:
            from agents import get_agent_manager
            self.agent_manager = get_agent_manager()
            # Start the scheduler for scheduled tasks
            self.agent_manager.start_scheduler()
            print("Agent system initialized with scheduler")
        except Exception as e:
            print(f"Could not setup agent system: {e}")
            self.agent_manager = None
    
    def setup_visual_assets(self):
        """Setup visual assets (avatars, icons, backgrounds)"""
        self.visual_assets = {}
        images_dir = Path(__file__).parent / "images"
        
        if not IMAGETK_AVAILABLE:
            print("ImageTk not available - visual assets disabled")
            return
        
        try:
            # Load avatars
            avatar_dir = images_dir / "avatars"
            self.visual_assets["serena_avatar"] = ImageTk.PhotoImage(Image.open(avatar_dir / "serena_avatar.png"))
            self.visual_assets["astrid_avatar"] = ImageTk.PhotoImage(Image.open(avatar_dir / "astrid_avatar.png"))
            
            # Load icons
            icon_dir = images_dir / "icons"
            icon_files = {
                "agent": "agent_icon.png",
                "media": "media_icon.png", 
                "server": "server_icon.png",
                "photo": "photo_icon.png",
                "chat": "chat_icon.png",
                "settings": "settings_icon.png"
            }
            
            for icon_name, icon_file in icon_files.items():
                icon_path = icon_dir / icon_file
                if icon_path.exists():
                    self.visual_assets[f"{icon_name}_icon"] = ImageTk.PhotoImage(Image.open(icon_path))
            
            # Load backgrounds
            bg_dir = images_dir / "backgrounds"
            self.visual_assets["serena_background"] = Image.open(bg_dir / "serena_background.png")
            self.visual_assets["astrid_background"] = Image.open(bg_dir / "astrid_background.png")
            
            print("Visual assets loaded successfully")
            
        except Exception as e:
            print(f"Could not load visual assets: {e}")
            self.visual_assets = {}

    def create_tray_icon(self):
        """Create a simple icon for the system tray"""
        try:
            # Use current character's theme color
            theme = get_character_theme()
            char_color = theme["tray_icon_color"]
            char_initial = get_character()["name"][0]  # First letter of character name
            
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), color=char_color)
            dc = ImageDraw.Draw(image)
            
            # Draw character initial in the center
            dc.text((24, 15), char_initial, fill='white', font=None)
            
            return image
        except Exception as e:
            print(f"Could not create tray icon: {e}")
            # Return a simple colored rectangle as fallback
            return Image.new('RGB', (64, 64), color='#ff80ab')

    def build_chat_ui(self, mode_result, is_startup: bool = True):
        # ── TOP BAR ────────────────────────────────────────
        top_bar = tk.Frame(self.chat_frame, bg=self.current_theme["primary_bg"])
        top_bar.pack(fill=tk.X, padx=10, pady=(10, 0))

        self.input_method = tk.StringVar(value="text")
        
        # Mode indicator
        self.mode_label = tk.Label(top_bar, text=f"Mode: {mode_result}", fg=self.current_theme["accent_color"],
                                   bg=self.current_theme["primary_bg"], font=self.current_theme["header_font"])
        self.mode_label.pack(side=tk.LEFT)
        
        # Status indicator
        self.status_label = tk.Label(top_bar, text="● Ready", fg=self.current_theme["status_ready"],
                                    bg=self.current_theme["primary_bg"], font=("Segoe UI", 9))
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))

        # Input method radio buttons
        tk.Radiobutton(top_bar, text="Text", variable=self.input_method,
                       value="text", fg=self.current_theme["text_color"], bg=self.current_theme["primary_bg"],
                       selectcolor=self.current_theme["secondary_bg"], font=("Segoe UI", 9),
                       command=self.toggle_input).pack(side=tk.RIGHT)
        tk.Radiobutton(top_bar, text="Voice", variable=self.input_method,
                       value="voice", fg=self.current_theme["text_color"], bg=self.current_theme["primary_bg"],
                       selectcolor=self.current_theme["secondary_bg"], font=("Segoe UI", 9),
                       command=self.toggle_input).pack(side=tk.RIGHT, padx=(0, 10))
        
        # Voice output toggle
        self.voice_output_var = tk.BooleanVar(value=True)
        tk.Checkbutton(top_bar, text="🔊", variable=self.voice_output_var,
                       fg=self.current_theme["text_color"], bg=self.current_theme["primary_bg"], 
                       selectcolor=self.current_theme["secondary_bg"],
                       font=("Segoe UI", 9), command=self.toggle_voice_output).pack(side=tk.RIGHT, padx=(0, 10))
        
        # Continuous conversation indicator
        self.conv_label = tk.Label(top_bar, text="", fg="#ff9800",
                                   bg=self.current_theme["primary_bg"], font=("Segoe UI", 9))
        self.conv_label.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Agent status indicator with icon
        if IMAGETK_AVAILABLE and hasattr(self, 'visual_assets') and "agent_icon" in self.visual_assets:
            self.agent_label = tk.Label(top_bar, image=self.visual_assets["agent_icon"],
                                       bg=self.current_theme["primary_bg"])
        else:
            self.agent_label = tk.Label(top_bar, text="🤖 Agents", fg=self.current_theme["accent_color"],
                                       bg=self.current_theme["primary_bg"], font=("Segoe UI", 9))
        self.agent_label.pack(side=tk.RIGHT, padx=(0, 10))

        # ── CHAT DISPLAY ────────────────────────────────────
        self.chat = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            bg=self.current_theme["secondary_bg"],
            fg=self.current_theme["text_color"],
            font=self.current_theme["body_font"],
            state="disabled"
        )
        self.chat.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # ── BOTTOM INPUT AREA ───────────────────────────────
        self.bottom = tk.Frame(self.chat_frame, bg=self.current_theme["primary_bg"])
        self.bottom.pack(fill=tk.X, padx=10, pady=10)

        self.entry = tk.Entry(
            self.bottom,
            bg=self.current_theme["secondary_bg"],
            fg=self.current_theme["text_color"],
            font=("Segoe UI", 12),
            insertbackground=self.current_theme["text_color"]
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.entry.bind("<Return>", self.send_text)

        self.send_btn = tk.Button(
            self.bottom,
            text="Send",
            command=self.send_text,
            bg=self.current_theme["button_color"],
            fg="white",
            font=("Segoe UI", 10, "bold")
        )
        self.send_btn.pack(side=tk.RIGHT)

        self.listen_btn = tk.Button(
            self.bottom,
            text="🎤  Listen",
            command=self.send_voice,
            bg=self.current_theme["button_color"],
            fg="white",
            font=("Segoe UI", 12, "bold"),
            height=2
        )
        self.listen_btn.pack(fill=tk.X)
        self.listen_btn.pack_forget()  # hidden by default

        # ── APPROVAL STATUS INDICATOR (Phase 1) ───────────────
        self.approval_status_frame = tk.Frame(self.chat_frame, bg=self.current_theme["primary_bg"])
        self.approval_status_label = tk.Label(
            self.approval_status_frame,
            text="",
            bg=self.current_theme["primary_bg"],
            fg=self.current_theme["text_color"],
            font=("Segoe UI", 9)
        )
        self.approval_status_label.pack(pady=5)
        self.approval_status_frame.pack_forget()  # hidden by default

        # Character-specific welcome message (only once on startup)
        if is_startup:
            char = get_character()
            if self.current_character == "serena":
                welcome_msg = f"Hey trainer! I'm ready for our adventure!\n{mode_result}\nI can help with coding, web search, generate images and GIFs, and much more.\nI'll automatically switch modes based on what we talk about - just start chatting!"
            else:
                welcome_msg = f"Welcome, friend. I am Astrid, ready to assist you.\n{mode_result}\nI can help with coding, web search, generate images and GIFs, and much more.\nI'll automatically switch modes based on what we talk about - just start chatting."
            
            self.add_message(char["name"], welcome_msg)

    def show_window(self, icon=None, item=None):
        """Show the main window"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide_window(self, icon=None, item=None):
        """Hide the main window"""
        self.root.withdraw()

    def show_hotkeys_tray(self, icon=None, item=None):
        """Show hotkeys from tray"""
        self.show_window()
        self.show_hotkeys()

    def start_launcher(self, icon=None, item=None):
        """Start the launcher script for global hotkey access"""
        try:
            import subprocess
            launcher_path = Path(__file__).parent / "launcher.py"
            if os.name == 'nt':
                subprocess.Popen([sys.executable, str(launcher_path)], 
                              creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([sys.executable, str(launcher_path)], 
                              start_new_session=True)
            char_name = get_character()["name"]
            self.add_message(char_name, "Launcher started! Press Ctrl+Alt+S from anywhere to launch.")
        except Exception as e:
            char_name = get_character()["name"]
            self.add_message(char_name, f"Failed to start launcher: {e}")

    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        self.root.quit()
        if icon:
            icon.stop()

    def toggle_input(self):
        if self.input_method.get() == "text":
            self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
            self.send_btn.pack(side=tk.RIGHT)
            self.listen_btn.pack_forget()
        else:
            self.entry.pack_forget()
            self.send_btn.pack_forget()
            self.listen_btn.pack(fill=tk.X)

    def toggle_voice_output(self):
        """Toggle voice output on/off"""
        self.voice_output_enabled = self.voice_output_var.get()
        status = "enabled" if self.voice_output_enabled else "disabled"
        char_name = get_character()["name"]
        self.add_message(char_name, f"Voice output {status}")

    def _load_voice(self):
        if not self.voice_loaded and self.voice_available:
            try:
                from voice_enhanced import listen, speak, ContinuousConversation
                self.listen = listen
                self.speak = speak
                self.ContinuousConversation = ContinuousConversation
                self.voice_loaded = True
            except Exception as e:
                print(f"Voice system not available: {e}")
                self.voice_available = False
                self.voice_loaded = False

    def _speak(self, text, emotion=None):
        char_name = get_character()["name"]
        print(f"{char_name}:", text)
        if self.voice_output_enabled and self.voice_available:
            self._load_voice()
            if self.speak:
                try:
                    self.speak(text, emotion=emotion, context="chat", character=self.current_character)
                except Exception as e:
                    print(f"Voice output error: {e}")
                    # Continue without voice - don't crash
    
    # ==================== PHASE 1 APPROVAL WORKFLOW UI ====================
    
    def show_approval_dialog(self, operation: str, details: str, danger_level: str = "DANGEROUS") -> bool:
        """
        Show approval dialog for dangerous operations.
        
        Phase 1: Human-in-the-loop approval workflow UI.
        
        Args:
            operation: The operation requiring approval
            details: Human-readable description
            danger_level: The danger level of the operation
            
        Returns:
            True if approved, False if denied
        """
        # Create approval dialog window
        approval_window = tk.Toplevel(self.root)
        approval_window.title(f"Approval Required - {danger_level}")
        approval_window.geometry("500x300")
        approval_window.configure(bg=self.current_theme["primary_bg"])
        approval_window.transient(self.root)
        approval_window.grab_set()
        
        # Center the window
        approval_window.update_idletasks()
        x = (self.root.winfo_x() + self.root.winfo_width() // 2) - (approval_window.winfo_width() // 2)
        y = (self.root.winfo_y() + self.root.winfo_height() // 2) - (approval_window.winfo_height() // 2)
        approval_window.geometry(f"+{x}+{y}")
        
        # Make modal
        approval_window.focus_set()
        
        # Approval result
        approval_result = {"approved": False}
        
        def approve():
            approval_result["approved"] = True
            approval_window.destroy()
        
        def deny():
            approval_result["approved"] = False
            approval_window.destroy()
        
        # UI elements
        tk.Label(
            approval_window,
            text=f"⚠️ {danger_level} OPERATION",
            font=("Segoe UI", 14, "bold"),
            bg=self.current_theme["primary_bg"],
            fg="#ff6b6b" if danger_level == "DANGEROUS" else "#ffd93d"
        ).pack(pady=20)
        
        tk.Label(
            approval_window,
            text=f"Operation: {operation}",
            font=("Segoe UI", 11),
            bg=self.current_theme["primary_bg"],
            fg=self.current_theme["text_color"]
        ).pack(pady=5)
        
        tk.Label(
            approval_window,
            text=f"Details: {details}",
            font=("Segoe UI", 10),
            bg=self.current_theme["primary_bg"],
            fg=self.current_theme["text_color"],
            wraplength=450
        ).pack(pady=10, padx=20)
        
        tk.Label(
            approval_window,
            text="Do you want to approve this operation?",
            font=("Segoe UI", 11, "bold"),
            bg=self.current_theme["primary_bg"],
            fg=self.current_theme["text_color"]
        ).pack(pady=10)
        
        button_frame = tk.Frame(approval_window, bg=self.current_theme["primary_bg"])
        button_frame.pack(pady=20)
        
        tk.Button(
            button_frame,
            text="✓ Approve",
            command=approve,
            bg="#51cf66",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            width=12
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame,
            text="✗ Deny",
            command=deny,
            bg="#ff6b6b",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            width=12
        ).pack(side=tk.LEFT, padx=10)
        
        # Wait for window to close
        self.root.wait_window(approval_window)
        
        return approval_result["approved"]
    
    def show_approval_status(self, message: str):
        """
        Show approval status indicator in the chat interface.
        
        Phase 1: Approval status notification.
        
        Args:
            message: The status message to display
        """
        self.approval_status_frame.pack(pady=5)
        self.approval_status_label.config(text=f"⚠️ {message}")
        
        # Auto-hide after 5 seconds
        self.root.after(5000, self.hide_approval_status)
    
    def hide_approval_status(self):
        """Hide the approval status indicator."""
        self.approval_status_frame.pack_forget()
        self.approval_status_label.config(text="")

    def add_message(self, sender, text):
        self.chat.configure(state="normal")
        if sender == "You":
            self.chat.insert(tk.END, f"You: {text}\n\n", "user")
        else:
            char_name = get_character()["name"]
            self.chat.insert(tk.END, f"{char_name}: {text}\n\n", "character")
        
        # Apply theme colors
        self.chat.tag_config("user", foreground=self.current_theme["user_message_color"])
        self.chat.tag_config("character", foreground=self.current_theme["character_message_color"])
        self.chat.configure(state="disabled")
        self.chat.see(tk.END)
        
        # Update mode label if mode changed
        if hasattr(self, 'mode_label'):
            from ai import get_current_mode, get_mode_config
            current_mode = get_current_mode()
            mode_config = get_mode_config(current_mode)
            self.mode_label.config(text=f"Mode: {mode_config['label']}")

    def process(self, user_input):
        if not user_input:
            return
        self.add_message("You", user_input)
        self.status_label.config(text="● Processing...", fg="#ff9800")

        def run():
            from router import route
            # Pass agent_manager to router for Phase 3 integration
            response = route(user_input, agent_manager=self.agent_manager)
            char_name = get_character()["name"]

            if response == "__SHUTDOWN__":
                self.add_message(char_name, "Shutting down... goodnight.")
                self._speak("Shutting down. Goodnight.")
                self.root.after(1500, self.root.destroy)
                return

            self.add_message(char_name, response)
            self.status_label.config(text="● Ready", fg="#00e676")
            
            # Detect emotion in response for voice output
            if self.voice_loaded:
                from voice_enhanced import detect_emotion
                response_emotion = detect_emotion(response)
                self.status_label.config(text="● Speaking...", fg="#ff4081")
                self._speak(response, emotion=response_emotion)
                self.status_label.config(text="● Ready", fg="#00e676")
            else:
                self._speak(response)

        threading.Thread(target=run, daemon=True).start()

    def send_text(self, event=None):
        user_input = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        self.process(user_input)

    def send_voice(self):
        self._load_voice()
        char_name = get_character()["name"]
        if not self.listen:
            self.add_message(char_name, "Voice module failed to load.")
            return

        self.listen_btn.config(text="Listening...", state="disabled")
        self.root.update()

        def run():
            user_input, emotion = self.listen(duration=6, emotion_detection=True)
            self.root.after(0, lambda: self.listen_btn.config(text="🎤  Listen", state="normal"))
            if user_input:
                self.root.after(0, lambda: self.process(user_input))
            else:
                self.root.after(0, lambda: self.add_message(char_name, "I didn't catch that."))

        threading.Thread(target=run, daemon=True).start()

    def __del__(self):
        """Cleanup when app is destroyed"""
        if self.hotkeys_enabled:
            try:
                keyboard.unhook_all_hotkeys()
            except:
                pass
        pystray = _try_import_pystray()
        if pystray and hasattr(self, 'tray_icon'):
            try:
                self.tray_icon.stop()
            except:
                pass


if __name__ == "__main__":
    root = tk.Tk()
    app = SerenaApp(root)
    root.mainloop()