# Architecture: PYPOST-4

## Overview
Implementation of a style manager to load and apply custom QSS files from the configuration directory.

## Components

### 1. ConfigManager (`pypost/core/config_manager.py`)
Extension of functionality to work with the styles directory.

**Additions:**
- Property `styles_dir` (Path): path to `styles` folder inside config.
- Method `_ensure_styles_dir()`: checks for folder existence and creates it along with default `main.qss` if missing.
- Constant `DEFAULT_STYLE`: string with example QSS.

### 2. StyleManager (`pypost/core/style_manager.py`) - NEW COMPONENT
Responsible for reading and merging styles.

**Responsibility:**
- Receives path to styles directory from `ConfigManager`.
- Scans directory for `.qss` files.
- Reads file contents.
- Merges them into a single style string.
- Provides method `apply_styles(app: QApplication)`.

**Interface:**
```python
class StyleManager:
    def __init__(self, styles_dir: Path):
        ...

    def load_styles(self) -> str:
        """Reads all .qss files from styles_dir and returns merged string."""
        ...

    def apply_styles(self, app_or_widget: QObject):
        """Applies loaded styles to application or widget."""
        ...
```

### 3. MainWindow (`pypost/ui/main_window.py`)
Integration of `StyleManager`.

**Changes:**
- Initialize `StyleManager` in `__init__`.
- Call `style_manager.apply_styles(QApplication.instance())` or apply to `self` (but better to `QApplication` for global effect).

## Default Style (DEFAULT_STYLE)
Content that will be written to `main.qss` on first launch:

```css
/* Example configuration for tab close buttons */
QTabBar::close-button {
    /* Uncomment and change sizes as desired */
    /* width: 16px; */
    /* height: 16px; */
}

/* Example configuration for the tab itself */
QTabBar::tab {
    /* padding: 5px; */
}
```

## Execution Flow
1. `MainWindow` initializes.
2. `ConfigManager` is created.
3. `ConfigManager` in constructor (or lazily) checks `styles` folder. If missing — creates folder and `main.qss`.
4. `MainWindow` creates `StyleManager`.
5. `MainWindow` calls `style_manager.apply_styles(app)`.
6. Application displays with applied styles.
