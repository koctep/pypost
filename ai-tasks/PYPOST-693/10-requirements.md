# PYPOST-693: Resolve Qt throughout core

## Goals

PyPost documents a layered architecture where the **core** package holds business logic and
services that depend on shared data definitions (`models/`), while the **presentation** package
(`ui/`) owns the PySide6 user interface. The PYPOST-684 architecture audit found that multiple
core modules import PySide6 for threading, signals, and timers — not for widgets, but still
coupling the core package to the GUI framework (finding **D-004**, recommendation **R-P1-002**).

That coupling has real cost for the team: maintainers cannot treat core as
framework-agnostic; lightweight unit tests and headless reuse of business capabilities require
a Qt event loop or heavy mocking; and existing patterns invite new Qt-dependent code in core,
further blurring the presentation/core boundary. Related finding **L-001** notes that MCP
lifecycle and request workers function as integration and presentation glue while living under
core.

With R-P1-001 (style management core → UI import) addressed in PYPOST-692, R-P1-002 is the
remaining P1 boundary item from the audit. Closing it restores trust in documented layer rules
and makes the cost of framework coupling an explicit, managed decision rather than an
undocumented convention.

**Business intent:** Make the relationship between core business capabilities and the Qt
framework **clear, honest, and maintainable** — so developers, reviewers, and test authors
know what to expect when working in core — without changing what PyPost users experience.

## Programming Language

Python (existing PyPost desktop application codebase).

## User Stories

- As a **maintainer**, I want the core package boundary to accurately reflect which
  capabilities require the Qt framework so I can enforce layer rules during code review and
  avoid accidental spread of framework coupling.
- As a **developer**, I want to import core modules for HTTP execution, templating, history,
  and storage logic without implicitly requiring PySide6 unless the capability genuinely needs
  it, so that unit tests stay fast and headless tooling remains viable where appropriate.
- As a **developer writing tests**, I want framework-dependent core code to be identifiable
  and documented so I can choose the right test setup (mock, offscreen Qt, or integration) without
  discovering hidden dependencies at runtime.
- As a **reviewer**, I want PYPOST-684 finding D-004 / recommendation R-P1-002 resolved so
  the known P1 boundary debt from the audit is closed with a traceable outcome.
- As a **PyPost user**, I want request execution, collection and environment persistence,
  encryption migration, MCP server lifecycle, session state, and metrics to behave exactly as
  today — no regressions in responsiveness, reliability, or feature availability.

## Definition of Done

- The PYPOST-684 **R-P1-002** remediation is complete: the team has a clear, documented
  stance on Qt usage within core (either an explicit accepted boundary or a structural change
  that separates framework-dependent code from framework-agnostic business logic).
- A developer reading project documentation can determine **which core capabilities require
  PySide6** and which do not, without manually scanning imports across dozens of modules.
- All user-facing behavior preserved for capabilities currently using Qt threading/signals in
  core:
  - HTTP request execution from the GUI (background worker, progress/cancellation signals).
  - MCP server start/stop, tool exposure, and activity signaling.
  - Debounced session state persistence.
  - Metrics collection and emission to interested UI components.
  - Asynchronous collection storage (save/load with UI responsiveness).
  - Asynchronous environment storage (save/load with coalescing and single-flight behavior).
  - Encryption migration running in the background without blocking the UI.
- Existing automated tests covering the affected capabilities pass without weakening
  assertions; `make check` passes.
- Architecture audit documentation (`doc/dev/architecture_audit.md` and related dev docs)
  can be updated in Step 7 to mark D-004 / R-P1-002 as remediated; Step 1 acceptance is the
  behavioral and boundary outcome, not doc edits here.

## Task Description

**Problem:** PYPOST-684 identified recommendation **R-P1-002** (finding **D-004**): nine
core modules currently import PySide6. They use Qt for concurrency and event-loop integration
(threads, signals, timers, and in one gateway path a runtime `QApplication` check) — not for
widgets — but the import still binds core to the presentation framework. Documented layer rules
state that core depends on models only; in practice, a significant subset of core cannot be
imported or tested without PySide6.

**Why now:** R-P1-002 is prioritized P1 (high) tech debt. It is the remaining top-tier boundary
finding after R-P1-001 (style manager) is remediated. Unresolved, it continues to undermine
architecture documentation, increases test friction, and sets a precedent for placing
framework glue alongside pure business logic.

### Affected capabilities (business view)

| Capability | Role today | Why Qt appears |
| --- | --- | --- |
| Request execution worker | Runs HTTP requests off the UI thread; reports results and errors back to presenters | Background thread and signal bridge |
| MCP server lifecycle | Starts/stops the collection MCP server; coordinates with env suppliers and activity log | Thread management and signal bridge to UI |
| Session state manager | Persists UI session state (open tabs, layout) with debounced saves | Timer and object signals |
| Metrics manager | Tracks and emits execution metrics consumed by UI and observability surfaces | Signal bridge |
| Collection storage (async) | Saves/loads collections without blocking the UI | Worker thread and gateway signal coordination |
| Environment storage (async) | Saves/loads environment variables with coalescing and single-flight queue | Worker thread and gateway signal coordination |
| Encryption migration (async) | Runs bulk re-encryption without freezing the UI | Worker thread and progress signals |

### Functional requirements

- Resolve the architectural ambiguity of PySide6 usage across core so the boundary between
  **framework-dependent integration glue** and **framework-agnostic business logic** is
  explicit for maintainers.
- Preserve end-to-end behavior for all capabilities listed above: threading model,
  responsiveness, signal delivery to UI consumers, error propagation, and cancellation
  semantics must remain equivalent from the user and presenter perspective.
