import json
import logging
import os
from pathlib import Path

from pypost.core.encryption_key import EncryptionKey, build_key_id
from pypost.core.key_sources.file_cache import MtimeFileCache
from pypost.core.key_sources.registry import KeyRegistry

logger = logging.getLogger(__name__)

_registry_cache: MtimeFileCache[KeyRegistry] = MtimeFileCache()


class EnvKeySource:
    """Resolves keys from process environment and optional JSON registry file."""

    ENV_KEY = "PYPOST_ENV_ENCRYPTION_KEY"
    KEYS_FILE = "PYPOST_ENV_ENCRYPTION_KEYS_FILE"

    @property
    def name(self) -> str:
        return "environment"

    def _read_registry_file(self, path: Path) -> KeyRegistry | None:
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            logger.debug("env_keys_file_load_failed path=%s reason=%s", path, exc)
            return None
        active_key_id = data.get("active_key_id", "")
        keys = data.get("keys", {})
        if not active_key_id or not isinstance(keys, dict) or not keys:
            logger.debug("env_keys_file_invalid path=%s", path)
            return None
        return KeyRegistry(active_key_id=active_key_id, keys=keys)

    def _load_registry(self) -> KeyRegistry | None:
        path_value = os.getenv(self.KEYS_FILE, "").strip()
        if not path_value:
            return None
        path = Path(path_value)
        if not path.is_file():
            logger.debug("env_keys_file_missing path=%s", path)
            return None
        return _registry_cache.get(path, self._read_registry_file)

    def _key_from_material(self, material: str) -> EncryptionKey:
        return EncryptionKey(key=material, key_id=build_key_id(material))

    def try_resolve_active(self) -> EncryptionKey | None:
        registry = self._load_registry()
        if registry is not None:
            material = registry.keys.get(registry.active_key_id, "").strip()
            if material:
                logger.debug(
                    "env_encryption_key_resolved source=keys_file key_id=%s",
                    registry.active_key_id,
                )
                return EncryptionKey(key=material, key_id=registry.active_key_id)
            return None
        key = os.getenv(self.ENV_KEY, "").strip()
        if not key:
            return None
        key_id = build_key_id(key)
        logger.debug("env_encryption_key_resolved source=env_var key_id=%s", key_id)
        return EncryptionKey(key=key, key_id=key_id)

    def try_resolve_by_id(self, key_id: str) -> EncryptionKey | None:
        registry = self._load_registry()
        if registry is not None:
            material = registry.keys.get(key_id, "").strip()
            if material:
                logger.debug("env_encryption_key_match source=keys_file key_id=%s", key_id)
                return EncryptionKey(key=material, key_id=key_id)
            return None
        key = os.getenv(self.ENV_KEY, "").strip()
        if not key:
            return None
        current_id = build_key_id(key)
        if current_id != key_id:
            return None
        logger.debug("env_encryption_key_match source=env_var key_id=%s", key_id)
        return EncryptionKey(key=key, key_id=current_id)
