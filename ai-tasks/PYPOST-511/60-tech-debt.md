# PYPOST-511: Technical Debt Analysis

## Shortcuts Taken

- YAML and XML folding use stub scanners that return no regions until PYPOST-513 wires
  `BodyFormat` from the format selector. JSON folding is fully implemented.
- `JsonStructureScanner` validates with `json.loads()` before a line-based brace scan; invalid
  documents get no folds (all-or-nothing gate per architecture).

## Code Quality Issues

- `FoldController.apply_visibility()` resets all blocks visible then hides collapsed ranges in a
  single pass. Correct but O(blocks × collapsed_regions); acceptable for body payload sizes.
- Tests call `FoldController._run_scan()` directly to bypass the debounce timer; production uses
  `QTimer` (200 ms). Acceptable test shortcut.

## Missing Tests

- No test that collapsed region IDs survive debounced re-scan after edits elsewhere in the
  document (only boundary-unchanged regions are kept).
- document (only boundary-unchanged regions are kept). — [PYPOST-517](https://pypost.atlassian.net/browse/PYPOST-517)
- No automated test that `RequestWidget` Body tab shows fold chevrons in an integrated hierarchy
  (covered indirectly via `CodeEditor` unit tests).
  Jira: extend [PYPOST-516](https://pypost.atlassian.net/browse/PYPOST-516) (non-blocker)
- No YAML/XML folding tests (scanners are stubs until format selector lands).

## Performance Concerns

- `JsonStructureScanner` runs `json.loads()` on the full document plus a character scan on every
  debounced re-scan. Fine for typical payloads; very large bodies may benefit from a single-pass
- debounced re-scan. Fine for typical payloads; very large bodies may benefit from a single-pass — [PYPOST-637](https://pypost.atlassian.net/browse/PYPOST-637)

## Follow-up Tasks

- Implement YAML and XML structure scanners and enable folding when those formats are active.
- Implement YAML and XML structure scanners and enable folding when those formats are active. — [PYPOST-518](https://pypost.atlassian.net/browse/PYPOST-518)
  [PYPOST-513](https://pypost.atlassian.net/browse/PYPOST-513))
- Add unit tests for fold remapping after document edits while sections are collapsed.
- Add unit tests for fold remapping after document edits while sections are collapsed. — [PYPOST-517](https://pypost.atlassian.net/browse/PYPOST-517)
- Extend RequestWidget integration test to assert body gutter chevrons and fold toggle.
- Extend RequestWidget integration test to assert body gutter chevrons and fold toggle. — [PYPOST-516](https://pypost.atlassian.net/browse/PYPOST-516)
