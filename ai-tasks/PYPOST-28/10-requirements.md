# Requirements: PYPOST-28 - MCP Testing Collection

## Goals
Create a set of test data (collection and environment) to verify the functionality of the MCP server. This will allow developers and users to quickly check if the integration with AI agents works.

## User Stories
- As a developer, I want to have a ready-made collection of requests that I can use to test the MCP server.
- As a developer, I want to have a pre-configured environment with variables for test requests.

## Acceptance Criteria
- [ ] **Collection**: Created `MCP_Test.json` collection containing:
    - GET request (e.g., `httpbin.org/get`).
    - POST request with JSON body (e.g., `httpbin.org/post`).
    - Request using variables.
    - Request with post-request script.
- [ ] **Environment**: Created `Test Env` environment containing variables used in the collection.
- [ ] **Configuration**: Requests in the collection have `expose_as_mcp=True`.

## Task Description
Create JSON files for the collection and environment manually or via PyPost interface and commit them to the repository.

### Technical Details
- **Path**: `collections/MCP_Test.json`, `environments.json`.
- **Content**: Valid JSON matching PyPost models.
