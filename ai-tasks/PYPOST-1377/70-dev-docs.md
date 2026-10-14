# PYPOST-1377: Developer Documentation Record

Developer documentation decisions and records for [PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377) (Layer 1 / MASK-1: Request model, persistence, and RequestEditor UI for hidden response fields under parent epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312)).

## Documentation Updates

1. **Updated Developer Documentation**:
   - [`doc/dev/hidden_response_fields.md`](../../doc/dev/hidden_response_fields.md): Expanded Section 1 to document the full MASK-1 architecture and implementation details:
     - **RequestData Schema Extension**: Details the `hidden_response_fields: list[str] = Field(default_factory=list)` attribute in `pypost/models/models.py`, serialization to JSON arrays, strict string typing, and 100% backward compatibility for legacy collections without schema migrations.
     - **Persisted Field Dirty-Tracking**: Details the inclusion of `"hidden_response_fields"` in `_PERSISTED_FIELD_NAMES` and `_DRAFT_FIELD_NAMES` in `pypost/core/request_persisted_fields.py`, equality checks in `persisted_fields_equal()` and `request_draft_fields_equal()`, and dirty indicator (`*`) integration in `pypost/ui/presenters/tab_dirty.py`.
     - **Tab Copy Isolation Deep-Copy Semantics**: Explains how `copy_request_for_isolated_tab(data)` in `pypost/core/request_persisted_fields.py` clones `hidden_response_fields` into an independent list instance (`list(data.hidden_response_fields)`) to enforce tab draft isolation and prevent cross-tab state mutation.
     - **HiddenFieldsTable Component API**: Documents the `HiddenFieldsTable` widget in `pypost/ui/widgets/hidden_fields_table.py`, including widget identity `REQUEST_HIDDEN_FIELDS_TABLE = "request_hidden_fields_table"`, single-column layout with header `"Field Selector"`, auto-expanding trailing empty row pattern, public methods (`set_data()`, `get_data()`, `add_row()`, `remove_selected_rows()`), signals (`data_changed`, `changed`), context menu, and keyboard shortcuts (`Delete`/`Backspace`).
     - **RequestEditor Detail Tab Integration**: Details the `"Hidden Fields"` detail tab layout in `pypost/ui/widgets/request_editor.py`, header guidance label, toolbar buttons ("Add Selector", "Remove Selected"), and wiring into `load_data()`, `update_request_data()`, `get_request_data_from_ui()`, and change propagation.

2. **Updated User Documentation**:
   - [`doc/user/requests.md`](../../doc/user/requests.md): Added a new `## Hidden fields` section explaining:
     - How users can configure response field selectors to mask sensitive information (tokens, passwords, secrets, PII) in API responses.
     - Adding and managing selectors via the table's auto-expanding trailing row, "Add Selector" / "Remove Selected" buttons, context menu, and keyboard deletion.
     - Supported selector syntax: simple keys (`token`), dot-notation paths (`auth.token`), and array wildcard paths (`users[*].email`).
     - Dual protection goals: visual privacy during screen sharing and irreversible redaction for AI coding agents via MCP.

## Verification Instructions

To verify the developer documentation and project integrity:

1. **Verify AI Task Artifact Integrity**:
   ```bash
   make verify-ai-tasks
   ```
   Validates that all roadmap files, task artifacts, and documentation records conform to repo standards.

2. **Run Static Analysis and Doc Linting**:
   ```bash
   make lint
   ```
   Verifies that Python code passes flake8 and markdown files adhere to linting rules.

3. **Run Test Suite**:
   ```bash
   make test
   ```
   Runs fast test suite including `tests/test_request_hidden_fields_model_and_ui.py` covering model schema, backward-compatible persistence, tab copy isolation, dirty checking, and RequestEditor UI data binding.

## Traceability

- Parent Epic: [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312)
- Architecture Planning: [PYPOST-1376](https://pypost.atlassian.net/browse/PYPOST-1376)
- Foundational Task (MASK-1): [PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377)
- Downstream Stories:
  - MASK-2 (Fail-closed MCP Permanent Masking): [PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378)
  - MASK-3 (GUI Click-to-Reveal in ResponseView): [PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379)
  - MASK-4 (Integration Test Suite and Fixtures): [PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380)
