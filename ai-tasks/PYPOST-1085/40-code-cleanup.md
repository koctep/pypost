# Code Cleanup: PYPOST-1085

## Overview

Audited all files modified in PYPOST-1085 for dead code, style, and attribute cleanup.

## Checks Performed

1. **Flake8 / Style**:
   - `make lint` passes cleanly (flake8, markdown lint, link check).
   - Clean whitespace and PEP 8 compliance.

2. **Removed Dead Code / Aliases**:
   - Removed `for_window` classmethod and `MainWindow` type-checking import from `pypost/ui/mcp_server_controller.py`.
   - Removed `self.mcp_manager` and `self.mcp_registry` attribute assignments from `pypost/ui/main_window.py`.
   - Updated call sites in `main.py` and `main_window.py` to route through `self.mcp_controller.manager` and `self.mcp_controller.registry`.

3. **Targeted Tests**:
   - `tests/test_main_window.py` and `tests/test_mcp_server_controller.py` pass cleanly.
