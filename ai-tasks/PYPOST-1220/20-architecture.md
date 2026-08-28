# PYPOST-1220: [Libraries] Core schema and serializers for self-contained collection format with variable metadata

## Research

### 1. Existing Collection & Persistence Ecosystem in PyPost

A thorough analysis of the PyPost codebase reveals the following existing components and patterns:

- **Core Collection Domain Models** (`pypost/models/models.py`):
  - `Collection`: Currently defines `id` (UUID string), `name` (string), `requests` (`List[RequestData]`), `websockets` (`List[WebSocketConnection]`), and `mcp_clients` (`List[McpClientConnection]`).
  - `RequestData`: Encapsulates HTTP request attributes (`id`, `name`, `method`, `url`, `headers`, `params`, `body`, `body_type`, `yaml_as_json`, `post_script`, `expose_as_mcp`, `mcp_description`, `mcp_params`, `retry_policy`).
  - `McpToolParam`: Defines agent parameter schemas (`type`, `description`, `required`, `default`) with validation of default values against a whitelist (`string`, `integer`, `integer_or_string`, `number`, `boolean`, `array`, `object`).
  - Currently, `Collection` lacks collection-level variable declarations, description, versioning metadata, and preset profile bindings.

- **Environment Persistence & Variable Resolution** (`pypost/models/models.py`, `pypost/core/environment_ops.py`, `pypost/core/environment_variable_resolver.py`):
  - Environments (`Environment`) store flat string-to-string mappings (`variables: Dict[str, str]`) with `hidden_keys: Set[str]` for masking in the UI.
  - Environment storage is completely disconnected from collection files (`environments.json`).
  - Variable substitution in requests (`{{var_name}}`) resolves tokens against active environment dictionaries and function expressions.

- **Collection Export Logic** (`pypost/core/collection_export.py`):
  - Exports collections via `build_export_payload` (`collection.model_dump(mode="json")`) and `write_export_file` (`write_json_export_file`).
  - Filename suggestion (`suggested_export_filename`) generates sanitized `<name>.json` names.
  - Strictly writes JSON format.

- **Collection Import Logic** (`pypost/core/collection_import.py`, `pypost/core/collection_messages.py`):
  - `_read_records` parses JSON text into dict records (supporting single collection dict or array of collection dicts).
  - `_shape_error` validates basic fields (`name`, `requests`, `websockets`, `mcp_clients`).
  - `load_collection_import_candidates` instantiates `Collection(**record)`.
  - `_materialize` reconstructs collection instances while preserving or regenerating IDs to prevent conflicts.
  - Currently only parses JSON; does not handle YAML or parse variable schemas/presets.

- **YAML Capabilities in PyPost** (`pypost/core/yaml_json_converter.py`, `pyproject.toml`):
  - `PyYAML` is already bundled as a direct dependency.
  - `yaml.safe_load` and `yaml.safe_dump` are used for request body translation and configuration.

### 2. Gap Analysis

| Capability | Current State | Required State (PYPOST-1220) |
| --- | --- | --- |
| **Variable Metadata** | None in collection; untyped `Dict[str, str]` in separate environment files | Formal schema in collection (`name`, `type`, `default`, `description`, `required`, `secret`) |
| **Variable Types** | Implicit string-only | Explicit: `string`, `integer`, `number`, `boolean`, `array`, `object` |
| **Preset Profiles** | Unattached standalone environments | Named profiles (`local`, `staging`, `production`) embedded in the collection |
| **File Formats** | Monolithic JSON only | Human-friendly YAML (`.yaml`/`.yml`) and standard JSON (`.json`) |
| **Round-Trip Fidelity** | JSON dump only | Lossless round-trip serialization and deserialization across YAML and JSON |
| **Backward Compatibility** | Existing JSON import | Transparent ingestion of legacy JSON collections + optional legacy JSON export |

---

## Implementation Plan

### High-Level Execution Phases

1. **Phase 1 (Step 3): Automated Failing Repro Tests**
   - Author a dedicated test suite `tests/test_collection_format_v2_repro.py` testing the complete target contract before adding production code.
   - Assert validation failures on bad types / defaults, YAML/JSON round-trip equality, preset definitions, and legacy backward-compatible parsing.

