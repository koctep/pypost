# PYPOST-953: Code Cleanup

## Lint / format

- [x] `flake8 --jobs=1 tests/test_mcp_server_impl.py` — clean on touched import + test
- [x] No production files edited

## Test hygiene

- [x] Module-level `pytestmark = pytest.mark.timeout(60)` covers new test
- [x] Test method on existing `TestMCPServerImpl` unittest class (consistent style)

## Scope

- Single test method + one import — no refactors beyond task need
