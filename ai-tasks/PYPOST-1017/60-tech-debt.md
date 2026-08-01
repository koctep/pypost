# PYPOST-1017: Technical Debt Analysis

**Verdict:** Small maintainability debt only (fixtures/docs + shallow contract
tests). No application-code debt. None of it blocks shipping. SAFE TO CLOSE
for this story's DoD.

Scope reviewed: `examples/collections/jira_mcp.json`,
`examples/environments/jira_cloud.json`, `examples/README.md`, `.gitignore`
exceptions, root `README.md` Documentation pointer, User Guide Example
fixtures / Related pointers, `tests/test_example_fixtures.py`, and
`ai-tasks/PYPOST-1017/*`. Unrelated working-tree noise (PYPOST-1015 drafts,
tech-debt consolidate / sync residue, etc.) ignored.

## Shortcuts Taken

- **Finish/review baseline drafts, not redesign** — Kept the existing 12-tool
  Jira Cloud MCP shape and companion env rather than regenerating from
  Atlassian OpenAPI. Faster and matches requirements; API surface can drift
  from current Cloud REST docs over time.
- **Green contract tests only** — Optional Step 4 guard parses fixtures via
  native loaders and checks counts, placeholders, `hidden_keys`, and
  `enable_mcp`. No UI import e2e and no assertion that every request template
  variable is covered by the companion environment.
- **Hub-and-spoke docs** — Fixture detail lives in `examples/README.md`; User
  Guide pages keep short pointers only (no second import tutorial). Matches
  architecture; readers must follow a link for the full import order.
- **`.gitignore` exceptions verified/added** — Negation rules for
  `examples/{collections,environments}/*.json` are present so fixtures stay
  trackable beside ignored local `collections/` data. No broader ignore-model
  redesign.
- **No live Jira smoke** — Placeholders only; nothing in CI calls a real
  Atlassian site (correct for secret safety; leaves endpoint freshness
  human-gated).

## Code Quality Issues

- **No application code debt** — this story did not change `pypost/` packages.
- **Auth/header boilerplate** — All 12 requests repeat the same
  `Authorization: Basic {{ base64(jira_credentials) }}` and Accept/Content-Type
  pattern. Intentional for native JSON importability; editing the auth recipe
  later means touching every request.
- **Long JSON description strings** — Some `mcp_description` / param
  description literals exceed the 100-character source guideline because JSON
  cannot wrap string values. Accepted in Step 5; not a runtime issue.
- **Hardcoded `maxResults: 50`** on board/sprint list requests — Reasonable
  example defaults; not parameterized via MCP inputs. Fine for a starter
  collection; agents that need different page sizes must edit the fixture or
  request.
- **Architecture inventory tables left historical** — `20-architecture.md`
  still describes pre-delivery git state (“untracked draft”, “README
  missing”). Intentional design-time baseline; not rewritten post-Step-4.

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| Native loader parse + placeholder / `hidden_keys` | Present |
| Explicit pytest timeout markers (`pytestmark`) | Present — not a blocker |
| Collection ↔ env variable coupling | Missing (TD-1) |
| Per-request auth / MCP expose consistency | Partial (see below) |
| UI Import Collection / Environment e2e | Missing; out of scope |
| Jira Cloud REST path freshness vs docs | Missing (TD-2) |
| Relative link check examples ↔ `doc/user/` | Missing (TD-3) |

Details:

- Present coverage is in `tests/test_example_fixtures.py` (3 tests) with
  module `pytestmark = pytest.mark.timeout(30)`.
- Partial auth/MCP checks: all requests `expose_as_mcp`; collection text
  contains `jira_base_url` / `base64(jira_credentials)` — not per-request.
- UI e2e omitted; existing product import tests cover the import path.
- TD-3 overlaps User Guide link-check debt from PYPOST-1015.

## Performance Concerns

None. Static JSON fixtures and Markdown have no runtime cost. The contract
tests are pure file parse / model validate and stay well under the 30s
timeout.

## Deviations from Architecture

None material. Delivered Option A (finish drafts + thin discoverability):

- Curated Jira pair + `mcp.json` role clarity
- `.gitignore` exceptions for tracked examples
- `examples/README.md` hub + root README / User Guide pointers
- Optional green contract test (not a Step 3 red)
- No application package changes; Step 3 and Step 6 remain N/A as planned

Optional Related pointers (workflows, guide index) are present; MCP tools page
kept its existing Cursor config example without a second fixtures tutorial.

## Follow-up Tasks

Concrete items for a later sync via `tech-debt-jira-sync` / `jira-create-issue`.
**No Jira browse links yet.** Do not auto-create Debt tickets from this Step 7
unless the orchestrator explicitly asks.

### TD-1 — Low

- **Item:** Strengthen `tests/test_example_fixtures.py`: assert companion env
  keys cover collection template vars (`jira_base_url`, `jira_credentials`);
  optionally assert every request has Basic `base64(jira_credentials)` auth.
- **Notes:** Prevents silent drift if a request is added without updating the
  env.

### TD-2 — Low

- **Item:** Periodic human or scripted check that Jira Cloud paths in
  `jira_mcp.json` still match current Atlassian REST docs (especially
  `/search/jql` and Agile board/sprint routes).
- **Notes:** No live credentials in CI; doc/OpenAPI compare is enough.

### TD-3 — Low

- **Item:** Include `examples/README.md` (and root README examples bullet) in
  any future relative link checker for docs.
- **Notes:** Complements User Guide link-check follow-ups from PYPOST-1015.

### Accepted / out of scope (do not ticket from this story)

- Application import/export redesign or Postman/OpenAPI converters.
- Full User Guide completion (PYPOST-1015).
- Live Jira integration tests with real tokens.
- Regenerating the 12-tool set from OpenAPI as a greenfield redesign.
- Runtime observability for static fixture “usage.”
- Deduplicating auth headers via a non-native fixture format.

## Blocker Review

| Check | Result |
| ----- | ------ |
| Temporary solutions / crutches | Docs/fixture shortcuts only; none block ship |
| Missing tests with timeout markers | **None** — `timeout(30)` present |
| Deviations from architecture | None material |
| Acceptance gaps vs DoD | **None** — fixtures + discoverability wired |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** for PYPOST-1017; follow-ups are optional fixture-maintenance
improvements.
