"""PYPOST-923/924/925: Qt/EGL apt parity and shared composite contract."""

from __future__ import annotations

import importlib
import inspect
import re
from pathlib import Path

import pytest

from tests.helpers.ci_workflow_yaml import workflow_job_block

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "test.yml"
_QT_EGL_COMPOSITE_ACTION = (
    _REPO_ROOT / ".github" / "actions" / "install-qt-egl-runtime" / "action.yml"
)
_QT_EGL_COMPOSITE_USES = "./.github/actions/install-qt-egl-runtime"
_QT_USING_JOBS = ("test", "make-install-smoke", "agent-e2e")
_APT_PKG_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9+._-]*$")
_QT_EGL_SENTINEL_PKG = "libegl1"


def _packages_from_apt_install_block(text: str) -> frozenset[str]:
    """Extract Debian package names from apt-get install continuation lines."""
    found: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip().rstrip("\\").strip()
        if not stripped or stripped.startswith("#"):
            continue
        if _APT_PKG_NAME_RE.fullmatch(stripped):
            found.add(stripped)
    return frozenset(found)


def _expected_qt_egl_packages() -> frozenset[str]:
    """Authoritative Qt/EGL package set from the shared composite action."""
    if not _QT_EGL_COMPOSITE_ACTION.is_file():
        pytest.fail(
            f"Missing composite action {_QT_EGL_COMPOSITE_ACTION.relative_to(_REPO_ROOT)}"
        )
    text = _QT_EGL_COMPOSITE_ACTION.read_text(encoding="utf-8")
    return _packages_from_apt_install_block(text)


def _count_inline_libegl1_apt_install_blocks(workflow_text: str) -> int:
    """Return count of inline run blocks with apt-get install listing libegl1."""
    count = 0
    for match in re.finditer(r"run:\s*\|\s*\n((?:          .*\n)*)", workflow_text):
        block = match.group(1)
        if "sudo apt-get install" in block and "libegl1" in block:
            count += 1
    return count


def test_install_qt_egl_composite_action_exists_with_full_package_set() -> None:
    """Composite action must exist, be composite, and install Qt/EGL packages."""
    rel = _QT_EGL_COMPOSITE_ACTION.relative_to(_REPO_ROOT)
    if not _QT_EGL_COMPOSITE_ACTION.is_file():
        pytest.fail(f"Missing composite action {rel}")

    text = _QT_EGL_COMPOSITE_ACTION.read_text(encoding="utf-8")
    if "using: composite" not in text:
        pytest.fail(f"{rel}: runs.using must be composite")

    pkgs = _expected_qt_egl_packages()
    if not pkgs:
        pytest.fail(f"{rel}: apt install must list at least one package")
    if _QT_EGL_SENTINEL_PKG not in pkgs:
        pytest.fail(f"{rel}: apt install must include {_QT_EGL_SENTINEL_PKG!r}")


def test_qt_using_jobs_reference_install_qt_egl_composite() -> None:
    """Jobs test, make-install-smoke, and agent-e2e must use the composite."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    missing_jobs: list[str] = []
    for job_id in _QT_USING_JOBS:
        block = workflow_job_block(text, job_id, workflow_path=_WORKFLOW)
        if _QT_EGL_COMPOSITE_USES not in block:
            missing_jobs.append(job_id)
    if missing_jobs:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)}: jobs {missing_jobs} must "
            f"contain uses: {_QT_EGL_COMPOSITE_USES!r}"
        )


def test_workflow_has_zero_inline_libegl1_apt_install_blocks() -> None:
    """test.yml must contain zero inline apt-get install blocks listing libegl1."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    count = _count_inline_libegl1_apt_install_blocks(text)
    if count != 0:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)} must contain zero inline "
            f"apt-get install blocks listing libegl1; found {count}"
        )


def test_make_install_smoke_job_exists() -> None:
    """Workflow must define the make-install-smoke job."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    workflow_job_block(text, "make-install-smoke", workflow_path=_WORKFLOW)


def test_composite_qt_egl_packages_inherited_by_qt_using_jobs() -> None:
    """Composite must provision Qt/EGL set inherited by all ``_QT_USING_JOBS``.

    Jobs ``test``, ``make-install-smoke``, and ``agent-e2e`` reference the same
    composite action; per-job ``uses:`` coverage lives in
    ``test_qt_using_jobs_reference_install_qt_egl_composite``. This test asserts
    derived package integrity (non-empty, ``libegl1`` sentinel) that all three
    jobs inherit. Without these packages, shared conftest PySide6 import fails
    collection under ``QT_QPA_PLATFORM=offscreen``.
    """
    rel = _QT_EGL_COMPOSITE_ACTION.relative_to(_REPO_ROOT)
    pkgs = _expected_qt_egl_packages()
    if not pkgs:
        pytest.fail(f"{rel}: apt install must list at least one package")
    if _QT_EGL_SENTINEL_PKG not in pkgs:
        pytest.fail(
            f"{rel}: apt install must include {_QT_EGL_SENTINEL_PKG!r} "
            "(PySide6 headless runtime; inherited by test, make-install-smoke, agent-e2e)"
        )


def _reference_packages_from_composite_action() -> frozenset[str]:
    """Independent apt-line parse of composite action.yml for contract tests."""
    text = _QT_EGL_COMPOSITE_ACTION.read_text(encoding="utf-8")
    return _packages_from_apt_install_block(text)


def test_qt_egl_contract_has_no_duplicate_authoritative_frozenset() -> None:
    """PYPOST-925: expected package set must not live in a hardcoded frozenset."""
    mod = importlib.import_module("tests.test_ci_make_install_smoke_qt_runtime")
    assert not hasattr(mod, "_PEER_QT_EGL_PACKAGES"), (
        "module must not define _PEER_QT_EGL_PACKAGES; "
        "derive expected packages from composite action.yml only"
    )


def test_expected_qt_egl_packages_derived_from_composite_only() -> None:
    """PYPOST-925: _expected_qt_egl_packages() parses composite without frozenset gate."""
    mod = importlib.import_module("tests.test_ci_make_install_smoke_qt_runtime")
    helper = getattr(mod, "_expected_qt_egl_packages", None)
    assert helper is not None, (
        "module must define _expected_qt_egl_packages() derived from composite action.yml"
    )

    direct = _reference_packages_from_composite_action()
    derived = helper()
    assert derived == direct, (
        "_expected_qt_egl_packages() must equal packages parsed from action.yml directly; "
        f"direct={sorted(direct)} derived={sorted(derived)}"
    )

    helper_source = inspect.getsource(helper)
    assert "_PEER_QT_EGL_PACKAGES" not in helper_source, (
        "_expected_qt_egl_packages() must not intersect with _PEER_QT_EGL_PACKAGES"
    )


def test_composite_validation_uses_derived_package_helper() -> None:
    """PYPOST-925: composite package checks must call _expected_qt_egl_packages()."""
    mod = importlib.import_module("tests.test_ci_make_install_smoke_qt_runtime")
    for test_name in (
        "test_install_qt_egl_composite_action_exists_with_full_package_set",
        "test_composite_qt_egl_packages_inherited_by_qt_using_jobs",
    ):
        fn = getattr(mod, test_name)
        source = inspect.getsource(fn)
        assert "_expected_qt_egl_packages" in source, (
            f"{test_name} must call _expected_qt_egl_packages()"
        )
        assert "_PEER_QT_EGL_PACKAGES" not in source, (
            f"{test_name} must not gate package validation on _PEER_QT_EGL_PACKAGES"
        )
