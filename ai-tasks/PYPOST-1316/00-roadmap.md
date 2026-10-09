# Roadmap: PYPOST-1316

## Task Metadata

- **Implementation language**: JSON/YAML examples (`examples/`) + Python tests (`tests/`,
  pytest run only via `make` targets)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Independent requirements review passed; orchestrator accepted Step 1.
  - [x] Roadmap created; implementation language recorded
  - [x] References reviewed: `examples/collections/jira_mcp.json`,
    `examples/environments/jira_cloud.json`, `examples/pypost-library.yaml`,
    `examples/README.md`, `tests/test_example_fixtures.py`,
    `tests/test_examples_modernization.py`, `tests/test_mcp_collection_e2e.py`, `Makefile`
  - [x] Requirements written: `ai-tasks/PYPOST-1316/10-requirements.md` (business goal, user
    stories, capability-level tool set, encoding and secret rules, docs, offline-only checks,
    scope boundaries)
  - [x] `make verify-ai-tasks` — exit 0, "ai-tasks artifacts baseline OK (397 completed tasks; 2
    grandfathered legacy gaps)"
  - [x] Step 1 review and acceptance (gate owner)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Inputs reviewed: `10-requirements.md`, Jira pair fixtures, `jira_mcp_critical_rest_paths.json`,
    `pypost-library.yaml`, `examples/README.md`, `tests/test_example_fixtures.py`,
    `tests/test_examples_modernization.py`, `tests/test_predefined_library_pypost_1281_repro.py`,
    `tests/test_mcp_collection_e2e.py`, template/MCP core modules (`function_registry`,
    `function_expression_resolver`, `template_service`, `http_client`, `mcp_tool_contract`,
    `mcp_secrets_policy`, `mcp_server_impl`, `sensitive_text_sanitizer`), `Makefile`, doc scripts
  - [x] Architecture written: `ai-tasks/PYPOST-1316/20-architecture.md` — 25 `gitlab_*` tools,
    `Authorization: Bearer {{ gitlab_token }}`, `examples/environments/gitlab.json`, MCP-overridable
    `gitlab_project`, full locked path catalog `examples/collections/gitlab_mcp_rest_paths.json` +
    `make check-gitlab-mcp-path-freshness`, offline test plan, Step 3 red design, risks
  - [x] `make verify-ai-tasks` — exit 0, "ai-tasks artifacts baseline OK (397 completed tasks; 2
    grandfathered legacy gaps)"
  - [x] Review fix: manifest `gitlab_project` default changed from `""` to the placeholder
    `your-group/your-project` (Jira manifest uses `"PROJ"`, not `""`) plus test
    `test_gitlab_library_manifest_project_default_matches_environment_placeholder`; AC3.3 now
    proven at the wire layer (loopback 7a with `ref="feature/x&y=1#z"`, `search="a b&c"`, and
    prepared-request test 7b `test_gitlab_query_reserved_characters_stay_single_key_on_wire`);
    dot-segment (`.`/`..`) limitation documented; encoding table shows a string-only project ID
  - [x] `make verify-ai-tasks` after review fix — exit 0, "ai-tasks artifacts baseline OK (397
    completed tasks; 2 grandfathered legacy gaps)"
  - [x] Step 2 review and acceptance (gate owner): independent re-review passed after one fix
    round; orchestrator accepted Step 2.
