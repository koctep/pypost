# PYPOST-179: Script to generate MCP test collection fixtures

## Goals

The MCP test collection and environment under `examples/collections/` and `config/test/`
were created manually in PyPost UI and committed ([PYPOST-25](https://pypost.atlassian.net/browse/PYPOST-25)).
Contributors who change MCP test data need a repeatable way to regenerate those JSON files
without hand-editing or re-exporting from the GUI, so fixtures stay consistent with PyPost
models and CI expectations ([PYPOST-180](https://pypost.atlassian.net/browse/PYPOST-180)).

## User Stories

- As a **contributor**, I want a script that regenerates the MCP test collection and
  environment JSON from code so I do not rely on manual UI export.
- As a **maintainer**, I want CI or pre-commit checks to detect when committed fixtures drift
  from the canonical generator output.
- As a **test author**, I want fixture definitions in one place so PYPOST-180/181 loaders and
  integration tests stay aligned.

## Definition of Done

- [x] Programmatic builders define the MCP test collection and environment.
- [x] CLI script writes `examples/collections/mcp.json` and `config/test/environments.json`.
- [x] `--check` mode exits non-zero when committed files do not match generated models.
- [x] Automated tests cover builders and the `--check` CLI path.
- [x] Developer documentation describes how to regenerate and verify fixtures.
- [x] Full test suite passes.

## Task Description

Follow-up from [PYPOST-25](https://pypost.atlassian.net/browse/PYPOST-25) tech debt:
"Manual File Creation: Files were created via PyPost UI and then committed. No script for
generating test data."

## Q&A

- **Q:** Should the script replace existing committed files?
  **A:** Yes — running the script updates fixtures to match current models; `--check` verifies
  they are already in sync.
- **Q:** Does this add live MCP tests?
  **A:** No — that remains [PYPOST-181](https://pypost.atlassian.net/browse/PYPOST-181).
