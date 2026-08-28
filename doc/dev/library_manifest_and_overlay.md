# Library Manifest Schema Validator and Local Secrets Overlay Manager

## Overview

As part of parent epic [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219) (*Git-based Collection Libraries & Self-Contained Collection Format*), **PYPOST-1221** establishes the core specification, parsing infrastructure, local secret storage, and variable resolution engine for version-controlled collection libraries.

Collection libraries allow teams to package, distribute, and version-control multiple PyPost collection files (`.yaml` / `.yml` / `.json`) within a single Git repository or directory tree.

### Core Capabilities

1. **Library Manifest Specification (`pypost-library.yaml` / `pypost-library.json`)**:
   - Central descriptor defining library identity (`id`, `name`, `version`, `description`), collection file registry (`collections`), library-wide shared variable schemas (`variables`), and preset environment profiles (`presets`).
2. **Local Overlay Manager (`~/.pypost/libraries_data/<library_id>/overlay.json`)**:
   - Secure local storage for sensitive secrets (API keys, passwords, bearer tokens) and developer-specific variable overrides.
   - Strictly isolated from the Git repository to prevent accidental credential leakage into version control.
   - Enforces POSIX file permissions (`0o600` for files, `0o700` for directories) with atomic writes.
3. **3-Tier Layered Variable Precedence Engine**:
   - Computes effective runtime variables across base defaults, active preset profiles, and local overlay overrides/secrets.
   - Provides granular provenance tracking (`default`, `profile`, `local_override`, `local_secret`) and type validation against declared variable schemas.
4. **Structured Error Diagnostics**:
   - Standardized `ManifestDiagnosticError` hierarchy with structured error codes, file paths, line contexts, and actionable remediation messages.

---

## Architecture & Data Models

```text
pypost/
├── models/
│   ├── collection_variable.py       # [EXISTING] CollectionVariable schema and type validation
│   ├── library_manifest.py          # [NEW] LibraryManifest, LocalLibraryOverlay, Resolution models
│   ├── models.py                    # [EXISTING] Core Collection & RequestData domain models
│   └── __init__.py                  # [UPDATED] Re-exports library manifest models
└── core/
    ├── library_manifest.py          # [NEW] Manifest YAML/JSON parser, validator, file discovery
    ├── local_overlay_manager.py     # [NEW] Local storage manager for ~/.pypost/libraries_data/
    └── variable_resolver.py         # [NEW] 3-tier variable resolution engine with provenance
```

### Component Architecture

```mermaid
graph TD
    subgraph Filesystem [Filesystem Storage]
        subgraph WorkspaceRepo [Git Working Tree / Workspace]
            MF[pypost-library.yaml / .json]
            C1[collections/billing.yaml]
            C2[collections/users.json]
        end
        
        subgraph UserHomeConfig [User Local Storage: ~/.pypost/libraries_data/]
            OV[library-id/overlay.json<br/>- active_profile<br/>- secrets<br/>- overrides]
        end
    end

    subgraph DomainModels [pypost.models.library_manifest]
        LM[LibraryManifest<br/>- id: str<br/>- name: str<br/>- version: str<br/>- collections: list[str]<br/>- variables: list[CollectionVariable]<br/>- presets: dict[str, dict]]
        LLO[LocalLibraryOverlay<br/>- library_id: str<br/>- active_profile: str | None<br/>- secrets: dict[str, Any]<br/>- overrides: dict[str, Any]]
        VRC[VariableResolutionContext<br/>- manifest<br/>- overlay<br/>- active_profile<br/>- collection<br/>- strict_required]
        VRR[VariableResolutionResult<br/>- variables: dict[str, Any]<br/>- provenance: dict[str, VariableProvenance]<br/>- missing_required: list[str]]
        RV[ResolvedVariable<br/>- name: str<br/>- value: Any<br/>- origin: VariableProvenance<br/>- is_secret: bool]
    end

    subgraph CoreComponents [pypost.core]
        LMP[library_manifest.py<br/>Manifest Parser & Path Validator]
        LOM[local_overlay_manager.py<br/>LocalOverlayManager<br/>Atomic & Secure 0o600 Storage]
        LVR[variable_resolver.py<br/>LibraryVariableResolver<br/>3-Tier Layered Precedence Engine]
    end

    MF --> LMP
    LMP --> LM
    LMP -. verifies relative paths .-> C1
    LMP -. verifies relative paths .-> C2

    OV --> LOM
    LOM --> LLO

    LM --> LVR
    LLO --> LVR
    VRC --> LVR
    LVR --> VRR
    LVR --> RV
```

