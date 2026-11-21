#!/usr/bin/env bash
# Installs everything the studio needs on a fresh cloud machine. Safe to run twice.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
(cd studio && npm ci --no-audit --no-fund --loglevel=error)
echo "Studio ready."
