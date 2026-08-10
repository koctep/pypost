# PYPOST-1000: Technical Debt Analysis

## Shortcuts Taken

- None that compromise correctness. The locking test patches
  `EnvironmentDialog` (same pattern as the existing export-serializer wiring
  test) so the suite never runs a real modal `exec()`. That is intentional
  isolation, not a crutch: the assertion still invokes the captured
  `read_import_file` against a temp JSON file and a `FakeStorageManager`
  subclass.
- `ImportFakeStorage` locally overrides
  `deserialize_environment_records` because the shared
  `FakeStorageManager` stub returns empty results. This avoids changing the
  shared helper’s behavior for unrelated collection tests.

## Code Quality Issues

- Shared `FakeStorageManager.deserialize_environment_records` remains a
  no-op stub (`([], ())`). A future improvement could provide a plaintext
  `model_validate` default (or an opt-in helper) so import/presenter tests
  need not redefine the method. Low priority; not required to close this
  task.
- The production `read_import_file` binding is still a one-line lambda in
  `_open_env_manager`. That matches PYPOST-986 design; extracting a named
  helper is optional readability only and is not needed for this lock.

## Missing Tests

- None for this task’s DoD: presenter → dialog `read_import_file` working
  callable is now locked.
- Sibling gaps remain tracked elsewhere (do not re-ticket here):
  - Import… button `QTest.mouseClick` wiring (PYPOST-1001)
  - Overwrite × ciphertext reuse round-trip (PYPOST-999)
  - 3+ conflict / `generate_import_copy_name` combinatorial cases
    (PYPOST-1002)

## Performance Concerns

None. The new test is hermetic and sub-second; no production path changed.

## Deviations from Initial Architecture

None. Implementation matches `20-architecture.md`: patch-where-used,
FakeStorageManager-based double, invoke captured callable, no production
change when green.

## Hardcoded Values

- Fixture JSON uses a single illustrative host string
  (`imported.example.com`) inside the test only — acceptable for a locking
  fixture.

## Follow-up Tasks

1. **Optional: give `FakeStorageManager.deserialize_environment_records` a
   plaintext `Environment.model_validate` default** (or a documented helper
   factory) so import/presenter tests can use the shared fake without a
   local subclass. Low priority; does not block shipping this lock.
   Jira: [PYPOST-1060](https://pypost.atlassian.net/browse/PYPOST-1060)
   - Priority: Low
   - Type: Debt
2. No other follow-ups from this task. Sibling verification debt stays on
   existing tickets (PYPOST-999 / 1001 / 1002).
