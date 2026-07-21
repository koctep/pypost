# PYPOST-860: Failure artifacts — snapshot dump on assert fail

## Goals

When an agent e2e scenario fails an assertion (or raises during the test
call), authors and CI need a **diagnosable UI snapshot** and concise
diagnostics without re-running the failing test locally. Today the env pack
contract ([agent_e2e_env.md](../../doc/dev/agent_e2e_env.md)) names failure
artifacts as an area owned by this story, but nothing dumps a snapshot on
fail.

This story’s business goal is to make agent e2e / env-pack failures
**self-explaining**: on assert fail, capture a masked UI snapshot plus
short diagnostics, wire that behavior into golden and env-pack scenarios,
document where files land and how to read them, and never weaken the
snapshot secret-masking policy from PYPOST-835.

## Programming Language

Python (`.cursor/lsr/do-python.md`) for dump helper, pytest hook/fixture
wiring, and tests. Developer docs in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **scenario author / AI agent**, when a golden or env-pack assertion
  fails, I want a UI snapshot dump on disk so I can see what the UI showed
  without reproducing the failure.
- As a **CI reader**, I want failure output (or docs) to point at the
  artifact location so I can open the dump from the job workspace.
- As a **security-conscious maintainer**, I want dumps to reuse snapshot
  masking so secrets in the UI are not written cleartext to artifacts or
  logs.
- As an **env-pack consumer**, I want this to apply automatically to
  scenarios that use the shared session fixtures (golden + seeded env
  pack), not only when I remember a manual helper call.

## Definition of Done

- A failure hook or helper dumps a UI snapshot and concise diagnostics on
  assert / call failure for agent e2e sessions.
- Behavior is wired so golden and env-pack tests that use shared session
  fixtures get dumps without per-assert boilerplate.
- Developer docs describe where artifacts land and how to read them.
- Dumps do not log or persist secrets contrary to `ui_snapshot` masking
  (reuse that capture path).
- Env contract status for “Failure artifacts” can move to Delivered.

## Task Description

**Problem:** Agent e2e failures often leave only an assert message; the UI
state at failure time is lost when the session tears down.

**Business need:** Capture a masked snapshot (+ concise diagnostics) on
failure so diagnosis is possible from CI or a single local run.

### In Scope

- Failure hook and/or helper that dumps snapshot + concise diagnostics
  (optional widget_id / session context when available).
- Automatic wiring for tests using shared agent e2e session fixtures
  (covers golden and env-pack Send scenarios).
- Docs: artifact path, file layout, how to read, secrets note.
- Update env-contract status for failure artifacts.
- Tests proving dump on failure, masking reuse, and that success paths do
  not leave failure dumps.

### Out of Scope

- Replacing or forking the PYPOST-835 snapshot API.
- Network MCP `ui_snapshot` tool.
- Uploading artifacts to a remote store (CI upload config may be docs-only
  guidance; not a required product feature).
- Changing product UI or RequestWorker behavior.
- User-facing product docs (`doc/user/`).
- Make/CI env-pack entry (PYPOST-861).

## Functional Requirements

- FR1: On test **call** failure for a scenario that holds a live agent e2e
  session fixture, dump a UI snapshot to a documented on-disk location.
- FR2: Dump includes **concise diagnostics** (at least test identity and a
  short failure summary); may include optional widget/session context when
  available without secrets.
- FR3: Dump uses the existing snapshot capture path so string values follow
  the same masking as `capture_ui_snapshot` / `ui_snapshot`.
- FR4: Golden and env-pack scenarios that use `agent_e2e_session` /
  `seeded_agent_e2e_session` are covered by the automatic wiring.
- FR5: Docs state artifact root, per-failure layout, and how to interpret
  snapshot vs diagnostics files.
- FR6: Logging around dumps must not emit secret values or the full tree
  (scalars / paths only, consistent with snapshot observability).

## Non-functional Requirements

- **Safety:** No cleartext secrets in artifact files beyond what the
  snapshot API would already emit after masking.
- **Best-effort:** Dump failures must not replace or hide the original
  test failure (log and continue).
- **Timeouts:** New/changed pytest tests declare explicit
  `pytest.mark.timeout` per `.cursor/lsr/do-testing.md`.
- **Discoverability:** Artifact location is stable enough to document and
  find after a local or CI run.
- **Minimalism:** Prefer hook + shared helper over per-test try/except
  dumps in every golden/env scenario.

## Constraints and Assumptions

- Parent epic: [PYPOST-855](https://pypost.atlassian.net/browse/PYPOST-855).
- Builds on [PYPOST-835](https://pypost.atlassian.net/browse/PYPOST-835)
  snapshot API and masking.
- Env contract: [PYPOST-856](https://pypost.atlassian.net/browse/PYPOST-856) /
  [doc/dev/agent_e2e_env.md](../../doc/dev/agent_e2e_env.md).
- Session fixtures: [PYPOST-858](https://pypost.atlassian.net/browse/PYPOST-858)
  (`tests/_pytest_plugins/agent_e2e.py`).
- Golden: `tests/test_agent_golden_e2e.py`; env Send:
  `tests/test_agent_e2e_http_env.py`.
- Step 1 review is treated as pre-approved under sprint-task-runner
  autonomy (user: do not commit / do not transition Jira).

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Failure dump helper | Writes snapshot + diagnostics to disk |
| Failure hook (pytest) | Detects call failure; invokes helper when session present |
| Agent e2e session fixture | Live window source for snapshot at failure time |
| UI snapshot (835) | Masked structured tree reused for the dump |
| Artifact files | On-disk snapshot + diagnostics for humans/CI |
| Docs | Where artifacts land and how to read them |

Interaction overview:

1. Scenario uses shared session fixture and fails during call.
2. Hook notices failure while the session is still alive.
3. Helper captures masked snapshot + concise diagnostics to disk.
4. Author or CI opens the documented path to diagnose.
5. Session tears down as usual.

## Q&A

- Q: Why dump on fail instead of always?
  A: Success runs should stay cheap and quiet; failures need the UI state
  that is about to be destroyed.
- Q: Why automatic hook vs only a manual helper?
  A: AC requires wiring into golden/env pack; authors should not forget a
  dump call. A public helper remains useful for unit tests of the dump
  itself.
- Q: Who owns secret masking?
  A: Reuse PYPOST-835 `capture_ui_snapshot` / session `ui_snapshot()`;
  do not invent a second sanitizer for tree values.
- Q: Does this upload CI artifacts?
  A: Docs may mention upload patterns; implementing a GitHub Actions
  upload is optional / follow-up unless required for DoD (DoD is dump +
  docs, not remote storage).
