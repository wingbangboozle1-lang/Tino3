#!/usr/bin/env python3
"""Deterministic projection and decision model for the plan/ edition.

Inputs are the figures as published (already privacy-coarsened); nothing more
precise is stored anywhere in this repository. Every dollar output is rounded
to the nearest $10. Run:  python plan/tools/model.py
Writes plan/data/model.json and plan/data/*.csv. No third-party packages.
"""
from __future__ import annotations
import csv, json, math
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"


def r10(x: float) -> int:
    """Round half up to the nearest $10."""
    return int(math.floor(x / 10 + 0.5) * 10)


# ----------------------------------------------------------------------------
# 1. INPUTS
# ----------------------------------------------------------------------------
# Owner-provided (status: not officially verifiable without identifying the
# parcel). Assessed values are deliberately coarsened to the nearest $10,000.
A = dict(
    label="Property A", market_2026=3_100_000, assessed_2026=550_000,
    bill_year=2025, bill=7_210, bill_assessed=540_000,
    water_month=(100, 150), elec_month=(-20, -10), insurance=1_500,
)
B = dict(
    label="Property B", market_2026=1_800_000, assessed_2025=110_000,
    bill_year=2025, bill=2_440, bill_assessed=110_000,
    rent_month=7_150, rented_units=2, units=3,
    water_month=(330, 400), elec_month=(30, 70), insurance=1_500,
)

# Official figures (see plan/data/sources.json for where each was read).
RATE_A_PARTS = {  # Santa Clara County tax rate book FY2025-26, per $100
    "1% maximum levy": 1.00000, "County retirement levy": 0.03880,
    "County library retirement levy": 0.00240, "VMC 2008": 0.00520,
    "County housing bond 2016": 0.00560, "Cupertino Elementary 2001": 0.01650,
    "Cupertino Elementary 2012": 0.01690, "Cupertino Elem 2024": 0.00010,
    "Fremont Union High 2008": 0.00880, "Fremont Union High 2014": 0.01070,
    "Fremont Union High 2018": 0.01180, "Fremont High 2022": 0.01040,
    "Foothill-De Anza College 1999": 0.00750, "Foothill College 2006": 0.01010,
    "Foothill-De Anza CCD 2020": 0.01350, "Mid Peninsula Open Space 2014": 0.00140,
    "SCVWD State Water Project": 0.00390,
}
RATE_A = round(sum(RATE_A_PARTS.values()), 5) / 100      # 1.16360 per $100
RATE_B = 1.18162182 / 100                                # SF secured rate FY2026-27
PROP13_FACTOR = 1.02                                     # maximum annual factor
PROP19_CAP_2025_27 = 1_044_586                           # BOE LTA 2025/009
HOMEOWNERS_EXEMPTION = 7_000
EXCLUSION = {2026: 15_000_000, 2027: 15_480_000}         # IRS
ESTATE_TOP_RATE = 0.40
TRANSFER_TAX = 0.55 / 500                                # R&TC 11911
TREASURY_10Y = 0.0488                                    # 11/09/2026 par yield
SF_RENT_CPI_SHARE = 0.60                                 # SF Rent Board formula
FHFA_CA_HPI = {"1975Q1": 41.65, "1996Q2": 200.89, "2006Q2": 643.96,
               "2016Q2": 553.43, "2025Q2": 966.27, "2026Q2": 974.97}

# Assumptions (no official forecast exists; all flagged for review).
G = {"low": 0.020, "base": 0.035, "high": 0.050}         # home appreciation
INFL = 0.025                                             # general inflation
IDX = {"low": 0.020, "base": 0.025, "high": 0.030}       # exclusion indexing
R = {"treasury": TREASURY_10Y, "equity": 0.070}          # reinvestment return
SELL_COST = 0.05                                         # broker + closing
HORIZON = 10
T_YEARS = (2040, 2045, 2050)
YEARS = list(range(2026, 2051))


def mid(pair):
    return sum(pair) / 2


# Derived from the published inputs ------------------------------------------
FIXED_A = A["bill"] - RATE_A * A["bill_assessed"]        # non-ad-valorem residual
FIXED_B = B["bill"] - RATE_B * B["bill_assessed"]
UNIT3_RENT_2026 = B["rent_month"] / B["rented_units"]    # average of rented units


