# PYPOST-1372: Developer Documentation Decisions

Step 8 artifact for [PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372) (WIZARD-1: Extend CollectionVariable schema with help_text guidance attribute under parent epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)).

---

## Documentation Scope & Target Selection

### Developer Documentation Locations

The guidance attribute `help_text` on `CollectionVariable` (`pypost/models/collection_variable.py`) impacts the collection schema specification, serialization subsystems, and library integration documentation.

The developer documentation updates were applied directly to:
1. **`doc/dev/collection_format_v2.md`** (Primary specification):
   - Updated the architecture Mermaid diagram (`CV[CollectionVariable]`) to include `help_text: Optional[str]`.
   - Updated the `CollectionVariable` attribute table to include `help_text` (`str | None`, default `None`, description and Jira reference).
   - Added a dedicated subsection: **"Guidance Attribute (`help_text`) Validation & Normalization"** detailing validation rules, sanitization behavior, backward compatibility, and example JSON/YAML snippets.
2. **`doc/dev/mcp_server_registry.md`** (Cross-reference):
   - Verified cross-reference in Section "Planned Variable Setup Wizard (PYPOST-1284)" pointing to `CollectionVariable.help_text` schema extension ([PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372)) and downstream UI wizard stories ([PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373), [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374), [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375)).

---

## Schema & Validation Specification Documented

### Attribute Definition

| Attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `help_text` | `Optional[str]` | `None` | Optional markdown guidance and instructions explaining credential acquisition or variable configuration. |

### Validation Rules

1. **Strict String Type Enforcement**:
   - `help_text` strictly accepts `str` or `None`.
   - Non-string scalar and complex types (e.g., `int`, `float`, `bool`, `list`, `dict`) are rejected during pre-validation (`@field_validator("help_text", mode="before")`), raising a `ValueError` (which Pydantic encapsulates as `ValidationError`).
2. **Boundary Whitespace Stripping**:
   - Leading and trailing boundary whitespace is automatically trimmed (`value.strip()`).
   - Internal indentation, newlines, and code block formatting within multiline markdown strings are preserved intact.
3. **Empty / Blank Normalization**:
   - Blank strings (`""`) and whitespace-only strings (e.g., `"   \n\t  "`) are normalized cleanly to `None`.
   - Serialized representations do not persist redundant empty strings.
4. **Backward Compatibility**:
   - Omission of `help_text` defaults safely to `None`.
   - Legacy collection schemas, JSON/YAML fixtures, and manifest definitions continue to deserialize without error or behavioral change.

---

## Example Snippets Documented

### JSON Snippet

```json
{
  "name": "google_oauth_token",
  "type": "string",
  "default": null,
  "description": "Google Cloud OAuth Bearer Token",
  "help_text": "### How to obtain a token:\n1. Open Google Cloud Console: https://console.cloud.google.com\n2. Navigate to APIs & Services > Credentials.\n3. Create OAuth 2.0 Client ID or generate a temporary access token via `gcloud auth print-access-token`.",
  "required": true,
  "secret": true
}
```

### YAML Snippet

```yaml
variables:
  - name: google_oauth_token
    type: string
    default: null
    description: Google Cloud OAuth Bearer Token
    help_text: |
      ### How to obtain a token:
      1. Open Google Cloud Console: https://console.cloud.google.com
      2. Navigate to APIs & Services > Credentials.
      3. Create OAuth 2.0 Client ID or generate a temporary access token via `gcloud auth print-access-token`.
    required: true
    secret: true
```

---

## Downstream Integration Notes

- **PYPOST-1373 (`VariableSetupWizardDialog` & `VariableGuidanceCard`)**:
  - The wizard UI inspects `variable.help_text`. When present (`is not None`), it renders an expandable markdown card with clickable links. When `None`, the guidance card is collapsed or omitted.
- **PYPOST-1374 (`McpServersDialog` & `_McpServerEditor`)**:
  - MCP server editor consumes manifest variables carrying `help_text` and launches the setup wizard during server configuration.
- **PYPOST-1375 (`examples/collections/google_drive.json`)**:
  - Adds real-world OAuth token acquisition guidance using `help_text` in reference fixtures.
