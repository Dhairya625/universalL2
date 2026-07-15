"""Local, read-only repository intelligence used by Automate Desktop."""

from automate_core.engine import scan_repository
from automate_core.models import Finding, ProposedTask, ScanReport, TaskReviewState

__all__ = ["Finding", "ProposedTask", "ScanReport", "TaskReviewState", "scan_repository"]
