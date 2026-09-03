# PYPOST-1102 Technical Debt

## Retained follow-up

`MCPProxyServerImpl` still creates a new upstream connection and performs MCP
initialization for each forwarded operation. This preserves current dynamic
header behavior and avoids session ownership changes in this refactor, but adds
handshake latency under burst traffic. Connection pooling and header-aware
session reuse remain the separately tracked scope of PYPOST-1101.

## Not duplicated

No new technical-debt Jira issue was created. The refactor is local to the proxy
dispatch lifecycle, has no new dependency or setting, and does not alter the
existing protocol route or transport contract. The repository's unrelated
parser/template/SOLID/Qt baseline failures remain tracked by PYPOST-1261.

## Verification limitation

The delegated review service returned repeated 404 errors. The orchestrator
performed the required read-only review locally and recorded the limitation in
the roadmap. This is an execution-environment limitation, not a production
implementation debt item.
