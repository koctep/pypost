"""Subprocess stdio IPC test harness for MCP transports.

Encapsulates child process execution, non-blocking asynchronous stream
reading, response registry synchronization, and timeout enforcement.

Jira: PYPOST-1429
Architecture: ai-tasks/PYPOST-1429/20-architecture.md
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import threading
import time
from typing import Any, Callable, Sequence


class McpStdioHarness:
    """Subprocess stdio IPC test harness with asynchronous stream draining.

    Manages child process lifecycle, non-blocking background stdout/stderr
    reader worker threads, synchronized response collection, and bounded
    timeout enforcement. Prevents OS pipe deadlocks (>64KB buffers) and
    guarantees clean process cleanup.
    """

    def __init__(
        self,
        command: Sequence[str | Path] | str,
        *,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
        auto_start: bool = True,
    ) -> None:
        """Initialize the stdio harness with target command and execution options.

        Args:
            command: Command argument sequence (or shell string) to execute.
            cwd: Optional working directory for the child process.
            env: Optional environment dictionary override for the child process.
            auto_start: If True, automatically launches child process and worker threads.
        """
        self._command = command
        self._cwd = cwd
        self._env = env

        self.process: subprocess.Popen[bytes] | None = None
        self._t_out: threading.Thread | None = None
        self._t_err: threading.Thread | None = None

        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._stdin_lock = threading.Lock()
        self._stderr_lock = threading.Lock()

        self._responses: dict[Any, dict[str, Any]] = {}
        self._messages: list[dict[str, Any]] = []
        self._stderr_lines: list[str] = []
        self._stdout_decode_errors: list[str] = []

        if auto_start:
            self.start()

    def start(self) -> None:
        """Launch the child process and spawn asynchronous reader threads.

        Spawns child process with subprocess.PIPE on stdin, stdout, and stderr with
        bufsize=0. Starts dedicated daemon threads for stdout and stderr draining.

        Raises:
            RuntimeError: If the process is already running.
        """
        if self.is_alive:
            raise RuntimeError("Child process is already running")

        if isinstance(self._command, (list, tuple)):
            cmd: Sequence[str] | str = [str(arg) for arg in self._command]
            shell = False
        elif isinstance(self._command, Path):
            cmd = str(self._command)
            shell = False
        elif isinstance(self._command, str):
            cmd = self._command
            shell = True
        else:
            cmd = [str(arg) for arg in self._command]
            shell = False

        cwd = str(self._cwd) if self._cwd is not None else None

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            cwd=cwd,
            env=self._env,
            shell=shell,
        )

        self._t_out = threading.Thread(target=self._stdout_worker, daemon=True)
        self._t_err = threading.Thread(target=self._stderr_worker, daemon=True)
        self._t_out.start()
        self._t_err.start()

    def close_stdin(self) -> None:
        """Flush and close child process stdin to signal EOF.

        Safe to call multiple times or if stdin is already closed.
        """
        with self._stdin_lock:
            if (
                self.process is not None
                and self.process.stdin is not None
                and not self.process.stdin.closed
            ):
                try:
                    self.process.stdin.flush()
                except (BrokenPipeError, OSError):
                    pass
                try:
                    self.process.stdin.close()
                except (BrokenPipeError, OSError):
                    pass

    def stop(self, timeout: float = 5.0) -> int:
        """Stop child process gracefully with fallback to forceful termination.

        Closes stdin if open, waits up to timeout seconds for process exit. If the
        process does not exit within timeout, issues kill() and waits up to 2.0s.
        Joins background reader threads and returns the final process returncode.

        Args:
            timeout: Graceful exit timeout in seconds before issuing kill().

        Returns:
            The integer process returncode.
        """
        if self.process is None:
            return 0
        self.close_stdin()
        if self.process.poll() is None:
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                return self.kill(timeout=2.0)
        self._join_threads()
        return self.process.returncode if self.process.returncode is not None else 0

    def kill(self, timeout: float = 2.0) -> int:
        """Forcefully terminate the child process immediately.

        Issues process.kill(), waits up to timeout seconds, joins reader threads.

        Args:
            timeout: Maximum wait time in seconds after kill().

        Returns:
            The integer process returncode.
        """
        if self.process is None:
            return 0
        if self.process.poll() is None:
            try:
                self.process.kill()
            except OSError:
                pass
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                pass
        self._join_threads()
        return self.process.returncode if self.process.returncode is not None else -1

    def wait_for_exit(self, timeout: float = 5.0) -> int:
        """Wait for child process to terminate and return its exit code.

        Args:
            timeout: Maximum wait time in seconds before raising TimeoutError.

        Returns:
            The integer process returncode.

        Raises:
            TimeoutError: If the child process does not terminate within timeout.
            RuntimeError: If the child process was never started.
        """
        if self.process is None:
            raise RuntimeError("Child process was never started")
        try:
            retcode = self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"Process did not exit within {timeout}s") from exc
        self._join_threads()
        return retcode

    def __enter__(self) -> McpStdioHarness:
        """Context manager entry: starts process if not running, returns self."""
        if self.process is None:
            self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit: guarantees stop() is executed, cleaning up all resources."""
        self.stop()

    @property
    def is_alive(self) -> bool:
        """Return True if the child process is currently running."""
        return self.process is not None and self.process.poll() is None

    @property
    def returncode(self) -> int | None:
        """Return the process returncode if terminated, or None if still running."""
        if self.process is None:
            return None
        return self.process.poll()

    def send_raw(self, data: bytes | str) -> None:
        """Transmit raw bytes or string to child process stdin and flush immediately.

        Args:
            data: Raw string or bytes to write.

        Raises:
            RuntimeError: If process is not running or stdin is closed.
        """
        if not self.is_alive or self.process is None or self.process.stdin is None:
            raise RuntimeError("Child process is not running")
        with self._stdin_lock:
            if self.process.stdin.closed:
                raise RuntimeError("Child process stdin is closed")
            if isinstance(data, str):
                raw = data.encode("utf-8")
            elif isinstance(data, (bytes, bytearray)):
                raw = bytes(data)
            else:
                raise TypeError(f"Expected bytes or str, got {type(data).__name__}")
            try:
                self.process.stdin.write(raw)
                self.process.stdin.flush()
            except (BrokenPipeError, OSError) as exc:
                raise RuntimeError(f"Failed to write to stdin: {exc}") from exc

    def send_message(self, message: dict[str, Any] | str) -> None:
        """Transmit a JSON-RPC message dictionary (or JSON string) to stdin and flush.

        Args:
            message: Dictionary to serialize to JSON or raw JSON string.

        Raises:
            RuntimeError: If process is not running or stdin is closed.
        """
        if isinstance(message, dict):
            line = json.dumps(message) + "\n"
        elif isinstance(message, str):
            line = message if message.endswith("\n") else message + "\n"
        else:
            raise TypeError(f"Expected dict or str, got {type(message).__name__}")
        self.send_raw(line)

    def send_request(
        self,
        request_id: Any,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Convenience method to format and transmit a standard JSON-RPC 2.0 request.

        Args:
            request_id: Identifier for request/response correlation.
            method: JSON-RPC method name.
            params: Optional parameter mapping.
        """
        msg: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params is not None:
            msg["params"] = params
        self.send_message(msg)

    def send_notification(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Convenience method to format and transmit a standard JSON-RPC 2.0 notification.

        Args:
            method: JSON-RPC method name.
            params: Optional parameter mapping.
        """
        msg: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params is not None:
            msg["params"] = params
        self.send_message(msg)

    def get_response(self, request_id: Any) -> dict[str, Any] | None:
        """Look up a received response by ID in a thread-safe manner.

        Args:
            request_id: Identifier to look up.

        Returns:
            Response dictionary if received, or None if not yet arrived.
        """
        with self._lock:
            res = self._responses.get(request_id)
            return dict(res) if res is not None else None

    def get_all_responses(self) -> dict[Any, dict[str, Any]]:
        """Return a thread-safe copy of all collected response dictionaries keyed by ID."""
        with self._lock:
            return {k: dict(v) for k, v in self._responses.items()}

    def get_messages(self) -> list[dict[str, Any]]:
        """Return a thread-safe ordered list copy of all received JSON-RPC messages."""
        with self._lock:
            return [dict(m) for m in self._messages]

    def get_stderr(self) -> str:
        """Return all captured standard error output as a single decoded string."""
        with self._stderr_lock:
            return "".join(self._stderr_lines)

    def wait_for_response(
        self,
        request_id: Any,
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        """Wait until a response matching request_id arrives or timeout expires.

        Uses thread condition synchronization to wake up immediately when the response
        is decoded by the stdout worker.

        Args:
            request_id: Expected response identifier.
            timeout: Maximum wait time in seconds.

        Returns:
            The matched response dictionary.

        Raises:
            TimeoutError: If the response is not received within timeout seconds.
        """
        deadline = time.time() + timeout
        with self._condition:
            while request_id not in self._responses:
                remaining = deadline - time.time()
                if remaining <= 0:
                    break
                self._condition.wait(timeout=remaining)
            if request_id in self._responses:
                return dict(self._responses[request_id])

        raise TimeoutError(
            f"Waiting for response id={request_id!r} timed out after {timeout}s. "
            f"Stderr: {self.get_stderr()}"
        )

    def wait_for_responses(
        self,
        total_count: int,
        timeout: float = 15.0,
    ) -> dict[Any, dict[str, Any]]:
        """Wait until at least total_count responses have arrived or timeout expires.

        Args:
            total_count: Minimum number of responses expected in the registry.
            timeout: Maximum wait time in seconds.

        Returns:
            Thread-safe copy of all collected responses.

        Raises:
            TimeoutError: If total_count responses are not received within timeout seconds.
        """
        deadline = time.time() + timeout
        with self._condition:
            while len(self._responses) < total_count:
                remaining = deadline - time.time()
                if remaining <= 0:
                    break
                self._condition.wait(timeout=remaining)
            if len(self._responses) >= total_count:
                return {k: dict(v) for k, v in self._responses.items()}

        raise TimeoutError(
            f"Waiting for {total_count} responses timed out after {timeout}s "
            f"(got {len(self._responses)}). Stderr: {self.get_stderr()}"
        )

    def wait_for_predicate(
        self,
        predicate: Callable[[McpStdioHarness], bool],
        timeout: float = 5.0,
        interval: float = 0.05,
    ) -> None:
        """Wait until custom condition predicate returns True or timeout expires.

        Args:
            predicate: Callable taking self and returning bool.
            timeout: Maximum wait time in seconds.
            interval: Poll interval in seconds if condition variable is not triggered.

        Raises:
            TimeoutError: If predicate does not evaluate to True within timeout seconds.
        """
        deadline = time.time() + timeout
        with self._condition:
            while not predicate(self):
                remaining = deadline - time.time()
                if remaining <= 0:
                    break
                self._condition.wait(timeout=min(interval, remaining))
            if predicate(self):
                return

        raise TimeoutError(
            f"Predicate did not evaluate to True within {timeout}s. "
            f"Stderr: {self.get_stderr()}"
        )

    def _join_threads(self) -> None:
        if self._t_out is not None and self._t_out.is_alive():
            self._t_out.join(timeout=1.0)
        if self._t_err is not None and self._t_err.is_alive():
            self._t_err.join(timeout=1.0)

    def _stdout_worker(self) -> None:
        if self.process is None or self.process.stdout is None:
            return
        for raw_line in iter(self.process.stdout.readline, b""):
            line = raw_line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line.decode("utf-8"))
                if isinstance(msg, dict):
                    with self._condition:
                        self._messages.append(msg)
                        if "id" in msg:
                            self._responses[msg["id"]] = msg
                        self._condition.notify_all()
            except Exception as exc:
                with self._lock:
                    self._stdout_decode_errors.append(str(exc))
                with self._stderr_lock:
                    self._stderr_lines.append(f"stdout decode error: {exc}\n")

    def _stderr_worker(self) -> None:
        if self.process is None or self.process.stderr is None:
            return
        for raw_line in iter(self.process.stderr.readline, b""):
            text = raw_line.decode("utf-8", errors="replace")
            with self._stderr_lock:
                self._stderr_lines.append(text)