2. **Phase 2 (Step 4): Model Definition & Validation Logic**
   - Create `pypost/models/collection_variable.py` defining `CollectionVariable` with Pydantic validators.
   - Enhance `pypost/models/models.py` `Collection` model to include `description`, `version`, `variables`, and `presets`.
   - Update `pypost/models/__init__.py` to export the new models cleanly.

3. **Phase 3 (Step 4): Serializers & Deserializers (`pypost/core/collection_serializer.py`)**
   - Implement pure functions for YAML and JSON serialization and deserialization.
   - Implement safe YAML dumping with deterministic key ordering and clean multi-line string formatting.
   - Implement schema validation during deserialization with informative error diagnostics (`CollectionSerializationError`).

4. **Phase 4 (Step 4): Export/Import Subsystem Integration**
   - Update `pypost/core/collection_export.py` to support format-aware serialization (`.yaml`, `.json`, legacy format).
   - Update `pypost/core/collection_import.py` to support reading `.yaml`/`.yml` alongside `.json`, and update `_materialize` to preserve `variables`, `presets`, `description`, `version`, and `mcp_clients`.
   - Extend collection messages in `pypost/core/collection_messages.py` for new error conditions.

5. **Phase 5 (Steps 5–8): Cleanup, Observability, Tech Debt, Dev Docs**
   - Ensure clean typing (Mypy clean), docstrings, structured logging, and developer documentation in `doc/dev/collection_format_v2.md`.

---

### Mandatory — Failing Repro (Step 3 Design)

- **Test File Path**: `tests/test_collection_format_v2_repro.py`
- **What it Asserts**:
  1. `CollectionVariable` creation with valid types (`string`, `integer`, `number`, `boolean`, `array`, `object`) and valid defaults.
  2. Rejecting unsupported variable types (e.g. `type="invalid_type"`) with a validation error.
  3. Rejecting default values that do not match the declared type (e.g. `type="integer", default="not_an_int"`, `type="boolean", default=123`, `type="array", default="string"`, `type="object", default=[1, 2]`).
  4. `Collection` accepts `description`, `version`, `variables: list[CollectionVariable]`, and `presets: dict[str, dict[str, Any]]`.
  5. Round-trip YAML serialization and deserialization (`serialize_collection_to_yaml` $\rightarrow$ `deserialize_collection_from_yaml`) preserves every field with semantic identity.
  6. Round-trip JSON serialization and deserialization (`serialize_collection_to_json` $\rightarrow$ `deserialize_collection_from_json`) preserves every field with semantic identity.
  7. Backward compatibility: parsing legacy JSON payloads without `variables` or `presets` succeeds cleanly, initializing `variables=[]` and `presets={}`.
  8. Import planning / materialization in `pypost.core.collection_import` retains variables and presets when importing collections.
- **How it Fails Before Implementation**:
  - `CollectionVariable` cannot be imported (`ModuleNotFoundError` / `ImportError`).
  - `Collection` model does not accept `variables`, `presets`, `description`, or `version` in Pydantic schema validation.
  - `pypost.core.collection_serializer` functions (`serialize_collection_to_yaml`, `deserialize_collection_from_yaml`, etc.) do not exist.
- **Sequencing**:
  - Step 2: Architecture approved.
  - Step 3: Write red test `tests/test_collection_format_v2_repro.py` and verify failure.
  - Step 4: Implement models, serializers, import/export updates until all tests pass green.

---

## Architecture

### 1. System Module Breakdown & Responsibilities

```
pypost/
├── models/
│   ├── collection_variable.py       # [NEW] CollectionVariable, supported types & validation
│   ├── models.py                    # [UPDATED] Collection model with variables & presets
│   └── __init__.py                  # [UPDATED] Re-exports CollectionVariable
└── core/
    ├── collection_serializer.py     # [NEW] Pure YAML & JSON serialization/deserialization logic
    ├── collection_export.py         # [UPDATED] Format-aware export payloads & file writing
    ├── collection_import.py         # [UPDATED] YAML/JSON parsing & candidate loading
    └── collection_messages.py       # [UPDATED] Error messages for schema & format errors
```

