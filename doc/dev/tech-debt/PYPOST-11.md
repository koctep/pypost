# Technical Debt for Task PYPOST-11

## 1. Lack of Localization
Currently, all menu items and dialogs are hardcoded in English. In the future, a localization mechanism (e.g., `gettext` or `Qt Linguist`) needs to be implemented to support multiple languages.

## 2. Hardcoded Hotkeys in HotkeysDialog — **Addressed (PYPOST-599)**
Shortcuts are registered via `pypost/ui/hotkeys.py` (`register_hotkey`, `tag_action`). The help
dialog collects tagged `QAction` metadata from the main window. See `doc/dev/hotkeys.md`.

## 3. No Version Update Mechanism
The application version in `AboutDialog` is hardcoded ("Version 0.1.0"). The version needs to be moved to a separate constant (e.g., in `pypost/__init__.py`) or read from package metadata.

## 4. Menu Styling
Current menu styling via QSS (padding) is a workaround to improve readability on large fonts. A more robust way to manage interface scaling (DPI awareness) or use system style settings should be considered.
