# PYPOST-1063: Close Small Async Collection-Import Test Gaps

## Goals

Improve test coverage and verify critical edge cases for the asynchronous collection import workflow. Ensure that concurrent import attempts, unexpected worker failures, and status bar cue transitions are strictly tested and documented to prevent regressions in user feedback and error handling.

## Background

During the implementation of asynchronous collection import parsing in PYPOST-1005, several secondary test scenarios were identified in technical debt analysis:
1. Re-entrant / duplicate import clicks while a background parse is already active must be ignored and logged cleanly.
2. Unexpected exceptions during file reading/parsing must be caught, logged as errors, and surfaced gracefully to the user via invalid-file dialogs.
3. Status-bar transitions from preparing to completion or error must be asserted.
4. Parsing real, large JSON collection files from disk must remain responsive and complete successfully without blocking the main event loop.

## Scope

### In Scope
- Automated test coverage for busy re-entry prevention during import execution.
- Automated test coverage for unexpected exception handling during worker execution.
- Automated test coverage for status message feedback.
- Real-file JSON parsing test validating end-to-end responsiveness.

### Out of Scope
- Modifying UI layouts or dialog designs.
- Changing core collection data models or conflict resolution rules.

## Functional Requirements

1. **Busy Re-entry Prevention**: While an import parse worker is running (`is_busy() == True`), subsequent user requests to import must be rejected without launching duplicate worker threads.
2. **Robust Exception Handling**: If the injected reader raises an unhandled exception (e.g. `RuntimeError` or `IOError`), the worker must catch it, emit `parse_failed`, and present an invalid file error to the user without crashing the application.
3. **Status Feedback Lifecycle**: The UI status bar must display the preparing message when background parsing starts and clear or update when finished.
4. **Real File Parsing**: Verify that decoding and parsing a valid multi-record JSON file from disk completes asynchronously and updates the presenter collection model.

## Non-Functional Requirements

1. **Test Stability & Timeouts**: All tests must include explicit timeout markers (`pytestmark = pytest.mark.timeout(...)`) and use bounded asynchronous waiting helpers (`process_until`) per `do-testing`.
2. **Clean Logging**: Log events (`collection_import_skipped reason=busy`, `collection_import_parse_worker_failed`) must be verified via pytest's `caplog` fixture.

## User Scenarios

### Scenario 1: User Rapidly Clicks Import Button
- **Given** the user triggers an import on a large file.
- **When** the user clicks the Import button a second time while parsing is in progress.
- **Then** the second request is skipped with an informational log, avoiding duplicate dialogs or race conditions.

### Scenario 2: File Reading Raises Unexpected Error
- **Given** a corrupted file or unexpected reader failure.
- **When** the parse worker executes.
- **Then** the error is caught, logged with full exception details, and an error dialog is presented to the user.
