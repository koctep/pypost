# Agent UI E2E (PYPOST-839)

## Overview

PyPost’s **agent UI e2e** stack lets an in-process harness (or agent) launch
the desktop app offscreen, address controls by stable ids, drive actions,
wait for settle, capture UI snapshots, and prove one golden product flow.

This page is the **umbrella entry** for that stack. Capability contracts live
in sibling docs; the golden Send → response proof lives in
[agent_golden_e2e.md](agent_golden_e2e.md). The PYPOST-887 double-body
regression lock (exactly-once panel body) is
[agent_e2e_double_response_body.md](agent_e2e_double_response_body.md).
The method × body **presentation matrix** (PYPOST-890) is
[agent_e2e_presentation_matrix.md](agent_e2e_presentation_matrix.md).
The reusable **environment pack** model (seed, isolation, fixtures inventory)
is [agent_e2e_env.md](agent_e2e_env.md). Product **dialog settle** after Settings
open (PYPOST-919) is [agent_dialog_settle.md](agent_dialog_settle.md).

`make test-agent-e2e` is the **primary packaging** path for the **broader**
agent e2e pack **beyond golden** (PYPOST-922). Prefer it over ad-hoc pytest
one-liners. CI gates the same target via the `agent-e2e` job in
`.github/workflows/test.yml` (PYPOST-861); the main fast suite also includes
these tests via `-m "not slow"` (intentional 3.11 double-run; DEFER after
evidence — PYPOST-873 / PYPOST-907 / PYPOST-930 continued DEFER; PYPOST-908
timing notes in [testing.md](testing.md)).

This is **not** live MCP verification against a running PyPost. For MCP tools
and Prometheus checks, see [testing.md](testing.md) and
[mcp_integration.md](mcp_integration.md).

## Architecture

| Layer | Doc / module | Role |
| --- | --- | --- |
| Lifecycle | [agent_lifecycle.md](agent_lifecycle.md) | Launch → ready → shutdown |
| Identity | [ui_identity.md](ui_identity.md) | Stable `objectName` / `widget_ids` |
| Actions | [ui_actions.md](ui_actions.md) | click / fill / select / key |
| Snapshot | [ui_snapshot.md](ui_snapshot.md) | Structured visible-UI tree |
| Wait | [ui_wait.md](ui_wait.md) | Settle predicates after actions |
| Golden | [agent_golden_e2e.md](agent_golden_e2e.md) | Composed Send → response proof |
| Body lock | [lock doc](agent_e2e_double_response_body.md) | Exactly-once body (889) |
| Presentation matrix | [matrix](agent_e2e_presentation_matrix.md) | Method × body (890) |
| Env pack | [agent_e2e_env.md](agent_e2e_env.md) | Seed, isolation, HTTP, markers (855) |
| Seed inventory | [agent_e2e_seed.md](agent_e2e_seed.md) | Known collections/envs/requests (857) |
| HTTP stubs | [agent_e2e_http.md](agent_e2e_http.md) | Canned responses at send boundary (859) |
| GUI notes | [gui_testing.md](gui_testing.md) | Offscreen Qt, fixtures, pitfalls |

```mermaid
flowchart LR
  Life[Lifecycle] --> Id[Identity]
  Id --> Act[Actions]
  Act --> Wait[Wait]
  Wait --> Snap[Snapshot]
  Snap --> Golden[Golden e2e]
```

Public APIs are re-exported from `pypost.agent` (session mirrors included).
Do not reinvent helpers inside tests when the package API already covers the
step.

## API / Usage

### How to run

Install once, then use the dedicated primary packaging target (offscreen Qt
via Makefile). Default selection is the **broader** `@pytest.mark.agent_e2e`
pack **beyond golden** (`-m "agent_e2e and not slow"`; CLI `-m` overrides
`addopts`):

```bash
make install
make test-agent-e2e
# equivalent: pytest -m "agent_e2e and not slow"
```

Harness modules under the marker (also the documented file-list override):

