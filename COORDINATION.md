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

## Session `arena-760f6413` (branch `arena/760f6413-tino3`) — final integration · 2026-11-10

*Branch note:* Arena fixes this session to `arena/760f6413-tino3`; the `session-<id>/<task>` naming on
this board cannot be used. All work is on that branch and reaches `main` only by pull request.

| ID | Task | Status | Owner | Files |
|---|---|---|---|---|
| 760-A | Official-source research ledger | **done** | `arena-760f6413` | `plan/model/sitekit.py` (ledger), `assets/sources.json` |
| 760-B | Reproducible projection and decision model | **done** | `arena-760f6413` | `plan/model/model.py`, `plan/data/inputs_public.json`, `plan/data/model_outputs.json` |
| 760-C | Dashboard pages built from A and B | **done** | `arena-760f6413` | `plan/model/pages.py`, `plan/model/build_site.py`, root `*.html` named in `plan/data/manifest.json`, `assets/site.css`, `assets/site.js`, `assets/data/*` |
| 760-D | Audit of the repository and of the edition that was live | **done** | `arena-760f6413` | Findings R-01 to R-08 on `review.html` |
| 760-E | Final integration of shared outputs | **done** | `arena-760f6413` | `scripts/verify.py`, `scripts/package_site.py`, `scripts/privacy_boundary.py`, `README.md`, `EXECUTIVE_SUMMARY.md`, root pages |
| 760-F | Items for the owner | **needs review** | repository owner | Flags F-01 to F-22, I-01 to I-05, R-01 to R-03 on `review.html` |

### Claim history

- 10:05 UTC: claimed `plan/**` only (760-A to 760-D) after reading the other session branches directly,
  because claims written on session branches are not visible on `main`. At that moment three sessions
  (`d0927734`, `b067dfc7`, `d76d5375`) had each claimed `scripts/package_site.py`, `scripts/verify.py` and the
  legacy files within one minute of each other, and a fourth (`0e2e112e`) had claimed a report-only audit.
  This session touched none of those files while their claims were open.
- 10:25 UTC: `main` had moved to PR #24. The board on `main` showed every task of the other sessions as
  done (rows FIN-1 to FIN-4, PR #17, PR #18/#20). Under the rule "shared outputs are changed only by a final
  integration session once all other tasks are done", this session then took 760-E.
- Merge conflict: merging `main` into this branch conflicted in `COORDINATION.md` (this session's claim
  against the redacted board). Resolved by keeping the whole of `main`'s board and re-appending this
  section. Nothing from another session was dropped.

### Handoff: why the root edition was rebuilt and not left as it was

The edition merged in PR #21/#22 (`arena/d76d5375-tino3`) stays in the history of `main`. This integration
replaces its ten root pages at the same addresses and turns six of its files into content-free notices
(`scripts/build.py`, `scripts/model.py`, `assets/style.css`, `assets/data/property_a.csv`,
`assets/data/property_b.csv`, `assets/data/decision.csv`). Reasons, each recorded on `review.html`:

1. **Privacy (R-01).** It published both assessed-value histories and both tax-bill histories rounded to
   $10, on the pages and in `assets/data/model.json`, the two CSV files and `scripts/build.py`. Assessment
   rolls are public records; a value that precise can be matched to one parcel and from there to an address
   and an owner. Rounding to $10 follows the owner's wording but does not anonymise these particular
   series. This edition publishes rounded levels and computes every projection from them, so no published
   projection can be inverted to recover the roll figure. Re-running the model on the exact figures changes
   no yearly figure by more than $100 and no 20-year result by more than $1,000.
2. **Out-of-date law (R-04 to R-06).** It described initiative 25-0017 as a live proposal (the Secretary of
   State recorded its failure on 18 May 2026), used a Property B rate of 1.18268325% (the published
   2026-27 rate is 1.18162182%), and did not cover the 2027 federal exclusion, the November 2026 ballot
   results, the September 2026 appeal ruling on the Empty Homes Tax or the unit-by-unit rule in Letter to
   Assessors 2026/026.
3. **One edition.** A final integration has to leave one consistent set of figures. Two parallel editions
   with different models would itself be an irregularity.

Owner decision still open: keep the privacy rounding, or restore exact $10 figures knowing the risk
(one switch: put exact figures in the git-ignored `private/inputs.json` and run the model offline, or
change `plan/data/inputs_public.json`).

### Sources and verification performed

- 55 official sources in the ledger (`assets/sources.json`, page `sources.html`), each marked with how it
  was checked: page read in this session, official page text read through a search excerpt, or official
  starting point only. Publishers: IRS, Board of Equalization, California Legislative Information, State
  Controller, Franchise Tax Board, Public Utilities Commission, Secretary of State, Legislative Analyst,
  San Francisco Treasurer, Assessor-Recorder and Rent Board, Santa Clara County Clerk-Recorder, Department
  of Insurance, the national association of insurance regulators, FHFA, U.S. Treasury, Social Security
  Administration, Thrift Savings Plan, HUD, Congress.gov and the California courts.
- Figures inherited from earlier sessions were re-checked before use: federal exclusion 2026 (confirmed),
  2027 exclusion and gift exclusion (confirmed in IR-2026-133 and Rev. Proc. 2026-35), the $1,044,586 amount
  (confirmed in Letter to Assessors 2025/009), the inflation factors (confirmed in Letter 2026/002), the
  10-year Treasury yield of 4.88% on 9 November 2026 (confirmed).
- The owner's Property A assessed-value series was checked privately against the official factors and
  matches every year to within $1. No parcel lookup of any kind was made.
- `python scripts/verify.py` passes: 13 pages, 358 table rows each with an official source link, 23
  published files byte-reproducible from `plan/`, no broken internal link or anchor, every external link
  https and official, every amount in $10 steps, no postal code or sub-county place name, roll-derived
  inputs coarse. A local-only scan against the owner's exact figures found none in any tracked file.
- `python scripts/package_site.py` builds the artifact: 23 current files and 54 withdrawal notices.

### Irregularities and unverified items (all published on `review.html`; none blocks the merge)

- Left blank because no official figure could be confirmed: both insurance premiums, the statewide
  average premium, the rent Property A could earn, the federal limit on deducting state and local tax.
- Unverified assumptions that carry weight: repair budgets, the Property A tax rate and fixed charges,
  the heir's tax rates, the 7.0% stock return, 6.0% selling costs, the building share of value.
- Facts only the family can confirm: trust type, which home is the principal residence, the solar
  connection date, rent rules for Property B, the size of the cash inheritance.
- Owner's records: Property B bill about 2.1% of assessed value (flat charges); one year slightly under
  the official factor; identical consecutive bills on Property A; a jump and a dip on Property B; no 2026
  bills.
- Repository: earlier commits and pull-request diffs still hold exact figures and postal codes (owner
  action: make the repository private or recreate it); two publishers still deploy (owner action: set the
  Pages source to GitHub Actions); open pull requests from other sessions were left untouched.

### Requests to other sessions

- Any later integration: please keep roll-derived series coarse (`plan/model/verify.py` enforces it) or
  record the owner's explicit decision to do otherwise on this board first.
- `plan/**` and the root files listed in `plan/data/manifest.json` are generated. Change
  `plan/model/pages.py` or `plan/data/inputs_public.json` and run `python plan/model/build_site.py`;
  hand edits to the root pages fail the reproducibility check.

### Publication result

Recorded after the merge: see the entry appended below.
