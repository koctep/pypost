# Testing via MCP and Prometheus

## Overview

PyPost testing spans **automated pytest** (local and CI) and **optional AI-assisted checks**
(MCP tools, Prometheus metrics). This document is the developer reference for pytest, CI
guardrails, and coverage. Agent authoring rules live in
[`.cursor/lsr/do-testing.md`](../../.cursor/lsr/do-testing.md) — not a substitute for
`make test`.

### Automated pytest (primary)

```bash
make test            # fast suite (excludes -m slow)
make test-cov        # with coverage report
make test-slow       # network-heavy Makefile smoke
make test-agent-e2e  # agent UI e2e + env pack (-m agent_e2e; PYTEST_ARGS overrides)
```

Agent UI e2e (in-process offscreen harness) is documented in
[agent_e2e.md](agent_e2e.md). The reusable env pack model (seed, isolation,
fixture areas) is in [agent_e2e_env.md](agent_e2e_env.md). CI runs the pack via
`make test-agent-e2e` in job `agent-e2e` (PYPOST-861); the main fast suite also
includes those tests under `-m "not slow"`. That path is separate from live MCP
checks against a running PyPost (see § Testing via MCP below and
[mcp_integration.md](mcp_integration.md)).

Pass extra pytest arguments via `PYTEST_ARGS` (PYPOST-791). When set, `PYTEST_ARGS`
**replaces** the default path/marker arguments for that target; when unset, behavior is
unchanged.

```bash
make test PYTEST_ARGS="tests/test_mcp_server_manager.py -q"
make test PYTEST_ARGS="-k test_format_mcp_bind_error"
make test-cov PYTEST_ARGS="--cov=pypost.core.qt.mcp_server tests/test_mcp_server_manager.py"
make test-agent-e2e PYTEST_ARGS="tests/test_agent_golden_e2e.py -v"
```

See § Reproducible test environment, § Per-test timeouts, § CI guardrails, and § Makefile
automation tests below.

## Reproducible test environment (PYPOST-465)

Use this checklist on a **clean checkout** to match CI regression coverage locally.

| Step | Command / detail |
| --- | --- |
| **Python** | 3.11+ recommended ([README](../../README.md)); CI matrix runs **3.11** and **3.13** |
| **Install** | `make install` — creates `.venv`, runs `pip install -e ".[dev,otel]"` |
| **Fast regression** | `make test` — full suite except `-m slow` |
| **Slow smoke** | `make test-slow` — Makefile install smoke (`tests/test_makefile.py`) |
| **Coverage** | `make test-cov` — fast suite with `--cov=pypost` |
| **CI parity** | Main job (`.github/workflows/test.yml`) installs `pip install -e ".[dev,otel]"` |

`run`, `test`, and `lint` do not auto-install dependencies — run `make install` first after
clone or Python version change. See [setup.md](setup.md).

### Local vs CI test parity troubleshooting (PYPOST-723)

CI (`.github/workflows/test.yml`) runs on **Ubuntu** with a **Python 3.11 / 3.13 matrix**.
Local development on **macOS** commonly uses a newer system Python (e.g. 3.14.x via Homebrew),
which can surface differences that don't reproduce in CI or vice versa.

| Symptom | Cause | Fix |
| --- | --- | --- |
| `test_makefile.py` fails locally but passes in CI (or vice versa) | `make` subprocess spawns with the system `python3`/`PYTHON` default, which may differ from the interpreter running pytest | Tests pass `PYTHON={sys.executable}` explicitly to `make` invocations (PYPOST-718) — if you add a new Makefile integration test, do the same |
| Qt/PySide6 import errors or segfaults on Linux only | CI runner image lacks EGL/XCB/fontconfig shared libraries that are preinstalled on macOS | `.github/workflows/test.yml` installs `libegl1`, `libxcb-cursor0`, `libxkbcommon0`, etc. before running tests — see the "Install Qt / EGL runtime" step |
| A test passes locally on Python 3.14 but fails on CI's 3.11/3.13 | Newer Python stdlib/typing behavior not yet exercised by the CI matrix | Install a matching interpreter locally with `pyenv install 3.11` / `3.13` and re-run `make test` under that version before assuming a CI-only bug |
| Coverage differs slightly between local and CI runs | `--cov-fail-under` threshold (70%) is enforced identically, but conditional imports (e.g. platform-specific branches like `sys.platform == "win32"` in `curl_generator.py`) only execute on the OS where the branch is true | Don't chase 100% parity on OS-gated branches; rely on the CI matrix as the source of truth for the threshold gate |
| macOS-only Qt segfault during a specific GUI test | Rare; not reproducible on Linux CI | Run the failing module in isolation (`pytest tests/test_x.py -v`) to confirm it's environment-specific before filing a bug — see `doc/dev/test_audit.md` § Local vs CI |

**Quick parity check before debugging a "works locally, fails in CI" report:**

1. Confirm Python version: `python3 --version` locally vs the matrix entries in
   `.github/workflows/test.yml` (`strategy.matrix.python-version`).
