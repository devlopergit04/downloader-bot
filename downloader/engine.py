"""Core download engine: routes a URL to the right tool and runs it."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Callable

from . import ytdlp, gallery, http
from .models import DownloadResult
from config import Settings


# A URL regex that tolerates the many shapes people paste into chat.
URL_RE = re.compile(
    r"(?:https?://|www\.)"
    r"[A-Za-z0-9\-._~%]+"
    r"(?:/[A-Za-z0-9\-._~%!/?#\[\]@:+&=,;]*)?",
    re.IGNORECASE,
)


# Domains we send to gallery-dl (image galleries / sets) rather than yt-dlp.
GALLERY_DOMAINS = (
    "instagram.com",
    "x.com",
    "twitter.com",
    "pikabu.ru",
    "behance.net",
    "deviantart.com",
    "500px.com",
    "flickr.com",
    "pinterest.com",
    "reddit.com",
    "imgur.com",
)

# Domains that are usually better served by the raw HTTP downloader.
DIRECT_DOMAINS = (
    "github.com",
    "raw.githubusercontent.com",
    "objects.githubusercontent.com",
)


class DownloaderEngine:
    """Detects the URL, picks the best tool, and runs the download."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    # -- routing -----------------------------------------------------------
    def _classify(self, url: str) -> str:
        low = url.lower()
        for domain in DIRECT_DOMAINS:
            if domain in low:
                return "direct"
        for domain in GALLERY_DOMAINS:
            if domain in low:
                return "gallery"
        return "video"

    def detect_url(self, text: str) -> str | None:
        match = URL_RE.search(text or "")
        return match.group(0) if match else None

    # -- public API -------------------------------------------------------
    async def download(
        self,
        url: str,
        progress: Callable[[int, int], Awaitable[None]] | None = None,
    ) -> DownloadResult:
        kind = self._classify(url)

        if kind == "gallery":
            return await gallery.download(
                url, self.settings.download_dir, progress
            )
        if kind == "direct":
            return await http.download(
                url, self.settings.download_dir, progress
            )
        return await ytdlp.download(
            url, self.settings, progress
        )


async def _noop(_: int, _n: int) -> None:  # pragma: no cover
    return None
