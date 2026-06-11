# PYPOST-499: Add integration test for settings-to-encryption policy MainWindow flow

## Goals

PYPOST-481 wired user-facing encryption policy from Settings through `MainWindow` into
`StorageManager`. Unit tests cover the dialog, resolver, and storage in isolation, but no
single acceptance check follows the connected flow. A wiring break could regress
encryption policy without detection.

This task closes that quality gap with regression protection for the end-to-end contract
from PYPOST-481 technical debt.

## Programming Language

Python 3.10+

## User Stories

- As a **security-conscious user**, I want assurance that enabling encryption in Settings
  actually causes hidden environment values to be encrypted on save after I apply settings.
- As a **maintainer**, I want one automated check covering Settings save →
  `MainWindow.open_settings()` → `StorageManager.apply_encryption_settings()` so refactors
  cannot silently break encryption wiring.
- As a **developer**, I want coverage for enabled, disabled, and default (env-fallback)
  encryption modes through the MainWindow path.

## Definition of Done

1. An automated acceptance check verifies Settings save through `open_settings()` reaches
   `StorageManager` with the selected encryption policy.
2. **Enabled** mode: hidden keys are encrypted on subsequent environment save.
3. **Disabled** mode: hidden keys remain plain text even when env var would enable encryption.
4. **Default** mode: policy follows `PYPOST_ENV_ENCRYPTION_ENABLED` env fallback.
5. Coverage is traceable to [PYPOST-481 technical debt](ai-tasks/PYPOST-481/60-tech-debt.md).
6. No product behavior change unless a wiring defect is discovered.

## Task Description

### Problem Statement

Encryption policy flows through four touchpoints (Settings dialog, MainWindow, env idle wait,
StorageManager). Split unit coverage increases regression risk for security-relevant behavior.

### In Scope

- End-to-end flow from Settings through `open_settings()` to storage encryption policy.
- All three encryption modes: enabled, disabled, default (env fallback).
- Behavioral verification via environment save round-trip (encrypted vs plain hidden values).

### Out of Scope

- Key source / multi-provider chain E2E ([PYPOST-501](https://pypost.atlassian.net/browse/PYPOST-501)).
- Async startup gating ([PYPOST-509](https://pypost.atlassian.net/browse/PYPOST-509)).
- New product features or observability changes.

## Q&A

| Question | Answer |
|----------|--------|
| Feature or test task? | Test-coverage debt; behavior unchanged unless wiring defect found. |
| Why not only unit tests? | Unit tests miss the MainWindow orchestration hop. |
| Source? | [PYPOST-481 60-tech-debt.md](ai-tasks/PYPOST-481/60-tech-debt.md) Missing Tests. |
