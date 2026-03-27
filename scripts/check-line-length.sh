#!/usr/bin/env bash
awk 'length>100{print FILENAME ":" FNR ": " length ": " $0; failed=1} END{exit failed}' "$@"
