"""Unit tests for encryption settings resolution (PYPOST-481)."""

import pytest

from pypost.core.encryption_config import (
    build_key_provider,
    resolve_encryption_enabled,
    resolve_key_source,
)
from pypost.core.key_provider import LocalKeyProvider
from pypost.models.settings import AppSettings


def test_resolve_encryption_enabled_uses_settings_when_set(monkeypatch):
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_ENABLED", raising=False)
    settings = AppSettings(env_encryption_enabled=True)
    assert resolve_encryption_enabled(settings) is True


def test_resolve_encryption_enabled_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    settings = AppSettings(env_encryption_enabled=None)
    assert resolve_encryption_enabled(settings) is True


def test_resolve_key_source_defaults_to_environment():
    assert resolve_key_source(AppSettings()) == "environment"


def test_resolve_key_source_uses_settings_value():
    settings = AppSettings(env_encryption_key_source="environment")
    assert resolve_key_source(settings) == "environment"


def test_resolve_key_source_unsupported_falls_back(monkeypatch):
    monkeypatch.setattr(
        "pypost.core.encryption_config.logger.warning",
        lambda *args, **kwargs: None,
    )
    settings = AppSettings(env_encryption_key_source="vault")
    assert resolve_key_source(settings) == "environment"


def test_build_key_provider_environment_returns_local_provider():
    provider = build_key_provider("environment")
    assert isinstance(provider, LocalKeyProvider)


def test_build_key_provider_unsupported_raises():
    with pytest.raises(ValueError, match="Unsupported encryption key source"):
        build_key_provider("vault")  # type: ignore[arg-type]
