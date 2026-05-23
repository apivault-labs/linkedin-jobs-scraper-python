"""
Pay-transparency compliance audit — find companies in pay-transparency
states (CA, CO, CT, MD, NV, NY, RI, WA, DC, IL, MN, MA) that aren't
disclosing salary as required by law.

Use cases:
  - HR-tech compliance audits
  - Legal-tech / employment-law analytics
  - ESG / DEI reporting
  - Journalism / labor-research

    export APIFY_API_TOKEN=apify_api_xxxxxx
    python examples/pay_transparency_compliance_audit.py
"""

from collections import Counter

from linkedin_jobs import LinkedInJobsClient


def main() -> None:
    client = LinkedInJobsClient(timeout=1500)

    # Target a state with strong pay-transparency law
    jobs, _ = client.search(
        keywords="manager",
        location="New York, NY",
        max_pages=10,
        posted_within="week",
    )
    print(f"Analyzed {len(jobs)} NY listings")

    # Filter to those subject to a pay-transparency law
    in_scope = [j for j in jobs if j.get("pay_transparency_state")]
    compliant = client.filter_with_pay_transparency(jobs)
    non_compliant = [
        j for j in in_scope
        if not j.get("pay_transparency_compliant")
    ]

    print(f"\n  In scope (subject to law):     {len(in_scope)}")
    print(f"  Compliant (salary disclosed):  {len(compliant)}")
    print(f"  Non-compliant:                 {len(non_compliant)}")
    if in_scope:
        rate = 100 * len(compliant) / len(in_scope)
        print(f"  Compliance rate:               {rate:.1f}%")

    if non_compliant:
        print(f"\n=== Top 10 non-compliant employers ===")
        by_company = Counter(j.get("companyName", "?")
                             for j in non_compliant)
        for company, count in by_company.most_common(10):
            sample = next((j for j in non_compliant
                            if j.get("companyName") == company), None)
            law = sample.get("pay_transparency_law") if sample else "?"
            print(f"  {company:30}  {count} listing(s)  ({law})")

    # DEI bonus stats
    if jobs:
        diverse = client.filter_diverse_employers(jobs, min_signals=3)
        print(f"\n  Diverse employers (≥3 DEI signals): "
              f"{len(diverse)}/{len(jobs)} "
              f"({100 * len(diverse) // len(jobs)}%)")


if __name__ == "__main__":
    main()
