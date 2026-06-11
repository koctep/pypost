# PYPOST-544: Observability

## Existing logging

Settings re-encrypt already logs `settings_encryption_reencrypt_completed` with success, backup
path, and error count. No change required.

## Operator visibility

- **Before**: Operators saw inventory summary only after Settings re-encrypt.
- **After**: Result dialog adds **Re-encrypted** and **Reused** counts when the service returns
  `reencrypt_stats` — parity with CLI human output.

## Metrics

No new Prometheus counters (per PYPOST-535 scope).

## Verification

- [x] Unit test asserts stats in QMessageBox body
- [x] Service logs unchanged
