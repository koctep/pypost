# Library Manager UI & Two-Way Git Flow

## Overview

As part of parent epic [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219) (*Git-based Collection Libraries & Self-Contained Collection Format*), **PYPOST-1223** delivers the desktop UI library manager panel, dirty check guards, and two-way Git commit/push workflow for connected collection libraries.

The UI provides an interactive desktop experience for discovering, inspecting, synchronizing, committing, and pushing collection libraries directly from the PyPost application. PYPOST-1278 extends this flow with durable connection records, local-directory registration, source-aware lifecycle actions, stale status handling, and a manageable model/view list.

### Core Capabilities

1. **Library Manager Dialog (`LibraryManagerDialog`)**:
   - Master-detail interface listing all connected collection libraries, including local directories without a remote.
   - Git status header showing current branch, clean/dirty/unavailable working tree state, and commit ahead/behind sync counts.
   - Bundled collections viewer displaying all collections declared in the library manifest.
2. **Dirty Check Guard Modal (`LibraryDirtyPullWarningDialog`)**:
   - Intercepts pull operations when uncommitted local edits or untracked files are present.
   - Displays modified file paths and presents options to abort or navigate directly to the commit dialog.
3. **Two-Way Commit & Push Flow (`LibraryCommitPushDialog`)**:
   - Allows users to select files to stage and author descriptive commit messages.
   - Supports "Commit Only" and "Commit & Push" actions with remote upstream tracking.
4. **Clone Dialog with Hybrid Authentication (`LibraryCloneDialog`)**:
   - Form-based wizard for cloning public or private Git collection repositories.
   - Configures authentication modes: System SSH Agent, Personal Access Token (PAT), or Custom SSH Private Key with passphrase.
5. **Branch Switching UI (`LibraryBranchSwitchDialog`)**:
   - Enumerates local and remote branches for checkout with safety dirty checks.
6. **Presenter Coordination (`LibraryPresenter`)**:
   - Decoupled `QObject` presenter handling background Git service calls, manifest loading, status caching, and structured diagnostic error presentation.

---

## Architecture & Components

```text
pypost/
├── models/
│   ├── git_library.py            # Git operation and repository status models
│   └── library_manager.py       # Connection, row, status, and operation guard models
├── core/
│   ├── git_service.py            # Git lifecycle and path-aware operations
│   ├── library_connection_store.py # Durable connection registry
│   ├── library_manager_service.py  # Connection-aware business facade
│   ├── library_status.py         # Status normalization and stale-state rules
│   └── qt/library_operation_worker.py # Bounded worker boundary for UI operations
└── ui/
    ├── widget_ids.py            # Automation identifiers for library manager surfaces
    ├── main_window.py           # Menu bar and top-bar button integration
    ├── presenters/
    │   └── library_presenter.py # LibraryPresenter coordinating UI state and GitLibraryService
    ├── widgets/
    │   └── library_manager_panel.py # LibraryListWidget, LibraryDetailWidget, LibraryCollectionsWidget
    └── dialogs/
        └── library_dialogs.py   # LibraryManagerDialog, CloneDialog, CommitPushDialog, GuardDialogs
```

## Connection and Status Contract

`LibraryConnectionStore` persists connection metadata atomically in the user's PyPost configuration directory. A connection is one of two explicit source types:

- **Registered local directory**: points at an existing directory without cloning it. Connecting and disconnecting do not rewrite or delete the directory; explicit user-approved Git actions such as commit, pull, or checkout can mutate it through path-aware methods.
- **Cloned managed copy**: is created below the Git service's managed clone root. Delete is available only for an authoritative cloned record, after confirmation and managed-root containment checks; it also removes the associated overlay.

Rows use the manifest/library stable ID for identity and retain the exact `local_path` separately. Display names fall back to the stable ID when a manifest name is unavailable. Clone URLs are sanitized before persistence, including userinfo, sensitive query values, and fragments.

Status snapshots distinguish ordinary synchronization from conditions that need operator attention:

