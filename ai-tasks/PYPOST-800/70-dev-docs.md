# PYPOST-800: Developer Documentation

## Overview

`tests/test_makefile.py` now includes a fast smoke test that runs `make help` in an isolated
workspace and asserts non-empty stdout. This guards PYPOST-794 self-documenting Makefile
annotations from accidental removal.

## Coverage

| Test | Assertion |
| --- | --- |
| `TestHelpTarget::test_help_prints_non_empty_output` | `make help` exits 0; stdout is non-empty |

## Running

Included in default `make test` and `make check` — no extra flags required.

See [testing.md](../../doc/dev/testing.md) Makefile automation tests section.
