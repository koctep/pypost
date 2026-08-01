# PYPOST-938: Dev Docs

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | New § **Packaging doc lock strategy (PYPOST-922 / PYPOST-938)** — KEEP decision, locked modules/tokens, HARDEN revisit triggers, focused pytest command |
| `doc/dev/testing.md` | Makefile automation table row for PYPOST-938 |
| `tests/test_agent_e2e_broader_packaging_doc.py` | Module docstring pointer to testing.md strategy section |

## Overview

Developers editing broader agent e2e packaging docs should preserve locked
tokens or update the lock module intentionally. Hardening is deferred until
documented triggers fire.

## Troubleshooting

If a doc edit fails packaging contract tests, check the token table in
`doc/dev/testing.md` § Packaging doc lock strategy before rephrasing prose.
