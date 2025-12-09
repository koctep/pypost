# Architecture: PYPOST-5 - Hotkeys

## Overview
Architecture for implementing the hotkey system in PyPost. Hotkeys are divided into two levels: global (MainWindow) and contextual (RequestWidget).

## Components

### 1. MainWindow (`pypost/ui/main_window.py`)
Handles global hotkeys available at the application level.

**Additions:**
- Method `_setup_shortcuts()`: initializes all global hotkeys
- Handler methods for each hotkey
- Use of `QShortcut` for registering key combinations

**New Methods:**
```python
def _setup_shortcuts(self):
    """Initializes all global hotkeys."""
    # Exit application
    # Create new tab
    # Close tab
    # Switch between tabs
    # Switch to specific tab
    # Open settings
    # Manage environments
    # Focus on URL

def handle_exit(self):
    """Handler for application exit (Ctrl+Q)."""

def handle_new_tab(self):
    """Handler for creating new tab (Ctrl+N)."""

def handle_close_tab(self):
    """Handler for closing current tab (Ctrl+W)."""

def handle_next_tab(self):
    """Handler for switching to next tab (Ctrl+Tab)."""

def handle_previous_tab(self):
    """Handler for switching to previous tab (Ctrl+Shift+Tab)."""

def handle_switch_to_tab(self, index):
    """Handler for switching to specific tab (Alt+1-9)."""

def handle_open_settings(self):
    """Handler for opening settings (Ctrl+, / F12)."""

def handle_open_environments(self):
    """Handler for opening environment management (Ctrl+E)."""

def handle_focus_url(self):
    """Handler for setting focus on URL field (Ctrl+L / Alt+D)."""
```

**Imports:**
```python
from PySide6.QtGui import QShortcut, QKeySequence
```

### 2. RequestWidget (`pypost/ui/widgets/request_editor.py`)
Handles contextual hotkeys working only when focus is in the request editing area.

**Additions:**
- Method `_setup_shortcuts()`: initializes contextual hotkeys
- Override `keyPressEvent()` for handling special combinations (Ctrl+Enter, F5)
- Handler methods for contextual actions

**New Methods:**
```python
def _setup_shortcuts(self):
    """Initializes context shortcuts."""
    # Save request (Ctrl+S)
    # Switch between editor tabs (Ctrl+P/H/B)

def keyPressEvent(self, event):
    """Handles key presses for special combinations."""
    # Ctrl+Enter or F5 to send request
    # Escape to cancel (if applicable)

def handle_save_request_shortcut(self):
    """Handler for saving request via shortcut (Ctrl+S)."""

def handle_switch_to_params(self):
    """Handler for switching to Params tab (Ctrl+P)."""

def handle_switch_to_headers(self):
    """Handler for switching to Headers tab (Ctrl+H)."""

def handle_switch_to_body(self):
    """Handler for switching to Body tab (Ctrl+B)."""
```

**Imports:**
```python
from PySide6.QtGui import QShortcut, QKeySequence
```

### 3. RequestTab (`pypost/ui/main_window.py`)
Intermediate component that may be required for handling some hotkeys at tab level.

**Changes:**
- Possible addition of Escape handling to close dialogs (if required)

### 4. Dialogs (`pypost/ui/dialogs/*.py`)
Escape handling for closing dialogs.

**Changes:**
- All dialogs should handle Escape to close
- Use standard Qt behavior (QDialog automatically closes on Escape if not overridden)

## Implementation Mechanism

### QShortcut vs keyPressEvent

**QShortcut is used for:**
- Global hotkeys (Ctrl+Q, Ctrl+N, Ctrl+W, etc.)
- Key combinations with modifiers (Ctrl, Alt, Shift)
- Hotkeys that should work regardless of widget focus (for global actions)

**keyPressEvent is used for:**
- Special combinations requiring context handling (Ctrl+Enter, F5)
- Combinations that might conflict with standard widget behavior (e.g., Enter in text fields)

### Platform-specific Combinations

For macOS support (Cmd instead of Ctrl):
```python
ctrl = Qt.MetaModifier if sys.platform == 'darwin' else Qt.ControlModifier
```
# Determining modifier depending on platform
# But QKeySequence("Ctrl+C") automatically handles this on macOS (maps to Cmd+C) if using standard names.

**Alternative Approach:**
Use `QKeySequence` with standard names, which Qt automatically converts:
```python
QKeySequence("Ctrl+Q")  # Automatically becomes Cmd+Q on macOS
```

### Context Activation

**Global Hotkeys (MainWindow):**
- Registered at MainWindow level
- Work always when application is active
- Examples: Ctrl+Q, Ctrl+N, Ctrl+W, Ctrl+Tab, Alt+1-9

**Contextual Hotkeys (RequestWidget):**
- Registered at RequestWidget level
- Work only when focus is in RequestWidget or its child widgets
- Examples: Ctrl+Enter, F5, Ctrl+S, Ctrl+P/H/B

