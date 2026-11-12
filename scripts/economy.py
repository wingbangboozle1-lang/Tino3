#!/usr/bin/env python3
"""Year-by-year economy section: real paths instead of one constant growth rate.

Why this file exists
    Every other page of this edition projects with a single constant rate (4% house prices,
    2.5% inflation, 7% stocks, 4.88% Treasuries). The owner's brief is explicit that growth and
    inflation are never that even over fifty years. This module builds the year-by-year case:

      1. official annual series, read from the publisher's own export on 12 November 2026;
      2. whole-path replays of the official record (2026-2075 mapped onto 1977-2025);
      3. a block bootstrap - 2,000 fifty-year paths drawn in ten-year blocks from the 40 complete
         ten-year stretches of the official record - so the 50-year figures are distributions,
         not a single guess;
      4. the sell / rent / move-in decision re-run on each of the 40 real ten-year stretches;
      5. adversarial paths as the counter-case (stagflation, a lost decade for houses,
         high inflation, deflation);
      6. the RTC 51 "lesser of" rule applied year by year, which the constant model cannot show.

Year convention
    The value of a property *at the start of* year Y is its 2026 value grown by every recorded
    annual change from 2026 to Y-1. A fifty-year projection therefore runs 2026 to 2075 and is
    stated at the start of 2076.

Guarantees
    * Every money figure written out is rounded to the nearest $10.
    * No name, address, ZIP code, parcel number, city or county name appears here.
    * Arithmetic reuses the root model's own constants (scripts/model.py), and the constant case
      in this module is asserted equal to that model's published answer at build time.
    * Nothing is inferred: the publisher's blank years are excluded and the exclusion is stated
      on the page.

Output: assets/data/economy.json, consumed by scripts/build.py.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import model as base  # noqa: E402  (the root edition's model, for identical constants)

OUT = ROOT / "assets" / "data"
r10 = base.r10

# ---------------------------------------------------------------------------------------------
# 1. Official annual series. Retrieved 12 November 2026 from each publisher's own export.
#    Percent per year, except "tsy", which is a yield level in percent.
# ---------------------------------------------------------------------------------------------
RETRIEVED = "12 November 2026"

SERIES = {
    # CPIAUCSL - consumer price index, annual average, percent change from a year ago
    # (U.S. Bureau of Labor Statistics via FRED). The publisher's percent-change export ends
    # blank at 2025, so 2025 is computed from the published annual index levels
    # 321.962 / 313.698 - 1 = 2.6345%. 2026 is excluded: the annual average is not yet published.
    "cpi": (1977, [
        6.46956, 7.62991, 11.25303, 13.50172, 10.37831, 6.15836, 3.15953, 4.36820, 3.52790, 1.94393,
        3.57821, 4.10004, 4.79109, 5.41922, 4.21583, 3.04162, 2.96965, 2.59560, 2.80542, 2.93667,
        2.33757, 1.54701, 2.19314, 3.36668, 2.81663, 1.59567, 2.29800, 2.66757, 3.36583, 3.22209,
        2.87055, 3.81495, -0.32036, 1.63657, 3.13965, 2.07319, 1.46597, 1.61546, 0.12114, 1.26736,
        2.13144, 2.43900, 1.81326, 1.25294, 4.68124, 7.99082, 4.12696, 2.95211, 2.63454]),
    # ATNHPIUS41940Q - all-transactions house price index, metropolitan area of Property A
    # (Federal Housing Finance Agency data via FRED), annual average, percent change.
    "house_a": (1977, [
        28.44154, 14.93783, 17.72602, 21.71026, 11.75401, -5.07396, 7.90608, 5.89226, 7.80106, 7.27449,
        8.99835, 18.63166, 30.19487, 3.36953, -4.07066, -1.24806, -2.52766, -1.99139, 1.23059, 4.01184,
        11.08767, 13.58757, 11.62214, 26.86831, 11.68823, 0.55117, 2.64622, 10.58592, 20.88524, 9.15501,
        -2.13347, -11.36730, -12.31781, 0.01867, -2.15967, 2.87918, 14.09707, 11.92381, 10.05582, 7.95046,
        4.54400, 9.91454, -1.10663, -0.23957, 6.14748, 15.09501, 3.58776, 5.29865, 0.69254]),
    # ATNHPIUS41884Q - the same index for the area of Property B.
    "house_b": (1977, [
        23.23613, 12.67514, 21.22210, 20.09511, 3.85225, -6.45460, 14.64423, 4.67774, 8.40854, 11.24737,
        17.03814, 23.34055, 21.10030, 3.39225, -4.77007, -1.74135, -2.89500, -1.87404, 0.33952, 1.34604,
        7.87077, 12.17825, 13.63157, 23.44088, 11.80393, 4.48647, 5.24100, 13.05059, 19.20015, 7.48889,
        -0.99902, -8.86612, -8.65201, -1.79851, -3.32270, 2.71858, 13.71519, 13.09985, 12.14671, 8.98352,
        4.63838, 9.02282, -0.41251, -2.78861, 1.26782, 12.24586, -0.24325, 4.05959, 0.79376]),
    # GS10 - 10-year Treasury constant maturity, annual average of daily yields
    # (Board of Governors of the Federal Reserve System via FRED). A level, not a return.
    "tsy": (1977, [
        7.42, 8.41, 9.44, 11.46, 13.91, 13.00, 11.11, 12.44, 10.62, 7.68,
        8.38, 8.85, 8.50, 8.55, 7.86, 7.01, 5.87, 7.08, 6.58, 6.44,
        6.35, 5.26, 5.64, 6.03, 5.02, 4.61, 4.02, 4.27, 4.29, 4.79,
        4.63, 3.67, 3.26, 3.21, 2.79, 1.80, 2.35, 2.54, 2.14, 1.84,
        2.33, 2.91, 2.14, 0.89, 1.44, 2.95, 3.96, 4.21, 4.29]),
    # NASDAQCOM - NASDAQ Composite, annual average, percent change (Nasdaq, Inc. via FRED).
    "stock": (1977, [
        9.80223, 19.06086, 16.20881, 23.45520, 20.48834, -6.97814, 51.04134, -12.80262, 16.61774, 26.43128,
        9.70274, -6.98965, 16.92319, -6.53823, 20.16498, 21.87786, 19.34022, 5.10352, 23.08698, 25.91474,
        26.14195, 22.14505, 51.99372, 38.69028, -46.21639, -24.33737, 6.95442, 20.61770, 5.68887, 7.81501,
        13.91956, -16.16394, -14.63210, 27.33893, 13.93881, 10.76097, 19.41397, 23.54540, 13.03855, 0.85409,
        25.01118, 19.09546, 6.92507, 28.47922, 40.87765, -14.89260, 6.04126, 32.97673, 18.86735]),
}

YEAR0, NYEARS = 1977, 49
OFFICIAL_YEARS = list(range(YEAR0, YEAR0 + NYEARS))
D = {k: {first + i: v for i, v in enumerate(vals)} for k, (first, vals) in SERIES.items()}
for k, (first, vals) in SERIES.items():
    assert len(vals) == NYEARS, (k, len(vals))

BLOCK = {y: {"cpi": D["cpi"][y] / 100.0, "ga": D["house_a"][y] / 100.0, "gb": D["house_b"][y] / 100.0,
             "rs": D["stock"][y] / 100.0, "rt": D["tsy"][y] / 100.0} for y in OFFICIAL_YEARS}
WINDOWS = [OFFICIAL_YEARS[i:i + 10] for i in range(NYEARS - 9)]        # 40 complete decades
assert len(WINDOWS) == 40

CAP = base.V["prop13_cap"]                                             # 2% assessment cap
START = 2026
HORIZON = 50                                                           # annual changes 2026-2075
END = START + HORIZON                                                  # values stated at the start of 2076
CONST = {"cpi": base.A["inflation"], "ga": base.A["g"], "gb": base.A["g"],
         "rs": base.A["stock_return"], "rt": base.V["treasury_10y"]}
CONST_PATH = [dict(CONST) for _ in range(HORIZON + 10)]


# ---------------------------------------------------------------------------------------------
# 2. Helpers
# ---------------------------------------------------------------------------------------------
def infl_factor(cpi_change: float) -> float:
    """RTC 51(a)(1)(D): the annual inflation factor, never more than 2%. Negative CPI is not used
    (the statute caps the increase; a falling CPI simply leaves the factor at zero)."""
    return max(0.0, min(CAP, cpi_change))


def path_arrays(path, start=START):
    keys = ("cpi", "ga", "gb", "rs", "rt")
    out = {k: {} for k in keys}
    for i, b in enumerate(path):
        for k in keys:
            out[k][start + i] = b[k]
    return out["cpi"], out["ga"], out["gb"], out["rs"], out["rt"]


def value_at(base_value: float, rates: dict, year: int, start: int = START) -> float:
    """Market value at the start of `year`, grown by every annual change from `start` to year-1."""
    v = base_value
    for y in range(start, year):
        v *= 1.0 + rates.get(y, 0.0)
    return v


def cpi_at(rates: dict, year: int, start: int = START) -> float:
    """Cumulative consumer-price multiple at the start of `year` (start year = 1.0)."""
    m = 1.0
    for y in range(start, year):
        m *= 1.0 + rates.get(y, 0.0)
    return m


def tax_path(base_value_start: float, market_rates: dict, cpi: dict, first_year: int = START,
             last_year: int = END - 1):
    """Taxable value year by year under RTC 51(a): the lesser of the factored base year value and
    the full cash value (market value) on the lien date. `base_value_start` is the base year value
    in `first_year` (2026), before that year's factor."""
    out, factor = [], 1.0
    for y in range(first_year, last_year + 1):
        if y > first_year:
            factor *= 1.0 + infl_factor(cpi.get(y, base.A["inflation"]))
        market = value_at(_market_start, market_rates, y)
        out.append({"year": y, "market": market, "factor": factor,
                    "taxable": min(base_value_start * factor, market)})
    return out


