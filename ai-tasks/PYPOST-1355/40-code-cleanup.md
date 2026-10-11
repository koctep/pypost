# PYPOST-1355: Code Cleanup Report

## Linter Fixes

`make lint` passes with no task-added warnings. Step 4 already wrapped the three reported
long lines. This step grouped the shared collection creation contract with core imports in
`mcp_controls_presenter.py` and the editor helper with its UI peers in `mcp_servers_dialog.py`.
These are import-order changes only.

## Code Formatting

The task uses four-space indentation, maximum 100-character production lines, and existing
UTF-8/LF conventions. No automatic formatting target exists in this Makefile, so no raw
formatter was invoked. The repository exposes `make lint` rather than the generic skill's
`make analyze`; the repository's required static-analysis target was used.

## Code Cleanup

The canonical owner and editor action remain delegated to cohesive helpers. No unused
task-added imports or variables, debug prints, stubs, commented-out code, or merge conflict
markers were found. No behavior, tests, module caps, or baseline thresholds changed during
cleanup. Existing storage publication and Save/Cancel boundaries are retained.

## Validation Results

- `make lint typecheck check-baseline-metrics`: passed after import grouping;
  `/tmp/pypost1355-step5-quality.log`.
- Typecheck accepted the unchanged baseline of 181 known errors. This is a baseline gate,
  not a claim that the entire repository has no type errors.
- Step 4 passed all 16 reviewed repro cases and all 10 focused regression modules;
  independent Step 4 review reran and passed the 16-case repro.
- Step 4 follow-up checks passed the repro, encrypted-startup adapter, audit CLI, and dialog
  inventory modules after repairing the task-caused failures from the broad run.
- The repro retains an explicit module-level `pytest.mark.timeout(30)`, bounded 5000 ms
  teardown, and scoped busy stubs restored before fixture teardown. No tests changed here.
- No broad test repeat was needed for these import-only edits. The previous full
  `make check` reported 369 passed, 14 failed, and 7 skipped files. Three failed modules were
  repaired and retested; the remaining 11 belong to the filed baseline clusters below.

## Notes

Known baseline failures are tracked in [PYPOST-1298][make-timeouts],
[PYPOST-1299][exit-policy], [PYPOST-1361][snapshots], and [PYPOST-1362][registry-race].
The [roadmap](00-roadmap.md) retains the exact full-gate failure nodes and classification.
No unrelated historical snapshot or infrastructure fix is included. Step 5 remains in
progress until independent acceptance review.

[make-timeouts]: https://pypost.atlassian.net/browse/PYPOST-1298
[exit-policy]: https://pypost.atlassian.net/browse/PYPOST-1299
[snapshots]: https://pypost.atlassian.net/browse/PYPOST-1361
[registry-race]: https://pypost.atlassian.net/browse/PYPOST-1362
