# Architecture: Adding Application Settings (Font Size)

## 1. General Approach

The MVC (Model-View-Controller) pattern will be implemented for managing settings.
*   **Model**: Pydantic model for validation and storage of settings structure.
*   **Controller**: Extension of `StorageManager` or a separate class for loading/saving.
*   **View**: New `SettingsDialog` and update to `MainWindow`.

## 2. Data Structure

The `settings.json` file will have the following structure:
```json
{
  "font_size": 12,
  "theme": "dark" // placeholder for future use, not implemented yet
}
```

### Model (`pypost/models/settings.py`)

```python
from pydantic import BaseModel

class AppSettings(BaseModel):
    font_size: int = 12
```

## 3. Module Changes

### 3.1 `pypost/core/config_manager.py` (New File)

Create a separate manager for configuration to avoid overloading `StorageManager`, which handles
business data (collections).

**Class `ConfigManager`**:
*   `__init__(self, config_path="settings.json")`
*   `load_config() -> AppSettings`: Loads settings, returns defaults on error.
*   `save_config(settings: AppSettings)`: Saves settings to file.

### 3.2 `pypost/ui/dialogs/settings_dialog.py` (New File)

Dialog for editing settings.

**Class `SettingsDialog(QDialog)`**:
*   Accepts current `AppSettings`.
*   Contains `QSpinBox` for font size.
*   Returns updated `AppSettings` object on save.

### 3.3 `pypost/ui/main_window.py`

*   Add "Settings" button to `top_bar`.
*   In `__init__`: Initialize `ConfigManager`, load settings, apply font.
*   Method `open_settings()`: Opens dialog, saves config and updates app font on save.
*   Method `apply_settings(settings)`: `QApplication.instance().setFont(...)`.

### 3.4 `pypost/main.py`

*   Consider loading settings here before creating the main window so the app starts with the
    correct font immediately. However, it's simpler to do this in `MainWindow` or pass settings to
    it.
*   *Decision*: Load settings in `main.py` and apply font globally before showing the window.

## 4. Implementation Plan

1.  Create `AppSettings` model.
1.  Implement `ConfigManager`.
1.  Create `SettingsDialog`.
1.  Integrate into `MainWindow` and `main.py`.
