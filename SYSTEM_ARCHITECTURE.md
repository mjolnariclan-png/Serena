# Serena System Architecture

## Complete Component Overview

```
Serena
│
├── Core AI
├── Serena / Astrid character system
├── Memory
├── Voice
├── Vision
├── Image generation
├── Web search
│
├── Agent System
│   ├── Base Agent
│   ├── Agent Manager
│   ├── Common
│   ├── Media Agent
│   ├── Server Agent
│   ├── Photo Agent
│   └── Development Agent
│
├── Agentic Executor
├── Agentic Tools
├── Permission System
├── Router
│
├── GUI / Visual System
│   ├── Themes
│   ├── Avatars
│   ├── Backgrounds
│   └── Icons
│
└── Tests
```

## Core AI

### Description
The foundational AI processing system that handles all language model interactions, context management, and intelligent response generation.

### Components
- **AI Processing** (`ai.py`): Core text generation, memory integration, mode switching
- **Local AI** (`local_ai.py`): Fallback deterministic responses and basic file handling
- **Ollama Integration**: Local model connection and chat completion
- **System Prompts**: Character-specific instruction templates
- **Context Management**: Conversation history and memory loading

### Features
- Character-aware text generation
- Mode-specific system prompts
- Memory integration for context continuity
- Local model support (Ollama)
- Graceful fallback to local responses

---

## Serena / Astrid Character System

### Description
Dual-character system with distinct personalities, themes, voices, and memories. Each character maintains separate contexts and behaviors.

### Components
- **Character Configuration** (`characters.py`): Data-driven character definitions
- **Theme System**: Visual themes per character (colors, fonts, styling)
- **Voice Configuration**: Character-specific voice settings and emotions
- **Memory System**: Separate conversation memory per character
- **Lore & Backstory**: Rich character backgrounds and personality traits

### Characters

