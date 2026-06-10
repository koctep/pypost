# PYPOST-483: Extend key provider for flexible sources and key rotation

## Goals

Environment encryption at rest (PYPOST-447) and user-facing encryption settings (PYPOST-481)
depend on resolving encryption key material at runtime. Today the product supports only a single
key supplied through a process environment variable. That limits how users and administrators can
operate the feature in real deployments: desktop users may not control launch scripts, teams may
require OS-integrated or centrally managed secret stores, and security policies expect periodic
key rotation without losing access to previously encrypted data.

This task defines business requirements for flexible, secure key resolution and a supported key
rotation lifecycle while preserving backward-compatible behavior for existing environment-variable
setups.

## Programming Language

Python 3.10+

## User Stories

- As a security-conscious administrator, I want encryption keys to be resolved from the secure
  location appropriate to my deployment so I am not forced to embed secrets in launch scripts.
- As a desktop user, I want the application to obtain key material through supported secure
  channels when environment variables are unavailable or impractical.
- As an administrator, I want a defined fallback order when a preferred key source is missing so
  the application can still start when a secondary source is configured.
- As a security-conscious administrator, I want to rotate encryption keys on a schedule so
  compromised or aged key material can be retired without blocking normal use.
- As an existing user, I want encrypted environment data written before a rotation to remain
  readable after the active key changes so I do not lose project secrets during rotation.
- As an existing user, I want my current environment-variable key setup to keep working without
  mandatory migration so upgrades do not disrupt current workflows.
- As a maintainer, I want predictable failure behavior when required key material cannot be
  resolved so support and operations can diagnose misconfiguration quickly.

## Definition of Done

- Key material can be resolved from more than one supported secure source, with a defined
  fallback order when configured sources are tried in sequence.
- The process-environment-variable key path remains a supported source and continues to work for
  deployments that rely on it today.
- The product supports an explicit key rotation workflow: a current active key for new encryption
  and access to previously used keys needed to read existing encrypted values.
- Encrypted environment values that reference an older key identifier remain decryptable while the
  corresponding historical key material is available.
- New encryption uses the current active key after rotation.
- Misconfiguration (missing keys, unavailable sources, unknown key identifiers) produces clear,
  safe errors without exposing key material.
- Automated tests verify multi-source resolution, rotation scenarios, and backward compatibility
  with the environment-variable path.
- User- or operator-facing documentation describes supported key sources, fallback behavior, and
  the rotation workflow at a business/operational level.

## Task Description

PYPOST-447 introduced optional encryption for hidden environment variable values at rest. Each
encrypted value is associated with a key identifier so the product knows which key was used at
encryption time. PYPOST-481 added application settings for encryption policy and key source
strategy, but only the environment-variable source is available in practice.

Technical debt from PYPOST-447 identified that key resolution is limited to one active key from
environment variables. That gap blocks planned key-management options (OS keyring, external secret
store, and configurable source fallback selected in application settings) and makes key rotation
unsafe: changing the active key can prevent reading data encrypted under the previous key.

### In Scope

- Business requirements for resolving encryption keys from multiple supported secure sources.
- Business requirements for ordered fallback among configured sources when a preferred source
  does not yield key material.
- Business requirements for key rotation: active key for new encryption, retained access to
  prior keys for existing encrypted data.
- Business requirements for key-identifier compatibility across rotation and mixed encrypted data.
- Backward-compatible support for the existing environment-variable key path.
- Enabling Settings options for newly available key sources (not a full UI redesign).
- Failure and observability expectations suitable for operations and support (without defining
  implementation).

### Supported key sources (in scope)

This task requires the product to resolve encryption key material from these source categories:

1. **Process environment variable** (existing): the current supported path; must remain available
   for backward-compatible deployments.
2. **OS-integrated keyring**: key material stored in the operating system's secure credential store.
3. **External secret store**: key material obtained from a centrally managed secret service via a
   configurable provider chain.

Application settings may select which source strategy to use and the fallback order among
configured sources. Settings must not persist raw encryption key material; keys remain in their
designated secure stores or in environment configuration managed outside application config files.

### Key rotation operator workflow

Administrators perform rotation using a supported workflow with these business steps:

1. **Introduce a new active key**: provision new key material and register it as the current
   active key with a new key identifier.
2. **Retain historical keys**: keep previously used keys registered and available so existing
   encrypted values remain readable.
3. **Verify access to existing data**: confirm that values encrypted before rotation still decrypt
   successfully while historical key material is available.
4. **Rotation complete**: the new active key is used for all new encryption; historical keys remain
   available for reading existing data; the operator has verified that pre-rotation data is still
   accessible. Bulk re-encryption of all stored values is not required for rotation to be
   considered complete.

### Out of Scope

- Automatic bulk re-encryption of all stored values immediately after rotation (covered by
  follow-up migration work such as PYPOST-487).
- Storing raw encryption key material in application settings or environment JSON files.
- Using application settings for anything other than strategy selection and source fallback order.
- Full UI redesign unrelated to enabling Settings options for newly available key sources.
- Changes to encryption algorithms or envelope format beyond what rotation compatibility requires.
- Cloud vault product selection or vendor-specific integration contracts (specific providers are
  decided in later steps if in scope).

## Functional Requirements

