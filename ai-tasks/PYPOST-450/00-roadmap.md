# Roadmap: PYPOST-450

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added first slice: allow-listed `urlencode` in template rendering with tests.
  - [x] Extended allow-list with `md5` and `base64`; added focused tests,
    including mixed function-placeholder usage.
  - [x] Enforced strict function-placeholder validation and added negative tests for
    malformed, nested, multi-arg, and unknown function variants.
  - [x] Added typed function-expression validation outcomes and tests for
    error-code mapping with backward-compatible rendering fallback.
  - [x] Added hover parity slice by resolving function expressions
    via runtime-compatible path and covering line/body hover contexts in tests.
  - [x] Closed table-cell hover parity for params/headers by resolving
    expressions in table widgets and adding focused tooltip tests.
  - [x] STEP 3 audit (2026-06-06): verified core split — `FunctionRegistry`,
    `FunctionExpressionResolver`, `ValidationResult`, `TemplateService` orchestration
    match architecture; catalog `urlencode`/`md5`/`base64` complete.
  - [x] STEP 3 audit: confirmed single-arg + nested chaining, multi-arg rejection,
    and invalid-expression fallback (original content) via resolver + render tests.
  - [x] STEP 3 audit: confirmed hover/runtime parity — `VariableHoverHelper` delegates
    to `render_string(..., render_path="hover")`; URL/body/table hover tests pass.
  - [x] STEP 3 audit: confirmed context coverage — runtime surfaces (URL, header/param
    keys and values, body) route through `HTTPClient` → `render_string`; hover surfaces
    covered by line-edit, body-editor, and table-widget tests; no code gaps found.
  - [x] STEP 3 audit: ran targeted suite — 89 passed (39 subtests), 0 failed.
  - [x] STEP 3 review fixes: HTTPClient integration tests for function expressions in URL,
    header value, param key/value, and invalid passthrough.
  - [x] STEP 3 review fixes: Jinja-negative security tests (`{{ db|md5 }}`,
    `{{ db.__class__ }}`) for validation + render fallback.
  - [x] STEP 3 review fixes: refreshed `60-tech-debt.md` for current module split.
- [x] **STEP 4: Code Cleanup**
  - [x] Simplified function-expression validation and hover resolution/mouse-move paths
    via helper extraction while keeping behavior unchanged.
  - [x] Ran flake8 7.3.0 on full PYPOST-450 scope (11 files); zero warnings/errors.
  - [x] Verified line length ≤ 100, no unused imports, debug prints, or dead code.
  - [x] Ran full PYPOST-450 test suite — 109 passed, 39 subtests, 0 failed.
  - [x] Updated `40-code-cleanup.md` with current cleanup report.
- [x] **STEP 5: Observability**
  - [x] Audited runtime and hover observability paths after module split
    (`FunctionRegistry`, `FunctionExpressionResolver`, `TemplateService`).
  - [x] Confirmed logging/metrics in `TemplateService`; no raw content logged.
  - [x] Confirmed metrics wiring: `main.py` → runtime; `RequestWidget` → hover via
    `VariableHoverHelper.set_metrics`.
  - [x] Ran observability tests — 12 passed, 2 subtests, 0 failed.
  - [x] Updated `50-observability.md` with audit results and validation output.
- [x] **STEP 6: Review and Technical Debt**
  - [x] Cross-checked implementation against DoD (9 criteria) — functionally complete.
  - [x] Audited shortcuts, code quality, missing tests, and performance across core modules
    and PYPOST-450 test suite.
  - [x] Marked resolved debt from PYPOST-451/452/453/454 and STEP 3 review fixes.
  - [x] Linked open follow-ups: PYPOST-455, 457, 460, 461 (456, 459 completed in Jira).
  - [x] Ran full PYPOST-450 test suite — 109 passed, 39 subtests, 0 failed.
  - [x] Updated `60-tech-debt.md` with functional completeness table and STEP 6 validation.
  - [x] Applied STEP 6 review fixes (DoD #6/#7, hover regex, warning count, Jira status).
- [x] **STEP 7: Dev Docs**
  - [x] Audited `doc/dev/template_expression_functions.md` against module split and
    current implementation (`FunctionRegistry`, `FunctionExpressionResolver`,
    `TemplateService`, `VariableHoverHelper`).
  - [x] Added context coverage matrix, invalid fallback flow, and security section.
  - [x] Documented HTTPClient integration test coverage and optional gaps from STEP 6
    tech debt.
  - [x] Synced observability metrics, orchestration stages (PYPOST-459), and known
    follow-ups (PYPOST-455, 457, 460, 461).
  - [x] Verified `doc/dev/README.md` index link to `template_expression_functions.md`.
  - [x] Applied STEP 7 review fixes (diagnostics table, fallback flow pseudocode).
  - [x] User review and approval received.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

## Implementation Context

- Programming language: `Python`

### STEP 1: Requirements

- `ai-tasks/PYPOST-450/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-450/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-450/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-450/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-450/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/`

## Branch Recommendation

- `feature/PYPOST-450-template-function-expressions`
