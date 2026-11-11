#!/usr/bin/env python3
"""Economic stress and black-swan module.

Why this file exists
  The main model runs one constant path (4% house growth, 2.5% inflation, 7% stocks, 4.88% Treasuries).
  Over a 50-year horizon that is not how the world behaves. This module replays the decision over the
  paths that actually occurred, taken from published official series, and over a set of parametric
  shocks. It answers one question: does the ranking of the four options survive conditions like the
  ones in the record?

Rules honoured here
  * Every annual input is a published official series, cited by id in assets/sources.json. Nothing is
    recalled from memory; the series are transcribed from the publisher's own CSV or page.
  * Every dollar figure written to the JSON is rounded to the nearest $10 (assessed values to $10,000,
    tax bills to $100, matching the main model's privacy rule).
  * No city, county, ZIP, address, parcel number or person appears here. Areas are Area A and Area B;
    properties are Property A and Property B.

Output: assets/data/stress.json and assets/data/stress_windows.csv, consumed by scripts/build.py.
"""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import model as M          # noqa: E402  (same-directory import; model.py is the main planning model)

OUT = ROOT / "assets" / "data"
r10 = M.r10
A, V, IN = M.A, M.V, M.IN

# ---------------------------------------------------------------------------------------------------
# Published annual series. Transcribed from the publisher's own file on 11 November 2026.
# ---------------------------------------------------------------------------------------------------
CPI = {1969: 36.683, 1970: 38.842, 1971: 40.483, 1972: 41.808, 1973: 44.425, 1974: 49.317,
       1975: 53.825, 1976: 56.933, 1977: 60.617, 1978: 65.242, 1979: 72.583, 1980: 82.383,
       1981: 90.933, 1982: 96.533, 1983: 99.583, 1984: 103.933, 1985: 107.600, 1986: 109.692,
       1987: 113.617, 1988: 118.275, 1989: 123.942, 1990: 130.658, 1991: 136.167, 1992: 140.308,
       1993: 144.475, 1994: 148.225, 1995: 152.383, 1996: 156.858, 1997: 160.525, 1998: 163.008,
       1999: 166.583, 2000: 172.192, 2001: 177.042, 2002: 179.867, 2003: 184.000, 2004: 188.908,
       2005: 195.267, 2006: 201.558, 2007: 207.344, 2008: 215.254, 2009: 214.565, 2010: 218.076,
       2011: 224.923, 2012: 229.586, 2013: 232.952, 2014: 236.715, 2015: 237.002, 2016: 240.005,
       2017: 245.121, 2018: 251.100, 2019: 255.653, 2020: 258.856, 2021: 270.973, 2022: 292.626,
       2023: 304.703, 2024: 313.698, 2025: 321.962}

GS10 = {1969: 6.67, 1970: 7.35, 1971: 6.16, 1972: 6.21, 1973: 6.84, 1974: 7.56, 1975: 7.99,
        1976: 7.61, 1977: 7.42, 1978: 8.41, 1979: 9.44, 1980: 11.46, 1981: 13.91, 1982: 13.00,
        1983: 11.11, 1984: 12.44, 1985: 10.62, 1986: 7.68, 1987: 8.38, 1988: 8.85, 1989: 8.50,
        1990: 8.55, 1991: 7.86, 1992: 7.01, 1993: 5.87, 1994: 7.08, 1995: 6.58, 1996: 6.44,
        1997: 6.35, 1998: 5.26, 1999: 5.64, 2000: 6.03, 2001: 5.02, 2002: 4.61, 2003: 4.02,
        2004: 4.27, 2005: 4.29, 2006: 4.79, 2007: 4.63, 2008: 3.67, 2009: 3.26, 2010: 3.21,
        2011: 2.79, 2012: 1.80, 2013: 2.35, 2014: 2.54, 2015: 2.14, 2016: 1.84, 2017: 2.33,
        2018: 2.91, 2019: 2.14, 2020: 0.89, 2021: 1.44, 2022: 2.95, 2023: 3.96, 2024: 4.21,
        2025: 4.29}

