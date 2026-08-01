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
make test-agent-e2e  # broader agent e2e beyond golden (primary packaging)
```

`make test-agent-e2e` is the **primary packaging** path for the **broader**
agent e2e pack **beyond golden** (PYPOST-922). Agent UI e2e (in-process
offscreen harness) is documented in [agent_e2e.md](agent_e2e.md). The reusable
env pack model (seed, isolation, fixture areas) is in
[agent_e2e_env.md](agent_e2e_env.md). CI runs the pack via `make test-agent-e2e`
in job `agent-e2e` (PYPOST-861); the main fast suite also includes those tests
under `-m "not slow"`. That path is separate from live MCP checks against a
running PyPost (see § Testing via MCP below and
[mcp_integration.md](mcp_integration.md)).

Pass extra pytest arguments via `PYTEST_ARGS` (PYPOST-791). When set, `PYTEST_ARGS`
**replaces** the default path/marker arguments for that target; when unset, behavior is
unchanged. Use it to narrow to the golden scenario (`test_agent_golden_e2e.py`)
or another single module without replacing the broader primary packaging entry:

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

### Install-first vs auto `venv-test` (PYPOST-872 / PYPOST-905)

**Preferred after clone / Python version change:** run `make install` once
(`pip install -e ".[dev,otel]"` in a single editable install). That path also
touches the extra stamp files so later split prerequisites stay no-ops. CI
installs `[dev,otel]` before pytest the same way.

**Safety net:** `make test`, `make test-slow`, `make test-cov`, and
`make test-agent-e2e` depend on `venv-test` and `venv-otel`, so a bare
`.venv` (marker only) still gets `[dev]` + `[otel]` before pytest runs.
`lint` and `typecheck` also depend on `venv-test`, so a bare venv gets
`[dev]` (flake8 / mypy) before those targets run (PYPOST-906). `run`
stays marker-only — run `make install` before `make run` if the base
venv is incomplete. See [setup.md](setup.md).

**Stamp-gated extras (PYPOST-905):** `venv-test` and `venv-otel` are thin
aliases over version-aware stamp files under `.venv/`
(`.venv-test-<major.minor>`, `.venv-otel-<major.minor>`). Each stamp recipe
depends on the base venv marker and `pyproject.toml`. When the stamp is
current, Make skips pip; when the stamp is missing or older than
`pyproject.toml`, the recipe reinstalls the extra and refreshes the stamp.
`make clean` removes `.venv` (and stamps), so the next visit reinstalls.

### Local vs CI test parity troubleshooting (PYPOST-723)

CI (`.github/workflows/test.yml`) runs on **Ubuntu** with a **Python 3.11 / 3.13 matrix**.
Local development on **macOS** commonly uses a newer system Python (e.g. 3.14.x via Homebrew),
which can surface differences that don't reproduce in CI or vice versa.

| Symptom | Cause | Fix |
| --- | --- | --- |
| `test_makefile.py` fails locally but passes in CI (or vice versa) | `make` subprocess spawns with the system `python3`/`PYTHON` default, which may differ from the interpreter running pytest | Tests pass `PYTHON={sys.executable}` explicitly to `make` invocations (PYPOST-718) — if you add a new Makefile integration test, do the same |
| Qt/PySide6 import errors or segfaults on Linux only | CI runner image lacks EGL/XCB/fontconfig shared libraries that are preinstalled on macOS | Jobs `test`, `make-install-smoke`, and `agent-e2e` invoke `.github/actions/install-qt-egl-runtime` (eight-package apt set in `action.yml` including `libegl1`, `libxcb-cursor0`, `libxkbcommon0`; PYPOST-923/924). Contract tests derive the expected set from that file only — no test-module frozenset (PYPOST-925) |
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
fixture (`tests/conftest.py`). Conftest sets the offscreen platform at import time but
**defers the PySide6 import until the `qapp` fixture runs** (PYPOST-926), so narrow
non-GUI collection paths that only load conftest do not require EGL/GL system libraries;
GUI test modules that import PySide6 at module level still do. Contract:
`tests/test_conftest_lazy_qt_import.py`. The project does not use the `pytest-qt` package; tests call
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
`pypost.agent.ui_wait.wait_until`; PYPOST-727 / PYPOST-837 / PYPOST-840). Agent
settle helpers
(`wait_for_widget` / `enabled` / `text` / `snapshot`) live in
[ui_wait.md](ui_wait.md). For TCP listen readiness, use
`wait_for_port` from `tests/helpers/mcp_live_server.py`.

To drive pytest **yield fixtures** outside a request (e.g. mocked packaging caplog proofs),
use `tests/helpers/fixture_drive.py` (`unwrap_yield_fixture`, `run_yield_fixture`,
`call_yield_fixture`; PYPOST-900). Private pytest unwrap (`_get_wrapped_function`) is isolated
there so upgrades touch one module. Consumer: `tests/test_agent_e2e_packaging_logs.py`.

Model-backed item views (`QTreeView`, `QListView`, etc.) must call `setModel(None)` before
closing isolated fixtures; otherwise Qt can emit teardown warnings or destabilize later
agent e2e sessions. Use `tests/helpers/qt_item_view.py` (`detach_item_view_model`,
`close_item_view_fixture`; PYPOST-940). Consumer: `tests/test_ui_actions.py` tree and
list-view ui_select fixtures; unit proofs in `tests/test_qt_item_view_teardown.py`.

Tree DisplayRole lookup for `ui_select` and `agent_e2e_tree` shares
`pypost/agent/tree_index.py` (`find_tree_index_by_display_text`; PYPOST-941).
Unit proofs in `tests/test_tree_index_walk.py` (deep nested row + error-type
boundaries).

List/tree negative `ui_select` paths (missing display text, out-of-range index)
are locked in `tests/test_ui_actions.py`
(`test_select_list_missing_option_raises`,
`test_select_list_index_out_of_range_raises`,
`test_select_tree_missing_option_raises`,
`test_select_tree_index_out_of_range_raises`; PYPOST-942), mirroring combo
`test_select_missing_option_raises`.

Fill DEBUG `ui_action_applied` scalars for default and opt-in keyClicks modes
are locked by parametrized `test_ui_action_applied_caplog` in the same module
(`via_key_clicks=false|true`; fill text must not appear in caplog; PYPOST-944).
Opt-in keyClicks fill on `QPlainTextEdit` and `QTextEdit` is locked by
`test_ui_fill_via_key_clicks_on_plain_text_fixture` and
`test_ui_fill_via_key_clicks_on_rich_text_fixture` (PYPOST-945).
Per-keystroke `textChanged` emission count on the line-edit keyClicks path is
locked by `test_ui_fill_via_key_clicks_emits_text_changed_per_keystroke`
(PYPOST-946; empty-start `QLineEdit` expects one emit per character).
Opt-in `delay` forwarding on the keyClicks path is locked by
`test_ui_fill_via_key_clicks_forwards_delay_kwarg` (PYPOST-947).

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
`mcp.json` is the local MCP/SSE probe fixture; the curated end-user Jira Cloud
pair and its import contract are covered separately under
[Example fixtures contract (PYPOST-1017)](#example-fixtures-contract-pypost-1017).

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

## Example fixtures contract (PYPOST-1017)

### Overview

Shipped importable fixtures under `examples/` are end-user / probe JSON only —
no application runtime change. A green contract test loads them through the
native import parsers and asserts parse success, placeholder markers, and
`hidden_keys`. Fixture inventory and import order for readers live in
[`examples/README.md`](../../examples/README.md).

### Architecture

| Artifact | Role |
| --- | --- |
| `examples/collections/jira_mcp.json` | Curated end-user Jira Cloud MCP collection |
| `examples/environments/jira_cloud.json` | Companion env (placeholders, hidden, MCP) |
| `examples/collections/mcp.json` | Local MCP/SSE probe (also PYPOST-180 helpers) |
| `tests/test_example_fixtures.py` | Import-parse + placeholder + `hidden_keys` |

Keep roles distinct: Jira pair for end users; `mcp.json` for contributors /
local probing.

### Usage

Focused contract run:

```bash
.venv/bin/python -m pytest tests/test_example_fixtures.py -v
```

### Configuration

No new env vars or settings. Committed fixtures must keep placeholders only
(sample site URL and `you@example.com:your-api-token`); never commit real
secrets. After import, substitute values locally and keep credential keys in
`hidden_keys`.

### Troubleshooting

| Issue | Resolution |
| --- | --- |
| Contract fails on placeholders | Keep sample URL/credentials in JSON; do not commit real tokens |
| Wrong fixture for a workflow | Use Jira pair for end users; `mcp.json` for local MCP/SSE probing |
| Import order unclear | See [`examples/README.md`](../../examples/README.md) (env first) |

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
| Product MCP catalog excludes ui_* tools | `tests/test_mcp_server_impl.py` | Unit | PYPOST-953; `list_tools` name guard vs agent sidecar |
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
`.venv`. Shared static parsers for `##` help lines and target recipe bodies live in
`tests/makefile_contract_helpers.py` (`makefile_target_help_comment`,
`makefile_target_recipe_body`) — use them when adding make-entry contract locks (PYPOST-937).
Unit coverage: `tests/test_makefile_contract_helpers.py`. Scope is split across two tasks to avoid duplicate fixtures:

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
| [PYPOST-872] | `venv-test` prerequisite on `test` / `test-slow` / `test-agent-e2e` |
| [PYPOST-873] | Deferred CI cost trim; dual-run docs + workflow lock |
| [PYPOST-907] | Evidence revisit; continued DEFER after CI duration evidence |
| [PYPOST-930] | ENABLE threshold revisit; continued DEFER (threshold not met) |
| [PYPOST-908] | Lock discoverable CI duration / overlap timing notes (cite 907) |
| [PYPOST-931] | Actions refresh script + Makefile target for overlap evidence |
| [PYPOST-874] | ENABLE agent-e2e failure artifact upload + doc/workflow lock |
| [PYPOST-909] | ENABLE main test matrix failure artifact upload + lock |
| [PYPOST-910] | Explicit `retention-days: 14` on failure artifact uploads |
| [PYPOST-911] | DEFER live Artifacts UI proof; procedure + doc lock |
| [PYPOST-928] | Shared `workflow_job_block` helper for CI workflow YAML contract tests |
| [PYPOST-905] | Stamp/cache `venv-test` / `venv-otel`; skip pip when extras current |
| [PYPOST-929] | Contract: `make install` touches both extra stamps |
| [PYPOST-906] | `lint` depends on `venv-test` (like `typecheck`); `run` stays marker-only |
| [PYPOST-932] | Contract: `typecheck` depends on marker + `venv-test` (peer lock) |
| [PYPOST-937] | Shared Makefile help/recipe parse helpers for make-entry contract locks |
| [PYPOST-938] | KEEP 873-style packaging doc locks; revisit criteria documented |
| [PYPOST-954] | Shared `packaging_doc_lock` helper; UI-action MCP packaging locks hardened |

