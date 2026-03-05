# Requirements: PYPOST-14 - Improve Request Save Logic

## Goals
Improve request saving logic, making it more intuitive and safe. Separate behavior for new and existing requests, and add an overwrite confirmation setting.

## User Stories
- As a user, I want the request to be updated automatically when I click "Save" on an already saved request, to speed up work.
- As a user, I want to be able to enable overwrite confirmation for existing requests to avoid accidental data loss.
- As a user, when I save a new (not yet saved) request, I want to see a dialog box to select a name and collection.

## Acceptance Criteria
- [ ] **Existing Request**:
    - When clicking "Save" (or Ctrl+S), the request is saved to the same file/location in the collection.
    - "Confirm before overwrite" setting is checked.
- [ ] **New Request**:
    - When clicking "Save", the "Save Request" dialog opens.
    - In the dialog, you can specify the request name.
    - In the dialog, you can select a collection (folder) for saving.
- [ ] **Settings**:
    - Added "Confirm before overwriting requests" option (checkbox) to application settings.
    - Setting persists between application launches.
    - If option is enabled: when saving an existing request, a Yes/No dialog appears.
    - If option is disabled: saving happens instantly without questions.
- [ ] **UI Updates**:
    - Indication that the request has unsaved changes (e.g., `*` in tab title) disappears after saving.
    - If it was a new request, the tab title updates to the new name after saving.

## Task Description
It is necessary to refine the save event handler in `MainWindow` or `RequestWidget`.
Current behavior (presumably) always calls "Save As" or lacks confirmation setting.
New behavior must distinguish request context:
1. **Is New**: Call save dialog (Save As).
2. **Is Existing**:
    - Read `confirm_overwrite` setting.
    - If `True` -> Confirmation dialog.
    - If `False` -> Direct write.

### Technical Details
- **Language**: Python (PySide6).
- **Components**:
    - `MainWindow`: Handling `actionSave`.
    - `TabWidget` / `RequestWidget`: Storing state (file path, `is_new`, `is_modified` flag).
    - `SettingsDialog`: Adding new setting.

## Q&A
- **What is the default value for the confirmation setting?**
    - *Assumption*: `True` (safer) or `False` (faster). Let's make it `False` (like in most IDEs), but user can enable it.
- **What happens on "Save As"?**
    - There should be a separate "Save As" command that always opens the dialog, even for existing ones. (This is standard behavior, but user requirements are about the Save button).