2. Re-run with `QT_QPA_PLATFORM=offscreen` set explicitly (CI always sets this; local shells
   may not).
3. Run `make test` (not a bare `pytest` invocation) so Makefile-driven env setup matches CI's
   `python -m pytest tests/ ...` invocation.

### AI-assisted verification (supplementary)

PyPost can also be exercised by the AI assistant in Cursor using the embedded MCP server and
Prometheus metrics when validating UI flows manually.

## Prerequisites

- **PyPost running** — `make run` or `python -m pypost.main`
- **MCP enabled** — in Manage Environments, check "Enable MCP Server"
- **Cursor connected** — add MCP server URL `http://<host>:1080/mcp` (Streamable HTTP).
  Legacy SSE clients may still use `http://<host>:1080/sse/`.
- **Host** — use the host from PyPost settings (e.g. `localhost`, `dev.int`)

## Testing via MCP

The AI calls MCP tools (requests with "MCP Tool" checked) and verifies responses.
See [do-testing.md](../../.cursor/lsr/do-testing.md) for the full procedure.

For **in-process agent UI e2e** (offscreen Qt harness, no live MCP server), use
`make test-agent-e2e` and [agent_e2e.md](agent_e2e.md) instead.

## Verification via Prometheus

Metrics: `http://<host>:9080/metrics/` (host from settings, default port 9080).

Key metrics for MCP testing:

| Metric | Labels | Description |
|--------|--------|--------------|
| `mcp_requests_received_total` | `method` | MCP tool invocations |
| `mcp_responses_sent_total` | `method`, `status` | MCP responses (success/error) |
| `requests_sent_total` | `method` | HTTP requests sent |
| `responses_received_total` | `method`, `status_code` | HTTP responses received |
| `request_retry_exhaustions_total` | `endpoint` | Outbound HTTP retries exhausted (PYPOST-443) |

## GUI / Qt widget tests

PyPost runs Qt tests headlessly with `QT_QPA_PLATFORM=offscreen` and a module-scoped `qapp`
fixture (`tests/conftest.py`). The project does not use the `pytest-qt` package; tests call
widget methods and assert on labels, models, and mocked dialogs. Plain pytest tests take
`qapp` as a parameter (including gateway / H3 stress modules after PYPOST-885);
`unittest.TestCase` Qt modules use `@pytest.mark.usefixtures("qapp")` instead of
module-local `setUpClass` `QApplication` or a duplicate local `def qapp()`
(PYPOST-830 / PYPOST-884 / PYPOST-886). Suite inventory guard:
`tests/test_suite_qapp_alignment.py`; gateway free-function style guard:
`tests/test_gateway_qapp_free_function_style.py` — see
[gui_testing.md](gui_testing.md) § Shared `qapp`.

For bounded event-loop polling (e.g. waiting for Qt signals while a background server starts),
use `wait_until` from `tests/helpers/qt_wait.py` (re-exports
`pypost.agent.ui_wait.wait_until`; PYPOST-727 / PYPOST-837). Agent settle helpers
(`wait_for_widget` / `enabled` / `text` / `snapshot`) live in
[ui_wait.md](ui_wait.md). For TCP listen readiness, use
`wait_for_port` from `tests/helpers/mcp_live_server.py`.

When a test must nest `QEventLoop.exec()` to deliver `QThread` queued signals, do **not** rely
on a QTimer-only timeout or on `pytest-timeout` SIGALRM alone — SIGALRM does not interrupt a
stuck C++ `exec()` without Python callbacks. Use the shared
`tests.helpers.process_until.process_until` helper (wall-clock deadline plus a daemon
`threading.Timer` that posts `QTimer.singleShot(0, loop, loop.quit)` onto the GUI thread;
PYPOST-823 / PYPOST-827). On timeout, the message is neutral and can include a lazy
`timeout_detail` snapshot (busy/pending / worker — PYPOST-828). Full contract and
troubleshooting: [gui_testing.md](gui_testing.md) § Bounded nested `QEventLoop` waits.

See [gui_testing.md](gui_testing.md) for patterns, representative modules, focused commands,
and troubleshooting (including ELF core dumps from native Qt crashes —
[PYPOST-429](../../ai-tasks/PYPOST-429/investigation-report.md)).

Unit testability seams for `RequestService`, `HTTPClient`, and `MainWindow` are documented in
[testability.md](testability.md) (PYPOST-382).

ResponseView search bar coverage (PYPOST-365):

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_response_view_search.py -v
```

RequestWidget GUI action metrics (PYPOST-170): Send click and Save/Save As/Copy cURL entry
points increment Prometheus counters; tests inject `MetricsManager` and scrape the registry.

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_request_editor_gui_metrics.py -v
```

## Response search flow integration (PYPOST-357)

RequestTab-level wiring tests load a response via `display_response`, then drive search through
widget signals and controls (type, Next button, Enter). Unit-level ResponseView behavior remains in
`tests/test_response_view_search.py`.

