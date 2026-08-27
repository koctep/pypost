# PYPOST-1186: Shared empty-row Key/Value table for HTTP, WS, MCP headers

## Goals

[PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) shipped an MCP
Client **Headers** editor that repeats the same empty-row Key/Value
experience already used on HTTP request Params/Headers and on WebSocket
handshake Params/Headers. Three copies exist so a bugfix or UX tweak in
one place can leave the others behind. The copies already diverge in small
product-visible ways (how keys are normalized when read back, how bulk
populate behaves, whether the table can lock while connected).

This debt item consolidates that shared empty-row Key/Value editor so
maintainers fix and evolve it once, while end users keep the same Key/Value
editing job on HTTP, WebSocket, and MCP Client. MCP Client Headers must stay
independent of the HTTP request editor surface — MCP chrome must not pull
in HTTP request-editor coupling just to reuse a table.

End users get no new feature. Maintainers get one shared Key/Value empty-row
editor used by all three protocol surfaces.

**Implementation language**: Python (PyPost desktop client UI).

## User Stories

- As a **maintainer**, I want one shared empty-row Key/Value editor for
  HTTP, WebSocket, and MCP Client Headers, so empty-row and get/set behavior
  is fixed in one place instead of three copies.
- As an **HTTP request user**, I want Params and Headers Key/Value editing
  to keep working as today (trailing empty row, Key/Value columns,
  environment-aware cells), so this cleanup does not change HTTP editing.
- As a **WebSocket user**, I want handshake Params and Headers Key/Value
  editing to keep working as today, including becoming non-editable while
  the connection is open, so connected sessions stay locked as they do now.
- As an **MCP Client user**, I want the Headers table to keep the same
  empty-row Key/Value and environment-aware editing as today, so auth
  headers remain editable without learning a new control.
- As a **maintainer of MCP Client**, I want MCP Client Headers to reuse the
  shared editor without depending on the HTTP request editor, so MCP chrome
  stays decoupled from HTTP request UI.
- As an **end user** of any of these editors, I want no intentional product
  expansion — only consolidation of the existing Key/Value empty-row job.

## Definition of Done

PYPOST-1186 is done when:

1. HTTP request Params/Headers, WebSocket handshake Params/Headers, and MCP
   Client Headers all use one shared empty-row Key/Value editor (same
   trailing empty-row add flow and Key/Value columns).
2. That shared editor remains environment-variable-aware for cell content
   the same way the current tables do (placeholders / hover preview rules
   already expected on these surfaces).
3. Existing user-visible behavior is preserved for each consumer:
   - HTTP Params/Headers: empty-row add, populate from stored pairs, read
     back pairs for send/save — same effective contract as today.
   - WebSocket Params/Headers: same populate / read-back contract as today,
     plus the ability to lock editing while connected.
   - MCP Client Headers: same empty-row add, populate, and read-back
     contract as today (including how keys are normalized when collected).
4. MCP Client Headers does **not** depend on the HTTP request editor module
   or surface to obtain the shared table.
5. Existing automated coverage for HTTP, WebSocket, and MCP Client header /
   key-value editing remains green (or is updated only to follow the shared
   editor without weakening the product contract).
6. No new end-user feature is in scope beyond consolidation and preserving
   the contracts above.
7. Sibling epic work (live Connect / tool browser, invoke, Collections
   persistence, Ctrl+H for MCP, user-doc rewrite) stays out of scope except
   as context.

## Task Description

### Programming Language

Python — PyPost desktop client UI and its automated test suite.

### Problem

Three protocol surfaces need the same Key/Value empty-row editor:

1. HTTP request editor — Params and Headers.
2. WebSocket connection editor — handshake Params and Headers.
3. MCP Client tab — connection Headers.

[PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) deliberately
copied the table for MCP Client rather than importing the HTTP request
editor’s nested table, because MCP Client must not couple to that HTTP
surface. The copy was acceptable for that story; continuing with three
implementations is maintainer debt.

