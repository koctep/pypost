# PYPOST-481: Add user-facing configuration for environment encryption settings

## Goals

Environment encryption at rest (PYPOST-447) is currently controlled only through process
environment variables. Users who run PyPost from the desktop UI cannot discover, enable, or
understand the encryption setup without external documentation and shell configuration. This task
exposes encryption controls in application settings so users can configure behavior from the app
while preserving backward-compatible defaults for existing deployments.

## User Stories

- As a security-conscious user, I want to enable environment encryption at rest from Settings so
  hidden secret values are protected on disk without editing launch scripts.
- As an existing user, I want unchanged behavior when I have not configured encryption in
  settings, so my current environment-variable workflow keeps working.
- As an administrator, I want to choose where encryption key material comes from (starting with
  environment variables) so I can plan future key-management options.
- As a user setting up encryption, I want clear guidance on secure key setup so I do not store
  secrets in the wrong place.

## Definition of Done

- Settings UI exposes an encryption-at-rest toggle with enabled/disabled (and default) options.
- Settings UI exposes key source strategy selection with at least environment-variable source.
- Saved settings persist across restarts and drive encryption behavior on environment save/load.
- When settings fields are unset, behavior falls back to `PYPOST_ENV_ENCRYPTION_ENABLED` and
  `PYPOST_ENV_ENCRYPTION_KEY` as today.
- Secure setup guidance is documented for users.
- Automated tests cover settings persistence and storage encryption behavior driven by app settings.

## Task Description

PYPOST-447 introduced optional encryption for hidden environment variable values at rest. The feature
is togg only via process environment variables, which is opaque to desktop users and hard to
discover. This task adds user-facing configuration in app settings while keeping env-var control
as the backward-compatible default and the initial key source.

### In Scope

- Application settings fields for encryption enabled state and key source strategy.
- Settings dialog controls for those fields.
- Applying saved settings to environment storage encryption on save.
- Backward-compatible fallback to environment variables when settings are unset.
- User-facing documentation for secure encryption setup.

### Out of Scope

- New key provider implementations (keyring, cloud vault).
- Storing encryption keys in `settings.json`.
- UI redesign unrelated to encryption settings.
- Re-encrypting existing data automatically on toggle change.

## Functional Requirements

- The application must expose encryption-at-rest configuration in Settings.
- Users must be able to enable or disable encryption from Settings independently of editing
  environment variables.
- Users must be able to select key source strategy; environment variable source must be supported.
- Saved settings must be applied to environment persistence without requiring an app restart.
- Unset settings must defer to existing environment-variable behavior.
- Settings must not persist raw encryption key material.

## Non-functional Requirements

- **Security**: key material remains outside persisted settings; guidance must warn against
  storing keys in config files.
- **Backward compatibility**: existing users with env-var-only setup see no behavior change until
  they save new settings.
- **Usability**: controls must be understandable without reading source code.
- **Maintainability**: key source selection must allow future providers without breaking saved
  settings shape.

## Constraints and Assumptions

- Encryption implementation from PYPOST-447 remains the runtime engine.
- `LocalKeyProvider` continues to read `PYPOST_ENV_ENCRYPTION_KEY` for the environment
  source strategy.
- Python 3.10+ is used for implementation.
- Project markdown and 100-character line length rules apply to artifacts.

## Main Entities and Interactions

- **Application settings**: persisted user preferences including encryption policy.
- **Encryption policy**: whether hidden environment values are encrypted at rest.
- **Key source strategy**: where encryption key material is resolved from.
- **Environment storage**: persists environments and applies encryption on save/load.
- **User**: configures encryption through Settings and manages key material securely outside the
  app config file.

Interaction overview:

1. User opens Settings and configures encryption toggle and key source.
2. Application persists settings to disk.
3. On environment save/load, storage applies encryption policy using configured key source.
4. If settings omit encryption fields, storage follows process environment variables.

## Q&A

- Q: Why not store the encryption key in settings?
  A: Storing key material in `settings.json` increases local disclosure risk; keys belong in
  environment or future secure providers.
- Q: What happens when a user enables encryption but has no key?
  A: Save/load error paths from PYPOST-447 apply; user must configure key material per documented
  secure setup path.
- Q: Must we support multiple key sources now?
  A: Only environment variable is required; UI and model must allow future sources.
