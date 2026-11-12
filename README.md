# Inheritance Atlas

A privacy-first decision dashboard for a trust inheritance expected between 2040 and 2050: one residence to
inherit, one three-unit building already held and partly rented, and enough inherited cash to matter for
federal estate tax.

**Live site:** https://wingbangboozle1-lang.github.io/Tino3/

## What this repository publishes

<<<<<<< HEAD
Fifteen static pages, one stylesheet, one source ledger, one privacy setting and three CSV downloads, plus the separate cross-check edition under `plan/` — nothing else. The published
=======
Fifteen static pages, one stylesheet, one source ledger and three CSV downloads, plus the separate cross-check edition under `plan/` — nothing else. The published
>>>>>>> origin/main
artifact is an allowlist built by `scripts/package_site.py`; every path an earlier edition published is
replaced by a content-free withdrawal notice, so a stale URL cannot return an old figure.

| Page | Contents |
|---|---|
| `index.html` | Dashboard: recommendation, decision snapshot, and a grouped index of the site |
| `executive-summary.html` | The decision, five numbers, what would change it |
| `questions.html` | 35 questions with status: what is settled and linked to its publisher, what is missing, the step that closes it, and what changes if the answer differs |
| `suggestions.html` | Four paths and sixteen suggestions, each with effort, privacy cost and status; the privacy-precision choice; four decision gates |
| `property-a.html` | The residence to inherit: inputs, the full 2014–2026 tax and assessment history against the published state factors, what the inheritance does to the assessed value |
| `property-b.html` | The rental: inputs, the 2016–2025 tax and assessment history, tax-bill breakdown, rent rules, reassessment exposure if it is in the same estate |
| `taxes.html` | Federal, California and local rules, verified; what the heir receives and what is still taxed; pending law changes |
| `projections.html` | Year-by-year value, assessed value, tax and running costs, 2026–2060, and the ten years after an inheritance |
| `decision.html` | Sell vs rent vs move in for 2040/2045/2050, break-evens, sensitivities, the assumption register |
| `stress.html` | Black swans, part 2: verified 1929, Great Inflation, oil-shock, dot-com, Great Recession and COVID episodes re-run against the 2045 inheritance; the playbook |
| `black-swans.html` | Black swans, part 1: baseline anchors (Fed, SSA, CBO), fifty years of official state inflation data, fixed-amount erosion, and the single-input stress cases |
| `inheritance.html` | Statutory timeline after the death, with deadlines |
| `review.html` | 29 flagged items (unverified values left blank, owner questions, record irregularities) and four privacy disclosures |
| `audit.html` | Independent verification: twelve corrections to the first quantitative edition, repository review |
| `suggestions.html` | Four paths and 20 suggestions with effort, privacy cost and status; four decision gates; the privacy-precision choice |
| `questions.html` | 39 questions with status: what is settled and linked to its publisher, what is missing, the step that closes it, and what changes if the answer differs |
| `sources.html` | 72 official sources, what each one supports and how each was checked |

## How the site is organised

<<<<<<< HEAD
The menu is grouped into six sections: **Start here** (overview, summary, questions, suggestions),
**The decision** (decision analysis, projections), **Black swans** (conditions and history, stress tests —
one section in two parts), **The properties** (A, B), **Tax and process** (tax and law watch, inheritance
steps) and **Evidence** (flagged items, independent verification, source library).
=======
The menu is grouped into six sections: **The decision** (overview, summary, decision analysis, projections),
**Black swans** (conditions and history, stress tests — one section in two parts), **The properties**
(A, B), **Tax and process** (tax and law watch, inheritance steps), **Decide next** (suggestions for review, questions before deciding) and **Evidence** (flagged items,
independent verification, source library).
>>>>>>> origin/main

Three editions of the same analysis sit in this repository. They use separate models, so their figures
differ and must not be mixed: the fifteen pages in the menu (the edition to act on), the independent
cross-check at `/plan/`, and the 50-year and ownership suite at `/analysis/`. The overview page says
which one a reader is looking at.

## Privacy rules enforced in code

