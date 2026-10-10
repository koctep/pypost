# Predefined Collection Library

## Overview

PyPost exposes the repository's official examples as the predefined
`pypost-examples` collection library. It is a local template intended for browsing, inspection,
collection import, and MCP experiments. The source remains read-only so application actions do
not modify the maintained examples.

## Architecture

- `PredefinedLibraryService` locates and validates the bundled examples root.
- `LibraryManagerService` combines the predefined record with explicit user library connections.
- `LibraryPresenter` and `LibraryListWidget` render the template as a predefined source and
  expose only safe actions for it.
- Existing manifest and collection import services read the same validated manifest-declared
  files used by connected libraries.

The predefined record is discovered in memory and is not written to the durable connection
registry. This prevents automatic startup discovery from changing user configuration.

## API / Usage

### `pypost.core.bundled_resources.bundled_examples_root()`

Provides authoritative filesystem discovery of the bundled PyPost examples root directory.
It resolves candidate paths using a strict hierarchy:
1. **Sibling source checkout**: Checks `examples/` relative to the active `pypost` module
   (`Path(pypost.__file__).resolve().parent.parent / "examples"`). Requires `__init__.py` and
   a readable `pypost-library.yaml` whose `id` matches `pypost-examples`.
2. **Package resource**: Queries `importlib.resources.files("pypost.bundled_examples")` traversable
   when backed by a filesystem directory containing `pypost-library.yaml`.
3. **Fallback**: Returns `None` when neither location is present or valid.

### `PredefinedLibraryService(root=None)`

Creates the bundled-library boundary. When `root` is omitted (`None`), it automatically calls
`bundled_examples_root()` to locate the shipped examples root. Callers may also pass an explicit
`Path` or `str` root (e.g. in test suites).

### `LibraryManagerService(..., predefined_root=None)`

Pass `predefined_root` when the application resource layout is known by the composition root.
`list_connections()` returns the validated predefined record before explicit connections. The
record has stable ID `pypost-examples`, source type `Predefined bundled library`, and
`is_read_only=True`.

When constructing a manager around an explicitly injected test or alternate connection store,
pass `include_predefined=True` to include the template deliberately; the default application
manager enables it automatically.

### `copy_predefined_library(destination)` / `PredefinedLibraryService.copy_to(destination)`

Copies the validated examples to a new destination, rejects an existing destination or a path
inside the bundled source, validates the copy, and registers it as an ordinary editable local
library. Changes to the copy do not change `examples/`.

During copying, `copy_to` filters out packaging and runtime artifacts (`__init__.py`,
`__pycache__`, `*.pyc`) via `shutil.ignore_patterns`. This ensures user library copies stay pure
collection data without Python packaging artifacts.

## Configuration

No user setting is required. The examples manifest remains at `examples/pypost-library.yaml` and
declares the collection files, variables, and profiles. A packaged deployment must provide that
manifest and its declared collection files at the injected resource root.

## Troubleshooting

- **The predefined row is absent:** inspect `LibraryManagerService.diagnostics`; the manifest may
  be missing, invalid, have the wrong `pypost-examples` identity, or reference missing files.
- **An edit action is rejected:** the predefined row is intentionally read-only. Use
  `copy_predefined_library()` or the Library Manager's editable-copy action first.
- **A copy fails:** choose a new destination outside the bundled examples and ensure the parent
  directory is writable.

## Validation

Run the scoped checks through the repository Makefile:

```bash
make test PYTEST_ARGS='tests/test_predefined_library_pypost_1281_repro.py'
make lint
make typecheck
make verify-ai-tasks
```

## Planned Built-in MCP Source (PYPOST-1335)

This section records the epic architecture and progression across child issues.
See the [decomposition and issue dependencies](../../ai-tasks/PYPOST-1335/decomposition.md) and
[approved architecture](../../ai-tasks/PYPOST-1336/20-architecture.md) for acceptance criteria.

### Architecture and Ownership

The Built-in source is a filtered, read-only view of the shipped `pypost-examples`
library. It offers Jira Cloud, GitLab, and GitHub MCP collections; the generated `mcp.json`
synthetic test fixture remains available only through the examples library.

