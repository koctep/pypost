# PYPOST-794: Developer Documentation

## Overview

Root `Makefile` now exposes a self-documenting `help` target. Bare `make` or `make help`
prints all targets annotated with `##` descriptions.

## Usage

```bash
make          # same as make help (default goal)
make help     # list targets and descriptions
```

## Architecture

- `.DEFAULT_GOAL := help` — default invocation shows help.
- Help parses `##` suffixes on target lines via `grep` and `awk` over `$(MAKEFILE_LIST)`.
- Internal file targets (e.g. `$(VENV_MARKER)`) omit `##` and do not appear in help.

## Configuration

No environment variables. Descriptions are co-located on each phony target line in `Makefile`.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Target missing from help | Add `## description` on the same line as the target rule |
| `make` runs wrong target | Confirm `.DEFAULT_GOAL := help` is set near top of Makefile |

See also: [setup.md](../../doc/dev/setup.md)
