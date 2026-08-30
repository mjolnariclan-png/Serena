import os
import datetime
import subprocess

def local_response(prompt: str):
    p = prompt.lower().strip()

    if p in ["open chrome", "launch chrome", "start chrome"]:
        subprocess.Popen(["google-chrome"])
        return "Opening Chrome."

    if p in ["open code", "launch code", "start vs code", "open vs code"]:
        subprocess.Popen(["code"])
        return "Opening VS Code."

    if any(x in p for x in ["what time is it", "current time", "tell me the time"]):
        return datetime.datetime.now().strftime("It's %I:%M %p on %B %d, %Y.")

    if p.startswith("type "):
        import pyautogui
        pyautogui.write(p[5:])
        return "Typed it out for you."

    return None