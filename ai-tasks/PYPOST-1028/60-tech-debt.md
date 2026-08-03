# PYPOST-1028: Technical Debt Analysis

**Verdict:** Test-module maintainability debt only. Delivery matches architecture
(Option A: shared checkers + `FIXED_INPUT_JIRA_MCP_REQUEST_IDS` in
`tests/test_example_fixtures.py`; no fixture JSON or `pypost/` package
changes). No missing pytest timeouts, no merge blockers. **SAFE TO CLOSE** for
this story's DoD once Step 8 docs land.

Scope reviewed: `tests/test_example_fixtures.py` (PYPOST-1028 checkers,
allowlist, positive + mutation tests), `ai-tasks/PYPOST-1028/*`, and the
unchanged shipped pair `examples/collections/jira_mcp.json` /
`examples/environments/jira_cloud.json`. Unrelated working-tree noise ignored.

## Shortcuts Taken

- **Test-local broad `mcp.request` scan instead of fixing production** —
  Contract checkers use `_MCP_REQUEST_NAME_PATTERN` so
  `to_int(mcp.request.*)` (and similar wrappers) still require matching
  `mcp_params` keys. Production
  `McpSecretsPolicy.extract_mcp_request_variables` still matches only bare
  `{{ mcp.request.VAR }}`. Intentional: architecture deferred the runtime
  change; curated fixtures already declare explicit `mcp_params`, so
  `resolve_mcp_param_specs` publishes those inputs today (TD-2).
- **Fixed-input allowlist retains `jira-list-boards`** — Empty `mcp_params`
  with env-bound `projectKeyOrId` and hardcoded `maxResults: "50"` remains
  the accepted escape hatch until pagination parameterization
  ([PYPOST-1029](https://pypost.atlassian.net/browse/PYPOST-1029)) lands.
  `jira-get-current-user` is a genuine fixed-input smoke tool (TD-1).
- **Offline mutation + positive contracts only** — No live Jira, UI import
  e2e, or network checks (requirements / architecture out of scope).
- **Requirements DoD checkboxes still open** — `10-requirements.md` Definition
  of Done remains unchecked until Step 8 verification (process, not product
  debt).
- **Architecture inventory left as design-time baseline** —
  `20-architecture.md` still describes Step-2 research state. Same pattern as
  sibling Jira fixture stories; not rewritten post-delivery.

## Code Quality Issues

- **No application code debt** — this story did not change `pypost/` packages.
- **Duplicated template-field walk** — Test helpers
  `_jira_mcp_template_fields` mirror production `_iter_request_template_fields`
  in `mcp_secrets_policy.py`. Acceptable while discovery regexes intentionally
  differ; consolidate only if TD-2 lands and one scanner serves both.
- **Module growth** — PYPOST-1028 added checkers + ~11 tests to an already
  large fixture-contract module. Matches Option A; splitting helpers is
  optional hygiene, not a ship blocker (do not ticket from this story).
- **Two allowlist mutation tests overlap** — Empty-outside-allowlist and
  empty-set-drift both clear `mcp_params` on a non-allowlisted id. Both are
  useful diagnostics pins; cosmetic redundancy only.

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| Companion env refs ⊆ companion `environment.variables` | Present |
| Per-request Basic `base64(jira_credentials)` auth | Present |
| Broad `mcp.request.<name>` ⊆ `mcp_params` (incl. wrappers) | Present |
| Empty `mcp_params` ids == `FIXED_INPUT_JIRA_MCP_REQUEST_IDS` | Present |
| Agent-driven query/body ⇒ `mcp_params` or allowlist | Present |
| Mutation negatives for each checker + diagnostic `match=` | Present |
| Explicit pytest timeout markers | Present (`pytestmark` 30s; not a blocker) |
| Production discovery for wrapped `mcp.request` forms | Missing (TD-2; product, not this story) |
| Live Jira / UI import e2e | Missing; out of scope by design |

Timeout-marker review: **no blocker** — `tests/test_example_fixtures.py`
declares module-level `pytestmark = pytest.mark.timeout(30)`.

## Performance Concerns

None. Checkers are pure offline parse / string scan / set compare and stay
well under the 30s timeout. No new runtime path; Step 6 correctly recorded
observability N/A.

## Deviations from Architecture

None material. Delivered as designed:

- Option A: extend `tests/test_example_fixtures.py` only
- `FIXED_INPUT_JIRA_MCP_REQUEST_IDS == {"jira-get-current-user",
  "jira-list-boards"}` with exact empty-`mcp_params` freeze
- Broad test-local `mcp.request` scan (not the narrow secrets-policy regex)
- Positive shipped-fixture tests + deepcopy mutation negatives
- No edits to `jira_mcp.json` / `jira_cloud.json`
- No pagination parameterization (owned by PYPOST-1029)
- No production `McpSecretsPolicy` regex change

## Follow-up Tasks

### TD-1 — Low (already ticketed)

- **Item:** Parameterize pagination on board/sprint list requests — expose
  `maxResults` (and optionally `startAt`) via `mcp_params` on
  `jira-list-boards`, `jira-list-board-sprints`, and
  `jira-get-sprint-issues`; replace empty `mcp_params` on list-boards.
  When that lands, remove `jira-list-boards` from
  `FIXED_INPUT_JIRA_MCP_REQUEST_IDS` and keep the freeze equality green.
- **Notes:** Carry from PYPOST-1026 TD-3; this story correctly left
  `jira-list-boards` on the allowlist. Pure fixture + contract-constant
  follow-up.
- **Jira:** [PYPOST-1029](https://pypost.atlassian.net/browse/PYPOST-1029)

### TD-2 — Low (optional product follow-up)

- **Item:** Widen `McpSecretsPolicy.extract_mcp_request_variables` (and any
  callers that rely on discovery alone) to recognize function-wrapped forms
  such as `{{ to_int(mcp.request.board_id) }}`, aligning production discovery
  with the broader fixture-contract scan.
- **Notes:** Not required for curated Jira MCP fixtures (explicit
  `mcp_params` already publish those inputs via `resolve_mcp_param_specs`).
  Matters for user-authored collections that omit explicit `mcp_params` and
  rely on auto-discovery. Out of scope for this story by architecture.
- **Jira:** [PYPOST-1052](https://pypost.atlassian.net/browse/PYPOST-1052)

### Accepted / out of scope (do not ticket from this story)

- Changing shipped Jira MCP request behavior or adding capabilities.
- Live Jira CI smoke or UI import e2e for curated examples.
- Deduplicating auth headers across fixture JSON.
- Splitting `tests/test_example_fixtures.py` into multiple modules.
- Exact inventory freeze (`len(requests) == N`) beyond existing floors /
  locked id sets from sibling stories.
- Rewriting historical `20-architecture.md` baseline narrative.
- New observability for static fixtures (Step 6 correctly N/A).
- Step 8 developer doc wrap-up and DoD checkbox closure (owned by STEP 8).

## Blocker Review

| Check | Result |
| ----- | ------ |
| Temporary solutions / crutches | Test-local scan + allowlist only; none block ship |
| Missing tests with timeout markers | **None** — module `pytestmark` present |
| Deviations from architecture | None material |
| Acceptance gaps vs DoD | Four contracts delivered offline; TD-1 is existing Low debt |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** for PYPOST-1028 Step 7; follow-ups are the already-ticketed
pagination story and an optional production discovery widening. Dev docs
remain for Step 8. STEP 7 left `[/]` pending review.
