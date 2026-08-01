# PYPOST-966: Code Cleanup

## Checklist

- [x] Extracted `_run_venv_python_snippet` — single subprocess wrapper for venv `-c` snippets
- [x] Extracted `_assert_post_install_sanity` — replaces inline pydantic subprocess in slow smoke
- [x] Declarative `POST_INSTALL_SANITY_SNIPPETS` — shared by slow smoke and contract guard
- [x] No trailing whitespace; line length ≤ 100 in changed files
- [x] Module docstrings unchanged where behavior is self-explanatory

## Validation

```bash
make test PYTEST_ARGS='tests/test_makefile_install_seed_contract.py -v'
```

Slow smoke not re-run locally (network-heavy); contract guard covers snippet policy.
