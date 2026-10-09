# Roadmap: PYPOST-1334

## Task Metadata

- **Implementation language**: JSON/YAML examples (`examples/`) + Python tests (`tests/`,
  pytest run only via `make` targets)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Roadmap created; implementation language recorded
  - [x] References reviewed: `ai-tasks/PYPOST-1316/` (roadmap, requirements),
    `examples/collections/gitlab_mcp.json`, `examples/environments/gitlab.json`,
    `examples/pypost-library.yaml`, `doc/dev/gitlab_mcp_collection.md`, `Makefile`
    (`check-gitlab-mcp-path-freshness`), `tests/test_predefined_library_pypost_1281_repro.py`
  - [x] Requirements written: `ai-tasks/PYPOST-1334/10-requirements.md` (business goal, user
    stories, capability-level tool set for Actions / pull requests / issues, GitHub headers,
    github.com vs Enterprise Server base URL, encoding and secret rules incl. `ghp_` /
    `github_pat_` rejection, locked path catalog + make freshness target, docs, offline-only
    checks, scope boundaries; merge PR left to Step 2)
  - [x] `make verify-ai-tasks` — exit 0, "ai-tasks artifacts baseline OK (398 completed tasks; 2
    grandfathered legacy gaps)"
  - [x] Step 1 review and acceptance (gate owner) — independent review PASS
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research: GitHub REST docs (API versions incl. GHES 3.19/3.22, 2026-03-10 breaking
    changes, authentication header forms, workflow dispatch) and PyPost runtime facts
    (`to_json_string` stringifies, MCP `array`/`object`/`boolean` types, strict body render)
  - [x] Open questions resolved: merge PR excluded (documented gap); `Authorization: Bearer`;
    `X-GitHub-Api-Version: 2022-11-28`; two overridable vars `github_owner` + `github_repo`;
    30 tools (`github_` prefix); file names `github_mcp.json`, `github.json`,
    `github_mcp_rest_paths.json`, make target `check-github-mcp-path-freshness`;
    review create requires `event` (`APPROVE`/`REQUEST_CHANGES`/`COMMENT`), pending reviews a
    documented gap
  - [x] Step 3 failing-repro plan defined (`tests/test_github_mcp_collection.py` plus
    deliberate inventory updates in 3 existing test modules)
  - [x] Artifact: `ai-tasks/PYPOST-1334/20-architecture.md`
  - [x] Step 2 review and acceptance (gate owner) — review FAIL (review `event` optional) → fix → re-review PASS
