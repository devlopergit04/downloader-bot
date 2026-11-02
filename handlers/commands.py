"""Command handlers: /start, /help, /ping, /cancel."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from .messages import _active

log = logging.getLogger(__name__)


HELP_TEXT = """\
🤖 **ربات دانلود**

ربات از هزاران سایت دنیا (ویدئو، صدا، تصویر و فایل) با کیفیت کامل دانلود می‌کند.

**کاربرد:**
• یک لینک بفرست — ربات نوع فایل را شناسایی می‌کند.
• کیفیت بهترین (best) همیشه انتخاب می‌شود.
• پیشرفت دانلود به صورت زنده نمایش داده می‌شود.
• تک‌تک لینک‌ها پشتیبانی می‌شوند.

**مثال:**
https://youtu.be/xxxx

**دستورها:**
/start — شروع
/help — کمک
/ping — تست ربات
/cancel — لغو دانلود فعلی
"""


def build_command_handlers():
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "سلام 👋 ربات دانلودی آماده‌ست.\n"
            "فقط یک لینک بفرست تا برات دانلود کنه."
        )

    async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(HELP_TEXT)

    async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("✅ ربات زنده‌ست و آماده.")

    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.message
        task = _active.get(msg.message_id) or (
            _active.get(msg.reply_to_message.message_id)
            if msg.reply_to_message
            else None
        )
        if task and not task.done():
            task.cancel()
            _active.pop(msg.message_id, None)
            await msg.reply_text("🚫 دانلود لغو شد.")
        else:
            await msg.reply_text("⚠️ هیچ دانلودی در جریان نیست.")

    return [
        CommandHandler("start", start),
        CommandHandler("help", help_cmd),
        CommandHandler("ping", ping),
        CommandHandler("cancel", cancel),
    ]
