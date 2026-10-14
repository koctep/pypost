# PYPOST-1378: [PYPOST-1312] Permanent MCP output masking for hidden response fields

## Goals

When HTTP requests are exposed as Model Context Protocol (MCP) tools, automated AI coding agents invoke them directly to inspect API behaviors and retrieve live data. However, many APIs return sensitive credentials such as authentication tokens, session cookies, API secrets, passwords, or Personally Identifiable Information (PII).

Allowing external AI agents to receive raw, unmasked sensitive response data introduces severe security risks:
1. **Model Context Ingestion**: Secrets returned in tool output payloads are ingested directly into external LLM context windows and third-party model inference traces.
2. **Log and Telemetry Leakage**: Agent interactions and tool call transcripts are commonly recorded in persistent agent transcripts, telemetry systems, or debugging logs.
3. **Prompt Injection & Extraction**: Untrusted agent instructions or compromised prompts could attempt to inspect or extract sensitive credentials from tool outputs.

Parent Epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312) ("Hide selected response fields: click-to-reveal in UI, permanently masked in MCP output") establishes response confidentiality throughout PyPost. Unlike human desktop developers who can selectively inspect secrets locally via click-to-reveal in the GUI (addressed in MASK-3), automated AI agents must be treated as untrusted with respect to sensitive credentials.

This task ([PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378), MASK-2) establishes the permanent masking and security boundary for all MCP tool outputs:
1. **Permanent Masking**: Ensure all response fields designated as hidden on a request are permanently masked with `***` in MCP tool execution outputs.
2. **Irreversible Security Boundary**: Strictly enforce that no MCP tool parameter, reveal tool, or configuration option allows an agent to bypass masking or retrieve raw secrets.
3. **Data Integrity & Immutability**: Guarantee that masking applies strictly to the serialized output returned to MCP clients, leaving internal in-memory response data and execution history pristine and uncorrupted.
4. **Robust Payload Handling**: Gracefully handle diverse response structures—including nested hierarchies, lists of objects, non-matching keys, non-JSON bodies, and error results—without crashing or failing closed insecurely.

## Programming Language

- **Implementation language**: Python (PyPost core MCP tool execution layer, sanitization pipelines, and test suites).

## User Stories

- As a **Security Officer / Team Lead**, I want PyPost to permanently redact all configured hidden response fields when requests are invoked as MCP tools by AI agents, so that secrets never leak into external LLM prompts, model context windows, or persistent agent transcripts.
- As an **AI Coding Agent**, I want tool output payloads to clearly mark masked sensitive fields (using a standard `'***'` placeholder) while keeping the surrounding response structure and metadata intact, so that I can verify request execution success and parse non-sensitive fields reliably.
- As an **API Developer**, I want to be confident that configuring hidden response fields on my requests establishes an airtight security boundary, ensuring that no tool parameter, configuration flag, or secondary tool exists in the MCP schema to reveal the masked values.
- As a **Developer / Auditor**, I want internal request execution history and in-memory responses to remain unmutated, so that local inspection, automated post-scripts, and auditing logs always retain the authentic execution data.
- As a **System Operator**, I want MCP output formatting to gracefully handle complex nested structures, lists of objects, non-matching keys, non-JSON payloads, and error conditions without crashing the MCP server or returning malformed data.

## Definition of Done

This task is considered complete when:

1. **Permanent Field Masking**:
   - MCP tool outputs permanently mask all response values matching the request's configured `hidden_response_fields` with `'***'`.
   - Masking applies across single objects, deeply nested objects, and arrays/lists of objects.
2. **Irreversible Security Boundary**:
   - Strictly no MCP tool parameter, reveal tool, or configuration bypass allows revealing masked response values through MCP.
   - The MCP tool schemas exposed to agents contain zero parameters or tools related to unmasking or revealing hidden response fields.
3. **Display-Only Transformation & Data Integrity**:
   - Masking is strictly an output formatting operation.
   - The underlying in-memory response data (`ResponseData`), execution results, and request execution history records remain unmodified and authentic.
4. **Resilient Payload Handling**:
   - Complex nested JSON objects and lists of objects with matching keys are sanitized accurately.
   - Non-matching keys and values remain completely unchanged.
   - Non-JSON payloads (plain text, HTML, XML, empty bodies) and execution error responses are handled gracefully without crashing or leaking unredacted content.
5. **Comprehensive Verification**:
   - Unit and integration tests verify permanent masking across single, nested, and array response fields.
   - Tests assert the complete absence of reveal mechanisms in MCP server schemas and tool definitions.
   - All repository quality gates (`make check`, `make lint`, `make typecheck`, `make verify-ai-tasks`) pass cleanly.

## Task Description

### Problem Statement

In PyPost, users can expose saved HTTP requests as tools for AI coding agents via the Model Context Protocol (MCP). While this unlocks powerful automated workflows, APIs often return sensitive credentials (e.g. access tokens, client secrets, passwords, session tokens, or personal identifiers).

When a request configured with hidden response fields is executed through MCP:
- Returning the raw response leaks confidential values into LLM context windows and transcripts.
- Unlike desktop users who have an authenticated, local GUI interface with click-to-reveal capabilities, external AI agents should never have a mechanism to reveal or request unmasked secrets.
- If sanitization modifies in-memory response objects directly, internal state (such as post-script execution or history logs) would be corrupted.

A robust, fail-closed sanitization mechanism is required to permanently redact sensitive response fields before serialized results are transmitted to MCP clients.

### Scope

