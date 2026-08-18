# PYPOST-1050: Technical Debt Analysis

**Verdict:** Technical debt and maintainability review complete. Implementation cleanly satisfies all requirements and Definition of Done items from [`10-requirements.md`](10-requirements.md) without introducing application code debt in `pypost/`. All tests in `tests/test_example_fixtures.py` include explicit module-level timeout markers (`pytestmark = pytest.mark.timeout(30)`). **SAFE TO CLOSE** for Step 7; proceed to Step 8 (Dev Docs).

Scope reviewed:
- `examples/collections/jira_mcp.json` (`jira-move-issues-to-backlog` `mcp_description` updated to document `(max 50 issues per batch)`).
- `examples/README.md` (`## Coverage vs gaps` updated to document `capped at ≤50 issues per batch by Jira Agile`).
- `tests/test_example_fixtures.py` (`JIRA_MCP_DISCOVERABILITY_SUBSTRINGS` updated to lock `"50"`; positive and mutation tests verified).
- `ai-tasks/PYPOST-1050/*` (workflow artifacts).
- Zero changes to product runtime code in `pypost/`.

---

## Shortcuts Taken

- **Locked lowercase substring `"50"` rather than exact-sentence equality or complex regex:**
  - *Rationale:* Following the discoverability contract pattern from PYPOST-1048, checking that `"50"` is present in `request.mcp_description.lower()` guarantees that the numeric batch limit constraint cannot be removed or altered without breaking the contract test. At the same time, it allows non-breaking cosmetic phrasing polish without brittle string comparisons.
- **Client-side request chunking omitted by design:**
  - *Rationale:* PyPost serves as a transparent API client and MCP bridge. AI planning agents and workflow orchestrators are responsible for partitioning bulk replanning workloads into valid batch sizes (≤50 issues). Adding implicit multi-batch looping inside the tool runner would obscure Jira rate limits, error handling boundaries, and transaction boundaries.
- **In-module constant table (`tests/test_example_fixtures.py`) rather than separate JSON catalog:**
  - *Rationale:* Prose discoverability substrings are test-only contracts without an external Atlassian REST endpoint path freshness dimension (unlike `jira_mcp_critical_rest_paths.json`). Defining `JIRA_MCP_DISCOVERABILITY_SUBSTRINGS` directly in `tests/test_example_fixtures.py` keeps test definitions cohesive and avoids unnecessary file overhead.
- **Offline fixture validation without live Jira API connectivity:**
  - *Rationale:* Contract tests load local JSON fixtures and companion environments via native parsers (`_load_jira_mcp_collection()`), enabling deterministic, sub-second, credential-free execution in CI/CD environments.
- **Step 8 developer documentation pending:**
  - *Rationale:* Updating `doc/dev/testing.md` to document `"50"` in the discoverability locked substring table and marking Definition of Done items in `10-requirements.md` is owned by Step 8 per workflow protocol.

---

## Code Quality Issues

- **No application code debt:** Zero lines of production code in `pypost/` were modified.
- **Test module consolidation:** `tests/test_example_fixtures.py` currently spans 800 lines and centralizes all fixture validation contracts (schema conformance, parameter declarations, pagination, secret policies, critical REST path locks, and discoverability substring contracts). The module is well-structured with clear section headers. If additional fixture test suites are introduced in the future, decomposing it into submodules under `tests/` may be considered.
- **Defensive input normalization:** `assert_jira_mcp_discoverability_guidance` checks `fragment not in guidance` where `guidance = request.mcp_description.lower()`. It assumes `required_substrings` elements are passed lowercased (enforced by convention and type annotations). Defensive normalization (`fragment.lower()`) could be added if external callers invoke it with mixed-case fragments.
- **Static analysis & formatting:**
  - `flake8 tests/test_example_fixtures.py` reports 0 errors/warnings.
  - `make lint` (`flake8 --jobs=1 pypost/`) reports 0 errors/warnings.
  - All lines in touched files are strictly ≤ 100 characters.
  - Fully typed with explicit type annotations.

---

## Missing Tests

