# PYPOST-910: Dev Docs

## Overview

Recorded **ENABLE** for explicit `retention-days: 14` on agent e2e
failure artifact uploads. Both job `agent-e2e`
(`agent-e2e-failure-artifacts`) and the main `test` matrix
(`agent-e2e-failure-artifacts-${{ matrix.python-version }}`) keep dumps
for 14 days instead of the Actions default window.

## Architecture

- **Dump producer** — PYPOST-860 hook/helper (unchanged).
- **CI consumers** — `actions/upload-artifact` on jobs `agent-e2e` (874)
  and `test` matrix (909), now with `retention-days: 14` (910).
- **Lock** — `tests/test_agent_e2e_ci_failure_retention_doc.py` guards
  docs + YAML for the retention contract.

## Usage

No new make targets. Run the lock with:

```bash
make test PYTEST_ARGS='tests/test_agent_e2e_ci_failure_retention_doc.py -v'
```

After a red run: open Actions → Artifacts → download within 14 days.

## Configuration

| Setting | Value |
| --- | --- |
| Path | `artifacts/agent_e2e/` |
| Retention | `retention-days: 14` |
| Jobs | `agent-e2e`, `test` matrix |
| Gate | `if: failure()` (unchanged) |
| Missing path | `ignore` (unchanged) |

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Lock fails on missing PYPOST-910 / 14 | Restore retention section in docs |
| Lock fails on missing `retention-days: 14` | Restore input under both failure uploads |
| Artifact gone after ~2 weeks | Expected; re-run CI or use local dumps |

## Files updated

| File | Change |
| --- | --- |
| `.github/workflows/test.yml` | `retention-days: 14` on both failure uploads |
| `doc/dev/agent_e2e_failure_artifacts.md` | Retention note + lock path |
| `doc/dev/agent_e2e.md` | CI / config / troubleshooting |
| `doc/dev/testing.md` | § CI upload; makefile table + link |
| `tests/test_agent_e2e_ci_failure_retention_doc.py` | Doc/workflow lock |
