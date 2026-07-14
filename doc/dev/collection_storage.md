# Collection Storage

## Overview

Collections are persisted as JSON under the user data directory. Each file stores a full
`Collection` model (metadata plus all `RequestData` templates). There is no encryption
layer — see [Security (operator guidance)](#security-operator-guidance) below.

## Filename convention

Each collection is persisted as a JSON file under the user data `collections/` directory.
The filename is `{collection.id}.json` — the stable UUID, not the display name.

This decouples persistence identity from rename operations and prevents same-name
collections from overwriting each other's files.

## API

Consumers type-hint against `StorageInterface` (`pypost/core/storage_interface.py`).
`StorageManager` is the production implementation; tests use `FakeStorageManager` or
`MagicMock(spec=StorageInterface)`.

### `StorageManager.save_collection(collection)`

Writes `collection` to `{id}.json`. If a legacy name-based file exists for the same
collection, it is removed after save.

### `StorageManager.delete_collection(collection_id, *, collection_name=None)`

Removes the ID-based file. When `collection_name` is provided, also removes a legacy
name-based file if present.

### `StorageManager.load_collections()`

Loads all `*.json` files. Legacy files whose stem equals `collection.name` (but not
`collection.id`) are migrated to the ID path and the old file is deleted.

## Rename behavior

`RequestManager.rename_collection` updates the `name` field in JSON and calls
`save_collection`. The on-disk filename does not change.

## Duplicate display names

`RequestManager.create_collection` and `rename_collection` reject duplicate
collection display names. Persistence uses collection IDs, so same-name collections
would not overwrite each other on disk, but the UI enforces unique names for clarity.

## Security (operator guidance)

**Finding:** [S-005](security_audit.md#storage-and-ui) (PYPOST-685 audit, remediated in
[PYPOST-713](https://pypost.atlassian.net/browse/PYPOST-713)).

Collection JSON files store request templates in **cleartext**. Each `{collection.id}.json`
file includes every persisted field on `RequestData`: URL, headers, query params, body,
post-script source, and MCP metadata. PyPost does not encrypt collection files at rest.

This is expected for a local API client, but operators are responsible for how secrets
appear in those files.

### What is stored in cleartext

| Field | Risk if secrets are embedded |
| --- | --- |
| `url` | API keys or tokens in query strings persist verbatim |
| `headers` | `Authorization`, API keys, and custom secret headers persist verbatim |
| `params` | Query parameters with credentials persist verbatim |
| `body` | JSON/form payloads with passwords or tokens persist verbatim |
| `post_script` | Hardcoded secrets in script source persist verbatim |

Environment variable **names** in `{{VAR}}` placeholders are stored; resolved values are
not written back into collection JSON. Secrets referenced only through hidden environment
variables therefore do not appear in collection files (see below).

### Recommended pattern: hidden environment variables

Store secrets in **environment variables**, not directly in request fields:

1. Put the secret value in the active environment (e.g. `API_KEY`).
2. Mark the variable **Hidden** in **Manage Environments** so the UI masks it during
   editing and screen sharing. See [Hidden Variables](hidden_variables.md).
3. Reference the variable in the request template: `Authorization: Bearer {{API_KEY}}`.
4. Optionally enable **environment encryption at rest** so hidden values are encrypted in
   `environments.json`. See [Environment Encryption at Rest](environment_encryption_at_rest.md).

Hidden-variable encryption applies to `environments.json` only. Collection files remain
plaintext even when environment encryption is enabled.

### Operational risks

- **Backups and sync** — cloud backup or sync of the user data directory copies collection
  JSON with any embedded secrets.
- **Shared or multi-user hosts** — restrict filesystem permissions on the PyPost data
  directory; treat collection exports like credential files.
- **Version control** — do not commit `{data_dir}/collections/` unless templates use
  `{{VAR}}` placeholders and no live secrets are embedded.

### Related security docs

- [Security and Secrets Handling Audit](security_audit.md) — S-005 finding and full audit
- [Hidden Variables](hidden_variables.md) — UI masking and `hidden_keys`
- [Environment Encryption at Rest](environment_encryption_at_rest.md) — hidden-key encryption
  scope (environments only)
- [Sensitive Data Masking Policy](sensitive_data_masking_policy.md) — history masking scope
