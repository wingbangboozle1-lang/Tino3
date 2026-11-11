# Inheritance Atlas

A privacy-first decision dashboard for a trust inheritance expected between 2040 and 2050: one residence to
inherit, one three-unit building already held and partly rented, and enough inherited cash to matter for
federal estate tax.

**Live site:** https://wingbangboozle1-lang.github.io/Tino3/

## What this repository publishes

Twelve static pages, one stylesheet, one source ledger and three CSV downloads, plus the separate cross-check edition under `plan/` — nothing else. The published
artifact is an allowlist built by `scripts/package_site.py`; every path an earlier edition published is
replaced by a content-free withdrawal notice, so a stale URL cannot return an old figure.

| Page | Contents |
|---|---|
| `index.html` | Dashboard, recommendation, decision snapshot |
| `executive-summary.html` | The decision, five numbers, what would change it |
| `property-a.html` | The residence to inherit: inputs, assessment-factor check, what the inheritance does to the assessed value |
| `property-b.html` | The rental: inputs, tax-bill breakdown, rent rules, reassessment exposure if it is in the same estate |
| `taxes.html` | Federal, California and local rules, verified; pending law changes |
| `projections.html` | Year-by-year value, assessed value, tax and running costs, 2026–2060, and the ten years after an inheritance |
| `black-swans.html` | Black-swan conditions: baseline anchors, fifty years of official economic history, stress cases for the plan |
| `decision.html` | Sell vs rent vs move in for 2040/2045/2050, break-evens, sensitivities, the assumption register |
| `inheritance.html` | Statutory timeline after the death, with deadlines |
| `review.html` | 24 flagged items (unverified values left blank, owner questions, record irregularities) and two privacy disclosures |
| `audit.html` | Independent verification: twelve corrections to the first quantitative edition, repository review |
| `sources.html` | 58 official sources, what each one supports and how each was checked |

## Privacy rules enforced in code

- No names, street addresses, ZIP codes, parcel numbers, utility account numbers or unrounded assessment
  figures in any published file. Assessment-roll values and tax bills can be matched to a parcel, so they are
  generalised further: assessed values to the nearest $10,000, bills to the nearest $100. `scripts/verify.py` fails the build if a ZIP-code pattern, a city name, an
  e-mail address, a street address or a non-$10 amount appears in a page or in the data files.
- Properties appear only as Property A and Property B; jurisdictions are described generically, with
  the official rate documents cited.
- No forms, no scripts, no analytics, no remote assets. Nothing on the site accepts or stores input.

## Verification standard

Every rule on the site was retrieved from the publishing agency's own domain on 10 or 11 November 2026 and linked
from the row that uses it. `assets/sources.json` records what each document verifies. Anything that could not
be verified is left blank or published on the Flagged for Review page — never inferred.

## Build

```bash
python3 scripts/model.py        # writes assets/data/model.json and the CSV downloads
python3 scripts/build.py        # renders the twelve pages
python3 scripts/verify.py       # reproducible-build, citation, link, privacy and rounding checks
python3 scripts/package_site.py # writes the _site artifact (allowlist + withdrawal notices)
```

`verify.py` re-runs the model and the renderer and fails if any published byte changes, so a stale committed
page cannot survive CI. It also fails on any table row that does not link to an official publisher, and on any
ledger entry that does not say how it was checked.

## Data

`assets/sources.json` — source ledger (58 entries, each with the words relied on and how it was checked).
`assets/data/model.json` — every figure on the site.
`assets/data/property_a.csv`, `property_b.csv`, `decision.csv` — the same numbers for offline work.

## Limits

This is a planning model, not an appraisal, a title report, a tax return or legal advice. Insurance premiums,
future market values, future statutory thresholds and county parcel facts are not verifiable from public
sources today and are flagged as unverified.

## Coordination

`COORDINATION.md` is the shared task board for parallel sessions, including the handoff log, the privacy
remediation record and the deployment result.

## Independent cross-check (`plan/`)

`plan/` is a second, self-contained edition published at `/plan/`. It answers the same question with a separate
model that uses only owner-provided figures and figures read on official pages, and reports break-evens where an
input cannot be verified. It reconciles its results with the main edition on `plan/flagged.html`.

```
python plan/tools/model.py     # writes plan/data/*.json, *.csv
python plan/tools/build.py     # renders plan/*.html
python plan/tools/verify.py    # reproducibility, citations, links, privacy patterns, $10 rounding
```
