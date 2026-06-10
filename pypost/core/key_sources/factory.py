from pypost.core.key_sources.env import EnvKeySource
from pypost.core.key_sources.keyring import KeyringKeySource
from pypost.core.key_sources.protocol import KeySource
from pypost.core.key_sources.secret_store import (
    FileSecretBackend,
    SecretBackend,
    SecretStoreKeySource,
)


def create_key_source(source: str) -> KeySource:
    if source == "environment":
        return EnvKeySource()
    if source == "keyring":
        return KeyringKeySource()
    if source == "secret_store":
        return SecretStoreKeySource()
    raise ValueError(f"Unsupported encryption key source: {source}")


def create_secret_backend(backend_type: str) -> SecretBackend | None:
    if backend_type == "file":
        return FileSecretBackend()
    return None
