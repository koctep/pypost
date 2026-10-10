"""Offline wheel checks and the bounded real Make packaging verification."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.check_package_data import inspect_wheel, main
from tests.makefile_test_helpers import REPO_ROOT, _materialize_slow_smoke_workspace, _run_make

pytestmark = pytest.mark.timeout(30)


def _canonical_sources(root: Path) -> dict[str, bytes]:
    sources = {
        "pypost/__init__.py": b"",
        "pypost/core/__init__.py": b"",
        "examples/__init__.py": b'"""Examples."""\n',
        "examples/pypost-library.yaml": b"collections: [collections/demo.json]\n",
        "examples/README.md": b"Examples\n",
        "examples/collections/demo.json": b"{}\n",
        "examples/environments/dev.json": b"{}\n",
    }
    for relative, content in sources.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return {relative.replace("examples/", "pypost/bundled_examples/", 1): content
            for relative, content in sources.items()}


def _write_wheel(wheel: Path, members: dict[str, bytes]) -> None:
    with ZipFile(wheel, "w") as archive:
        for member, content in members.items():
            archive.writestr(member, content)


def test_inspector_reports_all_required_members(tmp_path: Path) -> None:
    members = _canonical_sources(tmp_path)
    wheel = tmp_path / "test.whl"
    _write_wheel(wheel, members)
    assert inspect_wheel(wheel, tmp_path) == sorted(members)


@pytest.mark.parametrize("missing", [
    "pypost/core/__init__.py", "pypost/bundled_examples/__init__.py",
    "pypost/bundled_examples/pypost-library.yaml", "pypost/bundled_examples/README.md",
    "pypost/bundled_examples/collections/demo.json",
    "pypost/bundled_examples/environments/dev.json",
])
def test_inspector_rejects_missing_members(tmp_path: Path, missing: str) -> None:
    members = _canonical_sources(tmp_path)
    members.pop(missing)
    wheel = tmp_path / "test.whl"
    _write_wheel(wheel, members)
    with pytest.raises(ValueError, match=missing):
        inspect_wheel(wheel, tmp_path)


def test_inspector_checks_future_builtin_and_content(tmp_path: Path) -> None:
    members = _canonical_sources(tmp_path)
    (tmp_path / "examples/builtin-collections.yaml").write_bytes(b"collections: []\n")
    wheel = tmp_path / "test.whl"
    _write_wheel(wheel, members)
    with pytest.raises(ValueError, match="builtin-collections.yaml"):
        inspect_wheel(wheel, tmp_path)
    members["pypost/bundled_examples/builtin-collections.yaml"] = b"wrong\n"
    _write_wheel(wheel, members)
    with pytest.raises(ValueError, match="differs.*builtin-collections.yaml"):
        inspect_wheel(wheel, tmp_path)


def test_slow_seed_contains_packaging_target_dependencies(tmp_path: Path) -> None:
    _materialize_slow_smoke_workspace(tmp_path)
    assert (tmp_path / "scripts/check_package_data.py").read_bytes() == (
        REPO_ROOT / "scripts/check_package_data.py"
    ).read_bytes()


def test_inspector_cli_names_missing_members_and_exits_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    members = _canonical_sources(tmp_path)
    members.pop("pypost/core/__init__.py")
    wheel = tmp_path / "test.whl"
    _write_wheel(wheel, members)
    monkeypatch.setattr(
        "sys.argv",
        ["check_package_data.py", str(wheel), "--source-root", str(tmp_path)],
    )
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 1
    assert "pypost/core/__init__.py" in capsys.readouterr().err


def test_inspector_rejects_manifest_escape(tmp_path: Path) -> None:
    members = _canonical_sources(tmp_path)
    (tmp_path / "examples/pypost-library.yaml").write_text(
        "collections: [../outside.json]\n", encoding="utf-8",
    )
    wheel = tmp_path / "test.whl"
    _write_wheel(wheel, members)
    with pytest.raises(ValueError, match="escapes canonical source"):
        inspect_wheel(wheel, tmp_path)


@pytest.mark.slow
@pytest.mark.timeout(180)
def test_make_verifies_real_wheel() -> None:
    result = _run_make(REPO_ROOT, "check-package-data", timeout=170)
    assert result.returncode == 0, result.stdout + result.stderr
    for resource in ("pypost-library.yaml", "README.md", "environments/jira_cloud.json"):
        assert f"verified: pypost/bundled_examples/{resource}" in result.stdout
