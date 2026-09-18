# Serena — Begin Phase 2: Agent Ecosystem & Coordination

Phase 1 has been completed and validated.

Before making changes, inspect the actual current Serena code and Phase 1 implementation.

## Phase 1 Baseline

The Phase 1 implementation reports:

* `core_data_contracts.py` created and in use
* `CentralizedPermissionSystem` implemented
* AgenticExecutor requires a permission system
* router permission bypass removed
* Base Agent integrated with centralized authorization
* agentic tools use centralized permission checks
* verification implemented
* approval workflow implemented
* centralized `audit_log.py` implemented
* `ai_decide_task()` implemented
* Agent Manager task selection/planning implemented
* Phase 1 security tests: 9/9 passed

Treat the actual code as authoritative. Do not assume the completion summary is correct without inspection.

---

# Phase 2 Objective

Transform Serena's existing agents into a coordinated agent ecosystem.

Phase 2 must build on the Phase 1 architecture rather than replacing it.

The system must continue enforcing:

```text
AI
 ↓
TaskDecision
 ↓
Agent Manager
 ↓
Agent
 ↓
Permission System
 ↓
Approval if required
 ↓
Tool
 ↓
Execution
 ↓
Verification
 ↓
Audit Log
 ↓
TaskResult
```

No Phase 2 feature may create a bypass around this pipeline.

---

# CRITICAL RULE: REUSE PHASE 1 DATA CONTRACTS

Phase 1 already created:

```text
core_data_contracts.py
```

Before creating any new task/result classes:

1. Inspect `core_data_contracts.py`.
2. Inspect all existing task/result definitions.
3. Identify duplicate concepts.
4. Reuse the Phase 1 contracts wherever possible.
5. Extend them only when necessary.
6. Do NOT create a competing `TaskResult`, `Task`, or execution model.

If Phase 2 requires additional fields, evolve the existing contracts rather than creating parallel definitions.

Document any compatibility changes.

---

# Phase 2 Step 1 — Audit Current Agent Architecture

Inspect:

```text
agents/
agents/base_agent.py
agents/agent_manager.py
agents/media/
agents/photos/
agents/server/
agents/development/
core_data_contracts.py
permission_system.py
audit_log.py
agentic_executor.py
agentic_tools.py
router.py
```

Determine:

* which agents are actually registered
* which agents are functional
* how agents currently receive tasks
* how tasks currently return results
* how Agent Manager currently works
* whether agents can currently communicate
* whether tasks have persistent state
* whether any queue already exists
* whether any scheduler already exists
* whether any event system already exists
* whether any health/status system already exists

Do not create duplicate infrastructure if an existing implementation can be extended.

---

# Phase 2 Step 2 — Standardized Task Lifecycle

Use the existing Phase 1 task contracts.

Establish a consistent lifecycle:

```text
PENDING
 ↓
ASSIGNED
 ↓
IN_PROGRESS
 ↓
WAITING / BLOCKED
 ↓
COMPLETED
   OR
FAILED
   OR
CANCELLED
```

Tasks should support, where appropriate:

* task ID
* goal
* task type
* assigned agent
* parameters
* priority
* dependencies
* timestamps
* status
* correlation ID
* retry information
* result
* error information

Do not add unnecessary complexity.

---

# Phase 2 Step 3 — Upgrade Agent Manager

### File

```text
agents/agent_manager.py
```

Upgrade Agent Manager from a basic registry/dispatcher into the coordinator for the agent ecosystem.

It should manage:

* agent registration
* agent discovery
* agent capabilities
* agent status
* task assignment
* task coordination
* task lifecycle
* queue interaction
* dependencies
* multi-agent tasks

The Agent Manager is NOT the permission authority.

The Permission System remains the only authorization authority.

---

# Phase 2 Step 4 — Agent Capability Registry

Each agent should expose structured capability information.

At minimum:

```text
agent_id
name
description
capabilities
supported_task_types
status
health
permission_profile
```

The registry must not grant or modify permissions.

Permission profiles continue to come from the centralized permission system.

---

# Phase 2 Step 5 — Agent Selection

Implement controlled agent selection based on:

