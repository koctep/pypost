# PYPOST-1281: Provide predefined collection library seeded from built-in examples

## Research

The repository already has a manifest model and parser, a durable connection store, a
`LibraryManagerService`, collection import flows, and a Library Manager presenter/widget. The
tracked `examples/pypost-library.yaml` manifest identifies the bundled library as
`pypost-examples` and declares the built-in collection files. Existing connected libraries are
persisted separately from their source directories, which allows the bundled source to remain
read-only and avoids making automatic discovery look like a user registration.

## Implementation Plan

1. Add a small predefined-library boundary that locates the bundled examples directory,
   validates its manifest and declared collection files, and returns a stable read-only library
   record.
2. Integrate that record into Library Manager discovery while keeping explicit user connections
   and persisted connection metadata unchanged.
3. Add an explicit copy/seed operation that copies validated bundled assets to a user-selected
   destination and registers the destination as an editable library.
4. Reuse existing manifest and collection loading/import paths so predefined collections have the
   same metadata and validation behavior as connected libraries.
5. Present the predefined row with a clear read-only/template indication and make invalid bundled
   assets visible as a safe diagnostic rather than a usable library.
6. Add deterministic tests for service discovery, validation, copying, immutability, and the
   Library Manager UI boundary.

**Mandatory — Failing Repro (next Step 3):** Add
`tests/test_predefined_library_pypost_1281_repro.py` with red checks for a
`pypost-examples` predefined record, manifest-declared collection listing, copy-to-editable
behavior, invalid-root handling, and read-only presentation. The tests use temporary connection
and destination paths and never access a network or mutate the repository examples.

## Architecture

### Components

- **Predefined library boundary**: owns bundled-root discovery, identity, read-only semantics,
  manifest validation, and safe editable-copy creation.
- **Library manager service**: composes the predefined boundary with existing explicit library
  records and exposes one unified discovery surface.
- **Manifest/collection domain**: remains the source of truth for declared paths, collection
  parsing, and variable metadata.
- **Library Manager presenter/widget**: renders the predefined record distinctly and routes copy
  actions without exposing mutable bundled paths as editable targets.
- **Existing import service**: consumes a validated predefined collection and preserves its copy
  versus link semantics; it must never write into the bundled root.

### Interaction

```text
Application/Library Manager
        |
        v
LibraryManagerService -----> PredefinedLibraryBoundary
        |                              |
        |                              v
        |                    examples/ manifest + collections
        v
Explicit connection store       validated read-only record
        |
        +---------------------> unified Library Manager entries
                                      |
                                      +--> inspect/import/read
                                      +--> copy to user storage --> editable record
```

### Interfaces and invariants

- Predefined discovery returns either a validated stable record for `pypost-examples` or a safe
  diagnostic result; it never persists a normal user connection automatically.
- A predefined record is explicitly read-only and its source path is never passed to a write
  operation.
- Collection listing is derived only from manifest-declared relative paths and validates each
  file before exposing it.
- Copying requires a destination outside the bundled source, refuses accidental overwrite, and
  registers the copy only after the copied content validates.
- Existing explicit connection identities are not replaced by the predefined record; the stable
  predefined identity is presented once in a deterministic order.
- Diagnostics contain error categories and safe paths/identifiers only; no secret values are
  emitted.

## Q&A

- **Q: Should automatic discovery create a durable connection entry?**
  **A:** No. It is a built-in template and can be discovered without changing user metadata.
- **Q: How does a copy become editable?**
  **A:** The service copies validated content to a user-owned destination and registers that
  destination as an ordinary editable local library.
