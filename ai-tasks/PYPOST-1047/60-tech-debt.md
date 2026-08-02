# PYPOST-1047: Technical Debt Analysis

**Verdict:** Fixtures/docs/contract-test maintainability debt only. Delivery
matches architecture (new DELETE sprint + lock/document backlog move as
remove-from-sprint). No application-code debt, no missing pytest timeouts, no
merge blockers. **SAFE TO CLOSE** for this story's DoD once Step 8 docs land.

Scope reviewed: `examples/collections/jira_mcp.json` (22 MCP-exposed requests),
`examples/README.md`, `doc/dev/testing.md`, `doc/dev/README.md`,
`tests/test_example_fixtures.py`, and `ai-tasks/PYPOST-1047/*`. No `pypost/`
package changes. Pre-existing `verify-ai-tasks` baseline drift (other tasks
missing `70-dev-docs.md`) noted as out-of-scope ops debt.

## Shortcuts Taken

- **Reuse backlog move instead of a dedicated remove-from-sprint tool** —
  Intentional architecture decision B1. Tool MCP name stays
  `jira_move_issues_to_backlog`; discoverability relies on sharpened
  `mcp_description` plus `examples/README.md`. Agents must map "remove from
  sprint" to backlog move by description, not by tool name.
- **Offline contract tests only** — Count floor >=22, locked ids, method/path
  markers, placeholder hygiene. No live Jira smoke, no UI import e2e for the
  new request (same secret-safe pattern as PYPOST-1026).
- **Discoverability polish not regression-locked** — `mcp_description` for
  delete (irreversible / backlog side-effect) and backlog move
  ("Supported remove-from-sprint path") can regress without a red test;
  contracts only lock id + method + URL fragments (TD-1).
- **Agile <=50 issues / request limit undocumented in fixture copy** —
  Official `POST /rest/agile/1.0/backlog/issue` caps batch size; agent-facing
  description shows an example payload but does not state the limit (TD-2).
- **Architecture inventory left historical** — `20-architecture.md` still
  describes pre-delivery baseline and Step-2 "in progress". Design-time
  snapshot; not rewritten post-delivery (same pattern as PYPOST-1026).
- **Requirements DoD checkboxes still open** — `10-requirements.md` Definition
  of Done remains unchecked until Step 8 verification (process, not product
  debt).
- **Companion env unchanged** — Correct per architecture; no new keys for
  delete or backlog move.

## Code Quality Issues

- **No application code debt** — this story did not change `pypost/` packages.
- **Auth/header boilerplate x22** — Every request still repeats Basic auth /
  Accept (and Content-Type where needed). Intentional for native JSON
  importability; inherited from the curated collection pattern.
- **Long JSON description strings** — Several `mcp_description` literals
  exceed the 100-character source guideline because JSON cannot wrap string
  values. Accepted for fixtures; not a runtime issue.
- **DELETE uses empty body + `body_type: "json"`** — Matches existing GET-style
  empty-body requests in the same collection (e.g. get-sprint). Consistent,
  not a crutch.
- **Request order** — `jira-delete-sprint` sits between update and create.
  Readable enough; optional reorder next to other sprint writes is cosmetic
  only (do not ticket).

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| Native loader parse + count floor >=22 + all `expose_as_mcp` | Present |
| Locked ids include `jira-delete-sprint` + `jira-move-issues-to-backlog` | Present |
| DELETE .../sprint/ + POST .../backlog/issue path/method markers | Present |
| Env placeholders / `hidden_keys` / `enable_mcp` | Present |
| Explicit pytest timeout markers | Present (`pytestmark` 30s; not a blocker) |
| `mcp_description` discoverability substrings | Missing (TD-1) |
| Exact count `== 22` / full id inventory | Missing; floor only |
| Stretch ids (worklog get, assignable search) | Still unlocked (PYPOST-1026 carry) |
| Collection to env variable coupling | Missing; earlier jira_mcp carry |
| Live Jira / UI import e2e for new tools | Missing; out of scope by design |

Timeout-marker review: **no blocker** — `tests/test_example_fixtures.py`
declares module-level `pytestmark = pytest.mark.timeout(30)`.

