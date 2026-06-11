# PYPOST-455: Evaluate caching for repeated template renders

## Goals

Template fields are rendered on every HTTP request, hover preview, and masking pass. PYPOST-450
deferred caching until usage data was available. This task decides whether a lightweight cache
is warranted for the desktop client or should remain deferred.

## User Stories

- As a pypost user, I want request execution to stay responsive when sending HTTP requests with
  templated URLs, headers, params, and bodies.
- As a maintainer, I want an evidence-based decision on template render caching so we do not
  add complexity without measurable benefit.
- As a maintainer, I want existing observability metrics to inform the decision and remain the
  primary signal if render volume grows.

## Definition of Done

- Current render-path cost is measured or estimated with representative inputs.
- Caching options (compiled template, validation, full render) are compared with trade-offs.
- A clear recommendation is recorded: implement now, defer, or not needed.
- Existing `template_expression_render_attempts` metrics are mapped to decision criteria.
- Recommendation and rationale are documented for developers (`doc/dev`).
- No user-visible behavior change unless implementation is explicitly chosen (out of scope for
  deferral).

## Task Description

**Problem:** Each `render_string` call tokenizes, validates function expressions, compiles via
`Environment.from_string`, and renders. Identical template strings pay full cost on every call.

**Scope:** Evaluate cost, review observability, compare lightweight cache strategies, document
decision. Optional guard tests that capture properties required if caching is added later.

**Out of scope:** Production cache implementation, hover-path redesign, catalog changes.

**Constraints and assumptions:**

- Implementation language: **Python**.
- Desktop GUI client; typical request has modest template counts.
- PYPOST-460 already deduplicated tokenization (single scan per render).
- Shared `Environment` instance is long-lived per `TemplateService`.

## Main entities (business view)

- **Template field** — user-authored text with `{{ ... }}` placeholders.
- **Render attempt** — one substitution pass producing output or fallback content.
- **Render path** — caller context (`runtime`, `hover`, etc.) tracked in metrics.
- **Observability signal** — counters for success, validation errors, and render errors.

## Q&A

- **Q:** Should we cache full rendered output including variables?
  **A:** Out of scope for lightweight evaluation; variable values change per request. Focus on
  compile/validation reuse for identical template strings.
- **Q:** What triggers revisiting this decision?
  **A:** Sustained high `template_expression_render_attempts` rates, user-reported UI lag on
  hover, or templates with very large placeholder counts.
