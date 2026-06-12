# PYPOST-80: Remove Trailing Whitespace in http_client.py

## Goals

Close tech-debt item TD-1 from PYPOST-45: `pypost/core/http_client.py` must comply with
project file-handling rules (no trailing whitespace on any line). Clean style reduces noise in
diffs and keeps the codebase consistent with `.cursor/rules/files.mdc`.

## User Stories

- As a **contributor**, I want HTTP client source lines to have no trailing spaces so reviews
  focus on behavior, not incidental whitespace.
- As a **maintainer**, I want PYPOST-45 style debt tracked in Jira to be closed when the file
  is verified clean.

## Definition of Done

- Every line in `pypost/core/http_client.py` has no trailing spaces or tabs.
- Existing HTTP client tests pass.
- TD-1 from `ai-tasks/PYPOST-45/60-review.md` is marked resolved.

## Task Description

**Origin:** PYPOST-45 TD-1 — trailing whitespace in `http_client.py` (reported at lines 34,
51, and 57 in the review snapshot).

**Scope:** `pypost/core/http_client.py` only. No behavioral changes to HTTP transport.

## Q&A

| Question | Answer |
| --- | --- |
| Were lines already clean? | Yes — automated scan found zero trailing-whitespace lines at task execution. |
| Is a code edit required? | Only if violations are found; verification satisfies DoD when file is clean. |