| Module | Covers |
| --- | --- |
| `tests/test_agent_lifecycle_smoke.py` | Lifecycle smoke |
| `tests/test_agent_e2e_session_ready_logs.py` | Live ready-log caplog smoke (899) |
| `tests/test_agent_lifecycle_mid_start_cleanup.py` | Mid-start cleanup (841) |
| `tests/test_ui_identity_spotcheck.py` | Identity spot-check |
| `tests/test_ui_actions.py` | Action primitives; live `COLLECTION_TREE` negative select (975) |
| `tests/test_ui_snapshot.py` | Snapshot capture |
| `tests/test_ui_wait.py` | Settle / wait |
| `tests/test_agent_golden_e2e.py` | Golden product flow |
| `tests/test_agent_e2e_double_response_body.py` | Double-body lock (889) |
| `tests/test_agent_e2e_presentation_matrix.py` | Presentation matrix (890) |
| `tests/test_agent_e2e_seed.py` | Seeded workspace (857) + failure caplog (862) |
| `tests/test_agent_e2e_http_env.py` | Env Send + shared HTTP (859) |
| `tests/test_agent_e2e_http_seed_post.py` | Seed POST Send + body (871) |
| `tests/test_agent_e2e_http_mapping_multi_url.py` | Mapping stub two-URL Send (901) |
| `tests/test_agent_e2e_http_mapping_compound_keys.py` | Mapping compound-key same-URL Send (958) |
| `tests/test_agent_e2e_failure_artifacts.py` | Failure snapshot dumps (860) |
| `tests/test_agent_dialog_settle_e2e.py` | Dialog settle (919); [doc](agent_dialog_settle.md) |
| `tests/test_agent_ui_actions_mcp.py` | Out-of-process agent-UI MCP sidecar (952) |

**Keep this table synced with markers:** when you add or remove
`@pytest.mark.agent_e2e` on a module, update the Module column above in the
same change. Pure unit drift guards (for example seed inventory
`tests/test_agent_e2e_seed_inventory_doc.py`, or this table’s own guard
`tests/test_agent_e2e_harness_table_doc.py`) must **not** carry `agent_e2e`
and must **not** appear in this table — see [agent_e2e_seed.md](agent_e2e_seed.md)
for the seed inventory check. `make test` runs
`tests/test_agent_e2e_harness_table_doc.py`, which fails if the marked set
and this table diverge.

Narrow to the golden scenario (or another single module) via `PYTEST_ARGS`
(replaces the default `-m` expression; does not change the primary packaging
entry):

```bash
make test-agent-e2e PYTEST_ARGS="tests/test_agent_golden_e2e.py -v"
```

The same modules still run under the full fast suite:

```bash
make test
```

### CI (PYPOST-861)

| Entry | What runs |
| --- | --- |
| Job `agent-e2e` | `make install` then `make test-agent-e2e` (Python 3.11) |
| Job `test` (matrix) | `pytest tests/ -m "not slow"` — includes `agent_e2e` |

Prefer the make target locally and when debugging pack failures. The dedicated
job proves the Makefile recipe; the matrix keeps multi-version coverage.

