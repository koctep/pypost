# PYPOST-77: Move `import re` to Module Level in MCP Variable Extraction

## Goals

Close tech-debt item TD-5 from PYPOST-44: MCP request-variable extraction must follow PEP 8
import conventions so maintainers see dependencies at the top of the module, not buried inside
a method body.

## User Stories

- As a **maintainer**, I want all imports at module scope so I can quickly see what a file
  depends on without reading every function.
- As a **reviewer**, I want MCP extraction code to match project style so style-only diffs do
  not distract from behavioral changes.

## Definition of Done

- No `import re` inside MCP variable extraction functions or methods.
- `re` is imported at module level in the module that owns regex-based MCP placeholder
  discovery.
- Existing MCP secrets-policy and server tests pass.
- Developer docs reflect where regex extraction lives.

## Task Description

**Origin:** PYPOST-44 TD-5 — `_extract_mcp_variables` in `MCPServerImpl` placed
`import re` inside the method body instead of at file top level.

**Scope:** Style-only import placement for the regex path; no change to tool schemas or
execution behavior.

## Q&A

| Question | Answer |
| --- | --- |
| Which module owns extraction now? | `McpSecretsPolicy.extract_mcp_request_variables` in `mcp_secrets_policy.py` (PYPOST-554). |
| Was `_extract_mcp_variables` removed? | Yes — logic moved to `McpSecretsPolicy` in PYPOST-554; inline import removed with the method. |
| Any runtime behavior change? | No — import placement only. |