def market(p, year, g):
    return p["market_2026"] * (1 + g) ** (year - 2026)


def fbyv_a(year):
    return A["assessed_2026"] * PROP13_FACTOR ** (year - 2026)


def fbyv_b(year):
    return B["assessed_2025"] * PROP13_FACTOR ** (year - 2025)


def fixed(base, year, base_year=2025):
    return base * (1 + INFL) ** (year - base_year)


def cap(year, g):
    """Prop 19 $1 million amount: adjusted each odd-year Feb 16 by one year of CA HPI."""
    n = max(0, (year - 2025) // 2)
    return PROP19_CAP_2025_27 * (1 + g) ** n


def prop19_taxable(year, g):
    v, f, c = market(A, year, g), fbyv_a(year), cap(year, g)
    return f + max(0.0, v - f - c)


def tax_a_status_quo(year):
    return RATE_A * fbyv_a(year) + fixed(FIXED_A, year)


def tax_b_status_quo(year):
    return RATE_B * fbyv_b(year) + fixed(FIXED_B, year)


def infl(x, year, base_year=2026):
    return x * (1 + INFL) ** (year - base_year)


def exclusion(year, idx):
    if year in EXCLUSION:
        return EXCLUSION[year]
    return EXCLUSION[2027] * (1 + idx) ** (year - 2027)


def cagr(a, b, years):
    return (b / a) ** (1 / years) - 1


# ----------------------------------------------------------------------------
# 2. YEAR-BY-YEAR PROJECTIONS
# ----------------------------------------------------------------------------
def projection_a():
    rows = []
    for y in YEARS:
        g = G["base"]
        v = market(A, y, g)
        tl = prop19_taxable(y, g)
        rows.append(dict(
            year=y,
            market_low=r10(market(A, y, G["low"])), market_base=r10(v),
            market_high=r10(market(A, y, G["high"])),
            assessed_if_no_transfer=r10(fbyv_a(y)),
            tax_if_no_transfer=r10(tax_a_status_quo(y)),
            prop19_cap=r10(cap(y, g)),
            taxable_if_inherited_live_in=r10(tl),
            tax_if_inherited_live_in=r10(RATE_A * (tl - HOMEOWNERS_EXEMPTION) + fixed(FIXED_A, y)),
            taxable_if_inherited_not_lived_in=r10(v),
            tax_if_inherited_not_lived_in=r10(RATE_A * v + fixed(FIXED_A, y)),
        ))
    return rows


def projection_b():
    rows = []
    for y in YEARS:
        g = G["base"]
        v = market(B, y, g)
        rent = B["rent_month"] * 12 * (1 + SF_RENT_CPI_SHARE * INFL) ** (y - 2026)
        ins = infl(B["insurance"], y)
        water = infl(mid(B["water_month"]) * 12, y)
        elec = infl(mid(B["elec_month"]) * 12, y)
        tax = tax_b_status_quo(y)
        rows.append(dict(
            year=y,
            market_low=r10(market(B, y, G["low"])), market_base=r10(v),
            market_high=r10(market(B, y, G["high"])),
            assessed_if_no_transfer=r10(fbyv_b(y)),
            tax_if_no_transfer=r10(tax),
            tax_if_reassessed=r10(RATE_B * v + fixed(FIXED_B, y)),
            rent_two_units=r10(rent), insurance=r10(ins), water=r10(water),
            electricity=r10(elec),
            net_before_maintenance=r10(rent - tax - ins - water - elec),
        ))
    return rows


def costs_a():
    rows = []
    for y in YEARS:
        ins = infl(A["insurance"], y)
        water = infl(mid(A["water_month"]) * 12, y)
        elec = infl(mid(A["elec_month"]) * 12, y)
        tax = tax_a_status_quo(y)
        rows.append(dict(year=y, property_tax=r10(tax), insurance=r10(ins),
                         water=r10(water), electricity=r10(elec),
                         total_before_maintenance=r10(tax + ins + water + elec),
                         maintenance_per_1000_of_2026_spend=r10(infl(1000, y))))
    return rows


# ----------------------------------------------------------------------------
# 3. DECISION MODEL  (incremental to "keep living in Property B as today")
# ----------------------------------------------------------------------------
def fv(flows, r):
    """Future value at end of horizon of year-end flows reinvested at r."""
    n = len(flows)
    return sum(f * (1 + r) ** (n - 1 - k) for k, f in enumerate(flows))


def decision(T, g, r):
    v = market(A, T, g)
    # S: sell at date-of-death value, reinvest net proceeds
    net = v * (1 - SELL_COST - TRANSFER_TAX)
    w_s = net * (1 + r) ** HORIZON
    end_house = v * (1 + g) ** HORIZON
    # L: live in A, rent the freed unit in B
    taxable_l = prop19_taxable(T, g)
    cost_l, unit3, cost_r = [], [], []
    for k in range(HORIZON):
        y = T + k
        tax_l = RATE_A * (taxable_l * PROP13_FACTOR ** k - HOMEOWNERS_EXEMPTION) + fixed(FIXED_A, y)
        other = infl(A["insurance"], y) + infl(mid(A["water_month"]) * 12, y) + infl(mid(A["elec_month"]) * 12, y)
        cost_l.append(tax_l + other)
        unit3.append(infl(UNIT3_RENT_2026 * 12, T) * (1 + SF_RENT_CPI_SHARE * INFL) ** k)
        tax_r = RATE_A * v * PROP13_FACTOR ** k + fixed(FIXED_A, y)
        cost_r.append(tax_r + infl(A["insurance"], y))
    w_l = end_house + fv([u - c for u, c in zip(unit3, cost_l)], r)
    # R: rent out A. Rent is unknown, so solve for the break-even first-year rent
    # (growing with inflation) that makes R equal to S, and equal to L.
    annuity = fv([12 * (1 + INFL) ** k for k in range(HORIZON)], r)
    base_r = end_house - fv(cost_r, r)
    be_vs_s = (w_s - base_r) / annuity
    be_vs_l = (w_l - base_r) / annuity
    deflate = (1 + INFL) ** (T - 2026)
    return dict(
        T=T, g=g, r=r, value_at_T=r10(v), sale_net=r10(net),
        year1_tax_live_in=r10(RATE_A * (taxable_l - HOMEOWNERS_EXEMPTION) + fixed(FIXED_A, T)),
        year1_tax_rented=r10(RATE_A * v + fixed(FIXED_A, T)),
        year1_cost_live_in=r10(cost_l[0]), year1_unit3_rent=r10(unit3[0]),
        year1_income_if_sold=r10(net * r),
        wealth_sell=r10(w_s), wealth_live=r10(w_l), live_minus_sell=r10(w_l - w_s),
        breakeven_rent_vs_sell=r10(be_vs_s), breakeven_rent_vs_sell_2026usd=r10(be_vs_s / deflate),
        breakeven_rent_vs_live=r10(be_vs_l), breakeven_rent_vs_live_2026usd=r10(be_vs_l / deflate),
        breakeven_yield_vs_sell=round(be_vs_s * 12 / v * 100, 2),
        winner_live_vs_sell="Live in" if w_l > w_s else "Sell and reinvest",
    )


def decisions():
    return [decision(T, g, r) for T in T_YEARS for g in G.values() for r in R.values()]


# ----------------------------------------------------------------------------
# 4. ESTATE-TAX HEADROOM
# ----------------------------------------------------------------------------
def headroom():
    rows = []
    for y in (2026, 2027, 2030, 2035, 2040, 2045, 2050):
        ex = exclusion(y, IDX["base"])
        a, b = market(A, y, G["base"]), market(B, y, G["base"])
        ex_t = exclusion(y, IDX["low"])
        a_t, b_t = market(A, y, G["high"]), market(B, y, G["high"])
        rows.append(dict(
            year=y, exclusion_base=r10(ex), property_a=r10(a), property_b=r10(b),
            headroom_a_only=r10(ex - a), headroom_a_and_b=r10(ex - a - b),
            exclusion_tight=r10(ex_t), headroom_tight_a_only=r10(ex_t - a_t),
            headroom_tight_a_and_b=r10(ex_t - a_t - b_t),
        ))
    return rows


def main():
    hpi = FHFA_CA_HPI
    out = dict(
        generated_from="plan/tools/model.py",
        inputs=dict(A=A, B=B),
        rates=dict(rate_a_parts=RATE_A_PARTS, rate_a_pct=round(RATE_A * 100, 5),
                   rate_b_pct=round(RATE_B * 100, 8), fixed_a=r10(FIXED_A), fixed_b=r10(FIXED_B),
                   implied_rate_a_pct=round(A["bill"] / A["bill_assessed"] * 100, 2),
                   implied_rate_b_pct=round(B["bill"] / B["bill_assessed"] * 100, 2),
                   unit3_rent_2026=r10(UNIT3_RENT_2026)),
        assumptions=dict(G=G, INFL=INFL, IDX=IDX, R=R, SELL_COST=SELL_COST,
                         TRANSFER_TAX=TRANSFER_TAX, HORIZON=HORIZON),
        hpi_cagr=dict(
            since_1975=round(cagr(hpi["1975Q1"], hpi["2026Q2"], 51.25) * 100, 2),
            last_30y=round(cagr(hpi["1996Q2"], hpi["2026Q2"], 30) * 100, 2),
            last_20y=round(cagr(hpi["2006Q2"], hpi["2026Q2"], 20) * 100, 2),
            last_10y=round(cagr(hpi["2016Q2"], hpi["2026Q2"], 10) * 100, 2),
            last_1y=round(cagr(hpi["2025Q2"], hpi["2026Q2"], 1) * 100, 2)),
        exclusion_history_cagr=dict(
            y2011_2017=round(cagr(5_000_000, 5_490_000, 6) * 100, 2),
            y2018_2025=round(cagr(11_180_000, 13_990_000, 7) * 100, 2),
            y2026_2027=round(cagr(15_000_000, 15_480_000, 1) * 100, 2)),
        today=dict(
            a_tax=A["bill"], a_insurance=A["insurance"],
            a_water=r10(mid(A["water_month"]) * 12), a_elec=r10(mid(A["elec_month"]) * 12),
            a_total=r10(A["bill"] + A["insurance"] + mid(A["water_month"]) * 12 + mid(A["elec_month"]) * 12),
            b_rent=r10(B["rent_month"] * 12), b_tax=B["bill"], b_insurance=B["insurance"],
            b_water=r10(mid(B["water_month"]) * 12), b_elec=r10(mid(B["elec_month"]) * 12),
            b_net=r10(B["rent_month"] * 12 - B["bill"] - B["insurance"] - mid(B["water_month"]) * 12 - mid(B["elec_month"]) * 12),
            a_tax_if_reassessed_now=r10(RATE_A * A["market_2026"] + FIXED_A * (1 + INFL)),
            a_tax_if_prop19_now=r10(RATE_A * (prop19_taxable(2026, G["base"]) - HOMEOWNERS_EXEMPTION) + FIXED_A * (1 + INFL)),
            a_taxable_if_prop19_now=r10(prop19_taxable(2026, G["base"])),
            b_tax_if_reassessed_now=r10(RATE_B * B["market_2026"] + FIXED_B * (1 + INFL)),
            exclusion_2026=EXCLUSION[2026], exclusion_2027=EXCLUSION[2027],
            headroom_2026_a_only=EXCLUSION[2026] - A["market_2026"],
            headroom_2026_a_and_b=EXCLUSION[2026] - A["market_2026"] - B["market_2026"],
            prop19_cap=r10(PROP19_CAP_2025_27)),
        projection_a=projection_a(), projection_b=projection_b(), costs_a=costs_a(),
        decisions=decisions(), headroom=headroom(),
    )
    DATA.mkdir(exist_ok=True)
    (DATA / "model.json").write_text(json.dumps(out, indent=1) + "\n")
    for name in ("projection_a", "projection_b", "costs_a", "decisions", "headroom"):
        rows = out[name]
        with open(DATA / f"{name}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    return out


if __name__ == "__main__":
    o = main()
    print("model.json written;", len(o["decisions"]), "decision rows")
