# COORDINATION.md — Shared Task Board

Session ID: `arena-50c6b81e-tino3` (branch `arena/50c6b81e-tino3`)
Last updated: 2026-11-10

> Single-session project: this session is both worker and final integration session.
> No other sessions have claimed tasks. Scopes below are non-overlapping by file.

| Task | Status | Owner | Files touched | Sources / verification | Irregularities |
|---|---|---|---|---|---|
| 1. Research official sources (IRS, BOE, FTB, courts.ca.gov, BLS, SFPUC, Cupertino, CDI/NAIC, CPUC) | done | arena-50c6b81e-tino3 | data/sources.csv, sources-verification.html | See sources-verification.html; each row links to official .gov source | SF property-tax effective rate anomaly flagged (see Flagged page) |
| 2. Build reproducible projection model | done | arena-50c6b81e-tino3 | scripts/calculate.py, data/projections.csv, data/decision_analysis.csv | Prop 13 2% cap (BOE), Prop 19 $1M cap (BOE), Rev. Proc. 2025-32 $15M (IRS) | Market-growth & stock-return are labelled ASSUMPTIONS, not verified facts |
| 3. Build GitHub Pages site (dashboard + subpages) | done | arena-50c6b81e-tino3 | index.html, *.html, assets/, .github/workflows/pages.yml | Site builds statically; internal links checked by script | — |
| 4. Verification pass line-by-line | done | arena-50c6b81e-tino3 | sources-verification.html, flagged-review.html | User-provided values marked UNVERIFIED where no official source can confirm without APN/address | See Flagged page |
| 5. PR + merge + Pages deploy | in progress | arena-50c6b81e-tino3 | — | PR link recorded below after merge | — |

## Handoff log
- 2026-11-10: Session claimed all tasks (single session, no conflicts). Empty repo (README only) — no prior work to conflict with.
- 2026-11-10: Research, model, site, verification completed in this session. PR opened from integration branch to main.

## PR / deploy record
- PR: (to be filled after creation)
- Merge result: (to be filled)
- Pages deploy: (to be filled)

## Privacy rule (all sessions)
Personal information is anonymized with placeholders ([DECEDENT], [BENEFICIARY], [TRUSTEE], Property A/B). No personal data appears on the site.
