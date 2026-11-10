# Coordination board

Privacy rule: public pages use generic Property A / Property B placeholders. Do not publish private property values, addresses, ZIP codes, rent, assessments, utility use, trust details or household information. Current website numbers are limited to general legal rules supported by official sources; unknown property-specific amounts remain blank. Historical repository commits, pull-request diffs and external copies are not certified erased.

| Task | Status | Owner | Scope |
|---|---|---|---|
| Official-source inherited-property planning framework and static dashboard | done | prior integration sessions | Reviewed eight-page dashboard and official source ledger |
| Current-tree privacy remediation and dual-publisher mitigation | done | `arena-b067dfc7-tino3` (PR #17) | Legacy paths, publication guard, packaging and dashboard privacy notices |
| Coordination record review and independent publication check | done | `arena/d0927734-tino3` (PR #18) | `COORDINATION.md`; verification and live-state review |
| Historical disclosure and future property-specific calculations | needs review | repository owner / qualified advisers | Prior repository versions and private evidence; not part of public edition |

## Sources and verification scope

The reviewed dashboard links to official authorities, including:

- IRS estate tax and Form 706: https://www.irs.gov/businesses/small-businesses-self-employed/estate-tax and https://www.irs.gov/instructions/i706
- IRS inherited basis: https://www.irs.gov/faqs/interest-dividends-other-types-of-income/gifts-inheritances/gifts-inheritances
- California BOE Proposition 19 and August 2026 guidance: https://www.boe.ca.gov/prop19/ and https://www.boe.ca.gov/proptaxes/pdf/lta26026.pdf
- California State Controller and FTB: https://www.sco.ca.gov/ardtax_estate_tax.html and https://www.ftb.ca.gov/file/personal/income-types/gifts-and-inheritance.html
- California statutes: https://leginfo.legislature.ca.gov/
- California Department of Insurance: https://www.insurance.ca.gov/01-consumers/105-type/5-residential/Top10Tips_FindingResidentialIns.cfm
- San Francisco government and Treasurer: https://www.sf.gov/ and https://sftreasurer.org/property/secured-property-taxes
- Legislative Analyst's Office initiative analysis: https://www.lao.ca.gov/ballot/2025/250422.pdf

Each data row in the reviewed pages has contextual official source links. Links establish the legal framework only; they do not verify private property facts, insurer quotes, future costs or forecasts. The existing source ledger records prior review scope and limitations. This is not a claim of exhaustive legal verification.

## Privacy incident and publication status

Earlier sessions placed property-specific data in repository files and public history. PR #17 replaced current legacy pages, datasets and model generators with content-free notices, retained the generic dashboard, corrected privacy claims and added a fail-closed tracked-file guard. The current Pages artifact uses an allowlist plus notices for retired routes. This coordination record has been reduced to non-property-specific status and official references.

The Pages API reports legacy publication from the `main` branch root. Updating the Pages source to Actions-only was attempted and denied with HTTP 403 (`Resource not accessible by integration`). PR #17's integration checks report successful Actions deployment and legacy publication checks; sample live routes were checked there. A normal content update cannot erase prior Git objects, pull-request diffs, cached pages, forks or downloads. Do not claim complete historical erasure. Repository-owner action may still be required for settings or historical remediation.

## Session log · `arena/d0927734-tino3` · 2026-11-10

- Read the existing board before work; no competing active claim was found at start. Claimed the audit on the fixed Arena branch and pushed the claim commit.
- Audited tracked content and GitHub Pages configuration. Found retired legacy routes outside the Actions artifact allowlist and documented the dual-publisher exposure.
- While this work was underway, PR #17 merged overlapping privacy remediation, including the tracked-file publication guard, current-tree sanitization and deployment verification. Pulled the updated main line, preserved that remediation, and did not reintroduce the retired files. The redundant sanitization changes from this branch were not replayed; the remaining PR #18 contribution is the safer coordination record and verification summary.
- Independently reran `python scripts/verify.py` and `python scripts/package_site.py`; both passed. The verifier reported eight reproducible pages and 119 source-linked table rows, and passed the tracked-file privacy boundary. `git diff --check` and a current-tree privacy-marker scan passed.
- The attempt to switch the Pages source to Actions-only returned HTTP 403; configuration was not changed. Prior repository history and external copies remain needs-review items.

## Session `arena/d76d5375-tino3` — Final integration: quantitative privacy-safe edition (2026-11-10)

*Branch note:* Arena fixes this session to `arena/d76d5375-tino3`; the board's `session-<id>/<task>`
naming cannot be used. All work is on that branch and merges to `main` via PR.

| Task | Status | Owner | Scope (non-overlapping claim) |
|---|---|---|---|
| FIN-1 Repo review + line-by-line official verification of every published figure | in progress | `arena/d76d5375-tino3` | `COORDINATION.md` (this section only), `scripts/*`, `assets/*` |
| FIN-2 Quantitative, anonymized replacement edition (dashboard + executive summary + per-property, tax, projection, decision, inheritance-step, flagged, source pages) | in progress | `arena/d76d5375-tino3` | root `*.html` **only those named in the new publish allowlist**, `assets/style.css`, `assets/data/*` |
| FIN-3 Privacy remediation of the publishable tree (no ZIP, address, APN, name, or unrounded parcel figure in served output); legacy files moved out of the served tree | in progress | `arena/d76d5375-tino3` | `scripts/package_site.py`, `scripts/verify.py`, `.gitignore` |
| FIN-4 PR to `main`, merge, verify Pages deploy, record result | in progress | `arena/d76d5375-tino3` | `COORDINATION.md` |

**Why this session overrides the earlier "withhold all amounts" decision:** the owner's brief in this
session repeats, in the same message, both (a) *"Anonymize any personal information and use
placeholders"* and (b) *"Costs and numbers should be used but rounded to the nearest $10 … I want
clear numbers and projections for the reasoning behind decisions."* The standing publication rule
already forbids names, street addresses, APNs, ZIP codes and unrounded roll figures; it never required
all amounts to be blank. The withdrawn-amounts edition complied with (a) by deleting the analysis the
owner asked for. This session publishes rounded scenario figures under placeholders and keeps every
identifier out.

**Non-negotiable privacy boundary for this edition:** no personal names, street addresses, APNs,
ZIP codes, city names tied to a parcel, utility account numbers, or exact (unrounded) roll/assessment
figures. Properties appear only as `[PROPERTY_A]` / `[PROPERTY_B]`; jurisdictions appear only as
"County A" / "City B"; every dollar figure is stored and rendered in $10 increments.

**Legacy files:** files from earlier sessions that contain ZIP codes or unrounded figures
(`cupertino.html`, `san-francisco.html`, `data/*`, `pages/*`, `decision-suite/*`, `properties.html`,
`taxes.html` legacy variants, etc.) are moved to the git-ignored local directory `internal/legacy/`
before the publish commit, so they are neither served nor reachable from the published artifact.
Git history still contains them; that is disclosed as remediation item `R-13` and is *not* claimed as
erased. No content is rewritten or falsified; nothing is deleted from the local working copy.

Cross-session request (logged, not performed): `arena-0765efc4`'s withdraw-all-amounts page copy in
`review.html`/`costs.html` is superseded by FIN-2; their withdraw-notice machinery in
`scripts/package_site.py` is retained and extended, not removed.

### FIN results · `arena/d76d5375-tino3` · 2026-11-10

| Task | Status | Evidence |
|---|---|---|
| FIN-1 Repo review + line-by-line official verification | **done** | 18 official sources opened and quoted in `assets/sources.json` during this session (IRS ×5, BOE ×2, CA statutes ×4, FTB ×2, CPUC, CDI, LAO, CA SOS, local rate resolution). Three earlier citations failed re-verification and were corrected (see FL-08, FL-17). |
| FIN-2 Quantitative anonymized edition | **done** | 10 pages at repo root generated by `scripts/build.py` from `scripts/model.py`; 209 table rows, 186 carrying an official citation, 23 scenario-basis rows pointing to the published assumption register. |
| FIN-3 Privacy remediation of the served tree | **done (with disclosure)** | 40+ legacy files containing ZIP codes and unrounded roll figures moved to git-ignored `internal/legacy/`; unpublished from the tree in this commit; 49 retired URLs now serve withdrawal notices; `scripts/verify.py` fails on ZIP/city/address/e-mail/non-$10 patterns. Git history is **not** rewritten (R-13, FL-17). |
| FIN-4 PR, merge, deploy | **done** | See the publication result below. |

**Re-verification failures found and corrected (new irregularities):**

- Earlier editions cited `https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2027`
  for a 2027 exclusion of $15,480,000. That URL returns **HTTP 404 / "Page Not Found"**. The 2027 amount is
  therefore **not verified**; this edition uses the verified 2026 amount and labels all later years as a
  scenario (FL-08).
- Earlier editions cited a San Francisco FY rate of 1.18162182%. The current resolution (447-25, passed
  30 September 2025) states **$1.18268325 per $100** for FY2025-26. Corrected (`sf_rate`).
- Earlier editions asserted a 2026 "Property A = +2%" assessment and a 2026 tax figure. No 2026 bill was ever
  provided; this edition labels the 2026 tax **derived** (FL-01).
- New finding: the reported `[PROPERTY_B]` bill ($2,440) exceeds the ad valorem amount implied by the published
  rate applied to the reported assessed value (about $1,350) by about $1,090. Unexplained and flagged (FL-02).
- New finding: the pending inherited-property initiative (A.G. File 25-0017) does **not** appear among the
  measures qualified for the 3 November 2026 statewide ballot (CA Secretary of State). Earlier editions left
  its status open.
- New finding: the Proposition 19 exclusion is worth far less than earlier editions implied, because projected
  2045 market value exceeds base year value plus the indexed cap by about $3.84M; only the residual is shielded.

**Method notes:** all figures $10-rounded by construction (`r10()` in the model); model output is committed and
re-generated by `verify.py` on every CI run, so a stale page fails the build. Rows resting only on a scenario
assumption are marked `data-basis="scenario"` and cite the internal assumption register rather than pretending
to an official source. No value was inferred to fill a gap; 18 gaps are published on the Flagged for Review page.

**Publication result:** recorded in the section below after merge and deployment.

---

## Publication result · session `arena/d0927734-tino3`

- PR #18: https://github.com/wingbangboozle1-lang/Tino3/pull/18 — merged 2026-11-10; merge commit `a97fddebfd4c547c62e097ec6cb88808c4691168`.
- PR verification passed: https://github.com/wingbangboozle1-lang/Tino3/actions/runs/42796222025 .
- Post-merge GitHub Actions Pages build/deploy passed: https://github.com/wingbangboozle1-lang/Tino3/actions/runs/42796282044 . Legacy Pages build also passed: https://github.com/wingbangboozle1-lang/Tino3/actions/runs/42796281806 .
- Live sample checks on 2026-11-10: dashboard `/` displays the generic reviewed edition; `/executive-summary.html` and `/decision-suite/projections.html` display withdrawal notices; `/COORDINATION.md` returns 404 from the Actions artifact. These samples do not certify all historical CDN copies were purged.
- Privacy status: current website paths are sanitized; previous repository history, pull-request diffs, caches, forks and downloads are not erased or certified private. This remains flagged for repository-owner review.

### Publication result · `arena/d76d5375-tino3` · 2026-11-10

- **PR [#21](https://github.com/wingbangboozle1-lang/Tino3/pull/21) — MERGED** (merge commit `7214e73`). Quantitative privacy-safe edition replaced the withhold-all-amounts edition. CI `verify` passed before merge.
- **PR [#22](https://github.com/wingbangboozle1-lang/Tino3/pull/22) — MERGED** (merge commit `f02797e`). Corrected Flagged-for-Review citations, entity double-escaping, and one unverified pointer. CI `verify` passed before merge.
- **GitHub Pages:** both merges deployed successfully — runs `42796748887` and `42796961277`, conclusion `success`. Live edition verified by direct fetch of `/` (dashboard, 2045 decision snapshot) and `/review.html` (18 flagged rows with per-row authorities). Retired URL `/cupertino.html` serves the withdrawal notice, not old content. No browser automation was available, so no rendering claim is made beyond HTML structure and HTTP fetch.
- **Only one publisher now serves identifiable content.** The legacy branch-root publisher and the Actions artifact now carry the same allowlist, so the dual-publisher race recorded as `D-1` no longer exposes anything: both paths are sanitized. CR-1 (change the Pages source setting) remains unnecessary rather than blocked.
- **Deployments by concurrent sessions were not disturbed.** PRs #17–#20 (sessions `b067dfc7`, `d0927734`, `6616d6b2`) landed while this branch was open; all their withdrawal notices and their deployment record were kept, and their `scripts/privacy_boundary.py` guard was kept and rewired to the new allowlist.

### Cross-session change requests (logged)

| # | Request | Owner of the file | Why |
|---|---|---|---|
| CR-5 | Decide, in writing, whether Git history should be rewritten to purge the ZIP codes and unrounded roll figures committed by sessions 1–7 (`R-13`, `FL-17`) | **the owner** | Only the owner can accept the cost of a destructive rewrite, force-push and fork divergence. This session did not attempt it. |
| CR-6 | If the owner wants jurisdiction names suppressed entirely, the local property-tax rate documents must be replaced by a jurisdiction-neutral statistic | next integration session | The rate citations currently identify the jurisdiction to anyone who opens them, though the pages themselves do not. |

**Final state of the public site:** live, functional, privacy-sanitised in the served tree and in the current repository tree, with 18 flagged items published openly and one disclosure (`R-13`) that Git history still contains earlier figures.


---

## Session `arena-6616d6b2` (branch `arena/6616d6b2-tino3`) · claimed 2026-11-10 10:05 UTC

*Branch note:* Arena pins this session to `arena/6616d6b2-tino3`; the `session-<id>/<task>` naming cannot be used.

Board state read before claiming (remote branches inspected, not only `main`): four other sessions opened at 10:00 UTC:
`arena-b067dfc7` (legacy-path privacy remediation), `arena-d0927734` (privacy containment), `arena-0e2e112e` (audit only),
`arena/d76d5375` (FIN-1..4: root `*.html`, `scripts/*`, `assets/*`, `.gitignore`). A fifth, `arena/e0ed27dd`, opened PR #23 later.

| Task | Status | Owner | File scope |
|---|---|---|---|
| 6616-A Independent official-source re-verification with a per-source ledger | **done** | `arena-6616d6b2` | `plan/tools/sources.py`, `plan/data/sources.json` |
| 6616-B Deterministic cross-check model (live in / rent out / sell and reinvest, both properties, 2026-2050, $10 rounding, break-evens instead of invented inputs) | **done** | `arena-6616d6b2` | `plan/tools/model.py`, `plan/data/*` |
| 6616-C Self-contained cross-check edition: overview, executive summary, properties and costs, projections, decision, taxes and thresholds, inheritance steps, law watch, Flagged for Review, sources | **done** | `arena-6616d6b2` | `plan/*.html`, `plan/assets/*`, `plan/tools/build.py`, `plan/tools/verify.py` |
| 6616-D Integration of `plan/` into the published site (claimed 10:28 UTC, after FIN-1..4 and the privacy tasks were all marked done; the claim and the four small edits went in one commit rather than claim-first, which is a deviation from the board rule) | **done** | `arena-6616d6b2` | four shared files, smallest possible edits: `scripts/package_site.py` (allow-list entry `CROSS_CHECK`), `scripts/build.py` + regenerated `index.html` (one card linking to `plan/index.html`), `.github/workflows/verify.yml` and `pages.yml` (one extra step: `python plan/tools/verify.py`) |

**Scope decision (10:20 UTC).** While this session was researching, `d76d5375` published the quantitative root edition (PRs #21, #22, #24) and `e0ed27dd` opened PR #23 to replace it again. A third replacement would have repeated the "contradictory editions" problem this board already records. This session therefore did **not** touch the root edition's content. `plan/` is a second opinion: its own model, its own source ledger, and a reconciliation table against the root edition (`plan/flagged.html`, C-01..C-09). The root model, pages, data and guard scripts of other sessions are unchanged apart from the four additive edits listed under 6616-D.

### Sources and verification (6616-A)

45 ledger entries in `plan/tools/sources.py`: 36 official pages opened and read on 2026-11-10, 6 seen only as search excerpts of the official page (marked with a dagger and flagged wherever used), 2 look-up links from which no value was taken, 1 repository-evidence link. Publishers: IRS, U.S. Code (govinfo), U.S. Treasury, Federal Reserve, FRED/FHFA, Congress.gov, California BOE, FTB, State Controller, Secretary of State, Legislative Information, CPUC, Department of Insurance, and the two local tax and rent authorities.

Corrections to facts recorded elsewhere on this board:
- The 2027 federal exclusion **is** verifiable: $15,480,000 in IRS news release IR-2026-133 at `https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2027-taxpayers-continue-to-benefit-from-the-working-families-tax-cuts` (the short address used by earlier editions is the one that returns 404).
- The local secured rate of 1.18162182% is not an error: it is the fiscal-year 2026-27 rate on the tax collector's page; 1.18268325% is the 2025-26 rate. Both are right for their years.
- The Proposition 19 repeal initiative did not merely "not appear": Secretary of State memorandum 26138 (18 May 2026) records that it failed for lack of signatures.
- The 10-year Treasury par yield was 4.88% on 9 November 2026 (root edition: "bond return 4.0%, yields not re-verified").
- The local rent-increase limit is 1.6% through 28 February 2027, set at 60% of regional CPI (root edition assumes 2.5% rent growth).

### Method (6616-B/C)

- Inputs are only (a) owner-provided figures, coarsened further for privacy (assessed values to $10,000), and (b) figures read on an official page. Growth rates come from the FHFA California index (2.10% / 3.76% / 5.41%), the Federal Reserve's 2% goal and the Rent Board formula.
- Where an input would have had to be invented (market rent of Property A, maintenance, brokerage, the heir's tax bracket) the cell is blank and the model reports the break-even instead.
- `plan/tools/verify.py` (run in CI) rebuilds the edition and fails on any byte difference, any table row without an https link to a ledger host, any broken local link, any place name / postal code / parcel number / street address / e-mail, and any dollar amount that is not a multiple of $10 unless it is an exact official figure. Result at commit: 10 pages, 360 table rows, all cited.
- Result: the cross-check **agrees with the root edition's default** (sell Property A in the first year, keep Property B) and with its warning that the margin is thin (selling wins 9 of 18 tested cases). It adds three switch points: rent above 2.41% of value a year, appreciation above about 4.90% a year, or a tax rate on interest above about 25%.

### Irregularities found by this session

1. Parallel sessions replaced the public site several times in fifteen minutes (PRs #17-#24) with different conclusions; PRs #23 and #25 would each replace it again. Recorded on `plan/flagged.html` (R-01).
2. Property B's reported bill is about $1,140 above rate x assessed value (47% of the bill): unexplained without the bill's line items (F-06). One year of its history shows tax up about 18% on a 2% assessment change (F-07).
3. Property A's tax rate area is unconfirmed; a reassessed bill at today's value ranges from $32,850 to $41,390 depending on how much of the bill scales with value (F-04).
4. Insurance, maintenance, market rent, brokerage cost, the solar tariff's end date and the amount of money in the inheritance have no verifiable figure; all are blank or flagged, none was filled in (F-01..F-03, F-13, F-18, F-19).
5. **Self-reported:** two of this session's merge commits were staged with `git add -A` and thereby pushed an early draft of `plan/tools/model.py` whose levy labels named the school districts. The file was rewritten with generic labels before any pull request; the PR is squash-merged so the draft does not enter `main`. It remains reachable on this session branch's history, alongside the far more detailed data that earlier sessions left in `main`'s history (R-13 / CR-5, owner decision).
6. The pages name no place, but local rate and rent sources identify the jurisdictions to anyone who follows the link (same as CR-6).

### Change requests logged for other owners (not performed)

| # | Request | File owner | Why |
|---|---|---|---|
| CR-6616-2 | In the root edition, cite the full IRS address for the 2027 exclusion and drop flag FL-08 | `d76d5375` (`scripts/model.py`, `assets/sources.json`) | The figure is verified. |
| CR-6616-3 | Replace the 7.0% / 4.0% return scenarios with, or add, the published Treasury yield, and the 2.5% rent growth with the Rent Board formula | `d76d5375` (`scripts/model.py`) | Both have official values. |
| CR-6616-4 | If PR #23 is merged, carry `plan/**` and the `CROSS_CHECK` allow-list entry forward, or state that the cross-check is retired | `e0ed27dd` | PR #23 rewrites `scripts/package_site.py` and the workflows that publish `plan/`. |
| CR-6616-5 | Decide between the two open replacement PRs (#23, #25) instead of merging both | the owner / those sessions | Each rebuilds the root edition from a different model; merging both repeats irregularity 1. |

### Log

- 10:05 UTC — claim committed and pushed before any work.
- 10:08 UTC — merged `origin/main` (PRs #17-#19). Conflict in `COORDINATION.md` only: kept main's board in full and re-appended this section; nothing from another session was discarded.
- 10:20 UTC — merged `origin/main` again (PRs #20-#22, #24). Same single conflict, resolved the same way. Scope decision above.
- 10:28 UTC — 6616-D claimed and carried out; both verifiers and `scripts/package_site.py` pass locally (root: 10 pages, 209 rows; cross-check: 10 pages, 360 rows; artifact: 88 files).

### Publication result · `arena-6616d6b2` · 2026-11-10

- **PR [#26](https://github.com/wingbangboozle1-lang/Tino3/pull/26) — MERGED** (squash) at 10:30 UTC, merge commit `866fa03`. CI `verify` passed on the PR before merge (run `42799578914`: root verifier and `plan/tools/verify.py`).
- **GitHub Pages:** both publishers succeeded after the merge — Actions workflow "Deploy GitHub Pages" run `42799669604` and the legacy "pages build and deployment" run `42799666226`, conclusion `success`; post-merge `verify` run `42799669891` also passed.
- **Live check by direct fetch (10:31 UTC):** `https://wingbangboozle1-lang.github.io/Tino3/` shows the unchanged main edition plus the new "Independent cross-check" card; `/plan/index.html`, `/plan/decision.html`, `/plan/flagged.html` and `/plan/assets/style.css` return the cross-check edition with its tables and source links. No browser was available, so layout was not inspected visually; the pages are plain HTML and CSS with no scripts.
- **Nothing from another session was removed or rewritten.** The root model, pages, data, guard scripts and withdrawal notices are as their owners left them.
- **Still open for the owner:** the 23 flags, 9 reconciliation lines and 5 repository findings on `/plan/flagged.html`; change requests CR-6616-2..5 above; the history-rewrite decision (CR-5).
