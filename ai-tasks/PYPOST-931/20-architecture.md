# PYPOST-931: Automate CI duration evidence capture

## Research

### Jira / lineage

- Issue: [PYPOST-931](https://pypost.atlassian.net/browse/PYPOST-931) —
  script/checklist to refresh agent-e2e overlap evidence from Actions API.
- Evidence publisher: [PYPOST-907](https://pypost.atlassian.net/browse/PYPOST-907)
  — table in `doc/dev/testing.md` (2026-08-01, n=2).
- Discoverability: [PYPOST-908](https://pypost.atlassian.net/browse/PYPOST-908)
  — timing notes linked; automation explicitly deferred to this ticket.
- ENABLE trim: [PYPOST-930](https://pypost.atlassian.net/browse/PYPOST-930).

### GitHub Actions API

| Call | Purpose |
| --- | --- |
| `GET .../actions/workflows/test.yml/runs?status=completed&per_page=15` | Recent `Tests` runs |
| `GET .../actions/runs/{id}/jobs` | Job + step timings per run |

Filter runs where a job named like `make test-agent-e2e (env pack)` exists.
Extract:

- Main matrix 3.11 job `pytest (Python 3.11)` — total duration; step `Run tests`.
- Job `make test-agent-e2e (env pack)` — total; step `Run agent e2e env pack via make`.

Format durations like existing docs (`~11.8m`, `~172s`). Include run number and
run id for traceability.

### Decision

| Decision | Choice | Rationale |
| --- | --- | --- |
| Implementation | Python script + Makefile | Repeatable; matches other `scripts/*` |
| Doc update | Manual paste | Avoid auto-commit of unreviewed numbers |
| `--check` | Doc anchor verification | CI-safe without network |
| Live fetch | `make refresh-ci-duration-evidence` | Maintainer-only; needs network + optional token |

## Implementation Plan

1. **Step 3** — `tests/test_refresh_ci_duration_evidence.py` locks script path,
   Makefile targets, and doc procedure anchors (`PYPOST-931`,
   `refresh-ci-duration-evidence`). Expect **red** until Step 4.
2. **Step 4** — implement `scripts/refresh_ci_duration_evidence.py`, Makefile
   targets, update `doc/dev/testing.md` procedure + harness row; unit tests
   for format/extract with fixture JSON.
3. **Step 8** — cross-link from `agent_e2e.md` if needed (already mentions 931).

**Mandatory — Failing Repro (Step 3):**

- **Where:** `tests/test_refresh_ci_duration_evidence.py`
- **Asserts:** script exists; Makefile lists target; `testing.md` documents
  `make refresh-ci-duration-evidence`.
- **Run:**

```bash
make test PYTEST_ARGS='tests/test_refresh_ci_duration_evidence.py -v'
```

## Architecture

```mermaid
flowchart LR
  API["GitHub Actions API"]
  Script["refresh_ci_duration_evidence.py"]
  Make["make refresh-ci-duration-evidence"]
  Docs["doc/dev/testing.md\nmanual paste"]
  Lock["test_refresh_ci_duration_evidence"]
  API --> Script
  Script --> Make
  Make --> Docs
  Docs --> Lock
```

| Module | Responsibility |
| --- | --- |
| `scripts/refresh_ci_duration_evidence.py` | Fetch runs, emit markdown table |
| `Makefile` | Repeatable maintainer entry |
| `doc/dev/testing.md` | Procedure + evidence table (committed numbers) |
| `tests/test_refresh_ci_duration_evidence.py` | Lock wiring + unit tests |

## Q&A

| Q | A |
| --- | --- |
| Why stdlib urllib? | No new dependency; public repo works unauthenticated. |
| Can PYPOST-908 close? | Yes — 908 DoD was discoverable published notes; 931 is separate automation. |