- [x] **STEP 3: Failing Repro Test**
  - [x] Red tests written (test harness only; no `pypost/`, `examples/`, `Makefile` change):
    - new `tests/test_gitlab_mcp_collection.py` (`pytestmark` timeout 30 s; loopback e2e
      `@pytest.mark.timeout(60)` with `anyio.fail_after(10)` per MCP call). Locked 25-tool spec
      table (request id = kebab of tool name, catalog `capability` = design table column),
      guarded loaders (`Path.is_file()` assertions, never at import time)
    - new `tests/helpers/gitlab_mcp_collection_http.py` (capture-everything loopback stub,
      `127.0.0.1:0`, bounded 2 s join)
    - updated inventory: `tests/test_examples_modernization.py` (manifest GitLab collection,
      variables, token `secret`, `gitlab_com` preset; GitLab collection load, name, 25 requests),
      `tests/test_predefined_library_pypost_1281_repro.py` (exact list
      `[jira_mcp.json, gitlab_mcp.json, mcp.json]`)
  - [x] Command: `make test WORKERS=1 PYTEST_ARGS='tests/test_gitlab_mcp_collection.py
    tests/test_examples_modernization.py tests/test_predefined_library_pypost_1281_repro.py -rfE
    -q'` — exit 2; 71 failed, 17 passed; no ImportError, collection error, xfail or skip
  - [x] Red, reason "examples/collections/gitlab_mcp.json missing (PYPOST-1316)" (63 nodes):
    `test_gitlab_mcp_collection_imports_via_native_loader`,
    `test_gitlab_mcp_published_tools_match_documented_set`,
    `test_gitlab_mcp_query_params_match_documented_set`,
    `test_gitlab_mcp_headers_and_read_bodies_follow_conventions`,
    `test_gitlab_mcp_bodies_render_documented_json_fields`,
    `test_gitlab_mcp_requests_use_bearer_auth_convention`, `test_gitlab_mcp_params_declared_and_used`,
    `test_gitlab_mcp_companion_env_covers_referenced_names`,
    `test_gitlab_mcp_argument_names_do_not_shadow_dict_attributes`,
    `test_gitlab_mcp_full_render_leaves_no_template_markers`, `test_gitlab_template_encoding[*]`
    (13), `test_gitlab_numeric_path_ids_reject_non_decimal[*]` (33),
    `test_gitlab_numeric_identifier_paths_accept_decimal_strings_and_integers`,
    `test_gitlab_project_scoped_descriptions_explain_override`,
    `test_gitlab_query_reserved_characters_stay_single_key_on_wire[get-file-ref|list-projects-search|list-branches-search]`,
    `test_gitlab_mcp_loopback_e2e_wire_contract`, and
    `test_examples_modernization.py::TestModernizedExamplesLibrary::test_examples_collections_load_as_collections`
  - [x] Red, other missing artifacts (one node each):
    `test_gitlab_environment_imports_with_placeholders` — "examples/environments/gitlab.json
    missing"; `test_gitlab_mcp_http_contracts_match_locked_catalog` —
    "examples/collections/gitlab_mcp_rest_paths.json missing";
    `test_gitlab_library_manifest_lists_collection_variables_and_preset` — "pypost-library.yaml
    does not list collections/gitlab_mcp.json";
    `test_gitlab_library_manifest_project_default_matches_environment_placeholder` —
    "pypost-library.yaml missing variable gitlab_project";
    `test_gitlab_readme_documents_inventory_and_tool_parity` — "examples/README.md missing GitLab
    section '## Recommended import order (GitLab pair)'"; `test_gitlab_fixtures_contain_no_real_tokens`
    — "GitLab artifact(s) missing: [gitlab_mcp.json, gitlab.json, gitlab_mcp_rest_paths.json]";
    `test_examples_manifest_discovery_and_structure` — `'collections/gitlab_mcp.json' in
    manifest.collections` is False; `test_predefined_library_lists_valid_manifest_collections` —
    list diff at index 1 (`collections/gitlab_mcp.json` missing)
  - [x] Green by design (mutation twins on synthetic data, prove checkers can fail):
    `test_gitlab_mcp_catalog_check_rejects_path_drift`,
    `test_gitlab_mcp_auth_convention_rejects_private_token_header`,
    `test_gitlab_mcp_params_checker_rejects_dangling_and_dead_arguments`,
    `test_gitlab_query_wire_checker_rejects_prejoined_reserved_value`,
    `test_gitlab_fixtures_secret_scan_rejects_glpat_like_value`
  - [x] Unchanged tests in the touched modules still pass (3 legacy-fixture tests in
    `test_examples_modernization.py`, 9 in `test_predefined_library_pypost_1281_repro.py`)
  - [x] `make verify-ai-tasks` — exit 0, "ai-tasks artifacts baseline OK (397 completed tasks; 2
    grandfathered legacy gaps)"
  - [x] Review fix (test harness only): added
    `tests/test_gitlab_mcp_collection.py::test_gitlab_makefile_path_freshness_target_declared`
    (design Q5 / Implementation Plan step 2) — asserts `check-gitlab-mcp-path-freshness` is in
    `.PHONY`, its rule depends on `$(VENV_MARKER)` with a `## <help>` comment, and its recipe is
    exactly `QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest` +
    `::test_gitlab_mcp_http_contracts_match_locked_catalog` +
    `::test_gitlab_mcp_catalog_check_rejects_path_drift` + `-q` (mirrors
    `check-jira-mcp-path-freshness`). Red: "Makefile .PHONY does not declare
    check-gitlab-mcp-path-freshness (PYPOST-1316)"
  - [x] Review fix (advisory): README parity regex narrowed from `\bgitlab_[a-z_]+` to
    `\bgitlab_(?:get|list|create|update)_[a-z_]+` (covers all 25 locked tools: 9 get, 10 list,
    4 create, 2 update), so `gitlab_mcp` / `gitlab_project` / `gitlab_token` prose does not break
    parity
  - [x] Re-run after review fix: same `make test WORKERS=1 PYTEST_ARGS='...'` command — exit 2;
    72 failed, 17 passed (one new red node); no ImportError, collection error, xfail or skip
  - [x] Step 3 independent review and acceptance (gate owner): re-review passed after one
    test-harness fix; orchestrator accepted Step 3.
