# PYPOST-1388: Technical Debt Analysis

## Shortcuts Taken

1. **Dual compile artifacts (trie + `_path_selectors` list)**:
   - `_compile` still builds both `PathSelectorTrie` (steady-state match path) and
     `list[CompiledPathSelector]` (kept for DEBUG `path_selectors_count` and the FR-2
     regression probe that wraps `_path_selectors` iteration).
   - Steady-state `matches` never scans the list; retaining it is intentional so the
     scaling test can detect a regression to linear rule walks without inventing a new
     production counter. Cost is one extra list append + object per hierarchical rule at
     compile time only.

2. **Unused `PathSelectorTrie.matches_tokens` helper left in place**:
   - Production callers use `matches_path_and_key` / `matches_shorthand_path_and_key`
     (iterate path + key without allocating a combined token list).
   - `matches_tokens` remains as a thin sequence-oriented API for future callers / docs;
     it is dead on the current hot path (flagged in Step 5 cleanup).

3. **FR-2 efficiency lock probes a private attribute**:
   - `test_hierarchical_lookup_scaling_bounded_by_depth_not_rule_count` replaces
     `engine._path_selectors` with `_CountingPathSelectors` rather than using a dedicated
     test-only match-probe seam on the trie.
   - Acceptable while the list exists; if the list is removed later, the test must move to
     an explicit private counter or instrumentation hook (architecture already allowed a
     private probe).

4. **Developer docs (addressed in Step 8)**:
   - Pre-trie wording in `doc/dev/json_selector_engine.md` / Hidden Fields / README /
     response_mask_worker links is refreshed for `PathSelectorTrie` + mutable breadcrumbs
     under Step 8 (`td-70-dev-docs`).

5. **No new selector syntax / streaming sanitizer**:
   - Per requirements out-of-scope: JSONPath filters, `..`, slices, and SAX/`ijson`
     streaming remain intentionally unimplemented. Semantic freeze preferred over expanding
     the vocabulary while optimizing evaluation.

## Code Quality Issues

1. **`CompiledPathSelector.matches` unused by the engine hot path**:
   - Tokenizer (`_parse_tokens`) remains the single normalization path feeding the trie;
     `CompiledPathSelector.matches` is only exercised by older PYPOST-1394 unit coverage.
   - Optional cleanup: demote the instance matcher to a test helper or drop it once those
     tests assert trie outcomes instead.

2. **Shorthand miss path rescans the breadcrumb**:
   - On hierarchical miss, `matches` runs `any(str(t) == "*" for t in path)` before a
     second trie walk. Correct and cheap for typical depths; a boolean “path contains `*`”
     flag maintained by push/pop would avoid the linear scan on every miss.

3. **Mutable counter via single-element list**:
   - `_redact_node` still threads `masked_count: list[int]` (pre-existing pattern from
     PYPOST-1394 / PYPOST-1378). Idiomatic alternatives (context object or returning count
     tuples) were not introduced to keep the diff focused on trie + breadcrumbs.

4. **`canonical_path` / `format_path_variants` still allocate combined token lists**:
   - Helpers build `list(path) + [key]` for string forms used by GUI span metadata and
     backward-compatible adapters. Not on the redact match hot path; micro-optimization
     only if span formatting becomes a measured bottleneck.

5. **Wildcard trie fan-out allocates per step**:
   - `PathSelectorTrie._step` builds a fresh `list` and `set` of active nodes per token.
   - Correct for overlapping exact/`*` edges; catalogs dominated by wildcards could see
     cursor-set growth. Acceptable for current enterprise catalog shapes; profile before
     inventing a DFA or bitset cursor representation.

## Missing Tests

1. **Timeout markers (do-testing)**:
   - **No blocker**: `tests/test_pypost_1388_failing_repro.py` declares
     `pytestmark = pytest.mark.timeout(30)`. Observability asserts live under
     `tests/test_pypost_1394_failing_repro.py` (existing module timeout). Zero new tests
     lack explicit timeout markers.

2. **Isolated `PathSelectorTrie` unit surface**:
   - Coverage is indirect via engine semantic locks and efficiency repros. There is no
     dedicated table-driven suite for insert dedupe (`size`), empty trie, shorthand-only
     walks, or `matches_tokens` vs `matches_path_and_key` equivalence.

3. **Hostile / extreme nesting**:
   - No automated case for JSON depth near Python’s recursion limit. Recursive
     `_redact_node` / formatter descent can still `RecursionError` on pathological trees
     (pre-existing constraint; normal REST payloads stay shallow).

