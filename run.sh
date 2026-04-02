#!/usr/bin/env bash
# run.sh — Cron-friendly wrapper for ai-news-digest
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Load secrets from .env if present
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Run digest
python main.py 2>&1 | tee -a "data/cron.log"
