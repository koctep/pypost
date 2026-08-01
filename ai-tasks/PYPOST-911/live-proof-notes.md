# PYPOST-911: Live Artifacts UI proof notes

**Status:** DEFER — no qualifying public Actions artifact found
(2026-08-01 API scan of failed runs for `koctep/pypost`). Do not invent
screenshots.

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

## API scan notes (why DEFER)

Failed runs inspected via
`GET /repos/koctep/pypost/actions/runs` + per-run `/artifacts`:
none listed `agent-e2e-failure-artifacts*`. Recent failures exposed
`test-results-*` / `coverage-report-*` only (or zero artifacts).
