# PYPOST-1052: Widen McpSecretsPolicy discovery for wrapped mcp.request forms

## Research

### 1. Context and Problem Baseline

In PyPost, HTTP requests can be exposed as Model Context Protocol (MCP) tools for AI agents. When a request template utilizes dynamic agent-supplied parameters, these inputs are referenced using the `mcp.request.<var>` namespace (for example, `{{ mcp.request.board_id }}` or `{{ to_int(mcp.request.board_id) }}`).

In curated example collections (such as `examples/collections/jira_mcp.json`), request definitions declare explicit parameter metadata via `mcp_params`. The helper `resolve_mcp_param_specs` merges discovered variables with explicit `mcp_params`, ensuring curated collections publish accurate tool contracts.

However, user-authored collections often omit manual `mcp_params` metadata and rely entirely on automated parameter discovery from request templates. The discovery engine is implemented in `pypost/core/mcp_secrets_policy.py` via `McpSecretsPolicy.extract_mcp_request_variables`.

### 2. Existing Discovery Implementation

In `pypost/core/mcp_secrets_policy.py`:
```python
_MCP_REQUEST_VAR_PATTERN = re.compile(
    r"\{\{\s*mcp\.request\.([a-zA-Z0-9_]+)\s*\}\}"
)
```

The template field traversal is performed by `_iter_request_template_fields`:
```python
def _iter_request_template_fields(request: RequestData) -> list[str]:
    fields: list[str] = [request.url, request.body]
    fields.extend(request.headers.values())
    fields.extend(request.params.values())
    return [field for field in fields if field]
```

`McpSecretsPolicy.extract_mcp_request_variables(request: RequestData) -> Set[str]` iterates over these fields and applies `_MCP_REQUEST_VAR_PATTERN.findall(content)`.

**The Defect:**
Because the regular expression demands that `mcp.request.<name>` be the immediate and sole token inside `{{ ... }}`, any expression wrapping the variable in a transformation or casting function is ignored:
- `{{ to_int(mcp.request.board_id) }}` ❌ (fails to match)
- `{{ base64(mcp.request.payload) }}` ❌ (fails to match)
- `{{ upper(mcp.request.username) }}` ❌ (fails to match)
- `{{ urlencode(mcp.request.query) }}` ❌ (fails to match)
- `{{ mcp.request.prefix ~ "_suffix" }}` ❌ (fails to match)
- `{{ mcp.request.var1 + mcp.request.var2 }}` ❌ (fails to match)

As a result, automated discovery returns an empty set or omits the wrapped variable, leading to:
1. Tool contracts in `MCPServerImpl.list_tools` lacking required input properties.
2. Incomplete preview contracts in `pypost/core/mcp_tool_contract.py`.
3. The UI Request Editor (`RequestWidget._sync_mcp_params_from_template`) failing to auto-populate the parameter metadata table when users write function-wrapped template expressions.

### 3. Prior Art and Test Fixture Scan (PYPOST-1028 TD-2)

During PYPOST-1028 contract testing in `tests/test_example_fixtures.py`, a broader regex was introduced specifically to catch wrapped forms:
```python
# Broader than McpSecretsPolicy: also matches to_int(mcp.request.*), etc.
_MCP_REQUEST_NAME_PATTERN = re.compile(r"mcp\.request\.([a-zA-Z0-9_]+)")
```
Technical debt analysis in `ai-tasks/PYPOST-1028/60-tech-debt.md` (TD-2) noted:
> "Widen `McpSecretsPolicy.extract_mcp_request_variables` (and any callers that rely on discovery alone) to recognize function-wrapped forms such as `{{ to_int(mcp.request.board_id) }}`, aligning production discovery with the broader fixture-contract scan."

### 4. Consumer Inventory

The callers of `McpSecretsPolicy.extract_mcp_request_variables` across the codebase are:

1. **`pypost/core/mcp_secrets_policy.py`**:
   - `McpSecretsPolicy.filter_agent_param_specs`:
     Ensures that discovered `mcp_vars` are not stripped when calculating `forbidden = (set(env_names) | set(hidden_keys)) - mcp_vars`.
   - `McpSecretsPolicy.build_input_schema_for_request`:
     Directly extracts `mcp_vars` to construct schema properties and required fields.

