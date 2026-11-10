# Inheritance Atlas

A privacy-first decision dashboard for a trust inheritance expected between 2040 and 2050: one residence to
inherit, one three-unit building already held and partly rented, and enough inherited cash to matter for
federal estate tax.

**Live site:** https://wingbangboozle1-lang.github.io/Tino3/

## What this repository publishes

Ten static pages, one stylesheet, one source ledger, three CSV downloads, and three preserved annex editions
— nothing else. The published artifact is an allowlist built by `scripts/package_site.py`; every path an
earlier edition published is replaced by a content-free withdrawal notice, so a stale URL cannot return an old
figure. The annexes are published verbatim because they are already anonymized and `$10`-rounded:

| Annex | Contents | Verifier |
|---|---|---|
| `decision-suite/` | The earlier full Decision Brief restored from merged PR #15: 10 pages, 218 `.gov`-cited rows, 2026–2055 property-level series, estate headroom, trust-inheritance walkthrough, own source ledger | `decision-suite/scripts/verify_suite.py` |
| `verified-dashboard/` | Official-source research supplement (PR #14, preserved) | `tools/verify_416807ea.py` |
| `audit/` | Independent privacy and source audit record (PR #7, preserved) | — |

The two quantitative layers measure different things (strategy-level ten-year wealth contributions in the
annex versus household terminal net worth at 2055 in this edition), so their figures are not interchangeable;
both pages say so explicitly. Where they differ, this edition's figures and assumption register govern.

| Page | Contents |
|---|---|
| `index.html` | Dashboard, recommendation, decision snapshot |
| `executive-summary.html` | The decision, five numbers, what would change it |
| `property-a.html` | The residence to inherit: assessment history, carrying costs, 2026–2055 projection |
| `property-b.html` | The rental: rent roll, operating statement, the unreconciled tax bill, projections |
| `taxes.html` | Federal, California and local rules, verified; pending law changes |
| `projections.html` | 30-year outlook and the full assumption register |
| `decision.html` | Live vs rent vs sell/bonds, sensitivity matrix, break-even |
| `inheritance.html` | Statutory timeline after the death, with deadlines |
| `review.html` | 19 flagged items and the repository-history disclosure (R-13) |
| `sources.html` | 23 official sources, what each one actually verifies |

## Privacy rules enforced in code

- No names, street addresses, ZIP codes, parcel numbers, utility account numbers or unrounded assessment
  figures in any published file. `scripts/verify.py` fails the build if a ZIP-code pattern, a city name, an
  e-mail address, a street address or a non-$10 amount appears in a page or in the data files.
- Properties appear only as `[PROPERTY_A]` and `[PROPERTY_B]`; jurisdictions are described generically, with
  the official rate documents cited.
- No forms, no scripts, no analytics, no remote assets. Nothing on the site accepts or stores input.

## Verification standard

Every rule on the site was retrieved from the publishing agency's own domain on 10 November 2026 and linked
from the row that uses it. `assets/sources.json` records what each document verifies. Anything that could not
be verified is left blank or published on the Flagged for Review page — never inferred.

Integration re-check (`arena-9233adb2-tino3`, 2026-11-10) added five sources and resolved two flags:

- `irs_2027` — IRS IR-2026-133 / Rev. Proc. 2026-35: 2027 basic exclusion `$15,480,000`; 2027 annual gift
  exclusion `$20,000`. FL-08 resolved: the earlier 404 came from a truncated URL, so the model now anchors
  2026–2027 to published amounts instead of a scenario index (indexing after 2027 remains a scenario).
- `sos_memo` — CA SOS CC/ROV Memorandum #26138 (18 May 2026): initiative 25-0017 **failed to qualify**; it was
  not on the 3 November 2026 ballot and Proposition 19 rules stand.
- `sb974` — SB 974, Stats. 2026 ch. 665: court-established special needs trusts are an eligible medium of
  transfer under R&TC §63.2; effective 1 January 2027.
- `sf_treasurer` — FY2026-27 secured rate 1.18162182% (the edition previously used FY2025-26
  `$1.18268325`/`$100`; both are now cited and distinguished by fiscal year, irregularity I-1).
- `sf_rentboard` — allowable rent increase 1.6% (Mar 2026–Feb 2027), plus pending File No. 261020 (10%/yr cap
  on combined banked and capital-improvement increases; **not enacted**). FL-11 updated with the verified cap.

## Build

```bash
python3 scripts/model.py                        # writes assets/data/model.json and the CSV downloads
python3 scripts/build.py                        # renders the ten pages
python3 scripts/verify.py                       # reproducible-build, citation, link, privacy and rounding checks
python3 decision-suite/scripts/verify_suite.py  # annex: citations, $10 rounding, identifier-leak digests
python3 tools/verify_416807ea.py                # supplement: citation and identifier-token digests
python3 scripts/package_site.py                 # writes the _site artifact (allowlist + withdrawal notices)
```

CI runs the first three on every push and pull request (`.github/workflows/verify.yml`) and the packaging step
on merges to `main` (`.github/workflows/pages.yml`).

`verify.py` re-runs the model and the renderer and fails if any published byte changes, so a stale committed
page cannot survive CI. It also fails on any table row that cites neither an official source nor the internal
assumption register.

## Data

`assets/sources.json` — source ledger (23 entries).
`assets/data/model.json` — every figure on the site.
`assets/data/property_a.csv`, `property_b.csv`, `decision.csv` — the same numbers for offline work.

## Limits

This is a planning model, not an appraisal, a title report, a tax return or legal advice. Insurance premiums,
future market values, future statutory thresholds and county parcel facts are not verifiable from public
sources today and are flagged as unverified.

## Coordination

`COORDINATION.md` is the shared task board for parallel sessions, including the handoff log, the privacy
remediation record and the deployment result.
