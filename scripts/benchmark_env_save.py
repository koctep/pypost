#!/usr/bin/env python3
"""Local profiling harness for environment save with many hidden keys (PYPOST-534)."""

from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pypost.core.environment_variables_adapter import EnvironmentVariablesAdapter
from pypost.models.models import Environment


def _build_environment(hidden_key_count: int) -> Environment:
    variables = {f"SECRET_{i:03d}": f"value-{i}" for i in range(hidden_key_count)}
    variables["VISIBLE"] = "public"
    hidden_keys = {f"SECRET_{i:03d}" for i in range(hidden_key_count)}
    return Environment(
        id="bench-local",
        name="BenchLocal",
        variables=variables,
        hidden_keys=hidden_keys,
    )


def _median_seconds(samples: list[float]) -> float:
    return statistics.median(samples) if samples else 0.0


def _run_phase(
    adapter: EnvironmentVariablesAdapter,
    env: Environment,
    *,
    iterations: int,
    clear_cache: bool,
) -> tuple[float, int, int]:
    durations: list[float] = []
    encrypted_total = 0
    reused_total = 0
    for _ in range(iterations):
        if clear_cache:
            adapter.clear_persisted_state()
        start = time.perf_counter()
        _payload, stats = adapter.serialize_environment(env)
        durations.append(time.perf_counter() - start)
        encrypted_total = stats.encrypted_count
        reused_total = stats.reused_count
    return _median_seconds(durations), encrypted_total, reused_total


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Profile environment serialize with many hidden keys.",
    )
    parser.add_argument(
        "--keys",
        type=int,
        default=120,
        help="Number of hidden keys (default: 120)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Iterations per phase (default: 3)",
    )
    args = parser.parse_args(argv)

    if args.keys < 1:
        parser.error("--keys must be at least 1")
    if args.iterations < 1:
        parser.error("--iterations must be at least 1")

    os.environ.setdefault("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    if not os.environ.get("PYPOST_ENV_ENCRYPTION_KEY"):
        try:
            from cryptography.fernet import Fernet
        except ImportError:
            print("cryptography package required; install project dependencies first.", file=sys.stderr)
            return 1
        os.environ["PYPOST_ENV_ENCRYPTION_KEY"] = Fernet.generate_key().decode("utf-8")

    adapter = EnvironmentVariablesAdapter()
    env = _build_environment(args.keys)

    first_s, first_enc, first_reuse = _run_phase(
        adapter,
        env,
        iterations=1,
        clear_cache=True,
    )
    first_payload, _ = adapter.serialize_environment(env)
    adapter.remember_environment_state(env.id, first_payload["variables"], dict(env.variables))

    reuse_s, reuse_enc, reuse_reuse = _run_phase(
        adapter,
        env,
        iterations=args.iterations,
        clear_cache=False,
    )
    full_s, full_enc, full_reuse = _run_phase(
        adapter,
        env,
        iterations=args.iterations,
        clear_cache=True,
    )

    speedup = full_s / reuse_s if reuse_s > 0 else 0.0
    print(f"hidden_keys={args.keys} iterations={args.iterations}")
    print(f"first_save_ms={first_s * 1000:.2f} encrypted={first_enc} reused={first_reuse}")
    print(f"reuse_second_save_ms={reuse_s * 1000:.2f} encrypted={reuse_enc} reused={reuse_reuse}")
    print(f"full_reencrypt_ms={full_s * 1000:.2f} encrypted={full_enc} reused={full_reuse}")
    print(f"speedup_full_over_reuse={speedup:.2f}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
