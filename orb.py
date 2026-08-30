import tkinter as tk
from router import route
from voice import speak, listen

def start_orb():
    root = tk.Tk()
    root.title("Serena")

    root.geometry("120x120+100+100")
    root.overrideredirect(True)
    root.attributes("-topmost", True)

    canvas = tk.Canvas(root, width=120, height=120, bg="black", highlightthickness=0)
    canvas.pack()

    orb = canvas.create_oval(20, 20, 100, 100, fill="cyan")

    def ask():
        user_input = listen()

        print("DEBUG INPUT:", user_input)

        if not user_input:
            speak("I didn't hear anything.")
            return

        response = route(user_input)

        # 📴 SHUTDOWN HANDLER
        if response == "__SHUTDOWN__":
            speak("Goodnight. Shutting down now.")
            root.after(1500, root.destroy)  # let voice finish
            return

        speak(response)

    canvas.tag_bind(orb, "<Button-1>", lambda e: ask())

    root.mainloop()