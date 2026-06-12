# PYPOST-447: Technical Debt Analysis

## Shortcuts Taken

- Encryption settings are currently driven by process environment variables only
  (`PYPOST_ENV_ENCRYPTION_ENABLED`, `PYPOST_ENV_ENCRYPTION_KEY`) and are not yet integrated into
  user-facing application settings.
- user-facing application settings. — [PYPOST-481](https://pypost.atlassian.net/browse/PYPOST-481)

## Code Quality Issues

- `pypost/core/storage.py`
  - Encryption policy, serialization, deserialization, metrics, and logging are combined in one
    class, which increases maintenance complexity.
  - Suggested improvement: extract environment value serialization/encryption into a dedicated
    storage adapter service.
- storage adapter service. — [PYPOST-482](https://pypost.atlassian.net/browse/PYPOST-482)
- `pypost/core/key_provider.py`
  - `LocalKeyProvider` currently supports only one active key from environment variables.
  - Suggested improvement: add provider chain support (app config, keyring, external secret store)
    and explicit rotation workflows.
- and explicit rotation workflows. — [PYPOST-483](https://pypost.atlassian.net/browse/PYPOST-483)
- `pypost/core/environment_secrets_codec.py`
  - Envelope schema validation is manual and error-prone as fields evolve.
  - Suggested improvement: represent payload via typed model to centralize validation rules.
- Suggested improvement: represent payload via typed model to centralize validation rules. — [PYPOST-484](https://pypost.atlassian.net/browse/PYPOST-484)

## Performance Concerns

- Per-value encryption during each save can add overhead for large environment dictionaries with
  many hidden keys.
- many hidden keys. — [PYPOST-485](https://pypost.atlassian.net/browse/PYPOST-485)
- Encryption/decryption operations occur synchronously in storage flow; very large datasets may
  cause visible UI pauses during load/save actions.
- cause visible UI pauses during load/save actions. — [PYPOST-486](https://pypost.atlassian.net/browse/PYPOST-486)

## Follow-up Tasks

- Evaluate migration from env-var-only key source to a configurable key provider strategy.
- Evaluate migration from env-var-only key source to a configurable key provider strategy. — [PYPOST-487](https://pypost.atlassian.net/browse/PYPOST-487)
