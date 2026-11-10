"""Deterministic projection and decision model.

All money is computed in full precision and only rounded for display, always to
the nearest $10. Nothing in this file uses network access or private records.
Owner-supplied inputs are marked OWNER and are unverified; every rate that is
not OWNER comes from scripts/sources.py with a URL.
"""
from __future__ import annotations
import json
from pathlib import Path

from sources import V

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

# --------------------------------------------------------------------------
# 1. INPUTS
# --------------------------------------------------------------------------
OWNER = dict(
    a_value_2026=3_100_000,     # APPRAISAL SEARCH ESTIMATE, Nov 2026 - unverified
    a_assessed_2026=550_537,    # owner-supplied roll figure
    a_tax_2025=7_207,
    a_assessed_2025=539_743,
    b_value_2026=1_800_000,     # unverified estimate
    b_assessed_2025=114_248,
    b_tax_2025=2_439,
    b_rent_month=7_150,
    b_units=3,
    b_units_rented=2,
    a_water_month=125,          # midpoint of owner range $100-$150
    a_electric_month=-15,       # owner: solar credit, net negative cost
    b_water_month=365,          # midpoint of owner range $330-$400
    b_electric_month=50,        # midpoint of owner range $30-$70
    a_insurance_year=1_500,     # owner estimate
    b_insurance_year=1_500,     # owner estimate
)

# Scenario assumptions (labelled ASSUMPTION everywhere they are displayed).
ASSUMPTIONS = dict(
    g_market=0.030,          # property appreciation, base
    cpi=0.030,               # general inflation, base
    rent_growth=0.016,       # SF Rent Ordinance cap, TREASURY/SF-RENT derived
    equity=0.070,            # diversified equity total return, nominal
    treasury=V["treasury_10y"],
    a_maint_pct=0.0050,      # of market value per year
    b_maint_pct=0.0100,      # of market value per year
    a_building_share=0.40,   # depreciable share of property A (land is not depreciable)
    selling_cost=0.060,      # commission + closing + transfer costs
    vacancy=0.050,
    management=0.080,
    fed_ordinary=0.24,       # assumed marginal federal rate on net rent and Treasury interest
    ca_ordinary=0.093,       # FTB schedule, mid-bracket marginal
    insurance_growth=0.060,  # CDI-2026 ~6.9% recent filings, rounded down
    water_growth=0.060,      # between SFPUC's +7% water and +15% sewer near-term steps
    electric_growth=V["electricity_cpi"],
)

START, END = 2026, 2055
INHERIT_YEARS = (2040, 2045, 2050)
HORIZON = 20  # years of ownership evaluated after the inheritance year


def r10(x: float) -> int:
    """Round to the nearest $10 (the display rule for this project)."""
    return int(round(x / 10.0) * 10)


def grow(base: float, rate: float, years: int) -> float:
    return base * (1.0 + rate) ** years


# --------------------------------------------------------------------------
# 2. FLAT CHARGES RECONCILED AGAINST THE OWNER'S BILLS
# --------------------------------------------------------------------------
a_assessed_2025 = OWNER["a_assessed_2025"]
b_assessed_2025 = OWNER["b_assessed_2025"]
a_flat = OWNER["a_tax_2025"] - V["scc_advalorem"] * a_assessed_2025
b_flat = OWNER["b_tax_2025"] - V["sf_advalorem"] * b_assessed_2025

RECONCILE = {
    "a": dict(
        year=2025,
        assessed=a_assessed_2025,
        advalorem_rate=V["scc_advalorem"],
        advalorem_dollars=V["scc_advalorem"] * a_assessed_2025,
        observed_tax=OWNER["a_tax_2025"],
        residual=a_flat,
        observed_effective=OWNER["a_tax_2025"] / a_assessed_2025,
        official_element=0.0,
        official_element_note="No parcel-level official breakdown of the residual was retrieved.",
    ),
    "b": dict(
        year=2025,
        assessed=b_assessed_2025,
        advalorem_rate=V["sf_advalorem"],
        advalorem_dollars=V["sf_advalorem"] * b_assessed_2025,
        observed_tax=OWNER["b_tax_2025"],
        residual=b_flat,
        observed_effective=OWNER["b_tax_2025"] / b_assessed_2025,
        official_element=V["sf_parcel_2025"],
        official_element_note="Five named SF parcel taxes sum to $829.22 for a 3-unit building; "
                              "the observed residual is higher, so roughly $260 is unexplained (F-04).",
    ),
}
A_FLAT = a_flat
B_FLAT = b_flat

