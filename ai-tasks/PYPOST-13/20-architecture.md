# Architecture: PYPOST-13 - JSON Syntax Highlighting

## Research
To implement syntax highlighting in Qt (PySide6), the `QSyntaxHighlighter` class is used.
It allows applying formatting to text in `QTextDocument` (used in `QTextEdit` and `QPlainTextEdit`) without changing the text itself.

Key points:
1. Inherit from `QSyntaxHighlighter`.
2. Override `highlightBlock(text)` method.
3. Inside the method, use regular expressions to find patterns (keys, strings, numbers, etc.).
4. Apply `setFormat(start, length, format)` for found matches.

There are ready-made examples of JSON highlighter implementation for Qt. Usually, they use several regular expressions with different priorities.

Order of rule application matters. For example, first find strings, then numbers, then keywords.
For JSON, the specifics are:
- Strings (in double quotes).
- Keys (strings followed by a colon, possibly separated by spaces).
- Numbers.
- Literals (`true`, `false`, `null`).

## Implementation Plan
1. Create file `pypost/ui/widgets/json_highlighter.py`.
2. Implement `JsonHighlighter(QSyntaxHighlighter)` class.
    - Define colors and styles for different tokens.
    - Implement `highlightBlock` logic.
3. Integrate highlighter into `RequestWidget` (`pypost/ui/widgets/request_editor.py`).
    - Connect to `self.body_edit.document()`.
4. Integrate highlighter into `ResponseView` (`pypost/ui/widgets/response_view.py`).
    - Connect to `self.body_view.document()`.

## Architecture

### New Component: `JsonHighlighter`
Location: `pypost/ui/widgets/json_highlighter.py`

**Responsibilities:**
- Storing highlighting rules (Regex + TextCharFormat).
- Parsing text blocks and applying formatting.

**Interface:**
```python
class JsonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize rules and formats
    
    def highlightBlock(self, text):
        # Apply rules
```

### Changes in `RequestWidget`
In `init_ui` method after creating `self.body_edit`:
```python
self.json_highlighter = JsonHighlighter(self.body_edit.document())
```

### Changes in `ResponseView`
In `init_ui` method after creating `self.body_view`:
```python
self.json_highlighter = JsonHighlighter(self.body_view.document())
```

### Interaction
The highlighter automatically reacts to changes in the document. For `ResponseView`, which is `ReadOnly`, highlighting will apply once when text is set. For `RequestWidget` - in real-time during typing.

## Q&A
- **Do we need to handle complex cases (nested quotes)?**
    - JSON standard is quite simple, strings are always in double quotes. Escaped quotes `\"` need to be accounted for in string regex.
