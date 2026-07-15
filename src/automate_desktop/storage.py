from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QStandardPaths

from automate_core.models import ScanReport


class HistoryStore:
    def __init__(self) -> None:
        base = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
        self.directory = base / "history"

    def save(self, report: ScanReport) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self.directory / f"{report.scan_id}.json"
        target.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    def load(self) -> list[ScanReport]:
        if not self.directory.exists():
            return []
        reports: list[ScanReport] = []
        for path in self.directory.glob("*.json"):
            try:
                reports.append(ScanReport.from_dict(json.loads(path.read_text(encoding="utf-8"))))
            except (OSError, TypeError, KeyError, json.JSONDecodeError):
                continue
        return sorted(reports, key=lambda report: report.created_at, reverse=True)
