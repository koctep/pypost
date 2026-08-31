# PYPOST-1241: High-Level Architecture Design — Reconcile Mypy Baseline and Type Errors

## Research

### Background and Context

The static typechecking quality gate (`make typecheck`, invoking [`scripts/check_mypy_baseline.py`](file:///home/src/scripts/check_mypy_baseline.py)) enforces a strict ratchet mechanism against known typing issues across `pypost/core`, `pypost/models`, and `pypost/ui`:
1. Any newly introduced error not recorded in [`mypy-baseline.json`](file:///home/src/mypy-baseline.json) causes an immediate gate failure (exit code 1).
2. Any previously baselined error that is resolved must be retired from [`mypy-baseline.json`](file:///home/src/mypy-baseline.json), failing the gate until updated.

The gate is currently red at HEAD:
- **Recorded baseline:** 201 errors
- **Current live mypy run:** 240 errors
- **Delta:** 33 new error instances across 12 distinct root-cause clusters, and 4 resolved baseline entries.

The baseline was last updated at commit `f6c1124` (2026-08-22). Since then, approximately 14k lines across 104 new or modified modules landed, introducing protocol features (such as WebSocket and MCP Client workspaces, Git library management, and off-thread stream export) whose type contracts were not aligned with existing core abstractions.

### Live Error Diagnostic Triage

Running `make typecheck` isolates the exact delta into 12 distinct problem clusters and 4 resolved baseline entries:

| Cluster | Files | Error Description | Count | Root Cause Analysis | Architectural Fix Category |
|---|---|---|---|---|---|
| **C1: Generic Save Orchestration** | [`pypost/ui/request_save_orchestrator.py`](file:///home/src/pypost/ui/request_save_orchestrator.py)<br>[`pypost/ui/websocket_save_orchestrator.py`](file:///home/src/pypost/ui/websocket_save_orchestrator.py)<br>[`pypost/ui/mcp_client_save_orchestrator.py`](file:///home/src/pypost/ui/mcp_client_save_orchestrator.py)<br>[`pypost/ui/presenters/tabs_presenter.py`](file:///home/src/pypost/ui/presenters/tabs_presenter.py) | `SaveResult.request` and `StaleCheckContext.persisted_baseline` typed as `RequestData \| None`, but passed `WebSocketConnection` and `McpClientConnection`. | 18 errors | Monomorphic typing of `SaveResult` and `StaleCheckContext` for HTTP requests only, then reused verbatim by WebSocket and MCP orchestrators and presenters. | Parameterize `SaveResult[T]` and `StaleCheckContext[T]` with a generic type parameter `T`. |
| **C2: Tab Close Prompt Protocol** | [`pypost/ui/presenters/tabs_presenter_ws_close.py`](file:///home/src/pypost/ui/presenters/tabs_presenter_ws_close.py)<br>[`pypost/ui/presenters/tabs_presenter_mcp_close.py`](file:///home/src/pypost/ui/presenters/tabs_presenter_mcp_close.py)<br>[`pypost/ui/presenters/tabs_presenter.py`](file:///home/src/pypost/ui/presenters/tabs_presenter.py) | `Unexpected keyword argument "has_active_connection"` / `"has_unsaved_edits"`, and incompatible argument type to `close_tabs_for_*`. | 6 errors | `Callable[[QWidget, str, bool, bool], bool]` denotes positional-only arguments in typing, whereas [`prompt_deleted_websocket_profile_tab_close`](file:///home/src/pypost/ui/collection_item_dialogs.py#L131-L137) enforces keyword-only arguments (`*, has_unsaved_edits: bool, has_active_connection: bool`). | Define a structural `TabClosePromptProtocol(Protocol)` with keyword-only parameters. |
| **C3: Stream Export Typing** | [`pypost/core/qt/websocket_stream_export_worker.py`](file:///home/src/pypost/core/qt/websocket_stream_export_worker.py)<br>[`pypost/core/websocket_stream_export.py`](file:///home/src/pypost/core/websocket_stream_export.py) | `Argument 2 to "export_stream_to_json_file" has incompatible type "StreamExportSnapshot"; expected "MessageStream"`. | 2 errors | Export helper functions require `MessageStream`, but off-thread workers pass [`StreamExportSnapshot`](file:///home/src/pypost/core/websocket_stream_export.py#L33), which implements the same snapshot/dropped interface. | Widen function parameter type annotations to `MessageStream \| StreamExportSnapshot` (or `StreamExportSourceProtocol`). |
| **C4: Library Presenter Signals** | [`pypost/ui/dialogs/library_dialogs.py`](file:///home/src/pypost/ui/dialogs/library_dialogs.py)<br>[`pypost/ui/presenters/library_presenter.py`](file:///home/src/pypost/ui/presenters/library_presenter.py) | `No overload variant of "connect" of "SignalInstance" matches argument type "Callable[[GitRepoStatus \| None], None]"`. | 2 errors | `LibraryPresenter` declares `Signal(object)`. PySide6 stubs expect receiver callbacks taking `object`. Callbacks taking narrower types fail contravariance checks. | Connect via explicit wrapper callback or lambda adapter ensuring slot signature compatibility. |
| **C5: Settings Dialog Layout Property Shadowing** | [`pypost/ui/dialogs/settings_dialog.py`](file:///home/src/pypost/ui/dialogs/settings_dialog.py) | `"Callable[[], QLayout \| None]" has no attribute "addWidget"`. | 2 errors (1 new, 1 baselined) | `self.layout = QVBoxLayout(self)` shadows `QDialog.layout()`. Mypy resolves `self.layout` as the inherited method. | Rename instance attribute to `self.main_layout` or use local `main_layout = QVBoxLayout(self)`. |
| **C6: Qt Enum Attribute UserRole** | [`pypost/ui/presenters/collection_tree_actions.py`](file:///home/src/pypost/ui/presenters/collection_tree_actions.py) | `"type[Qt]" has no attribute "UserRole"`. | 4 errors (2 new, 2 baselined) | Legacy reference to `Qt.UserRole` instead of canonical PySide6 `Qt.ItemDataRole.UserRole`. | Replace with `Qt.ItemDataRole.UserRole` across [`collection_tree_actions.py`](file:///home/src/pypost/ui/presenters/collection_tree_actions.py). |
| **C7: Library Presenter API Alignment** | [`pypost/ui/presenters/library_presenter.py`](file:///home/src/pypost/ui/presenters/library_presenter.py) | Incompatible type `str \| None` for `library_id`; unexpected keyword arguments `auth` and `remote` for `list_branches`. | 3 errors | `GitLibraryService.clone` requires `library_id: str`; `GitLibraryService.list_branches` only accepts `(library_id, timeout)`. Presenter passed unhandled None and non-existent kwargs. | Provide fallback `library_id` derivation in `clone_library`; align `list_branches` call with `GitLibraryService.list_branches(lib_id)`. |
| **C8: Local Variable Disambiguation** | [`pypost/ui/presenters/tabs_presenter_draft.py`](file:///home/src/pypost/ui/presenters/tabs_presenter_draft.py) | Incompatible types in assignment (expression has type `McpClientConnection`, variable has type `WebSocketConnection`). | 1 error | Reused local variable `conn` previously inferred as `WebSocketConnection \| None` for `McpClientConnection`. | Use distinct local variable name `mcp_conn = tab.connection_data`. |
| **C9: Tab Type Narrowing** | [`pypost/ui/presenters/tabs_presenter_hotkeys.py`](file:///home/src/pypost/ui/presenters/tabs_presenter_hotkeys.py) | Incompatible return value type (got `QWidget \| None`, expected `RequestTab \| None`). | 1 error | Helper `_is_request_tab` returned plain `bool`, preventing mypy from narrowing `tab` from `QWidget \| None` to `RequestTab`. | Annotate helper as `TypeGuard[RequestTab]`. |
| **C10: Tab Presenter Index Of Tab Union** | [`pypost/ui/presenters/tabs_presenter.py`](file:///home/src/pypost/ui/presenters/tabs_presenter.py) | Argument 1 to `_index_of_tab` has incompatible type `McpClientTab`; expected `RequestTab \| WebSocketTab`. | 3 errors | `_index_of_tab` signature was not updated when `McpClientTab` support was introduced. | Expand `tab: RequestTab \| WebSocketTab \| McpClientTab` (or `QWidget`). |
| **C11: Environment Secrets Envelope Type Hint** | [`pypost/core/environment_variables_adapter.py`](file:///home/src/pypost/core/environment_variables_adapter.py) | Incompatible types in assignment (expression has type `EncryptedValueEnvelopeV2`, variable has type `EncryptedValueEnvelope`). | 1 error | `envelope` variable inferred from branch assigning v1 envelope, then assigned v2 envelope. | Explicitly type `envelope: EncryptedValueEnvelope \| EncryptedValueEnvelopeV2`. |
| **C12: QToolButton InstantPopup Stubs** | [`pypost/ui/widgets/mcp_client/mcp_client_tab.py`](file:///home/src/pypost/ui/widgets/mcp_client/mcp_client_tab.py)<br>[`pypost/ui/widgets/websocket/websocket_tab.py`](file:///home/src/pypost/ui/widgets/websocket/websocket_tab.py) | `"type[QToolButton]" has no attribute "InstantPopup"`. | 2 errors | Known PySide6 stub limitation where `QToolButton.InstantPopup` is not declared directly on `QToolButton` (matches existing baselined error in [`request_editor.py`](file:///home/src/pypost/ui/widgets/request_editor.py)). | Migrate to `QToolButton.ToolButtonPopupMode.InstantPopup` (or record in baseline consistent with `request_editor.py`). |
| **R1-R4: Resolved Baseline Entries** | [`pypost/core/request_service.py`](file:///home/src/pypost/core/request_service.py)<br>[`pypost/ui/widgets/request_editor.py`](file:///home/src/pypost/ui/widgets/request_editor.py)<br>[`pypost/core/environment_variables_adapter.py`](file:///home/src/pypost/core/environment_variables_adapter.py)<br>[`pypost/ui/dialogs/settings_dialog.py`](file:///home/src/pypost/ui/dialogs/settings_dialog.py) | 4 errors resolved in code but still listed in `mypy-baseline.json`. | 4 entries | Code refactoring resolved earlier typing defects without running `--update-baseline`. | Retire resolved entries via `scripts/check_mypy_baseline.py --update-baseline`. |

---

## Architecture

### System Module Diagram

The following Mermaid diagram shows the affected modules across `pypost/core` and `pypost/ui`, detailing how generic persistence contracts and protocol abstractions connect the presentation layer with model storage.

```mermaid
classDiagram
    direction TB

    namespace CoreDomainModels {
        class RequestData {
            +str id
            +str name
            +str url
            +str method
        }
        class WebSocketConnection {
            +str id
            +str name
            +str url
        }
        class McpClientConnection {
            +str id
            +str name
            +str server_command
        }
    }

    namespace SaveOrchestrators {
        class SaveAction {
            <<enumeration>>
            CANCELLED
            OVERWRITE
            CREATED_NEW
            SAVE_AS
        }
        class StaleCheckContext~T~ {
            +T | None persisted_baseline
            +bool stale_persisted
        }
        class SaveResult~T~ {
            +SaveAction action
            +T | None request
            +str | None collection_id
        }
        class RequestSaveOrchestrator {
            +save_request(data, parent, stale_context) SaveResult~RequestData~
            +save_as_request(data, parent) SaveResult~RequestData~
        }
        class WebSocketSaveOrchestrator {
            +save_profile(conn, parent, stale_context) SaveResult~WebSocketConnection~
            +save_as_profile(conn, parent) SaveResult~WebSocketConnection~
        }
        class McpClientSaveOrchestrator {
            +save_profile(conn, parent, stale_context) SaveResult~McpClientConnection~
            +save_as_profile(conn, parent) SaveResult~McpClientConnection~
        }
    }

    namespace PresenterAndUI {
        class TabClosePromptProtocol {
            <<protocol>>
            +__call__(parent, tab_title, *, has_unsaved_edits, has_active_connection) bool
        }
        class TabsPresenter {
            +_stale_context_for_tab(tab) StaleCheckContext~RequestData~
            +_stale_context_for_websocket_tab(tab) StaleCheckContext~WebSocketConnection~
            +_stale_context_for_mcp_client_tab(tab) StaleCheckContext~McpClientConnection~
            +_handle_save_request(tab, data)
            +_handle_save_websocket(tab, conn)
            +_handle_save_mcp_client(tab, conn)
            +_index_of_tab(tab) int | None
        }
    }

    namespace StreamExport {
        class StreamExportSourceProtocol {
            <<protocol>>
            +__len__() int
            +snapshot() tuple~StreamEntry, ...~
            +dropped dict~str, int~
        }
        class MessageStream {
            +__len__() int
            +snapshot()
            +dropped
        }
        class StreamExportSnapshot {
            +__len__() int
            +snapshot()
            +dropped
        }
    }

    StaleCheckContext~T~ <.. TabsPresenter : builds
    SaveResult~T~ <.. SaveOrchestrators : returns
    TabsPresenter --> RequestSaveOrchestrator : coordinates
    TabsPresenter --> WebSocketSaveOrchestrator : coordinates
    TabsPresenter --> McpClientSaveOrchestrator : coordinates
    TabClosePromptProtocol <.. TabsPresenter : receives
    StreamExportSourceProtocol <|.. MessageStream : satisfies
    StreamExportSourceProtocol <|.. StreamExportSnapshot : satisfies
```

### Module Responsibilities & Architectural Patterns

#### 1. Generic Parameterization Pattern (Save Orchestration)
- **Problem:** [`RequestSaveOrchestrator`](file:///home/src/pypost/ui/request_save_orchestrator.py), [`WebSocketSaveOrchestrator`](file:///home/src/pypost/ui/websocket_save_orchestrator.py), and [`McpClientSaveOrchestrator`](file:///home/src/pypost/ui/mcp_client_save_orchestrator.py) coordinate save/overwrite flows for three distinct protocol entities: [`RequestData`](file:///home/src/pypost/models/models.py), [`WebSocketConnection`](file:///home/src/pypost/models/websocket.py), and [`McpClientConnection`](file:///home/src/pypost/models/mcp_client.py).
- **Design:**
  - Define `T = TypeVar("T")` (or `ItemT = TypeVar("ItemT", bound=object)`).
  - Parameterize `StaleCheckContext[T]` and `SaveResult[T]` as generic dataclasses:
    ```python
    T = TypeVar("T")

    @dataclass(frozen=True)
    class StaleCheckContext(Generic[T]):
        persisted_baseline: T | None
        stale_persisted: bool

    @dataclass(frozen=True)
    class SaveResult(Generic[T]):
        action: SaveAction
        request: T | None = None
        collection_id: str | None = None
    ```
  - Note: The attribute `request: T | None` is retained as the field name to preserve 100% backward compatibility with keyword-argument callers (`SaveResult(..., request=...)`) and external test fixtures across the repository.
  - In `WebSocketSaveOrchestrator`:
    - `save_profile(..., stale_context: StaleCheckContext[WebSocketConnection] | None = None) -> SaveResult[WebSocketConnection]`
    - `save_as_profile(...) -> SaveResult[WebSocketConnection]`
  - In `McpClientSaveOrchestrator`:
    - `save_profile(..., stale_context: StaleCheckContext[McpClientConnection] | None = None) -> SaveResult[McpClientConnection]`
    - `save_as_profile(...) -> SaveResult[McpClientConnection]`
  - In [`TabsPresenter`](file:///home/src/pypost/ui/presenters/tabs_presenter.py):
    - `_stale_context_for_tab(...) -> StaleCheckContext[RequestData] | None`
    - `_stale_context_for_websocket_tab(...) -> StaleCheckContext[WebSocketConnection] | None`
    - `_stale_context_for_mcp_client_tab(...) -> StaleCheckContext[McpClientConnection] | None`
    - In `_handle_save_websocket` and `_handle_save_mcp_client`, `result.request` resolves cleanly to `WebSocketConnection | None` and `McpClientConnection | None` without requiring unsafe type casts or producing signal emission type mismatches.

#### 2. Structural Subtyping / Protocol Pattern (Tab Close Prompt Callbacks)
- **Problem:** Python's `Callable[[QWidget, str, bool, bool], bool]` assumes positional arguments. The dialog confirmation function [`prompt_deleted_websocket_profile_tab_close`](file:///home/src/pypost/ui/collection_item_dialogs.py#L131-L137) explicitly specifies keyword-only parameters (`*, has_unsaved_edits: bool, has_active_connection: bool`).
- **Design:**
  - Define `TabClosePromptProtocol` in `pypost/ui/collection_item_dialogs.py` (or `tabs_presenter_ws_close.py`):
    ```python
    class TabClosePromptProtocol(Protocol):
        def __call__(
            self,
            parent: QWidget,
            tab_title: str,
            *,
            has_unsaved_edits: bool,
            has_active_connection: bool,
        ) -> bool:
            ...
    ```
  - In `tabs_presenter_ws_close.py`, `tabs_presenter_mcp_close.py`, and `tabs_presenter.py`, replace `Callable[[QWidget, str, bool, bool], bool]` with `TabClosePromptProtocol`.

#### 3. Duck-Typing / Protocol Union Pattern (Stream Export Formatting)
- **Problem:** [`format_json_transcript`](file:///home/src/pypost/core/websocket_stream_export.py#L60), [`format_text_transcript`](file:///home/src/pypost/core/websocket_stream_export.py#L104), [`export_stream_to_json_file`](file:///home/src/pypost/core/websocket_stream_export.py#L143), and [`export_stream_to_text_file`](file:///home/src/pypost/core/websocket_stream_export.py#L166) are annotated with `stream: MessageStream`. The background worker [`WebSocketStreamExportWorker`](file:///home/src/pypost/core/qt/websocket_stream_export_worker.py) constructs an immutable [`StreamExportSnapshot`](file:///home/src/pypost/core/websocket_stream_export.py#L33) containing `snapshot()`, `dropped`, and `__len__()` to perform safe off-thread exports.
- **Design:**
  - In `pypost/core/websocket_stream_export.py`, widen the stream argument type to `MessageStream | StreamExportSnapshot` (both defined in that module or its sibling).
  - This preserves static safety while recognizing the legitimate immutable snapshot implementation.

#### 4. TypeGuard Pattern (Hotkeys Active Tab Resolution)
- **Problem:** [`_is_request_tab`](file:///home/src/pypost/ui/presenters/tabs_presenter_hotkeys.py#L158) returns `bool`. Mypy cannot narrow `presenter._tabs.currentWidget()` (type `QWidget | None`) to `RequestTab`.
- **Design:**
  - Annotate `def _is_request_tab(tab: object) -> TypeGuard[RequestTab]:`.
  - Calling `if _is_request_tab(tab): return tab` cleanly narrows the return type to `RequestTab`.

#### 5. Qt Enum & Shadowing Hygiene
- **`collection_tree_actions.py`:** Update all 4 occurrences of `Qt.UserRole` to `Qt.ItemDataRole.UserRole` to match the rest of the codebase and resolve the `attr-defined` error.
- **`settings_dialog.py`:** Replace `self.layout = QVBoxLayout(self)` with `main_layout = QVBoxLayout(self)` and use `main_layout.addWidget(...)`, preventing collision with inherited `QDialog.layout()`.
- **`library_dialogs.py`:** Wrap signal connections to `detail_panel.update_status` and `collections_panel.update_manifest` with lambda or typed adapter functions so `Signal(object)` connects without contravariance failures.
- **`library_presenter.py`:**
  - In `clone_library()`, guarantee `library_id: str` is provided (deriving from url slug `url.rstrip("/").split("/")[-1].removesuffix(".git")` if None).
  - In `list_branches()`, invoke `self.service.list_branches(lib_id)` directly, matching the `GitLibraryService` method signature.
- **`QToolButton.InstantPopup`:** Use `QToolButton.ToolButtonPopupMode.InstantPopup` or align with the existing `request_editor.py` baseline pattern.

#### 6. Ratchet Baseline Reconciliation
- Run `python scripts/check_mypy_baseline.py --update-baseline` once genuine defects are resolved.
- This automatically:
  - Discards the 4 resolved baseline errors (`environment_variables_adapter.py`, `request_service.py`, `settings_dialog.py`, `request_editor.py`).
  - Discards any baselined errors resolved by the above fixes (e.g. in `collection_tree_actions.py` and `settings_dialog.py`).
  - Freezes any legitimate unresolvable external stub issues into the ratchet manifest.

---

## Implementation Plan

### High-Level Phasing

1. **Phase 1 (Failing Repro — Step 3):**
   - Create an automated test in `tests/test_mypy_baseline_live.py` (or add to `tests/test_mypy_baseline.py`) that runs the live `check_mypy_baseline` gate and asserts `exit_code == 0` with zero unbaselined or stale errors.
   - Run the test via `make test` (or dedicated test filter) to prove it fails in red state against current HEAD (240 errors vs 201 baseline).
2. **Phase 2 (Core & Model Protocol Alignment — Step 4):**
   - Update `pypost/core/environment_variables_adapter.py` envelope type hint.
   - Update `pypost/core/websocket_stream_export.py` function signatures to accept `MessageStream | StreamExportSnapshot`.
3. **Phase 3 (Generic Save Orchestrators & Tabs Presenter — Step 4):**
   - Parameterize `SaveResult[T]` and `StaleCheckContext[T]` in `pypost/ui/request_save_orchestrator.py`.
   - Update `pypost/ui/websocket_save_orchestrator.py` and `pypost/ui/mcp_client_save_orchestrator.py` with generic type arguments.
   - Update `pypost/ui/presenters/tabs_presenter.py`: `_stale_context_*`, `_handle_save_*`, and expand `_index_of_tab`.
4. **Phase 4 (UI Presenters & Dialog Signatures — Step 4):**
   - Implement `TabClosePromptProtocol` in `pypost/ui/presenters/tabs_presenter_ws_close.py` and `tabs_presenter_mcp_close.py`.
   - Fix `tabs_presenter_draft.py` local variable collision (`mcp_conn`).
   - Add `TypeGuard[RequestTab]` to `tabs_presenter_hotkeys.py`.
   - Fix `collection_tree_actions.py` `Qt.ItemDataRole.UserRole`.
   - Fix `settings_dialog.py` layout attribute name.
   - Align `library_presenter.py` and `library_dialogs.py` signal connections and method calls.
   - Align `InstantPopup` references.
5. **Phase 5 (Baseline Update & Gate Verification — Step 4):**
   - Run `python scripts/check_mypy_baseline.py --update-baseline` to synchronize `mypy-baseline.json`.
   - Run `make typecheck` to verify the gate is 100% green with exit code 0.
   - Run `make check` (`make lint`, `make test`, `make verify-ai-tasks`) to verify overall repository integrity.

---

### Mandatory — Failing Repro (next Step 3)

- **Test Target:** Live typecheck baseline gate verification.
- **Location:** `tests/test_mypy_baseline_live.py` (or new test method in [`tests/test_mypy_baseline.py`](file:///home/src/tests/test_mypy_baseline.py)).
- **What it Asserts:**
  - Invokes `check_mypy_baseline.main()` (or runs `_run_mypy()` against `_load_baseline()`).
  - Asserts that `exit_code == 0`, `new_keys == []`, and `fixed_keys == []`.
- **How Failure is Observed Before Fixes:**
  - Running this test at current HEAD executes real mypy on `pypost/core`, `pypost/models`, `pypost/ui` and compares against the 201-item baseline.
  - Because current HEAD has 240 errors (33 new errors + 4 resolved errors), `check_mypy_baseline.main()` exits with 1, printing the new and resolved error reports, and the assertion fails with `AssertionError: exit_code 1 != 0` (RED).
- **Sequencing:**
  1. Write failing test in Step 3.
  2. Run test to demonstrate RED failure.
  3. Implement architectural fixes in Step 4 and update baseline.
  4. Run test to demonstrate GREEN pass.

---

## Q&A

- **Q: Why not use a union `RequestData | WebSocketConnection | McpClientConnection` instead of generics for `SaveResult`?**
  - **A:** A naive union on `SaveResult.request` weakens type safety across every consumer. When `TabsPresenter._handle_save_websocket` calls `self._ws_save_orchestrator.save_profile()`, it expects a `WebSocketConnection` back so it can pass it to `_apply_ws_save_result_to_tab(source_tab, saved)` and `self.websocket_persisted.emit(...)`. With a union, mypy would report that `RequestData` and `McpClientConnection` are not assignable to `WebSocketConnection`, shifting the type errors to every call site. Generic parameterization `SaveResult[WebSocketConnection]` guarantees compile-time type precision without casts.

- **Q: Why are `has_unsaved_edits` and `has_active_connection` keyword-only in `prompt_deleted_websocket_profile_tab_close`?**
  - **A:** For boolean parameters with similar types, Python keyword-only arguments prevent accidental argument transposition (e.g. passing `has_active_connection` where `has_unsaved_edits` was expected). Using a `Protocol` allows static type checkers to enforce this keyword-only contract on any prompt implementation.

- **Q: Why did `scripts/check_mypy_baseline.py` flag 4 resolved errors?**
  - **A:** The baseline operates as a strict ratchet. When an error recorded in the baseline is fixed in code, the ratchet requires removing that entry so the defect cannot be reintroduced in future commits. Running `--update-baseline` after fixing new errors retires these entries automatically.

- **Q: Will updating the baseline introduce non-determinism across developer machines?**
  - **A:** No. `scripts/check_mypy_baseline.py` strips all line numbers, keying errors strictly by `(path, code, message)`. The baseline is serialized with sorted keys and indent formatting, guaranteeing bitwise-identical output across environments.
