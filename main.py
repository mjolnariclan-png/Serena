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

        # ── BUILD UI WITH CHARACTER TABS ────────────────────
        self.build_main_ui()
        
        # ── START DIRECTLY IN CHAT MODE ───────────────────────
        set_mode("chat")
        self.build_chat_ui("Chat / Adventure mode")
    
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
        """Build the main UI with character tabs"""
        # Character selection tabs
        tab_frame = tk.Frame(self.root, bg=self.current_theme["primary_bg"])
        tab_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Serena tab
        self.serena_tab = tk.Button(
            tab_frame,
            text="⚡ Serena",
            command=lambda: self.switch_character("serena"),
            bg=self.current_theme["button_color"] if self.current_character == "serena" else self.current_theme["secondary_bg"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.RAISED if self.current_character == "serena" else tk.FLAT
        )
        self.serena_tab.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Astrid tab  
        self.astrid_tab = tk.Button(
            tab_frame,
            text="🛡️ Astrid",
            command=lambda: self.switch_character("astrid"),
            bg=self.current_theme["button_color"] if self.current_character == "astrid" else self.current_theme["secondary_bg"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.RAISED if self.current_character == "astrid" else tk.FLAT
        )
        self.astrid_tab.pack(side=tk.LEFT, padx=5, pady=5)
        
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
            dashboard = self.agent_manager.generate_dashboard_report()
            self.add_message(get_character()["name"], f"Agent System Status:\n{dashboard}")
        except Exception as e:
            self.add_message(get_character()["name"], f"Error getting agent status: {e}")

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
            print("Agent system initialized")
        except Exception as e:
            print(f"Could not setup agent system: {e}")
            self.agent_manager = None

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
        
        # Agent status indicator
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
            response = route(user_input)
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