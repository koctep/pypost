# User Guide and Documentation Layout

## Overview

PyPost ships a structured **User Guide** for end users under `doc/user/`.
Developer documentation stays in `doc/dev/`. The documentation hub is
[`doc/README.md`](../README.md).

The guide was completed and wired into the docs hub and root README in
[PYPOST-1015](https://pypost.atlassian.net/browse/PYPOST-1015).

## Documentation layout

| Path | Audience | Role |
| --- | --- | --- |
| [`doc/README.md`](../README.md) | All | Hub: user vs integration vs developer |
| [`doc/user/`](../user/README.md) | End users | Topic-based User Guide + index |
| [`doc/mcp_integration.md`](../mcp_integration.md) | Integrators | MCP transport / tool reference |
| [`prometheus_monitoring.md`](../prometheus_monitoring.md) | Operators | Metrics scrape reference |
| [`doc/dev/`](README.md) | Developers | Setup, architecture, capability notes |
| [`doc/adr/`](../adr/README.md) | Developers | Architecture Decision Records |

**Entry points:** the root project README Documentation section and
`doc/README.md` both link to the [User Guide index](../user/README.md).

Integration docs (MCP, Prometheus) remain top-level under `doc/`. The User
Guide links out to them for depth; it does not replace them.

## User Guide structure

Index: [`doc/user/README.md`](../user/README.md)

Fixed topic set (numbered TOC on the index):

1. Getting Started
2. Interface
3. Working with Requests
4. Collections
5. Environments
6. Templating
7. Post-Request Scripts
8. History and Copy cURL
9. MCP Tools for AI Agents
10. Settings
11. Hotkeys
12. Common Workflows

Do not invent a parallel topic list or Diátaxis folder redesign without an
explicit documentation story. Apply tutorial / how-to / reference *roles*
inside the existing pages.

## Maintaining the User Guide

When editing `doc/user/` (or the docs hub links):

- Follow [`.cursor/lsr/do-markdown.md`](../../.cursor/lsr/do-markdown.md):
  ATX headers, hyphen (`-`) lists, line length ≤100, UTF-8 LF, no trailing
  whitespace, fenced code with a language tag, clear link text.
- Keep steps and labels accurate against the **current** UI (menus, Settings
  names, default ports, hotkeys). There is no automated docs-contract check.
- Prefer progressive disclosure: user-level steps in `doc/user/`; deep MCP
  envelopes and scrape setup stay in the integration docs; implementation
  detail stays in `doc/dev/`.
- Update the numbered TOC in `doc/user/README.md` if you add or remove a
  topic page (product/docs decision, not a drive-by rename).
- Keep collections/environments import-export guidance consistent with the
  corresponding capability pages in `doc/dev/` when both exist.
- When a UI or defaults change ships, re-read the affected guide pages (label
  and default drift is the main ongoing risk).

Capability work that changes user-visible behavior should update the relevant
`doc/user/` page in the same change set (or a linked docs follow-up), not only
`doc/dev/`.

## Related

- [Documentation hub](../README.md)
- [User Guide](../user/README.md)
- [Architecture overview](architecture.md)
- [Documentation audit (PYPOST-690)](documentation_audit.md)
