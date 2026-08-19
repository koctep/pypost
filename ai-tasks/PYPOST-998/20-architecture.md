# PYPOST-998: Architecture Design

## Developer Quality Gate Architecture

1. **Gate Roles**:
   - `make check`: Developer loop gate. Fast (<10s), strictly offline, requires only standard virtualenv dependencies (`lint`, `test`, `verify-ai-tasks`).
   - `make check-lock-all`: Dependency verification gate. Invoked locally before pushing dependency edits and enforced in isolated CI matrix jobs.

2. **Makefile Target Structure**:
   - `check-lock-all` depends on `check-lock`, `check-lock-dev`, `check-lock-otel`, and `check-license-inventory`.
