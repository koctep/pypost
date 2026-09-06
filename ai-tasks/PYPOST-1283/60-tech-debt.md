# PYPOST-1283: Technical Debt Analysis

## Shortcuts Taken

1. **`MCPProxyServerImpl.overridable_keys_supplier` is interface parity only, with no
   enforcement behind it.** `MCPProxyServerImpl` (`pypost/core/mcp_proxy_server_impl.py`)
   gained the same constructor argument and `set_overridable_keys_supplier` method as
   `MCPServerImpl`, and it is threaded through the full supplier chain
   (`MCPServerManager` → `MCPServerRegistry` → `MCPProxyServerImpl`) identically to the real
   implementation. But the proxy forwards protocol calls to an upstream MCP server rather
   than building/executing a local HTTP request, so there is nothing local for it to apply
   an override to or reject an override against — the supplier is stored and never read.
   This is documented in-code (a comment on the field) and was a deliberate Iteration 5
   decision (see `00-roadmap.md` Step 4 Iteration 5) to keep the two implementations
   symmetric for callers (`MCPServerManager`, `MCPServerRegistry`) that construct either one
   interchangeably, rather than special-casing the proxy's constructor signature.
   - **Priority/Severity: Low.** No security gap today — the proxy has no local
     enforcement point to bypass because it never touches environment variables itself; an
     upstream MCP server, if any, is responsible for its own override policy. The risk is
     purely forward-looking: if `MCPProxyServerImpl` is ever extended to execute requests
     locally (rather than pure protocol forwarding), the stored-but-unused supplier could be
     mistaken for working enforcement by a future maintainer who doesn't re-read this
     comment.
   - **Rationale for not addressing now:** there is no local execution path to enforce
     against; adding real enforcement would be speculative work with no corresponding
     requirement, and requirements explicitly scope this task to environments actually used
     for MCP tool calls, not proxy forwarding semantics.

2. **The bundled `jira-create-issue` body template is a single hand-rolled Jinja
   mega-expression using unconditional `{% set %}` guards, not idiomatic Jinja.**
   (`examples/collections/jira_mcp.json`). The dual GUI/MCP path could have been written
   more readably with filters/ternaries (e.g. `{{ (mcp.request.issue_type | default("Task")) }}`),
   but `FunctionExpressionResolver` (pre-existing, not part of this task) only allows a bare
   safe-path or a single-arg allow-listed-function call inside `{{ }}` — no filters,
   ternaries, or method calls. Working around this required `{% set has_x = ... %}` /
   `{% if has_x %}` guard blocks, and — critically — all `{% set %}` statements had to stay
   **unconditional** (never nested inside an `{% if %}`) so that
   `McpSecretsPolicy.extract_environment_variable_names`'s use of Jinja's
   `meta.find_undeclared_variables` does not mistake the local `{% set %}` names for real
   environment variables that need hidden/override-visibility handling. This constraint and
   its reasoning live only in `00-roadmap.md` Step 4 Iteration 4 — not in the JSON file
   itself (JSON has no comment syntax) nor in any dev doc yet.
   - **Priority/Severity: Medium.** The current template is correct and tested, but a
     future engineer adding a second dual-mode example request (or modifying this one) has
     no in-repo guidance describing this constraint, and could easily reintroduce a
     conditionally-scoped `{% set %}` that silently breaks env-var-name discovery (a security-
     relevant path, since that discovery feeds hidden-key visibility filtering) without any
     test failing loudly enough to explain why.
   - **Rationale for not addressing now:** documenting this pattern belongs in Step 8 (Dev
     Docs), which is a separate, already-planned step in this same task's roadmap; writing
     the doc here would duplicate that step's scope. Flagged here so Step 8 does not miss it.

