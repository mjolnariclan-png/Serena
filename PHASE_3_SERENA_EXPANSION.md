# Implement Phase 3 — Serena Expansion

You are now implementing **Phase 3 of the Serena architecture**.

The authoritative Phase 3 implementation specification is:

`PHASE_3_SERENA_EXPANSION.md`

The current Serena project is located at:

`/home/eirik17/Desktop/Serena`

Phase 1 and Phase 2 have already been completed.

Before making ANY code changes, inspect the actual current implementation and verify that the Phase 1 and Phase 2 infrastructure described below actually exists.

---

# 1. READ THESE FIRST

Read:

* `SYSTEM_ARCHITECTURE_AUDIT.md`
* `PHASE1_STATUS.md`
* `PHASE2_STATUS.md`
* `PHASE2_BASELINE_AUDIT.md`
* `PHASE_1_ARCHITECTURAL_HARDENING.md`
* `PHASE_2_AGENT_ECOSYSTEM.md`
* `PHASE_3_SERENA_EXPANSION.md`

Also inspect the actual source code, especially:

* `router.py`
* `ai.py`
* `characters.py`
* `agentic_executor.py`
* `agentic_tools.py`
* `permission_system.py`
* `core_data_contracts.py`
* `audit_log.py`
* `agents/base_agent.py`
* `agents/agent_manager.py`
* `agents/task_queue.py`
* `agents/task_storage.py`
* `agents/event_system.py`
* `agents/communication.py`
* existing agents under `agents/`
* `main.py`
* existing tests

Do NOT assume that the status documents are correct simply because they claim completion.

Use the actual code as the source of truth.

---

# 2. CRITICAL ARCHITECTURAL RULE

Phase 3 must NOT create an alternate execution architecture.

Every operation must continue to follow the established pipeline:

Human / Serena / Astrid / GUI / Scheduler / Event / Agent / Future Autonomous Layer

↓

Task

↓

Agent Manager

↓

Agent

↓

Centralized Permission System

↓

Approval when required

↓

Tool

↓

Execution

↓

Verification

↓

Audit Log

↓

Task Result

There must be NO Phase 3 shortcut around this pipeline.

In particular:

* Development Agent cannot bypass permissions.
* Vision cannot bypass permissions for protected resources.
* Scheduled tasks cannot bypass permissions.
* Event-triggered tasks cannot bypass permissions.
* Agent-to-agent requests cannot automatically authorize operations.
* Serena cannot directly execute protected operations.
* Astrid cannot directly execute protected operations.
* The autonomous layer cannot bypass permissions.
* The autonomous layer cannot bypass approval requirements.
* The autonomous layer cannot bypass verification.
* The autonomous layer cannot bypass audit logging.
* GUI controls cannot create an alternate execution path.

The existing Phase 1 security architecture remains authoritative.

---

# 3. REUSE EXISTING INFRASTRUCTURE

Do not create competing versions of infrastructure that already exists.

Reuse:

* `core_data_contracts.py`
* `Task`
* existing `TaskResult`
* `TaskStatus`
* `AgentManager`
* `TaskQueue`
* `TaskStorage`
* `EventBus`
* existing scheduler architecture
* `CommunicationSystem`
* `CentralizedPermissionSystem`
* existing approval workflow
* existing verification system
* existing audit logging
* existing agent base class

Do NOT create:

* another Task class
* another TaskResult class
* another permission system
* another EventBus
* another scheduler
* another execution pipeline
* another agent manager

If an existing component needs modification, extend it rather than creating a duplicate.

---

# 4. PHASE 3 STEP 1 — DEVELOPMENT AGENT

Implement:

`agents/development/agent.py`

First inspect the existing:

`agents/development/`

directory and determine whether anything already exists.

The Development Agent should support controlled development/repository operations such as:

* inspect project files
* analyze source code
* inspect Git status
* inspect Git history
* run tests
* run linting/static analysis where available
* run builds where appropriate
* modify files within an approved workspace
* create backups where required
* verify modifications
* report results

## Development Agent security

This agent must have explicitly restricted capabilities.

Example capability boundaries:

READ:

* Serena project files
* Git metadata
* logs
* test results

ANALYZE:

* source code
* tests
* Git status/history
* build/test output

MODIFY:

* only approved Serena workspace

Git operations must be separated by risk.

Local operations such as inspecting status/history may be lower-risk.

Operations such as:

* commit
* branch creation
* merge
* reset
* checkout that discards work
* pull
* push
* remote configuration

must respect the centralized permission and approval architecture.

Remote push MUST require explicit approval unless the existing permission policy explicitly establishes another approved behavior.

Never give the Development Agent unrestricted filesystem or Git access.

Every operation must use the established permission boundary.

Every modification must be verified.

Every operation must be audit logged.

---

# 5. PHASE 3 STEP 2 — VISION

Implement/upgrade:

`vision.py`

First inspect the current file and existing vision-related infrastructure.

The Vision system should support:

