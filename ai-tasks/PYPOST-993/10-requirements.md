# PYPOST-993: Seed/collection injection for sidecar session

## Goals

The agent-UI MCP sidecar introduced in [PYPOST-952](https://pypost.atlassian.net/browse/PYPOST-952)
spawns an application session to drive UI widgets out-of-process. However, by default the sidecar
launches with empty application data, presenting an empty UI state.

To enable realistic automated evaluation, scenario reproduction, and workflow execution, AI agents
and test automation suites need the ability to launch the agent-UI MCP sidecar pre-loaded with
relevant collections, requests, or environment fixtures.

Business value:
- Enables AI agents to interact with meaningful, realistic UI fixtures rather than a blank canvas.
- Unlocks robust automated integration testing for UI-action workflows by providing predictable test fixtures.
- Eliminates manual setup steps required to seed collections before launching automated agent sessions.

Source: `ai-tasks/PYPOST-952/60-tech-debt.md` follow-up item 4 (TD-4).

## Programming Language

Python (`lsr-python`); developer documentation in English Markdown (`lsr-markdown`).

## User Stories

- As an **AI Agent Developer**, I want to spawn the agent-UI MCP sidecar pointing to an existing
  collection or seed file/directory, so that my agent can immediately interact with known requests
  and collection trees without having to create them manually via UI clicks.
- As an **Automation QA Engineer**, I want to pass seed paths via CLI flags or environment variables
  in CI workflows, so that end-to-end tests can reliably assert UI behavior against predetermined request data.
- As a **Maintainer**, I want seed injection to be completely optional and backwards-compatible, so that
  existing invocations and default unseeded sessions continue functioning without disruption.

## Definition of Done

- CLI argument (e.g. `--seed` / `--seed-file`) supported by the agent-UI MCP sidecar entry point.
- Environment variable (e.g. `PYPOST_AGENT_SEED_PATH`) supported as a configuration mechanism for seed injection.
- Precedence defined clearly between CLI argument, environment variable, and unseeded default.
- Sidecar session correctly loads the provided seed collection data on startup so widgets reflect seeded items upon becoming ready.
- Backward compatibility preserved: omitting seed arguments or environment variables defaults to the standard unseeded session.
- Graceful error handling for missing, unreadable, or invalid seed paths with clear diagnostics.
- At least one integration / end-to-end test verifying that a sidecar session launched with a seed displays the expected seeded data.
- Developer documentation updated under `doc/dev/` describing the seed configuration mechanisms and usage examples.

## Task Description

### Problem

When external agents spawn the out-of-process `pypost-agent-ui-mcp` sidecar, the underlying
session boots into a blank workspace. Driving UI actions (such as selecting collection items or
triggering requests) requires existing data. Without seed injection, agents must either perform
complex prerequisite UI steps to build requests from scratch or remain limited to empty-state interactions.

### In Scope

- CLI options on the agent-UI MCP entry point allowing specification of a seed data path.
- Environment variable support enabling seed path configuration without CLI modification.
- Startup initialization logic ensuring the sidecar session populates its workspace from the specified seed before signaling readiness.
- Validating that unseeded sidecar startup remains unmodified.
- Error handling when a specified seed path cannot be found or loaded.
- Automated integration test coverage verifying seed injection into the sidecar.
- Developer documentation describing how to configure and run the seeded sidecar.

### Out of Scope / Non-Goals

- Modifying the product `MCPServerImpl` HTTP request tools (hard separation preserved).
- Introducing new UI action tools beyond the existing `ui_click`, `ui_fill`, `ui_select`, and `ui_send_key`.
- Remote downloading or network fetching of seed files from external URLs.
- Creating a graphical seed import dialog inside the PyPost desktop application.
- Altering the file format or schema of PyPost collections and environments.

## Functional Requirements

- **FR1: CLI Seed Flag**: The agent-UI MCP executable must accept a CLI parameter to specify the path to seed data.
- **FR2: Environment Variable Configuration**: The agent-UI MCP executable must recognize an environment variable designating the seed data path when no CLI argument is provided.
- **FR3: Seed Loading on Startup**: When a valid seed path is configured, the launched sidecar application session must load the collection/environment data so that seeded entities exist in the workspace once the UI is ready.
- **FR4: Default Unseeded Mode**: If neither the CLI argument nor the environment variable is supplied, the sidecar must start up cleanly in the standard unseeded mode.
- **FR5: Error Reporting for Invalid Seeds**: If a specified seed path does not exist or cannot be loaded, the process must report an informative error and exit cleanly or abort initialization rather than silently proceeding with an empty state.

## Non-Functional Requirements

- **Backward Compatibility**: Existing scripts, tests, and Makefile targets invoking `pypost-agent-ui-mcp` without seed parameters must continue to operate without behavioral change.
- **Reliability & Determinism**: Seed loading must complete reliably before the sidecar begins processing incoming MCP tool requests.
- **Testability**: The functionality must be verifiable via automated tests executed in offscreen headless environments.
- **Observability**: Informative log messages must indicate whether a seed path was detected, loaded, or omitted during sidecar startup.

## Constraints and Assumptions

- The solution applies specifically to the agent-UI MCP sidecar (`pypost-agent-ui-mcp`).
- The sidecar runs in an environment where filesystem access to the seed path is available.
- Seed data format complies with existing PyPost collection/storage formats.
- Implementation details (architecture, exact classes, internal helpers) are strictly deferred to subsequent workflow steps.

## Main Entities and Interactions

| Entity | Role in Business Domain |
| --- | --- |
| **Sidecar Session** | The running agent-UI MCP instance managing the application lifecycle and MCP transport. |
| **Seed Specification** | The path or reference to collection/workspace fixtures provided via CLI or environment. |
| **Workspace Store** | The data store within the application session holding active collections and environments. |
| **External Agent / Test Runner** | The client or test runner that configures the seed and interacts with UI tools. |

## Q&A

- **Q**: What types of seed paths should be supported (e.g. pre-built storage directory vs single collection file vs built-in fixture identifier)?
  - **A**: The primary requirement is supporting a path to seed data (e.g. a seed file or directory as used by the storage manager/fixture builders). Specific path handling and formats will be resolved in Step 2 (Architecture).
- **Q**: What is the precedence if both CLI argument and environment variable are provided?
  - **A**: Standard CLI convention applies: the explicit CLI argument takes precedence over the environment variable.
- **Q**: Does this change affect product MCP (`MCPServerImpl`)?
  - **A**: No. The product MCP server remains strictly separate from the agent-UI MCP sidecar.
- **Q**: Should seed injection be mandatory?
  - **A**: No. It is entirely optional; omission results in the default empty session.
