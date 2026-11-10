# Inherited property plan

Static site: https://wingbangboozle1-lang.github.io/Tino3/

A planning dashboard for one home expected to be inherited through a trust between 2040 and 2050,
with a second rental property kept in view. Properties appear only as Property A and Property B.

## Pages

`index.html` dashboard · `executive-summary.html` · `decision.html` live, rent or sell ·
`projections.html` year by year · `property-a.html` · `property-b.html` · `insurance.html` ·
`taxes.html` thresholds and headroom · `law-changes.html` · `inheritance.html` trust process ·
`review.html` Flagged for Review · `sources.html` · `method.html` assumptions and privacy.

## How it is built

Everything published is generated from the `plan` folder.

| Path | What it is |
|---|---|
| `plan/data/inputs_public.json` | Model inputs. Roll-derived figures are privacy-rounded. |
| `plan/model/model.py` | Projection and decision model. |
| `plan/model/sitekit.py` | Official-source ledger, page shell, styles. |
| `plan/model/pages.py` | Page content and the flag register. |
| `plan/model/build_site.py` | Writes the root pages, `assets/`, `EXECUTIVE_SUMMARY.md` and `plan/data/manifest.json`. |
| `plan/model/verify.py` | Source, link, rounding, privacy and reproducibility checks. |
| `scripts/verify.py` | Entry point for both workflows. |
| `scripts/package_site.py` | Builds `_site/` from the manifest plus withdrawal notices for retired paths. |
| `scripts/privacy_boundary.py` | Fails if any tracked file is neither current nor a content-free notice. |

```
python plan/model/build_site.py   # rebuild every published file
python scripts/verify.py          # all checks
python scripts/package_site.py    # build the Pages artifact
```

## Rules

- Every table row links to an official source. A value that could not be confirmed is left blank and
  listed on Flagged for Review.
- Every amount is a multiple of $10.
- No names, addresses, parcel numbers, postal codes or neighbourhoods. Assessed values and tax bills are
  public records that can identify a parcel even when rounded to $10, so they are shown as rounded levels.
- To run the model on exact figures, put them in `private/inputs.json` (git-ignored) and run
  `python plan/model/model.py --inputs private/inputs.json --out private/model_outputs.json`.
- Root pages are generated. Edit `plan/`, rebuild, and read `COORDINATION.md` before starting.

Known limits: earlier commits of this public repository still contain exact figures, and GitHub's
branch build and the Actions workflow both publish the site. Both need the repository owner.

General information for planning, not legal, tax or investment advice.
