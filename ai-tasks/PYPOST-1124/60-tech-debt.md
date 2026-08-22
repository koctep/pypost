# PYPOST-1124: Technical Debt Analysis

## Scope Note

PYPOST-1124 is a discovery/research story with no production code — Steps 3, 4 and 5 each
independently confirmed that fact (no behavioral change, only Jira issues as "development," no
source to lint or format). This step analyzes **this task's own output**
(`10-requirements.md`, `20-architecture.md`, the roadmap, and the twelve Jira issues Step 4
created) for its own debt — not the future debt of the WS-1..WS-12 implementation stories, which
belongs to their own Step 7 when each is implemented. The analysis below is deliberately specific
rather than a blanket "no debt" — a 2187-line RFC that went through three independent review
rounds on Step 2 alone almost certainly has *something* left arguable, and it does.

## Shortcuts Taken

1. **Three of six "candidate non-goals" from Step 1 were never individually ratified in Step 2.**
   `10-requirements.md` ("Candidate non-goals for the epic," lines 498-508) lists six items and
   states the framing explicitly: "Recorded here as the starting position so that any inclusion
   is a deliberate, visible decision." `20-architecture.md`'s decision register (A-0) and
   follow-up list (A-13.14) explicitly confirm three of the six by name: Socket.IO -> FU-1,
   MQTT/gRPC streaming/SSE-as-a-session -> FU-8, record-and-replay -> FU-9. The other three
   bullets — comprising four distinct items, since the requirements doc bundled raw TCP/UDP
   clients into the Socket.IO bullet — are **raw TCP/UDP clients**, **acting as a WebSocket
   server or mock endpoint**, **load or performance testing of real-time endpoints**, and **team
   synchronization/sharing/cloud storage of sessions**. None of the four is individually named as
   a confirmed exclusion anywhere in
   `20-architecture.md`. They are excluded only by omission from the twelve-story breakdown, not
   by the "deliberate, visible decision" Step 1 itself asked for. This is a real, findable gap
   that survived three independent review rounds unflagged. Severity is low in practice — the
   broader stated constraint ("PyPost stays local-first and single-user, and no server-side
   component is introduced," `10-requirements.md` Assumptions and Constraints) already makes the
   intended answer unambiguous for "acting as a server" and "team sync/cloud storage" — but it is
   a genuine miss against the document's own stated bar, not a manufactured one.
2. **A-8.4 log *levels* are explicitly deferred to implementation time.** `20-architecture.md`
   A-8.4 names all ten `websocket_*` log events precisely (event name, fields, what must never
   appear) but assigns no severity level to any of them. This was independently confirmed while
   writing `50-observability.md`, whose own Log Structure section states plainly: "Log levels:
   not fixed per-event in the architecture doc; assigned by WS-10 at implementation time
   following the syslog-compatible levels already used elsewhere in PyPost." This is a concrete,
   citable instance of a decision pushed to "implementation time" that did not require running
   code to resolve — `doc/dev/logging.md` and the existing event-to-level conventions elsewhere
   in the codebase were available at Step 2 time. Low severity (WS-10's acceptance criteria and
   the existing convention constrain the choice enough that a wrong call is unlikely), but it is
   exactly the kind of arguable-not-settled item the task asked to look for.
3. **WS-2/WS-9 module-cap fallbacks are conditional, not measured.** R-1.1 gives WS-2
   (`request_manager.py`, 0 lines headroom) and WS-9 (`mcp_server_impl.py`, 13 lines headroom) an
   explicit contingency ("if the measured delta does not fit the remaining 13 lines, WS-9 moves
   `_generate_schema`... rather than raising a cap"). This is the one place in the RFC where a
   load-bearing numeric claim (a LOC delta) is conditional rather than settled, because it cannot
   be measured without writing the code. It is handled about as well as a document-only step can
   handle it — both the primary path and the fallback are named and bound by acceptance criteria,
   not left to the future implementer's judgment — so this is noted rather than flagged as a real
   gap.
4. **The 79-point/12-story breakdown itself.** One arithmetic correction happened mid-run (73 ->
   79 points, after the first fix pass added scope to WS-2 and WS-10) and is already recorded
   transparently in the roadmap and in `20-architecture.md`. Beyond that already-caught-and-fixed
   revision, no further compromise was found in the twelve-story split: FR-7.1's
   no-two-stories-own-the-same-behavior boundary is satisfied with named "Out of scope" sections
   per story and an explicit "no story inherits another's identity debt" rule (A-14). This is the
   working-as-intended outcome of the review process, not debt.

## Code Quality Issues

Not applicable in the traditional sense (no code); assessed as structural issues in the
deliverable documents themselves, per the step's own scope.

1. **`20-architecture.md` is 2187 lines in one file.** It passed three independent review rounds
   and Step 5's link/anchor verification with zero errors, so it is internally consistent — but a
   single 2187-line Markdown file is a real navigability cost for a future reader. A future WS-*
   story author has to jump between the A-0 decision register (~line 321), the relevant A-13.x
   story scope (~line 1480-1815), and the A-15 risks/open-questions section (~line 1913) that are
   over a thousand lines apart, with no sub-document split. This is not a defect — nothing in the
   Top-Down workflow requires splitting an RFC — but it is a genuine structural cost worth naming
   for whoever next has to find one specific decision in this file.
2. **No duplication-drift risk found between `10-requirements.md` and `20-architecture.md`.**
   Checked specifically for this step: `20-architecture.md`'s R-4 section states explicitly that
   its four UX inputs are "carried forward from `10-requirements.md`... without re-deriving," and
   the competitive-benchmark data (Postman/Insomnia/Hoppscotch/Bruno feature tables) appears only
   once, in `10-requirements.md`; `20-architecture.md` references it only by pointer (R-4, FU-10,
   R-B, OQ-2). The A-17 traceability tables cite FR/NFR IDs rather than re-stating their text.
   This is a genuine, verified negative finding — no drift risk identified — rather than an
   unchecked assumption.

## Missing Tests

Not applicable directly (no code produced by this task), but the Step 3 delegation pattern —
each future WS-* story owns its own red test — was checked for gaps, since a future story
silently skipping its Step 3 obligation would be real debt this task introduced by omission.

**Finding: the delegation pattern is not airtight.** `20-architecture.md`'s "Mandatory — Failing
Repro (next Step 3)" section (lines 280-317) names a specific red test, file, and assertion for
each of **WS-1 through WS-10** (ten stories) — e.g., WS-1's
`tests/test_websocket_session.py` asserting `Open` is reached against the local echo server. It
does **not** name a Step-3 red test for **WS-11** (the test harness itself) or **WS-12**
(documentation). Every other story in the epic has an RFC-specified red test to point to; these
two do not. This is a real, if narrow, risk: a future engineer picking up WS-11 or WS-12 has
nothing in the RFC to cite and must independently derive a red-test plan (or an N/A justification)
rather than following an explicit instruction the way every sibling story can. For WS-11, an
analogous pattern is plausible (e.g., "the fixture starts, serves, and tears down cleanly across N
sequential test runs with no leaked port/thread," which is already implied by A-13.11 AC 1, just
not written as a Step-3 red test). For WS-12 (documentation only), the reasonable move is the
exact N/A-with-delegation precedent PYPOST-1124's own Step 3 just established for a
documentation-only deliverable — but that precedent is not pointed to by name in
`20-architecture.md`, so a future implementer has to rediscover it. Recorded as a follow-up below
rather than fixed here, since fixing it means editing an already-reviewed-and-accepted
`20-architecture.md`, which is out of this step's scope.

## Performance Concerns

Not applicable to PYPOST-1124's own execution (no code ran, nothing to benchmark), but two of the
RFC's own performance/portability claims are explicitly open questions rather than settled facts,
per `20-architecture.md` A-15:

- **OQ-3 — the real-world throughput ceiling of a GUI-thread socket in PySide6.** This underlies
  R-C ("a high-rate stream degrades UI responsiveness because the socket shares the GUI thread")
  and the entire A-6 stream-handling design (coalesced 33 ms intake, bounded ring, drop counters).
  The RFC's own text says this is "not assumed" — WS-11's flood test is what will establish the
  number, and it becomes a CI-enforced bound only once WS-11 lands. Every quantitative
  responsiveness claim in this RFC (the coalescing interval, the "flat worst-case per session"
  language in the Q&A) is currently a design target, not a measured fact. This is appropriate for
  a discovery-stage RFC — but the task explicitly asked whether this is still open, and it is.
- **OQ-4 — whether the packaged Windows and macOS artifacts behave like the verified Linux one**
  (QtWebSockets presence in the shipped wheel, platform certificate store, system proxy handling).
  CI runs Linux only, so this is explicitly deferred to a manual per-platform release-checklist
  smoke step added by WS-12 (`20-architecture.md` A-16, A-13.12 AC 4), not resolved by automated
  test. This discovery could not close it from a Linux-only research/CI environment — a reasonable
  limit, but genuinely still open, not settled.

Both OQ-3 and OQ-4 already have a named owning story (WS-11, and WS-8/WS-12 respectively) and are
not silently dropped — they do not need a *new* follow-up, since the existing stories are the
correct place to close them.

## Follow-up Tasks

**Pre-existing test failures: none apply.** No test suite was touched or run during this task's
execution — Step 3 was N/A (no behavioral change; PYPOST-1124 has no production code) and Step 5
independently confirmed no code exists that could have tests. There is nothing to record under
the `NON-BLOCKER — pre-existing` convention for this task.

**A-13.14 cross-check.** `20-architecture.md` A-13.14 lists eleven follow-ups (FU-1..FU-11), each
with a one-line reason (Socket.IO client, session-summary history entry, persistent MCP session,
on-message scripting hook, `websocat`/`wscat` export, persisted TLS exceptions,
`permessage-deflate`, MQTT/gRPC/SSE, record-and-replay fixtures, timing comparison, pre-flight
HTTP probe). All eleven are genuine non-goals with a stated reason; none look silently dropped or
contradicted by the Jira breakdown created in Step 4. None needs promotion to a new follow-up
here.

**Candidates for a real follow-up surfaced by this step's own analysis** (not created as Jira
issues here — that is sprint-task-runner's later Phase D, reading this file):

1. **Ratify the unconfirmed candidate non-goals.** Add an explicit line to
   `20-architecture.md`'s decision register or A-13.14 confirming "raw TCP/UDP clients,"
   "acting as a WebSocket server/mock endpoint," "load/performance testing of real-time
   endpoints," and "team sync/sharing/cloud storage of sessions" as out of scope for the epic,
   matching the treatment Socket.IO/MQTT/gRPC/SSE/record-replay already got. Priority: low —
   documentation-completeness gap, not a functional one; the broader local-first/single-user
   constraint already makes the answer unambiguous.
2. **Assign per-event log levels for the ten A-8.4 log events**, either in the architecture doc
   or explicitly in WS-10's (PYPOST-1136) Jira description, rather than leaving "assigned by
   WS-10 at implementation time" as the only record. Priority: low — WS-10's acceptance criteria
   and the existing `doc/dev/logging.md` convention constrain the choice enough that a wrong call
   is unlikely, but it is a real open decision point worth closing before WS-10 starts.
3. **Name an explicit Step-3 red-test pattern (or an explicit N/A-with-delegation note) for WS-11
   and WS-12** in `20-architecture.md`'s "Mandatory — Failing Repro" section, matching the
   treatment already given to WS-1 through WS-10. Priority: medium relative to items 1-2 — this
   is the one gap identified in this step that could concretely let a future story's Step 3
   obligation slip through by omission rather than merely being under-documented.

None of these three block Step 8 (Dev Docs) or the COMMIT step for PYPOST-1124 itself. They are
about tightening the epic's own future execution (WS-1..WS-12), surfaced now because Step 7 exists
to catch exactly this kind of residual ambiguity rather than declaring a three-times-reviewed RFC
debt-free by default.
