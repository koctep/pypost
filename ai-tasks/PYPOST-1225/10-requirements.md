# PYPOST-1225: [Libraries] At-Rest Encryption for Local Overlay Secrets

## Goals

Collection library overlays stored at `~/.pypost/libraries_data/<library-id>/overlay.json` store user-specific configuration overrides and sensitive credentials (such as API keys, tokens, and basic auth passwords).
Currently, while file permissions are restricted (0o600 / 0o700), secrets in `overlay.json` are written in plaintext JSON.

To provide defense-in-depth and align with the application's overall encryption-at-rest architecture:
- Secret values stored in local library overlays must support optional symmetric encryption at rest using the existing application cryptographic key management infrastructure.
- Non-secret variable overrides, active profile selections, and metadata remain unencrypted to support inspection and indexing.
- Seamless backward compatibility must be guaranteed: existing plaintext overlays must continue to load without error, and encrypted overlays must transparently decrypt on load when encryption is enabled.

**Implementation language**: Python

## User Stories

- As a security-conscious developer or enterprise operator, I want local library secrets to be encrypted at rest on disk so that sensitive tokens are protected if local storage is accessed.
- As a collection library user, I want existing unencrypted overlay files to load seamlessly without manual migration steps.
- As an API developer, when encryption is enabled, I want secrets saved through `LocalOverlayManager` to be stored as encrypted envelopes on disk and transparently decrypted in memory upon load.

## Definition of Done

- `LocalOverlayManager` supports an optional encryption codec / key provider configuration.
- When an encryption codec is present and active, `LocalOverlayManager.save_overlay` encrypts dictionary values in `overlay.secrets` into standard encrypted envelopes on disk.
- Non-secret fields in `overlay.overrides` and metadata remain unencrypted.
- `LocalOverlayManager.get_overlay` transparently decrypts encrypted envelopes found in `overlay.secrets` back to plaintext in the returned `LocalLibraryOverlay` model.
- Plaintext secrets in existing files continue to load without failure (backward compatibility).
- Comprehensive unit and integration tests verify encryption, decryption, backward compatibility, and error handling.
- All quality gates pass cleanly.

## Task Description

- **Problem Description**: Sensitive API secrets and credentials in local library overlays are persisted in plaintext JSON within `overlay.json`.
- **Scope**: Extend `LocalOverlayManager` to optionally integrate with `EnvironmentSecretsCodec` (or `KeyProvider`) to encrypt secret values on write and decrypt on read, preserving full backward compatibility for plaintext files.
- **Constraints & Assumptions**: Do not break existing public methods on `LocalOverlayManager`. Plaintext overlays without encryption markers must load without error.

## Non-Functional Requirements

- **Security**: Secret credentials are encrypted using AES-GCM or Fernet envelopes at rest.
- **Robustness**: Graceful handling of missing or corrupt encryption keys without crashing the application.
- **Compatibility**: Plaintext JSON overlays continue to parse into `LocalLibraryOverlay`.

## Main Entities

- **Local Library Overlay**: Domain entity representing local overrides and secrets for a collection library.
- **Local Overlay Manager**: Service managing overlay file persistence, permissions, and serialization.
- **Secrets Codec**: Cryptographic component handling envelope encryption and decryption.

## User Scenarios

1. **Encrypted Overlay Persistence**: An operator saves an overlay with an API secret when encryption is active; the resulting `overlay.json` stores the secret as an encrypted envelope structure.
2. **Encrypted Overlay Loading**: The application reads `overlay.json` containing encrypted secret envelopes; `get_overlay` returns a `LocalLibraryOverlay` with decrypted plaintext secrets.
3. **Legacy Plaintext Loading**: The application reads a legacy `overlay.json` containing plaintext secret strings; `get_overlay` returns the overlay correctly without error.

## Q&A

| Question | Answer |
| --- | --- |
| Which fields in `overlay.json` are encrypted? | Only values in the `secrets` dictionary. Non-secret `overrides`, `active_profile`, and `library_id` remain unencrypted. |
| What happens if a secret is already encrypted or if encryption is disabled? | When encryption is disabled or no codec is provided, secrets are saved and loaded as-is in plaintext. |