UNRATE = {1969: 3.5, 1970: 5.0, 1971: 6.0, 1972: 5.6, 1973: 4.9, 1974: 5.6, 1975: 8.5, 1976: 7.7,
          1977: 7.1, 1978: 6.1, 1979: 5.9, 1980: 7.2, 1981: 7.6, 1982: 9.7, 1983: 9.6, 1984: 7.5,
          1985: 7.2, 1986: 7.0, 1987: 6.2, 1988: 5.5, 1989: 5.3, 1990: 5.6, 1991: 6.9, 1992: 7.5,
          1993: 6.9, 1994: 6.1, 1995: 5.6, 1996: 5.4, 1997: 4.9, 1998: 4.5, 1999: 4.2, 2000: 4.0,
          2001: 4.7, 2002: 5.8, 2003: 6.0, 2004: 5.5, 2005: 5.1, 2006: 4.6, 2007: 4.6, 2008: 5.8,
          2009: 9.3, 2010: 9.6, 2011: 8.9, 2012: 8.1, 2013: 7.4, 2014: 6.2, 2015: 5.3, 2016: 4.9,
          2017: 4.4, 2018: 3.9, 2019: 3.7, 2020: 8.1, 2021: 5.4, 2022: 3.7, 2023: 3.6, 2024: 4.0,
          2025: 4.3}

# House price index, the metropolitan area that contains Property A (FRED series ATNHPIUS41940Q).
HPI_A = {1976: 21.45, 1977: 27.55, 1978: 31.66, 1979: 37.28, 1980: 45.37, 1981: 50.70,
         1982: 48.13, 1983: 51.93, 1984: 54.99, 1985: 59.28, 1986: 63.60, 1987: 69.32,
         1988: 82.23, 1989: 107.06, 1990: 110.67, 1991: 106.17, 1992: 104.84, 1993: 102.19,
         1994: 100.16, 1995: 101.39, 1996: 105.46, 1997: 117.15, 1998: 133.07, 1999: 148.53,
         2000: 188.44, 2001: 210.46, 2002: 211.62, 2003: 217.22, 2004: 240.22, 2005: 290.39,
         2006: 316.97, 2007: 310.21, 2008: 274.95, 2009: 241.08, 2010: 241.13, 2011: 235.92,
         2012: 242.71, 2013: 276.93, 2014: 309.95, 2015: 341.11, 2016: 368.23, 2017: 384.97,
         2018: 423.13, 2019: 418.45, 2020: 417.45, 2021: 443.11, 2022: 510.00, 2023: 528.30,
         2024: 556.29, 2025: 560.14}

# House price index, the metropolitan area that contains Property B (FRED series ATNHPIUS41884Q).
HPI_B = {1976: 21.86, 1977: 26.94, 1978: 30.36, 1979: 36.80, 1980: 44.20, 1981: 45.90,
         1982: 42.94, 1983: 49.22, 1984: 51.53, 1985: 55.86, 1986: 62.14, 1987: 72.73,
         1988: 89.70, 1989: 108.63, 1990: 112.32, 1991: 106.96, 1992: 105.10, 1993: 102.05,
         1994: 100.14, 1995: 100.48, 1996: 101.83, 1997: 109.85, 1998: 123.23, 1999: 140.02,
         2000: 172.85, 2001: 193.25, 2002: 201.92, 2003: 212.50, 2004: 240.23, 2005: 286.36,
         2006: 307.80, 2007: 304.73, 2008: 277.71, 2009: 253.68, 2010: 249.12, 2011: 240.84,
         2012: 247.39, 2013: 281.32, 2014: 318.17, 2015: 356.82, 2016: 388.88, 2017: 406.91,
         2018: 443.63, 2019: 441.80, 2020: 429.48, 2021: 434.92, 2022: 488.18, 2023: 487.00,
         2024: 506.77, 2025: 510.79}

# Nasdaq Composite, annual average of daily closes (FRED series NASDAQCOM). Price index only.
NASDAQ = {1995: 925.188, 1996: 1164.948, 1997: 1469.488, 1998: 1794.907, 1999: 2728.146,
          2000: 3783.673, 2001: 2034.996, 2002: 1539.731, 2003: 1646.811, 2004: 1986.345,
          2005: 2099.346, 2006: 2263.410, 2007: 2578.467, 2008: 2161.685, 2009: 1845.385,
          2010: 2349.894, 2011: 2677.441, 2012: 2965.559, 2013: 3541.292, 2014: 4375.103,
          2015: 4945.553, 2016: 4987.793, 2017: 6235.299, 2018: 7425.958, 2019: 7940.210,
          2020: 10201.521, 2021: 14371.662, 2022: 12231.349, 2023: 12970.276, 2024: 17247.449,
          2025: 20501.586, 2026: 24992.561}

