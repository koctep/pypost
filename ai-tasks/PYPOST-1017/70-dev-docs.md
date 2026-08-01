# PYPOST-1017 — Developer Documentation

## Summary

Step 8 does **not** add a new `doc/dev/` feature page. This story ships
importable JSON under `examples/` plus discoverability docs
(`examples/README.md`, User Guide pointers). Application import/export
runtime is unchanged. Developers only need a brief pointer to the fixture
roles and the green contract test location.

## Changes

| File | Update |
| ---- | ------ |
| `doc/dev/testing.md` | Clarify `mcp.json` vs Jira pair; add PYPOST-1017 contract section |
| New `doc/dev/` pages | N/A — fixture hub remains `examples/README.md` |

The `doc/dev/testing.md` section covers Overview, Architecture (artifact
roles), Usage (focused pytest), Configuration (placeholders / no secrets),
and Troubleshooting. Detail for import order stays in `examples/README.md`.

## Components

| Doc | Audience | Coverage |
| --- | -------- | -------- |
| `examples/README.md` | Users / contributors | Inventory, import order, secrets |
| `doc/user/collections.md` | End users | Example fixtures pointer (Step 4) |
| `doc/user/environments.md` | End users | Example fixtures pointer (Step 4) |
| `doc/dev/testing.md` | Developers | Contract test + role distinction |

## Worklog

tokens_used: 6500
role: execution
step: 8
step_name: Dev Docs
