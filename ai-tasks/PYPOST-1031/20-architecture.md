# PYPOST-1031: Architecture Design

## Relative Link Checker Scope Expansion

1. **Target Aggregation**:
   - `_DEFAULT_TARGETS`:
     - `doc/user/*.md` (13 User Guide modules).
     - `doc/README.md` (Docs index).
     - `README.md` (Repository root).
     - `examples/README.md` (Example fixtures catalog).

2. **Automated Verification**:
   - `tests/test_doc_user_relative_links.py` validates all 16 documentation targets in CI and local `make check`.
