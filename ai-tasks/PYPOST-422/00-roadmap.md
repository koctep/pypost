# Roadmap: PYPOST-422

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Renamed Prometheus counter to `request_retry_exhaustions_total`, help text for
        outbound HTTP retry exhaustion; `MetricsManager.track_request_retry_exhaustion`;
        call site in `request_service.py`; tests updated (`TestMetricsManagerRetryExhaustion`,
        exhaustion mocks). **Tests:** `python3 -m pytest tests/test_metrics_manager.py
        tests/test_retry.py` — 42 passed.
  - [x] **Senior Engineer STEP 3 review (2026-03-27):** Approved for user review gate (see
        project management notes).
- [x] **STEP 4: Code Cleanup**
  - [x] Scoped flake8 on `metrics.py`, `request_service.py`, `test_metrics_manager.py`,
        `test_retry.py` — clean. Pytest subset: 42 passed. `40-code-cleanup.md` recorded;
        full-package `make lint` has pre-existing failures outside this task scope.
- [x] **STEP 5: Observability**
  - [x] Verified `request_retry_exhaustions_total` / `track_request_retry_exhaustion`:
        single emission in `_emit_exhaustion_alert`; `endpoint` label = request URL;
        WARNING `retry_exhausted` coherent with metric; no legacy names in `pypost/`.
        `50-observability.md` added. **Tests:** `. venv/bin/activate && python3 -m pytest
        tests/test_metrics_manager.py tests/test_retry.py -q` — 42 passed.
- [x] **STEP 6: Review and Technical Debt**
  - [x] Technical review and debt analysis in `60-review.md` (2026-03-27): delivered scope
        confirmed; no code blockers; FR-2/AC-3 dev docs deferred to STEP 7; consumer migration risk
        noted.
- [x] **STEP 7: Dev Docs**
  - [x] `70-dev-docs.md`: metric rename, migration (option A), verification commands,
        observability/troubleshooting; roadmap STEP 7 closed (2026-03-27).

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-422/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-422/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-422/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-422/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-422/60-review.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-422/70-dev-docs.md` (task developer notes; see also `doc/dev/` for
  general project docs)

## Project management notes

**PYPOST-422 — STEP 1 complete (2025-03-27).** Requirements captured in
`10-requirements.md` (origin: [PYPOST-402] tech debt TD-5, misleading
`email_notification_failures_total` name). **Product Owner review complete
(2026-03-27):** business logic and scope approved; clarifications applied in
`10-requirements.md`.

**STEP 2 complete (2026-03-27):** `20-architecture.md` added (naming alignment,
migration options, components, tests/observability). No implementation started under
this task.

**STEP 2 — Team Lead architecture review (2026-03-27):** **Approved.** The design
satisfies FR/NFR/AC (truthful `request_*_total` naming, unchanged labels, tests and
docs plan, traceability to PYPOST-402 TD-5). Minor refinements applied in
`20-architecture.md`: explicit requirements traceability table, NFR-2 release-note
obligations for breaking renames (or dual-export documentation), and a repo-wide
reference sweep under implementation step 4 for AC-3. **STEP 3 (Development) may
proceed.**

**STEP 3 complete (2026-03-27):** Hard rename (option A): `request_retry_exhaustions_total`,
`track_request_retry_exhaustion`; files `pypost/core/metrics.py`,
`pypost/core/request_service.py`, `tests/test_metrics_manager.py`,
`tests/test_retry.py`. Pytest subset: 42 passed. Dev docs / changelog (AC-3, FR-2)
deferred to STEP 7 per scope.

**STEP 3 — Senior Engineer review (2026-03-27):** **Approved** for the user review gate.
Verified alignment with `10-requirements.md` / `20-architecture.md`: counter name and help
describe retry exhaustion (not email-only); migration is rename-only (no dual export);
`endpoint` label contract unchanged; `tests/test_metrics_manager.py` scrapes
`request_retry_exhaustions_total{endpoint=...}` and `tests/test_retry.py` asserts
`track_request_retry_exhaustion` on exception and status exhaustion paths. No implementation
fixes were required in this review pass.

**STEP 4 complete (2026-03-27):** Code cleanup for PYPOST-422 scoped files only: flake8 clean;
`pytest tests/test_metrics_manager.py tests/test_retry.py` — 42 passed; no functional edits.
`40-code-cleanup.md` added. Full `pypost/` flake8 via `make lint` still reports unrelated
pre-existing issues (documented in cleanup report). **Ready for user review** (STEP 4).

**STEP 5 complete (2026-03-27):** Observability verification after metric rename — no code
changes required. Confirmed: one increment per exhaustion via `_emit_exhaustion_alert`;
`request_retry_exhaustions_total{endpoint}` matches prior label semantics; logs
(`retry_exhausted` then counter) consistent; no `email_notification_*` in `pypost/`.
`50-observability.md` records findings and pytest/static checks. **Ready for user review**
(STEP 5).

**STEP 6 complete (2026-03-27):** Team Lead review recorded in `60-review.md`. Scope matches
requirements (rename, tests, single emission path); technical debt documented (migration comms,
STEP 7 doc updates, historical ai-tasks references, repo-wide flake8); **no implementation
blockers** for proceeding to STEP 7 after user review gate.

**STEP 7 complete (2026-03-27):** `70-dev-docs.md` added — developer-facing rename summary,
PromQL migration from `email_notification_failures_total` to
`request_retry_exhaustions_total`, pytest/`rg` verification, observability and
troubleshooting. Top-down STEP 7 artifact done; **ready for user closure/review** (CHANGELOG
or release notes remain product/process owned if required outside this file).

## Recommended Branch Name

- `fix/PYPOST-422-rename-retry-exhaustion-metric`
