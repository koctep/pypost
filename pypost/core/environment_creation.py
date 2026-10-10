"""Admission and durable completion contract for workspace environment creation."""
from collections.abc import Callable

from pypost.models.models import Environment

EnvironmentCreationCompletion = Callable[[Environment | None, str | None], None]
CreateEnvironment = Callable[[Environment, EnvironmentCreationCompletion], bool]
