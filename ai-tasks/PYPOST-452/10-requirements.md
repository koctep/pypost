# PYPOST-452: Separate validation of template function expressions

## Goals

Users and integrators depend on predictable template placeholders (plain variables and
allow-listed functions) across request fields. Today, checks that decide whether a
function-style placeholder is acceptable are interleaved with broader template handling,
which slows safe evolution of the feature and increases regression risk when extending
rules or the function catalog.

This task exists to **isolate the “is this function placeholder allowed?” concern** so
maintainers can change validation and rendering workflows independently, while **end users
see no behavior change** for supported and unsupported patterns compared to the current
release.

## User Stories

- **As a pypost user**, I want my existing valid placeholders (variables and supported
  single-function calls) to keep working everywhere they work today, so I do not have to
  rewrite saved requests.
- **As a pypost user**, I want unsupported or malformed function placeholders to behave
  the same as today (for example, no new hard failures where the product currently falls
  back or skips rendering), so my workflows stay stable.
- **As a maintainer or contributor**, I want a single, obvious place that answers whether
  a function-style placeholder complies with product rules (syntax, arity, catalog
  membership), so I can extend or tighten rules without untangling unrelated logic.
- **As a maintainer**, I want rendering orchestration to focus on executing valid templates,
  relying on a dedicated outcome from the function-placeholder checks, so responsibilities
  stay clear and testable.

## Definition of Done

- For the same inputs, **observable outcomes** for template rendering and validation
  (success, fallback, logging, and metrics hooks from a user or operator perspective) match
  pre-change behavior within the current product’s documented intent for function
  placeholders.
- Rules for **which function names are allowed**, **argument shape**, and **nested calls**
  (allowed or not) remain **consistent** with whatever the product currently enforces until
  a separate follow-up explicitly changes policy.
- The product exposes a **clear boundary**: one area owns interpretation and validation of
  function-style placeholders; another owns orchestration of rendering and related
  diagnostics. The split is reflected in **maintainer-facing structure** (code layout and
  ownership), not only in comments.
- Automated checks cover representative valid, invalid, and edge placeholder forms so
  regressions are caught early (exact suite scope to be agreed during design; this item is
  about **not losing** coverage relative to today).

## Task Description

**Problem:** Function placeholder acceptance is not separated cleanly from template
execution paths, making the feature harder to extend and review.

**Scope:** Introduce a dedicated responsibility for parsing and validating function-style
placeholders against the allow-listed catalog and syntax rules, and adjust the template
workflow so rendering uses the results of that responsibility. Out-of-scope: new
end-user-visible functions, UI changes, or policy changes unless they are strictly
required to preserve current behavior.

**Constraints and assumptions:**

- Implementation language: **Python** (pypost codebase).
- Work follows the prior sprint outcome that centralized the allow-listed catalog; this
  task builds on that without redefining business semantics of individual functions.
- Jira reference:
  [PYPOST-452](https://pypost.atlassian.net/browse/PYPOST-452) (follow-up from PYPOST-450
  technical-debt analysis).

## Main entities (business view)

- **Field value with placeholders** — text a user enters in headers, URLs, bodies, etc.
- **Placeholder token** — content inside `{{ ... }}` delimiters.
- **Function-style placeholder** — token shaped as a named call with arguments per
  product rules (not a bare variable name).
- **Catalog entry** — a named, allow-listed callable the product may expose in templates.
- **Validation outcome** — valid, or invalid with a reason code suitable for logging and
  metrics (not necessarily shown to the end user).

## Q&A

| Question | Answer |
|----------|--------|
| Why not bundle this with changing nested-call policy? | Policy alignment is tracked as a
separate follow-up so this change stays focused on structure and parity with current
behavior. |
| Who is the primary “customer” of this work? | Maintainers and contributors; end users
benefit indirectly through safer evolution and stable behavior. |