# --------------------------------------------------------------------------
# 3. YEAR-BY-YEAR PROPERTY PROJECTION (2026-2055, pre-decision)
# --------------------------------------------------------------------------
def project_property(market_2026, assessed_2026, flat_2026, advalorem, cpi, g, years):
    rows = []
    for y in years:
        n = y - START
        mv = grow(market_2026, g, n)
        av = grow(assessed_2026, V["prop13_cap"], n)
        av = min(av, mv)  # RTC-51: taxable value is the lesser of factored base or full cash value
        flat = grow(flat_2026, cpi, n)
        tax = advalorem * av + flat
        rows.append(dict(year=y, market=r10(mv), assessed=r10(av), flat_charge=r10(flat),
                         tax=r10(tax), effective_rate=tax / av))
    return rows


YEARS = list(range(START, END + 1))
proj_a = project_property(OWNER["a_value_2026"], OWNER["a_assessed_2026"], A_FLAT,
                          V["scc_advalorem"], ASSUMPTIONS["cpi"], ASSUMPTIONS["g_market"], YEARS)
proj_b = project_property(OWNER["b_value_2026"], grow(b_assessed_2025, 0.02, 1), B_FLAT,
                          V["sf_advalorem"], ASSUMPTIONS["cpi"], ASSUMPTIONS["g_market"], YEARS)

# --------------------------------------------------------------------------
# 4. ANNUAL OPERATING COST PROJECTION
# --------------------------------------------------------------------------
def operating_costs(years, kind):
    rows = []
    for y in years:
        n = y - START
        if kind == "a":
            g = ASSUMPTIONS["g_market"]
            mv = grow(OWNER["a_value_2026"], g, n)
            water = grow(OWNER["a_water_month"] * 12, ASSUMPTIONS["water_growth"], n)
            elec = grow(OWNER["a_electric_month"] * 12, ASSUMPTIONS["electric_growth"], n)
            ins = grow(OWNER["a_insurance_year"], ASSUMPTIONS["insurance_growth"], n)
            maint = mv * ASSUMPTIONS["a_maint_pct"]
        else:
            g = ASSUMPTIONS["g_market"]
            mv = grow(OWNER["b_value_2026"], g, n)
            water = grow(OWNER["b_water_month"] * 12, ASSUMPTIONS["water_growth"], n)
            elec = grow(OWNER["b_electric_month"] * 12, ASSUMPTIONS["electric_growth"], n)
            ins = grow(OWNER["b_insurance_year"], ASSUMPTIONS["insurance_growth"], n)
            maint = mv * ASSUMPTIONS["b_maint_pct"]
        rows.append(dict(year=y, market=r10(mv), insurance=r10(ins), water=r10(water),
                         electricity=r10(elec), maintenance=r10(maint),
                         total=r10(ins + water + elec + maint)))
    return rows


costs_a = operating_costs(YEARS, "a")
costs_b = operating_costs(YEARS, "b")

# --------------------------------------------------------------------------
# 5. DECISION MODEL
# --------------------------------------------------------------------------
def prop19_cap(year: int) -> float:
    """Biennial Prop 19 cap, indexed forward from the verified 2025-2027 amount.

    Indexing rate is an ASSUMPTION (the BOE indexes by FHFA's California HPI);
    the base amount is verified (BOE-CAP).
    """
    return grow(V["prop19_cap_2025"], ASSUMPTIONS["cpi"], max(0, year - 2026))


def tax_on(value_base: float, flat: float, advalorem: float, n: int) -> float:
    return advalorem * value_base + grow(flat, ASSUMPTIONS["cpi"], n)


