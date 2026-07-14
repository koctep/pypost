# PYPOST-793: Centralize application appearance initialization under style management

## Goals

PyPost applies application appearance — theme, native look-and-feel policy, global styling
rules, and font size — through a multi-step pipeline that must stay consistent across startup
and whenever the user saves Settings. PYPOST-792 restored correct native tab layout on macOS by
aligning theme and styling policy in one place; follow-up analysis noted that **initial
appearance setup is still spread across more than one responsibility**, which creates drift
risk: a future change at one site can silently diverge from another and reintroduce layout or
styling regressions users already reported.

This task closes **R-P3-004** from the PYPOST-684 architecture audit (tracked originally as
PYPOST-702, with a narrower partial fix) by ensuring **one authoritative, style-management-owned
entry point** owns how the application receives its initial look-and-feel. Maintainers should
not need to update multiple call sites to keep startup appearance aligned with the policy
enforced when settings are applied.

**Business intent:** Reduce structural maintenance risk and protect the PYPOST-792 user-facing
fix — appearance behavior stays the same for users, while developers gain a single, obvious
place to reason about application appearance initialization.

## Programming Language

Python (existing PyPost desktop application codebase).

## User Stories

- As a **maintainer**, I want application appearance initialization to live in one
  authoritative place under style management, so that startup and settings-driven updates
  cannot drift apart and reintroduce tab-layout or theme regressions.
- As a **developer**, I want to change native look-and-feel policy or theme defaults in one
  location, so that I do not have to hunt for duplicate setup across application launch and
  the main window lifecycle.
- As a **reviewer**, I want the PYPOST-792 / PYPOST-684 follow-up on duplicated appearance
  bootstrapping resolved, so that pull requests no longer carry a known, documented
  duplication finding for initial appearance setup.
- As a **PyPost user**, I want theme selection (system, light, dark), global font size, and
  application styling to behave exactly as today on first launch and after saving Settings,
  so that this structural cleanup does not change what I see or how the app feels.

## Definition of Done

- **Single authoritative entry point:** Initial application appearance setup (theme and native
  look-and-feel policy reflected in saved settings) is owned by the style management
  capability — not duplicated or partially reimplemented elsewhere in the startup path.
- **No user-visible regression:** Visual and behavioral parity with current production on
  supported platforms, including:
  - Theme options **system**, **light**, and **dark** on first launch and after Settings save.
  - Global font size from Settings on startup and after save.
  - Bundled application stylesheets load and apply as today (icons render correctly, styling
    applies in a stable order, and repeated settings saves do not accumulate duplicate rules).
  - Native tab chrome and close-indicator sizing remain correct on macOS (PYPOST-792 acceptance
    criteria still met).
  - Invalid or unknown theme values fall back to safe default behavior consistent with today.
- **Settings refresh unchanged:** Saving Settings still reapplies appearance when preferences
  change; users see updates immediately without restart, as today.
- **Tests:** Existing automated tests covering themes, font size application, tab layout
  regression, and related appearance flows pass without weakening assertions; `make check`
  passes.
- **Documentation accuracy:** Developer documentation that describes the appearance startup
  pipeline reflects the consolidated ownership (may be completed in Step 7 if not required
  earlier to satisfy acceptance).

## Task Description

**Problem:** Application appearance initialization is not clearly centralized. Historical
startup code and style-management theme application both applied the same native look-and-feel
styling independently. A partial consolidation removed duplicate setup from the application
launch path, but **initial appearance is still orchestrated outside the style management
capability's single entry point**, and developer docs still describe the old two-location
model. That leaves maintainers with ambiguous ownership and ongoing drift risk called out in
PYPOST-792 technical-debt follow-up.

**Why now:** PYPOST-792 fixed a high-visibility macOS defect tied to inconsistent styling
policy. Leaving bootstrap duplication unresolved increases the chance that a well-intentioned
startup or theme change re-breaks tab layout or palette behavior. This is medium-priority
tech debt (Jira type: Debt) explicitly filed as the consolidation follow-up.

### Functional requirements

- Establish **one style-management-owned entry point** responsible for applying the full
  initial appearance pipeline according to persisted user settings (theme, global styling
  rules, application font size) when the application starts.
- **Eliminate redundant or parallel initial setup** of the same native look-and-feel styling
  policy anywhere else in the startup path.