# California statewide house price index (FRED series CASTHPI), used for the long-run check.
CASTHPI = {1975: 41.65, 1980: 100.00, 1985: 124.47, 1990: 227.30, 1995: 199.59, 2000: 260.81,
           2005: 538.37, 2006: 638.13, 2009: 440.32, 2010: 409.16, 2012: 380.93, 2015: 504.97,
           2020: 669.09, 2022: 866.74, 2024: 930.66, 2026: 974.97}

# Dividend yield assumed on the index fund when a price index is the return series (assumption, not fact).
DIV_ADD = 0.015

# Base-case continuation used when a historical window is shorter than the comparison period.
BASE = {"g": A["g"], "cpi": A["inflation"], "ty": V["treasury_10y"], "rs": A["stock_return"]}

YEARS = A["hold_years"]


def path_cpi(y0, n=YEARS, pad=True):
    out = []
    for t in range(n):
        y = y0 + t
        if y + 1 in CPI and y in CPI:
            out.append(CPI[y + 1] / CPI[y] - 1.0)
        elif pad:
            out.append(BASE["cpi"])
        else:
            break
    return out


def path_house(y0, n=YEARS, pad=True, series=HPI_A):
    out = []
    for t in range(n):
        y = y0 + t
        if y + 1 in series and y in series:
            out.append(series[y + 1] / series[y] - 1.0)
        elif pad:
            out.append(BASE["g"])
        else:
            break
    return out


def path_ty(y0, n=YEARS, pad=True):
    out = []
    for t in range(n):
        y = y0 + t
        if y in GS10:
            out.append(GS10[y] / 100.0)
        elif pad:
            out.append(BASE["ty"])
        else:
            break
    return out


def path_rs(y0, n=YEARS, pad=True):
    out = []
    for t in range(n):
        y = y0 + t
        if y + 1 in NASDAQ and y in NASDAQ:
            out.append(NASDAQ[y + 1] / NASDAQ[y] - 1.0 + DIV_ADD)
        elif pad:
            out.append(BASE["rs"])
        else:
            break
    return out


# ---------------------------------------------------------------------------------------------------
# Path engine. Same four options and the same tax treatment as scripts/model.py, but every year can
# differ. Cash flows are invested in the same index fund as the sale proceeds.
# ---------------------------------------------------------------------------------------------------
def run_path(option, p):
    gs, cpis, tys, rss = p["g"], p["cpi"], p["ty"], p["rs"]
    n = len(gs)
    fmv0 = p["fmv0"]
    base0 = p["base"]
    amt0 = p["amount"]
    rent_g = p.get("rent_growth", A["rent_growth"])
    city_g = p.get("city_rent_growth", M.RENT_CTRL)
    vac = p.get("vacancy", A["vacancy"])
    ins_mult = p.get("ins_mult", 1.0)
    elec = p.get("electricity", IN["a_electric"])
    maint_mult = p.get("maint_mult", 1.0)

    mval = [fmv0]
    for g in gs:
        mval.append(mval[-1] * (1.0 + g))
    cum = [1.0]
    for c in cpis:
        cum.append(cum[-1] * (1.0 + c))

    value = 0.0
    basis = 0.0
    flows = []
    tax_first = rent_first = 0.0
    if option in ("sell_stock", "sell_treasury"):
        start = fmv0 * (1.0 - M.SELL_COST)
        if option == "sell_treasury":
            value = start
            for t in range(n):
                value *= 1.0 + tys[t] * (1.0 - A["t_treasury"])
            return {"wealth": value, "asset": value, "flows": 0.0, "tax_first": 0.0, "rent_first": 0.0}
        value = basis = start

    dep = A["building_share_a"] * fmv0 / V["depreciation_years"]
    assessed = (base0 + max(0.0, fmv0 - base0 - amt0)) if option == "live" else fmv0
    for t in range(n):
        y = p["y0"] + t
        # Proposition 13 cap: the factored base year value, capped at 2% and at market value (RTC 51).
        cap = 1.0 + min(V["prop13_cap"], cpis[t])
        assessed = min(assessed * cap, mval[t + 1])
        ptax = assessed * A["rate_a"] + p["fixed_a"] * cum[t + 1]
        ins = IN["a_ins_guess"] * ins_mult * cum[t + 1]
        maint = A["maint_a"] * maint_mult * cum[t + 1]
        water = IN["a_water"] * cum[t + 1]
        if option == "live":
            unit3 = (A["unit3_rent_mo"] * 12 * (1 + rent_g) ** (y - 2026))
            a = 1.0
            for tt in range(t):
                a *= 1.0 + min(city_g, max(cpis[tt], 0.0) + 0.05)  # City B local cap, formula basis
            income = unit3 * a * (1 - vac) * (1 - A["t_ord"])
            cf = income - (ptax + ins + maint + water + elec * cum[t + 1])
        else:
            rent0 = A["rent_a_mo"] * 12 * (1 + rent_g) ** (y - 2026)
            rent = rent0 * (1 - vac)
            if t == 0:
                rent_first = rent
            noi = rent - ptax - ins - maint
            cf = noi - A["t_ord"] * (noi - dep)
        if t == 0:
            tax_first = ptax
        flows.append(cf)
        # cash flow added to the index fund at year end
        value += cf
        basis += max(cf, 0.0)
        d = value * A["stock_dividend"]
        dtax = d * A["t_div"]
        value = value * (1.0 + rss[t]) - dtax
        basis += d - dtax
    port = value - max(0.0, value - basis) * M.T_GAIN
    if option == "sell_stock":
        return {"wealth": port, "asset": port, "flows": 0.0, "tax_first": 0.0, "rent_first": 0.0}
    net_sale = mval[n] * (1.0 - M.SELL_COST)
    if option == "live":
        gain_tax = M.T_GAIN * max(0.0, net_sale - fmv0 - V["home_sale_exclusion_joint"])
    else:
        gain_tax = M.T_RECAP * dep * n + M.T_GAIN * max(0.0, net_sale - fmv0)
    asset = net_sale - gain_tax
    return {"wealth": asset + port, "asset": asset, "flows": sum(flows), "tax_first": tax_first,
            "rent_first": rent_first}