def evaluate(option: str, T: int, *, rent_month: float | None = None,
             prop19: bool = False, g: float | None = None,
             invest: str = "treasury", cpi: float | None = None) -> dict:
    """After-tax position HORIZON years after the inheritance year T."""
    g = ASSUMPTIONS["g_market"] if g is None else g
    cpi = ASSUMPTIONS["cpi"] if cpi is None else cpi
    mv_T = grow(OWNER["a_value_2026"], g, T - START)
    cap_T = prop19_cap(T)
    base = max(mv_T - cap_T, 0.0) if prop19 else mv_T
    flat_T = grow(A_FLAT, cpi, T - START)

    cash = 0.0            # accumulated after-tax cash flow (net of taxes, before reinvestment)
    tax_paid = 0.0
    depr_total = 0.0
    rent_total = 0.0

    if option == "sell":
        proceeds = mv_T * (1 - ASSUMPTIONS["selling_cost"])
        gain = max(mv_T - mv_T, 0.0)            # step-up: basis = date-of-death FMV
        proceeds -= gain * 0.0
        if invest == "treasury":
            bal = proceeds
            for n in range(HORIZON):
                interest = bal * ASSUMPTIONS["treasury"]
                after = interest * (1 - ASSUMPTIONS["fed_ordinary"])  # CA exempts U.S. obligations (F-11)
                bal += after
            terminal = bal
        else:
            terminal = proceeds * (1 + ASSUMPTIONS["equity"]) ** HORIZON
            gain = terminal - proceeds
            terminal -= gain * (V["fed_ltcg_top"] + V["niit"] + ASSUMPTIONS["ca_ordinary"])
        return dict(option="sell_" + invest, T=T, terminal=terminal, cash=0.0,
                    tax_paid=0.0, cg_tax=0.0, mv_end=r10(grow(mv_T, g, HORIZON)),
                    base_T=r10(base), props=r10(proceeds), _proceeds_raw=proceeds)

    # live-in or rent: hold for the horizon, then sell.
    depreciation = (mv_T * ASSUMPTIONS["a_building_share"]) / V["depr_years"]
    for n in range(HORIZON):
        y = T + n
        mv = grow(mv_T, g, n)
        ptax = tax_on(base, flat_T, V["scc_advalorem"], n)
        ins = grow(OWNER["a_insurance_year"], ASSUMPTIONS["insurance_growth"], T - START + n)
        water = grow(OWNER["a_water_month"] * 12, ASSUMPTIONS["water_growth"], T - START + n)
        elec = grow(OWNER["a_electric_month"] * 12, ASSUMPTIONS["electric_growth"], T - START + n)
        maint = mv * ASSUMPTIONS["a_maint_pct"]
        cost = ptax + ins + water + elec + maint
        tax_paid += ptax
        income = 0.0
        income_tax = 0.0
        if option == "rent":
            gross = rent_month * 12 * (1 + ASSUMPTIONS["rent_growth"]) ** n
            effective = gross * (1 - ASSUMPTIONS["vacancy"])
            management = effective * ASSUMPTIONS["management"]
            net_rent = effective - management
            taxable = max(net_rent - depreciation, 0.0)
            income_tax = taxable * (ASSUMPTIONS["fed_ordinary"] + ASSUMPTIONS["ca_ordinary"])
            income = net_rent
            rent_total += net_rent
            depr_total += depreciation
        else:
            # Occupying property A frees the owner-occupied unit in property B to rent.
            freed = GROSS_UNIT_RENT * (1 + ASSUMPTIONS["rent_growth"]) ** n
            effective = freed * (1 - ASSUMPTIONS["vacancy"])
            management = effective * ASSUMPTIONS["management"]
            income = effective - management
            income_tax = income * (ASSUMPTIONS["fed_ordinary"] + ASSUMPTIONS["ca_ordinary"])
        cash += income - income_tax - cost

    mv_end = grow(mv_T, g, HORIZON)
    proceeds = mv_end * (1 - ASSUMPTIONS["selling_cost"])
    adjusted_basis = mv_T - depr_total
    gain = mv_end - adjusted_basis
    recapture = min(depr_total, gain)
    remaining = max(gain - recapture, 0.0)
    fed_cg = recapture * V["unrecaptured_1250"] + remaining * (V["fed_ltcg_top"] + V["niit"])
    ca_cg = gain * ASSUMPTIONS["ca_ordinary"]
    if option == "live":
        excluded = min(remaining, V["sec121_single"])
        remaining_taxable = max(remaining - excluded, 0.0)
        fed_cg = remaining_taxable * (V["fed_ltcg_top"] + V["niit"])
        ca_cg = remaining_taxable * ASSUMPTIONS["ca_ordinary"]
    terminal = cash + proceeds - fed_cg - ca_cg
    return dict(option=option, T=T, terminal=terminal, cash=cash, tax_paid=tax_paid,
                mv_end=r10(mv_end), base_T=r10(base), rent_total=rent_total,
                cg_tax=fed_cg + ca_cg)


GROSS_UNIT_RENT = (OWNER["b_rent_month"] / OWNER["b_units_rented"])  # OWNER rent roll, derived