| Scenario / Contract | Status | Description |
| ------------------- | ------ | ----------- |
| Shipped `jira-move-issues-to-backlog` carries `"50"`, `"membership"`, `"remove-from-sprint"` | Present | Parametrized positive contract test over `examples/collections/jira_mcp.json` |
| Shipped `jira-delete-sprint` carries `"irreversible"`, `"backlog"` | Present | Parametrized positive contract test over `examples/collections/jira_mcp.json` |
| Full-strip mutation detection for `jira-move-issues-to-backlog` | Present | Negative mutation test asserting `AssertionError` with all missing sorted fragments |
| Single-fragment partial strip mutation for `"50"` | Present | Parametrized mutation test asserting `AssertionError` when `"50"` is omitted |
| Single-fragment partial strip mutation across all other locked fragments | Present | Parametrized mutation tests for `"irreversible"`, `"backlog"`, `"remove-from-sprint"`, `"membership"` |
| Diagnostic message format verification | Present | Regex assertion verifying request ID and sorted missing fragments in `AssertionError` |
| Explicit pytest timeout markers | Present | Module-level `pytestmark = pytest.mark.timeout(30)` in `tests/test_example_fixtures.py` |
| Discoverability substring locks for remaining 21 Jira MCP tools | Missing | Not required; only high-risk sprint operations are locked |
| Live Jira API integration tests | Missing | Out of scope by design (offline deterministic contracts) |

### Timeout Marker Review
- **NO BLOCKER:** `tests/test_example_fixtures.py` declares module-level `pytestmark = pytest.mark.timeout(30)`. All 33 tests in the module execute in ~0.10s, well within the 30-second timeout allocation.

---

## Performance Concerns

- **Zero runtime performance impact:** Declarative metadata updates in JSON fixtures and markdown documentation introduce no compute, memory, or network overhead.
- **Test execution speed:** All 33 tests in `tests/test_example_fixtures.py` execute in ~0.10s.
- **Resource overhead:** In-memory string lowercasing and substring lookups in contract tests execute in sub-millisecond time.

---

## Follow-up Tasks

### NON-BLOCKER — pre-existing

- **Pre-existing Task Artifacts Baseline Drift:**
  - *Node IDs:* `tests/test_verify_ai_task_artifacts.py`, `tests/test_solid_audit_baseline.py`
  - *Details:* `scripts/verify_ai_task_artifacts.py` fails on historical completed tasks missing `70-dev-docs.md` (e.g., PYPOST-968, 974-976, etc.).
  - *Jira:* [PYPOST-1049](https://pypost.atlassian.net/browse/PYPOST-1049)

### Accepted / Out of Scope (No Ticket Required)

- **Expanding discoverability substring locks to non-sprint Jira MCP tools:**
  - *Status:* Unnecessary unless discoverability regressions or agent confusion occur for other Jira tools.
- **Client-side request chunking in PyPost core engine:**
  - *Status:* Intentionally out of scope; batching decisions remain the responsibility of the calling AI agent / orchestrator.
- **Decomposing `tests/test_example_fixtures.py` into multiple modules:**
  - *Status:* Current file structure is cohesive and maintainable at ~800 lines.

---

## Blocker Review

| Check | Requirement | Status | Notes |
| ----- | ----------- | ------ | ----- |
| **Pytest Timeouts** | Explicit timeout marker on all tests | PASS | `pytestmark = pytest.mark.timeout(30)` present at line 21 of `tests/test_example_fixtures.py` |
| **Test Suite** | All tests pass cleanly | PASS | 33 passed in `tests/test_example_fixtures.py`; `make check-mcp-fixtures` and `make check-jira-mcp-path-freshness` pass |
| **Static Analysis** | No linter errors or warnings | PASS | `make lint` and `flake8 tests/test_example_fixtures.py` report 0 errors |
| **Architecture & DoD** | Matches approved architecture | PASS | Matches `20-architecture.md` and fulfills `10-requirements.md` Definition of Done |
| **Verdict** | Gate readiness | **SAFE TO CLOSE** | No blockers found; ready for Step 7 review and proceeding to Step 8 |
