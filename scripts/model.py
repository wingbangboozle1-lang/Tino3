#!/usr/bin/env python3
"""Planning model for the inherited-home decision (second, independently verified edition).

What this file guarantees
  * Every dollar figure written out is rounded to the nearest $10.
  * No name, address, ZIP code, parcel number or city name appears here.
  * Assessment-roll values and tax bills are public records that can be matched back to a parcel,
    so they enter this public model GENERALISED: assessed values to the nearest $10,000 and tax
    bills to the nearest $100. Nothing below can be matched to a roll entry.
  * Every assumption has an id, a value, a reason and an official reference (see ASSUMPTIONS).

Output: assets/data/model.json and three CSV files, consumed by scripts/build.py.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "data"


def r10(x: float) -> int:
    return int(round(float(x) / 10.0) * 10)


# ---------------------------------------------------------------------------------------------
# Owner-supplied inputs (not independently verified). Roll-derived values are generalised.
# ---------------------------------------------------------------------------------------------
IN = {
    "a_value": 3_100_000,     # owner estimate, November 2026
    "a_av_2026": 550_000,     # assessed value, generalised to the nearest $10,000
    "a_av_2025": 540_000,
    "a_bill_2025": 7_200,     # tax bill, generalised to the nearest $100
    "a_water": 1_500,         # $100-$150 a month; midpoint
    "a_electric": -180,       # solar: owner reports a $10-$20 monthly credit; midpoint
    "a_ins_guess": 1_500,     # owner's guess, no quote
    "b_value": 1_800_000,     # owner estimate, November 2026
    "b_av_2025": 110_000,     # assessed value, generalised to the nearest $10,000
    "b_bill_2025": 2_400,     # tax bill, generalised to the nearest $100
    "b_rent_mo": 7_150,       # two rented units, combined
    "b_water": 4_380,         # $330-$400 a month for the building; midpoint
    "b_electric": 600,        # $30-$70 a month; midpoint
    "b_ins_guess": 1_500,     # owner's guess, no quote
}

# ---------------------------------------------------------------------------------------------
# Verified figures (source ids refer to assets/sources.json)
# ---------------------------------------------------------------------------------------------
V = {
    "fed_excl_2026": 15_000_000,      # irs_estate
    "fed_excl_2027": 15_480_000,      # irs_2027
    "prop19_amount": 1_044_586,       # boe_lta25009 (shown rounded to $10)
    "prop13_cap": 0.02,               # boe_lta26002
    "rate_b_2026": 0.0118162182,      # cityb_rate   (fiscal year 2026-27)
    "rate_b_2025": 0.0118268325,      # cityb_res447 (fiscal year 2025-26)
    "rate_a_low": 0.011258, "rate_a_high": 0.012409,   # cnty_a_rates (range across tax rate areas)
    "county_transfer_tax": 0.0011,    # rtc11911
    "treasury_10y": 0.0488,           # treasury_cmt, 9 Nov 2026
    "rent_cap_share_of_cpi": 0.60,    # cityb_rent
    "depreciation_years": 27.5,       # irs_p527
    "fed_gain": 0.20, "fed_recapture": 0.25, "niit": 0.038, "ca_top": 0.123,  # irs_tc409, irs_tc559, ftb_rates
    "home_sale_exclusion_joint": 500_000, "home_sale_exclusion_single": 250_000,  # irs_tc701
}

# ---------------------------------------------------------------------------------------------
# Assumptions (scenario inputs, not facts). Each is shown on the site with its reason.
# ---------------------------------------------------------------------------------------------
A = {
    "g": 0.04, "g_low": 0.03, "g_high": 0.05,
    "inflation": 0.025,
    "rate_a": 0.0118,
    "stock_return": 0.07, "stock_dividend": 0.015,
    "rent_a_mo": 6_500, "rent_growth": 0.03,
    "vacancy": 0.05,
    "unit3_rent_mo": 3_580,
    "building_share_a": 0.30, "building_share_b": 0.40,
    "maint_a": 9_300, "maint_b": 10_800,
    "sale_cost": 0.05,
    "t_ord": 0.333, "t_div": 0.281, "t_treasury": 0.278,
    "fed_excl_index": 0.025,
    "hold_years": 10,
    "years": [2040, 2045, 2050],
}
T_GAIN = V["fed_gain"] + V["niit"] + V["ca_top"]            # 36.1%
T_RECAP = V["fed_recapture"] + V["niit"] + V["ca_top"]      # 41.1%
SELL_COST = A["sale_cost"] + V["county_transfer_tax"]       # 5.11%
RENT_CTRL = V["rent_cap_share_of_cpi"] * A["inflation"]      # 1.5%

# Fixed charges on each bill = bill minus (rate x assessed value); they do not scale with value.
FIXED_A = r10(IN["a_bill_2025"] - A["rate_a"] * IN["a_av_2025"])          # about $830
FIXED_B = r10(IN["b_bill_2025"] - V["rate_b_2025"] * IN["b_av_2025"])     # about $1,100

ASSUMPTIONS = [
    ("g", "House price growth, both properties", "3% / 4% / 5% a year", "Scenario band. The official index for each area rose 5.3% to 5.7% a year since 1995 but was flat to slightly down over the last four quarters, so the base case sits below the long-run rate.", ["fred_hpi_a", "fred_hpi_b"]),
    ("inflation", "General inflation, used for costs", "2.5% a year", "Scenario. The 2% assessment cap has been binding in every year since 2022 because the California CPI ran above 2%.", ["boe_lta26002"]),
    ("rate_a", "Ad valorem tax rate, Property A", "1.18%", "The owner's bill does not show the tax rate area, so the rate cannot be read off the county table. 1.18% sits inside the verified county range of 1.126% to 1.241%.", ["cnty_a_rates"]),
    ("fixed", "Fixed charges on each tax bill", "about $830 (A) and $1,100 (B) a year, rising with inflation", "The part of each bill that the percentage rate does not explain. Fixed charges do not grow when the assessed value is reset.", ["cnty_a_rates", "cityb_rate"]),
    ("cap_growth", "Growth of the Proposition 19 amount", "one year of house price growth, every second year", "Follows the adjustment rule as written: one year's index change, applied every other February.", ["boe_lta25009"]),
    ("stock_return", "Stock index fund, total return", "7.0% a year, of which 1.5% is dividends", "Scenario, not a forecast. One recent official 12-month figure for an S&P 500 index fund is 12.09%; a long-run official average could not be read in this session.", ["tsp_returns"]),
    ("treasury", "Treasury alternative", "4.88% a year", "The 10-year Treasury par yield on 9 November 2026, held constant.", ["treasury_cmt"]),
    ("rent_a", "Market rent, Property A", "$6,500 a month in 2026, rising 3% a year", "Scenario. No official rent figure for this home could be verified; see Flagged for Review. The break-even rent is reported so the conclusion does not rest on this number.", ["hud_fmr"]),
    ("vacancy", "Vacancy and turnover allowance", "5% of rent", "Scenario.", ["irs_p527"]),
    ("unit3", "Rent for the third unit of Property B when the family moves out", "$3,580 a month in 2026", "Set equal to the average of the two rented units. A new tenancy may start at any rent, then rises with the capped increase.", ["cityb_rent"]),
    ("rent_ctrl", "Rent growth for sitting tenants in Property B", "1.5% a year", "60% of the assumed 2.5% inflation, which is the published formula. The current allowed increase is 1.6%.", ["cityb_rent"]),
    ("building", "Share of value that is building, not land", "30% (A) and 40% (B)", "Scenario. Only the building is depreciated. The assessor's land and improvement split was not supplied.", ["irs_p527"]),
    ("maint", "Maintenance and repairs", "$9,300 a year (A) and $10,800 a year (B) in 2026, rising with inflation", "Scenario: 1.0% of building value for A and 1.5% for B. The owner states that A costs less to maintain than B.", ["irs_p527"]),
    ("sale_cost", "Cost of selling Property A", "5.11% of the price", "5.0% scenario allowance for agents, escrow, title and preparation, plus the verified 0.11% county transfer tax.", ["rtc11911", "cnty_a_recorder"]),
    ("t_ord", "Tax on rental income and on rental losses used", "33.3%", "Scenario household: 24% federal plus 9.3% California. Losses are assumed usable against Property B's rental income.", ["irs_p925", "ftb_rates"]),
    ("t_gain", "Tax on a large one-time gain", "36.1%", "20% federal, 3.8% net investment income tax and 12.3% California. Depreciation taken is taxed at 41.1%.", ["irs_tc409", "irs_tc559", "ftb_cg"]),
    ("t_div", "Tax on dividends and on Treasury interest", "28.1% and 27.8%", "15% + 3.8% + 9.3% on dividends. Treasury interest is assumed free of state tax: that exemption was not re-verified here.", ["irs_tc409", "irs_tc559"]),
    ("home_excl", "Home-sale exclusion if the family lives in A", "$500,000", "Joint return. It is $250,000 on a single return.", ["irs_tc701"]),
    ("fed_excl_index", "Federal estate exclusion after 2027", "2.5% a year", "Scenario. The amount is indexed by law; the future index is unknown.", ["irs_rp2532", "irs_2027"]),
    ("hold_years", "Comparison period", "10 years after the inheritance", "Every option is cashed out at the end and all taxes are paid, so the options are compared on the same footing.", ["irs_basis"]),
]


# ---------------------------------------------------------------------------------------------
# Historical paths, read from official FRED series (assets/sources.json gives each series).
# Levels only; the model derives annual changes. March of each year unless noted.
# ---------------------------------------------------------------------------------------------
HOUSE_IDX = [   # SFXRSA repeat-sales index, coastal metro proxy, Mar 2006 .. Mar 2016
    219.2946388516, 215.3193469719, 172.5664971958, 121.0882082123, 140.9317747859,
    133.6950846655, 129.2450510129, 157.1940784569, 189.5302794260, 208.2501219597,
    224.9857937857,
]
STOCK_IDX = [   # NASDAQCOM price index, Mar 2000 .. Mar 2010 (price only, no dividends)
    4802.988, 1986.663, 1863.046, 1349.500, 1979.614, 2030.434, 2300.256, 2401.491,
    2254.818, 1432.233, 2362.244,
]
CPI_IDX = [     # CPIAUCSL annual averages, 2006 .. 2016
    201.558, 207.344, 215.254, 214.565, 218.076, 224.923, 229.586, 232.952, 236.715,
    237.002, 240.005,
]


def _rates(levels):
    return [levels[i + 1] / levels[i] - 1.0 for i in range(len(levels) - 1)]


# Stress scenarios. Every non-baseline parameter is anchored to an official series recorded in
# assets/sources.json; the ids in "src" are shown with each row on the site.
SCENARIOS = [
    {"id": "baseline", "name": "Baseline",
     "note": "The plan's own assumptions: house prices 4% a year, stocks 7.0% a year including "
             "dividends, inflation 2.5%, and the 10-year Treasury at the verified 4.88% yield.",
     "params": "House 4%, stocks 7%, inflation 2.5%, Treasury 4.88%",
     "src": ["cbo_outlook26", "treasury_cmt"], "p": {}},
    {"id": "house_path", "name": "Housing lost decade (real path)",
     "note": "The actual year-by-year path of the coastal metro repeat-sales index from its "
             "March 2006 peak: 45.3% lower by May 2009 and only 2.6% higher ten years after the "
             "peak. Inflation at the actual 2006-16 average of 1.8% a year. Stocks at baseline.",
     "params": "Real 2006 housing path, inflation 1.8%",
     "src": ["fred_metro_hpi", "fred_cpi"], "p": {"g_path": _rates(HOUSE_IDX), "infl": 0.018}},
    {"id": "stock_path", "name": "Equity lost decade (real path)",
     "note": "The Nasdaq Composite price index replayed from its March 2000 peak: 50.8% lower "
             "ten years later. Price index only, so dividends are not added. House prices and "
             "inflation at baseline.",
     "params": "Real 2000 equity path, house 4%, inflation 2.5%",
     "src": ["fred_nasdaq"], "p": {"rs": _rates(STOCK_IDX)}},
    {"id": "stagflation", "name": "Stagflation (1973-82 style)",
     "note": "Inflation at the actual 1973-82 average of 9.0% a year, house prices 2% a year, "
             "stocks 4%, new rents rising 6% a year, and the 10-year Treasury at its 1981 "
             "average of 13.91%.",
     "params": "Inflation 9%, house 2%, stocks 4%, Treasury 13.91%",
     "src": ["fred_cpi", "fred_gs10"], "p": {"infl": 0.09, "g": 0.02, "rs": 0.04,
                                             "tsy": 0.1391, "rent_growth": 0.06}},
    {"id": "rate_shock", "name": "Rate shock (1981 style yields)",
     "note": "Only the interest-rate regime changes: the 10-year Treasury at its 1981 average "
             "of 13.91%, stocks 5%, inflation 4%, house prices 4%.",
     "params": "Treasury 13.91%, stocks 5%, inflation 4%, house 4%",
     "src": ["fred_gs10", "fred_mortgage"], "p": {"tsy": 0.1391, "rs": 0.05, "infl": 0.04,
                                                  "rent_growth": 0.04}},
    {"id": "insurance", "name": "Insurance shock",
     "note": "Insurance at three times the owner's guess for ten years, the case already tested "
             "on the decision page, against a regulator that describes a crisis of availability. "
             "Everything else at baseline.",
     "params": "Insurance 3x guess, otherwise baseline",
     "src": ["cdi_fair25", "cdi_compare"], "p": {"ins_mult": 3.0}},
    {"id": "combined", "name": "Combined stress (constructed)",
     "note": "The housing path, the equity path, 9.0% inflation and 13.91% Treasuries at the "
             "same time. Constructed: these shocks did not occur in the same decade.",
     "params": "Both real paths, inflation 9%, Treasury 13.91%",
     "src": ["fred_metro_hpi", "fred_nasdaq", "fred_cpi", "fred_gs10"],
     "p": {"g_path": _rates(HOUSE_IDX), "rs": _rates(STOCK_IDX), "infl": 0.09,
           "tsy": 0.1391, "rent_growth": 0.06}},
]

# ---------------------------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------------------------
def infl(year, base=2026):
    return (1 + A["inflation"]) ** (year - base)


def a_value(year, g):
    return IN["a_value"] * (1 + g) ** (year - 2026)


def b_value(year, g):
    return IN["b_value"] * (1 + g) ** (year - 2026)


def a_base(year):
    """Property A's assessed value if nothing changes: +2% a year."""
    return IN["a_av_2026"] * (1 + V["prop13_cap"]) ** (year - 2026)


