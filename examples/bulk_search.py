"""
Bulk LinkedIn Jobs search + read aggregate KV records.

The actor writes three free KV records on bulk runs:
  - SUMMARY                  — run-level metrics
  - TOP_HIRING_COMPANIES     — top 20 companies sorted by job count
  - TOP_JOBS                 — top 20 jobs sorted by recruiterScore

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/bulk_search.py
"""

from linkedin_jobs import LinkedInJobsClient


def main() -> None:
    client = LinkedInJobsClient(timeout=1500)
    print(f"Estimated cost: ${client.estimate_cost(250):.2f} for ~250 jobs\n")

    jobs, summary = client.search(
        keywords="data engineer",
        location="United States",
        max_pages=10,
        remote=True,
        posted_within="month",
    )
    print(f"Got {len(jobs)} jobs")

    if summary:
        print(f"\n--- SUMMARY ---")
        print(f"  Total companies: {summary.get('unique_companies')}")
        print(f"  Avg salary: ${summary.get('salary_median_usd', 0):,.0f}")
        print(f"  P25-P75: ${summary.get('salary_p25_usd', 0):,.0f} – "
              f"${summary.get('salary_p75_usd', 0):,.0f}")
        print(f"  Remote-friendly: {summary.get('remote_friendly_pct', 0)}%")
        print(f"  Salary disclosed: {summary.get('salary_disclosed_pct', 0)}%")
        print(f"  Open today: {summary.get('fresh_today_count', 0)}")
        print(f"\n  Top skills demanded:")
        for s in (summary.get("top_skills_demanded") or [])[:10]:
            print(f"    {s['name']:20}  {s['count']}")

    top_companies = client.get_top_hiring_companies()
    if top_companies:
        print(f"\n--- TOP 10 HIRING COMPANIES ---")
        for c in top_companies["top_companies"][:10]:
            print(f"\n{c['companyName']} ({c['jobs_count']} roles, "
                  f"max recruiterScore={c['max_recruiterScore']})")
            if c.get("avg_salary_usd"):
                print(f"  avg salary: ${c['avg_salary_usd']:,.0f}")
            top_skill = (c.get("top_skills") or [{"name": "?"}])[0]["name"]
            print(f"  top skill: {top_skill}")
            print(f"  pitch: {c['outreachPitch'][:100]}...")

    top_jobs = client.get_top_jobs()
    if top_jobs:
        print(f"\n--- TOP 5 JOBS (by recruiterScore) ---")
        for j in top_jobs["top_jobs"][:5]:
            print(f"\n{j['companyName']:25}  {j['jobTitle'][:55]}")
            print(f"  score={j['recruiterScore']}  "
                  f"city={j.get('city', '?')}, {j.get('state', '?')}  "
                  f"workMode={j.get('workMode', '?')}")


if __name__ == "__main__":
    main()
