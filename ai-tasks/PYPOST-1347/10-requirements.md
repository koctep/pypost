# PYPOST-1347: Library MCP rows keep running through lifecycle refreshes

## Goals

Ordinary (non-Built-in) library MCP servers must remain operational when the user refreshes
workspace collections, edits selected environments, or reconfigures a running server — with the
same resolved variables they would receive on a fresh start.

From a business perspective, users who connect MCP servers from an external library expect those
servers to behave as first-class, durable endpoints:
- A running library server must not stop merely because workspace collection membership changed or
  because an unrelated configuration dialog (such as Environment Manager) closed.
- Reconfiguring a running library server must succeed when the library connection, library
  collection, and selected environment remain valid.
- When the user updates workspace environment variables that a library server uses, the running
  server must refresh to the same complete variable set a fresh start would produce — including
  library manifest defaults, the active preset, and library overlay values — not a raw replacement
  that drops those contributions.
- A library server stops with clear diagnostics only when its library collection or selected
  environment is genuinely missing or unavailable.
- Workspace MCP servers and Built-in MCP servers retain their existing lifecycle behavior
  (Built-in stability is owned by PYPOST-1352).

This debt was found while designing epic PYPOST-1335. It is a pre-existing defect of ordinary
library rows, outside the epic (E8 leaves existing rows unchanged there). Related notes live in
`ai-tasks/PYPOST-1335/decomposition.md`.

## Implementation Language

- Python

## User Stories

- As an MCP server user, I want my running ordinary library MCP server to stay running when
  workspace collections are refreshed or when the Environment Manager closes, so that unrelated
  workspace activity does not interrupt my library tools.
- As an MCP server user, I want my running ordinary library MCP server to stop with clear
  diagnostics only when its library collection or selected environment is actually missing, so that
  I can trust stop reasons.
- As an MCP server user, I want to reconfigure a running ordinary library MCP server without failure
  when the library connection, collection, and environment remain valid, so that I can adjust
  settings without restarting from scratch.
- As an MCP server user, I want environment updates applied to a running ordinary library MCP
  server to match a fresh start — preserving manifest defaults, the active preset, and overlay
  values — so that required library parameters remain complete after I edit workspace variables.
- As a product maintainer, I want workspace MCP server lifecycle behavior unchanged, so that this
  fix does not regress existing workspace workflows.
- As a product maintainer, I want Built-in MCP server lifecycle behavior left to PYPOST-1352, so
  that ordinary library fixes do not reopen Built-in scope.

## Definition of Done

1. **Lifecycle stability for ordinary library servers**:
   - A running ordinary library MCP server stays running after reference reconciliation, whether or
     not a workspace collection-validity set is supplied.
   - The server is stopped only when its library collection or selected environment is genuinely
     missing or unavailable — not because it lacks a workspace collection identity.

2. **Reconfiguration succeeds**:
   - Reconfiguring a running ordinary library MCP server succeeds when the library connection,
     library collection, and selected environment remain valid.

3. **Environment refresh matches fresh start**:
   - After an environment refresh, the running ordinary library server’s resolved variables equal
     what a fresh start would produce for the same configuration (manifest defaults, active preset,
     and overlay values preserved).

4. **Backward compatibility**:
   - Workspace MCP server lifecycle behavior is unchanged (existing workspace tests remain green
     without assertion edits).
   - Built-in MCP server lifecycle behavior remains owned by PYPOST-1352 and is out of scope here.

5. **Quality gate verification**:
   - Automated red regression tests reproduce each defect before the fix is applied.
   - The combined quality gate (`make check`) passes after the fix.

## Task Description

This Debt restores correct runtime lifecycle handling for ordinary (non-Built-in) library MCP
server endpoints in the desktop application.

### Business Problem and Context

Users can run MCP servers sourced from a connected library. Those ordinary library servers are
distinct from workspace-defined servers and from Built-in (curated bundle) servers.

