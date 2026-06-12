# PYPOST-148: Template compile cache for `from_string`

## Goals

PYPOST-18 noted that `Environment.from_string` recompiles on every call. Maintainers need a
decision: add a bounded compile cache to `TemplateService` now, or document why deferral remains
appropriate for the desktop client.

## User Stories

- As a **pypost user**, I want HTTP requests and hover previews to stay responsive when
  templates repeat across sends.
- As a **maintainer**, I want evidence that compile caching is needed before adding memory bounds,
  invalidation rules, and test burden.
- As a **maintainer**, I want a documented revisit path if profiling later shows slowdown.

## Definition of Done

- [x] `TemplateService` is audited for an existing bounded compile cache.
- [x] If no cache: benchmark evidence is cited and deferral is documented for developers.
- [x] Revisit criteria are recorded (hover lag, high render rates, large templates).
- [x] Guard tests for future cache behavior remain in place (`test_template_service_caching_eval.py`).
- [x] PYPOST-18 follow-up item is marked resolved.

## Task Description

**Problem:** Repeated identical template strings pay a compile cost on each `render_string` call
because Jinja2 does not cache `from_string` bytecode by default.

**Scope:** Audit current implementation; implement bounded cache **only if** profiling shows
user-visible slowdown; otherwise document deferral with benchmark reference from PYPOST-455.

**Out of scope:** Full rendered-output memoization; hover-path redesign; catalog changes.

**Constraints and assumptions:**

- Implementation language: **Python**.
- Shared `Environment` per `TemplateService` (PYPOST-146) is already in place.
- PYPOST-455 micro-benchmark exists (local, order-of-magnitude).

## Main entities (business view)

- **Template string** — user-authored field content with `{{ ... }}` placeholders.
- **Compile step** — Jinja2 parsing/compilation before variable substitution.
- **Render attempt** — one `render_string` pass (success, validation error, or fallback).

## Q&A

- **Q:** Must we add `lru_cache` in this task?
  **A:** Only if slowdown is observed. PYPOST-455 measured sub-millisecond render cost; network
  I/O dominates. Deferral is the correct outcome.
- **Q:** What if a cache is added later?
  **A:** Prefer bounded `lru_cache` on compile (`maxsize=256`); see PYPOST-455 Strategy A.
