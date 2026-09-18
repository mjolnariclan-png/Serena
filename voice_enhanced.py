# Lazy imports for voice system to avoid crashes
try:
    import sounddevice as sd
    import numpy as np
    from scipy.io.wavfile import write
    import speech_recognition as sr
    import edge_tts
    import pygame
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VOICE_AVAILABLE = True
except Exception as e:
    print(f"Voice system dependencies not available: {e}")
    VOICE_AVAILABLE = False

import tempfile
import time
import asyncio
import threading
import random
from characters import get_character, get_character_voice

# Default voice (will be overridden by character configuration)
VOICE = "en-US-JennyNeural"

# Init pygame mixer once at module load if available
if VOICE_AVAILABLE:
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except Exception as e:
        print(f"Warning: Audio output initialization failed: {e}")
        VOICE_AVAILABLE = False

# Emotion analysis
if VOICE_AVAILABLE:
    sentiment_analyzer = SentimentIntensityAnalyzer()
else:
    sentiment_analyzer = None

# Default emotion-based voice variants (will be overridden by character config)
EMOTION_VOICES = {
    "happy": "en-US-JennyNeural",
    "sad": "en-US-GuyNeural", 
    "angry": "en-US-EmmaNeural",
    "excited": "en-US-AriaNeural",
    "calm": "en-US-JennyNeural",
    "flirty": "en-US-AriaNeural"
}

# Available voices
AVAILABLE_VOICES = {
    "Jenny": "en-US-JennyNeural",
    "Aria": "en-US-AriaNeural",
    "Guy": "en-US-GuyNeural",
    "Emma": "en-US-EmmaNeural",
    "Sara": "en-US-SaraNeural",
    "Tony": "en-US-TonyNeural",
    "Nova": "en-US-NovaNeural",
    "Sonora": "en-US-SonoraNeural",
    "JennyMultilingual": "en-US-JennyMultilingualNeural",
    "Ava": "en-US-AvaMultilingualNeural",
    "AvaMultilingual": "en-US-AvaMultilingualNeural",
    "Michelle": "en-US-MichelleNeural",
    "Roger": "en-US-RogerNeural",
    "Steffan": "en-US-SteffanNeural",
    "Ana": "en-US-AnaNeural",
    "Andrew": "en-US-AndrewNeural",
    "Brian": "en-US-BrianNeural",
    "Christopher": "en-US-ChristopherNeural",
    "Eric": "en-US-EricNeural",
    "Jacob": "en-US-JacobNeural",
    "Davis": "en-US-DavisNeural",
    "Jane": "en-US-JaneNeural",
    "Jason": "en-US-JasonNeural",
    "Nancy": "en-US-NancyNeural",
    "Amber": "en-US-AmberNeural",
    "AnaMultilingual": "en-US-AnaMultilingualNeural",
    "Brandon": "en-US-BrandonNeural",
    "ChristopherNeural": "en-US-ChristopherNeural",
    "Corinne": "en-US-CorinneNeural",
    "DavisMultilingual": "en-US-DavisMultilingualNeural",
    "Elizabeth": "en-US-ElizabethNeural",
    "EricMultilingual": "en-US-EricMultilingualNeural",
    "GuyMultilingual": "en-US-GuyMultilingualNeural",
    "JacobMultilingual": "en-US-JacobMultilingualNeural",
    "JasonMultilingual": "en-US-JasonMultilingualNeural",
    "MichelleMultilingual": "en-US-MichelleMultilingualNeural",
    "NancyMultilingual": "en-US-NancyMultilingualNeural",
    "RogerMultilingual": "en-US-RogerMultilingualNeural",
    "SteffanMultilingual": "en-US-SteffanMultilingualNeural",
    "TonyMultilingual": "en-US-TonyMultilingualNeural"
}

# Current selected voice
current_voice = "en-US-JennyNeural"

def set_voice(voice_name):
    """Set the current voice"""
    global current_voice
    voice_name_lower = voice_name.lower()
    
    # Try to find matching voice
    for name, voice_id in AVAILABLE_VOICES.items():
        if voice_name_lower in name.lower():
            current_voice = voice_id
            return f"Voice changed to {name}"
    
    # Try direct voice ID match
    if voice_name in AVAILABLE_VOICES.values():
        current_voice = voice_name
        return f"Voice changed to {voice_name}"
    
    return f"Voice '{voice_name}' not found. Available voices: {', '.join(AVAILABLE_VOICES.keys())}"

def get_current_voice():
    """Get the current voice"""
    global current_voice
    return current_voice

def list_voices():
    """List all available voices"""
    return list(AVAILABLE_VOICES.keys())

def detect_emotion(text):
    """Detect emotion from text using sentiment analysis"""
    if not VOICE_AVAILABLE or not sentiment_analyzer:
        return "calm"
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

def get_character_voice_safe(character=None):
    """Safely get character voice configuration"""
    try:
        return get_character_voice(character)
    except:
        return {"default_voice": current_voice, "emotion_voices": EMOTION_VOICES}

def get_emotion_voice(emotion, context="chat", character=None):
    """Get appropriate voice based on emotion, context, and character"""
    # Get character-specific voice configuration
    voice_config = get_character_voice_safe(character)
    emotion_voices = voice_config.get("emotion_voices", EMOTION_VOICES)
    
    # For chat mode, use character-appropriate voice selection
    if context == "chat":
        if emotion in ["calm", "sad"]:
            return emotion_voices.get("flirty", emotion_voices.get("calm", EMOTION_VOICES["calm"]))
        elif emotion == "excited":
            return emotion_voices.get("excited", EMOTION_VOICES["excited"])
        else:
            return emotion_voices.get("happy", EMOTION_VOICES["happy"])
    else:
        return emotion_voices.get(emotion, emotion_voices.get("calm", EMOTION_VOICES["calm"]))

# --------------------
# 🔊 SPEAK (Enhanced)
# --------------------

async def _speak_async(text, emotion=None, context="chat", character=None):
    if not VOICE_AVAILABLE:
        return
        
    try:
        # Get character-specific voice configuration
        if character:
            voice_config = get_character_voice_safe(character)
            default_voice = voice_config.get("default_voice", current_voice)
        else:
            default_voice = current_voice
        
        # Use emotion-based voice if emotion specified, otherwise use default
        if emotion:
            voice = get_emotion_voice(emotion, context, character)
        else:
            voice = default_voice
        
        communicate = edge_tts.Communicate(text, voice)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            path = f.name

        await communicate.save(path)

        # Play with pygame (works on Linux, Windows, Mac)
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
    except Exception as e:
        print(f"Voice synthesis error: {e}")
        # Don't crash the application if voice fails


def speak(text, emotion=None, context="chat", character=None):
    if not VOICE_AVAILABLE:
        char_name = get_character(character)["name"] if character else "AI"
        print(f"{char_name} (text only):", text)
        return
        
    try:
        char_name = get_character(character)["name"] if character else "AI"
        print(f"{char_name}:", text)
        asyncio.run(_speak_async(text, emotion, context, character))
    except Exception as e:
        print(f"Voice output error: {e}")
        # Continue without voice - don't crash


# --------------------
# 🎤 LISTEN (Enhanced)
# --------------------

def listen(duration=3, emotion_detection=True):
    if not VOICE_AVAILABLE:
        return "", None
        
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
        if not VOICE_AVAILABLE:
            print("Continuous conversation not available - voice system not loaded")
            return
            
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