# Roadmap: PYPOST-1124

## Task Metadata

- **Implementation language**: Markdown — PYPOST-1124 is a discovery/research story whose
  artifacts are documents. The engineering stories this discovery defines target the existing
  PyPost stack: Python 3.11+ with PySide6 (see `doc/dev/architecture.md`, `README.md`).
- **Branch name**: *[recorded by the commit procedure — reference only, do not switch]*

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Recorded the business reason for a discovery-first story under Epic PYPOST-1123
  - [x] Verified the current PyPost baseline against the repository (models, request execution,
    UI structure, collections/environments, MCP/agent integration, daemon)
  - [x] Benchmarked Postman, Insomnia, Bruno, and Hoppscotch WebSocket clients with cited sources
  - [x] Documented user journeys, functional/non-functional requirements, scope, entities,
    scenarios, and Definition of Done without architectural or implementation decisions
  - [x] Added `ai-tasks/PYPOST-1124/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Verified the PyPost baseline that constrains the design against real files
    (layering, one-shot worker, LOC caps, pydantic `extra='ignore'`, masking, MCP, daemon)
  - [x] Evaluated the networking engine: Qt-native `QWebSocket` vs asyncio
    (`websockets`/`aiohttp` with `qasync`, `PySide6.QtAsyncio`, or a dedicated loop thread);
    claims checked against Qt 6 / `websockets` documentation and against the pinned
    PySide6 6.11.1 wheel
  - [x] **Decision D-1: recommend Qt-native `QWebSocket`** behind a Qt-free transport seam,
    with trade-offs, per-option risks, and a reversibility path recorded
  - [x] Resolved the Step 1 tensions: FR-6.5 history (excluded, FU-2 recorded) and FR-6.7
    MCP exposure (in scope as a bounded one-shot probe; persistent sessions excluded, FU-3)
  - [x] Defined the domain model, `Collection.websockets` persistence, and the
    import/export/downgrade compatibility story
  - [x] Defined the PySide6 interaction model: ownership boundaries, session state machine,
    ASCII wireframes, widget identities and hotkeys (satisfies Jira AC (b))
  - [x] Defined stream data handling (dual-bound ring, virtualized rendering, backpressure,
    export), the security and masking model, and the test strategy
  - [x] Produced the implementation breakdown: 12 stories (73 points) for Epic PYPOST-1123
    with scope, acceptance criteria, dependencies, waves, and 11 recorded follow-ups
  - [x] Added `ai-tasks/PYPOST-1124/20-architecture.md`
  - [x] FIX pass after architecture review (2026-08-22): closed 10 review gaps in
    `20-architecture.md` — registered the previously dangling editing-while-connected decision
    as D-13; filled R-1.1 with the measured LOC/headroom of every module the epic grows
    (`request_manager.py` 260/260, `storage.py` 364/380, `mcp_server_impl.py` 312/325) and gave
    WS-2/WS-9 a named module-or-extraction plan plus cap acceptance criteria; fixed the
    ring-ownership contradiction with the A-3.1 rule (controller emits raw frames, presenter
    masks via `build_stream_entry`, `StreamListModel` is the sole ring writer) so WS-7 extends
    instead of rewiring WS-1/WS-4; added the D-14 process-wide `ws_max_concurrent_sessions`
    ceiling (A-12.1, assigned to WS-10); added the FR-5.6 presets/sequences wireframe and
    interaction spec (A-5.8) and tightened WS-6; reconciled the wave count to eight; gave the
    MCP profile fields a single owning story (WS-2); assigned the agent-e2e and identity
    spot-check work to WS-4/WS-5/WS-6; addressed the Portability NFR (A-16 — `QtWebSockets`
    ships in `pyside6-addons`, already locked and license-inventoried, plus OQ-4 for
    platform TLS/proxy); added FR-4/FR-5/NFR traceability tables (A-17)
  - [x] Correction to the two sub-items above: the epic is **eight** waves (wave 0-7), not
    seven, and story points were re-estimated for the scope the fix pass added — WS-2 5 -> 8,
    WS-10 5 -> 8, epic total **73 -> 79 points** across the same 12 stories
  - [x] FIX pass #2 after a second independent review (2026-08-22): closed 5 fixable gaps in
    `20-architecture.md` — added the missing WS-9 -> WS-10 dependency edge (A-13.9 "Depends
    on" and the A-13.13 table), since WS-9 AC 8 consumes the `SessionSlots` counter A-12.1
    assigns to WS-10; verified wave order already keeps WS-10 (wave 5) no later than WS-9
    (wave 6), so no wave renumbering was needed; specified `SessionSlots` cross-thread safety
    in A-12.1 with a `threading.Lock`, matching the existing `McpActivityLog` idiom
    (`pypost/core/mcp_activity_log.py:87-95`) for state shared between the GUI thread and the
    MCP threadpool; relabeled `websocket_active_sessions` as a new WS-10 metric instead of an
    existing one; added the missing A-5.7 widget ids for the A-5.8 preset `Duplicate`/`Save`
    and sequence `New`/`Duplicate`/`Delete`/step `Up`/`Down` controls; and moved the P-2 prose
    sentence out of the fenced wave diagram so it renders as normal paragraph text. Also fixed
    the `[A-10]` -> `[A-11]` link-label typo near line 1200 without changing the anchor
- [x] **STEP 3: Failing Repro Test**
  - [x] **N/A — no behavioral change.** Confirmed against both upstream artifacts: per
    `10-requirements.md` Non-goals/Definition of Done, PYPOST-1124's deliverables are
    Markdown documents only, with "no production code, dependency, or file outside
    `ai-tasks/PYPOST-1124/`" changed. `20-architecture.md` states this explicitly under
    "Mandatory — Failing Repro (next Step 3)": "PYPOST-1124 is a discovery story... no
    production module, dependency, or runtime behavior is touched, so there is no
    observable defect or missing behavior for an automated red test to assert." The
    obligation is delegated, not waived: each of the twelve WS-1..WS-12 implementation
    stories under Epic PYPOST-1123 runs its own Step 3 against the concrete red-test plan
    `20-architecture.md` already specifies per story (see "Mandatory — Failing Repro" /
    P-1..P-2). No test written; no file changed outside `ai-tasks/PYPOST-1124/`.
- [x] **STEP 4: Development**
  - [x] PYPOST-1124's own Development is "create the Jira issues": per `10-requirements.md`
    Definition of Done, this discovery story's obligation is to create the twelve
    engineering stories under Epic PYPOST-1123 from the reviewed breakdown in
    `20-architecture.md` section A-13 (A-13.1..A-13.12). No production code applies to
    PYPOST-1124 itself.
  - [x] Created PYPOST-1127 -- WS-1 WebSocket transport seam and Qt-native session engine (8 SP)
  - [x] Created PYPOST-1128 -- WS-2 Connection profile model, persistence and collection
    interchange (8 SP)
  - [x] Created PYPOST-1129 -- WS-11 WebSocket test harness (5 SP)
  - [x] Created PYPOST-1130 -- WS-3 Bounded message stream, codecs and export (5 SP) --
    depends on WS-1 (PYPOST-1127), WS-2 (PYPOST-1128)
  - [x] Created PYPOST-1131 -- WS-8 TLS and connection-security policy (5 SP) -- depends on
    WS-1 (PYPOST-1127)
  - [x] Created PYPOST-1132 -- WS-4 WebSocket session tab and minimal client (8 SP) --
    depends on WS-1 (PYPOST-1127), WS-2 (PYPOST-1128), WS-3 (PYPOST-1130)
  - [x] Created PYPOST-1133 -- WS-5 Stream inspector (8 SP) -- depends on WS-3 (PYPOST-1130),
    WS-4 (PYPOST-1132)
  - [x] Created PYPOST-1134 -- WS-6 Composer, saved presets and sequence runner (8 SP) --
    depends on WS-3 (PYPOST-1130), WS-4 (PYPOST-1132)
  - [x] Created PYPOST-1135 -- WS-7 Environments, templating and secret masking (5 SP) --
    depends on WS-4 (PYPOST-1132), WS-5 (PYPOST-1133)
  - [x] Created PYPOST-1136 -- WS-10 Settings, session ceiling, metrics and logging (8 SP) --
    depends on WS-1 (PYPOST-1127), WS-3 (PYPOST-1130), WS-4 (PYPOST-1132), WS-5 (PYPOST-1133)
  - [x] Created PYPOST-1137 -- WS-9 Bounded MCP WebSocket probe tool (8 SP) -- depends on
    WS-1 (PYPOST-1127), WS-2 (PYPOST-1128), WS-7 (PYPOST-1135), WS-10 (PYPOST-1136)
  - [x] Created PYPOST-1138 -- WS-12 User and developer documentation (3 SP) -- depends on
    WS-4 (PYPOST-1132), WS-5 (PYPOST-1133), WS-6 (PYPOST-1134), WS-7 (PYPOST-1135),
    WS-8 (PYPOST-1131), WS-9 (PYPOST-1137), WS-10 (PYPOST-1136)
  - [x] Verified 12 issues created, 79 SP total, all parented to PYPOST-1123. Each issue's
    story points came directly from the reviewed architecture (no re-estimation subagent,
    per the run's explicit deviation from `jira-create-issue`). None added to any sprint --
    these are backlog/future engineering work, not part of this discovery sprint. Every
    create was verified with `jira_get_issue` before proceeding to the next.
- [x] **STEP 5: Code Cleanup**
  - [x] **N/A — no production code in this task.** PYPOST-1124's only artifacts are
    `10-requirements.md`, `20-architecture.md`, `00-roadmap.md`, and the twelve Jira issues
    created in Step 4; no `pypost/` source, no Python files, no tests were added or changed.
    There is no linter, formatter, or test suite to run for this task's own changes (Step 3
    was N/A for the same reason). Applied Step 5 in the form that fits: treated the three
    Markdown artifacts as "the code" for cleanup purposes.
  - [x] Re-ran lsr-markdown compliance on all three files independently (not just trusting
    prior reviews): line length (<=100 chars), trailing whitespace, LF line endings, final
    newline, tabs, heading-level skips, fenced-code-block languages (excluding false-positive
    `#`-comment lines inside Python code fences), header blank-line spacing, bullet-style
    consistency, and internal/cross-file anchor resolution using a corrected GitHub-slug
    algorithm (space-to-hyphen is one-for-one, not collapsed — the earlier collapsing check
    produced 12 false "broken anchor" positives on em-dash headings in `20-architecture.md`,
    all of which resolve correctly). Result: zero violations found; no edits were necessary.
  - [x] Confirmed no TODO/FIXME/XXX markers, no duplicate headings (exact text or slug), no
    broken internal references in any of the three files
  - [x] Confirmed only the three expected files exist in `ai-tasks/PYPOST-1124/` and
    `git status --porcelain` shows no tracked file touched and nothing changed outside
    `ai-tasks/PYPOST-1124/` by prior steps
  - [x] Added `ai-tasks/PYPOST-1124/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] **N/A — no runtime/logging/metrics addition by this task.** PYPOST-1124 is a
    discovery story with no production code, dependency, or runtime component (confirmed
    the same way at Steps 3, 4, 5); there is nothing that executes in production for this
    task, so there are no logs or metrics for PYPOST-1124 itself to add.
  - [x] Confirmed the epic's future observability posture was already designed at Step 2 and
    carried into the Step 4 Jira breakdown rather than silently dropped: `20-architecture.md`
    A-8.4 (log events, "what must never be logged"), A-8.2 (masking tiers, metrics-label
    cardinality rule), A-12.1/D-14 (the `ws_max_concurrent_sessions` ceiling and its
    `websocket_active_sessions` gauge), and A-13.10 (the full WS-10 metrics/logging scope
    and acceptance criteria) all exist and are assigned to specific stories, not left
    floating. Verified against the actual Jira issue with `jira_get_issue`: **PYPOST-1136
    (WS-10 — Settings, session ceiling, metrics and logging)** carries the full A-13.10
    scope verbatim in its description (all nine `websocket_*` metrics, the `SessionSlots`
    ceiling, the log-secrecy acceptance criterion, doc updates to
    `doc/prometheus_monitoring.md` and `doc/dev/logging.md`), 8 SP, parented to
    PYPOST-1123.
  - [x] Added `ai-tasks/PYPOST-1124/50-observability.md`, documenting this as a
    cross-reference to Step 2's design rather than inventing new observability
    requirements for a task that has none of its own.
  - [x] **Fix pass (orchestrator, after review FAIL):** corrected a misattribution in
    `50-observability.md` — WS-10 (PYPOST-1136) owns all ten A-8.4 log events verbatim
    (verified against its live Jira description); WS-1 (PYPOST-1127) builds the session
    controller those events describe but carries no logging obligation in its own Jira
    scope. Fixed three passages (Owning stories, Log Structure, Validation Results) that
    had implied WS-1 co-owned or first-emitted the log events.
  - Left `[/]` — the executing agent does not mark its own step `[x]`; that is the
    acceptance-gate owner's action after an independent review passes.
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyzed this task's own output (not the future WS-* stories' debt) across shortcuts,
    doc-structural quality, the Step 3 delegation pattern's coverage, open performance/
    portability questions (OQ-3, OQ-4), and unticketed follow-ups
  - [x] Found real, specific debt: three of six candidate non-goal bullets from
    `10-requirements.md` (four distinct items, since raw TCP/UDP was bundled into the
    Socket.IO bullet) never individually ratified in `20-architecture.md`; A-8.4 log
    *levels* left for WS-10 to assign at implementation time; the Step-3 red-test
    delegation table names WS-1..WS-10 but not WS-11/WS-12; OQ-3 (flood-test throughput
    ceiling) and OQ-4 (cross-platform `wss://` behavior) are still open, not settled,
    facts; the 2187-line `20-architecture.md` is unwieldy as a single file for future
    readers
  - [x] No duplication-drift risk found between `10-requirements.md` and `20-architecture.md`
    (verified: R-4 and the competitive benchmark are cross-referenced, not copied)
  - [x] No pre-existing test failures apply — no test suite was touched or run this run (Step 3
    N/A, Step 5 confirmed no code)
  - [x] Added `ai-tasks/PYPOST-1124/60-tech-debt.md`
  - [x] **Fix pass (orchestrator, after review FAIL):** `60-tech-debt.md` item 1 said "the
    other three items" then listed four bolded items — self-contradictory count in a
    document whose job is precise counting. Reworded to "the other three bullets —
    comprising four distinct items" and corrected this same wording in the sub-item above
    (previously said "two candidate non-goals," inconsistent with the verified "three of
    six bullets / four items" count). No underlying analysis changed — the review
    confirmed all six substantive findings were already correct.
- [x] **STEP 8: Dev Docs**
  - [x] Added `ai-tasks/PYPOST-1124/70-dev-docs.md` detailing summary, artifacts produced, 12-story Epic PYPOST-1123 breakdown, and SAFE TO CLOSE blocker review note
  - [x] Dev Docs review pass (2026-08-22): Verdict: PASS
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1124/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1124/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1124/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1124/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1124/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-1124/70-dev-docs.md`

### COMMIT

- Commit: `docs(websocket): PYPOST-1124 product research and UX discovery for WebSocket support`
