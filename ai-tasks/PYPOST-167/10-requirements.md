# PYPOST-167: MetricsManager global singleton DI

## Goals

PYPOST-23 identified that `MetricsManager` was accessed via a singleton pattern
(`MetricsManager()` returning a shared instance) throughout the codebase. Hidden global state
makes unit testing harder and violates dependency inversion. Maintainers need confirmation that
metrics dependencies are injected from a single composition root.

## User Stories

- As a **developer**, I want metrics tracking injected from `main.py` so I can substitute fakes
  in tests without patching globals.
- As a **reviewer**, I want no production module outside the composition root to call
  `MetricsManager()` directly, so dependency graphs stay explicit.
- As a **maintainer**, I want the PYPOST-23 tech-debt item closed with documented evidence when
  the singleton anti-pattern is already removed.

## Definition of Done

- [x] `MetricsManager` is a plain class — no singleton `__new__` or module-level instance.
- [x] `main.py` creates one `MetricsManager` and injects it into `MainWindow` and services.
- [x] No production module outside `main.py` calls `MetricsManager()`.
- [x] Tracking consumers type-hint `MetricsTrackerProtocol` (PYPOST-73) with `resolve_metrics`
  (PYPOST-74).
- [x] `make test` passes.
- [x] Developer docs note composition-root injection; PYPOST-23 singleton debt closed.

## Task Description

**Source:** [PYPOST-23](https://pypost.atlassian.net/browse/PYPOST-23) tech-debt — global
singleton usage in `RequestWidget`, `HTTPClient`, `MCPServerImpl`.

PYPOST-44 removed the singleton and refactored all inline call sites. This task verifies that
migration is complete or completes any remaining refactor.

**In scope:** Verification of DI pattern; documentation; close debt item.

**Out of scope:** Changing metric names, splitting the facade (PYPOST-49/75), or new protocols
beyond existing `MetricsTrackerProtocol`.

## Q&A

| Question | Answer |
| --- | --- |
| Was code change required? | No — PYPOST-44 removed singleton and inline call sites. |
| New tests needed? | No — existing protocol and manager tests cover compliance. |