- [x] **STEP 4: Development**
  - Independent implementation review passed (all 25 tools checked against GitLab REST v4);
    orchestrator accepted Step 4.
  - [x] Iteration 1 — fixtures: new `examples/collections/gitlab_mcp.json` (id `gitlab-mcp`,
    25 `gitlab_*` requests per the design Q4 table: `/api/v4` paths with `urlencode` path
    segments and `to_int` IDs, raw query params, `page`/`per_page` defaults 1/20, guarded
    `namespace` + `to_json_string` bodies, `Accept` + `Authorization: Bearer {{ gitlab_token }}`
    headers plus `Content-Type` on POST/PUT, project-scoped descriptions explaining the
    `gitlab_project` override), `examples/environments/gitlab.json` (placeholders, hidden
    `gitlab_token`, overridable `gitlab_project`) and `examples/collections/gitlab_mcp_rest_paths.json`
    (locked catalog, all 25 tools, `reviewed_on` 2026-10-09, GitLab `doc_refs`)
  - [x] Iteration 2 — integration: `examples/pypost-library.yaml` (collection after
    `jira_mcp.json`, 3 GitLab variables with `gitlab_project` default `your-group/your-project`
    and secret `gitlab_token`, `gitlab_com` preset, description mentions GitLab);
    `examples/README.md` (library list/presets, inventory entries, GitLab import order,
    authentication, GitLab.com vs self-managed, default project and identifiers incl. the
    `.`/`..` limitation, coverage vs gaps, secret placeholder); `Makefile`
    `check-gitlab-mcp-path-freshness` (in `.PHONY`, `$(VENV_MARKER) venv-test venv-otel`
    prerequisites like the Jira target, `##` help, two catalog nodes with `-q`). No `pypost/`
    change. Reviewed tests unchanged.
  - [x] Validation: `make test WORKERS=1 PYTEST_ARGS='tests/test_gitlab_mcp_collection.py
    tests/test_examples_modernization.py tests/test_predefined_library_pypost_1281_repro.py'` —
    exit 0; 89 passed (74 + 5 + 10), 0 failed; the 72 red nodes are green
  - [x] `make check-gitlab-mcp-path-freshness` — 2 passed; `make check-jira-mcp-path-freshness`
    — 2 passed
  - [x] Related suites (`test_example_fixtures`, `test_mcp_collection_e2e`, `test_makefile_recipes`,
    `test_mcp_server_integration` and all 8 other tests referencing `examples/`) — 12 files, 208
    passed, 0 failed
  - [x] Full `make test` — 380 files: 371 passed, 7 skipped (deselected slow), 2 failed, both
    pre-existing: `tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing`
    (PYPOST-1299, known); `tests/test_collection_import_teardown_repro.py::test_unexpected_reader_exception_requires_teardown_and_reaps_worker`
    (worker timeout 120 s inside `process_until`; flaky 2/3 alone on this tree and reproduced
    1/3 at base 811fde38 in a scratch worktree, which was then removed; matches PYPOST-1320)
  - [x] `make lint` exit 0; `make typecheck` exit 0 (mypy baseline OK, 181 known errors);
    `make check-docs-links` exit 0 (18 files); `make verify-ai-tasks` exit 0 (397 completed
    tasks; 2 grandfathered legacy gaps)
  - [x] Secret hygiene: no GitLab token-like value (`gl(pat|oas|dt|...)-…`) in `examples/`,
    `Makefile` or this task folder; `test_gitlab_fixtures_contain_no_real_tokens` passes
