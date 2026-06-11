# PYPOST-484: Developer Documentation

## Updates

- `doc/dev/environment_encryption_at_rest.md`
  - Payload Format section: document `EncryptedValueEnvelope` typed model and `from_payload`.
  - API section: add `EncryptedValueEnvelope.from_payload` usage notes.

## Validation

- [x] Payload field table unchanged (v1 backward compatible).
- [x] Cross-links to codec module path preserved.
- [x] No user-facing doc changes required (`doc/` out of scope).

## Notes

Dev docs focus on maintainers extending envelope schema; operator troubleshooting unchanged.
