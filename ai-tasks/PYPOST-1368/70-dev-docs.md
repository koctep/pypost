# PYPOST-1368: Developer Documentation (Step 8)

DECOMPOSE / planning task — children under
[PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284) already exist.
This step records the `doc/dev` decision for the decompose story only.

## Decision

**Minimal product-doc change only** — a ticket pointer, not full wizard docs.

| Change | Rationale |
| --- | --- |
| Update `doc/dev/mcp_server_registry.md` under § Library-backed local servers | Existing library variable configuration section now points maintainers to epic PYPOST-1284 and child stories PYPOST-1372..1375 |
| Do **not** document `help_text` schema details or migration | Owned by [PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372) |
| Do **not** document `VariableSetupWizardDialog` or `VariableGuidanceCard` | Owned by [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373) |
| Do **not** document editor integration, launch actions, or overlay persistence | Owned by [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374) |
| Do **not** document reference OAuth fixtures or contract tests | Owned by [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375) |
| No new `doc/dev/<feature>.md` | No product feature code shipped on PYPOST-1368 |
| No `doc/user/` | Out of scope for this decompose story |

## What Was Updated

In `doc/dev/mcp_server_registry.md` under § Library-backed local servers, added a concise pointer section:
`#### Planned Variable Setup Wizard (PYPOST-1284)` referencing:
- Schema extension: [PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372) (`CollectionVariable.help_text`)
- UI components: [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373) (`VariableGuidanceCard`, `VariableSetupWizardDialog`)
- Editor integration: [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374) (wizard launch, overlay persistence in `_McpServerEditor`)
- Reference guidance & tests: [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375) (reference fixtures, contract tests)

It explicitly states that full wizard documentation, UI interaction, guidance card component architecture, and schema attribute prose belong to child stories PYPOST-1372..1375 when they run their own Step 8.

## Skill Sections (Template Mapping)

For this ticket type, the td-70 template (Overview / Architecture / Usage / Configuration / Troubleshooting) is **satisfied by the existing documentation** in `doc/dev/mcp_server_registry.md` and `doc/dev/library_manifest_and_overlay.md`, augmented with the planned wizard pointer note. Full feature sections land when the child implementation stories run their own Step 8.

## Completion Criteria (This Step)

- [x] `doc/dev` touched only as needed (pointer in `doc/dev/mcp_server_registry.md`; no wizard implementation prose)
- [x] Decision recorded in roadmap Step 8 notes and this artifact (`ai-tasks/PYPOST-1368/70-dev-docs.md`)
- [ ] Gate: leave Step 8 `[/]` until review / acceptance
