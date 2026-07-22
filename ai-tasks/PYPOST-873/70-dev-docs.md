# PYPOST-873: Dev Docs

## Overview

Recorded **DEFER** for optional CI cost trim of the agent e2e double-run on
Python 3.11. Dual coverage stays: main matrix (`-m "not slow"`) plus job
`agent-e2e` (`make test-agent-e2e`).

## Architecture

- **Main matrix** — multi-version (3.11, 3.13) includes `agent_e2e`.
- **Dedicated job** — make-gate on 3.11 only.
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
| Lock fails on missing phrases | Restore DEFER section in `testing.md` / `agent_e2e.md` |
| Lock fails on `not agent_e2e` in YAML | Revert premature ENABLE or update lock + docs together |
| Want to ENABLE trim | Follow revisit criteria in `testing.md`; expand coverage plan |

## Files updated

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | § Agent e2e CI double-run (PYPOST-873); makefile table row |
| `doc/dev/agent_e2e.md` | Overview + CI DEFER / revisit note |
| `doc/dev/setup.md` | Cross-link to intentional double-run / DEFER |
