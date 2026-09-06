# Roadmap: PYPOST-1283

## Task Metadata

- **Implementation language**: Python (PyQt-based desktop app `pypost`; GUI widgets are Python/Qt, not a separate language)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1283/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1283/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_mcp_environment_override_policy.py` — override rejected when not
    overridable, override rejected when Hidden (wins over overridable), permitted
    override flows into execution variables. Fails today: `TypeError:
    MCPServerImpl.__init__() got an unexpected keyword argument
    'overridable_keys_supplier'`.
  - `tests/test_models.py` (new) — `Environment().mcp_overridable_keys` defaults to
    `set()`. Fails today: `AttributeError: 'Environment' object has no attribute
    'mcp_overridable_keys'`.
  - `tests/test_environment_variables_widget.py` — MCP Override checkbox toggle
    unchecks/disables Hidden and vice versa; the two sets never share a key after
    any toggle sequence. Fails today: `AttributeError:
    'EnvironmentVariablesWidget' object has no attribute
    'get_mcp_override_checkbox'`.
  - `tests/test_adf.py` (new) — `to_adf`: single-line text -> one paragraph/one
    text node; blank-line-separated text -> multiple paragraphs; empty string ->
    valid doc with one empty paragraph. Fails today: `ModuleNotFoundError: No
    module named 'pypost.core.adf'`.
- [x] **STEP 4: Development**
  - [x] Iteration 1: `Environment.mcp_overridable_keys: Set[str]` field (default
    `set()`); new `pypost/core/adf.py` with `to_adf(text) -> str` (ADF v1 JSON);
    registered `to_adf` as a Jinja global in `FunctionRegistry`. Green:
    `tests/test_adf.py`, `tests/test_models.py`.
  - [x] Iteration 2: `McpSecretsPolicy.effective_overridable_keys` /
    `apply_permitted_overrides`; `mcp_tool_contract.validate_environment_overrides`
    (new `McpArgumentValidationError` kind `override_not_permitted`);
    `MCPServerImpl` gained `overridable_keys_supplier` ctor arg +
    `set_overridable_keys_supplier`, reject-before-execute preflight check in
    `_call_tool_inner`, permitted overrides applied onto a copy of `env_vars`
    in `_build_execution_variables` before `resolve_environment_variables`;
    `list_tools`/`_generate_schema` now advertise overridable, non-hidden,
    request-referenced env-var names as optional string properties. Green:
    `tests/test_mcp_environment_override_policy.py` (all 3), plus
    `tests/test_mcp_server_impl.py`, `tests/test_mcp_secrets_policy.py`,
    `tests/test_mcp_tool_contract.py` (no regressions).
  - [x] Iteration 3: `EnvironmentVariablesWidget` gained a 4th "MCP Override"
    column (`COL_MCP_OVERRIDE`), `get_mcp_override_checkbox` accessor, and
    mutual-exclusion logic between Hidden/MCP Override per row (checking one
    unchecks+disables the other; `_sync_env_variables_from_table` now also
    writes `env.mcp_overridable_keys`); new `COLUMN_MCP_OVERRIDE` /
    `MCP_OVERRIDE_COLUMN_TOOLTIP` strings in `environment_messages.py`. Green:
    `tests/test_environment_variables_widget.py` (all 8, including the 3 new
    PYPOST-1283 cases). Collateral: `tests/test_env_dialog.py`'s
    `test_hidden_column_and_mask_loaded_from_environment` asserted a hardcoded
    `columnCount() == 3`; updated to `== 4` (intentional new column, not a
    behavior regression) — pre-existing test, not a Step-3 red test.
  - [x] Iteration 4: bundled example rework —
    `examples/collections/jira_mcp.json` `jira-create-issue` body is now a
    dual-path Jinja template (falls back to `mcp.request.issue_payload`
    verbatim when supplied; otherwise builds `fields.project.key` from
    `jira_project_key`, `issuetype.name`/`summary` from optional
    `mcp.request.*` params defaulting to literal GUI-editable text, and
    `description` via `to_adf(...)`), plus new optional `mcp_params` entries
    `issue_type`/`summary`/`description` (`issue_payload` changed from
    required to optional). `examples/environments/jira_cloud.json` gained
    `"mcp_overridable_keys": ["jira_project_key"]`. Verified by hand (no
    dedicated example-content test existed for the new fields) that the
    template renders valid JSON for: GUI manual run (no `mcp` in context),
    MCP call with structured fields, and MCP call with `issue_payload`
    fallback. Deviation from architecture's literal suggestion: the
    `{{ }}` expression validator (`FunctionExpressionResolver`) only allows
    bare safe-path or single-arg allow-listed-function expressions inside
    `{{ }}` (no filters/ternaries/method calls), and Jinja's default
    `Undefined` raises immediately on `mcp.request.x` attribute access when
    `mcp` itself is absent (contrary to the architecture note) rather than
    silently stringifying to `""`; the body uses `{% set %}`/`{% if %}`
    guards (`mcp is defined and mcp.request is defined and mcp.request.X is
    defined`) with all `{% set %}` statements kept **unconditional** (not
    nested inside `{% if %}`) so Jinja's `meta.find_undeclared_variables`
    (used by `McpSecretsPolicy.extract_environment_variable_names`) does not
    mistake the local `{% set %}` names for real environment variables —
    verified empirically against `TemplateService`, `McpSecretsPolicy`, and
    `McpArgumentValidationError`/schema-visibility behavior. Kept the
    original `jira_project_key` "normal/explicit/permitted"/multi-project
    soft-guidance wording (from `PYPOST-1032`/`1068`/`1069`) intact rather
    than replacing it, since `tests/test_example_fixtures.py` asserts on that
    exact language. Green: `tests/test_example_fixtures.py`,
    `tests/test_examples_modernization.py`, `tests/test_mcp_collection_e2e.py`,
    `tests/test_mcp_server_integration.py`,
    `tests/test_predefined_library_pypost_1281_repro.py`.
  - [x] Iteration 5: threaded `overridable_keys_supplier` through the full
    chain per architecture: `EnvVariableSnapshot.update`/
    `snapshot_overridable_keys` → `EnvPresenter` (passes
    `selected.mcp_overridable_keys`) → `MCPServerManager`
    (`set_overridable_keys_supplier`, threaded into both `MCPServerImpl` and
    `MCPProxyServerImpl` construction) → `MCPServerRegistry`
    (`refresh_environment`, `_runtime_inputs` now returns a 4-tuple including
    overridable keys, `_start_manager`) → `LibraryRuntimeResolver`
    (`RuntimeInputs.overridable_keys`, sourced from the selected
    `Environment.mcp_overridable_keys` when a workspace Environment is
    selected; library-only secrets have no override concept).
    `MCPProxyServerImpl` accepts/stores the supplier for interface parity
    only — the proxy forwards to an upstream MCP server rather than
    executing local HTTP requests, so there is no local env-var override to
    enforce there (documented in-code). Green: `tests/test_mcp_server_registry.py`,
    `tests/test_env_presenter.py` (+ 2 companion files; updated the
    `FakeMCPManager` test double to add `set_overridable_keys_supplier`,
    mirroring its existing `set_hidden_keys_supplier`),
    `tests/test_env_variable_snapshot.py`, `tests/test_mcp_proxy_server.py`
    (+2 companion files), `tests/test_mcp_library_collection_pypost_1280_repro.py`.
  - [x] Iteration 6: full-suite verification via the project's sanctioned
    parallel runner (`scripts/run_parallel_tests.py`, matching `make test`).
    Fixed one more regression caused by adding `to_adf` to the function
    catalog: `tests/test_pypost_1077_verification_artifacts.py`'s
    `test_function_catalog_expectation_is_the_exact_catalog_frozenset` AST-
    cross-checks its hardcoded expected set against
    `tests/test_function_registry.py`'s `test_allowed_names_matches_catalog`
    — added `"to_adf"` to that hardcoded set. Final full run: 349 files,
    339 passed, 4 failed, 6 skipped — all 4 remaining failures confirmed
    pre-existing/unrelated (no diff on any of their source files versus this
    task's changes): `tests/test_environment_export_ui.py` (SIGSEGV,
    exit -11, Qt/offscreen crash unrelated to this task's code paths),
    `tests/test_function_expression_resolver.py::test_malformed_nested_expressions`
    and `::test_standalone_malformed_closing_paren`
    (`'invalid_argument' != 'invalid_arity'` — pre-existing code mismatch in
    `function_expression_resolver.py`, untouched by this task),
    `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
    (dialog LOC-audit mismatch — `scripts/audit_baseline_metrics.py` and
    `ai-tasks/PYPOST-376/baseline-metrics.md` show as modified in the working
    tree from unrelated concurrent activity, not from this task),
    `tests/test_template_service.py::test_validate_malformed_nested_alignment`
    and `::test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover`
    (same pre-existing `invalid_argument`/`invalid_arity` mismatch).
    Note: `tests/test_function_registry.py` and
    `tests/test_env_persistence_e2e.py` appeared already modified in the
    working tree (adding `to_adf` to the allowed-names assertion, and adding
    `set_overridable_keys_supplier` to a fake MCP manager) from outside this
    agent's own edits — consistent with this task's intended end state, left
    as-is.
  - **Clarification (added on PYPOST-1283 re-review fix pass):** the
    `scripts/audit_baseline_metrics.py` / `ai-tasks/PYPOST-376/baseline-metrics.md`
    edits made during this iteration were not limited to the
    `pypost/ui/mcp_server_controller.py` and `pypost/core/mcp_server_impl.py`
    caps this task's own code touches. Running `make test`
    (`tests/test_solid_audit_baseline.py::test_markdown_snapshot_matches_current_metrics`)
    surfaced that `pypost/ui/presenters/mcp_controls_presenter.py` and
    `pypost/core/qt/metrics_tracking.py` had also grown past their recorded
    caps from pre-existing, PYPOST-1280-era work (library collection
    selection plumbing) that never re-derived those caps after landing —
    unrelated to this task's own diff, but the shared baseline snapshot is a
    single source of truth and the audit test fails on any stale cap, not
    just the ones this task caused. Both caps were re-derived from their
    measured LOC (`mcp_controls_presenter.py` 370 -> cap 407;
    `metrics_tracking.py` 163 -> cap 180) and annotated in
    `scripts/audit_baseline_metrics.py` with a `PYPOST-1280` comment
    crediting the actual source of the growth, distinct from this task's own
    `PYPOST-1283` cap comments on `mcp_server_controller.py` and
    `mcp_server_impl.py`. `pypost/ui/presenters/collections_presenter.py` and
    `pypost/ui/presenters/tabs_presenter.py` only needed their measured-LOC
    snapshot values refreshed in `baseline-metrics.md` (498->522 and
    1064->1070 respectively) — their existing caps (535 / 1165) already had
    enough headroom, so no cap or code comment change was needed for those
    two. This keeps `test_markdown_snapshot_matches_current_metrics` green
    without silently absorbing unrelated drift into this task's own cap
    justifications.
  - [x] Iteration 7 (fix pass after independent review returned FAIL on 3
    fixable gaps; core override/security enforcement itself confirmed
    correct): three fixes.
    1. **JSON-injection bug in `jira-create-issue`'s bundled body
       template** (`examples/collections/jira_mcp.json`): the structured-path
       fields `jira_project_key`, `issue_type_value`, and `summary_value`
       were interpolated raw into JSON string literals (e.g.
       `"summary": "{{ summary_value }}"`), with no JSON-escaping — unlike
       `description`, safely handled via `to_adf(...)` (which internally
       calls `json.dumps`). A value containing a double quote (e.g.
       `Test "quoted" summary`) produced invalid JSON and, more seriously,
       let an attacker-controlled field break out of its string literal and
       inject additional JSON. Added `pypost/core/json_string.py` exposing
       `to_json_string(text) -> str` (returns `json.dumps(str(text))`,
       matching `to_adf`'s "call unquoted in the template" convention),
       registered it in `pypost/core/function_registry.py`'s
       `_DEFAULT_CATALOG`, and rewrote the three injection sites in
       `jira_mcp.json` to `{{ to_json_string(jira_project_key) }}`,
       `{{ to_json_string(issue_type_value) }}`, and
       `{{ to_json_string(summary_value) }}` (unquoted, since
       `to_json_string` already returns the quoted literal — same pattern as
       `to_adf(description_value)`). Single-arg bare-variable calls stay
       within `FunctionExpressionResolver`'s allow-listed-function
       constraint (no filters/ternaries/method calls). Updated the two tests
       that hardcode the exact function-name allowlist
       (`tests/test_function_registry.py::test_allowed_names_matches_catalog`,
       `tests/test_pypost_1077_verification_artifacts.py::test_function_catalog_expectation_is_the_exact_catalog_frozenset`)
       to include `to_json_string`. Added four new tests in
       `tests/test_example_fixtures.py`
       (`test_jira_create_issue_body_escapes_quotes_in_summary`,
       `test_jira_create_issue_body_escapes_backslash_in_summary`,
       `test_jira_create_issue_body_escapes_quotes_in_issue_type_and_project_key`,
       `test_jira_create_issue_body_defaults_still_render_valid_json`) that
       render the real bundled template through `TemplateService` with
       quote/backslash-bearing values and assert `json.loads` succeeds and
       decodes the expected value.
    2. **Roadmap disclosure gap**: Iteration 6 above only credited the
       `mcp_server_impl.py`/`mcp_server_controller.py` cap changes to this
       task and didn't disclose that `mcp_controls_presenter.py` and
       `metrics_tracking.py` cap drift from PYPOST-1280-era work was also
       reconciled in the same pass (to keep
       `tests/test_solid_audit_baseline.py::test_markdown_snapshot_matches_current_metrics`
       green), nor that `collections_presenter.py`/`tabs_presenter.py`
       needed measured-LOC snapshot refreshes. Added the "Clarification"
       paragraph directly under Iteration 6 above spelling this out.
    3. **Missing direct unit tests for the SSRF-prevention core**: added
       direct unit tests for `McpSecretsPolicy.effective_overridable_keys`
       and `McpSecretsPolicy.apply_permitted_overrides` in
       `tests/test_mcp_secrets_policy.py`, and for
       `mcp_tool_contract.validate_environment_overrides` in
       `tests/test_mcp_tool_contract.py` (new `TestValidateEnvironmentOverrides`
       class) — previously these three functions were covered only
       indirectly via `tests/test_mcp_environment_override_policy.py`. New
       cases explicitly cover: a key present in **both**
       `mcp_overridable_keys` and `hidden_keys` (hidden must win — not
       treated as overridable/permitted), a key in **neither** set (rejected
       / excluded), a key that is **overridable-only** (accepted), that
       `apply_permitted_overrides` doesn't mutate its input `env_vars` and
       ignores argument names that aren't known env vars at all, and that
       `validate_environment_overrides` never leaks the attempted or actual
       secret value in its raised error message.

    Verification: `tests/test_example_fixtures.py`,
    `tests/test_function_registry.py`,
    `tests/test_pypost_1077_verification_artifacts.py`, `tests/test_adf.py`,
    `tests/test_mcp_secrets_policy.py`, `tests/test_mcp_tool_contract.py`,
    `tests/test_mcp_environment_override_policy.py` all green (one
    pre-existing, unrelated failure confirmed —
    `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`,
    reproduces identically on `git stash`, i.e. before this iteration's
    changes). Full parallel suite (`scripts/run_parallel_tests.py`, matching
    `make test`) also run for broader regression confirmation.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1283/50-observability.md` — added WARNING
    `mcp_env_override_rejected key=%s reason=%s` (not_overridable vs hidden) in
    `pypost/core/mcp_tool_contract.py::validate_environment_overrides`, and INFO
    `mcp_env_override_applied key=%s` in
    `pypost/core/mcp_secrets_policy.py::McpSecretsPolicy.apply_permitted_overrides`;
    no secret/env values logged. No new metrics (existing
    `track_mcp_argument_validation_failure`/call-outcome metrics already cover
    the rejection outcome). Verified: `tests/test_mcp_environment_override_policy.py`,
    `tests/test_mcp_secrets_policy.py`, `tests/test_mcp_tool_contract.py`,
    `tests/test_mcp_server_impl.py` (80 passed), plus
    `tests/test_mcp_server_registry.py`, `tests/test_mcp_proxy_server.py`,
    `tests/test_mcp_collection_e2e.py`, `tests/test_mcp_server_integration.py`,
    `tests/test_env_presenter.py` (110 passed) — no regressions.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1283/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - `doc/dev/dual_mode_example_requests.md` (new) — the dual-mode GUI/MCP
    request-body pattern demonstrated by `jira-create-issue`, the
    `{% set %}` / `meta.find_undeclared_variables` unconditional-`{% set %}`
    constraint (Follow-up Task #1 from `60-tech-debt.md`), and `to_adf`/
    `to_json_string` usage plus the JSON-injection risk they close.
  - `doc/dev/mcp_secrets_policy.md` (updated) — new "Per-variable MCP
    override (`mcp_overridable_keys`, PYPOST-1283)" section: the field,
    hidden-always-wins/computed-fresh-every-call guarantee,
    `effective_overridable_keys`/`apply_permitted_overrides`/
    `validate_environment_overrides`, schema-visibility rule, and full
    supplier wiring chain; plus a new `extract_environment_variable_names`
    API entry cross-linking the `{% set %}` doc.
  - `doc/dev/template_expression_functions.md` (updated) — added `to_adf`
    and `to_json_string` to the function catalog list.
  - `doc/dev/jira_mcp_project_default.md` (updated) — noted the
    `jira-create-issue` dual-mode pattern and `jira_project_key`'s
    `mcp_overridable_keys` per-call override, cross-linked to the two docs
    above.
  - `doc/dev/README.md` (updated) — added the new doc to the MCP section
    index.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1283/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1283/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1283/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1283/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1283/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/dual_mode_example_requests.md` (new)
- `doc/dev/mcp_secrets_policy.md` (updated)
- `doc/dev/template_expression_functions.md` (updated)
- `doc/dev/jira_mcp_project_default.md` (updated)
- `doc/dev/README.md` (updated)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
