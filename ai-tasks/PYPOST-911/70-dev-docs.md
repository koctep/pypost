# PYPOST-911: Dev Docs

## Overview

Recorded **DEFER** for a one-time live GitHub Actions Artifacts UI
proof of downloadable `agent-e2e-failure-artifacts` (and matrix twin).
No qualifying public failed-run artifact existed at research time.
Maintainer checklist (what to capture) and notes location are locked
in developer docs.

## Architecture

- **Dump producer** — PYPOST-860 hook/helper (unchanged).
- **CI uploads** — PYPOST-874 / 909 with retention PYPOST-910
  (unchanged).
- **Proof** — deferred; procedure in
  `doc/dev/agent_e2e_failure_artifacts.md` § Live Artifacts UI proof.
- **Notes stub** — `ai-tasks/PYPOST-911/live-proof-notes.md`.
- **Lock** —
  `tests/test_agent_e2e_ci_failure_artifacts_ui_proof_doc.py`.

## Usage

No new make targets. Run the lock with:

```bash
make test PYTEST_ARGS='tests/test_agent_e2e_ci_failure_artifacts_ui_proof_doc.py -v'
```

When a red run uploads dumps: open Actions → Artifacts → download;
fill `live-proof-notes.md` and mark CAPTURED.

## Configuration

| Setting | Value |
| --- | --- |
| Proof status | DEFER (until CAPTURED in notes) |
| Artifact names | `agent-e2e-failure-artifacts` / matrix twin |
| Notes path | `ai-tasks/PYPOST-911/live-proof-notes.md` |
| Retention | 14 days (PYPOST-910) — capture promptly |

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Lock fails on missing PYPOST-911 / DEFER | Restore § Live Artifacts UI proof |
| Lock fails on missing notes stub | Restore `live-proof-notes.md` |
| Still no artifact on red run | Job may lack dumps; see failure_artifacts troubleshooting |

## Files updated

| File | Change |
| --- | --- |
| `doc/dev/agent_e2e_failure_artifacts.md` | DEFER section + checklist + lock path |
| `doc/dev/agent_e2e.md` | Cross-link / config / troubleshooting |
| `doc/dev/testing.md` | § CI upload note + makefile table + link |
| `ai-tasks/PYPOST-911/live-proof-notes.md` | Stub with checklist |
| `tests/test_agent_e2e_ci_failure_artifacts_ui_proof_doc.py` | Doc lock |
