"""Unit tests for McpStdioHarness subprocess stdio IPC test helper.

Jira: PYPOST-1429
Architecture: ai-tasks/PYPOST-1429/20-architecture.md
"""

from __future__ import annotations

import sys
import textwrap

import pytest

from tests.helpers.mcp_stdio_harness import McpStdioHarness

pytestmark = pytest.mark.timeout(30)


def test_harness_init_and_manual_start() -> None:
    """Harness supports auto_start=False, manual start(), and rejects duplicate start()."""
    cmd = [sys.executable, "-c", "import sys; sys.stdin.readline()"]
    harness = McpStdioHarness(cmd, auto_start=False)
    assert harness.is_alive is False
    assert harness.returncode is None

    try:
        harness.start()
        assert harness.is_alive is True
        with pytest.raises(RuntimeError, match="already running"):
            harness.start()
    finally:
        harness.stop()

    assert harness.is_alive is False


def test_harness_context_manager_lifecycle() -> None:
    """Context manager starts child process and ensures deterministic cleanup on exit."""
    script = textwrap.dedent("""
        import sys
        line = sys.stdin.readline()
        sys.stdout.write(line)
        sys.stdout.flush()
    """)
    cmd = [sys.executable, "-c", script]

    with McpStdioHarness(cmd) as harness:
        assert harness.is_alive is True
        harness.send_raw("ping\n")

    assert harness.is_alive is False
    assert harness.returncode == 0


def test_harness_request_response_dispatch() -> None:
    """Harness transmits JSON-RPC requests and synchronously awaits correlated responses."""
    script = textwrap.dedent("""
        import sys, json
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            req = json.loads(line)
            res = {
                "jsonrpc": "2.0",
                "id": req.get("id"),
                "result": {"echo_method": req.get("method")},
            }
            sys.stdout.write(json.dumps(res) + "\\n")
            sys.stdout.flush()
    """)
    cmd = [sys.executable, "-c", script]

    with McpStdioHarness(cmd) as harness:
        harness.send_request(request_id=1, method="test/echo")
        response = harness.wait_for_response(1, timeout=5.0)

        assert response["id"] == 1
        assert response["result"]["echo_method"] == "test/echo"
        assert harness.get_response(1) == response


def test_harness_batch_response_and_notifications() -> None:
    """Harness collects notification messages and awaits batches of numbered responses."""
    script = textwrap.dedent("""
        import sys, json
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            msg = json.loads(line)
            if "id" in msg:
                res = {"jsonrpc": "2.0", "id": msg["id"], "result": msg.get("params")}
                sys.stdout.write(json.dumps(res) + "\\n")
                sys.stdout.flush()
    """)
    cmd = [sys.executable, "-c", script]

    with McpStdioHarness(cmd) as harness:
        harness.send_notification("initialized", {"client": "test"})

        for seq in range(1, 6):
            harness.send_request(seq, "compute", {"seq": seq})

        responses = harness.wait_for_responses(5, timeout=5.0)
        assert len(responses) == 5
        for seq in range(1, 6):
            assert responses[seq]["result"]["seq"] == seq

        messages = harness.get_messages()
        assert len(messages) == 5
        assert harness.get_all_responses() == responses


def test_harness_large_payload_pipe_drain() -> None:
    """Background reader worker drains >64KB payloads without OS kernel pipe deadlock."""
    script = textwrap.dedent("""
        import sys, json
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            req = json.loads(line)
            payload = req["params"]["data"]
            res = {
                "jsonrpc": "2.0",
                "id": req["id"],
                "result": {"payload_len": len(payload), "head": payload[:5]},
            }
            sys.stdout.write(json.dumps(res) + "\\n")
            sys.stdout.flush()
    """)
    cmd = [sys.executable, "-c", script]

    with McpStdioHarness(cmd) as harness:
        large_payload = "Z" * 70000  # 70KB exceeds standard 64KB OS pipe buffer
        harness.send_request("large-1", "large_data", {"data": large_payload})

        response = harness.wait_for_response("large-1", timeout=5.0)
        assert response["id"] == "large-1"
        assert response["result"]["payload_len"] == 70000
        assert response["result"]["head"] == "ZZZZZ"


def test_harness_timeout_enforcement() -> None:
    """wait_for_response and wait_for_responses raise TimeoutError on expired deadlines."""
    script = textwrap.dedent("""
        import sys, time
        sys.stderr.write("server startup log\\n")
        sys.stderr.flush()
        for line in sys.stdin:
            time.sleep(2.0)
    """)
    cmd = [sys.executable, "-c", script]

    with McpStdioHarness(cmd) as harness:
        with pytest.raises(TimeoutError, match="timed out|never-delivered"):
            harness.wait_for_response("never-delivered", timeout=0.1)

        with pytest.raises(TimeoutError, match="timed out|responses"):
            harness.wait_for_responses(total_count=3, timeout=0.1)


def test_harness_stderr_collection() -> None:
    """Harness collects stderr stream asynchronously without blocking process execution."""
    script = textwrap.dedent("""
        import sys, json
        sys.stderr.write("diagnostic error: line 1\\n")
        sys.stderr.write("diagnostic error: line 2\\n")
        sys.stderr.flush()
        line = sys.stdin.readline()
        res = {"jsonrpc": "2.0", "id": 10, "result": "ok"}
        sys.stdout.write(json.dumps(res) + "\\n")
        sys.stdout.flush()
    """)
    cmd = [sys.executable, "-c", script]

    with McpStdioHarness(cmd) as harness:
        harness.send_raw('{"id": 10}\n')
        harness.wait_for_response(10, timeout=5.0)

        stderr_output = harness.get_stderr()
        assert "diagnostic error: line 1" in stderr_output
        assert "diagnostic error: line 2" in stderr_output


def test_harness_forceful_kill_hung_process() -> None:
    """Harness stop() terminates non-responsive child process via kill() when timeout expires."""
    script = textwrap.dedent("""
        import time
        while True:
            time.sleep(1.0)
    """)
    cmd = [sys.executable, "-c", script]

    with McpStdioHarness(cmd) as harness:
        assert harness.is_alive is True

    # On context exit, stop() forcefully kills the hanging process
    assert harness.is_alive is False
    assert harness.returncode is not None


def test_harness_wait_for_exit() -> None:
    """wait_for_exit returns exit code after child terminates or raises TimeoutError."""
    cmd = [sys.executable, "-c", "import sys; sys.exit(42)"]
    harness = McpStdioHarness(cmd)
    retcode = harness.wait_for_exit(timeout=5.0)
    assert retcode == 42
    assert harness.returncode == 42
    assert harness.is_alive is False


def test_harness_send_when_not_running() -> None:
    """Sending raw bytes or structured messages when harness is stopped raises RuntimeError."""
    cmd = [sys.executable, "-c", "import sys; sys.exit(0)"]
    harness = McpStdioHarness(cmd, auto_start=False)

    with pytest.raises(RuntimeError, match="not running|closed"):
        harness.send_raw("echo\n")

    with pytest.raises(RuntimeError, match="not running|closed"):
        harness.send_message({"jsonrpc": "2.0"})