- **`pypost.models.collection_variable`**:
  - `COLLECTION_VARIABLE_TYPES`: frozenset of allowed type names (`"string"`, `"integer"`, `"number"`, `"boolean"`, `"array"`, `"object"`).
  - `CollectionVariable`: Pydantic model for variable metadata (`name`, `type`, `default`, `description`, `required`, `secret`).
  - `validate_variable_value(value, var_type)`: Helper function to validate any value (default or preset override) against a declared variable type.

- **`pypost.models.models.Collection`**:
  - Enhanced with:
    - `description: str = ""`
    - `version: str = "1.0.0"`
    - `variables: List[CollectionVariable] = Field(default_factory=list)`
    - `presets: Dict[str, Dict[str, Any]] = Field(default_factory=dict)`

- **`pypost.core.collection_serializer`**:
  - `serialize_collection_to_dict(collection: Collection) -> dict`: Converts model to clean Python dict.
  - `serialize_collection_to_yaml(collection: Collection) -> str`: Produces clean, readable YAML string.
  - `serialize_collection_to_json(collection: Collection, indent: int = 2) -> str`: Produces indented UTF-8 JSON string.
  - `serialize_collection_to_legacy_dict(collection: Collection) -> dict`: Produces legacy JSON-compatible dict.
  - `deserialize_collection_from_dict(data: dict) -> Collection`: Validates dictionary into `Collection`.
  - `deserialize_collection_from_yaml(yaml_text: str) -> Collection`: Parses and validates YAML string into `Collection`.
  - `deserialize_collection_from_json(json_text: str) -> Collection`: Parses and validates JSON string into `Collection`.
  - `write_collection_file(path: Path, collection: Collection, format: str = "yaml") -> None`: Writes collection to disk.
  - `read_collection_file(path: Path) -> Collection`: Auto-detects format from extension/content and parses into `Collection`.

- **`pypost.core.collection_export` & `pypost.core.collection_import`**:
  - Extended to support both `.yaml`/`.yml` and `.json` files.
  - `_materialize` updated to pass `description`, `version`, `variables`, `presets`, and `mcp_clients` during conflict resolution.

---

### 2. Component Diagram (Mermaid)

```mermaid
graph TD
    subgraph Domain Models [pypost.models]
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

    subgraph Core Serialization [pypost.core.collection_serializer]
        SER_YAML[serialize_collection_to_yaml]
        SER_JSON[serialize_collection_to_json]
        DES_YAML[deserialize_collection_from_yaml]
        DES_JSON[deserialize_collection_from_json]
        VAL[Schema & Type Validator]
        
        SER_YAML --> COL
        SER_JSON --> COL
        DES_YAML --> VAL --> COL
        DES_JSON --> VAL --> COL
    end

    subgraph Storage & Workflows [pypost.core]
        EXP[collection_export.py<br/>Export YAML/JSON]
        IMP[collection_import.py<br/>Import YAML/JSON/Legacy]
        
        EXP --> SER_YAML
        EXP --> SER_JSON
        IMP --> DES_YAML
        IMP --> DES_JSON
    end
```

---

### 3. Data Models Specification

#### `CollectionVariable`

```python
class CollectionVariable(BaseModel):
    """Metadata schema for one variable defined in a self-contained collection."""

    name: str
    type: str = "string"  # string, integer, number, boolean, array, object
    default: Optional[Any] = None
    description: str = ""
    required: bool = False
    secret: bool = False

    def model_post_init(self, __context: Any) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Variable name cannot be empty")
        if self.type not in COLLECTION_VARIABLE_TYPES:
            raise ValueError(f"Unsupported variable type: {self.type}")
        self._validate_default_type()

    def _validate_default_type(self) -> None:
        if self.default is None:
            return
        if not validate_variable_value(self.default, self.type):
            raise ValueError(
                f"Default value {self.default!r} is not valid for variable type {self.type!r}"
            )
```

#### Supported Variable Types & Validation Rules

| Type Name | Python Allowed Types | Disallowed |
| --- | --- | --- |
| `string` | `str` | Numbers, booleans, lists, dicts |
| `integer` | `int` (strictly `isinstance(v, int) and not isinstance(v, bool)`) | `bool`, floats, strings |
| `number` | `int`, `float` (`not isinstance(v, bool)`) | `bool`, non-numeric strings |
| `boolean` | `bool` | `int` (0/1), strings ("true"/"false") |
| `array` | `list` | non-list types |
| `object` | `dict` | non-dict types |

