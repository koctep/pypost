"""Pure helpers for environment model operations."""

from pypost.models.models import Environment


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
