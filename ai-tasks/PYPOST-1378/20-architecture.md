# PYPOST-1378: [PYPOST-1312] Permanent MCP output masking for hidden response fields

Step 2 artifact for PYPOST-1378 (MASK-2). Translates approved requirements from
[`10-requirements.md`](10-requirements.md) and decomposition guidelines from
[`../PYPOST-1312/decomposition-notes.md`](../PYPOST-1312/decomposition-notes.md),
[`../PYPOST-1376/20-architecture.md`](../PYPOST-1376/20-architecture.md), and
[`../PYPOST-1377/20-architecture.md`](../PYPOST-1377/20-architecture.md) into a
concrete architectural design and implementation specification for permanent,
fail-closed MCP tool output masking.

---

## Research

### 1. MCP Tool Invocation and Result Formatting Flow

1. **Tool Invocation in `MCPServerImpl` ([`pypost/core/mcp_server_impl.py`](file:///home/src/pypost/core/mcp_server_impl.py)):**
   - The MCP server registers endpoints in `self.tools_map: Dict[str, RequestData | WebSocketConnection]`.
   - When an AI agent executes a tool via `call_tool(name, arguments)`:
     - `_call_tool_inner` resolves parameter specifications via `resolve_mcp_call_param_specs(item, ...)`.
     - Validates arguments against visible specs via `validate_mcp_call_arguments`.
     - Rejects environment variable override violations via `validate_environment_overrides`.
     - Dispatches request execution to `self._execute_request_sync(item, arguments, env_vars, hidden_keys, overridable_keys)` on a worker thread pool.
     - Receives an `ExecutionResult` containing `response: ResponseData`, `updated_variables: Dict[str, Any]`, `script_logs: List[str]`, and optional `execution_error: Optional[ExecutionError]`.
     - Serializes the result to JSON text using `format_structured_tool_result(result, env_vars=env_vars, hidden_keys=hidden_keys)`.
     - Wraps the formatted text in `TextContent(type="text", text=output_text)` and returns it to the agent.

2. **Access Point for `RequestData.hidden_response_fields`:**
   - In `_call_tool_inner`, `item` is the exact `RequestData` instance being executed.
   - `RequestData.hidden_response_fields: list[str]` was established in **MASK-1** ([`pypost/models/models.py`](file:///home/src/pypost/models/models.py)).
   - Extracting `hidden_response_fields = item.hidden_response_fields if isinstance(item, RequestData) else None` and passing it directly into `format_structured_tool_result(...)` establishes a direct link between user-configured hidden fields and output formatting.

3. **Current Role of `McpResponseSanitizer` ([`pypost/core/mcp_response_sanitizer.py`](file:///home/src/pypost/core/mcp_response_sanitizer.py)):**
   - Acts as a security facade for sanitizing output data before agent exposure:
     - `sanitize_text(text, env_vars=..., hidden_keys=...)`: Sanitizes plain strings.
     - `sanitize_body(body, env_vars=..., hidden_keys=...)`: Sanitizes HTTP response body text.
     - `sanitize_logs(logs, env_vars=..., hidden_keys=...)`: Sanitizes post-script log lines.
   - Currently delegates to `pypost.core.sensitive_text_sanitizer.sanitize_text`.
   - By extending `McpResponseSanitizer.sanitize_body` to accept `hidden_response_fields: Iterable[str] | None = None`, body sanitization seamlessly incorporates request-level hidden field redaction.

4. **Underlying Redaction Engine in `sensitive_text_sanitizer` ([`pypost/core/sensitive_text_sanitizer.py`](file:///home/src/pypost/core/sensitive_text_sanitizer.py)):**
   - Currently provides:
     - `_redact_hidden_values`: Replaces environment secret variable values with `***`.
     - `_redact_json_sensitive_fields`: Applies regex `_SENSITIVE_JSON_KEY` to redact known sensitive key names (`password`, `secret`, `token`, `api_key`, `authorization`, etc.).
     - `_BEARER_TOKEN` and `_QUERY_TOKEN`: Regexes redacting Bearer tokens and URL query parameters.
     - `sanitize_headers`: Redacts sensitive HTTP header values.
   - To support request-configured hidden response fields, a dedicated recursive traversal function `redact_json_response_fields(text, hidden_fields, placeholder="***")` is required. It evaluates selector syntax (simple keys, dot-notation paths, and array wildcards) and redacts matching values with `'***'`.

### 2. Irreversible Security Boundary Verification

- **Zero Reveal Parameters:**
  - `build_tool_input_schema` in [`pypost/core/mcp_tool_contract.py`](file:///home/src/pypost/core/mcp_tool_contract.py) generates tool schemas strictly from `req.mcp_params` (parameters referencing `{{mcp.request.<param>}}`) and permitted environment variable overrides.
  - No parameter named `unmask`, `reveal`, `reveal_secrets`, `show_hidden`, `raw`, or similar exists in generated tool schemas.
- **Zero Reveal Tools:**
  - `MCPServerImpl.register_tools` only registers endpoints where `item.expose_as_mcp == True`. No auxiliary tools (such as `reveal_response_field`, `get_raw_body`, or `unmask_secret`) are registered on the MCP server.
- **Unconditional Redaction:**
  - Masking is applied unilaterally during output serialization. Even if an agent crafts and sends an unauthorized argument (e.g. `{"unmask": true}`), the execution contract ignores or rejects unexpected parameters and `format_structured_tool_result` unconditionally masks all configured fields.

### 3. In-Memory Data Integrity and Immutability

- `ResponseData` ([`pypost/models/response.py`](file:///home/src/pypost/models/response.py)) holds the raw `status_code`, `headers`, and `body` string returned by the HTTP client.
- Python strings are immutable. `McpResponseSanitizer.sanitize_body` parses and creates a sanitized replacement string for the JSON response payload.
- The original `result.response.body` on the `ExecutionResult` and the historical records persisted by `HistoryManager` are never modified in place.
- Local post-request scripts, execution history logs, and UI components continue to observe the authentic upstream HTTP response.

### 4. Selector Traversal & Edge Cases

- **Simple Key Match**: Matches any JSON dictionary key equal to the configured selector at any nesting level (e.g., `"token"` masks root, nested, or list items).
- **Dot-Notation Path**: Matches exact hierarchical object paths from root (e.g., `"user.credentials.secret"` masks only that specific branch, leaving `"other.credentials.secret"` untouched).
- **Array Wildcard Path**: Traverses arrays of objects (e.g., `"items[*].key"` or shorthand `"items.key"`) and redacts matching keys on every array element.
- **Non-String Field Values**: When a matching key's value is an integer, boolean, object, or array (e.g. `{"pin": 1234}`, `{"auth": {"internal": True}}`), the entire value is replaced with `'***'`.
- **Non-JSON Payloads**: If `result.response.body` is plain text, HTML, XML, binary, or malformed JSON, `redact_json_response_fields` safely catches `(json.JSONDecodeError, TypeError)` and returns the body unmodified (letting downstream text heuristics handle any environment secrets).
- **Empty Payloads**: HTTP 204 or empty string `""` returns `""` immediately without error.

---

## Implementation Plan

### High-Level Approach

The implementation follows a strict test-driven development (TDD) workflow:
1. **Step 3 (Failing Repro)**: Implement comprehensive red tests in `tests/test_mcp_hidden_response_fields_masking.py` asserting permanent masking in MCP tool outputs, deep nesting and array masking, non-JSON pass-through, in-memory data immutability, and MCP schema reflection (no reveal tools or parameters).
2. **Step 4 (Development)**:
   - Implement `redact_json_response_fields` and selector matching in `pypost/core/sensitive_text_sanitizer.py`.
   - Update `McpResponseSanitizer.sanitize_body` in `pypost/core/mcp_response_sanitizer.py` to accept `hidden_response_fields`.
   - Update `format_structured_tool_result` and `MCPServerImpl._call_tool_inner` in `pypost/core/mcp_server_impl.py` to thread `hidden_response_fields` from the executed request into output serialization.
   - Run tests until green and verify zero regressions.

---

### Component Modifications and Signatures

#### 1. `pypost/core/sensitive_text_sanitizer.py`

Add `redact_json_response_fields` and selector evaluation helpers:

```python
def redact_json_response_fields(
    text: str,
    hidden_fields: Iterable[str],
    placeholder: str = HIDDEN_PLACEHOLDER,
) -> str:
    """Recursively redacts configured keys and selector paths in JSON response text.
    
    Args:
        text: JSON response body string.
        hidden_fields: Collection of field selectors (key names, dot paths, wildcard paths).
        placeholder: Replacement string (defaults to '***').
        
    Returns:
        Serialized JSON string with matching field values replaced by placeholder.
        If text is not valid JSON (or not an object/array), returns text unmodified.
    """

def _selector_matches(
    path: list[str],
    key: str,
    selectors: set[str],
) -> bool:
    """Return True if key or current path matches any configured selector."""
```

Extend `sanitize_headers` to optionally mask header selectors (e.g., `header:Authorization`):

```python
def sanitize_headers(
    headers: Mapping[str, str],
    *,
    env_vars: Mapping[str, str] | None = None,
    hidden_keys: Iterable[str] | None = None,
    hidden_response_fields: Iterable[str] | None = None,
) -> dict[str, str]:
```

#### 2. `pypost/core/mcp_response_sanitizer.py`

Extend `McpResponseSanitizer.sanitize_body`:

```python
class McpResponseSanitizer:
    @staticmethod
    def sanitize_body(
        body: str,
        *,
        env_vars: Mapping[str, str],
        hidden_keys: Iterable[str],
        hidden_response_fields: Iterable[str] | None = None,
    ) -> str:
        """Sanitizes HTTP body for MCP tool output, redacting hidden fields and env secrets."""
        if hidden_response_fields:
            body = sts.redact_json_response_fields(body, hidden_response_fields)
        return sts.sanitize_text(body, env_vars=env_vars, hidden_keys=hidden_keys)
```

#### 3. `pypost/core/mcp_server_impl.py`

Extend `format_structured_tool_result`:

```python
def format_structured_tool_result(
    result: ExecutionResult,
    *,
    env_vars: dict[str, str] | None = None,
    hidden_keys: set[str] | None = None,
    hidden_response_fields: list[str] | None = None,
) -> str:
    """Serialize ExecutionResult as agent-facing JSON (status, error, body, optional logs)."""
    env, hidden = env_vars or {}, hidden_keys or set()
    body = McpResponseSanitizer.sanitize_body(
        result.response.body,
        env_vars=env,
        hidden_keys=hidden,
        hidden_response_fields=hidden_response_fields,
    )
    payload: dict[str, Any] = {
        "status": result.response.status_code,
        "error": _tool_result_has_error(result),
        "body": body,
    }
    if result.script_logs:
        payload["logs"] = McpResponseSanitizer.sanitize_logs(
            result.script_logs, env_vars=env, hidden_keys=hidden
        )
    if result.execution_error is not None:
        payload["error_category"] = result.execution_error.category.value
        payload["error_message"] = result.execution_error.message
        if result.execution_error.detail is not None:
            payload["error_detail"] = McpResponseSanitizer.sanitize_text(
                result.execution_error.detail, env_vars=env, hidden_keys=hidden
            )
    return json.dumps(payload, ensure_ascii=False)
```

In `MCPServerImpl._call_tool_inner`:

```python
        hidden_fields = (
            item.hidden_response_fields if isinstance(item, RequestData) else None
        )
        output_text = format_structured_tool_result(
            result,
            env_vars=env_vars,
            hidden_keys=hidden_keys,
            hidden_response_fields=hidden_fields,
        )
```

---

### Mandatory — Failing Repro (next Step 3)

The failing repro test suite will be written in **Step 3** in `tests/test_mcp_hidden_response_fields_masking.py` before modifying production code.

- **Test File Path**: `tests/test_mcp_hidden_response_fields_masking.py`
- **Pytest Configuration**: Module-level `pytestmark = pytest.mark.timeout(60)` per `lsr-python` standard; uses `unittest.IsolatedAsyncioTestCase` for async MCP tool execution testing.
- **Test Scenarios Asserted**:
  1. **Single and Multiple JSON Field Masking**:
     - `test_mcp_output_masks_single_and_multiple_root_fields`: Request configured with `hidden_response_fields=["token", "client_secret"]`. When executed, the serialized MCP tool result replaces `"token"` and `"client_secret"` values with `'***'`, while keeping other fields (`"username"`, `"id"`) unmodified.
  2. **Nested Objects and Arrays of Objects Masking**:
     - `test_mcp_output_masks_nested_object_fields`: Configured selector `"secret"` or dot-notation `"user.auth.secret"` masks nested fields inside child dictionaries.
     - `test_mcp_output_masks_fields_in_array_of_objects`: Configured selector `"api_key"` or array wildcard `"items[*].api_key"` masks `api_key` in every object in a list `[{"id": 1, "api_key": "k1"}, {"id": 2, "api_key": "k2"}]`.
     - `test_mcp_output_masks_root_level_array_of_objects`: Top-level JSON array `[{"token": "t1"}, {"token": "t2"}]` has all `token` fields masked with `'***'`.
     - `test_mcp_output_masks_non_string_values`: Values that are integers, booleans, or nested dictionaries/lists configured as hidden are replaced with `'***'`.
  3. **Non-JSON Payloads and Non-Matching Fields Pass-Through**:
     - `test_mcp_output_non_json_body_passes_through`: Plain text or HTML response bodies (e.g. `"<html>OK</html>"`) pass through without raising exceptions.
     - `test_mcp_output_malformed_json_fallback`: Malformed JSON (e.g. `"{broken: json"`) passes through safely without crashing the server.
     - `test_mcp_output_empty_body_passes_through`: Empty response body `""` returns `""`.
     - `test_mcp_output_unmatched_fields_remain_intact`: Fields not matching any selector remain completely unaltered.
  4. **Underlying In-Memory Data Immutability**:
     - `test_underlying_response_data_not_mutated`: Asserts that `result.response.body` before and after formatting contains the raw secret string, proving that masking is strictly a serialization transformation.
  5. **Schema Reflection & Irreversible Security Boundary**:
     - `test_mcp_list_tools_contains_no_unmask_parameters`: Calls `server.list_tools()` and inspects each tool's `inputSchema["properties"]`. Asserts no property named `unmask`, `reveal`, `reveal_secrets`, `show_hidden`, `raw`, etc. exists.
     - `test_mcp_server_registers_no_reveal_tools`: Verifies that no tool named `reveal_*`, `unmask_*`, or `get_raw_*` exists in the registered tool list.
     - `test_mcp_call_tool_ignores_or_rejects_unmask_argument`: Invoking `call_tool` with malicious payload `{"unmask": True}` still returns permanently masked output `'***'`.
- **Failure Forcing & Clean Failure**:
  - In Step 3, running `make test` against `tests/test_mcp_hidden_response_fields_masking.py` will fail with red assertion errors because `format_structured_tool_result` currently ignores `hidden_response_fields`, and `McpResponseSanitizer.sanitize_body` does not perform recursive selector masking.
  - No live network services or external dependencies required.

---

## Architecture

### 1. System Module Breakdown

```mermaid
flowchart TB
    subgraph Agent_Boundary["Agent MCP Interface"]
        AGENT["AI Coding Agent"]
        MCP_SERVER["MCPServerImpl (pypost/core/mcp_server_impl.py)"]
        AGENT -->|tools/call request_tool| MCP_SERVER
        MCP_SERVER -->|Sanitized JSON text (***)| AGENT
    end

    subgraph Execution_Layer["Request Execution Layer"]
        REQ["RequestData (pypost/models/models.py)<br/>+hidden_response_fields: list[str]"]
        EXEC_SYNC["MCPServerImpl._execute_request_sync"]
        REQ_SVC["RequestService (pypost/core/request_service.py)"]
        RESP["ExecutionResult (pypost/core/request_service.py)<br/>.response: ResponseData (Raw, Unmutated)"]

        MCP_SERVER --> EXEC_SYNC
        REQ -.->|Passes request & config| EXEC_SYNC
        EXEC_SYNC --> REQ_SVC
        REQ_SVC --> RESP
    end

    subgraph Sanitization_Pipeline["Sanitization & Output Pipeline"]
        FSTR["format_structured_tool_result()<br/>(pypost/core/mcp_server_impl.py)"]
        MRS["McpResponseSanitizer.sanitize_body()<br/>(pypost/core/mcp_response_sanitizer.py)"]
        STS_REDACT["sensitive_text_sanitizer.redact_json_response_fields()<br/>(pypost/core/sensitive_text_sanitizer.py)"]
        STS_ENV["sensitive_text_sanitizer.sanitize_text()<br/>(Env secrets, Bearer tokens, URL query tokens)"]

        RESP --> FSTR
        REQ -.->|hidden_response_fields| FSTR
        FSTR --> MRS
        MRS --> STS_REDACT
        STS_REDACT --> STS_ENV
        STS_ENV --> FSTR
    end

    FSTR --> MCP_SERVER
```

### 2. Interaction Sequence Diagram

```mermaid
sequenceDiagram
    actor Agent as AI Coding Agent
    participant MCP as MCPServerImpl
    participant Service as RequestService
    participant Fmt as format_structured_tool_result
    participant Sanitizer as McpResponseSanitizer
    participant STS as sensitive_text_sanitizer

    Agent->>MCP: call_tool(name="login_api", arguments={"user": "alice"})
    Note over MCP: Validates arguments against schema; no reveal parameters exist
    MCP->>Service: _execute_request_sync(req, arguments, ...)
    Service-->>MCP: ExecutionResult(response=ResponseData(body='{"token": "xyz123", "id": 1}'))
    
    Note over MCP: Extract req.hidden_response_fields = ["token"]
    MCP->>Fmt: format_structured_tool_result(result, hidden_response_fields=["token"])
    Fmt->>Sanitizer: sanitize_body(result.response.body, hidden_response_fields=["token"])
    Sanitizer->>STS: redact_json_response_fields(body, ["token"])
    Note over STS: Traverses JSON tree -> replaces "token": "xyz123" with "***"
    STS-->>Sanitizer: '{"token": "***", "id": 1}'
    Sanitizer->>STS: sanitize_text(body, env_vars, hidden_keys)
    STS-->>Sanitizer: '{"token": "***", "id": 1}'
    Sanitizer-->>Fmt: '{"token": "***", "id": 1}'
    Fmt-->>MCP: '{"status": 200, "error": false, "body": "{\"token\": \"***\", \"id\": 1}"}'
    
    MCP-->>Agent: [TextContent(type="text", text=envelope)]
    Note over Agent: Agent receives permanent '***'; raw ResponseData was never mutated
```

### 3. Selector Matching Specification and Algorithm

The selector engine matches configured selectors against keys and hierarchical paths during JSON AST traversal:

```
Path Notation:
  - Root key:       ["token"]                -> "token"
  - Nested key:     ["auth", "token"]        -> "auth.token"
  - Array item:     ["items", "*", "token"]  -> "items[*].token" or "items.token"
```

#### Matching Logic

```python
def _selector_matches(path: list[str], key: str, selectors: set[str]) -> bool:
    """Evaluate whether (path, key) satisfies any configured selector."""
    full_path_dot = ".".join(path + [key]) if path else key
    # Also create wildcard notation: e.g. path ['items', '*'] -> 'items[*].key'
    wildcard_dot = ".".join(path + [key]).replace(".*.", "[*].").replace(".*", "[*]")
    # Shorthand notation: path with '*' removed -> 'items.key'
    shorthand_dot = ".".join([p for p in path if p != "*"] + [key])

    for sel in selectors:
        # 1. Simple key match (matches any key at any depth)
        if sel == key:
            return True
        # 2. Exact dot-notation path
        if sel == full_path_dot:
            return True
        # 3. Wildcard path match (e.g. items[*].token)
        if sel == wildcard_dot or sel.replace("[*]", ".*") == full_path_dot:
            return True
        # 4. Shorthand path match (e.g. items.token matching items[*].token)
        if sel == shorthand_dot:
            return True
    return False
```

### 4. Data Contracts and Interfaces

#### Interface: `pypost/core/sensitive_text_sanitizer.py`

```python
HIDDEN_PLACEHOLDER: str = "***"

def redact_json_response_fields(
    text: str,
    hidden_fields: Iterable[str],
    placeholder: str = HIDDEN_PLACEHOLDER,
) -> str:
    """Recursively redacts configured keys/selectors in JSON response text."""
    ...

def sanitize_headers(
    headers: Mapping[str, str],
    *,
    env_vars: Mapping[str, str] | None = None,
    hidden_keys: Iterable[str] | None = None,
    hidden_response_fields: Iterable[str] | None = None,
) -> dict[str, str]:
    """Redact sensitive header values, honoring header:<Name> selectors."""
    ...
```

#### Interface: `pypost/core/mcp_response_sanitizer.py`

```python
class McpResponseSanitizer:
    @staticmethod
    def sanitize_body(
        body: str,
        *,
        env_vars: Mapping[str, str],
        hidden_keys: Iterable[str],
        hidden_response_fields: Iterable[str] | None = None,
    ) -> str: ...
```

#### Interface: `pypost/core/mcp_server_impl.py`

```python
def format_structured_tool_result(
    result: ExecutionResult,
    *,
    env_vars: dict[str, str] | None = None,
    hidden_keys: set[str] | None = None,
    hidden_response_fields: list[str] | None = None,
) -> str: ...
```

---

## Q&A

### Q1: Why is masking permanent for MCP tool outputs while reversible in the GUI?
- **A**: AI agents operate autonomously and transmit tool outputs to external LLM providers, multi-tenant model logs, and persistent transcripts. Giving an automated agent an unmasking parameter or reveal tool would defeat confidentiality and enable prompt extraction attacks. Desktop users, by contrast, are authenticated local operators debugging locally who occasionally need to inspect a token.

### Q2: Why does masking occur in `format_structured_tool_result` instead of mutating `ResponseData` directly?
- **A**: Modifying `result.response.body` would corrupt the authentic execution history stored in `HistoryManager`, break post-request Python scripts that inspect `response.body`, and corrupt data exported to collections. Formatting at the serialization boundary preserves data integrity while guaranteeing zero secrets reach external agents.

### Q3: What happens if an API returns a non-JSON body (e.g. text/plain, HTML, or XML)?
- **A**: `redact_json_response_fields` safely handles non-JSON payloads by returning them unmodified if `json.loads` fails. `McpResponseSanitizer.sanitize_body` then applies `sts.sanitize_text` to catch any environment variable secrets, Bearer tokens, or query parameters. The MCP server never crashes on non-JSON content.

### Q4: How are non-string JSON values (numbers, booleans, objects, arrays) masked?
- **A**: If a key matching a selector has an integer (e.g. `{"pin": 1234}`), a boolean (e.g. `{"active": true}`), or a nested structure (e.g. `{"auth": {"token": "x"}}`), the entire value associated with that key is replaced with the string `'***'`.

### Q5: Can an agent pass arguments to reveal masked values?
- **A**: No. The MCP tool input schema generated for each request strictly derives from configured `mcp_params` and overridable environment variables. No unmasking parameters exist, and the serialization logic does not accept or check any unmask flag from agent inputs.
