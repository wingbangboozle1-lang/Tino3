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

Board state read before claiming (remote branches inspected, not only `main`): four other sessions opened at 10:00 UTC —
`arena-b067dfc7` (legacy-path privacy remediation), `arena-d0927734` (privacy containment), `arena-0e2e112e` (audit only),
`arena/d76d5375` (FIN-1..4: root `*.html`, `scripts/*`, `assets/*`, `.gitignore`). Their claims live on their own branches,
not on `main`, so they are repeated here to make the overlap visible.

| Task | Status | Owner | File scope (disjoint from every claim above) |
|---|---|---|---|
| 6616-A Independent official-source re-verification of every law, rate and threshold used (federal, state, county, city) with a per-fact evidence ledger | in progress | `arena-6616d6b2` | `plan/data/**` |
| 6616-B Deterministic projection + decision model (live / rent / sell-and-reinvest, both properties, 2026-2050, $10 rounding) | in progress | `arena-6616d6b2` | `plan/tools/**` |
| 6616-C Self-contained dashboard edition generated from A+B (landing, executive summary, properties, costs, taxes, projections, decision, inheritance steps, law watch, sources, Flagged for Review) | in progress | `arena-6616d6b2` | `plan/**` |
| 6616-D Final integration (root index/navigation, workflows, README) | unclaimed by this session until the sessions above are done or stale (>60 min without commits) | - | none yet |

Rules this session is holding itself to:
- No edits outside `plan/**` and this section of `COORDINATION.md` until 6616-D is legitimately open.
- Privacy boundary: no names, street addresses, APNs, ZIP codes, neighbourhood names, account numbers or unrounded roll figures in any tracked file this session writes. Properties are "Property A" / "Property B"; people are placeholders. Dollar figures are stored and rendered in $10 increments, as the brief requires ("costs and numbers should be used but rounded to the nearest $10").
- A value is marked verified only if this session retrieved the official page and read the figure there; otherwise the cell is blank and the row is flagged.

- 10:08 UTC — merged `origin/main` (PRs #17-#19). Conflict in `COORDINATION.md` only: kept main's board in full and re-appended this section; nothing from another session was discarded.
- 10:20 UTC — merged `origin/main` again (PRs #20-#22, #24: session `d76d5375` published the quantitative root edition and marked FIN-1..4 done). Same single conflict in `COORDINATION.md`, resolved the same way (main's text kept verbatim, this section re-appended). **Scope decision:** this session will *not* replace the root edition a third time. `plan/**` becomes an independent, official-inputs-only cross-check of the live edition (second model, second source ledger, reconciliation table), following the live edition's privacy conventions (placeholders, no place names in page text, $10 rounding).
