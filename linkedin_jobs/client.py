"""
LinkedInJobsClient — synchronous wrapper around the Apify
``apivault_labs/linkedin-jobs-scraper`` actor (v1.3).

The actor handles all heavy work on Apify infrastructure:
  - Thunderbit-powered scraping (no LinkedIn login needed)
  - Two-pass enrichment with 15 derived layers
  - Optional deep-fetch of top companies for full description + salary
  - Per-company aggregation, recruiter scoring, outreach pitch generation
  - SUMMARY + TOP_HIRING_COMPANIES + TOP_JOBS to KV store

This client forwards inputs, polls until the run finishes, then downloads
the dataset and exposes filters & helpers for sales-ops workflows.

Pricing: $0.003 per job ($3 / 1000). All enrichment included.

Quick start:

    from linkedin_jobs import LinkedInJobsClient

    client = LinkedInJobsClient(api_token="apify_api_xxxxxx")

    jobs, summary = client.search(
        keywords="senior backend engineer",
        location="United States",
        max_pages=3,
        remote=True,
    )

    for j in client.filter_by_recruiter_tier(jobs, "scorching", "hot"):
        print(j["companyName"], j["jobTitle"], j.get("salary_tier"))
"""

from __future__ import annotations

import os
import time
from typing import Any, Iterable, Sequence

import requests

from .exceptions import (
    ActorRunError,
    ActorTimeoutError,
    AuthenticationError,
    LinkedInJobsError,
)


ACTOR_ID = "apivault_labs~linkedin-jobs-scraper"
APIFY_API_BASE = "https://api.apify.com/v2"

TERMINAL_OK = {"SUCCEEDED"}
TERMINAL_FAIL = {"FAILED", "TIMED-OUT", "ABORTED"}

PRICE_PER_JOB_USD = 0.003


