# PYPOST-1372: [PYPOST-1284] Extend CollectionVariable schema with help_text guidance attribute

## Goals

Epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284) introduces a guided variable setup wizard with rich help guidance when adding or configuring MCP servers from a library collection. Currently, configuring required environment variables in PyPost is error-prone because complex credentials (such as Google Cloud OAuth Bearer tokens, GitHub personal access tokens, or Jira API tokens) require multi-step acquisition instructions that cannot be adequately expressed using the existing short `description` field.

The existing `CollectionVariable` data model and schema serialization in `pypost/models/collection_variable.py` defines `name`, `type`, `default`, `description`, `required`, and `secret`, but lacks a dedicated guidance attribute.

This task ([PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372), WIZARD-1) represents Layer 1 (Data Model & Schema Extension) of the epic decomposition defined in [PYPOST-1368](https://pypost.atlassian.net/browse/PYPOST-1368).

**Business Goal:**
Provide collection authors and library curators with the ability to define detailed, human-readable setup guidance (including markdown instructions, code snippets, and external links) for collection variables, while maintaining strict backward compatibility with existing collections, predictable schema serialization, and type safety across all library tools and downstream wizard UI components.

## Programming Language

- **Implementation language**: Python (Pydantic model, validation logic, serialization and deserialization routines, unit tests).

## User Stories

- As a **Collection Author / Library Maintainer**, I want to provide rich setup guidance (`help_text`) for variables in my collection definitions, so that users know the exact steps and permissions required to obtain sensitive tokens or configure complex parameters.
- As a **PyPost User**, I want collection variables to carry detailed instructions explaining how to obtain credentials, so that I do not have to leave the application to search external documentation.
- As a **Downstream UI Component Developer (WIZARD-2 / PYPOST-1373)**, I want the `CollectionVariable` model to reliably expose an optional string attribute `help_text` with clean default values and robust serialization, so that the variable setup wizard can render expandable guidance panels without handling malformed data.
- As a **System Integrator**, I want existing collection files that omit `help_text` to continue loading and validating identically, so that backward compatibility is preserved without regressions across existing collections or test fixtures.

## Definition of Done

This task is considered complete when:

1. The `CollectionVariable` model in `pypost/models/collection_variable.py` is extended with an optional `help_text` guidance attribute (`Optional[str] = None` or empty string equivalent consistent with model norms).
2. Default value handling ensures that variables instantiated or parsed without `help_text` default safely to `None` (or empty string) without raising validation errors.
3. String type validation is enforced for `help_text`: non-string values (unless explicitly `None`) are rejected with clear validation errors.
4. Input sanitization handles leading/trailing whitespace appropriately, normalizing empty or whitespace-only inputs consistently.
5. Serialization via `model_dump()`, `.dict()`, and standard dictionary export retains `help_text` faithfully, supporting round-trip serialization and deserialization.
6. Full backward compatibility is verified: legacy collection schemas, test fixtures, and manifest definitions that omit `help_text` parse without error and retain existing behavior.
7. Unit tests verify model initialization, default values, string validation, whitespace stripping, serialization fidelity, and backward compatibility.
8. Quality gates (`make check`, `make lint`, `make verify-ai-tasks`) pass cleanly.

## Task Description

### Problem Statement

In self-contained collection libraries and MCP server integrations:
- `CollectionVariable` only provides a brief `description` string (e.g. `"Google Cloud Bearer Token"`).
- Multi-step instructions (e.g., navigating to Google Cloud Console, enabling Drive API, creating OAuth 2.0 Client IDs, configuring scopes, and exchanging authorization codes) are too verbose for tooltip-style descriptions.
- Downstream wizard interfaces (such as `VariableSetupWizardDialog` planned in PYPOST-1373) require a structured field to store and render rich markdown guidance without overloading the short variable summary.

### Scope

- **In Scope**:
  - Updating `CollectionVariable` schema in `pypost/models/collection_variable.py`.
  - Adding `help_text: Optional[str] = None` (or string field with safe default).
  - Validation: ensure `help_text` is string or None; handle whitespace trimming / normalization.
  - Serialization: verify serialization via `model_dump()` / `.dict()` preserves `help_text` correctly.
  - Backward compatibility: ensure existing collections without `help_text` continue to deserialize without error.
  - Unit tests covering model validation, default assignment, round-trip serialization, and edge cases (e.g. whitespace-only strings, None values, non-string types).

- **Out of Scope**:
  - UI components, dialogs, expandable cards, or secret masking toggles (deferred to **PYPOST-1373** / WIZARD-2).
  - Integration with `McpServersDialog` or overlay persistence (deferred to **PYPOST-1374** / WIZARD-3).
  - Authoring reference fixture content in `examples/collections/google_drive.json` (deferred to **PYPOST-1375** / WIZARD-4).

### Functional Requirements

- **FR-1 Field Addition**: `CollectionVariable` must include a field `help_text: Optional[str] = None` (or `str = ""`, defaulting safely when omitted).
- **FR-2 Type Validation**: If provided, `help_text` must be a valid string. Non-string inputs (e.g., integers, lists, dicts) must raise a `ValidationError` / `ValueError`.
- **FR-3 Whitespace Handling**: Whitespace in `help_text` must be stripped or normalized so that whitespace-only strings are treated cleanly (e.g. converted to `None` or empty string, or stripped of boundary whitespace).
- **FR-4 Backward Compatibility**: Omission of `help_text` in input payloads, dictionary representations, or JSON/YAML collection files must not cause validation failures; legacy payloads must load with `help_text` defaulting safely.
- **FR-5 Serialization Stability**: Serializing a `CollectionVariable` to dictionary (`model_dump()`, `dict()`) or JSON/YAML must include `help_text` when set, and preserve `None` or omitted/empty states consistently across round-trips.

### Non-Functional Requirements

- **NFR-1 Backward Compatibility**: Zero regression on existing collection files, example collections, or test suites. All existing test cases in `tests/test_collection_serializer.py` and across the repository must pass without modification.
- **NFR-2 Performance**: Negligible overhead during model instantiation and validation.
- **NFR-3 Code Quality & Standards**: Conform strictly to PEP 8, mypy typing standards, and project linting rules checked via `make lint`.

### Constraints and Assumptions

- The project uses Pydantic V2 (`BaseModel`, `Field`, `ConfigDict`).
- `CollectionVariable` configuration currently uses `ConfigDict(populate_by_name=True)`.
- Existing variable attributes are: `name: str`, `type: str = "string"`, `default: Optional[Any] = Field(default=None, alias="default_value")`, `description: str = ""`, `required: bool = False`, `secret: bool = False`.

### Main Business Entities

| Entity | Description |
| --- | --- |
| **CollectionVariable** | Pydantic model representing a single declared configuration variable in an API collection or library manifest. |
| **help_text** | Optional multi-line string containing rich text / Markdown setup guidance and instructions for acquiring the variable value. |
| **description** | Short single-line summary of the variable's purpose. |
| **Variable Setup Wizard** | Downstream UI component (PYPOST-1373) that displays `help_text` in an expandable guidance card. |

## Q&A

- **Q: Why add `help_text` instead of reusing `description`?**  
  **A:** `description` is intended for compact tooltips and table column summaries (e.g., "OAuth access token"). Rich guidance requires multi-paragraph instructions, markdown formatting, bullet points, and URLs. Overloading `description` would degrade existing compact UI views.
- **Q: What should the default value of `help_text` be?**  
  **A:** `None` (or empty string `""` depending on architectural choice), ensuring that collections created without help text do not fail schema validation and serialize cleanly.
- **Q: Does this task modify UI dialogs or example collections?**  
  **A:** No. UI dialog implementation is scoped to PYPOST-1373, and sample collection enrichment is scoped to PYPOST-1375. PYPOST-1372 is strictly focused on the data model, validation, serialization, and unit tests.
