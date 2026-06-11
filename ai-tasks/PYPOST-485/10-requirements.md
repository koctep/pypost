# PYPOST-485: Optimize per-value encryption overhead on environment save

## Goals

Users with large environment datasets and many hidden (encrypted) variables experience
slow saves because every hidden value is re-encrypted on each persist, even when only one
variable changed. This task reduces save latency while preserving encryption-at-rest
security and deterministic round-trip behavior.

## User Stories

- As a developer with dozens of secret environment variables, I want saves to complete
  quickly when I edit a single value so the app stays responsive.
- As a security-conscious user, I want unchanged secrets to remain encrypted at rest with
  the same envelope as before, without unnecessary re-encryption that could complicate
  key-rotation auditing.
- As an operator, I want encryption policy changes (enable/disable, key source) to still
  produce correct on-disk payloads without stale ciphertext.

## Definition of Done

- Save path avoids re-encrypting hidden variables whose plaintext value is unchanged
  since the last successful persist.
- Changed, newly hidden, or policy-affected variables are still encrypted on save.
- Load/save round-trip and existing encryption tests pass.
- Observability distinguishes full encrypt vs envelope reuse where applicable.
- Developer documentation describes selective re-encrypt behavior.

## Task Description

Profile and optimize the environment save hot path introduced in PYPOST-447. Focus on
dirty tracking or selective re-encrypt so large `environments.json` writes do not
encrypt every hidden key on every save. Behavior must remain secure and deterministic
relative to acceptance criteria above.

## Q&A

- Q: Why optimize saves instead of only async I/O (PYPOST-486)?
  A: Async moved work off the UI thread; this task reduces CPU work per save so background
  saves finish faster and use less battery.
- Q: Source?
  A: Performance concern tracked in [PYPOST-447 tech debt](https://pypost.atlassian.net/browse/PYPOST-447).
