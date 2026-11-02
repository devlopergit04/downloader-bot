"""Application configuration loaded from the environment / .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:  # python-dotenv is optional at import time; only needed for real runs.
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv missing in dev is fine
    pass


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    token: str
    allowed_user_id: str
    max_upload_mb: int
    download_dir: Path
    ytdlp_retries: int
    ytdlp_concurrent: int
    log_level: str
    # List of supported domains is large; keep it out of the hot path.
    extra_formats: str = field(
        default="bestvideo*+bestaudio/best,bestquality/best"
    )

    @property
    def max_upload_bytes(self) -> int:
        if self.max_upload_mb <= 0:
            return 0  # 0 == unlimited
        return self.max_upload_mb * 1024 * 1024


def load_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN is not set. Copy .env.example to .env "
            "and add your bot token from https://t.me/BotFather"
        )

    download_dir = Path(os.getenv("DOWNLOAD_DIR", "./downloads")).expanduser()
    download_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        token=token,
        allowed_user_id=os.getenv("ALLOWED_USER_id", "").strip(),
        max_upload_mb=_get_int("MAX_UPLOAD_MB", 50),
        download_dir=download_dir,
        ytdlp_retries=_get_int("YTDLP_RETRIES", 10),
        ytdlp_concurrent=_get_int("YTDLP_CONCURRENT", 4),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
