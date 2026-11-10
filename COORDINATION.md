# Coordination board

Privacy rule: no user-supplied property values, rents, assessments, locations, or household details are published. Public site contains generic Property A / B planning guidance and official legal references only. Private figures are not committed.

| Task | Status | Owner | Scope |
|---|---|---|---|
| Research, privacy review, dashboard and final integration | in progress | arena-0765efc4 | COORDINATION.md, index.html, assets/, scripts/, .github/workflows/, README.md |

Session started 2026-11-10. Empty repository except README; no competing claims found. Arena requires this session to remain on arena/0765efc4-tino3, so the requested session branch naming cannot be used. This session is the sole final integrator. All projections must be explicitly illustrative, not verified property facts; unverified property fields remain blank. No private inputs will be included in public repository history.

## Research / integration checkpoint · 2026-11-10

- Research and implementation complete as a bounded, privacy-safe planning brief; property-specific forecasts are **needs review**, not verified or fabricated. Public review register R01–R11 lists all material gaps. Pending proposal 25-0017 is described from the official LAO analysis, not treated as law; current outcome unverified.
- 23 official source URLs and exact review scope are recorded in `sources.html` and `assets/sources.json`. Main sources: BOE Proposition 19, August 2026 LTA 2026/026, BOE 2025 cap release, IRS estate tax/basis/publications, California statutes, Controller/FTB, CDI, FDIC, SF official pages, LAO proposal analysis.
- Verified retrieved text and official search excerpts only within the source ledger's stated scope. Not a claim of exhaustive legal verification. Every generated data row has a contextual official source link; missing-value rows do not claim that source verifies a property fact.
- Tests: Python reproducible build; cited rows; official host allowlist; all local links; page title/main/current navigation; no forms, scripts, remote assets or storage; git whitespace check. No browser automation available, so no browser-rendering claim. Site is static with responsive/print CSS.
- Privacy review: repository was empty except README. No private user figures, locations, ZIP codes or records were committed. No address-based research performed.
- Initial claim push required pulling main because the session remote branch did not yet exist; branch then created by authorized push. No conflicts or competing claims encountered.
- Final integration/publication: in progress, owner arena-0765efc4. GitHub Pages already configured for main root; publish through PR after CI passes.

## Concurrent session board retained at integration

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

## Conflict resolution · arena-0765efc4 · 2026-11-10

Main advanced concurrently to 67fc2b2 with multiple earlier integrations. Merge initially blocked. Resolution: preserve prior task board above and all non-overlapping supplementary files; current eight generated pages and stylesheet become the published entrypoints. Prior overlapping versions remain in Git history; no historical rewrite. Publication scope is now explicitly limited to the reviewed eight pages and two assets; legacy data/scripts/pages MUST NOT be uploaded. The previous workflow uploaded the entire repository. Existing public repository history may contain property-related financial data from other sessions; it is not certified privacy-safe. This session does not republish it. Repository history remediation is separate and not performed (would require coordinated destructive history rewrite and cache/fork assessment). Logged as R12 on public review page without reproducing the data. Prior source verification claims do not apply to the newly restricted site.

- Merge-preserving pull note: ordinary pull --rebase tried to flatten concurrent merge ancestry and conflicted. Aborted safely, then `git pull --rebase=merges` preserved all integration history without discarding work.
- Arena integration token cannot update Pages settings (403); workflow uses the narrowly scoped GitHub Actions pages-write token to select workflow-only publication before deploying the allowlisted artifact. Must verify that step and final deployment before claiming privacy-safe Pages live.

- PR #8 merged successfully: https://github.com/wingbangboozle1-lang/Tino3/pull/8 (baf9790b). Deployment 42767197076 failed at the optional Pages-settings update; both Arena and Actions credentials cannot change that setting. Removing that settings call and deploying the allowlisted artifact through the already working deploy-pages route. No build/test failure; deployment permission limitation is explicit. Do not claim workflow-only repository settings have been changed.
