# PYPOST-1207: Technical Debt Analysis

ATTACH-2 capability — cooperative AF_UNIX attach host in interactive
desktop + sidecar `--attach` client, duck-typed `UiDriveSession`, spawn
default preserved, UI tools still off product MCP.

**Verdict:** No blockers for closing PYPOST-1207 capability. Fuller
verification remains on
[PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208). Mypy
baseline drift is out of scope (Step 5). **Do not create Jira issues in
this step** (Phase D / orchestrator). Unticketed follow-ups are listed
without browse links.

## Shortcuts Taken

- **AF_UNIX + NDJSON wire** — Architecture allowed `QLocalServer` /
  `QLocalSocket` or AF_UNIX; shipped plain `socket.AF_UNIX` with
  newline-delimited JSON (handshake / detach / four `ui_*` ops). Keeps
  the agent package free of Qt networking types on the sidecar attach
  client path.
- **Single cohesive `attach_ipc.py` (~494 LOC)** — Host, client,
  framing, and GUI marshal live in one module rather than a package
  split. Intentional cohesion for ATTACH-2; do not treat size alone as
  a split mandate.
- **Handshake version field is advisory** — Client sends
  `ATTACH_PROTOCOL_VERSION`; host replies with its version and `ok`
  without rejecting a mismatched client version. Fine while v1 is the
  only revision; negotiation is incomplete.
- **Always-on host in interactive `main()`** — Composition root always
  starts `AgentUiAttachHost` after `show()`; no CLI/env opt-out. Matches
  ATTACH-1 “host runs with desktop” product meaning; operators who do
  not want a socket must not run interactive desktop (or override the
  endpoint away from clients).
- **Stale socket unlink on `start()`** — If the AF_UNIX path exists, the
  host unlinks it before bind. Recovers from crashed peers; can steal
  an endpoint if two desktops share the same path.
- **Hardcoded IPC / GUI timeouts** — Connect 2.0s, accept poll 0.5s,
  GUI action wait 30.0s, accept-thread join 2.0s. Not configurable via
  CLI/env (spawn `--ready-timeout` is unrelated).
- **Thin `MainWindowUiDrive`** — Duplicates the four `ui_*` wrappers
  already on `AgentAppSession` rather than extracting a shared helper.
  Keeps spawn lifecycle free of attach imports; small duplication.

## Code Quality Issues

- **Byte-at-a-time NDJSON framing**
  (`attach_ipc._recv_line` / `recv(1)`): Correct and simple for short
  control messages; not buffered. Acceptable for local UI IPC.
- **No protocol-version reject**
  (`AgentUiAttachHost._handle_request` handshake): Host accepts any
  handshake with `op=handshake`; mismatched future clients would bind
  until a later op fails.
- **Late GUI job after timeout** (`_run_on_gui`): If `done.wait(30)`
  times out, the queued GUI callable may still run; client already got
  a timeout error. Low practical risk for agent-paced tools.
- **Multi-client accept** (`listen(5)` + per-peer threads): Concurrent
  attach clients can interleave `ui_*` on one live window. No
  single-client policy. Local trust assumes operator control.
- **Duplicate `ui_*` wrappers** (`ui_drive.MainWindowUiDrive` vs
  `lifecycle.AgentAppSession`): Same four methods calling `ui_actions`;
  protocol keeps duck typing. Cosmetic DRY only.
- **Agent package outside mypy baseline** (`pypost/agent/*`):
  Pre-existing project gate; attach modules not in baseline paths.
  **Out of scope** for this ticket.

No naming or layering deviations that break the architecture diagram
(sidecar → client → host → GUI thread → `ui_actions`).

## Missing Tests

**Timeout markers: no BLOCKER.** `tests/test_agent_ui_attach.py`
declares module `pytestmark = pytest.mark.timeout(30)`.

