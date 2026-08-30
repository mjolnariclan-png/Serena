"""
Switch Serena between CPU and GPU mode for image generation
Run this to toggle between CPU and GPU acceleration
"""

import os
import sys

def switch_to_gpu_mode():
    """Configure Serena for GPU mode"""
    print("Switching Serena to GPU mode...")
    
    image_gen_path = "image_gen.py"
    
    try:
        with open(image_gen_path, 'r') as f:
            content = f.read()
        
        # Replace CPU launch command with GPU command
        cpu_command = 'python launch.py --api --listen --skip-torch-cuda-test --no-half --use-cpu all'
        gpu_command = 'python launch.py --api --listen'
        
        if cpu_command in content:
            content = content.replace(cpu_command, gpu_command)
            
            with open(image_gen_path, 'w') as f:
                f.write(content)
            
            print("✓ Successfully switched to GPU mode")
            print("  Image generation will use GPU acceleration")
            print("  Make sure you have CUDA properly installed")
            print("  Run 'python check_cuda.py' to verify setup")
            return True
        else:
            print("✓ Already in GPU mode (or configuration not found)")
            return True
            
    except Exception as e:
        print(f"✗ Error switching to GPU mode: {e}")
        return False

def switch_to_cpu_mode():
    """Configure Serena for CPU mode"""
    print("Switching Serena to CPU mode...")
    
    image_gen_path = "image_gen.py"
    
    try:
        with open(image_gen_path, 'r') as f:
            content = f.read()
        
        # Replace GPU launch command with CPU command
        gpu_command = 'python launch.py --api --listen'
        cpu_command = 'python launch.py --api --listen --skip-torch-cuda-test --no-half --use-cpu all'
        
        if gpu_command in content:
            content = content.replace(gpu_command, cpu_command)
            
            with open(image_gen_path, 'w') as f:
                f.write(content)
            
            print("✓ Successfully switched to CPU mode")
            print("  Image generation will use CPU (slower)")
            print("  No GPU or CUDA required")
            return True
        else:
            print("✓ Already in CPU mode (or configuration not found)")
            return True
            
    except Exception as e:
        print(f"✗ Error switching to CPU mode: {e}")
        return False

def check_current_mode():
    """Check current mode configuration"""
    image_gen_path = "image_gen.py"
    
    try:
        with open(image_gen_path, 'r') as f:
            content = f.read()
        
        if '--use-cpu all' in content:
            return "CPU"
        elif '--api --listen' in content and '--use-cpu' not in content:
            return "GPU"
        else:
            return "Unknown"
    except:
        return "Unknown"

def main():
    """Main function"""
    print("=" * 50)
    print("Serena GPU Mode Switcher")
    print("=" * 50)
    
    current_mode = check_current_mode()
    print(f"Current mode: {current_mode}")
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == 'gpu':
            switch_to_gpu_mode()
        elif mode == 'cpu':
            switch_to_cpu_mode()
        else:
            print("Usage: python switch_gpu_mode.py [gpu|cpu]")
    else:
        print("\nUsage: python switch_gpu_mode.py [gpu|cpu]")
        print("  gpu  - Switch to GPU acceleration (requires CUDA)")
        print("  cpu  - Switch to CPU mode (no GPU required)")
        print("\nOr run 'python check_cuda.py' to see your GPU status")

if __name__ == "__main__":
    main()