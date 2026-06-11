# PYPOST-541: Technical Debt

## Resolved

| ID | Severity | Item | Resolution |
| --- | --- | --- | --- |
| TD-11 | Medium | Implement v2 decrypt handlers (fernet + aes-gcm) | Implemented in PYPOST-541 |

## Follow-ups

| ID | Severity | Item | Notes |
| --- | --- | --- | --- |
| TD-12 | Low | v2 encrypt in `EnvironmentSecretsCodec` | `encrypt()` still emits v1; add when migration writes v2 |
| TD-13 | Low | Bulk v1→v2 re-encrypt CLI option | Depends on v2 encrypt; extend `encryption_migrate.py` |

## Verdict

**SAFE TO CLOSE** — acceptance criteria met; no blockers.
