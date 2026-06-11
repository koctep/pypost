
import pytest

pytestmark = pytest.mark.timeout(120)

import logging
import tempfile
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

from pypost.core.config_manager import ConfigManager
from pypost.core.storage import StorageManager
from pypost.models.models import Environment
from pypost.models.settings import AppSettings
from pypost.ui.dialogs.env_dialog import EnvironmentDialog
from pypost.ui.presenters.env_presenter import EnvPresenter
from pypost.core.constants import HIDDEN_MASK


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


class _FakeMCPManager:
    def __init__(self):
        self.status_changed = MagicMock()
        self.status_changed.connect = MagicMock()

    def start_server(self, port, tools, host="127.0.0.1"):  # noqa: ARG002
        return None

    def stop_server(self):
        return None

    def set_variable_supplier(self, supplier):  # noqa: ARG002
        return None


def _empty_collections():
    return []


def test_env_with_hidden_keys_survives_presenter_save_and_restart(qapp):  # noqa: ARG001
    with tempfile.TemporaryDirectory() as td:
        with patch("pypost.core.storage.user_data_dir", return_value=td):
            storage = StorageManager()
            initial_env = Environment(
                name="Dev",
                variables={"API_KEY": "secret"},
                hidden_keys={"API_KEY"},
            )
            storage.save_environments([initial_env])

            with patch("pypost.core.config_manager.user_config_dir", return_value=td):
                presenter = EnvPresenter(
                    storage=storage,
                    config_manager=ConfigManager(),
                    mcp_manager=_FakeMCPManager(),
                    settings=AppSettings(),
                    get_collections=_empty_collections,
                    metrics=MagicMock(),
                )
                presenter.load_environments()
                presenter.env_selector.setCurrentIndex(1)
                presenter.handle_variable_set_request("NEW_KEY", "new-value")

                reloaded = storage.load_environments()
                assert len(reloaded) == 1
                assert reloaded[0].name == "Dev"
                assert reloaded[0].variables == {
                    "API_KEY": "secret",
                    "NEW_KEY": "new-value",
                }
                assert reloaded[0].hidden_keys == {"API_KEY"}

                presenter_after_restart = EnvPresenter(
                    storage=storage,
                    config_manager=ConfigManager(),
                    mcp_manager=_FakeMCPManager(),
                    settings=AppSettings(),
                    get_collections=_empty_collections,
                    metrics=MagicMock(),
                )
                presenter_after_restart.load_environments()
                loaded_env = presenter_after_restart.env_selector.itemData(1)
                assert isinstance(loaded_env, Environment)
                assert loaded_env.hidden_keys == {"API_KEY"}


def test_default_masked_toggle_log_after_persistence_round_trip(qapp, caplog):  # noqa: ARG001
    """PYPOST-489: default dialog masks key names after storage round-trip."""
    env_name = "Dev"
    variable_key = "API_KEY"
    variable_value = "secret"
    with tempfile.TemporaryDirectory() as td:
        with patch("pypost.core.storage.user_data_dir", return_value=td):
            storage = StorageManager()
            initial_env = Environment(
                name=env_name,
                variables={variable_key: variable_value},
            )
            storage.save_environments([initial_env])

            reloaded = storage.load_environments()
            dialog = EnvironmentDialog(reloaded)
            try:
                dialog.on_env_selected(0)
                hidden_cb = dialog._get_hidden_checkbox(0)
                assert hidden_cb is not None
                with caplog.at_level(logging.INFO):
                    hidden_cb.setChecked(True)
                assert any(
                    f"env_hidden_flag_changed env_name={env_name} key={HIDDEN_MASK} hidden=True"
                    in r.message
                    for r in caplog.records
                )
                assert not any(variable_key in r.message for r in caplog.records)
                assert not any(variable_value in r.message for r in caplog.records)
            finally:
                dialog.close()


def test_hidden_toggle_persists_and_reveal_keeps_original_value(qapp):  # noqa: ARG001
    with tempfile.TemporaryDirectory() as td:
        with patch("pypost.core.storage.user_data_dir", return_value=td):
            storage = StorageManager()
            initial_env = Environment(
                name="Dev",
                variables={"API_KEY": "secret"},
                hidden_keys={"API_KEY"},
            )
            storage.save_environments([initial_env])

            environments = storage.load_environments()
            dialog = EnvironmentDialog(environments)
            try:
                dialog.on_env_selected(0)
                assert dialog.vars_table.item(0, 1).text() == HIDDEN_MASK

                hidden_cb = dialog._get_hidden_checkbox(0)
                assert hidden_cb is not None
                hidden_cb.setChecked(False)
                assert dialog.vars_table.item(0, 1).text() == "secret"
                assert environments[0].hidden_keys == set()

                storage.save_environments(environments)
            finally:
                dialog.close()

            reloaded = storage.load_environments()
            assert len(reloaded) == 1
            assert reloaded[0].variables == {"API_KEY": "secret"}
            assert reloaded[0].hidden_keys == set()


def test_presenter_load_shows_no_env_when_key_missing_for_encrypted_data(qapp):  # noqa: ARG001
    fernet = pytest.importorskip("cryptography.fernet")
    with tempfile.TemporaryDirectory() as td:
        with patch("pypost.core.storage.user_data_dir", return_value=td):
            with patch.dict(
                "os.environ",
                {
                    "PYPOST_ENV_ENCRYPTION_ENABLED": "true",
                    "PYPOST_ENV_ENCRYPTION_KEY": fernet.Fernet.generate_key().decode("utf-8"),
                },
                clear=False,
            ):
                storage = StorageManager()
                storage.save_environments(
                    [
                        Environment(
                            id="e1",
                            name="Dev",
                            variables={"SECRET": "value"},
                            hidden_keys={"SECRET"},
                        )
                    ]
                )

            with patch("pypost.core.config_manager.user_config_dir", return_value=td):
                with patch.dict(
                    "os.environ",
                    {
                        "PYPOST_ENV_ENCRYPTION_ENABLED": "true",
                        "PYPOST_ENV_ENCRYPTION_KEY": "",
                    },
                    clear=False,
                ):
                    presenter = EnvPresenter(
                        storage=storage,
                        config_manager=ConfigManager(),
                        mcp_manager=_FakeMCPManager(),
                        settings=AppSettings(),
                        get_collections=_empty_collections,
                        metrics=MagicMock(),
                    )
                    presenter.load_environments()

                    assert presenter.env_selector.count() == 1
                    assert presenter.env_selector.currentIndex() == 0
