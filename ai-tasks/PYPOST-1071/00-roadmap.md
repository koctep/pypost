# Roadmap: PYPOST-1071

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `fix/PYPOST-1071-restore-green-baselines` — reference only; the work was
  committed directly on `dev`, no branch was created or switched.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1071/00-roadmap.md` — task progress journal and implementation language.
  - `ai-tasks/PYPOST-1071/10-requirements.md` — requirements for resolving the five remaining
    baseline failures while preserving the four contracts restored by PYPOST-1077.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1071/20-architecture.md` — evidence-backed mixed disposition: extract
    misplaced MCP responsibilities, explicitly refresh cohesive HTTP/collection caps, and align
    the artifact verifier with the current Step 8 `doc/dev/` contract.
  - Current evidence: four SOLID tests report five metric violations; the artifact scan's 30
    apparent additions all disappear when the obsolete `70-dev-docs.md` requirement is removed.
  - Step 3 design: add an offline red artifact-contract test and retain the existing four red
    SOLID tests as the structural repro; no source, caps, or baselines change before review.
- [x] **STEP 3: Failing Repro Test**
  - [/] `tests/test_verify_ai_task_artifacts.py` — new offline `TestCurrentStep8Contract` class
    asserting the required-file contract for the current Step 8 `doc/dev/` output. Red against
    today's 7-file `STANDARD_FILES` / 8-file `AUDIT_FILES` verifier. New red node ids:
    - `tests/test_verify_ai_task_artifacts.py::TestCurrentStep8Contract::test_standard_task_requires_six_current_artifacts`
    - `tests/test_verify_ai_task_artifacts.py::TestCurrentStep8Contract::test_audit_task_requires_seven_current_artifacts`
    - `tests/test_verify_ai_task_artifacts.py::TestCurrentStep8Contract::test_no_task_kind_requires_obsolete_dev_docs_summary`
    - `tests/test_verify_ai_task_artifacts.py::TestCurrentStep8Contract::test_completed_current_format_task_is_compliant_without_dev_docs_summary`
  - [/] Retained (unmodified) structural repro — the four already-red SOLID baseline tests in
    `tests/test_solid_audit_baseline.py`:
    - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_audit_module_inventory_within_caps`
    - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_main_window_class_loc_within_cap`
    - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_main_window_file_loc_within_cap`
    - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
  - [/] Repro command:
    `make test PYTEST_ARGS='tests/test_verify_ai_task_artifacts.py tests/test_solid_audit_baseline.py -p no:randomly -q'`
  - [/] Confirmed red state: 9 failed, 14 passed — the 4 new contract tests, the 4 SOLID tests, and
    the pre-existing `TestCommittedBaseline::test_baseline_matches_current_scan` (289 current vs 259
    baseline, every delta missing only `70-dev-docs.md`).
  - [/] No production code, cap value, baseline JSON, or snapshot changed in this step.
- [x] **STEP 4: Development**
  - [x] Iteration 1 — aligned the artifact verifier with the current Step 8 `doc/dev/` contract.
    Removed `70-dev-docs.md` from `STANDARD_FILES` and `AUDIT_FILES` in
    `scripts/verify_ai_task_artifacts.py` (6 and 7 required files); renamed
    `test_standard_task_requires_seven_files` → `..._six_files` and
    `test_code_audit_task_requires_eight_files` → `..._seven_files` and asserted the counts;
    repointed `test_missing_required_files_reports_sorted_gaps` at files the helper still
    creates; refreshed `doc/dev/setup.md`; regenerated `ai-tasks-artifacts-baseline.json`
    through `--update-baseline`: 259 → **227**, 0 additions, every delta only the removal of
    `70-dev-docs.md`. All 4 Step 3 repro tests and `test_baseline_matches_current_scan` green
    (19 passed); `scripts/verify_ai_task_artifacts.py` (no flag) exits 0.
  - [x] Iteration 2 — extracted MCP persistence/lifecycle from the composition root into
    `pypost/ui/mcp_server_controller.py` (`McpServerSettingsController`, plus a `for_window`
    factory). It owns registry construction, the legacy manager, persisted-row mutation,
    transactional reconfiguration completion, start/stop/remove, startup loading and
    `stop_all()`; `MainWindow` keeps composition and the two-source readiness gate.
    `main_window.py` 565 → **433** (cap 435), `MainWindow` class 520 → **387** (cap 390).
    Updated the two relocated `tests/test_main_window.py` cases and 10 `MCPServerManager`
    patch targets. 722 MCP/window/env/settings tests pass.
  - [x] Iteration 3 — extracted MCP status controls, dialogs and scoped refresh routing from
    `EnvPresenter` into `pypost/ui/presenters/mcp_controls_presenter.py`
    (`McpControlsPresenter`, and the `McpServerController` protocol). `EnvPresenter` keeps
    `refresh_mcp_tools()`, `mcp_status_text()`, `mcp_tools_button_text()` and
    `mcp_activity_button_text()` as delegating shims for `main_window_signals.py:18,21,31`
    and `tests/test_env_presenter.py`. `env_presenter.py` 599 → **392** (cap 470).
    967 MCP/window/env/settings/collection tests pass.
  - [x] Iteration 4 — recalibrated caps only after the extractions fit their existing caps,
    at about 10% headroom over the post-extraction measurements: `main_window.py` 435 → 477,
    `MainWindow` class 390 → 426, `env_presenter.py` 470 → 432. Applied the architecture's
    accepted-growth caps verbatim with adjacent rationale comments: `http_client.py`
    340 → 418, `collections_presenter.py` 330 → 403. Regenerated
    `ai-tasks/PYPOST-376/baseline-metrics.md` through `--markdown` only and updated
    `doc/dev/solid_audit.md` from that output. `--check` exits 0; the 4 SOLID tests, the
    artifact-verifier module and the PYPOST-1077 verification suite are green (27 passed).
  - [x] Iteration 5 — closed the two fixable gaps from the Step 4 review. (1) Type regression:
    `McpServerSettingsController._collection_by_id` returned the `Any` result of a `getattr`
    lookup from a `-> Collection | None` signature; the value now lands in an annotated
    `found: Collection | None` local before it is returned, with no `type: ignore` and no
    weakening of the declared return type. `make typecheck` off-baseline errors 9 → **8**,
    back to the HEAD baseline (the remaining 8 are pre-existing Qt signal/worker errors).
    (2) Doc drift: `doc/dev/setup.md:361` still read "predates the 8-file Code Audit pattern"
    under the new "Code Audit 7-file standard" heading — now "7-file"; the rest of the section
    was re-checked and carries no other stale 8-file or `70-dev-docs.md` wording. `make lint`
    clean; `tests/test_main_window.py`, `tests/test_env_presenter.py`,
    `tests/test_verify_ai_task_artifacts.py`, `tests/test_solid_audit_baseline.py`: 79 passed.
- [x] **STEP 5: Code Cleanup**
  - [/] `ai-tasks/PYPOST-1071/40-code-cleanup.md` — cleanup report for this task's diff only.
  - [/] Static analysis: `make analyze` has no rule; the gate is `make lint` (flake8,
    `max-line-length = 100`, `extend-select = T201`, `pypost/` only) plus `make typecheck`.
    `make lint` clean. flake8 also run explicitly over the in-scope `scripts/` and `tests/`
    files, and every in-scope file was linted at `HEAD` and in the working tree with the
    per-file violation-code counts diffed to separate this task's findings from pre-existing
    noise. Exactly one delta: `tests/test_main_window.py` E402 6 → 7, the added
    `McpServerSettingsController` import — kept, because `pytestmark` sits above the imports so
    every import in that module is E402 and the new line follows the existing pattern.
  - [/] Cleanup edits (3, all behaviour-neutral):
    - `pypost/ui/mcp_server_controller.py` — removed the redundant `else` after the early
      `return` in `upsert_mcp_server`, dead branch structure carried over verbatim from
      `MainWindow` during the Step 4 extraction.
    - `tests/test_verify_ai_task_artifacts.py` — rewrote two Step 3-era comments (the module
      comment above `OBSOLETE_DEV_DOCS_FILE` and the `TestCurrentStep8Contract` docstring) that
      still claimed in the present tense that the verifier demands `70-dev-docs.md` and that
      the checks are red. No assertion, node id or test name changed.
    - `doc/dev/solid_audit.md:118` — shortened the one new over-length line (105 > 100) by
      trimming the link text to `mcp_controls_presenter.py`; target unchanged.
      `scripts/check-line-length.sh`: 8 → 7 long lines, the remaining 7 pre-existing.
  - [/] No unused imports, variables, commented-out code, debug prints or `TODO/FIXME` found.
    `main_window.py` still uses `MCPServerManager`/`MCPServerRegistry` as parameter
    annotations; `EnvPresenter._metrics` is still live for variable-validation metrics.
  - [/] Validation: targeted affected modules **113 passed**; full fast suite re-run after the
    edits **2215 passed, 22 deselected** — unchanged. `--check` exits 0; `make verify-ai-tasks`
    exits 0. Every changed test module carries a module-level `pytestmark` timeout.
  - [/] `make typecheck` off-baseline errors remain **8**, all pre-existing Qt signal/worker
    errors at HEAD (`qt/worker.py` 2, `main_window_signals.py` 4,
    `collection_import_actions.py` 1, `tabs_presenter.py` 1); zero hits in this task's two new
    modules. Not fixed and the mypy baseline was not regenerated — out of this task's scope.
  - [/] Nothing regenerated: no `--update-baseline`, no `--markdown`, no cap, baseline or
    snapshot change in this step. `Makefile` and `tests/test_example_fixtures.py` (unrelated
    uncommitted PYPOST-1056/PYPOST-1048 work) deliberately untouched.
- [x] **STEP 6: Observability**
  - [/] `ai-tasks/PYPOST-1071/50-observability.md` — observability report for this task's
    diff only, including the deliberately-not-added sites and their reasons.
  - [/] Assessment first: Step 4 was a behaviour-preserving extraction, so every existing
    log moved verbatim. Downstream collaborators were inventoried before adding anything —
    `mcp_server_registry.py` already logs `mcp_registry_start_requested` (:90),
    `mcp_registry_stop_requested` (:117), `mcp_registry_reconfigure_rolled_back` (:428) and
    `mcp_registry_status` (:519) and publishes `set_mcp_server_instance_counts`, so the
    endpoint **runtime lifecycle** was already covered. The uncovered half was the
    **persistence** side the new controller now owns.
  - [/] Added 5 statements (4 INFO, 1 DEBUG; no new WARNING/ERROR):
    - `mcp_server_controller.py:264` `mcp_servers_persist_requested reason=%s count=%d` —
      one choke point covering all five settings-mutation paths; logged before the write so
      it pairs with `ConfigManager`'s `config_save_failed` ERROR.
    - `mcp_server_controller.py:236` `mcp_persisted_servers_loaded count=%d
      enabled_count=%d` — the only startup evidence that persisted rows were restored;
      separates "no endpoints configured" from "the readiness gate never fired".
    - `mcp_server_controller.py:211` `mcp_server_reconfigure_finished instance_id=%s
      committed=%s` — the `committed=False` branch previously returned silently.
    - `mcp_controls_presenter.py:292` `mcp_servers_dialog_opened server_count=%d` —
      mirrors its two already-logged sibling dialogs and anchors the mutation events.
    - `mcp_server_controller.py:133` (DEBUG) `mcp_server_activity_unavailable
      instance_id=%s` — the swallowed `KeyError` otherwise looks like "no activity yet".
  - [/] Counts and one opaque `instance_id` only; no host, port, collection/environment id
    set, tool name or `AppSettings`/`McpServerConfiguration` structure is formatted into a
    message. Asserted negatively by the new startup test.
  - [/] No metrics added, with evidence: the registry still publishes
    `set_mcp_server_instance_counts` on every upsert and status change through the same
    injected tracker, and `track_mcp_active_env_changed` moved intact to
    `mcp_controls_presenter.py:161`. `MetricsTrackerProtocol` is closed and out of scope.
  - [/] Contract fix found by this step: the extraction changed the logger name of **eight**
    moved events (a ninth DEBUG event in the controller, `mcp_registry_source`, is new code
    written with the extraction, not a move — `HEAD` built the registry unlogged). The only
    ERROR among the moved eight, `mcp_server_start_failed_ui`, now satisfies `do-testing`
    **C1** (an `assertLogs` block on the new logger in
    `tests/test_env_presenter.py::test_mcp_start_failed_shows_warning`). A **C2** rule was
    also added (`tests/expected_log_allowlist.yaml:45-51`) but is dead configuration today —
    `assertLogs` sets `logger.propagate = False`, so the ERROR never reaches `--log-file`.
    Kept deliberately, correct for when the event is logged outside an `assertLogs` block.
    `baseline_error_count` unchanged at 72 — no ERROR was added, an existing one was
    registered under its new name.
  - [/] Tests added (3 new in `tests/test_main_window.py`, 1 extended in
    `tests/test_env_presenter.py`); both modules already carry a `pytestmark` timeout.
  - [/] Validation: `make lint` clean; affected modules **117 passed**; full fast suite
    **2218 passed, 22 deselected** (2215 + 3 new); `--check` exits 0; `make verify-ai-tasks`
    exits 0. `scripts/verify_test_log_guardrails.py` on a captured MCP/UI slice: **exit 0
    both with and without the new allowlist rule** — `mcp_server_start_failed_ui` is
    captured zero times, so the rule is not exercised by the current suite.
  - [/] Nothing regenerated: no `--update-baseline`, no `--markdown`, no cap, baseline,
    snapshot or mypy-baseline change. `Makefile` and `tests/test_example_fixtures.py`
    untouched.
  - [/] Finding recorded for STEP 7 (pre-existing, unrelated to this diff): the CI step at
    `.github/workflows/test.yml:147` inspects an **empty** `pytest.log` on a full-suite run
    and reports `ERROR count: 0`, so the ERROR guardrail is vacuous. Collecting
    `tests/test_agent_lifecycle_smoke.py` first silences `--log-file` capture for the rest
    of the session; reproduction and ruled-out causes are in `50-observability.md`.
  - [/] Step 6 review fix round 1 — two factual inaccuracies corrected in
    `50-observability.md`, no production code, test, allowlist, cap, baseline or snapshot
    touched. (1) The moved/new split: `mcp_manager_source` moved from `main_window.py`
    (`HEAD`:92,95) but `mcp_registry_source` is new (`HEAD`:114 built the registry with no
    logging), so the module table now reads 2 moved DEBUG + 2 new DEBUG + 4 added by this
    step = 8, and the `modified` rows carry real counts (`main_window.py` 19 → 17,
    `env_presenter.py` 20 → 13) instead of "unchanged". (2) The guardrail claim: the
    verifier exits **0** on the captured MCP/UI slice with and without the rule, because the
    C1 `assertLogs` block at `tests/test_env_presenter.py:453` suppresses propagation
    (`unittest/_log.py` sets `logger.propagate = False`); the allowlist rule is recorded as
    dead configuration and kept. A probe emitting the event without an `assertLogs` wrapper
    confirms the rule works when the ERROR is captured (exit 1 without it, 0 with it).
  - [/] Follow-up recorded for STEP 8: `doc/dev/logging.md:266,274` still attributes
    `mcp_activity_dialog_opened` / `mcp_tools_overview_opened` to the env presenter and has
    no rows for the controller's persistence events. `doc/dev/` is Step 8's artifact, so
    the exact rows to add are tabulated in `50-observability.md` rather than edited here.
- [x] **STEP 7: Technical Debt Analysis**
  - [/] `ai-tasks/PYPOST-1071/60-tech-debt.md` — debt analysis of this task's implemented
    solution. 12 items: 2 BLOCKER, 8 deferred follow-ups, 2 `PRE-EXISTING` NON-BLOCKERs.
    11 follow-up rows (F1–F11) ready for Jira links.
  - [/] Analysis + artifact only. No production code, test, cap, baseline, snapshot,
    allowlist or mypy-baseline change in this step. `Makefile` and
    `tests/test_example_fixtures.py` (unrelated PYPOST-1056/PYPOST-1048 work) untouched.
    No state-changing git command was run.
  - [/] **BLOCKER D1** — the extraction moved **339** previously-capped lines into uncapped
    space and neither new module was added to the cap table.
    `pypost/ui/mcp_server_controller.py` (269 LOC) and
    `pypost/ui/presenters/mcp_controls_presenter.py` (329 LOC) appear in neither `FILE_CAPS`
    (`scripts/audit_baseline_metrics.py:29-56`) nor `AUDIT_ERA_LOC` (`:16-26`), so
    `measure_all()` (`:121-123`) never opens them and `check_caps()` (`:126-130`) cannot fail
    on them; `ai-tasks/PYPOST-376/baseline-metrics.md` has no row for either. `main_window.py`
    565 → 433 (−132) and `env_presenter.py` 599 → 392 (−207). This is the one
    Definition-of-Done item in `10-requirements.md` ("SOLID checks keep detecting future
    unapproved growth") that
    the implemented solution does not meet. Fix: caps 296 and 362 at the ~10% policy, then
    `--markdown` regeneration. Precedent checked: PYPOST-1025's `collections_panel.py` is also
    uncapped but is 53 LOC of stateless assembly, so it does not cover this case.
  - [/] **BLOCKER D2** — the comment this task added at
    `scripts/verify_ai_task_artifacts.py:16-18` justifies dropping `70-dev-docs.md` by claiming
    "Step 8 stays enforced through roadmap completion and the `doc/dev/` paths each roadmap
    records". Neither control exists: `is_roadmap_completed` (`:56-67`) ends with
    `all(... for step in range(1, 8))` — steps 1–7 only — the collapsed regex (`:40-43`)
    matches literally `STEP 1-7`, and the script never reads `doc/dev/`. `range(1, 8)` is
    pre-existing
    at `HEAD`; only the comment is new. Fix is a comment rewrite plus the matching sentence in
    `20-architecture.md`; restoring a real Step 8 check is deferred (F3).
  - [/] Deferred (D3–D10): no dedicated test module for either new module (measured 79% /
    78% line coverage from their own test neighbourhood, 88 passed); `_open_mcp_servers`
    (`mcp_controls_presenter.py:283-311`) has zero test references, so Step 6's
    `mcp_servers_dialog_opened` INFO (`:292`) and the `mcp_servers_dialog_no_controller`
    WARNING (`:287`) are unasserted; the dialog-open log deep-copies every persisted row;
    the inherited `getattr` "test-double-safe" fallback (`mcp_server_controller.py:190-203`);
    the `for_window` back-reference and its partially-built-window temporal coupling; the
    retained `EnvPresenter` shims plus its stale class docstring (`env_presenter.py:52`); the
    re-published `window.mcp_manager` / `window.mcp_registry` aliases; and the unreachable C2
    allowlist rule (`tests/expected_log_allowlist.yaml:45-51`, confirmed against
    `unittest/_log.py`, which sets `logger.propagate = False` **and** replaces the handlers).
  - [/] `PRE-EXISTING` NON-BLOCKERs, both re-verified rather than copied: the CI ERROR
    guardrail is vacuous — reproduced 111 bytes vs **0** bytes of `--log-file` output with and
    without `tests/test_agent_lifecycle_smoke.py` collected first, and
    `scripts/verify_test_log_guardrails.py` reports `ERROR count: 0 ... PASS` exit 0 on the
    empty file (`.github/workflows/test.yml:144,147-149`); and `make typecheck` exits 1 with
    8 off-baseline Qt overload errors plus one stale baseline entry, none in files this task
    touched and zero in the two new modules (`make check` does not run `typecheck`).
  - [/] No `do-testing` BLOCKER: every changed test module carries a module-level
    `pytestmark` timeout (verified individually, 30–120 s), and the only ERROR in this diff
    (`mcp_server_start_failed_ui`) satisfies caplog clause **C1** at
    `tests/test_env_presenter.py:453`.
  - [/] No pre-existing failing tests were observed at any point in this step.
  - [/] **Both BLOCKERs fixed after the Step 7 review** (F1, F2 in `60-tech-debt.md`;
    `Makefile` and `tests/test_example_fixtures.py` untouched, no state-changing git command).
    **D1/F1:** LOC re-measured with the generator's own `splitlines()` method — 269 and 329 —
    so the ~10% policy gives `ceil(269*1.10) = 296` and `ceil(329*1.10) = 362`;
    `pypost/ui/mcp_server_controller.py` (296) and
    `pypost/ui/presenters/mcp_controls_presenter.py` (362) added to `FILE_CAPS` with adjacent
    PYPOST-1071 rationale comments; `ai-tasks/PYPOST-376/baseline-metrics.md` regenerated with
    `--markdown` only (exactly two new rows, nothing else changed); `doc/dev/solid_audit.md`
    PYPOST-1071 paragraph updated with both caps. `AUDIT_ERA_LOC` untouched — neither module
    existed in the 2026-03 audit.
    **D2/F2:** the `STANDARD_FILES` comment in `scripts/verify_ai_task_artifacts.py` rewritten
    to state that `70-dev-docs.md` was retired because Step 8's output is `doc/dev/` and that
    **no automated check currently verifies Step 8 completion** (`range(1, 8)` covers steps
    1-7; the script never reads `doc/dev/`); the two matching sentences in `20-architecture.md`
    (data-flow invariant 6 and the Step 8 Q&A) corrected the same way. `range(1, 8)` and
    `_COLLAPSED_STEP_RE` deliberately unchanged — a real Step 8 check is deferred F3.
    No `--update-baseline` run; `ai-tasks-artifacts-baseline.json` untouched.
    Verification: `audit_baseline_metrics.py --check` exit 0;
    `verify_ai_task_artifacts.py` exit 0 (805 completed tasks; 227 grandfathered legacy gaps);
    `make lint` clean; full fast suite **2218 passed**, unchanged.
- [x] **STEP 8: Dev Docs**
  - [/] Step 8's artifact is `doc/dev/` itself — PYPOST-1071 retired the per-task
    `70-dev-docs.md` requirement, so no such file is created. Documentation only: no
    production code, test, cap, baseline, snapshot, allowlist or mypy-baseline change; no
    `--update-baseline` and no `--markdown` run. `Makefile` and
    `tests/test_example_fixtures.py` (unrelated PYPOST-1056/PYPOST-1048 work) untouched. No
    state-changing git command was run.
  - [/] `doc/dev/mcp_integration.md` — the architecture section described `EnvPresenter` as
    the owner of the MCP controls (old § 4). Replaced with three sections that match the
    post-extraction code: **§ 4 `McpServerSettingsController`** (registry/manager
    construction, persisted-row mutation, transactional reconfiguration, start/stop/remove,
    the readiness-gate pass-through and the `McpServerController` protocol surface),
    **§ 5 `McpControlsPresenter`** (widgets, status label, the three dialogs, legacy
    single-server adapter) and **§ 6 `EnvPresenter`** (environment state, variable supplier,
    and the four retained `mcp_*` shims with the `main_window_signals.py:18,21,31` reason and
    the PYPOST-1082 retirement link). Metrics stack renumbered § 5 → § 7. Four Key Flows
    corrected: startup load now attributed to the controller, tools overview and scoped
    refresh to the controls presenter, and activity inspection to
    `McpServerSettingsController.mcp_server_activity()` (`MainWindow` no longer has that
    method).
  - [/] `doc/dev/logging.md` — MCP catalog. Removed the two rows attributing
    `mcp_activity_dialog_opened` and `mcp_tools_overview_opened` to the "env presenter" and
    added two new subsections with all 14 UI-layer MCP events verified against the source:
    six controller events (`mcp_manager_source`, `mcp_registry_source`,
    `mcp_persisted_servers_loaded`, `mcp_servers_persist_requested`,
    `mcp_server_reconfigure_finished`, `mcp_server_activity_unavailable`) and eight controls
    events (`mcp_server_started`, `mcp_server_stopped`, `mcp_server_start_failed_ui`,
    `mcp_active_env_changed`, `mcp_tools_overview_opened`, `mcp_activity_dialog_opened`,
    `mcp_servers_dialog_opened`, `mcp_servers_dialog_no_controller`). Documented the
    `reason` value set, the log-before-write pairing with `config_save_failed`, the
    counts-only rule, the changed **logger name** for the moved events, and the dormant C2
    allowlist rule with its PYPOST-1087 link.
  - [/] `doc/dev/mcp_server_registry.md` — registry construction, persisted-row loading and
    non-running-edit persistence re-attributed from `MainWindow` to
    `McpServerSettingsController`; the **MCP Servers…** entry point from `EnvPresenter` to
    `McpControlsPresenter`; Observability section now names the controller's persistence
    events and links the catalog.
  - [/] `doc/dev/architecture.md` — `pypost/ui/` module tree gained
    `mcp_server_controller.py` and `McpControlsPresenter`; the MainWindow/Presenters bullets
    now state that MCP persistence/lifecycle belongs to `McpServerSettingsController` and MCP
    UI to `McpControlsPresenter`.
  - [/] `doc/dev/testability.md` — injection table: `MCPServerManager` consumer chain
    corrected to `MainWindow` → `McpServerSettingsController` → `EnvPresenter` →
    `McpControlsPresenter`, and a new `MCPServerRegistry` row added.
  - [/] `doc/dev/maintainability_audit.md` — the log/dialog example row for the MCP start
    failure moved from `EnvPresenter` to `McpControlsPresenter._on_mcp_start_failed`, and its
    "inline warning (migration candidate)" corrected to the real helper
    `show_mcp_server_start_failed` (`pypost/ui/collection_item_dialogs.py:180`).
  - [/] `doc/prometheus_monitoring.md` — one-line fix to the inbound anchor invalidated by
    the `mcp_integration.md` renumbering (`#4-…` → `#7-metrics-observability-stack-…`); the
    anchor was already stale before this task.
  - [/] Checked and left unchanged because they are already correct: `doc/dev/setup.md`
    (Step 8 / `doc/dev/` wording and the 7-file Code Audit standard, updated in Steps 4-5),
    `doc/dev/solid_audit.md` (PYPOST-1071 paragraph carries all five caps plus the two new
    module caps), `doc/dev/mcp_secrets_policy.md` and `doc/dev/architecture_audit.md`
    (`EnvPresenter` still owns the legacy variable supplier — verified at
    `env_presenter.py:86-87`).
  - [/] Verification: `tests/test_verify_ai_task_artifacts.py` +
    `tests/test_solid_audit_baseline.py` + `tests/test_mcp_user_docs.py` +
    `tests/test_ui_actions_mcp_packaging_doc.py` **35 passed**; `pytest tests/ -k doc`
    **56 passed, 2184 deselected**; `scripts/verify_ai_task_artifacts.py` exit 0
    (805 completed tasks; 227 grandfathered legacy gaps);
    `scripts/audit_baseline_metrics.py --check` exit 0.
  - [/] **Review fix round 1** — Step 8 review returned FAIL with four `fixable` gaps; all
    four closed, documentation only.
    1. `doc/dev/logging.md` — the `mcp_registry_*` parenthetical claimed all four events are
       keyed by `instance_id` **and** `port`. False for `mcp_registry_status`
       (`pypost/core/mcp_server_registry.py:520-523` logs
       `instance_id / state / message_present`, no port); the other three do carry `port`
       (`:91`, `:118`, `:429`). Restated as "all keyed by `instance_id`, and all but
       `mcp_registry_status` also by `port`".
    2. Line length — five rows exceeded the 100-char limit of
       `scripts/check-line-length.sh`. The two new logging tables each had a `Module` column
       whose value was identical on every row, so the column was replaced by a single
       "Every event below is emitted by the `<logger>` logger." lead-in (fixes
       `logging.md` `mcp_server_reconfigure_finished` 102 and `mcp_active_env_changed` 106).
       `testability.md` rows 34-35 (129 / 165) now point at a new "MCP chain (PYPOST-1071)"
       note below the table, which also records that the controller builds the registry
       unless `MainWindow(mcp_registry=…)` supplies one (`pypost/main.py:130-136` supplies
       none). `maintainability_audit.md:143` (111) shortened to `McpControlsPresenter` MCP
       start. No added line in any touched doc exceeds 100 chars.
    3. `doc/dev/logging.md` — the counts-only rule said "endpoint ids … never appear …;
       `instance_id` is the one opaque identifier permitted", but `instance_id` *is* the
       endpoint id and is logged at `pypost/ui/mcp_server_controller.py:133,211`. Reworded
       to "collection ids, environment ids, hosts and ports never appear".
    4. `doc/dev/architecture.md:63` — stale `pypost/ui/` module count `61` → **65**
       (`find pypost/ui -name '*.py' -not -name '__init__.py' | wc -l` = 65).
  - [/] Reviewer nit also taken (genuinely more accurate): `doc/dev/mcp_integration.md`
    § 6 cited `main_window_signals.py:18,21,31` as the reason all four `mcp_*` shims are
    retained, but those lines justify only `refresh_mcp_tools`. The other three getters are
    consumed only by `tests/test_env_presenter.py`; both reasons are now stated, matching the
    source comment at `env_presenter.py:179-181`.
  - [/] Fix-round verification: `tests/test_verify_ai_task_artifacts.py` +
    `tests/test_solid_audit_baseline.py` re-run after the edits.
- [x] **COMMIT: Commit Changes**
  - Commit `c38ab84d` on `dev` — `fix(audit): PYPOST-1071 restore green SOLID and artifact
    baselines` (35 files, +3154/-1054).
  - Deliberately excluded from this commit: `Makefile` and `tests/test_example_fixtures.py`,
    which carry unrelated in-progress PYPOST-1056 / PYPOST-1048 work and remain uncommitted.
  - Follow-ups filed in Phase D: PYPOST-1079 … PYPOST-1087 (31 SP).

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1071/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1071/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1071/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1071/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1071/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
