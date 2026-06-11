# PYPOST-484: Technical Debt Analysis

## Shortcuts Taken

None. Validation logic moved to `EncryptedValueEnvelope.from_payload` without behavior changes.

## Code Quality Issues

- v1 schema constants live on `EncryptedValueEnvelope`; future v2 support will need explicit
  version dispatch rather than extending the same dataclass fields ad hoc.

## Missing Tests

- Integration tests for adapter + codec paths already cover decrypt failures; no additional
  scenarios identified for this refactor.

## Performance Concerns

None. `from_payload` performs the same checks as the removed `_validate_payload` method.

## Follow-up Tasks

- Add envelope v2 design when a new algorithm or metadata fields are required.
  Jira: [PYPOST-533](https://pypost.atlassian.net/browse/PYPOST-533)