* image loading
* supported image formats
* image processing
* visual analysis
* image context for Serena/Astrid
* integration with the conversational system
* safe handling of inaccessible or unsupported images

Do not introduce unnecessary external dependencies if existing infrastructure can perform the job.

Vision must respect filesystem/resource permissions.

Do not allow image access to become an unrestricted filesystem access mechanism.

Vision should produce structured results that can be consumed by the existing AI/conversational layer.

---

# 6. PHASE 3 STEP 3 — SCHEDULED AND EVENT-DRIVEN WORK

Use the existing Phase 2 infrastructure.

DO NOT create another scheduler or EventBus.

Use:

* existing scheduler in AgentManager
* existing `TaskQueue`
* existing `EventBus`
* existing task lifecycle
* existing task persistence
* existing permission system

Scheduled and event-triggered work must create/submit normal Tasks.

They must then enter the same execution pipeline as manually requested tasks.

Example:

Event

↓

Task created

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

Execute

↓

Verify

↓

Audit

↓

Result

The scheduler/event system must NEVER directly execute protected tools.

Implement persistence and safe behavior consistent with Phase 2.

---

# 7. PHASE 3 STEP 4 — ADDITIONAL SPECIALIZED AGENTS

Implement the specialized agents described in:

`PHASE_3_SERENA_EXPANSION.md`

including the planned:

* Backup Agent
* Security Agent
* Monitoring Agent

Before creating each one, inspect whether an existing implementation already exists.

Each agent must:

* inherit/use the existing BaseAgent architecture
* register with AgentManager
* declare capabilities
* use centralized permissions
* use the existing Task model
* use the existing TaskQueue
* use verification
* use audit logging
* fail safely
* never permanently delete by default
* never overwrite protected data without authorization
* operate only within defined scopes

Do not create broad unrestricted system agents.

---

# 8. PHASE 3 STEP 5 — SERENA AND ASTRID AS THE CONVERSATIONAL INTERFACE

Upgrade the existing conversational architecture so Serena and Astrid can act as the natural-language interface to the agent ecosystem.

They should be able to:

* understand a user's requested goal
* determine whether the request requires an agent
* identify the appropriate agent/capability
* create or request a Task
* obtain task status
* explain what is happening
* report results
* report failures
* explain when approval is required
* coordinate multiple agents when appropriate

Serena and Astrid remain conversational interfaces.

They are NOT the security boundary.

They are NOT direct filesystem executors.

They are NOT direct tool executors.

They must go through AgentManager and the established execution pipeline.

Preserve their distinct personalities and modes.

Do not flatten Serena and Astrid into identical personalities.

---

# 9. PHASE 3 STEP 6 — CONTROLLED JARVIS-STYLE AUTONOMOUS LAYER

Implement:

`agents/autonomous_layer.py`

This is the most security-sensitive part of Phase 3.

The autonomous layer may eventually support:

* goals
* task generation
* task prioritization
* task scheduling
* historical performance analysis
* failure pattern analysis
* operational learning
* deciding when an agent should perform a task
* coordinating multiple agents

BUT:

Autonomy must remain constrained by the existing architecture.

The autonomous layer must NOT:

* bypass permissions
* bypass approval
* bypass verification
* bypass audit logging
* directly execute arbitrary tools
* directly modify protected files
* grant itself permissions
* modify the permission system
* modify its own security boundaries
* create unrestricted filesystem access
* create unrestricted network access
* silently retry destructive operations

## IMPORTANT

"Learning" in Phase 3 means operational learning such as:

* previous task results
* success/failure rates
* execution durations
* agent performance
* failure patterns
* scheduling history
* user-approved preferences

It does NOT mean:

* self-modifying code
* rewriting its own security architecture
* changing permission rules
* creating new unrestricted capabilities
* modifying its own source code autonomously

The autonomous layer should initially be conservative.

When uncertain, it should create a task or request approval rather than execute.

---

# 10. PHASE 3 STEP 7 — GUI AGENT DASHBOARD

Upgrade `main.py` only as necessary to expose the agent ecosystem.

The GUI should display information such as:

* agents
* agent status
* health
* current tasks
* queued tasks
* completed tasks
* failed tasks
* scheduled tasks
* recent events
* approvals
* task results
* activity/log information

The GUI is an interface.

It must use AgentManager and the existing task/event infrastructure.

Do NOT create a second backend architecture specifically for the GUI.

Do NOT make the GUI required for the agent system to function.

---

# 11. TESTING IS REQUIRED

For every major subsystem implemented, create/run tests.

At minimum test:

## Development Agent

* capability registration
* permission enforcement
* allowed reads
* denied operations
* modification boundaries
* Git permission boundaries
* verification
* audit logging

## Vision

* image loading
* supported/unsupported formats
* visual analysis
* permission restrictions
* conversational integration

## Scheduler/Event System

* scheduled task creation
* event-triggered task creation
* task queue integration
* permission enforcement
* no direct protected execution

## Specialized Agents

* registration
* capability discovery
* task selection
* permissions
* verification
* logging

