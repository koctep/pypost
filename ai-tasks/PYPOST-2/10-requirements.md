# Requirements: Adding Application Settings (Font Size)

## 1. Task Description
Add the ability to configure the font size in the application. This involves creating an interface for changing settings, saving them, and applying them to the application interface.

## 2. Programming Language
Python (using PySide6)

## 3. Functional Requirements
1.  **Settings Button**:
    *   Add a "Settings" button (or gear icon) to the application's Top Bar, next to the environment selector.
2.  **Settings Dialog**:
    *   Clicking the button opens a modal "Settings" dialog box.
3.  **Font Size Setting**:
    *   The dialog must contain an option to change the font size (Application Font Size).
    *   Control element: `QSpinBox` or `QComboBox`.
    *   Range of values: from 8 to 48 (default 10 or 12, depending on system default).
4.  **Applying Settings**:
    *   Font size changes apply **globally** to the entire application (`QApplication.setFont` or similar mechanism).
    *   Changes should ideally be applied immediately upon saving the dialog (clicking "Save" or "OK").
5.  **Saving Settings**:
    *   Settings must be saved to a `settings.json` file in the application's working directory (same location as collections).
    *   On startup, the application must load settings and apply them.

## 4. Non-Functional Requirements
1.  **Usability**: Settings must be intuitive.
2.  **Architecture**: Use an MVC-like approach. Separate configuration management into a distinct class (e.g., `ConfigManager` or extend `StorageManager`).

## 5. User Scenarios
1.  **Changing Font**:
    *   User launches the application.
    *   Clicks the "Settings" button in the top bar.
    *   In the opened window, changes the font size from 10 to 14.
    *   Clicks "Save".
    *   The dialog closes, and all labels and interface elements increase in size.
    *   On the next launch, the font remains at size 14.

## 6. Entities
*   `Settings` (model): stores setting values (font_size).
*   `SettingsDialog` (UI): dialog window.
*   `ConfigManager` (logic): responsible for load/save `settings.json`.
