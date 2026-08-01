# PYPOST-966: Post-install pypost import in slow smoke

## Goals

Slow Makefile install smoke (PYPOST-559) verifies `make install` in an isolated workspace
and runs a lightweight post-install import sanity check. PYPOST-943 restored the seed
contract but kept the PYPOST-559 **pydantic-only** check to avoid Qt/system dependencies.
Maintainers still want confidence that the **installed `pypost` package** is importable after
install — without importing UI/Qt modules.

**Business need:** Tighten FR3 (installed environment usability) by asserting package
importability via a version-module read, complementing the existing pydantic dependency check.

**Parent:** [PYPOST-943](https://pypost.atlassian.net/browse/PYPOST-943) TD-4.

## Programming Language

Python (pytest test helpers). Developer documentation in English Markdown.

## User Stories

- As a **maintainer**, I want slow smoke to verify the installed `pypost` package is
  importable so broken packaging or missing version modules fail before release.
- As a **reviewer**, I want post-install checks to stay free of Qt/UI imports so the slow
  job does not require GUI runtime for this assertion path.
- As a **developer**, I want a fast contract guard so post-install snippet policy cannot
  regress without a default-matrix failure.

## Definition of Done

- [x] Slow smoke runs a post-install check that reads `pypost.version.__version__` (or
  equivalent) after successful `make install`.
- [x] Post-install check does not import Qt/UI subpackages.
- [x] Fast contract test asserts `POST_INSTALL_SANITY_SNIPPETS` includes a pypost check.
- [x] Existing pydantic post-install check preserved (PYPOST-559).
- [x] Unticketed follow-ups (if any) live only in `60-tech-debt.md`.

## Task Description

### Problem

`TestSlowInstallSmoke` asserts `import pydantic` in the installed venv but never verifies
that the `pypost` package itself is on `PYTHONPATH` and importable. A broken editable/install
layout could still pass if dependencies install correctly.

### In Scope

- Add pypost version-module read to slow smoke post-install sanity.
- Extract shared snippet list + helper for slow smoke and fast contract guard.
- Document post-install sanity in `doc/dev/testing.md`.

### Out of Scope

- Importing full application subpackages (`pypost.ui`, `pypost.core.qt`, etc.).
- Changing slow smoke seed policy (PYPOST-963/964/965).
- Jira ticket creation or git commit in this run.

## Functional Requirements

- FR1: After `make install` succeeds in the slow smoke workspace, assert
  `pypost.version.__version__` is readable in the installed venv.
- FR2: Preserve existing pydantic import sanity (PYPOST-559).
- FR3: Fast contract test fails if pypost post-install check is removed from snippets.
- FR4: No new Qt/system dependency for the post-install assertion path.

## Non-Functional Requirements

- NFR1: Per-test timeouts unchanged for slow smoke (`@pytest.mark.timeout(180)`).
- NFR2: Isolated workspace pattern preserved — no repo `.venv` mutation.
- NFR3: Line length ≤ 100 characters in changed files.

## Constraints and Assumptions

- Slow smoke seed uses a stub `pypost/` tree with `version.py` copied from repo
  (PYPOST-963/943) — sufficient for version-module read.
- Empty `pypost/__init__.py` stub means version-module import avoids UI subpackages today;
  if `__init__.py` gains eager imports later, revisit snippet strategy (see 60-tech-debt).