- No names, street addresses, postal codes, parcel numbers, utility account numbers or unrounded figures in
  any published file. `scripts/verify.py` fails the build if a postal-code pattern, a city name, an e-mail
  address, a street address or an amount that is not a multiple of $10 appears in a page or a data file.
- Assessment-roll values and tax bills are published at a precision the owner chooses in
  `assets/privacy.json`: tier 1, the setting in force since 12 November 2026, is the nearest $10; tier 2 is
  the nearest $1,000; tier 3 the nearest $10,000. Percentage changes in the roll tables are computed before
  rounding, so they are identical at every tier. The setting is committed, so the build and the checks
  reproduce the same pages. What tier 1 does and does not protect is stated on every page and on
  `review.html`; changing it is `python3 scripts/privacy_tier.py 2` (or 3) followed by a rebuild.
- Properties appear only as Property A and Property B; jurisdictions are described generically, with
  the official rate documents cited.
- No forms, no scripts, no analytics, no remote assets. Nothing on the site accepts or stores input.

## Verification standard

Every rule on the site was retrieved from the publishing agency's own domain between 10 and 12 November 2026 (see the source library for the session that opened each document) and linked
from the row that uses it. Two independent passes re-checked the edition on 11 November 2026; the third pass re-opened thirteen ledger entries on the publishers' sites, recomputed
every projection row from the model's own formulas (all agreed to the nearest $10), closed one open flag with 31 U.S.C. 3124 (Treasury interest is exempt from state tax) and corrected a
stale source count. It found no wrong figure. A fourth pass on 12 November 2026 added the two rules the brief asks about that the edition had never covered (an inheritance is not income to the heir; what happens to an inherited retirement account) and removed two source badges that pointed at an unrelated IRS page. What it did not do is listed on `audit.html`. `assets/sources.json` records what each document verifies. Anything that could not
be verified is left blank or published on the Flagged for Review page — never inferred.

## Build

```bash
python3 scripts/model.py        # writes assets/data/model.json and the CSV downloads
python3 scripts/build.py        # renders the fifteen pages
python3 scripts/verify.py       # reproducible-build, citation, link, privacy and rounding checks
python3 scripts/package_site.py # writes the _site artifact (allowlist + withdrawal notices)

python3 scripts/privacy_tier.py 3   # optional: raise the roll-value precision, then rebuild
```

`verify.py` re-runs the model and the renderer and fails if any published byte changes, so a stale committed
page cannot survive CI. It also fails on any factual table row that does not link to an official publisher
(rows that record a choice must link to their reasoning), and on any ledger entry that does not say how it
was checked.

## Data

<<<<<<< HEAD
`assets/sources.json` — source ledger (72 entries, each with the words relied on and how it was checked).
`assets/privacy.json` — the published precision for assessment-roll values and tax bills.
=======
`assets/sources.json` — source ledger (70 entries, each with the words relied on and how it was checked).
>>>>>>> origin/main
`assets/data/model.json` — every figure on the site.
`assets/data/property_a.csv`, `property_b.csv`, `decision.csv` — the same numbers for offline work.

## Limits

This is a planning model, not an appraisal, a title report, a tax return or legal advice. Insurance premiums,
future market values, future statutory thresholds and county parcel facts are not verifiable from public
sources today and are flagged as unverified.

## Coordination

`COORDINATION.md` is the shared task board for parallel sessions, including the handoff log, the privacy
remediation record and the deployment result. The session of 12 November 2026 claimed the questions and
suggestions pages, the roll tables and the privacy setting there before editing anything.

## Independent cross-check (`plan/`)

`plan/` is a second, self-contained edition published at `/plan/`. It answers the same question with a separate
model that uses only owner-provided figures and figures read on official pages, and reports break-evens where an
input cannot be verified. It reconciles its results with the main edition on `plan/flagged.html`.

```
python plan/tools/model.py     # writes plan/data/*.json, *.csv
python plan/tools/build.py     # renders plan/*.html
python plan/tools/verify.py    # reproducibility, citations, links, privacy patterns, $10 rounding
```
