# PYPOST-795: Evaluate PyPostStyle.set_close_button_size API — document or remove

## Goals

PYPOST-792 removed a global 48px close-indicator override that drew close buttons over request
tab titles on macOS. The fix kept `PyPostStyle.set_close_button_size` as an opt-in API, but no
production code calls it. Maintainers need a clear decision: either document when deliberate
override is appropriate, or remove dead API surface that adds confusion.

**Business intent:** Reduce ambiguity for future UI changes — developers should know whether the
method is supported policy or legacy dead code, without risking a repeat of the tab-overlap
regression.

## Programming Language

Python (existing PyPost desktop application codebase).

## User Stories

- As a **maintainer**, I want a documented policy for tab close-indicator sizing, so that I do
  not reintroduce global overrides that break tab layout.
- As a **developer**, I want to know whether `set_close_button_size` is intentional API or
  removable dead code, so that refactors do not guess wrong.
- As a **PyPost user**, I want native tab chrome and correctly placed close buttons on macOS
  (PYPOST-792 outcome preserved), regardless of how this API is documented or removed.

## Definition of Done

- **Decision recorded:** Either (a) keep API with explicit documented use cases, or (b) remove
  API and update tests/docs accordingly.
- **No production regression:** `system` theme continues to use native
  `PM_TabCloseIndicator*` metrics; tab layout regression tests pass.
- **Developer documentation** reflects the decision in `doc/dev/ui_font_and_styles.md`.
- **`make check`** passes.

## Task Description

**Problem:** `PyPostStyle.set_close_button_size` has no production callers after PYPOST-792.
It was intentionally retained as an opt-in escape hatch but lacks a clear, discoverable use-case
statement beyond inline comments.

**Scope:** Evaluate `custom_style.py`, `doc/dev/ui_font_and_styles.md`, and
`tests/test_tab_layout_regression.py`. Make and implement one decision — document or remove.

**Out of scope:** Changing default tab metrics, QSS tab rules, close-icon contrast (PYPOST-796),
or appearance pipeline ownership (PYPOST-793).

### Functional requirements

- Audit all references to `set_close_button_size` (production, tests, docs).
- Choose document-or-remove based on whether a legitimate override scenario remains.
- If documenting: state when to call, when not to call, and that production leaves default `None`.
- If removing: delete method and attribute override path; adjust tests to match.

### Non-functional requirements

- No user-visible tab layout regression.
- Minimal diff — this is evaluation and documentation debt, not a feature.

### Constraints and assumptions

- PYPOST-792 established native-metrics-by-default policy; this task must not weaken it.
- Regression tests in `test_tab_layout_regression.py` are authoritative for close-indicator
  behaviour.

## Q&A

- **Q**: Why not remove unused API?
- **A**: Opt-in override remains valuable for platform-specific fixes, accessibility hit targets,
  and regression tests that prove override is explicit — cost of keeping is low; removal loses
  escape hatch without simplifying production paths.

- **Q**: Source references?
- **A**: Jira [PYPOST-795](https://pypost.atlassian.net/browse/PYPOST-795); parent
  [PYPOST-792](https://pypost.atlassian.net/browse/PYPOST-792) tech-debt item;
  `ai-tasks/PYPOST-793/60-tech-debt.md`.
