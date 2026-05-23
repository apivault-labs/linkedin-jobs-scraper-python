"""
Export LinkedIn Jobs to CSV ready for HubSpot / Pipedrive / Salesforce
import.

Two ways to do this:
  1. Server-side: pass `export_format="csv"` to `search()`.
     The actor returns rows already shaped for CRM import (40 columns flat).
  2. Client-side: keep the rich JSON and write only the columns you need.

Both shown below. Server-side is recommended for most workflows.

    pip install -r requirements.txt
    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/export_to_csv.py > leads.csv
"""

import csv
import sys

from linkedin_jobs import LinkedInJobsClient


def server_side() -> None:
    """Recommended path — actor flattens automatically."""
    client = LinkedInJobsClient()
    rows, _ = client.search(
        keywords="engineering manager",
        location="United States",
        max_pages=5,
        remote=True,
        posted_within="week",
        min_recruiter_score=40,
        export_format="csv",  # ← key flag
    )
    if not rows:
        print("# (no results)", file=sys.stderr)
        return
    writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for r in rows:
        writer.writerow(r)


CLIENT_COLUMNS = [
    "companyName", "jobTitle", "city", "state", "isUsListing",
    "isRemoteListing", "workMode",
    "seniority_normalized", "jobCategory", "applyMethod",
    "salaryMedianUsd", "salary_tier", "daysSincePosted",
    "recruiterScore", "recruiterTier",
    "skillsCount", "top_skills",
    "mentions_equity", "mentions_remote_work",
    "pay_transparency_state", "pay_transparency_compliant",
    "jobCanonicalUrl",
]


def client_side() -> None:
    """Custom shape if you want fewer columns."""
    client = LinkedInJobsClient()
    jobs, _ = client.search(
        keywords="engineering manager",
        location="United States",
        max_pages=5,
        remote=True,
        posted_within="week",
    )
    writer = csv.DictWriter(sys.stdout, fieldnames=CLIENT_COLUMNS)
    writer.writeheader()
    for j in jobs:
        if not j.get("success"):
            continue
        parsed = j.get("parsedLocation") or {}
        skills = j.get("skillsRequired") or []
        writer.writerow({
            "companyName": j.get("companyName"),
            "jobTitle": j.get("jobTitle"),
            "city": parsed.get("city"),
            "state": parsed.get("state"),
            "isUsListing": j.get("isUsListing"),
            "isRemoteListing": j.get("isRemoteListing"),
            "workMode": j.get("workMode"),
            "seniority_normalized": j.get("seniority_normalized"),
            "jobCategory": j.get("jobCategory"),
            "applyMethod": j.get("applyMethod"),
            "salaryMedianUsd": j.get("salaryMedianUsd"),
            "salary_tier": j.get("salary_tier"),
            "daysSincePosted": j.get("daysSincePosted"),
            "recruiterScore": j.get("recruiterScore"),
            "recruiterTier": j.get("recruiterTier"),
            "skillsCount": j.get("skillsCount") or 0,
            "top_skills": ", ".join(skills[:5]) if skills else None,
            "mentions_equity": j.get("mentions_equity"),
            "mentions_remote_work": j.get("mentions_remote_work"),
            "pay_transparency_state": j.get("pay_transparency_state"),
            "pay_transparency_compliant": j.get("pay_transparency_compliant"),
            "jobCanonicalUrl": j.get("jobCanonicalUrl"),
        })


if __name__ == "__main__":
    # Default: server-side (recommended)
    server_side()
