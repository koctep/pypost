# Consolidated Technical Debt Inventory

Generated for [PYPOST-57](https://pypost.atlassian.net/browse/PYPOST-57) on 2026-08-02.

Aggregated from `ai-tasks/**/60-review.md`, `ai-tasks/**/40-tech-debt.md`, and
`ai-tasks/**/60-tech-debt.md`. Each row links a source task artifact to its Jira
follow-up issue.

Regenerate: `python scripts/consolidate_tech_debt.py`

## Summary

| Metric | Count |
| --- | ---: |
| Source files scanned | 818 |
| Total Jira link references | 1460 |
| Unique linked Jira issues | 874 |
| Source tasks with linked debt | 270 |
| Debt files without Jira links | 445 |

## Key Source Tasks

| Source | Linked items | Primary file |
| --- | ---: | --- |
| PYPOST-41 | 8 | `PYPOST-41/60-review.md` |
| PYPOST-43 | 7 | `PYPOST-43/60-review.md` |
| PYPOST-44 | 7 | `PYPOST-44/60-review.md` |
| PYPOST-45 | 2 | `PYPOST-45/60-review.md` |
| PYPOST-52 | 7 | `PYPOST-52/60-review.md` |

## Inventory by Source Task

### PYPOST-8 (5 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-387](https://pypost.atlassian.net/browse/PYPOST-387) | Type Check Duplication**: In methods `on_tree_expanded`, `on_tree_collapsed`, and `restore_tree_s... | `PYPOST-8/40-tech-debt.md` |
| [PYPOST-388](https://pypost.atlassian.net/browse/PYPOST-388) | Unit tests for tree state save/restore** ( | `PYPOST-8/40-tech-debt.md` |
| [PYPOST-389](https://pypost.atlassian.net/browse/PYPOST-389) | Edge-case tests (stale collection ids in settings)** ( | `PYPOST-8/40-tech-debt.md` |
| [PYPOST-391](https://pypost.atlassian.net/browse/PYPOST-391) | UI state preservation tests** ( | `PYPOST-8/40-tech-debt.md` |
| [PYPOST-392](https://pypost.atlassian.net/browse/PYPOST-392) | Consider debouncing settings saving if I/O performance issues arise. | `PYPOST-8/40-tech-debt.md` |

### PYPOST-9 (7 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-393](https://pypost.atlassian.net/browse/PYPOST-393) | Simple Regex Implementation**: The used regular expressions for JSON are quite simple and may not... | `PYPOST-9/40-tech-debt.md` |
| [PYPOST-394](https://pypost.atlassian.net/browse/PYPOST-394) | No JSON Validation**: The highlighter simply colors tokens; it does not check the validity of the... | `PYPOST-9/40-tech-debt.md` |
| [PYPOST-395](https://pypost.atlassian.net/browse/PYPOST-395) | Hardcoded Colors**: Colors (`darkblue`, `blue`, `green`, `purple`) are defined directly in the `J... | `PYPOST-9/40-tech-debt.md` |
| [PYPOST-396](https://pypost.atlassian.net/browse/PYPOST-396) | Unit tests for `JsonHighlighter` are missing. Verification was done visually. Tests checking that... | `PYPOST-9/40-tech-debt.md` |
| [PYPOST-397](https://pypost.atlassian.net/browse/PYPOST-397) | Regex on Whole Block**: `QSyntaxHighlighter` works block by block, but complex regular expression... | `PYPOST-9/40-tech-debt.md` |
| [PYPOST-398](https://pypost.atlassian.net/browse/PYPOST-398) | Move color settings to application theme or config. | `PYPOST-9/40-tech-debt.md` |
| [PYPOST-399](https://pypost.atlassian.net/browse/PYPOST-399) | Add tests for `JsonHighlighter`. | `PYPOST-9/40-tech-debt.md` |

### PYPOST-10 (7 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-90](https://pypost.atlassian.net/browse/PYPOST-90) | Synchronous tree-state saves** ( | `PYPOST-10/40-tech-debt.md` |
| [PYPOST-91](https://pypost.atlassian.net/browse/PYPOST-91) | Type Check Duplication**: In methods `on_tree_expanded`, `on_tree_collapsed`, and `restore_tree_s... | `PYPOST-10/40-tech-debt.md` |
| [PYPOST-92](https://pypost.atlassian.net/browse/PYPOST-92) | Unit tests for tree state save/restore logic are missing. Testing was done manually. | `PYPOST-10/40-tech-debt.md` |
| [PYPOST-93](https://pypost.atlassian.net/browse/PYPOST-93) | No tests for edge cases (e.g., ID exists in settings but collection is gone). | `PYPOST-10/40-tech-debt.md` |
| [PYPOST-94](https://pypost.atlassian.net/browse/PYPOST-94) | Linear Search on Restore**: `restore_tree_state` iterates through all root level items. With a hu... | `PYPOST-10/40-tech-debt.md` |
| [PYPOST-95](https://pypost.atlassian.net/browse/PYPOST-95) | Write tests to verify UI state preservation. | `PYPOST-10/40-tech-debt.md` |
| [PYPOST-96](https://pypost.atlassian.net/browse/PYPOST-96) | Consider debouncing settings saving** ( | `PYPOST-10/40-tech-debt.md` |

### PYPOST-11 (7 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-97](https://pypost.atlassian.net/browse/PYPOST-97) | Simple Regex Implementation**: The used regular expressions for JSON are quite simple and may not... | `PYPOST-11/40-tech-debt.md` |
| [PYPOST-98](https://pypost.atlassian.net/browse/PYPOST-98) | No JSON Validation**: The highlighter simply colors tokens; it does not check the validity of the... | `PYPOST-11/40-tech-debt.md` |
| [PYPOST-99](https://pypost.atlassian.net/browse/PYPOST-99) | Hardcoded Colors**: Colors (`darkblue`, `blue`, `green`, `purple`) are defined directly in the `J... | `PYPOST-11/40-tech-debt.md` |
| [PYPOST-100](https://pypost.atlassian.net/browse/PYPOST-100) | Unit tests for `JsonHighlighter` are missing. Verification was done visually. Tests checking that... | `PYPOST-11/40-tech-debt.md` |
| [PYPOST-101](https://pypost.atlassian.net/browse/PYPOST-101) | Regex on Whole Block**: `QSyntaxHighlighter` works block by block, but complex regular expression... | `PYPOST-11/40-tech-debt.md` |
| [PYPOST-102](https://pypost.atlassian.net/browse/PYPOST-102) | Technical debt follow-up | `PYPOST-11/40-tech-debt.md` |
| [PYPOST-103](https://pypost.atlassian.net/browse/PYPOST-103) | Add tests for `JsonHighlighter`. | `PYPOST-11/40-tech-debt.md` |

### PYPOST-12 (9 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-104](https://pypost.atlassian.net/browse/PYPOST-104) | No Tests**: Creation of automated tests was skipped by user request. Auto-indentation and paste l... | `PYPOST-12/40-tech-debt.md` |
| [PYPOST-105](https://pypost.atlassian.net/browse/PYPOST-105) | Simplified Unindent Logic**: Unindentation works only if the line contains *only* the closing bra... | `PYPOST-12/40-tech-debt.md` |
| [PYPOST-106](https://pypost.atlassian.net/browse/PYPOST-106) | Manual Font Propagation**: ~~In `MainWindow.apply_settings`, the font is manually applied to indi... | `PYPOST-12/40-tech-debt.md` |
| [PYPOST-107](https://pypost.atlassian.net/browse/PYPOST-107) | Manual Font Propagation**: ~~(See above)~~ **Resolved | `PYPOST-12/40-tech-debt.md` |
| [PYPOST-108](https://pypost.atlassian.net/browse/PYPOST-108) | CodeEditor tests** ( | `PYPOST-12/40-tech-debt.md` |
| [PYPOST-109](https://pypost.atlassian.net/browse/PYPOST-109) | JSON Parsing on Paste**: When pasting *very* large text, attempting to parse it as JSON might cau... | `PYPOST-12/40-tech-debt.md` |
| [PYPOST-110](https://pypost.atlassian.net/browse/PYPOST-110) | Create tests for `CodeEditor`. | `PYPOST-12/40-tech-debt.md` |
| [PYPOST-111](https://pypost.atlassian.net/browse/PYPOST-111) | Implement asynchronous JSON check on paste for large data volumes (optional). | `PYPOST-12/40-tech-debt.md` |
| [PYPOST-112](https://pypost.atlassian.net/browse/PYPOST-112) | Manual Font Propagation**: ~~In `MainWindow.apply_settings`, the font is manually applied to indi... | `PYPOST-12/40-tech-debt.md` |

### PYPOST-13 (9 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-113](https://pypost.atlassian.net/browse/PYPOST-113) | Variable regex scope** ( | `PYPOST-13/40-tech-debt.md` |
| [PYPOST-114](https://pypost.atlassian.net/browse/PYPOST-114) | Default tooltip styling** ( | `PYPOST-13/40-tech-debt.md` |
| [PYPOST-115](https://pypost.atlassian.net/browse/PYPOST-115) | One-level tooltip vars** ( | `PYPOST-13/40-tech-debt.md` |
| [PYPOST-116](https://pypost.atlassian.net/browse/PYPOST-116) | Direct variable injection** ( | `PYPOST-13/40-tech-debt.md` |
| [PYPOST-117](https://pypost.atlassian.net/browse/PYPOST-117) | VariableHoverHelper tests** ( | `PYPOST-13/40-tech-debt.md` |
| [PYPOST-118](https://pypost.atlassian.net/browse/PYPOST-118) | Tooltip UI** ( | `PYPOST-13/40-tech-debt.md` |
| [PYPOST-120](https://pypost.atlassian.net/browse/PYPOST-120) | Mitigation: scan less text** ( | `PYPOST-13/40-tech-debt.md` |
| [PYPOST-121](https://pypost.atlassian.net/browse/PYPOST-121) | Technical debt follow-up | `PYPOST-13/40-tech-debt.md` |
| [PYPOST-122](https://pypost.atlassian.net/browse/PYPOST-122) | Technical debt follow-up | `PYPOST-13/40-tech-debt.md` |

### PYPOST-14 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-125](https://pypost.atlassian.net/browse/PYPOST-125) | Technical debt follow-up | `PYPOST-14/40-tech-debt.md` |
| [PYPOST-126](https://pypost.atlassian.net/browse/PYPOST-126) | Technical debt follow-up | `PYPOST-14/40-tech-debt.md` |
| [PYPOST-127](https://pypost.atlassian.net/browse/PYPOST-127) | [COMPLETED] Optimize Lookup**: Index for request IDs inside `RequestManager`. | `PYPOST-14/40-tech-debt.md` |

### PYPOST-15 (7 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-128](https://pypost.atlassian.net/browse/PYPOST-128) | Manual Variable Propagation**: Variable updates happen via explicit call to `set_variables` in `R... | `PYPOST-15/40-tech-debt.md` |
| [PYPOST-129](https://pypost.atlassian.net/browse/PYPOST-129) | VariableHoverHelper**: The helper performs two functions: finding a variable by index (for text f... | `PYPOST-15/40-tech-debt.md` |
| [PYPOST-130](https://pypost.atlassian.net/browse/PYPOST-130) | Unit Tests**: Unit tests for `VariableHoverHelper.resolve_text` are missing. Tests were created b... | `PYPOST-15/40-tech-debt.md` |
| [PYPOST-131](https://pypost.atlassian.net/browse/PYPOST-131) | UI Tests**: No automated UI tests to verify tooltip appearance in the table. | `PYPOST-15/40-tech-debt.md` |
| [PYPOST-132](https://pypost.atlassian.net/browse/PYPOST-132) | MouseMoveEvent**: Variable resolution happens inside `mouseMoveEvent`. Although the regular expre... | `PYPOST-15/40-tech-debt.md` |
| [PYPOST-133](https://pypost.atlassian.net/browse/PYPOST-133) | Write and commit unit tests for `VariableHoverHelper` (methods `find_variable_at_index` and `reso... | `PYPOST-15/40-tech-debt.md` |
| [PYPOST-134](https://pypost.atlassian.net/browse/PYPOST-134) | Consider moving variable substitution logic to a common `TemplateEngine`. | `PYPOST-15/40-tech-debt.md` |

### PYPOST-16 (8 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-135](https://pypost.atlassian.net/browse/PYPOST-135) | No Arguments Support**: Tools exposed via MCP do not accept arguments. They execute the request e... | `PYPOST-16/40-tech-debt.md` |
| [PYPOST-136](https://pypost.atlassian.net/browse/PYPOST-136) | Restart on Update**: When the list of tools (requests) changes, the server might need a restart o... | `PYPOST-16/40-tech-debt.md` |
| [PYPOST-137](https://pypost.atlassian.net/browse/PYPOST-137) | Single Environment**: The server uses the currently active environment in PyPost. If the user swi... | `PYPOST-16/40-tech-debt.md` |
| [PYPOST-138](https://pypost.atlassian.net/browse/PYPOST-138) | Thread Safety**: We are running `asyncio` server in a thread and calling PyPost core logic (which... | `PYPOST-16/40-tech-debt.md` |
| [PYPOST-139](https://pypost.atlassian.net/browse/PYPOST-139) | No automated tests for MCP server interaction. Testing is manual via MCP Inspector or Cursor. | `PYPOST-16/40-tech-debt.md` |
| [PYPOST-140](https://pypost.atlassian.net/browse/PYPOST-140) | ~~Implement argument parsing for tools.~~ | `PYPOST-16/40-tech-debt.md` |
| [PYPOST-141](https://pypost.atlassian.net/browse/PYPOST-141) | Add logging/inspection of MCP calls in UI. | `PYPOST-16/40-tech-debt.md` |
| [PYPOST-142](https://pypost.atlassian.net/browse/PYPOST-142) | Add tests using an MCP client mock. | `PYPOST-16/40-tech-debt.md` |

### PYPOST-18 (6 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-143](https://pypost.atlassian.net/browse/PYPOST-143) | ~~**Global TemplateService** ( | `PYPOST-18/40-tech-debt.md` |
| [PYPOST-144](https://pypost.atlassian.net/browse/PYPOST-144) | template_service imports** ( | `PYPOST-18/40-tech-debt.md` |
| [PYPOST-145](https://pypost.atlassian.net/browse/PYPOST-145) | ~~**TemplateService unit tests** ( | `PYPOST-18/40-tech-debt.md` |
| [PYPOST-146](https://pypost.atlassian.net/browse/PYPOST-146) | Shared Jinja2 Environment** ( | `PYPOST-18/40-tech-debt.md` |
| [PYPOST-147](https://pypost.atlassian.net/browse/PYPOST-147) | Technical debt follow-up | `PYPOST-18/40-tech-debt.md` |
| [PYPOST-148](https://pypost.atlassian.net/browse/PYPOST-148) | ~~**Jinja2 `from_string` caching** ( | `PYPOST-18/40-tech-debt.md` |

### PYPOST-19 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-149](https://pypost.atlassian.net/browse/PYPOST-149) | No Input Validation**: The host input field is a simple text field. There is no validation for IP... | `PYPOST-19/40-tech-debt.md` |
| [PYPOST-150](https://pypost.atlassian.net/browse/PYPOST-150) | No automated tests verifying that the server actually binds to the specified host. Testing is man... | `PYPOST-19/40-tech-debt.md` |
| [PYPOST-151](https://pypost.atlassian.net/browse/PYPOST-151) | Add validation for Host and Port fields in `SettingsDialog`. | `PYPOST-19/40-tech-debt.md` |

### PYPOST-20 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-152](https://pypost.atlassian.net/browse/PYPOST-152) | Hardcoded Routes**: Routes `/sse` and `/messages` are hardcoded in `MCPServerImpl`. If the MCP pr... | `PYPOST-20/40-tech-debt.md` |
| [PYPOST-153](https://pypost.atlassian.net/browse/PYPOST-153) | No Error Handling for Port Binding**: If the port is busy, `uvicorn` throws an exception that is ... | `PYPOST-20/40-tech-debt.md` |
| [PYPOST-154](https://pypost.atlassian.net/browse/PYPOST-154) | Improve error handling when starting the server (port in use). | `PYPOST-20/40-tech-debt.md` |

### PYPOST-21 (5 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-155](https://pypost.atlassian.net/browse/PYPOST-155) | POST + 405 on `/messages`** ( | `PYPOST-21/40-tech-debt.md` |
| [PYPOST-157](https://pypost.atlassian.net/browse/PYPOST-157) | MessagesEndpoint responses** ( | `PYPOST-21/40-tech-debt.md` |
| [PYPOST-158](https://pypost.atlassian.net/browse/PYPOST-158) | SSE close + 405 on `/messages`** ( | `PYPOST-21/40-tech-debt.md` |
| [PYPOST-160](https://pypost.atlassian.net/browse/PYPOST-160) | Technical debt follow-up | `PYPOST-21/40-tech-debt.md` |
| [PYPOST-161](https://pypost.atlassian.net/browse/PYPOST-161) | Technical debt follow-up | `PYPOST-21/40-tech-debt.md` |

### PYPOST-22 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-162](https://pypost.atlassian.net/browse/PYPOST-162) | Manual Signal Connection**: Signal connection happens in `add_new_tab`. If tabs are created elsew... | `PYPOST-22/40-tech-debt.md` |
| [PYPOST-163](https://pypost.atlassian.net/browse/PYPOST-163) | No Validation for New Variable Name**: Basic check for empty string is present, but no check for ... | `PYPOST-22/40-tech-debt.md` |
| [PYPOST-164](https://pypost.atlassian.net/browse/PYPOST-164) | No UI tests for context menu interaction. | `PYPOST-22/40-tech-debt.md` |
| [PYPOST-165](https://pypost.atlassian.net/browse/PYPOST-165) | Add validation for variable names. | `PYPOST-22/40-tech-debt.md` |

### PYPOST-23 (10 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-166](https://pypost.atlassian.net/browse/PYPOST-166) | Manual Route Handling**: The `MetricsManager` manually checks `environ['PATH_INFO'] == '/metrics'... | `PYPOST-23/40-tech-debt.md` |
| [PYPOST-167](https://pypost.atlassian.net/browse/PYPOST-167) | Global Singleton Usage**: The `MetricsManager` is accessed via `MetricsManager()` singleton patte... | `PYPOST-23/40-tech-debt.md` |
| [PYPOST-168](https://pypost.atlassian.net/browse/PYPOST-168) | Coupling**: `HTTPClient` and `MCPServerImpl` now have a direct dependency on `pypost.core.metrics... | `PYPOST-23/40-tech-debt.md` |
| [PYPOST-169](https://pypost.atlassian.net/browse/PYPOST-169) | Integration Tests**: There are no automated tests to verify that the HTTP server actually starts ... | `PYPOST-23/40-tech-debt.md` |
| [PYPOST-170](https://pypost.atlassian.net/browse/PYPOST-170) | Metric Verification**: No tests verify that specific actions (like clicking "Send") correctly inc... | `PYPOST-23/40-tech-debt.md` |
| [PYPOST-171](https://pypost.atlassian.net/browse/PYPOST-171) | Locking**: The `MetricsManager` uses locks for thread safety during server start/stop. This is lo... | `PYPOST-23/40-tech-debt.md` |
| [PYPOST-172](https://pypost.atlassian.net/browse/PYPOST-172) | Synchronous Tracking**: Metric increments are synchronous method calls. `prometheus_client` opera... | `PYPOST-23/40-tech-debt.md` |
| [PYPOST-173](https://pypost.atlassian.net/browse/PYPOST-173) | Add unit tests for `MetricsManager` to verify singleton behavior and metric registration. | `PYPOST-23/40-tech-debt.md` |
| [PYPOST-174](https://pypost.atlassian.net/browse/PYPOST-174) | Add integration tests to check if `/metrics` endpoint returns 200 OK and expected content type. | `PYPOST-23/40-tech-debt.md` |
| [PYPOST-175](https://pypost.atlassian.net/browse/PYPOST-175) | Consider refactoring metric tracking into an event-based system to decouple core logic from monit... | `PYPOST-23/40-tech-debt.md` |

### PYPOST-24 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-176](https://pypost.atlassian.net/browse/PYPOST-176) | Global Metrics Manager**: `MetricsManager` is accessed as a global singleton. Dependency injectio... | `PYPOST-24/40-tech-debt.md` |
| [PYPOST-177](https://pypost.atlassian.net/browse/PYPOST-177) | No unit tests for MCP metrics collection. Verified manually via `/metrics` endpoint. | `PYPOST-24/40-tech-debt.md` |
| [PYPOST-178](https://pypost.atlassian.net/browse/PYPOST-178) | Add unit tests for `MetricsManager`. | `PYPOST-24/40-tech-debt.md` |

### PYPOST-25 (15 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-179](https://pypost.atlassian.net/browse/PYPOST-179) | Manual File Creation**: Files were created via PyPost UI and then committed. No script for genera... | `PYPOST-25/40-tech-debt.md` |
| [PYPOST-180](https://pypost.atlassian.net/browse/PYPOST-180) | No automated tests that use this collection. It is intended for manual testing via MCP Inspector ... | `PYPOST-25/40-tech-debt.md` |
| [PYPOST-181](https://pypost.atlassian.net/browse/PYPOST-181) | Add integration tests that load this collection and execute requests via MCP. | `PYPOST-25/40-tech-debt.md` |
| [PYPOST-182](https://pypost.atlassian.net/browse/PYPOST-182) | Technical debt follow-up | `PYPOST-25/60-tech-debt.md` |
| [PYPOST-183](https://pypost.atlassian.net/browse/PYPOST-183) | Limited validation (no suite)** ( | `PYPOST-25/60-tech-debt.md` |
| [PYPOST-184](https://pypost.atlassian.net/browse/PYPOST-184) | Unstructured save logging** ( | `PYPOST-25/60-tech-debt.md` |
| [PYPOST-185](https://pypost.atlassian.net/browse/PYPOST-185) | RequestWidget: UI plus wiring** ( | `PYPOST-25/60-tech-debt.md` |
| [PYPOST-186](https://pypost.atlassian.net/browse/PYPOST-186) | Technical debt follow-up | `PYPOST-25/60-tech-debt.md` |
| [PYPOST-187](https://pypost.atlassian.net/browse/PYPOST-187) | Technical debt follow-up | `PYPOST-25/60-tech-debt.md` |
| [PYPOST-188](https://pypost.atlassian.net/browse/PYPOST-188) | Technical debt follow-up | `PYPOST-25/60-tech-debt.md` |
| [PYPOST-189](https://pypost.atlassian.net/browse/PYPOST-189) | Technical debt follow-up | `PYPOST-25/60-tech-debt.md` |
| [PYPOST-190](https://pypost.atlassian.net/browse/PYPOST-190) | Technical debt follow-up | `PYPOST-25/60-tech-debt.md` |
| [PYPOST-191](https://pypost.atlassian.net/browse/PYPOST-191) | Qt UI tests for Save** ( | `PYPOST-25/60-tech-debt.md` |
| [PYPOST-192](https://pypost.atlassian.net/browse/PYPOST-192) | Technical debt follow-up | `PYPOST-25/60-tech-debt.md` |
| [PYPOST-193](https://pypost.atlassian.net/browse/PYPOST-193) | Technical debt follow-up | `PYPOST-25/60-tech-debt.md` |

### PYPOST-26 (22 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-194](https://pypost.atlassian.net/browse/PYPOST-194) | Global Timeout Hardcoding**: We introduced a hardcoded timeout of `30.0` seconds in `HTTPClient.s... | `PYPOST-26/40-tech-debt.md` |
| [PYPOST-195](https://pypost.atlassian.net/browse/PYPOST-195) | Metrics Estimation**: While streaming, we estimate the size based on the utf-8 encoded length of ... | `PYPOST-26/40-tech-debt.md` |
| [PYPOST-196](https://pypost.atlassian.net/browse/PYPOST-196) | Time Updates**: The Status code is updated immediately via `headers_received` signal, but "Elapse... | `PYPOST-26/40-tech-debt.md` |
| [PYPOST-197](https://pypost.atlassian.net/browse/PYPOST-197) | SSE Endpoint Automated Test**: We verified manually with `test_streaming.py`, but haven't integra... | `PYPOST-26/40-tech-debt.md` |
| [PYPOST-198](https://pypost.atlassian.net/browse/PYPOST-198) | Cancellation Test**: We haven't added an automated test to verify that clicking "Stop" actually t... | `PYPOST-26/40-tech-debt.md` |
| [PYPOST-199](https://pypost.atlassian.net/browse/PYPOST-199) | Memory Usage on Large Streams**: We still accumulate the full body in `content_parts` (in `HTTPCl... | `PYPOST-26/40-tech-debt.md` |
| [PYPOST-200](https://pypost.atlassian.net/browse/PYPOST-200) | Add "Timeout" configuration to `RequestData` model and UI. | `PYPOST-26/40-tech-debt.md` |
| [PYPOST-201](https://pypost.atlassian.net/browse/PYPOST-201) | Implement "tail" mode for logging/streaming (limit buffer size). | `PYPOST-26/40-tech-debt.md` |
| [PYPOST-202](https://pypost.atlassian.net/browse/PYPOST-202) | Add real-time "Elapsed Time" counter in UI during request. | `PYPOST-26/40-tech-debt.md` |
| [PYPOST-203](https://pypost.atlassian.net/browse/PYPOST-203) | Refactor `HTTPClient` to better handle different content types and errors. | `PYPOST-26/40-tech-debt.md` |
| [PYPOST-204](https://pypost.atlassian.net/browse/PYPOST-204) | Manual `+` button geometry** ( | `PYPOST-26/60-tech-debt.md` |
| [PYPOST-205](https://pypost.atlassian.net/browse/PYPOST-205) | Untyped new-tab source field** ( | `PYPOST-26/60-tech-debt.md` |
| [PYPOST-206](https://pypost.atlassian.net/browse/PYPOST-206) | MainWindow still a god object** ( | `PYPOST-26/60-tech-debt.md` |
| [PYPOST-207](https://pypost.atlassian.net/browse/PYPOST-207) | Hardcoded tab-button spacing** ( | `PYPOST-26/60-tech-debt.md` |
| [PYPOST-208](https://pypost.atlassian.net/browse/PYPOST-208) | Technical debt follow-up | `PYPOST-26/60-tech-debt.md` |
| [PYPOST-209](https://pypost.atlassian.net/browse/PYPOST-209) | Technical debt follow-up | `PYPOST-26/60-tech-debt.md` |
| [PYPOST-210](https://pypost.atlassian.net/browse/PYPOST-210) | New-tab metrics coverage** ( | `PYPOST-26/60-tech-debt.md` |
| [PYPOST-211](https://pypost.atlassian.net/browse/PYPOST-211) | Tab button reposition cost** ( | `PYPOST-26/60-tech-debt.md` |
| [PYPOST-212](https://pypost.atlassian.net/browse/PYPOST-212) | Qt UI tests for new tab** ( | `PYPOST-26/60-tech-debt.md` |
| [PYPOST-213](https://pypost.atlassian.net/browse/PYPOST-213) | Tab-header component** ( | `PYPOST-26/60-tech-debt.md` |
| [PYPOST-214](https://pypost.atlassian.net/browse/PYPOST-214) | Technical debt follow-up | `PYPOST-26/60-tech-debt.md` |
| [PYPOST-215](https://pypost.atlassian.net/browse/PYPOST-215) | Technical debt follow-up | `PYPOST-26/60-tech-debt.md` |

### PYPOST-27 (16 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-216](https://pypost.atlassian.net/browse/PYPOST-216) | When implementing `on_env_update` we ignore updates if no environment is selected (`None`). | `PYPOST-27/40-tech-debt.md` |
| [PYPOST-217](https://pypost.atlassian.net/browse/PYPOST-217) | Small, idiomatic change** ( | `PYPOST-27/40-tech-debt.md` |
| [PYPOST-218](https://pypost.atlassian.net/browse/PYPOST-218) | No automated tests for `MainWindow` and `RequestWorker` interaction when updating variables. | `PYPOST-27/40-tech-debt.md` |
| [PYPOST-219](https://pypost.atlassian.net/browse/PYPOST-219) | Add unit test for `on_env_update` method, mocking `env_selector` and `storage`. | `PYPOST-27/40-tech-debt.md` |
| [PYPOST-220](https://pypost.atlassian.net/browse/PYPOST-220) | Synchronous save on script env updates** ( | `PYPOST-27/40-tech-debt.md` |
| [PYPOST-221](https://pypost.atlassian.net/browse/PYPOST-221) | Add unit tests for `MainWindow` (UI test coverage may currently be low). | `PYPOST-27/40-tech-debt.md` |
| [PYPOST-222](https://pypost.atlassian.net/browse/PYPOST-222) | Consider notifying the user if a script tries to write to an "empty" environment. | `PYPOST-27/40-tech-debt.md` |
| [PYPOST-223](https://pypost.atlassian.net/browse/PYPOST-223) | Sparse Makefile logging** ( | `PYPOST-27/60-tech-debt.md` |
| [PYPOST-224](https://pypost.atlassian.net/browse/PYPOST-224) | Flake8 debt outside this task** ( | `PYPOST-27/60-tech-debt.md` |
| [PYPOST-225](https://pypost.atlassian.net/browse/PYPOST-225) | No Makefile automation tests** ( | `PYPOST-27/60-tech-debt.md` |
| [PYPOST-226](https://pypost.atlassian.net/browse/PYPOST-226) | Pytest collection empty** ( | `PYPOST-27/60-tech-debt.md` |
| [PYPOST-227](https://pypost.atlassian.net/browse/PYPOST-227) | CI install cost** ( | `PYPOST-27/60-tech-debt.md` |
| [PYPOST-228](https://pypost.atlassian.net/browse/PYPOST-228) | Automate Make target checks** ( | `PYPOST-27/60-tech-debt.md` |
| [PYPOST-229](https://pypost.atlassian.net/browse/PYPOST-229) | CI dependency caching** ( | `PYPOST-27/60-tech-debt.md` |
| [PYPOST-230](https://pypost.atlassian.net/browse/PYPOST-230) | Technical debt follow-up | `PYPOST-27/60-tech-debt.md` |
| [PYPOST-231](https://pypost.atlassian.net/browse/PYPOST-231) | Reduce flake8 debt** ( | `PYPOST-27/60-tech-debt.md` |

### PYPOST-28 (17 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-232](https://pypost.atlassian.net/browse/PYPOST-232) | Implicit Context**: We rely on `self.tabs.currentWidget()` as a fallback. This works for the sing... | `PYPOST-28/40-tech-debt.md` |
| [PYPOST-233](https://pypost.atlassian.net/browse/PYPOST-233) | No significant shortcuts detected. The solution follows standard PySide6 patterns for thread mana... | `PYPOST-28/40-tech-debt.md` |
| [PYPOST-234](https://pypost.atlassian.net/browse/PYPOST-234) | No automated UI tests checking request retry. Testing was done manually. | `PYPOST-28/40-tech-debt.md` |
| [PYPOST-235](https://pypost.atlassian.net/browse/PYPOST-235) | No performance issues. Reference clearing is O(1). | `PYPOST-28/40-tech-debt.md` |
| [PYPOST-236](https://pypost.atlassian.net/browse/PYPOST-236) | Refactor signal passing to include context (tab reference). | `PYPOST-28/40-tech-debt.md` |
| [PYPOST-237](https://pypost.atlassian.net/browse/PYPOST-237) | Technical debt follow-up | `PYPOST-28/60-tech-debt.md` |
| [PYPOST-238](https://pypost.atlassian.net/browse/PYPOST-238) | Limited validation (no suite)** ( | `PYPOST-28/60-tech-debt.md` |
| [PYPOST-239](https://pypost.atlassian.net/browse/PYPOST-239) | Unstructured save logging** ( | `PYPOST-28/60-tech-debt.md` |
| [PYPOST-240](https://pypost.atlassian.net/browse/PYPOST-240) | RequestWidget: UI plus wiring** ( | `PYPOST-28/60-tech-debt.md` |
| [PYPOST-241](https://pypost.atlassian.net/browse/PYPOST-241) | Technical debt follow-up | `PYPOST-28/60-tech-debt.md` |
| [PYPOST-242](https://pypost.atlassian.net/browse/PYPOST-242) | Technical debt follow-up | `PYPOST-28/60-tech-debt.md` |
| [PYPOST-243](https://pypost.atlassian.net/browse/PYPOST-243) | Technical debt follow-up | `PYPOST-28/60-tech-debt.md` |
| [PYPOST-244](https://pypost.atlassian.net/browse/PYPOST-244) | Technical debt follow-up | `PYPOST-28/60-tech-debt.md` |
| [PYPOST-245](https://pypost.atlassian.net/browse/PYPOST-245) | Technical debt follow-up | `PYPOST-28/60-tech-debt.md` |
| [PYPOST-246](https://pypost.atlassian.net/browse/PYPOST-246) | Qt UI tests for Save** ( | `PYPOST-28/60-tech-debt.md` |
| [PYPOST-247](https://pypost.atlassian.net/browse/PYPOST-247) | Technical debt follow-up | `PYPOST-28/60-tech-debt.md` |
| [PYPOST-248](https://pypost.atlassian.net/browse/PYPOST-248) | Technical debt follow-up | `PYPOST-28/60-tech-debt.md` |

### PYPOST-29 (14 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-249](https://pypost.atlassian.net/browse/PYPOST-249) | StateManager Dependency**: `StateManager` is currently just a thin wrapper around `ConfigManager`... | `PYPOST-29/40-tech-debt.md` |
| [PYPOST-250](https://pypost.atlassian.net/browse/PYPOST-250) | Mixin Type Hinting**: `VariableHoverMixin` uses `self` as `QWidget` but inherits from `object` (i... | `PYPOST-29/40-tech-debt.md` |
| [PYPOST-253](https://pypost.atlassian.net/browse/PYPOST-253) | Manual `+` button geometry** ( | `PYPOST-29/60-tech-debt.md` |
| [PYPOST-254](https://pypost.atlassian.net/browse/PYPOST-254) | Untyped new-tab source field** ( | `PYPOST-29/60-tech-debt.md` |
| [PYPOST-255](https://pypost.atlassian.net/browse/PYPOST-255) | MainWindow still a god object** ( | `PYPOST-29/60-tech-debt.md` |
| [PYPOST-256](https://pypost.atlassian.net/browse/PYPOST-256) | Hardcoded tab-button spacing** ( | `PYPOST-29/60-tech-debt.md` |
| [PYPOST-257](https://pypost.atlassian.net/browse/PYPOST-257) | Technical debt follow-up | `PYPOST-29/60-tech-debt.md` |
| [PYPOST-258](https://pypost.atlassian.net/browse/PYPOST-258) | Technical debt follow-up | `PYPOST-29/60-tech-debt.md` |
| [PYPOST-259](https://pypost.atlassian.net/browse/PYPOST-259) | New-tab metrics coverage** ( | `PYPOST-29/60-tech-debt.md` |
| [PYPOST-260](https://pypost.atlassian.net/browse/PYPOST-260) | Tab button reposition cost** ( | `PYPOST-29/60-tech-debt.md` |
| [PYPOST-261](https://pypost.atlassian.net/browse/PYPOST-261) | Qt UI tests for new tab** ( | `PYPOST-29/60-tech-debt.md` |
| [PYPOST-262](https://pypost.atlassian.net/browse/PYPOST-262) | Tab-header component** ( | `PYPOST-29/60-tech-debt.md` |
| [PYPOST-263](https://pypost.atlassian.net/browse/PYPOST-263) | Technical debt follow-up | `PYPOST-29/60-tech-debt.md` |
| [PYPOST-264](https://pypost.atlassian.net/browse/PYPOST-264) | Technical debt follow-up | `PYPOST-29/60-tech-debt.md` |

### PYPOST-30 (15 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-265](https://pypost.atlassian.net/browse/PYPOST-265) | Manual Testing Only**: Since the automated test infrastructure (pytest) is not yet fully set up a... | `PYPOST-30/40-tech-debt.md` |
| [PYPOST-266](https://pypost.atlassian.net/browse/PYPOST-266) | None Identified**: The primary goal of this task was to improve code quality, and the changes suc... | `PYPOST-30/40-tech-debt.md` |
| [PYPOST-267](https://pypost.atlassian.net/browse/PYPOST-267) | RequestManager Indexing**: A unit test specifically ensuring that `_rebuild_index` is called corr... | `PYPOST-30/40-tech-debt.md` |
| [PYPOST-268](https://pypost.atlassian.net/browse/PYPOST-268) | HTTPClient Helper**: The new `_prepare_request_kwargs` method is now easily testable in isolation... | `PYPOST-30/40-tech-debt.md` |
| [PYPOST-269](https://pypost.atlassian.net/browse/PYPOST-269) | None**: The refactoring explicitly improved performance (O(1) lookup). | `PYPOST-30/40-tech-debt.md` |
| [PYPOST-270](https://pypost.atlassian.net/browse/PYPOST-270) | Add unit tests for `RequestManager` index integrity. | `PYPOST-30/40-tech-debt.md` |
| [PYPOST-271](https://pypost.atlassian.net/browse/PYPOST-271) | Add unit tests for `HTTPClient._prepare_request_kwargs`. | `PYPOST-30/40-tech-debt.md` |
| [PYPOST-272](https://pypost.atlassian.net/browse/PYPOST-272) | Sparse Makefile logging** ( | `PYPOST-30/60-tech-debt.md` |
| [PYPOST-273](https://pypost.atlassian.net/browse/PYPOST-273) | Flake8 debt outside this task** ( | `PYPOST-30/60-tech-debt.md` |
| [PYPOST-274](https://pypost.atlassian.net/browse/PYPOST-274) | No Makefile automation tests** ( | `PYPOST-30/60-tech-debt.md` |
| [PYPOST-275](https://pypost.atlassian.net/browse/PYPOST-275) | Pytest collection empty** ( | `PYPOST-30/60-tech-debt.md` |
| [PYPOST-276](https://pypost.atlassian.net/browse/PYPOST-276) | CI install cost** ( | `PYPOST-30/60-tech-debt.md` |
| [PYPOST-277](https://pypost.atlassian.net/browse/PYPOST-277) | Automate Make target checks** ( | `PYPOST-30/60-tech-debt.md` |
| [PYPOST-278](https://pypost.atlassian.net/browse/PYPOST-278) | CI dependency caching** ( | `PYPOST-30/60-tech-debt.md` |
| [PYPOST-280](https://pypost.atlassian.net/browse/PYPOST-280) | Reduce flake8 debt** ( | `PYPOST-30/60-tech-debt.md` |

### PYPOST-31 (12 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-281](https://pypost.atlassian.net/browse/PYPOST-281) | Technical debt follow-up | `PYPOST-31/60-tech-debt.md` |
| [PYPOST-282](https://pypost.atlassian.net/browse/PYPOST-282) | Limited validation (no suite)** ( | `PYPOST-31/60-tech-debt.md` |
| [PYPOST-283](https://pypost.atlassian.net/browse/PYPOST-283) | Unstructured save logging** ( | `PYPOST-31/60-tech-debt.md` |
| [PYPOST-284](https://pypost.atlassian.net/browse/PYPOST-284) | RequestWidget: UI plus wiring** ( | `PYPOST-31/60-tech-debt.md` |
| [PYPOST-285](https://pypost.atlassian.net/browse/PYPOST-285) | Technical debt follow-up | `PYPOST-31/60-tech-debt.md` |
| [PYPOST-286](https://pypost.atlassian.net/browse/PYPOST-286) | Technical debt follow-up | `PYPOST-31/60-tech-debt.md` |
| [PYPOST-287](https://pypost.atlassian.net/browse/PYPOST-287) | Technical debt follow-up | `PYPOST-31/60-tech-debt.md` |
| [PYPOST-288](https://pypost.atlassian.net/browse/PYPOST-288) | Technical debt follow-up | `PYPOST-31/60-tech-debt.md` |
| [PYPOST-289](https://pypost.atlassian.net/browse/PYPOST-289) | Technical debt follow-up | `PYPOST-31/60-tech-debt.md` |
| [PYPOST-290](https://pypost.atlassian.net/browse/PYPOST-290) | Qt UI tests for Save** ( | `PYPOST-31/60-tech-debt.md` |
| [PYPOST-291](https://pypost.atlassian.net/browse/PYPOST-291) | Technical debt follow-up | `PYPOST-31/60-tech-debt.md` |
| [PYPOST-292](https://pypost.atlassian.net/browse/PYPOST-292) | Technical debt follow-up | `PYPOST-31/60-tech-debt.md` |

### PYPOST-32 (10 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-293](https://pypost.atlassian.net/browse/PYPOST-293) | Manual `+` button geometry** ( | `PYPOST-32/60-tech-debt.md` |
| [PYPOST-294](https://pypost.atlassian.net/browse/PYPOST-294) | Untyped new-tab source field** ( | `PYPOST-32/60-tech-debt.md` |
| [PYPOST-295](https://pypost.atlassian.net/browse/PYPOST-295) | MainWindow still a god object** ( | `PYPOST-32/60-tech-debt.md` |
| [PYPOST-296](https://pypost.atlassian.net/browse/PYPOST-296) | Hardcoded tab-button spacing** ( | `PYPOST-32/60-tech-debt.md` |
| [PYPOST-297](https://pypost.atlassian.net/browse/PYPOST-297) | Technical debt follow-up | `PYPOST-32/60-tech-debt.md` |
| [PYPOST-298](https://pypost.atlassian.net/browse/PYPOST-298) | Technical debt follow-up | `PYPOST-32/60-tech-debt.md` |
| [PYPOST-299](https://pypost.atlassian.net/browse/PYPOST-299) | New-tab metrics coverage** ( | `PYPOST-32/60-tech-debt.md` |
| [PYPOST-300](https://pypost.atlassian.net/browse/PYPOST-300) | Tab button reposition cost** ( | `PYPOST-32/60-tech-debt.md` |
| [PYPOST-301](https://pypost.atlassian.net/browse/PYPOST-301) | Qt UI tests for new tab** ( | `PYPOST-32/60-tech-debt.md` |
| [PYPOST-302](https://pypost.atlassian.net/browse/PYPOST-302) | Tab-header component** ( | `PYPOST-32/60-tech-debt.md` |

### PYPOST-33 (5 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-305](https://pypost.atlassian.net/browse/PYPOST-305) | Sparse Makefile logging** ( | `PYPOST-33/60-tech-debt.md` |
| [PYPOST-306](https://pypost.atlassian.net/browse/PYPOST-306) | Flake8 debt outside this task** ( | `PYPOST-33/60-tech-debt.md` |
| [PYPOST-308](https://pypost.atlassian.net/browse/PYPOST-308) | Pytest collection empty** ( | `PYPOST-33/60-tech-debt.md` |
| [PYPOST-309](https://pypost.atlassian.net/browse/PYPOST-309) | CI install cost** ( | `PYPOST-33/60-tech-debt.md` |
| [PYPOST-313](https://pypost.atlassian.net/browse/PYPOST-313) | Reduce flake8 debt** ( | `PYPOST-33/60-tech-debt.md` |

### PYPOST-34 (7 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-314](https://pypost.atlassian.net/browse/PYPOST-314) | Technical debt follow-up | `PYPOST-34/60-tech-debt.md` |
| [PYPOST-315](https://pypost.atlassian.net/browse/PYPOST-315) | Noisy global flake8 baseline** ( | `PYPOST-34/60-tech-debt.md` |
| [PYPOST-316](https://pypost.atlassian.net/browse/PYPOST-316) | Save flows in MainWindow** ( | `PYPOST-34/60-tech-debt.md` |
| [PYPOST-318](https://pypost.atlassian.net/browse/PYPOST-318) | Technical debt follow-up | `PYPOST-34/60-tech-debt.md` |
| [PYPOST-319](https://pypost.atlassian.net/browse/PYPOST-319) | Save As reloads full tree** ( | `PYPOST-34/60-tech-debt.md` |
| [PYPOST-321](https://pypost.atlassian.net/browse/PYPOST-321) | Technical debt follow-up | `PYPOST-34/60-tech-debt.md` |
| [PYPOST-322](https://pypost.atlassian.net/browse/PYPOST-322) | Technical debt follow-up | `PYPOST-34/60-tech-debt.md` |

### PYPOST-35 (17 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-324](https://pypost.atlassian.net/browse/PYPOST-324) | Technical debt follow-up | `PYPOST-35/60-tech-debt.md` |
| [PYPOST-325](https://pypost.atlassian.net/browse/PYPOST-325) | Technical debt follow-up | `PYPOST-35/60-tech-debt.md` |
| [PYPOST-326](https://pypost.atlassian.net/browse/PYPOST-326) | Technical debt follow-up | `PYPOST-35/60-tech-debt.md` |
| [PYPOST-327](https://pypost.atlassian.net/browse/PYPOST-327) | Name-based storage filenames** ( | `PYPOST-35/60-tech-debt.md` |
| [PYPOST-328](https://pypost.atlassian.net/browse/PYPOST-328) | Stale tabs after delete** ( | `PYPOST-35/60-tech-debt.md` |
| [PYPOST-329](https://pypost.atlassian.net/browse/PYPOST-329) | Technical debt follow-up | `PYPOST-35/60-tech-debt.md` |
| [PYPOST-330](https://pypost.atlassian.net/browse/PYPOST-330) | Technical debt follow-up | `PYPOST-35/60-tech-debt.md` |
| [PYPOST-331](https://pypost.atlassian.net/browse/PYPOST-331) | Technical debt follow-up | `PYPOST-35/60-tech-debt.md` |
| [PYPOST-332](https://pypost.atlassian.net/browse/PYPOST-332) | Technical debt follow-up | `PYPOST-35/60-tech-debt.md` |
| [PYPOST-333](https://pypost.atlassian.net/browse/PYPOST-333) | Technical debt follow-up | `PYPOST-35/60-tech-debt.md` |
| [PYPOST-334](https://pypost.atlassian.net/browse/PYPOST-334) | Technical debt follow-up | `PYPOST-35/60-tech-debt.md` |
| [PYPOST-335](https://pypost.atlassian.net/browse/PYPOST-335) | Technical debt follow-up | `PYPOST-35/60-tech-debt.md` |
| [PYPOST-336](https://pypost.atlassian.net/browse/PYPOST-336) | Technical debt follow-up | `PYPOST-35/60-tech-debt.md` |
| [PYPOST-337](https://pypost.atlassian.net/browse/PYPOST-337) | Technical debt follow-up | `PYPOST-35/60-tech-debt.md` |
| [PYPOST-338](https://pypost.atlassian.net/browse/PYPOST-338) | Technical debt follow-up | `PYPOST-35/60-tech-debt.md` |
| [PYPOST-339](https://pypost.atlassian.net/browse/PYPOST-339) | Technical debt follow-up | `PYPOST-35/60-tech-debt.md` |
| [PYPOST-340](https://pypost.atlassian.net/browse/PYPOST-340) | Technical debt follow-up | `PYPOST-35/60-tech-debt.md` |

### PYPOST-36 (7 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-341](https://pypost.atlassian.net/browse/PYPOST-341) | Inline rename without delegate** ( | `PYPOST-36/60-tech-debt.md` |
| [PYPOST-343](https://pypost.atlassian.net/browse/PYPOST-343) | Monolithic MainWindow** ( | `PYPOST-36/60-tech-debt.md` |
| [PYPOST-344](https://pypost.atlassian.net/browse/PYPOST-344) | Duplicated error handling** ( | `PYPOST-36/60-tech-debt.md` |
| [PYPOST-347](https://pypost.atlassian.net/browse/PYPOST-347) | Full tree reload on rename** ( | `PYPOST-36/60-tech-debt.md` |
| [PYPOST-349](https://pypost.atlassian.net/browse/PYPOST-349) | Technical debt follow-up | `PYPOST-36/60-tech-debt.md` |
| [PYPOST-350](https://pypost.atlassian.net/browse/PYPOST-350) | Storage collision policy** ( | `PYPOST-36/60-tech-debt.md` |
| [PYPOST-351](https://pypost.atlassian.net/browse/PYPOST-351) | Technical debt follow-up | `PYPOST-36/60-tech-debt.md` |

### PYPOST-37 (13 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-352](https://pypost.atlassian.net/browse/PYPOST-352) | Search GUI tests skipped in CI** ( | `PYPOST-37/60-tech-debt.md` |
| [PYPOST-353](https://pypost.atlassian.net/browse/PYPOST-353) | Search input without debounce** ( | `PYPOST-37/60-tech-debt.md` |
| [PYPOST-354](https://pypost.atlassian.net/browse/PYPOST-354) | Duplicate search nav logging** ( | `PYPOST-37/60-tech-debt.md` |
| [PYPOST-355](https://pypost.atlassian.net/browse/PYPOST-355) | Hardcoded search UI strings** ( | `PYPOST-37/60-tech-debt.md` |
| [PYPOST-356](https://pypost.atlassian.net/browse/PYPOST-356) | ResponseView search untested** ( | `PYPOST-37/60-tech-debt.md` |
| [PYPOST-357](https://pypost.atlassian.net/browse/PYPOST-357) | Technical debt follow-up | `PYPOST-37/60-tech-debt.md` |
| [PYPOST-358](https://pypost.atlassian.net/browse/PYPOST-358) | Full-document match counting** ( | `PYPOST-37/60-tech-debt.md` |
| [PYPOST-359](https://pypost.atlassian.net/browse/PYPOST-359) | Keystroke-driven full scans** ( | `PYPOST-37/60-tech-debt.md` |
| [PYPOST-360](https://pypost.atlassian.net/browse/PYPOST-360) | Technical debt follow-up | `PYPOST-37/60-tech-debt.md` |
| [PYPOST-361](https://pypost.atlassian.net/browse/PYPOST-361) | Technical debt follow-up | `PYPOST-37/60-tech-debt.md` |
| [PYPOST-362](https://pypost.atlassian.net/browse/PYPOST-362) | Technical debt follow-up | `PYPOST-37/60-tech-debt.md` |
| [PYPOST-364](https://pypost.atlassian.net/browse/PYPOST-364) | Technical debt follow-up | `PYPOST-37/60-tech-debt.md` |
| [PYPOST-365](https://pypost.atlassian.net/browse/PYPOST-365) | Technical debt follow-up | `PYPOST-37/60-tech-debt.md` |

### PYPOST-38 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-366](https://pypost.atlassian.net/browse/PYPOST-366) | Technical debt follow-up | `PYPOST-38/60-tech-debt.md` |
| [PYPOST-370](https://pypost.atlassian.net/browse/PYPOST-370) | Technical debt follow-up | `PYPOST-38/60-tech-debt.md` |
| [PYPOST-371](https://pypost.atlassian.net/browse/PYPOST-371) | Technical debt follow-up | `PYPOST-38/60-tech-debt.md` |
| [PYPOST-372](https://pypost.atlassian.net/browse/PYPOST-372) | Technical debt follow-up | `PYPOST-38/60-tech-debt.md` |

### PYPOST-40 (11 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-373](https://pypost.atlassian.net/browse/PYPOST-373) | No radon/pylint/deps graph** ( | `PYPOST-40/60-tech-debt.md` |
| [PYPOST-374](https://pypost.atlassian.net/browse/PYPOST-374) | Dialogs audited as a group** ( | `PYPOST-40/60-tech-debt.md` |
| [PYPOST-375](https://pypost.atlassian.net/browse/PYPOST-375) | utils/ scope unclear** ( | `PYPOST-40/60-tech-debt.md` |
| [PYPOST-376](https://pypost.atlassian.net/browse/PYPOST-376) | No regression baseline metrics** ( | `PYPOST-40/60-tech-debt.md` |
| [PYPOST-377](https://pypost.atlassian.net/browse/PYPOST-377) | Technical debt follow-up | `PYPOST-40/60-tech-debt.md` |
| [PYPOST-378](https://pypost.atlassian.net/browse/PYPOST-378) | Technical debt follow-up | `PYPOST-40/60-tech-debt.md` |
| [PYPOST-380](https://pypost.atlassian.net/browse/PYPOST-380) | Technical debt follow-up | `PYPOST-40/60-tech-debt.md` |
| [PYPOST-381](https://pypost.atlassian.net/browse/PYPOST-381) | Technical debt follow-up | `PYPOST-40/60-tech-debt.md` |
| [PYPOST-382](https://pypost.atlassian.net/browse/PYPOST-382) | Testability gaps** ( | `PYPOST-40/60-tech-debt.md` |
| [PYPOST-383](https://pypost.atlassian.net/browse/PYPOST-383) | Technical debt follow-up | `PYPOST-40/60-tech-debt.md` |
| [PYPOST-384](https://pypost.atlassian.net/browse/PYPOST-384) | Technical debt follow-up | `PYPOST-40/60-tech-debt.md` |

### PYPOST-41 (8 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-58](https://pypost.atlassian.net/browse/PYPOST-58) | Debt item (line 13) | `PYPOST-41/60-review.md` |
| [PYPOST-59](https://pypost.atlassian.net/browse/PYPOST-59) | Debt item (line 28) | `PYPOST-41/60-review.md` |
| [PYPOST-60](https://pypost.atlassian.net/browse/PYPOST-60) | Debt item (line 40) | `PYPOST-41/60-review.md` |
| [PYPOST-61](https://pypost.atlassian.net/browse/PYPOST-61) | Debt item (line 52) | `PYPOST-41/60-review.md` |
| [PYPOST-62](https://pypost.atlassian.net/browse/PYPOST-62) | Debt item (line 65) | `PYPOST-41/60-review.md` |
| [PYPOST-63](https://pypost.atlassian.net/browse/PYPOST-63) | Debt item (line 78) | `PYPOST-41/60-review.md` |
| [PYPOST-64](https://pypost.atlassian.net/browse/PYPOST-64) | Debt item (line 93) | `PYPOST-41/60-review.md` |
| [PYPOST-65](https://pypost.atlassian.net/browse/PYPOST-65) | Debt item (line 107) | `PYPOST-41/60-review.md` |

### PYPOST-42 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-385](https://pypost.atlassian.net/browse/PYPOST-385) | Auto-switch metric untested** ( | `PYPOST-42/60-tech-debt.md` |
| [PYPOST-614](https://pypost.atlassian.net/browse/PYPOST-614) | `QT_QPA_PLATFORM` not in Makefile `test` \| Low \| `Makefile` \| UI tests fail in CI without it \| | `PYPOST-42/60-tech-debt.md` |

### PYPOST-43 (7 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-66](https://pypost.atlassian.net/browse/PYPOST-66) | Debt item (line 16) | `PYPOST-43/60-review.md` |
| [PYPOST-67](https://pypost.atlassian.net/browse/PYPOST-67) | Debt item (line 34) | `PYPOST-43/60-review.md` |
| [PYPOST-69](https://pypost.atlassian.net/browse/PYPOST-69) | Debt item (line 62) | `PYPOST-43/60-review.md` |
| [PYPOST-70](https://pypost.atlassian.net/browse/PYPOST-70) | Debt item (line 74) | `PYPOST-43/60-review.md` |
| [PYPOST-71](https://pypost.atlassian.net/browse/PYPOST-71) | Debt item (line 89) | `PYPOST-43/60-review.md` |
| [PYPOST-72](https://pypost.atlassian.net/browse/PYPOST-72) | Debt item (line 114) | `PYPOST-43/60-review.md` |
| [PYPOST-73](https://pypost.atlassian.net/browse/PYPOST-73) | Debt item (line 128) | `PYPOST-43/60-review.md` |

### PYPOST-44 (7 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-74](https://pypost.atlassian.net/browse/PYPOST-74) | TD-1: No `IMetricsManager` protocol/interface (Low | `PYPOST-44/60-review.md` |
| [PYPOST-75](https://pypost.atlassian.net/browse/PYPOST-75) | TD-2: `None`-guard pattern repeated at every call site (Low) | `PYPOST-44/60-review.md` |
| [PYPOST-76](https://pypost.atlassian.net/browse/PYPOST-76) | TD-3: `MetricsManager` bundles two unrelated concerns (Medium) | `PYPOST-44/60-review.md` |
| [PYPOST-77](https://pypost.atlassian.net/browse/PYPOST-77) | TD-4: `_extract_mcp_variables` dead-code path in `MCPServerImpl` (Low) | `PYPOST-44/60-review.md` |
| [PYPOST-78](https://pypost.atlassian.net/browse/PYPOST-78) | TD-5: `import re` inside method body in `MCPServerImpl` (Low) | `PYPOST-44/60-review.md` |
| [PYPOST-79](https://pypost.atlassian.net/browse/PYPOST-79) | TD-6: Trailing whitespace in `pypost/core/http_client.py` (Low) | `PYPOST-44/60-review.md` |
| [PYPOST-80](https://pypost.atlassian.net/browse/PYPOST-80) | TD-7: No unit tests for `MetricsManager` tracking methods (Medium) | `PYPOST-44/60-review.md` |

### PYPOST-45 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-81](https://pypost.atlassian.net/browse/PYPOST-81) | Debt item (line 22) | `PYPOST-45/60-review.md` |
| [PYPOST-82](https://pypost.atlassian.net/browse/PYPOST-82) | Debt item (line 32) | `PYPOST-45/60-review.md` |

### PYPOST-46 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-51](https://pypost.atlassian.net/browse/PYPOST-51) | Technical debt follow-up | `PYPOST-46/60-tech-debt.md` |

### PYPOST-47 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-629](https://pypost.atlassian.net/browse/PYPOST-629) | Low \| Optional: user-facing “Reload collections from disk” menu action calling `load_collections(... | `PYPOST-47/60-tech-debt.md` |
| [PYPOST-630](https://pypost.atlassian.net/browse/PYPOST-630) | Low \| Optional: unify `FakeRequestManager` with `tests.helpers.FakeStorageManager` \| | `PYPOST-47/60-tech-debt.md` |

### PYPOST-48 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-634](https://pypost.atlassian.net/browse/PYPOST-634) | Low \| If a third tree item type is added, register it in `DEFAULT_COLLECTION_ITEM_STRATEGIES` \| | `PYPOST-48/60-tech-debt.md` |

### PYPOST-52 (7 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-83](https://pypost.atlassian.net/browse/PYPOST-83) | Debt item (line 15) | `PYPOST-52/60-review.md` |
| [PYPOST-84](https://pypost.atlassian.net/browse/PYPOST-84) | Debt item (line 39) | `PYPOST-52/60-review.md` |
| [PYPOST-85](https://pypost.atlassian.net/browse/PYPOST-85) | Debt item (line 57) | `PYPOST-52/60-review.md` |
| [PYPOST-86](https://pypost.atlassian.net/browse/PYPOST-86) | Debt item (line 75) | `PYPOST-52/60-review.md` |
| [PYPOST-87](https://pypost.atlassian.net/browse/PYPOST-87) | Debt item (line 94) | `PYPOST-52/60-review.md` |
| [PYPOST-88](https://pypost.atlassian.net/browse/PYPOST-88) | Debt item (line 111) | `PYPOST-52/60-review.md` |
| [PYPOST-89](https://pypost.atlassian.net/browse/PYPOST-89) | Debt item (line 124) | `PYPOST-52/60-review.md` |

### PYPOST-53 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-54](https://pypost.atlassian.net/browse/PYPOST-54) | 1. **State Mutation in UI Components** ( | `PYPOST-53/60-tech-debt.md` |
| [PYPOST-56](https://pypost.atlassian.net/browse/PYPOST-56) | 3. **Missing UI Tests** ( | `PYPOST-53/60-tech-debt.md` |

### PYPOST-54 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-55](https://pypost.atlassian.net/browse/PYPOST-55) | Hardcoded UI strings in env widgets \| Low \| | `PYPOST-54/60-tech-debt.md` |
| [PYPOST-647](https://pypost.atlassian.net/browse/PYPOST-647) | Explicit OK/Cancel for discard-on-close \| Low \| Would change UX; not required for this story \| | `PYPOST-54/60-tech-debt.md` |

### PYPOST-57 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-580](https://pypost.atlassian.net/browse/PYPOST-580) | Unlinked PYPOST-52 INFO item \| **Resolved | `PYPOST-57/60-tech-debt.md` |
| [PYPOST-581](https://pypost.atlassian.net/browse/PYPOST-581) | Medium \| Bulk-fix truncated Jira summaries for all 480 linked debt issues \| | `PYPOST-57/60-tech-debt.md` |
| [PYPOST-582](https://pypost.atlassian.net/browse/PYPOST-582) | Low \| Standardize debt bullet format (PYPOST-53 table style) across legacy files \| | `PYPOST-57/60-tech-debt.md` |

### PYPOST-63 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-802](https://pypost.atlassian.net/browse/PYPOST-802) | TD-1 \| Low \| `ResolvedRequestFields` and `MaskedRequestData` share shape | `PYPOST-63/60-tech-debt.md` |

### PYPOST-66 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-672](https://pypost.atlassian.net/browse/PYPOST-672) | `main_window.py` still 260 LOC vs PYPOST-43 ≤ 150 target \| LOW \| Future PYPOST-43 chunks: layout,... | `PYPOST-66/60-tech-debt.md` |
| [PYPOST-673](https://pypost.atlassian.net/browse/PYPOST-673) | `MainWindow` class 222 LOC \| LOW \| Same | `PYPOST-66/60-tech-debt.md` |

### PYPOST-67 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-68](https://pypost.atlassian.net/browse/PYPOST-68) | TD-3 \| MEDIUM \| `EnvPresenter` exposes internal widgets via properties \| | `PYPOST-67/60-tech-debt.md` |

### PYPOST-68 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-803](https://pypost.atlassian.net/browse/PYPOST-803) | PYPOST-43 TD-1 Collections/Tabs presenter `apply_font` \| **Resolved | `PYPOST-68/60-tech-debt.md` |

### PYPOST-73 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-579](https://pypost.atlassian.net/browse/PYPOST-579) | \| Low \| [PYPOST-75](https://pypost.atlassian.net/browse/PYPOST-75) \| `NullMetrics` no-op to repla... | `PYPOST-73/60-tech-debt.md` |
| [PYPOST-674](https://pypost.atlassian.net/browse/PYPOST-674) | Facade still bundles server + counters at root \| Low \| Addressed by PYPOST-75 split; root still u... | `PYPOST-73/60-tech-debt.md` |

### PYPOST-74 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-675](https://pypost.atlassian.net/browse/PYPOST-675) | \| Low \| [PYPOST-75](https://pypost.atlassian.net/browse/PYPOST-75) \| Duplicate scope (NullMetrics... | `PYPOST-74/60-tech-debt.md` |

### PYPOST-75 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-676](https://pypost.atlassian.net/browse/PYPOST-676) | Facade still bundles registry + server at type level \| Low \| Call sites that only need counters s... | `PYPOST-75/60-tech-debt.md` |
| [PYPOST-799](https://pypost.atlassian.net/browse/PYPOST-799) | PYPOST-44 TD-2 \| Optional `MetricsProtocol` / `NullMetrics` / `None` guards at call sites \| Close... | `PYPOST-75/60-tech-debt.md` |

### PYPOST-102 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-586](https://pypost.atlassian.net/browse/PYPOST-586) | None for this closure. User-configurable JSON syntax colors in settings remain out of | `PYPOST-102/60-tech-debt.md` |

### PYPOST-115 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-13](https://pypost.atlassian.net/browse/PYPOST-13) | Multi-level chains** ( | `PYPOST-115/60-tech-debt.md` |

### PYPOST-119 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-123](https://pypost.atlassian.net/browse/PYPOST-123) | Technical debt follow-up | `PYPOST-119/60-tech-debt.md` |

### PYPOST-120 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-119](https://pypost.atlassian.net/browse/PYPOST-119) | Technical debt follow-up | `PYPOST-120/60-tech-debt.md` |

### PYPOST-122 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-124](https://pypost.atlassian.net/browse/PYPOST-124) | Technical debt follow-up | `PYPOST-122/60-tech-debt.md` |

### PYPOST-136 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-587](https://pypost.atlassian.net/browse/PYPOST-587) | `expose_as_mcp` toggle off mid-session \| Low \| Signature change triggers restart; agent may still... | `PYPOST-136/60-tech-debt.md` |

### PYPOST-143 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-588](https://pypost.atlassian.net/browse/PYPOST-588) | Remove leaf fallbacks; require explicit injection \| Low \| Future hardening \| | `PYPOST-143/60-tech-debt.md` |
| [PYPOST-589](https://pypost.atlassian.net/browse/PYPOST-589) | Inject hover `TemplateService` from presenter \| Low \| Future UI DI \| | `PYPOST-143/60-tech-debt.md` |

### PYPOST-155 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-159](https://pypost.atlassian.net/browse/PYPOST-159) | Mount + direct ASGI for SSE stream | `PYPOST-155/60-tech-debt.md` |

### PYPOST-160 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-156](https://pypost.atlassian.net/browse/PYPOST-156) | Technical debt follow-up | `PYPOST-160/60-tech-debt.md` |

### PYPOST-163 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-470](https://pypost.atlassian.net/browse/PYPOST-470) | Limited test coverage** ( | `PYPOST-163/60-review.md` |
| [PYPOST-475](https://pypost.atlassian.net/browse/PYPOST-475) | No integration tests for the full flow** ( | `PYPOST-163/60-review.md` |
| [PYPOST-476](https://pypost.atlassian.net/browse/PYPOST-476) | Negligible performance impact** ( | `PYPOST-163/60-review.md` |
| [PYPOST-478](https://pypost.atlassian.net/browse/PYPOST-478) | Consider centralizing validation** ( | `PYPOST-163/60-review.md` |

### PYPOST-171 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-590](https://pypost.atlassian.net/browse/PYPOST-590) | `start_server` may call `stop_server` while holding non-reentrant `Lock` \| Low \| Dead path in pro... | `PYPOST-171/60-tech-debt.md` |

### PYPOST-177 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-591](https://pypost.atlassian.net/browse/PYPOST-591) | Facade-only coverage in `test_metrics_manager.py` \| Low \| Complements new component tests \| | `PYPOST-177/60-tech-debt.md` |

### PYPOST-179 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-679](https://pypost.atlassian.net/browse/PYPOST-679) | TD-1 \| Low \| Makefile `generate-mcp-fixtures` target \| Convenience wrapper around the script \| Jira | `PYPOST-179/60-tech-debt.md` |

### PYPOST-180 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-593](https://pypost.atlassian.net/browse/PYPOST-593) | TD-2 \| Low \| No pytest fixture in `conftest.py` yet \| Add when PYPOST-181 needs session-scoped co... | `PYPOST-180/60-tech-debt.md` |

### PYPOST-181 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-592](https://pypost.atlassian.net/browse/PYPOST-592) | TD-1 \| Low \| Duplicate live-server harness \| Extract shared `tests/helpers/mcp_live_server.py` fr... | `PYPOST-181/60-tech-debt.md` |

### PYPOST-225 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-307](https://pypost.atlassian.net/browse/PYPOST-307) | `tests/test_makefile.py` covers Make targets; delivered via | `PYPOST-225/60-tech-debt.md` |
| [PYPOST-310](https://pypost.atlassian.net/browse/PYPOST-310) | `tests/test_makefile.py` covers Make targets; delivered via [PYPOST-307](https://pypost.atlassian... | `PYPOST-225/60-tech-debt.md` |

### PYPOST-229 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-311](https://pypost.atlassian.net/browse/PYPOST-311) | CI caching via `cache-dependency-path: requirements.txt` delivered in | `PYPOST-229/60-tech-debt.md` |

### PYPOST-230 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-279](https://pypost.atlassian.net/browse/PYPOST-279) | Exit code 5 policy in `tests/conftest.py` and `tests/test_pytest_exit_policy.py` ( | `PYPOST-230/60-tech-debt.md` |

### PYPOST-249 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-594](https://pypost.atlassian.net/browse/PYPOST-594) | Timer-fired persistence without flush in tests \| Low \| Already noted in PYPOST-386/252 debt \| | `PYPOST-249/60-tech-debt.md` |

### PYPOST-250 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-595](https://pypost.atlassian.net/browse/PYPOST-595) | Debt item (line 40) | `PYPOST-250/60-tech-debt.md` |

### PYPOST-251 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-252](https://pypost.atlassian.net/browse/PYPOST-252) | Technical debt follow-up | `PYPOST-251/60-tech-debt.md` |

### PYPOST-268 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-30](https://pypost.atlassian.net/browse/PYPOST-30) | Resolves debt from | `PYPOST-268/60-tech-debt.md` |

### PYPOST-302 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-32](https://pypost.atlassian.net/browse/PYPOST-32) | Technical debt follow-up | `PYPOST-302/60-tech-debt.md` |
| [PYPOST-303](https://pypost.atlassian.net/browse/PYPOST-303) | Technical debt follow-up | `PYPOST-302/60-tech-debt.md` |
| [PYPOST-304](https://pypost.atlassian.net/browse/PYPOST-304) | Technical debt follow-up | `PYPOST-302/60-tech-debt.md` |

### PYPOST-310 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-312](https://pypost.atlassian.net/browse/PYPOST-312) | Pytest exit code 5 policy** — existing debt | `PYPOST-310/60-tech-debt.md` |

### PYPOST-312 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-33](https://pypost.atlassian.net/browse/PYPOST-33) | question from | `PYPOST-312/60-tech-debt.md` |

### PYPOST-316 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-320](https://pypost.atlassian.net/browse/PYPOST-320) | Add GUI-level tests for save and save-as behavior | `PYPOST-316/60-tech-debt.md` |
| [PYPOST-323](https://pypost.atlassian.net/browse/PYPOST-323) | Repository-wide lint debt | `PYPOST-316/60-tech-debt.md` |

### PYPOST-319 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-596](https://pypost.atlassian.net/browse/PYPOST-596) | Low \| Consider incremental tree update for regular save when only one request changes \| | `PYPOST-319/60-tech-debt.md` |
| [PYPOST-597](https://pypost.atlassian.net/browse/PYPOST-597) | Low \| GUI save-as tests (PYPOST-320) \| | `PYPOST-319/60-tech-debt.md` |

### PYPOST-321 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-317](https://pypost.atlassian.net/browse/PYPOST-317) | Save-as tab rebinding edge cases \| Deferred \| | `PYPOST-321/60-tech-debt.md` |

### PYPOST-324 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-537](https://pypost.atlassian.net/browse/PYPOST-537) | Technical debt follow-up | `PYPOST-324/60-tech-debt.md` |

### PYPOST-329 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-538](https://pypost.atlassian.net/browse/PYPOST-538) | Technical debt follow-up | `PYPOST-329/60-tech-debt.md` |

### PYPOST-341 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-342](https://pypost.atlassian.net/browse/PYPOST-342) | Rename tests omit GUI** ( | `PYPOST-341/60-tech-debt.md` |
| [PYPOST-348](https://pypost.atlassian.net/browse/PYPOST-348) | Add GUI integration tests for context-menu rename lifecycle | `PYPOST-341/60-tech-debt.md` |

### PYPOST-342 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-345](https://pypost.atlassian.net/browse/PYPOST-345) | End-to-end rename via delegate editor** ( | `PYPOST-342/60-tech-debt.md` |
| [PYPOST-346](https://pypost.atlassian.net/browse/PYPOST-346) | Storage collision on collection rename** ( | `PYPOST-342/60-tech-debt.md` |

### PYPOST-344 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-539](https://pypost.atlassian.net/browse/PYPOST-539) | collection flows). | `PYPOST-344/60-tech-debt.md` |

### PYPOST-364 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-363](https://pypost.atlassian.net/browse/PYPOST-363) | Keystroke debounce:** Remains out of scope ( | `PYPOST-364/60-tech-debt.md` |

### PYPOST-366 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-367](https://pypost.atlassian.net/browse/PYPOST-367) | No unit tests for MCPServerImpl or MCP routing \| | `PYPOST-366/60-tech-debt.md` |
| [PYPOST-369](https://pypost.atlassian.net/browse/PYPOST-369) | do-testing.md vs automated pytest \| | `PYPOST-366/60-tech-debt.md` |

### PYPOST-367 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-368](https://pypost.atlassian.net/browse/PYPOST-368) | Live MCP client integration (tool list + call over SSE) | `PYPOST-367/60-tech-debt.md` |

### PYPOST-370 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-563](https://pypost.atlassian.net/browse/PYPOST-563) | Technical debt follow-up | `PYPOST-370/60-tech-debt.md` |
| [PYPOST-564](https://pypost.atlassian.net/browse/PYPOST-564) | Technical debt follow-up | `PYPOST-370/60-tech-debt.md` |

### PYPOST-374 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-598](https://pypost.atlassian.net/browse/PYPOST-598) | D1 \| `SettingsDialog` multi-domain SRP violation (423 LOC) \| High \| | `PYPOST-374/60-tech-debt.md` |
| [PYPOST-599](https://pypost.atlassian.net/browse/PYPOST-599) | D2 \| `HotkeysDialog` hardcoded shortcuts vs app actions \| Medium \| | `PYPOST-374/60-tech-debt.md` |
| [PYPOST-601](https://pypost.atlassian.net/browse/PYPOST-601) | D4 \| Hardcoded About version \| Low \| | `PYPOST-374/60-tech-debt.md` |

### PYPOST-382 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-43](https://pypost.atlassian.net/browse/PYPOST-43) | RequestWorker / MCPServerImpl | `PYPOST-382/60-tech-debt.md` |
| [PYPOST-46](https://pypost.atlassian.net/browse/PYPOST-46) | No HTTPClient protocol** ( | `PYPOST-382/60-tech-debt.md` |
| [PYPOST-379](https://pypost.atlassian.net/browse/PYPOST-379) | 1. [PYPOST-46](https://pypost.atlassian.net/browse/PYPOST-46) — HTTPClient protocol | `PYPOST-382/60-tech-debt.md` |

### PYPOST-388 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-390](https://pypost.atlassian.net/browse/PYPOST-390) | Linear search on restore at scale | `PYPOST-388/60-tech-debt.md` |

### PYPOST-390 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-386](https://pypost.atlassian.net/browse/PYPOST-386) | Synchronous tree-state saves on each expand/collapse | `PYPOST-390/60-tech-debt.md` |

### PYPOST-395 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-603](https://pypost.atlassian.net/browse/PYPOST-603) | Add `AppSettings.theme` and settings UI for explicit light/dark/system choice. | `PYPOST-395/60-tech-debt.md` |
| [PYPOST-604](https://pypost.atlassian.net/browse/PYPOST-604) | Optional user-configurable JSON syntax colors in settings. | `PYPOST-395/60-tech-debt.md` |

### PYPOST-400 (5 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-409](https://pypost.atlassian.net/browse/PYPOST-409) | Debt item (line 30) | `PYPOST-400/60-review.md` |
| [PYPOST-410](https://pypost.atlassian.net/browse/PYPOST-410) | Debt item (line 44) | `PYPOST-400/60-review.md` |
| [PYPOST-411](https://pypost.atlassian.net/browse/PYPOST-411) | Debt item (line 59) | `PYPOST-400/60-review.md` |
| [PYPOST-413](https://pypost.atlassian.net/browse/PYPOST-413) | Debt item (line 87) | `PYPOST-400/60-review.md` |
| [PYPOST-414](https://pypost.atlassian.net/browse/PYPOST-414) | Debt item (line 100) | `PYPOST-400/60-review.md` |

### PYPOST-401 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-415](https://pypost.atlassian.net/browse/PYPOST-415) | TD-1: `_reset_tab_ui_state` clears `sender_tab.worker = None` asynchronously via Qt signals ( | `PYPOST-401/60-review.md` |
| [PYPOST-416](https://pypost.atlassian.net/browse/PYPOST-416) | TD-2: No test for the `stale_worker_cleared` log path (RC-3 observable path) ( | `PYPOST-401/60-review.md` |
| [PYPOST-417](https://pypost.atlassian.net/browse/PYPOST-417) | TD-3: `RequestWorker` is not reusable after `stop()` ( | `PYPOST-401/60-review.md` |

### PYPOST-402 (7 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-418](https://pypost.atlassian.net/browse/PYPOST-418) | TD-1: `AlertManager` never injected into `RequestWorker` ( | `PYPOST-402/60-review.md` |
| [PYPOST-419](https://pypost.atlassian.net/browse/PYPOST-419) | TD-2: `AppSettings.default_retry_policy` is persisted but never applied ( | `PYPOST-402/60-review.md` |
| [PYPOST-420](https://pypost.atlassian.net/browse/PYPOST-420) | TD-3: Logger accumulation in `AlertManager` ( | `PYPOST-402/60-review.md` |
| [PYPOST-421](https://pypost.atlassian.net/browse/PYPOST-421) | TD-4: Bare `assert` in production retry path ( | `PYPOST-402/60-review.md` |
| [PYPOST-422](https://pypost.atlassian.net/browse/PYPOST-422) | TD-5: `email_notification_failures_total` metric name is misleading ( | `PYPOST-402/60-review.md` |
| [PYPOST-423](https://pypost.atlassian.net/browse/PYPOST-423) | TD-6: `retryable_codes_edit` silently drops invalid input ( | `PYPOST-402/60-review.md` |
| [PYPOST-424](https://pypost.atlassian.net/browse/PYPOST-424) | TD-7: `request_timeout` spin box created but never added to form layout ( | `PYPOST-402/60-review.md` |

### PYPOST-404 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-425](https://pypost.atlassian.net/browse/PYPOST-425) | Debt item (line 25) | `PYPOST-404/60-review.md` |

### PYPOST-406 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-605](https://pypost.atlassian.net/browse/PYPOST-605) | Low \| Optional: `track_gui_new_tab_action("collections_click")` on left-click for metric parity \| | `PYPOST-406/60-tech-debt.md` |
| [PYPOST-606](https://pypost.atlassian.net/browse/PYPOST-606) | Low \| Optional: merge `open_request_in_tab` / `open_request_in_isolated_tab` if product wants one... | `PYPOST-406/60-tech-debt.md` |
| [PYPOST-607](https://pypost.atlassian.net/browse/PYPOST-607) | Low \| Optional: integration test via `MainWindow` for full open path \| | `PYPOST-406/60-tech-debt.md` |

### PYPOST-407 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-608](https://pypost.atlassian.net/browse/PYPOST-608) | Low \| Optional: profile tab-open with multi-MB bodies if users store huge drafts \| | `PYPOST-407/60-tech-debt.md` |
| [PYPOST-609](https://pypost.atlassian.net/browse/PYPOST-609) | Low \| Optional: field hashing in `persisted_fields_equal` if sibling sync becomes hot \| | `PYPOST-407/60-tech-debt.md` |

### PYPOST-410 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-412](https://pypost.atlassian.net/browse/PYPOST-412) | \|----------\|------\|-------\| | `PYPOST-410/60-tech-debt.md` |
| [PYPOST-610](https://pypost.atlassian.net/browse/PYPOST-610) | Low \| History masking re-renders URL \| `SensitiveDataMaskingPolicy` renders templates again for h... | `PYPOST-410/60-tech-debt.md` |
| [PYPOST-611](https://pypost.atlassian.net/browse/PYPOST-611) | Low \| `TemplateService` silent fallback \| Render errors return original content; strict template ... | `PYPOST-410/60-tech-debt.md` |

### PYPOST-413 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-612](https://pypost.atlassian.net/browse/PYPOST-612) | TD-5 \| `_on_request_error` cancellation check on `ExecutionError.detail` imprecise \| `ErrorCatego... | `PYPOST-413/60-tech-debt.md` |

### PYPOST-415 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-613](https://pypost.atlassian.net/browse/PYPOST-613) | TD-1 (PYPOST-401) \| `_reset_tab_ui_state` cleared worker asynchronously via mixed UI/lifecycle he... | `PYPOST-415/60-tech-debt.md` |

### PYPOST-425 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-426](https://pypost.atlassian.net/browse/PYPOST-426) | Technical debt follow-up | `PYPOST-425/60-tech-debt.md` |

### PYPOST-426 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-427](https://pypost.atlassian.net/browse/PYPOST-427) | `main.py` ConfigManager ordering** ( | `PYPOST-426/60-tech-debt.md` |

### PYPOST-429 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-615](https://pypost.atlassian.net/browse/PYPOST-615) | Migrate `TestOnRequestError` to pytest + `qapp` \| Low \| | `PYPOST-429/60-tech-debt.md` |

### PYPOST-430 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-616](https://pypost.atlassian.net/browse/PYPOST-616) | TD-3 \| Low \| SSE probe without explicit Accept uses default timeout until headers \| Acceptable; p... | `PYPOST-430/60-tech-debt.md` |

### PYPOST-432 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-565](https://pypost.atlassian.net/browse/PYPOST-565) | Debt item (line 28) | `PYPOST-432/60-tech-debt.md` |

### PYPOST-433 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-617](https://pypost.atlassian.net/browse/PYPOST-617) | Inline rename delegate validation via F2 \| Low \| Rename validation covered via `_apply_environmen... | `PYPOST-433/60-tech-debt.md` |
| [PYPOST-618](https://pypost.atlassian.net/browse/PYPOST-618) | Full QMenu integration without mocking `QMenu` class \| Low \| Context-menu copy smoke test mocks m... | `PYPOST-433/60-tech-debt.md` |
| [PYPOST-619](https://pypost.atlassian.net/browse/PYPOST-619) | `add_environment` whitespace-only name \| Low \| Add path treats falsy `name` as no-op; copy empty-... | `PYPOST-433/60-tech-debt.md` |

### PYPOST-435 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-496](https://pypost.atlassian.net/browse/PYPOST-496) | Technical debt follow-up | `PYPOST-435/60-tech-debt.md` |
| [PYPOST-498](https://pypost.atlassian.net/browse/PYPOST-498) | Technical debt follow-up | `PYPOST-435/60-tech-debt.md` |

### PYPOST-439 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-620](https://pypost.atlassian.net/browse/PYPOST-620) | E2E: Settings save → `settings.json` round-trip for alert fields \| Low \| Covered indirectly by di... | `PYPOST-439/60-tech-debt.md` |
| [PYPOST-621](https://pypost.atlassian.net/browse/PYPOST-621) | Main window reload of `AlertManager` after settings save \| Medium \| Pre-existing gap \| | `PYPOST-439/60-tech-debt.md` |
| [PYPOST-622](https://pypost.atlassian.net/browse/PYPOST-622) | Rebuild or reconfigure `AlertManager` when alert settings change \| Medium \| `MainWindow.apply_set... | `PYPOST-439/60-tech-debt.md` |

### PYPOST-443 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-558](https://pypost.atlassian.net/browse/PYPOST-558) | Technical debt follow-up | `PYPOST-443/60-tech-debt.md` |
| [PYPOST-623](https://pypost.atlassian.net/browse/PYPOST-623) | Remove deprecated alias after sunset \| Low \| Follow-up | `PYPOST-443/60-tech-debt.md` |
| [PYPOST-624](https://pypost.atlassian.net/browse/PYPOST-624) | `doc/dev/testing.md` metric table omits retry exhaustion series \| Low \| Non-blocker; covered in m... | `PYPOST-443/60-tech-debt.md` |

### PYPOST-444 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-625](https://pypost.atlassian.net/browse/PYPOST-625) | reasons — low value given parser unit tests. | `PYPOST-444/60-tech-debt.md` |

### PYPOST-445 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-626](https://pypost.atlassian.net/browse/PYPOST-626) | `StateManager` load reflects timeout | `PYPOST-445/60-tech-debt.md` |

### PYPOST-446 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-463](https://pypost.atlassian.net/browse/PYPOST-463) | Refactor `RequestService.execute` history-recording block into dedicated helpers to reduce method | `PYPOST-446/60-tech-debt.md` |
| [PYPOST-464](https://pypost.atlassian.net/browse/PYPOST-464) | when `hidden_keys` is empty. **Closed | `PYPOST-446/60-tech-debt.md` |

### PYPOST-447 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-481](https://pypost.atlassian.net/browse/PYPOST-481) | user-facing application settings. | `PYPOST-447/60-tech-debt.md` |
| [PYPOST-484](https://pypost.atlassian.net/browse/PYPOST-484) | Suggested improvement: represent payload via typed model to centralize validation rules. | `PYPOST-447/60-tech-debt.md` |
| [PYPOST-486](https://pypost.atlassian.net/browse/PYPOST-486) | cause visible UI pauses during load/save actions. | `PYPOST-447/60-tech-debt.md` |

### PYPOST-448 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-448](https://pypost.atlassian.net/browse/PYPOST-448) | All tickets: type **Debt**, linked to | `PYPOST-448/60-tech-debt.md` |
| [PYPOST-490](https://pypost.atlassian.net/browse/PYPOST-490) | tests but not wired in one flow. | `PYPOST-448/60-tech-debt.md` |
| [PYPOST-627](https://pypost.atlassian.net/browse/PYPOST-627) | change is silent in logs; only the checkbox state in `settings.json` records the preference. | `PYPOST-448/60-tech-debt.md` |

### PYPOST-450 (8 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-451](https://pypost.atlassian.net/browse/PYPOST-451) | Technical debt follow-up | `PYPOST-450/60-tech-debt.md` |
| [PYPOST-452](https://pypost.atlassian.net/browse/PYPOST-452) | Technical debt follow-up | `PYPOST-450/60-tech-debt.md` |
| [PYPOST-453](https://pypost.atlassian.net/browse/PYPOST-453) | Technical debt follow-up | `PYPOST-450/60-tech-debt.md` |
| [PYPOST-455](https://pypost.atlassian.net/browse/PYPOST-455) | Acceptable now; revisit via | `PYPOST-450/60-tech-debt.md` |
| [PYPOST-456](https://pypost.atlassian.net/browse/PYPOST-456) | 5 \| Documentation and catalog examples \| **Met** \| `doc/dev/template_expression_functions.md` (ST... | `PYPOST-450/60-tech-debt.md` |
| [PYPOST-457](https://pypost.atlassian.net/browse/PYPOST-457) | Technical debt follow-up | `PYPOST-450/60-tech-debt.md` |
| [PYPOST-459](https://pypost.atlassian.net/browse/PYPOST-459) | instance, rebuilt via `set_metrics()`. Practical for reuse; less explicit than instance DI | `PYPOST-450/60-tech-debt.md` |
| [PYPOST-460](https://pypost.atlassian.net/browse/PYPOST-460) | Duplicate regex scans:** Counting and validation each walk all `{{...}}` tokens | `PYPOST-450/60-tech-debt.md` |

### PYPOST-451 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-450](https://pypost.atlassian.net/browse/PYPOST-450) | Technical debt follow-up | `PYPOST-451/60-tech-debt.md` |
| [PYPOST-458](https://pypost.atlassian.net/browse/PYPOST-458) | Technical debt follow-up | `PYPOST-451/60-tech-debt.md` |

### PYPOST-453 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-454](https://pypost.atlassian.net/browse/PYPOST-454) | ~~Malformed nested expressions, unbalanced depth edge cases, and spacing variants across all | `PYPOST-453/60-tech-debt.md` |

### PYPOST-455 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-628](https://pypost.atlassian.net/browse/PYPOST-628) | `20-architecture.md` (`lru_cache` on compile, `maxsize=256`). | `PYPOST-455/60-tech-debt.md` |

### PYPOST-457 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-461](https://pypost.atlassian.net/browse/PYPOST-461) | Deeper expression edge cases | `PYPOST-457/60-tech-debt.md` |

### PYPOST-460 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-536](https://pypost.atlassian.net/browse/PYPOST-536) | Technical debt follow-up | `PYPOST-460/60-tech-debt.md` |

### PYPOST-463 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-462](https://pypost.atlassian.net/browse/PYPOST-462) | Technical debt follow-up | `PYPOST-463/60-tech-debt.md` |

### PYPOST-464 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-465](https://pypost.atlassian.net/browse/PYPOST-465) | Full-project regression in CI | `PYPOST-464/60-tech-debt.md` |

### PYPOST-467 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-493](https://pypost.atlassian.net/browse/PYPOST-493) | Technical debt follow-up | `PYPOST-467/60-tech-debt.md` |

### PYPOST-470 (6 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-472](https://pypost.atlassian.net/browse/PYPOST-472) | \| Medium \| New (if product wants Jinja2 parity) \| Evaluate switching `validate_variable_name` fro... | `PYPOST-470/60-tech-debt.md` |
| [PYPOST-479](https://pypost.atlassian.net/browse/PYPOST-479) | \| Low \| [PYPOST-472](https://pypost.atlassian.net/browse/PYPOST-472) \| Deduplicate error message ... | `PYPOST-470/60-tech-debt.md` |
| [PYPOST-480](https://pypost.atlassian.net/browse/PYPOST-480) | `validation_failure_reason` contract. [PYPOST-475](https://pypost.atlassian.net/browse/PYPOST-475) | `PYPOST-470/60-tech-debt.md` |
| [PYPOST-631](https://pypost.atlassian.net/browse/PYPOST-631) | High \| STEP 7 \| Update `doc/dev/variable_validation.md` | `PYPOST-470/60-tech-debt.md` |
| [PYPOST-632](https://pypost.atlassian.net/browse/PYPOST-632) | Medium \| New (if product wants Jinja2 parity) \| Evaluate switching `validate_variable_name` from ... | `PYPOST-470/60-tech-debt.md` |
| [PYPOST-633](https://pypost.atlassian.net/browse/PYPOST-633) | Low \| Test hygiene \| Unify error-message constants and add `validation_failure_reason` to baselin... | `PYPOST-470/60-tech-debt.md` |

### PYPOST-478 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-471](https://pypost.atlassian.net/browse/PYPOST-471) | \| Medium \| [PYPOST-474](https://pypost.atlassian.net/browse/PYPOST-474) \| Complete automated edge... | `PYPOST-478/60-tech-debt.md` |
| [PYPOST-474](https://pypost.atlassian.net/browse/PYPOST-474) | \| Medium \| [PYPOST-477](https://pypost.atlassian.net/browse/PYPOST-477) \| Unit tests for shared v... | `PYPOST-478/60-tech-debt.md` |
| [PYPOST-477](https://pypost.atlassian.net/browse/PYPOST-477) | Comprehensive unit tests for `validate_variable_name` | `PYPOST-478/60-tech-debt.md` |

### PYPOST-479 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-473](https://pypost.atlassian.net/browse/PYPOST-473) | Verdict:** SAFE TO CLOSE | `PYPOST-479/60-tech-debt.md` |

### PYPOST-481 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-483](https://pypost.atlassian.net/browse/PYPOST-483) | Add additional key provider strategies (keyring, external secret store) and enable UI options. | `PYPOST-481/60-tech-debt.md` |
| [PYPOST-487](https://pypost.atlassian.net/browse/PYPOST-487) | Evaluate migration tooling when togg encryption settings togg existing plain-text hidden values. | `PYPOST-481/60-tech-debt.md` |
| [PYPOST-499](https://pypost.atlassian.net/browse/PYPOST-499) | `StorageManager` end-to-end (covered indirectly via storage + dialog unit tests). | `PYPOST-481/60-tech-debt.md` |

### PYPOST-482 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-508](https://pypost.atlassian.net/browse/PYPOST-508) | Add graceful shutdown wait for `EnvironmentStorageGateway` when encryption is enabled. | `PYPOST-482/60-tech-debt.md` |

### PYPOST-483 (7 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-500](https://pypost.atlassian.net/browse/PYPOST-500) | Add vault and env-indirection secret-store backends beyond file v1. | `PYPOST-483/60-tech-debt.md` |
| [PYPOST-502](https://pypost.atlassian.net/browse/PYPOST-502) | historical key resolution. | `PYPOST-483/60-tech-debt.md` |
| [PYPOST-503](https://pypost.atlassian.net/browse/PYPOST-503) | Consolidate `SUPPORTED_KEY_SOURCES` and secret-backend factory into a single module. | `PYPOST-483/60-tech-debt.md` |
| [PYPOST-504](https://pypost.atlassian.net/browse/PYPOST-504) | Consider registry caching with file-mtime invalidation for env/secret-store sources. | `PYPOST-483/60-tech-debt.md` |
| [PYPOST-505](https://pypost.atlassian.net/browse/PYPOST-505) | Warn in Settings UI when fallback text contains unsupported or duplicate entries. | `PYPOST-483/60-tech-debt.md` |
| [PYPOST-506](https://pypost.atlassian.net/browse/PYPOST-506) | Validate Fernet key material at registry load time with clear, safe error messages. | `PYPOST-483/60-tech-debt.md` |
| [PYPOST-507](https://pypost.atlassian.net/browse/PYPOST-507) | guidance. | `PYPOST-483/60-tech-debt.md` |

### PYPOST-484 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-533](https://pypost.atlassian.net/browse/PYPOST-533) | Add envelope v2 design when a new algorithm or metadata fields are required. | `PYPOST-484/60-tech-debt.md` |

### PYPOST-485 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-534](https://pypost.atlassian.net/browse/PYPOST-534) | Add benchmark or profiling harness for environments with 100+ hidden keys to guard regressions. | `PYPOST-485/60-tech-debt.md` |
| [PYPOST-535](https://pypost.atlassian.net/browse/PYPOST-535) | Consider persisted `kid` rotation batch job integration with reuse stats in migration CLI output. | `PYPOST-485/60-tech-debt.md` |

### PYPOST-486 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-482](https://pypost.atlassian.net/browse/PYPOST-482) | Extract environment serialization/encryption from `StorageManager` into a dedicated adapter. | `PYPOST-486/60-tech-debt.md` |
| [PYPOST-485](https://pypost.atlassian.net/browse/PYPOST-485) | for large datasets is the same. Per-value overhead remains tracked separately. | `PYPOST-486/60-tech-debt.md` |
| [PYPOST-509](https://pypost.atlassian.net/browse/PYPOST-509) | Add `MainWindow` integration test for encrypted async startup gating. | `PYPOST-486/60-tech-debt.md` |

### PYPOST-487 (8 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-525](https://pypost.atlassian.net/browse/PYPOST-525) | TD-1 \| Medium \| Add public `StorageManager` method to deserialize environments with per-item erro... | `PYPOST-487/60-tech-debt.md` |
| [PYPOST-526](https://pypost.atlassian.net/browse/PYPOST-526) | TD-2 \| Low \| Remove or unify `build_inventory(check_decrypt=True)` with `verify_decrypt_access()`... | `PYPOST-487/60-tech-debt.md` |
| [PYPOST-527](https://pypost.atlassian.net/browse/PYPOST-527) | TD-3 \| Medium \| Optional Settings UI: “Verify encryption” and “Re-encrypt all environments” deleg... | `PYPOST-487/60-tech-debt.md` |
| [PYPOST-528](https://pypost.atlassian.net/browse/PYPOST-528) | TD-5 \| Low \| Skip no-op `bulk_re_encrypt` when histogram already matches active `kid` only \| Avoi... | `PYPOST-487/60-tech-debt.md` |
| [PYPOST-529](https://pypost.atlassian.net/browse/PYPOST-529) | TD-6 \| Low \| Flag non-string/non-envelope hidden values in inventory as data-quality errors \| Saf... | `PYPOST-487/60-tech-debt.md` |
| [PYPOST-530](https://pypost.atlassian.net/browse/PYPOST-530) | TD-7 \| Low \| CLI `--json` output and optional `--data-dir` for scripted verify in CI/backup resto... | `PYPOST-487/60-tech-debt.md` |
| [PYPOST-531](https://pypost.atlassian.net/browse/PYPOST-531) | TD-8 \| Low \| Integration tests with keyring and secret_store fixtures \| Confidence for Stage 2–3 ... | `PYPOST-487/60-tech-debt.md` |
| [PYPOST-532](https://pypost.atlassian.net/browse/PYPOST-532) | TD-9 \| Low \| CLI test for `encrypt-plaintext --dry-run` \| Parity with service-layer dry-run cover... | `PYPOST-487/60-tech-debt.md` |

### PYPOST-490 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-488](https://pypost.atlassian.net/browse/PYPOST-488) | \| High \| [PYPOST-490](https://pypost.atlassian.net/browse/PYPOST-490) \| **This task** — integrati... | `PYPOST-490/60-tech-debt.md` |
| [PYPOST-489](https://pypost.atlassian.net/browse/PYPOST-489) | \| Low \| [PYPOST-492](https://pypost.atlassian.net/browse/PYPOST-492) \| Group security/logging set... | `PYPOST-490/60-tech-debt.md` |
| [PYPOST-491](https://pypost.atlassian.net/browse/PYPOST-491) | \| High \| [PYPOST-488](https://pypost.atlassian.net/browse/PYPOST-488) \| Document `log_hidden_key_... | `PYPOST-490/60-tech-debt.md` |
| [PYPOST-492](https://pypost.atlassian.net/browse/PYPOST-492) | \| Medium \| [PYPOST-491](https://pypost.atlassian.net/browse/PYPOST-491) \| Extract `HIDDEN_MASK` t... | `PYPOST-490/60-tech-debt.md` |

### PYPOST-492 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-635](https://pypost.atlassian.net/browse/PYPOST-635) | for a single dialog row; `hotkeys_dialog.py` uses a similar pattern. | `PYPOST-492/60-tech-debt.md` |
| [PYPOST-636](https://pypost.atlassian.net/browse/PYPOST-636) | No visual/regression screenshot test for Settings dialog layout. | `PYPOST-492/60-tech-debt.md` |

### PYPOST-496 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-467](https://pypost.atlassian.net/browse/PYPOST-467) | Technical debt follow-up | `PYPOST-496/60-tech-debt.md` |
| [PYPOST-497](https://pypost.atlassian.net/browse/PYPOST-497) | Domain validation remains in widget layer (deferred to | `PYPOST-496/60-tech-debt.md` |

### PYPOST-498 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-494](https://pypost.atlassian.net/browse/PYPOST-494) | Technical debt follow-up | `PYPOST-498/60-tech-debt.md` |

### PYPOST-499 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-501](https://pypost.atlassian.net/browse/PYPOST-501) | None for this task scope. Key-source chain E2E remains | `PYPOST-499/60-tech-debt.md` |

### PYPOST-510 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-10](https://pypost.atlassian.net/browse/PYPOST-10) | Reuse the line-number gutter on the Script tab editor (tracked in existing tech debt). | `PYPOST-510/60-tech-debt.md` |

### PYPOST-511 (5 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-513](https://pypost.atlassian.net/browse/PYPOST-513) | Technical debt follow-up | `PYPOST-511/60-tech-debt.md` |
| [PYPOST-516](https://pypost.atlassian.net/browse/PYPOST-516) | Extend RequestWidget integration test to assert body gutter chevrons and fold toggle. | `PYPOST-511/60-tech-debt.md` |
| [PYPOST-517](https://pypost.atlassian.net/browse/PYPOST-517) | Add unit tests for fold remapping after document edits while sections are collapsed. | `PYPOST-511/60-tech-debt.md` |
| [PYPOST-518](https://pypost.atlassian.net/browse/PYPOST-518) | Implement YAML and XML structure scanners and enable folding when those formats are active. | `PYPOST-511/60-tech-debt.md` |
| [PYPOST-637](https://pypost.atlassian.net/browse/PYPOST-637) | debounced re-scan. Fine for typical payloads; very large bodies may benefit from a single-pass | `PYPOST-511/60-tech-debt.md` |

### PYPOST-512 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-519](https://pypost.atlassian.net/browse/PYPOST-519) | Implement YAML and XML body validators when those formats are active via format selector. | `PYPOST-512/60-tech-debt.md` |
| [PYPOST-520](https://pypost.atlassian.net/browse/PYPOST-520) | Add unit test for validation error line alignment with folded/hidden blocks. | `PYPOST-512/60-tech-debt.md` |
| [PYPOST-521](https://pypost.atlassian.net/browse/PYPOST-521) | Extend RequestWidget integration test to assert body validation banner on invalid JSON. | `PYPOST-512/60-tech-debt.md` |

### PYPOST-513 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-585](https://pypost.atlassian.net/browse/PYPOST-585) | Add YAML/XML syntax highlighting when format-specific highlighters are available. | `PYPOST-513/60-tech-debt.md` |

### PYPOST-514 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-515](https://pypost.atlassian.net/browse/PYPOST-515) | behavior; no PYPOST-514 changes required until that task ships. | `PYPOST-514/60-tech-debt.md` |
| [PYPOST-522](https://pypost.atlassian.net/browse/PYPOST-522) | intentionally keep editor YAML; document or offer opt-in wire-form export if users need | `PYPOST-514/60-tech-debt.md` |
| [PYPOST-523](https://pypost.atlassian.net/browse/PYPOST-523) | `ErrorCategory.BODY` message formatting. | `PYPOST-514/60-tech-debt.md` |
| [PYPOST-524](https://pypost.atlassian.net/browse/PYPOST-524) | body content) if failure rates become useful for support. | `PYPOST-514/60-tech-debt.md` |

### PYPOST-525 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-638](https://pypost.atlassian.net/browse/PYPOST-638) | TD-2 \| Low \| Unify inventory scan and decrypt load to avoid duplicate file reads in migration \| P... | `PYPOST-525/60-tech-debt.md` |
| [PYPOST-639](https://pypost.atlassian.net/browse/PYPOST-639) | TD-3 \| Low \| Skip bulk re-encrypt when inventory shows no ciphertext to rotate \| PYPOST-487 debt \| | `PYPOST-525/60-tech-debt.md` |
| [PYPOST-678](https://pypost.atlassian.net/browse/PYPOST-678) | Technical debt follow-up | `PYPOST-525/60-tech-debt.md` |

### PYPOST-527 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-640](https://pypost.atlassian.net/browse/PYPOST-640) | TD-1 \| Low \| Add Settings action for encrypt-plaintext \| Parity with CLI M4 scenario \| | `PYPOST-527/60-tech-debt.md` |
| [PYPOST-642](https://pypost.atlassian.net/browse/PYPOST-642) | TD-3 \| Low \| Background worker for bulk re-encrypt from UI \| Avoid UI freeze on large files \| | `PYPOST-527/60-tech-debt.md` |

### PYPOST-530 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-540](https://pypost.atlassian.net/browse/PYPOST-540) | TD-10 \| Low \| Optional `--config-dir` for settings alongside `--data-dir` \| Restore workflows tha... | `PYPOST-530/60-tech-debt.md` |
| [PYPOST-643](https://pypost.atlassian.net/browse/PYPOST-643) | TD-6 \| Low \| Flag non-string/non-envelope hidden values in inventory \| | `PYPOST-530/60-tech-debt.md` |
| [PYPOST-644](https://pypost.atlassian.net/browse/PYPOST-644) | TD-8 \| Low \| Integration tests with keyring and secret_store fixtures \| | `PYPOST-530/60-tech-debt.md` |
| [PYPOST-645](https://pypost.atlassian.net/browse/PYPOST-645) | TD-9 \| Low \| CLI test for `encrypt-plaintext --dry-run` \| | `PYPOST-530/60-tech-debt.md` |

### PYPOST-531 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-543](https://pypost.atlassian.net/browse/PYPOST-543) | TD-11 \| Low \| Vault backend migration integration test \| Stage 4 rollout confidence when PYPOST-5... | `PYPOST-531/60-tech-debt.md` |

### PYPOST-532 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-646](https://pypost.atlassian.net/browse/PYPOST-646) | TD-10 \| Low \| Optional `--config-dir` for settings alongside `--data-dir` \| | `PYPOST-532/60-tech-debt.md` |

### PYPOST-533 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-541](https://pypost.atlassian.net/browse/PYPOST-541) | TD-11 \| Medium \| Implement v2 decrypt handlers (fernet + aes-gcm) \| Parsing scaffold exists; code... | `PYPOST-533/60-tech-debt.md` |
| [PYPOST-542](https://pypost.atlassian.net/browse/PYPOST-542) | TD-12 \| Low \| v1 → v2 re-encrypt migration path \| After v2 decrypt lands, optional CLI or service... | `PYPOST-533/60-tech-debt.md` |

### PYPOST-535 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-544](https://pypost.atlassian.net/browse/PYPOST-544) | TD-1 \| Low \| Surface `reencrypt_stats` in Settings re-encrypt dialog \| | `PYPOST-535/60-tech-debt.md` |

### PYPOST-539 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-547](https://pypost.atlassian.net/browse/PYPOST-547) | Technical debt follow-up | `PYPOST-539/60-tech-debt.md` |

### PYPOST-541 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-648](https://pypost.atlassian.net/browse/PYPOST-648) | TD-11 \| Medium \| Implement v2 decrypt handlers (fernet + aes-gcm) \| Implemented in PYPOST-541 \| | `PYPOST-541/60-tech-debt.md` |
| [PYPOST-649](https://pypost.atlassian.net/browse/PYPOST-649) | TD-12 \| Low \| v2 encrypt in `EnvironmentSecretsCodec` \| `encrypt()` still emits v1; add when migr... | `PYPOST-541/60-tech-debt.md` |
| [PYPOST-650](https://pypost.atlassian.net/browse/PYPOST-650) | TD-13 \| Low \| Bulk v1→v2 re-encrypt CLI option \| Depends on v2 encrypt; extend `encryption_migrat... | `PYPOST-541/60-tech-debt.md` |

### PYPOST-542 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-1018](https://pypost.atlassian.net/browse/PYPOST-1018) | TD-14 \| Low \| Default runtime encrypt to v2 \| Separate product decision; desktop saves still v1. | `PYPOST-542/60-tech-debt.md` |
| [PYPOST-1019](https://pypost.atlassian.net/browse/PYPOST-1019) | TD-15 \| Low \| Settings UI for upgrade-v2 \| CLI-only for now. | `PYPOST-542/60-tech-debt.md` |

### PYPOST-544 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-545](https://pypost.atlassian.net/browse/PYPOST-545) | TD-1 \| Low \| Dry-run projected reuse counts in CLI and Settings \| | `PYPOST-544/60-tech-debt.md` |
| [PYPOST-641](https://pypost.atlassian.net/browse/PYPOST-641) | TD-2 \| Low \| Extract shared migration report formatting for CLI and Settings \| Optional DRY; labe... | `PYPOST-544/60-tech-debt.md` |

### PYPOST-548 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-651](https://pypost.atlassian.net/browse/PYPOST-651) | Fix pre-existing E501/E203 in unrelated pypost files \| Low \| Out of PYPOST-548 scope \| | `PYPOST-548/60-tech-debt.md` |

### PYPOST-549 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-550](https://pypost.atlassian.net/browse/PYPOST-550) | Technical debt follow-up | `PYPOST-549/60-tech-debt.md` |
| [PYPOST-551](https://pypost.atlassian.net/browse/PYPOST-551) | Technical debt follow-up | `PYPOST-549/60-tech-debt.md` |
| [PYPOST-552](https://pypost.atlassian.net/browse/PYPOST-552) | TD-2 \| Low \| User-facing `doc/mcp_integration.md` still SSE URLs \| | `PYPOST-549/60-tech-debt.md` |
| [PYPOST-652](https://pypost.atlassian.net/browse/PYPOST-652) | TD-3 \| Low \| `HTTPClient` SSE URL heuristic \| Pre-existing debt (PYPOST-430). | `PYPOST-549/60-tech-debt.md` |

### PYPOST-550 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-575](https://pypost.atlassian.net/browse/PYPOST-575) | EnvPresenter supplier test \| Add `test_registers_variable_supplier_on_init` and `test_supplier_re... | `PYPOST-550/60-tech-debt.md` |
| [PYPOST-576](https://pypost.atlassian.net/browse/PYPOST-576) | Manager supplier propagation \| Add unit test in `tests/test_mcp_server.py` (or existing manager t... | `PYPOST-550/60-tech-debt.md` |
| [PYPOST-577](https://pypost.atlassian.net/browse/PYPOST-577) | Shared env snapshot \| Optional refactor: extract env-variable cache from `EnvPresenter`/`TabsPres... | `PYPOST-550/60-tech-debt.md` |

### PYPOST-551 (5 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-430](https://pypost.atlassian.net/browse/PYPOST-430) | TD-2 \| Low \| `HTTPClient` SSE probe uses `"/sse" in url` heuristic \| Resolved in | `PYPOST-551/60-tech-debt.md` |
| [PYPOST-560](https://pypost.atlassian.net/browse/PYPOST-560) | TD-3 \| Low \| `MCPClientService.run` uses `asyncio.run` \| Pre-existing (PYPOST-368); `anyio.run` m... | `PYPOST-551/60-tech-debt.md` |
| [PYPOST-578](https://pypost.atlassian.net/browse/PYPOST-578) | TD-4 \| Low \| User-facing `doc/mcp_integration.md` still describes SSE URL \| | `PYPOST-551/60-tech-debt.md` |
| [PYPOST-653](https://pypost.atlassian.net/browse/PYPOST-653) | TD-1 \| Low \| Dual SSE + Streamable HTTP maintenance \| Legacy `/sse` mounts kept for transition; r... | `PYPOST-551/60-tech-debt.md` |
| [PYPOST-654](https://pypost.atlassian.net/browse/PYPOST-654) | TD-5 \| Low \| `config/test/README.md` example URLs still reference `/sse` \| Update when refreshing... | `PYPOST-551/60-tech-debt.md` |

### PYPOST-552 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-655](https://pypost.atlassian.net/browse/PYPOST-655) | TD-3 \| Low \| `doc/dev/architecture.md` metrics MCP line still mentions `/sse` \| Minor; update in ... | `PYPOST-552/60-tech-debt.md` |
| [PYPOST-656](https://pypost.atlassian.net/browse/PYPOST-656) | TD-4 \| Low \| PYPOST-578 duplicate scope \| Close or link as duplicate of PYPOST-552 \| | `PYPOST-552/60-tech-debt.md` |

### PYPOST-553 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-657](https://pypost.atlassian.net/browse/PYPOST-657) | TD-1 \| Low \| Auto-populate MCP params table from template scan when URL/body changes \| | `PYPOST-553/60-tech-debt.md` |
| [PYPOST-658](https://pypost.atlassian.net/browse/PYPOST-658) | TD-2 \| Low \| Support `array` / `object` types in UI type combo (model already allows) \| | `PYPOST-553/60-tech-debt.md` |
| [PYPOST-659](https://pypost.atlassian.net/browse/PYPOST-659) | TD-3 \| Low \| Operator contract preview panel (PYPOST-555) \| | `PYPOST-553/60-tech-debt.md` |

### PYPOST-555 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-556](https://pypost.atlassian.net/browse/PYPOST-556) | TD-2 \| Low \| Global tools overview (PYPOST-556) \| Complements per-request preview. | `PYPOST-555/60-tech-debt.md` |
| [PYPOST-660](https://pypost.atlassian.net/browse/PYPOST-660) | TD-1 \| Low \| Refresh preview on MCP param type combo change \| `McpParamsTable` type `QComboBox` c... | `PYPOST-555/60-tech-debt.md` |

### PYPOST-556 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-661](https://pypost.atlassian.net/browse/PYPOST-661) | TD-1 \| Low \| Auto-refresh overview when collections change without env switch \| | `PYPOST-556/60-tech-debt.md` |
| [PYPOST-662](https://pypost.atlassian.net/browse/PYPOST-662) | TD-2 \| Low \| Link overview rows to open request tab \| | `PYPOST-556/60-tech-debt.md` |
| [PYPOST-663](https://pypost.atlassian.net/browse/PYPOST-663) | TD-3 \| Low \| Metrics MCP server same reliable status pattern \| | `PYPOST-556/60-tech-debt.md` |

### PYPOST-557 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-664](https://pypost.atlassian.net/browse/PYPOST-664) | UI tool preview structured result \| Low \| PYPOST-555 may show envelope preview \| | `PYPOST-557/60-tech-debt.md` |
| [PYPOST-680](https://pypost.atlassian.net/browse/PYPOST-680) | Agents must parse JSON TextContent \| Low \| Documented in `doc/dev/mcp_integration.md`; breaking c... | `PYPOST-557/60-tech-debt.md` |
| [PYPOST-681](https://pypost.atlassian.net/browse/PYPOST-681) | `error_message` omits `detail` field \| Low \| Agents can parse `body` for synthetic errors; option... | `PYPOST-557/60-tech-debt.md` |

### PYPOST-567 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-665](https://pypost.atlassian.net/browse/PYPOST-665) | Medium \| Refine expected/suspicious tags after worker/presenter audit \| | `PYPOST-567/60-tech-debt.md` |

### PYPOST-568 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-666](https://pypost.atlassian.net/browse/PYPOST-666) | Medium \| CI allowlist for expected ERROR lines from error-path tests \| | `PYPOST-568/60-tech-debt.md` |

### PYPOST-569 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-667](https://pypost.atlassian.net/browse/PYPOST-667) | Optional CI job: `--durations=10 --durations-min=5` on verbose runs \| Low \| | `PYPOST-569/60-tech-debt.md` |
| [PYPOST-668](https://pypost.atlassian.net/browse/PYPOST-668) | Monitor `test_makefile.py` (~4.6s peak); consider 45s marker after stable week \| Low \| | `PYPOST-569/60-tech-debt.md` |
| [PYPOST-669](https://pypost.atlassian.net/browse/PYPOST-669) | Re-run `scripts/parse_timeout_audit.py` when adding e2e/integration tests \| Low \| | `PYPOST-569/60-tech-debt.md` |

### PYPOST-570 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-670](https://pypost.atlassian.net/browse/PYPOST-670) | High \| CI allowlist / fail on unexpected ERROR \| | `PYPOST-570/60-tech-debt.md` |
| [PYPOST-671](https://pypost.atlassian.net/browse/PYPOST-671) | Medium \| Add `-o log_cli=false` to `test.yml` \| Optional small PR or part of PYPOST-571 \| | `PYPOST-570/60-tech-debt.md` |

### PYPOST-571 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-572](https://pypost.atlassian.net/browse/PYPOST-572) | Implement allowlist YAML + `verify_test_log_guardrails.py` + CI step \| M \| | `PYPOST-571/60-tech-debt.md` |
| [PYPOST-573](https://pypost.atlassian.net/browse/PYPOST-573) | Duration budget audit script + CI annotations \| M \| | `PYPOST-571/60-tech-debt.md` |
| [PYPOST-574](https://pypost.atlassian.net/browse/PYPOST-574) | `caplog` contract in `do-testing.md` + optional retrofits \| S \| | `PYPOST-571/60-tech-debt.md` |

### PYPOST-579 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-583](https://pypost.atlassian.net/browse/PYPOST-583) | TD-1 \| Low \| Wire OTel adapter in production composition root \| Requires operator OTLP config; de... | `PYPOST-579/60-tech-debt.md` |
| [PYPOST-584](https://pypost.atlassian.net/browse/PYPOST-584) | TD-2 \| Low \| Shared instrument definition table \| `MetricsRegistry` and `OtelMetricsTracker` dupl... | `PYPOST-579/60-tech-debt.md` |

### PYPOST-598 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-600](https://pypost.atlassian.net/browse/PYPOST-600) | D3 \| Duplicated encryption form-state between `accept()` and migration handlers \| Medium \| | `PYPOST-598/60-tech-debt.md` |
| [PYPOST-602](https://pypost.atlassian.net/browse/PYPOST-602) | D5 \| `EncryptionMigrationService` constructed inside dialog when storage provided \| Low \| | `PYPOST-598/60-tech-debt.md` |

### PYPOST-621 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-682](https://pypost.atlassian.net/browse/PYPOST-682) | E2E: emit alert after settings save uses new log path \| Low \| Unit tests cover reload wiring; ful... | `PYPOST-621/60-tech-debt.md` |

### PYPOST-659 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-555](https://pypost.atlassian.net/browse/PYPOST-555) | Technical debt follow-up | `PYPOST-659/60-tech-debt.md` |

### PYPOST-684 (9 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-692](https://pypost.atlassian.net/browse/PYPOST-692) | import. Remove `ui/` import from `core/`. | `PYPOST-684/60-tech-debt.md` |
| [PYPOST-693](https://pypost.atlassian.net/browse/PYPOST-693) | HTTP/templating/history in Qt-free modules. | `PYPOST-684/60-tech-debt.md` |
| [PYPOST-694](https://pypost.atlassian.net/browse/PYPOST-694) | `testability.md` table. | `PYPOST-684/60-tech-debt.md` |
| [PYPOST-697](https://pypost.atlassian.net/browse/PYPOST-697) | setup instead of module singleton (or document explicit acceptance). | `PYPOST-684/60-tech-debt.md` |
| [PYPOST-698](https://pypost.atlassian.net/browse/PYPOST-698) | `RequestWorker` for narrower integration tests. | `PYPOST-684/60-tech-debt.md` |
| [PYPOST-699](https://pypost.atlassian.net/browse/PYPOST-699) | Remediation:** Remove from docs or add shared helpers when needed. | `PYPOST-684/60-tech-debt.md` |
| [PYPOST-700](https://pypost.atlassian.net/browse/PYPOST-700) | Remediation:** Split expression helpers if growth continues. | `PYPOST-684/60-tech-debt.md` |
| [PYPOST-701](https://pypost.atlassian.net/browse/PYPOST-701) | parity with GUI. | `PYPOST-684/60-tech-debt.md` |
| [PYPOST-702](https://pypost.atlassian.net/browse/PYPOST-702) | (depends on R-P1-001). | `PYPOST-684/60-tech-debt.md` |

### PYPOST-685 (13 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-703](https://pypost.atlassian.net/browse/PYPOST-703) | size limits; document that agents see full upstream responses today. | `PYPOST-685/60-tech-debt.md` |
| [PYPOST-704](https://pypost.atlassian.net/browse/PYPOST-704) | binding beyond localhost. | `PYPOST-685/60-tech-debt.md` |
| [PYPOST-705](https://pypost.atlassian.net/browse/PYPOST-705) | non-localhost bind. | `PYPOST-685/60-tech-debt.md` |
| [PYPOST-706](https://pypost.atlassian.net/browse/PYPOST-706) | UX for the hidden flag. | `PYPOST-685/60-tech-debt.md` |
| [PYPOST-707](https://pypost.atlassian.net/browse/PYPOST-707) | (product decision). | `PYPOST-685/60-tech-debt.md` |
| [PYPOST-708](https://pypost.atlassian.net/browse/PYPOST-708) | Remediation:** Encrypt or externalize secret storage for webhook credentials. | `PYPOST-685/60-tech-debt.md` |
| [PYPOST-709](https://pypost.atlassian.net/browse/PYPOST-709) | Remediation:** Log template URL or redact query parameters containing tokens. | `PYPOST-685/60-tech-debt.md` |
| [PYPOST-710](https://pypost.atlassian.net/browse/PYPOST-710) | Remediation:** Sanitize or omit `logs` field for agent responses. | `PYPOST-685/60-tech-debt.md` |
| [PYPOST-711](https://pypost.atlassian.net/browse/PYPOST-711) | UI/docs on global tool catalog scope. | `PYPOST-685/60-tech-debt.md` |
| [PYPOST-712](https://pypost.atlassian.net/browse/PYPOST-712) | Remediation:** Bind default to localhost (see R-P1-002) plus optional auth for metrics MCP. | `PYPOST-685/60-tech-debt.md` |
| [PYPOST-713](https://pypost.atlassian.net/browse/PYPOST-713) | Remediation:** Operator documentation; expected for a local API client. | `PYPOST-685/60-tech-debt.md` |
| [PYPOST-714](https://pypost.atlassian.net/browse/PYPOST-714) | Remediation:** Forward `hidden_keys` when wiring MCP history. | `PYPOST-685/60-tech-debt.md` |
| [PYPOST-715](https://pypost.atlassian.net/browse/PYPOST-715) | Remediation:** Set `debug=False` for production MCP app. | `PYPOST-685/60-tech-debt.md` |

### PYPOST-687 (9 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-728](https://pypost.atlassian.net/browse/PYPOST-728) | from `template_service` if refactor preferred. | `PYPOST-687/60-tech-debt.md` |
| [PYPOST-730](https://pypost.atlassian.net/browse/PYPOST-730) | tests per step. | `PYPOST-687/60-tech-debt.md` |
| [PYPOST-731](https://pypost.atlassian.net/browse/PYPOST-731) | 785 with headroom. | `PYPOST-687/60-tech-debt.md` |
| [PYPOST-732](https://pypost.atlassian.net/browse/PYPOST-732) | parsers. | `PYPOST-687/60-tech-debt.md` |
| [PYPOST-735](https://pypost.atlassian.net/browse/PYPOST-735) | breach. | `PYPOST-687/60-tech-debt.md` |
| [PYPOST-737](https://pypost.atlassian.net/browse/PYPOST-737) | Remediation:** Delete unused `error_prefix` branch variable and import. | `PYPOST-687/60-tech-debt.md` |
| [PYPOST-738](https://pypost.atlassian.net/browse/PYPOST-738) | Remediation:** Adopt when touching files; no big-bang migration required. | `PYPOST-687/60-tech-debt.md` |
| [PYPOST-739](https://pypost.atlassian.net/browse/PYPOST-739) | Remediation:** Add section to `doc/dev/maintainability_audit.md` or `architecture.md`. | `PYPOST-687/60-tech-debt.md` |
| [PYPOST-740](https://pypost.atlassian.net/browse/PYPOST-740) | Remediation:** Rename to `tab_dirty_state.py` or move to `ui/presenters/`. | `PYPOST-687/60-tech-debt.md` |

### PYPOST-688 (11 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-741](https://pypost.atlassian.net/browse/PYPOST-741) | change. | `PYPOST-688/60-tech-debt.md` |
| [PYPOST-742](https://pypost.atlassian.net/browse/PYPOST-742) | Debt item (line 61) | `PYPOST-688/60-tech-debt.md` |
| [PYPOST-743](https://pypost.atlassian.net/browse/PYPOST-743) | docs. Default INFO; allow DEBUG for support sessions. | `PYPOST-688/60-tech-debt.md` |
| [PYPOST-744](https://pypost.atlassian.net/browse/PYPOST-744) | required for operators (document file sensitivity). | `PYPOST-688/60-tech-debt.md` |
| [PYPOST-745](https://pypost.atlassian.net/browse/PYPOST-745) | Remediation:** Log scheme + host + path prefix; omit auth query params if present. | `PYPOST-688/60-tech-debt.md` |
| [PYPOST-746](https://pypost.atlassian.net/browse/PYPOST-746) | `_init_encryption_metrics` helpers; no behavior change. | `PYPOST-688/60-tech-debt.md` |
| [PYPOST-747](https://pypost.atlassian.net/browse/PYPOST-747) | event catalog and migration guidance for legacy modules. | `PYPOST-688/60-tech-debt.md` |
| [PYPOST-748](https://pypost.atlassian.net/browse/PYPOST-748) | Debt item (line 120) | `PYPOST-688/60-tech-debt.md` |
| [PYPOST-749](https://pypost.atlassian.net/browse/PYPOST-749) | Remediation:** Add reciprocal links between `observability_audit.md` and `testing.md`. | `PYPOST-688/60-tech-debt.md` |
| [PYPOST-750](https://pypost.atlassian.net/browse/PYPOST-750) | `metric_rename_migration.md`. | `PYPOST-688/60-tech-debt.md` |
| [PYPOST-752](https://pypost.atlassian.net/browse/PYPOST-752) | Remediation:** Enable flake8-print (T201) for `pypost/` or extend audit script. | `PYPOST-688/60-tech-debt.md` |

### PYPOST-689 (12 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-753](https://pypost.atlassian.net/browse/PYPOST-753) | Emit counter `response_body_truncated_total`. Update tests with mocked oversized stream. | `PYPOST-689/60-tech-debt.md` |
| [PYPOST-754](https://pypost.atlassian.net/browse/PYPOST-754) | Debt item (line 63) | `PYPOST-689/60-tech-debt.md` |
| [PYPOST-755](https://pypost.atlassian.net/browse/PYPOST-755) | `test_response_view_search.py` large-doc cases. | `PYPOST-689/60-tech-debt.md` |
| [PYPOST-756](https://pypost.atlassian.net/browse/PYPOST-756) | `resolved` is provided; fall back to re-render only when resolved unavailable (MCP edge cases). | `PYPOST-689/60-tech-debt.md` |
| [PYPOST-757](https://pypost.atlassian.net/browse/PYPOST-757) | busy; incremental `refresh_tree` diff if cheap. | `PYPOST-689/60-tech-debt.md` |
| [PYPOST-758](https://pypost.atlassian.net/browse/PYPOST-758) | file changes; full rebuild only on explicit "Reload all". | `PYPOST-689/60-tech-debt.md` |
| [PYPOST-759](https://pypost.atlassian.net/browse/PYPOST-759) | configurable max concurrent tool executions; metric for queue depth if limited. | `PYPOST-689/60-tech-debt.md` |
| [PYPOST-760](https://pypost.atlassian.net/browse/PYPOST-760) | Debt item (line 126) | `PYPOST-689/60-tech-debt.md` |
| [PYPOST-761](https://pypost.atlassian.net/browse/PYPOST-761) | `render_path`; optional high-cardinality guard. | `PYPOST-689/60-tech-debt.md` |
| [PYPOST-762](https://pypost.atlassian.net/browse/PYPOST-762) | panel until ready. Low priority if files stay small. | `PYPOST-689/60-tech-debt.md` |
| [PYPOST-763](https://pypost.atlassian.net/browse/PYPOST-763) | Remediation:** Skip JSON reformat when `len(text) > LARGE_DOC_CHAR_THRESHOLD`. | `PYPOST-689/60-tech-debt.md` |
| [PYPOST-764](https://pypost.atlassian.net/browse/PYPOST-764) | from `architecture.md`. | `PYPOST-689/60-tech-debt.md` |

### PYPOST-690 (12 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-765](https://pypost.atlassian.net/browse/PYPOST-765) | Tech Debt). Re-run inventory script until gap is zero for capability docs. | `PYPOST-690/60-tech-debt.md` |
| [PYPOST-766](https://pypost.atlassian.net/browse/PYPOST-766) | Debt item (line 57) | `PYPOST-690/60-tech-debt.md` |
| [PYPOST-767](https://pypost.atlassian.net/browse/PYPOST-767) | Add "Related Audits" footer to each `*_audit.md` linking siblings. | `PYPOST-690/60-tech-debt.md` |
| [PYPOST-768](https://pypost.atlassian.net/browse/PYPOST-768) | `baseline-metrics.md` current caps (383 file / 343 class LOC). Mark PYPOST-43 complete. | `PYPOST-690/60-tech-debt.md` |
| [PYPOST-769](https://pypost.atlassian.net/browse/PYPOST-769) | Jira from `doc/dev/*_audit.md` when debt is ticketed separately. | `PYPOST-690/60-tech-debt.md` |
| [PYPOST-770](https://pypost.atlassian.net/browse/PYPOST-770) | Remediation:** Add bullet: "Developer documentation — [doc/dev/README.md](doc/dev/README.md)." | `PYPOST-690/60-tech-debt.md` |
| [PYPOST-771](https://pypost.atlassian.net/browse/PYPOST-771) | Remediation:** Add "Technical Debt" section with inventory link and major audit debt pages. | `PYPOST-690/60-tech-debt.md` |
| [PYPOST-772](https://pypost.atlassian.net/browse/PYPOST-772) | Debt item (line 113) | `PYPOST-690/60-tech-debt.md` |
| [PYPOST-773](https://pypost.atlassian.net/browse/PYPOST-773) | Remediation:** Add cross-link under Observability in dev README (or move to `doc/dev/`). | `PYPOST-690/60-tech-debt.md` |
| [PYPOST-774](https://pypost.atlassian.net/browse/PYPOST-774) | Remediation:** Add "See also" sections at top of each file. | `PYPOST-690/60-tech-debt.md` |
| [PYPOST-775](https://pypost.atlassian.net/browse/PYPOST-775) | Remediation:** Add Related Audits section (security, observability, maintainability). | `PYPOST-690/60-tech-debt.md` |
| [PYPOST-776](https://pypost.atlassian.net/browse/PYPOST-776) | Remediation:** Run `scripts/audit_baseline_metrics.py --markdown` and commit if caps change. | `PYPOST-690/60-tech-debt.md` |

### PYPOST-691 (11 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-777](https://pypost.atlassian.net/browse/PYPOST-777) | as the single source of truth. | `PYPOST-691/60-tech-debt.md` |
| [PYPOST-778](https://pypost.atlassian.net/browse/PYPOST-778) | Debt item (line 68) | `PYPOST-691/60-tech-debt.md` |
| [PYPOST-779](https://pypost.atlassian.net/browse/PYPOST-779) | CI installs from lock; document upgrade workflow in `doc/dev/setup.md`. | `PYPOST-691/60-tech-debt.md` |
| [PYPOST-781](https://pypost.atlassian.net/browse/PYPOST-781) | `github-actions` ecosystem on `test.yml`. | `PYPOST-691/60-tech-debt.md` |
| [PYPOST-782](https://pypost.atlassian.net/browse/PYPOST-782) | models on lower bound. | `PYPOST-691/60-tech-debt.md` |
| [PYPOST-783](https://pypost.atlassian.net/browse/PYPOST-783) | combo. | `PYPOST-691/60-tech-debt.md` |
| [PYPOST-784](https://pypost.atlassian.net/browse/PYPOST-784) | Debt item (line 132) | `PYPOST-691/60-tech-debt.md` |
| [PYPOST-785](https://pypost.atlassian.net/browse/PYPOST-785) | dev` and `otel`, pytest `pythonpath` if desired. | `PYPOST-691/60-tech-debt.md` |
| [PYPOST-786](https://pypost.atlassian.net/browse/PYPOST-786) | when obligations apply. | `PYPOST-691/60-tech-debt.md` |
| [PYPOST-787](https://pypost.atlassian.net/browse/PYPOST-787) | file; keep OTel tests installing extra in CI matrix. | `PYPOST-691/60-tech-debt.md` |
| [PYPOST-788](https://pypost.atlassian.net/browse/PYPOST-788) | and encryption packages. | `PYPOST-691/60-tech-debt.md` |

### PYPOST-694 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-695](https://pypost.atlassian.net/browse/PYPOST-695) | Medium \| Elevate `StorageManager`, `RequestManager`, `MCPServerManager` to composition root \| | `PYPOST-694/60-tech-debt.md` |

### PYPOST-734 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-813](https://pypost.atlassian.net/browse/PYPOST-813) | Remediation:** Annotate `send_request` / `execute` optional callbacks and variables. | `PYPOST-734/60-tech-debt.md` |
| [PYPOST-814](https://pypost.atlassian.net/browse/PYPOST-814) | `# type: ignore` only as last resort. | `PYPOST-734/60-tech-debt.md` |

### PYPOST-737 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-729](https://pypost.atlassian.net/browse/PYPOST-729) | Remaining W391/E501 from PYPOST-687 audit \| Low \| Closed in | `PYPOST-737/60-tech-debt.md` |
| [PYPOST-736](https://pypost.atlassian.net/browse/PYPOST-736) | Wire `make lint` into CI pipeline \| Medium \| | `PYPOST-737/60-tech-debt.md` |

### PYPOST-738 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-817](https://pypost.atlassian.net/browse/PYPOST-817) | \| Expand postponed annotations to `pypost/ui/` \| P3 \| ~60 UI modules remain \| | `PYPOST-738/60-tech-debt.md` |

### PYPOST-739 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-733](https://pypost.atlassian.net/browse/PYPOST-733) | R-P2-004 \| P2 \| Narrow `except Exception` in storage/request_manager \| | `PYPOST-739/60-tech-debt.md` |

### PYPOST-740 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-696](https://pypost.atlassian.net/browse/PYPOST-696) | Relocate `is_tab_dirty` to UI layer \| | `PYPOST-740/60-tech-debt.md` |

### PYPOST-747 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-751](https://pypost.atlassian.net/browse/PYPOST-751) | Bulk legacy log migration \| ~30 legacy patterns remain; migrate on touch \| | `PYPOST-747/60-tech-debt.md` |
| [PYPOST-801](https://pypost.atlassian.net/browse/PYPOST-801) | Startup/shutdown legacy strings \| `PyPost starting up` in `main.py` | `PYPOST-747/60-tech-debt.md` |

### PYPOST-772 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-816](https://pypost.atlassian.net/browse/PYPOST-816) | Remediation:** Implement `scripts/verify_ai_task_artifacts.py` and wire into Makefile. | `PYPOST-772/60-tech-debt.md` |

### PYPOST-779 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-780](https://pypost.atlassian.net/browse/PYPOST-780) | Remediation:** `requirements-dev.txt` with pins; `make install-dev`. | `PYPOST-779/60-tech-debt.md` |

### PYPOST-780 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-434](https://pypost.atlassian.net/browse/PYPOST-434) | Remediation | `PYPOST-780/60-tech-debt.md` |
| [PYPOST-804](https://pypost.atlassian.net/browse/PYPOST-804) | Remediation:** Add lightweight job with `uv` setup when CI uv adoption is standardized. | `PYPOST-780/60-tech-debt.md` |
| [PYPOST-805](https://pypost.atlassian.net/browse/PYPOST-805) | Remediation:** Add to `requirements-dev.in` if security tooling should share the dev lock. | `PYPOST-780/60-tech-debt.md` |

### PYPOST-785 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-806](https://pypost.atlassian.net/browse/PYPOST-806) | Remediation:** Add editable install target and migrate install docs when sibling ticket lands. | `PYPOST-785/60-tech-debt.md` |
| [PYPOST-807](https://pypost.atlassian.net/browse/PYPOST-807) | `pyproject.toml`. | `PYPOST-785/60-tech-debt.md` |

### PYPOST-786 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-809](https://pypost.atlassian.net/browse/PYPOST-809) | `LICENSES/` or document generation in CI. | `PYPOST-786/60-tech-debt.md` |
| [PYPOST-810](https://pypost.atlassian.net/browse/PYPOST-810) | `doc/dev/licensing.md` with any platform-specific notes. | `PYPOST-786/60-tech-debt.md` |

### PYPOST-787 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-811](https://pypost.atlassian.net/browse/PYPOST-811) | unconditionally. | `PYPOST-787/60-tech-debt.md` |
| [PYPOST-812](https://pypost.atlassian.net/browse/PYPOST-812) | Remediation:** Consider consolidating when editable install is wired (PYPOST-806). | `PYPOST-787/60-tech-debt.md` |

### PYPOST-792 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-688](https://pypost.atlassian.net/browse/PYPOST-688) | Low \| **Pre-existing: replace `print()` in `config_manager.py`** with structured logging \| PYPOST... | `PYPOST-792/60-tech-debt.md` |
| [PYPOST-793](https://pypost.atlassian.net/browse/PYPOST-793) | Medium \| **Consolidate style bootstrapping | `PYPOST-792/60-tech-debt.md` |
| [PYPOST-795](https://pypost.atlassian.net/browse/PYPOST-795) | Low \| **Evaluate removing `set_close_button_size`** if no caller materializes | `PYPOST-792/60-tech-debt.md` |

### PYPOST-793 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-794](https://pypost.atlassian.net/browse/PYPOST-794) | Low \| **Add Makefile `help` target** \| Workspace Makefile rule compliance \| | `PYPOST-793/60-tech-debt.md` |
| [PYPOST-796](https://pypost.atlassian.net/browse/PYPOST-796) | Medium \| **Improve `close.svg` contrast on dark tab chrome** \| Accessibility / polish; unrelated ... | `PYPOST-793/60-tech-debt.md` |

### PYPOST-794 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-800](https://pypost.atlassian.net/browse/PYPOST-800) | Low \| Add pytest smoke for `make help` non-empty output \| Would catch accidental removal of `##` ... | `PYPOST-794/60-tech-debt.md` |

### PYPOST-797 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-798](https://pypost.atlassian.net/browse/PYPOST-798) | Low \| **Add regression test for `tabBarClicked` fallback | `PYPOST-797/60-tech-debt.md` |

### PYPOST-799 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-677](https://pypost.atlassian.net/browse/PYPOST-677) | Composition root inject `MetricsServer` separately | `PYPOST-799/60-tech-debt.md` |

### PYPOST-813 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-734](https://pypost.atlassian.net/browse/PYPOST-734) | Remaining baseline work is ticketed under parent | `PYPOST-813/60-tech-debt.md` |
| [PYPOST-815](https://pypost.atlassian.net/browse/PYPOST-815) | \| R-P2-005b — Align ExecuteRequestProtocol with RequestService \| [PYPOST-814](https://pypost.atla... | `PYPOST-813/60-tech-debt.md` |

### PYPOST-823 (7 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-824](https://pypost.atlassian.net/browse/PYPOST-824) | Fix tabs-presenter close-focus failures (land-on-plus assertions) \| Medium \| Out of scope here; | `PYPOST-823/60-tech-debt.md` |
| [PYPOST-825](https://pypost.atlassian.net/browse/PYPOST-825) | Fix tabs-presenter close-focus failures (land-on-plus assertions) \| Medium \| Out of scope here; [... | `PYPOST-823/60-tech-debt.md` |
| [PYPOST-826](https://pypost.atlassian.net/browse/PYPOST-826) | Fix tabs-presenter close-focus failures (land-on-plus assertions) \| Medium \| Out of scope here; [... | `PYPOST-823/60-tech-debt.md` |
| [PYPOST-827](https://pypost.atlassian.net/browse/PYPOST-827) | Port hardened `_process_until` (or extract shared helper) to sibling gateway/worker tests \| Mediu... | `PYPOST-823/60-tech-debt.md` |
| [PYPOST-828](https://pypost.atlassian.net/browse/PYPOST-828) | Richer timeout diagnostics (busy/pending, optional worker state) in wait helper \| Low \| Architect... | `PYPOST-823/60-tech-debt.md` |
| [PYPOST-829](https://pypost.atlassian.net/browse/PYPOST-829) | Gateway worker `deleteLater` / short `wait` on finish (H3) \| Low \| Only if suite shows stranded `... | `PYPOST-823/60-tech-debt.md` |
| [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) | Align remaining gateway tests on shared `qapp` fixture \| Low \| Consistency with responsiveness mo... | `PYPOST-823/60-tech-debt.md` |

### PYPOST-824 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-831](https://pypost.atlassian.net/browse/PYPOST-831) | Apply same navigable reselect after `close_tabs_for_request_ids` \| Low \| Same Qt `removeTab` trap... | `PYPOST-824/60-tech-debt.md` |

### PYPOST-827 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-877](https://pypost.atlassian.net/browse/PYPOST-877) | Port `process_until` into env-presenter async-load nested wait \| Medium \| **NEW | `PYPOST-827/60-tech-debt.md` |

### PYPOST-828 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-878](https://pypost.atlassian.net/browse/PYPOST-878) | TD-1 \| Low \| Wire `worker_operation` into env gateway timeout detail \| Read env worker `_operatio... | `PYPOST-828/60-tech-debt.md` |
| [PYPOST-879](https://pypost.atlassian.net/browse/PYPOST-879) | TD-2 \| Lowest \| Optional shared `worker_timeout_detail` helper \| Extract from `test_collection_st... | `PYPOST-828/60-tech-debt.md` |
| [PYPOST-880](https://pypost.atlassian.net/browse/PYPOST-880) | TD-3 \| Low \| Run full `make check` when sibling noise is clear \| Deferred scoped gate; not a DoD ... | `PYPOST-828/60-tech-debt.md` |

### PYPOST-829 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-881](https://pypost.atlassian.net/browse/PYPOST-881) | TD-1 \| Lowest \| Optional shared finish-teardown helper for both gateways \| Extract only if a thir... | `PYPOST-829/60-tech-debt.md` |
| [PYPOST-882](https://pypost.atlassian.net/browse/PYPOST-882) | TD-2 \| Low \| Run full `make check` when sibling suite noise is clear \| Deferred scoped gate; not ... | `PYPOST-829/60-tech-debt.md` |

### PYPOST-830 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-883](https://pypost.atlassian.net/browse/PYPOST-883) | TD-1 \| Medium \| Investigate intermittent full-suite hang on `test_save_async_emits_save_completed... | `PYPOST-830/60-tech-debt.md` |
| [PYPOST-884](https://pypost.atlassian.net/browse/PYPOST-884) | TD-2 \| Low \| Align `test_collection_storage_worker.py` onto shared `qapp` \| Closest remaining sto... | `PYPOST-830/60-tech-debt.md` |
| [PYPOST-885](https://pypost.atlassian.net/browse/PYPOST-885) | TD-3 \| Lowest \| Optional: convert gateway `TestCase` modules to free functions with `qapp` param ... | `PYPOST-830/60-tech-debt.md` |
| [PYPOST-886](https://pypost.atlassian.net/browse/PYPOST-886) | TD-4 \| Low \| Suite-wide migrate remaining `setUpClass` / local `qapp` modules onto conftest `qapp... | `PYPOST-830/60-tech-debt.md` |

### PYPOST-833 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-840](https://pypost.atlassian.net/browse/PYPOST-840) | TD-1 \| Low \| Deduplicate `_wait_until` with a production-safe shared helper \| Keep `pypost.agent`... | `PYPOST-833/60-tech-debt.md` |
| [PYPOST-841](https://pypost.atlassian.net/browse/PYPOST-841) | TD-2 \| Low \| Harden mid-start failure cleanup (try/finally transactional shutdown) \| Best-effort ... | `PYPOST-833/60-tech-debt.md` |
| [PYPOST-842](https://pypost.atlassian.net/browse/PYPOST-842) | TD-3 \| Low \| Strengthen FR6 smoke: assert previous metrics port is free \| Soft relaunch coverage ... | `PYPOST-833/60-tech-debt.md` |
| [PYPOST-843](https://pypost.atlassian.net/browse/PYPOST-843) | TD-4 \| Low \| Run full `make check` after sibling noise is clear \| Deferred in Step 4 cleanup; not... | `PYPOST-833/60-tech-debt.md` |

### PYPOST-834 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-844](https://pypost.atlassian.net/browse/PYPOST-844) | TD-1 \| Low \| Optional assert: theme apply leaves key objectNames \| Low risk today \| | `PYPOST-834/60-tech-debt.md` |
| [PYPOST-845](https://pypost.atlassian.net/browse/PYPOST-845) | TD-2 \| Low \| Align `plus_tab_placeholder` to `pypost_` prefix \| Not an AC surface \| | `PYPOST-834/60-tech-debt.md` |
| [PYPOST-846](https://pypost.atlassian.net/browse/PYPOST-846) | TD-3 \| Low \| Multi-tab spot-check for role ids \| Implicit via constructors \| | `PYPOST-834/60-tech-debt.md` |
| [PYPOST-847](https://pypost.atlassian.net/browse/PYPOST-847) | TD-4 \| Low \| Run full `make check` when sibling noise is clear \| Deferred gate \| | `PYPOST-834/60-tech-debt.md` |

### PYPOST-835 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-848](https://pypost.atlassian.net/browse/PYPOST-848) | TD-1 \| Low \| Document or name the item-view selection cap (or raise it) \| `indexes[:5]` magic \| | `PYPOST-835/60-tech-debt.md` |
| [PYPOST-849](https://pypost.atlassian.net/browse/PYPOST-849) | TD-2 \| Low \| Truncation marker (e.g. ellipsis) when slicing values \| Agents can detect clip \| | `PYPOST-835/60-tech-debt.md` |
| [PYPOST-850](https://pypost.atlassian.net/browse/PYPOST-850) | TD-6 \| Low \| Optional richer roles (checkbox, spin, table) if agents need them \| Beyond v1 FR sur... | `PYPOST-835/60-tech-debt.md` |

### PYPOST-836 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-851](https://pypost.atlassian.net/browse/PYPOST-851) | Debt item (line 37) | `PYPOST-836/60-tech-debt.md` |

### PYPOST-837 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-852](https://pypost.atlassian.net/browse/PYPOST-852) | TD-2 \| Low \| Optional “no text API” fast-fail when widget exists but text cannot be read \| Delive... | `PYPOST-837/60-tech-debt.md` |

### PYPOST-838 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-853](https://pypost.atlassian.net/browse/PYPOST-853) | TD-3 \| Medium \| Failure-path golden (forced settle timeout) \| Delivered in | `PYPOST-838/60-tech-debt.md` |
| [PYPOST-920](https://pypost.atlassian.net/browse/PYPOST-920) | TD-1 \| Low \| Optional `pypost_response_status` / `pypost_response_body` ids \| | `PYPOST-838/60-tech-debt.md` |
| [PYPOST-921](https://pypost.atlassian.net/browse/PYPOST-921) | TD-4 \| Low \| Plus-tab create path when blank restore changes \| | `PYPOST-838/60-tech-debt.md` |
| [PYPOST-922](https://pypost.atlassian.net/browse/PYPOST-922) | TD-5 \| Medium \| Broader agent-e2e packaging / `make` entry \| | `PYPOST-838/60-tech-debt.md` |

### PYPOST-839 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-858](https://pypost.atlassian.net/browse/PYPOST-858) | TD-1 \| Low \| Optional `@pytest.mark.agent_e2e` + marker-based make target \| Absorbed by | `PYPOST-839/60-tech-debt.md` |
| [PYPOST-861](https://pypost.atlassian.net/browse/PYPOST-861) | TD-2 \| Low \| Optional `test_makefile.py` smoke for `test-agent-e2e` help/prereqs \| Absorbed by | `PYPOST-839/60-tech-debt.md` |

### PYPOST-851 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-916](https://pypost.atlassian.net/browse/PYPOST-916) | TD-1 \| Low \| Extend `ui_select` beyond QComboBox \| | `PYPOST-851/60-tech-debt.md` |
| [PYPOST-917](https://pypost.atlassian.net/browse/PYPOST-917) | TD-2 \| Low \| Optional fill-via-keyClicks mode \| | `PYPOST-851/60-tech-debt.md` |
| [PYPOST-918](https://pypost.atlassian.net/browse/PYPOST-918) | TD-3 \| Lowest \| Out-of-process MCP packaging for actions \| | `PYPOST-851/60-tech-debt.md` |

### PYPOST-856 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-857](https://pypost.atlassian.net/browse/PYPOST-857) | Workspace seed fixtures \| | `PYPOST-856/60-tech-debt.md` |
| [PYPOST-860](https://pypost.atlassian.net/browse/PYPOST-860) | Failure artifacts (+ secret-safe dumps) \| | `PYPOST-856/60-tech-debt.md` |

### PYPOST-857 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-862](https://pypost.atlassian.net/browse/PYPOST-862) | `tests/test_agent_e2e_seed.py`. | `PYPOST-857/60-tech-debt.md` |
| [PYPOST-863](https://pypost.atlassian.net/browse/PYPOST-863) | active-env or open-request guarantees; otherwise leave to consumers. | `PYPOST-857/60-tech-debt.md` |

### PYPOST-858 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-865](https://pypost.atlassian.net/browse/PYPOST-865) | existing marks, or document intentional deferral in testing.md. | `PYPOST-858/60-tech-debt.md` |
| [PYPOST-866](https://pypost.atlassian.net/browse/PYPOST-866) | table). | `PYPOST-858/60-tech-debt.md` |
| [PYPOST-867](https://pypost.atlassian.net/browse/PYPOST-867) | `caplog.at_level(INFO, logger="tests._pytest_plugins.agent_e2e")`. | `PYPOST-858/60-tech-debt.md` |

### PYPOST-859 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-868](https://pypost.atlassian.net/browse/PYPOST-868) | overload to `stub_agent_e2e_http` with documented match rules. | `PYPOST-859/60-tech-debt.md` |
| [PYPOST-870](https://pypost.atlassian.net/browse/PYPOST-870) | `caplog.at_level(INFO, logger="pypost.fixtures.agent_e2e_http")`. | `PYPOST-859/60-tech-debt.md` |
| [PYPOST-871](https://pypost.atlassian.net/browse/PYPOST-871) | (blank or seeded), asserting body/status. | `PYPOST-859/60-tech-debt.md` |

### PYPOST-860 (5 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-835](https://pypost.atlassian.net/browse/PYPOST-835) | Snapshot API / masking \| | `PYPOST-860/60-tech-debt.md` |
| [PYPOST-856](https://pypost.atlassian.net/browse/PYPOST-856) | Env contract model \| | `PYPOST-860/60-tech-debt.md` |
| [PYPOST-874](https://pypost.atlassian.net/browse/PYPOST-874) | `doc/dev/agent_e2e_failure_artifacts.md` | `PYPOST-860/60-tech-debt.md` |
| [PYPOST-875](https://pypost.atlassian.net/browse/PYPOST-875) | `pypost/fixtures/agent_e2e_failure.py` | `PYPOST-860/60-tech-debt.md` |
| [PYPOST-876](https://pypost.atlassian.net/browse/PYPOST-876) | Files:** `pypost/fixtures/agent_e2e_failure.py` | `PYPOST-860/60-tech-debt.md` |

### PYPOST-861 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-854](https://pypost.atlassian.net/browse/PYPOST-854) | Link 854 → 861 and close debt once make smoke + CI job are on main. | `PYPOST-861/60-tech-debt.md` |
| [PYPOST-872](https://pypost.atlassian.net/browse/PYPOST-872) | documenting the install-first contract in one place. | `PYPOST-861/60-tech-debt.md` |
| [PYPOST-873](https://pypost.atlassian.net/browse/PYPOST-873) | Only if double-run minutes become painful; keep dual coverage until then. | `PYPOST-861/60-tech-debt.md` |

### PYPOST-862 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-864](https://pypost.atlassian.net/browse/PYPOST-864) | Inventory drift guard (code ↔ doc) \| | `PYPOST-862/60-tech-debt.md` |

### PYPOST-867 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-899](https://pypost.atlassian.net/browse/PYPOST-899) | lifecycle smoke with caplog (cost: Qt session time). | `PYPOST-867/60-tech-debt.md` |
| [PYPOST-900](https://pypost.atlassian.net/browse/PYPOST-900) | Remediation:** `tests/helpers/` helper used by packaging log tests. | `PYPOST-867/60-tech-debt.md` |

### PYPOST-869 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-895](https://pypost.atlassian.net/browse/PYPOST-895) | `agent_e2e_timeouts.py`) and import in Send modules. | `PYPOST-869/60-tech-debt.md` |
| [PYPOST-896](https://pypost.atlassian.net/browse/PYPOST-896) | `response_panel_excerpt(last)` + diagnostics key. | `PYPOST-869/60-tech-debt.md` |

### PYPOST-870 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-859](https://pypost.atlassian.net/browse/PYPOST-859) | None specific to this HTTP-stub install caplog debt beyond the closed | `PYPOST-870/60-tech-debt.md` |
| [PYPOST-903](https://pypost.atlassian.net/browse/PYPOST-903) | `tests/test_agent_e2e_http_stub_logs.py`. | `PYPOST-870/60-tech-debt.md` |

### PYPOST-871 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-897](https://pypost.atlassian.net/browse/PYPOST-897) | for env). | `PYPOST-871/60-tech-debt.md` |
| [PYPOST-898](https://pypost.atlassian.net/browse/PYPOST-898) | POST item via tree identities, then Sends under the shared stub. | `PYPOST-871/60-tech-debt.md` |

### PYPOST-872 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-905](https://pypost.atlassian.net/browse/PYPOST-905) | reduce repeated editable install cost on every test target. | `PYPOST-872/60-tech-debt.md` |
| [PYPOST-906](https://pypost.atlassian.net/browse/PYPOST-906) | Same DX argument as pytest targets; out of PYPOST-872 title scope. | `PYPOST-872/60-tech-debt.md` |

### PYPOST-873 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-907](https://pypost.atlassian.net/browse/PYPOST-907) | `tests/test_agent_e2e_ci_double_run_doc.py` and docs. | `PYPOST-873/60-tech-debt.md` |
| [PYPOST-908](https://pypost.atlassian.net/browse/PYPOST-908) | the next ENABLE/DEFER call with numbers. | `PYPOST-873/60-tech-debt.md` |

### PYPOST-874 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-909](https://pypost.atlassian.net/browse/PYPOST-909) | Files: `.github/workflows/test.yml`, docs, lock test | `PYPOST-874/60-tech-debt.md` |
| [PYPOST-910](https://pypost.atlassian.net/browse/PYPOST-910) | Files: `.github/workflows/test.yml` | `PYPOST-874/60-tech-debt.md` |

### PYPOST-875 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-912](https://pypost.atlassian.net/browse/PYPOST-912) | `pypost/agent/lifecycle.py` | `PYPOST-875/60-tech-debt.md` |
| [PYPOST-913](https://pypost.atlassian.net/browse/PYPOST-913) | `doc/dev/agent_e2e_failure_artifacts.md`, tests | `PYPOST-875/60-tech-debt.md` |

### PYPOST-876 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-914](https://pypost.atlassian.net/browse/PYPOST-914) | `doc/dev/agent_e2e_failure_artifacts.md` | `PYPOST-876/60-tech-debt.md` |
| [PYPOST-915](https://pypost.atlassian.net/browse/PYPOST-915) | Files:** `tests/test_agent_e2e_failure_artifacts.py` | `PYPOST-876/60-tech-debt.md` |

### PYPOST-889 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-887](https://pypost.atlassian.net/browse/PYPOST-887) | Product double-body discard fix \| | `PYPOST-889/60-tech-debt.md` |
| [PYPOST-888](https://pypost.atlassian.net/browse/PYPOST-888) | Broader Send/response presentation matrix \| Epic | `PYPOST-889/60-tech-debt.md` |
| [PYPOST-892](https://pypost.atlassian.net/browse/PYPOST-892) | TD-1 \| Low \| Automate FR5 red-path proof \| Optional second test (or marked variant) that monkeypa... | `PYPOST-889/60-tech-debt.md` |
| [PYPOST-893](https://pypost.atlassian.net/browse/PYPOST-893) | TD-2 \| Lowest \| Improve stub catalog naming for streaming helpers \| When `stub_agent_e2e_http` re... | `PYPOST-889/60-tech-debt.md` |

### PYPOST-890 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-869](https://pypost.atlassian.net/browse/PYPOST-869) | extracting a shared helper (architecture: share later). Already tracked | `PYPOST-890/60-tech-debt.md` |
| [PYPOST-891](https://pypost.atlassian.net/browse/PYPOST-891) | Triage findings / file Bugs from matrix \| | `PYPOST-890/60-tech-debt.md` |
| [PYPOST-894](https://pypost.atlassian.net/browse/PYPOST-894) | TD-2 \| Lowest \| Spot-check / KEY list for `REQUEST_DETAIL_TABS` \| Optionally add to `KEY_WIDGET_I... | `PYPOST-890/60-tech-debt.md` |

### PYPOST-891 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-889](https://pypost.atlassian.net/browse/PYPOST-889) | Focused double-body lock \| | `PYPOST-891/60-tech-debt.md` |
| [PYPOST-890](https://pypost.atlassian.net/browse/PYPOST-890) | Presentation matrix + findings \| | `PYPOST-891/60-tech-debt.md` |

### PYPOST-901 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-902](https://pypost.atlassian.net/browse/PYPOST-902) | method+URL compound map keys \| Out of scope | `PYPOST-901/60-tech-debt.md` |
| [PYPOST-955](https://pypost.atlassian.net/browse/PYPOST-955) | TD-1 \| Medium \| Agent e2e timeout companion for mapping settle diagnostics \| Mirror `test_agent_g... | `PYPOST-901/60-tech-debt.md` |
| [PYPOST-956](https://pypost.atlassian.net/browse/PYPOST-956) | TD-2 \| Low \| Shared Send settle + timeout rewrap helper \| Extract `_wait_response` pattern from m... | `PYPOST-901/60-tech-debt.md` |
| [PYPOST-957](https://pypost.atlassian.net/browse/PYPOST-957) | TD-3 \| Low \| Caplog proof for `name=url_router` in mapping GUI module \| Optional sibling to PYPOS... | `PYPOST-901/60-tech-debt.md` |

### PYPOST-902 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-958](https://pypost.atlassian.net/browse/PYPOST-958) | GUI scenario: same URL, GET+POST under compound-key map \| Lowest \| Optional confidence raise; uni... | `PYPOST-902/60-tech-debt.md` |
| [PYPOST-959](https://pypost.atlassian.net/browse/PYPOST-959) | HTTP method case normalization in router \| Lowest \| Only if scenarios send inconsistent casing \| | `PYPOST-902/60-tech-debt.md` |

### PYPOST-903 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-904](https://pypost.atlassian.net/browse/PYPOST-904) | Technical debt follow-up | `PYPOST-903/60-tech-debt.md` |

### PYPOST-905 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-929](https://pypost.atlassian.net/browse/PYPOST-929) | pip). | `PYPOST-905/60-tech-debt.md` |

### PYPOST-906 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-932](https://pypost.atlassian.net/browse/PYPOST-932) | the Step 7 review. Historical ai-tasks prose left as point-in-time. | `PYPOST-906/60-tech-debt.md` |

### PYPOST-907 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-930](https://pypost.atlassian.net/browse/PYPOST-930) | a 3.13 coverage plan; update lock + docs for ENABLE. | `PYPOST-907/60-tech-debt.md` |

### PYPOST-908 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-931](https://pypost.atlassian.net/browse/PYPOST-931) | Already ticketed — may absorb any residual “refresh” work from 908. | `PYPOST-908/60-tech-debt.md` |

### PYPOST-909 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-911](https://pypost.atlassian.net/browse/PYPOST-911) | Files: `doc/dev/agent_e2e_failure_artifacts.md` (optional note) | `PYPOST-909/60-tech-debt.md` |

### PYPOST-911 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-933](https://pypost.atlassian.net/browse/PYPOST-933) | `doc/dev/agent_e2e_failure_artifacts.md` | `PYPOST-911/60-tech-debt.md` |

### PYPOST-915 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-960](https://pypost.atlassian.net/browse/PYPOST-960) | Shared exception tuple module \| | `PYPOST-915/60-tech-debt.md` |
| [PYPOST-962](https://pypost.atlassian.net/browse/PYPOST-962) | Priority:** Lowest | `PYPOST-915/60-tech-debt.md` |

### PYPOST-916 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-939](https://pypost.atlassian.net/browse/PYPOST-939) | TD-1 \| Low \| Support `QListView` / generic `QAbstractItemView` in `ui_select` \| Only if a golden ... | `PYPOST-916/60-tech-debt.md` |
| [PYPOST-940](https://pypost.atlassian.net/browse/PYPOST-940) | TD-2 \| Low \| Harden fixture teardown for Qt item views \| Documented `setModel(None)` pattern; con... | `PYPOST-916/60-tech-debt.md` |
| [PYPOST-941](https://pypost.atlassian.net/browse/PYPOST-941) | TD-3 \| Low \| Share tree text walk with `agent_e2e_tree` \| Avoid duplication if both keep growing;... | `PYPOST-916/60-tech-debt.md` |
| [PYPOST-942](https://pypost.atlassian.net/browse/PYPOST-942) | TD-4 \| Low \| Dedicated out-of-range / missing-option tests for list and tree \| Mirror combo `opti... | `PYPOST-916/60-tech-debt.md` |

### PYPOST-917 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-944](https://pypost.atlassian.net/browse/PYPOST-944) | TD-1 \| Low \| Caplog assert for `via_key_clicks=true` \| Mirror false-path scalar check; optional h... | `PYPOST-917/60-tech-debt.md` |
| [PYPOST-945](https://pypost.atlassian.net/browse/PYPOST-945) | TD-2 \| Low \| Fixture keyClicks coverage for plain/rich text edits \| Line-edit proof + type guard ... | `PYPOST-917/60-tech-debt.md` |
| [PYPOST-946](https://pypost.atlassian.net/browse/PYPOST-946) | TD-3 \| Lowest \| Optional `textChanged` multi-emit assert for keyClicks \| Proves per-key delivery ... | `PYPOST-917/60-tech-debt.md` |
| [PYPOST-947](https://pypost.atlassian.net/browse/PYPOST-947) | TD-4 \| Lowest \| Optional `delay` kwarg on keyClicks fill \| Architecture deliberately omitted; exp... | `PYPOST-917/60-tech-debt.md` |

### PYPOST-918 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-952](https://pypost.atlassian.net/browse/PYPOST-952) | Files (future): new agent-UI MCP entry + docs; not this debt’s surface | `PYPOST-918/60-tech-debt.md` |
| [PYPOST-953](https://pypost.atlassian.net/browse/PYPOST-953) | Files: `tests/test_mcp_server_impl.py` (or sibling) when prioritized | `PYPOST-918/60-tech-debt.md` |
| [PYPOST-954](https://pypost.atlassian.net/browse/PYPOST-954) | Files: `tests/test_ui_actions_mcp_packaging_doc.py` | `PYPOST-918/60-tech-debt.md` |

### PYPOST-919 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-934](https://pypost.atlassian.net/browse/PYPOST-934) | TD-1 \| Medium \| Agent e2e timeout companion for dialog settle diagnostics \| Mirror golden `test_a... | `PYPOST-919/60-tech-debt.md` |
| [PYPOST-935](https://pypost.atlassian.net/browse/PYPOST-935) | TD-2 \| Low \| `SETTINGS_DIALOG` widget id on `SettingsDialog` \| Set `objectName` via `widget_ids` ... | `PYPOST-919/60-tech-debt.md` |
| [PYPOST-936](https://pypost.atlassian.net/browse/PYPOST-936) | TD-3 \| Low \| Shared modal settle helper for agent e2e \| Extract timer + `wait_until` + fail-close... | `PYPOST-919/60-tech-debt.md` |

### PYPOST-920 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-948](https://pypost.atlassian.net/browse/PYPOST-948) | TD-1 \| Medium \| Migrate sibling agent e2e off panel-walk settle onto `wait_for_text` (`RESPONSE_S... | `PYPOST-920/60-tech-debt.md` |
| [PYPOST-949](https://pypost.atlassian.net/browse/PYPOST-949) | TD-2 \| Low \| Add `in_current_tab` (or root override) to `AgentAppSession.wait_for_text` / related... | `PYPOST-920/60-tech-debt.md` |
| [PYPOST-950](https://pypost.atlassian.net/browse/PYPOST-950) | TD-3 \| Low \| Align golden timeout-diagnostics lock with text-wait settle \| Force a short `wait_fo... | `PYPOST-920/60-tech-debt.md` |

### PYPOST-921 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-951](https://pypost.atlassian.net/browse/PYPOST-951) | TD-2 \| Low \| Document `removeTab` orphan hazard for agent authors \| Partially covered in golden d... | `PYPOST-921/60-tech-debt.md` |

### PYPOST-922 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-937](https://pypost.atlassian.net/browse/PYPOST-937) | Files: `tests/test_makefile.py` (or a small test helper module) | `PYPOST-922/60-tech-debt.md` |
| [PYPOST-938](https://pypost.atlassian.net/browse/PYPOST-938) | Files: `tests/test_agent_e2e_broader_packaging_doc.py` | `PYPOST-922/60-tech-debt.md` |

### PYPOST-923 (5 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-924](https://pypost.atlassian.net/browse/PYPOST-924) | TD-1 \| Low \| Extract shared Qt/EGL apt install into a composite action (or reusable workflow step... | `PYPOST-923/60-tech-debt.md` |
| [PYPOST-925](https://pypost.atlassian.net/browse/PYPOST-925) | TD-2 \| Low \| Strengthen smoke Qt contract: derive expected package set from peer job YAML (and/or... | `PYPOST-923/60-tech-debt.md` |
| [PYPOST-926](https://pypost.atlassian.net/browse/PYPOST-926) | TD-3 \| Lowest \| Optionally defer `PySide6` import in `tests/conftest.py` so non-GUI collection pa... | `PYPOST-923/60-tech-debt.md` |
| [PYPOST-927](https://pypost.atlassian.net/browse/PYPOST-927) | TD-4 \| Low \| Add CI `check-lock` job for production `requirements.txt` (sibling of `check-lock-de... | `PYPOST-923/60-tech-debt.md` |
| [PYPOST-928](https://pypost.atlassian.net/browse/PYPOST-928) | TD-5 \| Lowest \| Harden workflow YAML parsing helpers shared by CI contract tests (or adopt a tiny... | `PYPOST-923/60-tech-debt.md` |

### PYPOST-924 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-923](https://pypost.atlassian.net/browse/PYPOST-923) | `test`, `make-install-smoke`, and `agent-e2e`. Resolves | `PYPOST-924/60-tech-debt.md` |

### PYPOST-934 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-429](https://pypost.atlassian.net/browse/PYPOST-429) | function; avoids known multi-session-after-modal segfault risk | `PYPOST-934/60-tech-debt.md` |
| [PYPOST-919](https://pypost.atlassian.net/browse/PYPOST-919) | \| TD-1 \| Medium \| Agent e2e timeout companion for dialog settle diagnostics \| **Done** — `test_ag... | `PYPOST-934/60-tech-debt.md` |
| [PYPOST-968](https://pypost.atlassian.net/browse/PYPOST-968) | TD-3 \| Low \| `caplog` assert on `ui_wait_timeout` for forced path \| Only if DEBUG log regression ... | `PYPOST-934/60-tech-debt.md` |

### PYPOST-939 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-971](https://pypost.atlassian.net/browse/PYPOST-971) | TD-1 \| Low \| Share flat DisplayRole scan between item view and tree helpers \| Only if drift grows. | `PYPOST-939/60-tech-debt.md` |
| [PYPOST-972](https://pypost.atlassian.net/browse/PYPOST-972) | TD-2 \| Low \| Dedicated `item view has no model` test \| Mirror tree no-model coverage. | `PYPOST-939/60-tech-debt.md` |

### PYPOST-942 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-974](https://pypost.atlassian.net/browse/PYPOST-974) | TD-1 \| Low \| Combo out-of-range index contract test \| `_select_combo` raises the same `option ind... | `PYPOST-942/60-tech-debt.md` |
| [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) | TD-2 \| Low \| Live collection-tree negative select via `agent_e2e_session` \| Optional hardening; f... | `PYPOST-942/60-tech-debt.md` |

### PYPOST-943 (7 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-559](https://pypost.atlassian.net/browse/PYPOST-559) | Slow smoke job design + pydantic import sanity \| | `PYPOST-943/60-tech-debt.md` |
| [PYPOST-808](https://pypost.atlassian.net/browse/PYPOST-808) | Dynamic version attr trigger \| | `PYPOST-943/60-tech-debt.md` |
| [PYPOST-963](https://pypost.atlassian.net/browse/PYPOST-963) | TD-1 \| Low \| Document or assert minimum `pypost/` tree policy for slow-smoke seed (stub `__init__... | `PYPOST-943/60-tech-debt.md` |
| [PYPOST-964](https://pypost.atlassian.net/browse/PYPOST-964) | TD-2 \| Low \| Extend `_required_seed_paths_from_pyproject` when `pyproject.toml` gains additional ... | `PYPOST-943/60-tech-debt.md` |
| [PYPOST-965](https://pypost.atlassian.net/browse/PYPOST-965) | TD-3 \| Low \| Deduplicate slow-smoke workspace assembly: share one helper between `make_workspace_... | `PYPOST-943/60-tech-debt.md` |
| [PYPOST-966](https://pypost.atlassian.net/browse/PYPOST-966) | TD-4 \| Lowest \| Optionally add post-install `import pypost` (or version attr read) to slow smoke ... | `PYPOST-943/60-tech-debt.md` |
| [PYPOST-967](https://pypost.atlassian.net/browse/PYPOST-967) | TD-5 \| Low \| Refresh `test_verify_ai_task_artifacts` baseline after Step 8 dev docs land \| Expect... | `PYPOST-943/60-tech-debt.md` |

### PYPOST-945 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-976](https://pypost.atlassian.net/browse/PYPOST-976) | UT-1 \| Lowest \| Session body-editor keyClicks smoke \| `agent_e2e_session` fills request body via ... | `PYPOST-945/60-tech-debt.md` |
| [PYPOST-977](https://pypost.atlassian.net/browse/PYPOST-977) | UT-2 \| Lowest \| Caplog keyClicks on plain/rich fixtures \| Extend or sibling caplog test using pla... | `PYPOST-945/60-tech-debt.md` |

### PYPOST-946 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-980](https://pypost.atlassian.net/browse/PYPOST-980) | UT-1 \| Lowest \| Plain/rich `textChanged` multi-emit \| Sibling tests on plain/rich fixtures with d... | `PYPOST-946/60-tech-debt.md` |
| [PYPOST-981](https://pypost.atlassian.net/browse/PYPOST-981) | UT-2 \| Lowest \| Default setter single-emit contrast \| Optional test: default `ui_fill` emits one ... | `PYPOST-946/60-tech-debt.md` |

### PYPOST-948 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-969](https://pypost.atlassian.net/browse/PYPOST-969) | TD-3 \| Low \| Extend Send settle convention lock to seed POST \| Optional module migrated but not i... | `PYPOST-948/60-tech-debt.md` |
| [PYPOST-970](https://pypost.atlassian.net/browse/PYPOST-970) | TD-4 \| Low \| Golden adopt `wait_response_after_send` for DRY settle \| Reduces duplicate timeout w... | `PYPOST-948/60-tech-debt.md` |

### PYPOST-949 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-978](https://pypost.atlassian.net/browse/PYPOST-978) | TD-1 \| Low \| Optional golden migration to `session.wait_for_text(..., in_current_tab=True)` \| Gol... | `PYPOST-949/60-tech-debt.md` |
| [PYPOST-979](https://pypost.atlassian.net/browse/PYPOST-979) | TD-2 \| Low \| Explicit tests for tab-scoped `wait_for_widget` / `wait_for_enabled` \| Multi-tab fix... | `PYPOST-949/60-tech-debt.md` |

### PYPOST-952 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-990](https://pypost.atlassian.net/browse/PYPOST-990) | Files: `pypost/agent/ui_actions_mcp.py`, docs | `PYPOST-952/60-tech-debt.md` |
| [PYPOST-991](https://pypost.atlassian.net/browse/PYPOST-991) | Files: new IPC layer + sidecar lifecycle | `PYPOST-952/60-tech-debt.md` |
| [PYPOST-992](https://pypost.atlassian.net/browse/PYPOST-992) | Files: `tests/test_agent_ui_actions_mcp.py` | `PYPOST-952/60-tech-debt.md` |
| [PYPOST-993](https://pypost.atlassian.net/browse/PYPOST-993) | Files: `ui_actions_mcp.py` CLI flags, agent_e2e helpers | `PYPOST-952/60-tech-debt.md` |

### PYPOST-953 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-994](https://pypost.atlassian.net/browse/PYPOST-994) | Files: `tests/test_mcp_server_impl.py`, `tests/test_agent_ui_actions_mcp.py` | `PYPOST-953/60-tech-debt.md` |

### PYPOST-955 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901) | Parent mapping multi-URL happy path \| | `PYPOST-955/60-tech-debt.md` |
| [PYPOST-982](https://pypost.atlassian.net/browse/PYPOST-982) | TD-1 \| Low \| Optional POST-path timeout companion \| Force near-zero settle after POST Send; asser... | `PYPOST-955/60-tech-debt.md` |
| [PYPOST-983](https://pypost.atlassian.net/browse/PYPOST-983) | TD-2 \| Low \| Centralize `FORCED_SETTLE_TIMEOUT_S` \| Same 0.05 s constant appears in golden, dialo... | `PYPOST-955/60-tech-debt.md` |

### PYPOST-956 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-985](https://pypost.atlassian.net/browse/PYPOST-985) | TD-3 \| Low \| Extract private `_rewrap_send_settle_timeout` if third consumer appears \| Must prese... | `PYPOST-956/60-tech-debt.md` |

### PYPOST-960 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-961](https://pypost.atlassian.net/browse/PYPOST-961) | Dedicated hook best-effort units per type \| | `PYPOST-960/60-tech-debt.md` |

### PYPOST-966 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-1014](https://pypost.atlassian.net/browse/PYPOST-1014) | TD-1 \| Low \| Revisit post-install snippet if `pypost/__init__.py` gains eager UI imports \| Versio... | `PYPOST-966/60-tech-debt.md` |

### PYPOST-984 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-995](https://pypost.atlassian.net/browse/PYPOST-995) | Debt item (line 47) | `PYPOST-984/60-tech-debt.md` |
| [PYPOST-996](https://pypost.atlassian.net/browse/PYPOST-996) | Debt item (line 64) | `PYPOST-984/60-tech-debt.md` |
| [PYPOST-997](https://pypost.atlassian.net/browse/PYPOST-997) | Debt item (line 80) | `PYPOST-984/60-tech-debt.md` |
| [PYPOST-998](https://pypost.atlassian.net/browse/PYPOST-998) | Debt item (line 93) | `PYPOST-984/60-tech-debt.md` |

### PYPOST-986 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-999](https://pypost.atlassian.net/browse/PYPOST-999) | verified one for this specific new caller. | `PYPOST-986/60-tech-debt.md` |
| [PYPOST-1000](https://pypost.atlassian.net/browse/PYPOST-1000) | functions work in isolation. | `PYPOST-986/60-tech-debt.md` |
| [PYPOST-1001](https://pypost.atlassian.net/browse/PYPOST-1001) | complementing the existing direct-call tests. | `PYPOST-986/60-tech-debt.md` |
| [PYPOST-1002](https://pypost.atlassian.net/browse/PYPOST-1002) | reaches `(3)`, closing the two small combinatorial test gaps noted above. | `PYPOST-986/60-tech-debt.md` |

### PYPOST-987 (5 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-1003](https://pypost.atlassian.net/browse/PYPOST-1003) | names, and add a regression test on each side. | `PYPOST-987/60-tech-debt.md` |
| [PYPOST-1004](https://pypost.atlassian.net/browse/PYPOST-1004) | "reload from disk" recovery offered in the failure dialog. | `PYPOST-987/60-tech-debt.md` |
| [PYPOST-1005](https://pypost.atlassian.net/browse/PYPOST-1005) | cannot freeze the window. Include a large-file test. | `PYPOST-987/60-tech-debt.md` |
| [PYPOST-1006](https://pypost.atlassian.net/browse/PYPOST-1006) | collection side. | `PYPOST-987/60-tech-debt.md` |
| [PYPOST-1007](https://pypost.atlassian.net/browse/PYPOST-1007) | false positives. | `PYPOST-987/60-tech-debt.md` |

### PYPOST-988 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-1008](https://pypost.atlassian.net/browse/PYPOST-1008) | Priority: Low | `PYPOST-988/60-tech-debt.md` |
| [PYPOST-1009](https://pypost.atlassian.net/browse/PYPOST-1009) | Priority: Low | `PYPOST-988/60-tech-debt.md` |
| [PYPOST-1010](https://pypost.atlassian.net/browse/PYPOST-1010) | Priority: Low | `PYPOST-988/60-tech-debt.md` |

### PYPOST-989 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-1011](https://pypost.atlassian.net/browse/PYPOST-1011) | Priority: Low | `PYPOST-989/60-tech-debt.md` |
| [PYPOST-1012](https://pypost.atlassian.net/browse/PYPOST-1012) | Priority: Low | `PYPOST-989/60-tech-debt.md` |
| [PYPOST-1013](https://pypost.atlassian.net/browse/PYPOST-1013) | Priority: Low | `PYPOST-989/60-tech-debt.md` |

## Debt Files Without Jira Links

These files document debt but contain no `PYPOST-*` Jira links yet (445 files):

- `PYPOST-101/60-tech-debt.md`
- `PYPOST-105/60-tech-debt.md`
- `PYPOST-106/60-tech-debt.md`
- `PYPOST-107/60-tech-debt.md`
- `PYPOST-111/60-tech-debt.md`
- `PYPOST-112/60-tech-debt.md`
- `PYPOST-113/60-tech-debt.md`
- `PYPOST-114/60-tech-debt.md`
- `PYPOST-123/60-tech-debt.md`
- `PYPOST-127/60-tech-debt.md`
- `PYPOST-129/60-tech-debt.md`
- `PYPOST-134/60-tech-debt.md`
- `PYPOST-135/60-tech-debt.md`
- `PYPOST-137/60-tech-debt.md`
- `PYPOST-138/60-tech-debt.md`
- `PYPOST-140/60-tech-debt.md`
- `PYPOST-141/60-tech-debt.md`
- `PYPOST-144/60-tech-debt.md`
- `PYPOST-145/60-tech-debt.md`
- `PYPOST-147/60-tech-debt.md`
- `PYPOST-148/60-tech-debt.md`
- `PYPOST-150/60-tech-debt.md`
- `PYPOST-152/60-tech-debt.md`
- `PYPOST-153/60-tech-debt.md`
- `PYPOST-154/60-tech-debt.md`
- `PYPOST-159/60-tech-debt.md`
- `PYPOST-161/60-tech-debt.md`
- `PYPOST-162/60-tech-debt.md`
- `PYPOST-164/60-tech-debt.md`
- `PYPOST-165/60-tech-debt.md`
- `PYPOST-166/60-tech-debt.md`
- `PYPOST-167/60-tech-debt.md`
- `PYPOST-168/60-tech-debt.md`
- `PYPOST-169/60-tech-debt.md`
- `PYPOST-17/40-tech-debt.md`
- `PYPOST-170/60-tech-debt.md`
- `PYPOST-172/60-tech-debt.md`
- `PYPOST-173/60-tech-debt.md`
- `PYPOST-174/60-tech-debt.md`
- `PYPOST-175/60-tech-debt.md`
- … and 405 more

## Remediation Notes

- Markdown/Jira hygiene: see [tech-debt-diff.md](../tech-debt-diff.md).
- Sprint 502 executes linked backlog items (UI polish & cleanup).
- Re-run this script when new `60-tech-debt.md` / `60-review.md` artifacts land.
