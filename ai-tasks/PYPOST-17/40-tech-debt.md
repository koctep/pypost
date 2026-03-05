# PYPOST-17: Technical Debt Analysis

## Shortcuts Taken

* **Synchronous Execution in MCP:** `RequestService` was made synchronous because `HTTPClient` is
  built on `requests`. In `MCPServerImpl` this is handled via `run_in_threadpool`. In the future,
  when switching to an async HTTP client (e.g. `httpx`), `RequestService` will need to be updated.

## Code Quality Issues

* **Jinja2 Environment Duplication:** `MCPServerImpl` creates its own `Environment`, while
  `TemplateEngine` (used inside `HTTPClient` and indirectly `RequestService`) may use another (or
  recreate it). This is not critical in this iteration, but having a unified `TemplateService` is
  preferable.
* **Variable Extraction Logic:** The `_extract_mcp_variables` logic in `MCPServerImpl` still
  duplicates template parsing logic that partially exists in `TemplateEngine`.

## Missing Tests

* **Unit Tests for RequestService:** The class was created but no dedicated unit tests were added.
* **Integration Tests for MCP:** No automated tests verifying script execution via MCP.

## Performance Concerns

* **Thread Overhead:** Using `run_in_threadpool` for each MCP request may add overhead under high
  load, but for the current usage scenario (desktop app) this is acceptable.

## Follow-up Tasks

* **PYPOST-8:** Add unit tests for `RequestService`.
* **PYPOST-9:** Refactor `TemplateEngine` to eliminate Jinja2 usage duplication.
