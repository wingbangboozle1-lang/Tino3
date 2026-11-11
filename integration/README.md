# Requirements & verification

An independent, privacy-safe traceability section for the inheritance decision dashboard. It is an index and a check, not a fourth financial model.

| Page | Contents |
|---|---|
| `index.html` | Landing page, category cards, and the full requirements matrix |
| `executive-summary.html` | The decision and the important numbers, each labelled by basis |
| `findings.html` | Official-source ledger with the exact words relied on and how each document was checked |
| `flagged.html` | Unverified values left blank, irregularities, and owner decisions |

## Build and verify

```bash
python3 integration/tools/build.py
python3 integration/tools/verify.py
```

`build.py` renders the four pages and four CSV downloads from `integration/data/*.json`. `verify.py` re-runs the build and fails on stale output, broken links, non-official hosts, table rows without an official source link, PII patterns, or any dollar amount that is not a multiple of $10.

## Privacy

Placeholders only: Property A, Property B, County A, City B. No name, street address, postal code, parcel number, utility account number, or unrounded roll figure. Public-roll values are generalized further on the root edition; this section publishes no property-specific amounts.

## Coordination

This section was built on branch `arena/f31530e0-tino3`. The PR link, merge result, and GitHub Pages deployment confirmation are recorded in `COORDINATION.md`. Flagged items do not block publication; they are published for later review.