#### `Collection` (Updated)

```python
class Collection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Collection"
    description: str = ""
    version: str = "1.0.0"
    variables: List[CollectionVariable] = Field(default_factory=list)
    presets: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    requests: List[RequestData] = Field(default_factory=list)
    websockets: List[WebSocketConnection] = Field(default_factory=list)
    mcp_clients: List[McpClientConnection] = Field(default_factory=list)
```

---

### 4. Canonical File Format Representation (YAML & JSON)

#### Example YAML File (`Billing_API.yaml`)

```yaml
id: col-billing-01
name: Billing API
description: Core payment and invoice management collection
version: 1.0.0
variables:
  - name: base_url
    type: string
    default: "https://api.example.com"
    description: "API Gateway Base URL"
    required: true
    secret: false
  - name: api_key
    type: string
    default: null
    description: "Bearer authentication secret"
    required: true
    secret: true
  - name: timeout_seconds
    type: integer
    default: 30
    description: "Client request timeout"
    required: false
    secret: false
presets:
  local:
    base_url: "http://localhost:8080"
    timeout_seconds: 5
  staging:
    base_url: "https://staging.api.example.com"
    timeout_seconds: 15
  production:
    base_url: "https://api.example.com"
    timeout_seconds: 30
requests:
  - id: req-1
    name: Create Invoice
    method: POST
    url: "{{base_url}}/v1/invoices"
    headers:
      Authorization: "Bearer {{api_key}}"
      Content-Type: "application/json"
    params: {}
    body: '{"amount": 1000, "currency": "USD"}'
    body_type: json
    yaml_as_json: false
    post_script: "assert response.status_code == 201"
    expose_as_mcp: false
    mcp_description: ""
    mcp_params: {}
    retry_policy: null
websockets: []
mcp_clients: []
```

---

### 5. Backward Compatibility Strategy

1. **Ingesting Legacy Files**:
   - Legacy files exported by older versions contain `id`, `name`, `requests`, `websockets`, `mcp_clients`, and lack `variables`, `presets`, `description`, `version`.
   - When parsed into `Collection`, missing fields take default values: `variables=[]`, `presets={}`, `description=""`, `version="1.0.0"`.
   - Deserializer handles single-object and list-of-objects JSON files seamlessly.

2. **Exporting Legacy Files**:
   - `build_export_payload(collection)` remains available and continues to dump the collection model.
   - For downstream consumers that need strict legacy JSON export, `serialize_collection_to_legacy_dict(collection)` can omit `variables`/`presets` if requested or include them transparently.

3. **Safe YAML Parsing**:
   - Uses `yaml.safe_load` / `yaml.safe_dump` to avoid any unsafe Python object execution.
   - Deterministic field ordering ensures consistent diffs in Git repositories.

---

## Q&A

- **Q: Where will `CollectionVariable` and the new serializers be located?**
  - **A:** `CollectionVariable` is placed in `pypost/models/collection_variable.py` (and re-exported from `pypost.models.models` and `pypost.models`). Serializers and deserializers are placed in `pypost/core/collection_serializer.py`.
- **Q: How does this task interact with the downstream PYPOST-1221 through PYPOST-1224 tasks?**
  - **A:** This task provides the canonical models (`Collection`, `CollectionVariable`) and YAML/JSON codecs. PYPOST-1221 uses these models to validate `pypost-library.yaml` manifests and manage local secret overlays. PYPOST-1222 uses them for Git sync persistence, and PYPOST-1223 provides the GUI Library Manager.
- **Q: How are secret variables represented in exported collection files?**
  - **A:** Secret variables have `secret: true` and `default: null` (or non-sensitive placeholder). Actual sensitive secret values are excluded from version-controlled collection files.
- **Q: How is round-trip fidelity guaranteed?**
  - **A:** All properties on requests (headers, params, body types, post_scripts, mcp_params, retry policies), websockets, mcp_clients, variables, and presets are serialized and deserialized with explicit field mapping and verified in round-trip unit tests.
