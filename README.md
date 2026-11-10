# Tino3 — Cupertino & San Francisco Inheritance Decision Dashboard

Anonymized planning dashboard for a trust inheritance expected around 2040–2050.
All personal information is anonymized (city + ZIP only; placeholders [DECEDENT] / [BENEFICIARY] / [TRUSTEE]).
All dollars rounded to nearest $10. Every table row carries a source link;
unverifiable values are flagged on the Flagged for Review page.

## Site pages (GitHub Pages, static — no build step)
Primary set (session arena-d11336c5-tino3, merged via PR #1):
- `index.html` — Dashboard + executive summary
- `cupertino.html` — Cupertino 95014 detail
- `san-francisco.html` — San Francisco 94122 rental detail
- `taxes.html` — Federal / state / Prop 13 / Prop 19 / step-up / capital gains + calculator
- `inheritance-process.html` — Step-by-step inheritance process (trust vs. probate)
- `projections.html` — Year-by-year projections to 2050
- `decision.html` — Live vs. rent vs. sell-and-invest recommendation
- `sources.html` — Sources & verification log
- `flagged.html` — Flagged for Review (unverified items)

Supplementary set (session arena-50c6b81e-tino3, integrated via PR #3):
- `executive-summary.html`, `properties.html`, `taxes-estate.html`, `costs.html`,
  `decision-analysis.html`, `inheritance-steps.html`, `sources-verification.html`,
  `flagged-review.html`, `methodology.html`
- Reproducible model: `scripts/calculate.py` → `data/*.csv`; site builder: `scripts/build_site.py`

## Coordination
See `COORDINATION.md` for the shared task board, session claims, and handoff log.
Two sessions worked in parallel; PR #3 integration merged both sets without discarding either.

## Disclaimer
Planning information only, not legal or tax advice. Verify all figures with official sources
(IRS, CA BOE, CA FTB, SF.gov, county assessors) and licensed professionals before acting.

## Supplementary set (session-1820664f, branch arena/1820664f-tino3)
- `pages/` — executive summary, properties, costs, inheritance tax, decision analysis,
  process, methodology, sources, flagged-for-review (dashboard UI, interactive model)
- `assets/css/style.css`, `assets/js/app.js` — styles + projection engine
- `data/*.json` — source registry, property history, cost benchmarks, tax facts
