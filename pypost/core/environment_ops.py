"""Pure helpers for environment model operations."""

from pypost.core.variable_name_validation import validate_variable_name
from pypost.models.models import Environment


def validate_environment_variable_name(name: str) -> tuple[bool, str]:
    """Validate a proposed environment variable name (Jinja2-compatible)."""
    return validate_variable_name(name)


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
        return False, "", "Name cannot be empty."
    if stripped == old_name:
        return True, old_name, ""
    if any(name == stripped for i, name in enumerate(existing_names) if i != row):
        return False, "", f'An environment named "{stripped}" already exists.'
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
