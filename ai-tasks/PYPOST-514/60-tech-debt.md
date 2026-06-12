# PYPOST-514: Technical Debt Analysis

## Shortcuts Taken

No significant shortcuts. Send-time conversion lives in `HTTPClient._prepare_request_kwargs`
via a pure `yaml_json_converter` module, matching the architecture plan. PyYAML with
`safe_load_all` was chosen over `ruamel.yaml` as a documented trade-off (YAML 1.1 semantics,
lighter dependency) rather than a temporary workaround.

Intentional scope limits (not shortcuts):
- `CurlGenerator` and history continue to use editor YAML text, not the wire JSON payload.
- Conversion applies only on the HTTP send path; MCP requests are unchanged.

## Code Quality Issues

- `_update_yaml_as_json_enabled()` duplicates the `setEnabled` logic already in
  `_on_body_format_changed()`. Low impact; could be collapsed to a single helper when
  touched next.
- `ErrorCategory.BODY` is named for YAML→JSON conversion today but may broaden when
  PYPOST-518 adds YAML validation; message templates should stay category-specific.

## Missing Tests

- No `tabs_presenter` test for `ErrorCategory.BODY` user-facing dialog text (NETWORK,
  TIMEOUT, TEMPLATE, and UNKNOWN are covered in `test_tabs_presenter.py`).
- No assertion that `yaml_to_json_conversion_failed` ERR log is emitted on conversion
  failure (conversion and `ExecutionError` paths are tested; log content is not).
- No `RequestService` integration test exercising real `HTTPClient` YAML conversion
  end-to-end (retry tests mock `send_request`; HTTP tests mock `session.request`).

Coverage that meets requirements: converter unit tests, HTTP send-path tests (flag on/off,
invalid YAML, format gating), UI checkbox persistence/enabled-state, and BODY non-retry
behavior.

## Performance Concerns

None material. PyYAML parse plus `json.dumps` validation runs only when
`body_type == "yaml"`, `yaml_as_json` is true, and the body is non-blank. Typical API
payload sizes make this negligible on the send path.

## Follow-up Tasks

- **Copy cURL / history parity** — Apply `yaml_as_json` in `CurlGenerator.generate` so
  exported cURL matches the JSON wire body when conversion is enabled. History entries
  intentionally keep editor YAML; document or offer opt-in wire-form export if users need
- intentionally keep editor YAML; document or offer opt-in wire-form export if users need — [PYPOST-522](https://pypost.atlassian.net/browse/PYPOST-522)
- **Paste-time JSON→YAML** — PYPOST-515 shares the `yaml_as_json` flag for editor paste
  behavior; no PYPOST-514 changes required until that task ships.
- behavior; no PYPOST-514 changes required until that task ships. — [PYPOST-515](https://pypost.atlassian.net/browse/PYPOST-515)
- **BODY error dialog test** — Add `test_tabs_presenter` coverage for
  `ErrorCategory.BODY` message formatting.
- `ErrorCategory.BODY` message formatting. — [PYPOST-523](https://pypost.atlassian.net/browse/PYPOST-523)
- **Conversion analytics** — Optional `track_yaml_to_json_conversion_failed` counter (no
  body content) if failure rates become useful for support.
- body content) if failure rates become useful for support. — [PYPOST-524](https://pypost.atlassian.net/browse/PYPOST-524)
- **User documentation** — YAML 1.1 boolean/tag semantics covered in STEP 7 dev docs
  (`doc/dev/yaml_as_json.md`); cURL/history vs wire body behavior documented.
