# PYPOST-146: Single Jinja2 Environment for performance

## Goals

Close the PYPOST-18 technical-debt item **Shared Jinja2 Environment**. Confirm that
`TemplateService` already centralizes one `jinja2.Environment` per instance and that production
code no longer creates redundant `Environment` or ad-hoc `Template` objects as the old
`TemplateEngine` did.

## User Stories

- As a **maintainer**, I want evidence that runtime template rendering reuses one Jinja2
  `Environment`, so we avoid redundant object construction on every request field.
- As a **developer**, I want documented guidance on Jinja2 caching behavior (`from_string` vs
  `get_template`) and when further optimization (PYPOST-148) might apply.
- As a **reviewer**, I want a regression test that `render_string` and `parse` share the same
  env instance on a given `TemplateService`.

## Definition of Done

- [x] Audit confirms `TemplateService.__init__` creates exactly one `jinja2.Environment` stored
  on `self.env`.
- [x] Audit confirms `render_string` and `parse` both use `self.env` (not ad-hoc environments).
- [x] Grep audit: no production `jinja2.Environment()` outside `template_service.py`.
- [x] Production composition root (`main.py`) constructs one shared `TemplateService` instance.
- [x] Developer documentation records the performance verdict and deferral of template compile
  cache (PYPOST-148 / PYPOST-455).
- [x] Unit test guards shared env identity; full test suite passes.

## Task Description

**Origin:** `ai-tasks/PYPOST-18/40-tech-debt.md` — performance concern about shared Jinja2
`Environment`.

**Scope:** Verification audit, one focused unit test, documentation update. No new caching layer
unless audit finds duplicate environments (it does not).

### In Scope

- Code audit of `TemplateService` and Jinja2 usage in production modules
- Cross-reference to PYPOST-18, PYPOST-134, PYPOST-455, PYPOST-148
- `doc/dev/template_service.md` update

### Out of Scope

- Implementing `lru_cache` or Jinja2 compiled-template cache (PYPOST-148)
- Refactoring hover module-level `TemplateService` (documented exception, PYPOST-134)
- Dependency-injection cleanup for fallback constructors (PYPOST-45)

## Main entities (business view)

- **Template service** — owns Jinja2 configuration and renders or parses `{{...}}` placeholders.
- **Jinja2 environment** — long-lived object holding filters, globals, and optional compile cache.
- **Request pipeline** — HTTP/MCP/cURL/masking paths that call the template service at runtime.

## Q&A

| Question | Answer |
| --- | --- |
| Does one Environment improve performance today? | Yes — avoids per-call `Environment()`/`Template()` construction from the old path; compile cache for `from_string` is not enabled by default (see PYPOST-455). |
| Is further caching needed now? | No — PYPOST-455 benchmark showed network I/O dominates; defer to PYPOST-148 if profiling changes. |
| Are there multiple envs in production? | One per injected `TemplateService`; hover uses a separate module instance (UI-only, documented). |