On Python 3.11 that means an **intentional double-run** of the pack (main
matrix + `agent-e2e`). [PYPOST-873](https://pypost.atlassian.net/browse/PYPOST-873)
**DEFER**s a CI cost trim; [PYPOST-907](https://pypost.atlassian.net/browse/PYPOST-907)
reviewed **CI duration evidence** and chose **DEFER after evidence**;
[PYPOST-930](https://pypost.atlassian.net/browse/PYPOST-930) re-assessed the
ENABLE threshold and chose **continued DEFER** — **ENABLE threshold not
met** (checklist in [testing.md](testing.md) § Agent e2e CI double-run).
**Revisit when** the ENABLE threshold in that section is met. Job-duration /
overlap timing notes are locked under
[PYPOST-908](https://pypost.atlassian.net/browse/PYPOST-908) (same section;
do not invent numbers — run `make refresh-ci-duration-evidence` and paste into
[testing.md](testing.md) per PYPOST-931).

[PYPOST-874](https://pypost.atlassian.net/browse/PYPOST-874) **ENABLE**s
failure-only upload of `artifacts/agent_e2e/` from job `agent-e2e` as Actions
artifact `agent-e2e-failure-artifacts`.
[PYPOST-909](https://pypost.atlassian.net/browse/PYPOST-909) **ENABLE**s the
same path from the main `test` matrix as
`agent-e2e-failure-artifacts-${{ matrix.python-version }}`.
[PYPOST-910](https://pypost.atlassian.net/browse/PYPOST-910) sets
`retention-days: 14` on both failure uploads (see
[agent_e2e_failure_artifacts.md](agent_e2e_failure_artifacts.md)).
[PYPOST-911](https://pypost.atlassian.net/browse/PYPOST-911) **DEFER**s
a one-time live Artifacts UI screenshot/notes until a qualifying red
run uploads dumps; maintainer checklist (what to capture) lives in
[agent_e2e_failure_artifacts.md](agent_e2e_failure_artifacts.md) § Live
Artifacts UI proof and
`ai-tasks/PYPOST-911/live-proof-notes.md`.

See [testing.md](testing.md) for suite-wide CI layout.

### Marker: `agent_e2e`

Registered in `pyproject.toml` (`[tool.pytest.ini_options] markers`).

Apply it (usually at module scope next to `timeout`) on agent UI e2e /
env-pack scenarios:

```python
pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]
```

Select with `-m agent_e2e` (or the make target above). List markers via
`pytest --markers`.

### Shared session fixtures

Defined in `tests/_pytest_plugins/agent_e2e.py` (loaded via
`tests/conftest.py`). Both are **function-scoped** and yield a ready
`AgentAppSession` (`offscreen=True`, `ready_timeout=30.0`).

| Fixture | Workspace | Use when |
| --- | --- | --- |
| `agent_e2e_session` | Blank (session-owned temps) | Lifecycle, identity, actions, golden |
| `seeded_agent_e2e_session` | PYPOST-857 seed via `seeded_agent_dirs()` | Seeded inventory / env Send |
| `agent_e2e_http_stub` | Yields `stub_agent_e2e_http` | Deterministic Send (PYPOST-859) |

```python
def test_ready(agent_e2e_session):
    assert agent_e2e_session.window.is_ui_ready


def test_seeded(seeded_agent_e2e_session):
    assert seeded_agent_e2e_session.window.is_ui_ready
```

Multi-session isolation tests keep constructing `AgentAppSession` directly
(fixtures yield one instance per request). Prefer fixtures for single-session
scenarios. Direct constructions still auto-dump failure artifacts when the
agent e2e plugin is loaded — see
[agent_e2e_failure_artifacts.md](agent_e2e_failure_artifacts.md) (PYPOST-875).

After the session is ready, each packaging fixture logs INFO
`agent_e2e_fixture_ready mode=blank` or `mode=seeded` (logger
`tests._pytest_plugins.agent_e2e`). Caplog proofs:
- **Unit (PYPOST-867):** `tests/test_agent_e2e_packaging_logs.py` — pure unit
  (mocked session boundary); drives fixtures via
  `tests/helpers/fixture_drive.py` (PYPOST-900); must **not** carry
  `agent_e2e` and must **not** appear in the harness table above.
- **Live smoke (PYPOST-899):** `tests/test_agent_e2e_session_ready_logs.py` —
  real `agent_e2e_session` / `seeded_agent_e2e_session` under caplog (no
  session mocks); marked `agent_e2e` and listed in the harness table.
  Catalog: [logging.md](logging.md).

### Setup checklist

1. `make install` (venv + `.[dev,otel]`).
2. Prefer Makefile targets — they set `QT_QPA_PLATFORM=offscreen`.
3. Read identity convention before adding controls:
   [ui_identity.md](ui_identity.md).
4. Prefer `agent_e2e_session` / `seeded_agent_e2e_session`; mark new modules
   `agent_e2e`. Direct `AgentAppSession` remains valid for multi-session proofs.
5. For product proof, start from the golden scenario rather than a new
   one-off flow.

### Tools map (what agents call)

| Need | Entry |
| --- | --- |
| Session (shared) | fixtures `agent_e2e_session` / `seeded_agent_e2e_session` |
| Session (direct) | `AgentAppSession(offscreen=True)` |
| HTTP stub (shared) | `stub_agent_e2e_http` / fixture `agent_e2e_http_stub` |
| Find / ids | `pypost.ui.widget_ids` + `find_widget` |
| Drive UI | `session.ui_fill` / `ui_select` / `ui_click` / … |
| Observe | `session.ui_snapshot()` |
| Settle | `session.wait_for_text` / `wait_for_snapshot` / `wait_until` / … |
| | (Send → response: text-wait on status/body — [golden](agent_golden_e2e.md), |
| | [send settle helper](agent_e2e_send_settle.md)) |
| Failure dump | Auto on fixture **or** direct-session assert fail — [failure artifacts](agent_e2e_failure_artifacts.md) |
| Send settle (siblings) | `tests.helpers.agent_e2e_send_settle` — [send settle doc](agent_e2e_send_settle.md) |
| Response-panel snapshot helpers | `tests.helpers.agent_e2e_response_panel` — [helpers doc](agent_e2e_response_panel.md) |

### Identity convention

Stable ids live in `pypost/ui/widget_ids.py` and are applied on widgets as
`objectName`. Agents must target those constants — not brittle labels or
geometry. Details and catalog: [ui_identity.md](ui_identity.md).

### Golden scenario

One intentional flow: blank request → set URL/method → Send (shared HTTP
stub 200) → `wait_for_text` on `RESPONSE_STATUS` / `RESPONSE_BODY`
(display-form body; PYPOST-920). Full steps:
[agent_golden_e2e.md](agent_golden_e2e.md). Shared HTTP catalog:
[agent_e2e_http.md](agent_e2e_http.md). Sibling Send modules use the
shared [send settle helper](agent_e2e_send_settle.md) (PYPOST-948); panel
snapshot helpers remain for post-settle walks / excerpts:
[agent_e2e_response_panel.md](agent_e2e_response_panel.md).

### Double-body regression lock

PUT + malformed nested JSON-like body → stubbed Send with one streamed chunk
→ assert the response body token appears **exactly once** under
`RESPONSE_PANEL`. See
[agent_e2e_double_response_body.md](agent_e2e_double_response_body.md)
(product discard: [response-streaming-display.md](response-streaming-display.md)).

### Presentation matrix (PYPOST-890)

Parametrized method × body-shape cells assert once-only body token and
once-only status under `RESPONSE_PANEL`. Smoke slice runs under default
`make test-agent-e2e`; full 25-cell cartesian needs `-m agent_e2e` (includes
`slow`). Findings handoff: `ai-tasks/PYPOST-890/findings.md`. Triage
(PYPOST-891, empty findings → won’t file):
`ai-tasks/PYPOST-891/triage-summary.md`. See
[agent_e2e_presentation_matrix.md](agent_e2e_presentation_matrix.md).

## Configuration

| Setting | Source |
| --- | --- |
| Offscreen Qt | `make test-agent-e2e` / `make test` (`QT_QPA_PLATFORM=offscreen`) |
| Session offscreen | Fixtures / `AgentAppSession(offscreen=True)` setdefault the env var |
| Marker selection | `make test-agent-e2e` → `-m "agent_e2e and not slow"` |
| File-list override | `PYTEST_ARGS` replaces the default `-m` expression |
| CI make gate | `.github/workflows/test.yml` job `agent-e2e` (PYPOST-861) |
| Failure artifacts | On disk: `artifacts/agent_e2e/` or `PYPOST_AGENT_E2E_ARTIFACTS` (860) |
| Failure CI upload | `agent-e2e-failure-artifacts` on `agent-e2e` (874); matrix |
| | `agent-e2e-failure-artifacts-<py>` on `test` failure (909) |
| Failure retention | `retention-days: 14` on both uploads (PYPOST-910) |
| Live Artifacts UI proof | **DEFER** (PYPOST-911); checklist in failure_artifacts doc |
| Module timeouts | Per-test / module `pytest.mark.timeout` (see sibling docs) |

Failure dumps: [agent_e2e_failure_artifacts.md](agent_e2e_failure_artifacts.md).
Otherwise no extra env vars beyond the project’s standard GUI test path.

When adding another agent e2e module, mark it `@pytest.mark.agent_e2e`
and add a row to the harness table above (same PR). When removing the
mark, drop the row. File-list `PYTEST_ARGS` overrides remain supported
for narrow runs.

## Troubleshooting

| Issue | What to do |
| --- | --- |
| Qt / display errors | Run via `make test-agent-e2e` (not bare pytest without offscreen) |
| Golden wait timeout | See [agent_golden_e2e.md](agent_golden_e2e.md) failure table |
| Wrong tab / orphan find after strip | Bare `removeTab` leaves orphan role ids; use |
| | `deleteLater` pattern + current-tab scope — |
| | [golden removeTab hazard](agent_golden_e2e.md#tab-strip-hazards-removetab-orphans) |
| Missing control | Confirm id in `widget_ids` and `is_ui_ready` |
| Confused with MCP | MCP needs a running app + MCP enabled; agent e2e is in-process pytest |
| Want one file only | `make test-agent-e2e PYTEST_ARGS="tests/test_….py -v"` |
| Marker not listed | Confirm registration in `pyproject.toml`; run `pytest --markers` |
| CI make gate red | Reproduce with `make install && make test-agent-e2e`; see job |
| | `agent-e2e` in `.github/workflows/test.yml` |
| Assert fail, need UI state | Open `artifacts/agent_e2e/` — see |
| | [agent_e2e_failure_artifacts.md](agent_e2e_failure_artifacts.md) |
| CI `agent-e2e` red, need dumps | Download Actions artifact |
| | `agent-e2e-failure-artifacts` (PYPOST-874) |
| CI main `test` matrix red, need dumps | Download |
| | `agent-e2e-failure-artifacts-<python>` (PYPOST-909) |
| Failure artifact missing after ~14 days | Expected — `retention-days: 14` |
| | (PYPOST-910); re-run or use local dumps |
| No live UI proof / screenshot yet | Expected — PYPOST-911 **DEFER**; follow |
| | checklist in [agent_e2e_failure_artifacts.md](agent_e2e_failure_artifacts.md) |
| | and `ai-tasks/PYPOST-911/live-proof-notes.md` |
| Harness table ≠ marks | Align Module rows with `@pytest.mark.agent_e2e`; |
| | run `make test PYTEST_ARGS=` |
| | `"tests/test_agent_e2e_harness_table_doc.py -v"` |
| | (PYPOST-866) |
| Ready log missing / renamed | Assert under |
| | `caplog.at_level(INFO, logger="tests._pytest_plugins.agent_e2e")`; |
| | unit: `make test PYTEST_ARGS=` |
| | `"tests/test_agent_e2e_packaging_logs.py -v"` (PYPOST-867); |
| | live: `make test-agent-e2e PYTEST_ARGS=` |
| | `"tests/test_agent_e2e_session_ready_logs.py -v"` (PYPOST-899) |

More GUI pitfalls: [gui_testing.md](gui_testing.md). Suite-wide pytest /
timeouts: [testing.md](testing.md).

## Related

- [Agent App Lifecycle](agent_lifecycle.md)
- [UI Widget Identity](ui_identity.md)
- [UI Action Tools](ui_actions.md)
- [UI State Snapshot](ui_snapshot.md)
- [UI Settle / Wait Helpers](ui_wait.md)
- [Agent Golden E2E](agent_golden_e2e.md)
- [Agent E2E Product Dialog Settle](agent_dialog_settle.md)
- [Agent E2E Double Response-Body Lock](agent_e2e_double_response_body.md)
- [Agent E2E Presentation Matrix](agent_e2e_presentation_matrix.md)
- [Agent E2E Environment Contract](agent_e2e_env.md)
- [Agent E2E Seed Inventory](agent_e2e_seed.md)
- [Agent E2E HTTP Fixture Layer](agent_e2e_http.md)
- [Agent E2E Failure Artifacts](agent_e2e_failure_artifacts.md)
- [GUI Testing](gui_testing.md)
- [Testing via MCP and Prometheus](testing.md)
- [MCP Integration](mcp_integration.md)
