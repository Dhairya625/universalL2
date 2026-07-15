from __future__ import annotations

import ast
import hashlib
import io
import os
import re
import tokenize
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from automate_core.models import Evidence, FileRecord, Finding, Inventory, ProposedTask, ScanReport


EXCLUDED_DIRECTORIES = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "dist", "build",
    "coverage", ".next", ".cache", "__pycache__",
}
MAX_FILE_BYTES = 1_000_000
SOURCE_EXTENSIONS = {".py", ".pyi", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
MANIFESTS = {
    "package.json", "pyproject.toml", "requirements.txt", "poetry.lock", "uv.lock",
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
}
LANGUAGES = {
    ".py": "Python", ".pyi": "Python", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".json": "JSON", ".md": "Markdown", ".yaml": "YAML", ".yml": "YAML",
    ".toml": "TOML", ".swift": "Swift", ".go": "Go", ".rs": "Rust", ".java": "Java",
}
MARKER_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}


class ScanError(ValueError):
    pass


def scan_repository(repository: str | Path) -> ScanReport:
    root = Path(repository).expanduser().resolve()
    if not root.is_dir():
        raise ScanError(f"Repository is not a readable directory: {root}")
    files = _collect_files(root)
    if not files:
        raise ScanError("No readable files were found in the selected repository")
    fingerprint = _content_fingerprint(files)
    findings = [*_analyze_markers(root, files), *_analyze_test_gaps(files), *_analyze_coverage(root)]
    findings.sort(key=lambda finding: (SEVERITY_ORDER[finding.severity], finding.category, finding.id))
    finding_tuple = tuple(findings)
    return ScanReport(
        schema_version="automate.desktop-report/v1",
        scan_id="scn_" + _hash(fingerprint + "\0cross-platform-v1")[:20],
        repository_name=root.name,
        repository_path=str(root),
        content_fingerprint=fingerprint,
        created_at=datetime.now(timezone.utc).isoformat(),
        inventory=_build_inventory(files),
        findings=finding_tuple,
        proposed_tasks=_plan_tasks(finding_tuple),
    )


def _collect_files(root: Path) -> tuple[FileRecord, ...]:
    records: list[FileRecord] = []
    for current, directories, filenames in os.walk(root, topdown=True, followlinks=False):
        directories[:] = sorted(
            directory for directory in directories
            if directory not in EXCLUDED_DIRECTORIES and not (Path(current) / directory).is_symlink()
        )
        for filename in sorted(filenames):
            path = Path(current) / filename
            if path.is_symlink():
                continue
            try:
                size = path.stat().st_size
                if size > MAX_FILE_BYTES:
                    continue
                data = path.read_bytes()
            except (OSError, PermissionError):
                continue
            relative = path.relative_to(root).as_posix()
            records.append(
                FileRecord(
                    path=relative,
                    size=size,
                    digest=hashlib.sha256(data).hexdigest(),
                    language=LANGUAGES.get(path.suffix.lower(), "Other"),
                    categories=frozenset(_categories(relative, path.suffix.lower())),
                )
            )
    return tuple(sorted(records, key=lambda record: record.path))


def _categories(path: str, extension: str) -> set[str]:
    lower = path.lower()
    parts = lower.split("/")
    filename = parts[-1]
    result: set[str] = set()
    if filename in MANIFESTS:
        result.add("manifest")
    if filename.startswith("readme") or "docs" in parts or extension == ".md":
        result.add("documentation")
    if "test" in parts or "tests" in parts or filename.startswith("test_") or ".test." in filename or ".spec." in filename:
        result.add("test")
    if lower.startswith(".github/workflows/") or filename in {"gitlab-ci.yml", ".gitlab-ci.yml", "jenkinsfile"}:
        result.add("ci")
    if extension in SOURCE_EXTENSIONS:
        result.add("source")
    return result


