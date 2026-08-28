# Collection Format v2 (Self-Contained Collections)

## Overview

**Self-Contained Collection Format v2** ([PYPOST-1220](https://pypost.atlassian.net/browse/PYPOST-1220), part of parent epic [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219)) introduces a version-control-friendly, portable collection representation supporting both **YAML** (`.yaml` / `.yml`) and **JSON** (`.json`) formats.

Prior to v2, PyPost collections were stored and exported primarily as raw request trees with loose, untyped environment bindings in separate files. Format v2 addresses this by embedding:

1. **Explicit Variable Metadata Schemas**: Variable definitions with typed constraints (`string`, `integer`, `number`, `boolean`, `array`, `object`), default values, descriptions, required flags, and secret flags.
2. **Preset Profiles**: Named environment profiles (e.g., `local`, `staging`, `production`) embedded directly in the collection definition, mapping variable names to override values.
3. **Multi-Format Serialization**: Deterministic, human-readable YAML for clean Git diffs and pull requests, alongside standard JSON for machine interchange.
4. **Full Backward Compatibility**: Transparent bidirectional compatibility with legacy PyPost collection files and single/bulk import/export workflows.

---

## Architecture & Data Models

```text
pypost/
├── models/
│   ├── collection_variable.py       # CollectionVariable model, type whitelist & validation
│   ├── models.py                    # Enhanced Collection model with variables & presets
│   └── __init__.py                  # Re-exports CollectionVariable
└── core/
    ├── collection_serializer.py     # Pure YAML & JSON serialization/deserialization logic
    ├── collection_export.py         # Format-aware export payloads & file writing
    ├── collection_import.py         # YAML/JSON import parsing & candidate materialization
    └── collection_messages.py       # User-facing diagnostics and error strings
```

```mermaid
graph TD
    subgraph Models [pypost.models]
        CV[CollectionVariable<br/>- name: str<br/>- type: str<br/>- default: Any<br/>- description: str<br/>- required: bool<br/>- secret: bool]
        RD[RequestData]
        WS[WebSocketConnection]
        MCP[McpClientConnection]
        
        COL[Collection<br/>- id: str<br/>- name: str<br/>- description: str<br/>- version: str<br/>- variables: list[CollectionVariable]<br/>- presets: dict[str, dict[str, Any]]<br/>- requests: list[RequestData]<br/>- websockets: list[WebSocketConnection]<br/>- mcp_clients: list[McpClientConnection]]
        
        COL --> CV
        COL --> RD
        COL --> WS
        COL --> MCP
    end

    subgraph Serializer [pypost.core.collection_serializer]
        SER_YAML[serialize_collection_to_yaml]
        SER_JSON[serialize_collection_to_json]
        DES_YAML[deserialize_collection_from_yaml]
        DES_JSON[deserialize_collection_from_json]
        READ_FILE[read_collection_file]
        WRITE_FILE[write_collection_file]
        
        COL <--> SER_YAML
        COL <--> SER_JSON
        COL <--> DES_YAML
        COL <--> DES_JSON
        COL <--> READ_FILE
        COL <--> WRITE_FILE
    end

    subgraph Subsystems [pypost.core]
        EXP[collection_export.py<br/>Export YAML/JSON]
        IMP[collection_import.py<br/>Import YAML/JSON/Legacy]
        
        EXP --> WRITE_FILE
        IMP --> DES_YAML
        IMP --> DES_JSON
    end
```

---

## `CollectionVariable` Model & Supported Type Schemas

`CollectionVariable` (`pypost/models/collection_variable.py`) defines the schema metadata for an individual variable declared on a collection.

### Attributes

| Attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `name` | `str` | *required* | Unique variable identifier (non-empty). |
| `type` | `str` | `"string"` | Declared data type from `COLLECTION_VARIABLE_TYPES`. |
| `default` | `Any \| None` | `None` | Optional default fallback value conforming to `type`. Aliased as `default_value`. |
| `description` | `str` | `""` | Human-readable explanation / documentation for consumers and agents. |
| `required` | `bool` | `False` | When `True`, an effective value must be supplied before request execution. |
| `secret` | `bool` | `False` | When `True`, indicates sensitive credentials (passwords, tokens) to exclude from version-controlled defaults. |

### Supported Type Whitelist

The `COLLECTION_VARIABLE_TYPES` frozenset defines the supported type identifiers and their validation rules (`validate_variable_value`):

| Type Name | Allowed Python Types | Validation Rules & Disallowed Values |
| --- | --- | --- |
| `string` | `str` | Rejects non-string types (numbers, booleans, lists, dicts). |
| `integer` | `int` | Strictly integer (`isinstance(v, int) and not isinstance(v, bool)`). Rejects `bool` (0/1), floats, and strings. |
| `number` | `int`, `float` | Numeric types (`not isinstance(v, bool)`). Rejects `bool` and non-numeric strings. |
| `boolean` | `bool` | Strict boolean (`True` / `False`). Rejects `0`/`1` and `"true"`/`"false"`. |
| `array` | `list` | List of items (`isinstance(v, list)`). |
| `object` | `dict` | Key-value dictionary mapping (`isinstance(v, dict)`). |

A `None` (or YAML/JSON `null`) default value is always accepted regardless of `type`, representing the absence of a default.

---

## Preset Profiles & Variable Overrides

Collections support named preset profiles via the `presets: dict[str, dict[str, Any]]` field on `Collection`.

- **Key**: Unique profile name within the collection (e.g. `local`, `staging`, `production`).
- **Value**: Mapping of variable name to override value (`dict[str, Any]`).

### Example YAML Representation

```yaml
id: col-auth-service
name: Authentication Service
description: Core identity and token issuance API
version: 1.2.0
variables:
  - name: base_url
    type: string
    default: "https://auth.example.com"
    description: "Base URL for the authentication gateway"
    required: true
    secret: false
  - name: client_secret
    type: string
    default: null
    description: "OAuth2 client secret"
    required: true
    secret: true
  - name: timeout_seconds
    type: integer
    default: 15
    description: "HTTP client request timeout in seconds"
    required: false
    secret: false
presets:
  local:
    base_url: "http://localhost:9000"
    timeout_seconds: 5
  staging:
    base_url: "https://staging.auth.example.com"
    timeout_seconds: 10
  production:
    base_url: "https://auth.example.com"
    timeout_seconds: 30
requests:
  - id: req-login
    name: Token Grant
    method: POST
    url: "{{base_url}}/oauth/token"
    headers:
      Content-Type: "application/json"
    params: {}
    body: '{"grant_type": "client_credentials", "client_secret": "{{client_secret}}"}'
    body_type: json
    yaml_as_json: false
    post_script: "assert response.status_code == 200"
    expose_as_mcp: false
    mcp_description: ""
    mcp_params: {}
    retry_policy: null
websockets: []
mcp_clients: []
```

---

## Core Serializer API (`pypost.core.collection_serializer`)

The `pypost.core.collection_serializer` module provides pure functions for serializing, deserializing, reading, and writing collections.

### Exceptions

- **`CollectionSerializationError(Exception)`**: Base exception raised when serialization or deserialization fails.
- **`CollectionFormatError(CollectionSerializationError)`**: Raised when the payload root is not a dictionary/object or the format structure is malformed.

### Functions

#### `serialize_collection_to_yaml(collection: Collection) -> str`
Serializes a `Collection` instance into a human-readable, deterministic YAML string using `yaml.safe_dump(sort_keys=False, allow_unicode=True)`.

#### `deserialize_collection_from_yaml(content: str) -> Collection`
Parses a YAML string via `yaml.safe_load`, validates the root object mapping, and constructs a validated `Collection` instance. Raises `CollectionSerializationError` on syntax or validation errors.

#### `serialize_collection_to_json(collection: Collection, indent: int = 2) -> str`
Serializes a `Collection` instance into an indented, UTF-8 JSON string via `collection.model_dump_json(indent=indent)`.

#### `deserialize_collection_from_json(content: str) -> Collection`
Parses a JSON string via `json.loads`, validates that the root is an object, and instantiates a `Collection`. Raises `CollectionSerializationError` on decode or validation errors.

#### `serialize_collection_to_dict(collection: Collection) -> dict[str, Any]`
Converts a `Collection` instance into a JSON-serializable Python dictionary via `collection.model_dump(mode="json")`.

#### `serialize_collection_to_legacy_dict(collection: Collection) -> dict[str, Any]`
Converts a `Collection` instance into a dictionary compatible with legacy PyPost consumers.

#### `deserialize_collection_from_dict(data: dict[str, Any]) -> Collection`
Constructs and validates a `Collection` from a dictionary. Raises `CollectionFormatError` if `data` is not a `dict`, and `CollectionSerializationError` if validation fails.

#### `read_collection_file(path: Path | str) -> Collection`
Reads and deserializes a file from disk. Format detection:
1. `.yaml` / `.yml` $\rightarrow$ parses with `deserialize_collection_from_yaml`.
2. `.json` $\rightarrow$ parses with `deserialize_collection_from_json`.
3. Other/unknown extension $\rightarrow$ attempts JSON deserialization first, falling back to YAML.

#### `write_collection_file(collection: Collection, path: Path | str, format: str = "auto") -> Path`
Writes a collection to disk in YAML or JSON format, automatically creating parent directories.
- `format`: `"yaml"`, `"json"`, or `"auto"` (inferred from `path.suffix`).
- Returns the resolved `Path`.
- Raises `CollectionSerializationError` on write errors or unsupported formats.

---

## Export & Import Integration

### Export Subsystem (`pypost.core.collection_export`)

- **Format-Aware Writing**: `write_export_file(path, payload, format="auto")` automatically selects YAML safe dumping or JSON writing based on target file extension (`.yaml`/`.yml` vs `.json`).
- **Payload Preservation**: `build_export_payload` and `build_all_export_payload` preserve all v2 fields (`variables`, `presets`, `description`, `version`, `websockets`, `mcp_clients`, `requests`).
- **Suggested Filename**: `suggested_export_filename(collection, extension="json")` supports custom extensions for format-specific workflows.

### Import Subsystem (`pypost.core.collection_import`)

- **Multi-Format Ingestion**: `_read_records` seamlessly parses `.yaml`/`.yml` files alongside `.json` files.
- **Single and Multi-Record Normalization**: Normalizes single collection mappings (`dict`) or collection arrays (`list[dict]`).
- **Materialization & Identity Preservation**: `_materialize` preserves `description`, `version`, `variables`, `presets`, `websockets`, and `mcp_clients` when resolving ID conflicts and instantiating imported collections.
- **Backward Compatibility**: Ingesting legacy JSON files without `variables` or `presets` automatically initializes default empty collections (`variables=[]`, `presets={}`, `version="1.0.0"`, `description=""`) without validation errors.

---

## Observability & Logging

All serializer and file I/O operations log structured `key=value` events:

| Event | Level | Module | Fields |
| --- | --- | --- | --- |
| `collection_deserialization_failed` | WARNING | `collection_serializer` | `reason` |
| `collection_yaml_parse_failed` | WARNING | `collection_serializer` | `reason` |
| `collection_yaml_invalid_root` | WARNING | `collection_serializer` | `type` |
| `collection_json_parse_failed` | WARNING | `collection_serializer` | `reason` |
| `collection_json_invalid_root` | WARNING | `collection_serializer` | `type` |
| `collection_file_read_failed` | WARNING | `collection_serializer` | `path`, `reason` |
| `collection_file_read` | INFO | `collection_serializer` | `path`, `format`, `requests`, `variables`, `presets` |
| `collection_file_write_failed` | WARNING | `collection_serializer` | `path`, `format`, `reason` |
| `collection_file_written` | INFO | `collection_serializer` | `path`, `format`, `request_count`, `variable_count`, `preset_count` |
| `collection_export_payload_built` | INFO | `collection_export` | `collection_name`, `request_count`, `websocket_count`, `variable_count`, `preset_count` |
| `collection_import_yaml_parse_failed` | WARNING | `collection_import` | `path`, `reason` |

---

## Configuration

The serializer and format v2 subsystems (`pypost.core.collection_serializer`, `CollectionVariable` models, and associated import/export flows) are pure library components. They require no custom environment variables or configuration files, operating directly on in-memory domain models and explicitly passed file paths while adhering to standard runtime environment settings (such as UTF-8 file encoding and default Python `logging` configuration).

---

## Troubleshooting

| Symptom | Cause | Resolution |
| --- | --- | --- |
| `CollectionSerializationError: Unsupported variable type: <type>` | Variable schema declares a type outside `COLLECTION_VARIABLE_TYPES` | Use one of the supported types: `string`, `integer`, `number`, `boolean`, `array`, `object`. |
| `CollectionSerializationError: Default value ... is not valid for variable type ...` | The provided default value is incompatible with the declared type (e.g. `type="integer", default="abc"`, `type="boolean", default=1`) | Correct the default value to match the type, or set `default: null` if no default is provided. |
| `CollectionSerializationError: Variable name cannot be empty` | Variable schema is missing the `name` attribute or has an empty whitespace name | Provide a valid non-empty string identifier for every variable. |
| `CollectionSerializationError: YAML content root must be a mapping/object` | YAML document root is a list, scalar, or empty rather than a mapping object | Ensure the collection YAML file has a top-level dictionary root. |
| `CollectionSerializationError: JSON content root must be an object` | JSON document root is an array or primitive scalar | Ensure single collection JSON files have an object root `{ ... }`. Multi-collection lists should be imported via `collection_import.load_collection_import_candidates`. |
| `CollectionImportFileError: File is not valid JSON or YAML` | File syntax is corrupted or contains invalid characters | Validate syntax using a YAML/JSON linter and check `collection_import_yaml_parse_failed` logs. |

---

## Related Docs

- [Collection Export](collection_export.md) — Single and bulk collection export workflows.
- [Collection Import](collection_import.md) — Multi-format collection import, conflict resolution, and async parsing.
- [Collection Storage](collection_storage.md) — On-disk collection persistence under the user data directory.
- [Shared JSON Export Root Policy](json_export_root.md) — Root object/array export conventions.
- [Logging](logging.md) — Application logging catalog and event conventions.
