# PYPOST-996: Architecture Design

## Lock Check Target Architecture

All three Makefile lock checking targets (`check-lock`, `check-lock-dev`, `check-lock-otel`) share a unified design:

1. **Compilation with Exponential Backoff Retry**:
   - Loops up to 3 attempts with delays 1s, 2s on transient failure.
   - If compile fails on all attempts: emits distinct stderr diagnostic `$(TARGET): uv pip compile failed after 3 attempts (network or tool issue)`, cleans up scratch files, and exits with code 2.
2. **Body Comparison**:
   - Strips header comments (`tail -n +3`) to avoid volatile header timestamp drift.
   - Compares stripped body via `diff -q`.
   - If mismatch found: emits distinct stderr message `$(TARGET): $(TXT) is stale relative to $(IN) (run 'make $(LOCK_TARGET)' and commit)`, cleans up scratch files, and exits with code 1.
3. **Scratch File Cleanup**:
   - Removes `*.check`, `*.body`, and `*.check.body` in all paths (success, stale lock, compile error).
