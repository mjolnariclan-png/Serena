# main.py
import tkinter as tk
from tkinter import scrolledtext
from ai import set_mode, list_modes
import threading
import keyboard
import time
import pystray
from PIL import Image, ImageDraw
import sys
from pathlib import Path


class SerenaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Serena")
        self.root.geometry("700x600")
        self.root.configure(bg="#1e1e1e")

        # ── LAZY VOICE IMPORTS ───────────────────────────────
        self.voice_loaded = False
        self.listen = None
        self.speak = None

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

        # ── START DIRECTLY IN CHAT MODE ───────────────────────
        set_mode("chat")
        self.build_chat_ui("Chat / Sexting mode")

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
                'ctrl+shift+t': self.toggle_continuous_conversation
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
            print("  (Run launcher.py for Ctrl+Alt+S global startup)")
            
        except Exception as e:
            print(f"Could not setup hotkeys: {e}")
            self.hotkeys_enabled = False

    def toggle_voice_mode(self):
        """Toggle between text and voice input mode"""
        if hasattr(self, 'input_method'):
            current = self.input_method.get()
            new_mode = "voice" if current == "text" else "text"
            self.input_method.set(new_mode)
            self.toggle_input()
            self.add_message("Serena", f"Switched to {new_mode} mode")

    def clear_chat(self):
        """Clear the chat display"""
        if hasattr(self, 'chat'):
            self.chat.configure(state="normal")
            self.chat.delete(1.0, tk.END)
            self.chat.configure(state="disabled")
            self.add_message("Serena", "Chat cleared. Ready for new conversation.")

    def cycle_modes(self):
        """Cycle through available modes"""
        from ai import get_current_mode, MODES
        modes = list(MODES.keys())
        current = get_current_mode()
        current_index = modes.index(current)
        next_index = (current_index + 1) % len(modes)
        next_mode = modes[next_index]
        result = set_mode(next_mode)
        self.add_message("Serena", result)
        if hasattr(self, 'mode_label'):
            from ai import get_mode_config
            mode_config = get_mode_config(next_mode)
            self.mode_label.config(text=f"Mode: {mode_config['label']}")

    def quick_exit(self):
        """Quick exit with confirmation"""
        self.add_message("Serena", "Goodnight! Shutting down...")
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
• (Run launcher.py for Ctrl+Alt+S global startup)"""
        self.add_message("Serena", hotkey_info)

    def toggle_continuous_conversation(self):
        """Toggle continuous voice conversation mode"""
        if not self.voice_loaded:
            self._load_voice()
        
        if not self.ContinuousConversation:
            self.add_message("Serena", "Voice module not available for continuous conversation.")
            return
            
        if self.continuous_active:
            # Stop continuous conversation
            if self.continuous_conversation:
                self.continuous_conversation.stop()
            self.continuous_active = False
            self.conv_label.config(text="")
            self.add_message("Serena", "Continuous conversation stopped. Use text input or Ctrl+Shift+V for voice.")
        else:
            # Start continuous conversation
            self.continuous_conversation = self.ContinuousConversation(self.process)
            self.continuous_conversation.start()
            self.continuous_active = True
            self.conv_label.config(text="🎙️ Continuous")
            self.add_message("Serena", "Continuous conversation started. Just start talking! Press Ctrl+Shift+T to stop.")

    def setup_system_tray(self):
        """Setup system tray icon"""
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

    def create_tray_icon(self):
        """Create a simple icon for the system tray"""
        try:
            # Create a simple pink square with "S"
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), color='#ff80ab')
            dc = ImageDraw.Draw(image)
            
            # Draw "S" in the center
            dc.text((20, 15), "S", fill='white', font=None)
            
            return image
        except Exception as e:
            print(f"Could not create tray icon: {e}")
            # Return a simple colored rectangle as fallback
            return Image.new('RGB', (64, 64), color='#ff80ab')

    def build_chat_ui(self, mode_result):
        # ── TOP BAR ────────────────────────────────────────
        top_bar = tk.Frame(self.root, bg="#1e1e1e")
        top_bar.pack(fill=tk.X, padx=10, pady=(10, 0))

        self.input_method = tk.StringVar(value="text")
        
        # Mode indicator
        self.mode_label = tk.Label(top_bar, text=f"Mode: {mode_result}", fg="#ff80ab",
                                   bg="#1e1e1e", font=("Segoe UI", 10, "bold"))
        self.mode_label.pack(side=tk.LEFT)
        
        # Status indicator
        self.status_label = tk.Label(top_bar, text="● Ready", fg="#00e676",
                                    bg="#1e1e1e", font=("Segoe UI", 9))
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))

        # Input method radio buttons
        tk.Radiobutton(top_bar, text="Text", variable=self.input_method,
                       value="text", fg="white", bg="#1e1e1e",
                       selectcolor="#2d2d2d", font=("Segoe UI", 9),
                       command=self.toggle_input).pack(side=tk.RIGHT)
        tk.Radiobutton(top_bar, text="Voice", variable=self.input_method,
                       value="voice", fg="white", bg="#1e1e1e",
                       selectcolor="#2d2d2d", font=("Segoe UI", 9),
                       command=self.toggle_input).pack(side=tk.RIGHT, padx=(0, 10))
        
        # Voice output toggle
        self.voice_output_var = tk.BooleanVar(value=True)
        tk.Checkbutton(top_bar, text="🔊", variable=self.voice_output_var,
                       fg="white", bg="#1e1e1e", selectcolor="#2d2d2d",
                       font=("Segoe UI", 9), command=self.toggle_voice_output).pack(side=tk.RIGHT, padx=(0, 10))
        
        # Continuous conversation indicator
        self.conv_label = tk.Label(top_bar, text="", fg="#ff9800",
                                   bg="#1e1e1e", font=("Segoe UI", 9))
        self.conv_label.pack(side=tk.RIGHT, padx=(0, 10))

        # ── CHAT DISPLAY ────────────────────────────────────
        self.chat = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            bg="#2d2d2d",
            fg="white",
            font=("Segoe UI", 11),
            state="disabled"
        )
        self.chat.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # ── BOTTOM INPUT AREA ───────────────────────────────
        self.bottom = tk.Frame(self.root, bg="#1e1e1e")
        self.bottom.pack(fill=tk.X, padx=10, pady=10)

        self.entry = tk.Entry(
            self.bottom,
            bg="#3c3c3c",
            fg="white",
            font=("Segoe UI", 12),
            insertbackground="white"
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.entry.bind("<Return>", self.send_text)

        self.send_btn = tk.Button(
            self.bottom,
            text="Send",
            command=self.send_text,
            bg="#007acc",
            fg="white",
            font=("Segoe UI", 10, "bold")
        )
        self.send_btn.pack(side=tk.RIGHT)

        self.listen_btn = tk.Button(
            self.bottom,
            text="🎤  Listen",
            command=self.send_voice,
            bg="#007acc",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            height=2
        )
        self.listen_btn.pack(fill=tk.X)
        self.listen_btn.pack_forget()  # hidden by default

        self.add_message("Serena", f"Hey baby... I'm ready for you.\n{mode_result}\nI can help with coding, web search, generate images and GIFs, and much more.\nI'll automatically switch modes based on what we talk about - just start chatting!")
        self._speak("Hey baby. I'm ready for you.")

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
            subprocess.Popen([sys.executable, str(launcher_path)], 
                          creationflags=subprocess.CREATE_NEW_CONSOLE)
            self.add_message("Serena", "Launcher started! Press Ctrl+Alt+S from anywhere to launch Serena.")
        except Exception as e:
            self.add_message("Serena", f"Failed to start launcher: {e}")

    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        self.root.quit()
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
        self.add_message("Serena", f"Voice output {status}")

    def _load_voice(self):
        if not self.voice_loaded:
            from voice_enhanced import listen, speak, ContinuousConversation
            self.listen = listen
            self.speak = speak
            self.ContinuousConversation = ContinuousConversation
            self.voice_loaded = True

    def _speak(self, text, emotion=None):
        print("Serena:", text)
        if self.voice_output_enabled:
            self._load_voice()
            if self.speak:
                self.speak(text, emotion=emotion, context="chat")

    def add_message(self, sender, text):
        self.chat.configure(state="normal")
        if sender == "You":
            self.chat.insert(tk.END, f"You: {text}\n\n", "user")
        else:
            self.chat.insert(tk.END, f"Serena: {text}\n\n", "serena")
        self.chat.tag_config("user", foreground="#4fc3f7")
        self.chat.tag_config("serena", foreground="#ff80ab")
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

            if response == "__SHUTDOWN__":
                self.add_message("Serena", "Shutting down... goodnight.")
                self._speak("Shutting down. Goodnight.")
                self.root.after(1500, self.root.destroy)
                return

            self.add_message("Serena", response)
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
        if not self.listen:
            self.add_message("Serena", "Voice module failed to load.")
            return

        self.listen_btn.config(text="Listening...", state="disabled")
        self.root.update()

        def run():
            user_input, emotion = self.listen(duration=6, emotion_detection=True)
            self.root.after(0, lambda: self.listen_btn.config(text="🎤  Listen", state="normal"))
            if user_input:
                self.root.after(0, lambda: self.process(user_input))
            else:
                self.root.after(0, lambda: self.add_message("Serena", "I didn't catch that."))

        threading.Thread(target=run, daemon=True).start()

    def __del__(self):
        """Cleanup when app is destroyed"""
        if self.hotkeys_enabled:
            try:
                keyboard.unhook_all_hotkeys()
            except:
                pass
        if hasattr(self, 'tray_icon'):
            try:
                self.tray_icon.stop()
            except:
                pass


if __name__ == "__main__":
    root = tk.Tk()
    app = SerenaApp(root)
    root.mainloop()