# Tino3 — Cupertino & San Francisco House Inheritance Decision Dashboard

Anonymized decision dashboard for a trust inheritance expected ~2040–2050:
**live in vs. rent vs. sell & reinvest** Property A (Cupertino 95014) while keeping
Property B (San Francisco 94122, 3 units / 2 rented) in the analysis.

- **Live site:** GitHub Pages (deploys from `main` via `.github/workflows/pages.yml`)
- **Start:** `index.html` → Executive Summary → Decision Analysis
- **Model:** `python3 scripts/calculate.py` (writes `data/*.csv`)
- **Site build:** `python3 scripts/build_site.py` (regenerates all `*.html`)
- **Verification:** every verified row links to an official .gov source in
  `sources-verification.html` / `data/sources.csv`; unverified items are blank
  and listed on `flagged-review.html`.
- **Privacy:** placeholders only ([DECEDENT], [BENEFICIARY], [TRUSTEE]).
  No personal information appears on the site. All decision-analysis money
  figures are rounded to the nearest $10.

Coordination / task board: see `COORDINATION.md`.
