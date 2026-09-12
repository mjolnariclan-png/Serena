import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import speech_recognition as sr
import tempfile
import time
import edge_tts
import asyncio
import pygame
import threading
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import random

VOICE = "en-US-JennyNeural"

# Init pygame mixer once at module load
pygame.mixer.init()

# Emotion analysis
sentiment_analyzer = SentimentIntensityAnalyzer()

# Emotion-based voice variants
EMOTION_VOICES = {
    "happy": "en-US-JennyNeural",
    "sad": "en-US-GuyNeural", 
    "angry": "en-US-EmmaNeural",
    "excited": "en-US-AriaNeural",
    "calm": "en-US-JennyNeural",
    "flirty": "en-US-AriaNeural"
}

def detect_emotion(text):
    """Detect emotion from text using sentiment analysis"""
    try:
        scores = sentiment_analyzer.polarity_scores(text)
        
        # Determine emotion based on scores
        if scores['compound'] >= 0.5:
            return "excited"
        elif scores['compound'] >= 0.1:
            return "happy"
        elif scores['compound'] <= -0.5:
            return "sad"
        elif scores['compound'] <= -0.1:
            return "angry"
        else:
            return "calm"
    except:
        return "calm"

def get_emotion_voice(emotion, context="chat"):
    """Get appropriate voice based on emotion and context"""
    # For chat mode, use flirty/happy voices more often
    if context == "chat":
        if emotion in ["calm", "sad"]:
            return EMOTION_VOICES["flirty"]
        elif emotion == "excited":
            return EMOTION_VOICES["excited"]
        else:
            return EMOTION_VOICES["happy"]
    else:
        return EMOTION_VOICES.get(emotion, EMOTION_VOICES["calm"])

# --------------------
# 🔊 SPEAK (Enhanced)
# --------------------

async def _speak_async(text, emotion=None, context="chat"):
    detected_emotion = emotion or detect_emotion(text)
    voice = get_emotion_voice(detected_emotion, context)
    
    communicate = edge_tts.Communicate(text, voice)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        path = f.name

    await communicate.save(path)

    # Play with pygame (works on Linux, Windows, Mac)
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)


def speak(text, emotion=None, context="chat"):
    print("Serena:", text)
    asyncio.run(_speak_async(text, emotion, context))


# --------------------
# 🎤 LISTEN (Enhanced)
# --------------------

def listen(duration=3, emotion_detection=True):
    fs = 16000

    try:
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()

        if audio is None or len(audio) == 0:
            return "", None

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            write(f.name, fs, audio)
            wav_path = f.name

        recognizer = sr.Recognizer()

        with sr.AudioFile(wav_path) as source:
            recognizer.adjust_for_ambient_noise(source)
            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(audio_data)
        text_lower = text.lower().strip()
        
        detected_emotion = None
        if emotion_detection:
            detected_emotion = detect_emotion(text_lower)
            
        return text_lower, detected_emotion

    except sr.UnknownValueError:
        return "", None

    except Exception as e:
        print("Listen error:", e)
        return "", None


# --------------------
# 🎙️ CONTINUOUS CONVERSATION
# --------------------

class ContinuousConversation:
    def __init__(self, process_callback, context="chat"):
        self.process_callback = process_callback
        self.context = context
        self.running = False
        self.conversation_active = False
        
    def start(self):
        """Start continuous conversation mode"""
        self.running = True
        self.conversation_active = True
        threading.Thread(target=self._conversation_loop, daemon=True).start()
        
    def stop(self):
        """Stop continuous conversation mode"""
        self.running = False
        self.conversation_active = False
        
    def _conversation_loop(self):
        """Main conversation loop"""
        while self.running:
            try:
                # Listen for user input
                user_text, emotion = listen(duration=5, emotion_detection=True)
                
                if user_text:
                    # Process the input through callback
                    response = self.process_callback(user_text)
                    
                    # Speak response with detected emotion
                    response_emotion = detect_emotion(response)
                    speak(response, emotion=response_emotion, context=self.context)
                    
                    # Small pause before next listen
                    time.sleep(1)
                else:
                    # No speech detected, wait before trying again
                    time.sleep(2)
                    
            except Exception as e:
                print(f"Conversation loop error: {e}")
                time.sleep(2)