# PYPOST-1226: [Libraries] Field-Level Validation Diagnostics for Manifest Form Editor

## Research

`ManifestDiagnosticError` (`pypost/models/library_manifest.py`) is the core exception raised during manifest parsing and validation.
Currently:
- `ManifestDiagnosticError` only captures `code`, `message`, `path`, and `details`.
- When Pydantic raises a `ValidationError` during `LibraryManifest(**data)`, detailed field path information in `exc.errors()` is flattened into a single string `message=f"Failed to validate library manifest: {exc}"`.
- Form editors in the UI require structured field-level keys (e.g. `field="variables[0].name"`, `json_path="$.variables[0].name"`) and a `field_errors` list to bind validation messages to individual form widgets.

## Implementation Plan

1. **Step 3 (Failing Repro):**
   - Write automated tests in `tests/test_manifest_field_diagnostics.py`:
     - Test `ManifestDiagnosticError` instantiation with `field`, `json_path`, `line`, `column`, `field_errors`.
     - Test `deserialize_manifest_from_dict` with invalid field (e.g. empty name, invalid variable type) raises `ManifestDiagnosticError` with populated `field`, `json_path`, and `field_errors`.
     - Test JSON/YAML syntax error extraction with `line` and `column`.
   - Confirm tests fail on unmodified code.

2. **Step 4 (Development):**
   - Update `ManifestDiagnosticError` in `pypost/models/library_manifest.py`:
     - Add `field`, `json_path`, `line`, `column`, and `field_errors` attributes.
     - Add `to_dict()` helper method.
   - Update `deserialize_manifest_from_dict` in `pypost/core/library_manifest.py` to parse Pydantic `ValidationError.errors()` into structured `field_errors`, `field`, and `json_path`.
   - Update YAML and JSON deserializers to extract `line` and `column` from syntax errors.
   - Run tests and verify all pass.

3. **Steps 5–8:**
   - Code cleanup, observability logging, tech debt analysis, and dev docs.

## Architecture

```
+-------------------------------------------------------------+
|                  ManifestDiagnosticError                    |
+-------------------------------------------------------------+
|  code: str                                                  |
|  message: str                                               |
|  path: Optional[Path]                                       |
|  field: Optional[str]              # e.g. "variables[0].name"
|  json_path: Optional[str]          # e.g. "$.variables[0].name"
|  line: Optional[int]               # e.g. 12                 |
|  column: Optional[int]             # e.g. 4                  |
|  field_errors: list[dict[str, Any]]# [{"field", "json_path",|
|                                    #   "message", "type"}]  |
|  details: dict[str, Any]                                    |
|                                                             |
|  to_dict() -> dict[str, Any]                                |
+-------------------------------------------------------------+
```

### Path & Location Conversion Rules

- Pydantic location tuple `("variables", 0, "name")` translates to:
  - `field`: `"variables[0].name"`
  - `json_path`: `"$.variables[0].name"`
- Root-level field `("name",)` translates to:
  - `field`: `"name"`
  - `json_path`: `"$.name"`
- `JSONDecodeError`: `line=exc.lineno`, `column=exc.colno`.
- `yaml.YAMLError` with `problem_mark`: `line=mark.line + 1`, `column=mark.column + 1`.

## Q&A

| Question | Answer |
| --- | --- |
| What happens when multiple validation errors occur simultaneously? | `field` and `json_path` reflect the first error; `field_errors` contains all errors. |
| Is `to_dict()` JSON-serializable? | Yes, returns primitive types and strings only. |
