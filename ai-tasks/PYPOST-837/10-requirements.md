# PYPOST-837: Settle/wait helpers for UI actions

## Goals

AI agents and automated harnesses that can launch PyPost, address controls by
stable identity, observe UI state, and drive actions still lack a shared way to
**wait for asynchronous UI outcomes**. After Send, opening a dialog, or other
deferred updates, scripts either race (flaky) or invent one-off polling loops
with unclear timeouts and opaque failures.

This task establishes the business capability for **settle/wait helpers**:
bounded waits for common UI conditions so agents can stabilize flaky-prone
async paths after actions, with documented timeouts and failure diagnostics
when a condition never becomes true.

## Programming Language

Python (`.cursor/lsr/do-python.md`)

## User Stories

- As an **AI agent** (or test harness), I want to wait until a named control
  exists so I can proceed after deferred UI creation (for example a dialog
  opening) without sleeping blindly.
- As an **AI agent**, I want to wait until a named control is enabled so I can
  act only when the control is usable after async enablement.
- As an **AI agent**, I want to wait until a control’s text matches an expected
  value (or predicate) so I can confirm content updates after actions such as
  Send or fill.
- As an **AI agent**, I want to wait until a UI snapshot satisfies a predicate
  so I can express richer post-action readiness without inventing custom polls.
- As an **AI agent**, I want documented default timeouts and clear failure
  diagnostics when a wait expires so I can distinguish “still settling” from
  “will never happen” and recover or fail usefully.
- As a **maintainer**, I want automated tests that demonstrate flaky-prone async
  UI paths stabilize with these waits so regressions are caught in CI.
- As a **sibling story owner** (golden flow, packaging), I want waits available
  on the same agent/harness surface as lifecycle, identity, snapshot, and
  actions so stories compose drive → wait → observe.

## Definition of Done

- Agents and harnesses can wait for common conditions: widget exists, widget
  enabled, text matches, and snapshot predicate.
- Default (and overrideable) timeouts are documented; wait failures include
  diagnostics useful for agents and maintainers.
- Waits are integrated with the existing action tools / harness surface so
  agents can wait after Send, dialog open, and similar flows.
- Automated tests demonstrate that flaky-prone async UI paths stabilize when
  using these waits (runnable via the project’s standard test workflow).
- Production code does not import from `tests/`; any shared poll helper lives
  under the product package (`pypost.agent` or a shared `pypost` util).
- Scope stays on settle/wait; lifecycle, identity, snapshot, actions, golden
  flow, and packaging remain sibling stories under PYPOST-832.

## Task Description

**Problem:** After lifecycle ready, stable identities, snapshot, and action
primitives, agents can drive and observe the UI but still race asynchronous
settling (widgets appearing, enabling, text updating, dialog trees). Duplicated
test-only wait helpers cannot be imported into production agent code, and ad-hoc
sleeps cause flaky or slow harnesses.

**Business need:** A small, intentional set of settle/wait helpers for common
post-action conditions, with bounded timeouts and actionable timeout
diagnostics, delivered on the same agent/harness surface agents already use.

### In Scope

- Wait-until helpers for: widget exists, widget enabled, text matches, snapshot
  predicate.
- Documented timeouts and failure diagnostics on timeout.
- Integration with the existing agent/action harness so waits are usable after
  Send, dialog open, and similar flows.
- Tests that show async UI paths stabilize with waits.
- Production-safe helper location (agent package or shared `pypost` util); no
  `pypost` → `tests/` imports.

### Out of Scope

- Redefining agent lifecycle ready semantics — already PYPOST-833.
- Changing stable widget identity conventions — already PYPOST-834.
- Redesigning UI snapshot capture — already PYPOST-835.
- New click/fill/select/key primitives — already PYPOST-836.
- Golden end-to-end product scenario — PYPOST-838.
- Broader agent-e2e docs/`make` packaging — PYPOST-839.
- Arbitrary “UI idle / event-queue empty” quiescence as the primary contract
  (unless expressed via the listed condition waits).
- Network MCP tools for waits on `MCPServerImpl`.
- Removing every historical test-local wait duplicate in one story (may leave
  follow-up debt if a thin adapter remains).