- **In Scope**:
  - Sanitization of response payloads in MCP tool execution outputs based on the request's configured `hidden_response_fields`.
  - Permanent replacement of matching field values with the standard placeholder `'***'`.
  - Support for selector semantics: matching field keys at any object depth, hierarchical dot-notation paths, array item fields, and response header selectors where present.
  - Strict enforcement of an irreversible security boundary with zero reveal capabilities exposed in MCP tool schemas.
  - Preservation of raw in-memory response data, execution results, and execution history.
  - Robust handling of edge cases: non-matching fields, nested structures, arrays of objects, non-JSON or malformed payloads, empty responses, and execution errors.
  - Unit and integration test coverage verifying sanitization behavior and schema security boundaries.
- **Out of Scope**:
  - Request model schema definition and RequestEditor UI table (completed in **PYPOST-1377** / MASK-1).
  - GUI desktop response viewer masking, interactive click-to-reveal toggles, and syntax highlighting (addressed in **PYPOST-1379** / MASK-3).
  - End-to-end integration contracts spanning both GUI click-to-reveal and MCP output sanitization simultaneously (addressed in **PYPOST-1380** / MASK-4).

### Functional Requirements

- **FR-1 Permanent Response Field Redaction**:
  - When an MCP tool corresponding to an HTTP request is invoked, the output returned to the agent must mask all response fields matching the request's configured hidden response fields.
  - Every matching value must be replaced with the exact placeholder `'***'`.
  - Non-matching keys and values must remain unmodified.

- **FR-2 Hierarchical and Collection Traversal**:
  - Masking must correctly identify and redact matching fields regardless of where they appear in the JSON response:
    - Root-level object fields.
    - Deeply nested child object fields.
    - Fields inside objects within arrays or lists.
    - Specific paths specified via dot notation or array wildcards.

- **FR-3 Irreversible Security Boundary**:
  - The MCP interface must enforce a strict, fail-closed security boundary:
    - No MCP tool parameter (e.g. `reveal_secrets`, `unmask`, `raw`) shall be accepted or exposed to reveal masked values.
    - No secondary or auxiliary MCP tool (e.g. `reveal_field`, `get_raw_response`) shall exist to obtain unmasked response data.
    - Tool schema definitions exposed to agents must not advertise any reveal capabilities.

- **FR-4 Output-Only Masking and In-Memory Data Integrity**:
  - Masking must be applied strictly during output serialization for the MCP response.
  - The original, raw response payload in memory and in the execution history manager must remain unmutated and intact for local PyPost operations and audit logging.

- **FR-5 Safe Handling of Diverse Body Formats and Errors**:
  - If a response body is not valid JSON (e.g., plain text, HTML, XML, binary, or malformed data), the sanitization process must handle it safely without raising unhandled exceptions or crashing the MCP server.
  - Empty response bodies (e.g. HTTP 204 No Content) must be handled gracefully.
  - Execution errors (e.g., network failure, timeout, script failure) must retain standard error reporting without exposing sensitive data in error details.

### Non-Functional Requirements

- **NFR-1 Security & Confidentiality**: Fail-closed design ensures that no configuration oversight or agent prompting technique can bypass masking or exfiltrate hidden response fields through MCP.
- **NFR-2 Performance & Latency**: Payload sanitization must introduce negligible processing overhead (< 10ms for standard JSON payloads up to 1 MB), ensuring responsive MCP tool execution.
- **NFR-3 Reliability & Fault Tolerance**: Sanitization routines must never raise unhandled exceptions or crash the MCP server process, even when encountering malformed payloads, circular references, or deeply nested structures.
- **NFR-4 Maintainability & Testability**: All sanitization logic and schema boundary invariants must be verified by automated unit and integration tests with deterministic execution and explicit timeout markers.

### Main Business Entities

| Business Entity | Description |
| --- | --- |
| **MCP Tool Invocation** | A tool execution request issued by an AI agent over the Model Context Protocol to execute a designated PyPost request. |
| **Hidden Response Field Selector** | A user-configured rule or key identifying a sensitive response field that must not be exposed to external consumers. |
| **Sanitized Tool Result** | The agent-facing serialized output of an MCP tool execution where sensitive response fields have been permanently replaced with `'***'`. |
| **Raw Response Entity** | The authentic, unmutated HTTP response data stored in memory and execution history for internal auditing and local inspection. |
| **AI Coding Agent** | An external automated consumer interacting with PyPost via MCP tools that must operate under a zero-trust confidentiality model for hidden response fields. |

## Q&A

- **Q: Why must MCP output masking be permanent, while the desktop GUI provides click-to-reveal?**
  - **A:** Human developers operating the desktop GUI are authenticated local users who may need to inspect a secret during testing (e.g. copying a session token to debug an issue). In contrast, AI coding agents operate autonomously and transmit tool outputs to external LLM providers and logs. Giving an AI agent access to unmask secrets would defeat the purpose of hiding them and create severe prompt injection and data exfiltration risks.

- **Q: What placeholder should be used for masked fields?**
  - **A:** The standard placeholder `'***'`, consistent with PyPost's sensitive text and environment secret sanitization standards.

- **Q: Should masking alter the raw HTTP response stored in history or in memory?**
  - **A:** No. Masking is strictly a serialization/formatting operation for external presentation to MCP agents. The raw in-memory `ResponseData` and execution history must remain unmodified so that internal post-scripts, tests, and audit trails reflect authentic server responses.

- **Q: What happens if an API returns a non-JSON body (such as plain text or HTML) with hidden response fields configured?**
  - **A:** The sanitization process must handle non-JSON responses gracefully without crashing. Standard text and heuristic secret sanitization (e.g. environment variable secrets and Bearer tokens) continues to apply, while structured JSON field matching safely falls back.

- **Q: Can an AI agent request unmasked values by passing a special parameter?**
  - **A:** No. There is strictly no parameter, flag, or auxiliary tool that allows unmasking. The security boundary is permanent and irreversible for MCP consumers.
