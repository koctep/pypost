# PYPOST-1052: Widen MCP request parameter discovery for function-wrapped template expressions

## Programming Language

Python is the implementation language for the application runtime and automated test suites. English Markdown is used for workflow documentation and technical artifacts.

## Goals

When users configure API requests in PyPost and expose them as Model Context Protocol (MCP) tools for AI agents, the request definitions frequently use template expressions to inject dynamic values supplied by the agent. In many real-world workflows, these agent-provided inputs are wrapped inside helper functions or transformation expressions (for example, type casting such as integer conversion, string manipulation, or formatting).

When user-authored collections omit explicit manual parameter metadata and rely on automated parameter discovery:
- The system currently only discovers bare, unwrapped agent variable references. Any agent input wrapped in a helper function or nested expression is ignored during automated discovery.
- As a consequence, generated MCP tool definitions omit these required parameters from their input schemas. When AI agents inspect and invoke these tools, they lack the necessary input parameters, causing runtime request execution errors or missing values.
- In the request editor UI and contract preview, automated synchronization similarly misses function-wrapped agent inputs, creating discrepancies between the request template and the advertised tool interface.

**Business goal:** Ensure that automated MCP tool parameter discovery reliably identifies all agent-supplied inputs referenced across request definitions, even when wrapped in helper functions or transformation expressions, so that AI agents receive complete, accurate tool input schemas and users can expose customized requests as MCP tools without manual parameter configuration boilerplate.

## User Stories

- As an **AI agent using exposed MCP tools**, I want tool input schemas generated from user-authored requests to include all required inputs—even when the underlying request template wraps those inputs in helper functions or expressions—so that I can discover and supply every required parameter and avoid execution failures due to missing data.
- As an **API collection author / user**, I want automatic parameter discovery to recognize agent variables used within expressions and function calls throughout my request templates (URL, query parameters, headers, and request body), so that I do not have to manually configure parameter metadata tables for every wrapped variable.
- As an **application operator / user**, I want the request editor UI and tool preview to automatically sync and show all agent parameters used in templates (including wrapped ones), so that the exposed tool contract accurately reflects the template requirements in real time.
- As a **security / product steward**, I want widening agent parameter discovery to strictly preserve secret isolation and policy exclusion boundaries, ensuring sensitive environment variables and credentials are never mistakenly advertised as agent inputs.
- As a **contributor / maintainer**, I want deterministic offline validation to verify that function-wrapped and bare agent variables are discovered consistently across the entire platform, preventing regression.

## Definition of Done

- [x] Automated agent parameter discovery recognizes agent variable references across all request fields (URL, headers, query parameters, and request body) when wrapped inside helper functions or expressions.
- [x] Bare (unwrapped) agent variable references continue to be discovered accurately without regressions across all request fields.
- [x] Multiple agent variables occurring within the same request field or expression are all discovered without omission.
- [x] Requests exposed as MCP tools publish complete input schemas including both bare and function-wrapped agent parameters when relying on auto-discovery.
- [x] UI request editor synchronization automatically discovers and populates parameter tables for wrapped agent variables when template contents change.
- [x] Environment variables and sensitive secrets remain strictly protected and are not mistakenly classified as agent inputs.
- [x] Existing capability, authentication, environment variable resolution, and placeholder handling behaviors remain intact.
- [x] All verification is deterministic and supported by automated tests with standard test timeouts.
- [x] Developer documentation is updated to describe the supported agent parameter discovery behavior in template expressions.

## Task Description

**Problem:**
Follow-up from PYPOST-1028. Curated fixtures publish their inputs through explicit parameter metadata, but user-authored collections often omit manual parameter definitions and rely on automatic discovery. Currently, automated discovery only detects standalone/bare agent input placeholders. When an agent input is passed to a transformation function or embedded in an expression within a request URL, header, query parameter, or body, the discovery mechanism fails to register the variable as a tool input. This leads to incomplete tool contracts for AI agents and synchronization gaps in the user interface.

