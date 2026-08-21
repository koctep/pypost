import pytest

from pypost.core.config_manager import ConfigManager, StrictConfigError

pytestmark = pytest.mark.timeout(30)


def test_strict_config_missing_file_uses_defaults(tmp_path):
    settings = ConfigManager(config_dir=tmp_path).load_config_strict()

    assert settings.metrics_port == 9080


def test_strict_config_rejects_malformed_json_without_exposing_value(tmp_path):
    secret = "operator-secret-value"
    (tmp_path / "settings.json").write_text(f'{{"alert_webhook_auth_header": "{secret}"')

    with pytest.raises(StrictConfigError) as error:
        ConfigManager(config_dir=tmp_path).load_config_strict()

    assert error.value.category == "malformed_json"
    assert secret not in str(error.value)


def test_strict_config_translates_unreadable_file(monkeypatch, tmp_path):
    settings_path = tmp_path / "settings.json"
    settings_path.write_text("{}", encoding="utf-8")
    manager = ConfigManager(config_dir=tmp_path)

    def fail_open(*_args, **_kwargs):
        raise OSError("private filesystem detail")

    monkeypatch.setattr("builtins.open", fail_open)

    with pytest.raises(StrictConfigError) as raised:
        manager.load_config_strict()

    assert raised.value.category == "unreadable"
    assert "private filesystem detail" not in str(raised.value)


def test_strict_config_translates_invalid_settings_without_exposing_value(tmp_path):
    secret = "operator-private-setting"
    (tmp_path / "settings.json").write_text(
        '{"theme": "invalid-theme", "alert_webhook_auth_header": "'
        + secret
        + '"}',
        encoding="utf-8",
    )

    with pytest.raises(StrictConfigError) as raised:
        ConfigManager(config_dir=tmp_path).load_config_strict()

    assert raised.value.category == "invalid_settings"
    assert secret not in str(raised.value)
