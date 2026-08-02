# PYPOST-1026: Technical Debt Analysis

**Verdict:** Fixture/docs/test maintainability debt only (no application-code
debt). Partial Atlassian MCP parity and gap-listed niche surfaces are
**intentional** per requirements, not accidental incompleteness. None of it
blocks shipping. SAFE TO CLOSE for this story's DoD.

Scope reviewed: `examples/collections/jira_mcp.json` (21 MCP-exposed tools),
`examples/environments/jira_cloud.json`, `examples/README.md`,
`tests/test_example_fixtures.py`, and `ai-tasks/PYPOST-1026/*`. Unrelated
working-tree noise (e.g. PYPOST-376 baseline metrics) ignored. No `pypost/`
package changes.

## Shortcuts Taken

- **Practical analog, not full MCP parity** — Shipped **21** curated
  MCP-exposed requests against a live Atlassian MCP surface of **~63**
  `jira_*` tools. Done is skill/workflow capability coverage plus an explicit
  gap list, not a one-to-one tool dump (requirements Q&A).
- **Service Desk / ProForma / niche tools gap-listed** — JSM queues/request
  types/customer requests, ProForma forms/answers, watchers, attachments,
  delete issue, remote/issue-link CRUD beyond parent, versions/components
  batch, SLA, development info, cross-project deps, and
  `jira_batch_create_issues` remain documented omissions in
  `examples/README.md`. Correct prioritization; leaves a large surface for
  later stories if skills grow.
- **Stretch tools included but not contract-locked** — `jira-get-worklog`,
  `jira-move-issues-to-backlog`, and `jira-search-assignable-users` landed
  (21 = 12 starter + 6 must-haves + 3 stretch). Contract tests lock only the
  six must-have ids/paths and `len(requests) >= 18`. Stretch ids can regress
  without a red test as long as the floor stays ≥18.
- **Empty `mcp_params` on older list-boards request** —
  `jira-list-boards` keeps `mcp_params: {}` with hardcoded
  `params.maxResults: "50"`. Agents cannot page or raise the limit via MCP
  inputs without editing the fixture. Inherited from the PYPOST-1017 starter;
  not fixed while expanding.
- **Hardcoded pagination defaults** — `maxResults: "50"` also on
  `jira-list-board-sprints` and `jira-get-sprint-issues` (not exposed as
  `mcp_params`). Fine for a starter; agents that need other page sizes edit
  JSON or the request.
- **Serialized JSON string body params** — Nested Cloud payloads
  (`search_payload`, `issue_payload`, `sprint_payload`, etc.) remain opaque
  string MCP inputs matching the starter convention. Easier for native import
  than structured MCP schemas; worse agent ergonomics than Atlassian MCP’s
  typed fields.
- **Green offline contract tests only** — Native loader parse, count floor,
  required capability ids/paths, placeholder hygiene, env `hidden_keys` /
  `enable_mcp`. No UI import e2e, no live Jira smoke, no assertion that every
  collection template var is covered by the companion env.
- **Architecture inventory left historical** — `20-architecture.md` still
  describes the pre-delivery 12-request baseline and Step-2 “in progress”
  state. Design-time baseline; not rewritten post-Step-4 (same pattern as
  PYPOST-1017).
- **Companion env unchanged** — No new shared variables; MCP inputs stay on
  requests. Correct for scope; means assignable-user / board filters cannot
  default from env.
- **No live Jira smoke** — Placeholders only; CI never calls a real Atlassian
  site (secret-safe; endpoint freshness stays human-gated).

## Code Quality Issues

- **No application code debt** — this story did not change `pypost/` packages.
- **Auth/header boilerplate ×21** — Every request repeats
  `Authorization: Basic {{ base64(jira_credentials) }}` and Accept /
  Content-Type. Intentional for native JSON importability; auth recipe edits
  touch every request.
- **Long JSON description strings** — Several `mcp_description` / param
  description literals exceed the 100-character source guideline because JSON
  cannot wrap string values. Accepted in Step 5; not a runtime issue.
- **Uneven agent-facing descriptions** — e.g. `jira-get-worklog` is a single
  short sentence while assign/create-sprint descriptions carry payload
  examples. Stretch tools got thinner copy.
- **Assignable-user search requires `issue_key`** — Fixture always sends
  `issueKey`; Atlassian REST also supports project-scoped search. Narrower
  than the external MCP tool; acceptable for issue-assign workflows.
- **Requirements DoD checkboxes** — Resolved in Step 8: `10-requirements.md`
  Definition of Done list marked `[x]` after delivery verification.

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| Native loader parse + count floor ≥18 + all `expose_as_mcp` | Present |
| Locked must-have ids + path/method markers | Present |
| Env placeholders / `hidden_keys` / `enable_mcp` | Present |
| Explicit pytest timeout markers (`pytestmark`) | Present — not a blocker |
| Stretch request ids (worklog get, backlog, assignable) | Missing (TD-1) |
| Collection ↔ env variable coupling | Missing (TD-2; carry from PYPOST-1017) |
| Per-request auth / non-empty `mcp_params` where URL needs inputs | Partial / missing (TD-2) |
| Exact count `== 21` (or inventory snapshot) | Missing; floor only |
| UI Import Collection / Environment e2e | Missing; out of scope |
| Jira Cloud REST path freshness vs docs | Missing (TD-4) |
| Relative link check `examples/README.md` ↔ `doc/user/` | Missing (TD-5) |

