#!/usr/bin/env python3
"""Deterministic cross-check model (official inputs only).

Run:  python plan/tools/model.py      -> writes plan/data/model.json and CSVs.
No third-party packages. Every dollar output is rounded to the nearest $10.

Inputs are of two kinds only:
  * owner-provided figures, already coarsened for privacy (never more precise here);
  * figures read on an official page during the review (see plan/data/sources.json).
Nothing else is assumed. Where an input would have to be invented (market rent of
Property A, maintenance, brokerage cost, the heir's tax bracket) the model does not
invent it: it solves for the break-even value instead.
"""
from __future__ import annotations
import csv, json, math
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"


def r10(x: float) -> int:
    return int(math.floor(x / 10 + 0.5) * 10)


# ---- owner-provided (not officially verifiable without identifying the parcel) ----
A = dict(market_2026=3_100_000, assessed_2026=550_000, bill=7_210, bill_assessed=540_000,
         water_month=(100, 150), elec_month=(-20, -10), insurance=1_500)
B = dict(market_2026=1_800_000, assessed_2025=110_000, bill=2_440, rent_month=7_150,
         rented_units=2, units=3, water_month=(330, 400), elec_month=(30, 70), insurance=1_500)

# ---- official figures ----
RATE_A_PARTS = [  # County A compilation of tax rates FY2025-26, dollars per $100 of value
    ("Constitutional 1% levy", 1.00000),
    ("County retirement levy", 0.03880),
    ("County library retirement levy", 0.00240),
    ("County hospital bond (2008)", 0.00520),
    ("County housing bond (2016)", 0.00560),
    ("Elementary school district bonds (3 issues)", 0.03350),
    ("High school district bonds (4 issues)", 0.04170),
    ("Community college district bonds (3 issues)", 0.03110),
    ("Open space district bond (2014)", 0.00140),
    ("Water district, State Water Project (land and improvements)", 0.00390),
]
RATE_A = round(sum(v for _, v in RATE_A_PARTS), 5) / 100
RATE_A_LOW = 0.01                                   # constitutional levy only
RATE_A_HIGH = A["bill"] / A["bill_assessed"]        # whole bill scales with value
RATE_B = 1.18162182 / 100                           # City B secured rate FY2026-27
PROP13 = 1.02
CAP_2025_27 = 1_044_586
HOE = 7_000
EXCL = {2026: 15_000_000, 2027: 15_480_000}
EXCL_HISTORY = [(2011, 5_000_000), (2012, 5_120_000), (2013, 5_250_000), (2014, 5_340_000),
                (2015, 5_430_000), (2016, 5_450_000), (2017, 5_490_000), (2018, 11_180_000),
                (2019, 11_400_000), (2020, 11_580_000), (2021, 11_700_000), (2022, 12_060_000),
                (2023, 12_920_000), (2024, 13_610_000), (2025, 13_990_000), (2026, 15_000_000),
                (2027, 15_480_000)]
ESTATE_RATE = 0.40
TRANSFER_TAX = 0.55 / 500
TREASURY = {"1y": 0.0456, "5y": 0.0481, "10y": 0.0498, "20y": 0.0539, "30y": 0.0535}   # 10 November 2026
TREASURY_DATE = "10 November 2026"
TOP_FED_RATE = 0.37
RENT_CPI_SHARE = 0.60
RENT_CAP_NOW = 0.016
INFL = 0.02                                         # FOMC longer-run goal
HPI = {"1975Q1": 41.65, "1996Q2": 200.89, "2006Q2": 643.96, "2016Q2": 553.43,
       "2025Q2": 966.27, "2026Q2": 974.97}


def cagr(a, b, n):
    return (b / a) ** (1 / n) - 1


