# PYPOST-1208: Technical Debt Analysis

ATTACH-3 verification — expanded automated attach proofs under
`make test` norms plus proven-vs-manual doc agreement. No attach
capability rewrite; production IPC remains as shipped by PYPOST-1207.

**Verdict:** No blockers for closing PYPOST-1208. Residual matrix rows
that stay manual are documented and either already ticketed
(protocol-version enforce) or accepted residual (concurrent /
stale-socket). **Do not create Jira issues in this step** (Phase D /
orchestrator). Unticketed follow-ups, if any, are listed without browse
links.

## Shortcuts Taken

- **Verification-only surface** — Residual rows were proven with
  host+client / CLI tests and doc tables; `attach_ipc` / sidecar wiring
  were not redesigned. Matches ATTACH-3 non-goals.
- **Host exit via `AgentUiAttachHost.stop()`** — Product host-exit for
  CI is modeled as host stop (unlink + close peers), not
  `QApplication.exit()` / `quit()`, which would tear down the shared
  pytest-qt loop. Documented in proven list and architecture.
- **Abrupt sidecar-exit via private `_sock`** —
  `test_attach_sidecar_exit_leaves_host_listening` closes
  `AttachClientSession._sock` without a `detach` op to simulate
  peer-gone. Intentional probe; no public “hard close” API added.
- **Host-stop race window** —
  `test_attach_host_stop_unbinds_client` uses a short `time.sleep(0.2)`
  after connect so `host.stop()` can run before the next `ui_*`. Bounded
  and gated by events; not a full synchronisation primitive.
- **Endpoint proof without live MCP serve** —
  `test_attach_endpoint_override_env_and_cli` asserts env /
  `default_attach_endpoint()` and that `--attach-endpoint` appears in
  `--help`. Does not drive a full stdio MCP session with an overridden
  argv endpoint (architecture: feasible without full serve).
- **Manual residual rows left manual** — Protocol-version reject,
  concurrent interleaved `ui_*`, and stale multi-desktop socket steal
  stay out of the fast suite; documented under Proven vs manual in
  `doc/dev/agent_ui_actions_mcp.md`.

## Code Quality Issues

- **Repeated host+client worker boilerplate** in
  `tests/test_agent_ui_attach.py` (catalog / lifecycle proofs share
  thread + `_pump_until` + box dict). Clear and local; extracting a
  helper is optional polish, not required for ATTACH-3.
- **Private `_sock` touch in sidecar-exit proof** — Couples the test to
  `AttachClientSession` internals. Acceptable for abrupt-close
  simulation; a public test/close hook would be nicer later.
- **Fixed sleep in host-stop proof** — Prefer an explicit host-stopped
  signal if flakiness appears; current suite is green under module
  timeout 30.
- **Agent package outside mypy baseline** (`pypost/agent/*`, attach
  tests): Pre-existing project gate; Step 5 noted out-of-scope baseline
  drift. **Out of scope** for this ticket.

No production layering deviations from the verification architecture
(suite → host/client → GUI / CLI; packaging gates unchanged).

## Missing Tests

**Timeout markers: no BLOCKER.** `tests/test_agent_ui_attach.py`
declares module `pytestmark = pytest.mark.timeout(30)` (all eleven
attach tests covered).

| Scenario | Status |
| -------- | ------ |
| CLI `--attach` / no silent spawn / unbound fail | Covered (ATTACH-2 baseline) |
| Host+client `ui_click` / detach-rebind | Covered (ATTACH-2 baseline) |
| Host+client `ui_fill` / `ui_select` / `ui_send_key` | Covered (ATTACH-3) |
| Host exit → client unbound (`host.stop()`) | Covered (ATTACH-3) |
| Sidecar exit → host still listening (abrupt close) | Covered (ATTACH-3) |
| Endpoint override (env / default / CLI help) | Covered (ATTACH-3) |
| UI tools off product MCP / spawn continuity | Covered (sibling suites) |
| Protocol-version reject on mismatch | Manual; owned by PYPOST-1218 |
| Concurrent interleaved `ui_*` / multi-client | Manual / accepted residual |
| Stale multi-desktop socket steal | Manual / accepted residual |

