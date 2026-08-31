# PYPOST-1241: Technical Debt Analysis

## Shortcuts Taken

During the implementation of PYPOST-1241, several practical trade-offs were made to restore the `make typecheck` quality gate promptly and safely without introducing regressions or modifying runtime behavior:

1. **Baseline Reconciliation Kept 189 Pre-Existing Errors**:
   - The primary objective of PYPOST-1241 was to unblock the broken static type checking quality gate (`make typecheck`). While 12 distinct error clusters (~51 total errors across core, model, and UI packages) were resolved and 4 stale baseline entries retired (reducing the baseline count from 201 to 189), the remaining 189 pre-existing type errors were preserved in `mypy-baseline.json`.
   - Fixing all 189 legacy errors in a single task would require broad, risky refactorings across legacy components outside the scope of this ticket. The baseline ratchet mechanism correctly fences these errors while preventing any new ones.

2. **Inlined Lambda Adapters for Signal Overloads in `library_dialogs.py`**:
   - `LibraryPresenter` declares `status_updated = Signal(object)` and `manifest_updated = Signal(object)`.
   - PySide6's typing stubs enforce slot contravariance: a `Signal(object)` expects a receiver slot callable with parameter type `object` or broader. Passing methods annotated with narrower types (such as `Callable[[GitRepoStatus | None], None]` or `Callable[[LibraryManifest | None], None]`) causes mypy overload failures.
   - To resolve this without overhauling PySide6 signal architecture, inlined lambda wrappers (`lambda s: self._detail_panel.update_status(s)`) were used. While clean and type-safe, this introduces anonymous closures rather than a strongly typed generic signal interface.

3. **Retention of `request: T | None` Attribute Name in Generic `SaveResult[T]`**:
   - `SaveResult` and `StaleCheckContext` in `pypost/ui/request_save_orchestrator.py` were converted to generic classes parameterized by `T` (`SaveResult[T]`, `StaleCheckContext[T]`).
   - To preserve 100% backward compatibility with keyword-argument instantiations (`SaveResult(..., request=...)`) and existing test suites for HTTP, WebSocket, and MCP client save orchestrators, the field name `request` was preserved rather than renamed to a domain-neutral identifier like `item` or `entity`.

4. **URL Slug Fallback Derivation in `library_presenter.py`**:
   - `GitLibraryService.clone` requires `library_id: str`, but `LibraryPresenter.clone_library` allowed `library_id: str | None`.
   - A fallback was added (`url.rstrip("/").split("/")[-1].removesuffix(".git")`) if `library_id` is omitted. While this satisfies the type contract, it assumes standard git URL naming conventions rather than enforcing mandatory explicit identifiers or invoking a dedicated slugification utility.

5. **`QToolButton.ToolButtonPopupMode.InstantPopup` Alignment**:
   - PySide6 type stubs omit `QToolButton.InstantPopup` directly on the class attribute namespace.
   - In `mcp_client_tab.py` and `websocket_tab.py`, references were updated to `QToolButton.ToolButtonPopupMode.InstantPopup`, matching the existing baselined workaround pattern established in `pypost/ui/widgets/request_editor.py`.

---

## Code Quality Issues

1. **Semantic Dissonance in `SaveResult[T]` Field Names**:
   - For `WebSocketSaveOrchestrator` returning `SaveResult[WebSocketConnection]` or `McpClientSaveOrchestrator` returning `SaveResult[McpClientConnection]`, accessing the saved model instance via `result.request` is unintuitive and semantically misleading.
   - Refactoring `SaveResult` to provide an `entity: T | None` property (with `request` retained as a deprecated alias) will improve codebase readability.

2. **Decentralized Protocol Definitions**:
   - `TabClosePromptProtocol` was defined in `pypost/ui/collection_item_dialogs.py` to type the keyword-only parameters of `prompt_deleted_websocket_profile_tab_close`.
   - Tab close helpers across `tabs_presenter_ws_close.py` and `tabs_presenter_mcp_close.py` import this protocol from dialogs. Protocol abstractions should ideally be centralized in a dedicated `pypost/ui/protocols/` or `pypost/ui/contracts/` module.

3. **Union Typing vs Formal Protocol for Stream Export**:
   - In `pypost/core/websocket_stream_export.py`, stream export functions (`format_json_transcript`, `format_text_transcript`, `export_stream_to_json_file`, `export_stream_to_text_file`) accept `stream: MessageStream | StreamExportSnapshot`.
   - Both classes implement `__len__()`, `snapshot()`, and `dropped`. While the union resolves the type check, formalizing a `StreamExportSourceProtocol(Protocol)` would provide structural subtyping and decouple stream exporters from concrete snapshot classes.

4. **189 Baselined Type Errors**:
   - While ratcheted, 189 errors remain in `mypy-baseline.json`. These span untyped PySide6 widget attributes, missing type hints in legacy core utilities, and legacy request/collection models.

---

## Missing Tests

1. **Synthetic Failure Repro for Quality Gate**:
   - `tests/test_mypy_baseline_live.py` acts as a live regression guard, executing `scripts/check_mypy_baseline.py` against the real repository to assert exit code 0.
   - While `tests/test_mypy_baseline.py` provides unit test coverage with mocked data for ratchet behavior, `test_mypy_baseline_live.py` does not test synthetic failure conditions (e.g. intentionally introducing a bad type error in a dummy file to verify CI failure messages) to avoid polluting repo state.

