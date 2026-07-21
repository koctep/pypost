# PYPOST-878: Wire worker_operation into env gateway timeout detail

## Goals

When automated environment-storage gateway waits time out, maintainers need to
tell whether the stuck work was a **load** or a **save**. Today the timeout
diagnostic formatter can show that distinction, but live gateway timeout text
never includes it. Closing that gap speeds triage of load-vs-save flakes
without changing product behavior for end users.

Collection storage is load-only and does not need an operation label on timeout.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want environment gateway timeout messages to show
  whether the active worker was loading or saving when present, so I can
  triage async storage timeouts faster.
- As a **maintainer**, I want collection gateway timeouts to stay free of a
  misleading operation field, because those workers only load.
- As a **contributor**, I want existing busy/pending/worker_running timeout
  diagnostics and hang-resistant waits to keep working unchanged, so this
  polish does not regress PYPOST-828 harness behavior.
- As a **desktop user** (indirect), I want no change to environment load/save
  UX or persistence; this work is test-harness diagnostics only.

## Definition of Done

- When an environment gateway wait times out and a worker with a known
  operation (load or save) is attached, the timeout detail text includes that
  operation.
- When the worker has no operation attribute (collection / load-only style),
  timeout detail omits the operation field.
- Existing busy/pending and optional worker_running fields remain present and
  correct for gateway waits.
- Automated regression coverage proves the env load/save distinction appears
  and the collection-style omission holds.
- No intentional change to product storage behavior, encryption, or
  user-visible persistence UX.
- Task artifacts for Steps 1–8 exist.

## Task Description

**Problem:** After PYPOST-828, `format_storage_async_timeout_detail` accepts
`worker_operation`, and unit tests cover the formatter. Live
`gateway_timeout_detail` never passes that field. Environment workers already
expose load vs save via `_operation`; collection workers do not. Source:
[PYPOST-878](https://pypost.atlassian.net/browse/PYPOST-878), follow-up from
[PYPOST-828](https://pypost.atlassian.net/browse/PYPOST-828) TD-1
(`ai-tasks/PYPOST-828/60-tech-debt.md`).

**Business need:** Improve load-vs-save triage on environment gateway timeout
failures in CI and local runs. Leave collection load-only waits without the
field so messages stay accurate.

**Out of scope:** Changing worker public APIs beyond what diagnostics need;
extracting shared worker-only helpers (tracked separately); full-suite
`make check` noise cleanup; product UX or storage format changes.

## Constraints and Assumptions

- Harness-only change under `tests/helpers` (and docs); no production
  runtime behavior change for the desktop app.
- Environment workers continue to distinguish load vs save; collection
  workers remain load-only without an operation attribute.
- Duck-typed gateway snapshot remains acceptable (same pattern as
  PYPOST-828).

## Main Entities (business view)

- **Timeout detail** — short snapshot appended when a wait fails.
- **Environment gateway wait** — wait that may be stuck on load or save.
- **Collection gateway wait** — wait that is load-only; no operation label.
- **Worker operation** — load or save label when the worker exposes it.

## Q&A

| Q | A |
| --- | --- |
| Why wire this if busy/pending already exist? | Busy/pending show congestion, not whether the active op was load or save. |
| Why omit for collection? | Collection workers have no load/save operation attribute; inventing one would mislead. |
| User-facing change? | No — diagnostics for automated waits only. |
| Source debt item? | PYPOST-828 TD-1 → PYPOST-878. |
