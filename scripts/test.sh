#!/usr/bin/env bash
set -euo pipefail

QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q \
  "$@" \
  2>&1
