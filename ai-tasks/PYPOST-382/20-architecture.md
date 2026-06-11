# PYPOST-382: Architecture — pragmatic testability seams

## Current state (before)

| Component | Injectable today | Created internally | Test workaround |
| --- | --- | --- | --- |
| `RequestService` | metrics, template_service, history, alerts | `HTTPClient`, `MCPClientService` | Assign `svc.http_client = MagicMock()` in setUp |
| `HTTPClient` | metrics, template_service | `requests.Session` | Assign `client.session = MagicMock()` |
| `MainWindow` | metrics, template_service, config, alerts | storage, managers, presenters | Patch module-level classes in test |

## Target state (after)

| Component | New optional parameter | Behavior when omitted |
| --- | --- | --- |
| `RequestService` | `http_client` | Creates `HTTPClient(metrics=..., template_service=...)` |
| `RequestService` | `mcp_client` | Creates `MCPClientService()` |
| `HTTPClient` | `session` | Creates `requests.Session()` |

Production call sites (`RequestWorker`, `MCPServerImpl`) unchanged — defaults preserve behavior.

## MainWindow strategy

No structural refactor. Document:

1. Required constructor args (`metrics`, `template_service`).
2. Optional args (`config_manager`, `alert_manager`).
3. Patch-at-import pattern for presenters and layout helpers.
4. Link to [PYPOST-43](https://pypost.atlassian.net/browse/PYPOST-43) for decomposition.

## Documentation deliverable

New `doc/dev/testability.md`:

- Seam table per class.
- Copy-paste test examples.
- Test module index.
- Out-of-scope table with Jira links.

Cross-reference from `doc/dev/testing.md` and `doc/dev/gui_testing.md`.

## Test plan

| Test | Verifies |
| --- | --- |
| `TestRequestServiceInjection.test_injected_http_client_is_used` | HTTP client seam |
| `TestRequestServiceInjection.test_injected_mcp_client_is_used` | MCP client seam |
| `TestHTTPClientInjection.test_injected_session_is_used` | Session seam |
| `TestMainWindow.test_constructor_stores_injected_dependencies` | MainWindow DI retention |

## Acceptance mapping

| AC | Implementation |
| --- | --- |
| Seams without breaking callers | Optional params with defaults |
| Tests verify seams | Four new unit tests |
| Documentation | `doc/dev/testability.md` + cross-refs |
| Future work tracked | `60-tech-debt.md` links PYPOST-46, -379, -43 |
