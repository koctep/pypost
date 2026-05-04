# PYPOST-459: Dev Documentation

## Changes Made

### Updated: `doc/dev/template_expression_functions.md`

Added a new **"Rendering Orchestration Stages"** section between the Architecture and
Troubleshooting sections. The section contains:

- A table of the 7 private helper methods extracted from `render_string()`, with their
  execution order and single-sentence responsibility description.
- A parity contract list documenting what was deliberately left unchanged: metric names,
  log formats, fallback semantics, token counting regex, and `FunctionExpressionResolver`
  contract.

This allows maintainers to quickly identify which helper method owns each stage, reducing
the need to read the full `render_string()` orchestrator to locate a behavior.

## No New Files

No new documentation files were created. PYPOST-459 is a refactoring of an existing
component (`TemplateService`), and the existing `template_expression_functions.md` already
covers the component's purpose, API, and observability. The new section extends that
document rather than fragmenting it.

## Validation

- [x] Section header added to correct location (between Architecture and Troubleshooting)
- [x] Table matches the 7 helpers in `pypost/core/template_service.py` in execution order
- [x] Parity contract matches the architecture document (`20-architecture.md`)
- [x] No new Markdown files added (existing doc extended)