Details:

- Present coverage is in `tests/test_example_fixtures.py` (4 tests) with
  module `pytestmark = pytest.mark.timeout(30)`.
- Capability test locks six must-have ids only; stretch trio is unprotected.
- Collection text contains `jira_base_url` / `base64(jira_credentials)` —
  not per-request auth assertions.
- UI e2e omitted; existing product import tests cover the import path.
- TD-5 overlaps User Guide / examples link-check debt from PYPOST-1015 /
  PYPOST-1017.

## Performance Concerns

None. Static JSON fixtures and Markdown have no runtime cost. The contract
tests are pure file parse / model validate and stay well under the 30s
timeout. After import, product HTTP/MCP observability scales with more named
tools but was unchanged by this story (Step 6 N/A).

## Deviations from Architecture

None material. Delivered Option A (expand-in-place):

- Same `jira_mcp.json` + `jira_cloud.json` pair
- ≥18 floor met (21 shipped, including documented stretch)
- Parent-field epic link (`jira-link-issue-parent`)
- Dedicated assign + comment requests
- Coverage vs gaps section in `examples/README.md`
- Extended contract tests (count + required capabilities)
- No application package changes; Step 6 observability correctly N/A

Gap list and “capability over tool-count parity” match `20-architecture.md`.

## Follow-up Tasks

Concrete Debt candidates for a later sync via `tech-debt-jira-sync` /
`jira-create-issue`. **No Jira browse links yet** (orchestrator tickets after
blocker review). Leave links blank / unticketed.

### TD-1 — Low

- **Item:** Lock stretch request ids in
  `test_jira_mcp_collection_covers_required_skill_capabilities` (or a sibling
  test): `jira-get-worklog`, `jira-move-issues-to-backlog`,
  `jira-search-assignable-users` (+ path markers). Optionally assert
  `len(requests) == 21` or a frozen id set so silent drops fail CI.
- **Notes:** Prevents stretch regression while the floor stays at 18.
- **Jira:** [PYPOST-1027](https://pypost.atlassian.net/browse/PYPOST-1027)

### TD-2 — Low

- **Item:** Strengthen `tests/test_example_fixtures.py`: companion env keys
  cover collection template vars (`jira_base_url`, `jira_credentials`); every
  request has Basic `base64(jira_credentials)` auth; flag requests that use
  `mcp.request.*` without matching `mcp_params` keys; consider requiring
  non-empty `mcp_params` when query/body is agent-driven (or explicitly allowlist
  `jira-list-boards` until parameterized).
- **Notes:** Overlaps PYPOST-1017 TD-1; expand assertions for the 21-tool set.
- **Jira:** [PYPOST-1028](https://pypost.atlassian.net/browse/PYPOST-1028)

### TD-3 — Low

- **Item:** Parameterize pagination on board/sprint list requests — expose
  `maxResults` (and optionally startAt) via `mcp_params` on
  `jira-list-boards`, `jira-list-board-sprints`, and `jira-get-sprint-issues`;
  replace empty `mcp_params` on list-boards.
- **Notes:** Improves agent ergonomics; pure fixture change.
- **Jira:** [PYPOST-1029](https://pypost.atlassian.net/browse/PYPOST-1029)

### TD-4 — Low

- **Item:** Periodic human or scripted check that Jira Cloud / Agile paths in
  `jira_mcp.json` still match current Atlassian REST docs (especially
  `/search/jql`, sprint create/membership, parent-field epic link, assignee).
- **Notes:** No live credentials in CI; doc/OpenAPI compare is enough.
- **Jira:** [PYPOST-1030](https://pypost.atlassian.net/browse/PYPOST-1030)

### TD-5 — Low

- **Item:** Include `examples/README.md` (and root README examples bullet) in
  any future relative link checker for docs.
- **Notes:** Complements PYPOST-1015 / PYPOST-1017 link-check follow-ups.
- **Jira:** [PYPOST-1031](https://pypost.atlassian.net/browse/PYPOST-1031)

### TD-6 — Low (optional product/fixture expansion)

- **Item:** If skills start needing them, add curated MCP-exposed analogs for
  currently gap-listed surfaces that are low-cost REST (e.g. watchers, simple
  issue links, get project) — still not Service Desk/ProForma dumps unless
  skill priority changes.
- **Notes:** Only ticket when a concrete skill workflow is blocked; do not
  expand “for completeness.”
- **Jira:** unticketed

### Accepted / out of scope (do not ticket from this story)

- Full 63-tool Atlassian MCP parity or OpenAPI dump.
- Service Desk / JSM / ProForma fixture dump.
- Replacing external Atlassian MCP in agent config.
- In-process Atlassian MCP server in application code.
- Live Jira integration tests with real tokens.
- Deduplicating auth headers via a non-native fixture format.
- Runtime observability for static fixture “usage” (Step 6 correctly N/A).
- Rewriting historical architecture baseline tables.
- Application import/export redesign.

## Blocker Review

| Check | Result |
| ----- | ------ |
| Temporary solutions / crutches | Fixture/docs shortcuts only; none block ship |
| Missing tests with timeout markers | **None** — `timeout(30)` present |
| Deviations from architecture | None material |
| Acceptance gaps vs DoD | **None** — ≥18 tools, must-haves, gaps doc, placeholders, tests green |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** for PYPOST-1026; follow-ups are optional fixture-maintenance
and test-hardening improvements. STEP 7 left `[/]` pending user review.