### Data Models (`pypost.models.library_manifest`)

#### `LibraryManifest`
The root descriptor for a collection library.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `id` | `str` | `uuid4()` | Unique immutable slug/identifier for the library. |
| `name` | `str` | *required* | Human-readable library display name. Non-empty string. |
| `version` | `str` | `"1.0.0"` | Semantic version string of the library. |
| `description` | `str` | `""` | Markdown documentation or summary of the library. |
| `collections` | `list[str]` | *required* | List of relative paths to collection files within the library repo. |
| `variables` | `list[CollectionVariable]` | `[]` | Shared variable definitions across the library. |
| `presets` | `dict[str, dict[str, Any]]` | `{}` | Preset environment profile configurations (`local`, `staging`, etc.). |

#### `LibraryCollectionEntry`
Value object representing a referenced collection file inside a library.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `path` | `str` | *required* | Relative POSIX path to the collection file from the manifest root. |
| `name` | `str \| None` | `None` | Optional override display name for the collection entry. |
| `description` | `str` | `""` | Optional description of the collection entry. |

#### `LibraryEnvironmentEntry`
Value object representing an environment preset profile.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `name` | `str` | *required* | Environment preset identifier (e.g. `staging`, `production`). |
| `description` | `str` | `""` | Description of the target environment. |
| `variables` | `dict[str, Any]` | `{}` | Mapping of variable names to override values. |

#### `LocalLibraryOverlay`
Represents developer-local state stored outside version control.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `library_id` | `str` | *required* | ID of the library matching `LibraryManifest.id`. |
| `active_profile` | `str \| None` | `None` | Selected preset profile name (e.g. `local`, `staging`). |
| `secrets` | `dict[str, Any]` | `{}` | Secret credentials (API keys, tokens, passwords). |
| `overrides` | `dict[str, Any]` | `{}` | Non-secret local variable overrides. |
| `updated_at` | `str` | UTC ISO 8601 | Timestamp of the last overlay modification. |

#### `VariableProvenance` (Enum)
Indicates the source layer from which an effective variable value was resolved:
- `DEFAULT` (`"default"`): Resolved from manifest or collection variable default value.
- `PROFILE` (`"profile"`): Resolved from the active preset profile.
- `LOCAL_OVERRIDE` (`"local_override"`): Resolved from local non-secret overrides.
- `LOCAL_SECRET` (`"local_secret"`): Resolved from local secret credentials.

#### `ResolvedVariable`
Represents an individual resolved variable with origin tracking and secret classification:

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `name` | `str` | *required* | Variable identifier. |
| `value` | `Any` | *required* | Effective resolved value. |
| `origin` | `VariableProvenance` | `DEFAULT` | Layer source provenance. |
| `is_secret` | `bool` | `False` | True if marked secret in schema or provided via overlay secrets. |

#### `VariableResolutionContext`
Input parameter bundle passed to `LibraryVariableResolver.resolve_context()`.

#### `VariableResolutionResult`
Result object produced by `LibraryVariableResolver.resolve()`:
- `variables: dict[str, Any]`: Flat dictionary of effective variable values.
- `provenance: dict[str, VariableProvenance]`: Mapping of variable name to origin layer.
- `missing_required: list[str]`: List of required variable names missing values.
- `errors: list[str]`: Validation or type mismatch error messages.
- `is_valid: bool`: Convenience property returning `True` when there are no missing required variables and no validation errors.