- Preserve the **complete appearance pipeline** triggered from settings changes: theme, global
  styling rules (including font size), and application default font — same order and outcomes
  as today.
- Preserve structured logging behavior for style load and theme application (severity and
  intent of existing log events — no silent failure of user-visible styling).

### Non-functional requirements

- **No user-visible regression:** Visual parity on supported platforms; macOS native tab chrome
  validated as part of regression checks.
- **Maintainability:** After remediation, a reader can identify exactly where initial
  appearance is applied without cross-referencing multiple modules for the same policy.
- **Testability:** Appearance tests remain reliable in isolation and in the full suite.

### Constraints and assumptions

- Implementation language is Python; the app remains the existing PyPost desktop application.
- Scope is **consolidation of initial appearance bootstrap ownership** (R-P3-004 / PYPOST-792
  follow-up). No new themes, settings fields, or user-facing appearance options.
- **Out of scope:** Redesign of Settings UI, changes to shipped stylesheet content except as
  needed for behavioral parity, performance optimization of style loading, unrelated startup
  wiring refactors (other managers injected at application launch), and close-icon contrast
  polish (PYPOST-796).
- PYPOST-702 removed duplicate setup from the application launch path; this task completes the
  intended outcome by centralizing ownership under style management, not merely moving
  duplication to another caller.

### In scope

- Single authoritative initial appearance entry point under style management.
- Removing any remaining redundant initial native styling setup outside that entry point.
- Adjusting call sites and tests affected by the consolidation.
- Correcting inaccurate developer documentation of the startup appearance pipeline when
  required for acceptance.

### Out of scope

- New appearance features or visual redesign.
- Broader startup wiring of all managers at application launch.
- macOS close-icon contrast improvements (PYPOST-796).
- Makefile `help` target (PYPOST-794).

### Main entities (business perspective)

| Entity | Attributes | Role |
|--------|------------|------|
| Application appearance | theme (system/light/dark); global font size; shared styling rules; native look-and-feel policy | User-visible look-and-feel the user sees on launch and after saving Settings. |
| Appearance settings | theme preference; font size; persisted user configuration | User preferences applied on startup and when Settings are saved. |
| Style management capability | stylesheet loading; theme application; initial appearance setup ownership | Component responsible for applying appearance settings to the running application. |
| Application startup | launch timing; dependency on persisted settings; pre-interaction appearance | Phase when the desktop client launches, loads settings, and shows the main window with correct appearance. |
| Settings save flow | user save action; immediate refresh without restart | User action that updates preferences and refreshes appearance without requiring restart. |
| Architecture audit finding R-P3-004 | remediation scope (duplicate startup styling); linked follow-up (PYPOST-792) | Tracked remediation for duplicated native styling setup at application startup. |

## Q&A

- **Q**: Why is this needed if duplicate launch-path setup was already removed (PYPOST-702)?
- **A**: PYPOST-702 stopped applying native styling twice at launch, but initial appearance is
  still not owned by a single style-management entry point. The business goal is **complete
  consolidation of bootstrap ownership**, not only removing one duplicate call.

- **Q**: Must end users notice any difference?
- **A**: No. Acceptance is behavioral parity for themes, font size, global styling, and macOS
  tab layout (PYPOST-792).

- **Q**: Does the Jira description still match the codebase?
- **A**: Partially. The application launch path no longer applies native styling independently;
  the remaining gap is **centralized bootstrap ownership under style management** and outdated
  developer docs. Requirements reflect current state, not the original Jira wording alone.

- **Q**: Are documentation updates part of this task?
- **A**: Developer docs describing the startup pipeline must be accurate when the work is
  complete. Step 7 may carry detailed doc edits; requirements treat accuracy as an acceptance
  outcome.

- **Q**: Source references?
- **A**: Jira [PYPOST-793](https://pypost.atlassian.net/browse/PYPOST-793); parent
  [PYPOST-792](https://pypost.atlassian.net/browse/PYPOST-792) tech-debt follow-up; audit
  R-P3-004 in `ai-tasks/PYPOST-684/30-audit-report.md` and `ai-tasks/PYPOST-792/60-tech-debt.md`;
  partial prior work [PYPOST-702](https://pypost.atlassian.net/browse/PYPOST-702) (commit
  `bc72d91`).