- [x] **STEP 5: Code Cleanup**
  - Independent cleanup review passed; orchestrator accepted Step 5.
  - [x] Cleanup report: `ai-tasks/PYPOST-1316/40-code-cleanup.md`
  - [x] Formatting only, no behaviour change: `tests/test_gitlab_mcp_collection.py` (one
    `sorted(...)` call collapsed to one line; local `params` annotated `dict[str, str]`).
    No changes needed in the GitLab JSON files (canonical `indent=2`, key order matches the
    Jira fixtures, newline at EOF), README, Makefile or manifest.
  - [x] Direct inspection of the changed test files (`make lint` flake8 covers `pypost/` only,
    PYPOST-1303): no line over 100, no unused import or helper, no debug code, timeouts present
  - [x] `make lint` exit 0; `make typecheck` exit 0 (mypy baseline OK, 181 known errors);
    `make check-docs-links` exit 0 (18 files)
  - [x] `make test WORKERS=1 PYTEST_ARGS='tests/test_gitlab_mcp_collection.py
    tests/test_examples_modernization.py tests/test_predefined_library_pypost_1281_repro.py'` —
    exit 0, 3/3 files passed; `make check-gitlab-mcp-path-freshness` — 2 passed
  - [x] `make verify-ai-tasks` — exit 0 (397 completed tasks; 2 grandfathered legacy gaps)
