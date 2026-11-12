# Inherited Property Decision Guide

A privacy-first, general-purpose framework for comparing **Property A, treated as inherited**, with **Property B, treated as already owned**. It publishes no individualized recommendation, property description, address, assessment, rent, utility use, insurance estimate, owner-derived projection or household detail.

**Pages URL:** https://wingbangboozle1-lang.github.io/Tino3/

## Public edition

The current edition has 15 static HTML pages and one stylesheet:

| Page | Purpose |
|---|---|
| `index.html` | Scope and route through the guide |
| `executive-summary.html` | Decision status and the main steps |
| `decision.html` | Options and criteria for comparing A and B |
| `property-a.html` | Inherited-property rules and a blank evidence checklist |
| `property-b.html` | Already-owned-property rules and a separate blank checklist |
| `costs.html` | Private cost ledger template with no amounts |
| `projections.html` | Scenario method without personal inputs or a forecast |
| `stress.html` | Selected official-source historical economic episodes |
| `taxes.html` | General federal and California tax, property and rental-law references |
| `inheritance.html` | General estate, trust, assessor and tax steps |
| `questions.html` | Facts to obtain privately before comparing options |
| `suggestions.html` | Proposed improvements; none is selected automatically |
| `review.html` | Unknown and decision-sensitive items to resolve privately |
| `audit.html` | Privacy, evidence, deployment and history limitations |
| `sources.html` | Source ledger and the limits of each source |

This is a static, no-input site: it has no calculator, form, analytics, tracking pixel or remote asset. The private evidence fields are blank, and the site does not collect or store answers.

## Privacy and publication boundary

`scripts/build.py` renders only the 15-page general guide from `assets/sources.json`; it does not load the legacy property model or data. `scripts/package_site.py` copies only those pages and `assets/style.css`. Every other tracked path—and known legacy route—is emitted in the deployment artifact as a generic, content-free withdrawal notice. The source ledger, working models, old editions, data files, tools and repository documents are not copied as their original contents.

Rounded figures are not treated as anonymized. No owner-derived amounts or projections are included in the public pages. The artifact check also rejects known local place names and common direct identifiers. These checks reduce current-artifact exposure; they do not erase or certify the removal of old commits, pull-request diffs, caches, forks, downloads or external copies.

## Evidence and limits

The source ledger contains official federal, California and economic-history references checked for this edition on November 12, 2026. It records what each source supports and what it cannot establish. Legal rules, indexed amounts and bill status can change. The current code and any chaptered-but-not-yet-codified change must be checked again at the relevant transfer, filing or decision date.

The guide does not verify an individual's title, basis, occupancy, county, rental history, property condition, utility tariff, insurance coverage or tax position. It is not an appraisal, legal or tax opinion, or personalized financial recommendation. Local rules and professional advice may be necessary.

## Rebuild and verify

Requires Python 3.10 or later; no third-party packages are used.

```bash
python3 scripts/build.py
python3 scripts/verify.py
python3 scripts/package_site.py
python3 scripts/privacy_boundary.py
```

`verify.py` rebuilds the pages and fails if committed output is stale, checks official-source links and local links/fragments, packages the site, and runs the privacy boundary. `package_site.py` writes the deployable artifact to `_site/`. The Pages workflow should deploy this artifact through GitHub Actions; verify the repository's Pages source and the live deployment after publication.