## Functional Requirements

- FR1: After the UI is ready for agent interaction, a consumer can wait until a
  control identified by stable widget identity exists under a lookup root.
- FR2: A consumer can wait until an identified control exists and is enabled
  (usable for subsequent actions).
- FR3: A consumer can wait until an identified control’s text matches an
  expected value or a caller-supplied text predicate.
- FR4: A consumer can wait until a UI snapshot (from the existing snapshot
  capability) satisfies a caller-supplied predicate.
- FR5: Every wait is bounded by a timeout; defaults are documented and callers
  can override the timeout for a given wait.
- FR6: When a wait times out, the consumer receives a failure with diagnostics
  sufficient to identify which condition failed and useful context (for example
  timeout budget and last observed state relevant to that wait).
- FR7: Waits are available on the same agent/harness surface used for actions
  (session and/or module API) so agents can wait after Send, dialog open, etc.
- FR8: Automated tests cover success paths for the common conditions and at
  least one timeout/diagnostics path; tests demonstrate async (delayed) UI
  updates that would be flaky without waiting.
- FR9: Production agent/wait code must not import from `tests/`.

## Non-functional Requirements

- **Boundedness:** Waits must not hang indefinitely; wall-clock timeouts are
  mandatory.
- **Actionability of failures:** Timeout errors must be specific enough for
  agents and maintainers without relying on stack traces alone.
- **Discoverability:** Maintainers and agent authors can understand supported
  conditions, defaults, and diagnostics without reverse-engineering tests.
- **Compatibility:** Waits compose with ready (833), identity (834), snapshot
  (835), and actions (836).
- **CI suitability:** Coverage runs under the project’s offscreen/automated
  test path.
- **Minimalism:** A small condition set sufficient for agent flows; not a full
  UI synchronization framework.

## Constraints and Assumptions

- Programming language: Python.
- Parent epic: PYPOST-832. Builds on PYPOST-833–836. Siblings own golden flow
  and packaging.
- “Stable identity” means the widget id / naming contract from PYPOST-834.
- “Snapshot predicate” means a boolean function over the structured snapshot
  produced by PYPOST-835.
- Existing test-only `wait_until` is a reference pattern; this story delivers a
  production-safe equivalent for agent use (deduplication with test helpers may
  be partial in this story).
- Step 1 review is treated as pre-approved under sprint-task-runner autonomy
  (no approval / no Jira updates in this run).

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| AI agent / harness | Invokes waits after actions to stabilize async UI |
| Wait condition | Exists, enabled, text match, or snapshot predicate |
| Stable identity | Address of the target control (PYPOST-834) |
| UI snapshot | Structured observation used by snapshot waits (PYPOST-835) |
| Timeout budget | Bounded duration for each wait |
| Failure diagnostics | Context returned when the budget expires |
| Action surface | Prior click/fill/select/key primitives (PYPOST-836) |

Interaction overview:

1. Agent launches PyPost and waits until UI ready (PYPOST-833).
2. Agent drives controls via action primitives (PYPOST-836).
3. Agent waits for a settle condition (this story) before continuing.
4. On timeout, the agent receives diagnostics and can fail or recover.
5. Agent may snapshot (PYPOST-835) for further verification.
6. Tests prove delayed UI updates stabilize with waits.

## Q&A

- Q: Why is this separate from actions (PYPOST-836)?
  A: Actions answer “how do I change the UI?” Waits answer “when is it safe to
  continue?” Mixing them would blur epic ownership and acceptance.
- Q: Must waits be network MCP tools?
  A: No. Delivery should match the existing local agent/harness surface used by
  lifecycle, snapshot, and actions.
- Q: Is “UI completely idle” in scope?
  A: Not as a primary contract. Callers express readiness via the listed
  conditions (exists / enabled / text / snapshot predicate).
- Q: Can production code keep using `tests.helpers.qt_wait`?
  A: No. Production must use a helper under `pypost`; tests may continue to use
  or thin-wrap that production helper.
- Q: Does this replace lifecycle ready wait?
  A: No. Ready remains the launch gate (833). This story covers post-action
  settle conditions after ready.