OPTIONS = [("sell_stock", "Sell and buy an index fund"), ("sell_treasury", "Sell and buy Treasuries"),
           ("rent", "Keep and rent it out"), ("live", "Move in")]
SHORT = {"sell_stock": "Sell, index fund", "sell_treasury": "Sell, Treasuries", "rent": "Rent out", "live": "Move in"}


def base_path(y0=2045, g=None):
    """Starting point for a stress: the base-case value at the inheritance year, then the given path."""
    g = A["g"] if g is None else g
    return {"y0": y0, "fmv0": M.a_value(y0, g), "base": M.a_base(y0), "amount": M.prop19_amount(y0, g),
            "fixed_a": M.FIXED_A}


def evaluate(p, label, kind, note, sources, stock_note=""):
    rows = []
    res = {k: run_path(k, p) for k, _ in OPTIONS}
    best = max(r["wealth"] for r in res.values())
    cpi_cum = 1.0
    for c in p["cpi"]:
        cpi_cum *= 1.0 + c
    for k, name in OPTIONS:
        rows.append({"option": k, "name": name, "wealth": r10(res[k]["wealth"]),
                     "real": r10(res[k]["wealth"] / cpi_cum),
                     "gap": r10(res[k]["wealth"] - best),
                     "tax_first": r10(res[k]["tax_first"]), "rent_first": r10(res[k]["rent_first"])})
    rows.sort(key=lambda r: -r["wealth"])
    return {"label": label, "kind": kind, "note": note, "sources": sources, "stock_note": stock_note,
            "rows": rows, "winner": rows[0]["option"], "winner_name": rows[0]["name"],
            "gap_rent": r10(res["rent"]["wealth"] - res["sell_stock"]["wealth"]),
            "gap_live": r10(res["live"]["wealth"] - res["sell_stock"]["wealth"]),
            "avg_cpi": round(100 * (cpi_cum ** (1.0 / len(p["cpi"])) - 1.0), 1)}


