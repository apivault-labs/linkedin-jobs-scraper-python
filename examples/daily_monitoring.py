"""
Daily LinkedIn Jobs monitoring with cross-run dedup.

Save the run to disk, deduplicate against yesterday's, and process only
the truly new jobs. Avoids paying twice for the same listing across days.

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/daily_monitoring.py
"""

import json
import os
from pathlib import Path

from linkedin_jobs import LinkedInJobsClient


SNAPSHOT_FILE = Path("yesterday_jobs.json")


def load_previous() -> list[dict]:
    if not SNAPSHOT_FILE.exists():
        return []
    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_today(jobs: list[dict]) -> None:
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)


def main() -> None:
    client = LinkedInJobsClient(timeout=1500)

    previous = load_previous()
    print(f"Previous run had {len(previous)} jobs")

    today, _ = client.search(
        keywords="senior product manager",
        location="United States",
        max_pages=5,
        remote=True,
        posted_within="week",
    )
    print(f"Today's run has {len(today)} jobs")

    # Drop jobs we already saw yesterday (matched by jobId)
    new_jobs = client.deduplicate_across_runs(previous, today)
    print(f"\n=== {len(new_jobs)} BRAND-NEW jobs (since yesterday) ===")

    for j in sorted(new_jobs,
                    key=lambda x: -(x.get("recruiterScore") or 0))[:10]:
        salary = j.get("salaryMedianUsd")
        salary_str = f"${salary:,.0f}" if salary else "n/a"
        print(f"\n• {j['companyName']} — {j['jobTitle'][:55]}")
        print(f"  jobId: {j.get('jobId')}  "
              f"posted: {j.get('postedDate', '?')}")
        print(f"  salary: {salary_str}  "
              f"score: {j.get('recruiterScore', 0)}")

    # Persist for tomorrow's diff
    save_today(today)
    print(f"\nSnapshot saved → {SNAPSHOT_FILE}")


if __name__ == "__main__":
    main()
