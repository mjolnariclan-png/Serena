import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
from voice import speak


def on_exit(icon, item):
    icon.stop()


def create_image():
    image = Image.new('RGB', (64, 64), color=(0, 0, 0))
    dc = ImageDraw.Draw(image)
    dc.ellipse((10, 10, 54, 54), fill=(0, 120, 255))
    return image


def start_tray():
    icon = pystray.Icon("Serena")
    icon.icon = create_image()
    icon.menu = pystray.Menu(
        item("Say Hello", lambda: speak("Hello, I am Serena.")),
        item("Exit", on_exit)
    )
    icon.run()