G_LOW = round(cagr(HPI["2006Q2"], HPI["2026Q2"], 20), 4)     # FHFA California, last 20 years
G_HIGH = round(cagr(HPI["1996Q2"], HPI["2026Q2"], 30), 4)    # FHFA California, last 30 years
G_BASE = round((G_LOW + G_HIGH) / 2, 4)
G = {"low": G_LOW, "base": G_BASE, "high": G_HIGH}
R10Y = TREASURY["10y"]
HORIZON = 10
T_YEARS = (2040, 2045, 2050)
YEARS = list(range(2026, 2051))


def mid(p):
    return sum(p) / 2


FIXED_A = A["bill"] - RATE_A * A["bill_assessed"]
FIXED_B = B["bill"] - RATE_B * B["assessed_2025"]
UNIT3_2026 = B["rent_month"] / B["rented_units"]


def infl(x, year, base=2026):
    return x * (1 + INFL) ** (year - base)


def market(p, year, g):
    return p["market_2026"] * (1 + g) ** (year - 2026)


def fbyv_a(year):
    return A["assessed_2026"] * PROP13 ** (year - 2026)


def fbyv_b(year):
    return B["assessed_2025"] * PROP13 ** (year - 2025)


def cap(year, g):
    return CAP_2025_27 * (1 + g) ** (2 * max(0, (year - 2025) // 2))


def prop19_taxable(year, g):
    v, f = market(A, year, g), fbyv_a(year)
    return f + max(0.0, v - f - cap(year, g))


def fixed_a(year):
    return infl(FIXED_A, year, 2025)


def fixed_b(year):
    return infl(FIXED_B, year, 2025)


def tax_a_keep(year):
    return RATE_A * fbyv_a(year) + fixed_a(year)


def tax_a_live(year, g):
    return RATE_A * (prop19_taxable(year, g) - HOE) + fixed_a(year)


def tax_a_full(year, g, rate=RATE_A):
    if rate == RATE_A:
        return rate * market(A, year, g) + fixed_a(year)
    if rate == RATE_A_LOW:
        return rate * market(A, year, g) + infl(A["bill"] - rate * A["bill_assessed"], year, 2025)
    return rate * market(A, year, g)


def tax_b_keep(year):
    return RATE_B * fbyv_b(year) + fixed_b(year)


def tax_b_full(year, g):
    return RATE_B * market(B, year, g) + fixed_b(year)


def exclusion(year):
    return EXCL[year] if year in EXCL else EXCL[2027] * (1 + INFL) ** (year - 2027)


def a_costs(year):
    return dict(insurance=infl(A["insurance"], year), water=infl(mid(A["water_month"]) * 12, year),
                electricity=infl(mid(A["elec_month"]) * 12, year))


def b_costs(year):
    return dict(insurance=infl(B["insurance"], year), water=infl(mid(B["water_month"]) * 12, year),
                electricity=infl(mid(B["elec_month"]) * 12, year))


def b_rent(year):
    return B["rent_month"] * 12 * (1 + RENT_CPI_SHARE * INFL) ** (year - 2026)


def projection_a():
    out = []
    for y in YEARS:
        c = a_costs(y)
        keep = tax_a_keep(y)
        out.append(dict(
            year=y, market_low=r10(market(A, y, G_LOW)), market_base=r10(market(A, y, G_BASE)),
            market_high=r10(market(A, y, G_HIGH)), assessed_keep=r10(fbyv_a(y)), tax_keep=r10(keep),
            cap=r10(cap(y, G_BASE)), taxable_live=r10(prop19_taxable(y, G_BASE)),
            tax_live=r10(tax_a_live(y, G_BASE)), tax_full=r10(tax_a_full(y, G_BASE)),
            insurance=r10(c["insurance"]), water=r10(c["water"]), electricity=r10(c["electricity"]),
            total_keep=r10(keep + sum(c.values())), maintenance_index=r10(infl(1000, y))))
    return out


def projection_b():
    out = []
    for y in YEARS:
        c = b_costs(y)
        rent, keep, full = b_rent(y), tax_b_keep(y), tax_b_full(y, G_BASE)
        out.append(dict(
            year=y, market_low=r10(market(B, y, G_LOW)), market_base=r10(market(B, y, G_BASE)),
            market_high=r10(market(B, y, G_HIGH)), assessed_keep=r10(fbyv_b(y)), tax_keep=r10(keep),
            tax_full=r10(full), rent=r10(rent), insurance=r10(c["insurance"]), water=r10(c["water"]),
            electricity=r10(c["electricity"]), net_keep=r10(rent - keep - sum(c.values())),
            net_full=r10(rent - full - sum(c.values())), maintenance_index=r10(infl(1000, y))))
    return out


def fv(flows, r):
    n = len(flows)
    return sum(f * (1 + r) ** (n - 1 - k) for k, f in enumerate(flows))


def paths(T, g):
    v = market(A, T, g)
    tl0 = prop19_taxable(T, g)
    live_cost, unit3, rent_cost = [], [], []
    for k in range(HORIZON):
        y = T + k
        c = a_costs(y)
        live_cost.append(RATE_A * (tl0 * PROP13 ** k - HOE) + fixed_a(y) + sum(c.values()))
        unit3.append(infl(UNIT3_2026 * 12, T) * (1 + RENT_CPI_SHARE * INFL) ** k)
        rent_cost.append(RATE_A * v * PROP13 ** k + fixed_a(y) + c["insurance"])
    return v, live_cost, unit3, rent_cost


def wealth(T, g, r, t=0.0):
    """End-of-horizon wealth attributable to Property A under Sell and Live-in."""
    v, live_cost, unit3, _ = paths(T, g)
    ra = r * (1 - t)
    sell = v * (1 - TRANSFER_TAX) * (1 + ra) ** HORIZON
    live = v * (1 + g) ** HORIZON + fv([u * (1 - t) - c for u, c in zip(unit3, live_cost)], ra)
    return sell, live


def bisect(f, lo, hi):
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        return None
    for _ in range(80):
        m = (lo + hi) / 2
        fm = f(m)
        if flo * fm <= 0:
            hi = m
        else:
            lo, flo = m, fm
    return (lo + hi) / 2


def decision(T, g):
    v, live_cost, unit3, rent_cost = paths(T, g)
    s0, l0 = wealth(T, g, R10Y, 0.0)
    s1, l1 = wealth(T, g, R10Y, TOP_FED_RATE)
    r_star = bisect(lambda r: wealth(T, g, r)[1] - wealth(T, g, r)[0], 0.0, 0.25)
    t_star = bisect(lambda t: wealth(T, g, R10Y, t)[1] - wealth(T, g, R10Y, t)[0], 0.0, 0.60)
    ann = fv([12 * (1 + INFL) ** k for k in range(HORIZON)], R10Y)
    base_r = v * (1 + g) ** HORIZON - fv(rent_cost, R10Y)
    defl = (1 + INFL) ** (T - 2026)
    be_s, be_l = (s0 - base_r) / ann, (l0 - base_r) / ann
    return dict(
        T=T, g=g, value=r10(v), sale_net=r10(v * (1 - TRANSFER_TAX)), transfer_tax=r10(v * TRANSFER_TAX),
        tax_keep=r10(tax_a_keep(T)), tax_live=r10(tax_a_live(T, g)), tax_full=r10(tax_a_full(T, g)),
        tax_full_low=r10(tax_a_full(T, g, RATE_A_LOW)), tax_full_high=r10(tax_a_full(T, g, RATE_A_HIGH)),
        prop19_saving=r10(tax_a_full(T, g) - tax_a_live(T, g)),
        cost_live=r10(live_cost[0]), unit3=r10(unit3[0]), net_live=r10(unit3[0] - live_cost[0]),
        cost_rent=r10(rent_cost[0]), interest=r10(v * (1 - TRANSFER_TAX) * R10Y),
        sell_pre=r10(s0), live_pre=r10(l0), diff_pre=r10(l0 - s0),
        sell_post=r10(s1), live_post=r10(l1), diff_post=r10(l1 - s1),
        r_star=None if r_star is None else round(r_star * 100, 2),
        t_star=None if t_star is None else round(t_star * 100, 1),
        be_rent_vs_live=r10(be_l), be_rent_vs_live_2026=r10(be_l / defl),
        be_rent_vs_sell=r10(be_s), be_rent_vs_sell_2026=r10(be_s / defl),
        be_yield_vs_live=round(be_l * 12 / v * 100, 2), be_yield_vs_sell=round(be_s * 12 / v * 100, 2),
        one_pct_selling_cost=r10(v * 0.01))


def headroom():
    out = []
    for y in (2026, 2027, 2030, 2035, 2040, 2045, 2050):
        ex = exclusion(y)
        a, b = market(A, y, G_BASE), market(B, y, G_BASE)
        ah, bh = market(A, y, G_HIGH), market(B, y, G_HIGH)
        # The owner states Property B already belongs to the heir, so the estate holds Property A
        # and the money. The "with B" column is kept only as a contingency: the deed was not seen.
        out.append(dict(year=y, exclusion=r10(ex), a=r10(a), b=r10(b), room_a=r10(ex - a),
                        room_a_high=r10(ex - ah), room_a_two=r10(2 * ex - a),
                        room_ab=r10(ex - a - b), room_ab_high=r10(ex - ah - bh),
                        room_ab_two=r10(2 * ex - a - b)))
    return out


def cash_cases():
    out = []
    for cash in (2_000_000, 5_000_000, 10_000_000, 15_000_000, 20_000_000):
        gross = A["market_2026"] + cash                      # Property B is the heir's own (owner's statement)
        over = max(0, gross - EXCL[2026])
        over2 = max(0, gross - 2 * EXCL[2026])
        over_b = max(0, gross + B["market_2026"] - EXCL[2026])
        out.append(dict(cash=cash, gross=gross, over=over, tax=r10(over * ESTATE_RATE),
                        tax_two=r10(over2 * ESTATE_RATE), tax_if_b_in_estate=r10(over_b * ESTATE_RATE)))
    return out


# ---------------------------------------------------------------------------------------
# Uneven-path test ("black swan" check). No scenario is invented: the ten years after the
# inheritance are replayed along every ten-year stretch the official record contains.
#   HPI_Q2  - FHFA all-transactions house price index for California, second quarter
#   GS10_JUN - 10-year Treasury constant-maturity yield, June monthly average, percent
#   CPI_AVG - CPI-U, U.S. city average, all items, annual average
# All three were read on the publisher's site on 11 November 2026 (see sources.py).
# ---------------------------------------------------------------------------------------
HPI_Q2 = {1975: 42.79, 1976: 50.31, 1977: 63.02, 1978: 76.01, 1979: 88.68, 1980: 102.79, 1981: 112.83,
          1982: 107.26, 1983: 117.43, 1984: 120.06, 1985: 126.23, 1986: 134.74, 1987: 148.21, 1988: 169.63,
          1989: 205.79, 1990: 228.07, 1991: 226.97, 1992: 225.08, 1993: 217.24, 1994: 206.87, 1995: 201.49,
          1996: 200.89, 1997: 204.53, 1998: 221.56, 1999: 239.29, 2000: 267.83, 2001: 305.47, 2002: 335.73,
          2003: 373.71, 2004: 450.89, 2005: 569.94, 2006: 643.96, 2007: 622.92, 2008: 498.03, 2009: 420.20,
          2010: 407.91, 2011: 384.83, 2012: 381.57, 2013: 425.87, 2014: 484.00, 2015: 516.28, 2016: 553.43,
          2017: 590.29, 2018: 632.98, 2019: 651.64, 2020: 676.76, 2021: 761.06, 2022: 919.32, 2023: 905.46,
          2024: 945.84, 2025: 966.27, 2026: 974.97}
GS10_JUN = {1975: 7.86, 1976: 7.86, 1977: 7.28, 1978: 8.46, 1979: 8.91, 1980: 9.78, 1981: 13.47, 1982: 14.30,
            1983: 10.85, 1984: 13.56, 1985: 10.16, 1986: 7.80, 1987: 8.40, 1988: 8.92, 1989: 8.28, 1990: 8.48,
            1991: 8.28, 1992: 7.26, 1993: 5.96, 1994: 7.10, 1995: 6.17, 1996: 6.91, 1997: 6.49, 1998: 5.50,
            1999: 5.90, 2000: 6.10, 2001: 5.28, 2002: 4.93, 2003: 3.33, 2004: 4.73, 2005: 4.00, 2006: 5.11,
            2007: 5.10, 2008: 4.10, 2009: 3.72, 2010: 3.20, 2011: 3.00, 2012: 1.62, 2013: 2.30, 2014: 2.60,
            2015: 2.36, 2016: 1.64, 2017: 2.19, 2018: 2.91, 2019: 2.07, 2020: 0.73, 2021: 1.52, 2022: 3.14,
            2023: 3.75, 2024: 4.31, 2025: 4.38}
CPI_AVG = {1975: 53.817, 1976: 56.908, 1977: 60.608, 1978: 65.233, 1979: 72.575, 1980: 82.408, 1981: 90.925,
           1982: 96.500, 1983: 99.600, 1984: 103.883, 1985: 107.567, 1986: 109.608, 1987: 113.625,
           1988: 118.258, 1989: 123.967, 1990: 130.658, 1991: 136.192, 1992: 140.317, 1993: 144.458,
           1994: 148.225, 1995: 152.383, 1996: 156.850, 1997: 160.517, 1998: 163.008, 1999: 166.575,
           2000: 172.200, 2001: 177.067, 2002: 179.875, 2003: 183.958, 2004: 188.883, 2005: 195.292,
           2006: 201.592, 2007: 207.342, 2008: 215.303, 2009: 214.537, 2010: 218.056, 2011: 224.939,
           2012: 229.594, 2013: 232.957, 2014: 236.736, 2015: 237.017, 2016: 240.007, 2017: 245.120,
           2018: 251.107, 2019: 255.657, 2020: 258.811, 2021: 270.970, 2022: 292.655, 2023: 304.702,
           2024: 313.689, 2025: 321.943}
# Peaks and troughs of the quarterly index (same series), for the drawdown table.
HPI_DRAWDOWNS = [
    dict(peak="1990 Q3", peak_v=229.96, trough="1995 Q1", trough_v=199.59, regained="1998 Q4", years_down=4.5, years_to_regain=8.25),
    dict(peak="2006 Q3", peak_v=646.07, trough="2012 Q1", trough_v=380.93, regained="2019 Q2", years_down=5.5, years_to_regain=12.75),
]
REPLAY_T = 2045
WINDOWS = list(range(1975, 2016))          # 41 start years; the last window ends in 2025


def replay(s, T=REPLAY_T):
    """Ten years after an inheritance in year T, shaped like the ten years that began in year s."""
    v = market(A, T, G_BASE)
    y = GS10_JUN[s] / 100
    c = [CPI_AVG[s + k] / CPI_AVG[s] for k in range(HORIZON + 1)]            # price level, year k
    rentf = [1.0]
    for k in range(1, HORIZON + 1):
        rentf.append(rentf[-1] * (1 + RENT_CPI_SHARE * max(0.0, CPI_AVG[s + k] / CPI_AVG[s + k - 1] - 1)))
    house_end = v * HPI_Q2[s + HORIZON] / HPI_Q2[s]
    tl0 = prop19_taxable(T, G_BASE)
    cost0 = a_costs(T)
    live_flow, rent_cost = [], []
    for k in range(HORIZON):
        other = (fixed_a(T) + sum(cost0.values())) * c[k]
        live_cost = RATE_A * (tl0 * PROP13 ** k - HOE) + other              # assessed value capped at +2% a year
        unit3 = infl(UNIT3_2026 * 12, T) * rentf[k]
        live_flow.append(unit3 - live_cost)
        rent_cost.append(RATE_A * v * PROP13 ** k + (fixed_a(T) + cost0["insurance"]) * c[k])

    def sell_at(r):
        return v * (1 - TRANSFER_TAX) * (1 + r) ** HORIZON

    def live_at(r):
        return house_end + fv(live_flow, r)

    sell, live = sell_at(y), live_at(y)
    r_star = bisect(lambda r: live_at(r) - sell_at(r), -0.20, 0.40)
    ann = fv([12 * c[k] for k in range(HORIZON)], y)
    be_rent = (sell - (house_end - fv(rent_cost, y))) / ann                  # monthly rent, first-year dollars
    return dict(start=s, end=s + HORIZON,
                house_pct=round(cagr(HPI_Q2[s], HPI_Q2[s + HORIZON], HORIZON) * 100, 2),
                yield_pct=GS10_JUN[s], cpi_pct=round(cagr(CPI_AVG[s], CPI_AVG[s + HORIZON], HORIZON) * 100, 2),
                house_end=r10(house_end), sell=r10(sell), live=r10(live), diff=r10(live - sell),
                winner="Keep" if live > sell else "Sell",
                r_star=None if r_star is None else round(r_star * 100, 2),
                be_rent_yield=round(be_rent * 12 / v * 100, 2),
                sell_real_pct=round((sell / c[HORIZON] / v - 1) * 100, 1),
                live_real_pct=round((live / c[HORIZON] / v - 1) * 100, 1))


def history():
    rows = [replay(s) for s in WINDOWS]
    keep = [r for r in rows if r["winner"] == "Keep"]
    sell = [r for r in rows if r["winner"] == "Sell"]
    rs = sorted(r["r_star"] for r in rows)
    be = sorted(r["be_rent_yield"] for r in rows)
    eras = []
    for a, b, label in ((1975, 1981, ""),
                        (1982, 1989, ""),
                        (1990, 1996, ""),
                        (1997, 2002, ""),
                        (2003, 2008, ""),
                        (2009, 2015, "")):
        part = [r for r in rows if a <= r["start"] <= b]
        eras.append(dict(first=a, last=b, label=label, n=len(part),
                         keep=sum(1 for r in part if r["winner"] == "Keep"),
                         sell=sum(1 for r in part if r["winner"] == "Sell"),
                         house_lo=min(r["house_pct"] for r in part), house_hi=max(r["house_pct"] for r in part),
                         yield_lo=min(r["yield_pct"] for r in part), yield_hi=max(r["yield_pct"] for r in part),
                         cpi_lo=min(r["cpi_pct"] for r in part), cpi_hi=max(r["cpi_pct"] for r in part),
                         diff_lo=min(r["diff"] for r in part), diff_hi=max(r["diff"] for r in part)))
    bands = []
    for lo, hi in ((0, 4), (4, 6), (6, 8), (8, 20)):
        part = [r for r in rows if lo <= r["yield_pct"] < hi]
        bands.append(dict(lo=lo, hi=hi, n=len(part), sell=sum(1 for r in part if r["winner"] == "Sell"),
                          keep=sum(1 for r in part if r["winner"] == "Keep"),
                          diff_lo=min(r["diff"] for r in part), diff_hi=max(r["diff"] for r in part)))
    runup = []                                  # house-index change over the five years BEFORE the start year
    prior = {r["start"]: (HPI_Q2[r["start"]] / HPI_Q2[r["start"] - 5]) ** 0.2 - 1 for r in rows if r["start"] - 5 in HPI_Q2}
    for lo, hi in ((-1.0, 0.0), (0.0, 0.05), (0.05, 0.10), (0.10, 1.0)):
        part = [r for r in rows if r["start"] in prior and lo <= prior[r["start"]] < hi]
        runup.append(dict(lo=round(lo * 100), hi=round(hi * 100), n=len(part),
                          sell=sum(1 for r in part if r["winner"] == "Sell"),
                          keep=sum(1 for r in part if r["winner"] == "Keep"),
                          diff_lo=min(r["diff"] for r in part) if part else 0,
                          diff_hi=max(r["diff"] for r in part) if part else 0))
    decades = []
    for a in (1975, 1985, 1995, 2005, 2015):
        ys = [GS10_JUN[y] for y in range(a, a + 10)]
        decades.append(dict(first=a, last=a + 10, house_pct=round(cagr(HPI_Q2[a], HPI_Q2[a + 10], 10) * 100, 2),
                            cpi_pct=round(cagr(CPI_AVG[a], CPI_AVG[a + 10], 10) * 100, 2),
                            yield_avg=round(sum(ys) / 10, 2), yield_lo=min(ys), yield_hi=max(ys)))
    hp_changes = {y: HPI_Q2[y] / HPI_Q2[y - 1] - 1 for y in range(1976, 2027)}
    cpi_changes = {y: CPI_AVG[y] / CPI_AVG[y - 1] - 1 for y in range(1976, 2026)}
    worst_h, best_h = min(hp_changes, key=hp_changes.get), max(hp_changes, key=hp_changes.get)
    worst_c, best_c = min(cpi_changes, key=cpi_changes.get), max(cpi_changes, key=cpi_changes.get)
    dd = [dict(d, fall_pct=round((d["trough_v"] / d["peak_v"] - 1) * 100, 1),
               a_fall=r10(market(A, REPLAY_T, G_BASE) * (1 - d["trough_v"] / d["peak_v"]))) for d in HPI_DRAWDOWNS]
    now = dict(year=2026, runup_pct=round(((HPI_Q2[2026] / HPI_Q2[2021]) ** 0.2 - 1) * 100, 2), yield_pct=round(R10Y * 100, 2))
    return dict(
        T=REPLAY_T, value=r10(market(A, REPLAY_T, G_BASE)), now=now, rows=rows, n=len(rows), n_keep=len(keep), n_sell=len(sell),
        r_star_min=rs[0], r_star_median=rs[len(rs) // 2], r_star_max=rs[-1],
        be_min=be[0], be_median=be[len(be) // 2], be_max=be[-1],
        best_keep=max(rows, key=lambda r: r["diff"]), best_sell=min(rows, key=lambda r: r["diff"]),
        worst_sell_real=min(rows, key=lambda r: r["sell_real_pct"]), worst_live_real=min(rows, key=lambda r: r["live_real_pct"]),
        n_sell_real_loss=sum(1 for r in rows if r["sell_real_pct"] < 0),
        n_live_real_loss=sum(1 for r in rows if r["live_real_pct"] < 0),
        eras=eras, bands=bands, runup=runup, decades=decades, drawdowns=dd,
        extremes=dict(house_worst_year=worst_h, house_worst=round(hp_changes[worst_h] * 100, 1),
                      house_best_year=best_h, house_best=round(hp_changes[best_h] * 100, 1),
                      house_down_years=sum(1 for v in hp_changes.values() if v < 0), house_years=len(hp_changes),
                      cpi_worst_year=worst_c, cpi_worst=round(cpi_changes[worst_c] * 100, 1),
                      cpi_best_year=best_c, cpi_best=round(cpi_changes[best_c] * 100, 1),
                      cpi_over4_years=sum(1 for v in cpi_changes.values() if v > 0.04), cpi_years=len(cpi_changes),
                      yield_hi=max(GS10_JUN.values()), yield_hi_year=max(GS10_JUN, key=GS10_JUN.get),
                      yield_lo=min(GS10_JUN.values()), yield_lo_year=min(GS10_JUN, key=GS10_JUN.get)))


def main():
    dec = [decision(T, g) for T in T_YEARS for g in (G_LOW, G_BASE, G_HIGH)]
    ac, bc = a_costs(2026), b_costs(2026)
    today = dict(
        a_tax_2025=A["bill"], a_tax_keep=r10(tax_a_keep(2026)), a_ins=A["insurance"], a_water=r10(ac["water"]),
        a_elec=r10(ac["electricity"]), a_total=r10(tax_a_keep(2026) + sum(ac.values())),
        a_tax_live=r10(tax_a_live(2026, G_BASE)), a_taxable_live=r10(prop19_taxable(2026, G_BASE)),
        a_tax_full=r10(tax_a_full(2026, G_BASE)), a_tax_full_low=r10(tax_a_full(2026, G_BASE, RATE_A_LOW)),
        a_tax_full_high=r10(tax_a_full(2026, G_BASE, RATE_A_HIGH)),
        a_prop19_saving=r10(tax_a_full(2026, G_BASE) - tax_a_live(2026, G_BASE)),
        b_rent=r10(b_rent(2026)), b_tax_2025=B["bill"], b_tax_keep=r10(tax_b_keep(2026)), b_ins=B["insurance"],
        b_water=r10(bc["water"]), b_elec=r10(bc["electricity"]),
        b_net_keep=r10(b_rent(2026) - tax_b_keep(2026) - sum(bc.values())),
        b_tax_full=r10(tax_b_full(2026, G_BASE)),
        b_net_full=r10(b_rent(2026) - tax_b_full(2026, G_BASE) - sum(bc.values())),
        b_yield_keep=round((b_rent(2026) - tax_b_keep(2026) - sum(bc.values())) / B["market_2026"] * 100, 2),
        b_yield_full=round((b_rent(2026) - tax_b_full(2026, G_BASE) - sum(bc.values())) / B["market_2026"] * 100, 2),
        b_treasury_income=r10(B["market_2026"] * (1 - TRANSFER_TAX) * R10Y),
        unit3=r10(UNIT3_2026), unit3_year=r10(UNIT3_2026 * 12),
        room_a=EXCL[2026] - A["market_2026"], room_ab=EXCL[2026] - A["market_2026"] - B["market_2026"])
    hist = history()
    out = dict(
        generated_by="plan/tools/model.py",
        inputs=dict(A=A, B=B),
        rates=dict(parts=RATE_A_PARTS, a_pct=round(RATE_A * 100, 4), a_low_pct=1.0,
                   a_high_pct=round(RATE_A_HIGH * 100, 3), b_pct=round(RATE_B * 100, 8),
                   fixed_a=r10(FIXED_A), fixed_b=r10(FIXED_B),
                   b_implied_pct=round(B["bill"] / B["assessed_2025"] * 100, 2),
                   b_advalorem=r10(RATE_B * B["assessed_2025"])),
        assumptions=dict(g_low=G_LOW, g_base=G_BASE, g_high=G_HIGH, infl=INFL, r10y=R10Y,
                         top_fed=TOP_FED_RATE, rent_growth=round(RENT_CPI_SHARE * INFL, 4), treasury_date=TREASURY_DATE,
                         horizon=HORIZON, transfer_tax=TRANSFER_TAX, treasury=TREASURY),
        hpi=dict(index=HPI, since_1975=round(cagr(HPI["1975Q1"], HPI["2026Q2"], 51.25) * 100, 2),
                 y30=round(G_HIGH * 100, 2), y20=round(G_LOW * 100, 2),
                 y10=round(cagr(HPI["2016Q2"], HPI["2026Q2"], 10) * 100, 2),
                 y1=round(cagr(HPI["2025Q2"], HPI["2026Q2"], 1) * 100, 2)),
        exclusion_history=EXCL_HISTORY, today=today, projection_a=projection_a(),
        projection_b=projection_b(), decisions=dec, headroom=headroom(), cash_cases=cash_cases(), history=hist)
    DATA.mkdir(exist_ok=True)
    (DATA / "model.json").write_text(json.dumps(out, indent=1) + "\n")
    for name in ("projection_a", "projection_b", "decisions", "headroom", "cash_cases"):
        rows = out[name]
        with open(DATA / f"{name}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    return out


if __name__ == "__main__":
    o = main()
    print(f"model written: {len(o['projection_a'])} projection years, {len(o['decisions'])} decision cases")
