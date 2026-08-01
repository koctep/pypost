# PYPOST-908: Dev Docs

## Overview

Optional CI duration evidence for the agent-e2e intentional double-run is
now **discoverable and locked**. Timing notes (job durations / overlap cost)
remain those published by PYPOST-907 in `doc/dev/testing.md`; this task
cross-links PYPOST-908 from agent docs and the harness table, and extends
the dual-run lock so the evidence ticket stays findable. No invented
numbers; refresh automation stays on PYPOST-931.

## Architecture

- **Evidence source** — `testing.md` § Agent e2e CI double-run (Actions
  2026-08-01 table).
- **Discoverability** — `agent_e2e.md` overview + CI note; harness table row;
  `ai-tasks/PYPOST-908/20-architecture.md` cites the same numbers.
- **Lock** — `tests/test_agent_e2e_ci_double_run_doc.py` requires PYPOST-908
  in both docs plus existing 873/907/evidence/DEFER anchors.
- **Workflow** — unchanged (DEFER after evidence).

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
| Lock fails on missing PYPOST-908 in `agent_e2e.md` | Restore CI / overview link to 908 |
| Lock fails on missing PYPOST-908 in `testing.md` | Restore evidence-section / harness link |
| Want fresh Actions timings | Use PYPOST-931; do not invent numbers |
| Want to ENABLE trim | Meet threshold in `testing.md`; PYPOST-930 |

## Files updated

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | Evidence intro + overlap cost wording; harness row; footnote |
| `doc/dev/agent_e2e.md` | Overview + CI note link PYPOST-908 |
| `tests/test_agent_e2e_ci_double_run_doc.py` | Require PYPOST-908 in both docs |
| `ai-tasks/PYPOST-908/*` | Full top-down artifacts |
