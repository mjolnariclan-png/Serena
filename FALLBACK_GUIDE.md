# Serena Setup Guide for CPU-Only Systems

Since your system doesn't have CUDA GPU support, here's how to get Serena working with the features available:

## ✅ What Works Right Now

All of these features work without GPU:

- **Voice I/O** - Female voice responses and speech recognition
- **Conversation** - Natural AI conversation with memory
- **Web Search** - Search any topic online
- **Coding Help** - Code execution, file operations, debugging
- **Local Commands** - Open apps, check time, create files/folders
- **Multiple Modes** - Chat, Story, and Code personalities

## ⚠️ Image Generation Limitations

Image generation requires Stable Diffusion, which needs:

### Option 1: CPU Mode (Slow but Works)
```bash
cd stable-diffusion-webui
python launch.py --api --listen --skip-torch-cuda-test
```

This will be very slow (minutes per image) but functional.

### Option 2: Use Cloud Alternatives
You can modify Serena to use cloud image APIs instead:
- Add API keys for services like DALL-E, Midjourney, or Stable Diffusion Cloud
- This would be faster than CPU mode

### Option 3: Skip Image Generation
Simply don't use image commands. Serena will suggest alternatives:
- "Generate an image of X" → She'll offer to search for X instead
- "Create a picture of Y" → She'll help you find references

## 🚀 Quick Start (No Image Generation)

1. Install dependencies:
```bash
python setup_dependencies.py
```

2. Run Serena:
```bash
python main.py
```

3. Try these commands:
- "What can you do?"
- "Search for Python tutorials"
- "What time is it?"
- "Execute this code: ```python print('Hello')```"
- "Open Chrome"

## 🔧 Setting Up Stable Diffusion (Optional)

If you really want image generation:

1. Download a model:
   - Visit https://huggingface.co/models
   - Download a Stable Diffusion model (e.g., "runwayml/stable-diffusion-v1-5")
   - Place it in `stable-diffusion-webui/models/Stable-diffusion/`

2. Run WebUI in CPU mode:
```bash
cd stable-diffusion-webui
python launch.py --api --listen --skip-torch-cuda-test
```

3. Keep this running and start Serena in another terminal

## 💡 Alternative: Cloud Image Generation

You could modify `image_gen.py` to use cloud services:

Example for OpenAI DALL-E:
```python
import openai
openai.api_key = "your-key-here"

def generate_image_cloud(prompt):
    response = openai.Image.create(prompt=prompt, n=1, size="512x512")
    return response['data'][0]['url']
```

This would be much faster than CPU mode.

## 🎯 Recommended Approach

For now, I recommend:
1. Use Serena for all the features that work without GPU
2. Skip image generation or use web search as fallback
3. If you get a GPU later, image generation will work automatically

 Serena is still incredibly useful even without image generation!