# Base rent estimate for property A: the gross yield the owner actually achieves on
# property B, applied to property A's market value. Derived from owner data - NOT a
# market quote for property A (flag F-06).
A_GROSS_YIELD = (OWNER["b_rent_month"] * 12) / OWNER["b_value_2026"]
RENT_A_BASE = OWNER["a_value_2026"] * A_GROSS_YIELD / 12


def decision_table(T: int) -> list[dict]:
    rent_base = RENT_A_BASE * (1 + ASSUMPTIONS["rent_growth"]) ** (T - START)
    rows = []
    rows.append(evaluate("sell", T, invest="treasury"))
    rows.append(evaluate("sell", T, invest="equity"))
    rows.append(evaluate("live", T))
    rows.append(evaluate("live", T, prop19=True))
    rows.append(evaluate("rent", T, rent_month=rent_base))
    rows.append(evaluate("rent", T, rent_month=rent_base * 0.70))
    return rows


def breakeven_rent(T: int, target: float) -> float:
    """Monthly rent (in year-T dollars) at which renting matches `target`."""
    lo, hi = 1_000.0, 200_000.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if evaluate("rent", T, rent_month=mid)["terminal"] < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def crossover_growth(T: int, option: str, target: float | None = None,
                     rent_month: float | None = None) -> float:
    """Appreciation rate at which `option` matches selling at the SAME growth rate."""
    lo, hi = -0.05, 0.30
    for _ in range(80):
        mid = (lo + hi) / 2
        benchmark = evaluate("sell", T, g=mid, invest="treasury")["terminal"]
        if evaluate(option, T, g=mid, rent_month=rent_month)["terminal"] < benchmark:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


DECISIONS = {}
for T in INHERIT_YEARS:
    rows = decision_table(T)
    sell_t = next(r["terminal"] for r in rows if r["option"] == "sell_treasury")
    sell_e = next(r["terminal"] for r in rows if r["option"] == "sell_equity")
    live_b = next(r["terminal"] for r in rows if r["option"] == "live")
    be = breakeven_rent(T, sell_t)
    be_eq = breakeven_rent(T, sell_e)
    x_live = crossover_growth(T, "live")
    rent_base_T = RENT_A_BASE * (1 + ASSUMPTIONS["rent_growth"]) ** (T - START)
    x_rent = crossover_growth(T, "rent", rent_month=rent_base_T)
    DECISIONS[T] = dict(
        rows=[{k: (r10(v) if isinstance(v, float) and k in
                   ("terminal", "cash", "tax_paid", "mv_end", "base_T", "rent_total", "cg_tax", "props")
                   else v) for k, v in r.items()} for r in rows],
        market_T=r10(grow(OWNER["a_value_2026"], ASSUMPTIONS["g_market"], T - START)),
        rent_base_month=r10(RENT_A_BASE * (1 + ASSUMPTIONS["rent_growth"]) ** (T - START)),
        breakeven_month=r10(be),
        breakeven_month_vs_equity=r10(be_eq),
        crossover_live=x_live,
        crossover_rent=x_rent,
        sell_treasury=r10(sell_t),
        sell_equity=r10(sell_e),
        live_base=r10(live_b),
    )

# --------------------------------------------------------------------------
# 6. SENSITIVITY
# --------------------------------------------------------------------------
SENS = []
T = 2045
for g in (0.02, 0.03, 0.04):
    base = {r["option"]: r["terminal"] for r in decision_table(T)}
    sell = evaluate("sell", T, invest="treasury", g=g)["terminal"]
    live = evaluate("live", T, g=g)["terminal"]
    rent = evaluate("rent", T, rent_month=RENT_A_BASE * (1 + ASSUMPTIONS["rent_growth"]) ** (T - START),
                    g=g)["terminal"]
    SENS.append(dict(label=f"Appreciation {g*100:.1f}%", sell=r10(sell), live=r10(live), rent=r10(rent)))
for cpi in (0.025, 0.037):
    sell = evaluate("sell", T, invest="treasury", cpi=cpi)["terminal"]
    live = evaluate("live", T, cpi=cpi)["terminal"]
    rent = evaluate("rent", T, rent_month=RENT_A_BASE * (1 + ASSUMPTIONS["rent_growth"]) ** (T - START),
                    cpi=cpi)["terminal"]
    SENS.append(dict(label=f"Inflation {cpi*100:.1f}%", sell=r10(sell), live=r10(live), rent=r10(rent)))

