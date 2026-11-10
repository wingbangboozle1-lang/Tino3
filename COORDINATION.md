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

## Integration handoff — session arena-50c6b81e-tino3 (PR #3)
- 2026-11-10: Parallel session. PR #3 (branch arena/50c6b81e-tino3) conflicted with PR #1 already merged to main.
- Resolution: kept PR #1 pages as primary (index.html, projections.html, assets/style.css); added PR #3 supplementary pages + data/ + scripts/ without discarding either session's work. README merged. This entry logs the merge per COORDINATION rules.
- Verification: internal-link + PII scan on combined tree; both sets anonymized, $10 rounding, source-linked rows.
