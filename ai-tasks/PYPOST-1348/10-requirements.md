# PYPOST-1348: Ship the official examples with installed PyPost

## Goals

Users installing PyPost must receive its official examples, including the collections and
environments needed by the future Built-in collections feature. Maintainers must retain one
tracked source of those examples so published installations and the official examples library
cannot drift through independently maintained copies.

## User Stories

- As a PyPost user, I want the installed application to include its official example collections
  and environments so the shipped examples do not depend on a separate source checkout.
- As a maintainer, I want the existing examples to remain the single tracked source so an update
  to an example also updates what PyPost distributes.
- As a release maintainer, I want missing packaged examples or application packages detected
  before release so an apparently successful build cannot omit required content.
- As a contributor, I want installation checks to use a complete representative source seed so
  the checks accurately reflect the content the application needs.

## Definition of Done

1. The distributed wheel includes the official examples library manifest, example documentation,
   every manifest-declared file, and every shipped environment file. The distribution
   also covers the Built-in collections declaration when that declaration is introduced by its
   separately tracked task.
2. Existing application packages remain included; packaging validation detects an omitted
   application package, an uncovered manifest-declared file, or an uncovered environment file.
3. Lightweight packaging validation runs in the existing fast verification workflow without
   requiring additional development dependencies.
4. Installation verification uses a seed containing all listed application packages, the examples
   package marker, the library manifest, declared collections, and shipped environments. Missing
   required source directories cause an explicit failure instead of incomplete verification.
5. The slow verification workflow checks a built wheel and reports the required examples it
   contains. The fast test workflow retains its lightweight role.
6. Installation, fast quality checks, and slow packaging checks pass through the project's Make
   workflows. Development dependency locks remain unchanged.
7. The existing `examples/` source paths and references remain unchanged, and no second tracked
   copy of the official examples is introduced.

## Task Description

This Story is the shipping prerequisite for epic PYPOST-1335. It covers distributing the existing
official examples and validating their completeness. It has no prerequisite child issue.

The implementation language is Python, with TOML packaging configuration and Make workflows.
Detailed packaging decisions belong in the architecture artifact; the binding design input is
[the epic architecture](../PYPOST-1336/20-architecture.md), decision (a), and the issue scope is
recorded in [the C1a decomposition](../PYPOST-1335/decomposition.md).

### Scope

- Ship the existing official examples as application package data.
- Guard against missing application packages and missing examples in packaging declarations.
- Verify actual wheel contents in the slow verification tier.
- Keep installation-verification seeds complete for all declared packages and examples.

### Constraints and Exclusions

- `examples/` remains the only tracked copy; its files are not moved or renamed.
- The assigned package identity is `pypost.bundled_examples`.
- The existing examples and paired environments retain their content and paths.
- No setuptools or wheel dependency is added to development dependencies or their lock inputs.
- All build, installation, test, and validation operations use Make targets.
- Resource location and predefined-library integration are owned by PYPOST-1349.
- The Built-in collections view and its declaration are owned by PYPOST-1350.
- Runtime integration, user-interface changes, and migration of existing MCP servers are excluded.

### Main Entities

| Entity | Business attributes and relationship |
| --- | --- |
| Official examples library | One maintained source, library manifest, documentation, collections |
| Example collection | Manifest-declared file distributed with the official library |
| Example environment | Shipped environment file supporting example usage |
| Installed distribution | Contains required application packages and the official examples |
| Verification seed | Representative source content used to check installation completeness |

### User Scenarios

1. A user installs a published PyPost distribution and receives the official examples alongside
   the application, without needing the repository checkout.
2. A maintainer updates an official example in the existing source tree; the next distribution
   carries that same file without synchronizing a duplicate copy.
3. A packaging change omits a required file or application package; verification fails and
   identifies the incomplete packaging before release.
4. An installation check lacks a required mapped source directory; the check fails explicitly
   rather than silently creating an incomplete test seed.

## Q&A

- **Why is this required?** Installed PyPost must carry the official examples while preserving
  the single tracked source used by the official examples library (epic E3 and shipping for E2).
- **Does this enable Built-in selection or runtime lookup?** Those behaviors belong to subsequent
  child issues; this Story supplies and validates their distributed resources.
- **Are existing example paths or development dependencies changed?** No. Their preservation is
  an explicit acceptance constraint in PYPOST-1348.
- **Are further business decisions needed?** None for this scope; the goal and boundaries are
  explicit in the recorded Jira description.
