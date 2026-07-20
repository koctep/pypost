# PYPOST-821: Add smoke test for dark-theme tab close icon contrast

## Goals

After PYPOST-796 lightened the default tab close icon for dark native tab chrome, there was
no automated guard that the improved contrast contract remains in place. Maintainers need a
fast smoke check under `make test` so a regression to the old low-contrast default cannot
land unnoticed.

**Business intent:** Protect accessibility of the tab close control in dark appearance by
locking the post-PYPOST-796 visual contract in CI, without requiring manual macOS dark-mode
pixel inspection for every change.

## Programming Language

Python (existing PyPost test suite / pytest).

## User Stories

- As a **maintainer**, I want an automated check that the default tab close asset still meets
  the dark-theme contrast contract from PYPOST-796, so regressions are caught by `make test`.
- As a **contributor**, I want the expected asset or behaviour documented briefly next to the
  check, so I know why the assertion exists and what not to revert.
- As a **user** on dark tab chrome, I want confidence that the visible default close icon
  remains the shipped, improved asset rather than the older hard-to-see colour.

## Definition of Done

- An automated check covers the dark-theme tab close asset or contrast contract.
- Expected asset/behaviour is documented briefly in the test or a nearby comment.
- The check runs under `make test` and passes.
- Prefer a static asset/path (or equivalent contract) assertion over pixel contrast when
  pixel measurement is impractical in offscreen CI.
- Prefer extending `tests/test_tab_layout_regression.py`; production code only if a bug is
  found.

## Task Description

**Problem:** PYPOST-796 fixed default `close.svg` contrast for dark tab chrome, but
PYPOST-796 tech debt noted that the stroke colour itself was not covered by automation.
Manual dark-mode verification does not scale.

**Why now:** Explicit follow-up smoke test after the asset fix; labels include macos, tabs,
testing, ui.

### Functional requirements

- Add a smoke/regression check for the dark-theme default close-icon contrast contract.
- Document the expected asset or behaviour in or beside the test.
- Keep coverage discoverable next to existing tab layout regression tests.

### Non-functional requirements

- Must run reliably under CI / offscreen Qt (no fragile pixel screenshots required).
- Must not slow the suite materially.
- Explicit pytest timeout markers per project testing rules.

### Constraints and assumptions

- Scope is **test (and docs if needed)** — not redesigning icons or theme pipelines.
- Static asset/path assertions are preferred over WCAG pixel math.
- Related: PYPOST-796 close.svg contrast; see `ai-tasks/PYPOST-796/` and
  `tests/test_tab_layout_regression.py`.

### In scope

- Smoke test for default close-icon dark-theme contrast contract.
- Brief documentation in test comment and/or `doc/dev` as needed.

### Out of scope

- Theme-specific runtime icon variants.
- Pixel-diff / screenshot visual regression harness.
- Changing hover icon or QSS tab geometry policy.

### Main entities (business perspective)

| Entity | Role |
| --- | --- |
| Default tab close icon | User-visible control on closable tabs; must stay discernible on dark chrome |
| Dark-theme contrast contract | Post-PYPOST-796 expectation for default close visibility |
| Smoke test | Automated guard under `make test` |

## Q&A

| Question | Answer |
| --- | --- |
| Why not pixel contrast in CI? | Offscreen Qt and headless macOS CI cannot reliably render native dark tab chrome; static asset/path contract is the practical acceptance path. |
| Why after PYPOST-796? | That task fixed the asset; this task locks the contract so the fix cannot regress silently. |
| Production changes? | Only if the smoke test reveals a real bug in the shipped asset or wiring. |
