"""Observability helpers for inbound MCP validation failures (PYPOST-1100)."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import Any

from pypost.core.mcp_activity_log import McpActivityEntry, McpActivityLog
from pypost.core.mcp_tool_contract import (
    McpArgumentValidationError,
    validate_mcp_argument_values,
    validate_mcp_required_arguments,
)
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.models.models import McpToolParam

logger = logging.getLogger(__name__)


def record_mcp_call_outcome(
    metrics: MetricsTrackerProtocol,
    activity_log: McpActivityLog | None,
    method: str,
    outcome: str,
    tool_name: str,
    mcp_arg_count: int,
    http_status: int | None,
    detail: str | None,
    duration_ms: float,
) -> None:
    """Record the shared MCP response, duration, and activity outcomes."""
    metrics.track_mcp_response_sent(method, outcome)
    metrics.track_mcp_tool_call_duration(method, outcome, duration_ms / 1000.0)
    if activity_log is not None:
        activity_log.append(
            McpActivityEntry.new_call_tool(
                tool_name,
                outcome=outcome,
                mcp_arg_count=mcp_arg_count,
                http_status=http_status,
                detail=detail,
                duration_ms=duration_ms,
            )
        )


def validate_mcp_call_arguments(
    arguments: Mapping[str, Any],
    required_specs: Mapping[str, McpToolParam],
    value_specs: Mapping[str, McpToolParam],
    stage: str,
    transport: str,
    tool_name: str,
    method: str,
    mcp_arg_count: int,
    started: float,
    metrics: MetricsTrackerProtocol,
    activity_log: McpActivityLog | None,
) -> None:
    """Validate a call and record a safe outcome when the boundary rejects it."""
    try:
        validate_mcp_required_arguments(arguments, required_specs)
        validate_mcp_argument_values(arguments, value_specs)
    except McpArgumentValidationError as error:
        record_mcp_validation_failure(
            error,
            stage,
            transport,
            tool_name,
            method,
            mcp_arg_count,
            (time.perf_counter() - started) * 1000.0,
            metrics,
            activity_log,
        )
        raise


def record_mcp_validation_failure(
    error: McpArgumentValidationError,
    stage: str,
    transport: str,
    tool_name: str,
    method: str,
    mcp_arg_count: int,
    duration_ms: float,
    metrics: MetricsTrackerProtocol,
    activity_log: McpActivityLog | None,
) -> None:
    """Record one safe validation failure across the MCP observability surfaces."""
    logger.warning(
        "mcp_argument_validation_failed stage=%s transport=%s tool=%s param=%s "
        "expected_type=%s",
        stage,
        transport,
        tool_name,
        error.parameter_name,
        error.expected_type,
    )
    metrics.track_mcp_argument_validation_failure(
        stage, transport, error.expected_type
    )
    record_mcp_call_outcome(
        metrics,
        activity_log,
        method,
        "validation_error",
        tool_name,
        mcp_arg_count,
        None,
        str(error),
        duration_ms,
    )
