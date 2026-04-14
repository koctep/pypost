# PYPOST-451: Technical Debt Analysis

**Jira tasks created from this analysis** (descriptions link back to this file):

- [PYPOST-456](https://pypost.atlassian.net/browse/PYPOST-456) — update
  `doc/dev/template_expression_functions.md` for `FunctionRegistry` (STEP 7 doc debt).
- [PYPOST-457](https://pypost.atlassian.net/browse/PYPOST-457) — add explicit test that
  catalog allow-list matches Jinja `env.globals` for registered functions.
- [PYPOST-458](https://pypost.atlassian.net/browse/PYPOST-458) — trim `FunctionRegistry`
  / `register_into_env` docstring overlap.

## Shortcuts Taken

- **Intentional scope limits (not hacks):** Parsing, arity/nested rules, and validation
  orchestration remain in `TemplateService` per plan; only the catalog moved to
  `FunctionRegistry` ([PYPOST-452](https://pypost.atlassian.net/browse/PYPOST-452) owns
  resolver extraction).
- **`TemplateService` always builds a default `FunctionRegistry()`** in `__init__`; there
  is no public hook to inject an alternate registry for tests or product policy. That
  matches the architecture note to defer optional injection until needed.
- **Backward-compatible render fallback** (return original content on render failures
  after validation) is unchanged from prior behavior; not new debt for this ticket.

Overall: no temporary “crutches” were added to ship the registry split; remaining
shortcuts are the agreed follow-on work items below.

## Code Quality Issues

- **`TemplateService` remains a large orchestration type** (validation, render, metrics,
  logging). PYPOST-451 reduced allow-list duplication but did not split the resolver;
  coupling is lower for the catalog only.
- **Slight docstring overlap** between `FunctionRegistry` and `register_into_env` was
  noted in `40-code-cleanup.md`; track cleanup in
  [PYPOST-458](https://pypost.atlassian.net/browse/PYPOST-458).
- **`FunctionRegistry` keeps a mutable `dict` copy of the catalog** while
  `allowed_names` is a `frozenset` fixed at `__init__`. Today nothing mutates `_functions`
  after construction; if dynamic registration is added later, `allowed_names` and
  `is_allowed` must stay consistent (or the type should be refrozen explicitly).

None of these are release blockers for the registry extraction itself.

## Missing Tests

- **Alternate catalog / injection:** No test proves a custom registry instance wired into
  `TemplateService`, because the constructor does not accept one; debt is low until that
  API exists.
- **Parity assertion “validation allow-list matches `env.globals`”** is implied by
  integration tests (render + validation) and `register_into_env` unit tests, not by a
  single explicit cross-check test; follow up in
  [PYPOST-457](https://pypost.atlassian.net/browse/PYPOST-457).
- **Deeper expression edge cases** (unbalanced nesting, whitespace variants everywhere) are
  still the intended scope of
  [PYPOST-454](https://pypost.atlassian.net/browse/PYPOST-454); PYPOST-451 did not expand
  that matrix.

For this ticket, coverage is **adequate**: dedicated `tests/test_function_registry.py`
plus existing `TestTemplateService*` cases for golden renders, `unknown_function`, and
observability.

## Performance Concerns

- **No new hot-path costs** specific to PYPOST-451: allow-list checks are still O(1) name
  lookups (dict membership vs former set).
- **Pre-existing pattern unchanged:** `re.findall` for placeholders, validate-then-render,
  and no template cache—same trade-offs as documented under
  [PYPOST-450](https://pypost.atlassian.net/browse/PYPOST-450) /
  [PYPOST-455](https://pypost.atlassian.net/browse/PYPOST-455) if expression-heavy
  workloads appear.

## Follow-up Tasks

- [**PYPOST-452**](https://pypost.atlassian.net/browse/PYPOST-452): Introduce
  `FunctionExpressionResolver` (or equivalent) and migrate parsing/validation out of
  `TemplateService`; consume `FunctionRegistry.get()` from the stable catalog API.
- [**PYPOST-453**](https://pypost.atlassian.net/browse/PYPOST-453): Resolve nested-call
  policy vs architecture, then enforce with explicit rules and tests.
- [**PYPOST-454**](https://pypost.atlassian.net/browse/PYPOST-454): Add edge-case tests
  (malformed nesting, spacing variants, hover/runtime parity) called out in PYPOST-450
  debt.
- [**PYPOST-455**](https://pypost.atlassian.net/browse/PYPOST-455): Revisit caching /
  profiling for repeated template renders if metrics justify it.
- [**PYPOST-456**](https://pypost.atlassian.net/browse/PYPOST-456): Dev doc refresh for
  `FunctionRegistry` / `template_expression_functions.md` (from this debt file).
- [**PYPOST-457**](https://pypost.atlassian.net/browse/PYPOST-457): Explicit test for
  allow-list vs `env.globals` parity.
- [**PYPOST-458**](https://pypost.atlassian.net/browse/PYPOST-458): Docstring cleanup on
  `FunctionRegistry` / `register_into_env`.
- **STEP 7 (this epic):** Same doc work as
  [PYPOST-456](https://pypost.atlassian.net/browse/PYPOST-456) (roadmap reminder).

**Release stance:** No technical debt from this change set is treated as a merge or
release blocker; remaining items are tracked as structured follow-ups.
