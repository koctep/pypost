"""Pure helpers for environment model operations."""
from __future__ import annotations

from pypost.core.environment_variable_validation import (
    validate_environment_variable_key,
)
from pypost.models.models import Environment
from pypost.core.environment_messages import (
    MSG_EMPTY_NAME,
    format_duplicate_environment_name,
)


def validate_environment_variable_name(name: str) -> tuple[bool, str]:
    """Validate a proposed environment variable name (Jinja2-compatible)."""
    result = validate_environment_variable_key(name)
    return result.accepted, result.message


def validate_environment_rename(
    new_name: str,
    old_name: str,
    existing_names: list[str],
    row: int,
) -> tuple[bool, str, str]:
    """Validate an environment rename.

    Returns:
        Tuple of (accepted, normalized_name, error_message).
        accepted is True for a successful rename or a same-name no-op.
        normalized_name is the stripped new name when accepted; empty on reject.
        error_message is set when accepted is False.
    """
    stripped = new_name.strip()
    if not stripped:
        return False, "", MSG_EMPTY_NAME
    if stripped == old_name:
        return True, old_name, ""
    if any(name == stripped for i, name in enumerate(existing_names) if i != row):
        return False, "", format_duplicate_environment_name(stripped)
    return True, stripped, ""


def clone_environments(environments: list[Environment]) -> list[Environment]:
    """Return a deep copy of an environment list for dialog editing."""
    return [env.model_copy(deep=True) for env in environments]


def clone_environment(source: Environment, new_name: str) -> Environment:
    """Build a new Environment copied from source with a new name and id.

    Variables are shallow-copied as a new dict; values are strings.
    """
    return Environment(
        name=new_name.strip(),
        variables=dict(source.variables),
        hidden_keys=set(source.hidden_keys),
        enable_mcp=source.enable_mcp,
    )
