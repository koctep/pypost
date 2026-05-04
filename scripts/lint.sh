#!/usr/bin/env bash
set -euo pipefail

.venv/bin/python -m flake8 --jobs=1 \
  "$@" \
  2>&1
