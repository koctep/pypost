# Requirements for Task PYPOST-9

## Task Description
Add a main application menu containing "File" and "Help" items. The menu should provide access to basic application control functions (exit) and informational help (hotkeys, about).

## Programming Language
**Python** (PySide6/Qt for UI)

## Functional Requirements

### "File" Menu
1.  **"Quit" Item**:
    *   Closes the application when selected.
    *   Should duplicate the functionality of the existing `Ctrl+Q` hotkey.

### "Help" Menu
1.  **"Hotkeys" Item**:
    *   Opens a dialog box with a list of hotkeys when selected.
    *   The list must be up-to-date and correspond to implemented hotkeys (see `pypost/ui/main_window.py`).
2.  **"About" Item**:
    *   Opens an "About" dialog box when selected.
    *   The window should contain the application name ("PyPost"), a brief description, and possibly version/author.

## Non-functional Requirements
1.  The menu must integrate natively into the OS window interface (in PySide6 this is `QMenuBar`).
2.  Dialog boxes must be modal.

## Entities and Interactions
*   Add `QMenuBar`.
*   Create `QMenu` ("File", "Help").
*   Create `QAction` for menu items.
*   Implement slots for action handling (or reuse existing ones).
*   **HotkeysDialog** (new entity or `QMessageBox`):
    *   Display table/list of hotkeys.
*   **AboutDialog** (new entity or `QMessageBox`):
    *   Display program information.

## Constraints and Assumptions
*   Use standard PySide6 widgets.
*   Dialog design should match the general application style (if custom styles exist).
