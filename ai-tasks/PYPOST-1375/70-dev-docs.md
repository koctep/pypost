# PYPOST-1375: Developer Documentation Decisions

Developer documentation decisions and records for [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375) (Layer 4 / WIZARD-4: Reference Collections, Contract Test Suite, and Collection Author Guidance under parent epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)).

## Documentation Updates

1. **Created Documentation**:
   - [`doc/dev/collection_variable_guidance.md`](../../doc/dev/collection_variable_guidance.md)

2. **Updated Documentation**:
   - [`doc/dev/README.md`](../../doc/dev/README.md) (added entry under "Collections and environments")
   - [`doc/dev/google_drive_collection_example.md`](../../doc/dev/google_drive_collection_example.md) (cross-referenced setup guidance and authoring doc)

3. **Context & Motivation**:
   - Epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284) introduced a guided variable setup wizard with rich help guidance when adding MCP servers from a library collection.
   - Preceding stories established:
     - [PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372) (Layer 1): Schema extension (`help_text` attribute on `CollectionVariable`).
     - [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373) (Layer 2): UI components (`VariableGuidanceCard` and `VariableSetupWizardDialog`).
     - [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374) (Layer 3): Dialog integration in `_McpServerEditor` with draft overlay synchronization.
   - Story [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375) (Layer 4) delivers the canonical reference collection (`examples/collections/google_drive.json`), the contract test suite (`tests/test_reference_collection_variable_guidance_contract.py`), and collection author guidance documentation.
   - Creating `doc/dev/collection_variable_guidance.md` establishes a comprehensive developer reference for future collection authors, explaining how to write rich, actionable setup instructions while adhering to strict security rules (zero credential leakage).

4. **Key Topics Documented**:
   - **Schema & Additive Evolution**:
     - `CollectionVariable.help_text` specification, whitespace normalization, and backward compatibility with collections lacking `help_text`.
   - **Authoring Standards**:
     - Clear distinction between concise `description` (tooltips/summaries) and actionable `help_text` (step-by-step guidance).
     - Markdown standards: Level-3 headings (`###`), numbered steps, code backticks, and bullet points.
     - External link handling: using full protocol schemes (`https://`) rendered via Qt RichText with `openExternalLinks=True` and `TextBrowserInteraction`.
   - **Security & Secret Masking**:
     - Mandatory zero credential leakage rule (never hardcoding real credentials in fixtures or manifests).
     - Echo mode masking (`QLineEdit.EchoMode.Password`) and eye toggle controls in `VariableGuidanceCard`.
     - Partitioning of sensitive inputs into `LocalLibraryOverlay.secrets` vs configuration into `overrides`.
   - **UI Presentation Architecture**:
     - Component lifecycle across `CollectionVariable` -> `VariableGuidanceCard` -> `_GuidanceContainer` -> `VariableSetupWizardDialog` -> `LocalLibraryOverlay`.
     - Collapsed-by-default behavior preserving compact dialog real estate.
   - **Contract Testing & Quality Standards**:
     - 5-part contract pattern in `tests/test_reference_collection_variable_guidance_contract.py` (fixture validation, model deserialization fidelity, card initialization/interactivity, wizard partitioning, backward compatibility).
     - Bundled packaging integrity verification in `tests/test_bundled_examples_packaging.py`.
   - **Reference Fixture Showcase**:
     - Showcasing `examples/collections/google_drive.json` as the authoritative reference implementation for OAuth 2.0 access token configuration.

5. **Traceability**:
   - Parent Epic: [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)
   - Architectural Decomposition: [PYPOST-1368](https://pypost.atlassian.net/browse/PYPOST-1368)
   - Layer 1 (Schema): [PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372)
   - Layer 2 (UI Components): [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373)
   - Layer 3 (Editor Integration): [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374)
   - Layer 4 (Reference Collections & Author Guidance): [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375)