Today, ordinary library servers are treated as if they were workspace servers during lifecycle
checks and updates:
- Collection refreshes and Environment Manager dismissal incorrectly stop running library servers
  with a “missing collection” style failure, even when the library collection still resolves.
- Reconfiguration of a running library server fails even though the library connection and
  environment remain valid.
- Refreshing environment variables replaces the running snapshot with raw workspace environment
  values, dropping library-contributed defaults, preset values, and overlay values that a fresh
  start would include.

Users therefore lose tools mid-session, cannot reconfigure without disruption, and see incomplete
configuration after routine environment edits.

### Scope In

- Keep ordinary library MCP servers running across workspace collection synchronization and
  unrelated dialog closures when the library connection, library collection, and environment remain
  valid.
- Allow reconfiguration of running ordinary library MCP servers under those same validity rules.
- Refresh running ordinary library environment snapshots so they match fresh-start resolution
  (manifest defaults, active preset, overlay contributions).
- Stop ordinary library servers with clear diagnostics only when the library collection or
  environment is genuinely missing or unavailable.
- Prefer consistent lifecycle rules with the already-delivered Built-in handling (PYPOST-1352)
  where business validity overlaps, without changing Built-in product behavior.

### Scope Out

- Built-in MCP server lifecycle and persistence (PYPOST-1352).
- Changes to workspace MCP server lifecycle behavior.
- Migration or rewrite of persisted MCP server settings.
- User-interface changes to the MCP Servers dialog, badges, or source selectors.
- New library connection or collection-authoring features.

### Constraints and Assumptions

- Implementation language is Python.
- Ordinary library servers are identified as library-sourced, non-Built-in endpoints (they are not
  workspace collection rows).
- PYPOST-1352 may already provide Built-in lifecycle handling; this task must not regress Built-in
  or workspace behavior.
- No persisted settings schema migration is required or allowed.
- Verification uses the repository Make quality gate (`make check`).

### Main Domain Entities

- **Ordinary Library MCP Server Endpoint**: A user-configured MCP server sourced from a connected
  library (not Built-in, not a workspace collection row).
- **Connected Library**: An external library the user has linked; supplies collections and related
  runtime contributions (manifest defaults, presets, overlays).
- **Library Collection**: The collection entry within a connected library that defines the
  server’s tools and declared defaults.
- **Workspace Environment**: User-defined environment variable set selected by the server for
  instance-specific overrides.
- **Resolved Environment Snapshot**: The complete variable set active in a running server after
  combining library contributions with the selected workspace environment — equivalent to a fresh
  start for the same configuration.
- **Workspace MCP Server Endpoint**: A server tied to a workspace collection; lifecycle behavior
  must remain unchanged by this task.
- **Built-in MCP Server Endpoint**: A curated, shipped integration whose lifecycle is owned by
  PYPOST-1352.

## Q&A

- **Why is this separate from epic PYPOST-1335 / Built-in work (PYPOST-1352)?**
  Epic E8 leaves existing MCP rows unchanged inside the Built-in feature work. Ordinary library
  lifecycle failures are a pre-existing defect and are tracked as independent Debt so Built-in
  delivery is not blocked and library fixes stay explicitly scoped.
- **Why must environment refresh match a fresh start?**
  Library servers depend on more than raw workspace variables: manifest defaults, the active
  preset, and overlay values complete the configuration. Replacing the snapshot with workspace
  variables alone silently drops those contributions and can leave the server incomplete.
- **When should an ordinary library server be stopped?**
  Only when the library connection or collection no longer resolves, or the selected workspace
  environment is missing — not because the server lacks a workspace collection identity.
- **Why must workspace behavior stay unchanged?**
  Workspace servers are the established baseline. This Debt restores correct library handling
  without rewriting workspace rules or forcing test-expectation churn.
- **How does this relate to PYPOST-1352?**
  PYPOST-1352 delivers Built-in lifecycle stability. Where ordinary library validity rules overlap
  with that Built-in handling, this task should stay consistent with that product behavior rather
  than inventing divergent stop/refresh rules for library users.