| Issue | Responsibility | Status |
| --- | --- | --- |
| PYPOST-1348 | Package `examples/` as `pypost.bundled_examples`; build guards | Complete |
| PYPOST-1349 | Shared locator and predefined-library integration | Complete |
| PYPOST-1350 | `builtin-collections.yaml` view and structural validation | Implemented |
| PYPOST-1351 | Persisted marker, runtime resolution and headless daemon startup | Planned |
| PYPOST-1352 | Checked save, reconciliation, replacement and env refresh | Planned |
| PYPOST-1353 | Built-in dialog source, read-only picker and server-table UI | Planned |
| PYPOST-1354 | Editable paired-environment copy | Planned |
| PYPOST-1355 | Copy for editing into a workspace collection | Planned |
| PYPOST-1356 | Offline upgrade/copy end-to-end verification and user docs | Planned |

These nine children belong to epic PYPOST-1335 and sprint 2025, totaling 37 SP. Completed
PYPOST-1334 supplies the GitHub collection and environment and is linked to the epic.

Packaging maps `pypost.bundled_examples` to `examples/`, keeping one tracked source.
The shared locator first checks the `examples/` sibling of the imported `pypost`, then
the installed package resource, and returns `None` when neither is usable. The Built-in
view validates its collection and environment paths against the shipped library manifest.

A Built-in server persists `library_id = manifest_id = "pypost-examples"`, its
`library_collection_path`, and `bundled_library=True` (PYPOST-1351). Resolution uses the
predefined record directly, so a connected library with the same ID cannot shadow the bundle.
`LibraryRuntimeResolver` re-reads the installed collection on each start, including
headless daemon startup, to pick up content shipped by an application upgrade.

### Curated Built-in Catalog (`examples/builtin-collections.yaml`)

The Built-in catalog is declared in `examples/builtin-collections.yaml`. It provides a curated,
declarative registry of supported out-of-the-box MCP integrations shipped in the bundled examples
library:

```yaml
version: "1.0.0"
entries:
  - id: "jira-cloud-mcp"
    name: "Jira Cloud MCP"
    collection: "collections/jira_mcp.json"
    environment: "environments/jira_cloud.json"
  - id: "gitlab-mcp"
    name: "GitLab MCP"
    collection: "collections/gitlab_mcp.json"
    environment: "environments/gitlab.json"
  - id: "github-mcp"
    name: "GitHub MCP"
    collection: "collections/github_mcp.json"
    environment: "environments/github.json"
```

Key principles of the catalog format:
- **Curated entries**: Specifically pairs Jira Cloud, GitLab, and GitHub MCP collections with
  their respective template environments (`environments/jira_cloud.json`,
  `environments/gitlab.json`, `environments/github.json`).
- **Explicit exclusion of test fixtures**: The synthetic test fixture `collections/mcp.json`
  is deliberately omitted from this catalog. It does not possess a paired template environment
  and is intended solely for internal fixture testing, not as a user-facing built-in integration.
- **Manifest validation**: Every collection path listed under `entries` must be explicitly
  declared in the root `pypost-library.yaml` manifest. Catalog entries referencing undeclared or
  missing collections are excluded with diagnostic logs.

### `BuiltinCollectionEntry`

Defined in `pypost.core.builtin_collections.BuiltinCollectionEntry` as an immutable frozen
dataclass representing one curated entry:
- `collection_path`: Relative path within the examples root (e.g. `collections/jira_mcp.json`).
- `environment_path`: Relative path to paired template environment (for example,
  `environments/jira_cloud.json`).
- `name`: Human-readable display name, extracted from the catalog entry or the collection file.
- `collection_id`: Stable identifier of the collection (e.g. `jira-cloud-mcp`).
- `version`: Version string declared in the collection JSON (or `None`).

#### Identity Matching via `selection()`

To ensure seamless integration with the existing `McpServerConfiguration` model and library
selection mechanisms, `BuiltinCollectionEntry.selection()` produces a dictionary matching the
server configuration identity contract:

```python
entry.selection()
# -> {
#      "library_id": "pypost-examples",
#      "manifest_id": "pypost-examples",
#      "path": "collections/jira_mcp.json",
#    }
```

This guarantees identity alignment across the UI, persistent settings, and runtime resolution
subsystems without hardcoding path structures elsewhere.

### `BuiltinCollectionView`

`pypost.core.builtin_collections.BuiltinCollectionView` serves as the domain view layer over
`PredefinedLibraryService`:

- **Read-Only View Layer**: Operates purely over the validated predefined library root. It never
  modifies, writes, or persists data back into the bundled examples directory.
- **Fresh File Loading**: To prevent stale caches when application or library files are updated,
  `load_collection(collection_path)` and `load_paired_environment(collection_path)` perform fresh
  reads from disk on every invocation. Successive calls yield distinct model instances.
