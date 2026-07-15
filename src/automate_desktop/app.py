from __future__ import annotations

import os
import sys

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from automate_desktop.mainwindow import MainWindow
from automate_desktop.theme import APP_STYLESHEET


def main() -> int:
    # Approved direction: one Qt desktop codebase for macOS, Windows, and Linux.
    # It is a local application, not a browser UI or local web server.
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
