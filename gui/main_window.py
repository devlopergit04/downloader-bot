"""Main window of the graphical download manager."""

from __future__ import annotations

import os
import subprocess
import sys
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView, QFileDialog, QHeaderView, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from .styles import STYLESHEET
from .workers import DownloadWorker

STATUS_QUEUED = "queued"
STATUS_DOWNLOADING = "downloading"
STATUS_PAUSED = "paused"
STATUS_COMPLETED = "completed"
STATUS_ERROR = "error"
STATUS_CANCELLED = "cancelled"


@dataclass
class DownloadEntry:
    url: str
    name: str
    status: str = STATUS_QUEUED
    progress: int = 0
    speed: str = ""
    worker: DownloadWorker | None = field(default=None, repr=False)
    path: str = ""
    error: str = ""


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Downloader Bot — پنل دانلود")
        self.resize(900, 560)

        self.downloads: dict[int, DownloadEntry] = {}
        self._next_id = 0
        self.download_dir = str(Path.home() / "Downloads" / "downloader-bot")
        os.makedirs(self.download_dir, exist_ok=True)

        self._build_ui()
        self._build_menu()

    # -- UI construction -----------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # --- input row ---
        input_row = QHBoxLayout()
        self.url_edit = QLineEdit(self)
        self.url_edit.setPlaceholderText(
            "یک لینک بنویسید… (YouTube، Instagram، TikTok، X، فایل مستقیم، …)"
        )
        self.url_edit.returnPressed.connect(self.add_downloads)
        btn_add = QPushButton("➕ افزودن و دانلود", objectName="primary")
        btn_add.clicked.connect(self.add_downloads)
        btn_add.setMinimumWidth(170)
        input_row.addWidget(self.url_edit, 1)
        input_row.addWidget(btn_add)
        root.addLayout(input_row)

        # --- action row ---
        actions = QHBoxLayout()
        self.btn_pause = QPushButton("⏸️ pause")
        self.btn_pause.clicked.connect(self.toggle_pause)
        self.btn_cancel = QPushButton("🗑️ حذف", objectName="danger")
        self.btn_cancel.clicked.connect(self.cancel_selected)
        self.btn_open = QPushButton("📁 باز کردن folder")
        self.btn_open.clicked.connect(self.open_folder)
        self.btn_clear = QPushButton("🧹 پاک‌سازی completion")
        self.btn_clear.clicked.connect(self.clear_completed)
        for b in (self.btn_pause, self.btn_cancel, self.btn_open, self.btn_clear):
            b.setEnabled(False)
            actions.addWidget(b)
        actions.addStretch(1)
        self.lbl_dir = QLabel(f"📁 {self.download_dir}", objectName="muted")
        actions.addWidget(self.lbl_dir)
        root.addLayout(actions)

        # --- table ---
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["نام / لینک", "وضعیت", "پیشرفت", "speed / حجم"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnWidth(1, 130)
        self.table.itemSelectionChanged.connect(self._on_selection)
        root.addWidget(self.table, 1)

        # --- progress bar for selected ---
        self.overall = QProgressBar()
        self.overall.setFormat("آماده")
        self.overall.setValue(0)
        root.addWidget(self.overall)

        self.statusBar().showMessage("آماده")

    def _build_menu(self) -> None:
        m_file = self.menuBar().addMenu("⚙️‌ تنظیمات")
        act_dir = QAction("مسیر دانلود…", self)
        act_dir.triggered.connect(self.change_dir)
        m_file.addAction(act_dir)
        m_file.addSeparator()
        act_exit = QAction("خروج", self)
        act_exit.triggered.connect(self.close)
        m_file.addAction(act_exit)

        m_help = self.menuBar().addMenu("❓ کمک")
        act_about = QAction("درباره", self)
        act_about.triggered.connect(self.about)
        m_help.addAction(act_about)

    # -- adding / managing ---------------------------------------------------
    def add_downloads(self) -> None:
        text = self.url_edit.text().strip()
        if not text:
            return
        # Accept one URL per line, or a single URL.
        urls = [u.strip() for u in text.splitlines() if u.strip()]
        for url in urls:
            self._add_one(url)
        self.url_edit.clear()
        if self.downloads:
            self._start_free()
        self.statusBar().showMessage(f"{len(urls)} دانلود افزوده شد")

    def _add_one(self, url: str) -> None:
        self._next_id += 1
        entry = DownloadEntry(url=url, name=_friendly_name(url))
        self.downloads[self._next_id] = entry
        row = self.table.rowCount()
        self.table.insertRow(row)
        self._fill_row(row, entry)
        self._refresh_buttons()

    def _fill_row(self, row: int, e: DownloadEntry) -> None:
        self.table.setItem(row, 0, QTableWidgetItem(e.name))
        self.table.setItem(row, 1, QTableWidgetItem(_status_label(e.status)))
        self.table.setItem(row, 3, QTableWidgetItem(e.speed))
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(e.progress)
        bar.setFormat(f"{e.progress}%")
        self.table.setCellWidget(row, 2, bar)

    def _refresh_buttons(self) -> None:
        has = bool(self.downloads)
        for b in (self.btn_pause, self.btn_cancel, self.btn_open, self.btn_clear):
            b.setEnabled(has)

    def _start_free(self) -> None:
        """Start any queued download (respects a light concurrency cap)."""
        running = sum(1 for e in self.downloads.values()
                      if e.status == STATUS_DOWNLOADING)
        for e in self.downloads.values():
            if e.status == STATUS_QUEUED and running < 3:
                self._start(e)
                running += 1

    def _start(self, e: DownloadEntry) -> None:
        e.status = STATUS_DOWNLOADING
        e.progress = 0
        worker = DownloadWorker(e.url, self.download_dir)
        worker.progress.connect(self._on_progress)
        worker.status.connect(self._on_status)
        worker.finished_ok.connect(self._on_done)
        worker.failed.connect(self._on_error)
        worker.finished.connect(lambda _w=worker: self._start_free())
        e.worker = worker
        worker.start()
        self._set_status(e, STATUS_DOWNLOADING)

    # -- worker signal handlers (marshalled to GUI thread) -------------------
    def _on_progress(self, pct: int, speed: str) -> None:
        e = self._current_or_last()
        if e is None:
            return
        e.progress = pct
        e.speed = speed
        row = self._row_of(e)
        if row is not None:
            bar = self.table.cellWidget(row, 2)
            if isinstance(bar, QProgressBar):
                bar.setValue(pct)
                bar.setFormat(f"{pct}%")
            item = self.table.item(row, 3)
            if item:
                item.setText(speed)

    def _on_status(self, text: str) -> None:
        e = self._current_or_last()
        if e is not None:
            e.speed = text if not e.speed else e.speed
            self.statusBar().showMessage(text, 3000)

    def _on_done(self, path: str) -> None:
        e = self._current_or_last()
        if e is None:
            return
        e.status = STATUS_COMPLETED
        e.path = path
        e.progress = 100
        e.speed = ""
        self._set_status(e, STATUS_COMPLETED)
        self.statusBar().showMessage(f"✅ کامل شد: {path}", 5000)

    def _on_error(self, msg: str) -> None:
        e = self._current_or_last()
        if e is None:
            return
        e.status = STATUS_ERROR
        e.error = msg
        self._set_status(e, STATUS_ERROR)
        self.table.item(self._row_of(e) or 0, 3).setText(msg)

    def _current_or_last(self) -> DownloadEntry | None:
        rows = self.table.selectionModel().selectedRows()
        if rows:
            rid = rows[0].data()
            if rid in self.downloads:
                return self.downloads[rid]
        # fallback: last active
        for e in reversed(list(self.downloads.values())):
            if e.status == STATUS_DOWNLOADING:
                return e
        return None

    def _row_of(self, e: DownloadEntry) -> int | None:
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).data() == e.name:
                return row
        return None

    def _set_status(self, e: DownloadEntry, status: str) -> None:
        e.status = status
        row = self._row_of(e)
        if row is not None:
            self.table.item(row, 1).setText(_status_label(status))

    # -- actions --------------------------------------------------------------
    def _selected_entries(self) -> list[DownloadEntry]:
        rows = self.table.selectionModel().selectedRows()
        out = []
        for r in rows:
            rid = r.data()
            if rid in self.downloads:
                out.append(self.downloads[rid])
        return out

    def toggle_pause(self) -> None:
        for e in self._selected_entries():
            if e.status == STATUS_DOWNLOADING and e.worker:
                e.worker.cancel()
                e.status = STATUS_PAUSED
                self._set_status(e, STATUS_PAUSED)
            elif e.status in (STATUS_PAUSED, STATUS_QUEUED):
                self._start(e)

    def cancel_selected(self) -> None:
        for e in self._selected_entries():
            if e.worker:
                e.worker.cancel()
            e.status = STATUS_CANCELLED
            e.progress = 0
            e.speed = ""
            self._set_status(e, STATUS_CANCELLED)

    def open_folder(self) -> None:
        for e in self._selected_entries():
            if e.path and os.path.exists(e.path):
                folder = os.path.dirname(e.path) or self.download_dir
            elif os.path.exists(self.download_dir):
                folder = self.download_dir
            else:
                folder = self.download_dir
                os.makedirs(folder, exist_ok=True)
            _open_in_file_manager(folder)

    def clear_completed(self) -> None:
        for rid in [i for i, e in self.downloads.items()
                    if e.status in (STATUS_COMPLETED, STATUS_CANCELLED,
                                    STATUS_ERROR)]:
            e = self.downloads.pop(rid)
            row = self._row_of(e)
            if row is not None:
                self.table.removeRow(row)
        self._refresh_buttons()

    def change_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "مسیر دانلود",
                                              self.download_dir)
        if d:
            os.makedirs(d, exist_ok=True)
            self.download_dir = d
            self.lbl_dir.setText(f"📁 {d}")
            self.statusBar().showMessage(f"مسیر به {d} تغییر کرد", 4000)

    def about(self) -> None:
        QMessageBox.about(
            self, "درباره",
            "<h3>Downloader Bot</h3>"
            "<p>پنل گرافیکی دانلود ویدئو، صدا، تصویر و فایل از هزاران سایت.</p>"
            "<p> motors: yt-dlp · gallery-dl · HTTP</p>"
            "<p style='color:#6ee7b7'>ساخته شده با PyQt6</p>",
        )

    def _on_selection(self) -> None:
        entries = self._selected_entries()
        if not entries:
            self.overall.setFormat("آماده")
            self.overall.setValue(0)
            return
        e = entries[0]
        self.overall.setValue(e.progress)
        self.overall.setFormat(f"{e.progress}% — {e.speed}")

    # -- shutdown ---------------------------------------------------------------
    def closeEvent(self, event) -> None:
        for e in self.downloads.values():
            if e.worker and e.status == STATUS_DOWNLOADING:
                e.worker.cancel()
                e.worker.wait(3000)
        event.accept()


# -- helpers -------------------------------------------------------------------
class QLineEditPlaceholder:
    """(legacy shim — unused; kept for reference)"""
    pass


def _friendly_name(url: str) -> str:
    try:
        from urllib.parse import urlparse
        path = urlparse(url).path
        last = path.rstrip("/").split("/")[-1]
        if last:
            return last[:60] or url
    except Exception:
        pass
    return url[:60]


def _status_label(status: str) -> str:
    return {
        STATUS_QUEUED: "⏳ در صف",
        STATUS_DOWNLOADING: "⬇️ دانلود",
        STATUS_PAUSED: "⏸️ متوقف",
        STATUS_COMPLETED: "✅ کامل",
        STATUS_ERROR: "❌ خطا",
        STATUS_CANCELLED: "🗑️ حذف‌شده",
    }.get(status, status)


def _open_in_file_manager(path: str) -> None:
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        webbrowser.open("file://" + path)
