"""Background download workers for the GUI.

Each download runs in its own QThread. The engines are driven through their
**Python APIs** (not subprocesses) so the same code works in a PyInstaller
frozen Setup.exe: in a frozen app `sys.executable -m yt_dlp` cannot run.
Progress is marshalled to the GUI thread through Qt signals.

Cancellation:
- yt-dlp  — raises from its progress hook (yt-dlp propagates it up)
- gallery-dl — best-effort via a flag checked around the run
- HTTP    — clean (the streaming loop checks the flag each chunk)
"""

from __future__ import annotations

import os
import re
import threading
from pathlib import Path

import requests
import yt_dlp
import gallery_dl

from PyQt6.QtCore import QThread, pyqtSignal

FORMAT = "bestvideo*+bestaudio/best,bestquality/best"

GALLERY_DOMAINS = (
    "instagram.com", "x.com", "twitter.com", "pikabu.ru", "behance.net",
    "deviantart.com", "500px.com", "flickr.com", "pinterest.com",
    "reddit.com", "imgur.com",
)
DIRECT_DOMAINS = ("github.com", "raw.githubusercontent.com",
                  "objects.githubusercontent.com")

# Extensions that are almost certainly direct files (not media sites).
FILE_EXT = (
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm",
    ".jar", ".bin", ".iso", ".img", ".apk", ".appx",
    ".csv", ".txt", ".json", ".xml", ".yaml", ".yml",
)


def _engine_for(url: str) -> str:
    low = url.lower()
    path = low.split("?")[0].split("#")[0]
    if any(d in low for d in DIRECT_DOMAINS):
        return "http"
    if any(path.endswith(ext) for ext in FILE_EXT):
        return "http"
    if any(d in low for d in GALLERY_DOMAINS):
        return "gallery"
    return "video"


class DownloadWorker(QThread):
    progress = pyqtSignal(int, str)   # percent, speed-text
    status = pyqtSignal(str)
    finished_ok = pyqtSignal(str)     # file path
    failed = pyqtSignal(str)

    def __init__(self, url: str, out_dir: str, parent=None) -> None:
        super().__init__(parent)
        self.url = url
        self.out_dir = str(out_dir)
        self.engine = _engine_for(url)
        self._stop = threading.Event()

    def cancel(self) -> None:
        self._stop.set()

    # -- thread body ---------------------------------------------------------
    def run(self) -> None:  # noqa: C901
        os.makedirs(self.out_dir, exist_ok=True)
        if self._stop.is_set():
            return
        try:
            if self.engine == "video":
                self._run_ytdlp()
            elif self.engine == "gallery":
                self._run_gallery()
            else:
                self._run_http()
        except _Cancelled:
            self.status.emit("cancelled")
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))

    # -- yt-dlp --------------------------------------------------------------
    def _run_ytdlp(self) -> None:
        self.status.emit("starting yt-dlp…")

        def hook(d: dict) -> None:
            if self._stop.is_set():
                raise _Cancelled()
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                done = d.get("downloaded_bytes")
                if total and done is not None:
                    pct = int(done * 100 / total)
                    self.progress.emit(pct, _speed_from(d.get("speed")))
            elif d.get("status") == "finished":
                self.progress.emit(100, "")

        opts = {
            "format": FORMAT,
            "outtmpl": os.path.join(self.out_dir, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            "noplaylist": True,
            "retries": 10,
            "concurrent_fragment_downloads": 4,
            "geo_bypass": True,
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.extract_info(self.url, download=True)
        if self._stop.is_set():
            self.status.emit("cancelled")
            return
        self.finished_ok.emit(self._newest_file(
            (".mp4", ".mkv", ".webm", ".mp3", ".m4a")))

    # -- gallery-dl ------------------------------------------------------------
    def _run_gallery(self) -> None:
        self.status.emit("starting gallery-dl…")
        opts = {
            "out": os.path.join(self.out_dir, "%(path)s/%(filename)s"),
            "cache": True,
            "continue": True,
        }
        with gallery_dl.GalleryDL(opts) as gdl:
            if self._stop.is_set():
                raise _Cancelled()
            gdl.run([self.url])
        if self._stop.is_set():
            self.status.emit("cancelled")
            return
        self.finished_ok.emit(self._newest_file(
            (".jpg", ".jpeg", ".png", ".webp", ".gif")))

    # -- HTTP ------------------------------------------------------------------
    def _run_http(self) -> None:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; DownloaderBot/1.0)"}
        self.status.emit("connecting…")
        with requests.get(self.url, headers=headers, stream=True,
                          timeout=60) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("Content-Length", "0"))
            path = os.path.join(self.out_dir, _filename(resp, self.url))
            done = 0
            last_pct = 0
            with open(path, "wb") as fh:
                for chunk in resp.iter_content(1 << 16):
                    if self._stop.is_set():
                        raise _Cancelled()
                    if chunk:
                        fh.write(chunk)
                        done += len(chunk)
                        if total:
                            pct = int(done * 100 / total)
                            if pct >= last_pct + 2:
                                last_pct = pct
                                self.progress.emit(pct, _fmt(done))
            if self._stop.is_set():
                self.status.emit("cancelled")
                return
            self.finished_ok.emit(path)

    # -- helpers ----------------------------------------------------------------
    def _newest_file(self, suffixes: tuple[str, ...]) -> str:
        d = Path(self.out_dir)
        files = [f for f in d.rglob("*")
                 if f.is_file() and f.suffix.lower() in suffixes]
        if not files:
            return ""
        return str(max(files, key=lambda f: f.stat().st_mtime))


class _Cancelled(Exception):
    """Raised to abort an in-flight download when the user cancels."""


def _speed_from(speed) -> str:
    if not speed:
        return ""
    return f"{speed / (1 << 10):.0f} KiB/s"


def _filename(resp: requests.Response, url: str) -> str:
    cd = resp.headers.get("Content-Disposition", "")
    if "filename" in cd:
        start = cd.find("filename=") + len("filename=")
        end = cd.find(";", start)
        name = cd[start:end if end != -1 else len(cd)].strip('"')
        if name:
            return name
    return url.rsplit("/", 1)[-1] or "download.bin"


def _fmt(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"