3. **Only one example request (`jira-create-issue`) was converted to the dual-mode
   GUI/MCP pattern; no reusable pattern or helper was extracted.** Every other request in
   `examples/collections/jira_mcp.json` (e.g. create-comment, transition-issue, etc., all
   the "hand a whole payload through `mcp.request.*_payload`" shaped requests noted in
   `20-architecture.md`'s Research section) is unchanged and remains agent-only/GUI-unusable
   in the same way `jira-create-issue` was before this task. The task's requirements
   explicitly scoped only `jira-create-issue` for rework ("only `jira-create-issue` is being
   reworked for dual use; other Jira requests in the collection are unaffected" —
   `10-requirements.md`), so this is not a missed requirement, but it does mean the
   "GUI-usable by default" bar this task establishes for one example request is not yet the
   norm for the rest of the bundled collection.
   - **Priority/Severity: Low.** No functional gap against this task's Definition of Done;
     purely a product-completeness observation about the bundled examples as a whole.
   - **Rationale for not addressing now:** explicitly out of scope per Step 1 requirements;
     reworking the remaining requests would be new scope requiring its own
     requirements/architecture pass, not a Step 7 fix-up.

4. **No new GUI widget for structured issue fields — the Body JSON editor is reused as-is.**
   Per `20-architecture.md`'s Key Decision 7 and Q&A, a GUI user fills in `issue_type`,
   `summary`, and `description` by editing literal text and `to_adf(...)` calls directly
   inside the existing Body JSON editor, rather than through dedicated labeled input fields
   (a title box, a description textarea, a project-key dropdown, etc.). This satisfies "no
   hand-written ADF/JSON" (the stated pain point) but a GUI user customizing the default
   `summary`/`issue_type` literals still needs to locate and edit them inside a JSON-shaped
   text blob, which is friendlier than before but not a first-class form UI.
   - **Priority/Severity: Low.** Deliberate, requirements-driven scope boundary, not an
     oversight — `10-requirements.md`'s Scope — out explicitly excludes "general rework of
     the environment or MCP permission/config system beyond the single new per-variable
     override permission," and the architecture's entity list names no new request-editor
     widget.
   - **Rationale for not addressing now:** a structured-fields form editor is a
     meaningfully larger UI feature (new widget, new persistence shape for structured
     fields distinct from the free-form Body string) that was never in this task's approved
     requirements or architecture; building it here would be uncontrolled scope creep.

5. **`to_adf`'s paragraph-splitting only recognizes an exact double-newline (`"\n\n"`) as
   a paragraph boundary.** (`pypost/core/adf.py`). Three or more consecutive newlines
   produce one or more empty-string blocks, which `to_adf` maps to empty ADF paragraphs
   (valid per the module's own empty-string handling, but likely not what a user intended
   when leaving extra blank lines). Windows-style line endings (`"\r\n\r\n"`) are not
   normalized before splitting and would not be recognized as a paragraph boundary at all,
   producing a description with embedded literal `\r\n\r\n` inside a single paragraph's text
   node instead of separate paragraphs.
   - **Priority/Severity: Low.** Cosmetic/UX edge case, not a correctness or security
     issue — `json.dumps` still produces valid JSON either way, and Jira Cloud will still
     accept the ADF document; only the visual paragraph breaks may not match user intent for
     Windows-authored text or text with irregular blank-line runs.
   - **Rationale for not addressing now:** the requirements' three explicit `to_adf`
     acceptance cases (single-line, blank-line-separated multi-paragraph, empty string — all
     covered by `tests/test_adf.py`) do not exercise CRLF or 3+-newline input; there is no
     requirement calling for input normalization, and guessing at additional normalization
     rules without a concrete user story risks over-engineering a "pure, Jira-agnostic"
     helper (Key Decision 5 in `20-architecture.md`) with speculative behavior.

## Code Quality Issues

- The `jira-create-issue` `body` field in `examples/collections/jira_mcp.json` is a single
  very long JSON string value containing an entire multi-statement Jinja template with no
  internal line breaks (JSON strings cannot contain literal newlines without escaping,
  and the project's existing example-fixture style keeps bodies as single-line JSON
  strings). This is consistent with every other request body in the same collection file
  (pre-existing convention, not introduced by this task) but the specific body added here is
  the longest and most logically complex one in the file, making it harder to read/diff than
  a hypothetical multi-file or externally-templated request body would be. No action taken:
  changing the collection's body-storage format (e.g. to support multi-line template
  authoring) is a tooling/format change well outside this task's scope.
- `MCPServerImpl._request_overridable_env_names` and `list_tools`'s schema-advertisement
  loop (`pypost/core/mcp_server_impl.py`) duplicate the "effective overridable keys, then
  intersect with request-referenced env-var names" computation that
  `McpSecretsPolicy.effective_overridable_keys` already centralizes for the enforcement
  path — this is unavoidable duplication of *call sites*, not logic (the actual set-math
  still routes through the one shared static method), so it is not flagged as a shortcut,
  just worth noting for a future reader looking for "the one place overrides are computed."

## Missing Tests

