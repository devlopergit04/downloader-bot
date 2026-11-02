#!/usr/bin/env python3
"""Telegram downloader bot entry point.

Usage:
    pip install -r requirements.txt
    cp .env.example .env   # then edit token
    python bot.py
"""

from __future__ import annotations

import logging
import sys

from telegram.ext import Application, ApplicationBuilder

from config import load_settings
from downloader import DownloaderEngine
from handlers import build_command_handlers, build_message_handler


def main() -> int:
    settings = load_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    log = logging.getLogger("bot")

    engine = DownloaderEngine(settings)

    application = (
        ApplicationBuilder()
        .token(settings.token)
        .build()
    )

    application.add_handlers(build_command_handlers())
    application.add_handlers(
        [build_message_handler(engine, settings)]
    )

    log.info("Downloader Bot started.")
    application.run_polling(allowed_updates=None, drop_pending_updates=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