- [x] **STEP 3: Failing Repro Test**
  - [x] Red tests written (test harness only; no `pypost/`, `examples/`, `Makefile`, docs change):
    - new `tests/test_github_mcp_collection.py` (`pytestmark` timeout 30 s; loopback e2e
      `@pytest.mark.timeout(60)` with `anyio.fail_after(10)` per MCP call). Locked 30-tool spec
      table (request id = kebab of tool name, catalog `capability` = design table column, typed
      args `boolean`/`array`/`object`/`integer_or_string`), guarded loaders (`Path.is_file()`
      assertions, never at import time)
    - new `tests/helpers/github_mcp_collection_http.py` (capture-everything loopback stub,
      `127.0.0.1:0`, bounded 2 s join; also captures `Accept`, `X-GitHub-Api-Version`,
      `Content-Type`)
    - updated inventory: `tests/test_examples_modernization.py` (manifest GitHub collection, 4
      variables, `github_token.secret`, `github_com` preset; GitHub collection load, name, 30
      requests), `tests/test_predefined_library_pypost_1281_repro.py` and
      `tests/test_gitlab_mcp_collection.py::test_gitlab_library_manifest_lists_collection_variables_and_preset`
      (exact list `[jira_mcp.json, gitlab_mcp.json, github_mcp.json, mcp.json]`)
  - [x] Command: `make test WORKERS=1 PYTEST_ARGS='tests/test_github_mcp_collection.py
    tests/test_examples_modernization.py tests/test_predefined_library_pypost_1281_repro.py
    tests/test_gitlab_mcp_collection.py -rfE -q'` — exit non-zero; 121 failed, 90 passed; no
    ImportError, collection error, xfail or skip; all 121 failures are `AssertionError` on
    missing GitHub artifacts (re-run after review fix: body-integer dual-layer assertions, E225
    at `method_drift = [...]`)
  - [x] Red, reason "examples/collections/github_mcp.json missing (PYPOST-1334)" (109 nodes in
    `test_github_mcp_collection.py`: format/load, schemas, review `event`, query params, bodies,
    value types, cancel/rerun bodies, params, env coverage, dict shadowing, full render,
    `test_github_template_encoding[*]` (16), `test_github_body_value_encoding[*]` (6),
    `test_github_numeric_path_ids_reject_non_decimal[*]` (63),
    `test_github_body_integers_reject_non_decimal[*]` (6: `line`/`start_line` x `7a`/`1.5`/empty;
    dual-layer contract — MCP boundary `_build_execution_variables` raises
    `McpArgumentValidationError(kind="invalid", expected_type="integer_or_string")`, and the body
    rendered with raw `{**OFFLINE_ENV, "mcp": {"request": args}}` raises `IntegerConversionError`
    from `to_int`), numeric descriptions,
    repository-scoped descriptions, wire query (3), loopback e2e) plus
    `test_examples_modernization.py::TestModernizedExamplesLibrary::test_examples_collections_load_as_collections`
  - [x] Red, other missing artifacts (one node each): environment ("examples/environments/github.json
    missing"); `test_github_mcp_http_contracts_match_locked_catalog` and
    `test_github_mcp_requests_send_github_headers` ("github_mcp_rest_paths.json missing");
    manifest ("pypost-library.yaml does not list collections/github_mcp.json", "missing variable
    github_owner"); README ("missing GitHub section '## Recommended import order (GitHub
    pair)'"); secret scan ("GitHub artifact(s) missing"); Makefile (".PHONY does not declare
    check-github-mcp-path-freshness"); `test_examples_manifest_discovery_and_structure`
    (`'collections/github_mcp.json' in manifest.collections`);
    `test_predefined_library_lists_valid_manifest_collections` and
    `test_gitlab_library_manifest_lists_collection_variables_and_preset` (list diff at index 2)
  - [x] Green by design (mutation twins on synthetic data): `..._catalog_check_rejects_path_drift`,
    `..._auth_convention_rejects_token_scheme_and_missing_version`,
    `..._params_checker_rejects_dangling_and_dead_arguments`,
    `..._query_wire_checker_rejects_prejoined_reserved_value`,
    `..._secret_scan_rejects_ghp_and_github_pat_values`
  - [x] Full `make test` — 381 files, 366 passed, 8 failed, 7 skipped. Intended red: 4 files above
    (124 nodes). Unrelated to this change (not fixed; `pypost/` untouched):
    `tests/test_collection_export_ui.py` (worker crash, exit -7 / SIGBUS),
    `tests/test_collection_import_profile.py::test_plan_collection_import_large_dataset_performance`,
    `tests/test_mypy_baseline_live.py::test_mypy_baseline_live_gate_passes` (181 resolved baseline
    errors in `pypost/`, env/toolchain drift),
    `tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing`
  - [x] `make lint` exit 0; `make verify-ai-tasks` exit 0
  - [x] Step 3 review and acceptance (gate owner) — review FAIL (integer test expected wrong exception; E225) → test-only fix → re-review PASS. Pre-existing/flaky suite failures filed: PYPOST-1337 (mypy gate), PYPOST-1338 (import perf flake); evidence added to PYPOST-1315 (export UI segfault), PYPOST-1299 (exit policy)
- [x] **STEP 4: Development**
  - [x] Iteration 1 — fixtures per design Q6/Q7: `examples/collections/github_mcp.json`
    (`github-mcp`, 30 requests, request id = kebab tool name, `Accept` +
    `X-GitHub-Api-Version: 2022-11-28` + `Authorization: Bearer {{ github_token }}`,
    `Content-Type` on POST/PATCH, `namespace(sep)` guarded JSON bodies with `to_int` integers,
    boolean `if`, array/object Jinja loops, static cancel `{}`, review body renders required
    `event` unconditionally), `examples/collections/github_mcp_rest_paths.json` (`api_version`,
    12 `doc_refs`, 30 tools), `examples/environments/github.json` (placeholders,
    `hidden_keys: [github_token]`, overridable `github_owner`/`github_repo`). Dispatch body emits
    `inputs` before `ref` (field order is irrelevant to GitHub) so the serialized nested object
    never ends in `}}`, which the no-template-marker test would otherwise flag
  - [x] Iteration 2 — `Makefile` `check-github-mcp-path-freshness` (`.PHONY`, `##` help, same
    recipe shape as GitLab); `examples/pypost-library.yaml` (collection between GitLab and
    `mcp.json`, 4 GitHub variables, `github_com` preset, description mentions GitHub)
  - [x] Iteration 3 — `examples/README.md`: library list/presets, Standalone Inventory (3
    entries, "(30 REST tools)"), sections "Recommended import order (GitHub pair)", "GitHub
    authentication" (fine-grained per-group permissions, classic `repo`, Bearer, pinned
    version), "GitHub.com vs GitHub Enterprise Server", "GitHub default repository and
    identifiers", "GitHub coverage vs gaps" (30 tools; gaps: merge, pending reviews,
    `return_run_details`, review by ID); secret-handling bullet and `mcp.json` role updated.
    `pypost/` and the reviewed tests unchanged
  - [x] Targeted run: `make test WORKERS=1 PYTEST_ARGS='tests/test_github_mcp_collection.py
    tests/test_examples_modernization.py tests/test_predefined_library_pypost_1281_repro.py
    tests/test_gitlab_mcp_collection.py -rfE -q'` — 4/4 files passed (all Step 3 red nodes
    green); `make check-github-mcp-path-freshness` and `make check-gitlab-mcp-path-freshness`
    — 2 passed each
  - [x] Full `make test` — 381 files: 371 passed, 3 failed, 7 skipped; all 3 are the known
    pre-existing failures (not caused by this change): `tests/test_collection_export_ui.py`
    (worker crash, exit -11, PYPOST-1315),
    `tests/test_mypy_baseline_live.py::test_mypy_baseline_live_gate_passes` (PYPOST-1337),
    `tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing`
    (PYPOST-1299). `make lint` exit 0; `make verify-ai-tasks` exit 0
  - [x] Review fix — `examples/README.md` "GitHub authentication": classic PAT note states
    dispatch, re-run and cancel workflow tools need `repo` even on public repositories
    (`public_repo` covers the other tools on public repositories only); Metadata read scoped
    to the repository lookup (`GET /user` needs no repository permission)
  - [x] Step 4 review and acceptance (gate owner) — review FAIL (README classic `repo` scope for Actions writes) → README fix → re-review PASS
