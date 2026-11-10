# Cupertino &amp; San Francisco inheritance decision dashboard

A self-contained, dependency-free static site that collects, verifies and analyses a two-property
Bay Area inheritance expected to pass through a trust in roughly 2040–2050, and recommends a plan.

**Live site:** <https://wingbangboozle1-lang.github.io/Tino3/>

---

## What this repository contains

| Path | What it is |
|---|---|
| `index.html` | The dashboard / landing page |
| `pages/*.html` | Eleven sub-pages: executive summary, inheritance process, taxes &amp; law, one page per property, operating costs, projections, decision analysis, risks, source register, flagged items |
| `assets/style.css` | The entire stylesheet. No frameworks, no CDN, no web fonts. |
| `data/model.json` | Every number used on the site, in one file |
| `data/sources.json` | The machine-readable source register |
| `EXECUTIVE-SUMMARY.md` | The executive summary as a standalone document |
| `COORDINATION.md` | The shared task board and the verification log |
| `tools/model.py` | The projection and scenario engine |
| `tools/site_lib.py`, `tools/pages_*.py`, `tools/md_summary.py`, `tools/build_site.py` | The site generator |
| `tools/sources.py` | The single source register the site renders from |
| `tools/check_links.py` | Build check: links, anchors, reachability, template artefacts |
| `build/model-report.txt` | A plain-text dump of the model, for eyeballing |

The site is **generated**, not hand-written. Pages are Python templates that read `data/model.json`,
so a number cannot appear on two pages with two different values.

## Rebuilding

No dependencies beyond the Python 3 standard library.

```bash
python3 tools/model.py        # recompute every figure -> data/model.json + build/model-report.txt
python3 tools/build_site.py   # render index.html, pages/*.html, EXECUTIVE-SUMMARY.md
python3 tools/check_links.py  # verify links, anchors, reachability; inventory external URLs
```

All model inputs live in a single dictionary, `A`, at the top of `tools/model.py`. Each one is
commented and marked as **verified**, **reported by the owner**, or **assumption**.

## Verification standard

This project's rule is that no figure is invented.

* **Verified** — read directly from the publisher's own page or document. Cited as `Sxx`, linked on
  the Sources page, with a narrow statement of what the source establishes.
* **Reported** — supplied by the property owner (values, bills, utility costs, rent). Labelled
  wherever it appears. Not publicly verifiable, and never described as verified.
* **Assumption** — a modelling input (growth, inflation, returns, maintenance rates). Disclosed,
  and stress-tested wherever it matters.
* **Unverified** — listed on the *Flagged for review* page with what would close it. Never silently
  filled in, never inferred, never interpolated.

Twenty-three sources, all official: California State Board of Equalization, Internal Revenue Service,
California Legislative Analyst's Office, California Franchise Tax Board, California Legislative
Information, California Secretary of State, County of Santa Clara Controller-Treasurer, City and
County of San Francisco (Controller, Assessor-Recorder, Rent Board), California Department of
Insurance, and the Federal Housing Finance Agency.

## Privacy

The site publishes:

* ZIP codes (`95014`, `94122`), not addresses or parcel numbers
* value bands and assessment figures, not owner names
* rent as a two-unit aggregate, not per unit
* no tenant information of any kind

The owner-supplied tax and rent histories are reproduced as year-and-amount series only. No figure
on the public site identifies a person or a specific address.

## Status of the findings

The analysis recommends **plan F: live in the San Francisco building, sell Cupertino at
inheritance, invest the proceeds** — first of six plans on terminal after-tax wealth, in eight of
nine growth-and-return combinations tested.

Ten items could not be verified against an official source. Two of them (the San Francisco effective
tax rate and the insurance premium) are material to the absolute numbers. Neither changes the
recommended plan. All ten are published, with source links and a stated remedy, on the
**Flagged for review** page.

## Licence and disclaimer

Analysis and code: free to reuse. Third-party source material remains with its publishers.

This is not legal, tax, investment or appraisal advice. Statutory references are current as of
**10 November 2026**. Confirm every figure against your own documents and with a licensed California
attorney, CPA and insurance broker before acting.
