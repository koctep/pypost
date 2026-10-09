# Roadmap: PYPOST-1336

## Task Metadata

- **Implementation language**: N/A for this task (planning/decomposition; deliverables are
  Markdown notes and Jira issues). The child tasks it produces target Python (PyPost desktop
  client, `pypost/`) plus JSON/YAML bundled collection fixtures, executed via `make` only.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1336/10-requirements.md` — requirements for decomposing epic PYPOST-1335
    (coverage, granularity, estimation, epic linking incl. PYPOST-1334, sprint 2025 rule,
    notes in `ai-tasks/PYPOST-1335/`)
  - Scope scan (read-only): `pypost/ui/dialogs/mcp_servers_dialog.py` (sources today:
    Workspace collection / Connected library), `pypost/models/settings.py`
    (`McpServerConfiguration`), `pypost/core/predefined_library.py` (examples library read from
    repo `examples/`, outside the `pypost/` package)
  - PYPOST-1334 confirmed done (commit 31f2b25a); GitHub fixture present in `examples/`
  - [x] Step 1 review and acceptance (gate owner) — review PASS
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1336/20-architecture.md` — high-level design of epic PYPOST-1335 and
    the decomposition plan (9 new child tasks C1a, C1b, C2, C3a, C3b, C4–C7, 37 SP rough,
    each ≤ 5 SP)
  - Open questions resolved: (a) `examples/` stays the single source and ships as package
    data of `pypost.bundled_examples` (`package-dir`, `examples/__init__.py`), one locator
    (sibling source tree first, then package resource); move into `pypost/` rejected
    (churn: 16 Python files, 72 doc lines); (b) Copy for editing creates a workspace
    collection, persisted only on Save; (c) a Built-in server takes variables only from its
    workspace environment (no preset or overlay); paired-environment copy optional;
    structural consistency test (keys, `hidden_keys`, secret placeholders; not values) ties
    the environment file to the manifest; (d) `mcp.json` is not built-in; (e) Built-in is a
    filtered read-only view over the `pypost-examples` library plus a `bundled_library`
    marker, no separate catalog id
  - Validator rule: `library_id` precedence preserved; legacy rows with both fields keep
    working (AC in C3a)
  - Review fix: `examples/` reference inventory, `.gitignore`, packaging detail, Library
    reuse and validator rule addressed
  - Review fix #2: slow-smoke seed honours `package-dir` (C1a); `tomllib` guard, no
    `setuptools`/`wheel` dev dependency, isolated wheel check in slow tier (C1a); locator
    prefers the `examples/` sibling of the imported `pypost` (C1b); controller Built-in save
    branch without overlay (C3b); registry lifecycle fixed for Built-in rows (C3b), library
    rows recorded as a Debt issue created in Step 4; Jira environment values differ from the
    preset — consistency test is structural only, no data change (C2); non-entry Built-in
    rows load but are not served (C3a)
  - Review fix #3: `MCPServerRegistry.__init__` builds the bundled adapter by default, so
    Built-in rows start at every construction point (`McpServerSettingsController.__init__`,
    injected from `main_window.py`, headless `daemon_runtime.py`) — AC for `DaemonRuntime`
    (C3a, stays ~5 SP); Built-in save reuses the workspace checked save with `overlay={}`
    and never builds an overlay candidate (C3b)
  - Step 3 plan: `N/A — no behavioral change` (planning only); gate is `make verify-ai-tasks`
    plus the coverage/size checklist in `20-architecture.md`
  - Step 4 notes location: `ai-tasks/PYPOST-1335/decomposition.md` (no roadmap file there)
  - `make verify-ai-tasks` — run after writing the artifact
  - [x] Step 2 review and acceptance (gate owner) — 3 review rounds (7+7+2 fixable gaps) → re-review
        #3 PASS
- [x] **STEP 3: Failing Repro Test**
  - [x] N/A — no behavioral change: PYPOST-1336 produces only decomposition notes
        (ai-tasks/PYPOST-1335/) and Jira issues; no production code (DoD item 9). Verification gate
        per 20-architecture.md: `make verify-ai-tasks` + coverage/size checklist
  - [x] Step 3 review and acceptance (gate owner) — N/A review PASS
- [x] **STEP 4: Development**
  - [x] `ai-tasks/PYPOST-1335/decomposition.md` written (no roadmap in that folder): epic
    scope E1–E8, decisions (a)–(e) + validator rule with pointer to `20-architecture.md`,
    coverage table (E8 explicit exclusion), child list, dependency graph and execution order,
    PYPOST-1334 link note, out-of-scope statement
  - [x] Issue drafts with Jira-ready `text` descriptions (placeholders `{C1a}`…`{DEBT}` for
    keys): C1a Task ~5, C1b Task ~3, C2 Story ~3, C3a Story ~5, C3b Story ~5, C4 Story ~5,
    C5 Story ~3, C6 Story ~5, C7 Task ~3 (parent PYPOST-1335, sprint 2025; 37 SP rough) and
    DEBT library-row lifecycle defect (Debt ~3, no parent, no sprint)
  - [x] No production code, tests or fixtures changed; `make verify-ai-tasks` and `make lint`
    run
  - [x] Orchestrator: estimated and created all nine child issues PYPOST-1348–PYPOST-1356,
    assigned them to epic PYPOST-1335 and sprint 2025, and filled keys and binding estimates
    into `decomposition.md` (5, 3, 3, 5, 5, 5, 3, 5, 3 SP; total 37 SP).
    Debt PYPOST-1347 has 3 SP and no sprint or epic. PYPOST-1334 is linked to parent
    PYPOST-1335, remains Done, and retains sprint 2024.
  - [x] Review correction: the coverage table now maps E1–E8 to actual Jira keys;
    creation-complete instructions replace the former placeholder instructions. C1a, C1b
    and C7 were drafted as Tasks (history above) but created as Stories, as Jira rejects
    Task. The child list and issue metadata now record their actual types.
  - [x] Step 4 corrections accepted after independent re-review returned PASS.
- [x] **STEP 5: Code Cleanup**
  - `40-code-cleanup.md`: scoped Markdown formatted to 100 characters; lint and artifact
    validation pass; full-suite baseline triage and debt links recorded.
  - No production or test changes; independent acceptance remains pending.
- [x] **STEP 6: Observability**
  - `50-observability.md`: production logs and metrics are N/A for this planning-only task;
    child diagnostics remain assigned to their implementation issues. Review pending.
- [x] **STEP 7: Technical Debt Analysis**
  - `60-tech-debt.md`: no new production debt; existing PYPOST-1347, PYPOST-1298,
    PYPOST-1299 and PYPOST-1357 linked with scope and baseline evidence limitations.
  - Exact affected test identifiers and Make reproductions preserved; review pending.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/predefined_collection_library.md`: planned Built-in design, future usage,
    configuration, diagnostic ownership and no-migration boundary; implementation remains
    assigned to PYPOST-1348–PYPOST-1356. Independent acceptance pending.
  - `make lint` and `make verify-ai-tasks` pass; no production code or test changes.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1336/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1336/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1336/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1336/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1336/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