## Serena/Astrid

* natural-language task creation
* agent selection
* task status
* result reporting
* approval handling
* multi-agent coordination

## Autonomous Layer

Test that it:

* creates tasks rather than directly executing tools
* respects permissions
* respects approval
* respects verification
* produces audit entries
* cannot grant itself permissions
* cannot bypass the AgentManager

## GUI

* agent status display
* task display
* queue display
* event display
* no alternate execution path

---

# 12. SECURITY REGRESSION

After Phase 3 implementation, run ALL existing security tests.

At minimum:

* Phase 1 security tests
* Phase 2 tests
* Phase 3 tests
* existing project regression tests

Do not claim completion if tests were not actually executed.

Report the exact test counts and results.

If a Phase 1 or Phase 2 security test fails, stop and fix the regression before continuing.

---

# 13. IMPLEMENTATION RULES

Follow these rules throughout the implementation:

1. Inspect before modifying.
2. Use the actual current code as the source of truth.
3. Reuse existing infrastructure.
4. Do not create duplicate architectural systems.
5. Make incremental changes.
6. Test each subsystem after implementation.
7. Preserve backward compatibility where practical.
8. Do not silently remove existing functionality.
9. Preserve the centralized permission boundary.
10. Fail closed when required security infrastructure is unavailable.
11. Verify operations.
12. Audit operations.
13. Keep destructive operations conservative.
14. Document migrations when existing code is changed.
15. Do not claim something is implemented unless it actually exists and has been tested.
16. If the existing implementation conflicts with this plan, STOP and document the conflict rather than silently inventing a new architecture.

---

# 14. IMPLEMENTATION ORDER

Implement in this order:

### Phase 3A

Development Agent

### Phase 3B

Vision

### Phase 3C

Scheduled/Event-driven workflows using Phase 2 infrastructure

### Phase 3D

Backup/Security/Monitoring Agents

### Phase 3E

Serena/Astrid conversational orchestration

### Phase 3F

Controlled Autonomous Layer

### Phase 3G

GUI Agent Dashboard

### Phase 3H

Complete testing and regression validation

Do not jump ahead to autonomous behavior before the underlying agent infrastructure is verified.

---

# 15. DOCUMENTATION

Create/update:

* `PHASE3_BASELINE_AUDIT.md`
* `PHASE3_STATUS.md`
* appropriate architecture documentation
* test documentation where useful

The status document must clearly distinguish:

* IMPLEMENTED
* PARTIALLY IMPLEMENTED
* PRESENT BUT NOT INTEGRATED
* DOCUMENTED BUT MISSING
* PLANNED
* BLOCKED
* UNKNOWN

Do not mark something COMPLETE merely because a file exists.

---

# 16. FINAL ACCEPTANCE CRITERIA

Phase 3 is complete only when:

* Development Agent exists and is registered.
* Development Agent uses centralized permissions.
* Git operations respect permission/approval boundaries.
* Vision exists and is integrated safely.
* Scheduled tasks use the existing scheduler/task queue.
* Event-driven tasks use the existing EventBus/task queue.
* No second scheduler exists.
* No second EventBus exists.
* Specialized agents are registered and functional.
* Serena can interact with the agent ecosystem.
* Astrid can interact with the agent ecosystem.
* Serena/Astrid do not bypass the security architecture.
* Autonomous Layer exists.
* Autonomous Layer cannot bypass permissions.
* Autonomous Layer cannot bypass approval.
* Autonomous Layer cannot bypass verification.
* Autonomous Layer cannot bypass audit logging.
* Autonomous Layer does not self-modify security boundaries.
* GUI dashboard consumes the existing agent infrastructure.
* Phase 1 security tests pass.
* Phase 2 tests pass.
* Phase 3 tests pass.
* Existing regression tests pass.
* Documentation reflects the actual implementation.

---

# 17. IMPORTANT: DO NOT OVERBUILD

Phase 3 is the expansion phase, but do not interpret that as permission to make Serena unrestricted.

The goal is:

**More capable, not less controlled.**

The final system should remain:

**AI decides WHAT**

↓

**Agent Manager decides WHO**

↓

**Agent decides HOW**

↓

**Permission System decides WHETHER**

↓

**Approval determines whether human confirmation is required**

↓

**Tool performs the operation**

↓

**Verification determines whether it worked**

↓

**Audit Log records what happened**

↓

**Task Result returns to Serena/Astrid/user**

That architecture must remain intact.

---

# START

First perform the Phase 3 baseline inspection.

Before implementing anything, report:

1. What Phase 1 infrastructure actually exists.
2. What Phase 2 infrastructure actually exists.
3. What Phase 3 components already exist.
4. Any discrepancies between the documentation and actual code.
5. Any duplicate systems discovered.
6. Any security concerns discovered.
7. The exact implementation order you will follow.

Then begin Phase 3A.

Do not skip the inspection.
Do not rewrite the architecture.
Do not create duplicate systems.
Do not claim completion without running the tests.