| Module | Scope |
| --- | --- |
| `tests/test_response_search_flow_integration.py` | Tab → ResponseView search after response display |

Focused run:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_response_search_flow_integration.py -v
```

## MCP server unit tests

Automated pytest coverage for `MCPServerImpl` and Starlette routing lives in
`tests/test_mcp_server_impl.py` (PYPOST-367). Tests mock `RequestService` and avoid live
transport handshakes; routing cases assert `/mcp` and legacy `Mount("/sse")` structure.

Legacy SSE module tests in `tests/test_mcp_legacy_sse.py` (PYPOST-156, PYPOST-158) cover
`build_legacy_sse_app()` structure, SSE GET closure (`Response()` after mocked transport
teardown), and 405 guards for wrong methods on the inner stream (`GET /`) and messages
(`POST /messages`) paths, including the mounted `/sse` prefix.

ASGI compatibility tests in `tests/test_mcp_asgi_compatibility.py` (PYPOST-161) assert
Starlette registers legacy SSE `MessagesEndpoint`, Streamable HTTP `/mcp`, and metrics
`/metrics` mount as direct ASGI (not `request_response` wrappers), and that POST
`/messages` completes without `TypeError` when the transport is mocked.

| Class | Scope |
| --- | --- |
| `TestMCPServerImpl` | Tool registration, schemas, `call_tool`, metrics, script output |
| `TestMCPServerImplRouting` | `create_app()` route structure and method guards |
| `TestMCPServerImplInjection` | Constructor `TemplateService` injection |
| `TestMcpLegacySseModule` | Module-level endpoint imports and route structure |
| `TestMcpLegacySseHttpGuards` | SSE close contract and 405 method guards (PYPOST-158) |
| `TestLegacySseAsgiCompatibility` | Direct ASGI on `/messages`; POST without TypeError (PYPOST-161) |
| `TestStreamableHttpAsgiCompatibility` | Direct ASGI on `/mcp` for MCP and metrics apps (PYPOST-161) |
| `TestMetricsServerAsgiCompatibility` | `/metrics`, `/mcp`, `/sse` mount structure and scrape (PYPOST-161) |
| `TestMcpServerAsgiCompatibility` | MCP app Streamable HTTP + legacy SSE ASGI routes (PYPOST-161) |

Focused run:

```bash
.venv/bin/python -m pytest tests/test_mcp_server_impl.py tests/test_mcp_legacy_sse.py \
  tests/test_mcp_asgi_compatibility.py -v
