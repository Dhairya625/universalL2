from __future__ import annotations

import unittest

from automate_core import (
    AgentWorkState, TaskReviewState, WorkflowError, handoff_to_developer,
    next_agent_actions, transition_agent_work,
)
from automate_core.models import ProposedTask


def suggestion() -> ProposedTask:
    return ProposedTask(
        id="tsk_demo",
        title="Resolve repository gap",
        objective="Apply the approved remediation.",
        priority="normal",
        complexity="small",
        source_finding_ids=("fnd_demo",),
        affected_paths=("src/example.py",),
        acceptance_criteria=("Implement the change.", "Run focused tests."),
    )


class DeveloperWorkflowTests(unittest.TestCase):
    def test_handoff_requires_human_acceptance(self) -> None:
        task = suggestion()
        with self.assertRaisesRegex(WorkflowError, "accepted suggestion"):
            handoff_to_developer(task)
        self.assertEqual(task.agent_state, AgentWorkState.UNASSIGNED)

    def test_approved_work_moves_through_controlled_stages(self) -> None:
        task = suggestion()
        task.review_state = TaskReviewState.ACCEPTED
        handoff_to_developer(task, timestamp="2026-07-16T10:00:00+00:00")
        self.assertEqual(task.agent_state, AgentWorkState.QUEUED)
        self.assertIn(("Begin tracked work", AgentWorkState.IN_PROGRESS), next_agent_actions(task))

        for state in (
            AgentWorkState.IN_PROGRESS,
            AgentWorkState.VALIDATION,
            AgentWorkState.AWAITING_APPROVAL,
            AgentWorkState.COMPLETE,
        ):
            transition_agent_work(task, state, timestamp="2026-07-16T10:05:00+00:00")

        self.assertEqual(task.agent_state, AgentWorkState.COMPLETE)
        self.assertEqual(len(task.agent_activity), 5)

    def test_invalid_transition_is_rejected(self) -> None:
        task = suggestion()
        task.review_state = TaskReviewState.ACCEPTED
        handoff_to_developer(task)
        with self.assertRaisesRegex(WorkflowError, "Cannot move"):
            transition_agent_work(task, AgentWorkState.COMPLETE)


if __name__ == "__main__":
    unittest.main()
