# Inheritance Atlas

A privacy-first decision dashboard for a trust inheritance expected between 2040 and 2050: one residence to
inherit, one three-unit building already held and partly rented, and enough inherited cash to matter for
federal estate tax.

**Live site:** https://wingbangboozle1-lang.github.io/Tino3/

## What this repository publishes

Ten static pages, one stylesheet, one source ledger and three CSV downloads — nothing else. The published
artifact is an allowlist built by `scripts/package_site.py`; every path an earlier edition published is
replaced by a content-free withdrawal notice, so a stale URL cannot return an old figure.

| Page | Contents |
|---|---|
| `index.html` | Dashboard, recommendation, decision snapshot |
| `executive-summary.html` | The decision, five numbers, what would change it |
| `property-a.html` | The residence to inherit: assessment history, carrying costs, 2026–2055 projection |
| `property-b.html` | The rental: rent roll, operating statement, the unreconciled tax bill, projections |
| `taxes.html` | Federal, California and local rules, verified; pending law changes |
| `projections.html` | 30-year outlook and the full assumption register |
| `decision.html` | Live vs rent vs sell/bonds, sensitivity matrix, break-even |
| `inheritance.html` | Statutory timeline after the death, with deadlines |
| `review.html` | 18 flagged items and the repository-history disclosure (R-13) |
| `sources.html` | 18 official sources, what each one actually verifies |

## Privacy rules enforced in code

- No names, street addresses, ZIP codes, parcel numbers, utility account numbers or unrounded assessment
  figures in any published file. `scripts/verify.py` fails the build if a ZIP-code pattern, a city name, an
  e-mail address, a street address or a non-$10 amount appears in a page or in the data files.
- Properties appear only as `[PROPERTY_A]` and `[PROPERTY_B]`; jurisdictions are described generically, with
  the official rate documents cited.
- No forms, no scripts, no analytics, no remote assets. Nothing on the site accepts or stores input.

## Verification standard

Every rule on the site was retrieved from the publishing agency's own domain on 10 November 2026 and linked
from the row that uses it. `assets/sources.json` records what each document verifies. Anything that could not
be verified is left blank or published on the Flagged for Review page — never inferred.

## Build

```bash
python3 scripts/model.py        # writes assets/data/model.json and the CSV downloads
python3 scripts/build.py        # renders the ten pages
python3 scripts/verify.py       # reproducible-build, citation, link, privacy and rounding checks
python3 scripts/package_site.py # writes the _site artifact (allowlist + withdrawal notices)
```

`verify.py` re-runs the model and the renderer and fails if any published byte changes, so a stale committed
page cannot survive CI. It also fails on any table row that cites neither an official source nor the internal
assumption register.

## Data

`assets/sources.json` — source ledger (18 entries).
`assets/data/model.json` — every figure on the site.
`assets/data/property_a.csv`, `property_b.csv`, `decision.csv` — the same numbers for offline work.

## Limits

This is a planning model, not an appraisal, a title report, a tax return or legal advice. Insurance premiums,
future market values, future statutory thresholds and county parcel facts are not verifiable from public
sources today and are flagged as unverified.

## Coordination

`COORDINATION.md` is the shared task board for parallel sessions, including the handoff log, the privacy
remediation record and the deployment result.
