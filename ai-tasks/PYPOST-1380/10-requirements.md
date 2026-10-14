# PYPOST-1380: [PYPOST-1312] Integration test suite, edge-case coverage, and developer documentation

## Goals

When developers and automated tools interact with APIs, response payloads frequently contain confidential credentials, including authentication tokens, API keys, session secrets, passwords, and Personally Identifiable Information (PII). Parent Epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312) ("Hide selected response fields: click-to-reveal in UI, permanently masked in MCP output") addresses the dual security risks associated with response inspection:
1. **Interactive Desktop Presentation**: Preventing shoulder-surfing and accidental disclosure during demos and screen-sharing through default masking with an intuitive click-to-reveal mechanism.
2. **Autonomous AI Agent Safety**: Enforcing permanent, fail-closed sanitization for Model Context Protocol (MCP) tool outputs with zero unmasking avenues exposed to external AI agents.

To deliver this capability reliably, the implementation was broken down into focused, incremental units:
- [PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377) (MASK-1): Request configuration model, serialization, tab isolation deep-copy, and RequestEditor UI.
- [PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378) (MASK-2): Irreversible MCP response sanitization and strict agent security boundaries.
- [PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379) (MASK-3): Interactive click-to-reveal masking in desktop GUI ResponseView with subsystem coexistence.

As the final, consolidating task of Sprint 2032, [PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380) (MASK-4) delivers comprehensive verification, end-to-end integration contracts, edge-case validation, reference collection fixtures, and developer documentation:
1. **Cross-Cutting End-to-End Contracts**: Guarantee that a request configured with hidden response fields operates concurrently and harmoniously across both consumption surfaces—interactive click-to-reveal in the desktop GUI and irreversible redaction in MCP tool outputs—without data leakage, surface interference, or desynchronization.
2. **Exhaustive Edge-Case Coverage**: Validate system behavior against complex, real-world data structures, including deeply nested hierarchies, array wildcards, non-string primitive types, duplicate keys across divergent branches, non-JSON responses (HTML, XML, plain text), empty responses (HTTP 204 No Content), and multi-tab isolation scenarios.
3. **Reference Collection Fixtures**: Update bundled example collections with realistic sample hidden response field configurations to serve as ready-to-use patterns for users and integration test suites.
4. **Developer Documentation**: Provide complete developer documentation in `doc/dev/` covering the unified response field masking architecture, selector evaluation semantics, security boundaries, and data immutability guarantees.

## Programming Language

- **Implementation language**: Python (PyPost test suites, example collection configurations, and developer documentation).

## User Stories

- As a **Security Auditor / Compliance Lead**, I want automated integration contracts to verify that any request configured with hidden response fields simultaneously enforces interactive click-to-reveal in the GUI and permanent, irreversible redaction in MCP outputs, so that sensitive credentials can never be extracted by AI agents while remaining safely inspectable by human operators.
- As an **API Developer Testing Complex Schemas**, I want field selector evaluation to handle deeply nested objects, arrays of objects, and duplicate field names across different hierarchy levels reliably, so that only the targeted sensitive attributes are masked without corrupting sibling data.
- As a **Tester Working with Diverse API Payloads**, I want the response masking engine to handle non-string primitive values (numbers, booleans, nulls) as well as non-JSON responses (HTML error pages, XML payloads, plain text) and empty responses (HTTP 204 No Content) gracefully without crashing, throwing unhandled exceptions, or degrading application responsiveness.
- As a **Power User Managing Multiple Tabs**, I want concurrent request tabs with distinct hidden field selectors to operate in strict isolation, ensuring that modifying or executing a request in one tab has zero side effects on other active tabs.
- As a **New User or API Consumer**, I want bundled example collections to include sample requests with pre-configured hidden response fields, so that I can immediately explore and understand how response field masking works in practical scenarios.
- As a **Core Maintainer / Contributor**, I want centralized, authoritative developer documentation in `doc/dev/` detailing the response masking architecture, selector semantics, and security invariants, so that future codebase enhancements preserve security and functional guarantees.

## Definition of Done

This task is considered complete when:

1. **End-to-End Integration Contracts**:
   - Automated end-to-end integration tests verify that executing a request with configured hidden response fields delivers:
     - Interactive click-to-reveal presentation in the desktop GUI ResponseView (default masked, reveal on click, re-mask on click).
     - Permanent, irreversible redaction (`***`) in MCP tool outputs with zero reveal parameters or bypasses.
   - Both surfaces are validated against the same underlying request execution result, verifying that neither surface mutates the raw response data or interferes with the other.