- [x] **STEP 5: Code Cleanup**
  - [x] Manual flake8-rule review of `tests/test_github_mcp_collection.py` and
    `tests/helpers/github_mcp_collection_http.py` (not covered by `make lint`): fixed E203
    slice spacing; slice style unified; local `description` → `parameter` (held an
    `McpToolParam`); `ToolSpec` property docstrings; helper module docstring reflowed. No
    unused imports/locals, debug prints or lines > 100 chars. Behaviour-preserving
  - [x] JSON fixtures verified canonical (2-space indent, final newline); inventory test edits,
    `Makefile` target, manifest reviewed — no change needed
  - [x] Artifact: `ai-tasks/PYPOST-1334/40-code-cleanup.md`
  - [x] `make lint` exit 0; `make check-github-mcp-path-freshness` exit 0 (2 passed);
    targeted `make test WORKERS=1 PYTEST_ARGS='tests/test_github_mcp_collection.py
    tests/test_examples_modernization.py tests/test_predefined_library_pypost_1281_repro.py
    tests/test_gitlab_mcp_collection.py -q'` — 4/4 files passed; `make verify-ai-tasks` exit 0
  - [x] Step 5 review and acceptance (gate owner) — review PASS
- [x] **STEP 6: Observability**
  - [x] Decision: no production logging/metrics change (example content only; `git diff --
    pypost` empty), mirroring `ai-tasks/PYPOST-1316/50-observability.md`
  - [x] Existing coverage verified by code reading: MCP/HTTP log events and metrics apply to all
    30 `github_*` tools; GitHub token sent only as `Authorization: Bearer` and redacted
    (`_BEARER_TOKEN`, `sanitize_headers`, `hidden_keys` value redaction); no header logging
  - [x] Gaps recorded for Step 7: rendered-URL log sanitization (already PYPOST-1333), no
    per-tool metric label; no new offline test (precedent added none)
  - [x] Artifact: `ai-tasks/PYPOST-1334/50-observability.md`
  - [x] `make lint` exit 0; `make verify-ai-tasks` exit 0 (398 completed tasks; 2
    grandfathered legacy gaps); no tests touched in this step
  - [x] Step 6 review and acceptance (gate owner) — review PASS
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analysed fixtures, catalog, environment, manifest, README, Makefile target, new test
    module/helper and inventory edits against `10-requirements.md`, `20-architecture.md`,
    `40-code-cleanup.md`, `50-observability.md`; no BLOCKER (timeout markers present)
  - [x] Artifact: `ai-tasks/PYPOST-1334/60-tech-debt.md` — 16 items; new follow-ups (Jira
    pending): TD-1 marker test false positive (Medium), TD-2 shared MCP test helpers, TD-3/TD-4
    API version 2026-03-10 migration + dispatch run details, TD-5 `enum`/`items` in MCP
    schemas, TD-6 type-preserving JSON helper, TD-7 merge PR / pending-review story; linked
    existing PYPOST-1333 (+ alert `final_error_message` note), PYPOST-1122, PYPOST-1332,
    PYPOST-1303; pre-existing NON-BLOCKER failures PYPOST-1337, PYPOST-1338, PYPOST-1315,
    PYPOST-1299
  - [x] `make verify-ai-tasks` exit 0 (398 completed tasks; 2 grandfathered legacy gaps);
    `make lint` exit 0
  - [x] Review fix 1: replaced nonexistent `github_get_file_contents` with real list tools in
    `60-tech-debt.md` and `50-observability.md`; added TD-16 (Medium, new follow-up) — no
    test for empty-body `201`/`202`/`204` success (runtime already reports success per code
    reading); added PYPOST-1338 observed failure rate; `make verify-ai-tasks` and `make lint`
    exit 0
  - [x] Step 7 review and acceptance (gate owner) — review FAIL (wrong tool name; TD-16 missing) → doc fix → re-review PASS; citation nits fixed by orchestrator
