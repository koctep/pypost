"""Pure sequence planning models and validation compiler (PYPOST-1134 / WS-6).

Provides Qt-free execution plans, step resolution, and static payload format
validation for WebSocket multi-step message sequences.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Sequence

from pypost.core.websocket_codec import validate_format
from pypost.models.websocket import (
    WebSocketMessagePreset,
    WebSocketSequence,
    WsMessageFormat,
)

logger = logging.getLogger(__name__)

__all__ = [
    "StepExecutionPlan",
    "SequenceExecutionPlan",
    "StepExecutionResult",
    "SequenceRunOutcome",
    "compile_sequence_plan",
]


@dataclass(frozen=True)
class StepExecutionPlan:
    """Executable plan for an individual sequence step."""

    step_index: int
    display_name: str
    format: WsMessageFormat
    raw_payload: str
    delay_ms: int
    preset_id: Optional[str] = None


@dataclass(frozen=True)
class SequenceExecutionPlan:
    """Compiled, immutable execution plan for a full WebSocket sequence."""

    sequence_id: str
    sequence_name: str
    steps: tuple[StepExecutionPlan, ...]
    is_valid: bool
    validation_error: Optional[str] = None


@dataclass(frozen=True)
class StepExecutionResult:
    """Outcome of an executed sequence step."""

    step_index: int
    display_name: str
    format: WsMessageFormat
    encoded_bytes_or_str: bytes | str
    byte_size: int
    delay_ms: int
    success: bool
    error_message: Optional[str] = None


@dataclass(frozen=True)
class SequenceRunOutcome:
    """Final outcome summary of a sequence execution run."""

    sequence_id: str
    sequence_name: str
    total_steps: int
    executed_steps: int
    status: str  # "completed", "stopped", "failed"
    failure_step_index: Optional[int] = None
    failure_reason: Optional[str] = None


def compile_sequence_plan(
    sequence: WebSocketSequence,
    presets: Sequence[WebSocketMessagePreset],
) -> SequenceExecutionPlan:
    """Compile a sequence definition and its preset library into an executable plan.

    Resolves preset references, verifies integrity, detects missing presets,
    and pre-validates inline and preset payloads.
    """
    logger.debug(
        "compile_sequence_plan_started seq_id=%s name=%s steps=%d presets=%d",
        sequence.id,
        sequence.name,
        len(sequence.steps),
        len(presets),
    )
    preset_map: dict[str, WebSocketMessagePreset] = {p.id: p for p in presets}
    compiled_steps: list[StepExecutionPlan] = []
    overall_is_valid = True
    first_error: Optional[str] = None

    for idx, step in enumerate(sequence.steps):
        if step.preset_id:
            preset = preset_map.get(step.preset_id)
            if preset is not None:
                display_name = preset.name
                fmt = preset.format
                raw_payload = preset.payload
                if "{{" not in raw_payload:
                    valid, err = validate_format(raw_payload, fmt)
                else:
                    valid, err = True, None
                if not valid:
                    overall_is_valid = False
                    logger.warning(
                        "compile_sequence_plan_step_invalid seq_id=%s step_index=%d "
                        "preset_id=%s format=%s error=%s",
                        sequence.id,
                        idx + 1,
                        step.preset_id,
                        fmt.value,
                        err,
                    )
                    if first_error is None:
                        first_error = (
                            f"Step {idx + 1} ({display_name}) payload format error: {err}"
                        )
            else:
                display_name = f"<missing preset: {step.preset_id}>"
                fmt = step.format
                raw_payload = ""
                overall_is_valid = False
                logger.warning(
                    "compile_sequence_plan_missing_preset seq_id=%s step_index=%d preset_id=%s",
                    sequence.id,
                    idx + 1,
                    step.preset_id,
                )
                if first_error is None:
                    first_error = f"Step {idx + 1} references missing preset '{step.preset_id}'"
        else:
            display_name = "<inline>"
            fmt = step.format
            raw_payload = step.inline_payload
            if "{{" not in raw_payload:
                valid, err = validate_format(raw_payload, fmt)
            else:
                valid, err = True, None
            if not valid:
                overall_is_valid = False
                logger.warning(
                    "compile_sequence_plan_step_invalid seq_id=%s step_index=%d format=%s error=%s",
                    sequence.id,
                    idx + 1,
                    fmt.value,
                    err,
                )
                if first_error is None:
                    first_error = f"Step {idx + 1} inline payload format error: {err}"

        compiled_steps.append(
            StepExecutionPlan(
                step_index=idx,
                display_name=display_name,
                format=fmt,
                raw_payload=raw_payload,
                delay_ms=step.delay_ms,
                preset_id=step.preset_id,
            )
        )

    logger.info(
        "compile_sequence_plan_completed seq_id=%s is_valid=%s steps=%d",
        sequence.id,
        overall_is_valid,
        len(compiled_steps),
    )
    return SequenceExecutionPlan(
        sequence_id=sequence.id,
        sequence_name=sequence.name,
        steps=tuple(compiled_steps),
        is_valid=overall_is_valid,
        validation_error=first_error,
    )
