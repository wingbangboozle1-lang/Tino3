# Coordination board

Privacy rule: public pages use generic Property A / Property B placeholders. Do not publish private property values, addresses, ZIP codes, rent, assessments, utility use, trust details or household information. Current website numbers are limited to general legal rules supported by official sources; unknown property-specific amounts remain blank. Historical repository commits and external copies are not certified erased.

| Task | Status | Owner | Scope |
|---|---|---|---|
| Official-source inherited-property planning framework and static dashboard | done | prior integration sessions | `index.html`, `taxes.html`, `decision.html`, `costs.html`, `projections.html`, `inheritance.html`, `review.html`, `sources.html`, `assets/`, `scripts/build.py` |
| Current legacy-publication privacy containment, verification hardening and deployment check | in progress | `arena-d0927734-tino3` | `COORDINATION.md`, `scripts/verify.py`, `scripts/package_site.py`, withdrawn legacy paths |

## Verification boundaries

The public edition is informational, not individualized legal, tax, insurance or investment advice. Primary references are IRS (estate tax, Form 706, inherited basis, rental property and home sale), California BOE (Propositions 13 and 19), California State Controller / FTB, California statutes, California Department of Insurance, San Francisco official services and LAO analysis of a proposed initiative. The source ledger is `assets/sources.json`; the eight-page publication build and structural checks are in `scripts/build.py` and `scripts/verify.py`. Official sources support the stated legal framework only; they do not verify private property facts, quotes or future forecasts.

## Privacy incident / publication status

Earlier sessions placed property-specific data in repository files and public history. The current work removes legacy detail from present-day website paths and keeps only the reviewed, generic dashboard. A Pages API check reported legacy branch-root publication, and changing the Pages source through the connected integration was denied with HTTP 403. The Actions artifact is allowlisted, but legacy publication must be verified after deployment. A regular content update cannot erase prior Git objects, cached pages, forks or downloads. Do not claim historical erasure. Repository-owner action may be required to change Pages settings or coordinate history remediation.

## Session log · `arena/d0927734-tino3` · 2026-11-10

- Read the existing task board before work; no competing active claim was found at start. Claimed privacy containment on the fixed Arena branch and pushed the claim commit.
- Audited tracked content and current GitHub Pages configuration. Found legacy pages and data outside the reviewed artifact allowlist; property-specific values were present in current repository files.
- Replaced legacy output paths with content-free withdrawal notices/status records; preserved the reviewed generic eight-page dashboard and its official source ledger. Corrected the review page to distinguish current publication removal from historical erasure.
- Change request to repository owner: set Pages source to GitHub Actions (`build_type=workflow`) to disable legacy root publishing. Attempt returned HTTP 403 (`Resource not accessible by integration`); not changed.
- Verification and PR / deployment results to be appended after checks.