2. **Exhaustive Edge-Case Test Matrix**:
   - Automated test cases cover and pass 100% of the following edge-case scenarios:
     - **Deeply Nested Keys**: Selectors targeting deep paths (e.g. `auth.session.token`) mask only the targeted nested key, leaving siblings and parents intact.
     - **Array Wildcards & Collections**: Array wildcard selectors (e.g. `items[*].secret`, `users.email`) mask targeted keys across every object in an array, handling heterogeneous elements safely.
     - **Non-String Primitive Values**: Masking and GUI toggling operate cleanly on numbers, booleans, nulls, and nested arrays/objects without formatting corruption.
     - **Duplicate Key Names Across Branches**: Identical key names in separate branches (e.g. `user.id` vs `organization.id`) are disambiguated correctly when using dot-notation, while simple root selectors match across all branches.
     - **Non-JSON Payloads**: Plain text, HTML error pages, XML responses, and malformed JSON payloads pass through safely without unhandled exceptions or broken UI presentation.
     - **Empty Responses**: HTTP 204 No Content and empty string bodies are processed cleanly without errors.
     - **Multi-Tab Isolation**: Concurrent tabs with different hidden field configurations maintain complete independence during editing and execution.

3. **Reference Collection Fixtures**:
   - Curated example collections in `examples/collections/` are updated with sample hidden response field configurations representing realistic API use cases (e.g. authentication tokens, API secrets, user credentials).

4. **Comprehensive Developer Documentation**:
   - Developer documentation in `doc/dev/` (specifically `doc/dev/hidden_response_fields.md`) is maintained and verified, documenting:
     - Overall response field masking architecture and subsystem responsibilities.
     - Selector syntax rules and evaluation semantics (simple keys, dot notation, array wildcards, header selectors).
     - Security boundaries between desktop GUI (reversible presentation) and MCP tools (irreversible redaction).
     - RequestData copy policy, tab isolation, and in-memory response data immutability.

5. **Test Quality and Automation**:
   - All newly created test suites include explicit `@pytest.mark.timeout(...)` annotations per repository standards.
   - All tests pass cleanly under `make test` without flakiness or regressions.

6. **Quality Gate Compliance**:
   - Repository quality checks (`make lint`, `make typecheck`, `make verify-ai-tasks`, `make test`) pass with zero errors.

## Task Description

### Problem Statement

Parent Epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312) decomposes the response field masking capability across three distinct functional layers:
- Configuration, storage, and editor UI (MASK-1).
- Irreversible MCP tool output sanitization (MASK-2).
- Desktop GUI interactive click-to-reveal presentation (MASK-3).

While each unit includes isolated unit tests, the system requires end-to-end integration contracts to prove that both presentation and tool-output surfaces operate harmoniously on identical requests. Furthermore, real-world API responses frequently present complex and non-standard payloads—such as deeply nested hierarchies, array collections, non-string primitives, duplicate keys across branches, non-JSON formats (HTML, XML, plain text), empty HTTP 204 responses, and concurrent multi-tab editing. 

Without an exhaustive edge-case test suite, reference collection fixtures, and consolidated developer documentation, potential edge-case failures or regressions could compromise confidentiality or destabilize the application. Task [PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380) completes the epic by delivering these contracts, edge-case coverage, fixtures, and documentation.

### Scope

- **In Scope**:
  - End-to-end integration tests verifying both GUI click-to-reveal and MCP permanent masking on the same request execution.
  - Comprehensive edge-case test coverage:
    - Deeply nested keys.
    - Array wildcards and collections of records.
    - Non-string scalar values (numbers, booleans, nulls) and compound structures.
    - Duplicate key names at different levels of the hierarchy.
    - Non-JSON response bodies (HTML error pages, XML documents, plain text).
    - Empty bodies (HTTP 204 No Content, empty strings).
    - Multi-tab isolation and draft independence.
  - Updating reference collection fixtures in `examples/collections/` with sample hidden response field configurations.
  - Finalizing developer documentation in `doc/dev/` covering architecture, selector semantics, security boundaries, and copy policies.
  - Verifying all quality gates (`make lint`, `make typecheck`, `make verify-ai-tasks`, `make test`).

- **Out of Scope**:
  - Modifying the underlying `RequestData` data model or `HiddenFieldsTable` widget (completed in **PYPOST-1377** / MASK-1).
  - Modifying the core MCP tool registration or dispatch architecture (completed in **PYPOST-1378** / MASK-2).
  - Modifying the core GUI `ResponseMaskController` event loop or highlighting algorithms (completed in **PYPOST-1379** / MASK-3).
  - Exposing any secret reveal mechanism or parameter to MCP AI agents (strictly prohibited by security boundary).
  - GUI response header masking (the desktop GUI currently does not render response headers).

