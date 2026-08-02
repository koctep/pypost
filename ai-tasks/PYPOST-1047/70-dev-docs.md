# PYPOST-1047 — Developer Documentation

## Summary

Step 8 does **not** add a new `doc/dev/` feature page. This story extends the
curated jira-mcp fixtures (delete sprint + lock backlog move as
remove-from-sprint) and companion docs/tests. Application MCP runtime is
unchanged. Developers need the contract section and agent-facing API notes in
`doc/dev/testing.md`, plus the reader inventory in `examples/README.md`.

## Changes

| File | Update |
| ---- | ------ |
| `doc/dev/testing.md` | PYPOST-1047 contract (floor ≥22, locked ids); agent-facing API for `jira_delete_sprint` / `jira_move_issues_to_backlog`; troubleshooting |
| `doc/dev/README.md` | TOC anchor includes PYPOST-1047 fixtures section (Step 5) |
| `examples/README.md` | Inventory 22 tools; sprint delete + membership / remove-from-sprint note |
| New `doc/dev/` pages | N/A — fixture hub remains `examples/README.md` |

The `doc/dev/testing.md` section covers Overview, Architecture (artifact
roles), Coverage, Agent-facing API, Usage (focused pytest), Configuration
(placeholders / no secrets), and Troubleshooting.

## Components

| Doc | Audience | Coverage |
| --- | -------- | -------- |
| `examples/README.md` | Users / contributors | Inventory, import order, coverage vs gaps |
| `doc/dev/testing.md` | Developers | Contract + MCP tool names/params for sprint hygiene |
| `doc/dev/README.md` | Developers | TOC pointer to fixtures contract |
| `doc/user/collections.md` | End users | Points at examples pair (no tool inventory) |

## Agent-facing tools (PYPOST-1047)

| Request id | MCP tool | Role |
| ---------- | -------- | ---- |
| `jira-delete-sprint` | `jira_delete_sprint` | Delete sprint (irreversible) |
| `jira-move-issues-to-backlog` | `jira_move_issues_to_backlog` | Remove-from-sprint path |

## Worklog

tokens_used: 28000
role: execution
step: 8
step_name: Dev Docs
