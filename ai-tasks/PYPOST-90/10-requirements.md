# PYPOST-90: Close debt — synchronous settings save on every click

## Goals

Collection tree expand/collapse and other high-frequency UI session changes must not write the
full settings file to disk on every single click. Rapid interaction should coalesce persistence
so the app stays responsive and avoids redundant I/O.

This debt item originated from [PYPOST-10](https://pypost.atlassian.net/browse/PYPOST-10) tech
debt analysis. The implementation was delivered in
[PYPOST-386](https://pypost.atlassian.net/browse/PYPOST-386); this task verifies and closes the
original debt ticket.

**Programming language:** Python (PySide6).

## User Stories

- As a user, I want to expand and collapse collections quickly without triggering a disk write
  on every click.
- As a user, I want my final tree expansion state to persist after restart or normal quit.
- As a maintainer, I want automated tests that prove debounced coalescing and flush-on-exit
  behavior.

## Definition of Done

1. Expand/collapse and other `StateManager`-managed UI fields use debounced persistence (not
   synchronous per click).
2. Pending UI state is flushed before application exit.
3. Existing unit tests cover debounce, coalescing, and timer-fired persistence.
4. Developer documentation describes save timing and links this debt closure.
5. Source tech-debt entry in PYPOST-10 updated to FIXED with cross-reference.

## Task Description

### Problem

Originally, each collection expand/collapse called immediate `ConfigManager.save_config`,
rewriting the entire settings JSON on every toggle. Very frequent clicking added unnecessary I/O.

### Scope

**In scope**

- Verification that tree expand/collapse uses debounced `StateManager` saves.
- Documentation and debt closure for the PYPOST-10 item.

**Out of scope**

- Environment selection saves in `EnvPresenter` (still immediate by design; separate concern).
- Settings dialog OK path (immediate save on explicit user confirm).
- Partial JSON writes or settings file format changes.

## Q&A

- **Q:** Was new code required? **A:** No — PYPOST-386 implemented 300 ms debounced saves in
  `StateManager`; PYPOST-252 added tests.
- **Q:** Why close PYPOST-90 instead of PYPOST-386? **A:** PYPOST-90 is the original debt
  ticket from PYPOST-10; PYPOST-386 was the implementation task.