The copies already disagree in details that affect bulk populate, key
normalization when reading rows back, and WebSocket-only read-only while
connected. Without consolidation, every empty-row bugfix or env-aware
tweak risks three slightly different behaviors.

### Business Need

Maintainers need a **single** empty-row Key/Value editor shared by HTTP,
WebSocket, and MCP Client Headers so:

- Empty-row UX and pair get/set stay consistent across protocols.
- Fixes land once.
- MCP Client can reuse the editor **without** depending on the HTTP request
  editor.

End users should see the same editing job they already have; this is
cleanup debt, not a new Headers feature.

### Scope (this task)

**In scope**

- One shared empty-row Key/Value editor used by:
  - HTTP request Params and Headers
  - WebSocket handshake Params and Headers
  - MCP Client Headers
- Preserve each consumer’s existing product contract (empty trailing row,
  Key/Value labels, populate / read-back semantics as used today, WS
  read-only while connected, env-aware cells).
- Keep MCP Client free of a dependency on the HTTP request editor.
- Keep or adapt automated checks so the shared editor does not regress
  those contracts.

**Out of scope**

- New header features (multi-value headers, ordered duplicate keys as a new
  product rule, Ctrl+H for MCP Client).
- Changing Collections persistence of MCP headers (owned by later MCP-TM
  work).
- Live Connect / initialize / `list_tools` / invoke behavior.
- Extracting unrelated shared tab-factory helpers (e.g. insert-before-plus
  / `tabs_presenter` LOC — [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184)).
