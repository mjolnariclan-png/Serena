import json
from pathlib import Path
from typing import List, Dict, Optional, Any
import ollama
from characters import get_character, get_current_character, get_character_modes, get_character_memory_file, get_character_system_prompt

# Try to import Phase 1 and Phase 2 infrastructure
try:
    from core_data_contracts import Task, TaskDecision, generate_task_id, generate_correlation_id
    from agents.agent_manager import AgentManager
    CORE_CONTRACTS_AVAILABLE = True
    AGENT_MANAGER_AVAILABLE = True
except ImportError:
    CORE_CONTRACTS_AVAILABLE = False
    AGENT_MANAGER_AVAILABLE = False
    
    # Fallback definitions for Phase 1 data contracts
    import time
    import uuid
    
    class Task:
        def __init__(self, task_id: str, goal: str, priority: int = 5, agent_id: Optional[str] = None):
            self.task_id = task_id
            self.goal = goal
            self.priority = priority
            self.agent_id = agent_id
            self.created_at = time.time()
            self.context = {}
            self.metadata = {}
    
    class TaskDecision:
        def __init__(self, decision_id: str, task: Task, confidence: float, reasoning: str, 
                     suggested_agent: Optional[str] = None, suggested_parameters: Dict = None):
            self.decision_id = decision_id
            self.task = task
            self.confidence = confidence
            self.reasoning = reasoning
            self.suggested_agent = suggested_agent
            self.suggested_parameters = suggested_parameters or {}
            self.created_at = time.time()
    
    def generate_task_id() -> str:
        return f"task_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    
    def generate_correlation_id() -> str:
        return str(uuid.uuid4())

# Global state — set at startup or by command
current_mode = "chat"


def get_mode_config(mode: str = None, character_id: str = None) -> Dict:
    """Get mode configuration for specified or current character and mode."""
    m = mode or current_mode
    char_modes = get_character_modes(character_id)
    return char_modes.get(m, char_modes.get("chat", {}))


def get_memory_file(mode: str = None, character_id: str = None) -> str:
    """Get memory file path for specified or current character and mode."""
    m = mode or current_mode
    return get_character_memory_file(m, character_id)


def get_current_system_prompt(mode: str = None, character_id: str = None) -> str:
    """
    Generate the authoritative system prompt dynamically from the current
    character and mode configuration.
    """
    m = mode or current_mode
    return get_character_system_prompt(m, character_id)


def load_conversation_history(mode: str = None, character_id: str = None) -> List[Dict[str, str]]:
    """
    Load ONLY actual conversation turns (user and assistant messages) from disk.
    System messages from disk are filtered out so that old system prompts or
    stale character configurations never override dynamic configuration.
    """
    file_name = get_memory_file(mode, character_id)
    path = Path(file_name)
    turns: List[Dict[str, str]] = []

    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for msg in data:
                        if isinstance(msg, dict) and msg.get("role") in ["user", "assistant"]:
                            # Prevent corrupt or non-string content
                            content = str(msg.get("content", "")).strip()
                            if content:
                                turns.append({"role": msg["role"], "content": content})
        except Exception as e:
            print(f"Warning: Failed to load conversation history from {file_name}: {e}")
            turns = []

    return turns


