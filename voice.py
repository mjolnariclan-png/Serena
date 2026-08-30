import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import speech_recognition as sr
import tempfile
import time
import edge_tts
import asyncio
import pygame

VOICE = "en-US-JennyNeural"

# Init pygame mixer once at module load
pygame.mixer.init()

# --------------------
# 🔊 SPEAK
# --------------------

async def _speak_async(text):
    communicate = edge_tts.Communicate(text, VOICE)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        path = f.name

    await communicate.save(path)

    # Play with pygame (works on Linux, Windows, Mac)
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)


def speak(text):
    print("Serena:", text)
    asyncio.run(_speak_async(text))


# --------------------
# 🎤 LISTEN
# --------------------

def listen(duration=3):
    fs = 16000

    try:
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()

        if audio is None or len(audio) == 0:
            return ""

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            write(f.name, fs, audio)
            wav_path = f.name

        recognizer = sr.Recognizer()

        with sr.AudioFile(wav_path) as source:
            recognizer.adjust_for_ambient_noise(source)
            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(audio_data)
        return text.lower().strip()

    except sr.UnknownValueError:
        return ""

    except Exception as e:
        print("Listen error:", e)
        return ""
