"""
Tech-skills demand report — quantify which skills are most in demand
across LinkedIn listings, broken down by job category.

Use cases:
  - Tech-bootcamp curriculum design
  - Career-tools (which skills should I learn?)
  - Investment / market research

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/tech_skills_demand_report.py
"""

from collections import Counter, defaultdict

from linkedin_jobs import LinkedInJobsClient


SEARCHES = [
    ("software engineer", "engineering"),
    ("data scientist",    "data_science"),
    ("product manager",   "product"),
    ("ux designer",       "design"),
]


def main() -> None:
    client = LinkedInJobsClient(timeout=1500)

    by_category: dict[str, Counter] = defaultdict(Counter)

    for keywords, category in SEARCHES:
        print(f"Searching {keywords!r}...")
        jobs, _ = client.search(
            keywords=keywords,
            location="United States",
            max_pages=5,
            posted_within="month",
        )
        for j in jobs:
            for skill in (j.get("skillsRequired") or []):
                by_category[category][skill] += 1

    print(f"\n{'=' * 70}")
    print(f"Tech skills demand by category")
    print(f"{'=' * 70}")

    for category, counts in by_category.items():
        total = sum(counts.values())
        print(f"\n{category.replace('_', ' ').upper()} "
              f"({total} skill mentions across listings):")
        print(f"  {'Skill':<25} {'Count':>8}  {'% of mentions':>14}")
        for skill, count in counts.most_common(15):
            pct = 100 * count / total if total else 0
            print(f"  {skill:<25} {count:>8}  {pct:>13.1f}%")


if __name__ == "__main__":
    main()
