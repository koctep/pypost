# PYPOST-692: Move StyleManager out of core

## Goals

PyPost documents a clear separation between **core business logic** and **presentation**
(user interface). The PYPOST-684 architecture audit found that appearance management — themes,
global stylesheets, and related visual settings — currently lives in the core package while
depending on presentation-layer types at runtime. That is the only confirmed case where core
imports from the UI layer outside type-checking guards.

This inversion weakens the intended package boundaries: maintainers cannot treat core as
independent of the UI, tests and tooling that assume one-way dependencies are harder to trust,
and future changes increase the risk of circular coupling between layers. Remediating
R-P1-001 restores alignment between documented architecture and actual dependency direction,
so structural debt from the audit can be closed before larger boundary refactors (for example
broader Qt usage in core, tracked separately).

**Business intent:** Keep the codebase evolvable and predictable — appearance behavior stays
the same for users, while developers regain a enforceable core-vs-UI boundary for this
capability.

## Programming Language

Python (existing PyPost desktop application codebase).

## User Stories

- As a **maintainer**, I want appearance management to respect documented layer rules so that
  changes to UI styling do not pull core into presentation concerns and vice versa.
- As a **developer**, I want to import and reason about the core package without implicitly
  loading UI modules for style management, so that unit tests and future headless scenarios
  are not blocked by this coupling.
- As a **reviewer**, I want the PYPOST-684 P1 finding D-001 / L-004 (R-P1-001) resolved so
  that pull requests no longer carry a known, documented boundary violation for style code.
- As a **PyPost user**, I want theme selection (system, light, dark), global font size, and
  application styling to behave exactly as today when I change Settings or restart the app,
  so that this structural fix does not change what I see or how the app feels.

## Definition of Done

- The runtime dependency from core to the UI package for appearance management is eliminated
  (no core module imports from `pypost.ui` for this concern).
- All user-facing appearance behavior is unchanged:
  - Theme options **system**, **light**, and **dark** apply correctly on startup and after
    saving Settings.
  - Global font size from Settings applies across the application after save and on restart.
  - Bundled application stylesheets continue to load and apply (including icon path
    substitution and deterministic ordering of style sources).
  - Invalid or unknown theme values fall back to safe default behavior consistent with today.
- `MainWindow` (or its equivalent settings application path) still applies appearance when
  settings are loaded or updated — no regression in when or how often styling is refreshed.
- Existing automated tests that cover `StyleManager` themes, font injection, and related
  appearance flows pass without weakening assertions.
- `make check` passes.
- Architecture documentation that currently calls out this exception (`doc/dev/architecture.md`,
  `doc/dev/architecture_audit.md`) can be updated in a follow-up step to reflect the remediated
  boundary; this task’s acceptance is the behavioral and dependency outcome, not doc edits in
  Step 1.

## Task Description

**Problem:** PYPOST-684 identified recommendation **R-P1-001** (findings **D-001**, **L-004**):
appearance management is implemented in core but depends on presentation-layer styling at
import/runtime. That violates the project’s stated rule that core depends on models only and UI
depends on core — not the reverse.

**Why now:** R-P1-001 is prioritized P1 (high) tech debt from the audit. Leaving it open
undermines trust in layer rules and blocks closing the audit’s top dependency-direction finding
before other boundary work proceeds.

### Functional requirements

- Relocate or re-home **appearance management** (theme application, stylesheet loading and
  application, font-size rule injection for global QSS) so it no longer creates a core → UI
  runtime import.
- Preserve the full appearance pipeline triggered from application settings: theme, then
  global stylesheet (with optional font size), consistent with current product behavior
  documented for users and developers.
- Preserve structured logging behavior for style load and theme application (severity and
  intent of existing log events — no silent failure of user-visible styling).
- Update import sites and tests that reference the old module location so the application
  and test suite remain coherent.

### Non-functional requirements

- **No user-visible regression:** Visual parity with current production behavior on supported
  platforms; macOS native tab chrome and theme paths validated as part of regression checks.
- **Maintainability:** After remediation, a reader of package boundaries should not need an
  “exception” note for style management crossing from core into UI.
- **Testability:** Appearance tests should remain reliable in isolation and in the full suite
  (no new order-dependent failures introduced by the move).

### Constraints and assumptions

- Implementation language is Python; the app remains a PySide6 desktop client.
- Remediation scope is **R-P1-001 only** — the single confirmed core → UI runtime import for
  style management. Broader “Qt throughout core” (R-P1-002 / PYPOST-693) and duplicate style
  bootstrap in the entry point (R-P3-004 / PYPOST-702) are **out of scope** unless required
  as an unavoidable consequence of fixing R-P1-001; any such spillover should be minimal and
  tracked separately if not strictly necessary.
- No new themes, settings fields, or user-facing appearance options are in scope.
- Composition-root wiring (whether `StyleManager` is constructed in `main.py` vs `MainWindow`)
  is not a goal of this task unless needed to satisfy the boundary fix without behavior change.

### In scope

- Eliminating the core → UI runtime dependency for appearance management (R-P1-001).
- Preserving current theme, QSS, and font-size behavior end-to-end.
- Adjusting tests and imports affected by the move.

### Out of scope

- Resolving all PySide6 usage in core (PYPOST-693).
- Consolidating duplicate `PyPostStyle` installation at application startup (PYPOST-702).
- Moving other services (`StorageManager`, `RequestManager`, etc.) into the composition root.
- New appearance features, redesign of Settings UI, or changes to shipped `.qss` content
  except as required to keep behavior identical after the move.
- Performance optimization of style loading.

### Main entities (business perspective)

| Entity | Role |
|--------|------|
| Application appearance | The user-visible look-and-feel: theme (system/light/dark), global font size, and shared stylesheet rules. |
| Appearance settings | User preferences persisted in app configuration and applied on startup and when Settings are saved. |
| Style management capability | The component responsible for applying appearance settings to the running Qt application. |
| Core package | Business logic and services that should not depend on the presentation layer. |
| Presentation (UI) package | Windows, widgets, styles, and visual assets users interact with. |
| Architecture audit finding R-P1-001 | The tracked remediation item linking D-001 (dependency inversion) and L-004 (UI concern in core). |

## Q&A

- **Q**: Why is this a business requirement and not “just move a file”?
- **A**: The audit framed it as structural risk: violated boundaries make the codebase harder
  to test, review, and extend. The business outcome is **restored architectural integrity**
  without changing what users experience.

- **Q**: Must end users notice any difference?
- **A**: No. Acceptance is behavioral parity for themes, font size, and global styling.

- **Q**: Does this task choose between “move StyleManager to UI” vs “extract shared types”?
- **A**: No. Step 1 defines *what* must be true (no core → UI runtime dependency; behavior
  preserved). The *how* is decided in Step 2 (architecture).

- **Q**: Are documentation updates part of this task?
- **A**: Dev docs that mention the known exception should be updated when the implementation
  lands (Step 7). Requirements acceptance is the dependency and behavior outcome.

- **Q**: What if fixing the import requires touching `main.py` style bootstrap?
- **A**: Minimal, necessary touch points are allowed. Deliberate consolidation of startup
  style setup is PYPOST-702 and remains out of scope unless unavoidable for R-P1-001.

- **Q**: Source references?
- **A**: Jira [PYPOST-692](https://pypost.atlassian.net/browse/PYPOST-692); parent audit
  [PYPOST-684](https://pypost.atlassian.net/browse/PYPOST-684); finding detail in
  `ai-tasks/PYPOST-684/30-audit-report.md` and `ai-tasks/PYPOST-684/60-tech-debt.md`
  (R-P1-001).
