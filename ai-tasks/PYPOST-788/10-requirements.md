# PYPOST-788: Refresh setup.md dependency list

## Goals

Developers reading `doc/dev/setup.md` see only five of eleven direct production packages under
"Key Dependencies", which misrepresents what `make install` pulls in. This task closes audit finding
**R-P3-004** from PYPOST-691 by aligning setup guidance with the current production inventory.

## User Stories

- As a **new contributor**, I want setup docs to list or reference all production packages so I
  understand the runtime stack after `make install`.
- As a **maintainer**, I want a single authoritative inventory (`dependencies_audit.md`) linked
  from setup docs so future dependency changes need one table update.

## Definition of Done

- [x] `doc/dev/setup.md` no longer lists only five production packages.
- [x] Setup docs cover all direct production deps from `requirements.in` or link to the
  `dependencies_audit.md` inventory table.
- [x] MCP stack and encryption packages (`mcp`, `cryptography`, `keyring`) are mentioned.
- [x] `make check` passes.

## Task Description

**Source:** PYPOST-691 dependency audit — R-P3-004.

**Scope:** `doc/dev/setup.md`, cross-reference to `doc/dev/dependencies_audit.md`.

**Out of scope:** Changing `requirements.in`, lock files, or CI install paths.

**Constraints:**

- Documentation-only; no application code changes.
- Keep setup.md readable — prefer a summary table plus link over duplicating full audit prose.

## Q&A

- **Expand inline or link?** Use a concise production summary table in setup.md and link to
  `dependencies_audit.md` for pinned versions and audit context.
- **Why not duplicate the full audit table?** `dependencies_audit.md` is the version-pinned source
  of truth; setup.md summarizes roles for onboarding.
