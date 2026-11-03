#!/usr/bin/env python3
"""Top-level entry point used by the PyInstaller build / Setup.exe.

This mirrors `gui.main` so a frozen single-file build can start the app
without relying on package-relative imports.
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from gui.main_window import MainWindow
from gui.styles import STYLESHEET


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Downloader Bot")
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
