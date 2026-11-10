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
- 2026-11-10: Parallel session. PR #3 (branch arena/50c6b81e-tino3) conflicted with PR #1 already merged to main.
- Resolution: kept PR #1 pages as primary (index.html, projections.html, assets/style.css); added PR #3 supplementary pages + data/ + scripts/ without discarding either session's work. README merged. This entry logs the merge per COORDINATION rules.
- Verification: internal-link + PII scan on combined tree; both sets anonymized, $10 rounding, source-linked rows.

## Integration handoff — session-1820664f (branch arena/1820664f-tino3)
- 2026-11-10: Parallel session. Found main already integrated (PR #1 + PR #3). Kept main's site as primary; added supplementary set under pages/ + assets/css|js + data/*.json without discarding other sessions' work. Conflicts in index.html/README/COORDINATION/pages.yml resolved by keeping main's versions + this log entry.
- Verification: internal-link check on pages/ set passed; local preview 200. Sources: IRS, BOE Prop 13/19, FTB, CPUC NBT, SSA, Fed, FHFA. Irregularities F1–F11 logged on pages/flagged.html (incl. SF 2.14% effective rate).

## Final integration — PR #5 merged & deployed (session-1820664f)
- PR: https://github.com/wingbangboozle1-lang/Tino3/pull/5 — MERGED 2026-11-10 (merge commit 67fc2b2).
- Merge method: merge (no approval wait, per user instruction). Conflicts with main resolved by keeping main's primary pages and adding the supplementary set; nothing from any session discarded.
- Pre-merge verification: 524 internal refs checked across 19 HTML pages — 0 broken; balanced div/body/html tags; PII pattern scan (street addresses, SSN, APN) — only meta-references, no actual personal data.
- Deploy: "pages build and deployment" success + "Deploy GitHub Pages" success on main. Live: https://wingbangboozle1-lang.github.io/Tino3/ — verified by fetching / and /pages/executive-summary.html (content served correctly).
- Fixes made during integration: landing page index.html had duplicated markup after </body> and no link to the pages/ set — removed duplicate tail, restored closing tags, added "Additional dashboard set" card. sources.html gained an official-source verification table (IRS, BOE, FTB, CPUC, SSA, Fed, FHFA) so key legal figures trace to .gov pages rather than secondary sites.
- Task board status: T1–T9 done. Unverified items remain published on the Flagged for Review pages (root flagged.html, flagged-review.html, pages/flagged.html). Flagged items do not block publication per user instruction.
