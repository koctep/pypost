# PYPOST-786: Document PySide6 LGPL obligations

## Goals

The PYPOST-691 dependency audit identified PySide6 (LGPL-3.0) as the main license
consideration for anyone who redistributes PyPost as binaries or installers. PyPost itself
is MIT-licensed, but distributors need clear guidance on when LGPL obligations apply and
what steps to take. This task closes audit finding **R-P3-002 (L-002)**.

## User Stories

- As a **maintainer** preparing a release bundle, I want documented LGPL obligations so I
  know what notices and source offers to ship with PySide6.
- As a **contributor** evaluating packaging options, I want to understand when dynamic
  linking via pip wheels differs from shipping a frozen standalone binary.
- As a **reviewer**, I want the dependency audit to link to a single licensing guide instead
  of an unresolved P3 recommendation.

## Definition of Done

- [x] `doc/dev/licensing.md` exists and covers PySide6 LGPL-3.0 distribution obligations.
- [x] The guide explains when obligations apply (source-only vs binary redistribution).
- [x] The guide lists practical distributor actions (notices, license text, object-code offer).
- [x] `doc/dev/dependencies_audit.md` cross-links to the new guide and marks R-P3-002 done.
- [x] `make check` passes (no application code changes expected).

## Task Description

**Source:** PYPOST-691 dependency audit — R-P3-002 / L-002.

**Scope:** `doc/dev/licensing.md`, `doc/dev/dependencies_audit.md`, `doc/dev/README.md`.

**Out of scope:** Generating a full transitive license inventory (L-003 / R-P3-003 area),
legal review, CI license scanning, or changes to install/packaging scripts.

**Constraints:**

- Documentation only — no runtime or build behavior changes.
- Guide must be accurate for PySide6 6.x as consumed via pip (dynamic `.so`/`.dylib`/`.dll`).
- Not legal advice; point to official Qt/PySide6 and FSF LGPL references.

## Q&A

- **Why document now if impact is low for source-only development?** Enterprise adopters and
  future release packaging need a maintained in-repo reference; the audit flagged the gap.
- **Does this require a `LICENSES/` directory?** No — that is a separate recommendation
  (L-003 transitive inventory), out of scope for this ticket.