- [x] **STEP 6: Observability**
  - Independent observability re-review passed after two fix rounds; orchestrator accepted Step 6.
  - [x] Observability report: `ai-tasks/PYPOST-1316/50-observability.md`
  - [x] Decision: no production logging/metrics change (example-only change; `git diff --
    pypost` empty). GitLab tools reuse the generic MCP/HTTP pipeline: `mcp_server_impl`
    (`mcp_param_default_applied`, validation warnings, `record_mcp_call_outcome` metrics +
    activity log with tool name), `request_service` retry logs (template URL in `url=%r`; rendered URL can appear via
    `exc.message`),
    `http_client` ERR/WARNING/DEBUG events and request/response metrics
  - [x] Token redaction confirmed: Bearer-only auth (test-enforced); `sensitive_text_sanitizer`
    `_BEARER_TOKEN`, `authorization` header mask, JSON `token` keys; `gitlab_token` hidden →
    value redacted in MCP output; no header logging. Rendered URLs carry project/file paths and
    search terms only (no secrets by design) — acceptable
  - [x] Step 7 follow-up candidates (not implemented): (1) `http_client`
    `response_body_truncated`/`sse_stream_detected` and `request_service`
    `retryable_error`/`retry_exhausted` (`exc.message`) log the rendered URL unsanitized
    (generic, pre-existing); (2) MCP metrics
    have no per-tool label (method-only)
  - [x] No `pypost/`, `tests/`, `examples/`, `Makefile` change
  - [x] `make verify-ai-tasks` — exit 0, "ai-tasks artifacts baseline OK (397 completed tasks; 2
    grandfathered legacy gaps)"
  - [x] Review fix: corrected the "retry logs print the template URL only" claim. `url=%r` is the
    template, but `retryable_error` (`request_service.py:160-169`) and `retry_exhausted`
    (`request_service.py:332-342`) log `exc.message` (`Request to {url} timed out.` /
    `Could not connect to {url}.`, `http_client.py:302`/`313`), so the rendered,
    unsanitized URL can appear. Still acceptable for GitLab (token only in `Authorization`; no
    secrets in URLs). Follow-up candidate 1 extended to this path
  - [x] `make verify-ai-tasks` (after review fix) — exit 0, "ai-tasks artifacts baseline OK (397
    completed tasks; 2 grandfathered legacy gaps)"
  - [x] Review fix #2: removed `request_execution_failed` / `exc.detail` as a URL-leak path
    (Logs list, Request URLs, follow-up candidate 1, Step 6 bullets). Transport errors exit the
    retry loop only at `attempt == max_retries`, which sets `detail` to `retries_attempted: N`
    (`request_service.py:157`, also for `max_retries=0`); BODY/YAML parse/CANCELLED carry no URL.
    Leak paths kept: `retryable_error`, `retry_exhausted` (`exc.message`), `sse_stream_detected`,
    `response_body_truncated`. Still acceptable for GitLab
  - [x] `make verify-ai-tasks` (after review fix #2) — exit 0, "ai-tasks artifacts baseline OK
    (397 completed tasks; 2 grandfathered legacy gaps)"
- [x] **STEP 7: Technical Debt Analysis**
  - Independent tech-debt review passed and blocker review returned SAFE TO CLOSE;
    follow-ups filed as PYPOST-1332 (TD-2) and PYPOST-1333 (TD-1); orchestrator accepted Step 7.
  - [x] Inputs reviewed: `00-roadmap.md`, `10-requirements.md`, `20-architecture.md` (R1–R8,
    dot-segment limitation), `40-code-cleanup.md`, `50-observability.md` (follow-up candidates),
    the full change set (3 new GitLab fixtures, manifest, README, Makefile, 2 new and 2 edited
    test modules); no `pypost/` change
  - [x] Timeout rule (do-testing): all 4 touched test modules declare `pytestmark =
    pytest.mark.timeout(30)`; loopback e2e `@pytest.mark.timeout(60)`; helper join bounded 2 s —
    no BLOCKER
  - [x] Tech-debt report: `ai-tasks/PYPOST-1316/60-tech-debt.md` — TD-1..TD-16, no BLOCKER;
    2 new follow-ups (TD-1 Low: rendered URL in `sse_stream_detected` / `retryable_error` /
    `retry_exhausted`; TD-2 Low: fail-closed blank path variable), existing references
    PYPOST-1122, PYPOST-1303, PYPOST-753; pre-existing NON-BLOCKER PYPOST-1299, PYPOST-1320
  - [x] Dedupe: `ai-tasks/**/60-tech-debt.md` and `00-tech-debt-consolidated.md` searched for
    each candidate before proposing; no Jira issue created
  - [x] `make verify-ai-tasks` — see the Validation section of `60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] New dev doc `doc/dev/gitlab_mcp_collection.md`: overview, files and request
    conventions, encoding rules (`urlencode` path segments, raw query values,
    `integer_or_string` + `to_int`, `.`/`..` limitation), Bearer vs `PRIVATE-TOKEN` and secret
    handling, default project behaviour (R2, PYPOST-1332), locked catalog +
    `make check-gitlab-mcp-path-freshness` maintainer checklist (collection + catalog +
    `GITLAB_TOOL_SPECS`), test layout (offline contracts, loopback e2e, wire-level reserved
    characters, mutation twins, Makefile contract), observability (PYPOST-1122, PYPOST-1333),
    troubleshooting, follow-ups
  - [x] Registered in `doc/dev/README.md` (MCP section, after the Jira MCP e2e entry)
  - [x] Shared doc `doc/dev/examples_library_format.md`: directory layout lists the GitLab files;
    GitLab test module and manifest entries added, links to the new doc
  - [x] Step 7 doc note (TD-10): `examples/README.md` "GitLab coverage vs gaps" now says
    `gitlab_get_file` returns decoded text, so binary or very large files are not suitable
    (subject to the `max_response_bytes` cap)
  - [x] `make test WORKERS=1 PYTEST_ARGS='tests/test_gitlab_mcp_collection.py
    tests/test_examples_modernization.py'` — exit 0, 2/2 files passed
  - [x] `make lint` exit 0 (flake8 `pypost/`; Markdown lint 16 files; link check 18 files);
    `make check-docs-links` exit 0 (18 files). Neither covers `doc/dev/` (lint: `doc/user/*.md`
    + `doc/README.md`; links: those + root `README.md` + `examples/README.md`), so the relative
    links in the new and edited `doc/dev/` files were checked by hand — all resolve
  - [x] `make verify-ai-tasks` — exit 0, "ai-tasks artifacts baseline OK (397 completed tasks; 2
    grandfathered legacy gaps)"
  - [x] Step 8 review and acceptance (gate owner): independent dev-docs review passed;
    orchestrator accepted Step 8.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1316/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1316/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1316/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1316/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1316/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
