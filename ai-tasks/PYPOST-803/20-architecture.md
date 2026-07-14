# PYPOST-803: Architecture — presenter font closure

## Decision

**Close without adding `apply_font`.** Collections and Tabs presenters rely on global
font propagation established in PYPOST-106, PYPOST-404, and PYPOST-425.

## Current pipeline

```text
MainWindow.apply_settings(settings)
  → StyleManager.apply_appearance(app, theme, font_size)
       → apply_theme → apply_styles (QWidget { font-size: Npt; }) → app.setFont
  → tabs.apply_settings(settings)   # indent + JSON colors only
  → env.apply_settings(settings)    # stores settings only
```

No `collections.apply_settings` call exists; the collections tree inherits the
application default font like other `QWidget` descendants.

## Presenter widgets

| Presenter | Root widget | Font mechanism |
|-----------|-------------|----------------|
| `CollectionsPresenter` | `QTreeView` (`widget`) | Inherits `QApplication` font + global QSS |
| `TabsPresenter` | `QTabWidget` (`widget`) | Inherits app font; tab bar uses native metrics |
| `EnvPresenter` | `QWidget` top bar | Same (PYPOST-425 removed `apply_font`) |

## Changes

| Component | Change |
|-----------|--------|
| `collections_presenter.py` | No code change |
| `tabs_presenter.py` | No code change |
| `main_window.py` | No code change |
| `tests/test_presenter_font_inheritance.py` | New regression tests |
| `doc/dev/ui_font_and_styles.md` | Document PYPOST-803 closure |

## Rationale

PYPOST-43 TD-1's encapsulation goal is met: `MainWindow` does not expose or mutate
presenter internals for fonts. The belt-and-suspenders `apply_font` pattern was
superseded by centralized appearance (PYPOST-425).
