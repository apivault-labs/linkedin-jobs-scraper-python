"""
LinkedIn Jobs Scraper — Python SDK

Official Python client for the apivault_labs/linkedin-jobs-scraper Apify
actor (v1.3). Real-time LinkedIn Jobs scraping with **15 layers of
recruitment intelligence** — 40+ enrichment fields per job — for $0.003
per job.

Returns per job:

- Core (LinkedIn): title, company, location, job type, description preview,
  posted date, salary, company logo, direct URL
- Salary parser: `salaryMinUsd`, `salaryMaxUsd`, `salaryMedianUsd`,
  `salary_tier` (entry/mid/senior/principal/unicorn), `salaryPeriod`,
  `salaryCurrency` — USD-normalized across hourly/daily/weekly/monthly
- Job freshness: `daysSincePosted`, `freshness_tier` (today/week/month/older)
- Work-mode classifier: `workMode` = remote / hybrid / onsite
- Skills extraction: 200+ tech terms (`skillsRequired[]`), `softSkills[]`,
  `certifications[]`
- Benefits parser: 14 boolean flags (401k, equity, visa sponsorship,
  unlimited PTO, signing bonus, ...)
- Seniority normalizer: intern → c-level
- Job category auto-detect: engineering/data_science/product/design/
  sales/marketing/finance/hr/...
- Apply method: `easy_apply` / `external` / `unknown`
- Location parser: `parsedLocation: {city, state, country}`,
  `isUsListing`, `isRemoteListing`
- DEI signals: 7 boolean flags (diversity, LGBTQ, women, veteran,
  disability, EEO, pay transparency)
- US pay transparency law detection: CA/CO/CT/MD/NV/NY/RI/WA/DC/IL/MN/MA
  + `pay_transparency_compliant` (whether salary is disclosed as required)
- Job ID + canonical URL (cross-run dedup)
- **recruiterScore (0-100)** + `recruiterTier` (cold/warm/hot/scorching)
  for B2B recruitment-tech / ATS / sourcing-tool prospecting
- **outreachPitch** + 3 variants (consultative/aggressive/referral)
- **outreachLinks**: LinkedIn company page, hiring-manager search,
  role-owner search (engineering manager / cmo / cfo by category),
  Google search, careers-page guess, mailto template

Free aggregate KV records on bulk runs:
- **SUMMARY** — avg/p25/p75 salary, top skills, recruiter-tier breakdown
- **TOP_HIRING_COMPANIES** — top 20 companies sorted by job count, with
  3 outreach pitch variants per company
- **TOP_JOBS** — top 20 jobs sorted by recruiterScore (sales-ops digest)

Quick start:

    from linkedin_jobs import LinkedInJobsClient

    client = LinkedInJobsClient(api_token="apify_api_xxxxxx")

    jobs, summary = client.search(
        keywords="senior software engineer",
        location="United States",
        max_pages=3,
        remote=True,
    )

    for j in client.filter_by_recruiter_tier(jobs, "scorching", "hot"):
        print(f"{j['companyName']:30}  {j['jobTitle'][:50]}  "
              f"{j.get('salary_tier'):10}  ${j.get('salaryMedianUsd', 0):,.0f}")

    # Top hiring companies digest (free aggregate)
    top = client.get_top_hiring_companies()
    for company in top["top_companies"][:10]:
        print(company["companyName"], company["jobs_count"], "open roles")
        print(" ", company["outreachPitch"])

See https://github.com/apivault-labs/linkedin-jobs-scraper-python for full docs.
"""

from .client import LinkedInJobsClient
from .exceptions import (
    LinkedInJobsError,
    AuthenticationError,
    ActorRunError,
    ActorTimeoutError,
)

__version__ = "0.1.0"
__all__ = [
    "LinkedInJobsClient",
    "LinkedInJobsError",
    "AuthenticationError",
    "ActorRunError",
    "ActorTimeoutError",
]