[PYPOST-274]: https://pypost.atlassian.net/browse/PYPOST-274
[PYPOST-277]: https://pypost.atlassian.net/browse/PYPOST-277
[PYPOST-307]: https://pypost.atlassian.net/browse/PYPOST-307
[PYPOST-310]: https://pypost.atlassian.net/browse/PYPOST-310
[PYPOST-559]: https://pypost.atlassian.net/browse/PYPOST-559
[PYPOST-279]: https://pypost.atlassian.net/browse/PYPOST-279
[PYPOST-800]: https://pypost.atlassian.net/browse/PYPOST-800
[PYPOST-861]: https://pypost.atlassian.net/browse/PYPOST-861
[PYPOST-872]: https://pypost.atlassian.net/browse/PYPOST-872
[PYPOST-873]: https://pypost.atlassian.net/browse/PYPOST-873
[PYPOST-874]: https://pypost.atlassian.net/browse/PYPOST-874
[PYPOST-905]: https://pypost.atlassian.net/browse/PYPOST-905
[PYPOST-929]: https://pypost.atlassian.net/browse/PYPOST-929
[PYPOST-906]: https://pypost.atlassian.net/browse/PYPOST-906
[PYPOST-932]: https://pypost.atlassian.net/browse/PYPOST-932
[PYPOST-937]: https://pypost.atlassian.net/browse/PYPOST-937
[PYPOST-907]: https://pypost.atlassian.net/browse/PYPOST-907
[PYPOST-930]: https://pypost.atlassian.net/browse/PYPOST-930
[PYPOST-908]: https://pypost.atlassian.net/browse/PYPOST-908
[PYPOST-931]: https://pypost.atlassian.net/browse/PYPOST-931
[PYPOST-909]: https://pypost.atlassian.net/browse/PYPOST-909
[PYPOST-910]: https://pypost.atlassian.net/browse/PYPOST-910
[PYPOST-911]: https://pypost.atlassian.net/browse/PYPOST-911
[PYPOST-928]: https://pypost.atlassian.net/browse/PYPOST-928
[PYPOST-938]: https://pypost.atlassian.net/browse/PYPOST-938
[PYPOST-954]: https://pypost.atlassian.net/browse/PYPOST-954