## Performance Concerns

None. Static JSON fixtures and Markdown have no runtime cost. Contract tests
are pure file parse / model validate and stay well under the 30s timeout.
After import, existing product HTTP/MCP observability scales with one
additional named tool; Step 6 correctly recorded N/A (no new instruments).

## Deviations from Architecture

None material. Delivered as designed:

- New `jira-delete-sprint` DELETE with irreversibility + backlog side-effect
  copy
- Reuse + contract-lock of `jira-move-issues-to-backlog` (B1); no duplicate
  remove tool; no rename
- Floor `JIRA_MCP_MIN_EXPOSED_REQUESTS = 22`
- Docs: `examples/README.md` coverage + remove-path note;
  `doc/dev/testing.md` floor/locked ids; TOC anchor sync in `doc/dev/README.md`
- No Atlassian MCP or `pypost/` product changes
- User tool-inventory docs untouched (no inventory in `doc/user/` today)

## Follow-up Tasks

Concrete Debt follow-ups ticketed in Phase D:

### TD-1 — Low

- **Item:** Extend offline fixture contracts to assert key
  `mcp_description` substrings for `jira-delete-sprint` (e.g. irreversible /
  backlog) and `jira-move-issues-to-backlog` (e.g. remove-from-sprint /
  membership), so discoverability polish cannot silently regress.
- **Notes:** Id/method/path locks already prevent dropping the tools; this
  only protects agent-facing copy that was a primary DoD concern.
- **Jira:** [PYPOST-1048](https://pypost.atlassian.net/browse/PYPOST-1048)

### TD-2 — Low

- **Item:** Mention the Agile API batch limit (<=50 issues per
  `POST /rest/agile/1.0/backlog/issue`) in
  `jira-move-issues-to-backlog` `mcp_description` (and optionally
  `examples/README.md`).
- **Notes:** Prevents agent failures on large replans; does not change REST
  shape or params.
- **Jira:** [PYPOST-1050](https://pypost.atlassian.net/browse/PYPOST-1050)

### TD-3 — Medium (out of scope for this story)

- **Item:** Clear `scripts/verify_ai_task_artifacts.py` baseline drift:
  completed tasks missing `70-dev-docs.md` and not yet baselined
  (`PYPOST-968`, `974`-`976`, `978`-`979`, `1016`, `1025`, `1026`, `1033`
  per Step 5 notes). Either finish those Step 8 docs or refresh the
  allowlist/baseline so `make check` is green again.
- **Notes:** Pre-existing; **PYPOST-1047 is not among the missing set**
  (roadmap still incomplete, ignored by scanner). Blocks full-gate green
  independently of this story's suite (fixture contracts + lint were green).
- **Jira:** [PYPOST-1049](https://pypost.atlassian.net/browse/PYPOST-1049)

### Accepted / out of scope (do not ticket from this story)

- Dedicated `jira-remove-issues-from-sprint` duplicate tool (rejected B2).
- Renaming backlog move request id / MCP tool name (rejected B3; stability).
- Changing external Atlassian MCP to add delete-sprint.
- Live Jira CI smoke or UI import e2e for curated examples.
- Locking remaining stretch tools (`jira-get-worklog`,
  `jira-search-assignable-users`) — carry from PYPOST-1026 if still desired.
- Rewriting historical `20-architecture.md` baseline narrative.
- New observability for static fixtures (Step 6 correctly N/A).
- Step 8 developer doc wrap-up and DoD checkbox closure (owned by STEP 8).

## Blocker Review

| Check | Result |
| ----- | ------ |
| Temporary solutions / crutches | None that block ship |
| Missing tests with timeout markers | **None** — module `pytestmark` present |
| Deviations from architecture | None material |
| Acceptance gaps vs DoD | Delete + remove path delivered; TD-1 is Low |
| Merge / release blocker debt | **None** here; TD-3 is unrelated baseline drift |

**SAFE TO CLOSE** for PYPOST-1047 Step 7; follow-ups are Low polish plus
out-of-scope baseline hygiene. Dev docs remain for Step 8.
