# Inherited Property Decision Guide

A privacy-first decision dashboard for one household's question: **Property A**, a home expected to be
inherited through a trust between 2040 and 2050, against **Property B**, a partly rented multi-unit
building already owned by the beneficiary. Should the heir move into A, rent A, or sell A and reinvest?

The site publishes the analysis with every property figure rounded to the nearest $10 and every
identifying detail replaced by a placeholder. It cites only official publishers.

**Live site:** https://wingbangboozle1-lang.github.io/Tino3/

## What is published

Sixteen static pages, one stylesheet, one source ledger, the privacy setting, and four data downloads
(the model, two projection CSVs, the decision CSV, and the uneven-record data). Nothing else. The
artifact is an allowlist: every tracked path outside it is served as a content-free withdrawal notice,
so a stale URL cannot return an old figure.

| Page | Contents |
|---|---|
| `index.html` | The recommendation, four headline numbers, and a grouped map of the site |
| `executive-summary.html` | Twenty-three findings, each with its number and its official source |
| `decision.html` | Sell vs rent vs move in for 2040, 2045 and 2050; break-evens; every assumption |
| `projections.html` | Year-by-year value, assessed value, property tax and running costs, 2026–2060, plus the ten years after an inheritance |
| `black-swans.html` | Part 1: what the baseline assumes, fifty years of official price data, fixed amounts that do not inflate |
| `stress.html` | Part 2: verified 1929, 1965–82, 1987, 2000–02, 2007–09 and 2020 episodes, re-run against the 2045 inheritance |
| `economy.html` | The uneven record: 49 official years, decade by decade, and 2,000 fifty-year paths drawn from real ten-year stretches |
| `property-a.html` | The home to inherit: inputs, the full 2014–2026 tax and assessment history, what the inheritance does to it |
| `property-b.html` | The rental already owned: rent, the rent-cap paths, running costs, reassessment exposure |
| `taxes.html` | Federal, California and local rules; the estate-tax room by year; the law watch |
| `inheritance.html` | Eighteen timed steps from today to the years after the death |
| `suggestions.html` | Four paths and 20 suggestions, with effort and privacy cost, to review before changing anything |
| `questions.html` | 39 questions: what is settled, what is missing, the step that closes each, what changes if it differs |
| `review.html` | Every blank, every irregularity and every privacy disclosure, with the source that bears on it |
| `audit.html` | What independent passes corrected, and how the arithmetic was re-checked |
| `sources.html` | 78 official sources: what each supports and how each was checked |

The menu is grouped into six sections: The decision, Black swans, The properties, Tax and process,
Decide next, and Evidence. Older editions under `plan/` and `analysis/` remain in the repository for
audit and are not published.

## The decision, in one paragraph

Selling Property A soon after inheriting and holding a stock index fund ends ten years later with
$10,052,910; renting the home out ends with $8,583,500 and moving in with $7,945,420, all after taxes
and selling costs. Two rules drive it: the tax basis resets at death, so the sale is nearly tax-free;
and the property tax resets too, so today's $7,340 bill becomes $60,170 if a child moves in or $78,410
if the home is rented. The answer changes only if stocks return under 4.7% a year or house prices grow
about 7.0% a year.

## Privacy rules enforced in code

- **Placeholders only.** Properties appear as Property A and Property B; people as [GRANTOR],
  [SUCCESSOR_TRUSTEE] and [BENEFICIARY]; jurisdictions as County A and City B.
- **No direct identifiers.** `scripts/verify.py` fails the build on a name pattern, a postal code in
  context, a parcel number, a street address, an e-mail address, or a local place name.
- **No link may identify the jurisdiction.** `scripts/privacy_boundary.py` rejects any URL whose host or
  path names a local agency or a metro-level data series. That is why the property-tax and rent rules
  cite article XIII A of the California Constitution, Revenue and Taxation Code sections 51, 11911 and
  11930, and Civil Code sections 1947.12 and 1946.2, rather than a county rate book or a city rent board.
- **Every amount rounded to $10.** Assessment-roll values and tax bills are published at that precision,
  and percentage changes are computed before rounding so they are exact. The two officially published
  insurance averages are the only exception: they are quoted verbatim, listed in `ALLOWED_VERBATIM` in
  the verifier, and are statewide and national figures, not property figures.
- **Residual risk is disclosed, not hidden.** Rounding removes an exact match; it does not defeat a
  reader who already holds the county record and recognises the growth chain. `review.html` and
  `suggestions.html#privacy` say so, and the setting in `assets/privacy.json` can be raised to the
  nearest $1,000 or $10,000 with one command.

## Running it

```bash
python3 scripts/model.py     # decision model, projections, estate room
python3 scripts/economy.py   # the official annual record and the fifty-year paths
python3 scripts/build.py     # render the sixteen pages
python3 scripts/verify.py    # rebuild, repackage, then audit every page and every link
```

`verify.py` fails if the build is not reproducible, if a page is missing its title, its single `<main>`,
its single `<h1>` or its single current navigation link, if any internal link or fragment is broken, if
any external link is not HTTPS to an official publisher, if a factual table row cites nothing in the
source ledger, if any identifier pattern appears in a page or a data file, or if any dollar amount is not
a multiple of $10. `scripts/package_site.py` builds `_site` from the allowlist; `.github/workflows/pages.yml`
runs verify, packages, and deploys the artifact to GitHub Pages on every push to `main`.

## Limits

Every projection is a scenario built on assumed growth rates; the historical record on `economy.html` is
there precisely to show how wide the real range is. No value was inferred: where an official source does
not confirm a figure it is blank and listed on `review.html`. The site has no calculator, form, analytics,
tracking pixel or remote asset, so it collects nothing. It is not legal, tax or investment advice.
