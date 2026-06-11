# PYPOST-382: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/testability.md` | New — unit testability patterns for RequestService, HTTPClient, MainWindow |
| `doc/dev/testing.md` | Cross-reference to testability guide |
| `doc/dev/gui_testing.md` | Cross-reference for MainWindow testing |
| `doc/dev/solid_audit.md` | Link to testability guide; note partial resolution |
| `doc/dev/tech-debt/PYPOST-40.md` | Mark testability item partially addressed |

## Rationale

Developers adding request-execution or MainWindow tests previously had to discover mocking
patterns from scattered test files. A single guide reduces onboarding time and documents which
gaps remain out of scope.

## Verification

- Doc examples match constructor signatures in source.
- Test module index matches actual test class names.
- Jira follow-up links resolve to existing PYPOST-40 backlog items.
