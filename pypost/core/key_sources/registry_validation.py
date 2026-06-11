"""Fernet key-material validation for key registries."""

import logging

logger = logging.getLogger(__name__)


def is_valid_fernet_key_material(material: str) -> bool:
    if not material or not material.strip():
        return False
    try:
        from cryptography.fernet import Fernet

        Fernet(material.strip().encode("utf-8"))
        return True
    except (ImportError, TypeError, ValueError):
        return False


def filter_valid_registry_keys(
    keys: dict[str, str],
    *,
    context: str,
) -> dict[str, str]:
    valid: dict[str, str] = {}
    for key_id, material in keys.items():
        if not isinstance(material, str):
            logger.warning(
                "encryption_registry_invalid_key_type context=%s key_id=%s",
                context,
                key_id,
            )
            continue
        if is_valid_fernet_key_material(material):
            valid[str(key_id)] = material.strip()
        else:
            logger.warning(
                "encryption_registry_invalid_fernet_material context=%s key_id=%s",
                context,
                key_id,
            )
    return valid