### Functional Requirements

- **FR-1 Cross-Cutting End-to-End Integration Contract**:
  - The system must verify that when a request configured with `hidden_response_fields` is executed, the resulting response data can be consumed by both GUI presentation and MCP tool serialization without cross-surface interference.
  - In the GUI surface, matching fields must appear masked by default with working click-to-reveal and click-to-re-mask toggling.
  - In the MCP surface, matching fields must be permanently and irreversibly redacted with `***`.
  - Consuming the response in one surface must not mutate, pollute, or alter the response data consumed by the other surface.

- **FR-2 Deeply Nested & Hierarchical Key Resolution**:
  - Dot-notation selectors (e.g. `auth.tokens.access_token`) must match and mask only the targeted nested property.
  - Sibling properties at the same nesting level and parent objects must remain unmasked.
  - Simple root keys (e.g. `secret`) must match and mask occurrences across all nesting levels unless explicitly qualified by a path selector.

- **FR-3 Array Wildcard & Collection Handling**:
  - Array wildcard selectors (e.g. `items[*].secret`, `users.email`) must match and mask the targeted field across every object within a JSON array.
  - Arrays containing mixed element types, empty arrays, or objects where the target field is absent must process cleanly without errors or partial masking corruptions.

- **FR-4 Non-String Primitive & Complex Structure Masking**:
  - Hidden response field selectors targeting numbers, booleans, nulls, or complex nested structures (objects/arrays) must mask those values cleanly.
  - In the GUI presentation, clicking to reveal a non-string value must display its valid raw representation (e.g. `42`, `true`, `null`), and re-masking must restore the placeholder (`"***"`).

- **FR-5 Duplicate Key Disambiguation Across Branches**:
  - When identical key names exist in disparate object branches (e.g. `{"account": {"id": 1}, "device": {"id": 2}}`), a dot-notation selector (e.g. `account.id`) must mask exclusively the specified branch.
  - A simple key selector (e.g. `id`) must mask all matching keys regardless of branch location.

- **FR-6 Non-JSON Body Pass-Through**:
  - When a response body consists of non-JSON content (such as HTML error pages, XML payloads, plain text log files, or malformed JSON), field selector evaluation must safely catch parsing exceptions and pass the body through unmodified.
  - Global environment variable secret sanitization (e.g. Bearer tokens, Authorization credentials) must remain active even on non-JSON payloads.

- **FR-7 Empty Response Processing**:
  - When an API returns an empty body (e.g. HTTP 204 No Content, HTTP 200 with empty string, or null payload), response field masking must complete gracefully with zero errors or invalid state.

- **FR-8 Multi-Tab Isolation & Independence**:
  - Opening, editing, or executing requests across multiple isolated tabs must maintain strict independence of hidden response field configurations.
  - Modifying selectors in Tab A must never alter selectors, baseline snapshots, or rendered output in Tab B.

- **FR-9 Reference Example Collection Fixtures**:
  - Bundled example collections in `examples/collections/` must include realistic requests configured with sample hidden response fields (such as masking tokens or client secrets in authentication endpoints).
  - Example collections must validate cleanly under existing collection schema and library checks.

- **FR-10 Developer Documentation Maintenance**:
  - Centralized developer documentation in `doc/dev/hidden_response_fields.md` must be comprehensive, up-to-date, and accurately reflect:
    - End-to-end masking architecture and lifecycle.
    - Selector syntax grammar, precedence, and wildcard semantics.
    - Reversible GUI presentation vs irreversible MCP security boundary.
    - Deep-copy tab isolation and data immutability invariants.
    - Verification and testing instructions.

### Non-Functional Requirements

- **NFR-1 Test Determinism & Flakiness Prevention**: All integration and edge-case tests must execute deterministically without timing glitches, race conditions, or reliance on network connectivity.
- **NFR-2 Execution Performance**: End-to-end integration test suites must complete rapidly, adhering to repository test performance guidelines (< 5s per test suite).
- **NFR-3 Security & Fail-Closed Invariant**: In MCP tool output, sensitive values matching hidden selectors must be permanently redacted with `***`. No parameter or auxiliary tool may allow an external agent to reveal or bypass masking.
- **NFR-4 Data Immutability**: Masking transformations across both GUI and MCP boundaries must remain strictly presentation/serialization operations. In-memory `ResponseData` instances and saved history records must remain unmutated.
- **NFR-5 Documentation Quality**: Documentation in `doc/dev/` must adhere to repository markdown lint standards, contain valid relative links, and clearly explain architecture and security models.

