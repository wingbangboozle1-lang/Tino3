# COORDINATION.md — Shared Task Board

Session ID: `arena-d11336c5-tino3` (branch `arena/d11336c5-tino3`)
Repo: wingbangboozle1-lang/Tino3
Started: 2026-11-10

## Task board

| # | Task | Status | Owner session | Files touched | Sources / verification | Irregularities |
|---|------|--------|---------------|---------------|------------------------|----------------|
| 1 | Research: federal estate tax, CA inheritance tax, Prop 13/19, step-up basis, capital gains | done | arena-d11336c5-tino3 | research notes (in site sources page) | IRS estate-tax page (2026 threshold $15,000,000 verified via fetch); BOE Prop 19 page boe.ca.gov/prop19/; FTB capital-gains page ftb.ca.gov/file/personal/income-types/capital-gains-and-losses.html | BOE old URL /proptaxes/prop-19.htm returns 404 — use /prop19/ |
| 2 | Research: insurance, maintenance, utilities, market returns, probate/trust, SF rent ordinance | done | arena-d11336c5-tino3 | site pages | PolicyGenius SF avg; GetHomeInsuranceQuotes Cupertino avg; Insurance.com/NAIC landlord avg; Fannie Mae 1% rule; SF.gov rent ordinance; Goldman Sachs 10-yr forecast | Insurance averages are secondary (not official) — flagged on site |
| 3 | Build static GitHub Pages site (dashboard + subpages, tables with source links, projections, decision analysis) | in progress | arena-d11336c5-tino3 | index.html, cupertino.html, san-francisco.html, taxes.html, inheritance-process.html, projections.html, decision.html, sources.html, flagged.html, assets/style.css, assets/app.js | All figures rounded to nearest $10; user-provided figures labeled unverified | — |
| 4 | Final integration: verify links, confirm build, open PR to main, merge, confirm Pages deploy | pending | arena-d11336c5-tino3 | — | — | — |

## Rules followed
- Personal information anonymized; placeholders only. No PII on site.
- Costs/numbers rounded to nearest $10.
- Every table row carries a source link; unverifiable values left flagged as unverified.
- No hallucinations: assumptions labeled as assumptions.

## Handoff log
- 2026-11-10: Session arena-d11336c5-tino3 claimed tasks 1-4 (single-session repo; no other sessions active). Pushing claim immediately.
- 2026-11-10: Session `arena/653eba50-tino3` added independent source checks and integration notes. Concurrent PR #1 and PR #3 were merged into main while this PR was open; both sessions’ site assets/data were retained. Independent primary sources: IRS 2026 Form 706 https://www.irs.gov/instructions/i706 ($15,000,000); IRS Form 709 https://www.irs.gov/instructions/i709 ($19,000 annual exclusion); IRS basis FAQ https://www.irs.gov/faqs/interest-dividends-other-types-of-income/gifts-inheritances; BOE Prop 19 notice https://www.boe.ca.gov/news/2025/nr-25-02.htm ($1,044,586 for Feb 16 2025–Feb 15 2027); BOE Prop 13 guide https://boe.ca.gov/pdf/pub800-10.pdf. Confirmed BOE and IRS 706 pages directly.
- Integration validation: checked local HTML refs prior to merging; workflow now validates links across HTML pages. Combined calculations and secondary forecasts require careful review; user-provided tax data (particularly the SF anomaly) remains unverified. Rebased update was blocked by concurrent same-file commits; the merge commit preserving main is on this session branch.
- Deployment state must be verified after merge; do not claim live until Pages Actions succeeds.

## Integration handoff — session arena-50c6b81e-tino3 (PR #3)
- 2026-11-10: Retained PR #3 supplementary pages, data and scripts alongside PR #1 pages; no parallel work discarded.
- Combined tree must be checked for source accuracy and rounded figures before relying on outputs.
- PR #3: https://github.com/wingbangboozle1-lang/Tino3/pull/3 — MERGED 2026-11-10 (merge commit 2371569). GitHub Pages deploy: success (run 42766640207). Live: https://wingbangboozle1-lang.github.io/Tino3/ (verified via fetch; supplementary cross-links present).
