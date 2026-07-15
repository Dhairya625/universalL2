from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from automate_core import ScanReport, scan_repository


class CoreScannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repository"
        (self.root / "src").mkdir(parents=True)
        (self.root / "tests").mkdir()
        (self.root / "node_modules" / "ignored").mkdir(parents=True)
        (self.root / "src" / "app.py").write_text(
            "def greet():\n    # TODO: localize\n    return 'hello'\n", encoding="utf-8"
        )
        (self.root / "src" / "payments.py").write_text(
            "def charge():\n    raise NotImplementedError\n", encoding="utf-8"
        )
        (self.root / "tests" / "test_app.py").write_text(
            "def test_greet():\n    assert True\n", encoding="utf-8"
        )
        (self.root / "node_modules" / "ignored" / "index.js").write_text("// TODO hidden\n")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_scan_is_repeatable_evidence_backed_and_read_only(self) -> None:
        before = {path.relative_to(self.root).as_posix(): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        first = scan_repository(self.root)
        second = scan_repository(self.root)
        after = {path.relative_to(self.root).as_posix(): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(first.scan_id, second.scan_id)
        self.assertEqual(before, after)
        self.assertEqual(first.inventory.file_count, 3)
        self.assertEqual(len(first.findings), 3)
        self.assertEqual(len(first.proposed_tasks), 3)
        self.assertTrue(all(finding.evidence for finding in first.findings))
        self.assertEqual(
            {finding.category for finding in first.findings},
            {"implementation_marker", "implementation_stub", "test_gap_candidate"},
        )

    def test_report_round_trip_preserves_review_state(self) -> None:
        report = scan_repository(self.root)
        report.proposed_tasks[0].review_state = "accepted"
        restored = ScanReport.from_dict(json.loads(json.dumps(report.to_dict())))
        self.assertEqual(restored.scan_id, report.scan_id)
        self.assertEqual(restored.proposed_tasks[0].review_state, "accepted")


if __name__ == "__main__":
    unittest.main()
