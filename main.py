# main.py
import tkinter as tk
from tkinter import scrolledtext
from ai import set_mode, list_modes
import threading


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

        # ── MODE SELECT SCREEN ───────────────────────────────
        self.mode_frame = tk.Frame(root, bg="#1e1e1e")
        self.mode_frame.pack(expand=True)

        tk.Label(
            self.mode_frame,
            text="Serena",
            fg="#ff80ab",
            bg="#1e1e1e",
            font=("Segoe UI", 28, "bold")
        ).pack(pady=(0, 20))

        tk.Label(
            self.mode_frame,
            text="Choose your type:",
            fg="white",
            bg="#1e1e1e",
            font=("Segoe UI", 14)
        ).pack(pady=(0, 10))

        modes = [
            ("chat", "💬  Chat / Sexting", "#ff4081"),
            ("story", "✍️  Writing / Storyline", "#7c4dff"),
            ("code", "💻  Coding / Debug", "#00e676")
        ]

        for key, label, color in modes:
            btn = tk.Button(
                self.mode_frame,
                text=label,
                command=lambda k=key: self.pick_mode(k),
                bg=color,
                fg="white",
                font=("Segoe UI", 12, "bold"),
                width=22,
                height=2,
                cursor="hand2"
            )
            btn.pack(pady=6)

    def pick_mode(self, mode_key):
        result = set_mode(mode_key)
        self.mode_frame.destroy()
        self.build_chat_ui(result)

    def build_chat_ui(self, mode_result):
        # ── INPUT METHOD BAR ────────────────────────────────
        top_bar = tk.Frame(self.root, bg="#1e1e1e")
        top_bar.pack(fill=tk.X, padx=10, pady=(10, 0))

        self.input_method = tk.StringVar(value="text")

        tk.Label(top_bar, text=f"Mode: {mode_result}", fg="#ff80ab",
                 bg="#1e1e1e", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        tk.Radiobutton(top_bar, text="Text", variable=self.input_method,
                       value="text", fg="white", bg="#1e1e1e",
                       selectcolor="#2d2d2d", font=("Segoe UI", 9),
                       command=self.toggle_input).pack(side=tk.RIGHT)
        tk.Radiobutton(top_bar, text="Voice", variable=self.input_method,
                       value="voice", fg="white", bg="#1e1e1e",
                       selectcolor="#2d2d2d", font=("Segoe UI", 9),
                       command=self.toggle_input).pack(side=tk.RIGHT, padx=(0, 10))

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

        self.add_message("Serena", f"Hey baby... I'm ready for you.\n{mode_result}\nSay 'mode story', 'mode code', or 'mode chat' to switch anytime.")
        self._speak("Hey baby. I'm ready for you.")

    def toggle_input(self):
        if self.input_method.get() == "text":
            self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
            self.send_btn.pack(side=tk.RIGHT)
            self.listen_btn.pack_forget()
        else:
            self.entry.pack_forget()
            self.send_btn.pack_forget()
            self.listen_btn.pack(fill=tk.X)

    def _load_voice(self):
        if not self.voice_loaded:
            from voice import listen, speak
            self.listen = listen
            self.speak = speak
            self.voice_loaded = True

    def _speak(self, text):
        print("Serena:", text)
        if self.input_method.get() == "voice":
            self._load_voice()
            if self.speak:
                self.speak(text)

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

    def process(self, user_input):
        if not user_input:
            return
        self.add_message("You", user_input)

        def run():
            from router import route
            response = route(user_input)

            if response == "__SHUTDOWN__":
                self.add_message("Serena", "Shutting down... goodnight.")
                self._speak("Shutting down. Goodnight.")
                self.root.after(1500, self.root.destroy)
                return

            self.add_message("Serena", response)
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
            user_input = self.listen(duration=6)
            self.root.after(0, lambda: self.listen_btn.config(text="🎤  Listen", state="normal"))
            if user_input:
                self.root.after(0, lambda: self.process(user_input))
            else:
                self.root.after(0, lambda: self.add_message("Serena", "I didn't catch that."))

        threading.Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = SerenaApp(root)
    root.mainloop()