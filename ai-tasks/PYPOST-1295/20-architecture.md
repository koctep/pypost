# Architecture: PYPOST-1295 — Make Target for Baseline Metrics

## Research

1. **Current State in `scripts/audit_baseline_metrics.py`**:
   `render_markdown` / `format_markdown` builds markdown lines for the baseline LOC table.
   At lines 216-224, it embeds:
   ```markdown
   Regenerate:

   ```sh
   .venv/bin/python scripts/audit_baseline_metrics.py \
     --markdown ai-tasks/PYPOST-376/baseline-metrics.md
   ```
   ```
   This direct `.venv/bin/python` instruction contradicts `AGENTS.md` (make-only rule).

2. **Current State in `ai-tasks/PYPOST-376/baseline-metrics.md`**:
   The static snapshot contains the identical `.venv/bin/python` snippet.

3. **Current State in `tests/test_solid_audit_baseline.py`**:
   `test_markdown_snapshot_matches_current_metrics` compares the verbatim content of
   `_BASELINE_SNAPSHOT.read_text(encoding="utf-8")` against
   `_baseline.format_markdown(_baseline.measure_all())`.

4. **Makefile Conventions**:
   Existing tool/fixture generation targets follow:
   - Target names using kebab-case (e.g. `generate-mcp-fixtures`, `check-mcp-fixtures`,
     `generate-license-inventory`, `check-license-inventory`).
   - `.PHONY` listing at the top of `Makefile`.
   - `##` help docstrings aligned for `make help`.
   - Recipe invokes `$(BIN)/python scripts/...` guarded by `$(VENV_MARKER)`.

## Implementation Plan

### Step 3: Failing Repro Test
- Add unit assertions in `tests/test_solid_audit_baseline.py`:
  - `test_regeneration_instructions_prescribe_make_target`:
    Assert that `_baseline.format_markdown(_baseline.measure_all())` contains
    `make baseline-metrics` and does NOT contain `.venv/bin/python`.
  - Assert that `_BASELINE_SNAPSHOT.read_text(encoding="utf-8")` contains
    `make baseline-metrics`.
  - Also verify in a Makefile contract test that `baseline-metrics` and
    `check-baseline-metrics` exist as make targets.
- Before Step 4 code changes, this test will fail because `format_markdown` produces
  the old `.venv/bin/python` instruction.

### Step 4: Development
1. **`Makefile`**:
   - Add `baseline-metrics` and `check-baseline-metrics` to `.PHONY`.
   - Add targets:
     ```makefile
     baseline-metrics: $(VENV_MARKER) ## Regenerate baseline-metrics.md LOC snapshot
     	$(BIN)/python scripts/audit_baseline_metrics.py \
     		--markdown ai-tasks/PYPOST-376/baseline-metrics.md

     check-baseline-metrics: $(VENV_MARKER) ## Verify SOLID audit module inventory caps
     	$(BIN)/python scripts/audit_baseline_metrics.py --check
     ```
2. **`scripts/audit_baseline_metrics.py`**:
   - Update `format_markdown` to output `make baseline-metrics`.
3. **`ai-tasks/PYPOST-376/baseline-metrics.md`**:
   - Regenerate via `make baseline-metrics` (or update lines 35-40).
4. **Verification**:
   - Run `make test` on `tests/test_solid_audit_baseline.py` and `tests/test_makefile_targets.py`.
   - Verify `make baseline-metrics` and `make check-baseline-metrics` succeed.

## Architecture

```
                  +----------------------------------------------+
                  |                   Makefile                   |
                  |                                              |
                  |  baseline-metrics:                           |
                  |    $(BIN)/python scripts/audit_baseline_     |
                  |      metrics.py --markdown <path>            |
                  |                                              |
                  |  check-baseline-metrics:                     |
                  |    $(BIN)/python scripts/audit_baseline_     |
                  |      metrics.py --check                      |
                  +----------------------+-----------------------+
                                         |
                                         v
                      +--------------------------------------+
                      |  scripts/audit_baseline_metrics.py   |
                      |                                      |
                      |  format_markdown():                  |
                      |    outputs "make baseline-metrics"   |
                      +------------------+-------------------+
                                         |
                                         v
                      +--------------------------------------+
                      | ai-tasks/PYPOST-376/baseline-metrics |
                      |                                      |
                      | Regenerate:                          |
                      | ```sh                                |
                      | make baseline-metrics                |
                      | ```                                  |
                      +------------------+-------------------+
                                         ^
                                         |
                      +------------------+-------------------+
                      | tests/test_solid_audit_baseline.py   |
                      |                                      |
                      | test_markdown_snapshot_matches...    |
                      | test_regeneration_instructions...    |
                      +--------------------------------------+
```

## Q&A

- Q: Should `make check` also include `check-baseline-metrics`?
  A: No, `tests/test_solid_audit_baseline.py` is already part of the fast test suite run by
  `make test` and `make check`, which already enforces caps via `check_caps()`. Adding a separate
  target `check-baseline-metrics` provides a fast CLI target without running the full test suite.
- Q: Are any new dependencies needed?
  A: None. The script uses only the standard library (`argparse`, `dataclasses`, `pathlib`, `sys`).
