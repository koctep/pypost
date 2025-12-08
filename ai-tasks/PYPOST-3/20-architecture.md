# Architecture: PYPOST-3

## Overview
Architectural changes to support system storage paths and UI state persistence (environment, tabs).

## Components

### ConfigManager
Responsible for managing application configuration (`settings.json`).

### StorageManager
Responsible for saving and loading user data.

### AppSettings (Model)
Data model for application settings.

**Changes:**
- Add `open_tabs` field.

**Structure:**
```python
@dataclass
class AppSettings:
    theme: str = "light"
    # ... existing fields
    config_version: int = 1
    revision: int = 0
    last_environment_id: Optional[str] = None
    open_tabs: List[str] = field(default_factory=list)
```

### MainWindow (UI)
Main application window.

**Changes:**
- **Events**: Track tab opening/closing.
- **Saving**: On tab changes, update `settings.open_tabs` (list of request IDs) and save config.
- **Restoration**:
    - On startup, iterate through `settings.open_tabs`.
    - Find corresponding `RequestData` by ID in all loaded collections.
    - Open found requests.
    - If request not found (deleted), ignore ID.

## Interactions
1. `MainWindow` loads collections.
2. `MainWindow` reads `settings.open_tabs`.
3. For each ID in list:
    - Searches for request in `self.collections`.
    - If found -> `add_new_tab(request_data)`.
4. On tab add/remove:
    - Updates ID list in `settings.open_tabs`.
    - Calls `config_manager.save_config`.
