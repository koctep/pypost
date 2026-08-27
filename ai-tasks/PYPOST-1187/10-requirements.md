# PYPOST-1187: GUI proof of MCP Client Headers → outbound send and hidden-key hover

## Goals

[PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) shipped an MCP
Client **Headers** table and wired resolved headers into outbound
`execute_outbound` / `run(..., headers=)`. Automated coverage today builds
connection data in memory or seeds headers on the draft model — it does not
prove that **editing the live Headers table** is what the outbound path
sends. Hidden-key hover masking on that table is also unasserted, even though
env fan-out already pushes `hidden_keys` onto the widgets.

Maintainers need a hermetic GUI regression signal so a future break in
table → presenter sync or secret hover masking fails CI before auth headers
silently drop or secrets leak in tooltips.

End users get no new feature. This debt closes a verification gap called out
in [`ai-tasks/PYPOST-1167/60-tech-debt.md`](../PYPOST-1167/60-tech-debt.md)
item 5 ([PYPOST-1187](https://pypost.atlassian.net/browse/PYPOST-1187)).

**Implementation language**: Python (PyPost desktop client automated tests).

## User Stories

- As a **maintainer**, I want a GUI test that types into the MCP Client
  Headers table and then runs `execute_outbound`, so I know outbound
  `run(..., headers=)` reflects widget data — not only a pre-built
  connection model.
- As a **maintainer of secret-safe editors**, I want an optional hermetic
  assertion that hovering a Headers cell with a hidden env placeholder shows
  masked `********` (not the secret value), so masking on
  `pypost_mcp_client_headers_table` cannot regress unnoticed.
- As a **CI owner**, I want those checks to stay off the network and keep an
  explicit pytest timeout, so the suite stays hermetic and bounded.
- As an **MCP Client user**, I want no intentional product change — only
  stronger proof that Headers editing and secret hover already behave as
  shipped.

## Definition of Done

PYPOST-1187 is done when:

1. An automated GUI test edits the MCP Client Headers table (widget id
   `pypost_mcp_client_headers_table`), then drives `execute_outbound` (or
   the equivalent outbound path under test), and asserts that
   `run(..., headers=)` contains the headers read from that table after
   environment resolution as applicable.
2. An automated check (same module or companion) covers hidden-key hover
   masking on that Headers table: resolved hover text shows `********` and
   does not reveal the secret value for a hidden environment key.
3. Tests use the existing module `pytestmark` timeout (or an explicit
   equivalent) and do not open a live network session.
4. Existing MCP Client tab / presenter coverage remains green.
5. No new end-user chrome, Connect/invoke behavior, or Collections work is
   in scope beyond verification.

## Task Description

### Programming Language

Python — PyPost desktop GUI tests (PySide6 / offscreen Qt).

### Problem

PYPOST-1167 added Headers UI and outbound header forwarding. Coverage gaps
remain:

1. Presenter tests construct `McpClientConnection(headers=...)` without a
   live tab; they do not type into the Headers table.
2. Tab tests assert empty-row UX and Connect with headers seeded on the
   draft — they do not lock the full **edit table → `execute_outbound` →
   `run(..., headers=)`** path from widget data.
3. Hover / hidden-key `********` on
   `pypost_mcp_client_headers_table` was left optional and unasserted.

Without those proofs, a regression in `_sync_fields_from_tab`, table
`get_data`, or VariableAware hover masking can ship without failing CI.

### Business Need

Maintainers need hermetic GUI regression coverage so:

- Auth headers typed in the MCP Client Headers table continue to reach
  outbound `run`.
- Hidden environment values stay masked in Headers hover preview.

### Scope (this task)

**In scope**

- Hermetic GUI test(s) in the MCP Client tab suite (preferred:
  `tests/test_mcp_client_tab.py`) that:
  - Edit `pypost_mcp_client_headers_table`
  - Call `execute_outbound` (injected mock client; no network)
  - Assert `run(..., headers=)` matches resolved widget-backed headers
- Optional but expected: hidden-key hover `********` assertion on that table
- Keep explicit timeout; no live MCP server

**Out of scope**

- New Headers UI or product feature work (unless a red proof exposes a real
  defect — then restore the shipped contract only)
- Live Connect / invoke / Collections persistence polish
- Shared table extraction (already PYPOST-1186)
- User-facing docs rewrite
- Fixing unrelated suite flakes

### Constraints and Assumptions

- Offscreen Qt / existing `qapp` fixture; no display server required.
- Injected mock `mcp_client` (or equivalent) — never hit a real network.
- Module already declares `pytestmark = pytest.mark.timeout(30)`.
- Product Headers + resolve + hover masking already ship; this is
  verification debt. Green-on-first-run is acceptable if the contract holds.
- [PYPOST-1186](https://pypost.atlassian.net/browse/PYPOST-1186) extracted
  `EmptyRowKeyValueTable`; MCP Headers remains a thin wrapper — tests target
  the MCP Client table id, not the shared base alone.

### Main Entities (business)

- **MCP Client Headers table** — editable connection headers on the draft.
- **Outbound send path** — resolves env placeholders and passes headers to
  the MCP client `run` call.
- **Hidden environment keys** — secrets that must show as `********` in
  hover preview, not plaintext.

## Q&A

| Question | Answer |
| --- | --- |
| Why not only presenter unit tests? | They skip live table widgets; debt item 5 specifically asks for GUI edit → outbound proof. |
| Is hover required or optional? | Jira says optional; DoD includes it because it is cheap with existing `_resolve_cell_hover` patterns and closes the stated gap. |
| Production changes? | None expected unless Step 3 proves a real wiring/masking defect. |
| Source of truth for the gap? | `ai-tasks/PYPOST-1167/60-tech-debt.md` item 5. |
