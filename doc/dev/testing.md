# Testing via MCP and Prometheus

## Overview

PyPost can be tested by the AI assistant in Cursor using the embedded MCP server and
Prometheus metrics. Rules for the AI are defined in `.cursor/lsr/do-testing.md`.

## Prerequisites

- **PyPost running** — `make run` or `python -m pypost.main`
- **MCP enabled** — in Manage Environments, check "Enable MCP Server"
- **Cursor connected** — add SSE server URL `http://<host>:1080/sse` (or `http://<host>:1080/sse/`)
- **Host** — use the host from PyPost settings (e.g. `localhost`, `dev.int`)

## Testing via MCP

The AI calls MCP tools (requests with "MCP Tool" checked) and verifies responses.
See [do-testing.md](../../.cursor/lsr/do-testing.md) for the full procedure.

## Verification via Prometheus

Metrics: `http://<host>:9080/metrics/` (host from settings, default port 9080).

Key metrics for MCP testing:

| Metric | Labels | Description |
|--------|--------|--------------|
| `mcp_requests_received_total` | `method` | MCP tool invocations |
| `mcp_responses_sent_total` | `method`, `status` | MCP responses (success/error) |
| `requests_sent_total` | `method` | HTTP requests sent |
| `responses_received_total` | `method`, `status_code` | HTTP responses received |

## GUI / Qt widget tests

PyPost runs Qt tests headlessly with `QT_QPA_PLATFORM=offscreen` and a module-scoped `qapp`
fixture (`tests/conftest.py`). The project does not use the `pytest-qt` package; tests call
widget methods and assert on labels, models, and mocked dialogs.

See [gui_testing.md](gui_testing.md) for patterns, representative modules, focused commands,
and troubleshooting.

ResponseView search bar coverage (PYPOST-365):

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_response_view_search.py -v
```

## Per-test timeouts (mandatory)

Every test must declare an explicit timeout so the suite cannot hang indefinitely.
Agent rules: [.cursor/lsr/do-testing.md](../../.cursor/lsr/do-testing.md).

### Declaration

Use module-level `pytestmark` (preferred), class-level, or per-function markers:

```python
import pytest

pytestmark = pytest.mark.timeout(30)
```

Qt / event-loop tests use the default signal-based timeout (do not use `method="thread"`):

```python
pytestmark = pytest.mark.timeout(60)
```

### Recommended tiers

| Test kind | Suggested timeout (seconds) |
| --------- | --------------------------- |
| Pure unit (mocked I/O) | 10–30 |
| Qt widget / presenter | 30–60 |
| Integration / e2e / benchmark | 60–120 |

### Enforcement

[`tests/conftest.py`](../../tests/conftest.py) fails setup for any test without a closest
`timeout` marker. [`pytest.ini`](../../pytest.ini) registers the marker; `pytest-timeout` is
installed via `make venv-test`. There is no global default in `pytest.ini` — each test module,
class, or function must declare its own timeout.

```bash
make test
```

### PYPOST-400 regression surface

Worker/error-handling and related DI regressions (SSE probe, history flush):

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_http_client_sse_probe.py \
  tests/test_history_manager.py \
  tests/test_worker.py \
  tests/test_retry.py \
  tests/test_tabs_presenter.py::TestOnRequestError \
  -v --tb=short
```

When using `HistoryManager` with `tempfile.TemporaryDirectory`, call `hm.flush()` before the
context exits. SSE probe tests must inject `TemplateService()` (or rely on the `HTTPClient`
default from PYPOST-403).

## Collections tree test helpers

Shared fixtures for presenter and `CollectionTreeActions` tests live in
`tests/helpers/collections_tree.py` (`make_collection`, `FakeRequestManager`,
`patch_view_context_menu`, `build_isolated_tree_actions`, etc.). See
[collection_tree_actions.md](collection_tree_actions.md) for the isolated harness.

## Delete metric unit tests

Collection-tree delete telemetry (`gui_collection_delete_actions_total`) has dedicated
automated tests that assert `MetricsManager.track_gui_collection_delete_action` calls
without live Prometheus scraping.

| Layer | File | Status values |
| --- | --- | --- |
| Confirmation boundary | `tests/test_collection_tree_delete_confirmation.py` | `selected`, `cancelled`, `succeeded` |
| `handle_delete` failures | `tests/test_collection_tree_delete_metrics.py` | `error`, `not_found` |

Both modules cover `collection` and `request` item types. See
[collection_item_delete.md](collection_item_delete.md) for scenario details.

Focused run:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest \
  tests.test_collection_tree_delete_confirmation \
  tests.test_collection_tree_delete_metrics -v
```

## Makefile automation tests

`tests/test_makefile.py` validates root `Makefile` contracts without touching the repository
`.venv`. Scope is split across two tasks to avoid duplicate fixtures:

| Task | Scope |
| ---- | ----- |
| [PYPOST-307](https://pypost.atlassian.net/browse/PYPOST-307) | Marker lifecycle, `make -p` prerequisite chains, bare-venv `lint` failure |
| [PYPOST-310](https://pypost.atlassian.net/browse/PYPOST-310) | Lightweight execution smoke for `install`, `test`, and `lint` exit codes |

| Area | What is checked |
| ---- | ---------------- |
| Marker lifecycle | `make venv` creates `.venv/.initialized-<major.minor>`; `make clean` removes `.venv` |
| Dependency chain | `install` → `venv-test`; `run`/`test`/`lint` depend on the marker only (not `install`) |
| Exit behavior | `clean`/`venv` succeed; unknown targets fail; bare venv fails `test`/`lint` without tooling |
| Target execution | `install` with empty `requirements.txt` succeeds; `test`/`lint` succeed after `install` |

Each case runs GNU Make in an isolated `tmp_path` with a copied `Makefile`, minimal
`tests/test_noop.py`, and `pypost/__init__.py`. Focused run:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_makefile.py -v
```

## References

- [gui_testing.md](gui_testing.md) — Qt offscreen setup, `qapp` fixture, GUI test patterns
- [.cursor/lsr/do-testing.md](../../.cursor/lsr/do-testing.md) — AI assistant rules
- [MCP Integration](mcp_integration.md) — MCP setup
- [Collection item delete](collection_item_delete.md) — delete flow and metric matrix
- [pypost/core/metrics.py](../../pypost/core/metrics.py) — metric definitions