def save_conversation_history(turns: List[Dict[str, str]], mode: str = None, character_id: str = None) -> None:
    """
    Save ONLY user and assistant conversation turns to disk.
    Filters out any system prompts to keep the memory clean.
    """
    file_name = get_memory_file(mode, character_id)
    filtered_turns = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in turns
        if isinstance(msg, dict) and msg.get("role") in ["user", "assistant"]
    ]
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(filtered_turns, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Failed to save conversation history to {file_name}: {e}")


def load_memory(mode: str = None, character_id: str = None) -> List[Dict[str, str]]:
    """
    Construct the full message list for Ollama:
    Index 0 is ALWAYS the dynamically generated current system prompt,
    followed by the filtered conversation turns.
    """
    system_prompt = get_current_system_prompt(mode, character_id)
    turns = load_conversation_history(mode, character_id)
    return [{"role": "system", "content": system_prompt}] + turns


def save_memory(messages: List[Dict[str, str]], mode: str = None, character_id: str = None) -> None:
    """Save conversation messages by persisting only the actual conversation turns."""
    save_conversation_history(messages, mode, character_id)


def set_mode(mode: str) -> str:
    """Set mode for current character."""
    global current_mode
    character_modes = get_character_modes()
    if mode not in character_modes:
        available = ", ".join(character_modes.keys())
        return f"Unknown mode '{mode}'. Available: {available}"
    current_mode = mode
    config = character_modes[mode]
    char_name = get_character()["name"]
    return f"Switched to {config['label']} mode. Using model: {config['model']}."


def get_current_mode() -> str:
    return current_mode


def list_modes() -> str:
    """List available modes for current character."""
    character_modes = get_character_modes()
    char_name = get_character()["name"]
    lines = [f"Available modes for {char_name}:"]
    for key, cfg in character_modes.items():
        marker = "  → " if key == current_mode else "    "
        lines.append(f"{marker}{key}: {cfg['label']} (model: {cfg['model']})")
    return "\n".join(lines)


def generate_text(prompt: str) -> str:
    """
    Generate text using current character's dynamic mode configuration
    and isolated conversation memory.
    """
    config = get_mode_config()
    current_char = get_character()
    system_prompt = get_current_system_prompt()
    
    # Load actual conversation history
    turns = load_conversation_history()
    
    # Add new user message
    turns.append({"role": "user", "content": prompt})

    # Keep conversation context focused: last 20 turns
    recent_turns = turns[-20:] if len(turns) > 20 else turns

    # Construct clean payload for Ollama with dynamic system prompt at top
    context_messages = [{"role": "system", "content": system_prompt}] + recent_turns

    try:
        response = ollama.chat(
            model=config["model"],
            messages=context_messages,
            options={
                "temperature": config.get("temperature", 0.7),
                "num_predict": config.get("num_predict", 800),
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        )
        reply = response["message"]["content"].strip()
    except Exception as e:
        reply = f"AI error ({type(e).__name__}): {str(e)}\n(Make sure Ollama is running with model '{config['model']}')"

    # Add assistant response to history
    turns.append({"role": "assistant", "content": reply})
    
    # Keep total stored history manageable (last 50 turns)
    if len(turns) > 50:
        turns = turns[-50:]
    
    save_conversation_history(turns)

    return reply


def clear_memory(mode: str = None, character_id: str = None) -> str:
    """
    Wipe conversation history for the specified (or current) character and mode
    without deleting configuration or affecting other characters/modes.
    """
    m = mode or current_mode
    char = get_character(character_id)
    config = get_mode_config(m, character_id)
    save_conversation_history([], m, character_id)
    return f"Memory cleared for {char['name']}'s {config['label']} mode. Starting fresh."


def clear_all_character_memory(character_id: str = None) -> str:
    """Clear conversation history for all modes of a given character."""
    char = get_character(character_id)
    char_id = character_id or get_current_character()
    for mode in char.get("modes", {}).keys():
        save_conversation_history([], mode, char_id)
    return f"All conversation memories cleared for {char['name']}."


def ai_decide_task(user_input: str) -> TaskDecision:
    """
    AI analyzes user input and decides WHAT should happen.
    
    Phase 1: AI decision-making interface that creates structured task decisions
    without executing tools. Creating a task does not grant permission.
    
    Args:
        user_input: The user's natural language input
        
    Returns:
        TaskDecision containing the task, confidence, reasoning, and suggested agent
    """
    current_char = get_character()
    current_mode = get_current_mode()
    
    # Analyze the user input to determine task type
    task = Task(
        task_id=generate_task_id(),
        goal=user_input,
        priority=5,
        agent_id=None  # Will be determined by Agent Manager
    )
    
    # Use AI to analyze the task and provide reasoning
    try:
        analysis_prompt = f"""
You are {current_char['name']}, analyzing a user request. Your current mode is {current_mode}.

User request: "{user_input}"

Analyze this request and provide:
1. What type of task this is (file operation, system command, search, code generation, etc.)
2. Which agent would be best suited (MediaAgent, ServerAgent, PhotoAgent, or none if not an agent task)
3. Your confidence level (0.0 to 1.0)
4. Brief reasoning for your decision

Respond in this format:
TASK_TYPE: [task type]
SUGGESTED_AGENT: [agent name or "none"]
CONFIDENCE: [0.0-1.0]
REASONING: [brief explanation]
"""
        
        response = ollama.chat(
            model=get_mode_config()["model"],
            messages=[{"role": "user", "content": analysis_prompt}],
            options={"temperature": 0.3, "num_predict": 200}
        )
        
        analysis = response["message"]["content"].strip()
        
        # Parse the AI's analysis
        task_type = "unknown"
        suggested_agent = None
        confidence = 0.5
        reasoning = analysis
        
        for line in analysis.split('\n'):
            if line.startswith("TASK_TYPE:"):
                task_type = line.split(":", 1)[1].strip()
            elif line.startswith("SUGGESTED_AGENT:"):
                agent_name = line.split(":", 1)[1].strip().lower()
                if agent_name != "none":
                    suggested_agent = agent_name
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":", 1)[1].strip())
                except:
                    confidence = 0.5
            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()
        
        # Enhance task context
        task.context = {
            "task_type": task_type,
            "character": current_char["name"],
            "mode": current_mode,
            "original_input": user_input
        }
        
        # Create task decision
        decision = TaskDecision(
            decision_id=f"decision_{generate_task_id()}",
            task=task,
            confidence=confidence,
            reasoning=reasoning,
            suggested_agent=suggested_agent,
            suggested_parameters={"task_type": task_type}
        )
        
        return decision
        
    except Exception as e:
        # Fallback to simple heuristic if AI analysis fails
        user_input_lower = user_input.lower()
        
        task_type = "unknown"
        suggested_agent = None
        confidence = 0.3
        reasoning = f"AI analysis failed ({str(e)}), using heuristic analysis"
        
        # Simple heuristic-based task classification
        if any(word in user_input_lower for word in ["media", "movie", "tv", "jellyfin", "video"]):
            task_type = "media_operation"
            suggested_agent = "MediaAgent"
            confidence = 0.7
            reasoning = "Media-related task detected"
        elif any(word in user_input_lower for word in ["server", "disk", "service", "system", "maintenance"]):
            task_type = "system_maintenance"
            suggested_agent = "ServerAgent"
            confidence = 0.7
            reasoning = "System maintenance task detected"
        elif any(word in user_input_lower for word in ["photo", "picture", "image", "organize"]):
            task_type = "photo_organization"
            suggested_agent = "PhotoAgent"
            confidence = 0.7
            reasoning = "Photo organization task detected"
        elif any(word in user_input_lower for word in ["backup", "archive"]):
            task_type = "backup_operation"
            suggested_agent = "BackupAgent"
            confidence = 0.7
            reasoning = "Backup task detected"
        elif any(word in user_input_lower for word in ["security", "login", "failed"]):
            task_type = "security_check"
            suggested_agent = "SecurityAgent"
            confidence = 0.7
            reasoning = "Security check task detected"
        elif any(word in user_input_lower for word in ["monitor", "cpu", "memory", "status"]):
            task_type = "system_monitoring"
            suggested_agent = "MonitoringAgent"
            confidence = 0.7
            reasoning = "System monitoring task detected"
        elif any(word in user_input_lower for word in ["code", "test", "git", "development"]):
            task_type = "development"
            suggested_agent = "DevelopmentAgent"
            confidence = 0.7
            reasoning = "Development task detected"
        
        # Enhance task context
        task.context = {
            "task_type": task_type,
            "character": current_char["name"],
            "mode": current_mode,
            "original_input": user_input
        }
        
        # Create task decision
        decision = TaskDecision(
            decision_id=f"decision_{generate_task_id()}",
            task=task,
            confidence=confidence,
            reasoning=reasoning,
            suggested_agent=suggested_agent,
            suggested_parameters={"task_type": task_type}
        )
        
        return decision


