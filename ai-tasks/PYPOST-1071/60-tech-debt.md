# PYPOST-1071: Technical Debt Analysis

Scope: the solution this task implemented — the two new MCP modules, the four modified
source/script files, the changed tests and allowlist, and the two regenerated baselines.
Items that pre-date this diff are marked `PRE-EXISTING` and classified `NON-BLOCKER`.

Every file, line number, count and command below was re-measured against the working tree
while writing this report. Measurement commands are quoted where a number is load-bearing.

## Summary

| # | Item | Severity | Priority | Classification |
| --- | --- | --- | --- | --- |
| D1 | New modules absent from `FILE_CAPS` | High | High | **BLOCKER — RESOLVED** |
| D2 | Verifier comment claims a Step 8 control that does not exist | Medium | High | **BLOCKER — RESOLVED** |
| D3 | No dedicated test module for either new module | Medium | Medium | Deferred |
| D4 | `_open_mcp_servers` untested, including its new INFO log | Medium | Medium | Deferred |
| D5 | Dialog-open log deep-copies every persisted MCP row | Low | Low | Deferred |
| D6 | `getattr` "test-double-safe" fallback in production lookup | Low | Low | Deferred |
| D7 | `for_window` back-reference and partially-built window | Low | Low | Deferred |
| D8 | `EnvPresenter` MCP shims, stale docstring, reach-through test | Low | Low | Deferred |
| D9 | `MainWindow` re-publishes the controller's manager/registry | Low | Low | Deferred |
| D10 | C2 allowlist rule is unreachable configuration | Low | Low | Deferred |
| D11 | CI ERROR guardrail is vacuous (`PRE-EXISTING`) | Medium | Medium | NON-BLOCKER |
| D12 | 8 off-baseline mypy errors + 1 stale entry (`PRE-EXISTING`) | Low | Low | NON-BLOCKER |

Two blockers. Both are cheap to close and both map onto a stated Definition-of-Done item in
[10-requirements.md](10-requirements.md); neither requires reopening the extraction.

