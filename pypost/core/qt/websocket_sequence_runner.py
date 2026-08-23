"""Qt asynchronous WebSocket sequence runner (PYPOST-1134 / WS-6).

Executes compiled SequenceExecutionPlan step-by-step with non-blocking QTimer
pacing, mid-run cancellation, and failure safety guards.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from PySide6.QtCore import QObject, QTimer, Signal

from pypost.core.template_service import TemplateService
from pypost.core.websocket_codec import encode_payload
from pypost.core.websocket_sequence import (
    SequenceExecutionPlan,
    SequenceRunOutcome,
    StepExecutionResult,
)

logger = logging.getLogger(__name__)

__all__ = ["WebSocketSequenceRunner"]


class WebSocketSequenceRunner(QObject):
    """Asynchronous, timer-paced executor for WebSocket sequences."""

    step_started = Signal(int, str)  # (step_index, display_name)
    step_completed = Signal(object)   # StepExecutionResult
    sequence_finished = Signal(object)  # SequenceRunOutcome

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._is_running: bool = False
        self._plan: Optional[SequenceExecutionPlan] = None
        self._controller: Any = None
        self._env_vars: dict[str, str] = {}
        self._current_step_index: int = 0
        self._executed_steps: int = 0
        self._template_service = TemplateService()

        self._pacing_timer = QTimer(self)
        self._pacing_timer.setSingleShot(True)
        self._pacing_timer.timeout.connect(self._execute_current_step)

    @property
    def is_running(self) -> bool:
        """True if a sequence is currently executing."""
        return self._is_running

    def run_sequence(
        self,
        plan: SequenceExecutionPlan,
        controller: Any,
        env_vars: Optional[dict[str, str]] = None,
    ) -> bool:
        """Begin asynchronous execution of a compiled sequence plan."""
        if self._is_running:
            logger.warning("sequence_runner_already_running")
            return False

        if not plan.is_valid:
            logger.warning(
                "sequence_runner_rejected_invalid_plan seq_id=%s error=%s",
                plan.sequence_id,
                plan.validation_error,
            )
            outcome = SequenceRunOutcome(
                sequence_id=plan.sequence_id,
                sequence_name=plan.sequence_name,
                total_steps=len(plan.steps),
                executed_steps=0,
                status="failed",
                failure_reason=plan.validation_error or "Sequence plan is invalid",
            )
            self.sequence_finished.emit(outcome)
            return False

        is_open = getattr(controller, "is_open", True)
        if not is_open:
            logger.warning(
                "sequence_runner_rejected_controller_closed seq_id=%s",
                plan.sequence_id,
            )
            outcome = SequenceRunOutcome(
                sequence_id=plan.sequence_id,
                sequence_name=plan.sequence_name,
                total_steps=len(plan.steps),
                executed_steps=0,
                status="failed",
                failure_reason="WebSocket session is not open",
            )
            self.sequence_finished.emit(outcome)
            return False

        if len(plan.steps) == 0:
            logger.info("sequence_runner_completed_empty seq_id=%s", plan.sequence_id)
            outcome = SequenceRunOutcome(
                sequence_id=plan.sequence_id,
                sequence_name=plan.sequence_name,
                total_steps=0,
                executed_steps=0,
                status="completed",
            )
            self.sequence_finished.emit(outcome)
            return True

        self._plan = plan
        self._controller = controller
        self._env_vars = dict(env_vars) if env_vars is not None else {}
        self._current_step_index = 0
        self._executed_steps = 0
        self._is_running = True

        logger.info(
            "sequence_runner_started seq_id=%s name=%s steps=%d",
            plan.sequence_id,
            plan.sequence_name,
            len(plan.steps),
        )
        self._schedule_step(0)
        return True

    def stop(self) -> None:
        """Cancel the active sequence execution without disconnecting the session."""
        if not self._is_running:
            return

        plan = self._plan
        logger.info(
            "sequence_runner_stopped_by_user seq_id=%s step=%d executed=%d",
            plan.sequence_id if plan else "",
            self._current_step_index,
            self._executed_steps,
        )
        self._pacing_timer.stop()
        self._is_running = False

        outcome = SequenceRunOutcome(
            sequence_id=plan.sequence_id if plan else "",
            sequence_name=plan.sequence_name if plan else "",
            total_steps=len(plan.steps) if plan else 0,
            executed_steps=self._executed_steps,
            status="stopped",
            failure_step_index=self._current_step_index,
        )
        self.sequence_finished.emit(outcome)

    def _schedule_step(self, step_idx: int) -> None:
        if not self._is_running or self._plan is None:
            return

        if step_idx >= len(self._plan.steps):
            self._is_running = False
            outcome = SequenceRunOutcome(
                sequence_id=self._plan.sequence_id,
                sequence_name=self._plan.sequence_name,
                total_steps=len(self._plan.steps),
                executed_steps=self._executed_steps,
                status="completed",
            )
            logger.info(
                "sequence_runner_completed seq_id=%s total_steps=%d executed=%d",
                self._plan.sequence_id,
                len(self._plan.steps),
                self._executed_steps,
            )
            self.sequence_finished.emit(outcome)
            return

        step = self._plan.steps[step_idx]
        logger.debug(
            "sequence_runner_scheduling_step seq_id=%s step=%d name=%s delay_ms=%d format=%s",
            self._plan.sequence_id,
            step.step_index,
            step.display_name,
            step.delay_ms,
            step.format.value,
        )
        self.step_started.emit(step.step_index, step.display_name)

        if step.delay_ms <= 0:
            QTimer.singleShot(0, self._execute_current_step)
        else:
            self._pacing_timer.start(step.delay_ms)

    def _execute_current_step(self) -> None:
        if not self._is_running or self._plan is None:
            return

        step_idx = self._current_step_index
        step = self._plan.steps[step_idx]

        is_open = getattr(self._controller, "is_open", True)
        if not is_open:
            self._is_running = False
            logger.error(
                "sequence_runner_step_disconnected seq_id=%s step=%d",
                self._plan.sequence_id,
                step_idx,
            )
            outcome = SequenceRunOutcome(
                sequence_id=self._plan.sequence_id,
                sequence_name=self._plan.sequence_name,
                total_steps=len(self._plan.steps),
                executed_steps=self._executed_steps,
                status="failed",
                failure_step_index=step_idx,
                failure_reason="Session disconnected during sequence execution",
            )
            self.sequence_finished.emit(outcome)
            return

        raw_payload = step.raw_payload
        if self._env_vars and raw_payload:
            try:
                payload = self._template_service.render_string(raw_payload, self._env_vars)
            except Exception:
                payload = raw_payload
        else:
            payload = raw_payload

        try:
            encoded = encode_payload(payload, step.format)
        except Exception as exc:
            self._is_running = False
            logger.error(
                "sequence_runner_step_encoding_failed seq_id=%s step=%d format=%s error=%s",
                self._plan.sequence_id,
                step_idx,
                step.format.value,
                exc,
            )
            outcome = SequenceRunOutcome(
                sequence_id=self._plan.sequence_id,
                sequence_name=self._plan.sequence_name,
                total_steps=len(self._plan.steps),
                executed_steps=self._executed_steps,
                status="failed",
                failure_step_index=step_idx,
                failure_reason=f"Step {step_idx + 1} encoding error: {exc}",
            )
            self.sequence_finished.emit(outcome)
            return

        try:
            if isinstance(encoded, bytes):
                self._controller.send_binary(encoded)
                byte_size = len(encoded)
            else:
                self._controller.send_text(encoded)
                byte_size = len(encoded.encode("utf-8"))
        except Exception as exc:
            self._is_running = False
            logger.error(
                "sequence_runner_step_send_failed seq_id=%s step=%d error=%s",
                self._plan.sequence_id,
                step_idx,
                exc,
            )
            outcome = SequenceRunOutcome(
                sequence_id=self._plan.sequence_id,
                sequence_name=self._plan.sequence_name,
                total_steps=len(self._plan.steps),
                executed_steps=self._executed_steps,
                status="failed",
                failure_step_index=step_idx,
                failure_reason=str(exc),
            )
            self.sequence_finished.emit(outcome)
            return

        logger.info(
            "sequence_runner_step_executed seq_id=%s step=%d name=%s "
            "format=%s bytes=%d delay_ms=%d",
            self._plan.sequence_id,
            step_idx,
            step.display_name,
            step.format.value,
            byte_size,
            step.delay_ms,
        )
        result = StepExecutionResult(
            step_index=step_idx,
            display_name=step.display_name,
            format=step.format,
            encoded_bytes_or_str=encoded,
            byte_size=byte_size,
            delay_ms=step.delay_ms,
            success=True,
        )
        self._executed_steps += 1
        self._current_step_index += 1
        self.step_completed.emit(result)
        self._schedule_step(self._current_step_index)
