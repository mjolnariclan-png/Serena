import sounddevice as sd
import numpy as np

def main():
    fs = 16000
    duration = 5

    print("Recording... speak now")

    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    print("Done. Audio shape:", audio.shape)
    print("Max volume:", np.max(audio))

if __name__ == "__main__":
    main()