# PYPOST-911: Live Artifacts UI proof notes

**Status:** DEFER — no qualifying public Actions artifact found
(2026-08-01 PYPOST-933 re-scan of 23 completed / 10 failed runs for
`koctep/pypost`). Do not invent screenshots.

When a red run uploads `agent-e2e-failure-artifacts` (or the matrix
twin), fill this file and flip status to **CAPTURED**.

## Checklist (what to capture)

- [ ] Actions run URL (failed conclusion)
- [ ] Job name (`agent-e2e` or `test` / Python version)
- [ ] Artifact name in Artifacts UI
  (`agent-e2e-failure-artifacts` or
  `agent-e2e-failure-artifacts-<python>`)
- [ ] Confirmed Download works (optional: unzip shows
  `ui_snapshot.json` + `diagnostics.json`)
- [ ] Screenshot of Artifacts list only (no dump body / secrets)
- [ ] Screenshot path or link recorded below

## Capture record

| Field | Value |
| --- | --- |
| Captured at | *(pending)* |
| Run URL | *(pending)* |
| Job | *(pending)* |
| Artifact name | *(pending)* |
| Screenshot path | *(pending)* |
| Notes | Wait for natural red run with dumps; see doc/dev |
| | `agent_e2e_failure_artifacts.md` § Live Artifacts UI proof |

## PYPOST-933 re-scan (2026-08-01)

Follow-up [PYPOST-933](https://pypost.atlassian.net/browse/PYPOST-933)
re-checked public Actions before attempting CAPTURED proof.

| Field | Value |
| --- | --- |
| Scanned at | 2026-08-01 |
| Method | GitHub REST API (`gh` unavailable) |
| Runs (completed) | 23 |
| Failed conclusions | 10 |
| Qualifying artifacts | **0** (`agent-e2e-failure-artifacts*`) |
| Outcome | **DEFER** continued — checklist unchanged |

Recent failures exposed `test-results-*` / `coverage-report-*` only (or
zero artifacts). No invented screenshots.

## API scan notes (PYPOST-911 initial + PYPOST-933 re-scan)

Failed runs inspected via
`GET /repos/koctep/pypost/actions/runs` + per-run `/artifacts`:

- **PYPOST-911 (2026-08-01):** none listed `agent-e2e-failure-artifacts*`.
- **PYPOST-933 (2026-08-01):** full 23-run scan — still none.

Recent failures exposed `test-results-*` / `coverage-report-*` only (or
zero artifacts).
