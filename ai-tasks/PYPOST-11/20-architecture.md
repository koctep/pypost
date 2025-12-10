# Architecture for Task PYPOST-11

## Overview
Implementation of the main application menu with "File" and "Help" items in the `MainWindow` class. Addition of dialog boxes for displaying help and program information.

## Components

### MainWindow (`pypost/ui/main_window.py`)
Extend the `__init__` method (or create a separate `setup_menu` method) to initialize `QMenuBar`.

*   **Methods**:
    *   `_create_menu_bar()`: Private method to create the menu structure.
    *   `handle_show_hotkeys()`: Slot to display the hotkeys dialog.
    *   `handle_show_about()`: Slot to display the "About" dialog.

### HotkeysDialog (`pypost/ui/dialogs/hotkeys_dialog.py`)
New class inheriting from `QDialog` to display the list of hotkeys.

*   **UI Elements**:
    *   `QTableWidget` or `QFormLayout` to display "Action - Key" pairs.
    *   Data for display can be passed to the constructor or stored as a constant in the class, or extracted dynamically (harder but more correct), but for MVP, hardcoding the list according to `doc/README.md` or `main_window.py` is acceptable.
    *   "Close" button.

### AboutDialog (`pypost/ui/dialogs/about_dialog.py`)
New class inheriting from `QDialog` (or using `QMessageBox.about`) to display information.

*   **Content**:
    *   Program name (bold font).
    *   Version.
    *   Brief description.
*   **UI Elements**:
    *   "OK" button.

## Interaction
1.  User clicks a menu item.
2.  `MainWindow` intercepts the `triggered` signal from `QAction`.
3.  Corresponding handler is called (`handle_exit`, `handle_show_hotkeys`, `handle_show_about`).
4.  For dialogs, a dialog instance is created and `exec()` is called.

## Implementation Plan
1.  Create `pypost/ui/dialogs/about_dialog.py` with `AboutDialog` class.
2.  Create `pypost/ui/dialogs/hotkeys_dialog.py` with `HotkeysDialog` class.
3.  In `pypost/ui/main_window.py`:
    *   Import new dialogs.
    *   Implement `_create_menu_bar` method.
    *   Add `_create_menu_bar` call to `__init__`.
    *   Implement `handle_show_hotkeys` and `handle_show_about` slots.
