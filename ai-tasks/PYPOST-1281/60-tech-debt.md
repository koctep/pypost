# PYPOST-1281: Technical Debt Analysis

## Shortcuts Taken

- The predefined root defaults to the repository's `examples/` directory when running from the
  source tree. A packaged distribution that relocates examples must inject its resource path.
- The editable-copy operation intentionally creates a complete local copy; deduplicated or
  copy-on-write storage is deferred because correctness and source immutability are the priority.

## Code Quality Issues

- The predefined source type is represented in the existing library-source enum and uses the
  existing manager row projection. A future library capability model could express read-only,
  copyable, and remotely synchronized capabilities independently.

## Missing Tests

- No desktop-level test launches the full Library Manager dialog and clicks the copy action; the
  service, presenter, and widget boundaries are covered independently.
- Crash recovery across a process interruption during `copytree` is not simulated. The operation
  refuses existing destinations and validates the completed copy, so partial destinations fail
  safely but may require manual cleanup.

## Performance Concerns

- Discovery validates all manifest-declared files whenever the library list is loaded. The built-in
  example set is small; caching or background validation can be considered if the library grows.

## Follow-up Tasks

- NON-BLOCKER: add an installed-package resource integration test for locating the bundled
  examples outside a source checkout.
- NON-BLOCKER: add a full dialog automation test for the predefined copy action and its error
  messages.

## Blocker Decision

SAFE TO CLOSE. The known gaps are packaging and broader UI/crash test coverage, not failures of
the requested discovery, read-only, validation, copying, or presentation behavior.