- The synchronization values are `Checking`, `Unknown`, `Local changes and remote updates`, `Local changes`, `Remote updates available`, `Locally ahead`, `No remote source`, and `Current`.
- The deterministic status sort order is exactly the order above; `Checking` sorts first and `Current` last.
- `Offline`, `Unavailable`, `Invalid`, and `Error` are independent conditions. `Stale` is added when the last successful snapshot is being shown.
- `Offline` means the remote probe failed while local facts remain available; the row is marked `Stale` and retains the last successful local snapshot.
- `Unavailable` means the local path or manifest/collection files cannot be read.
- `Invalid` means manifest validation failed.

## Model/View and Operation Boundaries

`LibraryListWidget` renders a typed `LibraryEntryListModel` through a `LibraryEntryFilterProxyModel`. The source model owns stable-ID rows and deterministic sorting; the proxy owns case-insensitive search and exact status filtering. Selection and path-copy actions use the stable ID and exact local path rather than display text.

Most user-triggered Git mutations and explicit refresh/check/branch actions use `LibraryPresenter.run_operation_async()`, which admits one operation per library/operation pair and dispatches it to `LibraryOperationWorker`. Completion, failure, and blocked safety guards return to the presenter through Qt signals; duplicate admission is reported immediately as `False` with a warning log and rejection metric. Initial list loading synchronously reads the small connection registry, and selection synchronously loads its manifest (and can synchronously refresh status) for immediate detail rendering. The presenter and service retain other synchronous methods for compatibility and unit-test seams, so callers must keep those I/O methods off the GUI thread. Dirty-tree checks run before pull, checkout, and commit/push flows.

## Observability

The presenter emits structured `INFO`, `WARNING`, and `ERROR` events named `library_operation_started`, `library_operation_completed`, `library_operation_blocked`, `library_operation_rejected`, and `library_operation_failed`. Events contain only a bounded library identifier, operation, outcome, and exception type; credentials, Git URLs, file contents, and local paths are excluded. Path-derived local-connect operation IDs are opaque hashes; normal registered-library operations use their stable IDs.

The existing metrics stack exposes `gui_library_operations_total{operation,outcome}` for the bounded operation vocabulary (`refresh`, `check_dirty`, `pull`, `commit`, `push`, `commit_and_push`, `switch_branch`, `list_branches`, `clone`, `connect`, `disconnect`, and `delete`) and outcomes (`started`, `success`, `failure`, `blocked`, and `rejected`). The Prometheus registry, Qt metrics manager, and OpenTelemetry tracker share the same labels.

## Usage and API

Open **Collection Libraries** from the main-window Library Manager button or menu action. Select a row to inspect its manifest, status, collections, and exact local path. Use **Connect** to register an existing manifest directory, **Clone** to create a managed copy, **Refresh** to recheck status, **Copy path** to copy the exact directory, and **Disconnect** to forget a connection without deleting its files. **Delete** is offered only for cloned rows and always requires explicit confirmation before removing the managed copy. Canceling any add, disconnect, or delete dialog before submission leaves the connection record and local files unchanged.

The presenter entry points used by the dialog are `load_libraries()`, `connect_local_library_async()`, `clone_library_async()`, `refresh_status_async()`, `check_dirty_async()`, `pull_library_async()`, `commit_library_async()`, `commit_and_push_async()`, `switch_branch_async()`, `disconnect_library_async()`, and `delete_library_async()`. Keep service calls behind `LibraryManagerService` when adding a new manager action so registered directories continue to use path-aware Git methods.

## Configuration

`LibraryConnectionStore` writes the atomic connection registry to `~/.pypost/library_connections.json` by default. Managed Git clones live under `~/.pypost/libraries` unless `GitLibraryService(base_dir=...)` is injected. A clone ID must be a single non-empty path component; absolute and traversal IDs are rejected before Git runs. The application passes its configured metrics manager into the Library Manager presenter; isolated tests may use the no-op metrics implementation.

## Troubleshooting

