# PYPOST-1033: Technical Debt Analysis

**Verdict:** Small maintainability / coverage debt only. The grammar fix matches
architecture Option B (`_SAFE_PATH_RE`); R1–R3 and underscore-attribute locks
are green; timeout markers present; no new observability. **SAFE TO CLOSE** for
this story’s core DoD (path substitution + safety). Follow-ups below are
non-blocking; **do not create Jira issues in this step** (Phase D later).

Scope reviewed: `pypost/core/function_expression_resolver.py`,
`tests/test_function_expression_resolver.py`, `tests/test_template_service.py`,
`tests/test_mcp_server_integration.py`, and `ai-tasks/PYPOST-1033/*`.

## Shortcuts Taken

- **Broader safe dotted paths (Option B), not MCP-only allowlist** — Intentional
  architecture decision. Slightly wider than the jira-mcp bug surface; same
  segment rules as an MCP-only path would need. Not a crutch.
- **No soft max path depth** — Architecture left an optional depth cap (e.g. 8)
  as DoS hardening; not implemented. Segment character rules remain strict;
  practical product paths are shallow (`mcp.request.<param>`).
- **Automated R3 covers path only** — Integration repro asserts URL path
  substitution (`/issue/PROJ-1`). Query and body shapes used by
  `examples/collections/jira_mcp.json` rely on the same render path but are not
  separately locked end-to-end in this change (TD-1).
- **Dev docs deferred to Step 8** — Safe-path grammar and continued rejection of
  underscore attribute segments are not yet written into
  `doc/dev/template_expression_functions.md` / `doc/dev/template_service.md`
  (planned; not a Step 7 ticket).
- **Silent fail-closed fallback unchanged** — Invalid or missing expressions
  still return original content via `TemplateService` (pre-existing contract).
  Operators can still see unsubstituted `{{ ... }}` text without a hard error;
  this bug only stops *false* `invalid_syntax` for safe dotted paths.
- **No live jira-mcp smoke in CI** — Local stub HTTP + MCP harness covers the
  render contract; full example against 127.0.0.1:1080 / real Jira remains a
  manual DoD checklist item (secret-safe).

## Code Quality Issues

- **Minimal production change** — `_IDENTIFIER_RE` replaced by `_SAFE_PATH_RE`
  for plain expressions and function arguments; docstring updated. No MCP
  coupling in the resolver (matches architecture).
- **No named `_is_safe_variable_path` helper** — Architecture allowed either a
  helper or compiled regex; class-level `_SAFE_PATH_RE` is clear and sufficient.
- **Hover / `PLAIN_VARIABLE_PATTERN` still undotted** — Out of scope by design.
  Dotted MCP paths validate/render at runtime but hover plain-variable UX may
  still treat them as non-plain (accepted; TD-4 optional).
- **mypy baseline drift noted in Step 5** — Unrelated project-wide typecheck
  count drift; resolver module itself clean. Not owned by this bugfix.

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| R1: validate `{{ mcp.request.issue_key }}` | Covered |
| R1 locks: `db.__class__`, `mcp.request.__class__` → `invalid_syntax` | Covered |
| R2: `TemplateService` nested mcp.request render | Covered |
| R3: MCP `call_tool` path substitution (stub HTTP) | Covered |
| Explicit pytest timeout markers | Present — `30` / `30` / `120` (not a blocker) |
| Function-arg safe path e.g. `urlencode(mcp.request.query)` | Missing (TD-2) |
| MCP `call_tool` query-param substitution | Missing (TD-1) |
| MCP `call_tool` body substitution | Missing (TD-1) |
| Edge rejects: trailing/leading `.`, empty segment, `_private` attr | Partial — only `__class__` locked (TD-3) |
| Live jira-mcp against local MCP + Jira | Manual / out of CI |

Timeout-marker review: **no blocker** — all touched test modules declare
`pytestmark = pytest.mark.timeout(...)`.

## Performance Concerns

None material. `_SAFE_PATH_RE` is a compiled class attribute; matching is
linear over short expression strings. No depth limit is unlikely to matter for
author-written templates. No new instruments on the hot path (Step 6: reuse
existing TemplateService metrics/logs).

## Deviations from Architecture

None material. Delivered Option B as designed:

- Resolver accepts safe dotted paths; underscore-leading **attribute** segments
  rejected
- MCP merge / RequestService / TemplateService orchestration untouched
- No Jinja `SandboxedEnvironment` migration
- Dev-doc updates correctly deferred to Step 8

## Follow-up Tasks

Concrete Debt candidates for a later sync via `tech-debt-jira-sync` /
`jira-create-issue`. **No Jira browse links yet** (orchestrator tickets in
Phase D). Leave links pending.

### TD-1 — Medium

- **Item:** Add MCP integration coverage for query and body
  `{{ mcp.request.* }}` substitution (mirror R3 path test), ideally shaped
  like `jira_mcp.json` placeholders (`params.query`, JSON body string).
- **Notes:** Closes the DoD gap where only path is automated; same render
  pipeline, different request fields.
- **Jira:** [PYPOST-1034](https://pypost.atlassian.net/browse/PYPOST-1034)

### TD-2 — Low

- **Item:** Unit-test that function arguments accept safe dotted paths, e.g.
  `validate_content("{{ urlencode(mcp.request.query) }}")` is valid and
  `render_string` substitutes nested values.
- **Notes:** Architecture explicitly called this out; plain-path tests do not
  lock the argument branch of `_validate_function_args`.
- **Jira:** [PYPOST-1035](https://pypost.atlassian.net/browse/PYPOST-1035)

### TD-3 — Low

- **Item:** Expand safe-path grammar locks: reject leading/trailing `.`, empty
  segments, and underscore-leading attribute segments beyond `__class__`
  (e.g. `mcp.request._private`); optionally assert a deep-but-safe path still
  validates.
- **Notes:** Documents the allow-list edge cases for future grammar edits.
- **Jira:** [PYPOST-1036](https://pypost.atlassian.net/browse/PYPOST-1036)

### TD-4 — Low (optional)

- **Item:** If hover UX should preview dotted MCP paths, extend
  `PLAIN_VARIABLE_PATTERN` / hover path to safe dotted forms (or document that
  hover remains undotted).
- **Notes:** Explicitly out of scope for PYPOST-1033; ticket only if operators
  report hover confusion. Not ticketed in Phase D.
- **Jira:** n/a (optional; skipped)


### Accepted / out of scope (do not ticket from this story)

- MCP-only allowlist instead of general safe paths (rejected in architecture).
- Jinja `SandboxedEnvironment` migration.
- Changing fail-closed “return original content” TemplateService contract.
- Expanding jira-mcp tool surface or auth/env wiring.
- New resolver-level DEBUG logs / metrics (Step 6 correctly declined).
- Step 8 developer doc updates (owned by STEP 8 of this ticket).
- Unrelated mypy baseline count drift.

## Blocker Review

| Check | Result |
| ----- | ------ |
| Temporary solutions / crutches | None that block ship |
| Missing tests with timeout markers | **None** — markers present |
| Deviations from architecture | None material |
| Acceptance gaps vs DoD | Path + safety automated; query/body e2e are follow-ups (TD-1), not merge blockers for the grammar fix |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** for PYPOST-1033 Step 7; follow-ups are coverage hardening.
Dev docs remain for Step 8.
