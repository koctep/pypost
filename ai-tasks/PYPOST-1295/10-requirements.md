# PYPOST-1295: make target to regenerate ai-tasks/PYPOST-376/baseline-metrics.md

## Goals

1. **Make-Only Compliance**: Adhere strictly to the project-wide `AGENTS.md` make-only rule
   by eliminating the direct invocation of `.venv/bin/python scripts/audit_baseline_metrics.py`.
2. **Standardized Regeneration Target**: Provide a standard make target (`make baseline-metrics`)
   to regenerate `ai-tasks/PYPOST-376/baseline-metrics.md` automatically.
3. **Verification Target**: Provide a convenience verification target
   (`make check-baseline-metrics`) to check that module inventory caps are respected.
4. **Snapshot & Documentation Consistency**: Synchronize the markdown generation logic in
   `scripts/audit_baseline_metrics.py` with `ai-tasks/PYPOST-376/baseline-metrics.md` so that
   `tests/test_solid_audit_baseline.py::test_markdown_snapshot_matches_current_metrics` passes.

## User Stories

- As an AI agent or developer touching `main_window.py` or capped modules, I want to execute
  `make baseline-metrics` to update the baseline metrics documentation without having to manually
  edit line numbers or invoke forbidden raw `.venv` binaries.
- As a developer or CI check, I want to run `make check-baseline-metrics` to verify that no
  module lines-of-code caps have been breached.

## Definition of Done

- `Makefile` includes `baseline-metrics` and `check-baseline-metrics` targets added to `.PHONY`
  and annotated with `##` comments for `make help`.
- `make baseline-metrics` executes `scripts/audit_baseline_metrics.py` with
  `--markdown ai-tasks/PYPOST-376/baseline-metrics.md`.
- `make check-baseline-metrics` executes `scripts/audit_baseline_metrics.py --check`.
- `scripts/audit_baseline_metrics.py`'s `format_markdown` function outputs the
  `make baseline-metrics` regeneration instruction.
- `ai-tasks/PYPOST-376/baseline-metrics.md` contains the updated `make baseline-metrics`
  instructions.
- Unit and integration tests verify the Makefile targets and script consistency.
- Quality gates pass: `make lint`, `make typecheck`, and `make verify-ai-tasks`.

## Task Description

In `ai-tasks/PYPOST-1285/60-tech-debt.md` (item TD-8), it was noted that
`ai-tasks/PYPOST-376/baseline-metrics.md` is a hand-maintained LOC snapshot checked by
`tests/test_solid_audit_baseline.py::test_markdown_snapshot_matches_current_metrics`.
During PYPOST-1285, developers were forced to edit it by hand because the only documented command
was `.venv/bin/python scripts/audit_baseline_metrics.py --markdown ...`, which violates `AGENTS.md`.
Furthermore, `Makefile` lacked any target to regenerate or check baseline metrics.

Constraints:
- Implementation language: Python and Makefile.
- All lines in documentation and markdown <= 100 characters.
- Must execute all commands exclusively through `make`.

## Q&A

- Q: What should the target names be?
  A: `baseline-metrics` (for regeneration) and `check-baseline-metrics` (for checking caps).
- Q: What dependencies should the Makefile targets have?
  A: `$(VENV_MARKER)` to ensure the virtual environment and python interpreter are available.
- Q: Does `test_markdown_snapshot_matches_current_metrics` fail if only `Makefile` is changed?
  A: Yes, because `test_markdown_snapshot_matches_current_metrics` checks that
  `ai-tasks/PYPOST-376/baseline-metrics.md` matches `format_markdown(measure_all())`.
  Both the script and the markdown file must be synchronized.
