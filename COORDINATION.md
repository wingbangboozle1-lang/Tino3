# COORDINATION.md — Shared Task Board

Repo: wingbangboozle1-lang/Tino3
Last updated: 2026-11-10

## Active / recent sessions

| Session ID | Branch | Status | Notes |
|---|---|---|---|
| `arena-a0172814-tino3` | `arena/a0172814-tino3` (fixed by platform) | **active — owns tasks 1–5 below** | Integration session for this round. |
| `arena-d11336c5-tino3` | `arena/d11336c5-tino3` | done / merged (PR #1) | Built v1 site (13 files) that is currently on `main`. Its research claims are being re-verified line by line below. |
| `arena-0765efc4-tino3` | `arena/0765efc4-tino3` | abandoned (claim-only commit `4fdb4fa` from the initial commit, no site work, >60 min stale) | Task handoff noted below. Nothing to salvage. |

## Task board (current round)

| # | Task | Status | Owner session | Files touched | Sources / verification | Irregularities |
|---|------|--------|---------------|---------------|------------------------|----------------|
| 1 | Re-verify every v1 figure line by line against official sources (IRS, BOE, FTB, CA Courts, county assessors, CPUC, SFPUC, SJWC) | in progress | arena-a0172814-tino3 | `data/*.json`, `SOURCES.md` | see `SOURCES.md` verification log | see Flagged page |
| 2 | Build canonical data layer (single JSON source of truth for all tables, values, sources) | in progress | arena-a0172814-tino3 | `data/*.json`, `build.py` | n/a | |
| 3 | Rebuild site: landing dashboard + category subpages, table-first, every row sourced | unclaimed→in progress | arena-a0172814-tino3 | `index.html`, `*.html`, `assets/*` | n/a | |
| 4 | Projections engine 2026–2060 (values, assessed values, Prop 13 tax, costs, inheritance, sell-vs-hold-vs-rent NPV) | in progress | arena-a0172814-tino3 | `data/projections.json`, `projections.html`, `decision.html` | assumption table with citations | |
| 5 | Flagged-for-Review page + verification report; link check; final integration, PR, merge, confirm Pages deploy | pending | arena-a0172814-tino3 | `flagged.html`, `COORDINATION.md` | n/a | |

## File ownership (non-overlapping)

`arena-a0172814-tino3` owns the entire file tree this round (`data/`, `assets/`, all `*.html`, `build.py`, `SOURCES.md`, this file). No other session is active.

## Rules followed

- Personal information anonymized; placeholders only. No names, addresses, APNs, account numbers anywhere in the repo or site.
- Rounded to nearest $10 in all cost/number reporting; raw exact figures kept only where a law specifies an exact statutory amount (e.g. $1,044,586 Prop 19 adjustment, $15,000,000 federal exclusion) and explicitly labelled as statutory.
- Every table row carries a source link to an official source where one exists; anything unconfirmable is left blank and flagged `UNVERIFIED`.
- No hallucinations: every number is either (a) cited to a source, (b) user-provided input, or (c) a labelled `ASSUMPTION` in the assumption register.

## Handoff / change log

- 2026-11-10 — `arena-a0172814-tino3` claimed tasks 1–5. Claim pushed immediately.
- 2026-11-10 — Took over task from stale `arena-0765efc4-tino3` (claim-only commit, no work produced, claim >60 min stale). No files to recover.
- 2026-11-10 — v1 site (from `arena-d11336c5-tino3`, merged as PR #1) reviewed. It contained several unverified/secondary-source figures and at least one arithmetic error carried into the executive summary. This round replaces the data layer with a generated, source-linked one.
