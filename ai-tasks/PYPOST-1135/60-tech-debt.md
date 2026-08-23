# PYPOST-1135: Technical Debt Analysis

## Shortcuts Taken

1. **Private Attribute Fallback Inspection (`getattr(presenter, "_env_vars")`):**
   - In `WebSocketComposer.send_current_payload()` and `WebSocketStreamView.export_json()` / `export_text()`, active environment variables and hidden keys are retrieved from the presenter using `getattr(self.presenter, "_env_vars", self._variables)` to support standalone widget testing and headless presenter configurations. While this provides backward compatibility and test isolation, it accesses private presenter attributes rather than a formalized public property interface.
2. **Per-Entry Mask Accounting Counter Trigger:**
   - In `build_stream_entry`, the `on_mask_applied` callback is invoked once per entry if any hidden value is masked (`masked_payload or masked_detail`), incrementing `hidden_value_masks_applied_total{surface="websocket"}` by 1 per entry rather than counting each individual secret token occurrence within a multi-secret payload. This follows the existing HTTP stream entry masking metric behavior, but represents an entry-level granularity shortcut.
3. **Template Fast-Path Delimiter Check:**
   - In `WebSocketComposer.send_current_payload()`, a fast-path substring check (`"{{" in raw_payload`) is used before invoking `TemplateService.render_string()`. This avoids unnecessary Jinja parsing overhead on literal payloads, but assumes standard `{{ ... }}` delimiters are always used.

## Code Quality Issues

1. **Encapsulation of Presenter Environment Properties:**
   - `WebSocketPresenter` manages `_env_vars` and `_hidden_keys` as private state. Exposing explicit read-only properties `env_vars -> Mapping[str, str]` and `hidden_keys -> AbstractSet[str]` will eliminate `getattr(..., "_env_vars")` references in child views and models.
2. **Extraction of Query Parameter Merging Helper:**
   - `_merge_url_and_params` in `pypost/ui/presenters/websocket_presenter.py` contains URL parsing and query string combining logic. Moving this pure function to a dedicated utility module (e.g. `pypost/core/websocket_url_utils.py` or `pypost/core/url_helpers.py`) will allow reuse across future WebSocket probe runners and MCP tools.
3. **Widget Hierarchy Hover Interface Standardization:**
   - `VariableAwareTextEdit` was introduced in `pypost/ui/widgets/variable_aware_widgets.py` to wrap `QTextEdit` with `VariableHoverMixin`. Establishing a formal `VariableAwareWidgetProtocol` across line edits, plain text edits, text edits, and tables would unify hover and variable propagation type hints.

## Missing Tests

1. **Large Binary Frame Substitution with Decode Replacement:**
   - While binary frames (Hex / Base64 presentation) and text frames are covered, a specific test verifying behavior when a massive (>10MB) invalid UTF-8 binary stream contains byte patterns that decode to replacement characters (`errors="replace"`) alongside exact secret substrings could be added.
2. **Immutable Retained Ring Mask Invariance on Mid-Session Variable Changes:**
   - While tests verify that handshake entries and sent frames are masked at ingestion time and mid-session variable modifications do not alter active connection parameters, an explicit test asserting that older retained `StreamEntry` objects in `MessageStream` remain unchanged when a new secret is subsequently added to `hidden_keys` could be added to test suites.
3. **Stress Testing of Rapid Egress File Exports:**
   - Automated tests verify JSON and plain-text export formatting and file serialization under normal conditions, but do not test export under high concurrency (e.g. continuous frame ingestion during simultaneous transcript export).

## Performance Concerns

1. **Linear Search in Exact Secret Masking (`_mask_secrets`):**
   - `_mask_secrets` performs sequential `text.replace(val, "***")` across all hidden variable values sorted by length. For normal workspaces (<50 environment variables) and typical payloads (<1MB), execution takes <0.05ms. However, if a workspace contains hundreds of hidden keys and very large payloads (>10MB), string searching could benefit from an Aho-Corasick or multi-pattern matching algorithm.
2. **Synchronous File Export Serialization:**
   - `export_stream_to_json_file` and `export_stream_to_text_file` iterate over all entries in `MessageStream` and format/sanitize them synchronously. For maximum-capacity streams (5,000 entries) with large payloads, exporting on the Qt main thread could take 20-50ms. Moving export processing to a worker thread or chunked async generator would guarantee zero UI frame drops during massive exports.

## Follow-up Tasks

1. **Expose Public Environment Properties on `WebSocketPresenter`:**
   - Refactor `WebSocketPresenter` to expose `@property def env_vars(self) -> dict[str, str]` and `@property def hidden_keys(self) -> set[str]` and update `WebSocketComposer` and `WebSocketStreamView`.
   - Jira: [PYPOST-1143](https://pypost.atlassian.net/browse/PYPOST-1143)
2. **Asynchronous Stream Export Processing:**
   - Implement optional background thread execution for `WebSocketStreamView.export_json` and `WebSocketStreamView.export_text` to keep the UI completely responsive during multi-megabyte exports.
   - Jira: [PYPOST-1144](https://pypost.atlassian.net/browse/PYPOST-1144)
3. **WS-8 TLS Security Policies and Certificate Overrides (Epic PYPOST-1123):**
   - Implement TLS certificate error handling, custom CA bundles, and trust policy overrides for `wss://` endpoints.
   - Jira: [PYPOST-1131](https://pypost.atlassian.net/browse/PYPOST-1131)
4. **WS-9 MCP WebSocket Probe Tools (Epic PYPOST-1123):**
   - Implement Model Context Protocol tools for automated WebSocket session probing and inspection.
   - Jira: [PYPOST-1137](https://pypost.atlassian.net/browse/PYPOST-1137)
5. **WS-10 WebSocket Session Concurrency Ceilings & Settings Persistence (Epic PYPOST-1123):**
   - Implement workspace-wide session limits and connection profile persistence.
   - Jira: [PYPOST-1136](https://pypost.atlassian.net/browse/PYPOST-1136)
