"""Local, read-only repository intelligence used by Automate Desktop."""

from automate_core.engine import scan_repository
from automate_core.models import AgentWorkState, Finding, ProposedTask, ScanReport, TaskReviewState
from automate_core.workflow import WorkflowError, handoff_to_developer, next_agent_actions, transition_agent_work

__all__ = [
    "AgentWorkState", "Finding", "ProposedTask", "ScanReport", "TaskReviewState",
    "WorkflowError", "handoff_to_developer", "next_agent_actions", "scan_repository",
    "transition_agent_work",
]
