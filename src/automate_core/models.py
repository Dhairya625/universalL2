from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class TaskReviewState(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEFERRED = "deferred"


@dataclass(frozen=True)
class Evidence:
    path: str
    kind: str
    detail: str
    line: int | None = None
    excerpt: str | None = None

    @property
    def location(self) -> str:
        return f"{self.path}:{self.line}" if self.line else self.path


@dataclass(frozen=True)
class Finding:
    id: str
    analyzer: str
    analyzer_version: str
    category: str
    title: str
    severity: str
    confidence: float
    confidence_explanation: str
    why_it_matters: str
    remediation: str
    complexity: str
    evidence: tuple[Evidence, ...]


@dataclass
class ProposedTask:
    id: str
    title: str
    objective: str
    priority: str
    complexity: str
    source_finding_ids: tuple[str, ...]
    affected_paths: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    review_state: str = TaskReviewState.PROPOSED


@dataclass(frozen=True)
class Inventory:
    file_count: int
    total_bytes: int
    languages: dict[str, int]
    category_counts: dict[str, int]
    manifests: tuple[str, ...]
    ci_files: tuple[str, ...]
    documentation_files: tuple[str, ...]
    test_files: tuple[str, ...]


@dataclass
class ScanReport:
    schema_version: str
    scan_id: str
    repository_name: str
    repository_path: str
    content_fingerprint: str
    created_at: str
    inventory: Inventory
    findings: tuple[Finding, ...]
    proposed_tasks: list[ProposedTask]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ScanReport":
        inventory = Inventory(**payload["inventory"])
        findings = tuple(
            Finding(
                **{
                    **item,
                    "evidence": tuple(Evidence(**evidence) for evidence in item["evidence"]),
                }
            )
            for item in payload["findings"]
        )
        tasks = [
            ProposedTask(
                **{
                    **item,
                    "source_finding_ids": tuple(item["source_finding_ids"]),
                    "affected_paths": tuple(item["affected_paths"]),
                    "acceptance_criteria": tuple(item["acceptance_criteria"]),
                }
            )
            for item in payload["proposed_tasks"]
        ]
        return cls(
            **{
                **payload,
                "inventory": inventory,
                "findings": findings,
                "proposed_tasks": tasks,
            }
        )


@dataclass(frozen=True)
class FileRecord:
    path: str
    size: int
    digest: str
    language: str
    categories: frozenset[str] = field(default_factory=frozenset)
