import json
import logging
import os
from pathlib import Path
from typing import Any

from pypost.core.encryption_key import EncryptionKey
from pypost.core.key_sources.registry import KeyRegistry

logger = logging.getLogger(__name__)

SECRETS_FILE_ENV = "PYPOST_ENV_ENCRYPTION_SECRETS_FILE"


class SecretBackend:
    """Abstract base class for one secret-store channel."""

    def try_load_registry(self, backend_config: dict[str, Any]) -> KeyRegistry | None:
        raise NotImplementedError


class FileSecretBackend(SecretBackend):
    """Loads a key registry from a local JSON file."""

    def try_load_registry(self, backend_config: dict[str, Any]) -> KeyRegistry | None:
        path_value = backend_config.get("path", "")
        if not path_value:
            return None
        path = Path(str(path_value))
        if not path.is_file():
            logger.debug("secret_backend_file_missing path=%s", path)
            return None
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            logger.debug("secret_backend_file_load_failed path=%s reason=%s", path, exc)
            return None
        return _registry_from_dict(data)


class SecretBackendChain:
    """Ordered fallback across secret-store backends."""

    def __init__(self, backends: list[SecretBackend]) -> None:
        self._backends = backends

    def resolve_registry(
        self,
        spec: dict[str, Any],
        backend_configs: list[dict[str, Any]],
    ) -> KeyRegistry | None:
        for index, config in enumerate(backend_configs):
            backend_type = config.get("type", "")
            backend = _create_backend_for_type(backend_type)
            if backend is None:
                logger.debug("secret_backend_type_unsupported type=%s", backend_type)
                if index + 1 < len(backend_configs):
                    next_type = backend_configs[index + 1].get("type", "")
                    logger.warning(
                        "secret_backend_chain_fallback failed_type=%s next_type=%s",
                        backend_type,
                        next_type,
                    )
                continue
            registry = backend.try_load_registry(config)
            if registry is not None:
                if index > 0:
                    logger.info(
                        "secret_backend_chain_resolved_via_fallback "
                        "backend_type=%s skipped_types=%s",
                        backend_type,
                        ",".join(str(c.get("type", "")) for c in backend_configs[:index]),
                    )
                return registry
            if index + 1 < len(backend_configs):
                next_type = backend_configs[index + 1].get("type", "")
                logger.warning(
                    "secret_backend_chain_fallback failed_type=%s next_type=%s",
                    backend_type,
                    next_type,
                )
        return _registry_from_dict(spec)


def _registry_from_dict(data: dict[str, Any]) -> KeyRegistry | None:
    active_key_id = data.get("active_key_id", "")
    keys = data.get("keys", {})
    if not active_key_id or not isinstance(keys, dict) or not keys:
        return None
    return KeyRegistry(active_key_id=str(active_key_id), keys=keys)


def _create_backend_for_type(backend_type: str) -> SecretBackend | None:
    if backend_type == "file":
        return FileSecretBackend()
    return None


class SecretStoreKeySource:
    """Resolves keys from an operator-managed secret-store spec file."""

    @property
    def name(self) -> str:
        return "secret_store"

    def _load_spec(self) -> dict[str, Any] | None:
        path_value = os.getenv(SECRETS_FILE_ENV, "").strip()
        if not path_value:
            return None
        path = Path(path_value)
        if not path.is_file():
            logger.debug("secret_store_spec_missing path=%s", path)
            return None
        try:
            with open(path, encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            logger.debug("secret_store_spec_load_failed path=%s reason=%s", path, exc)
            return None

    def _resolve_registry(self) -> KeyRegistry | None:
        spec = self._load_spec()
        if spec is None:
            return None
        backends = spec.get("backends", [])
        if isinstance(backends, list) and backends:
            chain = SecretBackendChain([])
            return chain.resolve_registry(spec, backends)
        return _registry_from_dict(spec)

    def try_resolve_active(self) -> EncryptionKey | None:
        registry = self._resolve_registry()
        if registry is None:
            return None
        material = registry.keys.get(registry.active_key_id, "").strip()
        if not material:
            return None
        logger.debug(
            "secret_store_encryption_key_resolved key_id=%s",
            registry.active_key_id,
        )
        return EncryptionKey(key=material, key_id=registry.active_key_id)

    def try_resolve_by_id(self, key_id: str) -> EncryptionKey | None:
        registry = self._resolve_registry()
        if registry is None:
            return None
        material = registry.keys.get(key_id, "").strip()
        if not material:
            return None
        logger.debug("secret_store_encryption_key_match key_id=%s", key_id)
        return EncryptionKey(key=material, key_id=key_id)
