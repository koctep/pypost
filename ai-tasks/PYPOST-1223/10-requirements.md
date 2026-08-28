# PYPOST-1223: [Libraries] UI library manager panel, dirty check guards, and two-way Git commit/push flow

## Goals

As part of parent epic [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219) (*Git-based Collection Libraries & Self-Contained Collection Format*), PyPost is introducing version-controlled collection libraries that engineering teams can share and collaborate on via Git repositories.

With the collection serialization format ([PYPOST-1220](https://pypost.atlassian.net/browse/PYPOST-1220)), the manifest schema validator and local overlay manager ([PYPOST-1221](https://pypost.atlassian.net/browse/PYPOST-1221)), and the core Git library backend service ([PYPOST-1222](https://pypost.atlassian.net/browse/PYPOST-1222)) established, users require an intuitive, first-class desktop UI experience to manage connected Git collection libraries.

Without a dedicated UI management interface:
1. **Lack of Visual Visibility**: Users cannot easily see which collection libraries are connected, what Git branches they are on, whether local changes are uncommitted (dirty), or how many commits their local copy is ahead or behind upstream remotes.
2. **Accidental Overwriting & Data Loss**: When pulling upstream updates, users editing collections need explicit visual warnings and confirmation modals if their working directory has unstaged or uncommitted changes, preventing destructive overwrites.
3. **Friction in Two-Way Collaboration**: Contributing local collection changes back to upstream Git repositories requires leaving PyPost to manually stage, commit, and push via external Git tools. A seamless, built-in commit and push workflow allows users to save and publish collection improvements directly within their workspace.
4. **Complex Onboarding & Cloning**: Connecting a new Git repository requires manual terminal setup unless a friendly cloning modal guides the user through entering repository URLs, selecting branches, and choosing appropriate hybrid authentication credentials (SSH agent, PAT tokens, or custom SSH private keys).

**Business Goal:**
Deliver an interactive desktop UI library manager panel and dialog suite in PyPost. The interface enables users to list and browse connected Git collection libraries, inspect synchronization status (branch, clean/dirty state, ahead/behind commit counts), trigger safe pulls with dirty-check guard warning modals, stage/commit/push local changes back to Git remotes, switch branches, and clone new libraries with hybrid authentication inputs.

## Programming Language

- **Implementation language**: Python (desktop UI dialogs/widgets, view controllers/presenters, integration with PySide6/Qt, service integration with GitLibraryService and LibraryManifest, and UI/unit tests).

## User Stories

- As an **API Designer / Collection Author**, I want to view my connected collection libraries in a visual manager panel, make local edits to collections, and stage, commit, and push those changes directly to the remote Git repository with a descriptive commit message, so that my team receives updated API requests without me needing external Git CLI tools.
- As a **QA Engineer / API Consumer**, I want to see visual indicators showing if a library is out-of-date (behind remote) and click a "Sync / Pull" button to retrieve the latest team updates, receiving a clear warning dialog if my local working tree is dirty so I do not accidentally lose uncommitted work.
- As a **Team Lead / Repository Maintainer**, I want to browse collections packaged inside a library, inspect repository status (current branch, commit hash, ahead/behind counts), switch active branches from a dropdown, and clone new private or public repositories using flexible authentication options (SSH agent, PAT, or SSH private key).
- As an **Automated Test / E2E Suite**, I want headless-compatible UI components and presenter actions that can be driven and asserted deterministically in automated tests without requiring interactive human prompts.

## Definition of Done

This task is considered complete when:

1. Business requirements, user stories, functional and non-functional requirements for the UI library manager panel, dirty check guards, and two-way Git flow are documented and accepted.
2. A **Library Manager Panel / Dialog** (`LibraryManagerDialog` / widget) is implemented in PyPost UI, accessible via main menu / toolbar actions.
3. A **Library List & Overview** view displays all connected libraries with real-time status indicators:
   - Library display name, version, and description.
   - Current Git branch name and tracking status.
   - Working tree cleanliness status (Clean vs. Dirty with modified file count).
   - Synchronization indicator showing commits ahead of and behind the upstream remote.
4. A **Collection Browser** displays all collections bundled within the selected library manifest, allowing users to inspect collection metadata and open/view collections in the workspace.
5. A **Sync / Pull Action with Dirty Check Guard Modal** is implemented:
   - Triggers an upstream pull when the working copy is clean.
   - If the working tree is dirty, displays a blocking warning modal listing modified/uncommitted files with options to abort or review before proceeding.
6. A **Two-Way Commit & Push Dialog** is implemented:
   - Displays list of modified, added, and deleted files in the library.
   - Provides commit message input field with validation (non-empty message required).
   - Allows selecting target branch and provides a single-action "Commit & Push" or separate "Commit" / "Push" workflow.
   - Integrates with hybrid authentication if remote push requires credentials.
7. A **Clone New Library Modal** is implemented:
   - Provides input fields for Git repository URL and optional custom library name / target folder.
   - Supports initial branch selection.
   - Offers hybrid authentication selection: System SSH Agent, Personal Access Token (PAT with token and username), and Custom SSH Private Key (key file path picker and optional passphrase).
   - Executes clone operation, validates discovered manifest, and registers library in the UI list.
8. A **Branch Switcher UI** allows users to discover available local and remote branches and switch the working branch with safety dirty checks.
9. A **Disconnect / Remove Library Action** allows unregistering or deleting a connected library with confirmation.
10. Scope boundaries are strictly respected: GUI panels and view controllers integrate with existing `GitLibraryService` ([PYPOST-1222](https://pypost.atlassian.net/browse/PYPOST-1222)) and `LibraryManifest` / `LocalOverlayManager` ([PYPOST-1221](https://pypost.atlassian.net/browse/PYPOST-1221)); legacy fixture modernization remains in [PYPOST-1224](https://pypost.atlassian.net/browse/PYPOST-1224).
11. Comprehensive test suite verifies UI controllers, dialogs, state updates, dirty check modals, commit/push flows, branch switching, and error handling.
12. Full repository quality gates pass (`make check`, `make lint`, `make typecheck`, `make test`, `make verify-ai-tasks`).

## Task Description

### Problem

While the backend services for Git operations (`GitLibraryService`) and manifest validation (`LibraryManifest`) exist, end users interact with PyPost through a graphical desktop interface. Without UI integration:
- Users cannot discover, inspect, or manage their cloned collection libraries within the application.
- Pulling remote changes poses a risk of silently losing local edits if uncommitted modifications are present and no visual warning is shown.
- Pushing updates back to shared team repositories requires exiting PyPost to run terminal Git commands, breaking workflow continuity.
- Non-technical or GUI-focused users cannot easily clone repositories or configure authentication methods without manual configuration.

### Current State (Inventory)

- **Collection Serialization & Models** ([PYPOST-1220](https://pypost.atlassian.net/browse/PYPOST-1220)):
  - `Collection` and `CollectionVariable` domain models and YAML/JSON serialization.
- **Library Manifest & Local Overlay** ([PYPOST-1221](https://pypost.atlassian.net/browse/PYPOST-1221)):
  - `LibraryManifest` model, manifest validator, and `LocalOverlayManager` for user secrets.
- **Git Backend Service** ([PYPOST-1222](https://pypost.atlassian.net/browse/PYPOST-1222)):
  - `GitLibraryService` supporting clone, fetch, pull, status, list_branches, checkout, dirty check guards, and hybrid authentication adapters (`GitAuthConfig`, `GitAuthMode`).
- **Missing Capabilities (Addressed in This Task)**:
  - No visual Library Manager panel/dialog in PyPost UI to list connected libraries.
  - No visual status badges for Git branch, clean/dirty state, or ahead/behind counts.
  - No UI pull action with dirty check warning modal.
  - No commit & push dialog for authoring commit messages and pushing local edits.
  - No clone modal with hybrid authentication inputs.
  - No branch switching UI controls.

### Scope (This Task)

- Implement UI components and presenters for:
  - **Library Manager Main Panel/Dialog**: Connected library list, selected library details, status header, collection list, and action buttons.
  - **Status Indicators**: Visual badges or labels showing current branch, clean/dirty state (with dirty file count), and synchronization status (ahead/behind counts).
  - **Sync / Pull Action & Guard Modal**: Pull button triggering status check, displaying a warning modal when dirty changes are detected, or executing pull when clean.
  - **Two-Way Commit & Push Dialog**: Dialog displaying modified files, commit message input, branch selector, and commit/push execution.
  - **Clone Library Dialog**: Modal capturing Git URL, branch, and hybrid auth configuration (SSH Agent, HTTPS PAT, Custom SSH Key) and triggering clone + manifest discovery.
  - **Branch Switching Interface**: Dropdown or dialog listing local and remote branches to checkout.
  - **Remove / Disconnect Action**: Confirming and removing a connected library.
- Integrate UI presenters with `GitLibraryService`, `LibraryManifest`, and `LocalOverlayManager`.
- Provide robust error handling, progress indicators, and non-blocking background execution for Git operations.

### Out of Scope (This Task)

- Core Git CLI operations service and credential helpers (implemented in [PYPOST-1222](https://pypost.atlassian.net/browse/PYPOST-1222)).
- Manifest schema validation and secret overlay storage backend (implemented in [PYPOST-1221](https://pypost.atlassian.net/browse/PYPOST-1221)).
- Example library updates and test fixture modernization (assigned to [PYPOST-1224](https://pypost.atlassian.net/browse/PYPOST-1224)).
- Merge conflict resolution editor (complex 3-way merge tools); if conflicts arise, diagnostic error is displayed instructing resolution.

### Functional Requirements

- **FR-1: Library Manager Panel & Connected Library Listing**
  - The system shall provide a dedicated Library Manager panel or dialog displaying all locally connected collection libraries.
  - Each library item in the list shall show the library display name, version, and current sync status.
  - Selecting a library from the list shall populate the detail view with library metadata, collection list, and available Git actions.

- **FR-2: Real-Time Git Status & Visual State Indicators**
  - The UI shall display comprehensive status information for the selected library:
    - **Current Branch**: Active Git branch name or detached HEAD state.
    - **Working Tree State**: Visual badge showing "Clean" or "Dirty (N modified files)".
    - **Sync State**: Visual indicator showing commits ahead of and behind upstream remote (e.g. `↑2 ↓1` or `Up to date`).
    - **Latest Commit**: Abbreviated commit hash and commit message summary.
  - The UI shall provide a "Refresh" action to re-query the repository status on demand.

- **FR-3: Collection Browsing within Libraries**
  - The UI shall list all collection files declared in the library manifest.
  - For each collection, the UI shall display the collection name, relative file path, request count, and description.
  - Users shall be able to click a collection to inspect its details or load it into the main PyPost collection workspace.

- **FR-4: Safe Sync / Pull Action with Dirty Check Guard Warning Modal**
  - The UI shall provide a "Sync" / "Pull" action button for the selected library.
  - Before executing the pull, the system shall evaluate the repository's dirty state via the dirty check guard.
  - If the working tree is dirty (modified, staged, or untracked conflicting files exist), the UI shall display a modal warning dialog:
    - Explaining that local uncommitted changes may be affected.
    - Listing the modified/dirty file paths.
    - Providing clear options: "Cancel" (abort pull) or "Commit Changes First" (redirect to Commit Dialog).
  - If the working tree is clean, the pull shall proceed, displaying progress and updating the UI status upon completion.

- **FR-5: Two-Way Git Commit & Push Flow Dialog**
  - The UI shall provide a "Commit & Push" (or "Commit Changes") action when a library has dirty changes or is ahead of remote.
  - The commit dialog shall include:
    - A file list showing all modified, staged, and untracked files with change status (Modified, Added, Deleted).
    - A multi-line commit message input area.
    - Validation ensuring the commit message is not empty.
    - Options to "Commit & Push" (atomic stage, commit, and push to upstream) or "Commit Only".
    - Integration with authentication credentials if pushing to a remote that requires PAT or SSH credentials.
  - Upon successful commit/push, the dialog shall close, notify the user, and refresh the library status to clean.

- **FR-6: Clone New Library Modal with Hybrid Authentication Inputs**
  - The UI shall provide a "Clone Library" action opening a modal with:
    - Repository URL input (HTTPS or SSH format).
    - Optional Target Library ID / Folder Name.
    - Optional Initial Branch / Tag input.
    - Authentication Mode selector offering three options:
      1. **System SSH Agent**: No additional input required.
      2. **Personal Access Token (PAT)**: Inputs for Username and Secret Token (masked input).
      3. **Custom SSH Key**: File picker for private key path and optional passphrase input (masked).
  - Submitting the modal shall execute the clone in the background with progress feedback.
  - Upon successful clone, the system shall discover the manifest, register the library, and select it in the Library Manager list.

- **FR-7: Branch Discovery & Branch Switching UI**
  - The UI shall provide a branch switcher (e.g. dropdown or dialog) showing all available local and remote branches for the selected library.
  - Selecting a branch shall invoke the checkout operation.
  - If the working tree is dirty, branch switching shall be blocked by the dirty check guard with an informative warning dialog.
  - Upon switching branches, the UI shall refresh and reload the corresponding library manifest and collections.

- **FR-8: Library Disconnect / Deletion**
  - The UI shall provide an option to disconnect or delete a connected library.
  - A confirmation dialog shall ask the user whether to disconnect the library (remove from registry) or delete the repository files from disk.
  - Deleting a library shall also clean up associated local overlay data if confirmed.

- **FR-9: Actionable Error Handling, Diagnostics & Notifications**
  - Any failed Git operation (clone error, auth failure, network timeout, merge conflict) shall be caught gracefully.
  - The UI shall display user-friendly error banners or dialogs containing actionable diagnostic messages rather than raw stack traces.
  - Long-running network operations (clone, fetch, pull, push) shall show progress spinners or disabled button states to prevent duplicate submissions.

- **FR-10: Main Window Navigation & Menu/Toolbar Integration**
  - The Library Manager shall be easily accessible from PyPost's main application menu (e.g., `Tools -> Library Manager` or `Libraries -> Manage Libraries`) and toolbar shortcut.
  - Status indicators or badges in the main window shall alert users if active libraries have pending updates or dirty changes.

### Non-Functional Requirements

- **NFR-1 UI Responsiveness & Non-Blocking Execution**: All network and disk Git operations (clone, fetch, pull, push, status) must execute asynchronously or with progress feedback so the desktop UI remains responsive and does not freeze or block the event loop.
- **NFR-2 Safety & Data Loss Prevention**: Dirty check guards must be enforced before every mutating operation (pull, checkout, branch switch). The UI must never offer an option to silently discard uncommitted user changes without explicit confirmation.
- **NFR-3 Usability & Clear Visual Feedback**: Status indicators (Clean, Dirty, Ahead, Behind, Current Branch) must be visually prominent using intuitive icons, colors, and concise badge counts.
- **NFR-4 Testability & Headless UI Automation**: UI dialogs, widgets, and view controllers must be fully testable with automated PySide6/Qt unit tests and headless test fixtures, supporting mock Git services and simulated user actions.
- **NFR-5 Cross-Platform Consistency & Theme Compatibility**: UI widgets and dialog layouts must render correctly across Linux, macOS, and Windows, adhering to standard PyPost styling and theme guidelines (dark/light themes).

### Constraints and Assumptions

- Python and PySide6/Qt are the implementation frameworks for desktop UI components.
- The UI layer delegates Git commands to `GitLibraryService` ([PYPOST-1222](https://pypost.atlassian.net/browse/PYPOST-1222)) and manifest inspection to `LibraryManifest` / `LocalOverlayManager` ([PYPOST-1221](https://pypost.atlassian.net/browse/PYPOST-1221)).
- Network operations require internet connectivity and valid remote Git credentials.
- Git CLI must be installed on the host system.

### Main Entities (Business Perspective)

| Entity | Description | Key Business Attributes |
| --- | --- | --- |
| **Library Manager View / Dialog** | Main user interface container for viewing and managing connected Git libraries. | Library List, Selected Library Details, Action Toolbars, Refresh Trigger |
| **Library Status Presentation** | Visual model representing the real-time Git state of a library. | Display Name, Branch Name, Clean/Dirty Status, Dirty Files Count, Ahead Count, Behind Count, Latest Commit Summary |
| **Dirty Check Warning Modal** | Guard dialog alerting the user to uncommitted changes before destructive actions. | Modified Files List, Warning Message, Cancel Action, Commit Action |
| **Commit & Push Dialog** | Interactive modal for staging, authoring commit messages, and pushing changes. | Changed Files Checklist, Commit Message Field, Target Branch Selector, Commit & Push Action |
| **Clone Library Dialog** | Modal interface for entering remote repository parameters and credentials. | Remote URL, Library Name/ID, Initial Branch, Auth Mode (SSH Agent / PAT / Custom Key), Credentials Inputs |
| **Branch Switcher** | Interface control for discovering and selecting active Git branches. | Local Branches List, Remote Branches List, Current Branch Indicator, Checkout Action |
| **Collection Inspector** | Sub-view displaying collections packaged in the active library manifest. | Collections List, File Paths, Request Counts, Open in Workspace Action |

## Q&A

| Question | Answer |
| --- | --- |
| **How does the UI prevent users from losing uncommitted collection edits during a pull?** | Before initiating a pull, the UI invokes the dirty check guard. If uncommitted changes exist, the operation is paused and a warning modal appears listing the modified files with options to cancel or commit changes first. |
| **Can users commit and push changes directly from PyPost without using terminal Git commands?** | Yes. The Commit & Push dialog provides a complete two-way sync flow: users review modified files, write a commit message, and submit a single action to stage, commit, and push changes to the remote repository. |
| **What authentication methods are available when cloning a repository from the UI?** | The Clone dialog supports all three hybrid authentication modes: (1) System SSH Agent, (2) Personal Access Token (PAT with username and token), and (3) Custom SSH Private Key (with key file picker and optional passphrase). |
| **How are secrets and local variable overrides kept out of Git commits?** | As established in PYPOST-1221, secret values and local overrides are stored in `~/.pypost/libraries_data/`, which is outside the Git repository directory (`~/.pypost/libraries/`). The Commit dialog only tracks files within the Git working tree, ensuring secrets are never staged or pushed. |
| **Where does the Library Manager fit in the main PyPost interface?** | It is accessible via the main application menu (`Libraries -> Manage Libraries`) and a dedicated toolbar button, opening as a modal dialog or dockable manager panel. |
| **Is backend Git CLI logic implemented in this task?** | No. Backend Git operations, credential helpers, and repository status checks were implemented in PYPOST-1222. This task implements the UI panels, dialogs, presenters, dirty check modals, and their integration with the Git service. |

## References

- [PYPOST-1223](https://pypost.atlassian.net/browse/PYPOST-1223) — This task: *UI library manager panel, dirty check guards, and two-way Git commit/push flow*
- [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219) — Parent Epic: *Git-based Collection Libraries & Self-Contained Collection Format*
- [PYPOST-1220](https://pypost.atlassian.net/browse/PYPOST-1220) — Preceding story: *Core schema and serializers for self-contained collection format with variable metadata*
- [PYPOST-1221](https://pypost.atlassian.net/browse/PYPOST-1221) — Preceding story: *Library manifest schema validator and local secrets overlay manager*
- [PYPOST-1222](https://pypost.atlassian.net/browse/PYPOST-1222) — Preceding story: *Git repository clone, pull, and hybrid auth service*
- [PYPOST-1224](https://pypost.atlassian.net/browse/PYPOST-1224) — Sibling story: *Modernize examples to unified library format and preserve legacy fixtures in tests*
- `pypost/core/git_service.py` — Git library service implementation
- `pypost/core/git_auth.py` — Hybrid authentication manager
- `pypost/models/git_library.py` — Git domain and status models
- `pypost/core/library_manifest.py` — Library manifest models and validators
- `pypost/core/local_overlay_manager.py` — Local overlay manager