- **Offline / Stale**: the local directory is readable but the remote probe failed. Local branch and dirty facts are retained; check connectivity and refresh.
- **Unavailable**: the path, manifest, or declared collection file cannot be read. The detail panel shows `Status unavailable` rather than claiming the tree is clean.
- **Invalid**: the manifest is missing, malformed, or references absent collection files. Correct the manifest or collection files and refresh.
- **Pull or checkout blocked**: commit or stash the listed local changes first; the manager does not discard dirty work automatically.
- **Clone validation/registration failure**: the newly created managed directory is removed before the diagnostic is returned. If cleanup fails, inspect the error log by event name and exception type; credentials and paths are not emitted by the manager's event.
- **Baseline test failures**: consult the PYPOST-1261 and PYPOST-1262 links in Testing & Verification below before changing unrelated parser, Qt, audit, or Make lifecycle code.

### Automation Identities (`pypost.ui.widget_ids`)

| Identifier Constant | Value | Description |
| --- | --- | --- |
| `LIBRARY_MANAGER_BUTTON` | `pypost_library_manager_button` | Top-bar button to open Library Manager |
| `LIBRARY_MANAGER_DIALOG` | `pypost_library_manager_dialog` | Main Library Manager window |
| `LIBRARY_LIST` | `pypost_library_list` | Connected libraries list widget |
| `LIBRARY_CLONE_BUTTON` | `pypost_library_clone_button` | Button to open clone dialog |
| `LIBRARY_PULL_BUTTON` | `pypost_library_pull_button` | Button to trigger sync/pull |
| `LIBRARY_COMMIT_PUSH_BUTTON` | `pypost_library_commit_push_button` | Button to open commit & push dialog |
| `LIBRARY_SWITCH_BRANCH_BUTTON` | `pypost_library_switch_branch_button` | Button to open branch switch dialog |
| `LIBRARY_DELETE_BUTTON` | `pypost_library_delete_button` | Button to remove library |
| `LIBRARY_DIRTY_BADGE` | `pypost_library_dirty_badge` | Working tree clean/dirty badge |
| `LIBRARY_BRANCH_BADGE` | `pypost_library_branch_badge` | Active Git branch badge |
| `LIBRARY_SYNC_BADGE` | `pypost_library_sync_badge` | Ahead/behind sync status badge |
| `LIBRARY_COLLECTIONS_LIST` | `pypost_library_collections_list` | Bundled collections list widget |
| `LIBRARY_CLONE_DIALOG` | `pypost_library_clone_dialog` | Clone repository dialog |
| `LIBRARY_COMMIT_PUSH_DIALOG` | `pypost_library_commit_push_dialog` | Two-way commit and push dialog |
| `LIBRARY_DIRTY_PULL_WARNING_DIALOG` | `pypost_library_dirty_pull_warning_dialog` | Dirty working tree pull guard dialog |
| `LIBRARY_BRANCH_SWITCH_DIALOG` | `pypost_library_branch_switch_dialog` | Branch switcher dialog |

---

## Testing & Verification

- `tests/test_ui_library_manager_pypost_1278_repro.py`: Focused PYPOST-1278 coverage for rows, filtering/sorting, stale status, source-safe lifecycle, clone cleanup, async admission, observability, and path redaction. The module has a 30-second timeout marker.
- `tests/test_ui_library_manager_repro.py`: Earlier repro coverage for models, widget IDs, presenter dirty guards, and two-way commit/push flow.
- `tests/test_ui_library_manager.py`: Comprehensive test suite verifying all dialog actions, hybrid authentication mode forms, branch selection, and presenter signals.

Run the focused checks through the repository Make targets:

```bash
make test PYTEST_ARGS='tests/test_ui_library_manager_pypost_1278_repro.py tests/test_ui_library_manager.py tests/test_ui_library_manager_repro.py -q'
make lint
make typecheck
```

When a clone succeeds at Git level but manifest validation or registry registration fails, the manager removes the newly created managed directory before re-raising the diagnostic. If this cleanup itself fails, the event is logged by type only and the original failure remains the user-facing error.

Known unrelated baseline issues remain tracked in [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261) (nested-expression diagnostics, Qt SIGSEGV, and audit snapshot) and [PYPOST-1262](https://pypost.atlassian.net/browse/PYPOST-1262) (load-sensitive Make lifecycle timeouts). Do not duplicate or fix those issues while changing the Library Manager.
