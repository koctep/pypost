# PYPOST-1048: Technical Debt Analysis

**Verdict:** Maintainability and test contract debt analysis complete. Delivery matches architecture (locked `mcp_description` discoverability substrings for `jira-delete-sprint` and `jira-move-issues-to-backlog` in `tests/test_example_fixtures.py`). No application code debt in `pypost/`, no missing pytest timeouts, no merge blockers. **SAFE TO CLOSE** for Step 7; proceed to Step 8 (Dev Docs).

Scope reviewed:
- `tests/test_example_fixtures.py` (constant table `JIRA_MCP_DISCOVERABILITY_SUBSTRINGS`, shared checker `assert_jira_mcp_discoverability_guidance`, positive parametrized tests, and full/partial mutation tests).
- `ai-tasks/PYPOST-1048/*` (workflow artifacts).
- Zero changes to application source (`pypost/`) or fixture JSON (`examples/collections/jira_mcp.json`).

---

## Shortcuts Taken

- **Meaning-bearing lowercase substring matching instead of exact-sentence or AST matching:**
  - *Rationale:* Per requirements in [`10-requirements.md`](10-requirements.md), descriptive phrasing is allowed to evolve as long as critical consequences and meanings survive. Exact string equality would introduce brittle test failures on trivial copy edits, while NLP/AST parsing would introduce unnecessary dependencies. Lowercase substring matching provides a resilient and deterministic contract.
- **In-module constant table (`tests/test_example_fixtures.py`) rather than external JSON catalog:**
  - *Rationale:* Following the pattern established in PYPOST-1028 (Option A), prose discoverability strings have no upstream Atlassian REST freshness dimension (unlike the critical REST paths in PYPOST-1030). A test-module constant table avoids unnecessary JSON file overhead.
- **Targeted scope (2 of 23 Jira MCP tools):**
  - *Rationale:* Locks are specifically focused on high-risk sprint management actions (`jira-delete-sprint` and `jira-move-issues-to-backlog`) where ambiguity could lead an AI agent to perform irreversible deletions or misunderstand backlog membership clearance. The remaining 21 Jira MCP tools are not locked for description text.
- **Offline contract tests only:**
  - *Rationale:* Native collection loading (`_load_jira_mcp_collection()`) without live Jira connectivity or AI agent execution ensures fast, deterministic, credential-free CI execution.
- **Step 8 dev documentation pending:**
  - *Rationale:* Updating `doc/dev/testing.md` with the fifth `assert_jira_mcp_*` agreement and checking Definition of Done items in `10-requirements.md` is owned by Step 8.

---

## Code Quality Issues

- **No application code debt:** No production code in `pypost/` was modified.
- **Test module size:** `tests/test_example_fixtures.py` has grown to ~797 lines. It serves as the centralized fixture contract suite for `examples/collections/jira_mcp.json` and companion environments. Code is well-structured and separated by clear comment headers; if additional fixture test suites are introduced in the future, decomposing into submodules under `tests/` could be considered.
- **Checker parameter assumption:** `assert_jira_mcp_discoverability_guidance` checks `fragment not in guidance` where `guidance = request.mcp_description.lower()`. It assumes elements of `required_substrings` are passed in lowercase (which `JIRA_MCP_DISCOVERABILITY_SUBSTRINGS` adheres to). Defensive normalization (`fragment.lower()`) could be added if external callers invoke it with mixed-case fragments.
- **Static analysis & formatting:**
  - Fully compliant with PEP 8 and repo conventions.
  - All lines <= 100 characters.
  - `flake8 tests/test_example_fixtures.py` reports 0 errors/warnings.
  - Fully typed with explicit type annotations (`tuple[tuple[str, tuple[str, ...]], ...]`, `Sequence[str]`).

---

## Missing Tests

| Scenario | Status | Description |
| -------- | ------ | ----------- |
| Shipped `jira-delete-sprint` carries `irreversible` and `backlog` | Present | Parametrized positive lock over `examples/collections/jira_mcp.json` |
| Shipped `jira-move-issues-to-backlog` carries `remove-from-sprint` and `membership` | Present | Parametrized positive lock over `examples/collections/jira_mcp.json` |
| Full-strip mutation detection for `jira-delete-sprint` | Present | Negative mutation test with diagnostic regex assertion |
| Full-strip mutation detection for `jira-move-issues-to-backlog` | Present | Negative mutation test with diagnostic regex assertion |
| Single-fragment partial strip mutation across all locked fragments | Present | Parametrized mutation test (4 cases) ensuring each fragment is independently required |
| Diagnostic message format verification | Present | Mutations verify request ID and sorted missing fragments in `AssertionError` |
| Explicit pytest timeout markers | Present | Module-level `pytestmark = pytest.mark.timeout(30)` |
| Discoverability locks for remaining 21 Jira MCP tools | Missing | Not required by PYPOST-1048 scope |
| Mixed-case `required_substrings` input test | Missing | Minor edge case; checker docstring specifies lowercase contract |
| Live Jira API / MCP runtime integration | Missing | Out of scope by design (offline deterministic contracts) |

### Timeout Marker Review
- **NO BLOCKER:** `tests/test_example_fixtures.py` declares `pytestmark = pytest.mark.timeout(30)`. All 32 tests complete in ~0.10s total.

---

## Performance Concerns

- **Zero runtime performance impact:** No production code or request dispatch pathways were modified.
- **Test execution speed:** Entire test module runs 32 tests in ~0.10s in pytest, well within the 30s timeout budget.
- **Resource overhead:** In-memory string lowercasing and substring lookups are instantaneous and introduce negligible CPU/memory usage.

---

## Follow-up Tasks

### NON-BLOCKER — pre-existing

- **Pre-existing Task Artifacts Baseline Drift:**
  - *Node IDs:* `tests/test_verify_ai_task_artifacts.py`, `tests/test_solid_audit_baseline.py`
  - *Details:* `scripts/verify_ai_task_artifacts.py` fails on historical completed tasks missing `70-dev-docs.md` (e.g. PYPOST-968, 974-976, etc.).
  - *Jira:* [PYPOST-1049](https://pypost.atlassian.net/browse/PYPOST-1049)

### Follow-up from PYPOST-1047

- **Document Agile API Batch Limits in Backlog Move Description:**
  - *Details:* Mention the official Jira Software Agile API batch limit (<= 50 issues per `POST /rest/agile/1.0/backlog/issue`) in `jira-move-issues-to-backlog` `mcp_description` and `examples/README.md`.
  - *Jira:* [PYPOST-1050](https://pypost.atlassian.net/browse/PYPOST-1050)

### Accepted / Out of Scope (No Ticket Required)

- Expanding description substring locks to non-sprint Jira MCP tools unless discoverability regressions occur.
- Decomposing `tests/test_example_fixtures.py` into separate files (current file length ~797 lines is clean and cohesive).
- Live Jira network testing for fixture validation.
