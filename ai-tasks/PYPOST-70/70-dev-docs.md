# PYPOST-70: Dev Docs

## Updated files

No `doc/dev/` updates required.

## Summary

Internal attribute rename with no public API or user-facing behavior change. `RequestTab` still
uses `QVBoxLayout(self)`; callers should use `tab.layout()` per standard Qt conventions.
