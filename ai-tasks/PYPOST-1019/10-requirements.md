# PYPOST-1019: Settings UI for upgrade-v2

## Goals

From a business and operator perspective, environment secrets stored in earlier schema versions (v1) need a seamless, safe, and easily discoverable way to be modernized to the current standard format (v2) directly from the application's Settings interface. Providing a visual affordance prevents operators and end-users from having to drop into a command-line terminal to migrate their sensitive environments, while ensuring automatic backup protection against data loss.

## User Stories

- **As an Application User / Security Operator**, I want an intuitive action in the Settings dialog under Encryption Migration to upgrade existing stored secrets to version 2, so that all persisted environments use the latest cryptographic envelope format.
- **As an Application User**, I want to be prompted with a clear confirmation dialog and have a backup automatically created before any files are rewritten, so that my sensitive secrets are never corrupted or lost during migration.
- **As an Application User**, I want clear visual feedback showing the migration results (number of upgraded envelopes, reused items, errors) once the operation completes, so that I have certainty regarding the outcome.

## Definition of Done

- A dedicated "Upgrade encrypted values to v2" action is available within the Settings interface under the Encryption Migration section.
- The action is enabled only when encryption services are configured and operational.
- Triggering the action displays a safety confirmation dialog explaining the operation.
- Confirming the action executes the upgrade safely with an automatic timestamped backup of the environment data.
- Rejecting the confirmation cancels the operation with no changes to stored data.
- The user receives a structured result dialog detailing the outcome upon completion.
- Automated tests verify user interface behavior, cancellation paths, and execution feedback.

## Task Description

- **Implementation Language**: Python
- **Problem**: Previously, upgrading encrypted stored secrets from version 1 to version 2 was accessible only via the CLI migration tool. Users managing environments through the graphical desktop interface had no in-app mechanism to initiate the upgrade.
- **Business Scope & Boundaries**:
  - Add an in-app trigger for secret format upgrade in the settings interface.
  - Run the migration in the background to prevent interface freezing.
  - Ensure zero data loss via automatic pre-migration backup.
  - Exclude changes to the underlying cryptographic encryption algorithm itself (which is already implemented).
- **Business Domain Entities**:
  - *Environment Secret*: Sensitive key-value pair stored in an encrypted envelope on disk.
  - *Migration Backup*: A timestamped archive copy of the environments storage created prior to modifications.
  - *Migration Summary*: A structured report presented to the user indicating success status, upgraded counts, and any errors.

## Q&A

- **Q**: What happens if an environment is already upgraded to version 2?
  - **A**: The upgrade process safely skips already-upgraded secrets and reports the status without redundant modifications.
- **Q**: Is user data backed up before migration?
  - **A**: Yes, a timestamped backup of the storage file is created before any disk write.
