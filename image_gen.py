import requests
import json
import os
import subprocess
import time
import platform
from pathlib import Path

# Stable Diffusion WebUI API configuration
SD_API_URL = "http://127.0.0.1:7860"
SD_WEBUI_PATH = "stable-diffusion-webui"
OUTPUT_DIR = "generated_images"

# CPU-optimized default settings
DEFAULT_WIDTH = 384  # Reduced from 512 for CPU
DEFAULT_HEIGHT = 384  # Reduced from 512 for CPU
DEFAULT_STEPS = 15  # Reduced from 20 for CPU
DEFAULT_SAMPLER = "Euler a"  # Fast sampler for CPU
DEFAULT_CFG = 7  # Lower CFG scale for faster generation

def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    Path(OUTPUT_DIR).mkdir(exist_ok=True)

def is_sd_running():
    """Check if Stable Diffusion WebUI is running."""
    try:
        response = requests.get(f"{SD_API_URL}/sdapi/v1/sd-models", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_sd_webui():
    """Start Stable Diffusion WebUI in API mode."""
    if is_sd_running():
        return True
    
    if not os.path.exists(SD_WEBUI_PATH):
        print("Stable Diffusion WebUI directory not found.")
        return False

    try:
        # Start webui with API enabled and CPU optimization
        if platform.system() == "Windows":
            api_script = os.path.join(SD_WEBUI_PATH, "launch_api.bat")
            with open(api_script, 'w') as f:
                f.write('@echo off\n')
                f.write('cd /d "%~dp0"\n')
                f.write('python launch.py --api --listen --skip-python-version-check --skip-torch-cuda-test --no-half --use-cpu all\n')
            subprocess.Popen(api_script, shell=True)
        else:
            api_script = os.path.join(SD_WEBUI_PATH, "launch_api.sh")
            with open(api_script, 'w') as f:
                f.write('#!/usr/bin/env bash\n')
                f.write('cd "$(dirname "$0")"\n')
                f.write('export PIP_BREAK_SYSTEM_PACKAGES=1\n')
                f.write('python3 launch.py --api --listen --skip-python-version-check --skip-torch-cuda-test --no-half --use-cpu all\n')
            os.chmod(api_script, 0o755)
            subprocess.Popen([api_script])
        
        # Check if server starts up
        print("Starting Stable Diffusion WebUI API in CPU mode...")
        for i in range(5):
            time.sleep(1)
            if is_sd_running():
                print("Stable Diffusion WebUI API is ready!")
                return True
        
        print("Stable Diffusion WebUI is starting in the background or needs manual launch.")
        return False
        
    except Exception as e:
        print(f"Error starting SD WebUI: {e}")
        return False

def generate_image(prompt: str, negative_prompt: str = "", steps: int = None, width: int = None, height: int = None) -> str:
    """
    Generate an image using Stable Diffusion WebUI API.
    Optimized for CPU performance with faster settings.
    Returns the path to the generated image.
    """
    # Use defaults if not specified
    if steps is None:
        steps = DEFAULT_STEPS
    if width is None:
        width = DEFAULT_WIDTH
    if height is None:
        height = DEFAULT_HEIGHT
    
    ensure_output_dir()
    
    if not is_sd_running():
        if not start_sd_webui():
            return "Failed to start Stable Diffusion WebUI. Please check if it's installed correctly."
    
    try:
        print(f"Generating image (CPU optimized: {width}x{height}, {steps} steps)...")
        
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": steps,
            "width": width,
            "height": height,
            "sampler_name": DEFAULT_SAMPLER,  # Fast sampler good for CPU
            "cfg_scale": DEFAULT_CFG,  # Lower CFG for faster generation
            "seed": -1  # Random seed
        }
        
        print("Sending request to Stable Diffusion...")
        response = requests.post(f"{SD_API_URL}/sdapi/v1/txt2img", json=payload)
        response.raise_for_status()
        
        print("Processing image data...")
        result = response.json()
        
        # Save the image
        import base64
        image_data = base64.b64decode(result["images"][0])
        
        timestamp = int(time.time())
        image_path = os.path.join(OUTPUT_DIR, f"serena_gen_{timestamp}.png")
        
        with open(image_path, 'wb') as f:
            f.write(image_data)
        
        print(f"Image saved to: {image_path}")
        estimated_time = steps * 8  # Rough estimate for CPU
        return f"Image generated and saved to: {image_path}\n(CPU mode - {width}x{height}, {steps} steps - ~{estimated_time} seconds)"
        
    except requests.exceptions.RequestException as e:
        return f"Error generating image: {str(e)}. Make sure Stable Diffusion WebUI is running with API enabled."
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def is_image_request(text: str) -> bool:
    """Check if the user is requesting an image generation."""
    text_lower = text.lower().strip()
    
    # Negative filters - coding, file operations, web search, conversation, etc.
    if any(non_img in text_lower for non_img in [
        "create file", "create folder", "create directory", "create project",
        "write code", "generate code", "write a story", "tell a story",
        "write story", "open chrome", "open code", "system info", "what time", "what day"
    ]):
        return False
        
    explicit_patterns = [
        "generate image", "generate an image", "generate a picture", "generate picture",
        "create image", "create an image", "create a picture", "create picture",
        "make an image", "make a picture", "draw an image", "draw a picture",
        "draw me", "paint me", "draw a ", "paint a ", "picture of", "image of",
        "photo of", "illustration of", "render an image", "render a picture",
        "generate art", "generate wallpaper", "create wallpaper"
    ]
    if any(pat in text_lower for pat in explicit_patterns):
        return True
        
    image_nouns = ["image", "picture", "photo", "illustration", "painting", "drawing", "artwork", "wallpaper"]
    action_verbs = ["generate", "draw", "paint", "render"]
    
    has_noun = any(noun in text_lower for noun in image_nouns)
    has_verb = any(verb in text_lower for verb in action_verbs)
    
    return has_noun and has_verb

def extract_quality_settings(text: str) -> dict:
    """Extract quality settings from user text."""
    settings = {
        "width": DEFAULT_WIDTH,
        "height": DEFAULT_HEIGHT,
        "steps": DEFAULT_STEPS
    }
    
    text_lower = text.lower()
    
    # Check for high quality requests
    if any(word in text_lower for word in ["high quality", "hq", "best quality", "detailed"]):
        settings["width"] = 512
        settings["height"] = 512
        settings["steps"] = 25
    
    # Check for quick/low quality requests
    elif any(word in text_lower for word in ["quick", "fast", "low quality", "small"]):
        settings["width"] = 256
        settings["height"] = 256
        settings["steps"] = 10
    
    # Check for custom size
    if "512x512" in text_lower:
        settings["width"] = 512
        settings["height"] = 512
    elif "256x256" in text_lower:
        settings["width"] = 256
        settings["height"] = 256
    
    return settings

def extract_image_prompt(text: str) -> str:
    """Extract the image prompt from user text."""
    # Remove common prefixes
    prefixes = [
        "generate an image of", "generate a picture of", "create an image of",
        "create a picture of", "make an image of", "make a picture of",
        "draw", "paint", "generate", "create", "make"
    ]
    
    text_lower = text.lower()
    for prefix in prefixes:
        if text_lower.startswith(prefix):
            return text[len(prefix):].strip()
    
    return text.strip()
