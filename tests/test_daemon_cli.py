import sys
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.timeout(30)


def test_daemon_help_documents_both_directories(capsys):
    from pypost.daemon import main

    with pytest.raises(SystemExit) as error:
        main(["--help"])

    assert error.value.code == 0
    output = capsys.readouterr().out
    assert "--collections-dir" in output
    assert "--environments-dir" in output


def test_daemon_invalid_explicit_directory_returns_nonzero(tmp_path):
    from pypost.daemon import main

    environments_dir = tmp_path / "environments"
    environments_dir.mkdir()

    assert main(
        [
            "--collections-dir",
            str(tmp_path / "missing"),
            "--environments-dir",
            str(environments_dir),
        ]
    ) == 1


def test_daemon_import_does_not_add_widget_modules():
    widgets_before = "pypost.ui.main_window" in sys.modules

    import pypost.daemon  # noqa: F401

    assert ("pypost.ui.main_window" in sys.modules) is widgets_before


def test_packaging_declares_daemon_console_script():
    from pathlib import Path

    project = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'pypost-daemon = "pypost.daemon:main"' in project


def test_daemon_injects_process_environment_and_cleans_up_on_normal_signal(
    monkeypatch,
):
    import pypost.daemon as daemon

    registered_handlers = []
    observed = {}

    class FakeSignal:
        def __init__(self):
            self.slots = []

        def connect(self, slot):
            self.slots.append(slot)

        def emit(self):
            for slot in tuple(self.slots):
                slot()

    class FakeApplication:
        aboutToQuit = FakeSignal()

        @staticmethod
        def instance():
            return None

        def __init__(self, _argv):
            self.quit_requested = False

        def quit(self):
            self.quit_requested = True

        def exec(self):
            registered_handlers[0](15, None)
            assert self.quit_requested
            self.aboutToQuit.emit()

    class FakeTimer:
        timeout = FakeSignal()

        def setInterval(self, _interval):
            return None

        def start(self):
            return None

        def stop(self):
            return None

        @staticmethod
        def singleShot(_interval, slot):
            slot()

    class FakeRuntime:
        latest = None

        def __init__(self, paths):
            self.paths = paths
            self.exit_code = 0
            self.started = False
            self.shutdown_calls = 0
            FakeRuntime.latest = self

        def start(self):
            self.started = True

        def shutdown(self):
            if self.shutdown_calls == 0:
                self.shutdown_calls = 1

    paths = SimpleNamespace()

    def resolve_paths(**kwargs):
        observed.update(kwargs)
        return paths

    def install_signal(_number, handler):
        if callable(handler) and handler not in registered_handlers:
            registered_handlers.append(handler)
        return object()

    monkeypatch.setattr(daemon, "resolve_daemon_paths", resolve_paths)
    monkeypatch.setattr(daemon, "validate_daemon_paths", lambda _paths: None)
    monkeypatch.setattr(daemon, "QCoreApplication", FakeApplication)
    monkeypatch.setattr(daemon, "QTimer", FakeTimer)
    monkeypatch.setattr(daemon, "DaemonRuntime", FakeRuntime)
    monkeypatch.setattr(daemon.signal, "signal", install_signal)

    assert daemon.main([]) == 0
    assert observed["environ"] is daemon.os.environ
    assert FakeRuntime.latest.started
    assert FakeRuntime.latest.shutdown_calls == 1
