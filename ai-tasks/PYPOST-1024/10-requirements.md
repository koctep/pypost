# PYPOST-1024: Expand thin Settings/Hotkeys User Guide pages

## Programming Language

English Markdown for user documentation.

## Goals

Follow-up from PYPOST-1015 (TD-5). `doc/user/settings.md` and `doc/user/hotkeys.md` were thin and lacked operational context for environment encryption migration workflows and focus-dependent in-app shortcuts.

**Business goal:** Expand `settings.md` with concrete encryption key sources, migration steps (Verify Key, Encrypt Plaintext, Re-encrypt/Key Rotation), and sensitive data masking; expand `hotkeys.md` with application, composer, body editor, response viewer, and history list shortcuts while maintaining clean relative links and Markdown lint compliance.

## Definition of Done

- [ ] `doc/user/settings.md` documents encryption configuration and migration steps.
- [ ] `doc/user/hotkeys.md` documents application, composer, editor, response, and history shortcuts with macOS modifier notes.
- [ ] All linters (`make lint-docs`, `make check-docs-links`) pass cleanly.
