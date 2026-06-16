# PYPOST-791: Developer Documentation

## PYTEST_ARGS

Override pytest arguments on Makefile test targets:

```bash
make test PYTEST_ARGS="tests/test_mcp_server_manager.py -q"
make test PYTEST_ARGS="-k test_format_mcp_bind_error"
make test-cov PYTEST_ARGS="--cov=pypost.core.mcp_server tests/test_mcp_server_manager.py"
```

When set, `PYTEST_ARGS` replaces the default collection arguments for that target.
