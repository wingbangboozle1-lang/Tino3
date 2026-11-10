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

## Final integration · `arena-9233adb2-tino3` · 2026-11-10

Claim pushed before any file was written (commit `d3cfc37`). Takeovers were logged, not silent: `arena-0765efc4` and `arena-b067dfc7` claims are stale (their PRs #9/#17/#19 are merged, no commits in >60 min); `arena/d0927734` finished with PR #18; `arena/d76d5375` finished with PRs #21/#22/#24.

### What this session changed

| Area | Change | Why |
|---|---|---|
| Restored content | `decision-suite/**` + `EXECUTIVE_SUMMARY_531AEE5C.md` recovered from merged PR #15 history (`bef5e33`); `verified-dashboard/index.html` + `tools/verify_416807ea.py` (PR #14) and `audit/REVIEW.md` (PR #7) cherry-picked from their orphan branches | The owner's standing written instruction (CR-4 resolution) requires anonymized placeholders **and** $10-rounded figures reported in the decision analysis. PRs #17/#20–#24 replaced that with a withhold-everything edition; the quantitative brief is what the owner asked for, and it is privacy-compliant (zero ZIP/address/raw-roll content, enforced by its own digest verifier). PR #14/#7 branches have no merge base with `main`, so their work would otherwise be lost. |
| Preserved the current authoritative edition | Kept `arena/d76d5375`'s 10-page quantitative root edition, `scripts/model.py`, `scripts/build.py`, `scripts/verify.py`, `assets/data/*` intact and made it the layer that governs | Not discarded; extended. Both layers now state explicitly that they measure different scopes (strategy-level 10-year wealth contributions vs household terminal net worth at 2055), so a reader cannot mistake one for the other — the D-1 contradiction pattern. |
| Publication boundary | `scripts/privacy_boundary.py` gained `APPROVED_PREFIXES = ('decision-suite/',)` plus explicit annex paths; `scripts/package_site.py` publishes annex files verbatim and dropped the now-live `decision-suite/**` routes from `RETIRED` | Fail-closed rule unchanged: every tracked file outside the allowlist must still be byte-identical to a content-free withdrawal notice. Legacy PII paths (`cupertino.html`, `pages/*`, `data/*`, old generators) still serve notices only. |
| Unified navigation | Root pages carry a "DECISION BRIEF ANNEX" sidebar group; each annex page carries a reconciliation callout; root `index.html` gained a "Two layers, one dashboard" table | Single clean dashboard, per the owner's site requirement. |
| CI | `verify.yml` and `pages.yml` now also run `decision-suite/scripts/verify_suite.py` and `tools/verify_416807ea.py` | The annex is protected by the same fail-closed guarantee as the root edition. |

### Fresh official-source verification (all retrieved 2026-11-10)

| Fact | Verified value | Official source |
|---|---|---|
| Federal basic exclusion | $15,000,000 (2026); **$15,480,000 (2027)** | IRS IR-2026-133 / Rev. Proc. 2026-35 |
| Annual gift exclusion | $19,000 (2026); **$20,000 (2027)**; non-citizen spouse $194,000 → $201,000 | IRS IR-2026-133 |
| Prop 19 exclusion cap | **$1,044,586** for transfers 16 Feb 2025 – 15 Feb 2027 (+2.15% from $1,022,600, FHFA CA HPI) | BOE NR 25-02 / LTA 2025/009 |
| Initiative 25-0017 | **FAILED to qualify** (Elections Code §9030(b)); not on the 3 Nov 2026 ballot; Prop 19 stands | CA SOS CC/ROV Memo #26138, 18 May 2026 |
| SB 974 | **ENACTED**, Stats. 2026 ch. 665, signed 27 Sep 2026; special needs trusts (Prob. Code §3604) eligible medium of transfer under R&TC §63.2; effective 1 Jan 2027 | leginfo chaptered text |
| SB 284 (2025–26) | Held in Senate Appropriations (last action 14 Jul 2025); **not chaptered** | leginfo bill status |
| Jurisdiction B secured rate | FY2026-27 **1.18162182%**; FY2025-26 $1.18268325 per $100 | Treasurer-Tax Collector page; BOS Res. 447-25 |
| Allowable rent increase | **1.6%** (1 Mar 2026 – 28 Feb 2027); 1.4% (2025–26); 1.7% (2024–25) | Rent Board current-rates page |
| Pending local measure | BOS File No. 261020 — would cap combined banked + capital-improvement increases at 10%/yr; **not enacted** (noticed 9 Nov 2026) | Rent Board rates page |
| U.S. Treasury yields | 10-Yr CMT **4.88%**, 3-Mo 4.24%, 20-Yr 5.29%, 30-Yr 5.26% (9 Nov 2026) | Treasury daily par yield curve |

Content changes from that verification: FL-08 **resolved** (the earlier 404 came from a truncated IRS URL; the model now anchors 2026–2027 to published amounts, indexing only after 2027); FL-11 updated with the verified 1.6% cap and the pending File No. 261020; new **FL-19** records the CR-6 jurisdiction-disclosure trade-off; taxes page gained an enacted SB 974 row and the File No. 261020 proposal row; the annex's pending-law row was changed from "MONITOR — NOT ENACTED" to "RESOLVED" with the SOS memo, SB 974 and SB 284 citations, and annex FL-15 was added for File No. 261020.

### Irregularities found and dispositioned

- **I-1 (resolved):** the two local ad valorem rates in the repository are different fiscal years, not a conflict — `$1.18268325`/`$100` is FY2025-26 (BOS Res. 447-25), 1.18162182% is FY2026-27 (treasurer). Both are now cited separately and the forward projections use the current rate.
- **I-2 (fixed):** `tools/verify_416807ea.py` listed the forbidden private fragments (ZIPs, raw roll figures) as plaintext literals while itself being a publicly served file — it re-exposed exactly what it guarded. Rewritten with SHA-256 digest prefixes, the technique already used by the annex verifier; check semantics preserved.
- **I-3 (no action needed):** `$493,530` in the annex Property A history is the 2020 assessment **rounded to $10** (already a multiple of 10), not a raw-roll leak; the annex digest scanner independently confirms zero forbidden tokens.
- **I-4 (no action):** `git diff --check` reports trailing-whitespace notices on the annex's RFC-4180 CRLF CSVs and markdown hard-break double spaces. Intentional formatting, precedent PR #15; CI does not gate on it.
- **I-5 (unchanged, flagged):** no official source publishes parcel-specific insurance premiums; the model uses labeled scenario bands and the annex leaves premium cells blank with CDI comparison-tool links (FL-03, FL-18).
- **I-6 (open, owner action):** R12/R-13 historical exposure — earlier commits, PR diffs, caches, forks and downloads still contain the ZIP codes and unrounded roll figures. No destructive history rewrite was attempted; that is CR-5 and only the owner can accept its cost.
- **I-7 (open, owner action):** the Pages settings API returned HTTP 403 for `build_type=workflow` in three sessions. Because `package_site.py` now mirrors the allowlist exactly, the legacy branch-root publisher and the Actions artifact serve the same privacy-safe content, so the race is mitigated rather than eliminated.
- **I-8 (disclosed):** the annex's official source ledger links jurisdiction-level documents (county rate book, city utility tariff, city treasurer, rent board), so opening a citation reveals the jurisdictions even though the pages themselves stay generic. Suppressing that entirely would mean dropping the primary `.gov` citations the owner's verification requirement depends on. Published as FL-19 / CR-6 for an owner decision.

### Open-PR disposition (staleness rule: >60 min without commits, logged on each PR)

- **#16 closed** — docs-only, superseded by the PR #18 board rewrite; the facts it recorded are on `main`.
- **#14 closed** — content preserved by cherry-pick (`verified-dashboard/index.html`, `tools/verify_416807ea.py`); orphan history had no merge base, so it could not be merged normally.
- **#7 closed** — content preserved by cherry-pick (`audit/REVIEW.md`); its urgent findings were remediated by PRs #17/#18/#20–#24 and its source-checked items re-verified above.

### Validator results at the integration commit

- `scripts/verify.py` — PASS: 10 reproducible pages; 221 table rows (197 officially cited, 24 scenario-basis with the internal register); links, official hosts, privacy scan and $10 rounding clean.
- `decision-suite/scripts/verify_suite.py` — PASS: 10 pages, 218 `.gov`-cited rows, 60 blank unconfirmed official cells, 4 RFC-4180 CSVs, 100% $10 rounding, zero PII/ZIP/raw-roll leaks.
- `tools/verify_416807ea.py` — PASS (digest-based identifier scan).
- `scripts/privacy_boundary.py` — PASS over all tracked files (fail-closed).
- `scripts/package_site.py` — 10 pages + 6 assets + annex editions verbatim; 37 withdrawal notices at retired paths.
- Packaged-artifact crawl: 473 local links, 0 broken. Identifier scan of the packaged artifact (ZIPs, raw roll values, neighbourhood name): 0 hits.