def b_base(year):
    return IN["b_av_2025"] * (1 + V["prop13_cap"]) ** (year - 2025)


def prop19_amount(year, g):
    """One year's house price change, applied every second February from 2027."""
    n = 0 if year < 2027 else (year - 2027) // 2 + 1
    return V["prop19_amount"] * (1 + g) ** n


def tax_a(assessed, year, ir=None):
    """Ad valorem tax plus fixed charges. ir overrides the scenario inflation rate."""
    g = A["inflation"] if ir is None else ir
    return assessed * A["rate_a"] + FIXED_A * (1 + g) ** (year - 2026)


def tax_b(assessed, year):
    return assessed * V["rate_b_2026"] + FIXED_B * infl(year, 2025)


def stock_after_tax(p0, n, rs=None):
    """rs may be one annual rate or a sequence of n annual rates (a historical path).

    On a path the returns are used as total returns: no separate dividend is modelled,
    so the whole change is taxed once at the end.
    """
    seq = rs if isinstance(rs, (list, tuple)) else None
    p = basis = p0
    for i in range(n):
        r = A["stock_return"] if rs is None else (seq[i] if seq else rs)
        if seq is not None:
            p = p * (1 + r)
        else:
            div = p * A["stock_dividend"]
            tax = div * A["t_div"]
            p = p * (1 + r) - tax
            basis += div - tax
    return p - max(0.0, p - basis) * T_GAIN


