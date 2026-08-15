# Shared JSON Export Root Policy

## Overview

PYPOST-1010 defines one JSON root-shape contract for exports of record lists:

- Exactly one record is written as a JSON object.
- Zero records or more than one record are written as a JSON array.

The policy changes only the outer JSON container. It does not change record fields, record
ordering, serialization, file encoding, import conflict handling, or encryption behavior. An
empty bulk export remains the valid JSON array `[]`.

## Architecture

`pypost.core.json_export_root.json_root_for_records` is the single, Qt-free policy helper. It
accepts an already-serialized `list[dict]`, returns its sole dictionary when the list has one
item, and otherwise returns the original list. It does no model access, I/O, logging, or copying.

```text
existing serializer -> list[dict] -> json_root_for_records -> existing file writer -> JSON file
```

The helper is called at every final export seam that owns a JSON-ready record list:

- `pypost.core.environment_export.build_export_payload` for the core environment export path.
- `EnvironmentListWidget.export_environments` after its injected environment serializer.
- `CollectionExportActions.export_all_collections` after its injected collection serializer.

Single-collection export already produces one dictionary and therefore does not call the helper.
Environment and collection importers already accept either an object or an array and normalize an
object to one candidate, so no import behavior changes.

## API / Usage

```python
from pypost.core.json_export_root import json_root_for_records

payload = json_root_for_records(serialized_records)
write_export_file(destination, payload)
```

`serialized_records` must be the complete ordered `list[dict]` for one export operation. Call the
helper once, immediately before the existing domain writer. Do not call it per record, serialize
inside it, or add duplicate one-record conditionals at callers.

| Number of records | Returned root |
| --- | --- |
| `0` | The original empty list (`[]`) |
| `1` | The single record dictionary |
| `2+` | The original ordered list |

The helper returns existing objects rather than copies. Callers must treat their serialized input
as the payload source and keep any mutations or domain conversions before this boundary.

## Configuration

There are no settings, environment variables, feature flags, or user choices for this policy. The
existing collection and environment export dialogs continue to choose scope and destination; the
record count determines the JSON root automatically.

## Observability

The helper deliberately emits no log events because logging serialized records could disclose
collection content or environment values. Existing action-layer completion and failure events,
including `collections_export_completed`, `collections_export_failed`,
`environment_export_completed`, and `environment_export_failed`, remain the operational signals.

## Troubleshooting

### One-record bulk export is an array

Ensure the final export action passes its complete serialized record list through
`json_root_for_records` immediately before `write_export_file`. Updating only a core bulk builder
is insufficient when a UI action uses an injected serializer directly.

### Empty bulk export is an object or fails

Do not special-case an empty list. The policy returns `[]`, which remains a valid, importable
empty export.

### Import rejects a one-record export

Check that the writer received the one dictionary as one JSON document, not a list serialized to a
string. Both `load_import_candidates` and `load_collection_import_candidates` accept object and
array roots; a failure usually indicates malformed JSON or invalid record content instead.

### Environment export has a different root than the core path

The Qt widget uses an injected serializer for testability, so it must apply the shared helper after
that injected callable returns records. Keep it aligned with
`environment_export.build_export_payload`.

## Tests

`tests/test_json_export_root.py` covers zero, one, and multiple records. The export workflow
coverage in `tests/test_collection_export_ui.py` and `tests/test_environment_export_ui.py` verifies
that the final written JSON root follows the policy at the injected UI seams.

Run the focused checks with:

```bash
uv run pytest -q tests/test_json_export_root.py tests/test_collection_export_ui.py \
  tests/test_environment_export.py tests/test_environment_export_ui.py
```

## Related docs

- [Collection Export](collection_export.md)
- [Environments Dialog](environments_dialog.md#export-environments-pypost-988)
- [Collection Import](collection_import.md)
