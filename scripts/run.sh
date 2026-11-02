#!/usr/bin/env bash
# Quick local launcher for the downloader bot.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "Copy .env.example to .env and add your TELEGRAM_BOT_TOKEN first." >&2
    exit 1
fi

python3 bot.py
