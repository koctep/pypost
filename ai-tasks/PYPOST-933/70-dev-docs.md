# PYPOST-933: Dev Docs

## Overview

Re-scanned public GitHub Actions for qualifying
`agent-e2e-failure-artifacts*` on failed runs (PYPOST-933 follow-up to
PYPOST-911). **0** qualifying artifacts across 23 completed runs (10
failed) as of 2026-08-01. Continued **DEFER**; scan evidence recorded in
notes stub and developer docs.

## Architecture

- **Dump producer** — PYPOST-860 hook/helper (unchanged).
- **CI uploads** — PYPOST-874 / 909 with retention PYPOST-910
  (unchanged).
- **Proof** — still deferred; PYPOST-933 re-scan noted in
  `doc/dev/agent_e2e_failure_artifacts.md` § Live Artifacts UI proof.
- **Notes** — `ai-tasks/PYPOST-911/live-proof-notes.md` (PYPOST-933
  re-scan section).
- **Lock** —
  `tests/test_agent_e2e_ci_failure_artifacts_ui_proof_recapture_doc.py`.

## Usage

Run the recapture lock with:

```bash
make test PYTEST_ARGS='tests/test_agent_e2e_ci_failure_artifacts_ui_proof_recapture_doc.py -v'
```

When a red run uploads dumps: open Actions → Artifacts → download;
fill `live-proof-notes.md`, mark **CAPTURED**, update doc status.

## Configuration

| Setting | Value |
| --- | --- |
| Proof status | DEFER (continued after PYPOST-933 re-scan) |
| Last scan | 2026-08-01 (23 runs, 0 qualifying artifacts) |
| Artifact names | `agent-e2e-failure-artifacts` / matrix twin |
| Notes path | `ai-tasks/PYPOST-911/live-proof-notes.md` |

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Recapture lock fails on missing PYPOST-933 | Restore re-scan section in notes |
| Still no artifact on red run | Job may lack dumps; see failure_artifacts troubleshooting |
| CAPTURED proof available | Fill capture record; update doc status from DEFER |

## Files updated

| File | Change |
| --- | --- |
| `ai-tasks/PYPOST-911/live-proof-notes.md` | PYPOST-933 re-scan section |
| `doc/dev/agent_e2e_failure_artifacts.md` | PYPOST-933 re-scan in status line |
| `tests/test_agent_e2e_ci_failure_artifacts_ui_proof_recapture_doc.py` | Recapture lock |