**Scope (in):**
- Widen automated agent parameter discovery across all request template fields (URL, headers, query parameters, body) to recognize agent variables wrapped in functions and expressions.
- Ensure all callers relying on automated discovery (tool schema generation, contract previews, UI parameter synchronization) consistently receive discovered wrapped agent variables.
- Maintain existing discovery for bare agent variables.
- Maintain existing sensitive variable exclusions and environment variable resolution rules.
- Add comprehensive automated test coverage for function-wrapped agent variables across various template contexts.
- Update developer documentation describing MCP parameter discovery behavior.

**Scope (out):**
- Modifying curated example fixture definitions (which already declare explicit parameter metadata).
- Redesigning the underlying templating syntax or adding new template functions.
- Altering the network MCP transport protocols, HTTP/SSE routing, or tool invocation dispatch.
- Changing authentication mechanisms or live integration behaviors.

**Constraints and assumptions:**
- Agent input variables follow the established naming convention for agent-supplied request values.
- Discovery must operate across all configurable request fields (URL, headers, query parameters, body).
- Existing explicit parameter metadata continues to take precedence or merge seamlessly with discovered parameters.
- Secret safety and sensitive variable policies must be strictly preserved.
- Verification must be offline, deterministic, and self-contained without requiring network access or live external services.

## Main Entities and Interactions

- **Request Definition:** A user-configured HTTP request containing URL, headers, query parameters, and body with embedded template expressions.
- **Agent Input Variable:** A dynamic parameter placeholder intended to be supplied by an AI agent during tool execution.
- **Expression / Function Wrapper:** A template expression or helper function wrapping an agent input variable to perform type conversions, formatting, or data transformations.
- **MCP Tool Contract / Schema:** The published tool definition presented to AI agents describing available input parameters, descriptions, and types.
- **Automated Discovery Engine:** The mechanism that scans request template fields to identify all referenced agent input variables when explicit metadata is absent.
- **Policy Exclusion Guard:** The security mechanism that ensures environment secrets and sensitive values are excluded from agent tool schemas.
- **UI Parameter Synchronizer:** The editor component that automatically populates parameter tables from template contents as users edit requests.

**Interaction Flow:**
1. A user authors an HTTP request template using expressions that wrap agent variables in functions (e.g. converting a parameter to an integer in a URL or query parameter).
2. When the request is configured as an MCP tool (or inspected in the UI / queried by an AI agent), the automated discovery engine scans all template fields.
3. The discovery engine extracts all agent variable names—both bare and function-wrapped.
4. The policy exclusion guard validates that sensitive environment variables and secrets are not included.
5. The tool contract builder constructs a complete input schema containing all discovered agent parameters.
6. The AI agent inspects the tool contract, supplies the required parameters, and successfully invokes the tool without runtime missing-parameter errors.

## Non-Functional Requirements

- **Completeness & Accuracy:** All agent input variables within request templates must be discovered regardless of surrounding function calls or expression nesting.
- **Security & Secret Safety:** Sensitive environment keys and secrets must remain isolated and never exposed as agent parameters.
- **Performance:** Automated discovery must perform efficiently during request editing and tool listing without introducing perceptible latency.
- **Backward Compatibility:** Existing requests using bare agent variables and collections with explicit parameter metadata must continue to function without behavioral changes.
- **Determinism:** Discovery results must be strictly deterministic across all platforms and execution environments.

## Q&A

**Q: Why is widening discovery necessary if curated example fixtures already work?**
**A:** Curated example fixtures declare explicit parameter metadata (`mcp_params`), but real-world users frequently author custom collections without manually defining parameter metadata, relying entirely on automatic discovery. Without wrapped discovery, user-authored templates with helper functions fail when exposed to AI agents.

**Q: Does this change allow arbitrary expressions in place of agent parameters?**
**A:** It allows agent input variables to be embedded inside expressions and helper functions within request templates, while ensuring the underlying variable names are discovered as required tool inputs.

**Q: How does this interact with existing sensitive secret protection?**
**A:** Sensitive environment variables and secret exclusions remain strictly enforced. Widening discovery only expands the recognition of agent-supplied request variables (`mcp.request.*`), not environment secrets.

**Q: Does this require live network or external service testing?**
**A:** No. All discovery and schema generation logic is tested deterministically and offline using unit and contract test suites.
