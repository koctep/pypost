# PYPOST-1124: Observability Implementation

## Scope Note

PYPOST-1124 is a discovery/research story. Its only artifacts are Markdown documents
(`00-roadmap.md`, `10-requirements.md`, `20-architecture.md`, `40-code-cleanup.md`, this file)
and the twelve Jira issues created in Step 4 (PYPOST-1127..PYPOST-1138). No `pypost/` production
code, no daemon process, no service, and no dependency was added or changed by this task — Steps
3, 4 and 5 each confirmed the same fact independently (no behavior to test, no code to write, no
code to lint/format). There is therefore nothing that executes in production **for this task**,
so PYPOST-1124 itself has no logs and no metrics to add.

That absence is not the end of this step, though. The Top-Down process gate exists to stop an
observability obligation from being silently dropped, and this epic *does* carry one: it was
designed in Step 2 (`20-architecture.md`) and needs to be confirmed as still owned by name in the
Step 4 Jira breakdown, not left as prose that nobody is on the hook for. That confirmation is
this step's real content, reported below as a cross-reference — not a new decision, and not
something invented for this task to have something to write.

## Logging Implementation

### Added Logs

None added by PYPOST-1124 — no code exists for this task to log from.

The epic's future logging was designed in `20-architecture.md` **A-8.4 "What must never be
logged"** and is assigned to the implementation stories that will write the code:

- **Never logged, at any level** (A-8.4, restated as the hard boundary the design sets): message
  payloads (incoming or outgoing), handshake header values, resolved URLs containing query
  strings, close reasons echoed from a peer, preset/sequence payload text, `pong` payloads. This
  mirrors the existing repository rule "Never log chunk body text"
  (`doc/dev/response-streaming-display.md`), so the epic is not inventing a new masking
  philosophy, only extending the existing one to a new transport.
- **NOTICE/INFO-shaped lifecycle events** (A-8.4's `snake_case key=value` catalogue, per
  `doc/dev/logging.md`): `websocket_connect_initiated`, `websocket_connected`,
  `websocket_handshake_failed`, `websocket_closed`, `websocket_reconnect_scheduled`,
  `websocket_reconnect_exhausted`, `websocket_heartbeat_timeout`, `websocket_stream_overflow`,
  `websocket_session_refused`, `websocket_probe_completed` — each carries only identifiers,
  counts, durations, and outcome/category labels; the one field that could leak data
  (`url_masked`) is explicitly required to go through `sanitize_text` first (A-8.4), never the
  raw resolved URL.
- **Owning stories.** All ten A-8.4 log events, including the log-secrecy acceptance test
  (A-13.10 AC 3: "No payload, header value or unmasked URL appears at any log level, verified by
  a test that sends a known secret and asserts its absence from `caplog`"), are owned by
  **WS-10** (PYPOST-1136, A-13.10 — verified verbatim in the live Jira description). WS-1
  (PYPOST-1127, A-13.1) builds the `WebSocketSessionController` these events describe but its own
  Jira scope carries no logging obligation; no A-8.4 event is unassigned or left as a floating
  "someday" note — WS-10 is a backlog Jira issue under Epic PYPOST-1123 today.

### Log Structure

Not applicable to this task's own changes (no code, no log calls). For the epic design this
cross-references:

- Structured logs: yes — `snake_case key=value` per `doc/dev/logging.md`, matching the existing
  repository convention (A-8.4).
- Includes context: yes — every event carries `session_id`, plus event-specific fields
  (`profile_id`, `handshake_ms`, `close_code`, `attempt`, `reason`, etc.), never raw payload.
- Log levels: not fixed per-event in the architecture doc; assigned by WS-10 at implementation
  time following the syslog-compatible levels already used elsewhere in PyPost.

## Metrics Implementation (if applicable)

Not applicable to PYPOST-1124 itself — no code, no metrics registry entries added by this task.

The epic's future metrics were designed in `20-architecture.md` **A-12.1 (D-14, the
concurrent-session ceiling)** and **A-13.10 (the full WS-10 metrics scope)**, and are assigned to
**WS-10 (PYPOST-1136)**, verified directly against the live Jira issue with `jira_get_issue` (see
Validation Results below) rather than trusted from the roadmap alone.

### Performance Metrics

Designed, not yet built — owned by WS-10 (PYPOST-1136):

- **Response time**: `websocket_probe_duration_seconds{outcome}` (histogram) — MCP probe
  duration, A-13.10.
- **Throughput**: `websocket_messages_total{direction,kind}` and
  `websocket_message_bytes_total{direction}` — A-13.10.
- **Error rate**: `websocket_sessions_closed_total{reason}`,
  `websocket_reconnect_attempts_total{outcome}`,
  `websocket_stream_entries_dropped_total{reason}` — A-13.10.

### Business Metrics

- `websocket_sessions_opened_total{outcome}` — sessions attempted/succeeded, by outcome —
  A-13.10, owned by WS-10 (PYPOST-1136).

### System Health Metrics

- **Resource usage**: `websocket_active_sessions` (gauge) — current live-socket occupancy
  against the `ws_max_concurrent_sessions` ceiling (D-14, A-12.1); introduced by WS-10 alongside
  the ceiling counters (A-13.10, PYPOST-1136).
