# Inheritance Decision Atlas

A static decision dashboard for one question: when a Cupertino house arrives through a trust between
2040 and 2050, should it be lived in, rented, or sold and reinvested?

**Live site:** https://wingbangboozle1-lang.github.io/Tino3/

## What it contains

| Page | What it answers |
|---|---|
| `index.html` | Dashboard: five figures, one recommendation |
| `executive-summary.html` | The full case, twelve findings, three next actions |
| `properties.html` | Both properties and the reconciliation of their tax bills |
| `property-tax.html` | Prop 13 and Prop 19 mechanics, forward assessed values |
| `operating-costs.html` | Insurance, water, electricity, repairs, the SF rent roll |
| `taxes-estate.html` | Federal, California and local treatment; step-up; estate headroom |
| `projections.html` | Every year from 2026 to 2055, both houses |
| `decision-analysis.html` | Live vs rent vs sell, after tax, with break-even thresholds |
| `inheritance-process.html` | Twelve steps with the statutory deadlines |
| `laws-watch.html` | Enacted, scheduled and merely proposed rules |
| `flagged-for-review.html` | Fifteen unverified or assumed items, and what would settle each |
| `sources.html` | Twenty-four official sources with the scope of each |
| `privacy.html` | Exactly what was withheld and why |

## Evidence rules

- Every table row links an official publisher, or is explicitly labelled as owner-supplied or computed.
- A value that could not be confirmed from an official source was **left blank and flagged**, never inferred.
- All computed amounts are displayed rounded to the nearest $10; statutory amounts are quoted verbatim.
- No names, street addresses, parcel numbers, ZIP codes, or account details appear anywhere.
- No analytics, cookies, forms, remote assets or storage. One local stylesheet and one local script
  (mobile menu only).

## Build and test

No dependencies. Python 3.11+.

```sh
python scripts/model.py            # writes data/*.csv and data/model_outputs.json
cd scripts && python webbuild.py   # writes the 13 HTML pages
cd .. && python scripts/verify.py  # reproducible, cited, host-allow-listed, private, rounded
python scripts/package_site.py     # assembles _site/
```

`verify.py` fails the build if any page is stale, any data row lacks an official citation, any link
leaves the allow-listed official hosts or is broken locally, any ZIP code or street address appears,
or any computed amount is not rounded to $10. It does not prove legal correctness and it cannot check
that a government page still says the same thing.

## Publication

This repository's GitHub Pages site is configured with `build_type: legacy`, which publishes the
**branch root** rather than a workflow artifact. There is therefore no allow-list: whatever is at the
root is public. `scripts/package_site.py` mirrors the whole tree into `_site/` so the Actions artifact
and the branch publisher always agree, and the current site keeps superseded editions under `archive/`
instead of deleting other sessions' work.

**Not advice.** This is a planning model on stated assumptions. Obtain qualified legal, tax and
fiduciary review before executing anything.
