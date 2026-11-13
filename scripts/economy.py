#!/usr/bin/env python3
"""Irregular-economy module: distributions instead of one constant growth rate.

Why this file exists
    Every other page of this edition projects with a single constant rate
    (4% house prices, 2.5% inflation, 7% stocks). The owner's brief is explicit
    that growth and inflation are never that even over fifty years. This module
    rebuilds the year-by-year case against the CURRENT root model API
    (scripts/model.py), which earlier sessions' merge left behind:

      1. official annual series from assets/data/series.json (FRED, retrieved
         2026-11-13), sliced into complete ten-year blocks;
      2. a seeded block bootstrap - 2,000 fifty-year paths drawn in ten-year
         blocks from the windows where BOTH the house price series and the
         consumer price series are present, so house and inflation history
         always move together as they did in the record;
      3. distributions (p05/p50/p95) for the two dates the decision turns on:
         the value at the 2045 inheritance and the value thirty years later;
      4. the share of draws in which selling at the inheritance and investing
         beats holding the house for thirty years (gross of income tax, which
         is near zero on a step-up sale, and net of selling costs);
      5. the Revenue and Taxation Code section 51 lesser-of rule applied along
         each draw's inflation path: the share of years in which the
         inflation-adjusted base year value falls below the 2%-capped value,
         and the property-tax difference that follows;
      6. the erosion of fixed nominal thresholds (section 121 exclusion, the
         Proposition 19 excluded amount, the federal basic exclusion) in 2045
         dollars at the modelled inflation rate.

Determinism
    The bootstrap uses random.Random(20261113) - a fixed seed - so the written
    economy.json is byte-stable across runs. No network access, no wall-clock
    input. Re-run after any change to series.json or the model constants.

Rounding and privacy
    Every money figure written out is rounded to the nearest $10 with the root
    model's money10(). No name, address, postal code, parcel number, city or
    county name appears here or in the output.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import model as base  # noqa: E402  (the root edition's model, for identical constants)

DATA = base.DATA
SERIES = base.SERIES
ASM = base.ASM
A = base.A
B = base.B
V = base.V

MODEL_JSON = json.loads((DATA / "model.json").read_text(encoding="utf-8"))

SEED = 20261113
DRAWS = 2_000
BLOCK_YEARS = 10
INFL = ASM["inflation"]["baseline"]
G = ASM["house_growth"]["baseline"]
EQ = ASM["equity_return_nominal_gross"]["baseline"]
DRAG = ASM["equity_tax_drag"]["baseline"]
SELL_PCT = ASM["selling_cost_pct"]["baseline"]
RATE_A = ASM["ad_valorem_rate_a"]["value"]
RATE_B = V["sf_secured_rate_2026_27"]["value"]
HOLD_YEARS = 30                      # the decision horizon used elsewhere on the site
INHERIT_YEAR = 2045
VALUE_A_2026 = A["estimated_market_value_2026"]

BE_GROWTH = next(p["breakeven_house_growth"] for p in MODEL_JSON["paths"]
                 if p["inherit_year"] == INHERIT_YEAR)


def money10(x: float) -> int:
    return base.money10(x)


def annual_changes(series: dict) -> tuple[dict[int, float], str, str]:
    vals = {int(y): float(v) for y, v in series["values"].items()}
    years = sorted(vals)
    chg = {y: vals[y] / vals[y - 1] - 1.0 for y in years[1:]}
    return chg, series["id"], f"{years[0]}-{years[-1]}"


def pctile(sorted_vals: list[float], q: float) -> float:
    idx = q * (len(sorted_vals) - 1)
    lo = int(idx)
    if lo >= len(sorted_vals) - 1:
        return sorted_vals[-1]
    frac = idx - lo
    return sorted_vals[lo] * (1.0 - frac) + sorted_vals[lo + 1] * frac


def p3(sorted_vals: list[float]) -> dict[str, float]:
    return {"p05": pctile(sorted_vals, 0.05),
            "p50": pctile(sorted_vals, 0.50),
            "p95": pctile(sorted_vals, 0.95)}


def build() -> dict:
    chg_house, house_id, house_span = annual_changes(SERIES["hpi_a"])
    chg_cpi, cpi_id, cpi_span = annual_changes(SERIES["cpi"])

    # Complete ten-year blocks where BOTH series have a change for every year.
    shared_years = sorted(y for y in chg_house if y in chg_cpi)
    starts = [y for y in shared_years if y + BLOCK_YEARS - 1 in chg_cpi]
    house_blocks = [[chg_house[y] for y in range(s, s + BLOCK_YEARS)] for s in starts]
    cpi_blocks = [[chg_cpi[y] for y in range(s, s + BLOCK_YEARS)] for s in starts]

    rng = random.Random(SEED)
    mult50, mult30, real30_cagr, nom50_cagr, real50_cagr = [], [], [], [], []
    val_2045, val_2076, real_2076 = [], [], []
    hold_lt_be = real30_neg = nom50_below_const = sell_wins = 0

    base_a = A["roll"][0]["assessed"]   # rolls are stored newest-first
    base_b = B["roll"][0]["assessed"]
    less_years_below_a = []
    save_a, save_b = [], []

    for _ in range(DRAWS):
        picks = [rng.randrange(len(starts)) for _ in range(5)]
        h50 = [c for b in picks for c in house_blocks[b]]
        c50 = [c for b in picks for c in cpi_blocks[b]]
        h30, c30 = h50[:HOLD_YEARS], c50[:HOLD_YEARS]

        mh50 = 1.0
        mc50 = 1.0
        for ch in h50:
            mh50 *= 1.0 + ch
        for cc in c50:
            mc50 *= 1.0 + cc
        mh30 = 1.0
        mc30 = 1.0
        for ch in h30:
            mh30 *= 1.0 + ch
        for cc in c30:
            mc30 *= 1.0 + cc

        mult50.append(mh50)
        mult30.append(mh30)
        nom50_cagr.append(mh50 ** (1.0 / 50) - 1.0)
        real50_cagr.append((mh50 / mc50) ** (1.0 / 50) - 1.0)
        real30_cagr.append((mh30 / mc30) ** (1.0 / HOLD_YEARS) - 1.0)
        val_2045.append(VALUE_A_2026 * mh30)
        val_2076.append(VALUE_A_2026 * mh50)
        real_2076.append(VALUE_A_2026 * mh50 / mc50)

        if mh30 < (1.0 + BE_GROWTH / 100.0) ** HOLD_YEARS:
            hold_lt_be += 1
        if mh30 < mc30:
            real30_neg += 1
        if mh50 < (1.0 + G) ** 50:
            nom50_below_const += 1
        if (1.0 - SELL_PCT) * (1.0 + EQ - DRAG) ** HOLD_YEARS > mh30:
            sell_wins += 1

        # RTC 51 lesser-of rule along this draw's inflation path, forward from
        # each roll's latest assessed value. Capped growth 2%; the inflation-
        # adjusted base year value is taken equal to the capped value at the
        # start (the cap has bound in every supplied year) and then grown at
        # the drawn consumer prices.
        cap_a, idx_a = float(base_a), float(base_a)
        cap_b, idx_b = float(base_b), float(base_b)
        years_below_a = 0
        tot_a = tot_b = 0.0
        for cc in c50:
            cap_a *= 1.02
            idx_a *= 1.0 + cc
            cap_b *= 1.02
            idx_b *= 1.0 + cc
            if idx_a < cap_a:
                years_below_a += 1
                tot_a += (cap_a - idx_a) * RATE_A
            if idx_b < cap_b:
                tot_b += (cap_b - idx_b) * RATE_B
        less_years_below_a.append(years_below_a / 50.0)
        save_a.append(tot_a)
        save_b.append(tot_b)

    s_mult50, s_mult30 = sorted(mult50), sorted(mult30)
    s_val45, s_val76, s_real76 = sorted(val_2045), sorted(val_2076), sorted(real_2076)
    s_n50, s_r50, s_r30 = sorted(nom50_cagr), sorted(real50_cagr), sorted(real30_cagr)
    s_below_a, s_save_a, s_save_b = sorted(less_years_below_a), sorted(save_a), sorted(save_b)

    def money_row(key: str, vals: list[float], constant: float, note: str) -> dict:
        d = p3(sorted(vals))
        return {"key": key, "unit": "money", "p05": money10(d["p05"]),
                "p50": money10(d["p50"]), "p95": money10(d["p95"]),
                "constant": money10(constant), "note": note}

    def pct_row(key: str, vals: list[float], constant: float, note: str) -> dict:
        d = p3(sorted(vals))
        return {"key": key, "unit": "pct", "p05": d["p05"] * 100, "p50": d["p50"] * 100,
                "p95": d["p95"] * 100, "constant": constant * 100, "note": note}

    rows = [
        money_row("Property A value at the 2045 inheritance, nominal",
                  s_val45, VALUE_A_2026 * (1 + G) ** 19,
                  "Constant case: the model's 4% a year."),
        money_row("Property A value in 2076, nominal",
                  s_val76, VALUE_A_2026 * (1 + G) ** 50,
                  "Constant case: the model's 4% a year."),
        money_row("Property A value in 2076, in 2026 dollars",
                  s_real76, VALUE_A_2026 * ((1 + G) / (1 + INFL)) ** 50,
                  "Deflated by the same draw's consumer price path."),
        pct_row("House growth per year over fifty years, nominal",
                s_n50, G, "The constant model sits inside the band, not at its middle."),
        pct_row("House growth per year over fifty years, real",
                s_r50, (1 + G) / (1 + INFL) - 1,
                "Growth after the same draw's inflation."),
        pct_row(f"House growth per year, {INHERIT_YEAR} to {INHERIT_YEAR + HOLD_YEARS}, nominal",
                s_mult30 and [(m ** (1.0 / HOLD_YEARS)) - 1.0 for m in s_mult30], G,
                "The window the hold-versus-sell decision actually turns on."),
    ]

    shares = [
        {"key": f"Draws where fifty-year nominal house growth is below the {G * 100:.0f}% constant",
         "value": nom50_below_const / DRAWS},
        {"key": f"Draws where growth from {INHERIT_YEAR} is below the {BE_GROWTH:.2f}% break-even the decision page publishes",
         "value": hold_lt_be / DRAWS},
        {"key": f"Draws where real house growth from {INHERIT_YEAR} is negative",
         "value": real30_neg / DRAWS},
        {"key": f"Draws where selling at {INHERIT_YEAR} and investing beats holding for {HOLD_YEARS} years",
         "value": sell_wins / DRAWS},
    ]

    bootstrap = {
        "series": {"house": house_id, "house_span": house_span,
                   "cpi": cpi_id, "cpi_span": cpi_span},
        "blocks": len(starts), "block_years": BLOCK_YEARS,
        "draws": DRAWS, "seed": SEED,
        "method": ("Ten-year blocks are drawn with replacement from the complete windows where "
                   "both the house price series and the consumer price series are present, so "
                   "house and inflation history move together as they did in the record. The "
                   "consumer price series ends before the house price series, which is why the "
                   "count of blocks is smaller than the house record alone allows. Each draw is "
                   "five blocks: fifty years."),
        "rows": rows,
        "shares": shares,
        "wins": {"case": f"Sell at {INHERIT_YEAR} and invest at {((EQ - DRAG) * 100):.2f}% net, "
                         f"against holding the house for {HOLD_YEARS} years",
                 "sell_wins_share": sell_wins / DRAWS, "draws": DRAWS,
                 "note": ("A pure asset-price race, and nothing more: the sell path deducts "
                          "selling costs and then earns the net equity return; the hold path "
                          "earns only the house price path. Rents, property tax, insurance, "
                          "maintenance and the housing that living in the home provides are "
                          "excluded on BOTH sides, so this share says nothing on its own about "
                          "the decision. The tax-aware comparison is the break-even share above: "
                          "holding has to outgrow the published break-even rate, which the "
                          "constant model derives from the full cost and tax structure.")},
    }

    lesser_of = {
        "rule": "Revenue and Taxation Code section 51: the taxable value is the lesser of the "
                "enrolled (Proposition 13-capped) value or the base year value adjusted for "
                "inflation. The assessor applies it when prices fall.",
        "a": {"share_years_indexed_below_cap_p50": s_below_a[len(s_below_a) // 2],
              "share_years_indexed_below_cap_p95": s_below_a[int(0.95 * (DRAWS - 1))],
              "saving_p05": money10(p3(s_save_a)["p05"]),
              "saving_p50": money10(p3(s_save_a)["p50"]),
              "saving_p95": money10(p3(s_save_a)["p95"]),
              "rate": RATE_A, "base": base_a},
        "b": {"share_years_indexed_below_cap_p50": p3(s_below_a)["p50"],
              "saving_p05": money10(p3(s_save_b)["p05"]),
              "saving_p50": money10(p3(s_save_b)["p50"]),
              "saving_p95": money10(p3(s_save_b)["p95"]),
              "rate": RATE_B, "base": base_b},
        "note": ("Forward-looking only: the cap has bound in every supplied year, so the "
                 "inflation-adjusted value is taken equal to the capped value at the start and "
                 "the two are then grown apart by the drawn consumer prices and the 2% cap. "
                 "Savings are the ad valorem part of the bill only; fixed charges do not scale "
                 "with value."),
    }

    y19 = (1 + INFL) ** 19
    excl121 = V["section121_exclusion_joint"]["value"]
    prop19_cap = V["prop19_value_cap_2025_2027"]["value"]
    fed = V["federal_basic_exclusion_2026"]["value"]
    salt = 10_000
    prop19_nominal_2045 = prop19_cap * (1 + G) ** 10   # adjusted every second February, 2027 to 2045
    thresholds = [
        {"item": "Section 121 home-sale exclusion, joint",
         "nominal_2026": money10(excl121), "rule": "Fixed by statute since 1997; not indexed.",
         "nominal_2045": money10(excl121), "real_2045": money10(excl121 / y19),
         "note": "The same nominal dollars buy roughly a third less house.",
         "sources": ["irs_p523"]},
        {"item": "Proposition 19 excluded amount on a family-home transfer",
         "nominal_2026": money10(prop19_cap),
         "rule": "Adjusted every second February by the FHFA California house price index.",
         "nominal_2045": money10(prop19_nominal_2045), "real_2045": money10(prop19_nominal_2045 / y19),
         "note": "Modelled at the baseline house-growth rate. The real amount is published by the "
                 "board every second February and is not knowable in advance.",
         "sources": ["boe_lta25009"]},
        {"item": "Federal estate tax basic exclusion",
         "nominal_2026": money10(fed), "rule": "Indexed to inflation by law from 2026.",
         "nominal_2045": money10(fed * y19), "real_2045": money10(fed),
         "note": "Holds roughly constant in real terms if indexation tracks inflation; a change "
                 "of statute could cut it, which the estate page treats as the main risk.",
         "sources": ["irs_estate", "irs_2027"]},
        {"item": "State and local tax deduction cap",
         "nominal_2026": money10(salt), "rule": "Fixed by statute; not indexed. Not modelled on this site.",
         "nominal_2045": money10(salt), "real_2045": money10(salt / y19),
         "note": "Listed for completeness; the model takes no federal deduction for state tax.",
         "sources": []},
    ]

    return {
        "meta": {"built": "2026-11-13", "deterministic": True, "seed": SEED,
                 "draws": DRAWS, "block_years": BLOCK_YEARS,
                 "series_house": house_id, "series_cpi": cpi_id,
                 "rounding": "nearest $10",
                 "method": "Seeded block bootstrap of the official FRED annual record; "
                           "see the module docstring."},
        "bootstrap": bootstrap,
        "lesser_of": lesser_of,
        "thresholds": thresholds,
    }


if __name__ == "__main__":
    m = build()
    (DATA / "economy.json").write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
    b = m["bootstrap"]
    print("blocks", b["blocks"], "draws", b["draws"], "seed", b["seed"])
    for r in b["rows"]:
        print(f"  {r['key']}: p05 {r['p05']:,} p50 {r['p50']:,} p95 {r['p95']:,} "
              f"constant {r['constant']:,} ({r['unit']})")
    for s in b["shares"]:
        print(f"  share: {s['key']} = {s['value'] * 100:.1f}%")
    print("  wins:", b["wins"]["case"], "->", f"{b['wins']['sell_wins_share'] * 100:.1f}%")
    lo = m["lesser_of"]
    for k in ("a", "b"):
        print(f"  lesser-of {k}: years indexed below cap p50 "
              f"{lo[k]['share_years_indexed_below_cap_p50'] * 100:.1f}%, "
              f"saving p50 {lo[k]['saving_p50']:,}")
    for t in m["thresholds"]:
        print(f"  threshold: {t['item']} 2045 real {t['real_2045']:,}")
