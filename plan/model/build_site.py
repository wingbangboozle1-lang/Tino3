"""Build every published file from the model and the page content.

    python plan/model/build_site.py            # writes into the repository root
    python plan/model/build_site.py --out DIR  # writes the same files into DIR (used by verify)

The repository root is the published site: GitHub's branch build serves it directly and the
Actions workflow copies the same files into the artifact. Both therefore publish identical pages.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import model  # noqa: E402
import pages  # noqa: E402
import sitekit  # noqa: E402

# Paths that earlier editions published and this edition does not use. The packaged site answers
# them with a content-free notice so that a stale link can never return an old figure.
RETIRED = """cupertino.html san-francisco.html costs.html decision-analysis.html flagged.html
flagged-review.html inheritance-process.html inheritance-steps.html methodology.html properties.html
sources-verification.html taxes-estate.html script.js style.css assets/app.js assets/js/app.js
assets/css/style.css assets/style.css assets/data/property_a.csv assets/data/property_b.csv
assets/data/decision.csv pages/costs.html pages/decision-analysis.html pages/executive-summary.html
pages/flagged.html pages/inheritance-tax.html pages/methodology.html pages/process.html
pages/properties.html pages/sources.html data/costs.json data/properties.json data/summary.json
data/tax.json data/sources.json data/projections.csv data/sell_and_reinvest.csv data/sf_rental_pl.csv
data/estate_threshold.csv data/inheritance_scenarios.csv data/sources.csv data/cupertino_carrying_costs.csv
decision-suite/index.html decision-suite/executive-summary.html decision-suite/property-a.html
decision-suite/property-b.html decision-suite/taxes-and-laws.html decision-suite/projections.html
decision-suite/decision-analysis.html decision-suite/inheritance-process.html
decision-suite/flagged-for-review.html decision-suite/sources-ledger.html
decision-suite/assets/app.js decision-suite/assets/style.css""".split()


def csv_text(headers, rows) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(headers)
    w.writerows(rows)
    return buf.getvalue()


def executive_summary_md(m: dict) -> str:
    s = m["scenarios"]["2045"]
    o, bc, e = s["options"], s["b_common"], m["estate"]
    f = sitekit.money
    return f"""# Executive summary

Reviewed {sitekit.RETRIEVED}. Property A is a single-family home; Property B is a three-unit rental building.
Every amount is rounded to $10. Assessed values and tax bills are shown as privacy-rounded levels.
Full tables, sources and flags are on the site: https://wingbangboozle1-lang.github.io/Tino3/

## Best plan

Sell Property A soon after inheriting it and invest the proceeds. Keep Property B and let every unit
the heir does not occupy. Living in Property A is the right choice only if the heir wants that home
and accepts the cost shown below. Renting Property A out is never the best option.

## Why

- Inherited property takes a new tax basis equal to its value at death, so a prompt sale produces almost no income tax.
- Property A is reassessed at death. Its property tax in 2045 is about {f(s['a_tax_live_first'])} a year if the heir lives there and {f(s['a_tax_full_first'])} if not, against {f(m['status_quo'][0]['a_tax'])} today.
- A rent of $6,000 a month in today's dollars barely covers that tax, insurance and upkeep.

## Value after 20 years, inheritance in 2045, today's dollars

| Option | Result |
|---|---|
| Sell, buy a stock index fund (7.0% a year assumed) | {f(o['sell_stocks']['wealth_today'])} |
| Sell, buy U.S. Treasuries (4.8% a year) | {f(o['sell_treasuries']['wealth_today'])} |
| Rent Property A out | {f(o['rent']['wealth_today'])} |
| Live in Property A | {f(o['live']['wealth_today'])} |

Selling stays ahead when home prices rise 2.0% or 4.9% a year, when stocks return 5.0% or 9.0%, and
when Property A rents for $4,500 or $9,000 a month.

## Other findings

