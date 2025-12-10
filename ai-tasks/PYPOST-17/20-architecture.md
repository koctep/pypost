# Architecture: PYPOST-17 - Improve Request Save Logic

## Research
- **Current Implementation**:
    - `MainWindow.handle_save_request` always calls `SaveRequestDialog`.
    - No check if the request already exists in a collection.
    - Settings are stored in `AppSettings` (Pydantic model) and edited in `SettingsDialog`.

- **Needs**:
    - Need to distinguish "Save" (Ctrl+S) and "Save As" (but currently only Save button logic).
    - If request exists in collection -> overwrite (with optional confirmation).
    - If request is new -> name/collection selection dialog.
    - New setting `confirm_overwrite_request` (bool).

## Implementation Plan

1.  **Data Model**:
    - Add field `confirm_overwrite_request: bool = False` to `AppSettings`.

2.  **Settings UI**:
    - Add `QCheckBox` to `SettingsDialog` to control the new setting.

3.  **Save Logic (`MainWindow`)**:
    - In `handle_save_request`:
    - Try to find request by ID in all collections.
    - If found (`existing_request`):
        - Check `settings.confirm_overwrite_request`.
        - If enabled -> Show `QMessageBox.question`.
        - If confirmed or disabled -> Update `existing_request` fields with data from editor and save collection.
    - If not found (new) -> Open `SaveRequestDialog` (existing logic).

## Architecture

### Modules

#### Models (`pypost/models/settings.py`)
Change settings model.
```python
class AppSettings(BaseModel):
    # ... existing fields ...
    confirm_overwrite_request: bool = False
```

#### UI (`pypost/ui/dialogs/settings_dialog.py`)
Add UI element.
- Add `QCheckBox` "Confirm before overwriting requests".
- Bind to `confirm_overwrite_request`.

#### Logic (`pypost/ui/main_window.py`)
Change save handling logic.

**Algorithm `handle_save_request(self, request_data)`:**

1.  **Search**: Iterate through `self.collections` and nested `requests`. Find request with `id == request_data.id`.
    - *Optimization*: Could store ID -> (Collection, Request) map, but full scan is acceptable for now (small number of requests).

2.  **Branching**:
    - **CASE: New Request** (not found):
        - Call `SaveRequestDialog`.
        - (Logic for creating new record and adding to collection remains same).

    - **CASE: Existing Request** (found):
        - If `settings.confirm_overwrite_request == True`:
            - Show dialog "Overwrite Request? This will overwrite existing request...".
            - If "No" -> `return`.
        - **Overwrite**:
            - Update found request object with data from `request_data` (URL, method, headers, params, body, script).
            - Save corresponding collection: `self.storage.save_collection(found_collection)`.
            - Update UI (tab title if name changed - though name usually changes via Save As/Rename, here we just update content).
            - Reset modification flag (if implemented, for now user just visually sees it's saved).

## Q&A
- **How to distinguish new request from existing one if ID is generated on `RequestData` creation?**
    - Even if `RequestData` has an ID (generated in constructor), it doesn't mean it's saved in "database" (file system/collections).
    - Existence criterion: presence of this ID in `self.collections`.