---

## Manifest Specification & Example Formats

### Canonical `pypost-library.yaml`

```yaml
id: lib-payments-core
name: Payments Core Library
version: 1.2.0
description: Core API collections for payment processing, billing, and fraud checks.
collections:
  - collections/billing.yaml
  - collections/customers.yaml
  - collections/webhooks.json
variables:
  - name: base_url
    type: string
    default: "https://api.payments.example.com"
    description: "Payments API Gateway URL"
    required: true
    secret: false
  - name: api_key
    type: string
    default: null
    description: "API Key for service authentication"
    required: true
    secret: true
  - name: timeout_seconds
    type: integer
    default: 30
    description: "Request timeout in seconds"
    required: false
    secret: false
presets:
  local:
    base_url: "http://localhost:8080"
    timeout_seconds: 5
  staging:
    base_url: "https://staging.payments.example.com"
    timeout_seconds: 15
  production:
    base_url: "https://api.payments.example.com"
    timeout_seconds: 30
```

### Canonical Local Overlay `~/.pypost/libraries_data/lib-payments-core/overlay.json`

```json
{
  "library_id": "lib-payments-core",
  "active_profile": "local",
  "secrets": {
    "api_key": "sk_test_51Mz00000000000000000000000"
  },
  "overrides": {
    "base_url": "http://127.0.0.1:9090",
    "timeout_seconds": 10
  },
  "updated_at": "2026-08-28T00:00:00Z"
}
```

---

## 3-Tier Variable Precedence Hierarchy

The variable resolution engine evaluates effective variable values according to a strict 3-tier precedence hierarchy (lowest to highest priority):

```
┌─────────────────────────────────────────────────────────────┐
│ Tier 3 (Highest Priority): Local Overlay Storage            │
│   1. Local Secrets (overlay.json -> secrets)                │
│   2. Local Variable Overrides (overlay.json -> overrides)   │
├─────────────────────────────────────────────────────────────┤
│ Tier 2 (Middle Priority): Active Preset Profile             │
│   Preset Profile Values (manifest.presets[active_profile]   │
│   and collection.presets[active_profile])                   │
├─────────────────────────────────────────────────────────────┤
│ Tier 1 (Lowest Base Priority): Manifest & Collection        │
│   1. Manifest Variable Defaults (manifest.variables)        │
│   2. Collection Variable Defaults (collection.variables)    │
└─────────────────────────────────────────────────────────────┘
```

### Resolution Flow

1. **Base Defaults (Tier 1)**: All default values defined in `collection.variables` and `manifest.variables` are loaded.
2. **Active Profile Overrides (Tier 2)**: If an active profile is specified (e.g. `staging`), values from `manifest.presets[profile]` and `collection.presets[profile]` override base defaults.
3. **Local Overrides & Secrets (Tier 3)**: Values from `overlay.overrides` and `overlay.secrets` override all lower layers.
4. **Collection Namespace Resolution (PYPOST-1227)**:
   - When evaluating variables for a specific collection, scoped entries (`<collection_name>.<variable_name>`) defined in preset profiles, overlay overrides, and overlay secrets take precedence over generic shared variables.
   - Both stripped (`<variable_name>`) and fully qualified (`<collection_name>.<variable_name>`) keys are populated in the resolution output.
   - Matching supports exact collection names, lowercase, and normalized snake_case identifiers.
5. **Type Validation**: Each resolved value is verified against its declared schema type (`string`, `integer`, `number`, `boolean`, `array`, `object`).
6. **Required Check**: Any variable marked `required=True` that resolves to `None` or `""` is flagged in `missing_required`.

---

## Local Overlay Storage Model

### Location and Directory Layout

- **Base Directory**: Default path is `~/.pypost/libraries_data/` (configurable via `base_dir` parameter for testing).
- **Per-Library Storage**: Each library maintains an isolated subdirectory keyed by its `library_id`:
  ```text
  ~/.pypost/libraries_data/
  └── <library_id>/
      └── overlay.json
  ```