- [x] **PHASE C/D: Blocker review + Jira follow-ups** — blocker review SAFE TO CLOSE; follow-ups created: PYPOST-1339 (TD-1), PYPOST-1340 (TD-2), PYPOST-1341 (TD-3+4), PYPOST-1342 (TD-5), PYPOST-1343 (TD-6), PYPOST-1344 (TD-7 story), PYPOST-1345 (TD-16), PYPOST-1346 (TD-17); links written to 60-tech-debt.md
- [x] **STEP 8: Dev Docs**
  - [x] New `doc/dev/github_mcp_collection.md` (mirrors `doc/dev/gitlab_mcp_collection.md`):
    overview, file map, request conventions, JSON body typing (string/integer/boolean/array/
    object), design decisions (Bearer auth, pinned `X-GitHub-Api-Version: 2022-11-28` via
    catalog `api_version`, `github_owner`/`github_repo` variables, required review `event`,
    no merge tool), encoding rules incl. `.`/`..` limitation, secrets, github.com vs GHES,
    catalog freshness + add/modify-tool checklist, test layout, observability, configuration,
    troubleshooting, known limitations (PYPOST-1339..1346, PYPOST-1332/1333/1122/1303).
    User setup linked to `examples/README.md`, not duplicated
  - [x] Indexes updated: `doc/dev/README.md` (MCP list, after GitLab entry);
    `doc/dev/examples_library_format.md` (directory tree, verification list, new section
    "GitHub MCP collection (PYPOST-1334)")
  - [x] Step 8 review and acceptance (gate owner) — review PASS; placeholder wording nit fixed by orchestrator
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1334/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1334/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1334/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1334/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1334/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