_market_start = 0.0        # set by the caller through the closure below


def taxable_series(base_value_start: float, market_2026: float, market_rates: dict, cpi: dict,
                   first_year: int = START, last_year: int = END - 1):
    out, factor = [], 1.0
    for y in range(first_year, last_year + 1):
        if y > first_year:
            factor *= 1.0 + infl_factor(cpi.get(y, base.A["inflation"]))
        market = value_at(market_2026, market_rates, y)
        out.append({"year": y, "market": market, "factor": factor,
                    "taxable": min(base_value_start * factor, market)})
    return out


def tax_a(taxable: float, year: int, cpi: dict) -> float:
    """Property A's bill: the ad valorem rate on the taxable value plus fixed charges that rise
    with the path's own cumulative inflation."""
    return taxable * base.A["rate_a"] + base.FIXED_A * cpi_at(cpi, year + 1)


def tax_b(taxable: float, year: int, cpi: dict) -> float:
    # Property B's fixed charges are indexed from 2025 in the root model, so one extra year.
    return taxable * base.V["rate_b_2026"] + base.FIXED_B * cpi_at(cpi, year + 1)


# ---------------------------------------------------------------------------------------------
# 3. The decision re-run on a real path (same structure as model.run, rates for every year)
# ---------------------------------------------------------------------------------------------
def run_path(option: str, year: int, path, rent_a_mo: float | None = None,
             ins_mult: float = 1.0, n: int | None = None, from_start: bool = False):
    n = n or base.A["hold_years"]
    rent_a_mo = base.A["rent_a_mo"] if rent_a_mo is None else rent_a_mo
    # The path describes the years after the death. The years before it are the baseline
    # (2026 to the death year), so the market value at death and the cost index up to it match
    # scripts/model.py exactly; only the post-death economy varies.
    full = list(path) if from_start else [dict(CONST) for _ in range(max(0, year - START))] + list(path)
    cpi, ga, gb, rs, rt = path_arrays(full, START)

    fmv = value_at(base.IN["a_value"], ga, year)
    base_av = base.a_base(year)
    amount = base.V["prop19_amount"]
    for k in range(2027, year + 1, 2):
        amount *= 1.0 + ga.get(k - 1, base.A["g"])
    av_live = base_av + max(0.0, fmv - base_av - amount)
    av_rent = fmv
    start = fmv * (1 - base.SELL_COST)

    p = basis = start
    for y in range(year, year + n):
        div = p * base.A["stock_dividend"]
        tax = div * base.A["t_div"]
        p = p * (1 + rs.get(y, base.A["stock_return"])) - tax
        basis += div - tax
    stock_end = p - max(0.0, p - basis) * base.T_GAIN
    r_eq = (stock_end / start) ** (1 / n) - 1

    if option == "sell_stock":
        return {"wealth": stock_end, "first_cash": 0.0, "tax_first": 0.0, "asset": stock_end, "r_eq": r_eq}
    if option == "sell_treasury":
        w = start
        for y in range(year, year + n):
            w *= 1.0 + rt.get(y, base.V["treasury_10y"]) * (1 - base.A["t_treasury"])
        return {"wealth": w, "first_cash": 0.0, "tax_first": 0.0, "asset": w, "r_eq": r_eq}

    dep = base.A["building_share_a"] * fmv / base.V["depreciation_years"]
    flows, tax_first, rent_first = [], 0.0, 0.0
    for t in range(n):
        y = year + t
        mult = cpi_at(cpi, y, START)
        ins = base.IN["a_ins_guess"] * ins_mult * mult
        maint = base.A["maint_a"] * mult
        av = av_live if option == "live" else av_rent
        for k in range(year, y):
            av = min(av * (1 + infl_factor(cpi.get(k, base.A["inflation"]))), fmv * value_at(1.0, ga, k + 1, year))
        ptax = av * base.A["rate_a"] + base.FIXED_A * mult
        if option == "live":
            unit3 = (base.A["unit3_rent_mo"] * 12 * (1 + base.A["rent_growth"]) ** (year - 2026)
                     * (1 + base.V["rent_cap_share_of_cpi"] * cpi.get(y, base.A["inflation"])) ** t
                     * (1 - base.A["vacancy"]) * (1 - base.A["t_ord"]))
            cf = unit3 - (ptax + ins + maint + base.IN["a_water"] * mult + base.IN["a_electric"])
        else:
            rent = rent_a_mo * 12 * (1 + base.A["rent_growth"]) ** (y - 2026) * (1 - base.A["vacancy"])
            noi = rent - ptax - ins - maint
            cf = noi - base.A["t_ord"] * (noi - dep)
            if t == 0:
                rent_first = rent
        if t == 0:
            tax_first = ptax
        flows.append(cf)

    fv = sum(cf * (1 + r_eq) ** (n - 1 - t) for t, cf in enumerate(flows))
    net_sale = fmv * value_at(1.0, ga, year + n, year) * (1 - base.SELL_COST)
    if option == "live":
        gain_tax = base.T_GAIN * max(0.0, net_sale - fmv - base.V["home_sale_exclusion_joint"])
    else:
        gain_tax = base.T_RECAP * (dep * n) + base.T_GAIN * max(0.0, net_sale - fmv)
    return {"wealth": net_sale - gain_tax + fv, "first_cash": flows[0], "tax_first": tax_first,
            "asset": net_sale - gain_tax, "r_eq": r_eq, "rent_first": rent_first}


