# PYPOST-1349: Single locator for the shipped examples root

## Research

Research performed on 2026-10-10 against approved [requirements](10-requirements.md),
[epic architecture, decision (a)](../PYPOST-1336/20-architecture.md),
[decomposition notes Child C1b](../PYPOST-1335/decomposition.md), and the current codebase.

### Current code and gaps

1. **PredefinedLibraryService default root coupling**:
   - `pypost/core/predefined_library.py` hardcodes:
     ```python
     self.root = (
         Path(root)
         if root is not None
         else Path(__file__).resolve().parents[2] / "examples"
     )
     ```
   - This assumes a repository layout (`pypost/core/` -> parent `pypost/` -> parent repo root -> `examples/`).
   - In an installed wheel, `Path(__file__).resolve().parents[2]` resolves to `site-packages/` or Python library root, which does not contain `examples/`, causing `PredefinedLibraryService.discover()` to fail with `Predefined library is unavailable: ManifestDiagnosticError` (or `FileNotFoundError`).

2. **Package resource availability**:
   - PYPOST-1348 (commit `1226de04`) configured `pyproject.toml` with `[tool.setuptools.package-dir] "pypost.bundled_examples" = "examples"` and added `examples/__init__.py`.
   - In an installed wheel, `importlib.resources.files("pypost.bundled_examples")` returns a `pathlib.Path` pointing to the packaged examples directory within `site-packages/pypost/bundled_examples`.
   - In a local development environment (e.g. editable install, or running with `pythonpath = "."`), an editable finder mapping might point to a stale or foreign tree, or the package might not be imported as a package resource.

3. **Locator resolution precedence (Decision a / Gap 6)**:
   - The authoritative locator `bundled_examples_root() -> Path | None` must resolve using strict priority:
     1. **Sibling source tree**: `Path(pypost.__file__).resolve().parents[1] / "examples"`:
        - Must exist as a directory.
        - Must contain `__init__.py` (ensuring it is the intended packaged structure).
        - Must contain a readable `pypost-library.yaml` whose `id` equals `"pypost-examples"`.
        - If any check fails (missing directory, missing marker, missing manifest, or manifest identity mismatch), the sibling directory is rejected and not treated as authentic bundled examples.
     2. **Package resource**: `importlib.resources.files("pypost.bundled_examples")`:
        - Safely queries `importlib.resources`. If `pypost.bundled_examples` cannot be imported (e.g. `ModuleNotFoundError`, `TypeError`), fall through.
        - Checks that the resolved resource container is an instance of `pathlib.Path` (as expected on Python 3.11+ for regular packages on disk).
        - Verifies that `(resource / "pypost-library.yaml").is_file()` (contains the library manifest).
     3. **Fallback**: `None`.
        - When neither branch finds a valid directory, `bundled_examples_root()` returns `None`.
   - Precedence rationale: In active development checkouts, tests running under `pythonpath = "."`, or editable installs, the imported `pypost`'s sibling repository `examples/` must take precedence over any stale or foreign `pypost.bundled_examples` package finder mapping.

4. **Integration with `PredefinedLibraryService`**:
   - In `PredefinedLibraryService.__init__(self, root: Path | str | None = None)`:
     - If `root` is explicitly passed, use `Path(root)`.
     - If `root is None`, call `bundled_examples_root()`.
     - If `bundled_examples_root()` returns `None`, store `self.root = None` (or an empty/non-existent sentinel Path, but keeping `self.root: Optional[Path]`).
     - In `discover()`: if `self.root is None`, immediately append `"Predefined library is unavailable: No bundled examples root found."` (or preserve existing diagnostic format) and return `None`.

5. **Packaging artifact filtering in `copy_to`**:
   - When a user copies the predefined library via `PredefinedLibraryService.copy_to(destination)`, the destination represents editable user collection assets and templates.
   - `examples/__init__.py` was introduced solely as a Python packaging anchor.
   - Python runtime bytecode directories (`__pycache__` and `*.pyc`) are packaging and interpreter artifacts.
   - `shutil.copytree(source, target, ignore=shutil.ignore_patterns("__init__.py", "__pycache__", "*.pyc"))` cleanly excludes them.
   - The copied target directory contains only collection JSONs, environments, manifest, and docs, preserving clean data.

### External & library references