2. **`pypost/core/mcp_tool_contract.py`**:
   - `collect_policy_exclusions`:
     Uses `extract_mcp_request_variables` to differentiate between environment-only secrets and agent input variables.
   - `build_mcp_tool_contract_preview`:
     Extracts discovered variables to supply them to `resolve_mcp_param_specs(request, discovered)`.

3. **`pypost/core/mcp_server_impl.py`**:
   - `MCPServerImpl._generate_schema`:
     Uses `extract_mcp_request_variables(req)` to generate runtime `list_tools` JSON Schema definitions.

4. **`pypost/ui/widgets/request_editor.py`**:
   - `RequestWidget._sync_mcp_params_from_template`:
     Scans current request fields with `extract_mcp_request_variables(req)` and synchronizes `mcp_params_table` whenever URL, body, headers, or query parameters change.
   - `RequestWidget._on_mcp_preview_source_changed`:
     Triggers sync and re-renders the MCP contract preview.

5. **`tests/test_example_fixtures.py`**:
   - `_extract_mcp_request_names`: Test helper currently using `_MCP_REQUEST_NAME_PATTERN` to validate fixture parameter declarations.

---

## Implementation Plan

### High-Level Sequencing

1. **Step 3: Automated Failing Repro Tests**
   - Write dedicated unit tests in `tests/test_mcp_secrets_policy.py` asserting extraction of function-wrapped agent variables (`to_int`, `base64`, `urlencode`, `upper`, nested/concatenated expressions) across URL, headers, query params, and body.
   - Add failing test cases in `tests/test_mcp_tool_contract.py` and `tests/test_request_editor_mcp_params.py` demonstrating schema generation and UI parameter synchronization for function-wrapped agent inputs without explicit `mcp_params`.
   - Run tests to confirm red status under the current restrictive pattern.

2. **Step 4: Development**
   - Update `_MCP_REQUEST_VAR_PATTERN` in `pypost/core/mcp_secrets_policy.py` to `re.compile(r"mcp\.request\.([a-zA-Z0-9_]+)")`.
   - Update docstring in `McpSecretsPolicy.extract_mcp_request_variables` to reflect that any occurrence of `mcp.request.<var>` (bare or wrapped) is extracted.
   - Optionally align / consolidate `_extract_mcp_request_names` in `tests/test_example_fixtures.py` with `McpSecretsPolicy.extract_mcp_request_variables`.
   - Re-run all unit, contract, and fixture test suites to verify green status.

3. **Step 5: Code Cleanup**
   - Verify code formatting, typing annotations, docstrings, and remove any leftover debugging code.
   - Generate `ai-tasks/PYPOST-1052/40-code-cleanup.md`.

4. **Step 6: Observability**
   - Verify that offline parameter discovery and regex extraction do not require new telemetry or logging counters.
   - Generate `ai-tasks/PYPOST-1052/50-observability.md`.

5. **Step 7: Technical Debt Analysis**
   - Document the resolution of PYPOST-1028 TD-2.
   - Generate `ai-tasks/PYPOST-1052/60-tech-debt.md`.

6. **Step 8: Developer Documentation**
   - Update `doc/dev/mcp_secrets_policy.md` and related documentation to describe widened discovery for function-wrapped expressions.
   - Generate `ai-tasks/PYPOST-1052/70-dev-docs.md`.

### Mandatory — Failing Repro (Step 3 Design)

- **Test Locations:**
  - `tests/test_mcp_secrets_policy.py`
  - `tests/test_mcp_tool_contract.py`
  - `tests/test_request_editor_mcp_params.py`
