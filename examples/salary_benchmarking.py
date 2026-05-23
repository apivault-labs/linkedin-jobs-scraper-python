"""
Salary benchmarking — compare median compensation by seniority and
location across recent LinkedIn listings.

Use cases:
  - Compensation strategy decisions (hiring managers)
  - Candidate negotiation prep
  - Comp-tech / equity-comp tools

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/salary_benchmarking.py
"""

from collections import defaultdict
from statistics import mean, median

from linkedin_jobs import LinkedInJobsClient


SCENARIOS = [
    {"label": "Bay Area Senior SWE",
     "keywords": "senior software engineer",
     "location": "San Francisco Bay Area",
     "experience_level": "mid_senior"},
    {"label": "NYC Senior Backend",
     "keywords": "senior backend engineer",
     "location": "New York, NY",
     "experience_level": "mid_senior"},
    {"label": "Austin Senior SWE",
     "keywords": "senior software engineer",
     "location": "Austin, Texas",
     "experience_level": "mid_senior"},
    {"label": "Remote Senior SWE",
     "keywords": "senior software engineer",
     "location": "United States",
     "experience_level": "mid_senior",
     "remote": True},
]


def stats(values):
    if not values:
        return None
    s = sorted(values)
    return {
        "n": len(values),
        "min": int(min(values)),
        "p25": int(s[len(s) // 4]) if len(s) >= 4 else None,
        "median": int(median(values)),
        "p75": int(s[3 * len(s) // 4]) if len(s) >= 4 else None,
        "max": int(max(values)),
        "mean": int(mean(values)),
    }


def main() -> None:
    client = LinkedInJobsClient(timeout=1500)

    print(f"{'Scenario':30} {'N':>4}  {'Median':>10}  {'P25-P75':>20}")
    print("-" * 70)

    for sc in SCENARIOS:
        label = sc.pop("label")
        jobs, _ = client.search(
            **sc,
            max_pages=5,
            posted_within="month",
            only_with_salary=True,  # crucial — drop listings without salary
        )
        salaries = [j.get("salaryMedianUsd") for j in jobs
                    if j.get("salaryMedianUsd")]
        st = stats(salaries)
        if st:
            p25_75 = f"${st['p25']:,}-${st['p75']:,}" if st['p25'] else "n/a"
            print(f"{label:30} {st['n']:>4}  "
                  f"${st['median']:>9,}  {p25_75:>20}")

            # Salary tier distribution
            tier_counts = defaultdict(int)
            for j in jobs:
                if j.get("salary_tier"):
                    tier_counts[j["salary_tier"]] += 1
            tier_str = ", ".join(f"{k}:{v}" for k, v in
                                  sorted(tier_counts.items()))
            print(f"{'':30}      tiers: {tier_str}")

            # Equity %
            with_eq = sum(1 for j in jobs if j.get("mentions_equity"))
            print(f"{'':30}      with equity: {with_eq}/{len(jobs)} "
                  f"({100 * with_eq // max(len(jobs), 1)}%)")
        else:
            print(f"{label:30}  no salary data found")


if __name__ == "__main__":
    main()
