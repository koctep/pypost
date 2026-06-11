# PYPOST-541: Observability

## Logging

- Removed `env_value_decrypt_failed reason=unsupported_version` for v2 (decrypt now supported).
- v2 decrypt attempts log `env_value_decrypt_attempt` with `version` and `algorithm`.
- v2 aes-gcm success logs `env_value_decrypted` with `algorithm=aes-gcm`.
- v2 aes-gcm auth failure logs `env_value_decrypt_failed reason=invalid_token` with
  `algorithm=aes-gcm`.

## Metrics

No new metrics; existing decrypt counters apply when adapter/codec paths run.

## Operator impact

v2 envelopes on disk decrypt with registered key material; failures use the same message as v1
invalid-token paths.