- No test exercises `MCPProxyServerImpl` actually *attempting* an override through
  `set_overridable_keys_supplier` end-to-end (i.e. proving the supplier is genuinely inert
  for the proxy's call path) — existing tests only cover that the constructor accepts and
  stores the supplier (parity/no-crash), matching the "interface parity only" design
  documented above. A test asserting no-op behavior would mostly test the *absence* of a
  feature and was judged low-value relative to the explicit in-code documentation of the
  design choice; flagged here rather than added, since a well-named absence-of-behavior test
  can be brittle (it would need to be revisited the moment the proxy gains local execution,
  at which point it should become a real enforcement test instead).
- No test renders the `issue_payload` fallback path of the reworked `jira-create-issue`
  body through the *current* (post-injection-fix) template to confirm the verbatim-payload
  branch still round-trips unchanged JSON end-to-end via `TemplateService` — the fallback
  branch (`{% if has_payload %}{{ mcp.request.issue_payload }}{% endif %}`) is logically
  untouched by the Iteration 7 `to_json_string` fix (which only touched the structured-path
  literals), and is implicitly covered by the pre-existing
  `tests/test_example_fixtures.py`/`tests/test_mcp_collection_e2e.py`/
  `tests/test_mcp_server_integration.py` suites passing, but there is no single test with a
  name that specifically documents "issue_payload fallback still works after the structured
  path was added." Low risk (existing suites are green and would fail if this regressed),
  but a dedicated test would make the fallback's continued support more discoverable in the
  test file itself rather than only in the roadmap's iteration notes.
- All Python/pytest test files touched or added by this task were verified in Step 5 (Code
  Cleanup) to declare explicit `pytest.mark.timeout(...)` markers per `do-testing` — this was
  a **blocker-class** check and was confirmed passing (`40-code-cleanup.md`), so there is no
  outstanding timeout-marker debt to record here.

## Performance Concerns

None identified. Override enforcement (`McpSecretsPolicy.effective_overridable_keys` /
`apply_permitted_overrides`, `validate_environment_overrides`) is O(number of call
arguments) set-membership work inside the existing MCP preflight/execution-variable-build
path, already covered by the existing `track_mcp_tool_call_duration` metric
(`50-observability.md`). `to_adf`/`to_json_string` are pure, single-pass string/JSON
operations over one field's text at render time, with no loops over external data. No new
I/O, no new network calls, no new persistence format requiring migration.

## Follow-up Tasks

1. **[Medium]** Document the `{% set %}` / `meta.find_undeclared_variables` interaction
   constraint (unconditional `{% set %}` required so `McpSecretsPolicy` env-var-name
   discovery isn't fooled by local template variables) as part of Step 8 Dev Docs, so future
   authors of additional dual-mode GUI/MCP request bodies don't silently break hidden-key
   visibility filtering. Owner: this task's own Step 8 — not a new Jira ticket, called out
   here so Step 8 doesn't drop it.
2. **[Low]** If `MCPProxyServerImpl` is ever extended to execute requests locally instead of
   pure protocol forwarding, revisit `overridable_keys_supplier` there and give it real
   enforcement (mirroring `MCPServerImpl`'s `validate_environment_overrides` /
   `apply_permitted_overrides` calls) instead of parity-only storage. No ticket needed until
   that extension is actually planned — recorded here so it isn't forgotten if/when it is.
3. **[Low]** Consider normalizing line endings (CRLF → LF) and collapsing runs of 3+
   newlines to a single paragraph boundary in `to_adf` (`pypost/core/adf.py`) if real-world
   usage surfaces malformed paragraph breaks from Windows-authored or copy-pasted
   descriptions. No user report or requirement currently calls for this; do not action
   without one.
4. **[Low]** Extend the bundled example collection's dual-mode (GUI + MCP) pattern to the
   other Jira requests in `examples/collections/jira_mcp.json` that still require a
   hand-assembled `mcp.request.*_payload` for GUI use, following the precedent this task
   establishes for `jira-create-issue`. Out of scope for this task per its own requirements;
   worth a future backlog item if bundled-example GUI-usability is a recurring goal.
5. **[Low]** Consider a dedicated regression test explicitly asserting the `issue_payload`
   fallback path of `jira-create-issue` still renders the verbatim payload unchanged after
   the Iteration 7 JSON-escaping fix, distinct from the existing indirect coverage via the
   broader e2e/integration suites.

No pre-existing test failures were newly discovered during this Step 7 analysis beyond
those already fully triaged and documented in `00-roadmap.md` (Step 4 Iterations 6–7) and
`40-code-cleanup.md`:
`tests/test_environment_export_ui.py` (SIGSEGV, Qt/offscreen crash, unrelated to this
task), `tests/test_function_expression_resolver.py::test_malformed_nested_expressions`,
`tests/test_function_expression_resolver.py::test_standalone_malformed_closing_paren`,
`tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`,
`tests/test_template_service.py::test_validate_malformed_nested_alignment`,
`tests/test_template_service.py::test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover`
— all **NON-BLOCKER — pre-existing**, reproduced identically on `git stash` per the
roadmap's own verification, no PYPOST-1283 ticket association since they predate and are
independent of this task's diff.
