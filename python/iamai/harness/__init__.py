"""Provisional headless harness for general-agent research trials."""

from ._components import ExactEvaluator, LookupEnvironment, ScriptedAgent
from ._controlled import (
    Approver,
    ApprovalDecision,
    ApprovalRequest,
    ControlledToolEnvironment,
    ExecutionBudget,
    ExecutionPolicy,
    Tool,
    ToolCallStatus,
    ToolResult,
    ToolSpec,
)
from ._experiment import Experiment, ExperimentPlan, ExperimentResult
from ._jsonl import JsonlTrajectoryStore
from ._model import (
    Action,
    Evaluation,
    Observation,
    Task,
    TrialConfig,
    TrialFailure,
    TrialResult,
    TrialStatus,
    Trajectory,
    TrajectoryRecord,
    Transition,
)
from ._replay import replay
from ._trial import Trial

__all__ = [
    "Action",
    "ApprovalDecision",
    "ApprovalRequest",
    "Approver",
    "ControlledToolEnvironment",
    "Evaluation",
    "ExactEvaluator",
    "Experiment",
    "ExperimentPlan",
    "ExperimentResult",
    "ExecutionBudget",
    "ExecutionPolicy",
    "JsonlTrajectoryStore",
    "LookupEnvironment",
    "Observation",
    "ScriptedAgent",
    "Task",
    "Tool",
    "ToolCallStatus",
    "ToolResult",
    "ToolSpec",
    "Trial",
    "TrialConfig",
    "TrialFailure",
    "TrialResult",
    "TrialStatus",
    "Trajectory",
    "TrajectoryRecord",
    "Transition",
    "replay",
]
