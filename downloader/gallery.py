"""gallery-dl based image/gallery downloader."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Awaitable, Callable

import gallery_dl

from .models import DownloadResult

ProgressFn = Callable[[int, int], Awaitable[None]]


async def download(
    url: str,
    download_dir: Path,
    progress: ProgressFn | None = None,
) -> DownloadResult:
    """Download images/galleries for a URL via gallery-dl."""

    download_dir.mkdir(parents=True, exist_ok=True)
    opts = {
        "out": str(download_dir / "%(path)s/%(filename)s"),
        "cache": True,
        "recursive": True,
        "continue": True,
    }

    # Simple progress: gallery-dl calls the hook once per file.
    state = {"done": 0, "total": 1}

    def _hook(_result) -> None:
        state["done"] += 1
        if progress is not None:
            asyncio.ensure_future(
                progress(min(state["done"], 100), 100)
            )

    opts["progress_hooks"] = [_hook] if progress else []

    def _run() -> int:
        opts_with_hook = dict(opts)
        if progress:
            opts_with_hook["progress_hooks"] = [_hook]
        with gallery_dl.GalleryDL(opts_with_hook) as gdl:
            return gdl.run([url])

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _run)

    # Pick the newest file(s); send the most recent one for simplicity.
    candidates = sorted(
        download_dir.rglob("*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    path = next(
        (p for p in candidates if p.is_file() and p.suffix.lower()
         in {".jpg", ".jpeg", ".png", ".webp", ".gif"}),
        candidates[0] if candidates else Path(download_dir),
    )

    return DownloadResult(
        path=path,
        kind="image",
        title=url,
        size_bytes=path.stat().st_size if path.exists() else 0,
        engine="gallery-dl",
    )
