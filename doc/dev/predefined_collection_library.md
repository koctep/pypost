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

### `PredefinedLibraryService(root=None)`

Creates the bundled-library boundary. In a source checkout, `root` defaults to the repository's
`examples/` directory. Packaged applications should inject the installed examples resource root.

### `LibraryManagerService(..., predefined_root=None)`

Pass `predefined_root` when the application resource layout is known by the composition root.
`list_connections()` returns the validated predefined record before explicit connections. The
record has stable ID `pypost-examples`, source type `Predefined bundled library`, and
`is_read_only=True`.

### `copy_predefined_library(destination)`

Copies the validated examples to a new destination, rejects an existing destination or a path
inside the bundled source, validates the copy, and registers it as an ordinary editable local
library. Changes to the copy do not change `examples/`.

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
