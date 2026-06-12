#!/usr/bin/env python3
"""Apply debt summary fixes via Jira REST API (fallback when MCP batching is slow).

Requires env: JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN
Or run via Atlassian MCP jira_update_issue in batches of 15-20.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[1]
FIXES = ROOT / "scripts" / "debt_summary_fixes.json"
PROGRESS = ROOT / "scripts" / "debt_summary_update_progress.json"
BATCH_SIZE = 18


def _auth() -> tuple[str, str, str]:
    url = os.environ.get("JIRA_URL", "https://pypost.atlassian.net")
    email = os.environ.get("JIRA_EMAIL") or os.environ.get("ATLASSIAN_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN") or os.environ.get("ATLASSIAN_API_TOKEN")
    if not email or not token:
        print("Set JIRA_EMAIL and JIRA_API_TOKEN", file=sys.stderr)
        sys.exit(1)
    return url.rstrip("/"), email, token


def _update_one(base: str, auth: tuple[str, str], key: str, summary: str) -> tuple[str, bool, str]:
    if requests is None:
        return key, False, "requests not installed"
    url = f"{base}/rest/api/2/issue/{key}"
    resp = requests.put(
        url,
        auth=auth,
        json={"fields": {"summary": summary}},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    if resp.status_code in (200, 204):
        return key, True, ""
    return key, False, f"{resp.status_code}: {resp.text[:200]}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-batch", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    fixes: dict[str, str] = json.loads(FIXES.read_text(encoding="utf-8"))
    keys = list(fixes.keys())
    batches = [keys[i : i + BATCH_SIZE] for i in range(0, len(keys), BATCH_SIZE)]

    updated = 0
    failed: list[dict[str, str]] = []

    if args.dry_run:
        print(f"Would update {len(fixes)} issues in {len(batches)} batches")
        return

    base, email, token = _auth()
    auth = (email, token)

    for batch_num in range(args.start_batch, len(batches)):
        batch = batches[batch_num]
        print(f"Batch {batch_num}/{len(batches)-1}: {len(batch)} issues")
        with ThreadPoolExecutor(max_workers=BATCH_SIZE) as pool:
            futures = {
                pool.submit(_update_one, base, auth, k, fixes[k]): k for k in batch
            }
            for fut in as_completed(futures):
                key, ok, err = fut.result()
                if ok:
                    updated += 1
                else:
                    failed.append({"key": key, "error": err})
        time.sleep(0.5)

    result = {"updated_count": updated, "failed": failed, "total": len(fixes)}
    PROGRESS.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