| Scenario | Status |
| -------- | ------ |
| CLI accepts `--attach` | Covered |
| Attach does not call `AgentAppSession.start` | Covered |
| Unbound attach → nonzero fail, no silent spawn | Covered |
| Host + client `ui_click` round-trip | Covered |
| Detach leaves host listening / rebind | Covered |
| Spawn / packaging regression | Covered (existing suite) |
| Attach `ui_fill` / `ui_select` / `ui_send_key` | ATTACH-3 |
| Host exit → sidecar unbound | ATTACH-3 |
| Sidecar exit → host still listening | ATTACH-3 |
| Protocol version / endpoint override matrix | ATTACH-3 |
| Concurrent clients / stale-socket races | ATTACH-3 |
| Manual / CI gap documentation | ATTACH-3 |

Fuller attach matrix and any non-automatable manual checks belong to
[PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208)
(ATTACH-3), not new debt on this story.

## Performance Concerns

None material for v1 local attach:

- Control-plane messages are small; `recv(1)` cost is negligible vs Qt
  GUI work.
- GUI marshal waits up to 30s on the client IPC thread (expected for
  modal/slow UI); does not block the desktop event loop beyond the
  queued action itself.
- Per-client daemon threads are fine for occasional operator attach,
  not a high-QPS server.

## Follow-up Tasks

### Blockers

None.

### Non-blockers (already ticketed — do not duplicate)

- Fuller attach verification / CI vs manual (ATTACH-3) —
  [PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208)
- Streamable HTTP agent-UI MCP (sibling) —
  [PYPOST-990](https://pypost.atlassian.net/browse/PYPOST-990)
- Spawn-session `call_tool` tests (sibling) —
  [PYPOST-992](https://pypost.atlassian.net/browse/PYPOST-992)
- Seed/collection injection for spawn (sibling) —
  [PYPOST-993](https://pypost.atlassian.net/browse/PYPOST-993)

### Non-blockers (accepted residual — no new ticket)

- Cohesive ~494 LOC `attach_ipc.py` — accepted by design
- Always-on interactive attach host — accepted; matches ATTACH-1
- Stale path unlink on host start — accepted for v1 local trust
- Byte-at-a-time framing — low residual; control plane only
- `MainWindowUiDrive` vs session `ui_*` — low residual; avoid
  lifecycle↔attach coupling
- Mypy baseline drift outside attach — out of scope; do not expand
  1207

### Unticketed new debt (Phase D may create)

1. **Enforce attach protocol version on handshake**
   - Priority: Low
   - Reject (or require exact) `ATTACH_PROTOCOL_VERSION` from the client
     before returning `ok`, so future wire revisions fail fast unbound
     instead of binding then mis-dispatching.
   - Files: `pypost/agent/attach_ipc.py`, optionally a PYPOST-1208 case
   - Jira: [PYPOST-1218](https://pypost.atlassian.net/browse/PYPOST-1218)

### Explicitly not follow-ups of this ATTACH-2 story

- [PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208) —
  owns remaining test matrix (do not reopen as Debt)
- [PYPOST-1206](https://pypost.atlassian.net/browse/PYPOST-1206) —
  ATTACH-1 docs Done; capability note refined on this story
- Product MCP UI tools — forbidden; packaging gates unchanged
- Splitting `attach_ipc.py` for LOC alone — cohesive; no crisis

## Deviations from Architecture

None material.

- Cooperative local IPC host + sidecar → AF_UNIX host +
  `AttachClientSession` — Match
- Duck-typed `UiDriveSession` → protocol + spawn/attach DI — Match
- Spawn default preserved → `--attach` opt-in — Match
- UI tools off product MCP → packaging gates unchanged — Match
- Composition-root host start → lazy import around `app.exec()` —
  Match
- `QLocal*` or AF_UNIX → AF_UNIX chosen — Allowed
- Fuller tests on ATTACH-3 → capability proofs only here — Match

User `doc/` updates: N/A for Step 7 (capability notes already refined in
Step 4; Step 8 owns further `doc/dev/` if needed).
