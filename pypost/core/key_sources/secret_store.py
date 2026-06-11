import json
import logging
import os
from pathlib import Path
from typing import Any

import requests

from pypost.core.encryption_key import EncryptionKey
from pypost.core.key_sources.registry import KeyRegistry

logger = logging.getLogger(__name__)

DEFAULT_VAULT_TOKEN_ENV = "VAULT_TOKEN"
DEFAULT_VAULT_TIMEOUT_SECONDS = 10.0

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


class EnvIndirectionSecretBackend(SecretBackend):
    """Loads a key registry by reading Fernet material from named environment variables."""

    def try_load_registry(self, backend_config: dict[str, Any]) -> KeyRegistry | None:
        active_key_id = str(backend_config.get("active_key_id", "")).strip()
        key_env_vars = backend_config.get("keys", {})
        if not active_key_id or not isinstance(key_env_vars, dict) or not key_env_vars:
            return None
        resolved_keys: dict[str, str] = {}
        for kid, env_name in key_env_vars.items():
            if not isinstance(env_name, str):
                continue
            env_var = env_name.strip()
            if not env_var:
                continue
            material = os.getenv(env_var, "").strip()
            if material:
                resolved_keys[str(kid)] = material
        if active_key_id not in resolved_keys:
            logger.debug(
                "env_indirection_active_key_missing key_id=%s",
                active_key_id,
            )
            return None
        return KeyRegistry(active_key_id=active_key_id, keys=resolved_keys)


class VaultSecretBackend(SecretBackend):
    """Loads a key registry from a HashiCorp Vault KV HTTP endpoint."""

    def try_load_registry(self, backend_config: dict[str, Any]) -> KeyRegistry | None:
        url = str(backend_config.get("url", "")).strip()
        if not url:
            return None
        token_env = str(backend_config.get("token_env", DEFAULT_VAULT_TOKEN_ENV)).strip()
        token = os.getenv(token_env, "").strip()
        if not token:
            logger.debug("vault_backend_token_missing token_env=%s", token_env)
            return None
        timeout = float(backend_config.get("timeout", DEFAULT_VAULT_TIMEOUT_SECONDS))
        try:
            response = requests.get(
                url,
                headers={"X-Vault-Token": token},
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError, TypeError) as exc:
            logger.debug("vault_backend_fetch_failed url=%s reason=%s", url, exc)
            return None
        return _registry_from_vault_payload(payload)


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
            backend = _create_secret_backend(backend_type)
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


def _registry_from_vault_payload(payload: dict[str, Any]) -> KeyRegistry | None:
    data = payload.get("data", payload)
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    if not isinstance(data, dict):
        return None
    keys_value = data.get("keys")
    if isinstance(keys_value, str):
        try:
            data = {**data, "keys": json.loads(keys_value)}
        except json.JSONDecodeError:
            return None
    return _registry_from_dict(data)


def _create_secret_backend(backend_type: str) -> SecretBackend | None:
    from pypost.core.key_sources.factory import create_secret_backend

    return create_secret_backend(backend_type)


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