```

## MCP server integration tests

Live Streamable HTTP round-trip coverage (tool list + call against a running uvicorn server)
lives in `tests/test_mcp_server_integration.py` (PYPOST-368, PYPOST-551). Tests use the
official MCP Python SDK (`streamable_http_client`, `ClientSession`) with `anyio.run`, start
the server on an ephemeral port, and mock `RequestService.execute` for deterministic output.

| Class | Scope |
| --- | --- |
| `TestMCPServerIntegration` | `list_tools`, `call_tool`, MCP argument forwarding, and `MCPClientService` sync wrapper (PYPOST-560) |
| `TestMCPServerManagerIntegration` | `MCPServerManager` thread + uvicorn lifecycle |

Focused run:

```bash
.venv/bin/python -m pytest tests/test_mcp_server_integration.py -v
```

## MCP test fixture generator (PYPOST-179)

Committed MCP test artifacts are defined in code and written by
`scripts/generate_mcp_test_fixtures.py` (builders in `pypost/fixtures/mcp_test_fixtures.py`).
Regenerate after changing fixture definitions; use `--check` to fail when committed JSON drifts
from the canonical models.

```bash
.venv/bin/python scripts/generate_mcp_test_fixtures.py
.venv/bin/python scripts/generate_mcp_test_fixtures.py --check
```

Focused tests: `tests/test_generate_mcp_test_fixtures.py`.

## MCP test collection groundwork (PYPOST-180)

Committed manual-test artifacts under `examples/collections/mcp.json` and
`config/test/environments.json` are validated in CI without starting a live MCP server.
Shared loaders live in `tests/helpers/mcp_test_collection.py` for reuse by
[PYPOST-181](https://pypost.atlassian.net/browse/PYPOST-181) integration tests.

| Module | Scope |
| --- | --- |
| `tests/helpers/mcp_test_collection.py` | Repo paths, constants, `load_mcp_test_collection()` |
| `tests/test_mcp_test_collection.py` | Model parse, MCP tool overview, contract previews, env flags |

Assertions include expected exposed tools (`sse_probe_metrics`, `sse_probe_main`), List Tools
not exposed as an MCP tool, and MCP Test environment `enable_mcp: true`. Doc URL consistency
remains in `tests/test_mcp_user_docs.py` (PYPOST-552).

Focused run:

```bash
.venv/bin/python -m pytest tests/test_mcp_test_collection.py -v
```

## MCP test collection integration (PYPOST-181)

Live Streamable HTTP round-trip tests load exposed tools from the committed MCP test
collection (`examples/collections/mcp.json`) via `tests/helpers/mcp_test_collection.py`.
The harness starts `MCPServerImpl` on an ephemeral port and uses the official MCP Python SDK
(`list_tools`, `call_tool`). Upstream HTTP is mocked through `RequestService` for CI
determinism — same pattern as `tests/test_mcp_server_integration.py`.

| Module | Scope |
| --- | --- |
| `tests/helpers/mcp_test_collection.py` | `mcp_exposed_requests()` plus PYPOST-180 loaders |
| `tests/test_mcp_test_collection_integration.py` | Live `list_tools`, per-tool `call_tool`, request forwarding |

Assertions include expected tool names (`sse_probe_metrics`, `sse_probe_main`), structured
JSON envelopes on `call_tool`, and that the correct collection `RequestData` is passed to
`RequestService.execute`.

Focused run:

```bash
.venv/bin/python -m pytest tests/test_mcp_test_collection_integration.py -v
```

## MCP and metrics test coverage

PYPOST-370 closed the PYPOST-38 debt item for automated MCP tools and metrics tests as
duplicate scope: prior tickets already cover the intent.

| Concern | Module | Level | Notes |
| --- | --- | --- | --- |
| MCP tool Streamable HTTP (`list_tools`, `call_tool`) | `tests/test_mcp_server_integration.py` | Integration | PYPOST-368/551; `RequestService` mocked |
| MCP test collection live round-trip | `tests/test_mcp_test_collection_integration.py` | Integration | PYPOST-181; collection tools, `RequestService` mocked |
| `MCPServerImpl` metrics hooks | `tests/test_mcp_server_impl.py` | Unit | PYPOST-367; `MetricsManager` mocked |
| Metrics `read_resource("metrics://all")` | `tests/test_metrics_manager.py` | Unit | Facade; scrapes `mcp_*_total` after `read_resource` |
| `MetricsRegistry` MCP counters | `tests/test_metrics_registry.py` | Unit | PYPOST-177; pure `track_mcp_*` scrape assertions |
| HTTP `/metrics` scrape endpoint | `tests/test_metrics_server_endpoint.py` | Unit | PYPOST-177; `TestClient` on `MetricsServer` ASGI app |
| `MetricsServer` MCP resource counters | `tests/test_metrics_server_endpoint.py` | Unit | PYPOST-177; success, unknown URI, scrape error paths |
| Shared bind error messages | `tests/test_server_bind.py` | Unit | PYPOST-154; `format_bind_error` / MCP wrapper |
| Metrics server bind / startup signaling | `tests/test_metrics_server_startup.py` | Integration | PYPOST-153; port busy, deferred failure |
| Live HTTP `/metrics` scrape after uvicorn start | `tests/test_metrics_server_integration.py` | Integration | PYPOST-169; real socket bind + urllib GET |
| Live metrics MCP resource round-trip | `tests/test_metrics_server_integration.py` | Integration | PYPOST-563; Streamable HTTP and SSE |
| RequestWidget GUI action counters | `tests/test_request_editor_gui_metrics.py` | Integration | PYPOST-170; Send click + Save/Copy cURL scrape |
| MCP server bind / startup signaling | `tests/test_mcp_server_manager.py` | Integration | PYPOST-556; port busy, listen readiness |
| MCP and metrics bind host fidelity | `tests/test_server_bind_host_integration.py` | Integration | PYPOST-150; `127.0.0.1`, `0.0.0.0`, `localhost`, `::1` |

PYPOST-154 verified end-to-end port-in-use handling for both MCP and metrics (closes
PYPOST-20 bind-error debt). Implementation is in PYPOST-556 and PYPOST-153; 154 adds shared
helper tests and documentation.

To prevent native thread-termination crashes and segmentation faults on macOS under Python 3.11+
(tracked in PYPOST-429), the port-busy test cases in `test_metrics_server_startup.py` and
`test_mcp_server_manager.py` are stabilized (PYPOST-716) by using `unittest.mock.patch` to mock
`uvicorn.Server.serve` raising `OSError(errno.EADDRINUSE, ...)`. This avoids uvicorn's complex socket
bind and background thread exit cleanup, while still fully exercising the manager's custom
error signaling and status transition logic.

Not covered by the above (follow-up debt): integration tests with real outbound HTTP via a
local stub server for request execution paths.

Focused metrics HTTP integration run:

```bash
.venv/bin/python -m pytest tests/test_metrics_server_integration.py::TestMetricsServerHttpIntegration -v
```

Focused metrics MCP resource run:

```bash
.venv/bin/python -m pytest tests/test_metrics_manager.py::TestMetricsManagerMcpResource -v
```

PYPOST-177 component-level metrics tests:

```bash
.venv/bin/python -m pytest tests/test_metrics_registry.py tests/test_metrics_server_endpoint.py -v
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
`timeout` marker. [`pyproject.toml`](../../pyproject.toml) `[tool.pytest.ini_options]` registers
the marker; `pytest-timeout` is installed via `make venv-test`. There is no global default in
`pyproject.toml` — each test module,
class, or function must declare its own timeout.

