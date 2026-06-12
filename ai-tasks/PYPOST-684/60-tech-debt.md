# PYPOST-684: Technical Debt Analysis

**Task type:** Architecture and package boundary audit (no application code changes).

**Source:** `30-audit-report.md` — P1/P2/P3 remediation recommendations.

## Shortcuts Taken

- **Static analysis only:** Import scans (ripgrep), module inventory, and import smoke tests;
  no automated dependency-graph tooling (e.g. import-linter, pydeps) was run.
- **No code fixes in scope:** Findings are documented for follow-up; boundary violations and
  composition-root gaps remain in the codebase until remediated.
- **Documentation drift deferred:** `architecture.md` stale tree and related gaps are tracked as
  follow-ups (R-P2-005 targets Step 7 dev docs).
- **Qualitative severity:** Layer and service findings use manual severity ratings without formal
  metric thresholds beyond the existing LOC baseline script.

## Code Quality Issues

Documented in the audited codebase (not introduced by this task):

- **Core → UI import inversion (HIGH):** `pypost/core/style_manager.py` imports
  `PyPostStyle` from `pypost.ui` at runtime — the only confirmed layer-direction violation
  outside `TYPE_CHECKING` guards (D-001, L-004).
- **Qt bleed into core (MEDIUM):** Eight `core/` modules depend on PySide6 (`worker.py`,
  `mcp_server.py`, `state_manager.py`, `metrics.py`, encryption/env workers,
  `style_manager.py`), weakening the presentation/core boundary (D-004).
- **Partial composition root (MEDIUM):** `MainWindow` still constructs `StorageManager`,
  `RequestManager`, `HistoryManager`, `MCPServerManager`, and `StyleManager` instead of
  `main.py` wiring them like `ConfigManager` and `TemplateService`.
- **Core/UI placement blur (MEDIUM):** `request_sync.is_tab_dirty` ties core package semantics
  to a UI `RequestTab` type (L-003).
- **Dual TemplateService (MEDIUM):** Hover mixin holds a module-level `TemplateService`
  separate from the composition-root instance (S-TMPL-003).

## Missing Tests

- No tests were written or modified for this task (audit only).
- **Testability gaps from audit:** Workers, MCP manager, and modules with Qt dependencies
  require a Qt event loop or heavy mocking for unit tests; `RequestWorker` always constructs
  `RequestService` internally, limiting narrow integration-test injection (S-HTTP-003).

## Performance Concerns

None identified. Performance profiling was explicitly out of scope per `10-requirements.md`.

## Follow-up Tasks

Eleven remediation items ticketed in Jira; R-P2-005 resolved in PYPOST-684 Step 7 (no
separate ticket).

### P1 — High (remediate before major boundary refactors)

#### R-P1-001 — Move StyleManager out of core

- **Priority:** P1
- **Recommendation ID:** R-P1-001
- **Finding refs:** D-001, L-004
- **Description:** `pypost/core/style_manager.py` imports `PyPostStyle` from `pypost.ui` at
  runtime and manipulates QSS/QPalette. This is the only confirmed core → ui import outside
  `TYPE_CHECKING` guards.
- **Remediation:** Move `StyleManager` and theme application to `pypost/ui/` (e.g.
  `ui/styles/style_manager.py`) or extract `PyPostStyle` to a neutral module both layers can
  import. Remove `ui/` import from `core/`.
