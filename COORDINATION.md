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

- 10:08 UTC — merged `origin/main` (PRs #17-#19) into this branch. Conflict in `COORDINATION.md` only: kept main's redacted board in full and re-appended this section; nothing from another session was discarded. Noted that `scripts/privacy_boundary.py` now fails any tracked file outside its allowlist, so `plan/**` cannot pass CI until the guard's owner (or a legitimate final integrator) approves the paths. Logged as change request **CR-6616-1**: extend the allowlist to the generated `plan/` files, which carry their own stricter check (`plan/tools/verify.py`: no ZIP codes, no unrounded figures, no names, every table row cited to an official host).
