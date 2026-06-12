# PYPOST-485: Technical Debt Analysis

## Shortcuts Taken

- Persisted-state cache is in-process only; external edits to `environments.json` are not detected
  until the next `load_environments()` call.

## Code Quality Issues

- None blocking. Selective logic is localized to `EnvironmentVariablesAdapter`.

## Performance Concerns

- Very large single-environment dictionaries still iterate all keys on save (O(n)); only Fernet
  encrypt calls are skipped for unchanged hidden keys.
- Decrypt-on-load for large datasets remains synchronous on the worker thread (PYPOST-486 scope).

## Follow-up Tasks

- Add benchmark or profiling harness for environments with 100+ hidden keys to guard regressions.
- Add benchmark or profiling harness for environments with 100+ hidden keys to guard regressions. — [PYPOST-534](https://pypost.atlassian.net/browse/PYPOST-534)
- Consider persisted `kid` rotation batch job integration with reuse stats in migration CLI output.
- Consider persisted `kid` rotation batch job integration with reuse stats in migration CLI output. — [PYPOST-535](https://pypost.atlassian.net/browse/PYPOST-535)