- Preserve existing logging and observability intent for async operations (storage gateways,
  workers, MCP lifecycle) — failures must not become silent.
- Update import sites, tests, and any cross-module references affected by the remediation so
  the application and test suite remain coherent.

### Non-functional requirements

- **No user-visible regression:** GUI responsiveness, MCP server reliability, persistence
  durability, and encryption migration safety must match current production behavior.
- **Clarity:** After remediation, a new contributor should not need tribal knowledge to
  distinguish Qt-required core code from Qt-free business modules.
- **Testability:** The outcome must either reduce unnecessary Qt dependency for test authors
  or document an accepted trade-off with clear guidance on required test setup.
- **Maintainability:** The solution must not introduce new layer inversions (e.g. core
  importing ui at runtime beyond what already exists and is tracked separately).

### Constraints and assumptions

- Implementation language is Python; the application remains a PySide6 desktop client.
- Remediation scope is **R-P1-002 / D-004 only** — PySide6 usage that legitimately belongs
  in the presentation layer is out of scope unless unavoidable as a consequence of this task.
- R-P1-001 (style manager core → UI import) is **already remediated** in PYPOST-692 and is
  not in scope; the current core PySide6 footprint is the nine modules identified in the
  2026-07-14 codebase scan (see Q&A).
- Composition-root elevation (`HistoryManager`, `StorageManager`, etc. in `main.py`) is
  tracked separately (PYPOST-694, PYPOST-695) and is out of scope unless strictly required
  for R-P1-002.
- Relocating `request_sync.is_tab_dirty` (PYPOST-696), dual `TemplateService` for hover
  (PYPOST-697), and startup style bootstrap duplication (PYPOST-702) are out of scope.
- No new user-facing features, protocol changes, or MCP tool surface changes are in scope.

### In scope

- Addressing PYPOST-684 R-P1-002 / D-004: Qt framework coupling across core modules used for
  threading, signals, and timers.
- Preserving behavioral parity for request workers, MCP lifecycle, state/metrics signaling,
  and async storage/migration paths listed above.
- Adjusting tests and imports affected by the remediation.

### Out of scope

- Removing PySide6 from the application or rewriting the UI toolkit.
- PYPOST-692 (style manager boundary — already done).
- PYPOST-694–702 unless a minimal unavoidable touch point arises; any spillover should be
  tracked separately.
- Performance optimization of worker/gateway implementations beyond maintaining current
  responsiveness.
- Changing MCP protocol behavior, HTTP execution semantics, or encryption algorithms.

### Main entities (business perspective)

| Entity | Role |
| --- | --- |
| Core package | Business logic and services; documented to depend on models only. |
| Presentation (UI) package | PySide6 windows, widgets, presenters; orchestrates user actions. |
| Framework-dependent core glue | Capabilities using Qt threads/signals/timers to bridge async work and UI. |
| Framework-agnostic business logic | HTTP execution, templating, history, storage logic without Qt imports. |
| Request execution | Sending HTTP requests and delivering results to the UI without blocking. |
| MCP server lifecycle | Starting, stopping, and signaling state for the collection MCP server. |
| Async persistence | Collection and environment save/load with UI responsiveness guarantees. |
| Encryption migration | Background bulk re-encryption with progress feedback. |
| Session state | Debounced persistence of UI session (tabs, layout). |
| Metrics | Execution counters and signals consumed by UI and observability. |
| Architecture audit finding D-004 | PySide6 imports in core weaken the presentation/core boundary. |
| Remediation R-P1-002 | Tracked P1 item to resolve or explicitly document Qt throughout core. |

## Q&A

- **Q**: Why is this a business requirement and not “just reorganize imports”?
  **A**: The audit framed it as structural risk: undocumented framework coupling makes the
  codebase harder to test, review, and extend. The business outcome is **trustworthy package
  boundaries** without changing user-visible behavior.

- **Q**: Must end users notice any difference?
  **A**: No. Acceptance is behavioral parity for execution, persistence, MCP, migration, state,
  and metrics.

- **Q**: Does Step 1 choose between “document as accepted compromise” vs “split subpackage”?
  **A**: No. Step 1 defines *what* must be true (clear boundary, preserved behavior, closed
  audit item). The *how* is decided in Step 2 (architecture).

- **Q**: How many core modules are affected?
  **A**: Current codebase scan (2026-07-14) finds **nine** modules under `pypost/core/` with
  PySide6 imports: `worker.py`, `mcp_server.py`, `state_manager.py`, `metrics.py`,
  `collection_storage_worker.py`, `collection_storage_gateway.py`,
  `environment_storage_worker.py`, `environment_storage_gateway.py`, and
  `encryption_migration_worker.py`. The original audit counted eight, including
  `style_manager.py` (now remediated in PYPOST-692) and omitting the collection storage
  async pair — see issues noted for Step 2.

- **Q**: Are documentation updates part of this task?
  **A**: Dev docs referencing D-004 / R-P1-002 should be updated when implementation lands
  (Step 7). Requirements acceptance is the boundary and behavior outcome.

- **Q**: Source references?
  **A**: Jira [PYPOST-693](https://pypost.atlassian.net/browse/PYPOST-693); parent audit
  [PYPOST-684](https://pypost.atlassian.net/browse/PYPOST-684); finding detail in
  `ai-tasks/PYPOST-684/30-audit-report.md`, `ai-tasks/PYPOST-684/60-tech-debt.md`
  (R-P1-002), and `doc/dev/architecture_audit.md`.