def treasury_after_tax(p0, n, tsy=None):
    y = V["treasury_10y"] if tsy is None else tsy
    return p0 * (1 + y * (1 - A["t_treasury"])) ** n


def reassess(year, g, law="current"):
    """Assessed value of Property A in the year of inheritance under each use."""
    fmv, base, amt = a_value(year, g), a_base(year), prop19_amount(year, g)
    live = base + max(0.0, fmv - base - amt) if law == "current" else base
    rent = fmv if law == "current" else base
    return {"fmv": fmv, "base": base, "amount": amt, "live": live, "rent": rent}


def run(option, year, g, law="current", rs=None, rent_mo=None, ins_mult=1.0, n=None,
        infl=None, tsy=None, g_path=None, rent_growth=None):
    """Wealth from Property A and the third unit of Property B, n years after inheriting.

    Scenario overrides (all default to the base model): infl = annual inflation for costs and
    the rent-control formula; tsy = Treasury yield; g_path = house-price change for each year
    after the inheritance; rs = annual stock return or a path of them; rent_growth = annual
    rent growth. With no overrides the result is identical to the base model.
    """
    n = n or A["hold_years"]
    ir = A["inflation"] if infl is None else infl
    rc = V["rent_cap_share_of_cpi"] * ir
    rg = A["rent_growth"] if rent_growth is None else rent_growth
    rent_mo = A["rent_a_mo"] if rent_mo is None else rent_mo

    def IF(y):
        return (1 + ir) ** (y - 2026)

    rz = reassess(year, g, law)
    fmv = rz["fmv"]
    start = fmv * (1 - SELL_COST)
    stock_end = stock_after_tax(start, n, rs)
    r_eq = (stock_end / start) ** (1 / n) - 1          # after-tax return used for all cash flows
    flows = []
    if option == "sell_stock":
        return {"wealth": stock_end, "first_cash": 0.0, "cash_total": 0.0, "asset": stock_end, "tax_first": 0.0, "r_eq": r_eq}
    if option == "sell_treasury":
        w = treasury_after_tax(start, n, tsy)
        return {"wealth": w, "first_cash": 0.0, "cash_total": 0.0, "asset": w, "tax_first": 0.0, "r_eq": r_eq}
    dep = A["building_share_a"] * fmv / V["depreciation_years"]
    tax_first = rent_first = 0.0
    for t in range(n):
        y = year + t
        ins = IN["a_ins_guess"] * ins_mult * IF(y)
        maint = A["maint_a"] * IF(y)
        if option == "live":
            ptax = tax_a(rz["live"] * (1 + V["prop13_cap"]) ** t, y, ir)
            unit3 = (A["unit3_rent_mo"] * 12 * (1 + rg) ** (year - 2026)
                     * (1 + rc) ** t * (1 - A["vacancy"]) * (1 - A["t_ord"]))
            cf = unit3 - (ptax + ins + maint + IN["a_water"] * IF(y) + IN["a_electric"])
        else:
            ptax = tax_a(rz["rent"] * (1 + V["prop13_cap"]) ** t, y, ir)
            rent = rent_mo * 12 * (1 + rg) ** (y - 2026) * (1 - A["vacancy"])
            noi = rent - ptax - ins - maint
            cf = noi - A["t_ord"] * (noi - dep)
            if t == 0:
                rent_first = rent
        if t == 0:
            tax_first = ptax
        flows.append(cf)
    fv = sum(cf * (1 + r_eq) ** (n - 1 - t) for t, cf in enumerate(flows))
    if g_path is None:
        terminal = fmv * (1 + g) ** n
    else:
        terminal = fmv
        for rate in list(g_path)[:n]:
            terminal *= (1 + rate)
    net_sale = terminal * (1 - SELL_COST)
    if option == "live":
        gain_tax = T_GAIN * max(0.0, net_sale - fmv - V["home_sale_exclusion_joint"])
    else:
        d = dep * n
        gain_tax = T_RECAP * d + T_GAIN * max(0.0, net_sale - fmv)
    asset = net_sale - gain_tax
    return {"wealth": asset + fv, "first_cash": flows[0], "cash_total": sum(flows), "asset": asset,
            "tax_first": tax_first, "r_eq": r_eq, "rent_first": rent_first}


