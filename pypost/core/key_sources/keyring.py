import logging

from pypost.core.encryption_key import EncryptionKey, build_key_id

logger = logging.getLogger(__name__)

SERVICE_NAME = "pypost/env-encryption"
ACTIVE_ENTRY = "active"


class KeyringKeySource:
    """Resolves keys from the OS-integrated credential store via keyring."""

    @property
    def name(self) -> str:
        return "keyring"

    def _get_keyring(self):
        try:
            import keyring
        except ImportError:
            logger.debug("keyring_package_unavailable")
            return None
        return keyring

    def try_resolve_active(self) -> EncryptionKey | None:
        keyring_mod = self._get_keyring()
        if keyring_mod is None:
            return None
        try:
            material = keyring_mod.get_password(SERVICE_NAME, ACTIVE_ENTRY)
        except Exception as exc:
            logger.debug("keyring_active_lookup_failed reason=%s", exc)
            return None
        if not material or not material.strip():
            return None
        material = material.strip()
        key_id = build_key_id(material)
        logger.debug("keyring_encryption_key_resolved entry=active key_id=%s", key_id)
        return EncryptionKey(key=material, key_id=key_id)

    def try_resolve_by_id(self, key_id: str) -> EncryptionKey | None:
        keyring_mod = self._get_keyring()
        if keyring_mod is None:
            return None
        try:
            material = keyring_mod.get_password(SERVICE_NAME, key_id)
        except Exception as exc:
            logger.debug("keyring_key_lookup_failed key_id=%s reason=%s", key_id, exc)
            return None
        if not material or not material.strip():
            return None
        material = material.strip()
        logger.debug("keyring_encryption_key_match key_id=%s", key_id)
        return EncryptionKey(key=material, key_id=key_id)
