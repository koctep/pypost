# Step 3 Failing Repro: Seed/Collection Injection for Sidecar Session

**Task**: [PYPOST-993](https://pypost.atlassian.net/browse/PYPOST-993)  
**Step**: STEP 3 (Failing Repro Test)  
**Target Test File**: `tests/test_agent_ui_actions_mcp_seed.py`  
**Base Commit**: `5b1fba54c36ddd3f0607d1097f55ede0977e64b7`

---

## 1. Overview & Objective

Per [20-architecture.md](file:///home/src/ai-tasks/PYPOST-993/20-architecture.md), Step 3 provides automated failing repro tests that assert the target acceptance criteria *prior* to implementing production code in `pypost/`.

The tests cover:
1. **Seed Path Resolution**: `resolve_seed_path` precedence (CLI argument over environment variable `PYPOST_AGENT_SEED_PATH`).
2. **CLI Argument Parsing**: Sidecar entry point (`pypost.agent.ui_actions_mcp.main`) parsing `--seed` and alias `--seed-file`, and rejecting invalid combinations with `--attach`.
3. **Session Seed Injection**: `AgentAppSession(seed_path=..., offscreen=True)` pre-compose injection resulting in loaded collections in the UI tree and UI snapshot once `is_ui_ready` is reached.

---

## 2. Test Execution Command

Executed strictly via Make per repository guidelines (`AGENTS.md`):

```bash
make test PYTEST_ARGS="tests/test_agent_ui_actions_mcp_seed.py"
```

---

## 3. Repro Test Results

### Summary

```text
tests/test_agent_ui_actions_mcp_seed.py::test_resolve_seed_path_cli_env_precedence FAILED [0ms] [ 20%]
tests/test_agent_ui_actions_mcp_seed.py::test_ui_actions_mcp_cli_seed_argument_parsing FAILED [1ms] [ 40%]
tests/test_agent_ui_actions_mcp_seed.py::test_ui_actions_mcp_cli_seed_file_alias FAILED [1ms] [ 60%]
tests/test_agent_ui_actions_mcp_seed.py::test_ui_actions_mcp_cli_attach_with_seed_rejected FAILED [3ms] [ 80%]
tests/test_agent_ui_actions_mcp_seed.py::test_agent_app_session_with_seed_loads_collection_into_ui FAILED [1ms] [100%]

============================== 5 failed in 0.14s ===============================
```

### Detailed Failure Traces

#### 1. `test_resolve_seed_path_cli_env_precedence`
- **Failure Mode**: Missing module `pypost.agent.seed_loader`.
- **Traceback**:
  ```text
  tests/test_agent_ui_actions_mcp_seed.py:53: in test_resolve_seed_path_cli_env_precedence
      from pypost.agent.seed_loader import DEFAULT_SEED_ENV_VAR, resolve_seed_path
  E   ModuleNotFoundError: No module named 'pypost.agent.seed_loader'
  ```

#### 2. `test_ui_actions_mcp_cli_seed_argument_parsing`
- **Failure Mode**: CLI argument `--seed` not recognized by `argparse`.
- **Traceback**:
  ```text
  tests/test_agent_ui_actions_mcp_seed.py:84: in test_ui_actions_mcp_cli_seed_argument_parsing
      main(["--seed", str(seed_file)])
  pypost/agent/ui_actions_mcp.py:288: in main
      parsed = parser.parse_args(argv)
  /usr/lib/python3.13/argparse.py:1916: in parse_args
      self.error(msg)
  /usr/lib/python3.13/argparse.py:2672: in error
      self.exit(2, _('%(prog)s: error: %(message)s\n') % args)
  E   SystemExit: 2
  Captured stderr:
  -c: error: unrecognized arguments: --seed /tmp/pytest-of-il/pytest-2/test_ui_actions_mcp_cli_seed_a0/seed.json
  ```

#### 3. `test_ui_actions_mcp_cli_seed_file_alias`
- **Failure Mode**: CLI argument `--seed-file` not recognized by `argparse`.
- **Traceback**:
  ```text
  tests/test_agent_ui_actions_mcp_seed.py:99: in test_ui_actions_mcp_cli_seed_file_alias
      main(["--seed-file", str(seed_file)])
  pypost/agent/ui_actions_mcp.py:288: in main
      parsed = parser.parse_args(argv)
  E   SystemExit: 2
  Captured stderr:
  -c: error: unrecognized arguments: --seed-file /tmp/pytest-of-il/pytest-2/test_ui_actions_mcp_cli_seed_f0/seed.json
  ```

#### 4. `test_ui_actions_mcp_cli_attach_with_seed_rejected`
- **Failure Mode**: Combining `--attach` with `--seed` fails at `argparse` rather than sidecar business validation (expected exit code 1, observed 2).
- **Traceback**:
  ```text
  tests/test_agent_ui_actions_mcp_seed.py:115: in test_ui_actions_mcp_cli_attach_with_seed_rejected
      assert exc_info.value.code == 1
  E   assert 2 == 1
  ```

#### 5. `test_agent_app_session_with_seed_loads_collection_into_ui`
- **Failure Mode**: `AgentAppSession.__init__` lacks `seed_path` keyword parameter.
- **Traceback**:
  ```text
  tests/test_agent_ui_actions_mcp_seed.py:138: in test_agent_app_session_with_seed_loads_collection_into_ui
      session = AgentAppSession(seed_path=seed_file, offscreen=True, ready_timeout=30.0)
  E   TypeError: AgentAppSession.__init__() got an unexpected keyword argument 'seed_path'
  ```

---

## 4. Conformance & Integrity Verification

1. **Failure Validity**: All failures directly correspond to unwritten features (missing module, missing arguments, missing parameter). No unexpected environment or fixture issues occurred.
2. **Production Code Integrity**: Zero files modified in `pypost/`.
3. **Timeout Rules**: Complies with `do-testing` and `lsr-python`:
   - Module-level `pytestmark = [pytest.mark.timeout(60), pytest.mark.agent_e2e]`.
   - Function-level explicit `@pytest.mark.timeout(60)` annotations.

---

## 5. Downstream Handoff (Step 4: Development)

The failing tests will transition from RED to GREEN once Step 4 implements:
1. `pypost/agent/seed_loader.py` with `resolve_seed_path` and `inject_seed`.
2. `AgentAppSession.__init__(seed_path=...)` and pre-compose `inject_seed()` in `lifecycle.py`.
3. CLI argument parsing for `--seed` / `--seed-file` and rejection of `--attach` with seed in `ui_actions_mcp.py`.
