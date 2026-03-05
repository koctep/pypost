# Requirements: PYPOST-28 - Fix Crash on Request Retry

## Goals
Fix a critical bug where the application crashes when attempting to resend a request (e.g., by pressing Enter in the URL bar or F5) if the request was initiated not by clicking the "Send" button.

## User Stories
- As a user, I want to be able to resend a request using hotkeys (Ctrl+Enter, F5) without the application crashing.

## Acceptance Criteria
- [ ] The application does not crash when sending a request via hotkeys.
- [ ] The request is sent correctly from the active tab.

## Task Description
Investigate `handle_send_request` in `MainWindow`.
The problem is likely that `self.sender()` returns `None` or an object that is not a button when called via a hotkey, causing `sender_tab` to not be found.

### Technical Details
- **Component**: `MainWindow`.
- **Method**: `handle_send_request`.
