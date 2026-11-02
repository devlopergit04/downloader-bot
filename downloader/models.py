"""Shared data models for the downloader package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DownloadResult:
    path: Path
    kind: str          # "video" | "image" | "audio" | "file"
    title: str
    size_bytes: int
    engine: str        # "yt-dlp" | "gallery-dl" | "http"
