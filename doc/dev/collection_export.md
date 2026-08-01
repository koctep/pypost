# Collection Export

## Overview

**Export Collection** (PYPOST-989) writes the selected sidebar collection — with all of
its requests — to a JSON file the user chooses. The format is PyPost's native collection
serialization: one JSON object, the same shape as `{data_dir}/collections/{id}.json` and
as accepted by [Collection Import](collection_import.md) (PYPOST-987).

It mirrors [Export environments](environments_dialog.md) (PYPOST-988) structurally: a
Qt-free core for payload shaping and file writing, and a thin Qt shell for the save dialog
and result feedback. Collections export one selected tree node at a time (no scope dialog).

## Architecture

```text
CollectionsPresenter.panel          Export Collection… button (COLLECTION_EXPORT_BUTTON)
        │
        ▼  delegates
CollectionExportActions             selection → save dialog → write → result
        │
        ├─ collection_item_dialogs  QFileDialog.getSaveFileName + QMessageBox helpers
        └─ collection_export        pure: resolve target, payload, write, summary
```

- **`pypost/core/collection_export.py`** — pure core. Resolves the export target from a
  collection id, builds the JSON payload via `Collection.model_dump(mode="json")`, writes
  the file, and formats the success summary. No Qt, no storage.
- **`pypost/core/collection_messages.py`** — export dialog titles, button label, file
  filter, and the no-selection message (import strings live in the same module).
- **`pypost/ui/presenters/collection_export_actions.py`** — `CollectionExportActions`.
  Maps the tree's current index to a collection id (collection row or parent of a request
  row), runs the save dialog, writes through the core, and shows success or error.
- **`pypost/ui/collection_item_dialogs.py`** — `prompt_export_collection_file`,
  `show_collection_export_no_selection_error`, `show_collection_export_result`,
  `show_collection_export_error`.
- **`pypost/ui/presenters/collections_presenter.py`** — adds **Export Collection…** next
  to Import in the panel action row; exposes `export_collection()` delegating to
  `CollectionExportActions`. Optional constructor injection `serialize_collection` for tests
  (defaults to `build_export_payload`).

### Round-trip with import

Export produces a single JSON object. Import (`load_collection_import_candidates`) accepts
that shape directly. Automated tests in `tests/test_collection_export.py` assert export →
import field fidelity for method, URL, headers, params, body, scripts, and MCP flags.

### Selection rules

| Tree current index | Exported collection |
| --- | --- |
| Collection row | That collection |
| Request row | Parent collection |
| Invalid / none | Error: select a collection first |

Unlike environment export, there is no Hidden-secrets confirmation — collections do not
store encrypted environment variables.

## Widget identity

| Widget | `objectName` | In `KEY_WIDGET_IDS` |
| --- | --- | --- |
| Export button | `pypost_collection_export_button` | No (same as import button) |

## Tests

| Module | Coverage |
| --- | --- |
| `tests/test_collection_export.py` | Pure logic: target resolution, filename, payload fields, write, import round-trip |
| `tests/test_collection_export_ui.py` | Qt orchestration: button wiring, happy path, cancel, no selection, request → parent, write error, logging |

Run:

```bash
make test PYTEST_ARGS="tests/test_collection_export.py tests/test_collection_export_ui.py"
```

## Related docs

- User guide: `doc/user/collections.md` § Export a collection
- Import counterpart: `doc/dev/collection_import.md`
- On-disk format: `doc/dev/collection_storage.md`
