# Roadmap: PYPOST-421

## Programming language

- **Python** — implementation and tests for this task use Python, consistent with the `pypost`
  package and `.cursor/lsr/do-python.md`.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] HTTP retry exhaustion: removed bare `assert`; retryable status exhaustion uses
    `ExecutionError` + `_emit_exhaustion_alert` like the exception path; `try`/`except`/`else`
    so status exhaustion is not double-handled; defensive `ExecutionError` after loop for empty
    range. Tests: `TestRetryableStatusExhaustion` in `tests/test_retry.py`.
  - **Senior review (STEP 3):** Confirmed — no `assert` in `_execute_http_with_retry`; exhaustion
    raises `ExecutionError` (including defensive post-loop path); status exhaustion emits alert once
    (`else` branch raises before shared retry metrics); tests cover retryable HTTP status exhaustion
    (error, detail, metrics, alerts). **Approved for user review gate** before STEP 4.
  - **Tests:** `pytest tests/test_retry.py tests/test_request_service.py` — pass; full
    `pytest tests/` — 281 passed (2 DeprecationWarnings in UI tests, unrelated).
- [x] **STEP 4: Code Cleanup**
  - **Cleanup:** `logger` after imports and line wraps in `request_service.py`; unused imports and
    unused `result` in `tests/test_retry.py`. Flake8 clean on those files; `pytest`
    `tests/test_retry.py` + `tests/test_request_service.py` — 55 passed. See
    `40-code-cleanup.md`. **Ready for user review** before STEP 5.
- [x] **STEP 5: Observability**
  - **Observability:** Confirmed retry/exhaustion logging and metrics touchpoints; no
    duplicate `track_retry_attempt` on exhaustion; `retry_exhausted` log includes
    `detail`; defensive path logs `retry_loop_invariant_failed`. Documented in
    `50-observability.md`. **Verification:** flake8 `pypost/core/request_service.py`;
    pytest `tests/test_retry.py` + `tests/test_request_service.py` — 55 passed.
  - **Ready for user review** before STEP 6.
- [x] **STEP 6: Review and Technical Debt**
  - **Checkpoint:** Technical review and debt analysis recorded in `60-review.md` (delivered
    scope, non-blocking debt, risks, test adequacy, optional follow-ups). **Ready for user
    review** before STEP 7.
- [x] **STEP 7: Dev Docs**
  - **Documentation:** `70-dev-docs.md` added (developer summary, exhaustion behavior, test and
    lint commands, observability). **Completed** — ready for user review / task closure.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-421/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-421/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-421/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-421/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-421/60-review.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-421/70-dev-docs.md`

## PM status

- **Task**: PYPOST-421 (addresses defect scope under related item PYPOST-402: bare assert in
  production retry path).
- **STEP 1**: Completed — requirements in `10-requirements.md`. **PO review**: Requirements review
  for business logic is complete; approved to proceed to STEP 2 (architecture). Stakeholder sign-off
  on implementation may still follow per project process.
- **STEP 2**: Completed — `20-architecture.md` created (target
  `RequestService._execute_http_with_retry`, explicit `ExecutionError` strategy, tests,
  observability touchpoints). **Team lead architecture review**: **Approved** — design aligns with
  `10-requirements.md` (explicit exhaustion failure, preserved diagnostics, cancellation unchanged,
  test plan); traceability table and diagram cleanup recorded in `20-architecture.md`. **Next**:
  STEP 3 (development).
- **STEP 3**: Completed — `pypost/core/request_service.py`, `tests/test_retry.py`; pytest
  `tests/` 281 passed. **Senior review**: Approved for user review gate; **next**: STEP 4 (code
  cleanup) after stakeholder sign-off per `00-rules.mdc`.
- **STEP 4**: Completed — flake8 clean on task files; `40-code-cleanup.md` recorded. **Next**:
  user review gate, then STEP 5 (observability).
- **STEP 5**: Completed — `50-observability.md` recorded; exhaustion observability verified
  (logging, metrics, no duplicate retry counter on final failure). **Next**: user review gate,
  then STEP 6 (review / tech debt).
- **STEP 6**: Completed — `60-review.md` (technical review, debt, risks, tests, follow-ups).
  **Next**: user review gate, then STEP 7 (dev docs).
- **STEP 7**: Completed — developer notes in `70-dev-docs.md` (what changed, exhaustion behavior,
  tests, observability). **Next**: user closure / final review per `00-rules.mdc`.

## Recommended Branch Name

- `fix/PYPOST-421-retry-exhaustion-explicit-error`