```bash
make test
```

### Strict markers (PYPOST-865)

Default pytest `addopts` includes `--strict-markers`. Unknown custom markers fail
collection with a usage error. Local `make test` / `make test-cov` /
`make test-agent-e2e` and CI inherit the same flag from
`pyproject.toml` — do **not** duplicate `--strict-markers` in workflow YAML.

Registered custom markers today:

| Marker | Purpose |
| ------ | ------- |
| `timeout(seconds)` | Per-test timeout (mandatory; see above) |
| `slow` | Network-heavy / slow integration (excluded from default CI) |
| `agent_e2e` | Agent UI e2e / env-pack scenarios (`make test-agent-e2e`) |

When adding a new custom marker, register it under
`[tool.pytest.ini_options] markers` in `pyproject.toml` in the same change.
Built-in markers (`parametrize`, `usefixtures`, …) do not need registration.
Regression guard: `tests/test_pytest_strict_markers.py` (flag in `addopts` +
required markers registered).

```bash
make test PYTEST_ARGS="tests/test_pytest_strict_markers.py -v"
```

#### Troubleshooting

- **Unknown marker / usage error on collection** — typo or unregistered
  custom mark. Fix the name, or register it under `markers` in
  `pyproject.toml`.
- **Guard fails: missing `--strict-markers`** — restore
  `"--strict-markers"` in `[tool.pytest.ini_options]` `addopts`.
- **Guard fails: missing marker name** — re-add `timeout`, `slow`, or
  `agent_e2e` to the `markers` list.

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

## Core manager unit tests (PYPOST-252, PYPOST-251)

