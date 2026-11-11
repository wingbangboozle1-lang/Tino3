# Inheritance Atlas

**Live site:** https://wingbangboozle1-lang.github.io/Tino3/

A privacy-first, official-source decision dashboard about a future trust inheritance and a second property **already held by the heir**. It distinguishes estate tax, post-transfer property tax and later income tax, and refuses to fabricate a property-specific recommendation from unverified inputs.

## Public pages

| Section | What it does |
|---|---|
| [Overview](index.html), [Executive summary](executive-summary.html) | Ownership distinction, present rules, conditional recommendation |
| [Property A](property-a.html), [Property B](property-b.html) | Historic year labels and cost categories with unconfirmed personal amounts blank |
| [50-year reference](projections.html), [Black swans](black-swans.html) | BOE CCPI/factors and FHFA housing-index history replayed as a **non-uniform scenario**, not a property forecast |
| [Decision](decision.html), [Taxes & law](taxes.html) | Net-proceeds/rent/occupancy framework, official thresholds and law-watch dates |
| [Trust process](inheritance.html) | Step-by-step actions and current statutory deadlines |
| [Flagged for review](review.html), [Methodology](methodology.html), [Sources](sources.html) | Unverified items, past-publication incident and row-by-row official citations |

Published examples use a **hypothetical $1,000,000 assessment unit**, not either home's valuation. All displayed money is rounded to the nearest $10. The historical Q2 statewide price index comes from [FHFA via FRED](https://fred.stlouisfed.org/data/CASTHPI); the annual California inflation/factor table comes from [BOE letter 2026/002](https://www.boe.ca.gov/proptaxes/pdf/lta26002.pdf). Official agency links on *each table row* verify the stated rule or historical series, not a household's taxes or future outcome.

## Privacy and publication

- No names, addresses, postal codes, parcel IDs, household valuations, tenant payments, tax-roll series, utility bills or insurance guesses in the served edition. Property-specific entries remain truly empty in the HTML **and** CSV. A rounded amount plus a rare tax history can still identify a parcel.
- Old `plan/`, `analysis/`, `decision-suite/` and legacy root paths are replaced with content-free withdrawal notices in the repository's **current tree** and in the allowlisted Pages artifact. No analytics, forms, scripts, remote assets or visitor input.
- **The earlier public Git history and outside caches are not erased.** A repository owner must evaluate those separately; the site [flags this explicitly](review.html). Do not publish private records or source code derived from them again.
- The GitHub Pages repository setting **must be `build_type=workflow`**. A legacy `main`/`/` publisher would serve extra tracked files, bypassing the Pages allowlist; the deploy workflow alone does not change this setting.

## Rebuild and verify (Python standard library)

```bash
python3 public_site/build.py
python3 scripts/verify.py
python3 scripts/package_site.py
```

`public_site/data/official_hpi_q2.csv` and `boe_ccpi_factors.csv` are pinned, public official observations. `public_site/build.py` generates the 12 root pages, stylesheet, source ledger and three public CSV downloads. `public_site/verify.py` regenerates them in a scratch folder; checks every table row against the source ledger, local links and fragments; scans privacy/rounding; proves every private-value column is blank; and checks withdrawn URLs and the final artifact. Its checks cannot independently certify a private appraisal, a future tax law, a bound policy, or historical Git erasure.

The [source library](sources.html) records each official document and precisely how it was checked on 11 November 2026. [COORDINATION.md](COORDINATION.md) records work ownership, irregularities and publishing results without repeating private inputs.

**Planning education only; not legal, tax, appraisal or investment advice.** Recheck laws and get professional advice at the actual transfer.