- Property B is reassessed whatever is done with Property A. Its property tax in 2045 rises from about {f(bc['tax_before_transfer'])} to {f(bc['property_tax'])} while rents stay limited.
- Federal estate tax exclusion: $15,000,000 per person in 2026 and $15,480,000 in 2027. After both properties, about {f(e[0]['headroom_one'])} of room is left under one exclusion today. California and its cities and counties levy no estate or inheritance tax.
- To keep part of Property A's low assessed value the heir must move in within one year of the death and file two claims.
- The solar credit ends 20 years after the system was connected.
- No official source confirmed an insurance premium for either property; both are left blank and flagged.
- The initiative to restore the old inheritance rules failed to qualify in May 2026. November 2026 ballot results are unofficial until certified.

## Before relying on this

{len([x for x in pages.FLAGS if x[0].startswith('F')])} inputs are unverified or still to be confirmed, including the trust type, the rent Property A could earn,
repair budgets and both insurance premiums. See the Flagged for Review page.

This is general information for planning, not legal, tax or investment advice.
"""


def build(out: Path) -> list[str]:
    inp = json.loads(model.PUBLIC_INPUTS.read_text(encoding="utf-8"))
    m = model.run(inp)
    files: dict[str, str] = {}

    for fn in pages.PAGES:
        slug, title, lead, body = fn(m)
        files[slug] = sitekit.page(slug, title, lead, body)
    files["assets/site.css"] = sitekit.CSS.strip() + "\n"
    files["assets/site.js"] = sitekit.JS.strip() + "\n"

    sq = m["status_quo"]
    cols = list(sq[0].keys())
    files["assets/data/projections.csv"] = csv_text(cols, [["" if r[c] is None else r[c] for c in cols] for r in sq])
    rows = []
    for t, s in m["scenarios"].items():
        for k, o in s["options"].items():
            rows.append([t, "heir uses the spare unit of Property B", k, o["first_year_cash"], o["cumulative_cash"], o["wealth"], o["wealth_today"]])
    for t, n in m["needs_home"].items():
        for k in ("live", "sell_stocks", "sell_treasuries"):
            rows.append([t, "heir needs a similar house", k, n[k]["first_year_cash"], "", n[k]["wealth"], n[k]["wealth_today"]])
    files["assets/data/scenarios.csv"] = csv_text(
        ["inheritance_year", "case", "option", "first_year_cash", "cash_over_20_years", "value_after_20_years", "value_in_2026_dollars"], rows)
    files["assets/data/estate_headroom.csv"] = csv_text(
        ["year", "exclusion", "two_exclusions", "properties", "headroom_one", "headroom_two", "projected"],
        [[r["year"], r["exclusion"], r["two_exclusions"], r["properties"], r["headroom_one"], r["headroom_two"], r["projected"]] for r in m["estate"]])
    files["assets/data/model.json"] = json.dumps(m, indent=1) + "\n"
    ledger = [{"id": k, "publisher": v[0], "title": v[1], "url": v[2], "checked": v[3], "retrieved": sitekit.RETRIEVED}
              for k, v in sitekit.SOURCES.items()]
    files["assets/sources.json"] = json.dumps(ledger, indent=1) + "\n"
    flags = [{"id": f[0], "group": f[1], "item": f[2], "why": f[3], "action": f[4], "sources": f[5]} for f in pages.FLAGS]
    files["assets/data/flags.json"] = json.dumps(flags, indent=1) + "\n"
    files["EXECUTIVE_SUMMARY.md"] = executive_summary_md(m)
    files[".nojekyll"] = ""

    for rel, text in files.items():
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
    manifest = sorted(files)
    (out / "plan" / "data").mkdir(parents=True, exist_ok=True)
    (out / "plan" / "data" / "manifest.json").write_text(json.dumps({"published": manifest, "retired": RETIRED}, indent=1) + "\n", encoding="utf-8")
    (out / "plan" / "data" / "model_outputs.json").write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT))
    args = ap.parse_args()
    manifest = build(Path(args.out))
    print(f"built {len(manifest)} files into {args.out}")


if __name__ == "__main__":
    main()
