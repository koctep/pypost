# Consolidated Technical Debt Inventory

Generated for [PYPOST-57](https://pypost.atlassian.net/browse/PYPOST-57) on 2026-06-12.

Aggregated from `ai-tasks/**/60-review.md`, `ai-tasks/**/40-tech-debt.md`, and
`ai-tasks/**/60-tech-debt.md`. Each row links a source task artifact to its Jira
follow-up issue.

Regenerate: `python scripts/consolidate_tech_debt.py`

## Summary

| Metric | Count |
| --- | ---: |
| Source files scanned | 478 |
| Total Jira link references | 716 |
| Unique linked Jira issues | 482 |
| Source tasks with linked debt | 118 |
| Debt files without Jira links | 303 |

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
| [PYPOST-102](https://pypost.atlassian.net/browse/PYPOST-102) | Move color settings to application theme or config. | `PYPOST-11/40-tech-debt.md` |
| [PYPOST-103](https://pypost.atlassian.net/browse/PYPOST-103) | Add tests for `JsonHighlighter`. | `PYPOST-11/40-tech-debt.md` |

### PYPOST-12 (9 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-104](https://pypost.atlassian.net/browse/PYPOST-104) | No Tests**: Creation of automated tests was skipped by user request. Auto-indentation and paste l... | `PYPOST-12/40-tech-debt.md` |
| [PYPOST-105](https://pypost.atlassian.net/browse/PYPOST-105) | Simplified Unindent Logic**: Unindentation works only if the line contains *only* the closing bra... | `PYPOST-12/40-tech-debt.md` |
| [PYPOST-106](https://pypost.atlassian.net/browse/PYPOST-106) | Manual Font Propagation**: In `MainWindow.apply_settings`, the font is manually applied to indivi... | `PYPOST-12/40-tech-debt.md` |
| [PYPOST-107](https://pypost.atlassian.net/browse/PYPOST-107) | Manual Font Propagation**: (See above). This violates DRY principle and complicates UI maintenance. | `PYPOST-12/40-tech-debt.md` |
| [PYPOST-108](https://pypost.atlassian.net/browse/PYPOST-108) | CodeEditor tests** ( | `PYPOST-12/40-tech-debt.md` |
| [PYPOST-109](https://pypost.atlassian.net/browse/PYPOST-109) | JSON Parsing on Paste**: When pasting *very* large text, attempting to parse it as JSON might cau... | `PYPOST-12/40-tech-debt.md` |
| [PYPOST-110](https://pypost.atlassian.net/browse/PYPOST-110) | Create tests for `CodeEditor`. | `PYPOST-12/40-tech-debt.md` |
| [PYPOST-111](https://pypost.atlassian.net/browse/PYPOST-111) | Implement asynchronous JSON check on paste for large data volumes (optional). | `PYPOST-12/40-tech-debt.md` |
| [PYPOST-112](https://pypost.atlassian.net/browse/PYPOST-112) | Investigate reasons for font inheritance issues and refactor `apply_settings` for a cleaner solut... | `PYPOST-12/40-tech-debt.md` |

### PYPOST-13 (10 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-113](https://pypost.atlassian.net/browse/PYPOST-113) | Variable regex scope** ( | `PYPOST-13/40-tech-debt.md` |
| [PYPOST-114](https://pypost.atlassian.net/browse/PYPOST-114) | Default tooltip styling** ( | `PYPOST-13/40-tech-debt.md` |
| [PYPOST-115](https://pypost.atlassian.net/browse/PYPOST-115) | One-level tooltip vars** ( | `PYPOST-13/40-tech-debt.md` |
| [PYPOST-116](https://pypost.atlassian.net/browse/PYPOST-116) | Direct variable injection** ( | `PYPOST-13/40-tech-debt.md` |
| [PYPOST-117](https://pypost.atlassian.net/browse/PYPOST-117) | VariableHoverHelper tests** ( | `PYPOST-13/40-tech-debt.md` |
| [PYPOST-118](https://pypost.atlassian.net/browse/PYPOST-118) | Tooltip UI** ( | `PYPOST-13/40-tech-debt.md` |
| [PYPOST-119](https://pypost.atlassian.net/browse/PYPOST-119) | Mouse move + regex** ( | `PYPOST-13/40-tech-debt.md` |
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

### PYPOST-29 (16 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-249](https://pypost.atlassian.net/browse/PYPOST-249) | StateManager Dependency**: `StateManager` is currently just a thin wrapper around `ConfigManager`... | `PYPOST-29/40-tech-debt.md` |
| [PYPOST-250](https://pypost.atlassian.net/browse/PYPOST-250) | Mixin Type Hinting**: `VariableHoverMixin` uses `self` as `QWidget` but inherits from `object` (i... | `PYPOST-29/40-tech-debt.md` |
| [PYPOST-251](https://pypost.atlassian.net/browse/PYPOST-251) | Automated Tests**: No new automated tests were added because the project currently lacks a setup ... | `PYPOST-29/40-tech-debt.md` |
| [PYPOST-252](https://pypost.atlassian.net/browse/PYPOST-252) | Implement `pytest` infrastructure and add tests for `RequestManager` and `StateManager`. | `PYPOST-29/40-tech-debt.md` |
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

### PYPOST-42 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-385](https://pypost.atlassian.net/browse/PYPOST-385) | Auto-switch metric untested** ( | `PYPOST-42/60-tech-debt.md` |

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

### PYPOST-54 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-55](https://pypost.atlassian.net/browse/PYPOST-55) | Hardcoded UI strings in env widgets \| Low \| | `PYPOST-54/60-tech-debt.md` |

### PYPOST-57 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-580](https://pypost.atlassian.net/browse/PYPOST-580) | Unlinked PYPOST-52 INFO item \| **Resolved | `PYPOST-57/60-tech-debt.md` |
| [PYPOST-581](https://pypost.atlassian.net/browse/PYPOST-581) | Medium \| Bulk-fix truncated Jira summaries for all 480 linked debt issues \| | `PYPOST-57/60-tech-debt.md` |
| [PYPOST-582](https://pypost.atlassian.net/browse/PYPOST-582) | Low \| Standardize debt bullet format (PYPOST-53 table style) across legacy files \| | `PYPOST-57/60-tech-debt.md` |

### PYPOST-67 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-68](https://pypost.atlassian.net/browse/PYPOST-68) | TD-3 \| MEDIUM \| `EnvPresenter` exposes internal widgets via properties \| | `PYPOST-67/60-tech-debt.md` |

### PYPOST-73 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-579](https://pypost.atlassian.net/browse/PYPOST-579) | \| Low \| [PYPOST-75](https://pypost.atlassian.net/browse/PYPOST-75) \| `NullMetrics` no-op to repla... | `PYPOST-73/60-tech-debt.md` |

### PYPOST-115 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-13](https://pypost.atlassian.net/browse/PYPOST-13) | Multi-level chains** ( | `PYPOST-115/60-tech-debt.md` |

### PYPOST-122 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-123](https://pypost.atlassian.net/browse/PYPOST-123) | Technical debt follow-up | `PYPOST-122/60-tech-debt.md` |
| [PYPOST-124](https://pypost.atlassian.net/browse/PYPOST-124) | Technical debt follow-up | `PYPOST-122/60-tech-debt.md` |

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

### PYPOST-310 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-312](https://pypost.atlassian.net/browse/PYPOST-312) | Pytest exit code 5 policy** — existing debt | `PYPOST-310/60-tech-debt.md` |
| [PYPOST-559](https://pypost.atlassian.net/browse/PYPOST-559) | Full install smoke in CI** — existing debt | `PYPOST-310/60-tech-debt.md` |

### PYPOST-312 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-33](https://pypost.atlassian.net/browse/PYPOST-33) | question from | `PYPOST-312/60-tech-debt.md` |

### PYPOST-316 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-320](https://pypost.atlassian.net/browse/PYPOST-320) | Add GUI-level tests for save and save-as behavior | `PYPOST-316/60-tech-debt.md` |
| [PYPOST-323](https://pypost.atlassian.net/browse/PYPOST-323) | Repository-wide lint debt | `PYPOST-316/60-tech-debt.md` |

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

### PYPOST-368 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-560](https://pypost.atlassian.net/browse/PYPOST-560) | SSE servers | `PYPOST-368/60-tech-debt.md` |

### PYPOST-370 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-563](https://pypost.atlassian.net/browse/PYPOST-563) | Technical debt follow-up | `PYPOST-370/60-tech-debt.md` |
| [PYPOST-564](https://pypost.atlassian.net/browse/PYPOST-564) | Technical debt follow-up | `PYPOST-370/60-tech-debt.md` |

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

### PYPOST-410 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-412](https://pypost.atlassian.net/browse/PYPOST-412) | \|----------\|------\|-------\| | `PYPOST-410/60-tech-debt.md` |

### PYPOST-425 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-426](https://pypost.atlassian.net/browse/PYPOST-426) | Technical debt follow-up | `PYPOST-425/60-tech-debt.md` |

### PYPOST-426 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-427](https://pypost.atlassian.net/browse/PYPOST-427) | `main.py` ConfigManager ordering** ( | `PYPOST-426/60-tech-debt.md` |

### PYPOST-432 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-565](https://pypost.atlassian.net/browse/PYPOST-565) | Debt item (line 28) | `PYPOST-432/60-tech-debt.md` |

### PYPOST-435 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-496](https://pypost.atlassian.net/browse/PYPOST-496) | Technical debt follow-up | `PYPOST-435/60-tech-debt.md` |
| [PYPOST-498](https://pypost.atlassian.net/browse/PYPOST-498) | Technical debt follow-up | `PYPOST-435/60-tech-debt.md` |

### PYPOST-443 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-558](https://pypost.atlassian.net/browse/PYPOST-558) | Technical debt follow-up | `PYPOST-443/60-tech-debt.md` |

### PYPOST-446 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-462](https://pypost.atlassian.net/browse/PYPOST-462) | history panel display. Jira | `PYPOST-446/60-tech-debt.md` |
| [PYPOST-464](https://pypost.atlassian.net/browse/PYPOST-464) | when `hidden_keys` is empty. **Closed | `PYPOST-446/60-tech-debt.md` |

### PYPOST-447 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-481](https://pypost.atlassian.net/browse/PYPOST-481) | user-facing application settings. | `PYPOST-447/60-tech-debt.md` |
| [PYPOST-484](https://pypost.atlassian.net/browse/PYPOST-484) | Suggested improvement: represent payload via typed model to centralize validation rules. | `PYPOST-447/60-tech-debt.md` |
| [PYPOST-486](https://pypost.atlassian.net/browse/PYPOST-486) | cause visible UI pauses during load/save actions. | `PYPOST-447/60-tech-debt.md` |

### PYPOST-448 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-448](https://pypost.atlassian.net/browse/PYPOST-448) | All tickets: type **Debt**, linked to | `PYPOST-448/60-tech-debt.md` |
| [PYPOST-490](https://pypost.atlassian.net/browse/PYPOST-490) | tests but not wired in one flow. | `PYPOST-448/60-tech-debt.md` |

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

### PYPOST-457 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-461](https://pypost.atlassian.net/browse/PYPOST-461) | Deeper expression edge cases | `PYPOST-457/60-tech-debt.md` |

### PYPOST-460 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-536](https://pypost.atlassian.net/browse/PYPOST-536) | Technical debt follow-up | `PYPOST-460/60-tech-debt.md` |

### PYPOST-464 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-463](https://pypost.atlassian.net/browse/PYPOST-463) | Refactor `RequestService` history-recording block | `PYPOST-464/60-tech-debt.md` |
| [PYPOST-465](https://pypost.atlassian.net/browse/PYPOST-465) | Full-project regression in CI | `PYPOST-464/60-tech-debt.md` |

### PYPOST-467 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-493](https://pypost.atlassian.net/browse/PYPOST-493) | Technical debt follow-up | `PYPOST-467/60-tech-debt.md` |

### PYPOST-470 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-472](https://pypost.atlassian.net/browse/PYPOST-472) | \| Medium \| New (if product wants Jinja2 parity) \| Evaluate switching `validate_variable_name` fro... | `PYPOST-470/60-tech-debt.md` |
| [PYPOST-479](https://pypost.atlassian.net/browse/PYPOST-479) | \| Low \| [PYPOST-472](https://pypost.atlassian.net/browse/PYPOST-472) \| Deduplicate error message ... | `PYPOST-470/60-tech-debt.md` |
| [PYPOST-480](https://pypost.atlassian.net/browse/PYPOST-480) | `validation_failure_reason` contract. [PYPOST-475](https://pypost.atlassian.net/browse/PYPOST-475) | `PYPOST-470/60-tech-debt.md` |

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

### PYPOST-511 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-513](https://pypost.atlassian.net/browse/PYPOST-513) | Technical debt follow-up | `PYPOST-511/60-tech-debt.md` |
| [PYPOST-516](https://pypost.atlassian.net/browse/PYPOST-516) | Extend RequestWidget integration test to assert body gutter chevrons and fold toggle. | `PYPOST-511/60-tech-debt.md` |
| [PYPOST-517](https://pypost.atlassian.net/browse/PYPOST-517) | Add unit tests for fold remapping after document edits while sections are collapsed. | `PYPOST-511/60-tech-debt.md` |
| [PYPOST-518](https://pypost.atlassian.net/browse/PYPOST-518) | Implement YAML and XML structure scanners and enable folding when those formats are active. | `PYPOST-511/60-tech-debt.md` |

### PYPOST-512 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-519](https://pypost.atlassian.net/browse/PYPOST-519) | Implement YAML and XML body validators when those formats are active via format selector. | `PYPOST-512/60-tech-debt.md` |
| [PYPOST-520](https://pypost.atlassian.net/browse/PYPOST-520) | Add unit test for validation error line alignment with folded/hidden blocks. | `PYPOST-512/60-tech-debt.md` |
| [PYPOST-521](https://pypost.atlassian.net/browse/PYPOST-521) | Extend RequestWidget integration test to assert body validation banner on invalid JSON. | `PYPOST-512/60-tech-debt.md` |

### PYPOST-514 (4 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-515](https://pypost.atlassian.net/browse/PYPOST-515) | behavior; no PYPOST-514 changes required until that task ships. | `PYPOST-514/60-tech-debt.md` |
| [PYPOST-522](https://pypost.atlassian.net/browse/PYPOST-522) | intentionally keep editor YAML; document or offer opt-in wire-form export if users need | `PYPOST-514/60-tech-debt.md` |
| [PYPOST-523](https://pypost.atlassian.net/browse/PYPOST-523) | `ErrorCategory.BODY` message formatting. | `PYPOST-514/60-tech-debt.md` |
| [PYPOST-524](https://pypost.atlassian.net/browse/PYPOST-524) | body content) if failure rates become useful for support. | `PYPOST-514/60-tech-debt.md` |

### PYPOST-530 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-540](https://pypost.atlassian.net/browse/PYPOST-540) | TD-10 \| Low \| Optional `--config-dir` for settings alongside `--data-dir` \| Restore workflows tha... | `PYPOST-530/60-tech-debt.md` |

### PYPOST-531 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-543](https://pypost.atlassian.net/browse/PYPOST-543) | TD-11 \| Low \| Vault backend migration integration test \| Stage 4 rollout confidence when PYPOST-5... | `PYPOST-531/60-tech-debt.md` |

### PYPOST-533 (2 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-541](https://pypost.atlassian.net/browse/PYPOST-541) | TD-11 \| Medium \| Implement v2 decrypt handlers (fernet + aes-gcm) \| Parsing scaffold exists; code... | `PYPOST-533/60-tech-debt.md` |
| [PYPOST-542](https://pypost.atlassian.net/browse/PYPOST-542) | TD-12 \| Low \| v1 → v2 re-encrypt migration path \| After v2 decrypt lands, optional CLI or service... | `PYPOST-533/60-tech-debt.md` |

### PYPOST-535 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-544](https://pypost.atlassian.net/browse/PYPOST-544) | TD-1 \| Low \| Surface `reencrypt_stats` in Settings re-encrypt dialog \| Jira | `PYPOST-535/60-tech-debt.md` |

### PYPOST-539 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-547](https://pypost.atlassian.net/browse/PYPOST-547) | Technical debt follow-up | `PYPOST-539/60-tech-debt.md` |

### PYPOST-544 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-545](https://pypost.atlassian.net/browse/PYPOST-545) | TD-1 \| Low \| Dry-run projected reuse counts in CLI and Settings \| Jira | `PYPOST-544/60-tech-debt.md` |

### PYPOST-549 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-550](https://pypost.atlassian.net/browse/PYPOST-550) | Technical debt follow-up | `PYPOST-549/60-tech-debt.md` |
| [PYPOST-551](https://pypost.atlassian.net/browse/PYPOST-551) | Technical debt follow-up | `PYPOST-549/60-tech-debt.md` |
| [PYPOST-552](https://pypost.atlassian.net/browse/PYPOST-552) | TD-2 \| Low \| User-facing `doc/mcp_integration.md` still SSE URLs \| | `PYPOST-549/60-tech-debt.md` |

### PYPOST-550 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-575](https://pypost.atlassian.net/browse/PYPOST-575) | EnvPresenter supplier test \| Add `test_registers_variable_supplier_on_init` and `test_supplier_re... | `PYPOST-550/60-tech-debt.md` |
| [PYPOST-576](https://pypost.atlassian.net/browse/PYPOST-576) | Manager supplier propagation \| Add unit test in `tests/test_mcp_server.py` (or existing manager t... | `PYPOST-550/60-tech-debt.md` |
| [PYPOST-577](https://pypost.atlassian.net/browse/PYPOST-577) | Shared env snapshot \| Optional refactor: extract env-variable cache from `EnvPresenter`/`TabsPres... | `PYPOST-550/60-tech-debt.md` |

### PYPOST-551 (1 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-578](https://pypost.atlassian.net/browse/PYPOST-578) | TD-4 \| Low \| User-facing `doc/mcp_integration.md` still describes SSE URL \| | `PYPOST-551/60-tech-debt.md` |

### PYPOST-571 (3 items)

| Jira | Summary (from artifact) | File |
| --- | --- | --- |
| [PYPOST-572](https://pypost.atlassian.net/browse/PYPOST-572) | Implement allowlist YAML + `verify_test_log_guardrails.py` + CI step \| M \| | `PYPOST-571/60-tech-debt.md` |
| [PYPOST-573](https://pypost.atlassian.net/browse/PYPOST-573) | Duration budget audit script + CI annotations \| M \| | `PYPOST-571/60-tech-debt.md` |
| [PYPOST-574](https://pypost.atlassian.net/browse/PYPOST-574) | `caplog` contract in `do-testing.md` + optional retrofits \| S \| | `PYPOST-571/60-tech-debt.md` |

## Debt Files Without Jira Links

These files document debt but contain no `PYPOST-*` Jira links yet (303 files):

- `PYPOST-106/60-tech-debt.md`
- `PYPOST-113/60-tech-debt.md`
- `PYPOST-114/60-tech-debt.md`
- `PYPOST-123/60-tech-debt.md`
- `PYPOST-127/60-tech-debt.md`
- `PYPOST-129/60-tech-debt.md`
- `PYPOST-134/60-tech-debt.md`
- `PYPOST-135/60-tech-debt.md`
- `PYPOST-136/60-tech-debt.md`
- `PYPOST-137/60-tech-debt.md`
- `PYPOST-138/60-tech-debt.md`
- `PYPOST-140/60-tech-debt.md`
- `PYPOST-141/60-tech-debt.md`
- `PYPOST-143/60-tech-debt.md`
- `PYPOST-144/60-tech-debt.md`
- `PYPOST-145/60-tech-debt.md`
- `PYPOST-147/60-tech-debt.md`
- `PYPOST-148/60-tech-debt.md`
- `PYPOST-150/60-tech-debt.md`
- `PYPOST-152/60-tech-debt.md`
- `PYPOST-153/60-tech-debt.md`
- `PYPOST-154/60-tech-debt.md`
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
- `PYPOST-176/60-tech-debt.md`
- `PYPOST-177/60-tech-debt.md`
- `PYPOST-178/60-tech-debt.md`
- `PYPOST-179/60-tech-debt.md`
- … and 263 more

## Remediation Notes

- Markdown/Jira hygiene: see [tech-debt-diff.md](../tech-debt-diff.md).
- Sprint 502 executes linked backlog items (UI polish & cleanup).
- Re-run this script when new `60-tech-debt.md` / `60-review.md` artifacts land.
