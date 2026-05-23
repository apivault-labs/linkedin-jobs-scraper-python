# 💼 LinkedIn Jobs Scraper — Python SDK

[![PyPI version](https://img.shields.io/badge/pip-linkedin--jobs--scraper-blue.svg)](https://github.com/apivault-labs/linkedin-jobs-scraper-python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/apivault-labs/linkedin-jobs-scraper-python/actions/workflows/ci.yml/badge.svg)](https://github.com/apivault-labs/linkedin-jobs-scraper-python/actions/workflows/ci.yml)

> **40+ enrichment fields per LinkedIn job. $0.003 each. CRM-ready output.
> One-click outreach links. Sales-ops workflow built-in. No login required.**

Direct alternative to **LinkedIn Recruiter** for use cases the official APIs
can't cover: salary parsing across hourly/yearly/EUR/GBP, 200+ skills
extraction, 14 benefits flags, recruiter-score 0-100, industry-specific
outreach pitches, US pay-transparency law compliance detection, and ready-
to-paste mailto/LinkedIn-search URLs — none of which the LinkedIn Jobs UI
exposes.

```bash
pip install git+https://github.com/apivault-labs/linkedin-jobs-scraper-python
```

```python
from linkedin_jobs import LinkedInJobsClient

client = LinkedInJobsClient(api_token="apify_api_xxxxxx")

jobs, summary = client.search(
    keywords="senior software engineer",
    location="United States",
    max_pages=3,
    remote=True,
    posted_within="week",
)

# Hottest sales prospects (companies actively hiring × budget owners)
for j in client.filter_by_recruiter_tier(jobs, "scorching", "hot"):
    print(f"{j['companyName']:30}  lead={j['recruiterScore']:3}  "
          f"{j.get('salary_tier'):10}  {j['jobTitle']}")
```

## What you get for $0.003 per job

For every LinkedIn job analyzed, you get **40+ structured fields** combining
LinkedIn's data with **15 derived enrichment layers**.

### ⭐ Core (LinkedIn search-page)

- `jobTitle`, `companyName`, `location`, `jobType`
- `description` (preview), `postedDate`, `companyLogo`
- `jobUrl`, `jobId`, `jobCanonicalUrl` (stable ID for cross-run dedup)

### 💰 Salary parser (USD-normalized)

- `salaryMinUsd`, `salaryMaxUsd`, `salaryMedianUsd`
- `salary_tier` — entry/mid/senior/principal/unicorn
- `salaryPeriod` (auto-detected hourly/daily/weekly/monthly/yearly)
- `salaryCurrency` — USD/EUR/GBP/CAD/AUD/INR/JPY (FX-converted to USD)
- Hourly/daily/weekly/monthly auto-annualized to year

### ⏱️ Job freshness

- `daysSincePosted`, `freshness_tier` (today/this_week/this_month/older)

### 🌍 Work-mode classifier

- `workMode` — remote / hybrid / onsite / unknown
- `isRemoteListing` boolean

### 🛠️ Skills extraction (200+ tech terms)

- `skillsRequired[]` — Python, React, Postgres, AWS, Kubernetes, GraphQL,
  TensorFlow, LangChain, Salesforce, Shopify, ...
- `skillsCount`, `softSkills[]`, `certifications[]`

### 🎁 Benefits parser — 14 boolean flags

`mentions_401k`, `mentions_health_insurance`, `mentions_equity`,
`mentions_remote_work`, `mentions_visa_sponsorship`, `mentions_relocation`,
`mentions_unlimited_pto`, `mentions_parental_leave`, `mentions_signing_bonus`,
`mentions_4_day_week`, `mentions_stipend`, `mentions_meals`, `mentions_gym`,
`mentions_commuter_benefits`, plus `benefitsCount`

### 🎯 Seniority normalizer

`intern` / `junior` / `mid` / `senior` / `lead` / `staff` / `principal` /
`director` / `vp` / `c-level`. Reliable across noisy titles.

### 🏷️ Job category

`engineering` / `data_science` / `product` / `design` / `sales` /
`marketing` / `finance` / `hr` / `operations` / `legal` /
`customer_support` / `healthcare` / `education` / `construction_trades`

### 🚀 Apply method

`easy_apply` / `external` / `unknown` — Easy Apply has the lowest friction.

### 🏠 Location parser

`parsedLocation: {city, state, country}`, `isUsListing`, `isRemoteListing`

### 🏛️ DEI signals — 7 boolean flags

`mentions_diversity`, `mentions_lgbtq`, `mentions_women`,
`mentions_veteran_friendly`, `mentions_disability_friendly`, `mentions_eeo`,
`mentions_pay_transparency`

### ⚖️ US pay transparency law detection

For listings in **CA / CO / CT / MD / NV / NY / RI / WA / DC / IL / MN / MA**:

- `pay_transparency_state`, `pay_transparency_law` (descriptive name)
- `pay_transparency_compliant` — true if salary disclosed as required by law

### 🎯 **recruiterScore (0-100)** + tier + reasons

B2B prospecting score for recruitment-tech / ATS / sourcing-tool sales:

- Number of roles open at the same company in this run (active budget)
- Job freshness, salary disclosure, modern skills, benefits depth
- Decision-maker seniority (VP/director/C-level = budget owner)
- Remote-friendly / visa sponsorship (talent strategy)

`recruiterTier` — `cold` / `warm` / `hot` / `scorching`
`recruiterScoreReasons[]` — explainable signals

### 💬 3-variant outreach pitches (per company)

Written to `TOP_HIRING_COMPANIES.outreachPitchVariants`:

- `consultative` — soft sell (default)
- `aggressive` — leads with a metric
- `referral` — mutual-connection angle

A/B test which copy converts in your sequence.

### 📞 One-click outreach links

- `linkedin_company_url`
- `linkedin_jobs_at_company_url`
- `linkedin_hiring_manager_search_url`
- `linkedin_role_owner_search_url` — pre-filtered for the actual role
  (engineering manager / cmo / cfo / head of design / ...)
- `google_search_url`
- `careers_page_guess`
- `email_template_url` + `email_template_url_with_pitch`

### 📊 Free aggregate KV records on bulk runs

**SUMMARY** — avg/p25/p75 salary, by_category, by_seniority, by_work_mode,
by_recruiter_tier, top_companies, top_skills_demanded, salary_disclosed_pct,
remote_friendly_pct, fresh_today_count.

**TOP_HIRING_COMPANIES** — top 20 companies sorted by job count, with 3
outreach pitch variants and pre-built outreachLinks per company.

**TOP_JOBS** — top 20 jobs sorted by `recruiterScore` (the sales-ops
job-level digest).

## Sample output

```json
{
  "success": true,
  "jobTitle": "Senior Backend Engineer",
  "companyName": "Acme Corp",
  "jobId": "4368055728",
  "jobCanonicalUrl": "https://www.linkedin.com/jobs/view/4368055728",

  "parsedLocation": {
    "city": "San Francisco",
    "state": "CA",
    "country": "US"
  },
  "isUsListing": true,
  "isRemoteListing": true,
  "workMode": "remote",

  "salaryMinUsd": 180000,
  "salaryMaxUsd": 240000,
  "salaryMedianUsd": 210000,
  "salary_tier": "principal",
  "salaryPeriod": "year",
  "salaryCurrency": "USD",

  "daysSincePosted": 3,
  "freshness_tier": "this_week",

  "applyMethod": "easy_apply",
  "seniority_normalized": "senior",
  "jobCategory": "engineering",

  "skillsRequired": ["Python", "Fastapi", "Postgres", "Kubernetes",
                     "Aws", "Terraform", "React", "Graphql"],
  "skillsCount": 8,

  "mentions_equity": true,
  "mentions_401k": true,
  "mentions_unlimited_pto": true,
  "mentions_remote_work": true,
  "benefitsCount": 4,

  "mentions_diversity": true,
  "mentions_eeo": true,
  "mentions_pay_transparency": true,
  "dei_signals_count": 3,

  "pay_transparency_state": "CA",
  "pay_transparency_law": "California (SB 1162)",
  "pay_transparency_compliant": true,

  "recruiterScore": 78,
  "recruiterTier": "scorching",
  "recruiterScoreReasons": [
    "5 roles open",
    "posted this week",
    "salary disclosed",
    "high-tier comp",
    "8 skills listed",
    "4 benefits listed",
    "remote-friendly"
  ],

  "outreachLinks": {
    "linkedin_company_url": "https://www.linkedin.com/company/Acme+Corp",
    "linkedin_role_owner_search_url": "https://www.linkedin.com/search/results/people/?keywords=Acme+Corp+engineering+manager+OR+director+of+engineering",
    "google_search_url": "https://www.google.com/search?q=%22Acme+Corp%22+careers",
    "email_template_url": "mailto:?subject=Saw+your+team+is+hiring+at+Acme+Corp"
  }
}
```

## Use cases

### 🥇 Recruitment-tech / ATS / sourcing-tool B2B sales

```python
# 1. Find scorching-tier companies in pay-transparency states with senior+ roles
jobs, _ = client.search(keywords="engineering manager", max_pages=10)

prospects = client.filter_by_recruiter_tier(jobs, "scorching")
prospects = client.filter_by_seniority(prospects,
                                        "senior", "lead", "director", "vp")
prospects = client.filter_with_pay_transparency(prospects)

# 2. Pull the daily TOP_HIRING_COMPANIES digest
top = client.get_top_hiring_companies()
for company in top["top_companies"][:5]:
    pitch = company["outreachPitchVariants"]["aggressive"]
    print(f"\n{company['companyName']} ({company['jobs_count']} roles)")
    print(f"  {pitch}")
    print(f"  {company['outreachLinks']['linkedin_role_owner_search_url']}")
```

### 💰 Salary benchmarking

```python
# Bay Area senior engineers, USD-normalized
jobs, summary = client.search(
    keywords="senior software engineer",
    location="San Francisco Bay Area",
    max_pages=15,
    only_with_salary=True,
)
print(f"Median: ${summary['salary_median_usd']:,.0f}")
print(f"P25-P75: ${summary['salary_p25_usd']:,.0f} - "
      f"${summary['salary_p75_usd']:,.0f}")
```

### ⚖️ Pay transparency compliance audit (HR-tech)

```python
# Find companies in pay-transparency states that AREN'T disclosing salary
jobs, _ = client.search(keywords="product manager", location="New York, NY")

non_compliant = [
    j for j in jobs
    if j.get("pay_transparency_state")
    and not j.get("pay_transparency_compliant")
]
print(f"{len(non_compliant)} potentially non-compliant listings in NY")
```

### 📈 Hiring trends / market research

```python
# Track skills demand week-over-week
this_week, _ = client.search(keywords="data engineer", posted_within="week")
last_week_jobs = [...]   # loaded from previous run

new_listings = client.deduplicate_across_runs(last_week_jobs, this_week)
print(f"{len(new_listings)} brand-new jobs this week")
```

### 🌐 Remote job board

```python
# Build a remote-only ETL pipeline
jobs, _ = client.search(keywords="senior", remote=True, max_pages=15)
remote_jobs = client.filter_remote(jobs)
# → drop into your DB, expose via your job board UI
```

### 🚀 Easy Apply funnel for candidates

```python
# Your candidate-facing site only shows Easy Apply jobs (lower friction)
jobs, _ = client.search(keywords="frontend engineer", max_pages=10)
easy = client.filter_easy_apply(jobs)
```

## Pricing

| Volume | Cost |
|---|---|
| 1 job | $0.003 |
| 100 | $0.30 |
| 1,000 | $3.00 |
| 10,000 | $30.00 |

```python
client.estimate_cost(2_500)   # 7.5 USD
```

The Apify free tier ($5 credit) covers ~1,650 jobs.

## Installation

```bash
pip install git+https://github.com/apivault-labs/linkedin-jobs-scraper-python
```

Or pin to a release tag:

```bash
pip install git+https://github.com/apivault-labs/linkedin-jobs-scraper-python@v0.1.0
```

## Setup

1. Create an Apify account: <https://console.apify.com/sign-up>
2. Get your API token: <https://console.apify.com/account/integrations>
3. Either pass it explicitly or export `APIFY_API_TOKEN`:

```bash
export APIFY_API_TOKEN="apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

```python
client = LinkedInJobsClient()                        # picks up env var
client = LinkedInJobsClient(api_token="apify_...")   # explicit
```

## Examples

| File | What it shows |
|---|---|
| [`examples/quickstart.py`](examples/quickstart.py) | Single search with all defaults |
| [`examples/bulk_search.py`](examples/bulk_search.py) | Multi-page run + SUMMARY/TOP_JOBS/TOP_HIRING_COMPANIES |
| [`examples/recruiter_outreach_pipeline.py`](examples/recruiter_outreach_pipeline.py) | Full sales-ops workflow with 3 pitch variants |
| [`examples/salary_benchmarking.py`](examples/salary_benchmarking.py) | USD-normalized salary distribution analysis |
| [`examples/pay_transparency_compliance_audit.py`](examples/pay_transparency_compliance_audit.py) | HR-tech / legal-tech use case |
| [`examples/daily_monitoring.py`](examples/daily_monitoring.py) | Cross-run dedup with `jobId` |
| [`examples/tech_skills_demand_report.py`](examples/tech_skills_demand_report.py) | Skills-demand frequency by category |
| [`examples/export_to_csv.py`](examples/export_to_csv.py) | CSV export for HubSpot/Pipedrive/Salesforce |

## API reference

### `LinkedInJobsClient(api_token=None, timeout=1200, poll_interval=3.0)`

### `search(keywords, **kwargs) -> (jobs, summary)`

Forwards all 25 actor input flags. See full list in [`linkedin_jobs/client.py`](linkedin_jobs/client.py).

Key parameters: `location`, `max_pages` (1-15), `remote`, `experience_level`,
`job_type`, `posted_within`, `min_recruiter_score`, `only_with_salary`,
`only_remote`, `deep_fetch_top_n`, `export_format`.

### KV record helpers

- `get_summary() -> dict | None`
- `get_top_hiring_companies() -> dict | None`
- `get_top_jobs() -> dict | None`

### Filters (return new lists)

- `filter_by_recruiter_tier(jobs, *tiers)` — cold/warm/hot/scorching
- `filter_by_seniority(jobs, *levels)`
- `filter_by_category(jobs, *categories)`
- `filter_by_salary_tier(jobs, *tiers)` — entry/mid/senior/principal/unicorn
- `filter_by_min_salary(jobs, min_usd)`
- `filter_by_state(jobs, *states)` — US 2-letter codes
- `filter_remote(jobs)`
- `filter_easy_apply(jobs)`
- `filter_with_pay_transparency(jobs)`
- `filter_diverse_employers(jobs, min_signals=2)`
- `filter_by_skills(jobs, *skills, match_all=False)`
- `filter_by_freshness(jobs, *tiers)`

### Helpers

- `estimate_cost(expected_jobs) -> float`
- `deduplicate_across_runs(previous, new) -> list` — for daily monitoring loops

## How it works

```
your_code → LinkedInJobsClient → Apify API
                                    ↓
                            Apify actor v1.3
                                    ↓
                  ┌─────────────────┴──────────────────┐
                  ↓                                    ↓
       Thunderbit (LinkedIn data)         Optional deep-fetch top N
                  ↓                                    ↓
        Two-pass enrichment with 15 derived layers
                  ↓
                rich record + free SUMMARY/TOP_JOBS/TOP_HIRING_COMPANIES
                  ↓
               you, in Python
```

## FAQ

**Q: Do I need a LinkedIn account?**
A: No. The actor scrapes the public job-search results — no login.

**Q: How accurate is the salary parser?**
A: Recognizes ranges, single values, K/M suffixes, 7 currencies, hourly/
weekly/monthly auto-annualization. Falls back to scanning the description.

**Q: How accurate is `recruiterScore`?**
A: Heuristic — bigger hiring-active companies with senior roles, fresh
postings, and disclosed salaries score highest. Treat scorching/hot as
priority outreach.

**Q: How is this better than the official LinkedIn Jobs Search API?**
A: LinkedIn's "Talent Solutions API" requires Recruiter seat ($800+/mo) or a
partner agreement. This SDK gives you 40+ enrichment fields per job (salary,
skills, recruiter score, outreach pitches, pay transparency law detection)
that the official API doesn't expose, for $0.003/job pay-as-you-go.

**Q: Will I get blocked / banned?**
A: All scraping happens on Apify's infrastructure via Thunderbit's
whitelisted pool. You don't connect to LinkedIn directly — your IP and your
account are never touched.

**Q: Can I filter by skills like "must have Python AND AWS"?**
A: Yes — `client.filter_by_skills(jobs, "Python", "AWS", match_all=True)`.

## Keywords

`linkedin-jobs` `linkedin-api` `linkedin-jobs-scraper`
`linkedin-without-login` `linkedin-without-api-key`
`linkedin-recruiter-alternative`
`job-scraper` `salary-parser` `salary-benchmarking` `compensation-data`
`skills-extraction` `recruiter-tools` `recruitment-tech` `ats-data`
`sourcing-tool` `talent-acquisition` `lead-generation` `b2b-lead-gen`
`outreach-automation` `cold-email` `sales-intelligence`
`remote-jobs-api` `diversity-hiring` `pay-transparency`
`hiring-trends` `labor-market-data` `apify` `python-sdk`

## License

MIT — see [LICENSE](LICENSE).
