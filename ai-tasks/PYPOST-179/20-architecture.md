# PYPOST-179: Architecture

## Components

| Component | Role |
| --- | --- |
| `pypost/fixtures/mcp_test_fixtures.py` | Canonical builders, paths, serialize helpers, model-equality check |
| `scripts/generate_mcp_test_fixtures.py` | Operator CLI (`write` default, `--check` for drift detection) |
| `tests/test_generate_mcp_test_fixtures.py` | Builder parity and CLI `--check` smoke |
| `tests/helpers/mcp_test_collection.py` | Unchanged loaders; committed files remain source for CI |

## Data flow

```text
build_mcp_test_collection() ──► serialize_collection() ──► examples/collections/mcp.json
build_mcp_test_environments() ──► serialize_environments() ──► config/test/environments.json
```

`fixtures_match_committed()` compares **parsed models**, not raw bytes, so new optional
Pydantic fields can appear in regenerated JSON without breaking validation.

## Serialization

- Collections: `Collection.model_dump_json(indent=2)` — same as `StorageManager.save_collection`.
- Environments: `json.dumps([env.model_dump(mode="json")], indent=2)` for array file format.

## CLI

| Flag | Behavior |
| --- | --- |
| (default) | Write both fixture files |
| `--check` | Exit 0 when model equality holds; 1 with stderr message otherwise |

## Out of scope

- Makefile target (optional follow-up)
- Merging into user `~/.local/share/pypost` data dirs (documented in `config/test/README.md`)
