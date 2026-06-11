# PYPOST-513: Architecture — Body format selector

## Context

- `RequestWidget` (`request_editor.py`) hosts the Body tab with `CodeEditor`.
- `BodyFormat` enum (`fold/fold_region.py`) values match `RequestData.body_type` strings:
  `json`, `yaml`, `xml`, `plain`.
- `CodeEditor.set_body_format()` switches `FoldController` and `ValidationController` registries
  (PYPOST-511, PYPOST-512).
- `RequestData.body_type` defaults to `"json"` and is used by `http_client` for send serialization.

## Design

### Body tab layout

Replace the direct `CodeEditor` tab with a container widget:

```text
┌─ Body tab ─────────────────────────────┐
│ Format: [ JSON ▼ ]                     │
│ ┌────────────────────────────────────┐ │
│ │ CodeEditor (body_edit)             │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
```

- `QComboBox` with items JSON, YAML, XML (display labels; values map to `BodyFormat`).
- `body_edit` remains the `CodeEditor` instance (external references unchanged).
- `body_tab` is the container added to `detail_tabs`; auto-switch targets `body_tab`.

### Mapping helpers

Small functions in `request_editor.py`:

- `body_type_to_body_format(body_type: str) -> BodyFormat` — unknown/legacy → `JSON`.
- `body_format_to_body_type(fmt: BodyFormat) -> str` — returns enum `.value`.

### Event flow

1. `init_ui`: build combo, connect `currentIndexChanged` → `_on_body_format_changed`.
2. `load_data`: set combo from `request_data.body_type`; call `body_edit.set_body_format`.
3. `_on_body_format_changed`: if not `_loading`, call `set_body_format` on editor.
4. `get_request_data_from_ui` / `update_request_data`: set `body_type` from combo.

### Persistence

No model migration needed — `RequestData.body_type` already exists and serializes with
collections/tab state.

## Modules

| Module | Change |
| --- | --- |
| `request_editor.py` | Body tab container, format combo, mapping, load/save `body_type` |
| `tests/test_request_editor_body_format.py` | Selector wiring and persistence tests |
| `tests/test_request_editor_method_tab_switch.py` | Auto-switch targets `body_tab` |

## Decisions

1. **Reuse `body_type` field** — no new model property; selector writes existing string field.
2. **Default JSON** — matches current implicit behavior and `BodyFormat.JSON` default on editor.
3. **No metrics for format change** — low-value UI toggle; observability doc records decision.
4. **Keep JSON highlighter** — format-specific highlighting is out of scope; highlighter stays
   on the document regardless of selected format.

## Q&A

- Q: Why not add `BodyFormat` to `RequestData` as a typed field?
  A: `body_type: str` already exists and is consumed by `http_client`; enum mapping stays in UI
  layer to avoid model churn.