- Optional GUI hover / execute_outbound widget proofs
  ([PYPOST-1187](https://pypost.atlassian.net/browse/PYPOST-1187)).
- User-facing documentation rewrite for MCP headers.
- Unrelated suite flakes.

### Main Entities (Business Perspective)

- **Empty-row Key/Value editor** — Shared two-column Key/Value table with a
  trailing blank row for adding pairs; environment-aware cell content.
- **HTTP request Params / Headers** — Existing HTTP editor tables that
  collect name/value pairs for the request.
- **WebSocket handshake Params / Headers** — Existing WS connection tables;
  may be locked non-editable while connected.
- **MCP Client Headers** — Connection headers table on the MCP Client tab;
  must stay usable without coupling to the HTTP request editor.
- **Stored pair map** — The name→value map each surface populates into and
  reads back from the table (duplicate names last-wins, as today).

### Functional Requirements

#### FR-1: Shared empty-row Key/Value editor

- FR-1.1 HTTP Params/Headers, WebSocket Params/Headers, and MCP Client
  Headers must all use one shared empty-row Key/Value editor.
- FR-1.2 The shared editor must present Key and Value columns and keep a
  trailing empty row so the user can add another pair by typing in the last
  row.
- FR-1.3 The shared editor must remain environment-variable-aware for cell
  content consistent with current tables on these surfaces.

#### FR-2: Preserve HTTP Params/Headers contract

- FR-2.1 Users can still add, edit, and clear Key/Value rows on HTTP Params
  and Headers with the same empty-row add flow as today.
- FR-2.2 Populating the table from a stored pair map and reading pairs back
  for send/save must keep the same effective HTTP contract as today
  (including how keys and values are accepted when collected).

#### FR-3: Preserve WebSocket Params/Headers contract

- FR-3.1 Users can still add, edit, and clear Key/Value rows on WebSocket
  handshake Params and Headers with the same empty-row add flow as today.
- FR-3.2 Populating and reading back pairs must keep the same effective
  WebSocket contract as today.
- FR-3.3 While a WebSocket connection is open, those tables must still be
  lockable as non-editable; after disconnect they become editable again.

#### FR-4: Preserve MCP Client Headers contract

- FR-4.1 Users can still add, edit, and clear connection headers on the MCP
  Client Headers table with the same empty-row add flow as today.
- FR-4.2 Populating and reading back header pairs must keep the same
  effective MCP Client contract as today (including key normalization when
  collecting rows).

#### FR-5: MCP Client stays decoupled from HTTP request editor

- FR-5.1 MCP Client Headers must obtain the shared empty-row editor without
  depending on the HTTP request editor module or surface.
- FR-5.2 This debt must not introduce a new product requirement that MCP
  Client import or embed HTTP request-editor UI to reuse the table.

#### FR-6: No product expansion

- FR-6.1 This task does not add new header product features beyond
  consolidating the shared empty-row editor.
- FR-6.2 Existing automated coverage for these tables must remain green, or
  be updated only to track the shared editor while preserving the contracts
  above.

### Non-Functional Requirements

- **NFR-1 Consistency:** Empty-row Key/Value UX stays aligned across HTTP,
  WebSocket, and MCP Client after consolidation.
- **NFR-2 Maintainability:** A single shared editor is the place to fix
  empty-row / get-set Key/Value behavior for these three surfaces.
- **NFR-3 Decoupling:** MCP Client Headers remains free of HTTP request
  editor coupling.
- **NFR-4 Regression:** Existing green coverage for HTTP, WS, and MCP
  Client header/key-value editing must not weaken.
- **NFR-5 Time-bounded suite:** Any new or extended checks declare an
  explicit pytest timeout and avoid open-ended waits.
- **NFR-6 Stability:** Checks remain deterministic under parallel
  `make test`.

### Constraints and Assumptions

- Parent epic: [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155).
- Origin: NON-BLOCKER follow-up 4 in
  `ai-tasks/PYPOST-1167/60-tech-debt.md`; Jira
  [PYPOST-1186](https://pypost.atlassian.net/browse/PYPOST-1186).
- Related story: [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167)
  (MCP Client headers + env templating that introduced the third copy).
- Ticketed constraint: do not import the HTTP request editor from MCP
  Client to share the table.
- Implementations already diverge (key strip vs not on collect, bulk
  populate signaling, WebSocket read-only). Consolidation must preserve
  each consumer’s **current** effective contract unless a later product
  decision explicitly unifies them; this debt does not redefine HTTP vs
  MCP key normalization as a new feature.
- Duplicate header names still last-wins in the pair map (same as today).
- This task is maintainer debt, not a new UX feature.

## Q&A

- **Why extract if MCP already has a working Headers table?**
  Three copies drift. PYPOST-1167 accepted a copy to avoid HTTP request
  editor coupling; sharing a neutral empty-row editor closes that debt
  without reintroducing the coupling.
- **Does this change what users see?**
  No intentional new feature. Same empty-row Key/Value job on HTTP, WS, and
  MCP; WS can still lock while connected.
- **Must HTTP, WS, and MCP all normalize keys identically after this?**
  Only if that is already their effective contract. This debt preserves
  each surface’s current collect/populate behavior; unifying strip vs
  non-strip across protocols is not a required product change here.
- **Can MCP Client import the HTTP request editor to reuse its table?**
  No. That dependency was explicitly rejected when MCP Headers shipped.
- **Is Ctrl+H for MCP Client Headers in scope?**
  No. That remains out of scope (noted in PYPOST-1167 debt).
- **Is tabs_presenter LOC / insert-before-plus extraction in scope?**
  No. That is [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184).

## References

- [PYPOST-1186](https://pypost.atlassian.net/browse/PYPOST-1186) — this
  debt item
- [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) — MCP
  Client headers + env templating (source story)
- [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) — parent
  epic
- [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184) —
  related presenter capacity / shared factory debt (out of scope)
- [PYPOST-1187](https://pypost.atlassian.net/browse/PYPOST-1187) —
  related optional GUI proofs (out of scope)
- `ai-tasks/PYPOST-1167/60-tech-debt.md` — follow-up 4 (source)
- `ai-tasks/PYPOST-1167/10-requirements.md` — MCP headers business contract
