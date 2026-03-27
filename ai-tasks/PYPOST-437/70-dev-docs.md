# PYPOST-437: Developer Documentation Update

## Overview

Developer documentation was added for the hidden-variable feature introduced in PYPOST-437.
The doc explains behavior, architecture flow, persistence details, and operational notes.

## Updated Documentation

- Added: `doc/dev/hidden_variables.md`
- Updated index: `doc/dev/README.md` (added link to new page)

## Covered Topics

- Feature behavior and boundaries (display-only masking).
- Component-level architecture and signal/data propagation.
- Persistence approach (`model_dump(mode="json")` + atomic write).
- Troubleshooting paths and relevant test files.
- Security notes and linked Jira follow-up debts.

## Validation

- Line length check passed for updated markdown files.
