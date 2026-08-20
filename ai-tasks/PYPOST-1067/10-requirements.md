# PYPOST-1067: Keep mypy gate diagnostics aligned with its configured scope

## Goals

The mypy baseline gate has a configured set of project paths to check, but its diagnostic
recognition is maintained separately. This creates a silent-failure risk: a maintainer can
extend the checked scope while diagnostics from the added path remain unrecognized and therefore
unenforced.

The goal is to make the configured mypy scope the single source of truth for both checking and
diagnostic enforcement. Maintainers should be able to extend the scope once and trust that new
type-checking errors from every configured path will cause the gate to report a baseline
difference.

## Programming Language

Python.

## User Stories

- As a maintainer extending mypy coverage, I want diagnostics from a newly configured project
  path to be enforced automatically, so the expanded gate cannot silently overlook new errors.
- As a contributor, I want the mypy baseline gate to report new errors consistently across every
  configured path, so a passing result reliably represents the declared checking scope.
- As a reviewer, I want one authoritative scope declaration, so I do not need to verify that
  multiple independent scope definitions remain synchronized.

## Definition of Done

- [ ] Given an additional valid project path in the configured mypy scope, a mypy error reported
  from that path is recognized by the baseline gate without a second scope-maintenance change.
- [ ] A recognized error from the added path is compared with the baseline and causes the same
  new-error failure behavior used for existing configured paths.
- [ ] Diagnostics from all currently configured mypy paths continue to be recognized and enforced.
- [ ] Diagnostics outside the configured mypy scope are not treated as scoped baseline errors.
- [ ] Automated coverage demonstrates that extending the configured scope also extends diagnostic
  enforcement.

## Task Description

### Problem

The baseline gate's declared checking scope and the scope used to recognize mypy diagnostics can
drift apart. If a maintainer adds a path to the checked scope but does not update the separate
recognition scope, mypy can emit errors for the new path that the gate silently ignores. The gate
may then report success even though the expanded scope contains unbaselined type errors.

This weakens confidence in the type-checking quality gate and adds avoidable maintenance work each
time the scope changes.

### Scope

**In scope**

- Keeping diagnostic recognition aligned with the complete configured mypy scope.
- Preserving baseline comparison and failure behavior for recognized diagnostics.
- Covering future scope extensions through automated verification.

**Out of scope**

- Changing which project paths are currently included in the mypy scope.
- Resolving existing mypy errors or changing the stored baseline contents.
- Changing how mypy is invoked, how diagnostic identity is defined, or how results are presented.
- Expanding the baseline gate to diagnostics outside its configured scope.

### Functional Requirements

1. The baseline gate must recognize mypy error diagnostics originating from every configured
   project path.
2. When a project path is added to the configured scope, diagnostic recognition must include that
   path without an additional scope declaration.
3. Recognized diagnostics from a newly configured path must participate in the same baseline
   comparison and pass/fail decisions as diagnostics from existing paths.
4. The gate must continue to exclude diagnostics that do not belong to the configured scope.
5. Existing behavior for the current configured paths must remain unchanged.

### Non-Functional Requirements

- **Reliability:** A successful gate result must not hide new mypy errors solely because the
  configured scope and diagnostic-recognition scope drifted apart.
- **Maintainability:** Maintainers must update the checked scope in one authoritative place.
- **Backward compatibility:** Existing scoped diagnostics, baseline data, and user-facing gate
  outcomes must retain their current meaning.

### Constraints and Assumptions

- The existing configured mypy path collection remains the authoritative declaration of scope.
- Mypy continues to emit file-based error diagnostics for the configured paths.
- This task does not alter the current scope or baseline; it aligns enforcement with that scope.
- Implementation design is deferred to Step 2.

### Main Entities and Interactions

| Entity | Business role |
| --- | --- |
| Configured mypy scope | The authoritative set of project paths covered by the quality gate. |
| Mypy diagnostic | A reported type-checking error associated with a project file. |
| Baseline gate | Compares recognized scoped diagnostics with accepted baseline errors. |
| Maintainer | Extends or reviews the type-checking scope and relies on gate results. |

The maintainer changes the configured scope. Mypy checks that scope and emits diagnostics. The
baseline gate recognizes diagnostics belonging to every configured path, compares them with the
accepted baseline, and reports a failure when new scoped errors are present.

## Q&A

- **Why is this change needed?** It prevents the gate from silently passing when a newly
  configured path contains unbaselined mypy errors.
- **What is the source of truth for scope?** The existing configured collection of paths passed
  to mypy.
- **Does this task add another path to the current scope?** No. It ensures future and current
  configured paths are enforced consistently.
- **Should diagnostics outside the configured scope affect the baseline gate?** No. Only
  diagnostics from configured paths belong to this gate.
- **Does this task change baseline error identity or contents?** No. Those behaviors remain
  outside this task.