# ---------------------------------------------------------------------------------------------------
# 1. Historical replays: the ten years that followed each named episode, replayed on the decision.
# ---------------------------------------------------------------------------------------------------
EPISODES = [
    ("h1973", "Inflation shock and the Volcker tightening", 1973,
     "Consumer prices rose 8.4% in 1974 and 9.1% in 1975; the 10-year Treasury averaged 13.9% in 1981. "
     "Housing still rose: the local index tripled over the ten years.", "fred_cpi", 1973),
    ("h1989", "The early-1990s California housing recession", 1989,
     "The local index fell for five years from 1990 (110.67) to 1995 (100.16) and was still below its "
     "1990 level in 1999. A house bought near the 1989 peak lost ground for a decade.", "fred_hpi_a", 1989),
    ("h1999", "The dot-com collapse", 1999,
     "The Nasdaq index average fell from 3,783.67 in 2000 to 1,539.73 in 2002, then to 1,845.39 in 2009. "
     "Local house prices kept rising through it.", "fred_nasdaq", 1999),
    ("h2005", "The global financial crisis", 2005,
     "The local index fell from 316.97 in 2006 to 235.92 in 2011, a 26% decline, and did not regain the "
     "2006 level until 2014. Unemployment reached 9.6%.", "fred_hpi_a", 2005),
    ("h2009", "A decade of zero rates after the crisis", 2009,
     "The 10-year Treasury averaged 1.8% in 2012 and 0.89% in 2020. Cash and bonds paid almost nothing "
     "for a decade while house prices recovered.", "fred_gs10", 2009),
    ("h2016", "The 2021-2023 inflation shock and the rate rise", 2016,
     "Consumer prices rose 8.0% in 2022 and the 10-year Treasury went from 1.44% (2021) to 4.29% (2025). "
     "The local index, after a 31% rise in 2021-2022, was flat to slightly down by 2025.", "fred_cpi", 2016),
]


def historical_replays():
    out = []
    for eid, name, y0, note, src, _ in EPISODES:
        p = base_path()
        p["g"] = path_house(y0)
        p["cpi"] = path_cpi(y0)
        p["ty"] = path_ty(y0)
        p["rs"] = path_rs(y0)
        stock_note = ("stock path: Nasdaq index (1995 onward)" if y0 >= 1995
                      else "stock path: held at the base-case 7% (no official long-run index return was read)")
        res = evaluate(p, f"{name}, {y0}-{y0 + YEARS - 1}", "episode", note, [src, "fred_cpi", "fred_gs10"],
                       stock_note)
        res["id"] = eid
        res["start"] = y0
        res["house_cagr"] = round(100 * ((1 + _prod(p["g"])) ** (1 / YEARS) - 1), 1)
        res["cpi_cagr"] = res["avg_cpi"]
        res["ty_avg"] = round(100 * sum(p["ty"]) / len(p["ty"]), 1)
        res["rs_cagr"] = round(100 * ((1 + _prod(p["rs"])) ** (1 / YEARS) - 1), 1)
        out.append(res)
    return out


def _prod(xs):
    v = 1.0
    for x in xs:
        v *= 1.0 + x
    return v - 1.0


def every_window():
    """Every ten-year window in the record that has house, price and rate data (1976-2015 starts)."""
    out = []
    for y0 in range(1976, 2016):
        p = base_path()
        p["g"] = path_house(y0)
        p["cpi"] = path_cpi(y0)
        p["ty"] = path_ty(y0)
        p["rs"] = path_rs(y0)
        res = {k: run_path(k, p)["wealth"] for k, _ in OPTIONS}
        best = max(res, key=res.get)
        out.append({"start": y0, "house": round(100 * ((1 + _prod(p["g"])) ** (1 / YEARS) - 1), 1),
                    "cpi": round(100 * ((1 + _prod(p["cpi"])) ** (1 / YEARS) - 1), 1),
                    "ty": round(100 * sum(p["ty"]) / len(p["ty"]), 1),
                    "rs": round(100 * ((1 + _prod(p["rs"])) ** (1 / YEARS) - 1), 1),
                    "sell": r10(res["sell_stock"]), "treasury": r10(res["sell_treasury"]),
                    "rent": r10(res["rent"]), "live": r10(res["live"]), "winner": SHORT[best]})
    return out


# ---------------------------------------------------------------------------------------------------
# 2. Parametric shocks. Each replaces one or more inputs for the ten years after a 2045 inheritance.
# ---------------------------------------------------------------------------------------------------
def flat(v, n=YEARS):
    return [v] * n


