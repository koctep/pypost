"""Executable layer and persistence boundaries for architecture stage 5."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from pypost.core.storage import StorageManager
from pypost.models.models import Environment
from pypost.models.settings import AppSettings

pytestmark = pytest.mark.timeout(30)

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "pypost"
FORBIDDEN_CORE_PREFIXES = ("PySide6", "pypost.core.qt", "pypost.ui")
QUARANTINED_REPOSITORY_PREFIXES = ("pypost.adapters", "pypost.ports")


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
    return result


def _production_modules() -> list[Path]:
    return sorted(PACKAGE.rglob("*.py"))


def test_framework_neutral_core_does_not_import_qt_or_ui() -> None:
    violations: list[str] = []
    core = PACKAGE / "core"
    for path in core.rglob("*.py"):
        if (core / "qt") in path.parents:
            continue
        for imported in _imports(path):
            if imported.startswith(FORBIDDEN_CORE_PREFIXES):
                violations.append(f"{path.relative_to(ROOT)} -> {imported}")
    assert violations == []


def test_runtime_does_not_import_quarantined_repository_prototypes() -> None:
    violations: list[str] = []
    for path in _production_modules():
        if path.parts[-2] in {"adapters", "ports"}:
            continue
        for imported in _imports(path):
            if imported.startswith(QUARANTINED_REPOSITORY_PREFIXES):
                violations.append(f"{path.relative_to(ROOT)} -> {imported}")
    assert violations == []


def test_hidden_environment_values_never_reach_persisted_plaintext(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fernet = pytest.importorskip("cryptography.fernet")
    secret = "stage-five-secret-value"
    monkeypatch.setenv(
        "PYPOST_ENV_ENCRYPTION_KEY", fernet.Fernet.generate_key().decode("ascii")
    )
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_ENABLED", raising=False)
    storage = StorageManager(data_dir=tmp_path)
    storage.apply_encryption_settings(AppSettings(env_encryption_enabled=True))
    environment = Environment(
        name="contract",
        variables={"SECRET": secret, "VISIBLE": "public"},
        hidden_keys={"SECRET"},
    )

    storage.save_environments([environment])

    raw = storage.environments_file.read_text(encoding="utf-8")
    assert secret not in raw
    document = json.loads(raw)
    assert document[0]["variables"]["VISIBLE"] == "public"
    loaded = storage.load_environments()
    assert loaded[0].variables["SECRET"] == secret


def test_ui_has_no_infrastructure_fallback_constructors() -> None:
    forbidden = {
        "ConfigManager",
        "HistoryManager",
        "RequestManager",
        "StateManager",
        "StorageManager",
        "MCPServerManager",
        "QtMCPServerRegistry",
        "McpServerSettingsController",
    }
    violations: list[str] = []
    for path in (PACKAGE / "ui").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in forbidden
            ):
                violations.append(
                    f"{path.relative_to(ROOT)}:{node.lineno} calls {node.func.id}"
                )
    assert violations == []
