from __future__ import annotations

import os
import sys

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from automate_desktop.mainwindow import MainWindow
from automate_desktop.theme import APP_STYLESHEET


def main() -> int:
    # Approved direction: a Linear-inspired, keyboard-first Qt workspace for
    # macOS, Windows, and Linux. It remains a local desktop application.
    QCoreApplication.setOrganizationName("Automate")
    QCoreApplication.setApplicationName("Automate")
    QCoreApplication.setApplicationVersion("0.2.0")
    if sys.platform.startswith("linux"):
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    app = QApplication(sys.argv)
    app.setApplicationDisplayName("Automate")
    app.setFont(QFont("Inter", 11))
    app.setStyleSheet(APP_STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()
