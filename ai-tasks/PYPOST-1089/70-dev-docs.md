# PYPOST-1089: Developer Documentation

## Summary

Step 8 updates the existing MCP developer guide to document the two behaviors shipped in
Steps 3-4: `McpToolParam`'s new `default`-vs-`type` validation, and `McpParamsTable`'s new
editable **Default** column. No new `doc/dev/` file was created — `doc/dev/mcp_integration.md`
already carried the `McpToolParam` / `McpParamsTable` sections from PYPOST-1054 (which
originally flagged both gaps as limitations), so this step closes those flagged items in
place rather than duplicating coverage elsewhere. `grep`-ing `doc/dev/` for `McpParamsTable`,
`request_editor`, and `McpToolParam` before editing confirmed no other `doc/dev/*.md` file
covers either symbol, so a single file was the right target.

## Developer documentation

**File:** `doc/dev/mcp_integration.md` (updated, no new file)

### New section: Default value type validation (PYPOST-1089)

Added `### Default value type validation (PYPOST-1089)` right after the pre-existing
`#### Limitations` subsection of `### Optional MCP parameter defaults (PYPOST-1054)`
(that subsection's two now-resolved bullets were rewritten to point here). Covers:

- **Implementation**: the check runs from `McpToolParam.model_post_init`, calling
  `_validate_default_type()` — explicitly **not** a `@model_validator`-decorated method,
  matching the existing `Settings` convention in `models.py`. This directly closes the
  documentation gap flagged by
  [PYPOST-1098](https://pypost.atlassian.net/browse/PYPOST-1098) (the roadmap/Jira summary
  loosely called it a "model_validator" in prose; the shipped code was always
  `model_post_init`).
- **Type compatibility table**: the seven `type` values and their accepted Python type(s)
  for `default`, taken from reading `_validate_default_type()` in
  `pypost/models/models.py` directly.
- `None` is always permitted regardless of `type`.
- `bool` is explicitly excluded from `integer`, `number`, and `integer_or_string` (Python's
  `bool` is an `int` subclass).
- Where the resulting `ValueError`/`ValidationError` can surface: direct construction,
  loading untrusted collection JSON (cross-referenced to the existing
  `StorageManager.load_collections()` / `load_collection_import_candidates()` error-handling
  documented in `ai-tasks/PYPOST-1089/50-observability.md`), and confirmation that
  `McpParamsTable` itself can never trigger it (its `_COERCERS` always produce a
  type-matched value or `None` before construction).

### Rewritten section: `#### UI` (under Tool metadata authoring)

Replaced the PYPOST-1054-era paragraph ("`McpParamsTable` has no Default column...
renaming a param's Name cell silently drops its preserved default") with:

- The table is now a 5-column `QTableWidget`: Name, Type, Description, Required, Default.
- **Default column: rename-safe by construction** — explains the mechanism change: before
  PYPOST-1089 the default was cached in a name-keyed side dict (`self._defaults`) that
  went stale on rename; now `_set_row`/`get_data()` read/write the default from the same
  table row as the Name cell, so there is no separate key to go stale.
- **`_COERCERS`: type-aware string ↔ value coercion** — documents both directions
  (`_serialise_default` value→string, `_parse_default` string→value dispatch table), with
  a table listing all seven coercer functions and their exact behavior, read directly from
  `pypost/ui/widgets/request_editor.py`.
- **Known limitations** subsection with a brief note on the two behavioral edge cases
  identified in Step 7's tech-debt analysis, each linked to its follow-up ticket:
  scientific-notation numbers silently dropping the default
  ([PYPOST-1095](https://pypost.atlassian.net/browse/PYPOST-1095)) and unrecognized boolean
  text silently coercing to `False` instead of `None`
  ([PYPOST-1096](https://pypost.atlassian.net/browse/PYPOST-1096)), plus the still-open
  type-aware-editor UX gap ([PYPOST-1099](https://pypost.atlassian.net/browse/PYPOST-1099)).

### Smaller updates for consistency

- `#### UI round-trip` (under Optional MCP parameter defaults): "preserves but does not
  expose `default`" → "exposes `default` through an editable Default column".
- `#### Model` field table (Tool metadata authoring): added a one-line pointer from
  `McpToolParam`'s `default` field to the new validation section.
- `## Limitations & Tech Debt`: rewrote the two bullets that previously described both gaps
  as open (`McpToolParam.default` type-checking, no UI affordance) to describe them as
  resolved by PYPOST-1089, each retaining a pointer to its narrower open follow-up
  (PYPOST-1100 for runtime-argument type-checking; PYPOST-1099/1095/1096 for the UI
  edge cases).

## Out of scope for docs

- `doc/user/*` — no user-facing behavior changed; `mcp_params` was already documented
  generically in `doc/user/collections.md` and the Default column is an internal-editor
  detail with no new user-facing concept, consistent with how the Required column was
  never separately documented for end users.
- PYPOST-1100 (runtime MCP argument type-checking) — out of scope per PYPOST-1089's
  Definition of Done (default-only); referenced as a forward pointer only.
- PYPOST-1095/1096/1097/1099 (coercion edge cases, missing tests, type-aware editor) — left
  as brief "known limitations" notes with Jira links, not full write-ups, since none of them
  shipped in this task.

## Verification

- Dev doc content was checked line-by-line against the shipped code
  (`pypost/models/models.py::McpToolParam`, `_validate_default_type`,
  `pypost/ui/widgets/request_editor.py::McpParamsTable`, `_set_row`, `_serialise_default`,
  `_parse_default`, `_COERCERS`, and all seven `_coerce_default_*` functions) rather than
  from the architecture/requirements artifacts alone.
- `grep`-ed `doc/dev/` for `McpParamsTable`, `request_editor`, `McpToolParam` before and
  after editing — only `mcp_integration.md` matched for the first and third; confirmed it
  remains the sole and correct home for this content.
- New/edited heading anchors (`#default-value-type-validation-pypost-1089`, `#model-field`,
  `#ui`) verified against the repo's own slugify algorithm
  (`scripts/check_user_docs_links.py::slugify`); note that script's default target list
  (`doc/user/*.md`, `doc/README.md`, `README.md`, `examples/README.md`) does not include
  `doc/dev/`, so these anchors are not machine-checked by `make lint` — verified by hand
  instead.
- No production or test files were touched in this step.
- Re-ran the full scoped test pair and lint after the doc-only change (see roadmap Step 8
  sub-items for the exact commands and pass/fail counts).
