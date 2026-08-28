# PYPOST-1221: [Libraries] Library manifest schema validator and local secrets overlay manager

## Research

### 1. Library Manifest Ecosystem and Manifest Specification

As part of parent epic [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219) (*Git-based Collection Libraries & Self-Contained Collection Format*), PyPost is introducing version-controlled collection libraries that teams can share via Git repositories and standalone directories.

Following the core collection schema and serialization format introduced in [PYPOST-1220](https://pypost.atlassian.net/browse/PYPOST-1220), libraries need a formal manifest definition (`pypost-library.yaml` / `pypost-library.yml` / `pypost-library.json`) at the root of the library folder.

The manifest acts as the central descriptor for:
1. **Library Identity & Metadata**: Unique slug/identifier (`id`), human-readable display name (`name`), semantic version string (`version`), and markdown documentation (`description`).
2. **Collection Registry**: List of relative paths to collection files (`collections`) contained within the library repository (e.g., `["collections/billing.yaml", "collections/users.json"]`).
3. **Library-Level Variables**: Shared variable declarations (`variables`) defining parameter schemas (`name`, `type`, `default`, `description`, `required`, `secret`) common across all collections in the library.
4. **Preset Environment Profiles**: Named environment presets (`presets` / `environments`), such as `local`, `staging`, `production`, mapping variable names to predefined values.

### 2. Existing Configuration and Secrets Storage in PyPost

A thorough analysis of PyPost's existing persistence and configuration subsystem reveals:

- **Global Configuration Management** (`pypost/core/config_manager.py`):
  - `ConfigManager` uses `platformdirs.user_config_dir("pypost", None)` resolving to standard OS configuration directories:
    - Linux: `~/.config/pypost` or `~/.pypost`
    - macOS: `~/Library/Application Support/pypost`
    - Windows: `C:\Users\<User>\AppData\Local\pypost`
  - Provides `load_config()`, `load_config_strict()`, and `save_config()` with atomic file operations and directory initialization.
- **Secrets Codecs & Storage Encryption** (`pypost/core/settings_secrets.py`, `pypost/core/environment_secrets_codec.py`, `pypost/core/encryption_config.py`):
  - PyPost provides encryption codecs for sensitive credentials in `AppSettings` (e.g. webhook tokens).
  - Secrets are serialized in JSON envelopes and decrypted on load.
- **Local Overlay Storage Requirements** (PYPOST-1221):
  - Dedicated storage directory: `~/.pypost/libraries_data/<library-id>/overlay.json`.
  - Must remain strictly external to the library's Git repository.
  - Requires POSIX permission enforcement (`0o600` for files, `0o700` for directories) to prevent unauthorized read access by other local system users.
  - Requires configurable base directory parameter (`base_dir: Path | str | None`) for isolated test fixtures and sandboxed executions.

### 3. Variable Model and Resolution Mechanics in PyPost

- **Collection Variable Model** (`pypost/models/collection_variable.py`):
  - `CollectionVariable` model with validated types (`string`, `integer`, `number`, `boolean`, `array`, `object`).
  - Strict type checking via `validate_variable_value(value, var_type)`:
    - `string`: `isinstance(v, str)`
    - `integer`: `isinstance(v, int) and not isinstance(v, bool)`
    - `number`: `isinstance(v, (int, float)) and not isinstance(v, bool)`
    - `boolean`: `isinstance(v, bool)`
    - `array`: `isinstance(v, list)`
    - `object`: `isinstance(v, dict)`
- **Variable Name Validation** (`pypost/core/variable_name_validation.py`):
  - Validates Jinja2-compatible identifiers: non-empty, cannot start with a digit, alphanumeric + underscore characters only.
- **Variable Precedence Hierarchy** (PYPOST-1221):
  - **Tier 1 (Base Defaults)**: Library manifest variable defaults, supplemented by individual collection variable defaults.
  - **Tier 2 (Active Profile)**: Predefined values from the selected preset profile declared in the manifest (e.g., `presets.staging`).
  - **Tier 3 (Local Overlay & Secrets)**: User-specific local non-secret variable overrides and secret credential values stored in `~/.pypost/libraries_data/<library-id>/overlay.json`.

### 4. Gap Analysis

| Capability | Current State | Required State (PYPOST-1221) |
| --- | --- | --- |
| **Library Manifest Model** | None | `LibraryManifest` in `pypost/models/library_manifest.py` supporting metadata, collection paths, variables, and presets |
| **Manifest Parsing & Validation** | None | `pypost/core/library_manifest.py` parsing YAML & JSON manifests with path validation for referenced collections |
| **Local Secrets & Overlay Storage** | None | `LocalOverlayManager` in `pypost/core/local_overlay_manager.py` managing `~/.pypost/libraries_data/<library-id>/overlay.json` |
| **Variable Resolution Engine** | Legacy `EnvironmentVariableResolver` (flat string dicts) | `LibraryVariableResolver` in `pypost/core/variable_resolver.py` executing 3-tier layered resolution with provenance tracking and required secret validation |
| **Diagnostic Error Handling** | Generic exceptions | Structured `ManifestDiagnosticError` with error codes, clear remediation messages, and context details |

---

## Implementation Plan

### High-Level Execution Phases

1. **Phase 1 (Step 3): Automated Failing Repro Tests**
   - Implement `tests/test_library_manifest_and_overlay_repro.py` testing the complete target contract before adding production code.
   - Assert manifest validation failures, collection path resolution, local overlay CRUD, 3-tier variable precedence, and missing secret diagnostics.

2. **Phase 2 (Step 4): Domain Models Definition (`pypost/models/library_manifest.py`)**
   - Define `LibraryManifest`, `LibraryCollectionEntry`, `LibraryEnvironmentEntry`, `LocalLibraryOverlay`, `VariableResolutionContext`, `VariableResolutionResult`, and `VariableProvenance`.
   - Implement validation of manifest structure, version formatting, variable schemas, and preset profile definitions.
   - Re-export models in `pypost/models/__init__.py`.

3. **Phase 3 (Step 4): Manifest Serializers & Schema Validator (`pypost/core/library_manifest.py`)**
   - Implement YAML and JSON manifest deserialization (`deserialize_manifest_from_yaml`, `deserialize_manifest_from_json`, `deserialize_manifest_from_dict`).
   - Implement file loading with auto-detection (`read_manifest_file`, `find_and_read_manifest`).
   - Implement filesystem verification of referenced collection files relative to manifest directory (`validate_manifest_collections`).
   - Implement structured error diagnostics for syntax errors, missing fields, invalid collection paths, and schema violations.

4. **Phase 4 (Step 4): Local Overlay Persistence Manager (`pypost/core/local_overlay_manager.py`)**
   - Implement `LocalOverlayManager` class with configurable `base_dir` (defaulting to `~/.pypost/libraries_data`).
   - Implement overlay CRUD operations: `get_overlay()`, `save_overlay()`, `set_active_profile()`, `set_secret()`, `set_override()`, `remove_secret()`, `remove_override()`, `delete_overlay()`, `list_library_overlays()`.
   - Implement secure atomic writes with POSIX file permission enforcement (`0o600` / `0o700`).

5. **Phase 5 (Step 4): Layered Effective Variable Resolution Engine (`pypost/core/variable_resolver.py`)**
   - Implement `LibraryVariableResolver` resolving effective variables across:
     1. Manifest & collection variable defaults (Base Layer)
     2. Active preset profile overrides (Profile Layer)
     3. Local overlay overrides & secrets (Overlay Layer)
   - Implement required variable and secret validation, collecting missing entries into `missing_required: list[str]` and returning comprehensive diagnostics.
   - Implement provenance tracking recording the source layer (`default`, `profile`, `local_override`, `local_secret`) for every resolved key.

6. **Phase 6 (Steps 5–8): Code Cleanup, Observability, Technical Debt, and Dev Docs**
   - Run type checks (`make typecheck`), static analysis (`make lint`), and fast tests (`make test`).
   - Add structured logging events for manifest parsing, overlay mutations, and resolution diagnostics.
   - Author developer documentation in `doc/dev/library_manifest_and_overlay.md`.

---

### Mandatory — Failing Repro (Step 3 Design)

- **Test File Path**: `tests/test_library_manifest_and_overlay_repro.py`
- **What it Asserts**:
  1. **Manifest Model & Validation**:
     - `LibraryManifest` instantiation with `id`, `name`, `version`, `description`, `collections`, `variables`, `presets`.
     - Rejection of invalid manifest payloads (missing `id`/`name`, missing `collections`, invalid semantic version, unsupported variable types).
  2. **Multi-Format Manifest Parsing**:
     - Parsing valid YAML (`pypost-library.yaml`, `pypost-library.yml`) and JSON (`pypost-library.json`) manifest strings/files.
     - Raising `ManifestDiagnosticError` on malformed YAML/JSON syntax or schema violations.
  3. **Referenced Collection Path Verification**:
     - Validating relative collection paths on disk relative to manifest root.
     - Detecting missing or unreadable referenced collection files and reporting structured diagnostics.
  4. **Local Overlay Manager CRUD & Isolation**:
     - Initializing `LocalOverlayManager` with custom temporary `base_dir`.
     - Saving, loading, updating active profile, setting secrets, setting overrides, deleting overlay for a library ID.
     - Verifying atomic writes and file permissions (`0o600` for `overlay.json`).
     - Verifying that overlay storage is isolated in `base_dir` and never writes into the library workspace folder.
  5. **3-Tier Layered Variable Resolution & Precedence**:
     - Level 1 (Defaults) < Level 2 (Active Profile) < Level 3 (Local Overrides & Secrets).
     - Local secrets and overrides correctly override active profile and default values.
     - Active profile values correctly override default values.
  6. **Required Variable & Secret Enforcement**:
     - Detecting unpopulated required variables (`required: true` with no default, profile, or overlay value).
     - Reporting missing required variables and secrets in `VariableResolutionResult.missing_required` and raising diagnostic errors when strict execution is requested.
  7. **Provenance Tracking**:
     - Tracing the exact origin layer for each variable in `VariableResolutionResult.provenance` (`default`, `profile`, `local_override`, `local_secret`).
  8. **Round-Trip Persistence & Integrity**:
     - Verifying that updating an overlay preserves unmodified secrets/overrides and survives manager reload.
- **How it Fails Before Implementation**:
  - `pypost.models.library_manifest` does not exist (`ModuleNotFoundError`).
  - `pypost.core.library_manifest` does not exist (`ModuleNotFoundError`).
  - `pypost.core.local_overlay_manager` does not exist (`ModuleNotFoundError`).
  - `pypost.core.variable_resolver` does not exist (`ModuleNotFoundError`).
- **Sequencing**:
  - Step 2: Architecture approved.
  - Step 3: Write red test `tests/test_library_manifest_and_overlay_repro.py` and verify all tests fail.
  - Step 4: Implement domain models, schema validators, local overlay manager, and resolution engine until all tests pass green.

---

## Architecture

### 1. System Module Breakdown & Responsibilities

```
pypost/
├── models/
│   ├── collection_variable.py       # [EXISTING] CollectionVariable schema and type validation
│   ├── library_manifest.py          # [NEW] LibraryManifest, LocalLibraryOverlay, Resolution models
│   ├── models.py                    # [EXISTING] Core Collection & RequestData domain models
│   └── __init__.py                  # [UPDATED] Re-exports library manifest models
└── core/
    ├── library_manifest.py          # [NEW] Manifest YAML/JSON parser, validator, file discovery
    ├── local_overlay_manager.py     # [NEW] Local storage manager for ~/.pypost/libraries_data/
    ├── variable_resolver.py         # [NEW] 3-tier variable resolution engine with provenance
    └── collection_serializer.py     # [EXISTING] YAML/JSON collection codecs
```

#### Detailed Module Responsibilities

1. **`pypost.models.library_manifest`**:
   - `LibraryManifest`: Pydantic model representing `pypost-library.yaml` / `.json` structure.
   - `LibraryCollectionEntry`: Value object representing a collection reference (relative path, display name, optional description).
   - `LocalLibraryOverlay`: Pydantic model for user-local configuration (`library_id`, `active_profile`, `secrets`, `overrides`, `updated_at`).
   - `VariableProvenance`: Enum / string type indicating the origin layer (`DEFAULT`, `PROFILE`, `LOCAL_OVERRIDE`, `LOCAL_SECRET`).
   - `VariableResolutionContext`: Input parameter bundle for resolution (`manifest`, `overlay`, `active_profile`, `collection`, `strict_required`).
   - `VariableResolutionResult`: Result container holding resolved key-value mapping (`variables: dict[str, Any]`), provenance map (`provenance: dict[str, VariableProvenance]`), and missing required variables list (`missing_required: list[str]`).
   - `ManifestDiagnosticError`: Structured exception capturing error codes, file paths, line numbers, and actionable messages.

2. **`pypost.core.library_manifest`**:
   - `read_manifest_file(path: Path | str) -> LibraryManifest`: Loads and validates manifest from file.
   - `find_and_read_manifest(directory: Path | str) -> tuple[LibraryManifest, Path]`: Auto-discovers `pypost-library.yaml`, `pypost-library.yml`, or `pypost-library.json` in a directory.
   - `deserialize_manifest_from_yaml(content: str) -> LibraryManifest`: Parses YAML manifest text.
   - `deserialize_manifest_from_json(content: str) -> LibraryManifest`: Parses JSON manifest text.
   - `deserialize_manifest_from_dict(data: dict[str, Any]) -> LibraryManifest`: Validates dictionary payload into `LibraryManifest`.
   - `serialize_manifest_to_yaml(manifest: LibraryManifest) -> str`: Serializes manifest to formatted YAML string.
   - `serialize_manifest_to_json(manifest: LibraryManifest, indent: int = 2) -> str`: Serializes manifest to formatted JSON string.
   - `validate_manifest_collections(manifest: LibraryManifest, manifest_dir: Path) -> list[str]`: Checks if all referenced collection files exist on disk relative to manifest root, returning any missing collection paths.

3. **`pypost.core.local_overlay_manager`**:
   - `LocalOverlayManager`:
     - `__init__(base_dir: Path | str | None = None)`: Configures overlay root directory (defaults to `~/.pypost/libraries_data`).
     - `get_overlay(library_id: str) -> LocalLibraryOverlay`: Loads overlay for given library ID (or returns empty overlay instance if none exists).
     - `save_overlay(overlay: LocalLibraryOverlay) -> Path`: Persists overlay to `~/.pypost/libraries_data/<library-id>/overlay.json` with `0o600` permissions and atomic replacement.
     - `set_active_profile(library_id: str, profile_name: str | None) -> LocalLibraryOverlay`: Updates active preset profile.
     - `set_secret(library_id: str, key: str, value: Any) -> LocalLibraryOverlay`: Sets secret value.
     - `set_override(library_id: str, key: str, value: Any) -> LocalLibraryOverlay`: Sets local variable override.
     - `remove_secret(library_id: str, key: str) -> LocalLibraryOverlay`: Removes secret value.
     - `remove_override(library_id: str, key: str) -> LocalLibraryOverlay`: Removes local variable override.
     - `delete_overlay(library_id: str) -> bool`: Deletes overlay file and library directory on disk.
     - `list_library_overlays() -> list[str]`: Lists all library IDs with existing overlay configurations.

4. **`pypost.core.variable_resolver`**:
   - `LibraryVariableResolver`:
     - `resolve(manifest: LibraryManifest, overlay: LocalLibraryOverlay | None = None, active_profile: str | None = None, collection: Collection | None = None, strict_required: bool = False) -> VariableResolutionResult`: Computes effective variable map following 3-tier hierarchy.
     - `resolve_context(context: VariableResolutionContext) -> VariableResolutionResult`: Computes effective variable map from context object.
     - Validates types of effective values against declared `CollectionVariable` schemas.
     - Checks all variables marked `required: true` for presence and non-emptiness.
     - Tracks provenance metadata for each variable key.

---

### 2. Component Architecture Diagram (Mermaid)

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

    subgraph DomainModels [pypost.models]
        LM[LibraryManifest<br/>- id: str<br/>- name: str<br/>- version: str<br/>- collections: list[str]<br/>- variables: list[CollectionVariable]<br/>- presets: dict[str, dict]]
        LLO[LocalLibraryOverlay<br/>- library_id: str<br/>- active_profile: str | None<br/>- secrets: dict[str, Any]<br/>- overrides: dict[str, Any]]
        VRC[VariableResolutionContext<br/>- manifest<br/>- overlay<br/>- active_profile<br/>- collection<br/>- strict_required]
        VRR[VariableResolutionResult<br/>- variables: dict[str, Any]<br/>- provenance: dict[str, VariableProvenance]<br/>- missing_required: list[str]]
    end

    subgraph CoreComponents [pypost.core]
        LMP[library_manifest.py<br/>Manifest Parser & Path Validator]
        LOM[local_overlay_manager.py<br/>LocalOverlayManager<br/>Atomic & Secure 0o600 Storage]
        LVR[variable_resolver.py<br/>LibraryVariableResolver<br/>3-Tier Layered Precedence Engine]
    end

    MF --> LMP
    LMP --> LM
    LMP -. verifies paths .-> C1
    LMP -. verifies paths .-> C2

    OV --> LOM
    LOM --> LLO

    LM --> LVR
    LLO --> LVR
    VRC --> LVR
    LVR --> VRR
```

---

### 3. Data Models Specification

#### `pypost/models/library_manifest.py`

```python
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pypost.models.collection_variable import (
    COLLECTION_VARIABLE_TYPES,
    CollectionVariable,
    validate_variable_value,
)
from pypost.models.models import Collection


class VariableProvenance(str, Enum):
    """Source layer from which an effective variable value originated."""
    DEFAULT = "default"
    PROFILE = "profile"
    LOCAL_OVERRIDE = "local_override"
    LOCAL_SECRET = "local_secret"


class LibraryCollectionEntry(BaseModel):
    """Reference to a collection file contained in a collection library."""
    model_config = ConfigDict(populate_by_name=True)

    path: str
    name: Optional[str] = None
    description: str = ""

    @field_validator("path")
    @classmethod
    def validate_path_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Collection path cannot be empty")
        return v.strip()


class LibraryEnvironmentEntry(BaseModel):
    """Preset environment profile configuration in a library manifest."""
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: str = ""
    variables: Dict[str, Any] = Field(default_factory=dict)


class LibraryManifest(BaseModel):
    """Descriptor manifest for a version-controlled collection library."""
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str = "1.0.0"
    description: str = ""
    collections: List[str] = Field(default_factory=list)
    variables: List[CollectionVariable] = Field(default_factory=list)
    presets: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def validate_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Library ID cannot be empty")
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Library name cannot be empty")
        return v.strip()

    @field_validator("collections")
    @classmethod
    def validate_collections_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Library must declare at least one collection file")
        cleaned = [item.strip() for item in v if item and item.strip()]
        if not cleaned:
            raise ValueError("Library collections cannot contain only empty paths")
        return cleaned


class LocalLibraryOverlay(BaseModel):
    """User-specific local overrides and secrets stored outside version control."""
    model_config = ConfigDict(populate_by_name=True)

    library_id: str
    active_profile: Optional[str] = None
    secrets: Dict[str, Any] = Field(default_factory=dict)
    overrides: Dict[str, Any] = Field(default_factory=dict)
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class VariableResolutionContext(BaseModel):
    """Input parameters for resolving effective library variables."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    manifest: LibraryManifest
    overlay: Optional[LocalLibraryOverlay] = None
    active_profile: Optional[str] = None
    collection: Optional[Collection] = None
    strict_required: bool = False


class VariableResolutionResult(BaseModel):
    """Result of effective variable resolution with provenance and validation status."""
    model_config = ConfigDict(populate_by_name=True)

    variables: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, VariableProvenance] = Field(default_factory=dict)
    missing_required: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """True if there are no missing required variables and no validation errors."""
        return len(self.missing_required) == 0 and len(self.errors) == 0


class ManifestDiagnosticError(Exception):
    """Structured diagnostic error for manifest parsing and validation issues."""
    def __init__(
        self,
        code: str,
        message: str,
        path: Optional[Path | str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.code = code
        self.message = message
        self.path = Path(path) if path else None
        self.details = details or {}
        super().__init__(f"[{code}] {message}" + (f" (file: {path})" if path else ""))
```

---

### 4. Canonical Manifest and Overlay File Formats

#### Example `pypost-library.yaml`

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

#### Example `~/.pypost/libraries_data/lib-payments-core/overlay.json`

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

### 5. Effective Variable Resolution Algorithm

The resolution engine evaluates effective variable values according to a strict 3-tier precedence hierarchy (lowest to highest priority):

```
┌─────────────────────────────────────────────────────────────┐
│ Tier 3 (Highest): Local Overlay Storage                     │
│   1. Local Secrets (overlay.json -> secrets)                │
│   2. Local Variable Overrides (overlay.json -> overrides)   │
├─────────────────────────────────────────────────────────────┤
│ Tier 2 (Middle): Active Preset Profile                      │
│   Preset Profile Values (manifest -> presets[active_profile])│
├─────────────────────────────────────────────────────────────┤
│ Tier 1 (Lowest Base): Manifest & Collection Defaults        │
│   1. Collection Variable Defaults (collection -> variables) │
│   2. Manifest Variable Defaults (manifest -> variables)     │
└─────────────────────────────────────────────────────────────┘
```

#### Resolution Algorithm Flow:

```mermaid
flowchart TD
    Start([Start Resolution]) --> Step1[Step 1: Collect Variable Schema Definitions<br/>from Manifest and Collection]
    Step1 --> Step2[Step 2: Apply Layer 1 Defaults<br/>manifest.variables.default, collection.variables.default]
    Step2 --> Step3{Active Profile Selected?}
    Step3 -- Yes --> Step4[Step 3: Apply Layer 2 Preset Overrides<br/>manifest.presets[active_profile]]
    Step3 -- No --> Step5[Skip Layer 2]
    Step4 --> Step6{Local Overlay Provided?}
    Step5 --> Step6
    Step6 -- Yes --> Step7[Step 4: Apply Layer 3 Local Overrides & Secrets<br/>overlay.overrides, overlay.secrets]
    Step6 -- No --> Step8[Skip Layer 3]
    Step7 --> Step9[Step 5: Validate Data Types<br/>validate_variable_value for each effective value]
    Step8 --> Step9
    Step9 --> Step10[Step 6: Enforce Required Variables<br/>Check if any required=True variable is None or '']
    Step10 --> Step11{Any Missing Required or Type Errors?}
    Step11 -- Yes --> Step12[Record Missing Variables and Diagnostic Errors]
    Step11 -- No --> Step13[Mark Result Valid]
    Step12 --> Return([Return VariableResolutionResult])
    Step13 --> Return
```

---

### 6. Local Overlay Persistence and Storage Details

1. **Storage Location**:
   - `base_dir`: defaults to `Path.home() / ".pypost" / "libraries_data"`.
   - Per-library directory: `<base_dir>/<library-id>/`.
   - File path: `<base_dir>/<library-id>/overlay.json`.
2. **Directory and File Permissions**:
   - Directory created with mode `0o700` (`rwx------`).
   - File written with mode `0o600` (`rw-------`) to ensure only the current OS user can read or write secret values.
3. **Atomic File Writes**:
   - Overlays are serialized to a temporary file in the same directory (`overlay.json.tmp.<uuid>`) with `0o600` permissions.
   - Replaced atomically using `os.replace` to prevent corrupted state in case of unexpected termination or power loss.
4. **Isolation & Safety**:
   - The overlay directory path is strictly outside the repository workspace directory.
   - Even if the library repository is modified, deleted, or switched across Git branches, local overlays and secrets are maintained independently.

---

### 7. Security and Encryption Considerations

- **Strict Separation of Concerns**: Git repository contains structure and schemas (`pypost-library.yaml`), while all sensitive credentials (API tokens, private keys, passwords) reside in local configuration storage (`~/.pypost/libraries_data/`).
- **File System Permissions**: On POSIX systems, `overlay.json` is set to `0o600` so unprivileged local accounts cannot read sensitive tokens.
- **Log and Diagnostics Sanitization**: Sensitive values (variables with `secret: true` or entries in `overlay.secrets`) are never printed in plaintext in logs or debug metrics; they are masked as `[REDACTED]` or truncated.
- **Future-Proof Codec Support**: The `LocalOverlayManager` architecture is designed to optionally accept an encryption codec (using PyPost's `EnvironmentSecretsCodec` or OS Keychain) in future enhancements without altering the public API.

---

## Q&A

- **Q: How does the validator handle both YAML and JSON library manifests?**
  - **A:** The `read_manifest_file` function checks the file extension (`.yaml`, `.yml`, `.json`). If the extension is ambiguous, it attempts JSON decoding followed by YAML decoding. `find_and_read_manifest(dir)` checks for `pypost-library.yaml`, `pypost-library.yml`, and `pypost-library.json` in priority order.
- **Q: What happens if a manifest references a collection file that does not exist?**
  - **A:** `validate_manifest_collections(manifest, manifest_dir)` returns a list of missing collection relative paths. When validating strictly, `read_manifest_file` or `LibraryVariableResolver` raises a `ManifestDiagnosticError` with code `MISSING_COLLECTION_FILE` and the offending file path.
- **Q: Can a local overlay specify values for variables not declared in the manifest?**
  - **A:** Yes, local overrides allow arbitrary user keys (e.g. ad-hoc debugging variables). However, if the key matches a declared variable schema in the manifest or collection, its value is validated against the declared variable type.
- **Q: What is the precedence between manifest-level variables and collection-level variables?**
  - **A:** If a variable is declared in both the manifest and a collection within the library, the manifest-level declaration serves as the authoritative default for shared variables. Preset profile values and local overlay values override both.
- **Q: How are required variables enforced if no secret value has been provided yet?**
  - **A:** When resolving variables, any variable marked `required=True` that resolves to `None` or an empty string `""` is collected in `VariableResolutionResult.missing_required`. In non-strict mode, the resolution result is returned with `is_valid=False`, allowing UI panels (PYPOST-1223) to highlight the missing fields. In strict mode, a `ManifestDiagnosticError` with code `MISSING_REQUIRED_SECRET` is raised.
- **Q: How does `LocalOverlayManager` handle testing without touching the developer's real `~/.pypost/` directory?**
  - **A:** `LocalOverlayManager` accepts an optional `base_dir: Path | str | None` parameter. Tests supply a pytest temporary directory fixture (`tmp_path`), completely isolating test assertions from the user's home directory.
