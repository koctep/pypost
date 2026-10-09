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

When constructing a manager around an explicitly injected test or alternate connection store,
pass `include_predefined=True` to include the template deliberately; the default application
manager enables it automatically.

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

## Planned Built-in MCP Source (PYPOST-1335)

This section records the **planned design**, not an implemented API or available UI flow.
PYPOST-1336 decomposes the epic; it adds no runtime behavior. The existing predefined-library
APIs above remain the current interface. See the
[decomposition and issue dependencies](../../ai-tasks/PYPOST-1335/decomposition.md) and
[approved architecture](../../ai-tasks/PYPOST-1336/20-architecture.md) for acceptance criteria.

### Architecture and Ownership

The planned Built-in source is a filtered, read-only view of the shipped `pypost-examples`
library. It will offer Jira, GitLab and GitHub MCP collections; the generated `mcp.json`
fixture remains available only through the examples library.

| Issue | Planned responsibility |
| --- | --- |
| PYPOST-1348 | Package the single `examples/` tree as `pypost.bundled_examples`; build guards |
| PYPOST-1349 | Shared `bundled_examples_root()` locator and predefined-library integration |
| PYPOST-1350 | `builtin-collections.yaml` view and paired-environment structural validation |
| PYPOST-1351 | Persisted Built-in marker, runtime resolution and headless daemon startup |
| PYPOST-1352 | Checked controller save, reconciliation, replacement and environment refresh |
| PYPOST-1353 | Built-in dialog source, read-only picker and server-table presentation |
| PYPOST-1354 | Editable paired-environment copy |
| PYPOST-1355 | Copy for editing into a workspace collection |
| PYPOST-1356 | Offline upgrade/copy end-to-end verification and user documentation |

These nine children belong to epic PYPOST-1335 and sprint 2025, totaling 37 SP. Completed
PYPOST-1334 supplies the GitHub collection and environment and is linked to the epic.

Packaging will map `pypost.bundled_examples` to `examples/`, keeping one tracked source.
The shared locator will first check the `examples/` sibling of the imported `pypost`, then
the installed package resource, and return `None` when neither is usable. The Built-in
view will validate its collection and environment paths against the shipped library.

A Built-in server will persist `library_id = manifest_id = "pypost-examples"`, its
`library_collection_path`, and `bundled_library=True`. Resolution will use the predefined
record directly, so a connected library with the same ID cannot shadow the bundle.
`LibraryRuntimeResolver` will re-read the installed collection on each start, including
headless daemon startup, to pick up content shipped by an application upgrade.

### Future Usage and Configuration

After the children are implemented, users will select Built-in in the MCP server editor,
choose a read-only collection and select a workspace environment. Save will require an
environment. They may create an editable copy of the paired environment; the copy will
have a fresh ID, conflict-safe name, hidden-key metadata and empty secret values.

Built-in variables will use the selected workspace environment, with manifest defaults
only for missing keys. Built-in resolution will apply no library preset or overlay, and
the controller save will write no shared library overlay. Paired-file validation will
check keys, secret placeholders and metadata rather than compare values with presets.

Copy for editing will create an editable workspace collection and select it in the open
editor. Only Save will switch the persisted server to that copy; Cancel will leave the
server on Built-in while retaining the workspace copy. Copies will not receive shipped
updates. This action differs from the existing whole-library copy API above.

### Planned Diagnostics and Limits

- Missing bundle: the locator will retain the predefined-library-unavailable diagnostic
  (PYPOST-1349). Check the sibling tree or installed package contents.
- Invalid view: missing files, invalid JSON or invalid membership will produce an empty
  Built-in list with a diagnostic (PYPOST-1350). Check the shipped view and manifest.
- Non-entry collection path: a persisted row will load but will not be served, reporting
  `missing built-in collection` (PYPOST-1351); saving it will raise `builtin_invalid`
  (PYPOST-1352). Select a valid curated entry.
- Deleted selected workspace environment: lifecycle reconciliation will stop the running
  server and report `missing environment` (PYPOST-1352). Select or create a workspace
  environment.

There is no migration of existing workspace or Library servers. Missing marker fields
will default to `False`, and `library_id` precedence over a stale `collection_id` will
remain intact. Ordinary-library lifecycle repairs belong to independent Debt PYPOST-1347,
outside this epic and sprint. New packaging and end-to-end checks belong to the children;
`make check-package-data` is a planned target, not a current validation command.
