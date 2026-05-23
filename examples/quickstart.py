"""
Quickstart: search LinkedIn Jobs and print the top 5 prospects.

    pip install -r requirements.txt
    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/quickstart.py
"""

from linkedin_jobs import LinkedInJobsClient


def main() -> None:
    client = LinkedInJobsClient()  # picks up APIFY_API_TOKEN from env

    jobs, summary = client.search(
        keywords="senior software engineer",
        location="United States",
        max_pages=2,
        remote=True,
        posted_within="week",
    )

    print(f"\nTotal: {len(jobs)} jobs")
    if summary:
        print(f"  Avg salary: ${summary.get('salary_median_usd', 0):,.0f}")
        print(f"  Remote-friendly: {summary.get('remote_friendly_pct', 0)}%")
        print(f"  Lead-tier breakdown: {summary.get('by_recruiter_tier', {})}")

    print("\n=== Top 5 prospects (by recruiterScore) ===")
    top5 = sorted(jobs,
                  key=lambda j: -(j.get("recruiterScore") or 0))[:5]
    for j in top5:
        salary = j.get("salaryMedianUsd")
        salary_str = f"${salary:,.0f}" if salary else "n/a"
        print(f"\n{j['companyName']} — {j['jobTitle'][:60]}")
        print(f"  recruiterScore: {j.get('recruiterScore', 0)} "
              f"({j.get('recruiterTier', '?')})")
        print(f"  salary: {salary_str} ({j.get('salary_tier', '?')})")
        print(f"  freshness: {j.get('freshness_tier', '?')}, "
              f"workMode: {j.get('workMode', '?')}")
        skills = (j.get("skillsRequired") or [])[:5]
        if skills:
            print(f"  skills: {', '.join(skills)}")
        for r in (j.get("recruiterScoreReasons") or [])[:3]:
            print(f"    + {r}")


if __name__ == "__main__":
    main()
