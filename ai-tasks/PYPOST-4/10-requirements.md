# Requirements: PYPOST-4

## Task Description
It is necessary to implement support for loading external stylesheets (QSS) from the user configuration directory. This will allow users to customize the application's appearance, including the size of controls (e.g., tab close buttons).

## Implementation Language
Python (using PySide6)

## Functional Requirements

1. **Styles Directory**: The application must check for the existence of a `styles` subdirectory within the application configuration directory (determined by `ConfigManager`).
2. **Loading Styles**:
    - On startup, the application must scan the `styles` directory for `.qss` files.
    - If a `main.qss` file (or another agreed file) is found, its contents must be applied to `QApplication` or the main window.
    - Alternatively: load all `.qss` files and merge them.
3. **Application**: Styles must be correctly applied to widgets, including `QTabWidget` and its child elements (`QTabBar::close-button`).
4. **Default Creation**: If the `styles` directory does not exist, it must be created on startup. A default `main.qss` file with an example style (including tab close button styling) should be created in it so the user understands how it works.

## Non-functional Requirements

1. **Fault Tolerance**: Errors when reading or parsing the style file should not cause the application to crash. Errors should be logged (to console).
2. **Cross-platform**: File paths must be formed correctly on all supported OSes.

## Constraints and Assumptions

- The user is responsible for the correctness of QSS syntax.
- Style changes require restarting the application (or a "Reload Styles" button could be added in the future, but currently not required).
- The main focus now is on tab customization, but the mechanism should be generic.

## Main Entities

- `ConfigManager`: Should provide the path to the styles directory or methods to load them.
- `MainWindow`: Should initiate style application on startup.

## User Scenarios

1. User opens the application config folder.
2. Creates a `styles` folder (if missing).
3. Creates a `styles/tabs.qss` (or `main.qss`) file.
4. Writes:
    ```css
    QTabBar::close-button {
        width: 16px;
        height: 16px;
    }
    ```
5. Starts PyPost.
6. Close buttons on tabs have size 16x16.
