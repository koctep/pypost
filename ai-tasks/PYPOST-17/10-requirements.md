# PYPOST-17: Create abstraction for request execution

## Goals

Create a unified abstraction layer for executing HTTP requests that will be used both in the GUI
(via Worker) and in the MCP server. This will eliminate code duplication, ensure consistent
behavior (including script execution) and fix current implementation bugs in the MCP server.

## User Stories

- As **Developer**, I want request execution logic to be in one place so I don't have to fix bugs
  in two places.
- As **MCP User**, I want post-request scripts (e.g. for setting variables) to run when calling
  tools, the same as in the GUI.
- As **User**, I want request behavior to be predictable and identical regardless of whether I run
  them from the interface or via MCP.

## Task Description

Currently request execution logic is fragmented:

1. **GUI** uses `RequestWorker`, which calls `HTTPClient` and then separately `ScriptExecutor`.
2. **MCP Server** manually renders templates and calls `HTTPClient` (with incorrect signature,
   which is a bug).

It is necessary to extract a `RequestService` that encapsulates the entire request execution
process.

### Current Problems

- **Code duplication:** Template rendering and client invocation happen in different places.
- **MCP bug:** `MCPServerImpl` calls `HTTPClient.send_request` with arguments it doesn't accept.
- **Missing MCP functionality:** MCP server does not execute post-request scripts.

## Solution Requirements

### 1. Create `RequestService`

Create class `pypost.core.request_service.RequestService` (or `request_executor.py`) that will be
responsible for:

1. Accepting `RequestData` and variable context.
2. Executing request via `HTTPClient`.
3. Executing post-request scripts via `ScriptExecutor`.
4. Returning a comprehensive execution result.

### 2. `RequestService` Interface

The service must provide a synchronous method (since `HTTPClient` is synchronous, and thread
management is the caller's responsibility).

```python
@dataclass
class ExecutionResult:
    response: ResponseData
    updated_variables: Dict[str, Any] = None
    script_logs: List[str] = None
    script_error: str = None

class RequestService:
    def execute(self, request: RequestData, variables: Dict[str, Any] = None) -> ExecutionResult:
        pass
```

### 3. GUI Integration (`RequestWorker`)

`RequestWorker` must be refactored:

- Remove direct logic for calling `HTTPClient` and `ScriptExecutor`.
- Use `RequestService.execute`.
- Translate `ExecutionResult` to Qt signals.

### 4. MCP Server Integration (`MCPServerImpl`)

`MCPServerImpl` must be refactored:

- Remove manual template rendering.
- Remove incorrect `HTTPClient` call.
- Use `RequestService.execute`.
- Build MCP response from `ExecutionResult`.

## Acceptance Criteria

- [ ] `RequestService` class is created.
- [ ] `RequestWorker` uses `RequestService`.
- [ ] `MCPServerImpl` uses `RequestService`.
- [ ] Post-request scripts run in both GUI and MCP.
- [ ] `HTTPClient` call error in MCP is fixed.
- [ ] Tests (if any) pass.

## Q&A

**Q:** Should `RequestService` be asynchronous?
**A:** No, current `HTTPClient` is synchronous (based on `requests`). `RequestService` should also be
synchronous. Async/threading is managed at `RequestWorker` level (for GUI) and `run_in_threadpool`
(for MCP).

**Q:** How to pass request arguments from MCP?
**A:** They should be passed to `RequestService` via the `variables` dict (e.g. in structure
`{"mcp": {"request": args}}`), which `HTTPClient` uses for template rendering.
