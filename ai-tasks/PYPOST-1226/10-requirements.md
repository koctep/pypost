# PYPOST-1226: [Libraries] Field-Level Validation Diagnostics for Manifest Form Editor

## Goals

When editing collection library manifests via the UI Library Manager or form editors, validation errors must provide exact field-level locations and JSON paths rather than generic string error blobs.

To enable seamless UI highlighting and form validation:
- `ManifestDiagnosticError` must provide structured properties: `field`, `json_path`, `line`, `column`, and a structured `field_errors` list.
- Manifest deserialization and validation in `pypost/core/library_manifest.py` must populate these structured fields from Pydantic `ValidationError`s, schema errors, or file parse errors.
- The UI Library Manager and callers must be able to programmatic inspect validation errors per field (e.g. `$.variables[0].name`, `$.collections`, `$.name`).

**Implementation language**: Python

## User Stories

- As a collection library author using the UI Form Editor, I want validation errors to highlight the exact input field (e.g., missing collection name, invalid variable type) so that I can immediately locate and correct mistakes.
- As a frontend UI presenter developer, I want `ManifestDiagnosticError` to expose structured `json_path` and `field_errors` attributes so that I can map errors directly to form controls without fragile string regex parsing.

## Definition of Done

- `ManifestDiagnosticError` has attributes: `field: Optional[str]`, `json_path: Optional[str]`, `line: Optional[int]`, `column: Optional[int]`, `field_errors: List[Dict[str, Any]]`.
- `deserialize_manifest_from_dict` and file parser functions extract field locations, JSON paths (`$.<field>`), and individual field error descriptors from validation failures.
- All existing `ManifestDiagnosticError` consumers continue to work seamlessly.
- Comprehensive automated unit tests verify field-level error extraction, JSON path formatting, and diagnostic attributes.
- All quality gates pass cleanly.

## Task Description

- **Problem Description**: `ManifestDiagnosticError` provided only top-level `code`, `message`, `path`, and generic `details`, making programmatic field-level error mapping in the UI form editor difficult.
- **Scope**: Extend `ManifestDiagnosticError` and manifest parser functions in `pypost/models/library_manifest.py` and `pypost/core/library_manifest.py` to extract and expose structured field-level diagnostic metadata and JSON paths.
- **Constraints & Assumptions**: Maintain backward compatibility for existing constructor arguments and exception string formatting.

## Non-Functional Requirements

- **Clarity**: Standardized JSON path formatting (e.g. `$.variables[0].name`, `$.collections`).
- **Robustness**: Safe extraction that never crashes even on malformed inputs or non-standard errors.
- **Compatibility**: Standard Exception behavior preserved.

## Main Entities

- **Manifest Diagnostic Error**: Exception carrying diagnostic metadata for parser and validation errors.
- **Field Diagnostic**: Structured representation of a single field validation error.
- **Manifest Parser**: Serialization and validation module.

## User Scenarios

1. **Form Validation with Invalid Variable**: An author creates a variable with an invalid type or empty name; `ManifestDiagnosticError` reports `field="variables[0].name"` and `json_path="$.variables[0].name"`.
2. **Missing Required Collections**: A manifest without collections raises a diagnostic with `field="collections"` and `json_path="$.collections"`.
3. **Multiple Field Errors**: A manifest with multiple invalid fields provides a populated `field_errors` list detailing each field, JSON path, and message.

## Q&A

| Question | Answer |
| --- | --- |
| What format is used for `json_path`? | Standard RFC 9535 JSONPath starting with `$.` (e.g. `$.variables[0].name`, `$.name`). |
| Are line/column numbers supported for syntax errors? | Yes, YAML/JSON parse errors extract line and column numbers into `line` and `column` attributes when available. |
