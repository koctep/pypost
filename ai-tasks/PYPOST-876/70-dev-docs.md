# PYPOST-876: Dev Docs

## Overview

Documented narrowed best-effort exception types for the agent e2e failure
dump helper (PYPOST-876).

## Files updated

| File | Change |
| --- | --- |
| `doc/dev/agent_e2e_failure_artifacts.md` | `_DUMP_BEST_EFFORT_ERRORS` catalogue; propagation note; tests + troubleshooting |
| `doc/dev/logging.md` | Cross-link tag includes PYPOST-876 |

## Architecture (docs)

- Dump body catches only catalogued kinds → WARNING + `None`.
- Unexpected kinds propagate to the caller (fixture hook / lifecycle
  hook wrapper may still absorb at their boundary).

## Usage

Unchanged call sites. Authors diagnosing dump failures: see
troubleshooting table for WARNING vs unexpected traceback.

## Configuration

Unchanged: `PYPOST_AGENT_E2E_ARTIFACTS`, offscreen via Makefile.

## Troubleshooting

Documented in failure-artifacts doc (best-effort WARNING vs unexpected
dump exception).