OPTIONS = [("sell_stock", "Sell A, buy a stock index fund"), ("sell_treasury", "Sell A, buy Treasuries"),
           ("rent", "Keep A and rent it out"), ("live", "Move into A")]


def percentile(sorted_vals, q):
    i = (len(sorted_vals) - 1) * q
    lo, hi = int(i), min(int(i) + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (i - lo)


def cagr(mult: float, years: int) -> float:
    return round(mult ** (1 / years) - 1, 4)


# ---------------------------------------------------------------------------------------------
# 4. Build
# ---------------------------------------------------------------------------------------------
def build():
    d = {"meta": {"retrieved": RETRIEVED, "record": [YEAR0, OFFICIAL_YEARS[-1]], "n_years": NYEARS,
                  "windows": len(WINDOWS), "windows_first": [w[0] for w in WINDOWS],
                  "blocks_drawn": 2000, "block_years": 10, "seed": 20261112,
                  "horizon": [START, END - 1], "stated_at": END}}

    # --- 4a. what the official record shows, series by series
    d["stats"] = []
    for key, label, is_level in (("cpi", "Consumer prices (CPI-U, US city average)", False),
                                 ("house_a", "House prices, area of Property A", False),
                                 ("house_b", "House prices, area of Property B", False),
                                 ("tsy", "10-year Treasury yield (level, annual average)", True),
                                 ("stock", "NASDAQ Composite (index level change)", False)):
        vals = SERIES[key][1]
        mult = 1.0
        for v in vals:
            mult *= (1 + v / 100.0)
        d["stats"].append({
            "key": key, "label": label, "first": YEAR0, "last": OFFICIAL_YEARS[-1], "n": len(vals),
            "down": sum(1 for v in vals if v < 0),
            "min": min(vals), "min_year": OFFICIAL_YEARS[vals.index(min(vals))],
            "max": max(vals), "max_year": OFFICIAL_YEARS[vals.index(max(vals))],
            "mean": round(sum(vals) / len(vals), 2), "level": is_level,
            "cagr": None if is_level else cagr(mult, len(vals)),
            "spread": round(max(vals) - min(vals), 2)})

    # --- 4b. whole-path replays: the record read in order, thirty years at a time
    #      (a rotation of a 49-year record would share 49 of 50 values and say nothing)
    replay, RH = [], 30
    for off in range(1977, 2026 - RH + 1, 3):
        idx = OFFICIAL_YEARS.index(off)
        seq = OFFICIAL_YEARS[idx:idx + RH]
        path = [BLOCK[y] for y in seq]
        cpi, ga, gb, rs, rt = path_arrays(path)
        end = START + RH
        a_end = value_at(base.IN["a_value"], ga, end)
        b_end = value_at(base.IN["b_value"], gb, end)
        rm = cpi_at(cpi, end)
        a_tax = taxable_series(base.IN["a_av_2026"], base.IN["a_value"], ga, cpi, START, end - 1)
        b_tax = taxable_series(base.IN["b_av_2025"] * (1 + CAP), base.IN["b_value"], gb, cpi, START, end - 1)
        const_a = base.IN["a_value"] * (1 + base.A["g"]) ** RH
        replay.append({
            "start_analog": seq[0], "end_analog": seq[-1], "years": RH,
            "a_value": r10(a_end), "a_value_real": r10(a_end / rm),
            "b_value": r10(b_end), "b_value_real": r10(b_end / rm),
            "a_taxable": r10(a_tax[-1]["taxable"]), "a_tax": r10(tax_a(a_tax[-1]["taxable"], end - 1, cpi)),
            "b_tax": r10(tax_b(b_tax[-1]["taxable"], end - 1, cpi)),
            "a_tax_if_cap_only": r10(base.a_base(end - 1) * base.A["rate_a"] + base.FIXED_A * rm),
            "cpi_multiple": round(rm, 2),
            "a_cagr": cagr(a_end / base.IN["a_value"], RH),
            "b_cagr": cagr(b_end / base.IN["b_value"], RH),
            "cpi_cagr": cagr(rm, RH),
            "down_years_a": sum(1 for y in range(START, end) if ga.get(y, 0) < 0),
            "vs_constant": r10(a_end - const_a),
            "lesser_of_binds": sum(1 for r in a_tax[1:] if r["taxable"] < base.IN["a_av_2026"] * r["factor"] - 0.5),
        })
    d["replay"] = replay

    # --- 4c. block bootstrap: 2,000 fifty-year paths in ten-year blocks from the 40 windows
    rng = random.Random(d["meta"]["seed"])
    n_blocks = HORIZON // 10
    boot = []
    for _ in range(d["meta"]["blocks_drawn"]):
        path = []
        for _ in range(n_blocks):
            path.extend(BLOCK[y] for y in rng.choice(WINDOWS))
        boot.append(path)

    metrics = {k: [] for k in ("a_value", "a_value_real", "a_tax", "a_tax_real", "a_taxable",
                               "b_value", "b_tax", "cpi_multiple", "sell_stock", "sell_treasury", "rent", "live")}
    for path in boot:
        cpi, ga, gb, rs, rt = path_arrays(path)
        rm = cpi_at(cpi, END)
        a_tax = taxable_series(base.IN["a_av_2026"], base.IN["a_value"], ga, cpi)
        b_tax = taxable_series(base.IN["b_av_2025"] * (1 + CAP), base.IN["b_value"], gb, cpi)
        a_val = value_at(base.IN["a_value"], ga, END)
        bill = tax_a(a_tax[-1]["taxable"], END - 1, cpi)
        metrics["a_value"].append(a_val)
        metrics["a_value_real"].append(a_val / rm)
        metrics["a_taxable"].append(a_tax[-1]["taxable"])
        metrics["a_tax"].append(bill)
        metrics["a_tax_real"].append(bill / rm)
        metrics["b_value"].append(value_at(base.IN["b_value"], gb, END))
        metrics["b_tax"].append(tax_b(b_tax[-1]["taxable"], END - 1, cpi))
        metrics["cpi_multiple"].append(rm)
        for k, _ in OPTIONS:
            metrics[k].append(run_path(k, 2045, path)["wealth"])

    labels = {"a_value": "Property A market value, 2076", "a_value_real": "Property A market value, 2076, in 2026 dollars",
              "a_taxable": "Property A taxable value, 2076", "a_tax": "Property A tax bill, 2076",
              "a_tax_real": "Property A tax bill, 2076, in 2026 dollars",
              "b_value": "Property B market value, 2076", "b_tax": "Property B tax bill, 2076",
              "cpi_multiple": "Consumer prices, 2076 (2026 = 1.00)",
              "sell_stock": "Sell A and buy the index, 2045 inheritance, ten years later",
              "sell_treasury": "Sell A and buy Treasuries, 2045 inheritance, ten years later",
              "rent": "Keep A and rent it, 2045 inheritance, ten years later",
              "live": "Move into A, 2045 inheritance, ten years later"}
    d["bootstrap"] = {"rows": []}
    for k, vals in metrics.items():
        sv = sorted(vals)
        d["bootstrap"]["rows"].append({
            "key": k, "label": labels[k], "money": k != "cpi_multiple",
            "p05": percentile(sv, 0.05), "p25": percentile(sv, 0.25), "p50": percentile(sv, 0.50),
            "p75": percentile(sv, 0.75), "p95": percentile(sv, 0.95),
            "mean": sum(vals) / len(vals),
            "below_constant": sum(1 for v in vals if v < d["bootstrap"].get("constant_ref", {}).get(k, float("inf"))) if False else None})
    # how often each option wins across the 2,000 draws
    wins = {k: 0 for k, _ in OPTIONS}
    gaps = []
    for i in range(len(boot)):
        vals = {k: metrics[k][i] for k, _ in OPTIONS}
        best = max(vals, key=lambda k: vals[k])
        wins[best] += 1
        gaps.append(vals["sell_stock"] - max(vals["rent"], vals["live"]))
    d["bootstrap"]["wins"] = [{"case": k, "label": dict(OPTIONS)[k], "draws": wins[k],
                               "share": round(wins[k] / len(boot), 3)} for k, _ in OPTIONS]
    gs = sorted(gaps)
    d["bootstrap"]["gap"] = {"p05": r10(percentile(gs, 0.05)), "p50": r10(percentile(gs, 0.50)),
                             "p95": r10(percentile(gs, 0.95)), "neg_share": round(sum(1 for x in gaps if x < 0) / len(gaps), 3)}
    const_cpi, const_ga, const_gb, const_rs, const_rt = path_arrays(CONST_PATH)
    c_rm = cpi_at(const_cpi, END)
    c_at = taxable_series(base.IN["a_av_2026"], base.IN["a_value"], const_ga, const_cpi)
    c_bt = taxable_series(base.IN["b_av_2025"] * (1 + CAP), base.IN["b_value"], const_gb, const_cpi)
    const_vals = {"a_value": value_at(base.IN["a_value"], const_ga, END),
                  "a_value_real": value_at(base.IN["a_value"], const_ga, END) / c_rm,
                  "a_taxable": c_at[-1]["taxable"],
                  "a_tax": tax_a(c_at[-1]["taxable"], END - 1, const_cpi),
                  "b_value": value_at(base.IN["b_value"], const_gb, END),
                  "b_tax": tax_b(c_bt[-1]["taxable"], END - 1, const_cpi),
                  "cpi_multiple": c_rm}
    const_vals["a_tax_real"] = const_vals["a_tax"] / c_rm
    for k, _ in OPTIONS:
        const_vals[k] = run_path(k, 2045, CONST_PATH)["wealth"]
    d["bootstrap"]["constant"] = {k: (round(v, 3) if k == "cpi_multiple" else r10(v)) for k, v in const_vals.items()}
    for row in d["bootstrap"]["rows"]:
        ref = const_vals[row["key"]]
        vals = metrics[row["key"]]
        row["p_below_constant"] = round(sum(1 for v in vals if v < ref) / len(vals), 3)
        row["constant"] = round(ref, 3) if row["key"] == "cpi_multiple" else r10(ref)

    # --- 4d. the decision re-run on the 40 real ten-year stretches (inheritance in 2045)
    win_rows = []
    for w in WINDOWS:
        path = [BLOCK[y] for y in w]
        res = {k: run_path(k, 2045, path) for k, _ in OPTIONS}
        win_rows.append({"first": w[0], "last": w[-1],
                         "sell_stock": r10(res["sell_stock"]["wealth"]),
                         "sell_treasury": r10(res["sell_treasury"]["wealth"]),
                         "rent": r10(res["rent"]["wealth"]), "live": r10(res["live"]["wealth"]),
                         "winner": max(res, key=lambda k: res[k]["wealth"]),
                         "tax_first": r10(res["rent"]["tax_first"]),
                         "spread": r10(res["sell_stock"]["wealth"] - max(res["rent"]["wealth"], res["live"]["wealth"])),
                         "same_answers": 1 if res["sell_stock"]["wealth"] >= max(res["rent"]["wealth"], res["live"]["wealth"]) else 0})
    counts = {k: sum(1 for r in win_rows if r["winner"] == k) for k, _ in OPTIONS}
    const_res = {k: run_path(k, 2045, CONST_PATH) for k, _ in OPTIONS}
    d["decision"] = {
        "year": 2045, "n": len(win_rows),
        "constant": {k: r10(v["wealth"]) for k, v in const_res.items()},
        "windows": win_rows, "counts": counts,
        "sell_first_min": r10(min(r["sell_stock"] for r in win_rows)),
        "sell_first_max": r10(max(r["sell_stock"] for r in win_rows)),
        "gap_rent_min": r10(min(r["sell_stock"] - r["rent"] for r in win_rows)),
        "gap_rent_max": r10(max(r["sell_stock"] - r["rent"] for r in win_rows)),
        "gap_live_min": r10(min(r["sell_stock"] - r["live"] for r in win_rows)),
        "gap_live_max": r10(max(r["sell_stock"] - r["live"] for r in win_rows)),
        "wins": [{"case": k, "label": dict(OPTIONS)[k], "windows": counts[k]} for k, _ in OPTIONS],
        "windows_sale_ahead": sum(1 for r in win_rows if r["sell_stock"] >= max(r["rent"], r["live"])),
        "spread_min": r10(min(r["spread"] for r in win_rows)),
        "spread_max": r10(max(r["spread"] for r in win_rows)),
    }

    # reconciliation with the published edition: the constant case must equal model.run()
    recon = [{"option": k, "model": r10(base.run(k, 2045, base.A["g"])["wealth"]),
              "economy": r10(const_res[k]["wealth"]),
              "diff": r10(const_res[k]["wealth"] - base.run(k, 2045, base.A["g"])["wealth"])} for k, _ in OPTIONS]
    d["reconcile"] = recon
    d["reconcile_worst"] = max(abs(x["diff"]) for x in recon)
    assert d["reconcile_worst"] <= 10, f"constant case does not reconcile with scripts/model.py: {recon}"

    # --- 4e. adversarial paths: one rate held for every year of the horizon
    def adv(name, cpi_rate, house_rate, stock_rate, tsy_rate, note):
        path = [{"cpi": cpi_rate, "ga": house_rate, "gb": house_rate, "rs": stock_rate, "rt": tsy_rate}
                for _ in range(HORIZON + 10)]
        cpi, ga, gb, rs, rt = path_arrays(path)
        rm = cpi_at(cpi, END)
        at = taxable_series(base.IN["a_av_2026"], base.IN["a_value"], ga, cpi)
        res = {k: run_path(k, 2045, path, from_start=True) for k, _ in OPTIONS}
        return {"name": name, "note": note, "cpi": round(cpi_rate * 100, 2), "house": round(house_rate * 100, 2),
                "stock": round(stock_rate * 100, 2), "tsy": round(tsy_rate * 100, 2),
                "a_value": r10(value_at(base.IN["a_value"], ga, END)),
                "a_value_real": r10(value_at(base.IN["a_value"], ga, END) / rm),
                "a_taxable": r10(at[-1]["taxable"]),
                "a_tax": r10(tax_a(at[-1]["taxable"], END - 1, cpi)),
                "a_tax_if_cap_only": r10(base.a_base(END - 1) * base.A["rate_a"] + base.FIXED_A * rm),
                "cpi_multiple": round(rm, 2),
                "sell_stock": r10(res["sell_stock"]["wealth"]), "rent": r10(res["rent"]["wealth"]),
                "live": r10(res["live"]["wealth"]),
                "winner": max(res, key=lambda k: res[k]["wealth"]),
                "sell_gap": r10(res["sell_stock"]["wealth"] - max(res["rent"]["wealth"], res["live"]["wealth"]))}

    d["adversarial"] = [
        adv("Stagflation repeated", 0.07, 0.06, 0.05, 0.08, "Inflation, house prices and yields held at their 1977-1981 averages for the whole horizon."),
        adv("A lost decade for house prices", 0.025, 0.00, 0.07, 0.0488, "House prices flat every year from 2026 to 2075."),
        adv("Inflation above the 2% assessment cap", 0.06, 0.04, 0.07, 0.0488, "Costs and fixed charges rise 6% a year; the assessment cap holds at 2%."),
        adv("Deflation and falling house prices", -0.02, -0.05, -0.10, 0.01, "Prices fall every year, which tests the lesser-of rule and the 0% assessment factor."),
    ]

    # --- 4f. does the RTC 51 lesser-of rule ever bind? Two starting positions, three orders.
    #      Before a death the taxable value is far below market, so the rule needs a collapse.
    #      After a death the gap is closed, so any fall from the new base year value counts.
    def bind_threshold(taxable: float, market: float) -> float:
        return round(taxable / market - 1.0, 4)

    d["lesser_of"] = {
        "today": {"taxable": r10(base.IN["a_av_2026"]), "market": r10(base.IN["a_value"]),
                  "threshold": bind_threshold(base.IN["a_av_2026"], base.IN["a_value"])},
        "in_2045_no_reset": {"taxable": r10(base.a_base(2045)), "market": r10(base.a_value(2045, base.A["g"])),
                             "threshold": bind_threshold(base.a_base(2045), base.a_value(2045, base.A["g"]))},
        "just_after_inheriting": {"taxable": r10(base.a_value(2045, base.A["g"])),
                                  "market": r10(base.a_value(2045, base.A["g"])), "threshold": 0.0},
    }
    d["bind_cases"] = []
    for key, label, order in (
            ("crash_at_once", "2006-2011 crash immediately after the inheritance", list(range(2003, 2019))),
            ("crash_later", "2006-2011 crash four years after the inheritance", list(range(1999, 2015))),
            ("no_crash", "A recovering stretch (2010-2025), for comparison", list(range(2010, 2026)))):
        path = [BLOCK[y] for y in order]
        cpi, ga, gb, rs, rt = path_arrays(path)
        fmv = base.IN["a_value"]
        rows, factor_today, factor_reset = [], 1.0, 1.0
        for i, analog in enumerate(order):
            y = START + i
            if i:
                factor_today *= 1.0 + infl_factor(cpi.get(y, base.A["inflation"]))
                factor_reset *= 1.0 + infl_factor(cpi.get(y, base.A["inflation"]))
            market = value_at(base.IN["a_value"], ga, y)
            cap_today = base.IN["a_av_2026"] * factor_today
            cap_reset = fmv * factor_reset
            taxable_today = min(cap_today, market)
            taxable_reset = min(cap_reset, market)
            rows.append({"year": y, "analog": analog, "house": round(ga.get(y, 0.0) * 100, 2),
                         "market": r10(market),
                         "taxable_today": r10(taxable_today), "cap_only_today": r10(cap_today),
                         "tax_today": r10(tax_a(taxable_today, y, cpi)),
                         "tax_cap_only": r10(tax_a(cap_today, y, cpi)),
                         "taxable_reset": r10(taxable_reset), "cap_only_reset": r10(cap_reset),
                         "tax_reset": r10(tax_a(taxable_reset, y, cpi)),
                         "tax_reset_cap_only": r10(tax_a(cap_reset, y, cpi)),
                         "binds_today": taxable_today < cap_today - 0.5,
                         "binds_reset": taxable_reset < cap_reset - 0.5})
        d["bind_cases"].append({
            "key": key, "label": label, "rows": rows,
            "binds_today": sum(1 for r in rows if r["binds_today"]),
            "binds_reset": sum(1 for r in rows if r["binds_reset"]),
            "saved_today": r10(sum(r["tax_cap_only"] - r["tax_today"] for r in rows)),
            "saved_reset": r10(sum(r["tax_reset_cap_only"] - r["tax_reset"] for r in rows)),
            "market_low": r10(min(r["market"] for r in rows)),
            "first_analog": order[0], "last_analog": order[-1]})

    # --- 4g. inflation and the rules that do not keep up
    d["thresholds"] = [
        {"item": "Federal estate exclusion", "nominal_2026": 15_000_000, "indexed": "Yes, by law from 2026",
         "note": "Rises with the published inflation index; the 2027 amount is $15,480,000."},
        {"item": "Proposition 19 excluded amount", "nominal_2026": r10(base.V["prop19_amount"]),
         "indexed": "One year's house price change, every second February",
         "note": "Grows more slowly than house prices and not at all with consumer prices."},
        {"item": "Assessment cap", "nominal_2026": None, "indexed": "2% a year at most",
         "note": "A share of a taxable value, not an amount, so inflation cannot erode it."},
        {"item": "Home-sale exclusion", "nominal_2026": base.V["home_sale_exclusion_joint"], "indexed": "No",
         "note": "$500,000 fixed since 1997; it buys less each year and is worth nothing like $500,000 in 2045 dollars."},
        {"item": "State and local tax deduction cap", "nominal_2026": 10_000, "indexed": "No",
         "note": "Not modelled on this site; flagged FL-27. Fixed in nominal dollars."},
    ]
    return d


if __name__ == "__main__":
    m = build()
    (OUT / "economy.json").write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
    print("reconcile worst diff", m["reconcile_worst"])
    print("window winners", m["decision"]["counts"])
    print("bootstrap wins", [(w["case"], w["draws"]) for w in m["bootstrap"]["wins"]], "gap", m["bootstrap"]["gap"])
    print("lesser-of thresholds", m["lesser_of"])
    for c in m["bind_cases"]:
        print(c["key"], "binds today", c["binds_today"], "binds after reset", c["binds_reset"], "saved", c["saved_today"], c["saved_reset"])
    for r in m["bootstrap"]["rows"]:
        print(r["key"], "p05", round(r["p05"]), "p50", round(r["p50"]), "p95", round(r["p95"]),
              "constant", r["constant"], "below", r["p_below_constant"])

