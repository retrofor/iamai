---
status: accepted
---

# Control declared Tool calls inside an Environment

Controlled Tool execution belongs to a provisional Harness Environment. `ControlledToolEnvironment` treats each non-final `Action` as one Tool attempt, while a final `Action` terminates the Environment without becoming a Tool call. It does not reuse the stable messaging Runtime's `ToolRegistry` or `Permission` meanings.

Each Tool combines a callable implementation with a frozen, versioned `ToolSpec`. Before invoking the callable, the Environment checks the supported schema subset without coercion, applies a static default-deny `ExecutionPolicy`, verifies declared token and integer cost reservations against a run-scoped `ExecutionBudget`, and obtains an exact-request `ApprovalDecision` when required. A fresh per-invocation request nonce prevents a cached decision from authorizing a later otherwise-identical call. One `ControlledToolEnvironment` instance belongs to one Trial. A handled non-final Action records one `tool.call.outcome` before its non-terminating `Transition`; cancellation records a cancelled outcome before the Trial cancellation records.

The declaration, Policy, Budget, and Approver identity and configuration are covered by the Environment configuration hash. Implementations are not fingerprinted automatically, so callers must maintain honest Tool and Approver versions. `ToolResult` usage is trusted adapter evidence rather than an independently verified provider bill.

These controls do not provide OS, process, filesystem, network, credential, or Python capability isolation. The per-call timeout is cooperative, is shared by approval and Tool execution, and cannot revoke an external effect that already occurred. A Trajectory outcome is audit evidence, not a proof of safety, rollback, or external exactly-once execution.