### Security & Git Isolation

- **Git Isolation**: The overlay storage directory resides strictly in the user's home directory, outside of any Git repository or workspace folder. Branch switching, commits, pushes, and Git resets never affect or expose local secrets.
- **POSIX Permission Hardening**:
  - Overlay directory: Created with mode `0o700` (`rwx------`).
  - Overlay JSON file: Written with mode `0o600` (`rw-------`).
  - Ensures other non-root OS user accounts on shared workstations cannot read sensitive tokens or credentials.
- **Atomic File Writes**:
  - Overlays are written to a unique temporary file (`overlay.json.tmp.<uuid>`) with `0o600` permissions.
  - Safely swapped into place via `os.replace` to prevent file corruption during sudden terminations.
- **At-Rest Encryption for Secrets (PYPOST-1225)**:
  - `LocalOverlayManager` accepts an optional `secrets_codec: Optional[EnvironmentSecretsCodec] = None`.
  - When configured, sensitive fields in `overlay.secrets` are saved as standard encrypted envelopes on disk.
  - Transparently decrypts encrypted envelopes on load (`get_overlay`), while preserving full backward compatibility for legacy plaintext overlay files.
  - Non-secret fields (`overrides`, `active_profile`, `library_id`) remain unencrypted JSON.

---

## Core API & Usage

### 1. `pypost.core.library_manifest`

Provides reading, writing, parsing, discovery, and path validation for library manifests.

```python
from pathlib import Path
from pypost.core.library_manifest import (
    find_and_read_manifest,
    read_manifest_file,
    write_manifest_file,
    validate_manifest_collections,
    deserialize_manifest_from_yaml,
    deserialize_manifest_from_json,
    serialize_manifest_to_yaml,
)

# Auto-discover pypost-library.yaml/.json in a directory
manifest, manifest_path = find_and_read_manifest(Path("/path/to/repo"))

# Validate that all referenced collection files exist on disk
missing_files = validate_manifest_collections(manifest, manifest_dir=manifest_path.parent)
if missing_files:
    print(f"Warning: Missing collection files: {missing_files}")

# Read directly from a specific manifest file
manifest = read_manifest_file("/path/to/repo/pypost-library.yaml")

# Serialize and save changes
write_manifest_file(manifest, "/path/to/repo/pypost-library.yaml", format="yaml")
```

### 2. `pypost.core.local_overlay_manager`

Provides CRUD operations and persistent storage for user-local secrets and overrides.

```python
from pypost.core.local_overlay_manager import LocalOverlayManager

# Initialize manager (uses ~/.pypost/libraries_data by default)
overlay_mgr = LocalOverlayManager()

# Load overlay for a library
overlay = overlay_mgr.get_overlay("lib-payments-core")

# Update active profile
overlay_mgr.set_active_profile("lib-payments-core", "staging")

# Store sensitive API key in local overlay
overlay_mgr.set_secret("lib-payments-core", "api_key", "sk_live_secret123")

# Set local non-secret variable override
overlay_mgr.set_override("lib-payments-core", "base_url", "http://localhost:8080")

# Retrieve single override or secret
secret_val = overlay_mgr.get_variable_override("lib-payments-core", "api_key")

# Remove secret or override
overlay_mgr.remove_secret("lib-payments-core", "api_key")
overlay_mgr.remove_override("lib-payments-core", "base_url")

# List all library IDs with local overlays
configured_libraries = overlay_mgr.list_library_overlays()

# Delete local overlay directory
overlay_mgr.delete_overlay("lib-payments-core")
```

### 3. `pypost.core.variable_resolver`

Evaluates effective runtime variables across manifest, profile, and overlay layers.

