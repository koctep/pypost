# PYPOST-1379: Developer Documentation

## Overview

PYPOST-1379 (MASK-3) implements interactive click-to-reveal response masking in desktop GUI `ResponseView` for HTTP requests configured with `hidden_response_fields`. Sensitive fields (such as authentication tokens, passwords, secret keys, and PII) are masked by default with `"***"` and subtle styling to prevent visual exposure during screen sharing, while enabling developers to interactively click and reveal or re-mask values on demand.

---

## Documentation Updated

1. **`doc/dev/hidden_response_fields.md`**:
   - Expanded Section 3 with the comprehensive MASK-3 interactive click-to-reveal GUI masking architecture.
   - Documented the `MaskedTokenSpan` data structure and `JsonMaskFormatter` AST parsing.
   - Documented `ResponseMaskController` lifecycle, `ExtraSelection` visual styling (neutral dashed underline for masked, green dotted underline for revealed), viewport mouse hover cursor, and tooltips.
   - Documented in-place click-to-reveal toggle mechanics, `QTextCursor` text replacement, and downstream span offset delta shifting.
   - Documented subsystem coexistence: `JsonHighlighter` regex highlighting, search navigation / match counter synchronization, code folding block stability (`FoldController`), and selection context menu ('Set Variable', 'Copy').
   - Documented large-document fallback (>100 KB) and in-flight streaming response safety.
   - Documented raw `ResponseData` immutability and telemetry metrics (`hidden_value_masks_applied_total` with label `surface="gui_response"`).

2. **`doc/user/requests.md`**:
   - Updated User Guide under `## Response` with a dedicated section `### Interacting with masked fields`.
   - Documented hover tooltips and pointing hand cursor on masked fields (`"***"`).
   - Documented clicking `"***"` to reveal raw secret in place and clicking again to re-mask.
   - Documented drag-selection safety (not triggering toggle) and right-click context menu actions ("Copy" and "Set Variable").
   - Documented search synchronization with revealed/masked values and 100 KB large-response fallback.

---

## Architecture & Implementation Summary

- **Token Span Model & AST Parsing (`pypost/ui/widgets/response_mask_controller.py`)**:
  - `MaskedTokenSpan`: Lightweight dataclass tracking character boundaries (`start_pos`, `end_pos`), serialized unmasked value (`raw_value`), placeholder (`"***"`), presentation state (`is_revealed`), and selector path.
  - `JsonMaskFormatter`: Walks the parsed JSON structure with indentation, evaluates selector path variants via `sensitive_text_sanitizer.format_path_variants` (supporting root keys, dot paths, and array wildcards), emits `'"***"'`, and records exact token spans.
  - `format_masked_json`: Parses raw JSON and returns pretty-printed masked text with discovered token spans.
- **Controller Lifecycle & Affordance (`ResponseMaskController`)**:
  - Installs an event filter on `FoldableCodeView.viewport()` with mouse tracking enabled.
  - Maps viewport mouse moves to character offsets via `cursorForPosition(pos).position()`, setting `PointingHandCursor` and displaying hover tooltips (`"Click to reveal"` / `"Click to re-mask"`).
  - Decorates spans via `QTextEdit.ExtraSelection` (neutral dashed underline for masked, subtle green dotted underline for revealed) without mutating document text or syntax highlighting.
  - Detects left-clicks on `MouseButtonRelease` without active drag selection (`not textCursor().hasSelection()`), toggling the span in place via `QTextCursor.insertText()`.
  - Adjusts all subsequent downstream spans by `delta = len(new_text) - len(old_text)` to prevent index drift.
  - Resyncs fold regions via `fold_controller().ensure_scanned()` and updates search match counters via `_on_search_text_changed()`.
- **GUI Integration (`ResponseView` & `TabsPresenterWorker`)**:
  - `ResponseView.display_response(response, hidden_fields=...)` wires JSON masking when hidden fields are configured and document size is within threshold (`<= 100 KB`).
  - Increments Prometheus / OpenTelemetry counter `hidden_value_masks_applied_total` with `surface="gui_response"`.
  - Maintains `_last_response` and `_last_hidden_fields` to preserve masking during indentation re-formatting (`set_indent_size`).
  - Bypasses masking for documents larger than 100 KB (`LARGE_DOC_CHAR_THRESHOLD`) to guarantee UI responsiveness.
  - Handles streaming chunks via `append_body` without masking; formats and masks complete response upon finish.
  - `TabsPresenterWorker._on_request_finished` passes `tab.request_data.hidden_response_fields` to `display_response`.

---

## Verification Instructions

All verification operations must be executed exclusively through repository `make` targets:

```bash
# Run fast test suite for GUI response view click-to-reveal masking
make test PYTEST_ARGS="tests/test_gui_response_view_click_to_reveal.py"

# Run flake8 static analysis and doc linting
make lint

# Run static type checking against the baseline gate
make typecheck

# Verify integrity of AI task artifacts
make verify-ai-tasks

# Run combined quality gate
make check
```
