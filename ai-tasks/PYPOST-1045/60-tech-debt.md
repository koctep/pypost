# PYPOST-1045: Technical Debt Analysis

## Review Scope

Reviewed analysis deliverables for PYPOST-1045: inventory and recommendation
in `10-requirements.md`, Decision Lock and follow-up sketch in
`20-architecture.md`, offline doc-lock
`tests/test_pypost_1045_recommendation_doc_lock.py`, and Steps 5–6
artifacts. No `pypost/` package changes. Doc-lock test has module
`pytestmark = pytest.mark.timeout(10)`.

## Shortcuts Taken

- **Analysis only — harness not built** — Intentional DoD. Controlled
  backend need is decided; form, interfaces, Makefile name, and tool-id
  slice are locked; implementation is deferred (TD-1).
- **Doc-lock instead of runtime red test** — Correct for an analysis
  ticket; runtime e2e red→green belongs in the follow-up.
- **Stdlib loopback preferred over WireMock / process mock for v1** —
  Architecture decision; external process mock remains optional later if
  catalog complexity grows (do not ticket from this story unless needed).

## Code Quality Issues

- None in changed Python. Doc-lock reuses `tests.helpers.packaging_doc_lock`.
- Architecture Markdown is long by design (inventory + options + lock);
  acceptable for an analysis artifact.

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| Architecture file exists + `## Decision Lock` | Present (doc-lock) |
| `controlled_backend_needed: yes` | Present |
| `recommended_form: in-process loopback HTTP stand-in` | Present |
| `agent_e2e_http_primary: no` / `live_only: no` | Present |
| Four tool ids + `makefile_target: test-mcp-collection-e2e` | Present |
| Explicit pytest timeout | Present (`timeout(10)`) |
| Runtime `test-mcp-collection-e2e` pack | Missing — follow-up (TD-1) |

Timeout-marker review: **no blocker**.

## Performance Concerns

None. Doc-lock is a Path/string offline assert. Future loopback e2e should
stay fast enough for default CI (four tools; ephemeral ThreadingHTTPServer).

## Deviations from Architecture

None. Step 4 delivered Decision Lock only; no harness code, matching
“Implementation in this ticket? No”.

## Follow-up Tasks

### TD-1 — High (main follow-up from architecture)

- **Title (proposed):** CI-safe Jira MCP collection e2e via loopback HTTP
  stand-in
- **Item:** Implement the in-process loopback HTTP stand-in and e2e pack
  sketched in `20-architecture.md` § Follow-up ticket (harness delivery):
  - Shared fixture (e.g. `pypost/fixtures/mcp_collection_http.py` or
    `tests/helpers/mcp_collection_http.py`) wrapping `ThreadingHTTPServer`
    on `127.0.0.1` with deterministic JSON for the four smoke routes
  - Test module (e.g. `tests/test_mcp_collection_e2e.py`) loading
    `examples/collections/jira_mcp.json`, registering the four tool ids on
    `live_mcp_server` **without** `execute_result` mock, pointing
    `jira_base_url` at the stand-in
  - Marker (e.g. `mcp_collection_e2e`) suitable for default CI
  - **Makefile target `test-mcp-collection-e2e`** wired into default
    `make test` / PR CI (secret-free; not opt-in live)
  - Docs covering coverage vs `make test-jira-mcp-live` /
    `make test-agent-e2e`
- **Out of v1:** WireMock/JVM, long-lived mock process, full curated write
  surface, agent UI e2e conversion
- **Estimate hint:** ~5 story points
- **Priority:** High
- **Jira:** [PYPOST-1053](https://pypost.atlassian.net/browse/PYPOST-1053)

### Accepted / out of scope (do not ticket from this story)

- Implementing the stand-in inside PYPOST-1045 (explicitly out of scope).
- Making live Jira smoke the primary CI path.
- Reusing `agent_e2e_http` patches as the primary collection MCP stand-in.
- New production observability for an analysis-only change.

## Blocker Review

| Check | Result |
| ----- | ------ |
| Temporary solutions / crutches | None that block analysis close |
| Missing tests with timeout markers | **None** — module `pytestmark` present |
| Mock server shipped in this ticket | **Correctly absent** (out of scope) |
| Decision Lock + green doc-lock | **Present / PASS** |
| Deviations from architecture | None |
| Acceptance gaps vs DoD | Inventory, recommendation, tool ids, follow-up sketch done |
| Merge / release blocker debt | **None** — TD-1 is the planned follow-up |

**SAFE TO CLOSE** — PYPOST-1045 analysis DoD is met; the only material
follow-up is High-priority harness delivery (TD-1), left unticketed here for
tech-debt sync / sprint planning.
