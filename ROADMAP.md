# PyPost Remediation Roadmap

Audit of branch `fix/build-and-env-segfault` as it stood at `e83624f7` (base `48a112e6`). 26
defects and 11 architectural weaknesses. 23 of the 26 predate the branch; the files carrying most
findings are byte-identical to `master`.

**Status marks:** `[ ]` not started · `[~]` started, not finished · `[X]` done.

**Current status:** all remediation items are complete.

**Starting baseline, before remediation:** 374 tests passed
(`QT_QPA_PLATFORM=offscreen`, 5.6 s); `ruff check pypost` reported 65 findings and
`ruff check tests` reported 5. These figures are retained as the point from which the work began,
not as completion targets.

**Phases are dependency-ordered.** The structural work in phase 3 followed the visible fixes in
phases 1 and 2.

---

## Phase 1 — Make the advertised features work

Six user-visible features that do not work at all. Every item is a local change; none require
design decisions beyond the two recorded in [Resolved decisions](#resolved-decisions).

### [X] B5 — Segfault when opening the environment manager

Before the fix, the crash reproduced deterministically: Manage → Add environment → three single
clicks in the empty variable-name cell → double-click. Under `wayland` it segfaulted; under
`offscreen` and `minimal` it did not, so CI could not observe it.

Root cause is upstream: a bare `QTableWidget` with any `setCellWidget`, containing no PyPost code
at all, crashes identically on Qt/PySide6 6.11.2. PyPost made it reachable because the Hidden
column used a cell widget where Qt offers a checkable item.

- At audit time, `pypost/ui/dialogs/env_dialog.py:233,238,306` held the three `setCellWidget`
  calls and line 187 held the only `cellWidget` read in the project.
- The planned replacement was a `QTableWidgetItem` carrying `Qt.ItemIsUserCheckable` and
  `setCheckState`.
- This removed `_make_hidden_checkbox` (173-183), `_get_hidden_checkbox` (185-191), the whole
  `_on_hidden_toggled` (245-290) with its `self.sender()` row scan, and the `cb.isChecked()`
  reads in `on_var_changed` (319, 323).
- **Implementation constraint:** `itemChanged` also fires on check-state changes, so
  `on_var_changed` now has an explicit `COL_HIDDEN` branch instead of falling through to the
  "append a new row" path.
- At audit time no test read `cellWidget`; the delivered structural regression now does.
- **Verification:** the regression test in `tests/test_env_dialog.py` is structural — it asserts
  `checkState()` where `cellWidget()` used to be. It does not prove the segfault is gone. That
  requires a display-backed run; headless cannot cover it.
- **Delivered:** `db738b0b` replaced every Hidden-column cell widget with a checkable item and
  added coverage for toggling, masking, renaming and the blank row. The display-backed Wayland
  smoke result is recorded in [Verification status](#verification-status).

### [X] B1 — MCP tool arguments are never substituted

A request exposed as an MCP tool advertises its parameters correctly but receives none of them.

- `pypost/core/function_expression_resolver.py:8` — `_IDENTIFIER_RE` is
  `^[a-zA-Z_][a-zA-Z0-9_]*$`, which admits no dots.
- `{{ mcp.request.city }}` is neither an identifier nor a function signature, so validation
  returns `invalid_syntax`; `template_service.py:87` raises `ValueError`, line 100 catches it and
  returns the content unchanged. `{{ mcp.request['city'] }}` fails the same way.
- Verified: `render_string("https://api/x?q={{ mcp.request.city }}", ctx)` returns the template
  literally, with `ctx = {"mcp": {"request": {"city": "Berlin"}}}`.
- The contradiction sits inside one module: `mcp_server_impl._extract_mcp_variables` (152-191)
  parses the Jinja2 AST **directly, bypassing the validator**, so the generated schema does list
  `city` as required. The schema promises a parameter the renderer then discards.
- Context is built at `pypost/core/mcp_server_impl.py:107`: `{"mcp": {"request": args}}`.
- **Fix:** admit dotted attribute paths and `[...]` subscripts on identifiers generally, not only
  rooted at `mcp` (see [Resolved decisions](#resolved-decisions)).

### [X] B1a — Template validation failure is silent

`template_service.py:100-108` swallows the `ValueError` and returns the raw template. This is why
B1 survived unnoticed. Fix alongside B1: a failed render must be visible to the caller rather than
degrading to a literal.

### [X] B2 — The `MCP` method always times out

- `pypost/core/mcp_client_service.py:102` — `ClientSession(read_stream, write_stream)` is
  constructed without `async with`, so `BaseSession.__aenter__` never starts `_receive_loop` and
  `await session.initialize()` hangs until `MCP_TOTAL_TIMEOUT` (25 s), surfacing as a timeout.
- Fix: `async with ClientSession(...) as session:` and indent 103-114.
- `tests/test_mcp_client_service.py` mocks the transport and stays green.

### [X] B3 — Saving crashes when a blank tab is open

- `pypost/ui/presenters/tabs_presenter.py:564` — `tab.request_data.id` with no `None` guard.
- The guard already exists in the same file at `save_tabs_state:217`
  (`tab.request_data and tab.request_data.id`). Apply the same shape.

### [X] B4 — Expanded collections and open tabs are never persisted

Two defects, not one, and both affect `open_tabs` as well as `expanded_collections`.

- `pypost/core/state_manager.py:20-21,28-29` — getters hand out the live list.
- `pypost/core/state_manager.py:24,32` — setters compare that list against itself, so the guard is
  always true and `save()` never runs.
- Aliasing callers: `collections_presenter.py:335-338,344-347`,
  `tabs_presenter.py:596-599,638-641`.
- `last_environment_id` is unaffected (it is a `str`).
- Verified: `cur = get_expanded_collections(); cur.append("col-1"); set_expanded_collections(cur)`
  persists `[]`.
- Existing tests pass only because they hand in fresh literals
  (`tests/test_settings_persistence.py:94`). Fix with `list(...)` in both getter and setter;
  `test_set_expanded_collections_noop_skips_save` (116) still holds.

### [X] R1 — A post-script error hides the response *(branch regression, `2e480e69`)*

- `pypost/core/worker.py:107-114` — an early `return` after `self.error.emit(...)`, so `finished`
  never fires and a perfectly good response is never displayed.
- Fix in the **worker**, not the service: `request_service.py:334-348` deliberately sets
  `execution_error` with category `SCRIPT` alongside a live `response`, and
  `tests/test_request_service.py:223` asserts exactly that. Narrow the early-return to
  "category is not `SCRIPT`". `tests/test_worker.py:60-92` uses `NETWORK` and stays green.
- **Second half, not optional:** `_on_script_output` (`tabs_presenter.py:487-491`) only logs, and
  `response_view` has no surface for an error — it holds `status_label`, `time_label`,
  `size_label` and the body, nothing else. Without a UI surface the response appears and the
  broken script stays invisible. Add a non-modal label in the status row next to `size_label`
  (see [Resolved decisions](#resolved-decisions)); a modal would cover the response just returned.

---

## Phase 2 — Make lifecycles honest

Races and shutdown behaviour. Nothing here is user-visible as a feature, but all of it produces
hangs, stale servers and lost errors.

### [X] R2 — Quitting hangs for the length of an in-flight request *(branch, `e83624f7`)*

`pypost/ui/presenters/tabs_presenter.py:227-231` — `worker.wait()` with no timeout. Use
`worker.wait(3000)`.

### [X] R3 — Worker lifetime hangs off a shadowed signal *(branch, `e83624f7`/`aa8d2fab`)*

- `pypost/core/worker.py:17` — `finished = Signal(ResponseData)` shadows `QThread.finished()`.
- Connect sites: `tabs_presenter.py:182-183` (`tab.deleteLater`), `409`, `424`, `426`.
- Rename to `request_finished`; hang `deleteLater` and `_workers.discard` off the real
  `QThread.finished` instead, so cleanup runs when the thread actually ends.
- Tests to update: `tests/test_tabs_presenter.py:109-110`, `tests/test_worker.py:47,67`.

### [X] C1 — Deadlock in the metrics server

`pypost/core/metrics.py:22` — `server_lock = threading.Lock()`, non-reentrant. `start_server:239`
holds it and calls `stop_server:272`, which takes the same lock. Triggers whenever `start_server`
runs against a live server. `restart_server` (280) currently escapes it only because it stops
before starting. Use `RLock`.

### [X] C2 — Race on `server_instance` in both servers

`pypost/core/metrics.py:263` and `pypost/core/mcp_server.py:87` assign the uvicorn instance
**inside the worker thread**, after `thread.start()`. `stop_server` can read `None`, never set
`should_exit`, fall out on the 2 s join timeout and leave the server running. Build the
`uvicorn.Config`/`Server` in the calling thread before starting the thread. Same fix in both.

### [X] C1+C2 follow-up — one ASGI server host

`metrics.py` and `mcp_server.py` carry near-identical thread/uvicorn/SSE plumbing with divergent
bugs. Extract a single `AsgiServerHost` once both fixes are in, so the next fix lands once.

### [X] D — Retry exhaustion destroys the real error

`pypost/core/request_service.py:168` — `last_error.detail = f"retries_attempted: {attempt}"`
overwrites the actual cause. Append instead of replacing; `tests/test_retry.py:136` uses
`assertIn` and stays green.

### [X] D — Streaming corrupts multi-byte characters

`pypost/core/http_client.py:213` — `chunk.decode("utf-8", errors="replace")` per chunk, so any
multi-byte character straddling a chunk boundary becomes replacement characters. Use
`codecs.getincrementaldecoder("utf-8")` across the loop.

---

## Phase 3 — Redraw the boundaries

Structural work. Eight of the defects above grow from three decisions; fixing the defects without
these keeps the same class of bug arriving.

### [X] A1 — Settings have no single owner

Two independent `load_config()` calls produce two `AppSettings` objects (`main.py:26` and
`StateManager.__init__`), verified distinct at runtime with diverging `revision` counters. Three
writers exist. Give settings one owner and route every read and write through it.

### [X] A2 — No copy discipline at the core/UI boundary

`find_request` hands back the live domain object; a UI-side mutation was observed landing in the
collection unsaved. Decide where copies are taken, apply it at the boundaries, and record the rule
in a `CLAUDE.md` so it survives.

### [X] A3+A8 — `TabsPresenter` owns business logic

651 lines covering execution, persistence, save flows and worker lifetime, while `RequestService`
takes four UI callbacks. Extract `RequestExecution` and `RequestStore`.

### [X] A6+A7 — Error policy is tangled with rendering

Split policy from presentation and add `ErrorCategory.CANCELLED`, so cancellation stops being
detected by substring-matching `"cancelled"` against `error.detail`
(`tabs_presenter.py:461-470`).

### [X] A10 — MCP server ownership

`MCPServerManager.update_tools` (`mcp_server.py:74`) has zero callers — the tool list silently
goes stale. Decide who owns the server's lifecycle and who refreshes its tools.

### [X] A9 — Durable history

History writes are best-effort and swallowed (`request_service.py:381-384`).

---

## Phase 4 — Guardrails

### [X] E1+E2 — Metrics server binds `0.0.0.0` by default

`pypost/models/settings.py:21` — `metrics_host: str = "0.0.0.0"`. Default to loopback. Drop the
URL label from metrics while here: it is unbounded-cardinality.

### [X] E7 — Lint is not enforced

Add `ruff` to `.github/workflows/test.yml`. Current debt: 65 findings in `pypost` (50 auto-fixable),
5 in `tests` (4 auto-fixable).

### [X] E3/D5/D6/D7 sweep

Wider than recorded here: the audit's D1 and D3 each had a half left over after phase 2, and
both are in. Landed as one commit per defect --

- D5 a blank post-script rewrote the whole environment
- D6 `RequestService` had no template service to render with on two of three paths
- D7 the advertised MCP metrics resource could not be read at all (two defects, either fatal)
- E3 the alert webhook blocked the request thread; measured at 2.00s, now 0.00s
- D1 retried attempts concatenated their response bodies
- D3 mid-stream failures escaped as raw `requests` exceptions and were never retried

### [X] Write up the Qt bug

`doc/qt-cell-widget-segfault.md` holds the ~30 line reproducer, the platform matrix, the
variations that ruled out a PySide ownership problem, and the workaround. In the final comparison,
the cell-widget reproducer crashes under wayland and survives under `offscreen` and `minimal`;
the checkable-item variant survives under wayland.

Not filed upstream -- the user asked for the write-up only. `xcb` and a non-WSL compositor remain
untested and should be checked before reporting.

### [X] Decide what CI can honestly cover

The starting 374 green tests coexisted with five blockers and a segfault. CI runs `offscreen`,
where B5 cannot reproduce under any amount of coverage. The guardrail is therefore defined
explicitly:

- The required PR gate is Ruff plus the complete pytest suite on CPython 3.11 and 3.13 under
  `QT_QPA_PLATFORM=offscreen`, with the existing 50% line-coverage floor.
- Headless Qt tests cover widget construction and application flows that do not depend on a real
  compositor. This now includes B3's save-with-blank-tab path.
- B5 is covered in CI only by a structural invariant: the Hidden column must use checkable items
  and no cell widgets. CI does **not** claim to cover native Wayland/X11 input dispatch, window
  manager behaviour or platform-plugin crashes.
- The B5 click sequence remains a release smoke check on a real Wayland display. An `xcb` and a
  non-WSL Wayland run are desirable before filing the Qt issue, but are not release gates.
- `pytest-timeout` fails an individual test after 60 seconds and pytest's faulthandler prints
  stacks after 45 seconds. The CI test job has a separate 15-minute ceiling so a session-level or
  native-code hang cannot consume the runner's multi-hour default.

---

## Resolved decisions

- **B1 scope** — dotted paths are admitted generally, not only when rooted at `mcp`. The validator
  exists to bar calls to arbitrary functions, not to bar navigation through the context; a
  narrow `mcp`-only exception would leave the same hole open for any other nested dict.
- **R1 surface** — the post-script error is shown in a non-modal label in the response status row,
  not a dialog.

## Verification status

Reproduced and confirmed by running code: B1, B2, B3, B4, B5, R1, R2, C1, C2, and the branch
attribution. The final headless verification passes 486 tests and 9 subtests in about 6.3 seconds;
`ruff check pypost tests` is clean. The phase 3 architectural items and the phase 4 sweep have
targeted regression tests but were not re-audited independently after implementation.

B5 also passed the original Add environment → three clicks → double-click sequence against the
real WSLg `wayland` platform plugin. Its structural CI regression remains necessarily weaker than
that display smoke check: `offscreen` cannot prove the absence of a platform-plugin crash.