2. **Headless Qt Event Loop Verification for Lambda Signal Adapters**:
   - The lambda adapters in `pypost/ui/dialogs/library_dialogs.py` were verified statically via `make typecheck` and `make lint`.
   - Dedicated headless Qt tests verifying that emitting `LibraryPresenter.status_updated` invokes `detail_panel.update_status` through the lambda adapter without argument loss or type errors in an active event loop would provide added regression safety.

3. **Stream Export Worker Corrupt Snapshot Handling**:
   - Tests exist for stream export responsiveness and basic file generation (`tests/test_websocket_stream_export_responsiveness.py`), but error recovery paths in `WebSocketStreamExportWorker` when passed a snapshot with invalid dropped metadata or empty streams under IO stress are not exhaustively covered.

4. **Test Timeout Compliance**:
   - Verified that the new test file `tests/test_mypy_baseline_live.py` declares an explicit timeout marker (`pytestmark = pytest.mark.timeout(60)`), fully compliant with the `do-testing` standard.

---

## Performance Concerns

1. **Subprocess Overhead in CI and Live Tests**:
   - `scripts/check_mypy_baseline.py` invokes `mypy` as an external subprocess. On developer workstations and CI runners, running full static analysis takes ~1.7s to 2.0s of wall-clock time.
   - In `tests/test_mypy_baseline_live.py`, running this subprocess during test execution adds ~1.7s. Running the full test suite in parallel mitigates this, but frequent invocations increase CPU and memory utilization.

2. **Baseline Scaling**:
   - The baseline currently stores 189 error records in JSON. Parsing and multiset hashing takes less than 5ms, posing zero current performance bottleneck. However, maintaining the JSON format in git requires care to avoid merge conflicts on concurrent branches.

---

## Follow-up Tasks

### Folded / Superseded Jira Tickets

- **PYPOST-1179**: `make typecheck baseline drift in websocket_stream_export_worker.py and settings_dialog.py`
  - **Classification**: `NON-BLOCKER — pre-existing (RESOLVED / SUPERSEDED)`
  - **Details**: Originally recorded in `ai-tasks/PYPOST-1173/60-tech-debt.md` as an observation of baseline drift in `websocket_stream_export_worker.py` and `settings_dialog.py`.
  - **Resolution**: Both drift clusters (C3: stream export snapshot typing in `websocket_stream_export_worker.py` and C5: `self.layout` shadowing in `settings_dialog.py`) were directly addressed and resolved in PYPOST-1241. PYPOST-1179 is completely fulfilled and superseded by PYPOST-1241.

---

### Pre-Existing Test Failures (Triaged During Testing)

The following pre-existing test failures were observed during testing and are unrelated to PYPOST-1241:

1. **PYPOST-1234**: Parallel runner timeout under full load
   - **Classification**: `NON-BLOCKER — pre-existing`
   - **Node ID**: `tests/test_makefile.py`
   - **Details**: `WORKER_TIMEOUT=120` exceeded under heavy full-suite parallel runner concurrency.
   - **Jira**: [PYPOST-1234](https://pypost.atlassian.net/browse/PYPOST-1234)

2. **PYPOST-1111**: Audit and baseline-metrics snapshot drift
   - **Classification**: `NON-BLOCKER — pre-existing`
   - **Node IDs**:
     - `tests/test_dialogs_audit.py::TestDialogsAuditInventory::test_audit_report_lists_every_dialog_module`
     - `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
     - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
   - **Details**: Dialog audit report LOC aggregate baseline drift and SOLID metrics markdown snapshot drift from prior refactoring tickets.
   - **Jira**: [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111)

---

### Candidate Follow-Up Tasks (Future Improvements)

1. **TD-1 (Non-Blocker): Ratchet Reduction of Remaining 189 Mypy Baseline Errors**
   - **Classification**: `NON-BLOCKER`
   - **Description**: Incrementally resolve the 189 legacy type errors tracked in `mypy-baseline.json` across `pypost/core`, `pypost/models`, and `pypost/ui` through dedicated, focused refactoring tickets.
   - **Estimated Effort**: 5 SP (Epic / Multi-task backlog).
   - **Jira**: [PYPOST-1255](https://pypost.atlassian.net/browse/PYPOST-1255) (Debt, 5 SP, Low priority)

2. **TD-2 (Non-Blocker): Domain-Neutral Entity Naming in `SaveResult[T]`**
   - **Classification**: `NON-BLOCKER`
   - **Description**: Add `entity: T | None` attribute or property to `SaveResult[T]` while preserving `request` as an alias for backwards compatibility, eliminating protocol confusion when saving WebSocket and MCP profiles.
   - **Estimated Effort**: 1 SP.

3. **TD-3 (Non-Blocker): Formalize `StreamExportSourceProtocol`**
   - **Classification**: `NON-BLOCKER`
   - **Description**: Define a formal `typing.Protocol` for `StreamExportSourceProtocol` in `pypost/core/protocols.py` implemented by both `MessageStream` and `StreamExportSnapshot`, replacing union annotations.
   - **Estimated Effort**: 1 SP.

4. **TD-4 (Non-Blocker): Centralize UI Protocols**
   - **Classification**: `NON-BLOCKER`
   - **Description**: Move `TabClosePromptProtocol` from `collection_item_dialogs.py` into a unified `pypost/ui/protocols/` module alongside other presenter contracts.
   - **Estimated Effort**: 1 SP.

5. **TD-5 (Non-Blocker): Headless Qt Integration Tests for `LibraryDialog` Signals**
   - **Classification**: `NON-BLOCKER`
   - **Description**: Add test coverage executing the lambda signal adapters in `library_dialogs.py` within a headless `QApplication` fixture.
   - **Estimated Effort**: 2 SP.
