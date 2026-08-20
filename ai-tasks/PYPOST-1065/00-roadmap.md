# Roadmap: PYPOST-1065

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `test/PYPOST-1065-format-report-tests` (reference only; work remains on `dev`)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1065/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1065/20-architecture.md` — test-focused functional-core
    design, formatter interfaces, exact report cases, and Step 3 N/A rationale
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change: this verification-debt task adds regression
    coverage for formatter behavior that the current implementation already
    satisfies; manufacturing a red assertion would encode a false contract.
  - Evidence: inspected `_format_new_report()` and `_format_fixed_report()` in
    `scripts/check_mypy_baseline.py`; the former sorts grouped source lines and
    both formatters conditionally render their partial-count qualifiers.
  - Verification command: `.venv/bin/python` direct-helper assertion script
    covering partial and whole-key new/fixed cases plus scrambled source-line
    input; result: `PASS: partial/whole qualifier branches and ascending line
    order match architecture`.
  - No production code or tests were modified in Step 3; the green contract
    tests remain Step 4 work.
- [x] **STEP 4: Development**
  - [x] Iteration 1: added direct exact-output unit coverage for partial and
    whole-key new/fixed reports, including deliberately scrambled current
    occurrences proving ascending source-line rendering; production code was
    unchanged because all established contracts already pass.
  - Test evidence: `.venv/bin/pytest -q tests/test_mypy_baseline.py` — 18 passed.
  - Lint evidence: `.venv/bin/flake8 tests/test_mypy_baseline.py` — passed.
  - Timeout evidence: `tests/test_mypy_baseline.py` retains the explicit module
    marker `pytestmark = pytest.mark.timeout(30)`, covering all four new tests.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1065/40-code-cleanup.md`
  - Task-scoped flake8 and targeted pytest passed (18 tests); explicit module timeout,
    syntax validity, and absence of conflict markers verified.
  - `make lint` passed. `make analyze` is unavailable in this repository.
  - Repository baseline evidence: `make typecheck` reports mypy-baseline drift outside the
    task diff; `make test` reports 2,339 passed and three unrelated pre-existing failures.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1065/50-observability.md`
  - N/A — the task adds hermetic direct unit coverage for pure report-formatting helpers;
    production execution paths and operational behavior are unchanged, so new logs or metrics
    would add test noise without improving production diagnostics.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1065/60-tech-debt.md`
  - No task-created technical debt or required follow-up was found; the test-only change follows
    the approved functional-core design and covers every required formatter branch.
  - All changed tests inherit the module-level `pytest.mark.timeout(30)` marker.
  - Repository-wide failures are pre-existing and unrelated: PYPOST-1110 tracks the local `qapp`
    fixture policy failure, PYPOST-1111 tracks only the two audit/snapshot pytest failures, and
    PYPOST-1086 tracks the eight Qt overload errors plus stale baseline entry that keep
    `make typecheck` from exiting 0. None are attributed to PYPOST-1065.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/static_type_checking.md` — document the partial-occurrence report qualifiers,
    qualifier omission for whole-key changes, and deterministic new-error line ordering.
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1065/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1065/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1065/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1065/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1065/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
