# PYPOST-802: Shared type alias for ResolvedRequestFields and MaskedRequestData

## Goals

PYPOST-63 introduced transport-level resolved request fields and history-safe masked request
data as separate frozen dataclasses with identical shape (url, headers, body). Maintaining two
structurally identical types increases duplication and drift risk. This debt task consolidates
them under one canonical type with semantic aliases — a pure refactor with no behavior change.

## User Stories

- As a maintainer, I want a single canonical request-fields type, so that URL/header/body shape
  changes happen in one place.
- As a developer reading transport vs masking code, I want semantic type names
  (`ResolvedRequestFields`, `MaskedRequestData`) preserved, so that intent stays clear at call
  sites without duplicate class definitions.

## Definition of Done

- One canonical frozen dataclass holds url, headers, and body.
- `ResolvedRequestFields` and `MaskedRequestData` are type aliases to that dataclass.
- Existing import paths and call sites continue to work without behavior changes.
- Full test suite passes (`make check`).

## Task Description

Follow-up from PYPOST-63 tech debt (TD-1). Scope is limited to type consolidation — no changes
to rendering, masking rules, history flow, or public API behavior.

Implementation: Python (PyPost core).

## Q&A

- **Q**: Should tests import the canonical type directly?
- **A**: No requirement — existing imports from `http_client` remain valid via re-export alias.
- **Q**: Is this a breaking change for external consumers?
- **A**: No — alias names and module locations for public imports are preserved.