- **What it Asserts:**
  1. `McpSecretsPolicy.extract_mcp_request_variables(request)` discovers variables wrapped inside template helper functions:
     - `url = "http://api.example/boards/{{ to_int(mcp.request.board_id) }}/sprints/{{ to_int(mcp.request.sprint_id) }}"` -> `{"board_id", "sprint_id"}`
     - `headers = {"Authorization": "Basic {{ base64(mcp.request.auth_token) }}", "X-Custom": "{{ upper(mcp.request.custom_header) }}"}` -> `{"auth_token", "custom_header"}`
     - `params = {"query": "{{ urlencode(mcp.request.search_term) }}", "filter": "{{ mcp.request.filter_type }}"}` -> `{"search_term", "filter_type"}`
     - `body = '{"id": {{ to_int(mcp.request.item_id) }}, "data": "{{ base64(mcp.request.raw_data) }}"}'` -> `{"item_id", "raw_data"}`
  2. `build_mcp_tool_contract_preview(request)` generates JSON Schema properties for wrapped variables when `mcp_params` is empty.
  3. `RequestWidget._sync_mcp_params_from_template()` populates `mcp_params_table` with wrapped variables from URL and body inputs.
- **How Failure is Forced:**
  Under the current code, `_MCP_REQUEST_VAR_PATTERN` requires `r"\{\{\s*mcp\.request\.([a-zA-Z0-9_]+)\s*\}\}"`. For wrapped expressions, `extract_mcp_request_variables` returns `set()` or omits the wrapped keys, causing the assertions (`assertIn("board_id", params)`, `assertEqual(discovered, {"board_id", "sprint_id"})`) to immediately fail with `AssertionError`.
- **Sequencing:**
  Write repro tests in Step 3 → execute to confirm failure → apply production fix in Step 4 → execute to confirm green.

---

## Architecture

### System Architecture & Data Flow Diagram

```mermaid
flowchart TD
    subgraph Request Template Fields
        URL["request.url (e.g. /boards/{{ to_int(mcp.request.board_id) }})"]
        Headers["request.headers (e.g. Basic {{ base64(mcp.request.auth) }})"]
        Params["request.params (e.g. q={{ urlencode(mcp.request.query) }})"]
        Body["request.body (e.g. {\"id\": {{ to_int(mcp.request.item_id) }}})"]
    end

    subgraph Discovery Engine
        Iter["_iter_request_template_fields(request)"]
        Regex["_MCP_REQUEST_VAR_PATTERN\nr'mcp\\.request\\.([a-zA-Z0-9_]+)'"]
        Extract["McpSecretsPolicy.extract_mcp_request_variables(request)\nReturns: Set[str] (e.g. {'board_id', 'auth', 'query', 'item_id'})"]
    end

    subgraph Policy & Contracts
        Resolve["resolve_mcp_param_specs(req, discovered)"]
        Filter["McpSecretsPolicy.filter_agent_param_specs\n(Excludes environment secrets & hidden keys)"]
        BuildSchema["build_tool_input_schema(specs)"]
    end

    subgraph Consumers
        Server["MCPServerImpl.list_tools\n(Publishes tool inputSchema to AI Agents)"]
        Preview["build_mcp_tool_contract_preview\n(Renders schema preview in UI)"]
        UIEditor["RequestWidget._sync_mcp_params_from_template\n(Syncs MCP Parameters table in UI)"]
        Exclusions["collect_policy_exclusions\n(Reports excluded environment keys)"]
    end

    URL --> Iter
    Headers --> Iter
    Params --> Iter
    Body --> Iter

    Iter --> Regex --> Extract

    Extract --> Resolve
    Extract --> Filter
    Extract --> Exclusions

    Resolve --> Filter --> BuildSchema
    BuildSchema --> Server
    BuildSchema --> Preview
    Extract --> UIEditor
```

### Components and Module Responsibilities

