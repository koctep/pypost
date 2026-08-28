# Library Manager UI & Two-Way Git Flow

## Overview

As part of parent epic [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219) (*Git-based Collection Libraries & Self-Contained Collection Format*), **PYPOST-1223** delivers the desktop UI library manager panel, dirty check guards, and two-way Git commit/push workflow for connected collection libraries.

The UI provides an interactive desktop experience for discovering, inspecting, synchronizing, committing, and pushing collection libraries directly from the PyPost application.

### Core Capabilities

1. **Library Manager Dialog (`LibraryManagerDialog`)**:
   - Master-detail interface listing all connected Git collection libraries.
   - Real-time Git status header showing current branch, clean/dirty working tree state, and commit ahead/behind sync counts.
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
│   └── git_library.py           # Extended with COMMIT, PUSH operation types and fields
├── core/
│   └── git_service.py           # Extended with commit() and push() methods
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

- `tests/test_ui_library_manager_repro.py`: Repro test verifying models, widget IDs, presenter dirty guards, and two-way commit/push flow.
- `tests/test_ui_library_manager.py`: Comprehensive test suite verifying all dialog actions, hybrid authentication mode forms, branch selection, and presenter signals.