def _analyze_markers(root: Path, files: tuple[FileRecord, ...]) -> list[Finding]:
    findings: list[Finding] = []
    for record in files:
        if "source" not in record.categories or "test" in record.categories:
            continue
        if record.language not in {"Python", "TypeScript", "JavaScript"}:
            continue
        try:
            text = (root / record.path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if record.language == "Python":
            findings.extend(_analyze_python(record, text))
        else:
            findings.extend(_analyze_ecmascript(record, text))
    return findings


def _analyze_python(record: FileRecord, text: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()
    try:
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            if token.type == tokenize.COMMENT and (marker := MARKER_PATTERN.search(token.string)):
                findings.append(_marker_finding(record.path, token.start[0], token.string, marker.group(1)))
    except (IndentationError, tokenize.TokenError):
        pass
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return findings
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise) or node.exc is None:
            continue
        exception = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
        if isinstance(exception, ast.Name) and exception.id == "NotImplementedError":
            line = node.lineno
            excerpt = lines[line - 1] if line <= len(lines) else "raise NotImplementedError"
            findings.append(_stub_finding(record.path, line, excerpt))
    return findings


def _analyze_ecmascript(record: FileRecord, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        comment = line.split("//", 1)[1] if "//" in line else None
        if comment and (marker := MARKER_PATTERN.search(comment)):
            findings.append(_marker_finding(record.path, line_number, line, marker.group(1)))
        code = line.split("//", 1)[0]
        if "throw new Error" in code and re.search(r"not implemented|todo", code, re.IGNORECASE):
            findings.append(_stub_finding(record.path, line_number, line))
    return findings


def _marker_finding(path: str, line: int, excerpt: str, label: str) -> Finding:
    title = f"{label.upper()} marker requires review"
    return _finding(
        "implementation_marker", title, "low", 0.92,
        "An explicit developer marker appears in a source comment.",
        "Unresolved markers can represent unfinished work, known defects, or intentional debt.",
        "Review the marker and complete, track, or remove the referenced work.",
        "unknown", path, line, excerpt,
    )


def _stub_finding(path: str, line: int, excerpt: str) -> Finding:
    return _finding(
        "implementation_stub", "Explicit implementation stub detected", "medium", 0.97,
        "The source uses a conventional explicit not-implemented construct.",
        "A reachable stub can cause runtime failure or leave a promised capability incomplete.",
        "Confirm the path is intentionally abstract or implement it with focused tests.",
        "unknown", path, line, excerpt,
    )



def _analyze_coverage(root: Path) -> list[Finding]:
    findings: list[Finding] = []

    # Check for coverage.xml
    coverage_xml = root / "coverage.xml"
    if coverage_xml.is_file():
        try:
            tree = ET.parse(coverage_xml)
            for cls in tree.findall(".//class"):
                filename = cls.attrib.get("filename")
                line_rate = float(cls.attrib.get("line-rate", 1.0))
                if filename and line_rate < 0.6:  # Less than 60% coverage
                    findings.append(
                        _finding(
                            "test_gap_candidate", "Low test coverage detected", "medium", 0.90,
                            f"Coverage report indicates {line_rate:.0%} line coverage for this file.",
                            "Low test coverage increases regression risk.",
                            "Write tests to cover critical execution paths.",
                            "medium", filename, 1, f"line-rate: {line_rate}"
                        )
                    )
        except Exception:
            pass

    # Check for lcov.info
    lcov_info = root / "lcov.info"
    if lcov_info.is_file():
        try:
            current_file = None
            lines_found = 0
            lines_hit = 0
            with open(lcov_info, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("SF:"):
                        current_file = line[3:]
                    elif line.startswith("LF:"):
                        lines_found = int(line[3:])
                    elif line.startswith("LH:"):
                        lines_hit = int(line[3:])
                    elif line == "end_of_record" and current_file and lines_found > 0:
                        coverage = lines_hit / lines_found
                        if coverage < 0.6:
                            findings.append(
                                _finding(
                                    "test_gap_candidate", "Low test coverage detected", "medium", 0.90,
                                    f"LCOV report indicates {coverage:.0%} line coverage for this file.",
                                    "Low test coverage increases regression risk.",
                                    "Write tests to cover critical execution paths.",
                                    "medium", current_file, 1, f"coverage: {coverage:.2f}"
                                )
                            )
                        current_file = None
                        lines_found = 0
                        lines_hit = 0
        except Exception:
            pass

    return findings

def _analyze_test_gaps(files: tuple[FileRecord, ...]) -> list[Finding]:
    supported = {"Python", "TypeScript", "JavaScript"}
    test_stems = {_normalized_stem(record.path) for record in files if "test" in record.categories and record.language in supported}
    ignored = {"__init__", "index", "main", "setup", "conftest"}
    findings: list[Finding] = []
    for record in files:
        if "source" not in record.categories or "test" in record.categories or record.language not in supported:
            continue
        stem = _normalized_stem(record.path)
        if stem in ignored or stem in test_stems:
            continue
        title = "No conventionally mapped test file found"
        findings.append(
            Finding(
                id="fnd_" + _hash("\0".join(("test-gaps", "test_gap_candidate", record.path, title)))[:16],
                analyzer="builtin.test-gaps",
                analyzer_version="1.0.0",
                category="test_gap_candidate",
                title=title,
                severity="low",
                confidence=0.55,
                confidence_explanation="No same-stem test filename was found; indirect coverage may still exist.",
                why_it_matters="Source without discoverable tests may carry regression risk and deserves human review.",
                remediation="Verify actual coverage and add focused tests if important behavior is not exercised.",
                complexity="small-to-medium",
                evidence=(Evidence(record.path, "inventory_fact", "No conventionally mapped test filename exists in this snapshot."),),
            )
        )
    return findings


def _finding(category: str, title: str, severity: str, confidence: float, confidence_explanation: str,
             why: str, remediation: str, complexity: str, path: str, line: int, excerpt: str) -> Finding:
    return Finding(
        id="fnd_" + _hash("\0".join(("builtin.markers", category, path, str(line), title)))[:16],
        analyzer="builtin.markers",
        analyzer_version="1.0.0",
        category=category,
        title=title,
        severity=severity,
        confidence=confidence,
        confidence_explanation=confidence_explanation,
        why_it_matters=why,
        remediation=remediation,
        complexity=complexity,
        evidence=(Evidence(path, "source_excerpt", "Explicit source evidence detected by a deterministic analyzer.", line, excerpt.strip()),),
    )


def _plan_tasks(findings: tuple[Finding, ...]) -> list[ProposedTask]:
    priorities = {"critical": "urgent", "high": "high", "medium": "normal", "low": "low", "informational": "backlog"}
    criteria = {
        "implementation_marker": ("Review the marker in context.", "Complete or explicitly track the work.", "Run relevant tests."),
        "implementation_stub": ("Confirm or replace the stub.", "Add focused automated coverage.", "Remove reachable not-implemented failures."),
        "test_gap_candidate": ("Document indirect coverage or add tests.", "Cover success and failure behavior.", "Run the relevant test suite."),
    }
    return [
        ProposedTask(
            id="tsk_" + _hash(finding.id + "\0" + finding.title)[:16],
            title=f"Review and resolve: {finding.title}",
            objective=finding.remediation,
            priority=priorities[finding.severity],
            complexity=finding.complexity,
            source_finding_ids=(finding.id,),
            affected_paths=tuple(sorted({evidence.path for evidence in finding.evidence})),
            acceptance_criteria=criteria.get(finding.category, ("Validate the finding.", "Apply an approved remediation.", "Run relevant checks.")),
        )
        for finding in findings
    ]


def _build_inventory(files: tuple[FileRecord, ...]) -> Inventory:
    languages = Counter(record.language for record in files)
    categories = Counter(category for record in files for category in record.categories)
    return Inventory(
        file_count=len(files),
        total_bytes=sum(record.size for record in files),
        languages=dict(sorted(languages.items())),
        category_counts=dict(sorted(categories.items())),
        manifests=tuple(record.path for record in files if "manifest" in record.categories),
        ci_files=tuple(record.path for record in files if "ci" in record.categories),
        documentation_files=tuple(record.path for record in files if "documentation" in record.categories),
        test_files=tuple(record.path for record in files if "test" in record.categories),
    )


def _normalized_stem(path: str) -> str:
    name = Path(path).name.lower()
    if name.startswith("test_"):
        name = name[5:]
    for token in (".test.", ".spec."):
        if token in name:
            name = name.split(token, 1)[0]
    return name.split(".", 1)[0]


def _content_fingerprint(files: tuple[FileRecord, ...]) -> str:
    return _hash("\0".join(value for record in files for value in (record.path, record.digest)))


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
