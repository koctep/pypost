# PYPOST-151: Add validation for Host and Port fields in SettingsDialog

## Goals

Operators configure MCP and metrics server bind addresses in Settings. Invalid host values
cause servers to fail at startup with log errors that are hard to connect to the settings
form. This task gives immediate, in-dialog feedback when host or port values are invalid,
closing the gap documented in PYPOST-19 technical debt (PYPOST-149).

## User Stories

- As an **operator**, I want invalid MCP or metrics host values rejected on Save so I know
  how to fix them before restarting servers.
- As an **operator**, I want port values outside the allowed range rejected with a clear
  message (defense in depth beyond spinbox limits).
- As a **maintainer**, I want validation covered by automated tests in CI.

## Definition of Done

1. Save is blocked when MCP Server Host or Metrics Server Host is empty or not a valid IP
   or hostname.
2. Save is blocked when MCP Server Port or Metrics Server Port is outside 1024–65535.
3. A warning dialog explains the problem; settings are not persisted.
4. Valid addresses (e.g. `127.0.0.1`, `0.0.0.0`, `localhost`, FQDNs) save successfully.
5. Unit tests cover the validator; Qt tests cover blocked and successful save paths.
6. Developer documentation updated.

## Task Description

Follow-up from [PYPOST-19](https://pypost.atlassian.net/browse/PYPOST-19) tech debt.
Implements the mitigation noted in [PYPOST-149](https://pypost.atlassian.net/browse/PYPOST-149).

**Scope:** `SettingsDialog` MCP and metrics host/port fields only.

**Out of scope:** Runtime server bind verification, duplicate port conflict detection,
changing default values.

## Programming language

Python — PySide6 UI, pytest offscreen tests.

## Q&A

| Question | Answer |
| -------- | ------ |
| Does this close PYPOST-149? | Yes — same root cause (missing host validation). |
| IPv6? | Accepted when `ipaddress` recognizes the literal. |
