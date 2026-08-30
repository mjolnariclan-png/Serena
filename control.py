import pyautogui
import os


def open_app(app_name):
    if "chrome" in app_name:
        os.startfile("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")

    elif "code" in app_name:
        os.system("code")


def type_text(text):
    pyautogui.write(text)