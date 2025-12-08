# Requirements: PYPOST-3

## Task Description
It is necessary to change the storage mechanism for application settings and user data (collections, environments) so that they are located in standard operating system directories, rather than in the application's working directory. It is also necessary to extend the settings file structure by adding versioning, saving the last used environment, and the state of open tabs.

## Implementation Language
Python 3.11+ (using PySide6)

## Functional Requirements

1. **Path Definition**:
    - The application must use the `platformdirs` library to determine correct paths.
    - **Linux/Unix**:
        - Configuration: `$XDG_CONFIG_HOME/pypost` (default `~/.config/pypost`)
        - Data: `$XDG_DATA_HOME/pypost` (default `~/.local/share/pypost`)
    - **Windows**:
        - Configuration: `%LOCALAPPDATA%\pypost` (or `%APPDATA%` depending on platformdirs implementation for user config)
        - Data: `%LOCALAPPDATA%\pypost`
    - **macOS**:
        - Configuration: `~/Library/Application Support/pypost`
        - Data: `~/Library/Application Support/pypost` (or separate, as defined by library)

2. **Settings Storage**:
    - The `settings.json` file must be saved to and read from the user configuration directory (`user_config_dir`).
    - **New settings fields**:
        - `config_version` (int): Configuration format version (initial value: 1).
        - `revision` (int): Settings revision number, increments on every save (initial value: 0).
        - `last_environment_id` (str|None): ID of the last selected environment.
        - `open_tabs` (List[str]): List of request IDs open in tabs.

3. **Data Storage**:
    - The `collections/` directory and `environments.json` file must be saved to and read from the user data directory (`user_data_dir`).

4. **Migration**:
    - Automatic migration is **not required**.
    - If data is missing in new directories, the application starts with a "clean slate" (default settings, empty collections).
    - The user must manually move files if necessary.

5. **Startup Behavior**:
    - On startup, the application must automatically select the environment saved in `last_environment_id`.
    - On startup, the application must restore tabs saved in `open_tabs`.

## Non-functional Requirements
- Use `platformdirs` library.
- The application must correctly create necessary directories if they do not exist (recursively).

## Entities and Changes

- **ConfigManager**:
    - Update logic for determining path to `settings.json`.
    - Update `AppSettings` model to support new fields.
    - Logic to increment `revision` on save.
- **StorageManager**: Update logic for determining paths to `collections/` and `environments.json`.
- **MainWindow**:
    - Save selected environment ID to settings.
    - Save list of open tabs (request IDs) on tab close or application exit (or on every change).
    - Restore state on startup.
- **Dependencies**: Add `platformdirs` to `requirements.txt`.