| Area | What is checked |
| ---- | ---------------- |
| Marker lifecycle | `make venv` creates marker; `make clean` removes `.venv`; idempotent `venv` |
| Dependency chain | `install` depends on marker only; pytest targets depend on marker + `venv-test` + `venv-otel`; `lint` and `typecheck` depend on marker + `venv-test` (906/932); `run` marker-only |
| Extra stamps | Skip pip when stamp current; install when missing/stale; alias→stamp; stamp→marker+pyproject (905); `install` touches both stamps (929) |
| Exit behavior | `clean`/`venv` succeed; unknown targets fail; bare venv succeeds `lint` via `venv-test`; `make test` succeeds via `venv-test` |
| Target execution | Tools install; `install` succeeds; `test`/`lint` run; `make test` excludes slow |
| Slow install smoke | `make install` with real `pyproject.toml` succeeds; post-install pydantic + `pypost.version` sanity; marked `@pytest.mark.slow` |
| Slow smoke seed contract | Isolated workspace seed mirrors packaging metadata from committed `pyproject.toml` (dynamic version attr, readme), not only dependency pins (PYPOST-943) |
| Help output | `make help` exits 0 and prints non-empty stdout (PYPOST-800) |
| Agent e2e target | deps (`venv-test` + `venv-otel`), help listing, recipe marker, selection smoke (861/872) |

