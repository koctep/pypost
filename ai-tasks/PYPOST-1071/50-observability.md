# PYPOST-1071: Observability Implementation

## Scope and Method

Step 4 was a behaviour-preserving extraction: almost every log statement in the two new
modules moved verbatim with the code it belongs to — the single exception is the
`mcp_registry_source` pair, which is new code (see
[Verbatim-Moved Logs](#verbatim-moved-logs-inventory-unchanged)). This step therefore did
**not** start from an empty slate. It asked one question per extracted seam — *which
operator question can this seam no longer answer?* — and added only the statements that
close a real gap.

Modules assessed. Counts are logging call sites, counted with a `grep -cE` over the
`logger.debug|info|warning|error|critical|exception` call forms in `git show HEAD:<file>`
versus the working tree:

| File | Status | Log calls at `HEAD` | Log calls now |
| --- | --- | ---: | ---: |
| `pypost/ui/mcp_server_controller.py` | new (extracted) | 2 moved in (DEBUG) | 8 |
| `pypost/ui/presenters/mcp_controls_presenter.py` | new (extracted) | 7 moved in | 8 |
| `pypost/ui/main_window.py` | modified | 19 | 17 |
| `pypost/ui/presenters/env_presenter.py` | modified | 20 | 13 |
| `scripts/verify_ai_task_artifacts.py` | modified | N/A (CLI gate) | N/A |
| `scripts/audit_baseline_metrics.py` | modified | modified caps only | N/A |

How the two new modules reach 8 each:

- `mcp_server_controller.py` = **2 moved** (`mcp_manager_source`, the injected/new pair from
  `main_window.py` at `HEAD`:92,95) **+ 2 new with the extraction**
  (`mcp_registry_source`, :61,64 — `HEAD` built the registry unlogged) **+ 4 added by this
  step** (:133 DEBUG, :211, :236, :264 INFO).
- `mcp_controls_presenter.py` = **7 moved** from `env_presenter.py` **+ 1 added by this
  step** (:292 INFO).

The two `modified` rows fall by exactly what left them: `main_window.py` 19 → 17 is the
`mcp_manager_source` pair moving into the controller, and `env_presenter.py` 20 → 13 is the
seven MCP events moving into the controls presenter. Neither file gained, lost or reworded
any other log statement.

Downstream collaborators were inventoried first, so that nothing already covered was
duplicated. `pypost/core/mcp_server_registry.py` already logs
`mcp_registry_start_requested` (:90), `mcp_registry_stop_requested` (:117),
`mcp_registry_reconfigure_rolled_back` (:428, WARNING) and `mcp_registry_status` (:519),
and publishes `set_mcp_server_instance_counts` on every status change.
`pypost/core/qt/mcp_server.py` already logs `mcp_server_listening` /
`mcp_server_start_failed`. The **runtime lifecycle** of an endpoint was therefore already
well covered; the gap was on the **persistence** side that the new controller now owns.

## Logging Implementation

### Added Logs

Five statements were added. Nothing was added at EMERG, ALERT, CRIT, ERR or WARNING —
no new failure mode was introduced by this task, and every existing failure path already
has an owner that logs it.

- **INFO**: `pypost/ui/mcp_server_controller.py:264` — `mcp_servers_persist_requested
  reason=<create|update|remove|start|stop|reconfigure> count=<n>`.
  Single choke point covering all five mutation paths (`upsert_mcp_server`,
  `remove_mcp_server`, `start_mcp_server`, `stop_mcp_server`, and the transactional
  commit). Before this, a write to `config.json` that changed the user's MCP endpoint set
  left no trace at all. It is logged *before* the write on purpose:
  `ConfigManager.save_config` swallows the exception and reports its own
  `config_save_failed` ERROR (`pypost/core/config_manager.py:57`), so this line is what
  identifies *which* MCP mutation was lost when the two lines appear adjacently.
- **INFO**: `pypost/ui/mcp_server_controller.py:236` — `mcp_persisted_servers_loaded
  count=<n> enabled_count=<n>`. The only startup evidence that persisted rows were
  restored, and the only way to separate "no endpoints are configured" from "the two-source
  readiness gate never fired" — the exact ambiguity the `start_enabled()` gate creates when
  it emits nothing.
- **INFO**: `pypost/ui/mcp_server_controller.py:211` — `mcp_server_reconfigure_finished
  instance_id=<id> committed=<true|false>`. The registry logs its own rollback; this line
  records the *persistence consequence* — whether the user's edit to a running endpoint
  survives the next restart. Previously the `committed=False` branch returned silently.
- **INFO**: `pypost/ui/presenters/mcp_controls_presenter.py:292` —
  `mcp_servers_dialog_opened server_count=<n>`. Its two sibling dialogs already log their
  open with a count (`mcp_tools_overview_opened`, `mcp_activity_dialog_opened`), and this
  dialog is the single entry point for every `mcp_servers_persist_requested` mutation
  below it, so the mutation events now have a "user opened the manager" anchor.
- **DEBUG**: `pypost/ui/mcp_server_controller.py:133` —
  `mcp_server_activity_unavailable instance_id=<id>`. `mcp_server_activity()` swallows
  `KeyError` and returns `[]`, which is indistinguishable from "this endpoint has done
  nothing yet". DEBUG because it is a UI read, not a fault.

### Deliberately Not Added

Recorded so the absences are decisions, not oversights:

- `McpServerSettingsController.start_enabled()` / `stop_all()` — pure pass-throughs. The
  registry logs `mcp_registry_start_requested` / `mcp_registry_stop_requested` per
  instance, and `main_window_ui_ready` already brackets the gate.
- `McpServerSettingsController._collection_by_id()` — called per MCP request resolution, a
  hot path. A missing collection is already surfaced by the registry's
  `_missing_reference` failure status.
- `McpControlsPresenter.handle_environment_selected()` — `MCPServerManager` logs
  `mcp_server_listening` / `mcp_server_start_failed`, and `_on_mcp_status_changed` logs
  `mcp_server_started` / `mcp_server_stopped`.
- `McpControlsPresenter.refresh_tools()` / `refresh_environment()` — fire on every
  collection and environment edit. The registry logs `mcp_registry_status` only when a
  status actually changes, which is the meaningful event.
- `main_window.py`, `env_presenter.py` — their diffs only *remove* code and delegate.
  `EnvPresenter`'s own `env_selected` / `env_deselected` / `load_environments_*` events are
  untouched.
- `scripts/*.py` — CI gates, not runtime services; see [Scripts](#scripts) below.

### Verbatim-Moved Logs (inventory, unchanged)

Eight event names moved with their code and were re-verified, not rewritten. Each was
diffed against `git show HEAD:<file>`:

- `mcp_manager_source` (DEBUG, `mcp_server_controller.py:53,56`) — moved from
  `pypost.ui.main_window`, where it sat at `HEAD`:92,95 on the same
  `if mcp_manager is not None:` branch. Matches the documented `*_source
  source=injected|new` composition-root convention (`doc/dev/logging.md:47`).
- `mcp_server_started`, `mcp_server_stopped`, `mcp_active_env_changed`,
  `mcp_tools_overview_opened`, `mcp_activity_dialog_opened` (INFO),
  `mcp_servers_dialog_no_controller` (WARNING), `mcp_server_start_failed_ui` (ERROR) —
  moved from `pypost.ui.presenters.env_presenter` (`HEAD`:419, 461, 471, 476, 504, 510,
  520), message strings byte-identical.

**One event in this module is not moved — it is new.** `mcp_registry_source
source=injected|new` (DEBUG, `mcp_server_controller.py:61,64`) has no counterpart at
`HEAD`. The injection seam existed — `MainWindow.__init__` already took an
`mcp_registry: MCPServerRegistry | None` parameter (`HEAD`:57) — but the registry was
built by a bare `self.mcp_registry = mcp_registry or MCPServerRegistry(...)`
(`HEAD`:114) with **no logging at all**. The extraction turned that `or` expression into
an explicit branch in the controller's constructor and, in doing so, brought the
composition-root convention to a seam that previously did not follow it. It is new code
written in this task, not a verbatim move; it is listed here rather than under
[Added Logs](#added-logs) because it arrived with the Step 4 extraction, not from this
step's gap analysis. This step's own additions remain the five statements above.

**The logger name changed for the eight moved events.** That is an observability-visible
consequence of the extraction and was verified explicitly:

- `tests/test_env_presenter.py:288` already re-pinned `mcp_active_env_changed` to
  `pypost.ui.presenters.mcp_controls_presenter` in Step 4.
- `mcp_server_start_failed_ui` is the only ERROR among them. It is deliberately triggered
  by `tests/test_env_presenter.py::test_mcp_start_failed_shows_warning`, which previously
  satisfied only clause **C3** of the `do-testing` caplog contract (behavioural assertions
  on status text and dialog). Because *this* task changed its logger identity, it now also
  satisfies **C1** (an `assertLogs` block pinned to the new logger,
  `tests/test_env_presenter.py:453`). A **C2** rule was also added
  (`tests/expected_log_allowlist.yaml:45-51`), but the contract requires only *one* clause
  and C1 is the clause that carries it — the C2 rule never fires, because `assertLogs`
  suppresses the very propagation the allowlist reads from. See
  [Commands run](#commands-run) for the reproduction and why the rule is still correct to
  keep. `baseline_error_count` was **not** changed (still 72) — no ERROR was added, an
  existing one was registered under its new name.

### Log Structure

- Structured logs: **yes** — `<event_name> key=value ...`, snake_case event first token,
  `%` formatting, per `doc/dev/logging.md`.
- Includes context: **yes** — `reason`, `instance_id`, `count`, `enabled_count`,
  `server_count`, `committed`.
- Log levels used: **INFO** (4 added), **DEBUG** (1 added). No new WARNING/ERROR.
- Booleans rendered as lowercase strings (`committed=true`), per the convention table.
- Suffix conventions reused from the existing catalog: `_requested`
  (cf. `mcp_registry_start_requested`), `_finished`, `_opened`, `_loaded`.

### Sensitive Data

No log added here emits an endpoint id set, host, port, collection id, environment id, tool
name, or variable value. `mcp_persisted_servers_loaded` and `mcp_servers_persist_requested`
emit **counts only**; `mcp_server_reconfigure_finished` and
`mcp_server_activity_unavailable` emit a single opaque `instance_id`, which the registry
already logs at the same level. This matches the "MCP args: log counts only" rule in
`doc/dev/logging.md` and `doc/dev/mcp_secrets_policy.md`. No large data structure
(`AppSettings`, `list[McpServerConfiguration]`, activity entries) is ever formatted into a
message.

## Metrics Implementation

**No metrics were added, and none are needed.** Evidence:

- `MCPServerRegistry._publish_instance_metrics` already calls
  `set_mcp_server_instance_counts({stopped, starting, running, failed})` on every `upsert`
  and every status transition (`pypost/core/mcp_server_registry.py:519+`), which is exactly
  the component-health gauge for the extracted lifecycle. The extraction did not move,
  disable, or reroute that call — `McpServerSettingsController` passes the same `metrics`
  instance into the registry it constructs.
- `McpControlsPresenter.track_active_env_changed` still calls
  `metrics.track_mcp_active_env_changed()` (`mcp_controls_presenter.py:161`), covered by
  `tests/test_env_presenter.py:256-292`.
- `MetricsTrackerProtocol` is a closed protocol with a `NullMetrics` mirror; adding a
  counter means editing `metrics_protocol.py`, `core/qt/metrics.py` and `NullMetrics`,
  none of which are in this task's scope, to publish a number the instance-count gauge
  already conveys.

### Performance / Business / Health Metrics

- **Response time**: N/A — no new request path; MCP tool-call duration is already
  `track_mcp_tool_call_duration`.
- **Throughput**: N/A — the added seams are user-driven config mutations (dialog clicks).
- **Error rate**: unchanged — `mcp_server_start_failed_ui` remains the single UI-level
  failure signal. It is now registered in the CI allowlist under its new logger name,
  though that rule is dormant until the event is captured outside an `assertLogs` block
  (see [Commands run](#commands-run)).
- **Component status**: `set_mcp_server_instance_counts` (registry) — unchanged.

### Scripts

`scripts/verify_ai_task_artifacts.py` and `scripts/audit_baseline_metrics.py` are offline
CI gates invoked by `make verify-ai-tasks` and `make check`, not runtime services. Their
correct observability surface is stderr diagnostics plus exit codes, and both already
provide itemised output — the artifact verifier prints every new / resolved / changed task
separately with a baseline-versus-current summary (`:177-196`), and the metrics auditor
prints every cap violation (`:207-209`). `logging` is not used and would not be read by
CI. `flake8` `T201` is scoped to `pypost/` only, so `print` is the sanctioned channel here.
**No change required.**

## Monitoring Integration

- [x] Prometheus metrics — pre-existing via `set_mcp_server_instance_counts`; no new
      series introduced by this task.
- [ ] Grafana dashboards — none in this repo.
- [ ] Alerting rules — the in-app `AlertManager` covers request failures, not MCP config.
- [x] Log aggregation — stdlib `logging` with the key=value convention consumed by
      `scripts/verify_test_log_guardrails.py` in CI.

## Validation Results

- [x] Logs correctly formatted — event-first snake_case, `key=value`, `%` formatting;
      asserted verbatim by the three new tests below.
- [x] Metrics collected correctly — `tests/test_mcp_server_registry.py` (19 tests) and
      `tests/test_env_presenter.py::test_tracks_mcp_active_env_changed_*` green.
- [x] Logging works in error scenarios — the rolled-back reconfiguration path
      (`committed=false`) and the ERROR start-failure path are both asserted with
      `assertLogs`.
- [x] Large data structures are not logged — asserted negatively: the new startup test
      fails if any endpoint id or port appears in the message.
- [x] Metrics available for monitoring — `scripts/audit_baseline_metrics.py --check`
      exits 0.

### Tests added (all `do-testing` compliant; module `pytestmark` timeouts already present)

In `tests/test_main_window.py::TestMainWindow` (new):

- `test_startup_logs_persisted_mcp_server_counts_without_endpoint_details` — locks
  `mcp_persisted_servers_loaded count=2 enabled_count=1` and asserts that no endpoint id
  or port appears in the message.
- `test_persisted_mcp_mutations_log_their_reason` — locks the ordered sequence
  `reason=start` → `reason=stop` → `reason=remove` with the correct row counts.
- `test_uncommitted_reconfiguration_is_logged_and_not_persisted` — locks
  `committed=false`, the absence of a persist event, and `save_config` not being called.

In `tests/test_env_presenter.py::TestEnvPresenter` (extended):

- `test_mcp_start_failed_shows_warning` — adds caplog clause **C1** pinned to the ERROR's
  new logger name, keeping its existing behavioural assertions.

### Commands run

- `make lint` — clean (exit 0). `flake8` over the in-scope `tests/` files shows a single
  delta versus `HEAD`: `E402` 6 → 8, the existing Step 4 import plus this step's
  `import logging`. `pytestmark` sits above the imports in that module, so every import
  there is `E402`; the new line follows the established pattern.
- Affected modules — `test_main_window`, `test_env_presenter`, `test_mcp_servers_dialog`,
  `test_mcp_server_registry`, `test_main_window_shutdown`,
  `test_verify_test_log_guardrails`, `test_verify_ai_task_artifacts`,
  `test_solid_audit_baseline`: **117 passed**.
- `make test` (full fast suite) — **2218 passed, 22 deselected** (2215 + 3 new).
- `scripts/audit_baseline_metrics.py --check` — exit 0.
- `scripts/verify_ai_task_artifacts.py` (no flag; its verification form) — exit 0.
- `scripts/verify_test_log_guardrails.py` on a captured MCP/UI slice — **exit 0 both with
  and without the new allowlist rule**. The rule is dead configuration today; the
  measurement is below.

No cap, baseline JSON, metrics snapshot or mypy baseline was regenerated. Neither
`Makefile` nor `tests/test_example_fixtures.py` was touched.

#### The C2 allowlist rule is currently dead configuration

The slice was captured with:

```sh
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
    tests/test_env_presenter.py tests/test_main_window.py tests/test_mcp_servers_dialog.py \
    -p no:randomly -o log_cli=false --log-file=slice.log --log-file-level=WARNING
```

Result: 66 passed, and `slice.log` contains exactly **one** ERROR line —
`pypost.ui.presenters.env_presenter: storage_save_failed ...`. `mcp_server_start_failed_ui`
appears **zero** times, even though
`tests/test_env_presenter.py::test_mcp_start_failed_shows_warning` runs in that slice and
its `assertLogs` block passes. Running that single test alone with
`--log-file-level=ERROR` produces a **0-byte** log file. The verifier therefore reports
`ERROR count: 1 (max allowed: 77) / PASS` and exits **0** both against
`tests/expected_log_allowlist.yaml` and against a copy with lines 45-51 deleted.

Cause: the C1 block at `tests/test_env_presenter.py:453` uses `unittest.assertLogs`, and
`unittest/_log.py:_AssertLogsContext.__enter__` sets `logger.propagate = False` for the
duration of the block (restored on exit). The ERROR is delivered to the assertion's own
handler and never reaches the root handler that `--log-file` installs, so the CI verifier
cannot see it. This is independent of the `--log-file` capture defect in
[Notes](#finding--the-ci-error-guardrail-is-vacuous-on-a-full-suite-run-pre-existing):
capture demonstrably works in this slice, since the `storage_save_failed` ERROR from the
same module *is* recorded — it simply is not wrapped in an `assertLogs` block.

**The rule at `tests/expected_log_allowlist.yaml:45-51` is therefore dead configuration —
harmless, and correct to keep.** It is not deleted, because it is exactly right for the
moment the ERROR is captured outside an `assertLogs` block. Verified with a throwaway probe
outside the repository that emits the event on the new logger with no `assertLogs` wrapper:
the captured line makes the verifier exit **1** (`FAIL: 1 unlisted ERROR line(s)`) without
the rule and exit **0** with it. So the rule is live the day the event is logged unguarded
— it is simply not exercised by the current test suite.

The `do-testing` caplog contract for `mcp_server_start_failed_ui` is satisfied by **C1**
(plus its retained **C3** behavioural assertions), not by the allowlist.

## Notes

### Finding — the CI ERROR guardrail is vacuous on a full-suite run (pre-existing)

While validating the moved ERROR path, the CI step at `.github/workflows/test.yml:147`
(`scripts/verify_test_log_guardrails.py pytest.log`) was found to inspect an **empty**
log file on a full-suite run, so it reports `ERROR count: 0` and passes unconditionally.

Reproduction (order-dependent, offline, ~3 s):

```sh
# 1 captured ERROR line (env_presenter: storage_save_failed)
pytest tests/test_env_presenter.py -p no:randomly \
       -o log_cli=false --log-file=a.log --log-file-level=WARNING
# 0 captured lines — same tests, agent module collected first
pytest tests/test_agent_lifecycle_smoke.py tests/test_env_presenter.py -p no:randomly \
       -o log_cli=false --log-file=b.log --log-file-level=WARNING
```

Collecting `tests/test_agent_lifecycle_smoke.py` first silences `--log-file` capture for
the remainder of the session. It is not the `agent_e2e_session` fixture (a single test that
does not use it reproduces the same result) and it is not the module-level
`logging.basicConfig` in `pypost/main.py` (`tests/test_log_level.py`, which imports it,
captures normally). The exact mechanism was not root-caused — it is outside Step 6's scope.

This is **pre-existing and unrelated to this task's diff**: PYPOST-1071 touches no test
configuration, conftest, or agent module. It is recorded here because it is the reason the
already-unlisted `mcp_server_start_failed_ui` ERROR never failed CI, and it is a candidate
Step 7 tech-debt item — an ERROR guardrail that cannot see ERRORs provides no protection
for any of the events catalogued above.

It is a **second, independent** reason the guardrail cannot see this particular ERROR. Even
on a slice where `--log-file` capture works, `assertLogs` suppresses propagation for the one
test that triggers it, so the event reaches the log file zero times — see
[the dead-configuration measurement](#the-c2-allowlist-rule-is-currently-dead-configuration).
Both are worth one Step 7 item each: a guardrail blinded by collection order, and an
allowlist that cannot observe events asserted through `assertLogs`.

### Follow-up for Step 8 — `doc/dev/logging.md` catalog drift

The MCP section of `doc/dev/logging.md:266,274` attributes `mcp_activity_dialog_opened` and
`mcp_tools_overview_opened` to the "env presenter". After this task's extraction their
module is `pypost/ui/presenters/mcp_controls_presenter.py`, and the section has no entries
at all for the controller's persistence events. The catalog is developer documentation
under `doc/dev/`, which is Step 8's artifact, so it is deliberately left for that step
rather than edited here. Rows Step 8 should add or correct:

Module `A` = `ui/mcp_server_controller`, `B` = `ui/presenters/mcp_controls_presenter`.

| Event | Level | Key fields | Module | Note |
| --- | --- | --- | --- | --- |
| `mcp_persisted_servers_loaded` | INFO | `count`, `enabled_count` | `A` | new |
| `mcp_servers_persist_requested` | INFO | `reason`, `count` | `A` | new |
| `mcp_server_reconfigure_finished` | INFO | `instance_id`, `committed` | `A` | new |
| `mcp_server_activity_unavailable` | DEBUG | `instance_id` | `A` | new |
| `mcp_servers_dialog_opened` | INFO | `server_count` | `B` | new |
| `mcp_activity_dialog_opened` | INFO | `entry_count` | `B` | module was wrong |
| `mcp_tools_overview_opened` | INFO | `tool_count` | `B` | module was wrong |
| `mcp_registry_source` | DEBUG | `source` | `A` | new (composition convention) |

### Honest summary

Observability at these seams was **largely, but not entirely, adequate before this step**.
The runtime half was genuinely well covered by the registry and the manager, and nothing
was invented there. The persistence half that the new controller now owns had zero
coverage, which is a real gap that the extraction made visible rather than created — four
INFO lines and one DEBUG line close it. The one thing the extraction *did* change is the
logger identity of eight existing events (a ninth, `mcp_registry_source`, is new code, not
a move), and that was the source of the only contract violation found and fixed here. That
violation is closed by the **C1** `assertLogs` block; the **C2** allowlist rule added
alongside it is dead configuration under the current suite and is documented as such rather
than presented as the fix.
