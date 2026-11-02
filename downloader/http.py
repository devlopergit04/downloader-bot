"""Generic async HTTP downloader for direct file links."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Awaitable, Callable

import aiohttp

from .models import DownloadResult

ProgressFn = Callable[[int, int], Awaitable[None]]


async def download(
    url: str,
    download_dir: Path,
    progress: ProgressFn | None = None,
) -> DownloadResult:
    """Stream a direct file to disk with progress reporting."""

    download_dir.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0 (compatible; DownloaderBot/1.0)"}

    timeout = aiohttp.ClientTimeout(total=None, sock_connect=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("Content-Length", "0"))
            filename = _filename_from_url(resp, url)
            path = download_dir / filename

            done = 0
            with open(path, "wb") as fh:
                async for chunk in resp.content.iter_chunked(1 << 16):
                    fh.write(chunk)
                    done += len(chunk)
                    if progress is not None:
                        pct = int(done * 100 / total) if total else 0
                        await progress(pct, 100)

    return DownloadResult(
        path=path,
        kind="file",
        title=filename,
        size_bytes=path.stat().st_size if path.exists() else 0,
        engine="http",
    )


def _filename_from_url(resp: aiohttp.ClientResponse, url: str) -> str:
    cd = resp.headers.get("Content-Disposition", "")
    if "filename" in cd:
        start = cd.find("filename=") + len("filename=")
        end = cd.find(";", start)
        name = cd[start:end if end != -1 else len(cd)]
        name = name.strip('"')
        if name:
            return name
    return url.rsplit("/", 1)[-1] or "download.bin"