**Escape Handling:**
- QDialog automatically closes on Escape (standard Qt behavior)
- If additional handling is required, override `keyPressEvent` in dialogs

## Hotkey Structure

### Global (MainWindow)

| Hotkey | Action | Handler Method |
| :--- | :--- | :--- |
| `Ctrl+Q` | Exit Application | `handle_exit()` |
| `Ctrl+N` | Create New Tab | `handle_new_tab()` |
| `Ctrl+W` | Close Current Tab | `handle_close_tab()` |
| `Ctrl+Tab` | Next Tab | `handle_next_tab()` |
| `Ctrl+Shift+Tab` | Previous Tab | `handle_previous_tab()` |
| `Alt+1` to `Alt+9` | Switch to Tab N | `handle_switch_to_tab(index)` |
| `Ctrl+,` or `F12` | Open Settings | `handle_open_settings()` |
| `Ctrl+E` | Manage Environments | `handle_open_environments()` |
| `Ctrl+L` or `Alt+D` | Focus on URL | `handle_focus_url()` |

### Contextual (RequestWidget)

| Hotkey | Action | Handler Method |
| :--- | :--- | :--- |
| `Ctrl+Enter` or `F5` | Send Request | `on_send()` (via keyPressEvent) |
| `Ctrl+S` | Save Request | `handle_save_request_shortcut()` |
| `Ctrl+P` | Switch to Params | `handle_switch_to_params()` |
| `Ctrl+H` | Switch to Headers | `handle_switch_to_headers()` |
| `Ctrl+B` | Switch to Body | `handle_switch_to_body()` |

## Execution Flow

### Hotkey Initialization

1. **MainWindow:**
   - After creating UI components
   - Call `self._setup_shortcuts()` at end of `__init__`
   - Registration of all global hotkeys

2. **RequestWidget:**
   - After creating UI components
   - Call `self._setup_shortcuts()` at end of `init_ui()`
   - Registration of contextual hotkeys

### Key Press Processing

1. **Global Hotkeys:**
   - User presses combination (e.g., Ctrl+Q)
   - QShortcut intercepts event at MainWindow level
   - Corresponding handler method is called
   - Action is executed

2. **Contextual Hotkeys:**
   - User presses combination (e.g., Ctrl+Enter)
   - If focus is in RequestWidget or its child widgets:
     - keyPressEvent intercepts event
     - Key combination is checked
     - Corresponding handler method is called
     - Action is executed
   - If focus is outside RequestWidget:
     - Event is processed normally

3. **QShortcut for Contextual Actions:**
   - For Ctrl+S, Ctrl+P/H/B use QShortcut
   - QShortcut automatically works only when widget has focus
   - Does not require overriding keyPressEvent

## Conflict Handling

### Processing Priority

1. **Standard Qt Actions** (Ctrl+C, Ctrl+V, Ctrl+A, etc.)
   - Have highest priority
   - Not overridden

2. **Global Application Hotkeys**
   - Processed by QShortcut at MainWindow level
   - Work when application is active

3. **Contextual Hotkeys**
   - Processed by QShortcut or keyPressEvent at RequestWidget level
   - Work only in appropriate context

### Avoiding Conflicts

- **Ctrl+P**: May conflict with Print in some apps, but acceptable in RequestWidget context
- **Ctrl+H**: May conflict with Find/Replace, but acceptable in RequestWidget context
- **Ctrl+B**: May conflict with Bold in text editors, but acceptable in RequestWidget context

All these combinations work only in RequestWidget context, so conflicts are minimal.

## Implementation Details

### Tab Switching (Ctrl+Tab)

Qt has built-in support for Ctrl+Tab for QTabWidget, but additional processing might be needed:

```python
# QTabWidget automatically handles Ctrl+Tab
# But explicit handling can be added for Ctrl+Shift+Tab
```

### Specific Tab Switching (Alt+1-9)

```python
# Create shortcuts for each combination Alt+1 to Alt+9
for i in range(1, 10):
    ...
```

### URL Focus (Ctrl+L / Alt+D)

```python
def handle_focus_url(self):
    """Sets focus to URL field in active tab."""
    ...
```

### Send Request (Ctrl+Enter / F5)

```python
def keyPressEvent(self, event):
    """Handles Ctrl+Enter and F5 for sending request."""
    ...
```

## Testing

### Test Scenarios

1. **Global Hotkeys:**
   - Verify all combinations work regardless of focus
   - Verify work on different platforms (Linux, Windows, macOS)

2. **Contextual Hotkeys:**
   - Verify work only when focus is in RequestWidget
   - Verify absence of conflicts with standard Qt actions

3. **Conflicts:**
   - Verify standard combinations (Ctrl+C, Ctrl+V) work normally
   - Verify work in text input fields

## Migration and Backward Compatibility

- Adding hotkeys does not affect existing functionality
- All existing methods remain unchanged
- Hotkeys are an additional way to access functions
- Buttons and menus continue to work as before
