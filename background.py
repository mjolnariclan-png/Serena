from voice import listen, speak
from router import route
from ai import set_mode, get_current_mode
import sys
import time

WAKE_WORD = "serena"

def run_background():
    # Default to chat mode on startup, but you can switch by voice
    set_mode("chat")
    speak("Hey.")

    while True:
        text = listen(duration=3)

        if not text:
            time.sleep(0.3)
            continue

        text = text.lower().strip()
        print("Heard:", text)

        # 🧠 WAKE WORD STATE
        if WAKE_WORD in text:
            speak("Yes?")

            command = listen(duration=5)

            if not command:
                speak("I didn't catch that.")
                continue

            command = command.lower().strip()
            response = route(command)

            print("DEBUG:", response)

            # 📴 SHUTDOWN
            if response == "__SHUTDOWN__":
                speak("Going offline.")
                time.sleep(1)
                sys.exit(0)

            speak(response)

        time.sleep(0.4)