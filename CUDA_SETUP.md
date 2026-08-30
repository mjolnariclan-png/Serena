# Setting Up CUDA for GPU-Accelerated Image Generation

This guide will help you set up CUDA for much faster image generation (seconds instead of minutes).

## Step 1: Check if You Have an NVIDIA GPU

First, verify you have an NVIDIA GPU that supports CUDA:

```bash
nvidia-smi
```

If this command works and shows your GPU information, you have NVIDIA GPU support.

If you get "command not found", you may not have an NVIDIA GPU or the drivers aren't installed.

## Step 2: Install NVIDIA Drivers (if needed)

If `nvidia-smi` doesn't work:

1. Go to: https://www.nvidia.com/Download/index.aspx
2. Select your GPU model and Windows version
3. Download and install the latest drivers
4. Restart your computer
5. Run `nvidia-smi` again to verify

## Step 3: Install CUDA Toolkit

Download and install CUDA Toolkit:

1. Go to: https://developer.nvidia.com/cuda-downloads
2. Select:
   - Operating System: Windows
   - Architecture: x86_64
   - Version: 11 or 12 (match your PyTorch requirements)
   - Installer Type: exe (local)

3. Download and install (this is large, ~3GB)
4. During installation, choose "Express" installation

## Step 4: Install cuDNN

1. Go to: https://developer.nvidia.com/cudnn (requires NVIDIA developer account)
2. Download cuDNN that matches your CUDA version
3. Extract the zip file
4. Copy the contents to your CUDA toolkit directory (usually `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.x\`)

## Step 5: Install PyTorch with CUDA Support

**Important:** First uninstall the CPU version:

```bash
pip uninstall torch torchvision torchaudio
```

Then install the CUDA version. Check https://pytorch.org/get-started/locally/ for the latest command.

For CUDA 11.8:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

For CUDA 12.1:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## Step 6: Verify CUDA Installation

Test that PyTorch can see your GPU:

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"GPU count: {torch.cuda.device_count()}")
print(f"GPU name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'No GPU'}")
```

Run this and you should see CUDA available: True

## Step 7: Configure Serena for GPU Mode

Edit `F:\Serena\image_gen.py`:

Change the startup command from CPU mode to GPU mode:

```python
# Remove CPU-specific flags
# OLD: python launch.py --api --listen --skip-torch-cuda-test --no-half --use-cpu all
# NEW: python launch.py --api --listen
```

Update the `start_sd_webui()` function:

```python
def start_sd_webui():
    """Start Stable Diffusion WebUI in API mode with GPU support."""
    if is_sd_running():
        return True
    
    try:
        # Create modified launch script for API mode (GPU enabled)
        api_script = os.path.join(SD_WEBUI_PATH, "launch_api.bat")
        with open(api_script, 'w') as f:
            f.write(f'@echo off\n')
            f.write(f'cd /d "%~dp0"\n')
            f.write(f'call venv\\Scripts\\activate\n')
            f.write(f'python launch.py --api --listen\n')  # GPU mode - no CPU flags
        
        # Start the API server
        subprocess.Popen(api_script, shell=True)
        
        # Wait for server to start
        print("Starting Stable Diffusion WebUI API with GPU acceleration...")
        for i in range(30):  # GPU mode starts faster
            time.sleep(1)
            if is_sd_running():
                print("Stable Diffusion WebUI API is ready! (GPU accelerated)")
                return True
        
        print("Failed to start Stable Diffusion WebUI API")
        return False
        
    except Exception as e:
        print(f"Error starting SD WebUI: {e}")
        return False
```

## Step 8: Download Stable Diffusion Model

Same as CPU setup - download a model and place it in:
`stable-diffusion-webui/models/Stable-diffusion/`

Recommended: Stable Diffusion 1.5 from https://huggingface.co/runwayml/stable-diffusion-v1-5

## Step 9: Test GPU Image Generation

Start Serena and try:
- "Generate an image of a sunset"

With GPU, this should take 5-15 seconds instead of 2-5 minutes!

## Performance Comparison

| Mode | Image Generation Time | Quality |
|------|---------------------|---------|
| CPU  | 2-5 minutes         | Same    |
| GPU  | 5-15 seconds        | Same    |

GPU is 10-20x faster for image generation.

## Troubleshooting

### "CUDA out of memory"
- Reduce image size: `generate_image(prompt, width=384, height=384)`
- Reduce batch size or steps
- Close other GPU-intensive applications

### "CUDA not available" after installation
- Restart your computer
- Check NVIDIA drivers are updated
- Verify CUDA toolkit is in PATH
- Try reinstalling PyTorch with correct CUDA version

### Wrong CUDA version error
- Check your CUDA version: `nvcc --version`
- Install PyTorch matching that version
- Or install the CUDA version that matches your PyTorch

## Quick Setup Script

I can create a setup script to automate some of this if you want. Just let me know!

## Current Status Check

Run this to check your current setup:

```python
import torch
import platform

print("=== System Info ===")
print(f"OS: {platform.system()} {platform.release()}")
print(f"Python: {platform.python_version()}")

print("\n=== PyTorch Info ===")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU count: {torch.cuda.device_count()}")
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
else:
    print("No CUDA GPU available - will use CPU mode")
```

This will tell you exactly what you have and what you need to install.