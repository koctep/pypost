# Static Type Checking (mypy)

## Overview

PyPost runs optional [mypy](https://mypy.readthedocs.io/) static analysis on **`pypost/core/`**,
**`pypost/models/`**, and **`pypost/ui/`** — domain, persistence, and Qt presentation layers.
Checker settings live in root `pyproject.toml` under `[tool.mypy]`; the authoritative checked path
prefixes live in `scripts/check_mypy_baseline.py` as `MYPY_PATHS`. Known errors are frozen in
`mypy-baseline.json`; `make typecheck` compares current findings with that committed baseline and
blocks unreviewed type-regression drift.

## Quick Start

```bash
make install      # editable install with [dev] extra (includes mypy)
make typecheck    # mypy + baseline gate (optional; not part of make check)
make lint         # repository lint checks
make verify-ai-tasks  # workflow artifact integrity
```

The current gate passes with 180 known errors. These are pre-existing baseline diagnostics; they do
not fail the gate while the current `(path, code, message)` multiset matches the committed baseline:

```text
mypy baseline OK (180 known errors in pypost/core, pypost/models, pypost/ui)
```

To see raw mypy output (including all known baseline errors):

```bash
.venv/bin/mypy pypost/core pypost/models pypost/ui --show-error-codes
```

## Architecture

| File | Role |
| --- | --- |
| `pyproject.toml` `[tool.mypy]` | Checker settings |
| `mypy-baseline.json` | Version 2 frozen `(path, code, message)` error records |
| `scripts/check_mypy_baseline.py` `MYPY_PATHS` | Authoritative checked path prefixes |
| `scripts/check_mypy_baseline.py` | Runs mypy, parses diagnostics, and compares the baseline |
| `tests/test_mypy_baseline_live.py` | Live pytest gate enforcing zero new and zero fixed baseline errors |
| `Makefile` `typecheck` | Developer entry point |

The baseline scope is exactly the three directory prefixes in
`MYPY_PATHS = ("pypost/core", "pypost/models", "pypost/ui")`. The JSON `scope` field and the
diagnostic parser use this same tuple; errors outside these directories are not baseline keys.

### Configuring checked paths

`MYPY_PATHS` drives the mypy invocation, baseline scope metadata, successful-run message, and
accepted diagnostic path prefixes. To extend coverage, add the repository-relative directory
prefix to `MYPY_PATHS` without a trailing slash. Do not edit `_ERROR_RE` or maintain a second path
list.

At module import, the gate escapes each configured prefix for literal regular-expression matching
and orders overlapping prefixes longest-first. The parser requires a literal slash immediately
after the selected prefix, so configuring `pypost/agent` accepts `pypost/agent/module.py` but not
the sibling path `pypost/agent_extra/module.py`.

### Typing Qt signals and thread lifecycle

Treat every custom Qt signal declaration as a runtime payload contract:

- Use concrete payload classes whenever the signal always emits one runtime family, such as
  `Signal(dict)`, `Signal(list)`, or `Signal(ResponseData)`.
- Do not shadow a native Qt lifecycle signal with a custom payload signal. In particular, a
  `QThread` subclass must preserve zero-argument `QThread.finished()` for termination handling and
  use a distinct name such as `request_finished` for response delivery.
- Connect thread cleanup, such as `deleteLater()`, to native `QThread.finished()` rather than to a
  success or error payload signal. Native termination occurs on every exit path.
- For a genuine optional union that Qt cannot express as one signal type, declare an `object`
  boundary and validate it immediately in the receiver. Accept only the documented types; reject
  anything else with a type-only warning that does not interpolate or stringify the payload.

Keep the connected callback annotation at least as precise as the validated value. Do not use a
broad `object` declaration when one concrete payload class describes every live emission.

### Baseline gate behavior

1. Run mypy on exactly `pypost/core`, `pypost/models`, and `pypost/ui`, preserving the tuple's
   configured order.
2. Parse errors into `(path, code, message)` keys — **not** `path:line:code`. The line number is
   parsed too, but only for display in the "new errors" report; it is deliberately excluded from
   the comparison key because it shifts whenever unrelated code moves above an error (an import
   added/removed/reordered, a docstring edited), which made line-keyed baselines flag phantom
   regressions on every reorder. PYPOST-987 hit this directly: ~30 phantom "new"/"fixed" pairs
   from pure line drift buried the one real regression in that run's mypy diff. Dropping the line
   removes that churn while keeping enough specificity to tell errors apart, since mypy's message
   text usually names the specific attribute/argument/variable involved.
3. Diff current vs. baseline as a `collections.Counter`-based **multiset** difference keyed by
   `(path, code, message)`, not a set difference. Because the key excludes line number, distinct
   errors on different lines can
   legitimately share the same `(path, code, message)` — empirically true for roughly half of
   today's baselined errors. A plain set diff would only track key *presence*, so fixing one of
   three duplicate-key instances (or introducing a new one) would look like no change at all. The
   Counter subtraction tracks per-key *counts*, so partial fixes and partial regressions within a
   duplicate-key group are still detected correctly.
4. **Pass** when the multiset of current-run keys equals the multiset in the committed baseline.
   In particular, an empty current run compared with an empty baseline has no differences and
   exits successfully.
5. **Fail** when new errors appear or baseline entries disappear without updating the JSON.
6. When the current run is clean but the baseline is non-empty, every baseline entry is resolved
   debt. The gate lists the resolved entries under `Resolved baseline errors (update baseline):`,
   reports the baseline and current counts, and exits with status `1`. It does not print ordinary
   `mypy baseline OK` output in this state because the committed baseline is stale.
7. `mypy-baseline.json` missing/wrong `"version"` (i.e. not `2`, including the legacy flat
   `path:line:code` format) is rejected outright with an error pointing at `--update-baseline` —
   there is no silent dual-format fallback.
8. The internal mypy subprocess is limited to 60 seconds. On timeout, the gate preserves any
   partial output, adds `mypy timed out after 60 seconds`, writes it visibly to stderr, and exits
   nonzero. A timeout does not perform a baseline comparison or rewrite the baseline.

### Reading occurrence reports

The gate reports duplicate-key changes by occurrence count:

- A partial regression appends `N new of M total`, where `N` is the number of new occurrences
  and `M` is the current number of occurrences for that key.
- A partial fix appends `N of M baselined`, where `N` is the number of resolved occurrences and
  `M` is the previous baseline count for that key.
- Entirely new and entirely resolved keys omit these qualifiers because every occurrence changed.
- New-error source lines are listed in ascending numerical order, independent of mypy's input
  order. The listed lines identify all current occurrences for the key; the qualifier identifies
  how many of them are new.

For example, a key with three current occurrences, two of which are new, is rendered as:

```text
New mypy errors (not in baseline):
  + pypost/core/client.py: Incompatible value [assignment]
    lines: 12, 45, 90  (2 new of 3 total)
```

These formatting contracts have direct regression coverage in `tests/test_mypy_baseline.py`.

After fixing type errors intentionally, explicitly regenerate the baseline and commit the result.
The normal `make typecheck` gate only compares results; it never rewrites the baseline
automatically:

```bash
.venv/bin/python scripts/check_mypy_baseline.py --update-baseline
git add mypy-baseline.json
```

### Automated ratchet reconciliation

The baseline gate functions as a strict, unidirectional ratchet:
- **Zero regressions allowed:** Any new error introduced in `pypost/core/`, `pypost/models/`, or
  `pypost/ui/` triggers an immediate gate failure (`New mypy errors (not in baseline)`).
- **Mandatory debt retirement:** When code refactoring or bug fixes resolve previously baselined
  errors, the gate exits with status `1` (`Resolved baseline errors (update baseline)`). Developers
  must run `--update-baseline` and commit the updated `mypy-baseline.json`.

This enforces that technical debt only decreases (ratcheting down from 217 to 201 to 189 to 180
records), preventing retired errors from silently resurfacing in future changes.

### Safe optional URL narrowing

`AlertManager._send_webhook()` copies its optional webhook URL to a local variable and returns
when that value is `None`. The subsequent request and `_webhook_log_target()` calls therefore use
a narrowed `str`, while configured-webhook request and logging behavior remains unchanged. Keep
this kind of guard local to the nullable use; it retires the relevant `arg-type` diagnostics
without changing the three-directory baseline scope or its update policy.

### Live test gate (`tests/test_mypy_baseline_live.py`)

In addition to the standalone `make typecheck` target, PyPost includes an automated live test gate
in [`tests/test_mypy_baseline_live.py`](file:///home/src/tests/test_mypy_baseline_live.py)
(introduced in PYPOST-1241). This test runs under `make test` and `make check`:
- It invokes `_run_mypy()`, parses live diagnostics, loads `mypy-baseline.json`, and computes
  the multiset difference via `_diff_errors()`.
- It asserts that `check_mypy_baseline.main()` exits with status `0`, `new_keys == []`, and
  `fixed_keys == []`.
- This ensures that unbaselined regressions and unratcheted baseline debt are caught immediately
  during routine developer test runs and CI pipelines without requiring a separate `make typecheck`
  step.

## Postponed annotations convention

All modules under **`pypost/core/`**, **`pypost/models/`**, and **`pypost/ui/`** must include
postponed evaluation of annotations. On Python 3.11, `from __future__ import annotations`
provides PEP 563-style postponed evaluation:

```python
"""Optional module docstring."""

from __future__ import annotations

import json
from typing import Optional
```

Rules:

1. **`from __future__ import annotations`** is the first import — only a module docstring may
   precede it.
2. Leave a **blank line** after the future import before other imports.
3. **New modules** in core, models, or ui must follow this pattern from the first commit.

This keeps forward references (`EncryptionKey | None`) consistent and aligns with mypy's scoped
paths. Core/models adopted in PYPOST-738; UI bulk migration in PYPOST-815; 100% UI coverage
verified in PYPOST-817 (67 modules).

## Key Typing Contracts and Protocols (PYPOST-1241)

### Generic save orchestrators (`SaveResult[T]`, `StaleCheckContext[T]`)

Save orchestrators coordinate dirty checks, overwrite warnings, save-as dialogs, and persistence
for tabs in the main window. Because PyPost supports multiple distinct protocol entities (HTTP
requests, WebSocket connection profiles, and MCP client configurations), save orchestrator
data structures in `pypost/ui/request_save_orchestrator.py` are parameterized over a generic
type variable `T = TypeVar("T")`:

```python
T = TypeVar("T")


@dataclass(frozen=True)
class StaleCheckContext(Generic[T]):
    """Tab persistence state used before overwriting an existing request or connection."""

    persisted_baseline: T | None
    stale_persisted: bool


@dataclass(frozen=True)
class SaveResult(Generic[T]):
    action: SaveAction
    request: T | None = None
    collection_id: str | None = None
```

Concrete parameterizations across the codebase:
- **HTTP Requests:** `SaveResult[RequestData]` and `StaleCheckContext[RequestData]` in
  [`RequestSaveOrchestrator`](file:///home/src/pypost/ui/request_save_orchestrator.py).
- **WebSocket Profiles:** `SaveResult[WebSocketConnection]` and
  `StaleCheckContext[WebSocketConnection]` in
  [`WebSocketSaveOrchestrator`](file:///home/src/pypost/ui/websocket_save_orchestrator.py).
- **MCP Client Connections:** `SaveResult[McpClientConnection]` and
  `StaleCheckContext[McpClientConnection]` in
  [`McpClientSaveOrchestrator`](file:///home/src/pypost/ui/mcp_client_save_orchestrator.py).

`TabsPresenter` implements typed helper methods (`_stale_context_for_tab`,
`_stale_context_for_websocket_tab`, `_stale_context_for_mcp_client_tab`) that produce these
strongly typed contexts, eliminating cross-entity union conflation and ensuring type safety when
inspecting `result.request` or `context.persisted_baseline`.

### Structural protocol for tab close prompts (`TabClosePromptProtocol`)

When closing modified or active tabs, presenters display confirmation dialogs before closing.
The dialog functions for protocol tabs (such as `prompt_deleted_websocket_profile_tab_close`
and `prompt_deleted_mcp_client_tab_close` in `pypost/ui/collection_item_dialogs.py`) declare
explicit keyword-only arguments:

```python
def prompt_deleted_websocket_profile_tab_close(
    parent: QWidget,
    tab_title: str,
    *,
    has_unsaved_edits: bool,
    has_active_connection: bool,
) -> bool: ...
```

In standard Python typing, `Callable[[QWidget, str, bool, bool], bool]` denotes positional-only
arguments. Passing keyword arguments to a callback annotated with `Callable` causes mypy errors
(`Unexpected keyword argument`). To enforce correct argument passing at type-check time,
`pypost/ui/collection_item_dialogs.py` defines `TabClosePromptProtocol`:

```python
class TabClosePromptProtocol(Protocol):
    def __call__(
        self,
        parent: QWidget,
        tab_title: str,
        *,
        has_unsaved_edits: bool,
        has_active_connection: bool,
    ) -> bool: ...
```

This protocol is used across `tabs_presenter_ws_close.py`, `tabs_presenter_mcp_close.py`, and
`tabs_presenter.py`, allowing dialog implementations and custom test fakes to be verified
statically with keyword-only contracts.

### Stream export typing with snapshots (`MessageStream | StreamExportSnapshot`)

WebSocket message streams are buffered in memory via `MessageStream`
(`pypost/core/websocket_stream.py`). For asynchronous disk exports, passing mutable in-memory
streams across threads risks data races. PyPost captures an immutable snapshot on the GUI thread
using `StreamExportSnapshot` (`pypost/core/websocket_stream_export.py`) before passing it to
`WebSocketStreamExportWorker` on a background thread.

Both `MessageStream` and `StreamExportSnapshot` provide identical structural read interfaces:
- `__len__() -> int`: Retained message count.
- `snapshot() -> tuple[StreamEntry, ...]`: Immutable tuple of stream entries.
- `dropped -> dict[str, int]`: Drop counters (`capacity`, `memory_budget`).

Core export formatters and writers in `pypost/core/websocket_stream_export.py`
(`format_json_transcript`, `format_text_transcript`, `export_stream_to_json_file`, and
`export_stream_to_text_file`) are annotated to accept the union:

```python
stream: MessageStream | StreamExportSnapshot
```

This allows synchronous headless callers to pass `MessageStream` directly, while off-thread workers
pass `StreamExportSnapshot` without type casts, maintaining pure Qt-free typing contracts in core.

## Configuration

Key mypy settings (see `pyproject.toml` for the full list):

| Setting | Value | Rationale |
| --- | --- | --- |
| `python_version` | `3.11` | Matches minimum supported Python |
| `check_untyped_defs` | `true` | Check bodies even without full annotations |
| `no_implicit_optional` | `true` | Require explicit `T \| None` for optional params |
| `disallow_untyped_defs` | `false` | Incremental adoption; baseline holds known gaps |

Dev dependencies: `mypy`, `types-PyYAML` (YAML stub types), and `types-PySide6` (Qt6 stub types)
in `requirements-dev.in`.

## Baseline Triage and History

The baseline error count reflects known technical debt across `pypost/core`, `pypost/models`, and
`pypost/ui`. The baseline history and key milestones:

- **PYPOST-734 / PYPOST-813 / PYPOST-814 / PYPOST-815 (July 2026):** Initial scoped baseline
  frozen at 218 errors (41 in `pypost/core/`, 0 in `pypost/models/`, 177 in `pypost/ui/`).
- **PYPOST-1007:** Migrated baseline keys from `path:line:code` to `(path, code, message)`
  multiset representation to eliminate line-drift false positives. Reconciled to 217 errors.
- **PYPOST-1241 (August 2026):** Reconciled the baseline down to **189 known errors**. Eliminated
  33 newly introduced errors across generic save orchestrators, tab close prompt protocols, stream
  export signatures, and Qt UserRole enums, while retiring 4 resolved baseline entries via
  automated ratchet reconciliation. Added `tests/test_mypy_baseline_live.py` to enforce zero drift.
- **PYPOST-1255 (September 2026):** Ratcheted the live baseline to **180 records** by retiring five
  direct `pypost/core/alert_manager.py` webhook `arg-type` occurrences. Added a 60-second internal
  mypy subprocess timeout with visible nonzero failure handling and regression coverage for the
  timeout and Counter-key contracts.

Per-code breakdown below is the original July 2026 snapshot; it illustrates *typical* fixes rather
than a live count. Open `mypy-baseline.json` (one JSON object per error, with an `error_count`
summary field) for the exact live breakdown.

### Core (`pypost/core/`) — 41 errors in 14 files

| Code | Count | Typical fix |
| --- | ---: | --- |
| `arg-type` | 12 | Narrow `str \| None` before use |
| `assignment` | 6 | Add `\| None` to optional parameters |
| `attr-defined` | 7 | Optional attributes, MCP server API typing |
| `var-annotated` | 4 | Add local variable annotations |
| `union-attr` | 4 | Nullable `TemplateService` |
| `misc` | 4 | Conditional `cryptography` imports |
| `return-value` | 2 | Protocol / envelope mismatches |
| `no-any-return` | 2 | Untyped third-party returns |

The `alert_manager.py` webhook URL guard was completed in PYPOST-1255. Remaining suggested fix
order: encryption codec conditional imports → nullable `TemplateService` in
`request_service.py`.

### UI (`pypost/ui/`) — 177 errors in 29 files

| Code | Count | Typical fix |
| --- | ---: | --- |
| `attr-defined` | 124 | Qt widget APIs, dynamic attributes, stub gaps |
| `misc` | 20 | Signal/slot typing, PySide6 stub edge cases |
| `no-any-return` | 10 | Annotate or narrow Qt method returns |
| `assignment` | 10 | Optional defaults, incompatible widget assignments |
| `override` | 6 | QWidget/QObject method override signatures |
| `arg-type` | 5 | `str \| None` vs `str`, enum arguments |

Suggested fix order: `mixins.py` hover helper guards → `collection_item_dialogs.py` dialog
helpers → presenter optional-parameter annotations.

Full breakdown: `ai-tasks/PYPOST-734/20-architecture.md` (core initial triage);
`ai-tasks/PYPOST-813/20-architecture.md` (R-P2-005a delta);
`ai-tasks/PYPOST-814/20-architecture.md` (R-P2-005b delta);
`ai-tasks/PYPOST-815/20-architecture.md` (R-P2-005c UI scope);
`ai-tasks/PYPOST-1241/20-architecture.md` (save orchestrator, dialog protocol,
and stream export delta).

## Relationship to Other Quality Gates

| Target | Includes mypy? |
| --- | --- |
| `make lint` | No (flake8) |
| `make test` | Yes (runs `tests/test_mypy_baseline_live.py`) |
| `make check` | Yes (lint + fast tests including live baseline gate + `verify-ai-tasks`) |
| `make typecheck` | Yes (direct `check_mypy_baseline.py` invocation) |

CI (`.github/workflows/test.yml`) runs `make check`, which executes
`tests/test_mypy_baseline_live.py`.

Use Make targets for local validation. `make typecheck` runs the baseline comparison,
`make lint` runs static/style checks, and `make verify-ai-tasks` verifies workflow artifacts.
The underlying mypy process may report the 180 known diagnostics and still yield a passing
`make typecheck` when no new or resolved Counter-key occurrences are present. A task-caused new
key or additional occurrence is different: it is reported as `New mypy errors (not in baseline)`
and makes the gate nonzero until the source change is fixed.

## Troubleshooting

### `make typecheck` reports new errors

Fix the type errors or revert the change. Do not edit the baseline to hide regressions.

### `make typecheck` reports a timeout

The gate fails visibly after the internal 60-second mypy limit with
`mypy timed out after 60 seconds`. Investigate the environment or checker run and retry; the
timeout path never rewrites `mypy-baseline.json`.

### Fixed errors but the gate still fails

Run `check_mypy_baseline.py --update-baseline` and commit the updated JSON.

### Mypy reports missing `yaml` or `PySide6` stubs

Run `make venv-test`. The `[dev]` extra includes `types-PyYAML` and `types-PySide6`.

### Mypy cannot import `pypost`

Run from the repository root. The configuration sets `mypy_path = "."`.

### Diagnostics from a newly configured path are not recognized

Confirm the `MYPY_PATHS` entry is a repository-relative directory prefix without a trailing slash,
then run the gate in a fresh process. Diagnostic recognition is compiled from `MYPY_PATHS` at
module import; do not patch `_ERROR_RE` separately.

## See Also

- [setup.md](setup.md) — dev dependency installation
- [testing.md](testing.md) — primary quality gate (`make check`)
- [maintainability_audit.md](maintainability_audit.md) — audit context for R-P2-005
- `tests/test_mypy_baseline_live.py` — live pytest gate enforcing baseline ratchet invariants
- `ai-tasks/PYPOST-1007/20-architecture.md` — full design rationale for the `(path, code,
  message)` key and Counter-based multiset diff, including the PYPOST-987 line-shift incident
- `ai-tasks/PYPOST-1241/20-architecture.md` — full architectural design for generic
  save orchestrator, protocol dialog, and stream export typing reconciliation
