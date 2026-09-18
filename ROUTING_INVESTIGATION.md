# Routing Investigation Findings

**Date:** 2026-09-18
**Purpose:** Investigate routing issues identified in Phase 4I

## Findings

### Issue 1: "hello" Returns None

**Root Cause:** The router's fallback path may be returning None when generate_text() fails or when agent_manager is not available.

**Current Flow:**
```
User: "hello"
    ↓
router.route(prompt)
    ↓
[No specific pattern matches]
    ↓
ai.submit_agent_task(prompt, agent_manager)
    ↓
ai_decide_task(prompt)
    ↓
AI analysis determines this is not an agent task
    ↓
Returns {"success": False, "is_agent_task": False}
    ↓
router receives result, falls through to generate_text(prompt)
    ↓
generate_text() calls Ollama
    ↓
If Ollama unavailable or error, returns error message
    ↓
If successful, returns response
```

**Potential Problem:** If generate_text() returns None or there's an exception handling issue, the response could be None.

### Issue 2: "hey baby" Routes to MediaAgent

**Root Cause:** The heuristic classification in ai.py conflates capabilities with agents.

**Location:** `ai.py` lines 336-340

```python
# Simple heuristic-based task classification
if any(word in user_input_lower for word in ["media", "movie", "tv", "jellyfin", "video"]):
    task_type = "media_operation"
    suggested_agent = "MediaAgent"
    confidence = 0.7
    reasoning = "Media-related task detected"
```

**Problem:** The word "media" appears in the heuristic list. While "hey baby" doesn't contain "media", the AI prompt itself (line 266) explicitly asks the AI to choose from "MediaAgent, ServerAgent, PhotoAgent, or none". This biases the AI toward suggesting an agent even for conversational requests.

**Current AI Prompt:** `ai.py` line 266
```
2. Which agent would be best suited (MediaAgent, ServerAgent, PhotoAgent, or none if not an agent task)
```

**Problem:** The prompt presents agents as the primary options, not "capability" as the primary decision with "agent" as a secondary option.

### Issue 3: No RequestClassification Contract

**Finding:** The system does not have a RequestClassification contract as specified in the architecture document.

**Current State:**
- `ai_decide_task()` returns a `TaskDecision` object
- `TaskDecision` contains: `decision_id`, `task`, `confidence`, `reasoning`, `suggested_agent`, `suggested_parameters`
- This conflates capability with agent
- No explicit `requires_agent` field
- No explicit `request_type` field
- No explicit `capability` field separate from `agent_type`

### Issue 4: Router Logic

**Current Router Flow:** `router.py`
1. Check specific patterns (shutdown, system commands, web search, face recognition, etc.)
2. Check if agent_manager available
3. If yes, call ai.submit_agent_task()
4. If ai.submit_agent_task() returns success with result, return formatted result
5. If ai.submit_agent_task() returns that it's not an agent task, fall through
6. Check agentic mode
7. Check image generation
8. Check GIF generation
9. Check file creation
10. Fall back to generate_text()

**Problem:** The router doesn't have a clear separation between conversational capabilities and agent tasks. It relies on ai.submit_agent_task() to make this decision, but ai.submit_agent_task() itself conflates capabilities with agents.

### Issue 5: MediaAgent References

**Finding:** MediaAgent is referenced throughout the codebase:
- `agents/__init__.py` - registered as MediaAgent
- `ai.py` - heuristic suggests MediaAgent for media keywords
- `ai.py` - AI prompt asks to choose from MediaAgent, ServerAgent, PhotoAgent
- `router.py` - direct MediaAgent execution for specific media operations
- `permission_system.py` - has MediaAgent permissions
- Various test files

**Status:** MediaAgent exists as a registered agent, but it's being incorrectly suggested for conversational requests due to the classification logic.

## Required Corrections

1. **Implement RequestClassification contract** - Create a proper classification object with separate fields for capability, agent_type, and requires_agent
2. **Fix AI prompt** - Change the prompt to ask about capability first, then agent (if required)
3. **Fix heuristic classification** - Remove keyword-based agent suggestions for conversational words
4. **Add classification validation** - Validate that requires_agent=False implies agent_type=None
5. **Fix router fallback** - Ensure generate_text() fallback works correctly
6. **Add conversational capability detection** - Detect conversational requests (hello, hey, etc.) before agent classification

## Next Steps

1. Create RequestClassification data contract
2. Refactor ai_decide_task() to use RequestClassification
3. Update AI prompt to separate capability from agent
4. Add validation logic
5. Test with "hello" and "hey baby"