| Component / File | Responsibility | Planned Changes |
| --- | --- | --- |
| `pypost.core.mcp_secrets_policy` (`pypost/core/mcp_secrets_policy.py`) | Core policy defining agent-visible input schema extraction and secret isolation. | Update `_MCP_REQUEST_VAR_PATTERN` from `r"\{\{\s*mcp\.request\.([a-zA-Z0-9_]+)\s*\}\}"` to `r"mcp\.request\.([a-zA-Z0-9_]+)"`. Update docstring. |
| `pypost.core.mcp_tool_contract` (`pypost/core/mcp_tool_contract.py`) | Helper functions for MCP tool naming, contract preview, and parameter specification resolution. | No code changes needed; automatically benefits from widened `extract_mcp_request_variables`. |
| `pypost.core.mcp_server_impl` (`pypost/core/mcp_server_impl.py`) | MCP server implementation serving `list_tools` and `call_tool` handlers over network transports. | No code changes needed; `_generate_schema` automatically discovers wrapped variables. |
| `pypost.ui.widgets.request_editor` (`pypost/ui/widgets/request_editor.py`) | UI widget for editing request properties and previewing/editing MCP tool configurations. | No code changes needed; `_sync_mcp_params_from_template` automatically populates wrapped variables. |
| `tests/test_mcp_secrets_policy.py` | Unit tests for secrets policy and request variable extraction. | Add comprehensive test cases for function-wrapped, multi-variable, and mixed placeholders. |
| `tests/test_mcp_tool_contract.py` | Unit tests for MCP tool contract preview and schema construction. | Add test cases verifying schema generation for requests with wrapped variables without `mcp_params`. |
| `tests/test_request_editor_mcp_params.py` | UI integration tests for request editor MCP parameters table. | Add test cases verifying automatic synchronization for wrapped variables. |
| `doc/dev/mcp_secrets_policy.md` | Developer documentation for secrets policy and parameter discovery. | Document the widened regular expression and wrapped expression discovery support. |

### Interfaces and API Design

The public signature of `McpSecretsPolicy.extract_mcp_request_variables` remains completely unchanged:

```python
class McpSecretsPolicy:
    @staticmethod
    def extract_mcp_request_variables(request: RequestData) -> Set[str]:
        """Placeholders matching ``mcp.request.VAR`` (bare or wrapped) become agent tool inputs."""
        found: set[str] = set()
        for content in _iter_request_template_fields(request):
            found.update(_MCP_REQUEST_VAR_PATTERN.findall(content))
        return found
```

**Pattern Specification:**
- Old: `re.compile(r"\{\{\s*mcp\.request\.([a-zA-Z0-9_]+)\s*\}\}")`
- New: `re.compile(r"mcp\.request\.([a-zA-Z0-9_]+)")`

**Behavioral Characteristics:**
- **Bare variable:** `{{ mcp.request.id }}` -> extracts `"id"`.
- **Function-wrapped variable:** `{{ to_int(mcp.request.board_id) }}` -> extracts `"board_id"`.
- **Nested function call:** `{{ base64(urlencode(mcp.request.data)) }}` -> extracts `"data"`.
- **Multiple variables in one expression:** `{{ mcp.request.first ~ mcp.request.second }}` -> extracts `"first"` and `"second"`.
- **Multiple placeholders across fields:** Discovered across URL, all header values, all query parameter values, and body text.
- **Identifier syntax:** `[a-zA-Z0-9_]+` matches standard Python/Jinja identifier characters.

### Secret Isolation and Security Boundaries

Widening the regular expression only matches the `mcp.request.` namespace prefix:
1. Environment variables (such as `{{ api_key }}` or `{{ base_url }}`) do not contain the `mcp.request.` prefix and are never extracted by `extract_mcp_request_variables`.
2. `extract_environment_variable_names` relies on Jinja AST parsing (`find_undeclared_variables`), where `mcp` is explicitly excluded from environment variables (`if var != "mcp"`).
3. `filter_agent_param_specs` calculates `forbidden = (set(env_names) | set(hidden_keys)) - mcp_vars`. Any environment variable or hidden key without an `mcp.request.` counterpart remains strictly excluded from the agent-visible `inputSchema`.
4. Therefore, secret isolation and policy exclusion boundaries are strictly preserved.

### Definition of Done Traceability Matrix

