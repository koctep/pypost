# PYPOST-999: Dev Docs

## Updated

| File | Change |
| --- | --- |
| `doc/dev/environments_dialog.md` | Point at Overwrite × ciphertext-reuse locking test |
| `doc/dev/environment_encryption_at_rest.md` | New § Overwrite × selective re-encrypt (999) |

## Not changed

| File | Rationale |
| --- | --- |
| `doc/dev/testing.md` | No new pytest/CI policy; timeout rules unchanged |
| `doc/dev/logging.md` | No new log events |
| `doc/user/environments.md` | No user-facing import/encryption behavior change |

## Template coverage (70-dev-docs.mdc)

- Overview — reuse/Overwrite interaction noted under encryption + environments dialog
- Architecture — cross-link between import docs and selective re-encrypt
- API / Usage — pytest invocation for the locking test
- Configuration — unchanged (local Fernet env vars already documented)
- Troubleshooting — guard table for KEEP reuse / CHANGE re-encrypt

## Self-Review

- [x] Docs in `doc/dev/`
- [x] English Markdown per `.cursor/lsr/do-markdown.md`
- [x] Test-only task — minimal delta; no duplicate product API rewrite
