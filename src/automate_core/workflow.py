from __future__ import annotations

from datetime import datetime, timezone

from automate_core.models import AgentWorkState, ProposedTask, TaskReviewState


class WorkflowError(ValueError):
    """Raised when a human or agent workflow transition is not permitted."""


AGENT_TRANSITIONS: dict[str, frozenset[str]] = {
    AgentWorkState.UNASSIGNED: frozenset({AgentWorkState.QUEUED}),
    AgentWorkState.QUEUED: frozenset({AgentWorkState.IN_PROGRESS, AgentWorkState.BLOCKED}),
    AgentWorkState.IN_PROGRESS: frozenset({AgentWorkState.VALIDATION, AgentWorkState.BLOCKED}),
    AgentWorkState.VALIDATION: frozenset({AgentWorkState.AWAITING_APPROVAL, AgentWorkState.IN_PROGRESS, AgentWorkState.BLOCKED}),
    AgentWorkState.AWAITING_APPROVAL: frozenset({AgentWorkState.COMPLETE, AgentWorkState.IN_PROGRESS}),
    AgentWorkState.BLOCKED: frozenset({AgentWorkState.QUEUED, AgentWorkState.IN_PROGRESS}),
    AgentWorkState.COMPLETE: frozenset(),
}


def handoff_to_developer(task: ProposedTask, *, timestamp: str | None = None) -> None:
    if str(task.review_state) != TaskReviewState.ACCEPTED:
        raise WorkflowError("Only an accepted suggestion can be sent to the developer agent.")
    if str(task.agent_state) != AgentWorkState.UNASSIGNED:
        raise WorkflowError("This suggestion has already entered the developer workflow.")
    now = timestamp or _now()
    task.agent_state = AgentWorkState.QUEUED
    task.assigned_at = now
    task.agent_updated_at = now
    _record(task, now, "Suggestion approved and added to the developer queue.")


def transition_agent_work(task: ProposedTask, target: str, *, timestamp: str | None = None) -> None:
    current = str(task.agent_state)
    try:
        target_state = AgentWorkState(target)
    except ValueError as exc:
        raise WorkflowError(f"Unknown developer workflow state: {target}") from exc
    if target_state not in AGENT_TRANSITIONS.get(current, frozenset()):
        raise WorkflowError(f"Cannot move developer work from {current} to {target_state}.")
    now = timestamp or _now()
    task.agent_state = target_state
    task.agent_updated_at = now
    _record(task, now, f"Developer workflow moved from {current} to {target_state}.")


def next_agent_actions(task: ProposedTask) -> tuple[tuple[str, str], ...]:
    actions: dict[str, tuple[tuple[str, str], ...]] = {
        AgentWorkState.QUEUED: (("Begin tracked work", AgentWorkState.IN_PROGRESS), ("Mark blocked", AgentWorkState.BLOCKED)),
        AgentWorkState.IN_PROGRESS: (("Send to validation", AgentWorkState.VALIDATION), ("Mark blocked", AgentWorkState.BLOCKED)),
        AgentWorkState.VALIDATION: (("Request human approval", AgentWorkState.AWAITING_APPROVAL), ("Return to development", AgentWorkState.IN_PROGRESS)),
        AgentWorkState.AWAITING_APPROVAL: (("Approve completion", AgentWorkState.COMPLETE), ("Request changes", AgentWorkState.IN_PROGRESS)),
        AgentWorkState.BLOCKED: (("Return to queue", AgentWorkState.QUEUED), ("Resume work", AgentWorkState.IN_PROGRESS)),
    }
    return actions.get(str(task.agent_state), ())


def _record(task: ProposedTask, timestamp: str, message: str) -> None:
    task.agent_activity = (*task.agent_activity, f"{timestamp} | {message}")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
