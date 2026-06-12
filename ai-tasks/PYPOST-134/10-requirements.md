# PYPOST-134: Verify variable substitution centralization

## Goals

Close the PYPOST-15 technical-debt item **Consider moving variable substitution logic to a common
`TemplateEngine`**. Determine whether a migration is still needed or whether prior work already
centralized substitution so maintainers can stop tracking this debt.

## User Stories

- As a **maintainer**, I want a single authoritative service for request-time variable
  substitution, so behavior stays consistent across HTTP, MCP, cURL, and masking paths.
- As a **maintainer**, I want documented evidence of which components call the central service,
  so future refactors do not reintroduce ad-hoc Jinja2 usage.
- As a **developer**, I want clarity on intentional exceptions (hover preview), so plain-variable
  chain resolution is not mistaken for duplicated runtime substitution.

## Definition of Done

- [x] Audit confirms `TemplateService` is the sole runtime substitution entry point.
- [x] `TemplateEngine` removal (PYPOST-18) is traced and no duplicate `Environment()` render
  paths remain outside `TemplateService`.
- [x] Hover preview exception (`VariableHoverResolver` plain chains) is documented as
  intentional, not debt.
- [x] Developer documentation records the consumer matrix and verdict.
- [x] Full test suite passes (no regression from verification work).

## Task Description

**Origin:** `ai-tasks/PYPOST-15/40-tech-debt.md` — suggested moving substitution to a common
`TemplateEngine`.

**Scope:** Verification audit, documentation, close with evidence. No migration unless audit
finds duplicate runtime render paths.

### In Scope

- Codebase audit of substitution call sites
- Cross-reference to PYPOST-18, PYPOST-129, PYPOST-450+
- `doc/dev` update with centralization map

### Out of Scope

- Merging hover plain-chain logic into `TemplateService`
- New substitution features or function catalog changes
- Dependency-injection refactors (PYPOST-45)

## Main entities (business view)

- **Template service** — central place that turns `{{...}}` placeholders into rendered values at
  execution time.
- **Request surfaces** — URL, headers, params, body fields that contain placeholders.
- **Hover preview** — UI-only resolution for tooltips (may differ from runtime for plain chains).

## Q&A

| Question | Answer |
| --- | --- |
| Was `TemplateEngine` already removed? | Yes — PYPOST-18 replaced it with `TemplateService`; `template_engine.py` no longer exists. |
| Does hover duplicate runtime substitution? | Function expressions delegate to `TemplateService`; plain `{{name}}` chains use hover-specific chain/cycle logic (PYPOST-129) by design. |
| Is further migration required? | No — audit shows all runtime paths use `TemplateService.render_string` or `parse`. |
