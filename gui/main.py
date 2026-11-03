"""Entry point for the graphical download manager.

Run with:  python -m gui.main
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow
from .styles import STYLESHEET


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Downloader Bot")
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
