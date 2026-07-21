# PYPOST-833: Agent app lifecycle — launch, ready, shutdown

## Goals

AI agents and automated harnesses need a trustworthy way to run PyPost end-to-end against
the real desktop UI. Today there is no agreed, agent-suitable lifecycle: start the app,
know when the UI is safe to drive, and stop without leaving orphan processes or locked
resources. Without that foundation, later agent UI work (actions, snapshots, waits, golden
flows under epic [PYPOST-832](https://pypost.atlassian.net/browse/PYPOST-832)) cannot be
reliable in local or CI environments.

This task establishes the business contract for application lifecycle only: **launch →
ready → shutdown**, with a minimal smoke check that proves the contract holds.

## Programming Language

Python (`.cursor/lsr/do-python.md`)

## User Stories

- As an **AI agent** (or test harness acting for one), I want a documented, repeatable way
  to start PyPost so I can drive product flows without ad-hoc, undocumented startup steps.
- As an **AI agent**, I want a clear ready condition before I send UI actions so I do not
  act while the application is still starting or incomplete.
- As an **AI agent**, I want a clean shutdown path so repeated runs do not leave orphan
  processes, hung sessions, or locked resources that block the next run.
- As a **maintainer**, I want a minimal automated smoke check (launch → ready → shutdown)
  so regressions in lifecycle reliability are caught early.
- As a **CI / headless runner**, I want lifecycle to work where a normal interactive display
  is unavailable (offscreen / headless-capable operation) so agent e2e can run in automated
  environments.

## Definition of Done

- There is a documented entry point suitable for agent or harness use to launch PyPost
  (project-supported CLI, `make`, or equivalent harness path — not a one-off undocumented
  shell recipe).
- Launch supports environments without a visible interactive display where that is needed
  for agent/CI use (offscreen / headless-capable as applicable).
- An explicit ready signal or pollable ready condition exists; agents must be able to wait
  until it is true before performing UI actions.
- Shutdown ends the run cleanly: no orphan PyPost (or child) processes and no leftover
  locks that prevent a subsequent launch.
- A minimal smoke test covers launch → ready → shutdown and is runnable via the project’s
  standard test/quality workflow.
- Scope stays on lifecycle; UI actions, snapshots, waits, identity conventions, and the
  golden product flow remain sibling stories under PYPOST-832.

## Task Description

**Problem:** Agents cannot reliably own the full PyPost process lifecycle. Startup may be
unclear or unsuitable for automation; there is no shared “UI is ready” contract; shutdown
may leave orphans or locked resources. That blocks trustworthy agent-driven e2e UI testing.

**Business need:** A small, durable lifecycle contract so any agent or harness can start
PyPost, wait until interaction is allowed, then stop cleanly — including in display-less
CI — before sibling stories add actions and observation.

### In Scope

- Documented launch entry point for agent/harness use.
- Ready condition that is explicit or pollable before UI actions are allowed.
- Clean shutdown with no orphans or blocking leftover locks.
- Support for offscreen / headless-capable launch where agent or CI use requires it.
- Minimal smoke coverage of launch → ready → shutdown.
- Documentation of that entry point and lifecycle expectations for agents/maintainers
  (detail may land with this story or the epic docs story; the contract must be stated).

### Out of Scope

- UI action primitives (click, type, select, hotkeys) — PYPOST-836.
- Structured UI snapshots — PYPOST-835.
- Stable widget identity conventions — PYPOST-834.
- Settle/wait helpers for post-action UI conditions — PYPOST-837.
- Golden end-to-end product scenario — PYPOST-838.
- Full agent-e2e docs/`make` packaging beyond what this lifecycle story needs —
  PYPOST-839 (except the minimal documented launch/ready/shutdown contract).
- Existing MCP HTTP request tools (already shipped; not part of this epic’s UI focus).
- Redesigning normal interactive desktop launch for human users beyond what agent
  lifecycle requires.

## Functional Requirements

- FR1: An agent or harness can launch PyPost through a documented, project-supported entry
  point suitable for automation.
- FR2: Launch must be usable in environments without a visible interactive display when
  required for agent or CI runs.
- FR3: The system exposes an explicit ready signal or a pollable ready condition that
  becomes true only when the UI is ready for agent actions.
- FR4: Agents must not be expected to perform UI actions before the ready condition is
  satisfied.
- FR5: An agent or harness can request shutdown and the application session ends fully.
- FR6: After shutdown, no orphan processes from that session remain, and no leftover locks
  block a subsequent launch.
- FR7: A minimal automated smoke check verifies launch → ready → shutdown in sequence.

## Non-functional Requirements

- **Reliability:** Repeated launch → ready → shutdown cycles must succeed without manual
  cleanup between runs.
- **Observability of readiness:** Ready vs not-ready must be distinguishable without guesswork
  or fixed blind waits as the only strategy.
- **CI suitability:** Lifecycle must work in automated, display-less environments used by
  the project’s quality gates where agent e2e will run.
- **Clarity:** Failure to become ready or to shut down cleanly must be diagnosable (clear
  failure, not a silent hang with orphans left behind).
- **Minimalism:** This story delivers the smallest lifecycle contract needed to unblock the
  epic; it does not expand into full agent action tooling.

## Constraints and Assumptions

- Programming language: Python.
- Parent epic: [PYPOST-832](https://pypost.atlassian.net/browse/PYPOST-832) (E2E Agent UI
  Testing). Sibling stories own actions, identity, snapshots, waits, golden flow, and
  broader docs/`make` packaging.
- “Agent” includes an AI agent or an automated harness acting on behalf of one.
- “Ready” means the application UI is in a state where subsequent agent UI work (from
  sibling stories) is allowed to begin — not that every product feature has finished all
  background work forever.
- “Clean shutdown” means the launched session and its processes are gone and resources that
  would block relaunch are released.
- Offscreen / headless-capable operation is a business requirement for agent/CI use, not a
  mandate to change the default interactive experience for desktop users.
- Step 1 review is treated as pre-approved under sprint-task-runner autonomy.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| AI agent / harness | Starts PyPost, waits for ready, later drives UI (siblings), then shuts down |
| PyPost application session | One launched instance of the desktop app under agent control |
| Launch entry point | Documented, supported way to start a session for agent use |
| Ready condition | Signal or pollable state meaning “UI actions may begin” |
| Shutdown | Requested end of the session with full cleanup |
| Smoke check | Automated verification of launch → ready → shutdown |
| CI / display-less environment | Runs lifecycle without an interactive display |

Interaction overview:

1. Agent or harness starts a PyPost session via the documented entry point.
2. Agent waits until the ready condition is true.
3. (Sibling stories) Agent may then perform UI actions and observe state.
4. Agent requests shutdown; the session ends with no orphans or blocking locks.
5. Smoke check exercises steps 1, 2, and 4 without requiring full product flows.

## Q&A

- Q: Why is this a separate story from UI actions and snapshots?
  A: Lifecycle is the foundation. Actions and observation are useless if start/ready/stop
  are unreliable. Sibling stories build on this contract.
- Q: Why mention offscreen / headless?
  A: Agent e2e must run in CI and similar environments without a human display; lifecycle
  must support that use case.
- Q: Is “ready” the same as “all background work finished”?
  A: No. Ready means the UI is safe for agent actions to begin. Later settle/wait helpers
  (PYPOST-837) cover waiting after specific actions.
- Q: Does this replace normal `make run` for human developers?
  A: No. Humans keep the existing interactive launch. This story adds or documents an
  agent-suitable lifecycle path (which may share or extend existing entry points).
- Q: What counts as done for documentation in this story?
  A: Enough that an agent or maintainer can find and use launch, ready, and shutdown without
  inventing steps. Epic-wide packaging lives in PYPOST-839.
- Q: Why a smoke test and not a full product flow?
  A: Full golden flow is PYPOST-838. This story only proves the lifecycle contract.