def submit_agent_task(user_input: str, agent_manager: Optional[AgentManager] = None, wait_for_result: bool = True) -> Dict[str, Any]:
    """
    Submit a task to the agent ecosystem through Serena/Astrid.
    
    Phase 3: Serena/Astrid as conversational interface to agent ecosystem.
    This function enables the conversational layer to interact with agents
    while maintaining the security pipeline.
    
    Args:
        user_input: The user's natural language request
        agent_manager: The AgentManager instance (if available)
        wait_for_result: Whether to wait for task completion and return result
        
    Returns:
        Dictionary with task submission status and information
    """
    current_char = get_character()
    
    # Check if AgentManager is available
    if not AGENT_MANAGER_AVAILABLE or agent_manager is None:
        return {
            "success": False,
            "error": "Agent Manager not available",
            "message": f"{current_char['name']} cannot access the agent ecosystem at this time."
        }
    
    # Get AI decision about the task
    decision = ai_decide_task(user_input)
    
    # Check if this is an agent task
    if not decision.suggested_agent:
        return {
            "success": False,
            "is_agent_task": False,
            "message": f"{current_char['name']} determined this is not an agent task.",
            "task_type": decision.task.context.get("task_type", "unknown"),
            "reasoning": decision.reasoning
        }
    
    # Check if the suggested agent is registered
    agent = agent_manager.get_agent(decision.suggested_agent)
    if not agent:
        return {
            "success": False,
            "error": f"Agent {decision.suggested_agent} not registered",
            "message": f"{current_char['name']} tried to use {decision.suggested_agent}, but it's not available.",
            "available_agents": list(agent_manager.agents.keys())
        }
    
    # Create task with enhanced context
    task = decision.task
    task.task_type = decision.task.context.get("task_type", "unknown")
    task.agent_id = decision.suggested_agent
    task.correlation_id = generate_correlation_id()
    
    # Submit task to AgentManager (goes through normal pipeline)
    submitted = agent_manager.submit_task(task)
    
    if not submitted:
        return {
            "success": False,
            "error": "Failed to submit task to queue",
            "message": f"{current_char['name']} could not submit the task to the agent queue."
        }
    
    # If waiting for result, poll for completion
    if wait_for_result:
        import time
        max_wait = 30  # seconds
        poll_interval = 0.5
        waited = 0
        
        while waited < max_wait:
            status_info = get_agent_task_status(task.task_id, agent_manager)
            if status_info.get("success"):
                status = status_info.get("status", "")
                if status in ["COMPLETED", "FAILED", "CANCELLED"]:
                    # Task finished, return the result
                    return {
                        "success": status == "COMPLETED",
                        "task_id": task.task_id,
                        "agent": decision.suggested_agent,
                        "goal": task.goal,
                        "task_type": task.task_type,
                        "correlation_id": task.correlation_id,
                        "status": status,
                        "result": status_info.get("result"),
                        "error_message": status_info.get("error_message"),
                        "message": f"{current_char['name']} reports: Task is {status.lower()}",
                        "reasoning": decision.reasoning,
                        "confidence": decision.confidence
                    }
            time.sleep(poll_interval)
            waited += poll_interval
        
        # Timeout
        return {
            "success": False,
            "task_id": task.task_id,
            "agent": decision.suggested_agent,
            "goal": task.goal,
            "task_type": task.task_type,
            "correlation_id": task.correlation_id,
            "status": "TIMEOUT",
            "message": f"{current_char['name']} reports: Task timed out after {max_wait} seconds",
            "reasoning": decision.reasoning,
            "confidence": decision.confidence
        }
    
    return {
        "success": True,
        "task_id": task.task_id,
        "agent": decision.suggested_agent,
        "goal": task.goal,
        "task_type": task.task_type,
        "correlation_id": task.correlation_id,
        "message": f"{current_char['name']} has submitted your request to {decision.suggested_agent}.",
        "reasoning": decision.reasoning,
        "confidence": decision.confidence
    }


