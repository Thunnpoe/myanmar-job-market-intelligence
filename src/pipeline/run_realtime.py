"""Continuously synchronize public JobNet and MyJobs postings.

This provides polling-based, near-real-time updates. A new cycle starts only
after the previous one completes, so collections never overlap.
"""
import time
from datetime import datetime

from config.settings import MAX_LISTING_PAGES, SYNC_INTERVAL_MINUTES
from src.database.mongo import ensure_indexes
from src.pipeline.run_collection import collect_jobnet, collect_myjobs


def timestamp():
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def run_sync_cycle():
    print(f"\n[{timestamp()}] Starting job-market sync")
    ensure_indexes()

    # MyJobs runs first so it is not blocked by the longer initial JobNet load.
    try:
        print("MyJobs result:", collect_myjobs(MAX_LISTING_PAGES))
    except Exception as error:
        print("MyJobs cycle failed:", error)

    try:
        print("JobNet result:", collect_jobnet())
    except Exception as error:
        print("JobNet cycle failed:", error)

    print(f"[{timestamp()}] Sync cycle completed")


def main():
    interval_seconds = max(5, SYNC_INTERVAL_MINUTES) * 60
    print(
        "Near-real-time collector started. "
        f"Polling interval: {SYNC_INTERVAL_MINUTES} minutes. Press Ctrl+C to stop."
    )
    try:
        while True:
            cycle_started = time.monotonic()
            run_sync_cycle()
            elapsed = time.monotonic() - cycle_started
            wait_seconds = max(60, interval_seconds - elapsed)
            print(f"Next check in {wait_seconds / 60:.1f} minutes.")
            time.sleep(wait_seconds)
    except KeyboardInterrupt:
        print("\nNear-real-time collector stopped.")


if __name__ == "__main__":
    main()
