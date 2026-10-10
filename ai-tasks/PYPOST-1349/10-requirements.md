# PYPOST-1349: Single locator for the shipped examples root

## Goals

Both the official examples library and the future Built-in MCP collections feature require a reliable, authoritative way to find the shipped examples directory. Whether running from a local source repository checkout, an editable installation, or an installed wheel distribution, PyPost must have a single source of truth for locating these bundled examples.

Furthermore, when users create editable copies of the predefined example library, those copies must contain only pure data and collection assets, free from Python packaging artifacts or runtime bytecode caches.

## User Stories

- As an MCP server author or user, I want PyPost to reliably locate its shipped examples across development and production environments so that predefined collections and templates are always accessible.
- As a PyPost developer working with an editable installation, I want the running application to use the active repository's examples rather than a stale or foreign path from an old environment mapping.
- As a user copying the predefined examples library for customization, I want the resulting editable library to contain clean data files without internal Python runtime or packaging clutter.
- As an operator running PyPost without bundled examples installed or accessible, I want the application to clearly indicate that the predefined library is unavailable rather than crashing or misbehaving.

## Definition of Done

1. A dedicated, unified locator provides the path to the shipped examples root for all consumers across environments:
   - Prioritizes the sibling repository checkout of the active `pypost` runtime package when it contains the required package marker and the expected `pypost-examples` manifest identity.
   - Falls back to the installed package resource when running from an installed distribution wheel.
   - Safely returns an unavailable status (or `None`) when neither a valid sibling tree nor a valid package resource is found.
2. Incomplete, foreign, or corrupted sibling directories (e.g., missing package marker or carrying an unexpected manifest identity) are ignored and do not masquerade as the authentic bundled examples root.
3. If an editable finder points to a different tree, the active imported `pypost` package's sibling tree takes precedence.
4. The predefined library service defaults to using the unified locator, preserving existing discovery behavior and diagnostics when examples are unavailable.
5. Editable library copies created via the predefined library service omit Python packaging markers (`__init__.py`) and runtime bytecode caches (`__pycache__`), preserving pure data for user workspaces.
6. The official examples library (`pypost-examples`) continues to be discovered with its four standard collections under normal installation and execution.
7. Developer documentation for the predefined collection library is updated with a concise description of the locator mechanism.
8. Repository verification passes (`make check`).

## Task Description

This Story represents Child C1b of epic PYPOST-1335 ("Built-in collections source for MCP server creation"). It builds directly on the packaging setup established in PYPOST-1348 (Child C1a) to establish the single authoritative locator mechanism needed by both the existing examples library and upcoming Built-in collection features.

The implementation language is Python. Architectural decisions are anchored in `ai-tasks/PYPOST-1336/20-architecture.md` (decision a, gap 6) and scope boundaries in `ai-tasks/PYPOST-1335/decomposition.md`.

### Scope

- Implement a single locator function (`bundled_examples_root`) in `pypost/core/bundled_resources.py` with hierarchical resolution:
  1. Active sibling tree of the imported package containing `__init__.py` and matching manifest `id`.
  2. Packaged resource directory containing the library manifest.
  3. Unavailable (`None`).
- Wire `PredefinedLibraryService` default root to the unified locator.
- Filter out packaging markers and bytecode caches when copying predefined examples to an editable workspace.
- Document locator behavior in `doc/dev/predefined_collection_library.md`.
- Comprehensive unit tests verifying each resolution branch and filtering behavior.

### Constraints and Exclusions

- Packaging configuration (`pyproject.toml`, packaging guards) belongs to PYPOST-1348 (C1a) and is not modified here.
- Built-in view definition (`BuiltinCollectionView`, `builtin-collections.yaml`) belongs to PYPOST-1350 (C2) and is not implemented here.
- Existing paths and references under `examples/` remain unchanged.
- All verification must be run exclusively via `make` targets.

### Main Entities

| Entity | Business Role |
| --- | --- |
| Shipped Examples Root | The authoritative filesystem root where bundled example collections, environments, and manifest reside |
| Bundled Resources Locator | The single resolution authority determining where shipped examples live in the current runtime |
| Predefined Library Service | The domain service providing discovery and copying of the read-only official example library |
| Editable Library Copy | User-owned, editable workspace directory containing pure example data |

### User Scenarios

1. **Running from Source / Editable Install**: A developer launches PyPost from their git checkout. The locator identifies the sibling `examples/` directory containing the expected manifest identity and serves the live repository examples.
2. **Running from Installed Wheel**: A user installs PyPost via a wheel package. The locator falls back to the package resources and serves the bundled examples.
3. **Foreign or Broken Tree**: A directory structure has an `examples/` folder lacking the package marker or with an mismatched manifest id. The locator ignores it and falls back to packaged resources or reports unavailable.
4. **Copying Examples**: A user clones the predefined library to customize examples. The resulting copy contains collections and environment JSON files, but no `__init__.py` or `__pycache__` artifacts.

## Q&A

- **Why is a unified locator needed instead of hardcoding relative paths?**
  Hardcoded paths (such as `Path(__file__).resolve().parents[2] / "examples"`) assume a source checkout layout and fail when PyPost is installed as a wheel in standard `site-packages`. A unified locator cleanly handles development checkouts, editable installations, and packaged distributions without duplication.
- **Why prioritize the sibling directory over package resources?**
  In development environments and test runs (e.g. `pythonpath = "."`), developers expect changes in the local repository's `examples/` tree to take effect immediately, even if a previously installed package finder points elsewhere.
- **Why filter out `__init__.py` and `__pycache__` during library copying?**
  `__init__.py` was added to `examples/` purely for Python packaging data resolution. An editable library created by a user represents data/templates, not a Python code package, so copying internal Python artifacts creates unnecessary clutter.
