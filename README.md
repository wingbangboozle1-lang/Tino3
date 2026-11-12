# Inheritance Atlas

A privacy-first decision dashboard for a trust inheritance expected between 2040 and 2050: one residence to
inherit, one three-unit building already held and partly rented, and enough inherited cash to matter for
federal estate tax.

**Live site:** https://wingbangboozle1-lang.github.io/Tino3/

## What this repository publishes

Fifteen static pages, one stylesheet, one source ledger and three CSV downloads, plus the separate cross-check edition under `plan/` — nothing else. The published
artifact is an allowlist built by `scripts/package_site.py`; every path an earlier edition published is
replaced by a content-free withdrawal notice, so a stale URL cannot return an old figure.

| Page | Contents |
|---|---|
| `index.html` | Dashboard: recommendation, decision snapshot, and a grouped index of the site |
| `executive-summary.html` | The decision, every important number with its source, what would change it, and the answer/choose/implement sequence |
| `property-a.html` | The residence to inherit: inputs, assessment-factor check, what the inheritance does to the assessed value |
| `property-b.html` | The rental: inputs, tax-bill breakdown, rent rules, reassessment exposure if it is in the same estate |
| `taxes.html` | Federal, California and local rules, verified; pending law changes |
| `projections.html` | Year-by-year value, assessed value, tax and running costs, 2026–2060, and the ten years after an inheritance |
| `decision.html` | Sell vs rent vs move in for 2040/2045/2050, break-evens, sensitivities, the assumption register |
| `stress.html` | Black swans, part 2: verified 1929, Great Inflation, oil-shock, dot-com, Great Recession and COVID episodes re-run against the 2045 inheritance; the playbook |
| `black-swans.html` | Black swans, part 1: baseline anchors (Fed, SSA, CBO), fifty years of official state inflation data, fixed-amount erosion, and the single-input stress cases |
| `inheritance.html` | Statutory timeline after the death, with deadlines |
| `suggestions.html` | A register of 15 proposed improvements, four decision paths to choose from, and five change-control gates. Nothing is adopted |
| `questions.html` | What the law already answers, what the owner must supply, a document-by-document discovery plan, and the thresholds that decide whether an unknown matters |
| `review.html` | 24 flagged items (unverified values left blank, owner questions, record irregularities) and three privacy disclosures |
| `audit.html` | Independent verification: thirteen corrections across three passes, including the 12 November 2026 surcharge finding, and the repository review |
| `sources.html` | 69 official sources, what each one supports and how each was checked |

## How the site is organised

The menu is grouped into six sections: **The decision** (overview, summary, decision analysis, projections),
**Black swans** (conditions and history, stress tests — one section in two parts), **The properties**
(A, B), **Tax and process** (tax and law watch, inheritance steps), **Decide next** (suggestions for review, questions before deciding) and **Evidence** (flagged items,
independent verification, source library).

Three editions of the same analysis sit in this repository. They use separate models, so their figures
differ and must not be mixed: the fifteen pages in the menu (the edition to act on), the independent
cross-check at `/plan/`, and the 50-year and ownership suite at `/analysis/`. The overview page says
which one a reader is looking at.

## Privacy rules enforced in code

- No names, street addresses, ZIP codes, parcel numbers, utility account numbers or unrounded assessment
  figures in any published file. Assessment-roll values and tax bills can be matched to a parcel, so they are
  generalised further: assessed values to the nearest $10,000, bills to the nearest $100. `scripts/verify.py` fails the build if a ZIP-code pattern, a city name, an
  e-mail address, a street address or a non-$10 amount appears in a page or in the data files.
- Properties appear only as Property A and Property B; jurisdictions are described generically, with
  the official rate documents cited.
- Residual risk is disclosed rather than hidden: the two owner-supplied market values and the monthly rent are
already multiples of $10, so rounding does not disguise them. The review page says so, and SG-14 puts the choice
between bands, a coarser rounding or withdrawal to the owner.

## Verification standard

Every rule on the site was retrieved from the publishing agency's own domain between 10 and 12 November 2026 (see the source library for the session that opened each document) and linked
from the row that uses it. Two independent passes re-checked the edition on 11 November 2026; the third pass re-opened thirteen ledger entries on the publishers' sites, recomputed
every projection row from the model's own formulas (all agreed to the nearest $10), closed one open flag with 31 U.S.C. 3124 (Treasury interest is exempt from state tax) and corrected a
stale source count. It found no wrong figure. What it did not do is listed on `audit.html`. `assets/sources.json` records what each document verifies. A fourth pass on 12 November 2026 re-opened fifteen entries, confirmed every published figure, and added one finding: the 1% California tax above $1,000,000 of taxable income (RTC 17043) is not in the 12.3% rate used in the model, so it is published as a sensitivity (the 2045 stock result falls by $36,170 and the ranking holds). Anything that could not
be verified is left blank or published on the Flagged for Review page — never inferred.

## Build

```bash
python3 scripts/model.py        # writes assets/data/model.json and the CSV downloads
python3 scripts/build.py        # renders the fifteen pages
python3 scripts/verify.py       # reproducible-build, citation, link, privacy and rounding checks
python3 scripts/package_site.py # writes the _site artifact (allowlist + withdrawal notices)
```

`verify.py` re-runs the model and the renderer and fails if any published byte changes, so a stale committed
page cannot survive CI. It also fails on any table row that does not link to an official publisher, and on any
ledger entry that does not say how it was checked.

## Data

`assets/sources.json` — source ledger (69 entries, each with the words relied on and how it was checked).
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
