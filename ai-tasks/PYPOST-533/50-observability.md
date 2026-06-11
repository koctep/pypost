# PYPOST-533: Observability

## Logging

- Added `env_value_decrypt_failed reason=unsupported_version` when decrypt receives a parsed v2
  envelope (includes `version` and `algorithm` in structured fields).
- Existing v1 encrypt/decrypt debug and error logs unchanged.

## Metrics

No new metrics; v2 decrypt is not yet supported and v2 payloads are not written by `encrypt()`.

## Operator impact

v2 envelopes on disk (if introduced manually or by a future migration) fail decrypt with a clear
`EnvironmentEncryptionError` message before key lookup.