- **Jira:** [PYPOST-692](https://pypost.atlassian.net/browse/PYPOST-692)

#### R-P1-002 — Resolve Qt throughout core

- **Priority:** P1
- **Recommendation ID:** R-P1-002
- **Finding refs:** D-004
- **Description:** Eight `core/` modules import PySide6 for threads, signals, and timers.
  Documented for MCP/UI bridging but `core/` is not UI-framework-agnostic; headless reuse and
  lightweight unit tests are blocked.
- **Remediation:** Document as an accepted boundary compromise **or** split `core/qt/` /
  `core/integration/` subpackages with an explicit "requires PySide6" boundary; keep
  HTTP/templating/history in Qt-free modules.
- **Jira:** [PYPOST-693](https://pypost.atlassian.net/browse/PYPOST-693)

### P2 — Medium (schedule as tech debt)

#### R-P2-001 — Inject HistoryManager from composition root

- **Priority:** P2
- **Recommendation ID:** R-P2-001
- **Finding refs:** S-HIST-003
- **Description:** `HistoryManager()` is constructed in `MainWindow.__init__`, not `main.py` or
  the `testability.md` injection table. It is passed to `TabsPresenter` → `RequestWorker` →
  `RequestService`, increasing test-setup cost.
- **Remediation:** Construct in `main.py` and inject into `MainWindow` / `TabsPresenter`; extend
  `testability.md` table.
- **Jira:** [PYPOST-694](https://pypost.atlassian.net/browse/PYPOST-694)

#### R-P2-002 — Elevate MainWindow service wiring to main.py

- **Priority:** P2
- **Recommendation ID:** R-P2-002
- **Finding refs:** Partial composition root
- **Description:** `main.py` wires `ConfigManager`, `MetricsManager`, `TemplateService`, and
  `AlertManager`, but `MainWindow` still constructs `StorageManager`, `RequestManager`,
  `MCPServerManager`, and related services.
- **Remediation:** Optionally elevate `StorageManager`, `RequestManager`, `MCPServerManager`
  wiring to `main.py` for parity with `TemplateService` / `ConfigManager`.
- **Jira:** [PYPOST-695](https://pypost.atlassian.net/browse/PYPOST-695)

#### R-P2-003 — Relocate tab-aware dirty-check helper

- **Priority:** P2
- **Recommendation ID:** R-P2-003
- **Finding refs:** L-003
- **Description:** `pypost/core/request_sync.py` implements `is_tab_dirty` accepting a UI
  `RequestTab` type. Refactoring `RequestTab` requires touching `core/`.
- **Remediation:** Relocate tab-aware helper to `ui/`; keep `RequestData` copy/compare helpers
  in core or `models/`.
- **Jira:** [PYPOST-696](https://pypost.atlassian.net/browse/PYPOST-696)

#### R-P2-004 — Unify hover TemplateService instance

- **Priority:** P2
- **Recommendation ID:** R-P2-004
- **Finding refs:** S-TMPL-003
- **Description:** `ui/widgets/mixins.py` holds a module-level `_hover_template_service =
  TemplateService()`, separate from the composition-root instance; metrics diverge unless
  `VariableHoverResolver.set_metrics()` is called.
- **Remediation:** Inject composition-root `TemplateService` into hover mixin via `MainWindow`
  setup instead of module singleton (or document explicit acceptance).
- **Jira:** [PYPOST-697](https://pypost.atlassian.net/browse/PYPOST-697)

#### R-P2-005 — Refresh architecture.md directory tree

- **Priority:** P2
- **Recommendation ID:** R-P2-005
- **Finding refs:** Documentation drift
- **Description:** `doc/dev/architecture.md` directory tree lists ~15 core files; live `core/`
  has 68 modules. Missing MCP stack, encryption, key_sources, history, metrics server,
  presenters subpackage, and fixtures.
- **Remediation:** Refresh directory structure and MCP/encryption/metrics sections in Step 7
  dev docs.
- **Resolved:** Addressed in PYPOST-684 Step 7 (`doc/dev/architecture.md`, `architecture_audit.md`).

#### R-P2-006 — Allow RequestService injection in RequestWorker

- **Priority:** P2
- **Recommendation ID:** R-P2-006
- **Finding refs:** S-HTTP-003
- **Description:** `RequestWorker` always constructs `RequestService` internally;
  `HTTPClient`/`MCPClientService` default-constructed inside `RequestService` when not injected.
- **Remediation:** Allow injecting `ExecuteRequestProtocol` factory or service into
  `RequestWorker` for narrower integration tests.
- **Jira:** [PYPOST-698](https://pypost.atlassian.net/browse/PYPOST-698)

### P3 — Low (track or accept)

#### R-P3-001 — Resolve empty utils/ package

- **Priority:** P3
- **Recommendation ID:** R-P3-001
- **Finding refs:** L-006
- **Description:** `pypost/utils/__init__.py` is empty; no imports of `pypost.utils` anywhere
  in the repo. Dead package entry in architecture docs.
- **Remediation:** Remove from docs or add shared helpers when needed.
- **Jira:** [PYPOST-699](https://pypost.atlassian.net/browse/PYPOST-699)

#### R-P3-002 — Split template_service.py if LOC grows

- **Priority:** P3
- **Recommendation ID:** R-P3-002
- **Finding refs:** S-TMPL-004
- **Description:** `template_service.py` at 204 LOC vs 200 cap (`audit_baseline_metrics.py`).
- **Remediation:** Split expression helpers if growth continues.
- **Jira:** [PYPOST-700](https://pypost.atlassian.net/browse/PYPOST-700)

#### R-P3-003 — MCP inbound history asymmetry

- **Priority:** P3
- **Recommendation ID:** R-P3-003
- **Finding refs:** S-HIST-004
- **Description:** `MCPServerImpl._create_request_service()` omits `history_manager`; inbound
  MCP tools do not record history (documented in `mcp_integration.md`).
- **Remediation:** Accept as documented product choice; revisit only if agents need audit trail
  parity with GUI.
- **Jira:** [PYPOST-701](https://pypost.atlassian.net/browse/PYPOST-701)

#### R-P3-004 — Consolidate PyPostStyle setup in main.py

- **Priority:** P3
- **Recommendation ID:** R-P3-004
- **Finding refs:** `main.py` duplicates styling
- **Description:** `main.py` duplicates `PyPostStyle` setup alongside `StyleManager` theme
  application.
- **Remediation:** Consolidate with `StyleManager.apply_theme` once style code moves to ui
  (depends on R-P1-001).
- **Jira:** [PYPOST-702](https://pypost.atlassian.net/browse/PYPOST-702)

## Blocker Review

**SAFE TO CLOSE** — audit deliverables complete; no application code changes required. Twelve
follow-up remediation items documented for Phase D Jira ticketing and future implementation.
