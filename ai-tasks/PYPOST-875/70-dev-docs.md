# PYPOST-875: Dev Docs

## Overview

Documented auto-dump for direct `AgentAppSession` constructions
(PYPOST-875) alongside the existing fixture makereport path from
PYPOST-860.

## Files updated

| File | Change |
| --- | --- |
| `doc/dev/agent_e2e_failure_artifacts.md` | Direct `__exit__` path, `session_fixture=direct`, usage, troubleshooting |
| `doc/dev/agent_e2e.md` | Tools map + multi-session note for auto-dump |
| `doc/dev/agent_lifecycle.md` | Context-manager dump-before-shutdown behavior |
| `doc/dev/logging.md` | `agent_session_failure_dump_hook_failed` catalog entry |

## Architecture (docs)

- Fixture path: makereport + funcargs session.
- Direct path: plugin installs dump hook; `__exit__` dumps while started.
- Same on-disk layout and masking.

## Usage

See `doc/dev/agent_e2e_failure_artifacts.md` § Automatic (preferred) for
fixture and direct examples.

## Configuration

Unchanged: `PYPOST_AGENT_E2E_ARTIFACTS`, offscreen via Makefile.

## Troubleshooting

Documented in failure-artifacts doc (no dump / direct provenance / WARNING).
