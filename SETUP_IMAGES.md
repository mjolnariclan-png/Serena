# Setting Up Image Generation for Serena

Since you need image and GIF generation working, here's how to get Stable Diffusion running on your CPU-only system.

## Required Setup

### 1. Download Stable Diffusion Model

You need a model file. Here are the best options:

**Option A: Stable Diffusion 1.5 (Recommended for CPU)**
- Download from: https://huggingface.co/runwayml/stable-diffusion-v1-5
- Download the file: `v1-5-pruned-emaonly.safetensors`
- Place it in: `stable-diffusion-webui/models/Stable-diffusion/`

**Option B: Stable Diffusion 2.1**
- Download from: https://huggingface.co/stabilityai/sd-v2-1
- Download: `v2-1_768-ema-pruned.safetensors`
- Place it in: `stable-diffusion-webui/models/Stable-diffusion/`

### 2. Install Required Dependencies for Stable Diffusion

In the `stable-diffusion-webui` directory:

```bash
cd stable-diffusion-webui
pip install -r requirements.txt
```

### 3. Install PyTorch for CPU

Since you don't have CUDA GPU, install CPU-only PyTorch:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 4. Test Stable Diffusion WebUI

Manually test if it works:

```bash
cd stable-diffusion-webui
python launch.py --api --listen --skip-torch-cuda-test --no-half --use-cpu all
```

If this starts successfully, you should see something like:
```
Running on local URL: http://127.0.0.1:7860
```

### 5. Use Serena's Image Generation

Once Stable Diffusion WebUI is running, Serena can automatically:
- Start it if needed
- Generate images from your prompts
- Create GIFs
- Save everything to the `generated_images/` folder

## Usage Examples

After setup, try these commands in Serena:

### Image Generation
- "Generate an image of a beautiful sunset"
- "Create a picture of a cyberpunk city"
- "Draw a cute cat in space"

### GIF Generation  
- "Generate a GIF of a dancing robot"
- "Create an animated ocean wave"
- "Make a GIF of flowers blooming"

## Performance Notes

**CPU Mode Performance:**
- Image generation: 2-5 minutes per image (512x512)
- GIF generation: 10-20 minutes (depending on frames)
- System may be slow during generation

**Tips for Better Performance:**
- Use smaller images: `generate_image(prompt, width=256, height=256)`
- Reduce steps: `generate_image(prompt, steps=10)`
- Close other applications while generating
- Generate fewer GIF frames

## Troubleshooting

### "Model not found" error
- Make sure the model file is in the correct folder
- Check the filename matches exactly
- Try restarting Stable Diffusion WebUI

### "Out of memory" error
- Reduce image size to 256x256 or 384x384
- Close other programs
- Reduce steps to 10-15

### Very slow generation
- This is normal for CPU mode
- Consider using smaller images
- Reduce the number of GIF frames

## Alternative: Cloud Image Generation

If CPU mode is too slow, you can modify Serena to use cloud APIs:

Edit `image_gen.py` to add cloud generation:

```python
# Example for OpenAI DALL-E (requires API key)
import openai
openai.api_key = "your-api-key-here"

def generate_image_cloud(prompt):
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="512x512"
    )
    return response['data'][0]['url']
```

This would be much faster (seconds vs minutes) but requires an API key and internet connection.

## Current Status

Your Serena is now configured with:
- ✅ Explicit personality restored
- ✅ Image generation (CPU mode)
- ✅ GIF generation (CPU mode)  
- ✅ All other features working
- ⚠️ Needs Stable Diffusion model download to complete image setup

The explicit personality and all features are ready - you just need to download the model file to complete image generation setup.