#### Serena (Pokémon-inspired)
- **Identity**: Pokémon-inspired AI Companion
- **Personality**: Bubbly, enthusiastic, flirty, supportive
- **Theme**: Bright pink (#ff80ab), playful colors
- **Voice**: en-US-JennyNeural (energetic)
- **Speaking Style**: Uses "trainer", exclamation points, Pokémon references
- **Modes**: Chat/Adventure, Story/Creative Writing, Code/Debug Adventure, Agentic/Quest Mode

#### Astrid (Viking/Norse-inspired)
- **Identity**: Viking/Norse-inspired AI Companion
- **Personality**: Grounded, wise, fiercely loyal, earthy
- **Theme**: Dark Nordic (#8b9dc3), earthier colors
- **Voice**: en-US-SonoraNeural (deeper, measured)
- **Speaking Style**: Calm, Norse metaphors, wisdom-focused
- **Modes**: Chat/Hall, Saga/Storytelling, Code/Craft, Agentic/Expedition

### Features
- Character switching with complete state isolation
- Character-specific system prompts and memories
- Dynamic theme application
- Separate voice configurations
- Mode-specific behavior per character

---

## Memory

### Description
Persistent conversation memory system that maintains context across sessions and modes.

### Components
- **Memory Files**: JSON-based storage per character and mode
- **Memory Loading**: Context restoration on startup
- **Memory Management**: Automatic context pruning and organization
- **System Message Integration**: Character identity embedded in memory

### Memory Structure
```
memory_chat.json          # General conversation memory
memory_story.json         # Creative writing/roleplay memory
memory_code.json          # Coding assistance memory
memory_agentic.json       # Task execution memory
memory_chat_astrid.json   # Astrid-specific chat memory
memory_story_astrid.json  # Astrid-specific story memory
memory_code_astrid.json   # Astrid-specific code memory
memory_agentic_astrid.json # Astrid-specific agentic memory
```

### Features
- Character-separated memory to prevent context mixing
- Mode-specific memory for different conversation types
- Automatic system message updates for character identity
- Persistent storage across sessions
- Memory capacity management

---

## Voice

### Description
Optional voice input/output system with character-specific voice configurations and emotion handling.

### Components
- **Voice Enhancement** (`voice_enhanced.py`): Core voice system with character support
- **Speech Recognition**: Microphone input using SpeechRecognition and sounddevice
- **Text-to-Speech**: Edge TTS for voice output
- **Character Voices**: Different voices and emotion mappings per character
- **Emotion Detection**: VADER sentiment analysis for emotional responses

### Features
- Character-specific voice configurations
- Emotion-based voice variations
- Graceful degradation when audio unavailable
- Microphone input with automatic speech recognition
- Text-to-speech output with rate/pitch control
- Error handling that doesn't crash the application

### Voice Configurations
- **Serena**: en-US-JennyNeural, rate 170, energetic emotion mapping
- **Astrid**: en-US-SonoraNeural, rate 150, calm emotion mapping

---

## Vision

### Description
Image analysis and computer vision capabilities for understanding visual content.

### Components
- **Image Processing**: PIL-based image manipulation and analysis
- **Image Understanding**: AI model integration for image description
- **Visual Context**: Integration of visual information into conversations

### Features
- Image file reading and processing
- Visual content analysis
- Image-to-text conversion
- Visual context integration

---

## Image Generation

### Description
AI-powered image and GIF generation for creative content creation.

### Components
- **Image Generation API**: Integration with image generation services
- **GIF Generation**: Animated content creation
- **Prompt Engineering**: Text-to-image prompt optimization
- **Style Control**: Artistic style and parameter adjustments

### Features
- Text-to-image generation
- GIF creation from prompts
- Style and parameter customization
- Creative prompt enhancement

---

## Web Search

### Description
Web search integration for real-time information retrieval and research.

### Components
- **Search Integration** (`router.py`): DuckDuckGo HTML search implementation
- **Content Extraction**: BeautifulSoup for web content parsing
- **Browser Integration**: Automatic browser opening for results
- **Search Queries**: Intelligent query formulation

### Features
- Real-time web search via DuckDuckGo
- Content extraction and summarization
- Automatic browser result display
- Search result integration into conversations

---

## Agent System

### Description
Background specialized agents for automated tasks and system maintenance with permission-based safety.

### Components

#### Base Agent (`agents/base_agent.py`)
- **Purpose**: Foundation class for all specialized agents
- **Features**: Permission system, safety rules, activity logging, error handling
- **Safety**: Never-delete rules, permission checking, operation verification

#### Agent Manager (`agents/agent_manager.py`)
- **Purpose**: Coordinates and manages multiple specialized agents
- **Features**: Agent registration, task execution, status monitoring, dashboard
- **Scheduler**: Background periodic task execution

#### Common (`agents/common/`)
- **Purpose**: Shared utilities and helper functions
- **Features**: File operations, shell commands, logging, error handling

#### Media Agent (`agents/media/agent.py`)
- **Purpose**: Organize media files and manage Jellyfin library
- **Features**: Media scanning, file identification, renaming, sorting, Jellyfin refresh
- **Safety**: Never delete, never overwrite, move uncertain items to Unsorted

#### Server Agent (`agents/server/agent.py`)
- **Purpose**: Monitor system health and perform maintenance
- **Features**: Disk space monitoring, service checking, update detection, maintenance reports
- **Safety**: No auto-reboots, check before operations, log everything

#### Photo Agent (`agents/photos/agent.py`)
- **Purpose**: Organize photos by date and detect duplicates
- **Features**: Date-based organization, EXIF extraction, duplicate detection, file type detection
- **Safety**: Hash-based duplicate detection, never delete, separate unsorted folder

#### Development Agent (Planned)
- **Purpose**: Assist with development tasks and project management
- **Features**: Code testing, git operations, project monitoring, automated builds
- **Safety**: Repository permissions, backup before changes

### Features
- Permission-based access control
- Rule-based safety constraints
- Comprehensive activity logging
- Error handling without system crashes
- Agent coordination and scheduling
- Dashboard and status reporting

---

## Agentic Executor

### Description
Advanced task execution system for complex, multi-step operations and autonomous task completion.

### Components
- **Task Planning**: Break down complex requests into executable steps
- **Step Execution**: Sequential execution of planned operations
- **Error Recovery**: Automatic error handling and retry logic
- **Progress Tracking**: Real-time progress updates and status reporting

### Features
- Complex task decomposition
- Autonomous step execution
- Error recovery and retries
- Progress monitoring
- Human-in-the-loop for critical operations

---

## Agentic Tools

### Description
Specialized tools and utilities for agent operations and task execution.

### Components
- **File Operations**: Safe file reading, writing, moving, copying
- **Shell Commands**: Controlled command execution with permissions
- **Git Operations**: Version control integration
- **Web Tools**: HTTP requests, API calls, web scraping
- **System Tools**: Process management, system monitoring

### Features
- Permission-based tool access
- Safe file operations
- Controlled command execution
- Version control integration
- Web API connectivity

---

## Permission System

### Description
Granular permission system for controlling agent and tool access to system resources.

### Components
- **Permission Definitions**: Directory and command access rules
- **Permission Checking**: Runtime permission validation
- **Rule Enforcement**: Safety rule application and enforcement
- **Audit Logging**: Permission usage tracking

### Features
- Directory-based read/write permissions
- Command execution permissions
- Safety rule enforcement
- Comprehensive audit logging
- Agent-specific permission sets

---

## Router

### Description
Command routing and feature detection system that interprets user requests and routes to appropriate handlers.

### Components
- **Command Analysis**: Natural language command interpretation
- **Feature Detection**: Identify user intent and required features
- **Routing Logic**: Direct requests to appropriate handlers
- **Character Context**: Maintain character awareness in routing

### Features
- Natural language command understanding
- Mode detection and switching
- Character context preservation
- Feature integration (search, coding, images, etc.)
- Agent system command routing

### Routed Features
- Character switching
- Mode switching
- Web search
- Image/GIF generation
- File operations
- System commands
- Agent system commands
- Memory management

---

## GUI / Visual System

### Description
Enhanced graphical user interface with character-specific theming, avatars, and visual assets.

### Components

#### Themes (`characters.py`)
- **Purpose**: Visual theme definitions per character
- **Features**: Color palettes, fonts, styling, gradients
- **Characters**: 15+ color options per character

#### Avatars (`images/avatars/`)
- **Purpose**: Character visual representation
- **Files**: serena_avatar.png, astrid_avatar.png
- **Features**: Character-specific designs, emoji fallbacks

#### Backgrounds (`images/backgrounds/`)
- **Purpose**: Character-themed background images
- **Files**: serena_background.png, astrid_background.png
- **Features**: Themed designs for future use

#### Icons (`images/icons/`)
- **Purpose**: UI icons for features and agents
- **Files**: agent_icon.png, media_icon.png, server_icon.png, photo_icon.png, chat_icon.png, settings_icon.png
- **Features**: Feature-specific visual indicators

### Features
- Character-specific visual themes
- Avatar display in character tabs
- Icon-based status indicators
- Dynamic theme switching
- Graceful fallback for missing assets
- Enhanced color palettes and gradients

---

## Tests

### Description
Comprehensive testing system for validating all components and functionality.

### Components

#### Character Tests (`test_characters.py`)
- **Purpose**: Validate character system functionality
- **Features**: Character switching, theme application, memory isolation, voice configuration

#### Functionality Tests (`test_functionality.py`)
- **Purpose**: Validate overall system functionality
- **Features**: Mode switching, AI integration, router functionality, feature parity

#### Agent Tests (`test_agents.py`)
- **Purpose**: Validate agent system functionality
- **Features**: Agent registration, task execution, dashboard generation, router integration

#### Visual System Tests (`test_visual_system.py`)
- **Purpose**: Validate visual system components
- **Features**: Asset generation, theme enhancement, photo agent, GUI integration

### Features
- Component isolation testing
- Integration testing
- Functional validation
- Visual asset verification
- Error scenario testing

---

## File Structure

```
Serena/
├── main.py                          # GUI application entry point
├── characters.py                    # Character configuration system
├── ai.py                            # AI processing and memory management
├── router.py                        # Command routing and feature detection
├── voice_enhanced.py                # Voice system with character support
├── local_ai.py                      # Local deterministic responses
├── system_commands.py               # OS/application/system commands
├── requirements.txt                 # Python dependencies
│
├── agents/                          # Background agent system
│   ├── agent_manager.py             # Agent coordination
│   ├── base_agent.py                # Agent framework
│   ├── common/                      # Shared utilities
│   ├── media/agent.py               # Media management agent
│   ├── server/agent.py              # Server maintenance agent
│   └── photos/agent.py              # Photo organization agent
│
├── images/                          # Visual assets
│   ├── avatars/                     # Character avatars
│   ├── backgrounds/                  # Character backgrounds
│   └── icons/                       # UI icons
│
├── memory_*.json                    # Character-specific conversation memory
│
├── test_characters.py                # Character system tests
├── test_functionality.py             # Overall functionality tests
├── test_agents.py                   # Agent system tests
├── test_visual_system.py            # Visual system tests
├── create_visual_assets.py          # Visual asset generator
│
├── DUAL_AI_IMPLEMENTATION.md        # Dual-AI implementation documentation
├── AGENT_SYSTEM_GUIDE.md            # Agent system usage guide
├── VISUAL_SYSTEM_SUMMARY.md         # Visual system documentation
├── FINAL_SYSTEM_SUMMARY.md          # Complete system summary
└── SYSTEM_ARCHITECTURE.md           # This file
```

---

## System Integration

### Data Flow
1. **User Input** → Router → Command Analysis
2. **Character Context** → AI Processing → Response Generation
3. **Agent Tasks** → Agent Manager → Specialized Agents
4. **Visual Updates** → Theme Application → GUI Refresh
5. **Memory Updates** → File Storage → Context Persistence

### Component Interactions
- **Character System** ↔ **AI Processing**: Character-specific prompts and context
- **Router** ↔ **Agent System**: Command routing to specialized agents
- **GUI** ↔ **Visual System**: Dynamic theme and asset application
- **Voice** ↔ **Character System**: Character-specific voice configurations
- **Memory** ↔ **AI Processing**: Context continuity and system messages

---

## Key Design Principles

1. **Separation of Concerns**: Interactive AI vs. background automation
2. **Character Isolation**: Complete separation of character contexts and memories
3. **Safety First**: Permission-based access, rule-based behavior, comprehensive logging
4. **Graceful Degradation**: System continues functioning when optional features unavailable
5. **Data-Driven Configuration**: Characters and agents defined in data structures
6. **Extensibility**: Easy to add new characters, agents, and features
7. **Visual Consistency**: Character-specific theming throughout the interface
8. **Error Resilience**: Comprehensive error handling without system crashes

---

## Current Status

**Overall System**: ✅ Production Ready
- Dual-AI characters with complete feature parity
- Background agent system with 3 operational agents
- Enhanced visual system with themes, avatars, and icons
- Comprehensive memory and voice systems
- Safe, permission-based architecture
- Full testing coverage
- Graceful fallbacks for missing dependencies
- Extensible architecture for future expansion