SHOCKS = [
    ("s_house_minus15", "House prices fall 15% in the first year, then 2% a year",
     {"g": [-0.15] + flat(0.02, YEARS - 1)}, "fred_hpi_a"),
    ("s_house_flat", "House prices do not move for ten years",
     {"g": flat(0.0)}, "fred_hpi_a"),
    ("s_house_boom", "House prices rise 8% a year",
     {"g": flat(0.08)}, "fred_hpi_a"),
    ("s_infl6", "Inflation runs at 6% a year and house prices keep up",
     {"cpi": flat(0.06), "g": flat(0.06)}, "fred_cpi"),
    ("s_stag", "Stagflation: 6% inflation, no house price growth, 2% on cash",
     {"cpi": flat(0.06), "g": flat(0.0), "ty": flat(0.02), "rs": flat(0.04)}, "fred_cpi"),
    ("s_zirp", "Zero-rate decade: Treasury at 2%, stocks at 4%",
     {"ty": flat(0.02), "rs": flat(0.04)}, "fred_gs10"),
    ("s_crash", "A 35% stock crash in the first year, then 8% a year",
     {"rs": [-0.35] + flat(0.08, YEARS - 1)}, "fred_nasdaq"),
    ("s_rent_squeeze", "Rent falls 10% and cannot keep up: 4% inflation, 0% rent growth, 12% vacancy",
     {"cpi": flat(0.04), "rent_growth": -0.01, "vacancy": 0.12, "maint_mult": 1.5}, "civ1947_12"),
    ("s_ins5", "Insurance costs five times the owner's placeholder",
     {"ins_mult": 5.0}, "cdi_compare"),
    ("s_solar_end", "The solar credit ends and electricity becomes a cost of $1,500 a year",
     {"electricity": 1_500.0}, "cpuc_nem"),
    ("s_both", "House prices fall 25% and stocks fall 20% in the first year",
     {"g": [-0.25] + flat(0.03, YEARS - 1), "rs": [-0.20] + flat(0.07, YEARS - 1)}, "fred_hpi_a"),
    ("s_def", "Deflation: prices fall 1% a year and house prices fall 2% a year",
     {"cpi": flat(-0.01), "g": flat(-0.02)}, "fred_cpi"),
]


def parametric_shocks():
    out = []
    for sid, name, override, src in SHOCKS:
        p = base_path()
        p["g"] = override.get("g", flat(A["g"]))
        p["cpi"] = override.get("cpi", flat(A["inflation"]))
        p["ty"] = override.get("ty", flat(V["treasury_10y"]))
        p["rs"] = override.get("rs", flat(A["stock_return"]))
        for k in ("rent_growth", "vacancy", "maint_mult", "ins_mult", "electricity"):
            if k in override:
                p[k] = override[k]
        srcs = list(dict.fromkeys([src, "fred_cpi", "civ1947_12" if "rent_growth" in override else src]))
        res = evaluate(p, name, "shock", "Scenario, not a forecast.", srcs, "")
        res["id"] = sid
        out.append(res)
    return out


# ---------------------------------------------------------------------------------------------------
# 3. Insurance: what an official source can and cannot establish.
# ---------------------------------------------------------------------------------------------------
INSURANCE = [
    ("What is published", "A 2026 homeowners premium comparison survey for California, by line of coverage",
     "The Department of Insurance surveys insurers and publishes the results as a comparison. The survey is not a quote and does not price a specific dwelling.",
     ["cdi_compare"]),
    ("Why no premium is shown", "No official premium exists for either property",
     "Nothing published by an official body prices Property A or Property B. The figures in the model are the owner's placeholders, carried at $1,500 for each property.",
     ["cdi_compare"]),
    ("If an insurer will not write the home", "The FAIR Plan is the residual market, with a residential limit of $3,000,000 per location",
     "Property A's estimated value is above that limit, so a FAIR Plan-only policy would not cover the whole house; the difference in conditions policy is bought separately. Property B's value is inside the limit.",
     ["cdi_fair"]),
    ("What the FAIR Plan covers", "A limited fire policy, not a comprehensive homeowners policy",
     "A comprehensive residential option is described by the Department as in progress. Until it exists, water damage, liability, theft and additional living expenses need a separate policy.",
     ["cdi_fair"]),
    ("Effect on the ranking", "None of the shocks tested changes which option is ahead",
     "At five times the placeholder, insurance is still small against the property tax reset and the lost investment return. The ranking is on the stress page.",
     ["cdi_compare"]),
]


