# PYPOST-97 Architecture: Document Regex Highlighting Limitations

## Overview

Documentation-only change. No new modules, regex changes, or runtime paths.

---

## Target Artifacts

| Artifact | Change |
| --- | --- |
| `pypost/ui/widgets/json_highlighter.py` | Expand class docstring: regex approach, five limitation bullets |
| `doc/dev/json_syntax_highlighting.md` | Add "Regex-based highlighting" section with patterns table and limitations |

---

## Docstring Content

1. **Approach** — `QRegularExpression` rules, not a JSON AST parser.
2. **Rationale** — per-block `QSyntaxHighlighter` model; speed for typical payloads.
3. **Limitations** — multiline strings/keys, escape edge cases, same-line key rule,
   numeric spec edge cases.
4. **Pointer** — `doc/dev/json_syntax_highlighting.md`.

---

## Out of Scope

- Changing regex patterns or rule order.
- New tests for spec edge cases not covered today.
- JSON validation in the highlighter (PYPOST-98).

---

## Verification

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_json_highlighter.py -q
```
