# Changelog

## [0.1.0] — 2026-05-23

Initial release of the Python SDK for the LinkedIn Jobs Scraper Apify
actor (v1.3).

### Added

- `LinkedInJobsClient` with `search()` and 11 client-side filter helpers:
  - `filter_by_recruiter_tier(jobs, *tiers)` — cold/warm/hot/scorching
  - `filter_by_seniority(jobs, *levels)` — intern → c-level
  - `filter_by_category(jobs, *categories)` — engineering / sales / ...
  - `filter_by_salary_tier(jobs, *tiers)` — entry/mid/senior/principal/unicorn
  - `filter_by_min_salary(jobs, min_usd)`
  - `filter_by_state(jobs, *states)` — US 2-letter codes
  - `filter_remote(jobs)` — fully-remote
  - `filter_easy_apply(jobs)` — LinkedIn Easy Apply listings only
  - `filter_with_pay_transparency(jobs)` — disclosed salary + applicable law
  - `filter_diverse_employers(jobs, min_signals=2)`
  - `filter_by_skills(jobs, *skills, match_all=False)`
  - `filter_by_freshness(jobs, *tiers)` — today/this_week/this_month/older
- KV record helpers: `get_summary()`, `get_top_hiring_companies()`, `get_top_jobs()`
- `deduplicate_across_runs()` for daily monitoring loops (uses `jobId`)
- `estimate_cost(expected_jobs)` for pre-run budgeting
- All 25 actor input flags exposed as keyword arguments
- 8 example scripts:
  - `quickstart.py`
  - `bulk_search.py` with SUMMARY/TOP_HIRING_COMPANIES/TOP_JOBS
  - `recruiter_outreach_pipeline.py` — full sales-ops workflow
  - `salary_benchmarking.py`
  - `pay_transparency_compliance_audit.py` — HR-tech / legal-tech use case
  - `daily_monitoring.py` with cross-run dedup
  - `tech_skills_demand_report.py`
  - `export_to_csv.py`
- MIT license
