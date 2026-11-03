"""Dark-green Qt stylesheet (QSS) for the download manager."""

STYLESHEET = """
QWidget {
    background-color: #021a15;
    color: #ecfdf5;
    font-family: "Segoe UI", "Tahoma", sans-serif;
    font-size: 13px;
}

QMainWindow, QDialog {
    background-color: #021a15;
}

QLabel {
    color: #ecfdf5;
}
QLabel#muted { color: #6ee7b7; }
QLabel#accent { color: #34d399; font-weight: 700; }

QLineEdit, QComboBox, QSpinBox {
    background-color: #022c22;
    border: 1px solid #064e3b;
    border-radius: 8px;
    padding: 6px 8px;
    selection-background-color: #10b981;
    color: #ecfdf5;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #10b981;
}

QPushButton {
    background-color: #065f46;
    color: #ecfdf5;
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover { background-color: #10b981; color: #021a15; }
QPushButton:pressed { background-color: #064e3b; }
QPushButton:disabled { background-color: #064e3b; color: #4b5563; }
QPushButton#primary { background-color: #10b981; color: #021a15; }
QPushButton#primary:hover { background-color: #34d399; }
QPushButton#danger { background-color: #7f1d1d; }
QPushButton#danger:hover { background-color: #b91c1c; color: #ecfdf5; }

QHeaderView::section {
    background-color: #022c22;
    color: #a7f3d0;
    border: none;
    border-right: 1px solid #064e3b;
    padding: 8px;
    font-weight: 700;
}
QTableWidget {
    background-color: #022c22;
    border: 1px solid #064e3b;
    border-radius: 8px;
    gridline-color: #064e3b;
    alternate-background-color: #043b30;
}
QTableWidget::item { padding: 6px; }
QTableWidget::item:selected { background-color: #10b981; color: #021a15; }

QProgressBar {
    background-color: #064e3b;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
    color: #ecfdf5;
    font-size: 10px;
}
QProgressBar::chunk {
    background-color: #10b981;
    border-radius: 6px;
}

QStatusBar { background-color: #022c22; color: #a7f3d0; }
QStatusBar::item { border: none; }

QGroupBox {
    border: 1px solid #064e3b;
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 10px;
    color: #34d399;
    font-weight: 700;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}

QMenuBar { background-color: #022c22; color: #ecfdf5; }
QMenuBar::item:selected { background-color: #065f46; }
QMenu { background-color: #022c22; border: 1px solid #064e3b; }
QMenu::item:selected { background-color: #10b981; color: #021a15; }

QToolTip {
    background-color: #022c22;
    color: #ecfdf5;
    border: 1px solid #10b981;
    border-radius: 6px;
}
"""
