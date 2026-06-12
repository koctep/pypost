# UI widget mixins

## Variable hover components (PYPOST-129)

Hover support is split into two classes in `pypost/ui/widgets/mixins.py`:

| Class | Use when |
| --- | --- |
| `VariableHoverLocator` | Finding which `{{...}}` token is under a cursor index |
| `VariableHoverResolver` | Resolving token(s) to tooltip preview values |
| `VariableHoverHelper` | Backward-compatible facade; delegates to both |

- **Line / plain-text editors** (`VariableHoverMixin`): locator on `mouseMoveEvent`, resolver
  for the matched token only.
- **Table cells** (`VariableAwareTableWidget`): locator pattern for detection, resolver on full
  cell text (no cursor index). Per-cell resolution cache avoids redundant `resolve_text` on
  repeated `mouseMoveEvent` over the same cell (PYPOST-132). This path is separate from
  line-scoped scan (PYPOST-120 / PYPOST-122), which applies only to multiline editors.
- **Metrics:** `VariableHoverResolver.set_metrics` (also exposed on the facade).

## VariableHoverMixin

`pypost/ui/widgets/mixins.py` defines `VariableHoverMixin`, shared tooltip logic for
`{{variable}}` placeholders in text widgets.

### Typing pattern (PYPOST-250)

The mixin uses a generic bound to `QWidget` so type checkers understand `self`:

```python
TWidget = TypeVar("TWidget", bound=QWidget)

class VariableHoverMixin(Generic[TWidget]):
    def mouseMoveEvent(self: TWidget, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)
```

Consumers declare multiple inheritance without type parameters:

```python
class VariableAwareLineEdit(VariableHoverMixin, QLineEdit):
    ...
```

Checkers infer `TWidget` as `QLineEdit` from the MRO.

### Requirements for host widgets

- Host must be a `QWidget` subclass (typically `QLineEdit` or `QPlainTextEdit`).
- Host must implement `_get_text_at_cursor(event) -> tuple[str, int]`.
- Initialize the mixin after the QWidget base: `QLineEdit.__init__(self)` then
  `VariableHoverMixin.__init__(self)`.

### Line-scoped scan (PYPOST-120, PYPOST-122)

For multiline editors, `VariableHoverMixin` limits expression lookup to the line under
the cursor instead of scanning the full document on every `mouseMoveEvent` (PYPOST-120
mitigation from PYPOST-13 tech debt; implemented in PYPOST-122):

- `_hover_line_scoped_scan` — when `True`, `_prepare_hover_scan_context` uses
  `_slice_line_at_index` before `_find_hover_expression`.
- `VariableAwarePlainTextEdit` sets this flag in `__init__` (JSON body / `CodeEditor`).
- `VariableAwareLineEdit` keeps the default (`False`) because the buffer is a single line.

This preserves tooltip behaviour while avoiding O(document) regex iteration on large bodies.

### Scan-position cache (PYPOST-119)

`VariableHoverMixin` caches the last expression lookup and resolved tooltip keyed by
`(scan_text, scan_index)` — the scoped text slice and index passed to
`find_expression_at_index`. Repeated `mouseMoveEvent` calls while the pointer jitters over the
same token reuse the cache instead of re-running regex and `resolve_text`. Cache is cleared on
`set_variables` and `set_hidden_keys`. Complements line-scoped scan (PYPOST-122); table widgets
use a separate per-cell cache (PYPOST-132).

### Table cell hover cache (PYPOST-132)

`VariableAwareTableWidget` caches the last resolved tooltip keyed by `(row, column, cell_text)`.
Cache is cleared when variables or hidden keys change, or when the pointer leaves table cells.
Table cells are short single-line strings, so line-scoped scan does not apply; caching addresses
high-frequency `mouseMoveEvent` while the pointer remains in one cell.

### Variable value resolution (PYPOST-115, PYPOST-123)

`VariableHoverResolver.get_variable_value` (and the `VariableHoverHelper` facade) resolves plain
`{{name}}` placeholders:

- **Direct lookup:** `host` → value from the variables dict, or `<not defined>`.
- **Multi-hop chain:** when variables reference each other via plain tokens (e.g.
  `A = {{B}}`, `B = {{C}}`, `C = value`), the tooltip follows the chain until a literal
  value, a missing variable, a cycle, or the depth bound (`TOOLTIP_REFERENCE_MAX_DEPTH`).
  On cycle or depth limit, the tooltip shows the unresolved `{{name}}` token at that hop.
- **Hidden keys:** masking applies at every hop in the chain.
- **Function expressions** (`{{urlencode(db)}}`, nested calls, etc.) use
  `TemplateService.render_string` with `render_path="hover"` — unchanged.

### Variable snapshot (`set_variables`)

Hover resolution reads `self._variables` set by `set_variables`. Values are pushed from
`TabsPresenter` through `RequestWidget.set_variables` — not via per-widget signals. See
`doc/dev/variable_propagation.md` for the full presenter → widget flow and extension
checklist.

### Related

- Variable propagation: `doc/dev/variable_propagation.md`
- Variable-aware widgets: `pypost/ui/widgets/variable_aware_widgets.py`
- Tests: `tests/test_variable_hover.py`

### Tooltip styling (PYPOST-114)

Variable hover tooltips use `QToolTip.showText`, which renders Qt's shared tooltip widget.
Appearance is controlled by the global application stylesheet from `StyleManager`:

- Default rules live in `pypost/ui/styles/main.qss` under the `QToolTip { ... }` selector.
- Customize colors there (prefer `palette(tooltip-text)` / `palette(tooltip-base)` over hex
  literals) so tooltips follow the active theme.
- The same rules apply to static `setToolTip` strings elsewhere in the UI.

See also `doc/dev/ui_font_and_styles.md` for how stylesheets are loaded and applied.
