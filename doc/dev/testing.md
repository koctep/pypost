# Testing via MCP and Prometheus

## Overview

PyPost can be tested by the AI assistant in Cursor using the embedded MCP server and
Prometheus metrics. Rules for the AI are defined in `.cursor/lsr/do-testing.md`.

## Prerequisites

- **PyPost running** — `make run` or `python -m pypost.main`
- **MCP enabled** — in Manage Environments, check "Enable MCP Server"
- **Cursor connected** — add MCP server URL `http://<host>:1080/mcp` (Streamable HTTP).
  Legacy SSE clients may still use `http://<host>:1080/sse/`.
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

Unit testability seams for `RequestService`, `HTTPClient`, and `MainWindow` are documented in
[testability.md](testability.md) (PYPOST-382).

ResponseView search bar coverage (PYPOST-365):

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_response_view_search.py -v
```

## MCP server unit tests

Automated pytest coverage for `MCPServerImpl` and Starlette routing lives in
`tests/test_mcp_server_impl.py` (PYPOST-367). Tests mock `RequestService` and avoid live
transport handshakes; routing cases assert `/mcp` and legacy `Mount("/sse")` structure.

| Class | Scope |
| --- | --- |
| `TestMCPServerImpl` | Tool registration, schemas, `call_tool`, metrics, script output |
| `TestMCPServerImplRouting` | `create_app()` route structure and method guards |
| `TestMCPServerImplInjection` | Constructor `TemplateService` injection |

Focused run:

```bash
.venv/bin/python -m pytest tests/test_mcp_server_impl.py -v
```

## MCP server integration tests

Live Streamable HTTP round-trip coverage (tool list + call against a running uvicorn server)
lives in `tests/test_mcp_server_integration.py` (PYPOST-368, PYPOST-551). Tests use the
official MCP Python SDK (`streamable_http_client`, `ClientSession`) with `anyio.run`, start
the server on an ephemeral port, and mock `RequestService.execute` for deterministic output.

| Class | Scope |
| --- | --- |
| `TestMCPServerIntegration` | `list_tools`, `call_tool`, MCP argument forwarding |
| `TestMCPServerManagerIntegration` | `MCPServerManager` thread + uvicorn lifecycle |

Focused run:

```bash
.venv/bin/python -m pytest tests/test_mcp_server_integration.py -v
```

## MCP and metrics test coverage

PYPOST-370 closed the PYPOST-38 debt item for automated MCP tools and metrics tests as
duplicate scope: prior tickets already cover the intent.

| Concern | Module | Level | Notes |
| --- | --- | --- | --- |
| MCP tool Streamable HTTP (`list_tools`, `call_tool`) | `tests/test_mcp_server_integration.py` | Integration | PYPOST-368/551; `RequestService` mocked |
| `MCPServerImpl` metrics hooks | `tests/test_mcp_server_impl.py` | Unit | PYPOST-367; `MetricsManager` mocked |
| Metrics `read_resource("metrics://all")` | `tests/test_metrics_manager.py` | Unit | Scrapes `mcp_*_total` after `read_resource` |

Not covered by the above (follow-up debt): live metrics-server MCP SSE round-trip and
integration tests with real outbound HTTP via a local stub server.

Focused metrics MCP resource run:

```bash
.venv/bin/python -m pytest tests/test_metrics_manager.py::TestMetricsManagerMcpResource -v
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

## Coverage threshold

PYPOST-88 introduced a minimum line-coverage gate; PYPOST-432 raised it incrementally toward
the 70% project target.

| Setting | Value |
| --- | --- |
| Enforcement | `--cov-fail-under=70` in `pytest.ini` `addopts` |
| CI summary display | `THRESHOLD=70` in `.github/workflows/test.yml` |
| Project target | 70% (follow-up when ready) |

Audit current coverage:

```bash
make test-cov
```

Look for `TOTAL ... XX%` and `Required test coverage of 60% reached` in the output. To raise
the threshold, update both `pytest.ini` and the `THRESHOLD` variable in `test.yml` together.
See `ai-tasks/PYPOST-88/70-dev-docs.md` for the full procedure.

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

## Pytest live logging (`log_cli`) (PYPOST-570)

`pytest.ini` enables live application logs during test runs:

| Setting | Value |
| --- | --- |
| `log_cli` | `true` |
| `log_cli_level` | `WARNING` |
| `log_format` | timestamp, level, logger name, message |

Every `make test` and CI invocation therefore prints application WARNING and ERROR lines to
stdout while tests run. On a green full-suite capture (PYPOST-567 baseline) that produced
**72 ERROR** and **138 WARNING** live-log lines across **126** tests — mostly intentional
error-path output, not test failures.