### Packaging doc lock strategy (PYPOST-922 / PYPOST-938 / PYPOST-954)

Packaging discoverability is guarded by **873-style substring / token locks**
— not structured doc schema or semantic asserts. Shared assertion helpers live
in `tests/helpers/packaging_doc_lock.py` ([PYPOST-954](https://pypost.atlassian.net/browse/PYPOST-954));
contract modules must import from that helper (locked by
`tests/test_packaging_doc_lock_helper.py`).

[PYPOST-938](https://pypost.atlassian.net/browse/PYPOST-938) assessed churn on
broader agent e2e locks since [PYPOST-922](https://pypost.atlassian.net/browse/PYPOST-922)
and chose **KEEP** substring strategy with documented revisit triggers.
[PYPOST-954](https://pypost.atlassian.net/browse/PYPOST-954) assessed UI-action
MCP packaging locks since [PYPOST-918](https://pypost.atlassian.net/browse/PYPOST-918)
(also low churn) and **HARDENED** via the shared helper when a second
doc-lock module made DRY pressure real (938 trigger #3).

| Module | Locked docs | Tokens (examples) |
| --- | --- | --- |
| `tests/test_agent_e2e_broader_packaging_doc.py` | `agent_e2e.md`, `agent_golden_e2e.md`, `testing.md` | `PYPOST-922`, `beyond golden`, `primary packaging`, `make test-agent-e2e`, `PYTEST_ARGS` |
| `tests/test_ui_actions_mcp_packaging_doc.py` | `ui_actions.md`, `mcp_integration.md`, `mcp_trust_model.md` | `PYPOST-918`, `out-of-process`, `packaging path`, `MCPServerImpl`, no-mix tuple (`never mount`, …) |
| `tests/test_makefile.py` (`TestAgentE2eTargetRecipe`, help cross-check) | Makefile `test-agent-e2e` | `broader`, `beyond golden`, marker default ≠ golden-only |

When editing locked prose, **preserve the tokens** above (case-insensitive
where the test uses `case_insensitive=True`). Rephrasing without tokens will
fail the contract suite — that is intentional for discoverability debt.

**Revisit / semantic HARDEN triggers** (open a new Debt story if **any two**
occur within one sprint):

1. ≥2 lock-test edits required **only** for prose rephrasing (not new
   packaging semantics) within 90 days.
2. ≥1 false failure from substring mismatch on an otherwise correct doc update.
3. A third packaging doc-lock module copies token blocks instead of extending
   `tests/helpers/packaging_doc_lock.py` (consider schema/section asserts only
   after helper DRY is exhausted).

Focused runs:

```bash
make test PYTEST_ARGS='tests/test_agent_e2e_broader_packaging_doc.py tests/test_makefile.py::TestAgentE2eTargetRecipe tests/test_makefile.py::TestHelpTarget::test_help_frames_test_agent_e2e_broader_beyond_golden -v'

make test PYTEST_ARGS='tests/test_ui_actions_mcp_packaging_doc.py tests/test_packaging_doc_lock_helper.py -v'
```

### CI workflow contract helpers (PYPOST-928)

Workflow/doc lock tests slice named jobs from `.github/workflows/test.yml` to assert upload
wiring, composite `uses:`, retention keys, and similar substrings. Use the shared helper instead
of copying local `_job_block` heuristics:

| Module | Role |
| --- | --- |
| `tests/helpers/ci_workflow_yaml.py` | `workflow_job_block(text, job_id, *, workflow_path=None)` |
| `tests/test_ci_workflow_yaml_helper.py` | Unit tests + import contract for consumer modules |

The helper validates the top-level `jobs` mapping with `yaml.safe_load`, confirms the job key
exists, then extracts the raw job text block (scoped to the `jobs:` section) for grep-style
assertions. New CI locks should import:

```python
from tests.helpers.ci_workflow_yaml import workflow_job_block

block = workflow_job_block(
    workflow_text,
    "my-job",
    workflow_path=path_to_test_yml,
)
```

Focused run:

```bash
make test PYTEST_ARGS='tests/test_ci_workflow_yaml_helper.py tests/test_ci_*.py tests/test_agent_e2e_ci_*.py -v'
```

### Python interpreter decoupling (PYPOST-718)

To ensure Makefile integration tests are robust and decoupled from system-level environment
differences, all test-spawns of `make` explicitly override the `PYTHON` variable with the active
interpreter executing the tests (i.e., `PYTHON=sys.executable`). This forces `make` to create
the virtual environment and markers with the exact matching Python version, preventing version
mismatch failures in environments where the system-default `python3` differs from the `pytest`
runner's interpreter.

Each case runs GNU Make in an isolated `tmp_path` with a copied `Makefile`, minimal
`tests/test_noop.py`, and `pypost/__init__.py`. Focused run:

### Slow smoke isolated workspace seed (PYPOST-943)

The slow install smoke (`make_workspace_full_deps` in `tests/test_makefile.py`) copies the
**committed** `pyproject.toml` into an isolated `tmp_path` and runs `make install` there.
Both the fixture and the fast seed-contract tests assemble that workspace via
`_materialize_slow_smoke_workspace` (Makefile copy, `pyproject.toml` copy, then
`_seed_installable_package`) so assembly steps cannot drift between slow and fast guards.
Dependency pins alone are not enough: setuptools resolves **dynamic metadata** from that
manifest at build time. The seed must therefore mirror install-time packaging artifacts, not
only the dependency list.

| `pyproject.toml` field | Seed requirement |
| --- | --- |
| `[tool.setuptools.dynamic] version.attr` | `pypost/version.py` with `__version__` (copied from repo) |
| `[project] readme` | `README.md` on disk (copied from repo) |
| `[project.scripts]` | Entry-point module files and parent `__init__.py` stubs (PYPOST-964) |
| `[project] license-files` / `[tool.setuptools] license-files` | Listed license files on disk |
| `[tool.setuptools.package-data]` | Files matching declared globs under the package dir |
| `[tool.setuptools.packages.find]` | Minimal `pypost/` package dir (`__init__.py` stub) |

`_seed_installable_package` materializes the version and readme files atop the existing stub
from `_seed_minimal_project`. A **fast contract guard** in
`tests/test_makefile_install_seed_contract.py` parses committed `pyproject.toml` and asserts
the seed includes those paths before any network install — so future dynamic metadata changes
fail in the default `make test` matrix instead of only in the 1–3 minute slow smoke job.

#### Minimum `pypost/` tree policy (PYPOST-963)

Slow smoke uses a **stub package**, not a full mirror of the repository `pypost/` tree.
Editable install metadata resolution only needs package discovery plus the dynamic version
module and readme file — not application subpackages such as `pypost/core/` or `pypost/ui/`.

| Location | Policy |
| --- | --- |
| `pypost/__init__.py` | Empty stub from `_seed_minimal_project` |
| `pypost/version.py` | Copied from repo (PYPOST-808 single version source) |
| `pypost/agent/**` | Stub modules for `[project.scripts]` entry points only (PYPOST-964) |
| `README.md` (workspace root) | Copied from repo |
| Other `pypost/**` paths | **Excluded** unless packaging requires them at install time |

The canonical stub file set is `SLOW_SMOKE_MINIMUM_PYPPOST_FILES` in `tests/test_makefile.py`
(currently `__init__.py`, `version.py`, and script entry-point stubs under `pypost/agent/`).
`_required_seed_paths_from_pyproject` derives workspace-root and out-of-tree install artifacts
(readme, license files, package-data); `test_slow_smoke_seed_materializes_minimum_pypost_tree`
asserts the `pypost/` stub shape exactly — catching under-seeding and accidental full-tree copies.

When adding new dynamic or install-time paths to `pyproject.toml`, extend the seed helper,
`SLOW_SMOKE_MINIMUM_PYPPOST_FILES` (if under `pypost/`), and the contract parser together;
see `ai-tasks/PYPOST-943/20-architecture.md` § Packaging fields the seed must satisfy.

#### Post-install sanity (PYPOST-559, PYPOST-966)

After `make install` succeeds in the slow smoke workspace, `TestSlowInstallSmoke` runs each
snippet in `POST_INSTALL_SANITY_SNIPPETS` (`tests/test_makefile.py`) via
`_assert_post_install_sanity` against `.venv/bin/python`:

| Snippet purpose | Check |
| --- | --- |
| Core dependency | `import pydantic` (PYPOST-559) |
| Installed package | `import pypost.version as v; assert v.__version__` (PYPOST-966) |

The version-module read verifies the installed `pypost` package without importing Qt/UI
subpackages. A fast contract guard
(`test_post_install_sanity_includes_pypost_version_read` in
`tests/test_makefile_install_seed_contract.py`) asserts the snippet list includes a pypost
check so policy cannot regress without a default-matrix failure.

Focused contract run:

```bash
make test PYTEST_ARGS='tests/test_makefile_install_seed_contract.py -v'
```

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
That job uses the same composite action `.github/actions/install-qt-egl-runtime` as the
main `test` matrix and `agent-e2e` before pytest collection (GUI test modules and `qapp`
still load PySide6; conftest alone no longer eager-imports — PYPOST-926). Parity is locked by
`tests/test_ci_make_install_smoke_qt_runtime.py`: all three jobs must reference the
composite, inline duplicate apt blocks are forbidden, and `_expected_qt_egl_packages()`
parses `.github/actions/install-qt-egl-runtime/action.yml` as the sole authoritative
package source (PYPOST-925 — no hardcoded frozenset in the test module).
Job `agent-e2e` runs `make install && make test-agent-e2e` on Python 3.11
(PYPOST-861 env-pack make gate; see [agent_e2e.md](agent_e2e.md)).

### Agent e2e CI double-run (PYPOST-873 / PYPOST-907 / PYPOST-930) — DEFER

On Python **3.11**, agent e2e / env-pack tests run in both the main `test`
matrix (`-m "not slow"`) and the dedicated `agent-e2e` job. That
**intentional double-run** is kept: the dedicated job proves
`make test-agent-e2e`; the matrix keeps multi-version coverage (3.11 +
3.13). [PYPOST-873](https://pypost.atlassian.net/browse/PYPOST-873)
**DEFER**red a cost trim; [PYPOST-907](https://pypost.atlassian.net/browse/PYPOST-907)
reviewed **CI duration evidence** and chose **DEFER after evidence** —
overlap is measurable but not wall-clock painful (see below).
[PYPOST-930](https://pypost.atlassian.net/browse/PYPOST-930) re-assessed the
**ENABLE threshold** and chose **continued DEFER** — **ENABLE threshold not
met** (checklist below).

#### CI duration evidence (Actions, 2026-08-01)

Timing notes (job durations / overlap cost) for the intentional double-run —
published under PYPOST-907 and discoverable via
[PYPOST-908](https://pypost.atlassian.net/browse/PYPOST-908). Do not invent
replacement numbers; refresh automation lives under
[PYPOST-931](https://pypost.atlassian.net/browse/PYPOST-931).

#### Refresh procedure (PYPOST-931)

Maintainers update the committed table below with **honest Actions timings**
only — the script prints fresh numbers; a human reviews and pastes into this
section (no auto-commit).

```bash
make refresh-ci-duration-evidence
# optional: GITHUB_TOKEN=... for higher API rate limits
# direct: .venv/bin/python scripts/refresh_ci_duration_evidence.py
```

1. Run `make refresh-ci-duration-evidence` (needs network; queries
   `koctep/pypost` workflow `Tests` for completed runs with job `agent-e2e`).
2. Copy the markdown table from stdout into **CI duration evidence** below;
   adjust the narrative sentence (`n=…`, fetch date) to match the sample.
3. Re-read overlap interpretation (wall clock vs billable 3.11 redundancy).
4. Run `make check-ci-duration-evidence` to verify this procedure stays
   documented; run `make test PYTEST_ARGS='tests/test_refresh_ci_duration_evidence.py -v'`
   for the wiring lock.

From completed `Tests` workflow runs on `koctep/pypost` that include job
`agent-e2e` (n=2 in a 15-run window):

| Run | Main `test` 3.11 | Job `agent-e2e` |
| --- | --- | --- |
| #21 | ~11.8m total; pytest step ~670s | ~3.6m total; `make test-agent-e2e` ~172s |
| #20 | ~7.4m | ~1.6m |

Wall clock is dominated by the main matrix; `agent-e2e` finishes in
parallel (~1.6–3.6m), so a trim would not shorten PR feedback in these
samples. Pack collect size locally: **82** tests (`agent_e2e and not slow`;
was 64 at PYPOST-907). Overlap cost: measurable 3.11 billable redundancy
(~172s dedicated pack step in run #21) while the same marker set also runs
in main pytest — not wall-clock painful at this sample size.

#### ENABLE threshold checklist (PYPOST-930, 2026-08-01)

| Trigger | Bar | Status |
| --- | --- | --- |
| Dedicated pack step | ≥6m across ≥3 recent green runs | **Not met** — n=2; max ~172s (~2.9m) |
| Maintainer pain | Painful double failures / queue cost | **Not met** — no report |
| Pack size + domination | ≥120 tests and main pytest pack-dominated | **Not met** — 82 collected; main pytest ~670s total |

**Decision:** **continued DEFER** — **ENABLE threshold not met**. Do not
exclude `agent_e2e` from the main matrix until a future revisit satisfies
the bar. An ENABLE trim must preserve 3.13 agent e2e coverage (expand
`agent-e2e` to a matrix) and update
`tests/test_agent_e2e_ci_double_run_doc.py`.

**Revisit when** (ENABLE threshold): dedicated `make test-agent-e2e` step
sustained ≥ 6 minutes across ≥3 recent green runs; or maintainers report
painful double failures / queue cost; or pack collect size sustained ≥ 120
**and** main pytest is clearly pack-dominated.

### Agent e2e failure artifact CI upload (PYPOST-874 / PYPOST-909) — ENABLE

When job `agent-e2e` fails, GitHub Actions uploads `artifacts/agent_e2e/`
(PYPOST-860 masked dumps) as artifact `agent-e2e-failure-artifacts`
(`if: failure()`, `if-no-files-found: ignore`). When a main `test` matrix
cell fails, the same path is uploaded as
`agent-e2e-failure-artifacts-${{ matrix.python-version }}` (PYPOST-909).
Both uploads set `retention-days: 14` (PYPOST-910). Download from the
run’s Artifacts UI within that window. Live UI proof of a downloadable
dump is **DEFER**red (PYPOST-911) until a qualifying red run exists —
see [agent_e2e_failure_artifacts.md](agent_e2e_failure_artifacts.md)
§ Live Artifacts UI proof for what to capture and
`ai-tasks/PYPOST-911/live-proof-notes.md`. Details:
[agent_e2e_failure_artifacts.md](agent_e2e_failure_artifacts.md).
Locks: `tests/test_agent_e2e_ci_failure_upload_doc.py` (874),
`tests/test_agent_e2e_ci_matrix_failure_upload_doc.py` (909),
`tests/test_agent_e2e_ci_failure_retention_doc.py` (910),
`tests/test_agent_e2e_ci_failure_artifacts_ui_proof_doc.py` (911).

## CI dependency caching (PYPOST-311)

Both CI jobs use `actions/setup-python@v5` with `cache: pip` and an explicit
`cache-dependency-path` listing `pyproject.toml`, `requirements.in`, `requirements.txt`,
`requirements-dev.in`, and `requirements-dev.txt`. The cache stores downloaded pip wheels under
the runner home directory and restores them before dependency installation.

| Aspect | Behavior |
| --- | --- |
| **Cache key** | OS + Python version + SHA-256 hash of `pyproject.toml` and all four requirements files |
| **Invalidation** | Any edit to a lock or source file produces a new key (cold install) |
| **Scope** | Main `test` matrix (3.11, 3.13), `make-install-smoke` (3.11), `agent-e2e` (3.11), `security-audit`, `check-license-inventory`, `check-lock`, and `check-lock-dev` |
| **Local dev** | `make install` uses Makefile `.venv`; GitHub cache applies to CI only |

The slow install smoke runs `make install` in an isolated `tmp_path` workspace; pip still
reuses cached wheels from the restored `~/.cache/pip` on the runner.

Verify cache behavior in the GitHub Actions log for the `setup-python` step (`Cache hit` /
`Cache miss`). First run after a dependency change is expected to miss and download fresh wheels.

## CI lock verification (PYPOST-804, PYPOST-927)

The `check-lock` job in `.github/workflows/test.yml` installs a **pinned**
[uv](https://docs.astral.sh/uv/) version (`version:` input on `astral-sh/setup-uv`, PYPOST-984 —
the sibling `check-lock-dev` job below installs whatever `uv` release is latest at run time) and
runs `make check-lock` once per workflow. `make check-lock` retries a failing `uv pip compile` up
to 3 times before failing with a distinct message, so the job fails only on a genuinely stale
`requirements.txt` or a persistent compile error (never on resolver-version drift alone; same
check as local maintainer workflow in [setup.md](setup.md) § Dependency lock file, PYPOST-984).

The `check-lock-dev` job installs [uv](https://docs.astral.sh/uv/)
and runs `make check-lock-dev` once per workflow. It fails when `requirements-dev.txt` is stale
relative to `requirements-dev.in` (same check as local maintainer workflow in
[setup.md](setup.md) § Development dependency lock file).

| Job | Input | Tool |
| --- | --- | --- |
| `check-lock` | `requirements.in` → `requirements.txt` | `uv pip compile` via Makefile |
| `check-lock-dev` | `requirements-dev.in` → `requirements-dev.txt` | `uv pip compile` via Makefile |

Production and dev lock drift are gated in CI; local parity uses the same Makefile targets
(PYPOST-779, PYPOST-780, PYPOST-804, PYPOST-927).

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