class LinkedInJobsClient:
    """Synchronous client for the LinkedIn Jobs Scraper Apify actor.

    Parameters
    ----------
    api_token : str, optional
        Apify Personal API token. Falls back to ``APIFY_API_TOKEN``.
    timeout : int, optional
        Maximum seconds to wait for an actor run. Default 1200 (20 min) —
        15-page runs with deep-fetch enabled can take 8-15 minutes.
    poll_interval : float, optional
        Seconds between status polls. Default 3.
    base_url : str, optional
        Override the Apify API base URL.
    """

    def __init__(
        self,
        api_token: str | None = None,
        timeout: int = 1200,
        poll_interval: float = 3.0,
        base_url: str = APIFY_API_BASE,
    ):
        token = api_token or os.environ.get("APIFY_API_TOKEN")
        if not token:
            raise AuthenticationError(
                "Apify API token is required. Pass api_token='apify_api_...' "
                "or set the APIFY_API_TOKEN environment variable. "
                "Get a token at https://console.apify.com/account/integrations"
            )
        self._token = token
        self._timeout = int(timeout)
        self._poll_interval = float(poll_interval)
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "User-Agent": "linkedin-jobs-scraper-python/0.1.0",
        })
        self._last_run_id: str | None = None
        self._last_dataset_id: str | None = None
        self._last_kvs_id: str | None = None

    # ------------------------------------------------------------------ public

    def search(
        self,
        keywords: str,
        *,
        location: str = "",
        max_pages: int = 3,
        remote: bool = False,
        experience_level: str = "any",
        job_type: str = "any",
        posted_within: str = "any",
        # Layer toggles (all default on)
        extract_salary_parse: bool = True,
        extract_freshness: bool = True,
        extract_work_mode: bool = True,
        extract_skills: bool = True,
        extract_benefits: bool = True,
        extract_seniority: bool = True,
        extract_category: bool = True,
        extract_recruiter_score: bool = True,
        extract_outreach_assets: bool = True,
        extract_dei_signals: bool = True,
        extract_pay_transparency_law: bool = True,
        extract_location_parts: bool = True,
        deep_fetch_top_n: int = 0,
        # Filters
        deduplicate_companies: bool = False,
        min_recruiter_score: int = 0,
        only_with_salary: bool = False,
        only_remote: bool = False,
        # Output
        export_format: str = "default",
        write_summary: bool = True,
        top_companies_n: int = 20,
        top_jobs_n: int = 20,
        # Plumbing
        thunderbit_retries: int = 1,
        max_concurrency: int = 2,
        timeout_per_page: int = 120,
        actor_timeout_secs: int = 1800,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        """Run a LinkedIn Jobs search and return enriched results.

        Parameters
        ----------
        keywords : str
            Job title or keywords. Required.
        location : str, optional
            City / country / 'Remote'.
        max_pages : int, optional
            1-15 pages, ~25 jobs per page. Default 3.
        remote : bool, optional
            Apply LinkedIn's `f_WT=2` remote filter at the URL level.
        experience_level : str, optional
            ``any`` / ``internship`` / ``entry`` / ``associate`` /
            ``mid_senior`` / ``director`` / ``executive``
        job_type : str, optional
            ``any`` / ``full_time`` / ``part_time`` / ``contract`` /
            ``temporary`` / ``volunteer`` / ``internship``
        posted_within : str, optional
            ``any`` / ``day`` / ``week`` / ``month``
        deep_fetch_top_n : int, optional
            For top-N companies (sorted by job count) open the highest-
            recruiter-score job's detail page to recover full description
            and salary. Adds ~30s per company. Default 0 (disabled).
        export_format : str, optional
            ``default`` (full JSON) or ``csv`` (40-column flat).
        min_recruiter_score : int, optional
            Drop jobs whose recruiterScore is below this threshold.
        only_with_salary, only_remote : bool, optional
            Server-side post-filters.

        Returns
        -------
        tuple[list[dict], dict | None]
            ``(jobs, summary)`` — ``summary`` contains aggregate stats or
            ``None`` for tiny runs.
        """
        if not keywords or not keywords.strip():
            raise ValueError("keywords must be a non-empty string")

        if export_format not in ("default", "csv"):
            raise ValueError(
                f"export_format must be 'default' or 'csv', got {export_format!r}"
            )

        payload = {
            "keywords": keywords.strip(),
            "location": location or "",
            "maxPages": max(1, min(15, int(max_pages))),
            "remote": bool(remote),
            "experienceLevel": experience_level,
            "jobType": job_type,
            "postedWithin": posted_within,
            "extractSalaryParse": bool(extract_salary_parse),
            "extractFreshness": bool(extract_freshness),
            "extractWorkMode": bool(extract_work_mode),
            "extractSkills": bool(extract_skills),
            "extractBenefits": bool(extract_benefits),
            "extractSeniority": bool(extract_seniority),
            "extractCategory": bool(extract_category),
            "extractRecruiterScore": bool(extract_recruiter_score),
            "extractOutreachAssets": bool(extract_outreach_assets),
            "extractDeiSignals": bool(extract_dei_signals),
            "extractPayTransparencyLaw": bool(extract_pay_transparency_law),
            "extractLocationParts": bool(extract_location_parts),
            "deepFetchTopN": max(0, min(25, int(deep_fetch_top_n))),
            "deduplicateCompanies": bool(deduplicate_companies),
            "minRecruiterScore": max(0, min(100, int(min_recruiter_score))),
            "onlyWithSalary": bool(only_with_salary),
            "onlyRemote": bool(only_remote),
            "exportFormat": export_format,
            "writeSummary": bool(write_summary),
            "topCompaniesN": max(5, min(100, int(top_companies_n))),
            "topJobsN": max(5, min(100, int(top_jobs_n))),
            "thunderbitRetries": max(0, min(3, int(thunderbit_retries))),
            "maxConcurrency": max(1, min(5, int(max_concurrency))),
            "timeout": max(30, min(300, int(timeout_per_page))),
        }

        run_id = self._start_run(payload, actor_timeout_secs=actor_timeout_secs)
        run = self._wait_for_run(run_id)
        self._last_run_id = run_id
        self._last_dataset_id = run.get("defaultDatasetId")
        self._last_kvs_id = run.get("defaultKeyValueStoreId")
        records = self._fetch_dataset(self._last_dataset_id)

        summary = None
        if write_summary and self._last_kvs_id:
            summary = self._fetch_kv_record(self._last_kvs_id, "SUMMARY")

        return records, summary

    # ------------------------------------------------------------------ KV helpers

    def get_summary(self) -> dict[str, Any] | None:
        """Fetch the aggregate ``SUMMARY`` record from the most recent run."""
        if not self._last_kvs_id:
            return None
        return self._fetch_kv_record(self._last_kvs_id, "SUMMARY")

    def get_top_hiring_companies(self) -> dict[str, Any] | None:
        """Fetch the ``TOP_HIRING_COMPANIES`` snapshot from the most recent run.

        Top 20 companies sorted by job count, each with:
        ``jobs_count``, ``max_recruiterScore``, ``categories``, ``top_skills``,
        ``avg_salary_usd``, ``outreachPitch``, ``outreachPitchVariants``,
        ``outreachLinks``.
        """
        if not self._last_kvs_id:
            return None
        return self._fetch_kv_record(self._last_kvs_id, "TOP_HIRING_COMPANIES")

    def get_top_jobs(self) -> dict[str, Any] | None:
        """Fetch the ``TOP_JOBS`` snapshot — top 20 jobs sorted by recruiterScore."""
        if not self._last_kvs_id:
            return None
        return self._fetch_kv_record(self._last_kvs_id, "TOP_JOBS")

    # ------------------------------------------------------------------ filters

    def filter_by_recruiter_tier(
        self,
        jobs: Sequence[dict[str, Any]],
        *tiers: str,
    ) -> list[dict[str, Any]]:
        """Filter to jobs whose ``recruiterTier`` is in the requested set.

        Tiers: ``cold`` / ``warm`` / ``hot`` / ``scorching``. Default keeps
        ``("scorching", "hot")``.
        """
        if not tiers:
            tiers = ("scorching", "hot")
        wanted = {t.lower() for t in tiers}
        return [
            j for j in jobs
            if (j.get("recruiterTier") or "").lower() in wanted
        ]

    def filter_by_seniority(
        self,
        jobs: Sequence[dict[str, Any]],
        *levels: str,
    ) -> list[dict[str, Any]]:
        """Filter by ``seniority_normalized`` (intern/junior/mid/senior/lead/
        staff/principal/director/vp/c-level)."""
        if not levels:
            return list(jobs)
        wanted = {lv.lower() for lv in levels}
        return [
            j for j in jobs
            if (j.get("seniority_normalized") or "").lower() in wanted
        ]

    def filter_by_category(
        self,
        jobs: Sequence[dict[str, Any]],
        *categories: str,
    ) -> list[dict[str, Any]]:
        """Filter by ``jobCategory`` (engineering / sales / marketing / ...)."""
        if not categories:
            return list(jobs)
        wanted = {c.lower() for c in categories}
        return [
            j for j in jobs
            if (j.get("jobCategory") or "").lower() in wanted
        ]

    def filter_by_salary_tier(
        self,
        jobs: Sequence[dict[str, Any]],
        *tiers: str,
    ) -> list[dict[str, Any]]:
        """Filter by ``salary_tier`` (entry/mid/senior/principal/unicorn)."""
        if not tiers:
            return list(jobs)
        wanted = {t.lower() for t in tiers}
        return [
            j for j in jobs
            if (j.get("salary_tier") or "").lower() in wanted
        ]

    def filter_by_min_salary(
        self,
        jobs: Sequence[dict[str, Any]],
        min_usd: int,
    ) -> list[dict[str, Any]]:
        """Keep only jobs whose ``salaryMedianUsd`` is at least ``min_usd``."""
        return [
            j for j in jobs
            if (j.get("salaryMedianUsd") or 0) >= min_usd
        ]

    def filter_by_state(
        self,
        jobs: Sequence[dict[str, Any]],
        *states: str,
    ) -> list[dict[str, Any]]:
        """Filter by US state (2-letter codes via ``parsedLocation.state``)."""
        wanted = {s.upper() for s in states if s}
        if not wanted:
            return list(jobs)
        return [
            j for j in jobs
            if ((j.get("parsedLocation") or {}).get("state") or "").upper()
                in wanted
        ]

    def filter_remote(
        self,
        jobs: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filter to fully-remote jobs (``workMode = "remote"`` or
        ``isRemoteListing``)."""
        out: list[dict[str, Any]] = []
        for j in jobs:
            if j.get("workMode") == "remote":
                out.append(j)
            elif j.get("isRemoteListing"):
                out.append(j)
        return out

    def filter_easy_apply(
        self,
        jobs: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filter to LinkedIn Easy Apply listings — lower friction = better
        candidate response rates."""
        return [j for j in jobs if j.get("applyMethod") == "easy_apply"]

    def filter_with_pay_transparency(
        self,
        jobs: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filter to jobs in pay-transparency law states with disclosed salary."""
        return [
            j for j in jobs
            if j.get("pay_transparency_state")
            and j.get("pay_transparency_compliant")
        ]

    def filter_diverse_employers(
        self,
        jobs: Sequence[dict[str, Any]],
        min_signals: int = 2,
    ) -> list[dict[str, Any]]:
        """Filter to employers signaling commitment to DEI (≥ N signals)."""
        return [
            j for j in jobs
            if (j.get("dei_signals_count") or 0) >= min_signals
        ]

    def filter_by_skills(
        self,
        jobs: Sequence[dict[str, Any]],
        *skills: str,
        match_all: bool = False,
    ) -> list[dict[str, Any]]:
        """Filter to jobs requiring any (or all) of the given skills.

        Case-insensitive substring match against ``skillsRequired[]``.
        """
        if not skills:
            return list(jobs)
        needles = [s.lower() for s in skills if s]
        out: list[dict[str, Any]] = []
        for j in jobs:
            stack = [s.lower() for s in (j.get("skillsRequired") or [])]
            if not stack:
                continue
            if match_all:
                if all(any(n in s for s in stack) for n in needles):
                    out.append(j)
            else:
                if any(any(n in s for s in stack) for n in needles):
                    out.append(j)
        return out

    def filter_by_freshness(
        self,
        jobs: Sequence[dict[str, Any]],
        *tiers: str,
    ) -> list[dict[str, Any]]:
        """Filter by ``freshness_tier`` (today/this_week/this_month/older)."""
        if not tiers:
            tiers = ("today", "this_week")
        wanted = {t.lower() for t in tiers}
        return [
            j for j in jobs
            if (j.get("freshness_tier") or "").lower() in wanted
        ]

    # ------------------------------------------------------------------ helpers

    def estimate_cost(self, expected_jobs: int) -> float:
        """Estimate USD cost for ``expected_jobs`` jobs at $3/1000.

        Use this *before* calling ``search()`` to budget your run. Each page
        returns up to 25 jobs, so 10 pages ≈ 250 jobs ≈ $0.75.
        """
        return round(expected_jobs * PRICE_PER_JOB_USD, 4)

    def deduplicate_across_runs(
        self,
        previous_jobs: Sequence[dict[str, Any]],
        new_jobs: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Drop jobs from ``new_jobs`` whose ``jobId`` was already in
        ``previous_jobs``. Useful for daily monitoring loops to avoid
        re-charging for the same job twice.
        """
        seen = {j.get("jobId") for j in previous_jobs if j.get("jobId")}
        return [j for j in new_jobs
                if j.get("jobId") and j["jobId"] not in seen]

    # ------------------------------------------------------------------ private

    def _start_run(self, payload: dict[str, Any], actor_timeout_secs: int) -> str:
        url = f"{self._base_url}/acts/{ACTOR_ID}/runs"
        params = {"timeout": int(actor_timeout_secs)}
        try:
            r = self._session.post(url, params=params, json=payload, timeout=30)
        except requests.RequestException as e:
            raise LinkedInJobsError(f"Failed to start actor run: {e}") from e
        if r.status_code == 401:
            raise AuthenticationError(
                "Apify rejected the API token. Generate a new one at "
                "https://console.apify.com/account/integrations"
            )
        if r.status_code >= 400:
            raise ActorRunError(
                f"Apify returned HTTP {r.status_code} when starting run: "
                f"{r.text[:300]}"
            )
        data = r.json().get("data") or {}
        run_id = data.get("id")
        if not run_id:
            raise ActorRunError(f"Apify response missing run id: {r.text[:300]}")
        return run_id

    def _wait_for_run(self, run_id: str) -> dict[str, Any]:
        url = f"{self._base_url}/actor-runs/{run_id}"
        deadline = time.time() + self._timeout
        while True:
            try:
                r = self._session.get(url, timeout=30)
            except requests.RequestException as e:
                raise LinkedInJobsError(f"Failed to poll run status: {e}") from e
            if r.status_code >= 400:
                raise ActorRunError(
                    f"Apify returned HTTP {r.status_code} when polling: "
                    f"{r.text[:300]}"
                )
            run = r.json().get("data") or {}
            status = run.get("status")
            if status in TERMINAL_OK:
                return run
            if status in TERMINAL_FAIL:
                raise ActorRunError(
                    f"Actor run {run_id} ended with status={status}: "
                    f"{run.get('statusMessage') or '(no message)'}"
                )
            if time.time() > deadline:
                raise ActorTimeoutError(
                    f"Actor run {run_id} did not finish within {self._timeout}s "
                    f"(last status={status}). Increase `timeout=` or fetch "
                    "the dataset manually."
                )
            time.sleep(self._poll_interval)

    def _fetch_dataset(self, dataset_id: str) -> list[dict[str, Any]]:
        url = f"{self._base_url}/datasets/{dataset_id}/items"
        params = {"clean": "true", "format": "json"}
        try:
            r = self._session.get(url, params=params, timeout=120)
        except requests.RequestException as e:
            raise LinkedInJobsError(f"Failed to download dataset: {e}") from e
        if r.status_code >= 400:
            raise ActorRunError(
                f"Apify returned HTTP {r.status_code} when fetching dataset: "
                f"{r.text[:300]}"
            )
        try:
            data = r.json()
        except ValueError as e:
            raise ActorRunError(f"Apify dataset is not valid JSON: {e}") from e
        if not isinstance(data, list):
            raise ActorRunError(
                f"Unexpected dataset payload: {type(data).__name__}"
            )
        return data

    def _fetch_kv_record(self, kvs_id: str, key: str) -> dict[str, Any] | None:
        url = f"{self._base_url}/key-value-stores/{kvs_id}/records/{key}"
        try:
            r = self._session.get(url, timeout=30)
        except requests.RequestException:
            return None
        if r.status_code >= 400:
            return None
        try:
            return r.json()
        except ValueError:
            return None