## Main System Components / Business Domain

| Business Entity | Description |
| --- | --- |
| **End-to-End Integration Contract** | The verified behavioral contract ensuring that configured hidden response fields function seamlessly across both GUI and MCP consumption surfaces on identical request configurations. |
| **Desktop GUI Presentation Surface** | The interactive user interface layer where sensitive fields are masked by default and can be interactively toggled between masked and revealed states via click-to-reveal. |
| **MCP AI Agent Output Surface** | The automated integration layer where sensitive fields are permanently and irreversibly redacted to prevent secret ingestion by AI models. |
| **Edge-Case Validation Matrix** | The comprehensive set of structural and format boundary tests covering deeply nested paths, array wildcards, non-string types, duplicate keys, non-JSON formats, empty bodies, and multi-tab isolation. |
| **Field Selector Syntax** | The expression grammar (simple keys, dot notation, array wildcards, header prefix) used by developers to specify which response attributes are sensitive. |
| **Reference Collection Fixture** | Curated example request collections demonstrating best-practice configurations of hidden response fields for common authentication and API workflows. |
| **Developer Documentation** | The technical specification and architectural guide in `doc/dev/` documenting the design, selector evaluation rules, security boundaries, and copy policies. |
| **Multi-Tab Request Context** | The isolated application context ensuring that request configurations and masking states remain segregated across multiple open tabs. |

## Q&A

- **Q: Why is an end-to-end integration test required when unit tests already exist for MASK-1, MASK-2, and MASK-3?**
  - **A:** Unit tests verify each subsystem in isolation (model serialization, MCP output string sanitization, and GUI widget event handling). An end-to-end integration test proves that a single request configuration seamlessly drives both consumption surfaces without discrepancy, verifies that neither surface alters shared state or in-memory responses, and prevents cross-cutting regressions as the codebase evolves.

- **Q: What is the core security distinction between the GUI and MCP surfaces?**
  - **A:** Desktop GUI users are trusted human developers inspecting their own workstation; masking protects against passive disclosure (screen-shares, shoulder-surfing) while allowing authorized click-to-reveal. In contrast, MCP clients are external automated AI agents; secrets must be permanently redacted (`***`) with zero reveal parameters or bypass tools to prevent leakage into LLM contexts or logs.

- **Q: How does the selector engine handle duplicate key names across distinct branches?**
  - **A:** Dot-notation paths (e.g. `user.id`) provide exact scoping to the designated branch, leaving `organization.id` unmasked. If a developer uses a simple root key (e.g. `id`), the selector intentionally matches and masks all occurrences of that key across all branches.

- **Q: How are array wildcards evaluated when array elements have heterogeneous structures?**
  - **A:** Selectors such as `items[*].secret` or `users.email` traverse array elements individually. If an element is an object containing the targeted key, that key's value is masked. If an element is missing the key, is empty, or is a primitive, it is safely bypassed without errors.

- **Q: How does the system handle non-string primitive values (numbers, booleans, nulls)?**
  - **A:** The masking engine masks non-string values just as it does string values (displaying `***` or `"***"` in formatted JSON). In the GUI, clicking to reveal replaces the placeholder with the formatted literal representation (e.g. `12345`, `false`, `null`), and clicking again restores the masked placeholder.

- **Q: What happens if an API returns an HTML error page or plain text when hidden JSON fields are configured?**
  - **A:** When JSON parsing fails, the system safely catches the exception and passes the raw text through intact. In MCP mode, global environment secret sanitization (e.g. redacting known secret variable values) still executes. In GUI mode, the body is displayed in clear text without crashing the viewer.

- **Q: How does the system handle empty responses (such as HTTP 204 No Content)?**
  - **A:** An empty response body contains no fields to match; the masking engine evaluates the empty body gracefully, returning the empty content without error across both GUI and MCP surfaces.

- **Q: What example collections will be updated with hidden response field configurations?**
  - **A:** Curated collections in `examples/collections/` (e.g. `jira_mcp.json`, `github_mcp.json`, or `mcp.json`) will be enhanced with realistic `hidden_response_fields` entries on endpoints that return authentication tokens or sensitive credentials, demonstrating proper usage.

- **Q: Does response masking alter the underlying response data in memory or history?**
  - **A:** No. In-memory `ResponseData` instances and saved request history remain completely unmasked and authentic. Masking is strictly a presentation and serialization transformation.
