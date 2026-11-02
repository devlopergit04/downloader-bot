"""yt-dlp based video/audio downloader with full-quality format selection."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Awaitable, Callable

import yt_dlp

from config import Settings
from .models import DownloadResult

ProgressFn = Callable[[int, int], Awaitable[None]]


async def download(
    url: str,
    settings: Settings,
    progress: ProgressFn | None = None,
) -> DownloadResult:
    """Download the best-quality media for a URL via yt-dlp."""

    outtmpl = str(
        settings.download_dir / "%(title)s.%(ext)s"
    )

    progress_pct: int = 0

    def _hook(d: dict) -> None:
        nonlocal progress_pct
        if d.get("status") == "downloading" and progress is not None:
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes")
            if total and done is not None:
                asyncio.ensure_future(progress(int(done * 100 / total), 100))
        elif d.get("status") == "finished":
            asyncio.ensure_future(progress(100, 100))

    opts: dict = {
        "format": settings.extra_formats,
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
        "retries": settings.ytdlp_retries,
        "concurrent_fragment_downloads": settings.ytdlp_concurrent,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "progress_hooks": [_hook],
        # Be polite; allow the broadest site coverage.
        "geo_bypass": True,
        "extractor_args": {"youtube": {"player_client": "default"}},
    }

    # gallery-dl fallback is handled by the engine; here we assume a video.
    def _run() -> dict:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info or {}

    loop = asyncio.get_running_loop()
    info = await loop.run_in_executor(None, _run)

    if not info:
        raise RuntimeError("yt-dlp returned no media information.")

    # Resolve the real path of the downloaded file.
    path = Path(outtmpl.replace("%(title)s", info.get("title", "video")).replace("%(ext)s", info.get("ext", "mp4")))
    if not path.exists():
        # Fallback: scan the download dir for a file created just now.
        candidates = sorted(
            settings.download_dir.glob("*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            path = candidates[0]

    title = info.get("title") or url
    size = path.stat().st_size if path.exists() else 0
    kind = "audio" if (info.get("vcodec") == "none") else "video"

    return DownloadResult(
        path=path,
        kind=kind,
        title=title,
        size_bytes=size,
        engine="yt-dlp",
    )
