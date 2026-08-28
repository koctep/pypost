# PYPOST-1223: Technical Debt Analysis

## Shortcuts Taken

1. **Synchronous Presenter Operations with UI Modals**:
   - Operations like pull, commit, and push in `LibraryManagerDialog` execute synchronously on click, showing dialog progress.
   - For fast local operations and small repos, this completes in milliseconds. For slower network operations over high-latency links, running long-running operations in dedicated `QThread` workers with cancel tokens can be added.
   - *Impact*: Low for standard Git repositories; modular `LibraryPresenter` architecture allows worker threads without API changes.

2. **Commit File Selection Granularity**:
   - `LibraryCommitPushDialog` allows selecting individual files to commit (staging specific files). When all files are checked, it runs `git add -A`. When a subset is selected, it passes `git add -- <files>`.
   - Untracked files that are unchecked remain untracked.
   - *Impact*: Clean behavior; future iterations can add diff previewing per file.

## Code Quality Issues

1. **Static Error Mapping Table**:
   - Error messages for `GitDiagnosticErrorCode` are mapped statically in `LibraryPresenter.ERROR_MESSAGES`.
   - While comprehensive and clear, internationalization / localization (i18n) support could be integrated when PyPost adopts multi-language desktop UI resources.

2. **Branch List Refresh on Remote Fetch**:
   - `LibraryBranchSwitchDialog` lists branches known to the local repository and cached remotes. Triggering a remote fetch before opening the branch switch dialog ensures newly pushed remote branches appear immediately.

## Missing Tests

1. **Interactive QFileDialog File Picker**:
   - Unit tests verify `LibraryCloneDialog` form fields, auth parameters, and validation logic. The file dialog picker for SSH keys (`QFileDialog.getOpenFileName`) is standard Qt and asserted via mock/path inputs.

## Performance Concerns

1. **Status Polling on Multiple Connected Libraries**:
   - Opening the Library Manager scans and queries status for the selected library. If a user connects 50+ repositories, lazy background evaluation of non-selected libraries will ensure instantaneous dialog launch.

## Follow-up Tasks

All follow-up tasks belong to parent epic **[PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219)** (*Git-based Collection Libraries & Self-Contained Collection Format*):

1. **[`PYPOST-1224`](https://pypost.atlassian.net/browse/PYPOST-1224)** (Modernize Examples to Unified Library Format & Preserve Legacy Fixtures):
   - Update repository collection examples to unified library format and ensure legacy fixtures remain intact.
   - Target Epic: [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219).

2. **[`PYPOST-1228`](https://pypost.atlassian.net/browse/PYPOST-1228)** (Background Worker Thread for Asynchronous Git Push/Pull in UI):
   - Move `GitLibraryService` push/pull network operations to `QThread` workers with animated progress spinners in `LibraryManagerDialog`.
   - Target Epic: [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219).

3. **[`PYPOST-1229`](https://pypost.atlassian.net/browse/PYPOST-1229)** (Side-by-Side Diff Viewer in Commit Dialog):
   - Add a diff inspector widget inside `LibraryCommitPushDialog` to view line-by-line diffs of modified collection JSON/YAML files before committing.
   - Target Epic: [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219).

### Pre-existing Test Failures
- None (all test suites pass).