Automated unit coverage for `RequestManager` and `StateManager` (debt follow-up from
[PYPOST-29](https://pypost.atlassian.net/browse/PYPOST-29)).
[PYPOST-251](https://pypost.atlassian.net/browse/PYPOST-251) closed the original blocker
(missing pytest setup); [PYPOST-252](https://pypost.atlassian.net/browse/PYPOST-252) added
manager tests and this section. Pytest infrastructure (`pyproject.toml`, `Makefile`,
`tests/conftest.py` timeout gate) is the standard entry point for local and CI runs.

| Module | Test file | Scope |
| --- | --- | --- |
| `RequestManager` | `tests/test_request_manager.py` | Create, save, find, reload, get, index consistency |
| `RequestManager` | `tests/test_request_manager_delete.py` | Delete, rename, routing, validation edge cases |
| `StateManager` | `tests/test_settings_persistence.py` | Persistence, no-op saves, coalescing, debounce, flush |

Patterns:

- **RequestManager** — `FakeStorageManager` from `tests/helpers/__init__.py` (in-memory
  collections; no filesystem I/O).
- **StateManager** — isolated config directory via
  `patch("pypost.core.config_manager.user_config_dir")`; debounce tests use `QTest.qWait(350)`
  with the module `qapp` fixture.

Focused run:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_request_manager.py \
  tests/test_request_manager_delete.py \
  tests/test_settings_persistence.py::TestStateManagerPersistence \
  tests/test_settings_persistence.py::test_state_manager_debounced_save_persists_after_timer \
  -v --cov=pypost.core.request_manager --cov=pypost.core.qt.state_manager --cov-report=term-missing
```

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
| Enforcement | `--cov-fail-under=70` in `pyproject.toml` `[tool.pytest.ini_options]` `addopts` |
| CI summary display | `THRESHOLD=70` in `.github/workflows/test.yml` |
| Project target | 70% (follow-up when ready) |

Audit current coverage:

```bash
make test-cov
```

Look for `TOTAL ... XX%` and `Required test coverage of 60% reached` in the output. To raise
the threshold, update both `pyproject.toml` `[tool.pytest.ini_options]` and the `THRESHOLD`
variable in `test.yml` together.
See `ai-tasks/PYPOST-88/70-dev-docs.md` for the full procedure.

## Makefile automation tests

`tests/test_makefile.py` validates root `Makefile` contracts without touching the repository
`.venv`. Scope is split across two tasks to avoid duplicate fixtures:

| Task | Scope |
| ---- | ----- |
| [PYPOST-274] | Makefile marker lifecycle, dependency chains, exit codes |
| [PYPOST-277] | Smoke for `venv`, `install`, `test`, `lint` (closed with PYPOST-274) |
| [PYPOST-307] | Implementation slice: marker lifecycle, `make -p` chains, lint failure |
| [PYPOST-310] | Implementation slice: execution smoke for install/test/lint exit codes |
| [PYPOST-559] | Optional slow `make install` with real `pyproject.toml` in isolated workspace |
| [PYPOST-279] | Pytest exit code `5` (no tests collected) policy in `make test` and CI |
| [PYPOST-800] | Smoke for `make help` non-empty output (PYPOST-794 follow-up) |
| [PYPOST-861] | Smoke for `make test-agent-e2e` (deps, help, recipe, marker selection) |

[PYPOST-274]: https://pypost.atlassian.net/browse/PYPOST-274
[PYPOST-277]: https://pypost.atlassian.net/browse/PYPOST-277
[PYPOST-307]: https://pypost.atlassian.net/browse/PYPOST-307
[PYPOST-310]: https://pypost.atlassian.net/browse/PYPOST-310
[PYPOST-559]: https://pypost.atlassian.net/browse/PYPOST-559
[PYPOST-279]: https://pypost.atlassian.net/browse/PYPOST-279
[PYPOST-800]: https://pypost.atlassian.net/browse/PYPOST-800
[PYPOST-861]: https://pypost.atlassian.net/browse/PYPOST-861

| Area | What is checked |
| ---- | ---------------- |
| Marker lifecycle | `make venv` creates marker; `make clean` removes `.venv`; idempotent `venv` |
| Dependency chain | `install` depends on marker only; `test-cov` depends on marker + `venv-test` + `venv-otel` |
| Exit behavior | `clean`/`venv` succeed; unknown targets fail; bare venv fails `test`/`lint` |
| Target execution | Tools install; `install` succeeds; `test`/`lint` run; `make test` excludes slow |
| Slow install smoke | `make install` with real `pyproject.toml` succeeds; marked `@pytest.mark.slow` |
| Help output | `make help` exits 0 and prints non-empty stdout (PYPOST-800) |
| Agent e2e target | deps (`venv-otel`), help listing, recipe marker, selection smoke (861) |

### Python interpreter decoupling (PYPOST-718)

To ensure Makefile integration tests are robust and decoupled from system-level environment
differences, all test-spawns of `make` explicitly override the `PYTHON` variable with the active
interpreter executing the tests (i.e., `PYTHON=sys.executable`). This forces `make` to create
the virtual environment and markers with the exact matching Python version, preventing version
mismatch failures in environments where the system-default `python3` differs from the `pytest`
runner's interpreter.

Each case runs GNU Make in an isolated `tmp_path` with a copied `Makefile`, minimal
`tests/test_noop.py`, and `pypost/__init__.py`. Focused run:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_makefile.py -v
```

Slow install smoke (network-heavy; excluded from default `make test` and main CI job):

```bash
make test-slow
# or
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_makefile.py -m slow -v
```

CI runs fast tests on every push/PR (Python 3.11 and 3.13). Default pytest
(`pyproject.toml` `[tool.pytest.ini_options]` `addopts`) and `make test` exclude `-m slow`. A
separate `make-install-smoke` job in
`.github/workflows/test.yml` runs `-m slow` Makefile tests on Python 3.11.
Job `agent-e2e` runs `make install && make test-agent-e2e` on Python 3.11
(PYPOST-861 env-pack make gate; see [agent_e2e.md](agent_e2e.md)).

## CI dependency caching (PYPOST-311)

Both CI jobs use `actions/setup-python@v5` with `cache: pip` and an explicit
`cache-dependency-path` listing `pyproject.toml`, `requirements.in`, `requirements.txt`,
`requirements-dev.in`, and `requirements-dev.txt`. The cache stores downloaded pip wheels under
the runner home directory and restores them before dependency installation.

| Aspect | Behavior |
| --- | --- |
| **Cache key** | OS + Python version + SHA-256 hash of `pyproject.toml` and all four requirements files |
| **Invalidation** | Any edit to a lock or source file produces a new key (cold install) |
| **Scope** | Main `test` matrix (3.11, 3.13), `make-install-smoke` (3.11), `agent-e2e` (3.11), `security-audit`, `check-license-inventory`, and `check-lock-dev` |
| **Local dev** | `make install` uses Makefile `.venv`; GitHub cache applies to CI only |

The slow install smoke runs `make install` in an isolated `tmp_path` workspace; pip still
reuses cached wheels from the restored `~/.cache/pip` on the runner.

Verify cache behavior in the GitHub Actions log for the `setup-python` step (`Cache hit` /
`Cache miss`). First run after a dependency change is expected to miss and download fresh wheels.

## CI lock verification (PYPOST-804)

The `check-lock-dev` job in `.github/workflows/test.yml` installs [uv](https://docs.astral.sh/uv/)
and runs `make check-lock-dev` once per workflow. It fails when `requirements-dev.txt` is stale
relative to `requirements-dev.in` (same check as local maintainer workflow in
[setup.md](setup.md) § Development dependency lock file).

| Job | Input | Tool |
| --- | --- | --- |
| `check-lock-dev` | `requirements-dev.in` → `requirements-dev.txt` | `uv pip compile` via Makefile |

Production lock verification (`make check-lock`) remains local-only until a sibling CI job is
added; dev lock drift is now gated in CI because test tooling installs from `pyproject.toml`
`[dev]` extra (PYPOST-806).

## CI dependency CVE scan (PYPOST-778, PYPOST-805, PYPOST-806)

The `security-audit` job installs dev tooling via `pip install -e ".[dev]"` (includes pinned
`pip-audit`), then runs `pip-audit -r requirements.txt` once per workflow on Python 3.11. Local
parity: `make security-audit` after `make install` (PYPOST-805 removed inline `pip install
pip-audit` from Makefile and CI).

See [dependencies_audit.md](dependencies_audit.md) § CVE Scanning for ignore-vuln policy.

## CI transitive license inventory (PYPOST-809)

The `check-license-inventory` job installs dev tooling via `pip install -e ".[dev]"` (includes
pinned `pip-licenses`), then runs `python scripts/generate_license_inventory.py --check` once per
workflow on Python 3.11. Local parity: `make check-license-inventory` after `make install`.

Regenerate committed output after production lock changes:

```bash
make generate-license-inventory
```

See [licensing.md](licensing.md) § Transitive license inventory.

## Pytest exit codes (PYPOST-279)

Pytest uses distinct exit codes. PyPost treats them as follows in `make test` and CI (native
propagation — no Makefile wrapper maps codes to success):

| Code | Meaning | CI / `make test` |
| --- | --- | --- |
| `0` | All tests passed | Success |
| `1` | Tests failed | Failure |
| `2` | User interrupt | Failure |
| `3` | Internal error | Failure |
| `4` | pytest usage error | Failure |
| `5` | No tests collected | **Failure** (default) or **Warning** (if configured) |

### Empty Tests Policy (`empty_tests_policy`)

To prevent false-positive CI/CD pipeline failures in empty-test repositories, templates, or newly
initialized projects, PyPost supports configuring the policy for handling pytest exit code `5`
(no tests collected) via the `empty_tests_policy` option in `pyproject.toml`
`[tool.pytest.ini_options]`.

#### Supported Policies

- `fail` (default): Exit code `5` is treated as a hard failure, causing the build or test run to
  fail. This is the recommended setting for mature repositories to prevent accidental deletion
  of tests or silent test suite bypasses due to misconfiguration.
- `warn` / `warning` / `ignore_and_warn`: Exit code `5` is intercepted and rewritten to `0`
  (success), but a highly visible warning message is printed to stderr/stdout and logged via
  Python's logging system to notify developers that no tests were executed. This is the
  recommended setting for empty-test or template repositories.

#### Configuration Example

In `pyproject.toml`:

```toml
[tool.pytest.ini_options]
empty_tests_policy = "warn"
```

Regression coverage: `tests/test_pytest_exit_policy.py`.

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_pytest_exit_policy.py -v
```

## Pytest live logging (`log_cli`) (PYPOST-570)

See [observability_audit.md — Test and CI Logging](observability_audit.md#test-and-ci-logging)
for the audit summary table (local vs CI `log_cli`, guardrail baseline 72 + margin 5).

`pyproject.toml` `[tool.pytest.ini_options]` enables live application logs during test runs:

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

1. **Keep** `pyproject.toml` defaults for local runs (helps correlate logs with failing tests).
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

A green `make test` run can still emit many ERROR/WARNING lines because `pyproject.toml`
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

## SOLID audit baseline (PYPOST-376)

PYPOST-40 identified maintainability risks but did not define numeric regression thresholds.
PYPOST-376 records LOC baselines and caps for audit-scoped modules (especially
`main_window.py` and presenters).

```bash
# Regenerate human-readable snapshot
.venv/bin/python scripts/audit_baseline_metrics.py \
  --markdown ai-tasks/PYPOST-376/baseline-metrics.md

# Fail if any cap exceeded
.venv/bin/python scripts/audit_baseline_metrics.py --check

# CI regression tests
pytest tests/test_solid_audit_baseline.py -v
```

Baseline date: **2026-06-11**. Audit-era vs current vs cap table:
[ai-tasks/PYPOST-376/baseline-metrics.md](../../ai-tasks/PYPOST-376/baseline-metrics.md).
See also [solid_audit.md](solid_audit.md#regression-baseline-metrics-pypost-376).

## Dialog audit inventory (PYPOST-374)

PYPOST-374 adds a per-dialog SOLID audit and a regression guard so new files under
`pypost/ui/dialogs/` are not omitted from the audit report.

```bash
# List dialog modules and LOC
.venv/bin/python scripts/audit_dialogs_inventory.py --markdown

# Fail if 30-dialogs-audit-report.md missing a module filename
.venv/bin/python scripts/audit_dialogs_inventory.py --check

pytest tests/test_dialogs_audit.py -v
```

Report: [ai-tasks/PYPOST-374/30-dialogs-audit-report.md](../../ai-tasks/PYPOST-374/30-dialogs-audit-report.md).
See also [solid_audit.md](solid_audit.md#individual-dialog-audit-pypost-374).

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
| `tests/test_worker.py` | 1 | `pypost.core.qt.worker` |

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
listed in the audit report. Agent rules (C1–C5): `.cursor/lsr/do-testing.md` § Error-path
logging. Example retrofit: `tests/test_worker.py::test_worker_wraps_unexpected_exception_logs_error`.

## CI guardrails (PYPOST-571 / PYPOST-572)

Enforceable CI gates so green runs cannot hide unexpected ERROR storms or timeout-boundary
passes. Full design: `ai-tasks/PYPOST-571/ci-guardrails-proposal.md`.

| Pillar | Summary |
| --- | --- |
| **Log allowlist** | `tests/expected_log_allowlist.yaml` — permit baseline ERROR prefixes from PYPOST-567; fail on unlisted lines |
| **`caplog` contract** | Error-path tests assert logs via `caplog` **or** register prefix in allowlist; behavioral assertions remain primary |
| **Duration budget** | Warn when test duration >80% of `pytest.mark.timeout`; fail at >95% (PYPOST-569) |
| **Post-run script** | `scripts/verify_test_log_guardrails.py` parses captured pytest log after run; wired in CI after pytest |

### Phase 1 — log allowlist + verifier (PYPOST-572)

After pytest in `.github/workflows/test.yml`, CI captures stdout/stderr to `pytest.log` and runs:

```bash
python scripts/verify_test_log_guardrails.py pytest.log
```

The verifier reuses `parse_log` from `scripts/parse_test_log_inventory.py`. It:

1. Parses live-log lines (`HH:MM:SS LEVEL logger: message`) from the capture.
2. Matches each **ERROR** against `tests/expected_log_allowlist.yaml` rules:
   - **Logger + prefix:** both must match (e.g. `pypost.core.request_service` +
     `request_execution_failed`).
   - **Prefix only:** `message_prefix` matches any logger (for shared event names).
3. **Fails** when any ERROR line is unlisted.
4. **Fails** when total ERROR count exceeds `baseline_error_count + error_margin`
   (baseline **72**, margin **5** from PYPOST-567).

Local reproduction:

```bash
make test 2>&1 | tee tests.txt
.venv/bin/python scripts/verify_test_log_guardrails.py tests.txt
```

When adding an intentional error-path test that emits a new ERROR pattern, add a rule to
`tests/expected_log_allowlist.yaml` in the same PR. Prefer structured event prefixes
(`request_execution_failed`, `mcp_operation_failed`, etc.) over raw message substrings.

### Per-test duration display (PYPOST-790)

The in-repo plugin `tests/_pytest_plugins/duration_report.py` (loaded via `tests/conftest.py`)
augments verbose pytest output:

- Each completed test line shows **call duration**: `PASSED [1.23s]` or `FAILED [450ms]`.
- After the session, a **top 5 slowest tests** block is printed (sorted by call duration).

This applies to `make test`, `pyproject.toml` pytest defaults, and CI. The existing `--durations=0`
section in `pytest-output.txt` is unchanged so `scripts/audit_test_durations.py` keeps working.

### Phase 2 — duration budget audit (PYPOST-573)

The main CI pytest run includes `--durations=0 --durations-min=1` (captured in
`pytest-output.txt` after PYPOST-671). After the log verifier:

```bash
python scripts/audit_test_durations.py pytest-output.txt
```

| Utilization | Action |
| --- | --- |
| ≥ 80% of `pytest.mark.timeout` | GitHub Actions `::warning` annotation |
| ≥ 95% | CI step fails (`exit 1`) |

Local reproduction:

```bash
make test 2>&1 | tee tests.txt
python scripts/audit_test_durations.py tests.txt
```

**Operational notes (PYPOST-569 follow-ups):**

- Re-run `scripts/parse_timeout_audit.py` when adding e2e/integration tests that may shift
  duration baselines (PYPOST-669).
- Monitor `tests/test_makefile.py` peak duration (~4.6s); consider a 45s timeout marker
  after a stable week if CI annotations persist (PYPOST-668).
- Optional verbose CI job: `--durations=10 --durations-min=5` on manual/workflow_dispatch runs
  (PYPOST-667).

Phase 2 caplog contract: [PYPOST-574](https://pypost.atlassian.net/browse/PYPOST-574).

### Documentation sync (PYPOST-371)

Agent timeout, Qt, caplog, and run commands in `.cursor/lsr/do-testing.md` must stay aligned
with the matching sections in this file. When either document changes testing policy, update
both in the same PR or file a Debt follow-up.

## References

- [observability_audit.md](observability_audit.md) — observability audit summary, Test and CI
  Logging (`log_cli` local vs CI, guardrail baseline)
- [gui_testing.md](gui_testing.md) — Qt offscreen setup, `qapp` fixture, GUI test patterns
- [.cursor/lsr/do-testing.md](../../.cursor/lsr/do-testing.md) — AI assistant rules
- [MCP Integration](mcp_integration.md) — MCP setup
- [Collection item delete](collection_item_delete.md) — delete flow and metric matrix
- [pypost/core/metrics_registry.py](../../pypost/core/metrics_registry.py) — counter definitions
- [pypost/core/metrics.py](../../pypost/core/metrics.py) — `MetricsManager` facade
