# Requirements: PYPOST-5 - Hotkeys

## Problem/Task Description
The PyPost application lacks support for hotkeys for quick access to main functions. Users have to use the mouse to perform frequent operations, which reduces work efficiency. It is necessary to add a system of hotkeys to speed up work with the application.

## Programming Language
**Python** (PySide6/Qt for UI)

## Functional Requirements

### Mandatory Hotkeys (Requested by User)

1. **Exit Application**
   - Hotkey: `Ctrl+Q` (Linux/Windows standard) or `Cmd+Q` (macOS)
   - Action: Close the application (optionally saving unsaved changes if required in future)

2. **Send HTTP Request**
   - Hotkey: `Ctrl+Enter` or `F5`
   - Action: Send current request in the active tab
   - Context: Should work only when focus is in the request editing area (URL, Params, Headers, Body)

3. **Save Request**
   - Hotkey: `Ctrl+S`
   - Action: Open save request dialog (or save if already saved)
   - Context: Should work in the active request tab

### Additional Proposed Hotkeys

4. **Create New Request/Tab**
   - Hotkey: `Ctrl+N` or `Ctrl+T`
   - Action: Create a new tab with an empty request
   - Priority: High (frequently used operation)

5. **Close Current Tab**
   - Hotkey: `Ctrl+W`
   - Action: Close active tab
   - Priority: High (standard operation in most apps)

6. **Switch Between Tabs**
   - Hotkeys: `Ctrl+Tab` (next), `Ctrl+Shift+Tab` (previous)
   - Action: Switch between open tabs
   - Priority: High (navigation convenience)

7. **Switch to Specific Request Tab**
   - Hotkeys: `Alt+1`, `Alt+2`, `Alt+3`, ..., `Alt+9`
   - Action: Switch to request tab with specified number (1-9) in main window
   - Context: Works at MainWindow level
   - Priority: Medium (useful with many tabs)

8. **Open Settings**
   - Hotkey: `Ctrl+,` (comma) or `F12`
   - Action: Open settings dialog
   - Priority: Medium

9. **Manage Environments**
   - Hotkey: `Ctrl+E`
   - Action: Open environment management dialog
   - Priority: Medium

10. **Cancel/Close Dialog**
    - Hotkey: `Escape`
    - Action: Close active dialog or cancel operation
    - Priority: High (standard behavior)

11. **Focus on URL Field**
    - Hotkey: `Ctrl+L` or `Alt+D`
    - Action: Set focus to URL input field in active tab
    - Priority: Medium (convenient for quick URL entry)

12. **Switch Between Request Editor Tabs (Params/Headers/Body)**
    - Hotkeys: `Ctrl+P` (Params), `Ctrl+H` (Headers), `Ctrl+B` (Body)
    - Action: Switch between request editing tabs (Params, Headers, Body)
    - Context: Works only when focus is in RequestWidget (request editing area)
    - Note: Mnemonic combinations used (P - Params, H - Headers, B - Body)
    - Priority: Medium (convenient for quick switching between editor tabs)

## Non-functional Requirements

1. **Platform Compatibility**
   - Hotkeys must work on Linux, Windows, and macOS
   - Account for differences in standard combinations (Ctrl vs Cmd on macOS)

2. **Conflict Handling**
   - Hotkeys must not conflict with standard Qt combinations
   - In case of conflict, priority is given to standard Qt actions (e.g., Ctrl+C for copy)

3. **Context Activation**
   - Hotkeys should activate only in the appropriate context
   - For example, Ctrl+Enter for sending request works only when focus is in request editing area

4. **Visual Feedback**
   - Visual feedback should be provided when hotkeys are pressed (if applicable)
   - For example, when sending a request, the "Send" button should change state

5. **Performance**
   - Hotkey processing should not affect application performance
   - Use efficient Qt mechanisms for keyboard event processing

## Constraints and Assumptions

1. **Qt Mechanism**
   - Use `QShortcut` or `keyPressEvent` mechanism from PySide6/Qt
   - Hotkeys are processed at widget or main window level

2. **Standard Combinations**
   - Do not override standard Qt combinations (Ctrl+C, Ctrl+V, Ctrl+A, etc.)
   - Preserve standard behavior of text input fields

3. **Modal Dialogs**
   - Hotkeys should work correctly when modal dialogs are open
   - Escape should close dialogs

4. **Multilingualism**
   - Hotkeys do not depend on interface language
   - Key combinations are universal for all keyboard layouts

## Main Entities and Their Attributes

- **MainWindow (UI)**
  - **Methods for handling hotkeys:**
    - `handle_exit()` - exit application
    - `handle_new_tab()` - create new tab
    - `handle_close_tab()` - close current tab
    - `handle_next_tab()` - switch to next tab
    - `handle_previous_tab()` - switch to previous tab
    - `handle_switch_to_tab(index)` - switch to specific tab
    - `handle_open_settings()` - open settings
    - `handle_open_environments()` - open environment management
    - `handle_focus_url()` - focus on URL field

- **RequestWidget (UI)**
  - **Methods for handling hotkeys:**
    - `handle_send_request()` - send request (already exists)
    - `handle_save_request()` - save request (already exists)
    - `handle_switch_detail_tab(index)` - switch between Params/Headers/Body tabs (Ctrl+P/H/B)

## Design Decisions

- Use standard Qt mechanisms for registering hotkeys
- Support platform-specific combinations (Ctrl vs Cmd)

## User Scenarios (Use Cases)

### UC1: Quick Request Sending
1. User edits URL or request parameters
2. User presses `Ctrl+Enter` or `F5`
3. Request is sent without needing to click "Send" button
4. Result is displayed in response area

### UC2: Quick Request Saving
1. User created or modified a request
2. User presses `Ctrl+S`
3. Save dialog opens (or request saves if already saved)
4. Request is saved to selected collection

### UC3: Quick Switching Between Requests
1. User works with multiple open tabs
2. User presses `Ctrl+Tab` to switch to next tab
3. Active tab changes without using mouse

### UC4: Quick Application Exit
1. User finished work
2. User presses `Ctrl+Q`
3. Application closes

### UC5: Quick New Request Creation
1. User presses `Ctrl+N`
2. New tab with empty request is created
3. Focus is set to URL input field

## Prioritization

### High Priority (MVP)
1. Exit Application (`Ctrl+Q`)
2. Send Request (`Ctrl+Enter` / `F5`)
3. Save Request (`Ctrl+S`)
4. Create New Tab (`Ctrl+N`)
5. Close Tab (`Ctrl+W`)
6. Switch Between Tabs (`Ctrl+Tab` / `Ctrl+Shift+Tab`)

### Medium Priority
7. Switch to Specific Request Tab (`Alt+1-9`)
8. Open Settings (`Ctrl+,` / `F12`)
9. Manage Environments (`Ctrl+E`)
10. Focus on URL (`Ctrl+L`)
11. Switch Between Request Editor Tabs (`Ctrl+P/H/B`)
12. Escape to close dialogs