```python
from pypost.core.variable_resolver import (
    LibraryVariableResolver,
    resolve_effective_variables,
    resolve_detailed_variables,
)

# Full resolution with diagnostics
resolver = LibraryVariableResolver()
result = resolver.resolve(
    manifest=manifest,
    overlay=overlay,
    active_profile="staging",
    collection=collection,
    strict_required=False,
)

print(result.variables)        # {'base_url': 'https://staging.example.com', 'api_key': '...'}
print(result.provenance)       # {'base_url': VariableProvenance.PROFILE, 'api_key': VariableProvenance.LOCAL_SECRET}
print(result.missing_required) # [] if all required variables have values
print(result.is_valid)         # True

# Convenience function returning flat dict
effective_vars = resolve_effective_variables(
    manifest=manifest,
    overlay=overlay,
    active_profile="staging",
    collection=collection,
)

# Detailed resolution with ResolvedVariable objects
detailed_vars = resolve_detailed_variables(
    manifest=manifest,
    overlay=overlay,
    active_profile="staging",
    collection=collection,
)
for name, var in detailed_vars.items():
    print(f"{name} = {var.value} (origin={var.origin}, is_secret={var.is_secret})")
```

---

## Configuration

The library manifest, local overlay manager, and variable resolver components are lightweight, standard library-driven modules.

### Runtime Environment Settings

| Setting / Path | Default Location | Description |
| --- | --- | --- |
| `base_dir` in `LocalOverlayManager` | `~/.pypost/libraries_data/` | Root filesystem directory where per-library overlays are stored. Can be overridden in tests or custom setups. |
| Manifest File Candidates | `pypost-library.yaml`, `pypost-library.yml`, `pypost-library.json` | Candidate filenames scanned during automatic discovery. |
| Encoding | `UTF-8` | All manifest and overlay file read/write operations strictly use `encoding="utf-8"`. |
| Directory Permissions | `0o700` (`rwx------`) | Applied on creation to `~/.pypost/libraries_data/<library_id>/`. |
| File Permissions | `0o600` (`rw-------`) | Applied on creation to `~/.pypost/libraries_data/<library_id>/overlay.json`. |

---

## Observability & Logging

All core operations emit structured `key=value` log events:

| Event | Level | Module | Fields |
| --- | --- | --- | --- |
| `manifest_file_read` | INFO | `library_manifest` | `path`, `id`, `name`, `collections`, `variables` |
| `manifest_file_written` | INFO | `library_manifest` | `path`, `format`, `id`, `name` |
| `manifest_discovered` | DEBUG | `library_manifest` | `path` |
| `manifest_file_read_failed` | WARNING | `library_manifest` | `path`, `reason` |
| `manifest_file_write_failed` | WARNING | `library_manifest` | `path`, `format`, `reason` |
| `manifest_collections_validation_failed` | WARNING | `library_manifest` | `manifest_id`, `missing_count`, `missing_paths` |
| `overlay_loaded` | INFO | `local_overlay_manager` | `library_id`, `path`, `secrets_count`, `overrides_count`, `active_profile` |
| `overlay_saved` | INFO | `local_overlay_manager` | `library_id`, `path`, `secrets_count`, `overrides_count` |
| `overlay_deleted` | INFO | `local_overlay_manager` | `library_id`, `path` |
| `overlay_directory_permissions_applied` | DEBUG | `local_overlay_manager` | `path`, `mode` |
| `overlay_file_permissions_applied` | DEBUG | `local_overlay_manager` | `path`, `mode` |
| `variable_resolution_completed` | DEBUG | `variable_resolver` | `total_resolved`, `default_count`, `profile_count`, `override_count`, `secret_count`, `missing_required_count`, `error_count` |
| `variable_resolution_missing_required` | WARNING | `variable_resolver` | `missing_count`, `missing_names` |
| `variable_resolution_validation_failed` | WARNING | `variable_resolver` | `error_count`, `errors` |

---

## Troubleshooting & Error Diagnostics

### Field-Level Validation Diagnostics (PYPOST-1226)

