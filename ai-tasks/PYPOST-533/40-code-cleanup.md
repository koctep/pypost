# PYPOST-533: Code Cleanup

## Lint and format

- No new linter issues in `environment_secrets_codec.py` or codec tests.
- `TypeAlias` import follows Python 3.10 typing conventions used elsewhere in the project.

## Scope check

- v1 parsing extracted to `_from_payload_v1` without behavior changes.
- v2 model and dispatch are self-contained; no adapter or storage changes.
- `encrypt()` output shape unchanged (v1 only).

## Review

Ready for observability and tech-debt review.
