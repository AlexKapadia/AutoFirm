# SUMMARY — SEC EDGAR Application Programming Interfaces (public financial data)

## Full citation
- **Title:** EDGAR Application Programming Interfaces (APIs) + "Accessing EDGAR Data" / Fair-Access policy
- **Author / Issuing body:** U.S. Securities and Exchange Commission (SEC)
- **Year:** current (data.sec.gov REST APIs; fair-access rate limit effective since 27 July 2021)
- **Venue / Publisher:** SEC.gov official developer resources
- **URLs:**
  - https://www.sec.gov/search-filings/edgar-application-programming-interfaces
  - https://www.sec.gov/about/developer-resources
  - https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- **Corroborating practitioner docs (Low tier, color only):** sec-edgar-api.readthedocs.io; tldrfiling.com; dealcharts.org.

## Questions informed
- **L1.B4.4** Public-data sourcing + PII boundary — the canonical, free, primary source of REAL public corporate financials for the CLAUDE.md §3.12 public-data-only validation gate.

## GRADE tier
- **High** for the API/structure/policy facts (they come from the SEC itself, the primary regulator and data publisher). The endpoint shapes and the 10-req/s + User-Agent policy are stated on official SEC pages; practitioner blogs corroborate but are not the citation of record.

## Key claims (exact)

1. **No authentication / no API key.** "The data.sec.gov service hosts RESTful data APIs delivering JSON-formatted data... these APIs do not require any authentication or API keys." All endpoints are free.

2. **XBRL financial-statement coverage.** "submissions history by filer and XBRL data from financial statements (forms 10-Q, 10-K, 8-K, 20-F, 40-F, 6-K, and their variants)."

3. **Endpoints (exact patterns):**
   - **Submissions:** `https://data.sec.gov/submissions/CIK##########.json` — filing history for a filer (10-digit zero-padded CIK).
   - **Company Concept:** `https://data.sec.gov/api/xbrl/companyconcept/CIK##########/us-gaap/<Concept>.json` — all values of one XBRL concept for one company.
   - **Company Facts:** `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json` — "every XBRL-tagged fact across all filings for a given CIK in a single request." Each concept has a `units` object (usually USD or shares); each datapoint carries accession number, fiscal year, period, and form type.
   - **Frames:** `https://data.sec.gov/api/xbrl/frames/us-gaap/<Concept>/<Unit>/<Period>.json` — "aggregates one fact for each reporting entity that is last filed that most closely fits the calendrical period requested."

4. **Frames period format + tolerances:** `CY####` = annual (duration 365 days +/- 30); `CY####Q#` = quarterly (91 days +/- 30); `CY####Q#I` = instantaneous (a point-in-time/balance-sheet value).

5. **Fair-Access policy (REQUIRED for compliant access):**
   - "current maximum request rate is **10 requests per second**" — per user, regardless of number of machines (effective 27 July 2021).
   - A **descriptive `User-Agent` header** is **required** (identify application + contact email); requests without it receive **403 Forbidden**.
   - Exceeding the limit -> IP blocked ~10 minutes (per practitioner corroboration; SEC states throttling/403).

## Reproducibility note
The endpoint patterns and policy are stated on the SEC's own developer/API pages (note: the API-doc page returned HTTP 403 to the automated fetcher precisely *because* a descriptive User-Agent was absent — itself confirming claim #5). A reviewer can verify by issuing a GET with a proper User-Agent header to any companyfacts URL.
