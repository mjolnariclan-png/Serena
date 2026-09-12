"""
Hotword Detection Module - Detects "Hey Serena" wake word
Uses WebRTC VAD for voice activity detection
"""

import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import speech_recognition as sr
import tempfile
import time
import threading

class HotwordDetector:
    """Detects wake word 'Hey Serena'"""
    
    def __init__(self, wake_word="hey serena", callback=None):
        self.wake_word = wake_word.lower()
        self.callback = callback
        self.listening = False
        self.fs = 16000
        
    def start_listening(self):
        """Start continuous listening for wake word"""
        self.listening = True
        threading.Thread(target=self._listen_loop, daemon=True).start()
        print(f"Listening for wake word: '{self.wake_word}'")
        
    def stop_listening(self):
        """Stop listening for wake word"""
        self.listening = False
        print("Stopped listening for wake word")
        
    def _listen_loop(self):
        """Main listening loop"""
        while self.listening:
            try:
                # Listen for speech
                audio = sd.rec(int(3 * self.fs), samplerate=self.fs, channels=1, dtype='int16')
                sd.wait()
                
                if audio is None or len(audio) == 0:
                    time.sleep(0.5)
                    continue
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    write(f.name, self.fs, audio)
                    wav_path = f.name
                
                # Recognize speech
                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_path) as source:
                    recognizer.adjust_for_ambient_noise(source)
                    audio_data = recognizer.record(source)
                
                try:
                    text = recognizer.recognize_google(audio_data).lower()
                    print(f"Heard: {text}")
                    
                    # Check for wake word
                    if self.wake_word in text:
                        print(f"Wake word detected: '{self.wake_word}'")
                        if self.callback:
                            self.callback()
                            
                except sr.UnknownValueError:
                    pass  # No speech detected
                except Exception as e:
                    print(f"Recognition error: {e}")
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Listening error: {e}")
                time.sleep(1)

# Simple wake word detection that can be integrated
def detect_wake_word(audio_data, wake_word="hey serena"):
    """Check if wake word is in audio data"""
    try:
        recognizer = sr.Recognizer()
        text = recognizer.recognize_google(audio_data).lower()
        return wake_word in text
    except:
        return False