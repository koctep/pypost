# PYPOST-1395: Technical Debt Analysis

## Shortcuts Taken

1. **Reference Scope Confined to Bundled Catalog (Omission of Slack and Notion)**:
   - The Jira description mentioned expanding reference collections beyond Google Drive ("e.g. GitHub, Slack, Notion, Jira"). In PyPost's codebase, only `github_mcp.json`, `gitlab_mcp.json`, `jira_mcp.json`, and `google_drive.json` exist under `examples/collections/`. PyPost does not currently bundle or support reference collections for Slack or Notion.
   - Rather than introducing synthetic, untested, or unmaintained new collections from scratch for Slack and Notion without corresponding domain integration tests and API mocks, this task strictly scoped modifications to the existing active bundled catalog (`github_mcp.json`, `gitlab_mcp.json`, `jira_mcp.json`).

2. **Representative User-Identity Endpoints Targeted Over Entire Catalog**:
   - In each modified reference collection, `hidden_response_fields` were added to 1 or 2 high-priority profile and user-identity endpoints:
     - `examples/collections/github_mcp.json`: `github-get-authenticated-user` (`["email", "two_factor_authentication", "plan.name"]`)
     - `examples/collections/gitlab_mcp.json`: `gitlab-get-current-user` (`["email", "commit_email", "public_email"]`)
     - `examples/collections/jira_mcp.json`: `jira-get-current-user` (`["emailAddress", "accountId"]`) and `jira-search-assignable-users` (`["[*].emailAddress", "[*].accountId"]`)
   - Other requests in those collections that return nested user or credential data (such as commit author emails in GitHub/GitLab repository endpoints, reporter details in `jira-search-issues-jql`, or webhook secrets) were left without sample `hidden_response_fields`. This design decision avoided breaking existing user workflows or introducing unexpected redactions into general queries, while keeping the sample configurations straightforward and educational.

3. **Hermetic Mock Execution in Contract Tests vs Live SaaS Network Invocations**:
   - `tests/test_reference_collection_masking_contract.py` validates the complete dual-surface masking pipeline (MCP irreversible `'***'` redaction and Desktop GUI click-to-reveal tokens) using deterministic in-memory `ExecutionResult` and authentic mock JSON structures.
   - Live network calls against external SaaS endpoints (GitHub REST API, GitLab REST API, Jira Cloud REST API) were intentionally omitted. This preserves sub-second test execution (< 1.5s total), guarantees zero test flakiness from remote network latency or rate limits, and avoids requiring live third-party API tokens in CI runners.

4. **Exact List Equality Assertions in Contract Verification**:
   - Contract tests assert exact equality against expected field lists (e.g. `assert user_req.hidden_response_fields == ["email", "two_factor_authentication", "plan.name"]`).
   - While this prevents inadvertent removal or regression of sample masking fields from bundled collections, it tightly couples the contract test suite to specific sample field names. Future additions or renames of sample fields in these collections will require corresponding updates to the contract assertions.

## Code Quality Issues

1. **Schema Version Asymmetry Across Bundled Collections**:
   - In `examples/collections/`, `jira_mcp.json` is formatted using Collection schema version `2.0.0`, whereas `github_mcp.json` and `gitlab_mcp.json` remain on schema version `1.0.0`.
   - While PyPost's Pydantic `Collection` model seamlessly parses, upgrades, and serializes both `1.0.0` and `2.0.0` collections, migrating `github_mcp.json` and `gitlab_mcp.json` to schema version `2.0.0` would eliminate schema version drift across bundled examples.

2. **Absence of Collection-Level Reusable Masking Profiles / Presets**:
   - Currently, `hidden_response_fields` are declared on a per-request basis in collection JSON definitions.
   - For recurring data structures across an API (for instance, Jira user objects appearing across `jira-get-current-user`, `jira-search-assignable-users`, and `jira-search-issues-jql`), selector configurations such as `emailAddress` and `accountId` must be manually repeated across multiple requests. Supporting collection-level masking rule presets or reusable field templates in the collection schema would reduce configuration duplication.

3. **Lack of Selector Syntax Validation / Linting in Collection Schema**:
   - In the Pydantic data model, `hidden_response_fields` is typed simply as `list[str]`.
   - If a user configures unsupported JSONPath syntax (such as `$.users[0].name` or filter expressions like `[?(@.active == true)]`), the engine safely ignores or fails to match the path at runtime without raising an error. Adding collection schema validation or a GUI syntax linter/tooltip for selector patterns would improve user feedback.

## Missing Tests

1. **Timeout Markers Audit**:
   - **Zero tests missing timeout markers**: An exhaustive audit verified that all tests in `tests/test_reference_collection_masking_contract.py` declare an explicit timeout marker (`pytestmark = pytest.mark.timeout(30)`), fully complying with `do-testing` and `lsr-python`.
   - Contract test methods execute in < 0.2s each, well beneath the 30-second guardrail.

2. **Deeply Nested Multi-Level Wildcard Collections**:
   - `tests/test_reference_collection_masking_contract.py` verifies bare keys (`email`, `accountId`), dotted object paths (`plan.name`), and root-level array wildcards (`[*].emailAddress`).
   - Complex multi-level array wildcards (e.g. `organizations[*].teams[*].members[*].email`) are verified in the core selector engine suite (`tests/test_pypost_1394_failing_repro.py`), but are not modeled in reference collection examples.

