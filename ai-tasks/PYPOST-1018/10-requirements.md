# PYPOST-1018: [PYPOST-542] Default Runtime Encrypt to v2

## Goals

Following the introduction of the version 2 encrypted envelope specification in PYPOST-542, the default runtime save/encrypt path should be upgraded to version 2 (v2) envelopes.

To complete the rollout of modern encryption envelopes:
- Flip the default encryption envelope version from version 1 to version 2 across all runtime serialization and encryption operations.
- Maintain transparent backward compatibility for reading/decrypting existing version 1 envelopes.
- Ensure that existing environments and settings saved to disk automatically adopt version 2 format upon encryption.
- Provide full test coverage for default version 2 encryption and legacy version 1 fallback.

**Implementation language**: Python

## User Stories

- As a security-conscious developer, I want all newly encrypted environment variables and secrets to use the v2 envelope specification by default so that encryption metadata and modern algorithms are standard.
- As a user upgrading from earlier versions, I want my existing stored v1 encrypted secrets to continue working seamlessly without requiring immediate manual migration.

## Definition of Done

- Default encryption operations produce version 2 envelopes (`v=2`).
- Serialization workflows default to generating version 2 envelopes when persisting encrypted variables.
- Legacy version 1 envelopes can still be explicitly created via dedicated v1 encryption APIs when necessary.
- Decryption handles both version 1 and version 2 envelopes transparently.
- Automated tests verify default v2 generation, v1-to-v2 upgrade on save, and backward compatibility.
- Developer documentation is updated to reflect v2 as the default runtime encryption envelope.
- All quality gates pass cleanly.

## Task Description

- **Problem Description**: Previously, runtime encryption operations defaulted to version 1 envelopes, requiring explicit parameters or migration tooling to write version 2 envelopes. Now that version 2 is stable across the application, version 2 must become the standard default for all encryption paths.
- **Scope**: Flip the default encryption version across runtime secret codecs and variable serialization adapters. Retain version 1 creation capability for backward compatibility.
- **Constraints & Assumptions**: Preserves 100% backward compatibility for loading and decrypting version 1 envelopes.

## Non-Functional Requirements

- **Security**: Ensures consistent adoption of version 2 envelope standard.
- **Performance**: Zero performance regression compared to version 1 encryption.

## Main Entities

- **Encrypted Value Envelope**: Data structure holding ciphertext, version identifier, key identifier, and algorithm metadata.
- **Secrets Codec**: Engine encoding and decoding encrypted secrets.
- **Variables Adapter**: Serializer managing environment variable persistence and encryption.

## User Scenarios

1. **New Secret Creation**: A user adds a secret variable to an environment. Upon saving, the secret is encrypted into a version 2 envelope (`v: 2, alg: "fernet", kid: "...", ct: "..."`).
2. **Reading Existing Data**: An environment containing legacy version 1 envelopes is loaded. It decrypts seamlessly.
3. **Saving Updated Data**: When the environment is saved again, modified or re-encrypted values are saved in version 2 envelopes.

## Q&A

| Question | Answer |
| --- | --- |
| Does this break existing stored files? | No. The decryption engine already supports both version 1 and version 2 envelopes. |
| Is explicit version 1 encryption still available? | Yes, an explicit version 1 encryption method is preserved for legacy compatibility or tests. |
