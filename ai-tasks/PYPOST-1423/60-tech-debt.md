# PYPOST-1423: Technical Debt Analysis

## Shortcuts Taken

1. **Dialog module still above 500 physical LOC**:
   After extracting the four virtualization components, `import_collection_variables_dialog.py`
   is ~637 lines because `ImportCollectionVariablesDialog` alone is ~555 lines. The Step 3
   acceptance OR (classes in target modules) is satisfied; the absolute <500 LOC aspirational
   target is not.

2. **Backward-compatible re-exports retained on the dialog module**:
   Tests and callers still import model/view/delegate/worker symbols from
   `pypost.ui.dialogs.import_collection_variables_dialog`. This preserves green suites without
   a broad import migration, but keeps the dialog as a facade package.

## Code Quality Issues

1. **Monolithic dialog class**:
   Layout construction, remote-fetch orchestration, and import acceptance remain in one
   `QDialog` subclass. Further extraction (e.g. fetch controller / UI builder) would be needed
   to bring the dialog *file* under 500 LOC.
2. **Compatibility facade proxies remain**:
   `HeaderItemProxy` / `TableItemProxy` / synthetic `cellWidget` still exist in the view module
   (originated in PYPOST-1415); dual mutation pathways unchanged.

## Missing Tests

1. **Direct imports from new module paths**:
   Suites still exercise components via dialog re-exports. Optional follow-up: add thin import
   smoke tests against `pypost.ui.models|views|delegates|workers` paths.
2. Pre-existing gaps from PYPOST-1415 (fault injection, accessibility) remain out of scope.

## Performance Concerns

None introduced by this extract. Virtualization and worker behavior unchanged.

## Follow-up Tasks

1. **Split `ImportCollectionVariablesDialog` to finish sub-500 dialog LOC**:
   - Extract remote-fetch orchestration and/or UI layout builder so
     `import_collection_variables_dialog.py` is physically under 500 lines.
   - Priority: Medium
   - Jira: [PYPOST-1448](https://pypost.atlassian.net/browse/PYPOST-1448)
2. **Migrate callers off dialog re-exports**:
   - Update tests/docs to import virtualization classes from dedicated modules; then slim
     dialog `__all__` re-exports.
   - Priority: Low
   - Jira: [PYPOST-1449](https://pypost.atlassian.net/browse/PYPOST-1449)
3. **`NON-BLOCKER — pre-existing`: lockfile drift / makefile concurrency failures**:
   - Inherited from PYPOST-1415 follow-ups [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397),
     [PYPOST-1413](https://pypost.atlassian.net/browse/PYPOST-1413) — not re-verified in this
     scoped run.
