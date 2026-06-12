# PYPOST-249: StateManager design — document or improve granular updates

## Goals

Close the follow-up debt from PYPOST-29: clarify whether `StateManager` should remain a thin
wrapper around a shared `AppSettings` object or be refactored. Developers need a clear contract
for which settings fields are UI-session state vs user preferences, and how persistence works.

## User Stories

- As a **maintainer**, I want documented ownership of settings fields so I know whether to route
  changes through `StateManager` or `ConfigManager`.
- As a **developer**, I want the shared mutable `AppSettings` pattern explained so refactors do
  not accidentally break Settings dialog or UI state persistence.
- As a **reviewer**, I want a pragmatic decision recorded: document the current design or apply a
  small improvement only when clearly beneficial — no large rewrite.

## Definition of Done

- [x] Current `StateManager` role verified against codebase (fields, save paths, MainWindow wiring).
- [x] Design contract documented for maintainers (`doc/dev/state_manager.md` + module docstring).
- [x] Explicit list of UI-state fields managed by `StateManager`.
- [x] Decision recorded: full settings JSON rewrite on save is acceptable; granular *in-memory*
      updates via `set_*` with change detection are sufficient.
- [x] No breaking API changes; existing tests continue to pass.
- [x] Top-down artifacts stored under `ai-tasks/PYPOST-249/`.

## Task Description

**Source:** `ai-tasks/PYPOST-29/40-tech-debt.md` — follow-up
[PYPOST-249](https://pypost.atlassian.net/browse/PYPOST-249).

**Original concern:** `StateManager` is a thin wrapper around `ConfigManager`'s loaded settings
object; it assumes `settings` is mutable and shared. A more robust approach might be separate
ownership or granular disk updates.

**Pragmatic scope:** Verify the current design is intentional and adequate (debounced UI saves
added in PYPOST-386; unit tests in PYPOST-252). Document boundaries. Defer partial JSON writes
or split settings models unless a measured problem appears.

**Out of scope:** Splitting `AppSettings` into separate models, partial file updates, presenter
refactors, new pytest infrastructure.

## Q&A

| Question | Answer |
| --- | --- |
| Is shared `AppSettings` a bug? | No — `MainWindow` and presenters read preference fields from the same object; UI state fields use `StateManager.set_*`. |
| Are granular updates needed on disk? | Not for current `settings.json` size; in-memory change detection + debounced full save is sufficient. |
| Should Settings dialog use StateManager? | No — user preferences save immediately via `ConfigManager` (unchanged since PYPOST-386). |