**Recommendation** (see `ai-tasks/PYPOST-570/log-cli-review.md`):

1. **Keep** `pytest.ini` defaults for local runs (helps correlate logs with failing tests).
2. **Disable in CI** with `-o log_cli=false` on the workflow pytest command (follow-up PR).
3. **PYPOST-571** — allowlist guardrail so CI still fails on unexpected ERROR lines without
   printing known noise on every green run.

Local overrides:

```bash
# Quiet run (matches recommended CI behavior)
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -o log_cli=false

# Extra verbose
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -o log_cli_level=DEBUG
```

Inventory capture still requires live logging enabled (default `make test` or explicit
`-o log_cli=true`).

## Test log inventory (PYPOST-567)

A green `make test` run can still emit many ERROR/WARNING lines because `pytest.ini`
enables live CLI logging at WARNING level. To audit that noise:

```bash
make test > tests.txt 2>&1
.venv/bin/python scripts/parse_test_log_inventory.py tests.txt \
  --markdown ai-tasks/PYPOST-567/inventory.md \
  --csv ai-tasks/PYPOST-567/inventory.csv
```

The script groups lines by logger, links them to the adjacent pytest node id, and tags
groups as **expected** (error-path tests), **suspicious**, or **unknown**. Baseline
capture (2026-06-11): 937 passed, 72 ERROR, 138 WARNING lines. See
`ai-tasks/PYPOST-567/inventory.md` for the full breakdown.

## Error-path test logging (PYPOST-568)

Many passing tests deliberately exercise failure paths (worker exceptions, retry
exhaustion, delete errors, request error dialogs). Production code correctly logs these at
ERROR; pytest live CLI logging (`log_cli_level = WARNING`) surfaces them during green runs.

PYPOST-568 audited 22 ERROR inventory rows across four modules. All are intentional
error-path tests with strong or moderate behavioral assertions; none rated high false-positive
risk. Full per-test ratings: `ai-tasks/PYPOST-568/error-path-test-audit.md`.

| Module | ERROR tests | Primary logger |
| --- | ---: | --- |
| `tests/test_retry.py` | 12 | `pypost.core.request_service` |
| `tests/test_tabs_presenter.py` | 6 | `pypost.ui.presenters.tabs_presenter` |
| `tests/test_collection_tree_delete_metrics.py` | 3 | `pypost.ui.presenters.collection_tree_actions` |
| `tests/test_worker.py` | 1 | `pypost.core.worker` |

Re-verify after worker/presenter/retry changes:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_worker.py \
  tests/test_tabs_presenter.py::TestOnRequestError \
  tests/test_collection_tree_delete_metrics.py \
  tests/test_retry.py \
  -v --tb=short
```

Optional hardening: add `caplog.at_level(logging.ERROR)` assertions for medium-risk tests
listed in the audit report.

## CI guardrails (PYPOST-571)

Proposal for enforceable CI gates so green runs cannot hide unexpected ERROR storms or
timeout-boundary passes. Full design:
`ai-tasks/PYPOST-571/ci-guardrails-proposal.md`.

| Pillar | Summary |
| --- | --- |
| **Log allowlist** | `tests/expected_log_allowlist.yaml` — permit baseline ERROR prefixes from PYPOST-567; fail on unlisted lines |
| **`caplog` contract** | Error-path tests assert logs via `caplog` **or** register prefix in allowlist; behavioral assertions remain primary |
| **Duration budget** | Warn when test duration >80% of `pytest.mark.timeout`; fail at >95% (PYPOST-569) |
| **Post-run script** | `scripts/verify_test_log_guardrails.py` parses captured pytest log after run; wired in CI after pytest |

Phase 1 implementation: [PYPOST-572](https://pypost.atlassian.net/browse/PYPOST-572) (allowlist
+ verifier). Phase 2: [PYPOST-573](https://pypost.atlassian.net/browse/PYPOST-573) (duration
audit). Caplog contract: [PYPOST-574](https://pypost.atlassian.net/browse/PYPOST-574).

## References

- [gui_testing.md](gui_testing.md) — Qt offscreen setup, `qapp` fixture, GUI test patterns
- [.cursor/lsr/do-testing.md](../../.cursor/lsr/do-testing.md) — AI assistant rules
- [MCP Integration](mcp_integration.md) — MCP setup
- [Collection item delete](collection_item_delete.md) — delete flow and metric matrix
- [pypost/core/metrics_registry.py](../../pypost/core/metrics_registry.py) — counter definitions
- [pypost/core/metrics.py](../../pypost/core/metrics.py) — `MetricsManager` facade
