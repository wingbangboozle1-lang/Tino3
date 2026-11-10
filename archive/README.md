# Superseded editions (kept, not published as the current site)

This directory preserves the editions built by earlier automated sessions so that no work is lost.
They are **not** the current product and they are **not** re-verified.

| Folder | What it is | Why it is here |
|---|---|---|
| `legacy-v1/` | An early dashboard set (one page per topic) with the original navigation and stylesheet | Superseded by the current 13-page dashboard |
| `decision-suite/` | A later anonymised decision suite with its own data and model scripts | Superseded; its verified findings were carried into the current edition |
| `pages/` | A second supplementary dashboard set | Superseded |
| `assets/`, `legacy-scripts/` | Stylesheets, scripts and JSON used by the editions above | Kept so the archived pages still render |

## Known differences from the current edition

- The archived pages still contain the two ZIP codes that the current edition removed.
- Several of them present an "empty framework" with no financial figures; the current edition publishes
  the figures with the identifying details removed.
- Their claims have not been re-verified. Do not rely on them. Use the [current dashboard](../index.html).

## `other-edition-2026-11-10/`

A concurrent session's quantitative edition (`arena/d76d5375-tino3`, merged as PR #21): two per-property
pages, `EXECUTIVE_SUMMARY.md`, and `assets/data/*.csv`, `model.json`. It is preserved here because the
current edition replaced the root pages and no longer ships `assets/style.css`, which those pages link
to. A copy of that stylesheet sits in `other-edition-2026-11-10/assets/` so they still render. Its
figures were not re-verified by the current edition.