- **Component status**: `websocket_session_start_refused_total{reason="max_concurrent"}` — fires
  when the process-wide ceiling refuses a connect, paired with the `websocket_session_refused`
  log event (A-8.4, A-12.1) — same owner, WS-10 (PYPOST-1136).
- **Existing counter reused, not duplicated**:
  `hidden_value_masks_applied_total{surface="websocket"}` extends the existing masking counter
  (`pypost/core/metrics_registry.py:160`) with a new `surface` label value rather than inventing
  a parallel one (A-8.2) — owned by whichever story
  first calls `build_stream_entry` with masking active (WS-1/WS-7 per the presenter ownership
  rule in A-3.1), tracked as part of the masking acceptance criteria on those stories, not WS-10.

## Monitoring Integration

Not applicable to this task (no code shipped). For the epic:

- [ ] Prometheus metrics — designed (A-13.10), not yet implemented; owned by WS-10 (PYPOST-1136),
  AC 2: "All new metrics scrape with the documented names and label sets and use only fixed
  low-cardinality label values," AC 4: `scripts/audit_baseline_metrics.py --check` must pass
  against a regenerated regression snapshot.
- [ ] Grafana dashboards — not designed in `20-architecture.md`; no story claims this. Out of
  this epic's scope as written (not tracked as a follow-up either — the architecture doc does not
  raise it).
- [ ] Alerting rules — explicitly **out of scope** for WS-10 (A-13.10 "Out of scope: Alerting
  rules").
- [ ] Log aggregation (ELK, Loki, etc.) — not designed; PyPost's existing logging conventions
  (`doc/dev/logging.md`) apply unchanged, no epic-specific aggregation work identified.

## Validation Results

- [x] PYPOST-1124 adds no logs or metrics of its own — confirmed by the same fact already
  established at Steps 3, 4 and 5 (no `pypost/` files touched, `git status --porcelain` shows
  nothing outside `ai-tasks/PYPOST-1124/`).
- [x] `20-architecture.md` A-8 (Security and secret handling) and A-12.1 (D-14, the
  concurrent-session ceiling) were read directly and cited above by section number and quoted
  metric/event names, not summarized from memory.
- [x] `20-architecture.md` A-13.10 (WS-10 story definition) was read directly: it lists all nine
  `websocket_*` metrics, the `SessionSlots` ceiling implementation, and the log-secrecy
  acceptance criterion in one place.
- [x] The Jira issue that owns this work was checked against the live tracker, not assumed from
  the roadmap: `jira_get_issue(PYPOST-1136)` returned a Story ("WS-10 Settings, session ceiling,
  metrics and logging"), 8 story points, parented to Epic PYPOST-1123, with a description that
  reproduces the A-13.10 metrics list, the `SessionSlots`/ceiling scope, the log-secrecy
  acceptance criterion, and the `doc/prometheus_monitoring.md` / `doc/dev/logging.md`
  documentation obligation verbatim — i.e. Step 4's Jira breakdown did not drop or water down
  Step 2's observability design when it turned the architecture doc into tickets.
- [x] The refusal-path observability (`websocket_session_start_refused_total{reason}` +
  `websocket_session_refused` log event, A-12.1) is confirmed to have the same owner, WS-10
  (PYPOST-1136), not left ownerless between the settings story and the transport story.
- Large data structures are not logged: N/A — no logging code exists yet; A-8.4 explicitly
  forbids payload/header logging as a design constraint the future implementer must satisfy, and
  WS-10's AC 3 makes that constraint testable (`caplog` assertion against a known secret).
- Metrics are available for monitoring: N/A — no metrics registry entries exist yet; WS-10 AC 2
  and AC 4 make "correct names, label sets and a passing baseline audit" a merge-blocking
  acceptance criterion for the story that will add them.

## Notes

- This report intentionally departs from the literal `50-observability.md` template's "Added
  Logs" / "Added Metrics" sections, which assume this task shipped runtime code. It instead
  follows the pattern Step 5 (`40-code-cleanup.md`) already established for this task: state the
  `N/A` plainly with the reason, then substitute the content that actually applies — here, a
  verified cross-reference confirming Step 2's observability design survived into Step 4's Jira
  breakdown under a named, estimated, parented story, rather than being silently dropped.
- Nothing in this file is a new architectural or observability decision. Every metric name, log
  event name, and acceptance criterion cited above already exists verbatim in
  `20-architecture.md` (A-8.2, A-8.4, A-12.1, A-13.10) and, independently, in the live Jira issue
  PYPOST-1136. This step only confirms the two agree.
- The owning story for the epic's entire metrics/logging surface is **WS-10 (PYPOST-1136)** —
  all ten A-8.4 log events, the metrics registry entries, the settings surface, and the
  log-secrecy acceptance test. WS-1 (PYPOST-1127) builds the session controller those events
  describe but carries no logging obligation of its own in its live Jira scope. WS-10 is not
  unticketed; it is a backlog issue under Epic PYPOST-1123 (not yet in a sprint), which is the
  expected state for future engineering work discovered by a Step 2 design rather than work due
  for this sprint.
- STEP 6 is left at `[/]` in `00-roadmap.md` — per `td-roadmap`, the executing agent does not
  mark its own step `[x]`; that is the acceptance-gate owner's action after an independent
  review passes.