`ManifestDiagnosticError` provides structured properties for UI Form Editors and programmatic inspection:
- `field: Optional[str]`: Dot-notation path to the invalid field (e.g. `"variables[0].name"` or `"name"`).
- `json_path: Optional[str]`: RFC 9535 JSONPath to the error location (e.g. `"$.variables[0].name"` or `"$.name"`).
- `line: Optional[int]`: 1-indexed source file line number for syntax or parse errors.
- `column: Optional[int]`: 1-indexed source file column number for syntax or parse errors.
- `field_errors: List[Dict[str, Any]]`: Complete list of field-level errors containing `field`, `json_path`, `message`, and error `type`.
- `to_dict() -> Dict[str, Any]`: Serializes the diagnostic error into a JSON-compatible dictionary for API / UI bridge serialization.

### Standard Diagnostic Error Codes

`ManifestDiagnosticError` provides structured error codes:

| Code | Trigger | Action / Remediation |
| --- | --- | --- |
| `MANIFEST_NOT_FOUND` | No `pypost-library.yaml`/`.json` found in target directory. | Ensure the root directory of the library contains a valid manifest descriptor. |
| `MANIFEST_SYNTAX_ERROR` | Malformed YAML or JSON syntax. | Fix formatting/syntax errors using a YAML or JSON validator. |
| `MANIFEST_INVALID_ROOT` | Document root is a list or scalar instead of a dictionary/mapping. | Ensure the manifest document begins with key-value pairs (mapping root). |
| `MANIFEST_VALIDATION_ERROR` | Missing required fields (`id`, `name`, `collections`) or invalid schema values. | Check that `id`, `name`, and at least one collection file path are provided in `collections`. |
| `MANIFEST_READ_ERROR` | Permissions or OS I/O error reading manifest file. | Verify file path existence and read permissions. |
| `MANIFEST_WRITE_ERROR` | Permissions or disk space error writing manifest file. | Verify write permissions for the destination directory. |
| `UNSUPPORTED_FORMAT` | Unsupported format specified for serialization. | Use `"yaml"`, `"json"`, or `"auto"`. |
| `MISSING_REQUIRED_SECRET` | Required variable/secret has no value assigned during strict resolution. | Provide the secret in `LocalOverlayManager.set_secret()` or select a profile containing the value. |
| `TYPE_MISMATCH` | Effective variable value does not match declared type. | Correct the variable value to conform to the schema (`string`, `integer`, `number`, `boolean`, `array`, `object`). |

### Common Issues and Solutions

1. **Collection file listed in manifest cannot be found on disk**:
   - **Symptom**: `validate_manifest_collections` returns missing paths.
   - **Cause**: The path in `collections` is relative to the manifest directory and was moved, renamed, or misspelled.
   - **Fix**: Check relative path spelling (e.g. `collections/billing.yaml`) and ensure files are committed in the repository.

2. **Required API key fails execution in strict mode**:
   - **Symptom**: `ManifestDiagnosticError: [MISSING_REQUIRED_SECRET] Missing required variables or secrets: api_key`.
   - **Cause**: The variable has `required: true` and `secret: true`, but no secret was supplied in the local overlay.
   - **Fix**: Use `LocalOverlayManager.set_secret(library_id, "api_key", "<value>")` to store the secret locally.

3. **Overlay permissions cannot be applied on Windows**:
   - **Behavior**: `os.chmod` calls for POSIX modes (`0o600`/`0o700`) are safely guarded by `if os.name == "posix":`.
   - **Outcome**: On Windows, files are written atomically using native permissions without raising exceptions.

---

## Related Docs

- [Collection Format v2](collection_format_v2.md) — Self-contained YAML/JSON collection format specification.
- [Collection Loading](collection_loading.md) — Collection disk discovery and loading.
- [Collection Storage](collection_storage.md) — Collection persistence architecture.
- [Environment Encryption at Rest](environment_encryption_at_rest.md) — Encryption codecs for stored environments.
- [Sensitive Data Masking Policy](sensitive_data_masking_policy.md) — Masking rules for secrets and credentials.