def get_agent_task_status(task_id: str, agent_manager: Optional[AgentManager] = None) -> Dict[str, Any]:
    """
    Get the status of a task submitted to the agent ecosystem.
    
    Phase 3: Enable Serena/Astrid to report task status.
    
    Args:
        task_id: The task ID to check
        agent_manager: The AgentManager instance (if available)
        
    Returns:
        Dictionary with task status information
    """
    current_char = get_character()
    
    if not AGENT_MANAGER_AVAILABLE or agent_manager is None:
        return {
            "success": False,
            "error": "Agent Manager not available"
        }
    
    # Try to get task from queue
    if agent_manager.task_queue:
        task = agent_manager.task_queue.get_task(task_id)
        if task:
            return {
                "success": True,
                "task_id": task.task_id,
                "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                "goal": task.goal,
                "agent": task.agent_id,
                "created_at": task.created_at,
                "message": f"{current_char['name']} reports: Task is {task.status.value if hasattr(task.status, 'value') else str(task.status)}"
            }
    
    # Task not in queue, check storage
    try:
        from agents.task_storage import get_task_storage
        storage = get_task_storage()
        task = storage.get_task(task_id)
        if task:
            return {
                "success": True,
                "task_id": task.task_id,
                "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                "goal": task.goal,
                "agent": task.agent_id,
                "created_at": task.created_at,
                "result": task.result,
                "error_message": task.error_message,
                "message": f"{current_char['name']} reports: Task is {task.status.value if hasattr(task.status, 'value') else str(task.status)}"
            }
    except ImportError:
        pass
    
    return {
        "success": False,
        "error": "Task not found",
        "message": f"{current_char['name']} could not find information about this task."
    }


def get_agent_ecosystem_status(agent_manager: Optional[AgentManager] = None) -> Dict[str, Any]:
    """
    Get the overall status of the agent ecosystem.
    
    Phase 3: Enable Serena/Astrid to report agent ecosystem status.
    
    Args:
        agent_manager: The AgentManager instance (if available)
        
    Returns:
        Dictionary with ecosystem status information
    """
    current_char = get_character()
    
    if not AGENT_MANAGER_AVAILABLE or agent_manager is None:
        return {
            "success": False,
            "error": "Agent Manager not available",
            "message": f"{current_char['name']} cannot access the agent ecosystem at this time."
        }
    
    # Get agent status
    agent_status = agent_manager.get_all_agent_status()
    
    # Get queue status
    queue_status = agent_manager.get_queue_status()
    
    # Get agent capabilities
    capabilities = agent_manager.get_agent_capabilities()
    
    return {
        "success": True,
        "message": f"{current_char['name']} reports agent ecosystem status:",
        "agents": agent_status,
        "queue": queue_status,
        "capabilities": capabilities
    }