* task type
* declared capabilities
* availability
* workload
* health
* explicit task constraints

Keep selection deterministic and explainable.

Do not introduce speculative AI-based agent ranking yet.

---

# Phase 2 Step 6 — Central Task Queue

Create one centralized task queue for the Agent Manager ecosystem.

The queue should support:

* priority
* FIFO behavior within the same priority
* task cancellation
* timeout
* retry policy
* dependency blocking

Do NOT create a separate queue inside each agent.

If Serena already has queue functionality, inspect and reuse it.

---

# Phase 2 Step 7 — Multi-Agent Coordination

Allow one parent task to coordinate multiple child tasks.

Example:

```text
Parent Task
 ├── Media Agent
 ├── Photo Agent
 └── Server Agent
       ↓
  Parent Result
```

Track:

* parent task
* child tasks
* dependencies
* child results
* failures
* completion state

Every child task must still pass through the Phase 1 security pipeline.

One agent must never be able to authorize another agent's privileged operation.

---

# Phase 2 Step 8 — Inter-Agent Communication

Create or extend:

```text
agents/communication.py
```

Provide a controlled communication mechanism.

Support:

* direct messages
* responses
* message IDs
* correlation IDs
* delivery state
* controlled broadcasts if genuinely needed
* communication logging

Agent communication must never be an authorization bypass.

For example:

```text
Agent A → Agent B: "Delete this file."
```

must NOT mean Agent B is automatically authorized to delete it.

Agent B's actual operation still requires centralized permission validation.

---

# Phase 2 Step 9 — Task Dependencies

Implement dependency handling.

Support:

* dependency registration
* dependency completion
* dependency failure
* blocked state
* dependent task release
* circular dependency detection

Example:

```text
Task A
 ↓
Task B
 ↓
Task C
```

Task C must not execute until its required dependencies are satisfied.

---

# Phase 2 Step 10 — Persistent Task State

Create or extend task persistence.

Suggested file if no suitable implementation exists:

```text
agents/task_storage.py
```

Persist:

* task state
* status changes
* history
* pending tasks
* results
* errors

Serena must be able to recover task state after restart.

### IMPORTANT

Do not automatically repeat potentially destructive or non-idempotent operations after a crash.

A recovered task should be classified safely before retrying.

---

# Phase 2 Step 11 — One Event System

Create or extend:

```text
agents/event_system.py
```

There must be ONE event architecture.

Possible events:

```text
task.created
task.started
task.completed
task.failed
task.blocked

agent.started
agent.stopped
agent.error
agent.health_changed

media.received
photo.received
server.warning
server.failure
```

Events may trigger tasks.

Events may NOT bypass the normal task/permission/execution lifecycle.

---

# Phase 2 Step 12 — One Scheduler Architecture

Establish one scheduler architecture for Serena.

Before creating one, inspect the repository for existing scheduling functionality.

Support where appropriate:

* one-time tasks
* date/time schedules
* interval schedules
* persistent schedules
* event-triggered tasks

Scheduled tasks still go through:

```text
Task
 ↓
Agent Manager
 ↓
Agent
 ↓
Permission
 ↓
Approval if required
 ↓
Tool
 ↓
Verification
 ↓
Audit
```

Do NOT create a second scheduler in Phase 3.

Phase 3 will consume this scheduler.

---

# Phase 2 Step 13 — Agent Health & Status

Implement basic health/status tracking.

Track:

* current status
* availability
* task count
* successful tasks
* failed tasks
* recent errors
* execution time
* heartbeat if appropriate

Do NOT implement advanced predictive health yet.

Do NOT make automated recovery overly complex.

---

# Phase 2 Step 14 — Safe Agent Recovery

Support conservative recovery such as:

* detecting stopped agents
* restarting safe/non-destructive workers
* marking tasks blocked
* preserving task state
* reporting failures

Do not silently repeat destructive operations.

---

# Phase 2 Step 15 — Serena/Astrid Integration

Expose the agent ecosystem to the conversational layer.

Serena and Astrid should be able to understand:

* what agents exist
* what they can do
* what they are currently doing
* task status
* task results
* failures
* approval requirements

