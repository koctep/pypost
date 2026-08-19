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
  names, default ports, hotkeys).
- Prefer progressive disclosure: user-level steps in `doc/user/`; deep MCP
  envelopes and scrape setup stay in the integration docs; implementation
  detail stays in `doc/dev/`.
- Update the numbered TOC in `doc/user/README.md` if you add or remove a
  topic page (product/docs decision, not a drive-by rename).
- Keep collections/environments import-export guidance consistent with the
  corresponding capability pages in `doc/dev/` when both exist.

Capability work that changes user-visible behavior should update the relevant
`doc/user/` page in the same change set (or a linked docs follow-up), not only
`doc/dev/`.

## Docs accuracy-drift checklist (PYPOST-1023)

Whenever code changes alter UI elements, default configurations, or shortcuts, engineers
and reviewers must execute this accuracy-drift checklist before merging:

### 1. Trigger events & ownership

- **Owner:** The engineer implementing the UI / defaults change is responsible for updating
  documentation in the same change set; the reviewer validates accuracy during code review.
- **Triggers:**
  - UI label changes (menu items, button text, dialog titles, tab labels, form field labels).
  - Default value changes (ports, timeouts, retry policies, format preferences).
  - Shortcut / hotkey alterations or additions.
  - New or altered workflow steps (import/export formats, authentication flows).

### 2. UI-to-docs topic mapping

Identify which User Guide pages correspond to the modified components:

| Modified component | User Guide topic page | Key items to inspect |
| --- | --- | --- |
| Menu bar / main window layout | [`doc/user/interface.md`](../user/interface.md) | Panes, menu names, status bar elements |
| Request builder / headers / params | [`doc/user/requests.md`](../user/requests.md) | Tabs, methods, send buttons, URL format |
| Collections tree & context menus | [`doc/user/collections.md`](../user/collections.md) | Import/export menus, folder actions |
| Environment manager & variables | [`doc/user/environments.md`](../user/environments.md) | Hidden variables, active selection |
| Template syntax / functions | [`doc/user/templating.md`](../user/templating.md) | Built-in functions, variable evaluation |
| Scripts & test assertion helpers | [`doc/user/scripts.md`](../user/scripts.md) | Post-response variables, assertions |
| History panel & cURL copy | [`doc/user/history-and-curl.md`](../user/history-and-curl.md) | Re-send actions, cURL formatting |
| MCP tools & servers | [`doc/user/mcp-tools.md`](../user/mcp-tools.md) | Server setup dialog, exposed tools |
| Settings dialog & defaults | [`doc/user/settings.md`](../user/settings.md) | Setting labels, default values, tabs |
| Hotkeys dialog / keybindings | [`doc/user/hotkeys.md`](../user/hotkeys.md) | Key combinations, action names |
| Multi-step procedures | [`doc/user/workflows.md`](../user/workflows.md) | End-to-end task sequences |

### 3. Verification checklist

- [ ] **Exact string match:** Documented button, menu, and dialog names match Qt UI text verbatim.
- [ ] **Defaults consistency:** Stated defaults (e.g. port 8000, 30s timeout) match runtime defaults.
- [ ] **Hotkeys verified:** Shortcut descriptions match `QKeySequence` bindings in code and in-app Help.
- [ ] **Formatting check:** Run `make lint-docs` (verifies line length ≤100, ATX headers, no trailing WS).
- [ ] **Link resolution:** Run `make check-docs-links` (verifies all relative links and anchor slugs).
- [ ] **Developer docs alignment:** Update corresponding `doc/dev/` capability notes if applicable.

## Related

- [Documentation hub](../README.md)
- [User Guide](../user/README.md)
- [Architecture overview](architecture.md)
- [Documentation audit (PYPOST-690)](documentation_audit.md)