| Requirement / DoD Item (from `10-requirements.md`) | Architectural Component | Verification / Test Strategy |
| --- | --- | --- |
| Automated discovery recognizes agent variables wrapped in functions/expressions across all fields (URL, headers, query params, body). | `pypost/core/mcp_secrets_policy.py` (`_MCP_REQUEST_VAR_PATTERN`) | `tests/test_mcp_secrets_policy.py`: `test_extract_mcp_request_variables_discovers_function_wrapped_placeholders` |
| Bare (unwrapped) agent variable references continue to be discovered accurately without regressions. | `pypost/core/mcp_secrets_policy.py` (`extract_mcp_request_variables`) | `tests/test_mcp_secrets_policy.py`: `test_extract_mcp_request_variables_from_request_fields` |
| Multiple agent variables occurring within the same request field or expression are all discovered. | `pypost/core/mcp_secrets_policy.py` (`_MCP_REQUEST_VAR_PATTERN.findall`) | `tests/test_mcp_secrets_policy.py`: `test_extract_multiple_mcp_request_variables_in_single_field` |
| Requests exposed as MCP tools publish complete input schemas including bare and wrapped agent parameters. | `pypost/core/mcp_server_impl.py` & `pypost/core/mcp_tool_contract.py` | `tests/test_mcp_tool_contract.py`: `test_preview_generates_schema_for_wrapped_variables_without_mcp_params` |
| UI request editor synchronization automatically populates parameter tables for wrapped agent variables. | `pypost/ui/widgets/request_editor.py` (`_sync_mcp_params_from_template`) | `tests/test_request_editor_mcp_params.py`: `test_wrapped_placeholder_populates_mcp_params_table` |
| Environment variables and sensitive secrets remain strictly protected and not classified as agent inputs. | `pypost/core/mcp_secrets_policy.py` (`filter_agent_param_specs`) | `tests/test_mcp_secrets_policy.py`: `test_filter_agent_param_specs_removes_hidden_env_only_params` |
| Existing capability, auth, environment resolution, and placeholder handling remain intact. | Entire `pypost.core` test suite | Full pytest execution on `tests/test_mcp_*.py` and `tests/test_example_fixtures.py` |
| All verification is deterministic and supported by automated tests with standard timeouts. | Pytest test suite with `pytestmark = pytest.mark.timeout(30)` | Offline deterministic test execution |
| Developer documentation updated to describe supported agent parameter discovery behavior. | `doc/dev/mcp_secrets_policy.md` | Doc review in Step 8 |

---

## Q&A

**Q: Why not parse the Jinja AST to extract `mcp.request.<var>` instead of using a regular expression?**
**A:** Jinja's `meta.find_undeclared_variables(ast)` only discovers top-level root identifiers (it returns `"mcp"`, not the attribute path `"request.board_id"`). To extract attribute accesses from the AST, one would need to implement a custom AST visitor walking `ast.Getattr` nodes, which is significantly more complex, slower, and prone to AST edge cases. The regular expression `r"mcp\.request\.([a-zA-Z0-9_]+)"` is lightweight, deterministic, robust, and already proven in `tests/test_example_fixtures.py`.

**Q: Could matching `mcp.request.<name>` outside `{{ ... }}` cause false positives if the text `mcp.request.foo` appears in a raw URL or body?**
**A:** In HTTP templates, `mcp.request.` is a reserved namespace token specifically intended to designate agent inputs. PyPost templates do not use `mcp.request.` for any other purpose. Even if a user mentions `mcp.request.foo` in a string, declaring it as an available tool parameter is harmless and consistent with user intent.

**Q: Does widening discovery break existing explicit `mcp_params` configurations?**
**A:** No. `resolve_mcp_param_specs(req, discovered)` preserves existing explicit metadata from `req.mcp_params`. If a parameter is explicitly configured with custom types (such as `integer_or_string`) or custom descriptions, those explicit specs take precedence over default discovered specs.

**Q: Will environment variables with the same name as a wrapped agent variable collide?**
**A:** No. In `filter_agent_param_specs`, `forbidden = (set(env_names) | set(hidden_keys)) - mcp_vars`. Because `mcp_vars` contains the discovered agent variable, it is explicitly preserved as an agent input. Environment variables with different names remain excluded from the agent schema.
