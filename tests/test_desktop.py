from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from automate_core import scan_repository
from automate_desktop.mainwindow import MainWindow


class DesktopSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_renders_report(self) -> None:
        window = MainWindow()
        repository = Path(__file__).parents[1] / "examples" / "demo-repository"
        report = scan_repository(repository)
        window.current_report = report
        window._show_report(report)
        self.assertEqual(window.overview.metric_labels["findings"].text(), "3")
        self.assertEqual(window.findings_page.list.count(), 3)
        self.assertEqual(window.tasks_page.table.rowCount(), 3)
        window.close()


if __name__ == "__main__":
    unittest.main()
