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
- 2026-11-10: Session `arena/653eba50-tino3` added an independent source-led dashboard and was unable to pull main before its first push because no remote branch existed. During PR integration, discovered PR #1 had merged concurrent full-site work into main. Kept the existing multi-page site and its assets (index, projections, county details, tax, process, decision, sources and review pages) rather than overwriting another session’s work. Conflict resolution preserves their files; review the combined source claims and calculations before treating them as verified.
- Independent primary-source checks by `arena/653eba50-tino3`: IRS 2026 Form 706 instructions https://www.irs.gov/instructions/i706 (2026 basic exclusion $15,000,000); IRS Form 709 https://www.irs.gov/instructions/i709 (2026 annual gift exclusion $19,000); IRS inherited-property basis FAQ https://www.irs.gov/faqs/interest-dividends-other-types-of-income/gifts-inheritances (general date-of-death FMV basis); BOE official release https://www.boe.ca.gov/news/2025/nr-25-02.htm ($1,044,586 Prop 19 adjustment effective Feb 16, 2025–Feb 15, 2027); BOE assessment guide https://boe.ca.gov/pdf/pub800-10.pdf (Prop 13 assessment framework). BOE notice and IRS 706 page fetched directly. Display values rounded to nearest $10.
- Integration checks: all single-page anchors were validated before merge; `git diff --check` passed before integration. Need rerun site-wide internal links after conflict resolution. Concurrent site's specific calculations, secondary insurance/market forecasts, and tax projections require additional review. User-given assessed values, especially SF implied effective rate, remain unverified and should not be relied upon.
- This site cannot prove it is live merely from a successful PR merge. Record actual Actions / Pages result below only after checking it.
