# Agent E2E HTTP Fixture Layer (PYPOST-859)

## Overview

Shared **deterministic HTTP** helpers for agent UI e2e: a canned-response
catalog and a context manager that stubs
`HTTPClient.send_request` at the RequestService import site.

Scenarios keep the real UI → `RequestWorker` → response panel path. Live
external HTTP is not the primary agent-flow path under offscreen CI.

Env contract area: [agent_e2e_env.md](agent_e2e_env.md). Session packaging:
[agent_e2e.md](agent_e2e.md). Golden composition:
[agent_golden_e2e.md](agent_golden_e2e.md). Double-body lock (streaming stub):
[agent_e2e_double_response_body.md](agent_e2e_double_response_body.md).
Method × body presentation matrix (streaming stubs, once-only asserts):
[agent_e2e_presentation_matrix.md](agent_e2e_presentation_matrix.md).

## Architecture

| Component | Role |
| --- | --- |
| `pypost/fixtures/agent_e2e_http.py` | Catalog, builder, `stub_agent_e2e_http` |
| `agent_e2e_http_stub` fixture | Yields the same CM from the agent_e2e plugin |
| Patch target | `pypost.core.request_service.HTTPClient.send_request` |
| Product path | UI actions → RequestWorker → stubbed send → panel |

```mermaid
flowchart LR
  Scenario --> Stub[stub_agent_e2e_http]
  Catalog[CANNED_*] --> Stub
  Stub -.->|patches| Boundary[send_request]
  UI[ui_click Send] --> Worker[RequestWorker] --> Boundary --> Panel
```

## API / Usage

### Canned catalog

| Name | Constant | Typical URL |
| --- | --- | --- |
| `golden_ok` | `CANNED_GOLDEN_OK` | `https://example.test/agent-golden` |
| `seed_get_ok` | `CANNED_SEED_GET_OK` | `https://example.test/get` |
| `seed_post_ok` | `CANNED_SEED_POST_OK` | `https://example.test/post` |
| `double_body_lock_ok` | `CANNED_DOUBLE_BODY_LOCK_OK` | `…/pypost-887-double-body` |

Also: `CANNED_HTTP_CATALOG` (`dict` name → result),
`make_canned_http_result(...)`, URL/body constants (`GOLDEN_*`,
`SEED_GET_RESOLVED_URL`, `LOCK_DOUBLE_BODY_*`, …).

### Streaming side effect (double-body lock)

Plain `return_value` stubs never call `stream_callback`, so the chunk-flush
vs `display_response` race cannot appear. For once-only presentation locks,
pass a side effect from `canned_send_with_one_chunk(result)`:

```python
from pypost.fixtures.agent_e2e_http import (
    CANNED_DOUBLE_BODY_LOCK_OK,
    canned_send_with_one_chunk,
    stub_agent_e2e_http,
)

with stub_agent_e2e_http(canned_send_with_one_chunk(CANNED_DOUBLE_BODY_LOCK_OK)):
    session.ui_click(SEND_BUTTON)
```

See [agent_e2e_double_response_body.md](agent_e2e_double_response_body.md).
The presentation matrix uses the same side effect per cell —
[agent_e2e_presentation_matrix.md](agent_e2e_presentation_matrix.md).

### Stub install

```python
from pypost.fixtures.agent_e2e_http import (
    CANNED_GOLDEN_OK,
    stub_agent_e2e_http,
)

with stub_agent_e2e_http(CANNED_GOLDEN_OK):
    session.ui_click(SEND_BUTTON)
    snap = session.wait_for_snapshot(predicate, timeout=15.0)
```

Or via the pytest fixture (same callable):

```python
def test_send(agent_e2e_session, agent_e2e_http_stub):
    with agent_e2e_http_stub(CANNED_GOLDEN_OK):
        ...
```

Pass a callable as `result` to use `side_effect` (multi-call sequences).
Optional `name=` labels custom installs in logs (catalog identities auto-name).

### How to add a new canned response

1. Add constants (URL/body/status) in
   `pypost/fixtures/agent_e2e_http.py` if they are shared inventory.
2. Build with `make_canned_http_result(...)` and assign a module-level
   `CANNED_*` name.
3. Register it in `CANNED_HTTP_CATALOG` under a stable string key.
4. If it should auto-log a friendly `name=`, extend the identity checks
   inside `stub_agent_e2e_http` (or always pass `name=`).
5. Document the row in this page’s catalog table and, if seed-related,
   keep URLs aligned with [agent_e2e_seed.md](agent_e2e_seed.md).
6. Prefer consuming the new entry from golden/env scenarios via
   `stub_agent_e2e_http` / `agent_e2e_http_stub` — do not add private
   `patch("…HTTPClient.send_request")` as the primary path.

## Configuration

| Setting | Value |
| --- | --- |
| Patch target | `SEND_REQUEST_PATCH_TARGET` in the fixture module |
| Offscreen Qt | `make test-agent-e2e` / fixtures `offscreen=True` |
| Timeouts | Module `pytest.mark.timeout(60)` for GUI Send; unit `timeout(10)` |

No extra env vars.

## Troubleshooting

| Failure | What to do |
| --- | --- |
| Wait timeout after Send | Confirm stub context wraps the click; grep |
| | `agent_e2e_http_stub_installed`. Check catalog body vs snapshot |
| | compact JSON form (see golden docs). |
| Live network / flaky CI | Do not remove the stub; do not mock RequestWorker |
| | wholesale. |
| Stub “not restoring” | Ensure `with stub_agent_e2e_http(...):` covers the |
| | Send; exceptions still exit the context manager. |
| Wrong patch target | Always use this helper (RequestService use site), not |
| | `pypost.core.http_client.HTTPClient.send_request` alone. |

## Related

- [Agent E2E Environment Contract](agent_e2e_env.md)
- [Agent UI E2E](agent_e2e.md)
- [Agent Golden E2E](agent_golden_e2e.md)
- [Agent E2E Double Response-Body Lock](agent_e2e_double_response_body.md)
- [Agent E2E Presentation Matrix](agent_e2e_presentation_matrix.md)
- [Agent E2E Seed Inventory](agent_e2e_seed.md)
- [Logging Event Naming Convention](logging.md)
