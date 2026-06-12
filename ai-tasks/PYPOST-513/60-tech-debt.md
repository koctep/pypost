# PYPOST-513: Technical Debt Analysis

## Shortcuts Taken

- JSON syntax highlighter remains active for all formats; YAML/XML-specific highlighting is
  deferred.
- Legacy `body_type` values outside JSON/YAML/XML (e.g. `"text"`) display as JSON in the selector
  until the user saves with an explicit format.

## Code Quality Issues

None identified. Selector wiring follows existing `RequestWidget` patterns (combo + load/save).

## Missing Tests

- No end-to-end GUI test verifying fold chevrons or validation banner switch when format changes
  (depends on YAML/XML scanner/validator implementations in PYPOST-518/PYPOST-519).
- No integrated test that saved collection files round-trip `body_type` through collection load
  (model field already serializes; collection UI path not exercised here).

## Performance Concerns

None. Format change triggers existing debounced fold/validation rescans on the editor.

## Follow-up Tasks

- Implement YAML and XML structure scanners for folding when those formats are selected.
- Implement YAML and XML structure scanners for folding when those formats are selected. — [PYPOST-518](https://pypost.atlassian.net/browse/PYPOST-518)
- Implement YAML and XML body validators when those formats are active.
- Implement YAML and XML body validators when those formats are active. — [PYPOST-519](https://pypost.atlassian.net/browse/PYPOST-519)
- - Add YAML/XML syntax highlighting when format-specific highlighters are available. — [PYPOST-585](https://pypost.atlassian.net/browse/PYPOST-585)
- Add YAML/XML syntax highlighting when format-specific highlighters are available. — Jira: [PYPOST-585](https://pypost.atlassian.net/browse/PYPOST-585) — [PYPOST-585](https://pypost.atlassian.net/browse/PYPOST-585)
