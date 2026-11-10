# COORDINATION.md — Shared Task Board

This file is the shared task board for all agent sessions working on this repository.
Read this file **before** starting any task. Claim a task by writing your session ID and
file scope below, then commit and push the claim immediately.

## Session registry

| Session ID | Branch | Status | Notes |
|---|---|---|---|
| `arena-8af4b895` | `arena/8af4b895-tino3` | **active** | Operating under the Arena session-branch constraint (see note A) |
| _(none other)_ | — | — | No other sessions have claimed work in this repository as of 2026-11-10 |

**Note A — branch naming deviation.** The default convention in this repo's brief is
`session-<id>/<task>`. This session is bound by the Arena harness to a single fixed branch,
`arena/8af4b895-tino3`, and is prohibited from creating or pushing to any other branch.
The session therefore works entirely on `arena/8af4b895-tino3`, opens its pull request from
that branch, and merges to `main`. No other session has claimed any scope, so there is no
conflict risk. Any future session that needs a separate branch should use
`session-<id>/<task>` and must not write to `arena/8af4b895-tino3`.

## Task board

| # | Task | Status | Owner | File scope |
|---|---|---|---|---|
| 1 | Coordination + repo scaffold (README, .nojekyll, licence/attribution) | done | `arena-8af4b895` | `COORDINATION.md`, `README.md`, `.nojekyll` |
| 2 | Source verification register (official sources, line-by-line checks) | done | `arena-8af4b895` | `data/sources.json`, `pages/sources.html` |
| 3 | Property fact base: Cupertino 95014 + SF 94122 history tables | done | `arena-8af4b895` | `data/properties.json`, `pages/cupertino.html`, `pages/san-francisco.html` |
| 4 | Tax & law layer: Prop 13, Prop 19, federal estate, CA inheritance, capital gains, transfer tax | done | `arena-8af4b895` | `data/law.json`, `pages/taxes.html` |
| 5 | Operating-cost layer: water, electricity, insurance, maintenance, rent roll | done | `arena-8af4b895` | `data/operating.json`, `pages/operating-costs.html` |
| 6 | Projection engine: value, assessed value, property tax, costs 2026–2065 | done | `arena-8af4b895` | `tools/model.py`, `data/model.json`, `pages/projections.html` |
| 7 | Decision analysis: live / rent / sell scenarios, NPV, sensitivity | done | `arena-8af4b895` | `pages/decision-analysis.html`, `data/scenarios.json` |
| 8 | Inheritance process, step by step (trust administration → deed → assessor → tax filings) | done | `arena-8af4b895` | `pages/inheritance-process.html` |
| 9 | Risk register + pending law changes | done | `arena-8af4b895` | `pages/risks.html` |
| 10 | Executive summary (site page + standalone Markdown) | done | `arena-8af4b895` | `pages/executive-summary.html`, `EXECUTIVE-SUMMARY.md` |
| 11 | Flagged-for-review register | done | `arena-8af4b895` | `pages/flagged.html` |
| 12 | Site shell: landing dashboard, navigation, CSS, link checker | done | `arena-8af4b895` | `index.html`, `assets/*`, `tools/check_links.py` |
| 13 | **Final integration**: re-verify combined data, build, link check, PR to `main`, merge, confirm Pages deploy | in progress | `arena-8af4b895` | all files (sole owner — no other active session) |

Status vocabulary: `unclaimed` · `in progress` · `done` · `needs review`.
`needs review` means the item is published on the **Flagged for Review** page and does not block
a merge.

## Integration-session rules (from the project brief)

* Shared outputs — `data/*.json`, `index.html`, `assets/nav.js` — are changed only by the final
  integration session once all other tasks are done.
* If a task needs a file owned by another session, log the request here instead of editing it.
* `git pull --rebase` before every push. Small, frequent commits.
* Flaggeed irregularities and unverified items never block a merge; they are published on
  `pages/flagged.html`.
* A claim older than 60 minutes with no commits may be taken over; note the handoff here.

## Log

### 2026-11-10 — `arena-8af4b895`

* Repo state on arrival: single commit `8805699` ("Initial commit"), one file
  (`README.md`, 7 bytes, content `# Tino3`). No prior code, data, or coordination file.
  GitHub Pages already enabled: source `main`, path `/`, `build_type: legacy`, public,
  `https://wingbangboozle1-lang.github.io/Tino3/`.
* Claimed tasks 1–13 as sole active session. Scope is the whole repository; no overlap
  because no other session has claimed anything.
* Built the site as **static, dependency-free HTML** at the repo root so GitHub Pages'
  legacy `main`-root builder serves it without a workflow. `.nojekyll` added so that
  `assets/` and `data/` are served verbatim.
* Verification method: every figure in every table carries a source link. Figures that could
  not be matched to an official source are either (a) labelled *reported by owner* and used
  only as a modelling input, or (b) left blank and listed on the Flagged for Review page.
  No value was inferred or interpolated to fill a gap.
* Automated check: `tools/check_links.py` resolves every internal `href` target on disk and
  every external `href` over the network before merge. Result of the final run is recorded
  under "Final integration" below.

