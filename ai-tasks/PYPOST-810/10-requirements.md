# PYPOST-810: Legal review before first binary release

## Goals

PYPOST-786 documented PySide6 LGPL distributor obligations and PYPOST-809 added a transitive
license inventory. Before PyPost publishes its **first** official frozen binary or installer,
maintainers need a documented **legal review gate** and **platform-specific packaging notes**
so release engineers and counsel share a single checklist.

This task closes the PYPOST-786 follow-up "Legal review before first binary release."

## User Stories

- As a **release engineer**, I want a numbered gate checklist (G1–G8) so I know what must be
  complete before tagging a binary artifact.
- As **legal counsel**, I want platform-specific Qt bundling notes for macOS, Windows, and
  Linux to review against the planned installer layout.
- As a **maintainer**, I want the dependency audit to link to the gate so audit readers find
  the process in one place.

## Definition of Done

- [x] `doc/dev/licensing.md` includes § Pre-binary-release legal review gate with G1–G8
  checklist and maintainer workflow.
- [x] `doc/dev/licensing.md` includes § Platform-specific distribution notes for macOS,
  Windows, and Linux (Qt/PySide6 bundling).
- [x] Troubleshooting table updated with gate and platform-note pointers.
- [x] `doc/dev/dependencies_audit.md` cross-links to the new gate section.
- [x] `make check` passes (documentation-only; no application code changes).

## Task Description

**Source:** PYPOST-786 follow-up — legal review before first binary release
([PYPOST-810](https://pypost.atlassian.net/browse/PYPOST-810)).

**Scope:** `doc/dev/licensing.md`, `doc/dev/dependencies_audit.md`, `ai-tasks/PYPOST-810/`.

**Out of scope:** Building installers, PyInstaller/cx_Freeze scripts, CI automation of the
legal gate, actual counsel engagement, SPDX SBOM JSON export.

**Constraints:**

- Documentation only — no runtime, Makefile, or packaging script changes.
- Gate is a process checklist, not legal advice; retain counsel disclaimer from PYPOST-786.
- Platform notes focus on LGPL/Qt dynamic-library bundling; signing/notarization noted but
  not fully specified.

## Q&A

| Question | Answer |
| --- | --- |
| Why now if no binaries ship yet? | Establishes the release blocker checklist before packaging work starts |
| Does this replace PYPOST-786 distributor checklist? | No — gate references and extends it |
| Automate G5 inventory check? | Already covered by `make check-license-inventory` / CI; gate cites it |