- The system must resolve encryption key material from multiple supported secure sources according
  to administrator or product configuration.
- The system must support an ordered fallback among configured sources when an earlier source does
  not provide usable key material.
- The environment-variable key path must remain a supported source and must not regress for
  existing users.
- The system must designate one current active key for encrypting new sensitive environment
  values.
- The system must resolve key material by key identifier so values encrypted before a rotation
  remain readable when historical key material is still available.
- After rotation, newly encrypted values must use the new active key and its identifier.
- The system must fail safely when no configured source provides the required key material.
- The system must fail safely when encrypted data references a key identifier for which no key
  material is available.
- Key resolution behavior must integrate with the existing encryption-at-rest feature and
  settings-driven key source strategy from PYPOST-481 without requiring users to bypass
  application settings.
- Application settings must record only encryption policy, source strategy, and fallback order;
  they must not store raw encryption key material.
- The product must support the key rotation operator workflow defined in this document.

## Non-functional Requirements

- **Security**: key material must not be written to persisted application or environment config
  files; resolution must minimize exposure in logs and error messages.
- **Backward compatibility**: deployments using only `PYPOST_ENV_ENCRYPTION_KEY` (and related
  settings defaults) must behave as today until administrators opt into additional sources or
  rotation steps.
- **Reliability**: encrypted environment data must remain readable across application restarts
  when configured key material is available.
- **Operability**: rotation and multi-source setup must be documentable for administrators
  without reading source code.
- **Maintainability**: requirements must allow automated verification of source fallback, rotation,
  and identifier compatibility in later development steps.

## Constraints and Assumptions

- Encryption-at-rest behavior from PYPOST-447 and settings integration from PYPOST-481 remain the
  surrounding product context.
- Encrypted payloads already carry a key identifier; compatibility requirements apply to that
  model.
- Python 3.10+ and project documentation conventions (including 100-character line length)
  apply to implementation artifacts in later steps.
- Additional key source options exposed in Settings depend on this work; enabling those Settings
  options is in scope for this task, while broader UI redesign is not.
- Application settings (`settings.json`) select strategy and fallback order only; they do not
  store key material.
- Administrators are responsible for provisioning and securing key material in external stores;
  the product resolves keys but does not replace enterprise secret-management policy.

## Main Entities and Interactions

- **Encryption key material**: secret used to protect hidden environment values at rest; must
  remain outside plain config files.
- **Key identifier**: stable label associated with a specific key version, stored with encrypted
  values so the correct key can be used when reading data.
- **Active encryption key**: the key currently used when encrypting new sensitive values.
- **Historical encryption key**: a previously active key still required to decrypt existing data
  until those values are re-encrypted or retired.
- **Key source**: a configured channel from which the product obtains key material; in scope
  categories are process environment variable, OS-integrated keyring, and external secret store.
- **Key source fallback order**: the sequence in which sources are attempted when resolving key
  material.
- **Key rotation workflow**: the supported operator steps to introduce a new active key while
  retaining access to keys needed for existing encrypted data.
- **Environment storage**: persisted environments containing plain and encrypted hidden values.
- **Encryption settings**: user or administrator preferences that select key source strategy,
  fallback order, and encryption policy (from PYPOST-481); they do not hold raw key material.
- **Administrator / operator**: configures key sources, fallback order, and performs rotation.

Interaction overview:

1. Administrator configures key sources and fallback order appropriate to the deployment.
2. On save or load of environment data, the product resolves the active key for encryption and
   resolves keys by identifier for decryption.
3. During rotation, the administrator follows the key rotation operator workflow: introduce a new
   active key, retain historical keys, verify existing data still decrypts, and confirm rotation
   complete when new writes use the new key and old data remains readable.
4. If the preferred source is unavailable, the product attempts configured fallback sources
   before failing.
5. If settings do not override key strategy, behavior aligns with the existing environment-variable
   default path.

## Q&A

- Q: Why not store the encryption key in application settings?
  A: Application settings select strategy and fallback order only. Persisting key material there
  increases local disclosure risk; keys belong in dedicated secure stores or environment
  configuration managed outside application config files.
- Q: What is the difference between application settings and key sources?
  A: Settings choose which source strategy and fallback order to use. Key material itself lives in
  the environment variable, OS keyring, or external secret store—not in settings or environment
  JSON files.
- Q: Why is key rotation required if encryption already works with one key?
  A: Security policies expect periodic key changes; without rotation support, changing the key
  breaks access to data encrypted under the old key.
- Q: Must every encrypted value be re-encrypted immediately after rotation?
  A: No. Mixed key identifiers in storage are acceptable during transition; new writes use the
  active key. Bulk re-encryption is out of scope for this task.
- Q: What happens if historical key material is removed too soon after rotation?
  A: Values encrypted with that key identifier cannot be decrypted; the product must surface a
  clear, safe error consistent with PYPOST-447 failure expectations.
- Q: How does this relate to PYPOST-481 Settings?
  A: PYPOST-481 introduced key source strategy and fallback preferences in settings but only the
  environment source is implemented; this task supplies the key-management capability those
  settings select, and enables Settings options for additional sources.
- Q: How does this relate to PYPOST-487?
  A: PYPOST-487 covers broader migration when encryption settings change; this task focuses on
  resolving keys from multiple sources and supporting rotation, which migration tooling depends on.
