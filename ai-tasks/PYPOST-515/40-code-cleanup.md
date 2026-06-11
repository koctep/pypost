# PYPOST-515: Code Cleanup

## Review

- `convert_json_object_to_yaml` lives beside send-path `convert_yaml_body_to_object` in
  `yaml_json_converter.py` — single module for YAML/JSON body helpers.
- Paste branch in `insertFromMimeData` is a small conditional; no new widget subclasses.
- `_sync_yaml_as_json_to_editor` centralizes editor flag updates from format and checkbox.

## Changes made

None beyond implementation — no dead code or unused imports introduced.

## Deferred

- Collapse `_update_yaml_as_json_enabled` duplicate in `request_editor.py` (from PYPOST-514
  tech debt) — not touched in this task.
