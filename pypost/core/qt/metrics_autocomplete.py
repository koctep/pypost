from __future__ import annotations

from pypost.core.metrics_registry import MetricsRegistry


class MetricsAutocompleteMixin:
    """Explicit delegation for variable autocomplete metrics."""

    _registry: MetricsRegistry

    def track_gui_variable_autocomplete_trigger(self, context: str) -> None:
        self._registry.track_gui_variable_autocomplete_trigger(context)

    def track_gui_variable_autocomplete_selection(self, context: str) -> None:
        self._registry.track_gui_variable_autocomplete_selection(context)

    def track_gui_variable_autocomplete_feedback(self, context: str, status: str) -> None:
        self._registry.track_gui_variable_autocomplete_feedback(context, status)

    def track_gui_variable_autocomplete_environment_refresh(self, context: str) -> None:
        self._registry.track_gui_variable_autocomplete_environment_refresh(context)
