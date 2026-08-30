# Serena - Your Personal AI Assistant

A fully-featured local AI assistant with female voice, conversation memory, web search, image generation, and coding assistance.

## Features

✨ **Core Capabilities:**
- 🎤 Voice input/output with female voice (Edge TTS)
- 💬 Natural conversation with context memory
- 🧠 Multiple AI modes: Chat, Story, Code
- 🔍 Web search integration
- 🎨 Image generation via Stable Diffusion
- 🎞️ GIF generation
- 💻 Coding assistance and code execution
- 🖥️ Local system commands (open apps, create files, etc.)
- 🌙 Background wake-word mode

## Quick Start

### 1. Install Dependencies

```bash
python setup_dependencies.py
```

This will install all required Python packages.

### 2. Run Serena

```bash
python main.py
```

### 3. Background Mode (Wake Word)

```bash
python background.py
```

Then say "Serena" to activate, followed by your command.

## Usage Examples

### Web Search
- "Search for Python tutorials"
- "What is the capital of France?"
- "Latest news about AI"

### Image Generation
- "Generate an image of a sunset over mountains"
- "Create a picture of a cyberpunk city"
- "Draw a cute cat in space"

### GIF Generation
- "Generate a GIF of a dancing robot"
- "Create an animated ocean wave"
- "Make a GIF of flowers blooming"

### Coding Assistance
- "Execute this code: ```python print('Hello')```"
- "Analyze file main.py"
- "Create project myapp src/main.py, src/utils.py"
- "Install package numpy"

### Local Commands
- "What time is it?"
- "Open Chrome"
- "Create file test.txt"
- "Create folder myproject"
- "Help" (see all capabilities)

### Mode Switching
- "Mode chat" - Conversational mode
- "Mode story" - Creative writing mode  
- "Mode code" - Coding assistance mode

## Project Structure

- `main.py` - GUI application entry point
- `ai.py` - AI model management and conversation memory
- `router.py` - Command routing and feature detection
- `voice.py` - Voice input/output (speech recognition + TTS)
- `web_search.py` - Web search functionality
- `image_gen.py` - Image generation via Stable Diffusion
- `gif_gen.py` - GIF generation
- `coding_helper.py` - Code execution and file operations
- `local_ai.py` - Local system commands
- `background.py` - Wake-word background mode
- `memory_chat.json` - Conversation memory for chat mode
- `generated_images/` - Output directory for images/GIFs

## Setup Requirements

### Stable Diffusion WebUI (Optional - for Image Generation)
The project includes Stable Diffusion WebUI as a submodule for image generation:

```bash
git submodule update --init --recursive
```

**Image Generation Options:**

1. **GPU Mode (Recommended)** - Fast (5-15 seconds per image)
   - Requires NVIDIA GPU with CUDA
   - See `CUDA_SETUP.md` for detailed setup
   - Run `python check_cuda.py` to check your GPU status
   - Run `python switch_gpu_mode.py gpu` to enable GPU mode

2. **CPU Mode (Default)** - Slow (2-5 minutes per image)
   - Works on any system
   - See `SETUP_IMAGES.md` for CPU setup
   - Run `python switch_gpu_mode.py cpu` to enable CPU mode

### Quick GPU Setup Check

Run this to see if you can use GPU acceleration:

```bash
python check_cuda.py
```

This will tell you:
- If you have an NVIDIA GPU
- If CUDA is installed
- If PyTorch can use your GPU
- What you need to install (if anything)

### Ollama
Serena uses Ollama for local AI models. Install from [ollama.ai](https://ollama.ai) and pull models:
```bash
ollama pull dolphin-llama3
ollama pull mistral  
ollama pull codellama
```

## Customization

### Voice
Edit `voice.py` to change the voice:
```python
VOICE = "en-US-JennyNeural"  # Change to other Edge TTS voices
```

### AI Personality
Edit the system prompts in `ai.py` to customize Serena's personality for each mode.

### Models
Add more modes in `ai.py` by extending the `MODES` dictionary.

## Troubleshooting

### Dependencies Not Installing
Run `python setup_dependencies.py` manually and check for errors.

### Voice Not Working
Ensure your microphone is set up correctly and test with `test_mic.py`.

### Image Generation Failing
Make sure Stable Diffusion WebUI is running with API enabled, or check that models are downloaded.

### Ollama Connection Issues
Ensure Ollama is running: `ollama serve`

## Development

### Testing
Run the feature tests:
```bash
python test_features.py
```

### Adding New Features
1. Create a new module in the project directory
2. Add import with try/except in `router.py` for optional dependencies
3. Add routing logic in the `route()` function
4. Update tests if needed

## Notes

- Serena is designed to be a local, privacy-focused assistant
- Web search uses DuckDuckGo (no API key required)
- All conversation memory is stored locally in JSON files
- Image generation requires a GPU for good performance
