# PYPOST-838: Golden e2e — agent completes one product flow

## Goals

Sibling stories under epic
[PYPOST-832](https://pypost.atlassian.net/browse/PYPOST-832) deliver the agent
and harness building blocks: application lifecycle, stable widget identity, UI
actions, UI snapshots, and settle/wait helpers. Those pieces are not yet proven
together against a real product outcome.

This task establishes one **golden end-to-end product scenario**: an agent (or
harness acting for one) launches PyPost, drives a complete request flow through
the UI, and verifies the response surface shows the expected outcome — using
those sibling capabilities, running through a documented automated path, and
failing with diagnosable context when something goes wrong.

Business value: confidence that the agent UI stack composes into a trustworthy
product proof, not only isolated helper unit behavior.

## Programming Language

Python (`.cursor/lsr/do-python.md`)

## User Stories

- As an **AI agent** (or test harness), I want one documented golden product
  flow I can run end-to-end so I can prove launch, drive, wait, observe, and
  assert work together on a real PyPost outcome.
- As an **AI agent**, I want that flow to open or create a request, set URL and
  method, send the request, and confirm the response UI shows the expected
  status and body (with HTTP satisfied in a deterministic way, such as a mocked
  OK response) so the scenario reflects a meaningful product path.
- As an **AI agent**, I want the scenario to use lifecycle, identity, actions,
  snapshot, and wait capabilities from siblings PYPOST-833–837 so the golden
  flow exercises the shared stack rather than reinventing one-off helpers.
- As a **CI / headless runner**, I want the scenario to be deterministic under
  the project’s offscreen GUI environment (`QT_QPA_PLATFORM=offscreen` or the
  project-equivalent documented path) so green/red results are trustworthy in
  automation.
- As a **maintainer**, I want failure output to include snapshot or assertion
  context so a broken golden run is diagnosable without replaying manually.
- As a **sibling story owner** (packaging / broader agent-e2e docs), I want this
  story to deliver the composed product proof while leaving wider docs/`make`
  packaging to PYPOST-839, except the minimum documentation needed to run the
  golden scenario via the documented agent/harness path.

## Definition of Done

- One golden end-to-end product scenario exists and runs via a documented
  agent/harness path (not manual-only click-through).
- The scenario uses lifecycle, identity, actions, snapshot, and wait helpers
  delivered by siblings PYPOST-833–837 (capability composition, not redefinition).
- The scenario covers: open or create a request → set URL and method → Send →
  assert the response UI shows the expected status and body for a deterministic
  successful HTTP outcome (mocked OK or equivalent).
- The scenario is deterministic in CI under offscreen / project-equivalent
  headless GUI settings.
- On failure, output includes snapshot or assertion context sufficient to
  diagnose which step or expectation failed.
- The scenario is runnable via the project’s standard test/quality workflow.
- Scope stays on this one golden product proof; broader agent-e2e packaging and
  docs remain PYPOST-839; individual helper redesign remains with sibling
  owners.

## Task Description

**Problem:** Lifecycle, identity, actions, snapshot, and wait capabilities can
exist in isolation while still leaving uncertainty that an agent can complete a
real product flow. Without a golden scenario, regressions in composition
(ready → identify → act → wait → observe → assert) may go unnoticed until
manual use.

**Business need:** A single, intentional golden e2e product flow that proves the
agent stack against a concrete request/response outcome, with CI-suitable
determinism and diagnosable failures.

### In Scope

- One golden product scenario composing sibling agent/harness capabilities
  (lifecycle, identity, actions, snapshot, wait).
- Documented agent/harness run path for that scenario (not manual-only).
- Request flow outcome: open/create request, set URL/method, Send, assert
  response UI status and body for a deterministic successful HTTP result.
- Deterministic CI execution under offscreen / project-equivalent GUI settings.
- Failure diagnostics via snapshot or assertion context.
- Minimal documentation required so maintainers and agents know how to run the
  golden scenario.

### Out of Scope

- Redesigning lifecycle launch/ready/shutdown — already PYPOST-833.
- Changing stable widget identity conventions — already PYPOST-834.
- Redesigning UI snapshot capture — already PYPOST-835.
- New click/fill/select/key primitives — already PYPOST-836.
- New settle/wait condition helpers — already PYPOST-837.
- Broader agent-e2e docs/`make` packaging beyond what this golden scenario needs
  — PYPOST-839.
- Multiple golden scenarios or a full product regression suite (one composed
  flow is the acceptance bar).
- Live, non-deterministic network dependency as the primary path for the golden
  assertion (HTTP must be satisfied deterministically, e.g. mocked OK).
- Network MCP tools redesign or unrelated MCP server work.
- Human interactive UX redesign unrelated to proving the agent flow.

## Functional Requirements

- FR1: A consumer can run one golden end-to-end product scenario through a
  documented agent/harness path without relying on manual-only steps.
- FR2: The scenario launches (or attaches via the established lifecycle) until
  the UI is ready for interaction, then shuts down cleanly as part of the run
  contract where the lifecycle capability already requires it.
- FR3: The scenario addresses controls via stable widget identity from the
  sibling identity capability.
- FR4: The scenario drives the UI using the sibling action capability
  (interaction primitives sufficient for the request flow).
- FR5: The scenario uses sibling wait capability where asynchronous UI settling
  is required after actions (for example after Send or deferred panel updates).
- FR6: The scenario uses sibling snapshot (and/or equivalent structured
  observation) capability to support verification and failure context.
- FR7: The product outcome of the scenario is: open or create a request, set
  URL and method, send the request, and assert that the response UI shows the
  expected status and body for a deterministic successful HTTP outcome.
- FR8: The HTTP dependency of the scenario is deterministic for CI (mocked OK
  or an equivalent non-flaky success path); the golden run must not depend on
  unpredictable external network availability.
- FR9: The scenario runs deterministically under the project’s offscreen GUI
  environment (`QT_QPA_PLATFORM=offscreen` or documented project equivalent).
- FR10: When the scenario fails, output includes snapshot or assertion context
  sufficient to identify which expectation or step failed.
- FR11: Automated coverage of the golden scenario is runnable via the project’s
  standard test/quality workflow.

## Non-functional Requirements

- **Composition proof:** The golden scenario must exercise the sibling stack as
  a whole, not replace it with ad-hoc one-off helpers for the same roles.
- **Determinism:** Repeated CI runs against the same code should yield stable
  pass/fail without timing races or live-network flakiness.
- **Diagnosability:** Failures must be actionable for agents and maintainers
  (snapshot or assertion context, not a bare exit code alone).
- **CI suitability:** Must work under offscreen / automated GUI conditions used
  by the project.
- **Minimalism:** Exactly one intentional golden product flow is required; a
  broad e2e matrix is out of scope.
- **Discoverability:** Maintainers can find and run the scenario via the
  documented agent/harness path without reverse-engineering tribal knowledge.

## Constraints and Assumptions

- Programming language: Python.
- Parent epic: PYPOST-832 (E2E Agent UI Testing). Story points: 5. Priority:
  High.
- Capability dependencies (business): PYPOST-833 lifecycle, PYPOST-834
  identity, PYPOST-835 snapshot, PYPOST-836 actions, PYPOST-837 wait. This
  story composes them; it does not redefine their contracts.
- Suggested product flow is a capability outcome: open/create request → set
  URL/method → Send → assert response UI status/body for successful HTTP
  (mocked OK or equivalent). Exact fixture URL/body values are not mandated
  beyond being expected and deterministic.
- “Documented agent/harness path” means a project-supported, repeatable entry
  that agents and CI can follow; full epic packaging remains PYPOST-839.
- Step 1 review is treated as pre-approved under sprint-task-runner autonomy
  (no approval gate / no Jira updates in this run).

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| AI agent / harness | Runs the golden scenario end-to-end |
| Golden product scenario | Single composed request/response UI proof |
| Lifecycle capability | Launch, ready, shutdown (PYPOST-833) |
| Stable identity | Addresses key controls (PYPOST-834) |
| Action capability | Drives UI interactions (PYPOST-836) |
| Wait capability | Settles async UI after actions (PYPOST-837) |
| Snapshot capability | Observes UI for assert and failure context (PYPOST-835) |
| Request editor surface | Where URL/method are set and Send is invoked |
| Response surface | Where expected status/body are verified |
| Deterministic HTTP outcome | Successful response source for the assert (e.g. mocked OK) |
| Failure diagnostics | Snapshot or assertion context on failure |

Interaction overview:

1. Agent/harness starts PyPost and waits until the UI is ready (lifecycle).
2. Agent opens or creates a request and addresses controls by stable identity.
3. Agent sets URL and method, then sends the request (actions).
4. Agent waits for asynchronous UI settlement where needed (waits).
5. Agent observes the response UI (snapshot / structured observation) and
   asserts expected status and body for the deterministic successful HTTP
   outcome.
6. On failure, diagnostics include snapshot or assertion context.
7. Run ends cleanly under the lifecycle contract; CI can repeat deterministically
   under offscreen settings.

## Q&A

- Q: Why is this separate from the helper stories (833–837)?
  A: Helpers answer “can each building block work?” The golden scenario answers
  “do they compose into one real product outcome?” That is the epic’s proof
  bar.
- Q: Must there be more than one golden scenario?
  A: No. Acceptance is one intentional product flow. Additional flows may be
  follow-up debt or later stories.
- Q: Can the golden flow use live external HTTP?
  A: Not as the primary path. The successful HTTP outcome must be deterministic
  for CI (mocked OK or equivalent).
- Q: Does this story own full agent-e2e packaging and docs?
  A: No. PYPOST-839 owns broader packaging. This story only needs enough
  documentation for the documented agent/harness path of the golden scenario.
- Q: What if a sibling helper is incomplete?
  A: This story assumes 833–837 deliver their accepted capabilities. Gaps in
  those contracts remain with the sibling owners; this story composes them.
- Q: Are exact expected status codes and body strings mandated here?
  A: Only that they are expected, asserted, and deterministic for a successful
  HTTP outcome. Concrete fixture values are left to later design/implementation
  steps.