- **Graceful Diagnostics**: Rather than crashing the application or throwing uncaught exceptions
  during listing, missing catalog files, corrupted YAML, missing collections, or path traversal
  attempts are captured in `view.diagnostics` and logged with structured telemetry. When errors
  occur, `list_entries()` safely returns an empty list `[]`.
- **Identity Predicate**: `is_builtin(configuration)` checks whether a given
  `McpServerConfiguration` targets a valid curated built-in collection by verifying that
  `configuration.library_id == "pypost-examples"` and that `configuration.library_collection_path`
  matches one of the curated entries.

### Structural Consistency Testing Principles

Paired template environments serve as user templates and configuration baselines. To ensure
they never drift from manifest definitions while avoiding brittle value checks or breaking live
fixtures, automated contract tests (`tests/test_builtin_collections.py`) enforce structural
consistency rules:

1. **Manifest Variable Validation**: The set of variable keys present in the paired environment
   must strictly equal the set of collection variable names declared in the library manifest
   (`pypost-library.yaml`). Missing or extraneous keys fail validation.
2. **Secret Hidden Keys**: Every variable declared as `secret: true` in the manifest must be
   registered in the environment's `hidden_keys` list.
3. **Non-Empty Committed Placeholders**: Secret variables in the committed environment files
   must contain non-empty string placeholders (e.g. `your-jira-api-token`).
4. **Overridable Keys Subset**: All keys listed in `mcp_overridable_keys` must be a strict subset
   of the environment's variable keys.
5. **No Value Comparison**: Structural testing explicitly avoids comparing actual variable
   values against manifest presets or defaults. This guarantees that realistic placeholders
   and test fixtures (e.g. `tests/test_example_fixtures.py`, `tests/test_jira_mcp_live_smoke.py`)
   remain functional and uncorrupted.

### Future Usage and Configuration

After the remaining child issues are implemented, users will select Built-in in the MCP server
editor, choose a read-only collection, and select a workspace environment. Save will require an
environment. Users may create an editable copy of the paired environment; the copy will have a
fresh ID, conflict-safe name, hidden-key metadata, and empty secret values.

Built-in variables will use the selected workspace environment, with manifest defaults only for
missing keys. Built-in resolution will apply no library preset or overlay, and the controller save
will write no shared library overlay.

Copy for editing will create an editable workspace collection and select it in the open editor.
Only Save will switch the persisted server to that copy; Cancel will leave the server on Built-in
while retaining the workspace copy. Copies will not receive shipped updates.

### Diagnostics and Limits

- Missing bundle: the locator will retain the predefined-library-unavailable diagnostic
  (PYPOST-1349). Check the sibling tree or installed package contents.
- Invalid view: missing files, invalid JSON, or invalid membership produces an empty Built-in list
  with a diagnostic (PYPOST-1350). Check the shipped view and manifest.
- Non-entry collection path: a persisted row will load but will not be served, reporting
  `missing built-in collection` (PYPOST-1351); saving it will raise `builtin_invalid`
  (PYPOST-1352). Select a valid curated entry.
- Deleted selected workspace environment: lifecycle reconciliation will stop the running server
  and report `missing environment` (PYPOST-1352). Select or create a workspace environment.

There is no migration of existing workspace or Library servers. Missing marker fields will
default to `False`, and `library_id` precedence over a stale `collection_id` will remain intact.
Ordinary-library lifecycle repairs belong to independent Debt PYPOST-1347.

### Packaging Implementation and Verification (PYPOST-1348)

The packaging foundation introduced in PYPOST-1348 establishes `examples/` as package data
without maintaining a separate source copy:
- `pyproject.toml` explicitly declares `packages` including `pypost.bundled_examples`, mapped via
  `[tool.setuptools.package-dir]` to the repository `examples/` directory.
- `[tool.setuptools.package-data]` explicitly matches `pypost-library.yaml`, `README.md`,
  `collections/*.json`, `environments/*.json`, and reserves `builtin-collections.yaml`.
- An isolated verification script `scripts/check_package_data.py` inspects built wheels to verify
  that every application initializer and all required bundled examples members are present and
  identical to their canonical sources.
- The `make check-package-data` target builds an isolated wheel with `pip wheel --no-deps` into a
  temporary directory and executes `scripts/check_package_data.py` to ensure package integrity.
  This check runs as part of `make test-slow`.
