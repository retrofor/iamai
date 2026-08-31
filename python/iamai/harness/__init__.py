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
from ._evidence import ExperimentComparison, TrialComparison, compare_experiment
from ._experiment import (
    Experiment,
    ExperimentPlan,
    ExperimentResult,
    TaskDistributionManifest,
)
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
    "ExperimentComparison",
    "ExperimentPlan",
    "ExperimentResult",
    "ExecutionBudget",
    "ExecutionPolicy",
    "JsonlTrajectoryStore",
    "LookupEnvironment",
    "Observation",
    "ScriptedAgent",
    "Task",
    "TaskDistributionManifest",
    "Tool",
    "ToolCallStatus",
    "ToolResult",
    "ToolSpec",
    "Trial",
    "TrialComparison",
    "TrialConfig",
    "TrialFailure",
    "TrialResult",
    "TrialStatus",
    "Trajectory",
    "TrajectoryRecord",
    "Transition",
    "compare_experiment",
    "replay",
]