# ---------------------------------------------------------------------------------------------------
# 4. Inherited cash and inherited retirement accounts: the income-tax side of an inheritance.
# ---------------------------------------------------------------------------------------------------
def inheritance_tax():
    """Income tax on what is inherited, as distinct from the estate tax."""
    y0 = 2045
    cash = M.a_value(y0, A["g"])
    out = {
        "note": ("An inheritance is not income to the recipient. The federal tax falls on the estate, above the "
                 "exclusion; California has neither an estate tax nor an inheritance tax. What can still be taxed "
                 "is the income the inherited assets produce, and - for retirement accounts - the forced "
                 "withdrawals."),
        "ira": [],
        "cash": [],
    }
    # A retirement account received by an adult child must be emptied within ten years (IRS).
    for principal in (500_000, 1_000_000, 2_000_000):
        yrs = 10
        # level annual withdrawals that empty the account, grossed up at the marginal rates used by the model
        rate = A["t_ord"] + 0.0
        gross = principal / yrs
        tax = gross * (A["t_ord"] + 0.093)  # federal 24% + California 9.3% (the model's 33.3% scenario rate)
        out["ira"].append({"principal": r10(principal), "years": yrs, "withdrawal": r10(gross),
                           "tax": r10(min(tax, gross * 0.5)), "net": r10(gross - min(tax, gross * 0.5)),
                           "tax_total": r10(min(tax, gross * 0.5) * yrs)})
    for amount in (1_000_000, 5_000_000, 10_000_000):
        out["cash"].append({"amount": r10(amount),
                            "note": "Not taxed on receipt; the income it produces is taxed as it arises."})
    # Headroom under the federal exclusion
    rows = []
    for yy in (2026, 2030, 2040, 2045, 2050):
        ex = V["fed_excl_2026"] if yy == 2026 else V["fed_excl_2027"] * (1 + A["fed_excl_index"]) ** (yy - 2027)
        homes = M.a_value(yy, A["g"]) + M.b_value(yy, A["g"])
        rows.append({"year": yy, "exclusion": r10(ex), "homes": r10(homes),
                     "room": r10(ex - homes),
                     "status": "Verified" if yy <= 2027 else "Scenario"})
    out["headroom"] = rows
    # What a lower exclusion would mean (hypothetical, quoted only as a scenario)
    hypo = []
    for level, label in ((7_000_000, "Half the 2026 amount"), (3_500_000, "A quarter of the 2026 amount")):
        for yy in (2045,):
            homes = M.a_value(yy, A["g"]) + M.b_value(yy, A["g"])
            hypo.append({"level": r10(level), "label": label, "year": yy, "homes": r10(homes),
                         "taxable": r10(max(0.0, homes - level)),
                         "tax": r10(max(0.0, homes - level) * 0.40)})
    out["hypo"] = hypo
    return out


# ---------------------------------------------------------------------------------------------------
# 5. Law watch: what is settled, what is pending, and what each would do to the numbers.
# ---------------------------------------------------------------------------------------------------
def law_watch():
    return [
        ("Statewide rent cap", "In force until 1 January 2030, then repealed by its own terms",
         "Civil Code 1947.12 limits increases to 5% plus the change in the cost of living, or 10%, whichever is lower.",
         "If it lapses, rent on a new tenancy is unconstrained; if it is extended, the 10-year horizon is covered.",
         ["civ1947_12"]),
        ("Local rent cap in City B", "1.6% for the year from 1 March 2026",
         "Set annually at 60% of the change in the regional consumer price index.", "Small.",
         ["cityb_rent"]),
        ("Proposed local limit on banked increases", "Not enacted",
         "The Board of Supervisors is considering File 261020, which would cap combined banked and capital-improvement increases at 10% a year. The city states it has not been enacted and may change.",
         "Would reduce the rent the building can recover after a period of no increases.", ["cityb_rent"]),
        ("Statewide tenancy bill", "Failed",
         "AB 1157 (2025-2026) would have amended the rent and just-cause statutes. It died on 31 January 2026.",
         "None.", ["ab1157"]),
        ("Local rent-control scope", "Unchanged since 1995",
         "Civil Code 1954.52 keeps local rent control off single-family homes and separately alienable units, and off housing first occupied after 1 February 1995. That is why a single-family home can be re-let at market rent while the older building cannot.",
         "Decides whether the rent option can ever reset to market.", ["civ1954_52"]),
        ("Solar compensation", "The current tariff pays export credits below the retail rate",
         "For systems interconnected from 15 April 2023 the net billing tariff applies, with a nine-year legacy period and export compensation that is usually below retail. Net surplus compensation at the annual true-up is about 2 to 3 cents a kilowatt-hour.",
         "The owner's reported credit is a retail-rate offset; it is worth less if the account changes tariff.", ["cpuc_nem"]),
        ("Property tax cap", "2% a year, and never more than market value",
         "The inflation factor cannot exceed 2%, and the taxable value is the lesser of the factored base year value and full cash value.",
         "In a falling market the assessed value must follow the market down.", ["rtc51", "boe_lta26002"]),
        ("Federal exclusion", "No scheduled cut",
         "The 2027 amount is $15,480,000; the 2026 amount is $15,000,000. The IRS release describes the underlying law as made permanent.",
         "Removes the 2026 sunset that earlier editions had to model as a risk.", ["irs_2027", "irs_estate"]),
        ("Statewide ballot, 3 November 2026", "Sixteen measures were on the ballot; outcomes are not reviewed here",
         "Among them, one measure would impose a one-time tax on certain taxpayers. Its text and its result are outside this review; see the Flagged for Review page.",
         "Unverified. Flagged.", ["sos_measures"]),
    ]


