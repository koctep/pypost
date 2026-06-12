# PYPOST-251: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | Note PYPOST-251 closure in Core manager unit tests section |
| `ai-tasks/PYPOST-29/40-tech-debt.md` | Mark PYPOST-251 automated-tests debt as resolved |

## Summary

Documented that the PYPOST-29 debt item — blocked on missing pytest setup — is obsolete. Pytest
infrastructure and a broad automated suite are operational; manager-specific follow-up was
completed in PYPOST-252.

## Verification

- `doc/dev/testing.md` cross-links PYPOST-251 and PYPOST-252 in the manager tests section.
- `make test` entry points and `tests/conftest.py` references remain accurate.
