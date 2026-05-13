# PYPOST-447 — Developer Documentation

> Team Lead: team_lead
> Date: 2026-05-13
> Sprint: 201

---

## 1. What Changed and Why

PYPOST-447 adds optional encryption-at-rest for sensitive environment values. Before this task,
hidden variables were only masked in UI surfaces while values in `environments.json` remained
plain text.

The implementation keeps runtime behavior stable (`Environment.variables` remains
`Dict[str, str]`) and encrypts hidden-key values only during persistence when encryption is
enabled.

---

## 2. New Core Modules

- `pypost/core/key_provider.py`
  - Defines key abstractions and `LocalKeyProvider`.
  - Uses `PYPOST_ENV_ENCRYPTION_KEY` as key source.
- `pypost/core/environment_secrets_codec.py`
  - Encodes/decodes encrypted value envelope.
  - Validates payload schema/version/algorithm.

---

## 3. Storage Integration

`pypost/core/storage.py` now:

- encrypts hidden-key values on `save_environments()` when
  `PYPOST_ENV_ENCRYPTION_ENABLED=true`;
- decrypts encrypted payloads on `load_environments()`;
- tracks encryption observability metrics and structured logs;
- preserves atomic save semantics (`.tmp` + `os.replace`).

---

## 4. Observability Additions

Added metrics in `pypost/core/metrics.py`:

- `environment_value_encryptions_total`
- `environment_value_decryptions_total`
- `environment_encryption_errors_total{stage,reason}`

`MainWindow` now injects `metrics` into `StorageManager` for these counters.

---

## 5. Documentation Added

- `doc/dev/environment_encryption_at_rest.md` (new)
- `doc/dev/README.md` updated with a navigation entry.
- `doc/dev/hidden_variables.md` updated to clarify hidden-mask vs at-rest encryption.

---

## 6. Testing

Scope-focused suites:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_environment_secrets_codec.py \
  tests/test_key_provider.py \
  tests/test_storage_environments.py \
  tests/test_env_persistence_e2e.py
```

Full regression:

```bash
make test
```

Result: full regression passed (`389 passed, 7 warnings, 4 subtests passed`).

---

## 7. Related Tickets

- `PYPOST-447` — optional encrypted-at-rest storage for sensitive env values.
- `PYPOST-481` ... `PYPOST-487` — follow-up debt items created from review.
