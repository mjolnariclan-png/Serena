import requests
import json
import os
import time
from pathlib import Path
from PIL import Image
import io
import base64
from image_gen import is_sd_running, start_sd_webui, SD_API_URL, OUTPUT_DIR

def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    Path(OUTPUT_DIR).mkdir(exist_ok=True)

def generate_frame(prompt: str, seed: int = None, width: int = 384, height: int = 384) -> Image.Image:
    """Generate a single frame for GIF using Stable Diffusion (CPU optimized)."""
    if not is_sd_running():
        if not start_sd_webui():
            raise Exception("Failed to start Stable Diffusion WebUI")
    
    payload = {
        "prompt": prompt,
        "steps": 12,  # Reduced steps for CPU
        "width": width,
        "height": height,
        "sampler_name": "Euler a",  # Fast sampler
        "cfg_scale": 7  # Lower CFG for speed
    }
    
    if seed is not None:
        payload["seed"] = seed
    
    response = requests.post(f"{SD_API_URL}/sdapi/v1/txt2img", json=payload)
    response.raise_for_status()
    
    result = response.json()
    image_data = base64.b64decode(result["images"][0])
    
    return Image.open(io.BytesIO(image_data))

def generate_gif(prompt: str, frames: int = 6, duration: int = 500, width: int = 384, height: int = 384) -> str:
    """
    Generate an animated GIF by creating multiple frames with slight variations.
    Optimized for CPU with fewer frames and smaller size.
    
    Args:
        prompt: The base prompt for image generation
        frames: Number of frames in the GIF (reduced for CPU)
        duration: Duration per frame in milliseconds
        width: Image width (reduced for CPU)
        height: Image height (reduced for CPU)
    
    Returns:
        Path to the generated GIF file
    """
    ensure_output_dir()
    
    try:
        print(f"Generating {frames} frames for GIF (CPU optimized)...")
        images = []
        
        # Generate frames with different seeds for variation
        for i in range(frames):
            print(f"Generating frame {i+1}/{frames}...")
            frame = generate_frame(prompt, seed=None, width=width, height=height)
            images.append(frame)
            time.sleep(0.3)  # Reduced delay between generations
        
        # Save as GIF
        timestamp = int(time.time())
        gif_path = os.path.join(OUTPUT_DIR, f"serena_gif_{timestamp}.gif")
        
        images[0].save(
            gif_path,
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=0,
            optimize=True
        )
        
        print(f"GIF saved to: {gif_path}")
        return f"GIF generated and saved to: {gif_path}\n(CPU mode - {frames} frames at {width}x{height})"
        
    except Exception as e:
        return f"Error generating GIF: {str(e)}"

def generate_morphing_gif(base_prompt: str, frames: int = 10, duration: int = 500) -> str:
    """
    Generate a GIF that morphs between two related concepts.
    
    Args:
        base_prompt: The starting concept
        frames: Number of frames
        duration: Duration per frame in milliseconds
    
    Returns:
        Path to the generated GIF file
    """
    ensure_output_dir()
    
    try:
        print(f"Generating morphing GIF with {frames} frames...")
        images = []
        
        # Create interpolation between prompts
        # This is a simple implementation - you could make it more sophisticated
        concepts = [
            base_prompt,
            f"{base_prompt}, stylized",
            f"{base_prompt}, artistic interpretation",
            f"{base_prompt}, abstract version",
            base_prompt  # Return to original
        ]
        
        frames_per_concept = frames // len(concepts)
        
        for concept in concepts:
            for i in range(frames_per_concept):
                print(f"Generating frame for: {concept}")
                frame = generate_frame(concept, seed=None)
                images.append(frame)
                time.sleep(0.3)
        
        timestamp = int(time.time())
        gif_path = os.path.join(OUTPUT_DIR, f"serena_morph_{timestamp}.gif")
        
        images[0].save(
            gif_path,
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=0,
            optimize=True
        )
        
        return f"Morphing GIF generated and saved to: {gif_path}"
        
    except Exception as e:
        return f"Error generating morphing GIF: {str(e)}"

def is_gif_request(text: str) -> bool:
    """Check if the user is requesting a GIF generation."""
    gif_keywords = [
        "generate gif", "generate a gif", "create a gif", "create gif",
        "make a gif", "make gif", "animated gif", "generate an animation",
        "create an animation", "make an animation"
    ]
    text_lower = text.lower().strip()
    return any(keyword in text_lower for keyword in gif_keywords)

def extract_gif_prompt(text: str) -> str:
    """Extract the GIF prompt from user text."""
    prefixes = [
        "generate a gif of", "create a gif of", "make a gif of",
        "generate an animated", "create an animated", "make an animated",
        "gif of", "animated"
    ]
    
    text_lower = text.lower()
    for prefix in prefixes:
        if text_lower.startswith(prefix):
            return text[len(prefix):].strip()
    
    return text.strip()
