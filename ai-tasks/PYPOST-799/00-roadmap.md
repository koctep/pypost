# Roadmap: PYPOST-799

**Programming language:** Python

**Task type:** Tech-debt closure — verify PYPOST-44 TD-2 optional-metrics guard debt is
resolved (optional injection, no-op default, direct recording at consumers).

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Verified `MetricsTrackerProtocol`, `NullMetrics`, `NULL_METRICS`, and
    `resolve_metrics()` in `pypost/core/metrics_protocol.py` — all protocol methods
    implemented as no-ops; `resolve_metrics(None)` returns shared singleton.
  - [x] Audited consumers: 11 `resolve_metrics` normalization sites; zero
    `if self._metrics` optional-injection guards in `pypost/` (only
    `resolve_metrics` and unrelated domain guards remain).
  - [x] Confirmed direct unconditional `track_*` calls at all consumer call sites;
    leaf presenters receive upstream-resolved trackers per architecture.
  - [x] Ran `make test` — **1587 passed**, 1 deselected, 61 subtests passed in 71s;
    `tests/test_metrics_protocol.py` green (protocol satisfaction, no-op smoke,
    resolve helper).
  - [x] **Verification-only closure** — no code changes required; PYPOST-44 TD-2
    acceptance outcomes satisfied by prior PYPOST-73/74 work.
- [x] **STEP 4: Code Cleanup**
  - [x] Ran `make check` — flake8 clean; **1587 passed**, 1 deselected, 61 subtests (~73s).
  - [x] **Verification-only** — no source edits; lint/format/cleanup N/A (debt already
    resolved in PYPOST-73/74).
  - [x] Created `ai-tasks/PYPOST-799/40-code-cleanup.md`.
- [x] **STEP 5: Observability**
  - [x] Verified `NullMetrics` observability pattern — silent omission when metrics not
    configured; unchanged Prometheus output when `MetricsManager` injected.
  - [x] Confirmed 11 `resolve_metrics` normalization sites; zero optional-injection
    `if self._metrics` guards in `pypost/`.
  - [x] **Verification-only** — no new logs or metrics; existing tracking contract and
    call-site clarity preserved from PYPOST-73/74.
  - [x] Created `ai-tasks/PYPOST-799/50-observability.md`.
- [x] **STEP 6: Review and Technical Debt**
  - [x] Verified zero optional-injection `if self._metrics` guards; 11 `resolve_metrics` sites
  - [x] Confirmed `tests/test_metrics_protocol.py` and full suite green (**1587 passed**)
  - [x] **Verdict: SAFE TO CLOSE** — PYPOST-44 TD-2 resolved; no new follow-ups for Phase D
  - [x] Created `ai-tasks/PYPOST-799/60-tech-debt.md`; updated `PYPOST-75/60-tech-debt.md`
- [x] **STEP 7: Dev Docs**
  - [x] Confirmed `doc/dev/testability.md` already documents NullMetrics pattern (PYPOST-73/74)
  - [x] Added PYPOST-799 closure cross-reference to testability.md
  - [x] Created `ai-tasks/PYPOST-799/70-dev-docs.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-799/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-799/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-799/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-799/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-799/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/testability.md`
- `ai-tasks/PYPOST-799/70-dev-docs.md`

## Suggested branch name

`refactoring/PYPOST-799-metrics-protocol-null-metrics-closure`