# ---------------------------------------------------------------------------------------------------
# 6. Cost-growth checks straight from published inflation data.
# ---------------------------------------------------------------------------------------------------
def cost_growth():
    return [
        ("All items, 12 months to September 2026", "3.7%", "Consumer price index, not seasonally adjusted",
         ["bls_cpi"]),
        ("Electricity, 12 months to September 2026", "4.4%", "Consumer price index, electricity",
         ["bls_cpi"]),
        ("Energy services, 12 months to September 2026", "4.6%", "Consumer price index, energy services",
         ["bls_cpi"]),
        ("Shelter, 12 months to September 2026", "3.2%", "Consumer price index, shelter", ["bls_cpi"]),
        ("Rent of primary residence, 12 months to September 2026", "2.8%",
         "Consumer price index, rent of primary residence", ["bls_cpi"]),
        ("Owners' equivalent rent, 12 months to September 2026", "3.3%",
         "Consumer price index, owners' equivalent rent", ["bls_cpi"]),
    ]


def build():
    d = {
        "generated_by": "scripts/stress.py",
        "method": ("Historical replays use published annual series transcribed from the publisher's own file. Where a "
                   "window has no official series for an input, the base-case assumption is used for that input and "
                   "the row says so. The stock series is a price index plus a 1.5% dividend add-on, so it understates "
                   "a total return and overstates a crash's severity measured by averaging."),
        "dividend_addon": DIV_ADD,
        "episodes": historical_replays(),
        "shocks": parametric_shocks(),
        "windows": every_window(),
        "insurance": [{"item": i, "finding": f, "detail": t, "src": s} for i, f, t, s in INSURANCE],
        "inheritance_tax": inheritance_tax(),
        "law_watch": [{"topic": t, "status": s, "detail": d_, "effect": e, "src": src}
                      for t, s, d_, e, src in law_watch()],
        "cost_growth": [{"item": i, "value": v, "detail": t, "src": s} for i, v, t, s in cost_growth()],
    }
    wins = {"sell_stock": 0, "sell_treasury": 0, "rent": 0, "live": 0}
    for w in d["windows"]:
        for k, n in SHORT.items():
            if n == w["winner"]:
                wins[k] += 1
    d["window_count"] = len(d["windows"])
    d["window_wins"] = wins
    d["windows_sell"] = wins["sell_stock"] + wins["sell_treasury"]
    d["shock_sell_wins"] = sum(1 for s in d["shocks"] if s["winner"] == "sell_stock")
    # worst and best decade in the record for each input
    d["extremes"] = {
        "house_worst": min(d["windows"], key=lambda w: w["house"]),
        "house_best": max(d["windows"], key=lambda w: w["house"]),
        "cpi_worst": max(d["windows"], key=lambda w: w["cpi"]),
        "ty_worst": max(d["windows"], key=lambda w: w["ty"]),
        "rs_worst": min(d["windows"], key=lambda w: w["rs"]),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "stress_windows.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(d["windows"][0].keys()))
        w.writeheader()
        w.writerows(d["windows"])
    (OUT / "stress.json").write_text(json.dumps(d, indent=1) + "\n", encoding="utf-8")
    return d


if __name__ == "__main__":
    m = build()
    print("windows", m["window_count"], "wins", m["window_wins"])
    for e in m["episodes"]:
        print(e["label"], "|", [(r["name"], r["wealth"]) for r in e["rows"]], "->", e["winner_name"])
    for s in m["shocks"]:
        print(s["label"][:48], "->", s["winner_name"], s["rows"][0]["wealth"], "vs sell", s["gap_rent"])
