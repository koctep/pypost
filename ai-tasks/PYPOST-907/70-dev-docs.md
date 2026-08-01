# PYPOST-907: Dev Docs

## Overview

Revisited the optional CI cost trim for the agent e2e double-run.
**DEFER after evidence**: dual coverage stays (main matrix `-m "not slow"`
plus job `agent-e2e`). Published Actions timing notes and an ENABLE
threshold.

## Architecture

- **Main matrix** — multi-version (3.11, 3.13) includes `agent_e2e`.
- **Dedicated job** — make-gate on 3.11 only.
- **Evidence** — Actions job/step timings in `testing.md`.
- **Lock** — `tests/test_agent_e2e_ci_double_run_doc.py` guards docs + YAML.

## Usage

No new make targets. Run the lock with:

```bash
make test PYTEST_ARGS='tests/test_agent_e2e_ci_double_run_doc.py -v'
```

## Configuration

None. Workflow selection unchanged.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Lock fails on missing PYPOST-907 / evidence phrases | Restore § in `testing.md` / `agent_e2e.md` |
| Lock fails on `not agent_e2e` in YAML | Revert premature ENABLE or update lock + docs together |
| Want to ENABLE trim | Meet threshold in `testing.md`; expand 3.13 coverage plan |

## Files updated

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | Evidence table, DEFER after evidence, ENABLE threshold |
| `doc/dev/agent_e2e.md` | Overview + CI note for PYPOST-907 |
| `tests/test_agent_e2e_ci_double_run_doc.py` | Extended lock anchors |
