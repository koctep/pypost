# Strict Rendering Performance

Strict rendering shares the lexer output used by validation with its failure-provenance and
fallback checks. When a render fails, valid strict placeholders are collected and evaluated in
one cached Jinja template. This avoids a second content scan and avoids compiling one temporary
template per placeholder.

The optimization is diagnostic-only: successful output, strict conversion exceptions, and
literal fallback behavior remain unchanged.