def bisect(f, lo, hi):
    for _ in range(70):
        mid = (lo + hi) / 2
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


OPTIONS = [("sell_stock", "Sell A, buy a stock index fund"), ("sell_treasury", "Sell A, buy Treasuries"),
           ("rent", "Keep A and rent it out"), ("live", "Move into A")]


def build():
    g = A["g"]
    n = A["hold_years"]
    d = {"inputs": {k: v for k, v in IN.items()}, "verified": {}, "fixed": {"a": FIXED_A, "b": FIXED_B},
         "rates": {"t_gain": T_GAIN, "t_recap": T_RECAP, "sell_cost": SELL_COST, "rent_ctrl": RENT_CTRL},
         "assumptions": [{"id": i, "item": a, "value": b, "reason": c, "src": s} for i, a, b, c, s in ASSUMPTIONS]}
    d["verified"] = {"prop19_amount": r10(V["prop19_amount"]), "fed_excl_2026": V["fed_excl_2026"],
                     "fed_excl_2027": V["fed_excl_2027"], "rate_b_2026": V["rate_b_2026"], "rate_b_2025": V["rate_b_2025"],
                     "rate_a_low": V["rate_a_low"], "rate_a_high": V["rate_a_high"], "treasury_10y": V["treasury_10y"]}

    # Year-by-year, nothing changes (no death, no sale): 2026-2060
    d["proj_a"], d["proj_b"] = [], []
    for y in range(2026, 2061):
        av = a_base(y)
        row = {"year": y, "value_low": r10(a_value(y, 0.03)), "value_base": r10(a_value(y, 0.04)),
               "value_high": r10(a_value(y, 0.05)), "assessed": r10(av), "property_tax": r10(tax_a(av, y)),
               "insurance": r10(IN["a_ins_guess"] * infl(y)), "water": r10(IN["a_water"] * infl(y)),
               "electricity": IN["a_electric"], "maintenance": r10(A["maint_a"] * infl(y))}
        row["total_cost"] = row["property_tax"] + row["insurance"] + row["water"] + row["electricity"] + row["maintenance"]
        d["proj_a"].append(row)
        bv = b_base(y)
        rent = IN["b_rent_mo"] * 12 * (1 + RENT_CTRL) ** (y - 2026)
        rb = {"year": y, "value_low": r10(b_value(y, 0.03)), "value_base": r10(b_value(y, 0.04)),
              "value_high": r10(b_value(y, 0.05)), "assessed": r10(bv), "property_tax": r10(tax_b(bv, y)),
              "rent": r10(rent), "vacancy": r10(rent * A["vacancy"]), "insurance": r10(IN["b_ins_guess"] * infl(y)),
              "water": r10(IN["b_water"] * infl(y)), "electricity": r10(IN["b_electric"] * infl(y)),
              "maintenance": r10(A["maint_b"] * infl(y))}
        rb["net_income"] = (rb["rent"] - rb["vacancy"] - rb["property_tax"] - rb["insurance"] - rb["water"]
                            - rb["electricity"] - rb["maintenance"])
        d["proj_b"].append(rb)

    # Property A after the inheritance: assessed value and tax, by use
    d["after"] = []
    for y0 in A["years"]:
        rz = reassess(y0, g)
        rows = []
        for t in range(n + 1):
            y = y0 + t
            f = (1 + V["prop13_cap"]) ** t
            rows.append({"year": y, "value": r10(a_value(y, g)),
                         "assessed_unchanged": r10(a_base(y)), "tax_unchanged": r10(tax_a(a_base(y), y)),
                         "assessed_live": r10(rz["live"] * f), "tax_live": r10(tax_a(rz["live"] * f, y)),
                         "assessed_rent": r10(rz["rent"] * f), "tax_rent": r10(tax_a(rz["rent"] * f, y))})
        d["after"].append({"year": y0, "fmv": r10(rz["fmv"]), "base": r10(rz["base"]), "amount": r10(rz["amount"]),
                           "live": r10(rz["live"]), "rent": r10(rz["rent"]),
                           "saving": r10(tax_a(rz["rent"], y0) - tax_a(rz["live"], y0)), "rows": rows})

    # Decision tables
    d["decision"] = []
    for y0 in A["years"]:
        for gg in (0.03, 0.04, 0.05):
            res = {k: run(k, y0, gg) for k, _ in OPTIONS}
            best = max(v["wealth"] for v in res.values())
            deflate = infl(y0 + n)
            rows = []
            for k, name in OPTIONS:
                v = res[k]
                rows.append({"option": k, "name": name, "wealth": r10(v["wealth"]), "wealth_today": r10(v["wealth"] / deflate),
                             "asset": r10(v["asset"]), "first_cash": r10(v["first_cash"]), "cash_total": r10(v["cash_total"]),
                             "tax_first": r10(v["tax_first"]), "rent_first": r10(v.get("rent_first", 0.0)), "gap": r10(v["wealth"] - best),
                             "gap_today": r10((v["wealth"] - best) / deflate)})
            live_cost = (max(res[k]["wealth"] for k in ("sell_stock", "sell_treasury", "rent")) - res["live"]["wealth"]) / (12 * n)
            d["decision"].append({"year": y0, "g": gg, "rows": rows, "start": r10(a_value(y0, gg) * (1 - SELL_COST)),
                                  "r_eq": round(res["live"]["r_eq"] * 100, 2),
                                  "live_cost_month": r10(live_cost), "live_cost_month_today": r10(live_cost / deflate)})

    # Sensitivities for the middle year
    y0 = 2045
    d["matrix"] = []
    for gg in (0.03, 0.04, 0.05, 0.06):
        for rs in (0.05, 0.06, 0.07, 0.08):
            w = {k: run(k, y0, gg, rs=rs)["wealth"] for k in ("sell_stock", "rent", "live")}
            best = max(w, key=w.get)
            d["matrix"].append({"g": gg, "rs": rs, "sell": r10(w["sell_stock"]), "rent": r10(w["rent"]), "live": r10(w["live"]),
                                "winner": {"sell_stock": "Sell", "rent": "Rent", "live": "Live"}[best]})
    base = {k: run(k, y0, g)["wealth"] for k, _ in OPTIONS}
    d["sens"] = []
    for label, kw in (("Rent for A is $5,000 a month, not $6,500", {"rent_mo": 5_000}),
                      ("Rent for A is $8,000 a month, not $6,500", {"rent_mo": 8_000}),
                      ("Insurance costs three times the owner's guess", {"ins_mult": 3.0}),
                      ("The pre-2021 exclusion is restored (proposal 25-0017)", {"law": "restored"})):
        w = {k: run(k, y0, g, **kw)["wealth"] for k, _ in OPTIONS}
        best = max(w, key=w.get)
        d["sens"].append({"case": label, "sell_stock": r10(w["sell_stock"]), "sell_treasury": r10(w["sell_treasury"]),
                          "rent": r10(w["rent"]), "live": r10(w["live"]), "rent_change": r10(w["rent"] - base["rent"]),
                          "live_change": r10(w["live"] - base["live"]), "winner": dict(OPTIONS)[best]})
    d["breakeven"] = {
        "stock_return": round(bisect(lambda r: run("sell_stock", y0, g, rs=r)["wealth"] - run("rent", y0, g, rs=r)["wealth"], 0.0, 0.2) * 100, 1),
        "house_growth": round(bisect(lambda x: run("rent", y0, x)["wealth"] - run("sell_stock", y0, x)["wealth"], 0.0, 0.2) * 100, 1),
        "house_growth_vs_treasury": round(bisect(lambda x: run("rent", y0, x)["wealth"] - run("sell_treasury", y0, x)["wealth"], 0.0, 0.2) * 100, 1),
        "rent_month": r10(bisect(lambda m: run("rent", y0, g, rent_mo=m)["wealth"] - base["sell_stock"], 1_000, 60_000)),
        "rent_month_vs_treasury": r10(bisect(lambda m: run("rent", y0, g, rent_mo=m)["wealth"] - base["sell_treasury"], 1_000, 60_000)),
    }
    rz = reassess(y0, g)
    restored = reassess(y0, g, "restored")
    d["law"] = {"year": y0, "tax_live_current": r10(tax_a(rz["live"], y0)), "tax_rent_current": r10(tax_a(rz["rent"], y0)),
                "tax_restored": r10(tax_a(restored["live"], y0))}

    # Black swan stress scenarios: each anchored to official series, run through the same model
    d["black_swan"] = []
    for sc in SCENARIOS:
        kw = {k: v for k, v in sc["p"].items() if k != "g"}
        res = {k: run(k, 2045, sc["p"].get("g", A["g"]), **kw) for k, _ in OPTIONS}
        best = max(v["wealth"] for v in res.values())
        rows = []
        for k, name in OPTIONS:
            v = res[k]
            rows.append({"option": k, "name": name, "wealth": r10(v["wealth"]),
                         "gap": r10(v["wealth"] - best), "first_cash": r10(v["first_cash"]),
                         "tax_first": r10(v["tax_first"])})
        winner = max(res, key=lambda k: res[k]["wealth"])
        d["black_swan"].append({"id": sc["id"], "name": sc["name"], "note": sc["note"],
                                "params": sc["params"], "src": sc["src"],
                                "winner_id": winner, "winner": dict(OPTIONS)[winner],
                                "rows": rows})

    # Property B if it passes in the same estate
    d["b_reset"] = []
    for yy in A["years"]:
        fmv = b_value(yy, g)
        keep, reset = tax_b(b_base(yy), yy), tax_b(fmv, yy)
        rent = IN["b_rent_mo"] * 12 * (1 + RENT_CTRL) ** (yy - 2026)
        costs = (IN["b_ins_guess"] + IN["b_water"] + IN["b_electric"] + A["maint_b"]) * infl(yy) + rent * A["vacancy"]
        d["b_reset"].append({"year": yy, "value": r10(fmv), "assessed_keep": r10(b_base(yy)), "tax_keep": r10(keep),
                             "tax_reset": r10(reset), "increase": r10(reset - keep), "rent": r10(rent),
                             "net_keep": r10(rent - costs - keep), "net_reset": r10(rent - costs - reset)})

    # Federal estate tax headroom
    d["estate"] = []
    for yy in (2026, 2027, 2030, 2035, 2040, 2045, 2050):
        ex = V["fed_excl_2026"] if yy == 2026 else V["fed_excl_2027"] * (1 + A["fed_excl_index"]) ** (yy - 2027)
        row = {"year": yy, "exclusion": r10(ex), "exclusion_couple": r10(2 * ex),
               "status": "Verified" if yy <= 2027 else "Scenario"}
        for tag, gg in (("low", 0.03), ("base", 0.04), ("high", 0.05)):
            re_ = a_value(yy, gg) + b_value(yy, gg)
            row[f"homes_{tag}"] = r10(re_)
            row[f"room_single_{tag}"] = r10(ex - re_)
            row[f"room_couple_{tag}"] = r10(2 * ex - re_)
        row["room_single_half"] = r10(ex / 2 - a_value(yy, g) - b_value(yy, g))
        d["estate"].append(row)

    # Current-year costs, side by side
    pa, pb = d["proj_a"][0], d["proj_b"][0]
    d["now"] = {"a": pa, "b": pb}

    OUT.mkdir(parents=True, exist_ok=True)

    def dump(name, rows):
        with (OUT / name).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    dump("property_a.csv", d["proj_a"])
    dump("property_b.csv", d["proj_b"])
    dump("decision.csv", [{"inheritance_year": b["year"], "house_growth": b["g"], **r} for b in d["decision"] for r in b["rows"]])
    (OUT / "model.json").write_text(json.dumps(d, indent=1) + "\n", encoding="utf-8")
    return d


if __name__ == "__main__":
    m = build()
    for b in m["decision"]:
        if b["g"] == 0.04:
            print(b["year"], [(r["option"], r["wealth"]) for r in b["rows"]], "live costs/month today", b["live_cost_month_today"])
    print("break-even", m["breakeven"], "fixed", m["fixed"])
