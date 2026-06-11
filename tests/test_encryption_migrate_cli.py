"""CLI tests for scripts/encryption_migrate.py (PYPOST-487)."""

import json

import pytest

from pypost.core.storage import StorageManager
from pypost.models.models import Environment
from pypost.models.settings import AppSettings


def _patch_dirs(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    monkeypatch.setattr(
        "pypost.core.config_manager.user_config_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-config"),
    )


def _write_settings(tmp_path, settings: AppSettings) -> None:
    config_dir = tmp_path / "pypost-config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "settings.json").write_text(
        json.dumps(settings.model_dump()),
        encoding="utf-8",
    )


def _import_cli_main():
    import importlib.util
    from pathlib import Path

    cli_path = Path(__file__).resolve().parents[1] / "scripts" / "encryption_migrate.py"
    spec = importlib.util.spec_from_file_location("encryption_migrate", cli_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.main


def test_cli_report_empty_inventory(tmp_path, monkeypatch, capsys):
    _patch_dirs(tmp_path, monkeypatch)
    _write_settings(tmp_path, AppSettings())
    main = _import_cli_main()

    code = main(["report"])

    captured = capsys.readouterr()
    assert code == 0
    assert "environments: 0" in captured.out


def test_cli_verify_success(tmp_path, monkeypatch, capsys):
    fernet = pytest.importorskip("cryptography.fernet")
    _patch_dirs(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    _write_settings(tmp_path, AppSettings(env_encryption_enabled=True))

    storage = StorageManager()
    storage.apply_encryption_settings(AppSettings(env_encryption_enabled=True))
    storage.save_environments(
        [
            Environment(
                name="Dev",
                variables={"SECRET": "value"},
                hidden_keys={"SECRET"},
            )
        ]
    )

    main = _import_cli_main()
    code = main(["verify"])

    captured = capsys.readouterr()
    assert code == 0
    assert "encrypted_envelopes: 1" in captured.out


def test_cli_re_encrypt_requires_encryption_enabled(tmp_path, monkeypatch, capsys):
    _patch_dirs(tmp_path, monkeypatch)
    _write_settings(tmp_path, AppSettings(env_encryption_enabled=False))
    main = _import_cli_main()

    code = main(["re-encrypt"])

    captured = capsys.readouterr()
    assert code == 1
    assert "Encryption is not enabled" in captured.err


def test_cli_re_encrypt_dry_run(tmp_path, monkeypatch, capsys):
    fernet = pytest.importorskip("cryptography.fernet")
    _patch_dirs(tmp_path, monkeypatch)
    active_key = fernet.Fernet.generate_key().decode("utf-8")
    historical_key = fernet.Fernet.generate_key().decode("utf-8")
    from pypost.core.key_provider import build_key_id
    from pypost.core.key_sources.env import EnvKeySource

    active_id = build_key_id(active_key)
    historical_id = build_key_id(historical_key)
    registry_path = tmp_path / "keys.json"
    registry_path.write_text(
        json.dumps(
            {
                "active_key_id": active_id,
                "keys": {active_id: active_key, historical_id: historical_key},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(EnvKeySource.KEYS_FILE, str(registry_path))
    monkeypatch.delenv(EnvKeySource.ENV_KEY, raising=False)
    _write_settings(tmp_path, AppSettings(env_encryption_enabled=True))

    storage = StorageManager()
    storage.apply_encryption_settings(AppSettings(env_encryption_enabled=True))
    storage.save_environments(
        [
            Environment(
                name="Dev",
                variables={"SECRET": "value"},
                hidden_keys={"SECRET"},
            )
        ]
    )

    registry_path.write_text(
        json.dumps(
            {
                "active_key_id": historical_id,
                "keys": {active_id: active_key, historical_id: historical_key},
            }
        ),
        encoding="utf-8",
    )

    main = _import_cli_main()
    code = main(["re-encrypt", "--dry-run", "--no-backup"])

    captured = capsys.readouterr()
    assert code == 0
    assert "dry_run: true" in captured.out
    assert f"  {historical_id}: 1" in captured.out


def test_cli_encrypt_plaintext(tmp_path, monkeypatch, capsys):
    fernet = pytest.importorskip("cryptography.fernet")
    _patch_dirs(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    _write_settings(tmp_path, AppSettings(env_encryption_enabled=True))

    storage = StorageManager()
    plain_payload = [
        {
            "id": "e1",
            "name": "Plain",
            "variables": {"SECRET": "plain"},
            "hidden_keys": ["SECRET"],
            "enable_mcp": False,
        }
    ]
    with open(storage.environments_file, "w", encoding="utf-8") as handle:
        json.dump(plain_payload, handle, indent=2)

    main = _import_cli_main()
    code = main(["encrypt-plaintext", "--no-backup"])

    captured = capsys.readouterr()
    assert code == 0
    assert "plaintext_hidden: 0" in captured.out
    assert "encrypted_envelopes: 1" in captured.out
