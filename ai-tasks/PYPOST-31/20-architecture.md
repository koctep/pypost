# Architecture: PYPOST-31 - Fix Crash on Request Retry

## Research
In `handle_send_request(self, request_data)`:
```python
sender_tab = None
for i in range(self.tabs.count()):
    tab = self.tabs.widget(i)
    if tab.request_editor == self.sender(): # <--- Problem here
        sender_tab = tab
        break
```
When called via signal from `RequestWidget` (button click), `self.sender()` is `RequestWidget` (or button).
When called via `handle_send_request_global` (hotkey), `self.sender()` might be `QShortcut` or `MainWindow` or `None`.

## Implementation Plan

1.  **Update `handle_send_request`**:
    -   If `sender_tab` is not found via `self.sender()`, assume the request comes from the *active* tab.
    -   Use `self.tabs.currentWidget()` as a fallback.

## Architecture

### `MainWindow.handle_send_request`

```python
def handle_send_request(self, request_data: RequestData):
    sender_tab = None
    # ... search by sender ...
    
    if not sender_tab:
        # Fallback: use current tab
        current = self.tabs.currentWidget()
        if isinstance(current, RequestTab) and current.request_data.id == request_data.id:
             sender_tab = current
    
    if not sender_tab:
         return
    # ...
```
