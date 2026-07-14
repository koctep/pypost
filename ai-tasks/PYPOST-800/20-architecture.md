# PYPOST-800: Architecture — make help smoke test

## Overview

Add one fast pytest case to `tests/test_makefile.py` that validates `make help` returns exit
code 0 and prints non-empty stdout in an isolated `tmp_path` workspace.

## Components

### 1. Test module extension

| Property | Value |
| --- | --- |
| File | `tests/test_makefile.py` |
| Class | `TestHelpTarget` (new) |
| Helper | `_run_make(make_workspace, "help")` — existing |
| Fixture | `make_workspace` — copies root `Makefile` into `tmp_path` |

### 2. Assertions

1. `returncode == 0`
2. `stdout.strip()` is non-empty

Non-empty stdout implies the `grep`/`awk` help pipeline found at least one `##`-annotated
target line in the copied Makefile.

### 3. Suite placement

- No `@pytest.mark.slow` — runs in default `make test` and CI fast job.
- Inherits module-level `pytestmark = pytest.mark.timeout(120)`.

## Out of Scope

- Asserting specific target names or ANSI formatting
- Testing bare `make` default goal (help-only scope)
- Makefile or CI workflow changes