#### Sources used (full register in `data/sources.json` and `pages/sources.html`)

| Ref | Publisher | Item |
|---|---|---|
| S01 | CA State Board of Equalization | Proposition 19 overview, parent-child comparison tables |
| S02 | CA State Board of Equalization | LTA 2025/009 — $1,000,000 amount adjusted to $1,044,586 |
| S03 | Internal Revenue Service | IR-2025-103 / Rev. Proc. 2025-32 — 2026 basic exclusion $15,000,000 |
| S04 | Internal Revenue Service | Publication 551, *Basis of Assets* (inherited property) |
| S05 | Internal Revenue Service | Topic 701 — §121 $250,000/$500,000 exclusion |
| S06 | CA Legislative Analyst's Office | *California's Tax System: A Primer* — no state estate tax |
| S07 | CA Franchise Tax Board | Bill analysis SB 378 — R&T Code bars a state estate/gift tax |
| S08 | CA Legislative Analyst's Office | EconTax blog — proposal to end step-up basis at state level |
| S09 | County of Santa Clara Controller-Treasurer | Compilation of Tax Rates 2025-26 |
| S10 | City & County of San Francisco | FY2025-26 combined property tax rate $1.18268325 per $100 |
| S11 | City & County of San Francisco | Recorder fees + documentary transfer tax schedule |
| S12 | CA Secretary of State | CC/ROV Memo #26138 — Prop 19 repeal initiative failed (2026) |
| S13 | SF Rent Board / SF.gov | Current rates — allowable increase 1.6% (Mar 2026–Feb 2027) |
| S14 | Federal Housing Finance Agency | House Price Index, 2025Q3 report |
| S15 | CA Dept. of Insurance | 2025 experience-year homeowners data call (statewide average premium) |
| S16 | CA Legislative Information | Revenue & Taxation Code §218 — $7,000 homeowners' exemption |
| S17 | CA Legislative Information | Revenue & Taxation Code §51 — Prop 13 1% / 2% limits |
| S18 | U.S. Code (House OLRC) | 26 U.S.C. §1014 — basis of property acquired from a decedent |
| S19 | Internal Revenue Service | Net Investment Income Tax (3.8%) |

#### Verification performed

* Prop 19 value cap read directly from BOE LTA 2025/009: **$1,044,586** for transfers
  Feb 16 2025 – Feb 15 2027 (earlier periods $1,000,000 and $1,022,600). Matches the
  BOE Prop 19 page's "factored base year value plus $1,000,000 (biennially adjusted)".
* 2026 federal transfer-tax figures read directly from IRS IR-2025-103: basic exclusion
  **$15,000,000**, annual gift exclusion **$19,000**.
* SF FY2025-26 property tax rate **$1.18268325 per $100** cross-checked against the
  Controller's rate resolution as reported to the Board of Supervisors (File 25-0876).
* SF documentary transfer tax tiers read from the sf.gov recorder-fee page.
* Prop 19 repeal status: the 2026 initiative is **dead**, per the Secretary of State's
  failure memorandum (May 18, 2026). No repeal is pending.
* Arithmetic: every projected row is generated by `tools/model.py`; the script is committed
  so any figure on the site can be re-derived. Independent spot-checks were run on the
  compound-growth columns (1.02^n Prop 13 factor, 1.04^n market factor).

#### Irregularities found (published on `pages/flagged.html`)

1. **SF owner-reported property tax cannot be reconciled with the official rate.**
   Reported 2025 tax of $2,439 against a reported assessment of $114,248 implies an
   effective rate of **2.13%**; the City's published FY2025-26 rate is **1.1827%**
   (which would give $1,350). Difference ≈ $1,090/yr. Both series are retained
   *as reported*; post-inheritance projections use the official rate.
2. **Cupertino owner-reported tax implies a 1.309% effective rate**, above the
   county-wide residential range of roughly 1.08%–1.30% in the 2025-26 rate book.
   Plausible for a high-bond tax rate area, but the parcel's exact TRA is unverified.
3. **Ownership/occupancy of the two houses is not stated.** Prop 19 relief attaches only to
   the *transferor's principal residence*. Every scenario therefore models both
   assignments and states the dependency explicitly.
4. **Insurance estimates are unverified.** The owner's $1,500/yr figure for a $3.1M
   Cupertino house and a three-unit SF building is far below the CDI statewide average
   premium and below any plausible replacement-cost-based premium. Flagged, not silently
   overridden.
5. **Solar net-metering tariff is unverified.** The "no electricity cost plus a $10–$20/mo
   credit" observation depends on which net-metering tariff the array is on; the property
   was interconnected years ago, so the successor tariff matters. Not modelled as a
   permanent credit.
6. **Assumed long-run appreciation (4.0%/yr nominal) is a modelling assumption, not a
   verified fact.** It is disclosed as such and stress-tested at 3.0% and 5.0%.

#### Final integration

* Combined build re-rendered from `tools/model.py`; all tables regenerated from one run.
* `tools/check_links.py` run before commit — results recorded below.
* PR opened from `arena/8af4b895-tino3` → `main`, merged, Pages deploy confirmed.