**Both blockers were fixed in this task after this analysis was written** (see the
`RESOLVED` blocks under D1 and D2, and F1/F2 in [Follow-up Tasks](#follow-up-tasks)). The
descriptions below are kept as written — they record the state that was found — and each
carries a resolution note.

## Shortcuts Taken

### D1 — the extraction moved 339 capped lines into uncapped space (BLOCKER)

**What.** Step 4 resolved three of the five baseline failures by extracting code out of two
capped modules into two brand-new modules. Neither new module was added to the cap table, so
the SOLID guard no longer measures that code at all.

**Where.**

- `scripts/audit_baseline_metrics.py:29-56` — `FILE_CAPS`, 13 entries, neither new module.
- `scripts/audit_baseline_metrics.py:16-26` — `AUDIT_ERA_LOC`, neither new module.
- `scripts/audit_baseline_metrics.py:121-123` — `measure_all()` measures exactly
  `set(FILE_CAPS) | set(AUDIT_ERA_LOC)`, so an unlisted file is never opened.
- `scripts/audit_baseline_metrics.py:126-130` — `check_caps()` iterates only `measure_all()`.
- `ai-tasks/PYPOST-376/baseline-metrics.md` — 12 module rows, no row for either new module.

**Measured evidence.**

```console
$ wc -l pypost/ui/mcp_server_controller.py pypost/ui/presenters/mcp_controls_presenter.py
     269 pypost/ui/mcp_server_controller.py
     329 pypost/ui/presenters/mcp_controls_presenter.py
```

| Module | LOC at `HEAD` | LOC now | Capped now? |
| --- | ---: | ---: | --- |
| `pypost/ui/main_window.py` | 565 | 433 | yes (477) |
| `pypost/ui/presenters/env_presenter.py` | 599 | 392 | yes (432) |
| `pypost/ui/mcp_server_controller.py` | — | 269 | **no** |
| `pypost/ui/presenters/mcp_controls_presenter.py` | — | 329 | **no** |

`132 + 207 = 339` lines that were under a cap before this task are under no cap after it.

**Why it is debt.** [10-requirements.md](10-requirements.md) states the user story *"As a
maintainer, I want SOLID checks to keep detecting future unapproved growth, so resolving
today's failures does not silently weaken regression protection"*, and the Definition of Done
requires the SOLID baseline to *"continue to reject future unapproved regressions"*. The
growth that caused this task was PYPOST-1044 adding multi-server MCP persistence, lifecycle
and dialog code. That code now lives where an identical future addition fails no check.

**Precedent, checked honestly.** PYPOST-1025's extraction target
`pypost/ui/presenters/collections_panel.py` is also uncapped, so "extraction targets are
capped" is not an existing repository rule. But that file is 53 lines of stateless panel
assembly, whereas these are 269 and 329 lines of stateful persistence, lifecycle and dialog
routing — the exact category the `MainWindow` regression guard exists to watch. The precedent
does not cover this case.

**Severity High / Priority High. BLOCKER** — it is the one requirement in this task's own
Definition of Done that the implemented solution does not satisfy.

**Suggested fix (Step 4 procedure, already documented in `doc/dev/solid_audit.md`):** add both
paths to `FILE_CAPS` at the repository's ~10% headroom policy — `ceil(269 * 1.10) = 296` and
`ceil(329 * 1.10) = 362` — with adjacent rationale comments, regenerate
`ai-tasks/PYPOST-376/baseline-metrics.md` through `--markdown` only, and refresh the
`doc/dev/solid_audit.md` PYPOST-1071 paragraph. `--check` and
`tests/test_solid_audit_baseline.py` then cover the new modules.

**RESOLVED in this task (F1).** LOC was re-measured with the generator's own method
(`Path.read_text().splitlines()`, as `count_file_lines()` does), confirming 269 and 329;
`ceil(269 * 1.10) = 296` and `ceil(329 * 1.10) = 362`. Both paths were added to `FILE_CAPS`
(`scripts/audit_baseline_metrics.py`) with adjacent PYPOST-1071 rationale comments in the
style of the existing cap comments. `ai-tasks/PYPOST-376/baseline-metrics.md` was regenerated
with `--markdown` (the only approved path); the regeneration added exactly the two new rows
`| pypost/ui/mcp_server_controller.py | — | 269 | 296 |` and
`| pypost/ui/presenters/mcp_controls_presenter.py | — | 329 | 362 |` and changed nothing else.
`doc/dev/solid_audit.md`'s PYPOST-1071 paragraph now records both new caps. `--check` exits 0
and `tests/test_solid_audit_baseline.py` passes (4 tests), so the 339 relocated lines are
measured again. `AUDIT_ERA_LOC` was deliberately not touched: neither module existed in the
2026-03 audit, and the generator renders `—` for a missing audit-era value.

### D2 — the removal of `70-dev-docs.md` cites a control that does not exist (BLOCKER)

**What.** Step 4 removed `70-dev-docs.md` from the required artifact sets. The disposition
itself is sound (all 30 apparent additions were only that obsolete file). The *justification
committed alongside it* is factually wrong.

**Where.** `scripts/verify_ai_task_artifacts.py:16-18`, added by this task:

> `# Step 8 stays enforced through roadmap completion and the doc/dev/ paths each roadmap`
> `# records, so the obsolete filename is not a required artifact.`

**Counter-evidence in the same file.**

- `scripts/verify_ai_task_artifacts.py:56-67` — `is_roadmap_completed()` ends with
  `return all(step_status.get(step, False) for step in range(1, 8))`. `range(1, 8)` is steps
  **1 through 7**. STEP 8 is never required for a folder to count as completed.
- `scripts/verify_ai_task_artifacts.py:40-43` — the collapsed form matches literally
  `STEP 1-7`, so it too ignores Step 8.
- Nothing in the script reads `doc/dev/` at all — `grep -n "doc/dev"` over
  `scripts/verify_ai_task_artifacts.py` returns nothing.

So after this change there is **no automated evidence anywhere** that a completed task
produced Step 8 developer documentation, and the comment tells a reader the opposite. The same
claim appears in [20-architecture.md](20-architecture.md) ("A task still must mark Step 8
complete in its roadmap") and, more carefully worded, in `doc/dev/setup.md:331-333`.

**Why it is debt.** The Definition of Done says *"No protected check is skipped, removed, or
made ineffective merely to obtain a green result"*, and the Transparency non-functional
requirement says accepted baseline changes must be reviewable. A false compensating control in
the production script is the least reviewable form this could take. Two earlier artifacts in
this task were rejected for unverified claims; this is the same class of defect, but shipped in
code rather than in a report.

**Not caused here, and stated as such:** `range(1, 8)` is present verbatim at `HEAD`
(`git show HEAD:scripts/verify_ai_task_artifacts.py`). Only the comment is new.

**Severity Medium / Priority High. BLOCKER** — the fix is a comment rewrite, no behaviour
change: state that Step 8 output is reviewed manually under `doc/dev/` and that the verifier
deliberately does not check it. Correcting the matching sentence in
[20-architecture.md](20-architecture.md) is recommended in the same pass. Restoring a real
Step 8 check (see [Follow-up Tasks](#follow-up-tasks), F3) is separate, deferred work.

**RESOLVED in this task (F2).** The comment above `STANDARD_FILES` in
`scripts/verify_ai_task_artifacts.py` was rewritten to state the retirement reason (Step 8's
output is `doc/dev/`, per `td-70-dev-docs`) and to say plainly that **no automated check
currently verifies Step 8 completion** — naming both facts that make it so, `range(1, 8)` in
`is_roadmap_completed` and the absence of any `doc/dev/` read — and that restoring one is
tracked follow-up work. No compensating control was invented. The two matching sentences in
[20-architecture.md](20-architecture.md) (data-flow invariant 6 and the "Does removing
`70-dev-docs.md` stop developer-documentation enforcement?" Q&A) were corrected the same way;
the Q&A now answers that nothing automated replaces it and points at F3. `range(1, 8)` and
`_COLLAPSED_STEP_RE` were left exactly as they are — changing them is F3, out of scope.
Behaviour is unchanged: `tests/test_verify_ai_task_artifacts.py` passes (19 tests) and
`scripts/verify_ai_task_artifacts.py` exits 0 with the same
`805 completed tasks; 227 grandfathered legacy gaps` line, with no `--update-baseline` run.

### D10 — the C2 allowlist rule cannot fire under the current suite

**What.** Step 6 registered `mcp_server_start_failed_ui` under its new logger name in the CI
ERROR allowlist. The rule is unreachable.

**Where.** `tests/expected_log_allowlist.yaml:45-51`; the only test that emits the event is
`tests/test_env_presenter.py:453`.

**Verified mechanism.** `unittest._log._AssertLogsContext.__enter__` sets both
`logger.handlers = [handler]` and `logger.propagate = False`
(`/opt/homebrew/.../python3.14/unittest/_log.py`, read directly). The ERROR reaches the
assertion's handler and never the root handler that `--log-file` installs, so the CI verifier
cannot observe it and the rule is never consulted.

**Assessment.** [50-observability.md](50-observability.md) already documents this honestly and
keeps the rule deliberately, which is the right call — the rule becomes live the moment the
event is logged outside an `assertLogs` block. It is recorded here only because unreachable
configuration decays silently. **Severity Low / Priority Low. Deferred.**

## Code Quality Issues

### D6 — duck-typed fallback that exists for test doubles

`pypost/ui/mcp_server_controller.py:190-203`:

```python
def _collection_by_id(self, collection_id: str) -> Collection | None:
    """Use the collection presenter lookup, with a test-double-safe fallback."""
    lookup = getattr(self._collections_provider(), "collection_by_id", None)
```

A production branch whose stated reason is accommodating test doubles. It is **inherited, not
created** — `git show HEAD:pypost/ui/main_window.py` carries the identical method with the
identical docstring at `HEAD`:398-410. This task relocated it and (Step 4 iteration 5) edited
its return typing. Recording it because the relocation is the moment it acquired a new owner.
**Severity Low / Priority Low. Deferred.**

### D7 — `for_window` couples the extracted controller back to the composition root

- `pypost/ui/mcp_server_controller.py:22-23` — `TYPE_CHECKING` import of `MainWindow`
  (commented "import cycle guard").
- `pypost/ui/mcp_server_controller.py:76-97` — `for_window(cls, window: MainWindow, ...)`.
- `pypost/ui/main_window.py:107-109` — the call site.

Two observations. First, the extracted controller now names its own composition root, which
partially re-couples what [20-architecture.md](20-architecture.md) separated; the primary
`__init__` is clean (callables only), so this is a convenience factory, not a structural
regression. Second, and more concrete: `for_window` is invoked at `main_window.py:107` while
`self.env` is not assigned until `main_window.py:121`, and the constructor calls
`_load_persisted_mcp_servers()` (`:74`) before returning. Nothing breaks today —
`MCPServerRegistry.upsert()` (`pypost/core/mcp_server_registry.py:73-80`) does not invoke
`collection_lookup` or `environment_lookup`, so the `lambda … window.env.environment_by_id(…)`
is never called during construction. It is a latent temporal coupling: any future eager
reference resolution in the controller's constructor raises `AttributeError`.
**Severity Low / Priority Low. Deferred.**

### D8 — retained `EnvPresenter` shims, stale docstring, reach-through test

- `pypost/ui/presenters/env_presenter.py:182-189` (three text shims) and `:363-365`
  (`refresh_mcp_tools`) — four delegating `mcp_*` shims, kept deliberately because
  `pypost/ui/main_window_signals.py:18,21,31` connect `window.env.refresh_mcp_tools` to three
  Qt signals. Verified: all three connect lines are present. This is documented and correct for
  this task's scope, but it leaves MCP refresh routed through the environment presenter after
  MCP was extracted out of it.
- `pypost/ui/presenters/env_presenter.py:52` — class docstring still reads *"Owns the
  environment selector: loading envs, propagating vars, managing MCP lifecycle."* After the
  extraction it delegates MCP lifecycle to `McpControlsPresenter`. Step 5 audited comments and
  missed this one.
- `tests/test_env_presenter.py:454` — `p._mcp_controls._on_mcp_start_failed("Port is busy")`
  reaches through two private members. Before the extraction this was a single-level private
  call; the relocated test kept the shape rather than driving the seam.

**Severity Low / Priority Low. Deferred.**

### D9 — the window re-publishes what the controller now owns

`pypost/ui/main_window.py:110-111` assigns `self.mcp_manager = self.mcp_controller.manager` and
`self.mcp_registry = self.mcp_controller.registry`, so every existing caller and test can still
bypass the new boundary through the window. Necessary for a behaviour-preserving extraction,
and a genuine leak of the seam this task created. **Severity Low / Priority Low. Deferred.**

## Missing Tests

All changed test modules carry an explicit timeout marker — verified individually:
`test_main_window.py:3` (60), `test_env_presenter.py:3` (60), `test_verify_ai_task_artifacts.py:21`
(30), `test_solid_audit_baseline.py:11` (30), `test_apply_settings_font.py:4` (60),
`test_main_window_alert_reload.py:15` (60), `test_main_window_encrypted_startup.py:11` (120),
`test_main_window_shutdown.py:5` (120), and the four `test_settings_*_main_window_e2e.py`
modules (120 each). **No `do-testing` timeout BLOCKER exists.**

The `do-testing` caplog contract applies to tests that deliberately trigger production **ERROR**
logs. This task's only ERROR, `mcp_server_start_failed_ui`, satisfies C1 at
`tests/test_env_presenter.py:453`. **No caplog BLOCKER exists.**

### D3 — neither new module has a dedicated test module

`ls tests/ | grep -iE "mcp|controller|presenter"` lists 31 modules; there is no
`test_mcp_server_controller.py` and no `test_mcp_controls_presenter.py`. Both new modules are
exercised only through the relocated `tests/test_main_window.py` and
`tests/test_env_presenter.py` cases plus patch targets in eight further window/settings modules.

Measured coverage of the two modules from their own test neighbourhood:

```console
$ QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
    tests/test_main_window.py tests/test_env_presenter.py tests/test_mcp_servers_dialog.py \
    tests/test_main_window_shutdown.py tests/test_mcp_server_registry.py \
    -p no:randomly -q --cov=pypost.ui.mcp_server_controller \
    --cov=pypost.ui.presenters.mcp_controls_presenter --cov-report=term-missing
88 passed
pypost/ui/mcp_server_controller.py                 110   23   79%
pypost/ui/presenters/mcp_controls_presenter.py     175   38   78%
```

Uncovered in that run: `mcp_server_controller.py` 108, 117, 124, 128-135, 141-142, 148-156,
192-196, 246 — this includes the whole `mcp_server_activity()` `KeyError` path (128-135) and
the whole create/update persist path of `upsert_mcp_server` (148-156); the tested mutations are
start/stop/remove only. `mcp_controls_presenter.py` 132, 141, 171-175, 190, 195, 212-216, 257,
267-273, 276-281, 285-311, 314-315, 318, 323.

79% is not alarming for behaviour-preserving extraction, and the moved behaviour keeps the
tests it always had. The debt is structural: a 269-line and a 329-line module with no test file
of their own accrete untested branches, and the gaps above show that already starting.
**Severity Medium / Priority Medium. Deferred.**

### D4 — `_open_mcp_servers` is not exercised by any test

`grep -rn "_open_mcp_servers\|_mcp_servers_btn\|mcp_servers_dialog_opened" tests/` returns
**zero** hits. The whole method `pypost/ui/presenters/mcp_controls_presenter.py:283-311` is
untested, which includes:

- the `mcp_servers_dialog_no_controller` WARNING at `:287` (moved here with the extraction), and
- the `mcp_servers_dialog_opened` INFO added by Step 6 at `:292-295`.

Four of the five statements Step 6 added are locked by new tests
(see [50-observability.md](50-observability.md)); this one is not. It is the only added
observability statement with no assertion behind it, and it sits on the single entry point for
every `mcp_servers_persist_requested` mutation. **Severity Medium / Priority Medium. Deferred.**

## Performance Concerns

### D5 — the dialog-open log deep-copies every persisted MCP row

`pypost/ui/presenters/mcp_controls_presenter.py:292-295` calls
`controller.mcp_server_configurations()` purely to take its `len()`, and then passes the same
bound method to the dialog at `:297`. `McpServerSettingsController.mcp_server_configurations()`
(`pypost/ui/mcp_server_controller.py:115-120`) is not a cheap accessor:

```python
return [
    configuration.model_copy(deep=True)
    for configuration in self._settings.mcp_servers
]
```

So opening the dialog performs one extra full deep copy of every configured endpoint purely to
produce an integer. Honest magnitude: this is a user-initiated click, and `mcp_servers` holds
single-digit rows in practice, so the measurable cost is negligible — it is recorded as
avoidable work introduced by this task, not as a user-visible problem. Taking the length of
`self._settings.mcp_servers`, or adding a dedicated count accessor, removes it.
**Severity Low / Priority Low. Deferred.**

No other performance concern was found. The extraction added no new request path, no new loop
over collections, and no additional I/O; `_save_mcp_server_configurations`
(`pypost/ui/mcp_server_controller.py:257-269`) writes exactly as often as `MainWindow` did at
`HEAD`.

## Deviations from the Approved Architecture

None material. [20-architecture.md](20-architecture.md) prescribed the two extractions, the
`McpServerController` protocol, the retained `EnvPresenter` shims, the 418/403 accepted caps and
the artifact-contract change; all landed as designed. Two soft deviations are recorded above
rather than here because they are small: the `for_window` back-reference (D7), which the
architecture did not describe, and the cap table not being extended to the new modules (D1),
which the architecture did not mention either way.

## Hardcoded Values

Reviewed and accepted; nothing new is a magic number.

- The caps this task set — `477` (`scripts/audit_baseline_metrics.py:33`), `403` (`:39`),
  `432` (`:43`), `418` (`:52`) and `MAIN_WINDOW_CLASS_CAP = 426` (`:60`) — each carry an
  adjacent PYPOST-1071 rationale comment and follow the documented ~10% headroom policy.
- UI strings and colours in `mcp_controls_presenter.py` (`"MCP: OFF"`, `#b8860b`, `#b00020`,
  `"MCP Server Tools…"`) moved verbatim from `env_presenter.py`; styling is inline throughout
  this UI layer, so this task neither improved nor worsened it.
- `CODE_AUDIT_TASKS = frozenset(f"PYPOST-{number}" for number in range(684, 690))`
  (`scripts/verify_ai_task_artifacts.py:38`) is pre-existing and untouched.

## Pre-existing Findings (NON-BLOCKER)

### D11 — the CI ERROR guardrail inspects an empty log on a full-suite run

**Where.** `.github/workflows/test.yml:144` writes `--log-file=pytest.log --log-file-level=WARNING`;
`.github/workflows/test.yml:147-149` runs `scripts/verify_test_log_guardrails.py pytest.log`.

**Reproduced during this step**, offline, in a few seconds:

```console
$ pytest tests/test_env_presenter.py -p no:randomly -o log_cli=false \
      --log-file=a.log --log-file-level=WARNING
$ wc -c a.log
     111 a.log          # 1 ERROR: pypost.ui.presenters.env_presenter: storage_save_failed

$ pytest tests/test_agent_lifecycle_smoke.py tests/test_env_presenter.py -p no:randomly \
      -o log_cli=false --log-file=b.log --log-file-level=WARNING
$ wc -c b.log
       0 b.log

$ .venv/bin/python scripts/verify_test_log_guardrails.py b.log
ERROR count: 0 (max allowed: 77)
PASS: all ERROR lines match allowlist and count within margin   # exit 0
```

Collecting `tests/test_agent_lifecycle_smoke.py` silences `--log-file` capture for the rest of
the session, and that module is collected in the full `-m "not slow"` run. The guardrail
therefore passes unconditionally in CI, which is why the (previously unlisted)
`mcp_server_start_failed_ui` ERROR never failed a build. The exact mechanism inside the agent
module was not root-caused; [50-observability.md](50-observability.md) records the causes
already ruled out.

**PRE-EXISTING and unrelated to this diff** — PYPOST-1071 touches no conftest, no test
configuration and no agent module. **Severity Medium / Priority Medium. NON-BLOCKER.**

### D12 — `make typecheck` is red at `HEAD`

`make typecheck` exits 1 with **8** off-baseline errors, all Qt `SignalInstance.connect` /
worker `emit` overload complaints: `pypost/core/qt/worker.py` (2 errors, lines 31 and 147),
`pypost/ui/main_window_signals.py` (4 errors, across lines 22, 23, 24, 28 and 32),
`pypost/ui/presenters/collection_import_actions.py` (1, line 103),
`pypost/ui/presenters/tabs_presenter.py` (1, line 127). It additionally reports one **stale
baseline entry** to remove (`pypost/ui/widgets/settings/encryption_migration_section.py`).
Baseline 219, current 227.

None of those files appear in this task's `git status`, and zero off-baseline errors point at
either new module, so the extraction introduced no type regression. `make check` is
`lint test verify-ai-tasks` (`Makefile:143`) and does not include `typecheck`, so the
repository gate is unaffected. **PRE-EXISTING. Severity Low / Priority Low. NON-BLOCKER.**

### Pre-existing failing tests found during this run

None. No test failure was observed at any point in this step.

## Follow-up Tasks

Rows without a Jira link are unticketed; `tech-debt-jira-sync` fills the link column in place.

| ID | Follow-up | Item | Priority | Jira |
| --- | --- | --- | --- | --- |
| F1 | Cap both new modules and regenerate the snapshot | D1 | High | *BLOCKER — done in this task* |
| F2 | Correct the false Step 8 enforcement claim | D2 | High | *BLOCKER — done in this task* |
| F3 | Give Step 8 a real automated check | D2 | Medium | [PYPOST-1079](https://pypost.atlassian.net/browse/PYPOST-1079) (5 SP) |
| F4 | Add dedicated test modules for the two new modules | D3, D4 | Medium | [PYPOST-1080](https://pypost.atlassian.net/browse/PYPOST-1080) (5 SP) |
| F5 | Restore `--log-file` capture so the CI guardrail sees ERRORs | D11 | Medium | [PYPOST-1081](https://pypost.atlassian.net/browse/PYPOST-1081) (8 SP) |
| F6 | Retire the `EnvPresenter` MCP shims and fix its docstring | D8 | Low | [PYPOST-1082](https://pypost.atlassian.net/browse/PYPOST-1082) (3 SP) |
| F7 | Stop deep-copying rows to log a dialog-open count | D5 | Low | [PYPOST-1083](https://pypost.atlassian.net/browse/PYPOST-1083) (1 SP) |
| F8 | Replace the `getattr` test-double fallback with injection | D6 | Low | [PYPOST-1084](https://pypost.atlassian.net/browse/PYPOST-1084) (2 SP) |
| F9 | Drop the window back-reference and the re-published aliases | D7, D9 | Low | [PYPOST-1085](https://pypost.atlassian.net/browse/PYPOST-1085) (3 SP) |
| F10 | Clear the 8 Qt overload mypy errors and the stale entry | D12 | Low | [PYPOST-1086](https://pypost.atlassian.net/browse/PYPOST-1086) (3 SP) |
| F11 | Revisit the unreachable C2 allowlist rule | D10 | Low | [PYPOST-1087](https://pypost.atlassian.net/browse/PYPOST-1087) (1 SP) |

Scope notes for the rows that need more than their one-line summary:

- **F1** — **DONE in this task.** `pypost/ui/mcp_server_controller.py` capped at `296` and
  `pypost/ui/presenters/mcp_controls_presenter.py` at `362` in `FILE_CAPS` with adjacent
  rationale comments; `ai-tasks/PYPOST-376/baseline-metrics.md` regenerated with `--markdown`;
  `doc/dev/solid_audit.md` refreshed. `--check` exits 0.
- **F2** — **DONE in this task.** `scripts/verify_ai_task_artifacts.py`'s `STANDARD_FILES`
  comment and the two matching sentences in [20-architecture.md](20-architecture.md) now state
  that Step 8's output is `doc/dev/` and that no automated check verifies Step 8 completion.
  No behaviour change.
- **F3**: either require the roadmap's STEP 8 mark — `is_roadmap_completed` stops at step 7 —
  or verify the `doc/dev/` paths a completed roadmap records.
- **F4**: `tests/test_mcp_server_controller.py` and `tests/test_mcp_controls_presenter.py`,
  covering the `mcp_server_activity()` `KeyError` path, the create/update persist path, and
  `_open_mcp_servers` including `mcp_servers_dialog_opened` and
  `mcp_servers_dialog_no_controller`.
- **F5**: root-cause the `--log-file` silencing that `tests/test_agent_lifecycle_smoke.py`
  triggers for the rest of a session.
- **F6**: rewire `main_window_signals.py:18,21,31` to the controls presenter, drop the four
  `mcp_*` shims, fix the `EnvPresenter` docstring at `env_presenter.py:52`, and stop the
  reach-through call at `tests/test_env_presenter.py:454`.
- **F7**: `mcp_controls_presenter.py:292-295`.
- **F11**: `tests/expected_log_allowlist.yaml:45-51` — revisit once the event is emitted
  outside an `assertLogs` block, or replace the rule with a note.

## User Documentation

No `doc/` user-facing change is required by this analysis. `doc/dev/solid_audit.md` and
`doc/dev/setup.md` already changed in Step 4/5; F1 and F2 adjust `doc/dev/solid_audit.md` and a
code comment respectively, and the `doc/dev/logging.md` catalog drift is already tabulated for
Step 8 in [50-observability.md](50-observability.md).
