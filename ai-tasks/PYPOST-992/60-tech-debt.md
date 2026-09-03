# PYPOST-992 Technical Debt

The test intentionally does not click controls that open menus or dialogs.
Offscreen Qt plugins can block on keyboard-grab behavior for those controls,
which would turn this protocol smoke into an environment-specific UI test.
The broader agent e2e suites cover tab creation and request flows separately.

No new Jira debt issue is needed: this is a documented test-boundary choice,
and the requested click/fill MCP contract is covered through a stable fixture
widget.
