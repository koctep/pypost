# PYPOST-770: Link root README to dev docs

## Goals

Close documentation audit finding **R-P2-004 (D-008)** from PYPOST-690: the root README
`## Development` section lists Make targets but does not point contributors to the developer
documentation hub at `doc/dev/README.md`.

## User Stories

- As a **new contributor**, I want the root README to link to developer documentation, so I can
  find setup, architecture, and capability docs without searching the repo.
- As a **maintainer**, I want a single obvious entry point from the project README, so onboarding
  paths stay consistent with the documentation audit recommendations.

## Definition of Done

- [x] Root `README.md` `## Development` section includes a bullet linking to `doc/dev/README.md`.
- [x] Link text clearly indicates developer documentation (not user-facing `doc/` guides).
- [x] `make check` passes.

## Task Description

**Problem:** Root README lacks a dev doc pointer (R-P2-004).

**Business intent:** Reduce onboarding friction by surfacing the existing developer documentation
index from the primary project README.

**Source:** PYPOST-690 — R-P2-004.

**Scope:** Root `README.md` Development section only. No changes to `doc/dev/README.md` TOC or
content.

## Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-1 | `README.md` contains a markdown link to `doc/dev/README.md` under `## Development` |
| AC-2 | Link appears alongside existing Make command bullets |
| AC-3 | No regression in `make check` |