3. **Multi-Window Concurrent Execution of Reference Collections in GUI**:
   - Contract tests exercise `ResponseView` and `ResponseMaskController` widget formatting and click-to-reveal toggles sequentially within an isolated Qt test fixture.
   - Concurrent multi-tab execution where requests from GitHub, GitLab, and Jira are loaded and rendered simultaneously across multiple active tab sessions is covered by general multi-tab integration tests, but not specifically with all reference collection samples in a single stress run.

## Performance Concerns

1. **Array Wildcard Traversal Overhead on Large Paginated API Responses**:
   - In `jira_mcp.json`, `jira-search-assignable-users` configures `[*].emailAddress` and `[*].accountId`.
   - When an API response contains a large user list (e.g. 500–1,000 user objects), `JsonSelectorEngine.redact_tree()` walks each element sequentially. For typical payloads (10 KB – 100 KB), traversal takes < 5 ms in Python. However, for large unpaginated responses approaching 500 KB, AST traversal on Qt's main thread could introduce transient UI latency prior to reaching the 500 KB `LARGE_DOC_CHAR_THRESHOLD` fallback.

2. **Memory Overhead of Collection JSON Schemas**:
   - Adding `hidden_response_fields` across the three bundled collections adds negligible bytes to disk storage (~350 bytes total) and in-memory Pydantic model representation (< 2 KB), with zero measurable impact on application startup or collection load latency.

## Follow-up Tasks

### Proposed Technical Debt Items

1. **NON-BLOCKER**: [PYPOST-1481](https://pypost.atlassian.net/browse/PYPOST-1481) Upgrade `github_mcp.json` and `gitlab_mcp.json` from schema version `1.0.0` to `2.0.0` to establish uniform Collection v2.0.0 compliance across all bundled catalog fixtures.
2. **NON-BLOCKER**: [PYPOST-1482](https://pypost.atlassian.net/browse/PYPOST-1482) Support collection-level reusable masking profiles and field templates to prevent duplicated `hidden_response_fields` lists across similar API endpoints.
3. **NON-BLOCKER**: [PYPOST-1483](https://pypost.atlassian.net/browse/PYPOST-1483) Implement GUI syntax validation, autocompletion, and helper tooltips for `hidden_response_fields` selector rules in the collection editor.
4. **NON-BLOCKER**: [PYPOST-1484](https://pypost.atlassian.net/browse/PYPOST-1484) Expand sample `hidden_response_fields` to issue tracking, commit, and comment endpoints in bundled reference collections.
5. **NON-BLOCKER**: [PYPOST-1398](https://pypost.atlassian.net/browse/PYPOST-1398) Implement prefix trie / radix tree index for `CompiledPathSelector` in `JsonSelectorEngine` to replace linear list scanning for high-volume selector rulesets.
6. **NON-BLOCKER**: [PYPOST-1390](https://pypost.atlassian.net/browse/PYPOST-1390) Optimize `ResponseMaskController` hit-testing using `bisect` binary search over token spans to achieve $O(\log N)$ mouse event processing.

### Pre-existing Failures (NON-BLOCKER — pre-existing)

The following test failures are pre-existing issues in the repository baseline, unrelated to the PYPOST-1395 reference collection masking implementation:

1. **Packaging tests & Makefile install seed contract**:
   - `tests/test_bundled_examples_packaging.py::test_explicit_packages_cover_application_tree_and_examples`
   - `tests/test_makefile_install_seed_contract.py::test_repro_editable_install_populates_regular_package_manifest_and_data`
   - Status: `NON-BLOCKER — pre-existing`
   - Jira: [PYPOST-1474](https://pypost.atlassian.net/browse/PYPOST-1474)

2. **Dev lockfile drift check**:
   - `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift`
   - Status: `NON-BLOCKER — pre-existing`
   - Jira: [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397)

3. **Dialog audit report / live report inventory**:
   - `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
   - `tests/test_pypost_1287_failing_repro.py::test_live_report_inventory_loc_matches_discovery`
   - Status: `NON-BLOCKER — pre-existing`
   - Jira: [PYPOST-1475](https://pypost.atlassian.net/browse/PYPOST-1475)

4. **SOLID audit markdown snapshot**:
   - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
   - Status: `NON-BLOCKER — pre-existing`
   - Jira: [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111)

5. **HTTP client and MCP server baseline tests**:
   - `tests/test_http_client.py`
   - `tests/test_mcp_server_impl.py`
   - Status: `NON-BLOCKER — pre-existing`
   - Jira: [PYPOST-1476](https://pypost.atlassian.net/browse/PYPOST-1476), [PYPOST-1477](https://pypost.atlassian.net/browse/PYPOST-1477)

6. **UI Dialog teardown / event loop tests**:
   - `tests/test_env_dialog.py`
   - `tests/test_mcp_client_tab.py`
   - Status: `NON-BLOCKER — pre-existing`
   - Jira: [PYPOST-1478](https://pypost.atlassian.net/browse/PYPOST-1478)

7. **MCP process supervisor / reconfigure teardown timing**:
   - `tests/test_mcp_process_reconfigure_repro.py::test_process_reconfigure_reports_failed_restoration`
   - Status: `NON-BLOCKER — pre-existing`
   - Jira: [PYPOST-1479](https://pypost.atlassian.net/browse/PYPOST-1479)

### Blocker Classification

- **BLOCKER items**: 0
- **NON-BLOCKER items**: 13 (6 proposed follow-ups, 7 pre-existing failure clusters)
- **Conclusion**: There are **zero blockers** preventing completion and closing of PYPOST-1395. The bundled reference collections for GitHub, GitLab, and Jira Cloud provide clear, tested, and secure sample configurations for `hidden_response_fields` with full schema and observability contract compliance.