They must remain presentation/conversational interfaces.

They must NOT become:

* permission authorities
* direct tool executors
* security bypasses

Their personalities may affect how they explain an operation, but never whether the operation is allowed.

---

# Phase 2 Step 16 — GUI Compatibility

Do not make the GUI a dependency of the core agent architecture.

The future dashboard should consume Agent Manager state.

For now, expose enough structured state that `main.py` can later display:

* agents
* status
* current tasks
* queue
* schedules
* approvals
* failures

Do not build the full Phase 3 dashboard yet unless the existing architecture requires a minimal compatibility change.

---

# Phase 2 Step 17 — Testing

Create/update Phase 2 tests.

At minimum test:

### Task System

* task creation
* serialization
* status lifecycle
* task results
* cancellation

### Agent Manager

* registration
* capability discovery
* agent selection
* assignment
* coordination

### Queue

* priority
* FIFO
* cancellation
* timeout
* retry

### Multi-Agent

* parent/child tasks
* dependency handling
* child failure
* parent completion

### Communication

* message delivery
* responses
* correlation IDs
* communication logging

### Persistence

* save
* load
* restart recovery
* unsafe retry prevention

### Events

* event creation
* subscription
* delivery
* event-triggered tasks

### Scheduler

* scheduled task creation
* persistence
* execution
* cancellation

### Health

* status
* heartbeat/availability
* failure tracking

### SECURITY REGRESSION

Most importantly, verify that Phase 2 did NOT weaken Phase 1.

Test that:

* every privileged task still requires permission
* approval is still required where policy says so
* tools cannot bypass authorization
* verification still occurs
* audit logging still occurs
* missing permission infrastructure still fails closed
* scheduled tasks cannot bypass permission
* event-triggered tasks cannot bypass permission
* agent-to-agent requests cannot bypass permission

Run:

```text
Phase 1 security tests
+
Phase 2 tests
+
existing Serena test suite
```

---

# Phase 2 Acceptance Criteria

Phase 2 is complete only when:

* one standardized task/result model exists
* existing Phase 1 contracts are reused
* Agent Manager functions as the coordinator
* agent capabilities are discoverable
* tasks can be queued and tracked
* multiple agents can participate in coordinated work
* agents can communicate through a controlled system
* dependencies are supported
* task state survives restart
* one EventBus architecture exists
* one scheduler architecture exists
* basic agent health/status works
* recovery is conservative
* Serena/Astrid can access agent/task information
* Phase 1 permission enforcement remains mandatory
* approval remains mandatory where required
* verification remains mandatory where required
* audit logging remains mandatory
* existing functionality remains operational
* Phase 1 security tests still pass
* Phase 2 tests pass
* existing regression tests pass

---

# Explicit Phase 2 Non-Goals

Do NOT implement:

* Development Agent expansion
* Vision
* autonomous task generation
* self-improvement
* self-modifying code
* unrestricted autonomous execution
* predictive agent health
* complex autonomous recovery
* a second scheduler
* a second EventBus
* a second permission system

Those belong to later work.

---

# Implementation Rules

1. Inspect before modifying.
2. Reuse existing code where sound.
3. Do not create duplicate systems.
4. Keep changes incremental.
5. Run tests after each logical subsystem.
6. Preserve the Phase 1 security boundary.
7. Fail closed for security-sensitive infrastructure.
8. Do not silently remove existing functionality.
9. Document migrations and compatibility decisions.
10. Do not claim completion until tests actually run.

---

# Final Phase 2 Execution Principle

Regardless of task source:

```text
Human
Serena
Astrid
GUI
CLI
Scheduler
Event
Agent
Future Autonomous Layer
        ↓
      TASK
        ↓
  AGENT MANAGER
        ↓
      AGENT
        ↓
    PERMISSION
        ↓
APPROVAL IF NEEDED
        ↓
       TOOL
        ↓
    EXECUTION
        ↓
   VERIFICATION
        ↓
     AUDIT LOG
        ↓
    TASK RESULT
```

There must be no alternate execution path.

Begin by auditing the current Phase 1 implementation and existing agent infrastructure. Then implement Phase 2 incrementally.
