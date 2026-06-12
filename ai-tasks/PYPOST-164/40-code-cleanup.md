# PYPOST-164: Code Cleanup

## Scope

Test-only change; no production code modified.

## Checks

| Check | Result |
| --- | --- |
| Line length ≤ 100 | Pass |
| Trailing whitespace | None |
| Per-test timeout (`pytestmark`) | `60` on module |
| `qapp` fixture + `finally: view.close()` | Applied in all tests |
| Import order | stdlib → third-party → local |

## Notes

No lint or format changes required beyond the new test module.
