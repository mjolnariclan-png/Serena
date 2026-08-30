"""
CUDA/GPU Diagnostic Script for Serena
Run this to check your current GPU/CUDA setup
"""

import sys
import subprocess
import platform

def check_nvidia_gpu():
    """Check if NVIDIA GPU is available"""
    print("=== Checking NVIDIA GPU ===")
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✓ NVIDIA GPU detected")
            # Extract GPU info
            lines = result.stdout.split('\n')
            for line in lines:
                if 'GPU' in line or 'CUDA' in line:
                    print(f"  {line.strip()}")
            return True
        else:
            print("✗ NVIDIA GPU not detected or drivers not installed")
            return False
    except FileNotFoundError:
        print("✗ nvidia-smi command not found - no NVIDIA GPU or drivers")
        return False
    except Exception as e:
        print(f"✗ Error checking GPU: {e}")
        return False

def check_cuda_installation():
    """Check if CUDA toolkit is installed"""
    print("\n=== Checking CUDA Toolkit ===")
    try:
        result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✓ CUDA toolkit found")
            for line in result.stdout.split('\n'):
                if 'release' in line.lower() or 'version' in line.lower():
                    print(f"  {line.strip()}")
            return True
        else:
            print("✗ CUDA toolkit not found")
            return False
    except FileNotFoundError:
        print("✗ nvcc command not found - CUDA toolkit not installed")
        return False
    except Exception as e:
        print(f"✗ Error checking CUDA: {e}")
        return False

def check_pytorch():
    """Check PyTorch installation and CUDA support"""
    print("\n=== Checking PyTorch ===")
    try:
        import torch
        print(f"✓ PyTorch version: {torch.__version__}")
        print(f"  CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"  CUDA version: {torch.version.cuda}")
            print(f"  GPU count: {torch.cuda.device_count()}")
            if torch.cuda.device_count() > 0:
                print(f"  GPU name: {torch.cuda.get_device_name(0)}")
                print(f"  GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            return True
        else:
            print("  ✗ PyTorch cannot access CUDA - using CPU mode")
            return False
    except ImportError:
        print("✗ PyTorch not installed")
        return None
    except Exception as e:
        print(f"✗ Error checking PyTorch: {e}")
        return False

def main():
    """Run all checks"""
    print("=" * 50)
    print("Serena CUDA/GPU Diagnostic Tool")
    print("=" * 50)
    
    gpu_available = check_nvidia_gpu()
    cuda_installed = check_cuda_installation()
    pytorch_status = check_pytorch()
    
    print("\n" + "=" * 50)
    print("=== SUMMARY ===")
    print("=" * 50)
    
    if gpu_available and cuda_installed and pytorch_status:
        print("✓ Everything is ready for GPU acceleration!")
        print("  Serena will use GPU for image generation")
        print("  Expected performance: 5-15 seconds per image")
    elif gpu_available and not cuda_installed:
        print("⚠ NVIDIA GPU found but CUDA toolkit not installed")
        print("  Follow CUDA_SETUP.md to install CUDA toolkit")
    elif gpu_available and cuda_installed and not pytorch_status:
        print("⚠ GPU and CUDA found but PyTorch not configured for CUDA")
        print("  Reinstall PyTorch with CUDA support:")
        print("  pip uninstall torch torchvision torchaudio")
        print("  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    elif not gpu_available:
        print("✗ No NVIDIA GPU detected")
        print("  Serena will use CPU mode for image generation")
        print("  Expected performance: 2-5 minutes per image")
        print("  Consider using cloud image generation for better performance")
    else:
        print("⚠ Mixed configuration - check individual results above")
    
    print("\nFor detailed setup instructions, see:")
    print("  - CUDA_SETUP.md (GPU setup)")
    print("  - SETUP_IMAGES.md (model download)")

if __name__ == "__main__":
    main()