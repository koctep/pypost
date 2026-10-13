# PYPOST-1375: [PYPOST-1284] Add reference collection with OAuth setup guidance and contract test suite

## Goals

Epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284) introduces a guided variable setup wizard with rich help guidance when adding or configuring MCP servers from a library collection. Previous layers delivered:
- **Layer 1 ([PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372))**: Extended the `CollectionVariable` model with optional `help_text` guidance.
- **Layer 2 ([PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373))**: Implemented the standalone `VariableSetupWizardDialog` with expandable `VariableGuidanceCard` widgets and secret masking toggles.
- **Layer 3 ([PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374))**: Integrated the wizard launch action and draft overlay persistence into `McpServersDialog` (`_McpServerEditor`).

While the core models and UI components exist, the repository lacks a realistic, production-grade reference collection demonstrating full end-to-end OAuth setup instructions, as well as a contract test suite verifying serialization, deserialization, wizard contract loading, and documentation integrity. Currently, `examples/collections/google_drive.json` defines bare variables (such as `google_drive_access_token`) with short single-line `description` strings, but no actionable step-by-step setup guidance.

This task ([PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375), WIZARD-4) represents Layer 4 (Reference Fixtures, Docs & Contract Testing) of the epic decomposition defined in [PYPOST-1368](https://pypost.atlassian.net/browse/PYPOST-1368).

**Business Goals:**
1. Provide users and collection authors with an authoritative, practical reference collection (`google_drive.json`) containing complete, step-by-step instructions for configuring OAuth 2.0 credentials in the Google Cloud Console (project creation, API enablement, OAuth consent screen, client IDs/secrets, scope assignment, and access token retrieval).
2. Validate and enforce that reference collection schemas parse cleanly without data loss, that rich guidance renders properly across the wizard UI contracts, that secrets remain strictly masked, and that package bundling/distribution remains uncompromised.
3. Deliver comprehensive developer and author guidance documentation detailing how collection authors should design, structure, and test rich variable help guidance in their own collections.

## Programming Language

- **Implementation language**: Python (contract test suites, collection fixture validation routines, packaging contract verification).

## User Stories

- As a **PyPost User**, I want to configure the Google Drive MCP server using step-by-step OAuth 2.0 instructions right inside the Variable Setup Wizard, so that I can successfully obtain and enter my access tokens without searching third-party documentation.
- As a **Collection Author**, I want an official reference collection and authoring guide demonstrating best practices for writing `help_text` guidance and OAuth setup instructions, so that I can easily create well-documented library collections for my own APIs.
- As a **System Integrator / Release Engineer**, I want automated contract tests ensuring that collections with rich markdown guidance deserialize accurately, load seamlessly into the UI wizard, and pass packaging integrity checks, so that regressions in schemas or bundling are caught before release.
- As a **Security Auditor**, I want sensitive credentials (such as OAuth bearer tokens) configured via reference collections to be consistently marked as `secret: true`, masked by default in the UI wizard, and properly segregated from non-sensitive configuration overrides.

## Definition of Done

This task is considered complete when:

1. `examples/collections/google_drive.json` is enriched with realistic, step-by-step `help_text` instructions for OAuth 2.0 variables (such as `google_drive_access_token`), walking users through Google Cloud Console setup (creating projects, enabling APIs, configuring consent screens, obtaining credentials, and retrieving access tokens).
2. Model and manifest schema validation verifies that `google_drive.json` and all reference collections parse cleanly through `CollectionVariable` and collection manifest schemas without schema degradation or data loss.
3. An automated contract test suite verifies that reference collections with rich `help_text` guidance load properly into `VariableSetupWizardDialog`, populate `VariableGuidanceCard` widgets, preserve secret masking defaults, and validate input types.
4. Packaging and distribution integrity tests (`tests/test_bundled_examples_packaging.py`) pass without regressions, ensuring all bundled reference examples are intact and distributed correctly.
5. Developer documentation in `doc/dev/` provides a comprehensive guide for collection authors on structuring rich variable guidance, formatting markdown/links, handling secrets, and writing contract tests.
6. Quality gates (`make check`, `make lint`, `make typecheck`, `make verify-ai-tasks`) pass cleanly with zero errors or regressions.

## Task Description

### Problem Statement

When connecting library collections that require external API authentication (such as Google Drive v3 REST API), users encounter variables like `google_drive_access_token` that have no inline instructions. Without step-by-step guidance on navigating provider consoles (e.g., Google Cloud Console), setting up OAuth 2.0 client IDs, choosing authorization scopes (`https://www.googleapis.com/auth/drive.readonly`, etc.), and generating bearer tokens, users experience significant onboarding friction.

Furthermore, because Layer 1, 2, and 3 introduced new schema fields and UI widgets, an end-to-end contract test suite is required to guarantee that real-world collections containing markdown `help_text` can be serialized, deserialized, loaded into the wizard, and displayed without errors.

### Scope

- **In Scope**:
  - Enhancing `examples/collections/google_drive.json` with step-by-step `help_text` guidance for OAuth 2.0 credentials (`google_drive_access_token`, client IDs, authorization scopes, Google Cloud Console setup steps).
  - Verifying model and manifest schema validation against `CollectionVariable` and collection manifest schemas without schema degradation or data loss.
  - Creating a contract test suite verifying serialization, deserialization, wizard contract loading, secret masking, and input validation for reference collections with rich guidance.
  - Verifying packaging compliance with `tests/test_bundled_examples_packaging.py`.
  - Authoring developer/author guidance documentation in `doc/dev/` for writing collections with rich variable guidance and OAuth help panels.
- **Out of Scope**:
  - Modifying the core `CollectionVariable` schema or validator implementation (completed in **PYPOST-1372**).
  - Modifying the core `VariableSetupWizardDialog` or `VariableGuidanceCard` widget implementations (completed in **PYPOST-1373**).
  - Modifying `McpServersDialog` / `_McpServerEditor` integration or overlay persistence (completed in **PYPOST-1374**).
  - Implementing automated OAuth token refresh or active token exchange flows at runtime (out of scope for static collection guidance).

### Functional Requirements

- **FR-1 Reference Collection Enhancement**:
  - Enhance `examples/collections/google_drive.json` with step-by-step `help_text` guidance for OAuth 2.0 credentials (`google_drive_access_token`, client IDs, authorization scopes, Google Cloud Console setup steps).
  - Guidance must be formatted using clean, readable Markdown with numbered steps, bullet points, scope declarations, and official console links.
  - Secret variables (such as access tokens) must remain explicitly flagged with `"secret": true`.

- **FR-2 Model & Manifest Schema Validation**:
  - Ensure reference collections strictly parse and validate against `CollectionVariable` and collection manifest schemas without schema degradation or data loss.
  - Round-trip serialization must preserve all variable metadata, including `help_text`, default values, descriptions, required flags, and secret flags.

- **FR-3 End-to-End Wizard Contract Compatibility**:
  - Contract verification ensuring reference collection variables with rich guidance properly populate `VariableSetupWizardDialog`.
  - Ensure guidance cards (`VariableGuidanceCard`) format guidance text correctly, allow toggling expansion, mask secrets with show/hide controls, and validate default and user inputs without exception.

- **FR-4 Bundled & Packaging Contract Compliance**:
  - Ensure enhanced collections maintain compatibility with package bundling tests (`tests/test_bundled_examples_packaging.py`).
  - Ensure changes do not regress packaging, distribution declarations in `pyproject.toml`, or example manifest coverage (`pypost-library.yaml`).

- **FR-5 Collection Authoring Guidance Documentation**:
  - Author comprehensive developer/author documentation explaining how to write collections with rich variable guidance and OAuth help panels.
  - Document conventions for markdown formatting, URL linking, secret identification, and validating collections using test suites.

### Non-Functional Requirements

- **NFR-1 Schema Stability & Backward Compatibility**:
  - All existing collections, manifests, and test fixtures must continue to validate and parse without breaking changes.
  - Collections with or without `help_text` must interoperate seamlessly across all layers.

- **NFR-2 Zero Secret Leakage**:
  - Sensitive tokens in reference collections must never default to real credentials or leak into log streams or unmasked display widgets.
  - Guidance text must clearly instruct users on secure handling of sensitive keys and tokens.

- **NFR-3 Packaging & Distribution Integrity**:
  - Bundled example files must remain fully declared in package metadata, ensuring that distribution wheels and source distributions package all reference files.

- **NFR-4 Performance & Usability**:
  - Loading and parsing reference collections into the wizard dialog must execute instantaneously (< 20ms) without blocking the UI thread.
  - Guidance text must render clearly with readable typography and proper word wrapping.

### Constraints and Assumptions

- The implementation language for contract tests and tooling is Python.
- Testing must adhere to the repository quality standard: all checks executed through `make check`, `make lint`, `make test`, `make typecheck`, and `make verify-ai-tasks`.
- Tests must include explicit test timeouts (`pytestmark = pytest.mark.timeout(...)`) complying with the `do-testing` standard.
- Reference collections use valid JSON syntax conforming to PyPost collection format specifications.

### Main Business Entities

| Entity | Description |
| --- | --- |
| **Reference Collection (`google_drive.json`)** | Curated official example collection showcasing Google Drive v3 REST API requests and variable definitions. |
| **OAuth 2.0 Setup Guidance** | Detailed, structured instructions guiding users through acquiring credentials from the identity provider (Google Cloud Console). |
| **CollectionVariable** | Core data model representing an individual variable, including its metadata, requirement status, secrecy, and `help_text`. |
| **VariableSetupWizardDialog** | Modal wizard UI facilitating variable review, input, and configuration before MCP server creation. |
| **VariableGuidanceCard** | Component widget displaying an individual variable's input field, secret toggle, and collapsible guidance instructions. |
| **Contract Test Suite** | Automated regression and contract tests verifying schema fidelity, UI wizard loading, secret masking, and package bundling. |
| **Authoring Documentation** | Developer documentation guiding collection authors on creating collections with rich guidance. |

## Q&A

- **Q: Why focus the reference guidance on Google Drive OAuth?**  
  **A:** Google Drive v3 API is one of the primary example collections bundled with PyPost. Configuring Google APIs involves standard OAuth 2.0 concepts (Google Cloud Console, project creation, OAuth consent screen, scopes, client IDs, and bearer tokens), making it the ideal realistic reference implementation for complex credential setup.
- **Q: Does this task modify the underlying `VariableSetupWizardDialog` widget code?**  
  **A:** No. `VariableSetupWizardDialog` was implemented in Layer 2 (PYPOST-1373) and integrated into the editor in Layer 3 (PYPOST-1374). This task (Layer 4) focuses on reference data fixtures (`google_drive.json`), authoring documentation, and end-to-end contract testing verifying that the entire stack functions seamlessly together.
- **Q: Will changes to `google_drive.json` break existing tests?**  
  **A:** The `help_text` field is an additive optional field on `CollectionVariable`. However, contract tests and packaging validation (`test_bundled_examples_packaging.py`) must be verified to ensure full schema and distribution compatibility.
