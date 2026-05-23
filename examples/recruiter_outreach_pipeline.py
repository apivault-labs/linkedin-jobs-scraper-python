"""
Full recruitment-tech B2B outreach pipeline.

Workflow:
  1. Search across multiple keywords
  2. Filter to scorching-tier companies in pay-transparency states
  3. For each company, generate 3 outreach variants (consultative,
     aggressive, referral)
  4. Write per-prospect mailto URLs ready to paste into a sequence

Run as a daily cron / GitHub Action. Pipe TOP_HIRING_COMPANIES.json to
your sales team's Slack channel.

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/recruiter_outreach_pipeline.py
"""

import json

from linkedin_jobs import LinkedInJobsClient


SEARCHES = [
    {"keywords": "senior software engineer", "experience_level": "mid_senior"},
    {"keywords": "engineering manager",      "experience_level": "director"},
    {"keywords": "vp engineering",           "experience_level": "executive"},
]


def main() -> None:
    client = LinkedInJobsClient(timeout=1500)

    all_companies: dict[str, dict] = {}

    for s in SEARCHES:
        print(f"\nSearching: {s['keywords']!r} "
              f"(level={s['experience_level']})")
        jobs, _ = client.search(
            location="United States",
            max_pages=5,
            remote=True,
            posted_within="week",
            min_recruiter_score=40,
            **s,
        )
        # Filter to highest-intent prospects only
        prospects = client.filter_by_recruiter_tier(jobs,
                                                     "scorching", "hot")

        # Aggregate per company
        top = client.get_top_hiring_companies()
        if top:
            for c in top.get("top_companies") or []:
                if c["companyName"] not in all_companies:
                    all_companies[c["companyName"]] = c
                else:
                    # Merge: update if higher recruiterScore
                    existing = all_companies[c["companyName"]]
                    if c["max_recruiterScore"] > existing["max_recruiterScore"]:
                        all_companies[c["companyName"]] = c

        print(f"  → {len(prospects)} hot prospects, "
              f"{len(top.get('top_companies', [])) if top else 0} companies in TOP")

    # Sort companies across all searches by max_recruiterScore
    rolled_up = sorted(
        all_companies.values(),
        key=lambda c: c["max_recruiterScore"],
        reverse=True,
    )[:20]

    print(f"\n{'=' * 70}")
    print(f"Aggregate top {len(rolled_up)} prospects across searches:")
    print(f"{'=' * 70}")

    out = []
    for c in rolled_up:
        variants = c.get("outreachPitchVariants") or {}
        links = c.get("outreachLinks") or {}
        prospect = {
            "company": c["companyName"],
            "openRoles": c["jobs_count"],
            "score": c["max_recruiterScore"],
            "tier": c.get("max_recruiterTier"),
            "topSkills": [s["name"] for s in c.get("top_skills") or []][:3],
            "pitches": {
                "consultative": variants.get("consultative"),
                "aggressive": variants.get("aggressive"),
                "referral": variants.get("referral"),
            },
            "linkedin_role_owner": links.get("linkedin_role_owner_search_url"),
            "mailto": links.get("email_template_url_with_pitch"),
        }
        out.append(prospect)
        print(f"\n• {c['companyName']:30}  score={c['max_recruiterScore']:3}  "
              f"{c['jobs_count']} open  tier={c.get('max_recruiterTier')}")
        if variants.get("aggressive"):
            print(f"  aggressive: {variants['aggressive'][:120]}...")

    with open("hot_prospects.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to hot_prospects.json — paste into your sequence")


if __name__ == "__main__":
    main()