Docs and tests agree via the Proven vs manual table in
`doc/dev/agent_ui_actions_mcp.md`.

## Performance Concerns

None material for this verification story:

- New proofs reuse the same local AF_UNIX + GUI pump pattern as ATTACH-2;
  wall time stays within the module 30s timeout.
- No production hot-path change; no new metrics or logging surface
  (Step 6 N/A).

## Follow-up Tasks

### Blockers

None.

### Non-blockers (already ticketed — do not duplicate)

- Enforce attach protocol version on handshake —
  [PYPOST-1218](https://pypost.atlassian.net/browse/PYPOST-1218)
  (reject or require exact `ATTACH_PROTOCOL_VERSION` before `ok`;
  optionally add a case once enforcement lands). **Do not open a second
  Debt issue for FR8 / advisory handshake.**

Sibling / epic context (not new debt from this story):

- Streamable HTTP agent-UI MCP —
  [PYPOST-990](https://pypost.atlassian.net/browse/PYPOST-990)
- Spawn-session `call_tool` tests —
  [PYPOST-992](https://pypost.atlassian.net/browse/PYPOST-992)
- Seed/collection injection for spawn —
  [PYPOST-993](https://pypost.atlassian.net/browse/PYPOST-993)
- Parent epic —
  [PYPOST-991](https://pypost.atlassian.net/browse/PYPOST-991)

### Non-blockers (accepted residual — no new ticket)

- **Concurrent interleaved `ui_*` / multi-client** — Documented manual
  check; full race stress is outside fast-suite norms (FR9 / NFR-2).
  Local trust assumes operator control (same as PYPOST-1207).
- **Stale multi-desktop socket steal** — Documented manual check;
  `host.start()` unlink-before-bind remains accepted v1 local-trust
  behavior from ATTACH-2.
- Host-exit CI approximation via `host.stop()` (not full process exit) —
  intentional pytest-qt constraint; product meaning documented.
- Abrupt-close via `_sock` and host-stop `sleep(0.2)` — low test-harness
  residual; revisit only if flaky.
- Endpoint proof without full `--attach-endpoint` live MCP serve —
  largest feasible subset; help + env cover operator-visible override.
- Repeated IPC worker boilerplate / mypy baseline drift outside attach —
  polish / out of scope; do not expand 1208.

### Unticketed new debt (Phase D may create)

None. Protocol-version enforce is already PYPOST-1218. Concurrent and
stale-socket rows are accepted residual with written manual checks — do
not invent Debt tickets that restate documented ATTACH-3 manual gaps.

### Explicitly not follow-ups of this ATTACH-3 story

- Re-implementing attach capability (PYPOST-1207 Done)
- Enforcing protocol-version reject here (PYPOST-1218)
- Primary ATTACH-1 trust/lifecycle rewrite (PYPOST-1206 Done)
- Product MCP UI tools / packaging redesign
- Splitting `attach_ipc.py` for LOC alone

## Deviations from Architecture

None material.

- Expand feasible residual automated proofs → six new green proofs in
  `test_agent_ui_attach.py` — Match
- Host exit via `host.stop()` — Match
- Sidecar exit / peer-gone rebind — Match (abrupt close)
- Endpoint override as feasible without full MCP serve — Match
- Protocol-version reject → manual + PYPOST-1218 — Match
- Concurrent / stale races → manual residual — Match
- Docs proven-vs-manual table — Match
- No attach rewrite / no packaging change — Match

User `doc/` updates: N/A for Step 7 (proven-vs-manual alignment already
landed in Step 4; Step 8 owns further `doc/dev/` if needed).
