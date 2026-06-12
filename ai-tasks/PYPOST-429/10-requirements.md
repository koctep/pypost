# PYPOST-429: Investigate root cause of ELF core dump removed from repo

Related: [PYPOST-403](https://pypost.atlassian.net/browse/PYPOST-403) (removed the dump),
[Sprint 134 report](../../ai-sprints/134/90-sprint-report.md) TD-4

## Goals

During PYPOST-403 housekeeping, an ~86 MB ELF `core` file was deleted from the repository root.
The team needs a documented root-cause analysis so maintainers understand whether an application
defect remains, and how to avoid leaving crash artifacts in the working tree again.

## Programming Language

Python 3.11+ (PySide6). Investigation is documentation-only; no production code changes expected
unless a reproducible defect is found.

## User Stories

- As a **maintainer**, I want a written investigation of the deleted `core` dump so I know
  whether follow-up code fixes are required.
- As a **developer running Qt tests locally**, I want guidance on headless Qt setup and what to
  do if a native crash produces a `core` file.
- As a **reviewer**, I want the investigation linked from developer docs so future segfaults are
  triaged consistently.

## Definition of Done

- [x] Investigation report documents evidence gathered (file metadata, git history, test runs).
- [x] Root cause is classified: reproduced defect, unreproducible native crash, or inconclusive
  with ranked hypotheses.
- [x] Reproduction steps are documented (or explicitly marked not reproducible on current HEAD).
- [x] Preventive measures already in place (`.gitignore`, offscreen Qt) are recorded.
- [x] Developer documentation updated with troubleshooting for ELF core dumps during Qt tests.
- [x] No open **blocker** tech debt remains for closing the ticket.

## Task Description

PYPOST-403 removed an 86 MB ELF crash dump from the repo root and added `/core` / `/core.*` to
`.gitignore`. PYPOST-403 requirements attributed the dump to a prior manual `pytest` run against
`tests/test_tabs_presenter.py`. The underlying native crash was not diagnosed at that time.

This debt ticket closes that gap: investigate, document findings, and update dev docs. A code fix
is in scope only if a reproducible application bug is identified.

## Q&A

- **Was the dump ever committed?**
  Git history shows no commit that added `core`; it was a local working-tree artifact removed in
  the PYPOST-403 commit.
- **Is a code fix required?**
  Only if investigation reproduces a defect on current HEAD. Otherwise document as unreproducible
  native crash with preventive guidance.
