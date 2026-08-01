# PYPOST-948: Migrate sibling agent e2e to wait_for_text settle

## Goals

[PYPOST-920](https://pypost.atlassian.net/browse/PYPOST-920) added stable
response **status** and **body** identities and migrated the golden Send →
response flow to identity-scoped text waits. Several sibling `agent_e2e` locks
still settle after Send by walking the whole response panel snapshot and
matching joined panel text — the pattern golden deliberately left behind.

That split leaves automation inconsistent: one canonical path uses targeted
status/body waits; double-body, presentation-matrix, env, and seed-post flows
remain coupled to snapshot sanitize shape for readiness. Maintainers carry two
settle conventions for the same business proof (Send completed → status and
body visible as users see them).

**Business why:** Align sibling agent e2e Send settle with the PYPOST-920
identity contract so response readiness proofs are stable, consistent across
locks, and decoupled from full-panel snapshot walks — without changing what
users see or weakening existing cardinality / regression assertions.

Source: [PYPOST-920](https://pypost.atlassian.net/browse/PYPOST-920)
`60-tech-debt.md` TD-1 (Medium). Parent story:
[PYPOST-920](https://pypost.atlassian.net/browse/PYPOST-920). Browse:
[PYPOST-948](https://pypost.atlassian.net/browse/PYPOST-948).

## Programming Language

Python (`.cursor/lsr/do-python.md`). Test-only changes under the project’s
`agent_e2e` harness path. Task artifacts in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As an **agent e2e maintainer**, I want double-body, presentation-matrix, and
  env Send flows to settle on the same status/body identity targets as golden,
  so one settle convention applies across the sibling lock family.
- As a **CI runner**, I want those flows to stay green under
  `make test-agent-e2e` after migration, with bounded wall-clock budgets
  unchanged in intent.
- As a **regression owner** (double-body / presentation matrix), I want
  post-settle cardinality and once-only body proofs to remain as strong after
  migration — only readiness detection changes, not the product invariants
  under test.
- As a **seed-post scenario owner**, I want optional migration of seed POST
  response settle to the same pattern when it reduces snapshot coupling without
  weakening tree-open or multi-tab behaviour covered elsewhere.

## Definition of Done

- **Double-body lock** (`test_agent_e2e_double_response_body.py`): Send settle
  uses identity-scoped text waits on response status and body (not a
  panel-snapshot predicate for readiness).
- **Presentation matrix** (`test_agent_e2e_presentation_matrix.py`): each cell’s
  Send settle uses the same status/body text-wait pattern.
- **HTTP env seed GET** (`test_agent_e2e_http_env.py`): both env Send scenarios
  settle via status/body text waits.
- **Seed POST (optional):** response settle in
  `test_agent_e2e_http_seed_post.py` migrated where it clearly matches the
  above pattern; tree-open / editor-ready waits may remain snapshot-based.
- Body readiness waits match **display-form** body text (what the response body
  surface shows users), consistent with golden — not compact snapshot JSON
  re-dumps used only for panel walks.
- Forced-timeout rewraps on Send settle retain actionable diagnostics (stable
  step name and response excerpt context) comparable to today’s sibling locks.
- Full `agent_e2e` suite green under `make test-agent-e2e`.
- Unticketed follow-ups (if any) live only in this task’s `60-tech-debt.md`
  (no Jira ticket creation in this run).

Acceptance (from Jira): **Sibling modules settle via wait_for_text; suite
green.**

## Task Description

**Problem:** PYPOST-920 proved status/body text waits on golden but explicitly
deferred sibling e2e. Those siblings still gate Send completion on
`wait_for_snapshot` + joined panel values, keeping sanitize-coupled readiness
and divergent maintainer conventions.

**Business need:** Complete the sibling migration so agent e2e Send → response
readiness consistently uses the PYPOST-920 status/body identity contract,
while preserving each lock’s downstream assertions (exactly-once body counts,
matrix cell invariants, stub/logging checks).

### In Scope

- Migrate Send settle (readiness after click Send) in:
  - `tests/test_agent_e2e_double_response_body.py`
  - `tests/test_agent_e2e_presentation_matrix.py`
  - `tests/test_agent_e2e_http_env.py`
  - Optionally `tests/test_agent_e2e_http_seed_post.py` (response settle only)
- Status waits target the established response status identity; body waits
  target the established response body identity (PYPOST-920 catalog names).
- Body expected text uses display form for JSON payloads (golden precedent).
- Preserve existing test intent: chunk-flush settle delay, cardinality asserts,
  caplog smoke, tree-open flow structure where unchanged.
- Preserve or equivalent Send-settle timeout diagnostics (step + excerpt).

### Out of Scope

- Production UI, widget identity, or wait-helper API changes.
- Golden e2e (already on text waits) and its timeout-diagnostics companion
  (PYPOST-950).
- Tab-scoped text waits for multi-tab Send (`in_current_tab` on text wait —
  PYPOST-949).
- Migrating other panel-walk tests not listed (e.g. HTTP mapping multi-URL,
  generic response-panel unit helpers, seed editor-ready snapshot waits).
- Redesigning `joined_panel_values`, snapshot helpers, or Send stub fixtures.
- User-facing product docs (`doc/user/`).
- Creating Jira Debt tickets (unticketed items only in `60-tech-debt.md`).
- Commit or Jira status transitions / worklog MCP writes (orchestrator).

## Functional Requirements

- FR1: Double-body lock Send settle waits for expected status text on the
  response status identity, then expected body text on the response body
  identity — without requiring a full-panel snapshot predicate for readiness.
- FR2: Presentation matrix Send settle per cell follows FR1 for that cell’s
  status label and body token.
- FR3: HTTP env seed GET Send scenarios (including caplog smoke) follow FR1 for
  seeded status and display-form body text.
- FR4: Optional seed POST response settle follows FR1 where applied; acceptance
  does not require seed POST if migration risks multi-tab scope without
  PYPOST-949.
- FR5: Post-settle product assertions unchanged in meaning (e.g. body token
  count == 1, status count == 1, shared stub identity, caplog line present).
- FR6: Send-settle timeout failures remain diagnosable with stable step
  identifiers and response excerpt context aligned with each scenario’s today
  behaviour.
- FR7: `make test-agent-e2e` passes with migrated modules.

## Non-Functional Requirements

- **Consistency:** Sibling Send settle matches golden’s identity-scoped text-wait
  business contract (status then body).
- **Stability:** Body waits use display-form text for JSON responses; plain-text
  stub tokens wait on the literal displayed body where applicable.
- **CI suitability:** Modules keep bounded `agent_e2e` timeout markers; no new
  hangs from settle migration.
- **Minimalism:** Test-only diff; no new production dependencies or imports from
  `tests/` into production code.
- **Compatibility:** Panel snapshot helpers remain available for post-settle
  cardinality checks and excerpts where locks still need them.
- **English docs;** line length ≤ 100 where practical.

## Constraints and Assumptions

- Programming language: Python.
- Parent / source debt: PYPOST-920 TD-1; status/body identities and golden
  text-wait pattern already shipped and documented in `doc/dev/`.
- Reference behaviour: golden Send settle waits status then display-form body
  on `RESPONSE_STATUS` / `RESPONSE_BODY` — business precedent for siblings.
- Presentation matrix body tokens are plain text; env/seed JSON bodies need
  display-form derivation (indent consistent with response UI default).
- Double-body and matrix tests retain short post-settle delay before snapshot
  cardinality checks (chunk-flush visibility) — requirement preserves intent,
  not a mandate to remove that delay.
- Seed POST tree-open editor-ready settle may stay snapshot-based; only
  response-after-Send settle is in optional scope.
- Multi-tab seed POST Send uses `in_current_tab=True` on actions; window-scoped
  text wait first-match is acceptable for single active response tab (same
  assumption as golden until PYPOST-949).
- Step 1 review is treated as pre-approved under sprint-task-runner autonomy
  (no approval gate / no Jira updates in this step).

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Sibling agent e2e lock | Automated Send → response proof (double-body, matrix, env, seed) |
| Golden e2e | Reference path already using status/body text waits (PYPOST-920) |
| Response status identity | Stable target for status text readiness |
| Response body identity | Stable target for body text readiness |
| Text wait | Bounded wait until expected text appears on a named surface |
| Panel snapshot walk | Legacy readiness pattern being replaced for Send settle only |
| Post-settle assertion | Cardinality, stub, or logging checks after readiness |
| CI / agent_e2e runner | Runs suite under bounded budget; must stay green |

Interaction overview:

1. Harness launches PyPost and reaches UI ready (existing fixtures).
2. Harness fills request fields and clicks Send under deterministic HTTP stub.
3. Harness waits for status text on the status identity, then body text on the
   body identity (display form where JSON).
4. Harness runs any existing post-settle delay and snapshot-based cardinality
   or logging assertions unchanged in business meaning.
5. On timeout, harness surfaces step + response excerpt diagnostics.
6. CI runs full `agent_e2e` selection green.

## Q&A

- Q: Why migrate if panel walks still work?
  A: PYPOST-920’s business value was identity-scoped waits; deferring siblings
  leaves two conventions and sanitize-coupled readiness on high-value locks.
  This ticket completes that adoption.

- Q: Must every assertion stop using panel snapshots?
  A: No. Only **Send settle** (readiness) migrates. Post-settle count checks
  and excerpts may still use panel snapshot helpers.

- Q: Why display-form body text?
  A: Golden and developer docs establish that the body surface shows
  pretty-printed JSON; waits must match what users and agents see, not compact
  snapshot joins.

- Q: Is seed POST mandatory?
  A: Optional per parent TD-1 and Jira description. Core acceptance is
  double-body, presentation matrix, and env modules.

- Q: Does this change production behaviour?
  A: No. Test-only migration using identities and waits already in the product.

- Q: What about multi-tab text waits?
  A: Out of scope (PYPOST-949). Current single-tab / window first-match
  assumption matches golden until tab-scoped waits exist.

- Q: Jira / commit in this run?
  A: No — parent orchestrator owns Phase D/F.
