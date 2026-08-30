"""
Setup script for Serena's dependencies.
Run this to install all required packages.
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"[OK] Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"[FAIL] Failed to install {package}")
        return False

def main():
    """Install all required packages."""
    print("=" * 50)
    print("Installing Serena Dependencies")
    print("=" * 50)
    
    packages = [
        "ollama",
        "sounddevice",
        "numpy",
        "scipy",
        "SpeechRecognition",
        "edge-tts",
        "pygame",
        "pyautogui",
        "requests",
        "beautifulsoup4",
        "Pillow"
    ]
    
    results = []
    for package in packages:
        print(f"\nInstalling {package}...")
        result = install_package(package)
        results.append(result)
    
    print("\n" + "=" * 50)
    print(f"Installation Results: {sum(results)}/{len(results)} successful")
    print("=" * 50)
    
    if all(results):
        print("[OK] All packages installed successfully!")
        print("\nYou can now run Serena with: python main.py")
        return 0
    else:
        print("[FAIL] Some packages failed to install")
        print("You may need to install them manually")
        return 1

if __name__ == "__main__":
    sys.exit(main())