INVEST_SENS = []
for rate in (0.035, V["treasury_10y"], 0.060, 0.070):
    bal = evaluate("sell", T, invest="treasury")["_proceeds_raw"]
    b = bal
    for _ in range(HORIZON):
        b += b * rate * (1 - ASSUMPTIONS["fed_ordinary"])
    INVEST_SENS.append(dict(label=f"Reinvest at {rate*100:.2f}%", terminal=r10(b),
                            after_tax_rate=r10(rate * (1 - ASSUMPTIONS["fed_ordinary"]) * 100) / 100))

# --------------------------------------------------------------------------
# 7. ESTATE TAX HEADROOM
# --------------------------------------------------------------------------
ESTATE = []
for y in range(2026, END + 1):
    if y == 2026:
        excl = V["fed_excl_2026"]
    elif y == 2027:
        excl = V["fed_excl_2027"]
    else:
        excl = grow(V["fed_excl_2027"], ASSUMPTIONS["cpi"], y - 2027)
    combined = grow(OWNER["a_value_2026"] + OWNER["b_value_2026"], ASSUMPTIONS["g_market"], y - START)
    ESTATE.append(dict(year=y, exemption=r10(excl), combined_property=r10(combined),
                       headroom=r10(excl - combined)))

# --------------------------------------------------------------------------
# 8. SF RENTAL P&L
# --------------------------------------------------------------------------
SF_PL = []
for y in YEARS:
    n = y - START
    gross = OWNER["b_rent_month"] * 12 * (1 + ASSUMPTIONS["rent_growth"]) ** n
    eff = gross * (1 - ASSUMPTIONS["vacancy"])
    mgmt = eff * ASSUMPTIONS["management"]
    ptax = V["sf_advalorem"] * grow(grow(b_assessed_2025, 0.02, 1), V["prop13_cap"], n) + grow(B_FLAT, ASSUMPTIONS["cpi"], n)
    c = costs_b[n]
    net = eff - mgmt - ptax - c["insurance"] - c["water"] - c["electricity"] - c["maintenance"]
    SF_PL.append(dict(year=y, gross=r10(gross), vacancy=r10(gross - eff), management=r10(mgmt),
                      property_tax=r10(ptax), insurance=c["insurance"], water=c["water"],
                      electricity=c["electricity"], maintenance=c["maintenance"],
                      net=r10(net)))

# --------------------------------------------------------------------------
# 9. WRITE OUTPUTS
# --------------------------------------------------------------------------
def write_csv(name, rows):
    if not rows:
        return
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    lines = [",".join(cols)]
    for r in rows:
        out = []
        for c in cols:
            v = r.get(c, "")
            s = "" if v == "" else (f"{v}" if not isinstance(v, float) else f"{v:.4f}")
            if any(ch in s for ch in ',"\n'):
                s = '"' + s.replace('"', '""') + '"'
            out.append(s)
        lines.append(",".join(out))
    (DATA / name).write_text("\n".join(lines) + "\n")


write_csv("property_a_projection.csv", proj_a)
write_csv("property_b_projection.csv", proj_b)
write_csv("property_a_operating_costs.csv", costs_a)
write_csv("property_b_operating_costs.csv", costs_b)
write_csv("sf_rental_pl.csv", SF_PL)
write_csv("estate_headroom.csv", ESTATE)
for T, d in DECISIONS.items():
    write_csv(f"decision_{T}.csv", d["rows"])
write_csv("decision_sensitivity.csv", SENS)

OUT = dict(
    owner=OWNER, assumptions=ASSUMPTIONS, values=V, reconcile=RECONCILE,
    a_flat=r10(A_FLAT), b_flat=r10(B_FLAT),
    proj_a=proj_a, proj_b=proj_b, costs_a=costs_a, costs_b=costs_b, sf_pl=SF_PL,
    decisions={str(k): v for k, v in DECISIONS.items()}, sensitivity=SENS, estate=ESTATE,
    invest_sens=INVEST_SENS,
    rent_a=dict(gross_yield=A_GROSS_YIELD, base_month=r10(RENT_A_BASE),
                unit_rent_b=r10(GROSS_UNIT_RENT)),
    checked=dict(
        a_2025_reproduced=r10(V["scc_advalorem"] * a_assessed_2025 + A_FLAT),
        a_2025_observed=OWNER["a_tax_2025"],
        b_2025_reproduced=r10(V["sf_advalorem"] * b_assessed_2025 + B_FLAT),
        b_2025_observed=OWNER["b_tax_2025"],
    ),
)
(DATA / "model_outputs.json").write_text(json.dumps(OUT, indent=1))
print("model: wrote", len(list(DATA.glob('*.csv'))), "CSV files and model_outputs.json")
