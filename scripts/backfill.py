#!/usr/bin/env python3
"""
当前公开接口只能拿到实时状态，无法做历史补抓。
这个脚本的 backfill 定义为：按固定间隔重复采集若干次，用于本地快速积累样本。
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.collector import collect_once  # noqa: E402
from app.db import SessionLocal, init_db  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Repeat live collection to accumulate sample data.")
    parser.add_argument("--runs", type=int, default=5, help="How many collection runs to execute.")
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=120,
        help="Seconds to wait between runs.",
    )
    args = parser.parse_args()

    init_db()

    for index in range(args.runs):
        with SessionLocal() as db:
            stats = collect_once(db)
        print(
            f"[{index + 1}/{args.runs}] collected_at={stats.collected_at} "
            f"stores={stats.store_count} queue_ok={stats.queue_success_count} "
            f"queue_error={stats.queue_error_count}"
        )
        if index < args.runs - 1:
            time.sleep(args.interval_seconds)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
