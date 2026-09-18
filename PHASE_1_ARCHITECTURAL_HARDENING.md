# Phase 1 — Architectural Hardening & Security Foundation

## Objective

Establish the secure execution foundation for Serena before adding new autonomous capabilities.

Authoritative lifecycle:

**AI → Router/Planner → Agent Manager → Agent → Permission System → Tool → Execute → Verify → Audit Log → Result**

Phase 1 hardens the existing architecture rather than rebuilding Serena.

## Priority

**CRITICAL**

Phase 1 must be completed and validated before Phase 2 begins.

## 1. Core Architectural Rules

- **AI decides WHAT:** creates a structured task decision; it does not execute tools.
- **Agent Manager decides WHO:** selects and coordinates the appropriate agent.
- **Agent decides HOW:** creates the execution plan.
- **Permission System decides WHETHER:** centralized authorization is mandatory.
- **Tool performs the operation:** tools perform external operations.
- **Verification determines WHETHER IT WORKED:** verification is separate from authorization.
- **Audit Log records WHAT HAPPENED:** lifecycle events are recorded with correlation IDs.

No router, agent, executor, autonomous component, or tool may bypass the permission boundary.

## 2. Core Data Contracts

Reconcile and formalize consistent contracts for:

- `Task`
- `TaskDecision`
- `ExecutionPlan`
- `ExecutionStep`
- `PermissionRequest`
- `PermissionDecision`
- `ApprovalRequest`
- `ToolResult`
- `VerificationResult`
- `TaskResult`
- `AuditEntry`

Inspect existing `TaskStep` and `AgenticTask` structures and reuse, adapt, or deliberately replace them. Do not create duplicate concepts without a documented compatibility reason.

## 3. Centralized Permission Authority

### File
`permission_system.py`

Evolve the existing system into the single authoritative authorization service.

It must support:

- operation validation
- agent-specific permission profiles
- path/resource restrictions
- dangerous-operation classification
- approval requirements and state
- permission decision logging
- correlation IDs
- clear allow/deny reasons

**Important:** permission authorizes; verification verifies. Do not merge those responsibilities.

Conceptual interface:

```python
class CentralizedPermissionSystem:
    def validate_operation(self, operation, agent_id, context) -> PermissionDecision: ...
    def request_approval(self, operation, details, context) -> ApprovalRequest: ...
    def check_approval_status(self, request_id) -> ApprovalStatus: ...
    def grant_approval(self, request_id, user) -> bool: ...
    def deny_approval(self, request_id, reason) -> bool: ...
    def get_agent_permissions(self, agent_id): ...
    def set_agent_permissions(self, agent_id, permissions): ...
```

Reconcile exact signatures with the existing code before implementation.

## 4. Base Agent

### File
`agents/base_agent.py`

Integrate Base Agent with centralized authorization.

Required:

- remove duplicate authorization ownership
- preserve useful input/path/safety validation
- add execution lifecycle hooks
- add verification interface
- add approval handling
- use standardized task/result contracts

Do not blindly delete all safety checks. Separate authorization, validation, safety, and verification responsibilities.

## 5. Tool Enforcement

### File
`agentic_tools.py`

Every externally affecting tool must require permission validation.

Keep appropriate defense-in-depth tool checks.

Example:

```text
Permission System
        ↓
Authorized workspace
        ↓
Tool validation
        ↓
Actual requested path/operation is safe
        ↓
Execution
```

The Permission System is mandatory, but it does not need to be the only safety mechanism.

## 6. Remove Agentic Permission Bypass

### Files
- `router.py`
- `agentic_executor.py`

Remove the existing path where `perm_system = None`.

The executor must fail closed if authorization infrastructure is unavailable.

A missing permission system must never result in privileged execution.

## 7. Agentic Executor Lifecycle

The executor orchestrates:

```text
Receive Task
 ↓
Validate
 ↓
Execution Plan
 ↓
Permission
 ↓
Approval if required
 ↓
Authorized Tool
 ↓
Execute
 ↓
Verify
 ↓
Audit
 ↓
TaskResult
```

The executor must not become a second permission authority.

## 8. Router / AI / Agent Manager Separation

### Files
- `router.py`
- `ai.py`
- `agents/agent_manager.py`

Target:

```text
User
 ↓
Serena / Astrid
 ↓
AI decision
 ↓
TaskDecision
 ↓
Agent Manager
 ↓
Agent selection
 ↓
ExecutionPlan
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
 ↓
TaskResult
 ↓
Serena / Astrid response
```

The router may route requests and handle user-facing approval state, but it must not directly perform privileged operations.

## 9. AI Decision Interface

### File
`ai.py`

Add/reconcile a structured interface such as:

```python
def ai_decide_task(user_input) -> TaskDecision:
    ...
```

The AI determines what should happen without executing it. Creating a task does not grant permission.

## 10. Agent Manager Execution Interface

### File
`agents/agent_manager.py`

Establish concepts equivalent to:

```python
get_agent_for_task(task_decision)
plan_execution(agent, task)
execute_agent_task(task)
```

Return standardized results and reconcile these APIs with existing code.

## 11. Verification

Verification is independent from permission.

Integration:

- `agents/base_agent.py`
- `agentic_executor.py`

Cover file operations, command operations, and other relevant side effects.

Verification failure must produce:

- failed/uncertain task state
- audit entry
- clear result
- rollback only when a safe rollback exists

Do not assume every operation is reversible.

## 12. Approval Workflow

Dangerous operations must pause before execution.

Suggested states:

```text
PENDING
APPROVED
DENIED
EXPIRED
CANCELLED
```

Execution cannot proceed while approval is pending.

Approval policy is independent of Serena/Astrid personality.

## 13. Centralized Audit Logging

### New file
`audit_log.py`

Create one structured audit system capturing:

- correlation ID
- task ID
- agent ID
- operation
- permission decision
- approval request/result
- tool execution result
- verification result
- timestamps
- failures/errors
- final task result

Audit logging records events; it does not authorize or execute them.

## 14. Existing Duplicate Systems

Before implementation, inspect and classify overlaps such as:

- `voice.py` vs `voice_enhanced.py`
- memory in `ai.py` vs `memory.py`
- web search in router vs `web_search.py`
- overlapping safety checks
- existing task/execution objects

Classify each:

- retain
- merge
- replace
- compatibility wrapper
- deprecated

Do not automatically delete anything.

## 15. Testing

Create/update Phase 1 security tests covering:

1. permission bypass attempts
2. missing permission system fails closed
3. all privileged tools require authorization
4. router cannot bypass permission
5. AI can create a task without executing
6. Agent Manager selection
7. execution planning
8. permission denial
9. pending approval
10. approval denial
11. approved dangerous operation
12. authorized tool execution
13. verification failure detection
14. permission audit logging
15. approval audit logging
16. execution audit logging
17. verification audit logging
18. correlation IDs
19. verification-failure results
20. safe rollback where defined

Run existing tests and new security tests.

## 16. Acceptance Criteria

Phase 1 is complete only when:

- one authoritative permission boundary exists
- no privileged path bypasses authorization
- missing permission infrastructure fails closed
- AI does not directly execute tools
- router does not directly execute privileged tools
- agents cannot grant themselves permissions
- tools cannot bypass centralized authorization
- appropriate defense-in-depth remains
- approval blocks dangerous operations when required
- verification is separate from authorization
- verification appears in task results
- audit logging captures the lifecycle
- task/execution objects are consistent
- existing functionality remains operational
- existing and new tests pass

## 17. Explicit Non-Goals

Do not implement:

- new specialized agents
- Development Agent
- Vision
- autonomous layer
- predictive health
- broad autonomous event behavior
- a second scheduler
- self-modifying behavior

## 18. Implementation Strategy

Implement incrementally. After each logical change:

1. run relevant tests
2. run security tests
3. inspect logs
4. verify existing functionality
5. document migration issues

Prefer adapting sound code over a wholesale rewrite.

## 19. Rollback

Preserve working states and make small commits.

If a change fails:

1. revert the affected change
2. restore working behavior
3. document the failure
4. revise
5. retest

Never weaken the permission boundary for compatibility.

## 20. Completion Gate

```text
OBSERVE
 ↓
PLAN
 ↓
ASK / APPROVE when required
 ↓
AUTHORIZE
 ↓
EXECUTE
 ↓
VERIFY
 ↓
LOG
 ↓
REPORT
```

Only after this lifecycle is demonstrably enforced should Phase 2 begin.
