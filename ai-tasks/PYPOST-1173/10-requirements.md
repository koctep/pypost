# PYPOST-1173: Send configured headers on MCP method requests

## Goals

PyPost lets users configure **Headers** on every request, including method
**MCP**. For ordinary HTTP methods those headers — Bearer tokens, API keys,
custom metadata — leave the client and reach the server. For method **MCP**
they do not. The product still prepares them (environment substitution and a
History snapshot), so Send looks complete while the MCP server never received
the auth the user configured.

The business goal is **auth parity and honest History** on the shipped MCP
method path: if the user configured headers, the MCP server must receive the
resolved values, and History must describe what was actually transmitted. This
is independent of the planned MCP Client tab. Users already call MCP endpoints
from the request editor today.

## User Stories

- As a **developer calling a header-gated MCP server**, I want the Bearer
  token and API-key headers I configured on the request to reach that server,
  so that Send authenticates instead of failing as unauthorized.
- As a **developer using environment templates**, I want `{{ variable }}`
  placeholders in MCP request headers to resolve from the active environment
  before Send, so that secrets live in the environment the same way they do
  for HTTP.
- As a **user reviewing History**, I want the recorded headers to match what
  was actually sent, so that I can debug auth and replay calls without being
  misled.
- As a **user switching between HTTP and MCP**, I want **Headers** to mean
  the same thing on both methods, so that I do not have to remember a silent
  exception for MCP.

## Definition of Done

PYPOST-1173 is done when:

1. Sending a method **MCP** request that has configured outbound headers
   transmits those **resolved** headers to the MCP server (after environment
   substitution).
2. Sending a method **MCP** request with no headers still works (empty or
   absent headers are not an error).
3. History for that send lists the same resolved headers that were
   transmitted — it must not claim headers that never left the client.
4. Existing sensitive-data masking of History and resolved fields continues
   to apply; this task does **not** add new masking rules.
5. HTTP method Send behavior is unchanged.
6. No new MCP Client tab-mode UI ships as part of this ticket.
7. Automated tests prove that user-configured headers reach the outbound MCP
   call.
8. `make check` passes.

## Task Description

### Programming Language

Python — existing PyPost request-send product path.

### Problem

Users follow the documented request workflow: choose method **MCP**, fill URL,
Headers, and Body, then click Send. Header values support `{{ variable }}`
placeholders. That editor contract is the same as HTTP.

Today the product substitutes templates for URL, body, **and** headers, then
delivers only URL and body to the MCP server. Auth that lives in headers never
arrives. History still stores the prepared headers, so the record looks
complete while the server never saw them.

### Business Need

Header-gated MCP endpoints (Bearer tokens, API keys) are unusable from the
current MCP method path. Users cannot tell from History that auth never left
the client. HTTP already honors Headers; MCP must match that user-visible
contract. MCP Proxy already lets operators authenticate to upstream MCP
servers with templated headers — outbound method **MCP** should not be the
exception.

This defect was found during the [PYPOST-1164](https://pypost.atlassian.net/browse/PYPOST-1164)
MCP UX audit (Critical). A later story
([PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167), MCP-TM-5)
will add header UX on a new MCP Client tab, but that work sits behind
unstarted stories. Auth is broken **now** on the shipped path; this ticket
closes that live gap without waiting for the new editor.

### Scope (this task)

- Transmit resolved outbound headers on method **MCP** Send, matching HTTP.
- Keep History truthful once those headers are actually sent.
- Cover the current method-MCP path only.

### Out of Scope

- New masking or redaction rules (existing policy already masks resolved
  fields).
- New MCP Client tab-mode UI, protocol picker, or tool-discovery editor
  ([PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165) …
  [PYPOST-1172](https://pypost.atlassian.net/browse/PYPOST-1172)).
- Changing how HTTP requests send headers.
- New user-facing header editor chrome.

### Main Entities (Business Perspective)

| Entity | Role |
| --- | --- |
| **MCP method request** | Request editor item with method MCP: URL, headers, body |
| **Outbound headers** | User-configured key/value pairs, including auth |
| **Resolved fields** | URL, headers, and body after environment substitution |
| **MCP server** | Remote endpoint that may require header-based auth |
| **History entry** | Record of a send; must match what was transmitted |
| **HTTP request** | Working reference: Headers already reach the server |
| **Active environment** | Source of `{{ variable }}` values in headers |

Interaction overview:

1. User configures Headers (often Bearer or API key) on a method MCP request.
2. On Send, PyPost resolves templates from the active environment.
3. The MCP server must receive those resolved headers.
4. History stores the resolved request, including headers, consistent with
   what was transmitted. Masking of secrets in that record stays as today.

### Functional Requirements

- **FR-1:** Resolved outbound headers on a method MCP Send must be delivered
  to the MCP server as part of that call.
- **FR-2:** A method MCP Send with no outbound headers must still complete
  (headers optional).
- **FR-3:** History for a method MCP Send must not list outbound headers that
  were not transmitted.
- **FR-4:** Header `{{ variable }}` substitution uses the active environment,
  same as HTTP Headers.
- **FR-5:** HTTP Send and existing History masking behavior are unchanged.
- **FR-6:** The fix applies to the current method-MCP path and does not
  depend on MCP Client tab mode.

### Non-Functional Requirements

- **NFR-1 Security:** Secrets in headers remain masked in History under the
  existing policy; they must still be sent to the intended MCP server.
- **NFR-2 Consistency:** Method MCP Headers follow the same user-visible
  contract as HTTP Headers.
- **NFR-3 Minimal scope:** No new UI and no new masking product behavior.
- **NFR-4 Reliability:** Empty header maps and templated header values are
  both supported.

### Constraints and Assumptions

- Issue type: **Debt**; priority: **High**; labels: `mcp`; estimate: **3 SP**.
- Sprint: **MCP Client Tab Core UX**.
- Independent of MCP Client tab mode
  ([PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165) …
  [PYPOST-1172](https://pypost.atlassian.net/browse/PYPOST-1172)).
- Existing sensitive-data masking of resolved fields is sufficient.
- Approval for Step 1 is deferred to the orchestrator review gate
  (autonomous run).

## Q&A

**Q: Why not wait for PYPOST-1167 (MCP Client headers)?**

A: That story is a new editor behind unstarted work. Auth is already broken on
the shipped method-MCP path.

**Q: Does this ticket add new masking of secrets?**

A: No. Existing policy already masks resolved fields. HTTP sends headers the
same way.

**Q: Does History need a separate product change?**

A: Once headers are actually transmitted, History's record matches the wire.
No separate History feature is required.

**Q: What happens when the user configured no headers?**

A: Still valid — headers are optional, as on HTTP.

**Q: Does this include the new MCP Client tab UI?**

A: No. Out of scope. This ticket applies only to the current method-MCP path.

**Q: Why is this a standalone debt ticket?**

A: The live defect was discovered in PYPOST-1164 and would otherwise wait on
an unstarted feature chain. Users calling method MCP today cannot authenticate
with headers.

## References

- [PYPOST-1173](https://pypost.atlassian.net/browse/PYPOST-1173) — this debt
  issue
- [PYPOST-1164](https://pypost.atlassian.net/browse/PYPOST-1164) — MCP UX
  audit that recorded the Critical header-drop finding
- [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) — later MCP
  Client tab header UX (not a substitute for this live-path fix)
