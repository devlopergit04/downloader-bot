"""Handles incoming text messages: detects URLs and downloads media."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from config import Settings
from downloader import DownloaderEngine

log = logging.getLogger(__name__)

# In-flight downloads keyed by message id — lets /cancel stop a task.
_active: Dict[int, asyncio.Task] = {}


def build_message_handler(engine: DownloaderEngine, settings: Settings):
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if settings.allowed_user_id and str(user.id) != settings.allowed_user_id:
            await update.message.reply_text("⛔ این ربات مخصوص کاربر مجاز است.")
            return

        url = engine.detect_url(update.message.text or "")
        if not url:
            return  # ignore non-URL text

        msg = await update.message.reply_text(
            f"⬇️ در حال دانلود:\n{url}\n\nدر حال آماده‌سازی…"
        )

        # Progress throttling so we don't spam edit calls.
        state = {"last": 0}

        async def progress(pct: int, _total: int) -> None:
            now = asyncio.get_running_loop().time()
            if now - state["last"] < 0.25:
                return
            state["last"] = now
            try:
                await msg.edit_text(f"⬇️ {_bar(pct)} {pct}%")
            except Exception:  # message may have been deleted already
                pass

        async def run() -> None:
            try:
                result = await engine.download(url, progress)
                await _send_file(msg, result, settings)
            except Exception as exc:  # noqa: BLE001
                log.exception("download failed")
                await msg.edit_text(f"❌ خطای دانلود:\n{exc}")
            finally:
                _active.pop(msg.message_id, None)

        task = asyncio.create_task(run())
        _active[msg.message_id] = task

    return MessageHandler(filters.TEXT & ~filters.COMMAND, handle)


async def _send_file(msg, result, settings: Settings) -> None:
    path = result.path
    if not path.exists():
        await msg.edit_text("❌ فایل تولید نشد.")
        return

    size = path.stat().st_size
    limit = settings.max_upload_bytes

    kind_label = {
        "video": "ویدیو",
        "audio": "صوت",
        "image": "تصویر",
        "file": "فایل",
    }.get(result.kind, "فایل")

    caption = (
        "✅ دانلود کامل\n"
        f"نوع: {kind_label}\n"
        f"نیتی: {result.engine}\n"
        f"حجم: {_human(size)}"
    )

    # For very large files fall back to a document so nothing gets dropped.
    force_document = bool(limit) and size > limit

    try:
        if force_document or result.kind == "file":
            with open(path, "rb") as fh:
                await msg.bot.send_document(
                    chat_id=msg.chat_id,
                    document=fh,
                    caption=caption,
                )
        elif result.kind == "video":
            with open(path, "rb") as fh:
                await msg.bot.send_video(
                    chat_id=msg.chat_id,
                    video=fh,
                    caption=caption,
                )
        elif result.kind == "audio":
            with open(path, "rb") as fh:
                await msg.bot.send_audio(
                    chat_id=msg.chat_id,
                    audio=fh,
                    caption=caption,
                )
        elif result.kind == "image":
            with open(path, "rb") as fh:
                await msg.bot.send_photo(
                    chat_id=msg.chat_id,
                    photo=fh,
                    caption=caption,
                )
        else:
            with open(path, "rb") as fh:
                await msg.bot.send_document(
                    chat_id=msg.chat_id,
                    document=fh,
                    caption=caption,
                )
        await msg.delete()
    except Exception as exc:  # noqa: BLE001
        await msg.edit_text(
            f"⚠️ ارسال فایل با حجم {_human(size)} شکست خورد. خطای {exc}"
        )


def _bar(pct: int) -> str:
    filled = int(pct / 100 * 10)
    return "█" * filled + "░" * (10 - filled)


def _human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"
