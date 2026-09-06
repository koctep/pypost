# PYPOST-1281: Provide predefined collection library seeded from built-in examples

## Goals

PyPost should make its maintained examples immediately useful as a trustworthy starting
collection library. New users should be able to discover the examples, understand what they
contain, and use them without accidentally changing the source files shipped with PyPost.

The business reason is to reduce setup time and make the official examples a consistent,
discoverable entry point for collection browsing, importing, and MCP experimentation.

## User Stories

- As a new PyPost user, I want the official examples to appear as a predefined collection
  library without manual registration.
- As a user exploring examples, I want to browse and inspect the bundled collections and their
  available environment information.
- As a user importing or running an example, I want the bundled source to remain unchanged.
- As a user who wants to customize the examples, I want to copy them into editable user storage.
- As a maintainer, I want the predefined library to stay aligned with the built-in manifest and
  all collections declared by it.

## Definition of Done

- The built-in examples are recognized as one first-class predefined library with the stable
  identity `pypost-examples`.
- Discovery works on initial application use and from the Library Manager, without requiring a
  network connection or a prior user registration.
- The predefined library exposes only valid manifest-declared collections and useful display
  metadata.
- Browsing, inspecting, importing, and using a collection from the predefined library do not
  modify the source-controlled examples.
- A user can create an editable copy in user-managed storage and the copy is independently
  usable.
- Invalid or incomplete built-in example content is reported clearly and does not create a
  misleading usable library entry.
- Automated tests cover discovery, validation, collection loading, source immutability, editable
  copying, and the Library Manager presentation.
- Developer documentation explains the predefined library, its read-only semantics, and the
  editable-copy workflow.

## Task Description

The `examples/` directory contains the official collection examples and the
`pypost-library.yaml` manifest. These assets should be presented as a predefined library named
`pypost-examples`. The library is a bundled template: users can read from it and use its
collections, but changes must be made only to a user-owned copy. The feature is limited to the
built-in examples and their presentation through existing collection-library surfaces.

Non-functional expectations include deterministic discovery, no secret values in diagnostics,
safe handling of missing or malformed assets, and compatibility with existing connected-library
records and collection imports.

## Q&A

- **Q: Which language is used?**
  **A:** Python, matching the existing library-management and UI code.
- **Q: Does this task add or change remote repositories?**
  **A:** No. The predefined library is local and bundled with the application.
- **Q: Is the bundled source editable?**
  **A:** No. Users must copy it into editable storage before making changes.