- Python `importlib.resources` (<https://docs.python.org/3/library/importlib.resources.html>):
  `importlib.resources.files(anchor)` returns a `Traversable`. For filesystem-backed packages, this is a `pathlib.Path` (or wraps one).
- Python `shutil.copytree` (<https://docs.python.org/3/library/shutil.html#shutil.copytree>):
  Accepts an `ignore` callable, standardly created with `shutil.ignore_patterns(*patterns)`.

---

## Implementation Plan

### High-level steps

1. **Step 3: Failing Repro Test (Automated Red Tests)**:
   - Create automated unit tests in `tests/test_bundled_resources_locator.py` covering:
     - Branch 1: Sibling source tree discovery when valid (`__init__.py` + manifest id `"pypost-examples"`).
     - Branch 1 precedence: Sibling tree takes precedence even if `importlib.resources.files("pypost.bundled_examples")` resolves to a different directory.
     - Sibling tree rejection: Sibling directory lacking `__init__.py` is rejected.
     - Sibling tree rejection: Sibling directory with foreign manifest `id` (e.g. `foreign-library`) is rejected.
     - Sibling tree rejection: Sibling directory lacking `pypost-library.yaml` is rejected.
     - Branch 2: Packaged resource discovery when sibling tree is absent/rejected and package resource is valid.
     - Branch 3: Fallback to `None` when neither sibling tree nor package resource exists or is valid.
     - `PredefinedLibraryService` integration: Default root uses `bundled_examples_root()`; when locator returns `None`, discovery returns `None` with unavailable diagnostic.
     - `PredefinedLibraryService.copy_to`: Copied library does not contain `__init__.py`, `__pycache__`, or `*.pyc`.
   - Running `make test PYTEST_ARGS='tests/test_bundled_resources_locator.py'` will fail because `pypost.core.bundled_resources` does not yet exist.

2. **Step 4: Development**:
   - Create `pypost/core/bundled_resources.py` implementing `bundled_examples_root() -> Path | None` and helper functions.
   - Update `pypost/core/predefined_library.py`:
     - Default `root` in `PredefinedLibraryService.__init__` to `bundled_examples_root()`.
     - Gracefully handle `self.root is None` in `discover()`.
     - Update `copy_to()` to ignore `__init__.py`, `__pycache__`, and `*.pyc`.
   - Verify that all unit tests in `tests/test_bundled_resources_locator.py` and existing `tests/test_predefined_library_pypost_1281_repro.py` pass.

3. **Step 5: Code Cleanup**:
   - Inspect diff, verify type annotations, remove any dead code or debug artifacts. Document cleanups in `40-code-cleanup.md`.

4. **Step 6: Observability**:
   - Ensure structured logging is emitted in `pypost/core/bundled_resources.py` (e.g. `bundled_examples_root_resolved`, `bundled_examples_root_not_found`, `bundled_examples_sibling_rejected`) and `predefined_library.py`. Document in `50-observability.md`.

5. **Step 7: Technical Debt**:
   - Record technical debt analysis in `60-tech-debt.md`.

6. **Step 8: Developer Docs**:
   - Update `doc/dev/predefined_collection_library.md` with details on `bundled_examples_root()` locator resolution order and packaging artifact filtering.

### Mandatory — Failing Repro (next Step 3)

- **Test file**: `tests/test_bundled_resources_locator.py`.
- **Test annotations**: Decorated with `@pytest.mark.timeout(30)` or module-level `pytestmark = pytest.mark.timeout(30)`.
- **Assertions**:
  1. `test_bundled_examples_root_resolves_sibling_tree`: With monkeypatched or standard `pypost.__file__`, finds `examples/` with `__init__.py` and matching manifest id.
  2. `test_bundled_examples_root_sibling_takes_precedence_over_package_resource`: When both sibling tree and package resource exist, sibling tree is returned.
  3. `test_bundled_examples_root_rejects_sibling_without_init`: Temporary tree with `examples/pypost-library.yaml` but missing `__init__.py` is ignored.
  4. `test_bundled_examples_root_rejects_sibling_with_mismatched_manifest_id`: Temporary tree with `examples/__init__.py` and manifest with `id: foreign-examples` is ignored.
  5. `test_bundled_examples_root_resolves_package_resource_when_no_sibling`: When sibling tree is absent, falls back to `importlib.resources.files("pypost.bundled_examples")`.
  6. `test_bundled_examples_root_returns_none_when_both_unavailable`: Returns `None` when sibling is absent and package resource raises `ModuleNotFoundError` or contains no manifest.
  7. `test_predefined_library_service_defaults_to_locator`: `PredefinedLibraryService()` uses locator; when locator returns `None`, `discover()` returns `None` and records diagnostic.
  8. `test_predefined_library_copy_to_filters_packaging_artifacts`: Creating a copy from a source containing `__init__.py` and `__pycache__` results in a target directory without those entries.
- **Forcing red failure**: Since `pypost/core/bundled_resources.py` does not exist yet, importing `bundled_examples_root` fails immediately with `ImportError` / `ModuleNotFoundError`.

---

## Architecture

### Module Diagram

```mermaid
flowchart TD
    subgraph Locator["pypost.core.bundled_resources"]
        BER["bundled_examples_root() -> Path | None"]
        CHK_SIB["_resolve_sibling_root(pypost_file)"]
        CHK_RES["_resolve_package_resource()"]
        VAL_SIB["_validate_sibling_manifest(root)"]
    end

    subgraph Consumers["Core Services"]
        PLS["PredefinedLibraryService<br/>(pypost.core.predefined_library)"]
        BCV["BuiltinCollectionView<br/>(pypost.core.builtin_collections - PYPOST-1350)"]
    end

    subgraph FilesystemSources["Filesystem & Package Resources"]
        SIB["Sibling Source Checkout:<br/>.../examples/ (__init__.py, pypost-library.yaml)"]
        PKG["Installed Wheel Package Resource:<br/>pypost.bundled_examples (Traversable -> Path)"]
    end

    BER --> CHK_SIB
    CHK_SIB --> VAL_SIB
    VAL_SIB -->|1. Valid Sibling| SIB
    BER --> CHK_RES
    CHK_RES -->|2. Valid Package Resource| PKG
    BER -->|3. Fallback| NONE["None"]

    PLS -->|default root| BER
    BCV -.->|via PredefinedLibraryService| PLS
    PLS -->|copy_to (filter __init__.py, __pycache__)| USER_COPY["Clean Editable Workspace Copy"]
```

### Module Responsibilities

1. **`pypost.core.bundled_resources`** (NEW module):
   - Responsibility: Provide authoritative filesystem discovery of bundled assets shipped with PyPost.
   - Primary function: `bundled_examples_root() -> Path | None`.
   - Resolution algorithm:
     ```python
     def bundled_examples_root() -> Path | None:
         # 1. Check sibling source tree of active pypost module
         sibling = _resolve_sibling_root()
         if sibling is not None:
             return sibling

         # 2. Check package resource pypost.bundled_examples
         pkg_resource = _resolve_package_resource()
         if pkg_resource is not None:
             return pkg_resource

         # 3. None fallback
         return None
     ```
   - Sibling check details:
     - `pypost_dir = Path(pypost.__file__).resolve().parent`
     - `candidate = pypost_dir.parent / "examples"`
     - Must satisfy:
       - `candidate.is_dir()`
       - `(candidate / "__init__.py").is_file()`
       - `(candidate / "pypost-library.yaml").is_file()`
       - Manifest parsed using `find_and_read_manifest(candidate)` or light YAML parsing: `manifest.id == "pypost-examples"`.
   - Package resource details:
     - Calls `importlib.resources.files("pypost.bundled_examples")`.
     - Catches `(ModuleNotFoundError, TypeError, ValueError, AttributeError)`.
     - Validates that the resource resolves to a `pathlib.Path` (via `isinstance(ref, Path)` or conversion if applicable).
     - Checks `(ref / "pypost-library.yaml").is_file()`.

2. **`pypost.core.predefined_library`** (UPDATED module):
   - Responsibility: Expose the bundled example library as a validated read-only library connection and provide editable copying.
   - Changes:
     - `__init__(self, root: Path | str | None = None)`: If `root is None`, calls `bundled_examples_root()`. Stores `self.root: Path | None`.
     - `discover(self)`: If `self.root is None`, records `Predefined library is unavailable: bundled examples root not found.` and returns `None`.
     - `copy_to(self, destination: Path | str)`: When copying `self.root` to `destination`, passes `ignore=shutil.ignore_patterns("__init__.py", "__pycache__", "*.pyc")` to `shutil.copytree()`.

3. **`doc/dev/predefined_collection_library.md`** (UPDATED documentation):
   - Responsibility: Document the locator resolution hierarchy and the clean copy semantics.

### Interfaces and Types

```python
# pypost/core/bundled_resources.py
from pathlib import Path

EXPECTED_LIBRARY_MANIFEST_ID = "pypost-examples"
BUNDLED_EXAMPLES_PACKAGE = "pypost.bundled_examples"

def bundled_examples_root() -> Path | None:
    """Return the authoritative root directory for bundled examples, or None if unavailable.

    Checks:
    1. Sibling source tree of imported `pypost` with `__init__.py` and matching manifest id.
    2. Package resource `pypost.bundled_examples` containing `pypost-library.yaml`.
    3. Returns None if neither is present or valid.
    """
    ...
```

---

## Q&A

- **Q: Why should `bundled_examples_root` validate the manifest identity in the sibling directory?**
  **A**: If a developer or foreign workspace checkout has an `examples/` directory that belongs to another project or has an arbitrary manifest, we must not falsely identify it as PyPost's authentic bundled examples. Validating that `id == "pypost-examples"` prevents accidental hijacking.

- **Q: Why use `shutil.ignore_patterns("__init__.py", "__pycache__", "*.pyc")`?**
  **A**: `__init__.py` in `examples/` was introduced strictly so `pypost.bundled_examples` functions as a regular Python package for packaging and resource loading. When a user creates an editable copy of the library, the copy is pure data for their own collections. Copying Python package markers or Python bytecode caches into user workspaces creates clutter and confusion.

- **Q: What happens if `importlib.resources.files()` returns a virtual or non-Path traversable?**
  **A**: For zip/wheel packages, Python 3.11 `importlib.resources.files` returns a `ZipPath`. However, PyPost requires filesystem directory paths for SQLite/filesystem library loading. If `isinstance(ref, Path)` is false, it cannot be used directly as a directory root and returns `None` (or falls back safely), ensuring robust typing and runtime safety.
