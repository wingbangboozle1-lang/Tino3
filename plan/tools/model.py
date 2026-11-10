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
TREASURY = {"1y": 0.0438, "5y": 0.0467, "10y": 0.0488, "20y": 0.0529, "30y": 0.0526}
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
        out.append(dict(year=y, exclusion=r10(ex), a=r10(a), b=r10(b), room_a=r10(ex - a),
                        room_ab=r10(ex - a - b), room_ab_high=r10(ex - ah - bh),
                        room_ab_two=r10(2 * ex - a - b)))
    return out


def cash_cases():
    out = []
    for cash in (2_000_000, 5_000_000, 10_000_000, 15_000_000, 20_000_000):
        gross = A["market_2026"] + B["market_2026"] + cash
        over = max(0, gross - EXCL[2026])
        over2 = max(0, gross - 2 * EXCL[2026])
        out.append(dict(cash=cash, gross=gross, over=over, tax=r10(over * ESTATE_RATE),
                        tax_two=r10(over2 * ESTATE_RATE)))
    return out


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
    out = dict(
        generated_by="plan/tools/model.py",
        inputs=dict(A=A, B=B),
        rates=dict(parts=RATE_A_PARTS, a_pct=round(RATE_A * 100, 4), a_low_pct=1.0,
                   a_high_pct=round(RATE_A_HIGH * 100, 3), b_pct=round(RATE_B * 100, 8),
                   fixed_a=r10(FIXED_A), fixed_b=r10(FIXED_B),
                   b_implied_pct=round(B["bill"] / B["assessed_2025"] * 100, 2),
                   b_advalorem=r10(RATE_B * B["assessed_2025"])),
        assumptions=dict(g_low=G_LOW, g_base=G_BASE, g_high=G_HIGH, infl=INFL, r10y=R10Y,
                         top_fed=TOP_FED_RATE, rent_growth=round(RENT_CPI_SHARE * INFL, 4),
                         horizon=HORIZON, transfer_tax=TRANSFER_TAX, treasury=TREASURY),
        hpi=dict(index=HPI, since_1975=round(cagr(HPI["1975Q1"], HPI["2026Q2"], 51.25) * 100, 2),
                 y30=round(G_HIGH * 100, 2), y20=round(G_LOW * 100, 2),
                 y10=round(cagr(HPI["2016Q2"], HPI["2026Q2"], 10) * 100, 2),
                 y1=round(cagr(HPI["2025Q2"], HPI["2026Q2"], 1) * 100, 2)),
        exclusion_history=EXCL_HISTORY, today=today, projection_a=projection_a(),
        projection_b=projection_b(), decisions=dec, headroom=headroom(), cash_cases=cash_cases())
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