4. **Streaming / partial-chunk sanitization**:
   - Still absent by product design; tracked historically as
     [PYPOST-1389](https://pypost.atlassian.net/browse/PYPOST-1389).

5. **Wildcard fan-out stress**:
   - Efficiency lock uses many *distinct exact* dotted rules (R=400) and asserts no linear
     `_path_selectors` scan. It does not stress catalogs where almost every segment is `*`
     and active trie cursors multiply.

## Performance Concerns

1. **Recursive tree walk retained**:
   - Redaction and GUI formatting remain recursive. Stack breadcrumbs removed per-level
     *list* allocation, but call-stack depth still tracks document depth. Iterative /
     trampoline traversal was out of scope.

2. **Second trie walk for shorthand**:
   - When the candidate path contains `*`, a full second walk runs after a miss. Preserves
     FR-4 shorthand semantics; only paid on array-traversed locations that miss the primary
     walk.

3. **Immutable output trees**:
   - `redact_tree` still allocates a parallel dict/list hierarchy so raw inputs stay
     immutable (hard constraint). Peak memory ~2× structure size during redact remains;
     streaming SAX (PYPOST-1389) is the path for multi-megabyte envelopes if MCP ever
     streams tool results.

4. **GUI span path string construction**:
   - Matched fields still call `canonical_path` (joined string) for revealable spans.
   - Unrelated to FR-2/FR-3 match cost; noted only if medium-document formatting budgets
     need further cuts beyond [PYPOST-1396](https://pypost.atlassian.net/browse/PYPOST-1396).

## Follow-up Tasks

| Item | Verdict | Jira / action | Notes |
| --- | --- | --- | --- |
| Remove or wire `PathSelectorTrie.matches_tokens`; optionally drop unused `CompiledPathSelector.matches` once 1394 tests migrate | NON-BLOCKER — new | [PYPOST-1542](https://pypost.atlassian.net/browse/PYPOST-1542) | Dead helper flagged in Step 5; no runtime impact; SP 2 |
| Replace `_path_selectors` FR-2 probe with private match-probe / drop dual list if DEBUG can use `trie_size` only | NON-BLOCKER — new | [PYPOST-1543](https://pypost.atlassian.net/browse/PYPOST-1543) | Keeps regression lock without compiling unused list; SP 2 |
| Shorthand “path has `*`” flag on breadcrumb push/pop | NON-BLOCKER — new | [PYPOST-1544](https://pypost.atlassian.net/browse/PYPOST-1544) | Avoids `any(...)` scan on hierarchical misses; SP 1 |
| Isolated `PathSelectorTrie` unit table + wildcard fan-out stress | NON-BLOCKER — new | [PYPOST-1545](https://pypost.atlassian.net/browse/PYPOST-1545) | Complements existing 1388 repro locks; SP 3 |
| Streaming / SAX JSON sanitizer for huge payloads | NON-BLOCKER — pre-existing | [PYPOST-1389](https://pypost.atlassian.net/browse/PYPOST-1389) | Out of scope; still valid if MCP streaming arrives |
| Medium-doc off-thread mask formatting | NON-BLOCKER — pre-existing | [PYPOST-1396](https://pypost.atlassian.net/browse/PYPOST-1396) | Consumer latency; engine work here does not replace it |
| `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics` | NON-BLOCKER — pre-existing | [PYPOST-1492](https://pypost.atlassian.net/browse/PYPOST-1492) | Snapshot vs live metrics drift; fails at base |
| `tests/test_http_client.py` (many `TestHTTPClient*` cases) | NON-BLOCKER — pre-existing | [PYPOST-1534](https://pypost.atlassian.net/browse/PYPOST-1534) | Fails at base |
| `tests/test_mcp_server_impl.py::TestMCPServerImpl::test_call_tool_applies_mcp_param_defaults_when_args_omitted` (+ 3 sibling identity/register failures) | NON-BLOCKER — pre-existing | [PYPOST-1535](https://pypost.atlassian.net/browse/PYPOST-1535) | Fails at base |
| `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift` | NON-BLOCKER — pre-existing / env drift | [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397) | `make check-lock-dev` stale lock; independent of selector work |
| `tests/test_bundled_examples_packaging.py::test_explicit_packages_cover_application_tree_and_examples` | NON-BLOCKER — pre-existing | [PYPOST-1474](https://pypost.atlassian.net/browse/PYPOST-1474) | Missing `pypost.ui.{models,views,workers}` packages |
| `tests/test_makefile_install_seed_contract.py::test_committed_seed_covers_independent_source_inventory` | NON-BLOCKER — pre-existing | [PYPOST-1474](https://pypost.atlassian.net/browse/PYPOST-1474) | Same packaging/seed inventory gap |
| `tests/test_pypost_1287_failing_repro.py::test_live_report_inventory_loc_matches_discovery` | NON-BLOCKER — pre-existing | [PYPOST-1475](https://pypost.atlassian.net/browse/PYPOST-1475) | Dialog LOC inventory drift |
| `tests/test_pypost_1077_verification_gates.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates` | NON-BLOCKER — pre-existing | [PYPOST-1475](https://pypost.atlassian.net/browse/PYPOST-1475) | Dialog audit aggregate coherence |
| `tests/test_mcp_server_integration.py::TestMCPServerIntegration::test_call_tool_substitutes_jira_mcp_json_body` | NON-BLOCKER — flaky | [PYPOST-1541](https://pypost.atlassian.net/browse/PYPOST-1541) | Port bind errno 98 under parallel `make test`; passes alone |

Repro for suite triage evidence: `make test` (full suite) and baseline worktree at
`4dc78f4346f3caf5bdf7e85244f51af6cf43cf1a`.

### Architecture adherence

- **No material deviation** from Step 2: in-module segment trie (exact + `*` edges), mutable
  breadcrumbs in engine redaction and `JsonMaskFormatter`, public `JsonSelectorEngine` API
  frozen, bare-key set unchanged, stdlib-only.
- Earlier debt notes that named “PYPOST-1398” for trie indexing alone were a mis-link; Jira
  [PYPOST-1398](https://pypost.atlassian.net/browse/PYPOST-1398) is an unrelated fold-helper
  Debt item. Trie + stack breadcrumbs are delivered by **this** ticket (PYPOST-1388).

### Blocker Classification

- **BLOCKER items**: 0 (including zero missing pytest timeout markers on new tests)
- **NON-BLOCKER items**: new engine-surface / test cleanups (PYPOST-1542–1545) + filed
  pre-existing suite failures (PYPOST-1492, 1534, 1535, 1397, 1474, 1475, 1541) + prior
  streaming/worker debts (1389, 1396)
- **Conclusion**: Nothing blocks closing Step 7 or proceeding to Step 8 (dev docs).
