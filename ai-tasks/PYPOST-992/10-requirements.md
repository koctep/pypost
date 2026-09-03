# PYPOST-992 Requirements

## Business reason

The existing agent-UI MCP sidecar test proves only that `list_tools` returns
the catalog. It does not prove that a real stdio MCP client can invoke the
actions against the sidecar-owned Qt session.

## Functional requirements

1. Start the packaged sidecar in a separate subprocess using its stdio MCP
   transport and an offscreen Qt environment.
2. Initialize a real MCP `ClientSession` and invoke `ui_fill` through
   `call_tool` against the active request URL field.
3. Invoke `ui_click` through `call_tool` against a stable, non-networking
   fixture widget.
4. Assert both calls return the established JSON success envelope.
5. Keep existing list-tools, packaging, HTTP, seed, and attach coverage intact.

## Non-functional requirements

- The subprocess test must have a bounded timeout and cleanly close the stdio
  context so the sidecar cannot outlive the test.
- Use only deterministic offscreen widgets; do not depend on an external HTTP
  service or a modal/menu interaction.
- Keep the test behind the existing `agent_e2e` marker for the fast suite's
  subprocess policy.

## Out of scope

- Additional UI action primitives, protocol changes, or production behavior.
- Full request execution or response verification; those are covered by the
  broader agent e2e suites.

## Acceptance criteria

- A process-level stdio test invokes both click and fill via MCP `call_tool`.
- The test passes through the repository Make test target.
- Existing stdio sidecar behavior remains green.
