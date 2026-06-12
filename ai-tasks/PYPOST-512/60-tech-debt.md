# PYPOST-512: Technical Debt Analysis

## Shortcuts Taken

- YAML and XML validators are stubs returning no errors until PYPOST-513 wires `BodyFormat` from
  the format selector and concrete parsers ship.
- Only the first JSON parse error is shown (`json.loads()` single `JSONDecodeError`).

## Code Quality Issues

- `ValidationController` accesses `_error_label` in tests for visibility checks; acceptable test
  shortcut mirroring fold controller `_run_scan()` pattern.
- Error banner is a child `QLabel` overlaid on the editor bottom; may overlap last visible line
  on very short editors — acceptable for typical Body tab height.

## Missing Tests

- No test that validation line numbers stay correct when fold regions hide intermediate lines
  (logical line numbers should still match — not exercised automatically).
- No YAML/XML validation tests (validators are stubs until format selector lands).
- No integrated `RequestWidget` test asserting error banner on Body tab.

## Performance Concerns

- `json.loads()` runs on full document every debounced validation (200 ms), same cost as fold
  scanner gate. Fine for typical payloads.

## Follow-up Tasks

- Implement YAML and XML body validators when those formats are active via format selector.
- Implement YAML and XML body validators when those formats are active via format selector. — [PYPOST-519](https://pypost.atlassian.net/browse/PYPOST-519)
  [PYPOST-513](https://pypost.atlassian.net/browse/PYPOST-513))
- Add unit test for validation error line alignment with folded/hidden blocks.
- Add unit test for validation error line alignment with folded/hidden blocks. — [PYPOST-520](https://pypost.atlassian.net/browse/PYPOST-520)
- Extend RequestWidget integration test to assert body validation banner on invalid JSON.
- Extend RequestWidget integration test to assert body validation banner on invalid JSON. — [PYPOST-521](https://pypost.atlassian.net/browse/PYPOST-521)
