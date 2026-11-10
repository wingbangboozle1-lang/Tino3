#!/usr/bin/env python3
"""
model.py — projection and decision engine for the Cupertino / San Francisco
inheritance analysis.

Design rules
------------
1. Every input is either (a) VERIFIED against an official source and tagged with a
   source id, (b) REPORTED by the property owner and used only as a modelling
   input, or (c) an explicit ASSUMPTION.  Nothing is inferred to fill a gap.
2. All currency output is rounded to the nearest $10 as instructed.
3. The module is deterministic: same inputs -> same output.  Output is written to
   data/model.json and a human-readable report to build/model-report.txt so that
   every figure published on the site can be re-derived and audited.

Run:  python3 tools/model.py
"""

from __future__ import annotations
import json
import math
import os

# ----------------------------------------------------------------------------
# 0. Meta
# ----------------------------------------------------------------------------

MODEL_VERSION = "1.0.0"
BUILD_DATE = "2026-11-10"

BASE_YEAR = 2026
INHERIT_YEAR = 2045          # midpoint of the stated 2040-2050 window
INHERIT_LOW = 2040
INHERIT_HIGH = 2050
HORIZON_END = 2065           # terminal sale year for the decision analysis


def r10(x: float) -> int:
    """Round to the nearest $10 (half away from zero)."""
    return int(round(x / 10.0) * 10)


def pct(x: float, dp: int = 2) -> str:
    return f"{x * 100:.{dp}f}%"


# ----------------------------------------------------------------------------
# 1. Assumptions — every one is disclosed on the site
# ----------------------------------------------------------------------------

A = {
    # --- growth -----------------------------------------------------------
    # ASSUMPTION: nominal long-run Bay Area house-price appreciation.
    # Anchored to FHFA HPI history (S14); FHFA publishes past change only, it
    # does not forecast.  4.0% base with 3.0% / 5.0% stress cases.
    "g_market": 0.040,
    "g_market_low": 0.030,
    "g_market_high": 0.050,

    # ASSUMPTION: general inflation applied to insurance, utilities, maintenance.
    "g_cpi": 0.025,
    "g_cpi_low": 0.020,
    "g_cpi_high": 0.035,

    # ASSUMPTION: insurance premiums inflate faster than headline CPI
    # (observed carrier rate filings); modelled as CPI + 2 points.
    "insurance_loading": 0.020,

    # VERIFIED (S17): Proposition 13 caps annual assessed-value growth at 2%.
    # Applying the full cap every year is deliberately conservative for the
    # *inherited* case because it maximises the step-up in the tax base.
    "prop13_cap": 0.020,

    # VERIFIED (S02): the $1,000,000 Prop 19 allowance is adjusted every second
    # February by the change in the FHFA California HPI.  ASSUMPTION: it grows
    # 3.5%/yr between now and 2045 (mid-point of recent CA HPI moves).
    "prop19_allowance_2026": 1_044_586,
    "g_prop19_allowance": 0.035,

    # ASSUMPTION: after-tax nominal return on a diversified 60/40 portfolio.
    # 6.0% base; 4.0% / 8.0% stress.  Not a verified figure - it is a forecast.
    "g_invest": 0.060,
    "g_invest_low": 0.040,
    "g_invest_high": 0.080,

    # ASSUMPTION: blended marginal tax rate on investment / rental income for an
    # heir in the top California bracket.
    #   federal LTCG 20% + NIIT 3.8% + CA 13.3% = 37.1% (S19, S05, S06-adjacent)
    "tax_invest_gain": 0.371,
    # annual income component of the portfolio taxed as it is received
    "portfolio_income_yield": 0.020,
    "tax_portfolio_income": 0.371,

    # ASSUMPTION: marginal rate on net positive rental income
    #   federal 32% + NIIT 3.8% + CA 9.3% = 45.1%
    "tax_rental_income": 0.451,

    # VERIFIED structure, ASSUMED rate: depreciation.  IRC 168 / 27.5-year
    # straight line on the building portion only.  California conforms.
    "depreciation_years": 27.5,

    # ASSUMPTION: share of inherited value allocated to the *building*
    # (depreciable) vs land.  Cupertino SFH 75%; SF 3-unit 60%.
    "building_share_cup": 0.75,
    "building_share_sf": 0.60,

    # ASSUMPTION: selling costs (commission + closing) at 5.0%.
    "selling_cost": 0.050,

    # ASSUMPTION: vacancy & credit loss on rental units 5.0%; management 8.0%.
    "vacancy": 0.050,
    "management": 0.080,

    # ASSUMPTION: discount rate for NPV is set equal to the assumed investment
    # return (6.0%) so that NPV and terminal-wealth rankings agree.  The site
    # also reports NPV at 4% and 5%, which is where the ranking can flip.
    "discount": 0.060,

    # ASSUMPTION: market rent of an *equivalent* Cupertino house.  Derived as a
    # 3.0% gross yield on the 2026 value ($93,000/yr) - i.e. what the heir would
    # have to pay to rent the same standard of housing if they sold the house.
    "rent_cup_2026": 93_000,
    "g_rent": 0.030,
    "g_rent_cup": 0.030,
}

# ----------------------------------------------------------------------------
# 2. Verified inputs
# ----------------------------------------------------------------------------

# Santa Clara County 2025-26 Compilation of Tax Rates (S09).
# Bond / debt components that apply inside the Cupertino-area tax rate areas,
# summed from the published rate book.  NOTE: the parcel's exact TRA is
# unverified, so this is a *floor* for the ad-valorem rate.
SCC_2025_26 = {
    "1% maximum levy": 1.00000,
    "county retirement levy": 0.03880,
    "Cupertino Elem 2001": 0.01650,
    "Cupertino Elem 2012": 0.01690,
    "Cupertino Elem 2024": 0.00010,
    "El Camino Hospital 2003": 0.00200,
    "Foothill-De Anza Coll 1999": 0.00750,
    "Fremont Union High 2008": 0.00880,
    "Fremont Union High 2014": 0.01070,
    "Fremont Union High 2018": 0.01180,
    "SCVWD State Water Proj": 0.00390,
}
SCC_RATE = sum(SCC_2025_26.values()) / 100.0     # 1.117% -> as a fraction

# San Francisco FY2025-26 combined secured property tax rate (S10).
SF_RATE = 1.18268325 / 100.0                      # 1.1827%

# San Francisco documentary transfer tax tiers (S11), rate applied to the FULL
# consideration (not marginal slices).
SF_TRANSFER_TIERS = [
    (100, 250_000, 2.50 / 500),
    (250_000, 1_000_000, 3.40 / 500),
    (1_000_000, 5_000_000, 3.75 / 500),
    (5_000_000, 10_000_000, 11.25 / 500),
    (10_000_000, 25_000_000, 27.50 / 500),
    (25_000_000, math.inf, 30.00 / 500),
]

# Santa Clara County documentary transfer tax: $0.55 per $500 county + $0.55 per
# $500 city of Cupertino? Cupertino imposes no city transfer tax; the county
# rate of $1.10 per $1,000 is used (0.11%).
SCC_TRANSFER = 1.10 / 1000.0

# Revenue & Taxation Code 218 (S16): homeowners' exemption removes $7,000 of
# assessed value from an owner-occupied principal residence.
HOMEOWNERS_EXEMPTION = 7_000

# IRC 121 (S05): $500,000 joint exclusion of gain on a principal residence.
SEC121_JOINT = 500_000


def sf_transfer_tax(value: float) -> float:
    for lo, hi, rate in SF_TRANSFER_TIERS:
        if lo <= value < hi:
            return value * rate
    return value * SF_TRANSFER_TIERS[-1][2]


# ----------------------------------------------------------------------------
# 3. Properties
# ----------------------------------------------------------------------------

CUP = {
    "key": "cup",
    "name": "Cupertino",
    "zip": "95014",
    "fmv_2026": 3_100_000,          # REPORTED by owner (Nov 2026 estimate)
    "assessed_2026": 550_537,       # REPORTED (assessor roll history supplied)
    "tax_2026": 7_207,              # REPORTED (2025-26 bill)
    "tax_2025": 7_003,
    # effective rate implied by the owner's own bill; used for pre-inheritance
    # projection because it is the only evidence of this parcel's actual rate.
    "eff_rate_reported": 7_207 / 550_537,
    "published_rate": SCC_RATE,
    "building_share": A["building_share_cup"],
    "maintenance_pct": 0.0030,      # ASSUMPTION, see flagged page
    "insurance_2026": 2_340,        # CDI statewide avg (S15) used as floor
    "water_month": 125,             # REPORTED midpoint of $100-$150
    "electric_month": -15,          # REPORTED: net credit from solar
    "units": 1,
}

SF = {
    "key": "sf",
    "name": "San Francisco (Outer Sunset)",
    "zip": "94122",
    "fmv_2026": 1_800_000,          # REPORTED
    "assessed_2025": 114_248,       # REPORTED
    "assessed_2026": r10(114_248 * 1.02),
    "tax_2025": 2_439,              # REPORTED
    "tax_2026": None,               # derived below from the reported series
    "eff_rate_reported": 2_439 / 114_248,
    "published_rate": SF_RATE,
    "building_share": A["building_share_sf"],
    "maintenance_pct": 0.0085,      # ASSUMPTION
    "insurance_2026": 2_340,        # CDI statewide avg (S15) used as floor
    "water_month": 365,             # REPORTED midpoint of $330-$400, all 3 units
    "electric_month": 50,           # REPORTED midpoint of $30-$70
    "units": 3,
    "rent_occupied_month": 7_150,   # REPORTED, two rented units combined
    "rent_vacant_month": 3_575,     # ASSUMPTION: vacant unit at the same per-unit rate
}
SF["tax_2026"] = r10(SF["tax_2025"] * 1.02)

PROPS = [CUP, SF]


# ----------------------------------------------------------------------------
# 4. Growth paths
# ----------------------------------------------------------------------------

def prop19_allowance(year: int) -> float:
    return A["prop19_allowance_2026"] * (1 + A["g_prop19_allowance"]) ** max(0, year - BASE_YEAR)


def fmv(prop, year: int, g: float | None = None) -> float:
    g = A["g_market"] if g is None else g
    return prop["fmv_2026"] * (1 + g) ** (year - BASE_YEAR)


def assessed_prop13(prop, year: int) -> float:
    start = prop["assessed_2026"]
    return start * (1 + A["prop13_cap"]) ** (year - BASE_YEAR)


def reported_tax(prop, year: int) -> float:
    """Pre-inheritance tax: the owner's reported bill grown at the Prop 13 cap."""
    start = prop["tax_2026"]
    return start * (1 + A["prop13_cap"]) ** (year - BASE_YEAR)


# ----------------------------------------------------------------------------
# 5. Prop 19 mechanics
# ----------------------------------------------------------------------------

def prop19_new_base(prop, year: int, excluded: bool, g: float | None = None) -> dict:
    """
    Returns the new taxable base and the components, per S01 / S02.

    If `excluded` is False the property is reassessed to full market value
    (either it was not the transferor's principal residence, or the heir did not
    occupy it within one year and claim the homeowners' exemption).
    """
    f = fmv(prop, year, g)
    fbyv = assessed_prop13(prop, year)
    allowance = prop19_allowance(year)
    if not excluded:
        return {
            "excluded": False,
            "fmv": f,
            "fbyv": fbyv,
            "allowance": allowance,
            "cap": fbyv + allowance,
            "new_base": f,
            "excess_added": f - fbyv,
        }
    cap = fbyv + allowance
    excess = max(0.0, f - cap)
    return {
        "excluded": True,
        "fmv": f,
        "fbyv": fbyv,
        "allowance": allowance,
        "cap": cap,
        "new_base": fbyv + excess,
        "excess_added": excess,
    }


# ----------------------------------------------------------------------------
# 6. Projection table 2026-2065
# ----------------------------------------------------------------------------

def projection_table(g: float | None = None) -> list[dict]:
    rows = []
    for y in range(BASE_YEAR, HORIZON_END + 1):
        row = {"year": y}
        for p in PROPS:
            k = p["key"]
            row[f"{k}_fmv"] = r10(fmv(p, y, g))
            row[f"{k}_assessed"] = r10(assessed_prop13(p, y))
            row[f"{k}_tax"] = r10(reported_tax(p, y))
            row[f"{k}_basis"] = "reported" if y <= INHERIT_YEAR else "continued Prop 13"
        row["cumulative"] = y
        rows.append(row)
    return rows


# ----------------------------------------------------------------------------
# 7. Operating costs
# ----------------------------------------------------------------------------

def opex(prop, year: int, occupied_by_heir: bool, g: float | None = None) -> dict:
    """Annual operating costs *paid by the owner* for a property in a given year."""
    n = year - BASE_YEAR
    infl = (1 + A["g_cpi"]) ** n
    ins_infl = (1 + A["g_cpi"] + A["insurance_loading"]) ** n
    f = fmv(prop, year, g)

    # Water / electricity: the heir pays them when occupying; a tenant pays them
    # when the unit is let.  For the SF building the owner keeps common-area and
    # common-meter service in both cases (landlord-paid water is the norm for a
    # three-unit building with a shared meter).
    if occupied_by_heir or prop["key"] == "sf":
        water = prop["water_month"] * 12 * infl
        electric = prop["electric_month"] * 12 * infl
    else:
        water = 0.0
        electric = 0.0

    return {
        "insurance": prop["insurance_2026"] * ins_infl,
        "water": water,
        "electric": electric,
        "maintenance": f * prop["maintenance_pct"],
    }


def market_rent_cup(year: int) -> float:
    """Market rent for an equivalent Cupertino house, annual, gross."""
    return A["rent_cup_2026"] * (1 + A["g_rent_cup"]) ** (year - BASE_YEAR)


def rental_income(prop, year: int, let_units: int) -> float:
    """
    Gross scheduled rent after an allowance for vacancy.

    Cupertino single-family: market rent from market_rent_cup().
    San Francisco 3-unit: the two sitting tenancies escalate at the SF Rent
    Board allowable increase (S13) - they are rent-controlled; the third unit is
    let at the assumed market rent and escalates at 3.0%/yr.
    """
    if prop["key"] != "sf":
        return market_rent_cup(year) * (1 - A["vacancy"]) * (1 if let_units else 0)

    n = max(0, year - BASE_YEAR)
    rc = prop["rent_occupied_month"] * 12 * (1 + 0.016) ** n      # S13 1.6%
    mkt = prop["rent_vacant_month"] * 12 * (1 + A["g_rent"]) ** n
    if let_units >= 3:
        inc = rc + mkt
    elif let_units == 2:
        inc = rc
    else:
        inc = 0.0
    return inc * (1 - A["vacancy"])


# ----------------------------------------------------------------------------
# 8. Scenario engine
# ----------------------------------------------------------------------------

def run_scenario(
    name: str,
    live_in: str | None,            # "cup" | "sf" | None
    sell: dict,                     # property sold at inheritance
    rent_cup: bool,
    rent_sf_units: int,
    parent_residence: str = "cup",  # which house is the transferor's principal residence
    g: float = A["g_market"],
    disc: float | None = None,
    short: str = "",
) -> dict:
    """
    After-tax wealth model, 2045 -> 2065.

    Method
    ------
    * Every annual net cash flow (rent received, less property tax, insurance,
      utilities, maintenance, income tax and - where the heir does not occupy an
      inherited house - market rent for equivalent housing) is deposited into /
      drawn from a single portfolio.
    * The portfolio compounds at the assumed 6.0% nominal return; the 2.0% income
      component is taxed annually.
    * At 2065 any remaining house is sold: 5.0% selling costs, documentary
      transfer tax, capital-gains tax on the post-inheritance gain with
      depreciation recapture on let property, and IRC 121 relief on an
      owner-occupied home.
    * The portfolio is liquidated at 2065 and taxed on unrealised gains.
    * Terminal wealth is therefore the single consistent bottom line; NPV is the
      same stream discounted at the assumed opportunity cost.
    """
    disc = A["discount"] if disc is None else disc
    y0 = INHERIT_YEAR

    # Basis: IRC 1014 step-up to date-of-death fair market value (S18).
    basis = {p["key"]: fmv(p, y0, g) for p in PROPS}

    # Property tax in the first post-inheritance year.
    tax0, p19 = {}, {}
    for p in PROPS:
        k = p["key"]
        if sell.get(k):
            tax0[k] = None
            p19[k] = None
            continue
        qualifies = (k == parent_residence) and (live_in == k)
        p19[k] = prop19_new_base(p, y0, qualifies, g)
        base = p19[k]["new_base"]
        if live_in == k:
            base = max(0.0, base - HOMEOWNERS_EXEMPTION)
        rate = p["eff_rate_reported"] if k == "cup" else p["published_rate"]
        tax0[k] = base * rate

    # Immediate sales.
    proceeds, sale_detail = 0.0, {}
    for k, do in sell.items():
        if not do:
            continue
        p = CUP if k == "cup" else SF
        price = fmv(p, y0, g)
        cost = price * A["selling_cost"]
        tt = sf_transfer_tax(price) if k == "sf" else price * SCC_TRANSFER
        gain = max(0.0, price - cost - basis[k])   # ~0 thanks to the step-up
        cgt = gain * A["tax_invest_gain"]
        net = price - cost - tt - cgt
        proceeds += net
        sale_detail[k] = {
            "price": r10(price), "selling_cost": r10(cost), "transfer_tax": r10(tt),
            "capital_gains_tax": r10(cgt), "net": r10(net),
        }

    portfolio = proceeds
    port_basis = proceeds
    cashflows = []

    for year in range(y0, HORIZON_END + 1):
        cf = {"year": year, "rent": 0.0, "opex": 0.0, "proptax": 0.0,
              "income_tax": 0.0, "housing": 0.0, "portfolio_end": 0.0}

        dep_year = 0.0
        for p in PROPS:
            k = p["key"]
            if sell.get(k):
                continue
            occupied = (live_in == k)
            o = opex(p, year, occupied, g)
            cf["opex"] += o["insurance"] + o["water"] + o["electric"] + o["maintenance"]
            cf["proptax"] += tax0[k] * (1 + A["prop13_cap"]) ** (year - y0)

            if k == "cup" and rent_cup and not occupied:
                cf["rent"] += rental_income(p, year, 1) * (1 - A["management"])
                dep_year += basis[k] * p["building_share"] / A["depreciation_years"]
            if k == "sf":
                let_units = 2 if occupied else (rent_sf_units or 0)
                if let_units:
                    cf["rent"] += rental_income(p, year, let_units) * (1 - A["management"])
                    dep_year += (basis[k] * p["building_share"] /
                                 A["depreciation_years"]) * (let_units / 3.0)

        taxable_rent = cf["rent"] - cf["opex"] - cf["proptax"] - dep_year
        if taxable_rent > 0:
            cf["income_tax"] = taxable_rent * A["tax_rental_income"]

        # Equivalent housing has to be paid for if no inherited house is occupied.
        if live_in is None:
            cf["housing"] = market_rent_cup(year)

        cf["net"] = (cf["rent"] - cf["opex"] - cf["proptax"]
                     - cf["income_tax"] - cf["housing"])

        # Cash flow into / out of the portfolio, then portfolio growth.
        portfolio += cf["net"]
        port_basis += cf["net"]
        if portfolio > 0:
            inc = portfolio * A["portfolio_income_yield"]
            portfolio = portfolio * (1 + A["g_invest"]) - inc * A["tax_portfolio_income"]
        cf["portfolio_end"] = portfolio
        cashflows.append(cf)

    # Terminal: sell any remaining house, then liquidate the portfolio.
    terminal, term_detail = 0.0, {}
    for p in PROPS:
        k = p["key"]
        if sell.get(k):
            continue
        price = fmv(p, HORIZON_END, g)
        cost = price * A["selling_cost"]
        tt = sf_transfer_tax(price) if k == "sf" else price * SCC_TRANSFER
        let = ((k == "cup" and rent_cup and live_in != "cup") or
               (k == "sf" and live_in != "sf" and rent_sf_units))
        dep_total = 0.0
        if let:
            share = 1.0
            if k == "sf":
                share = (2.0 / 3.0) if live_in == "sf" else 1.0
            dep_total = min(basis[k] * p["building_share"] * share,
                            basis[k] * p["building_share"] / A["depreciation_years"]
                            * (HORIZON_END - y0 + 1) * share)
        adj_basis = basis[k] - dep_total
        gain = max(0.0, price - cost - adj_basis)
        recapture = min(dep_total, gain)
        other = max(0.0, gain - recapture)
        if live_in == k:
            other = max(0.0, other - SEC121_JOINT)     # IRC 121 (S05)
        cgt = recapture * 0.25 + recapture * 0.133 + other * A["tax_invest_gain"]
        net = price - cost - tt - cgt
        terminal += net
        term_detail[k] = {
            "price": r10(price), "selling_cost": r10(cost), "transfer_tax": r10(tt),
            "gain": r10(gain), "capital_gains_tax": r10(cgt), "net": r10(net),
            "depreciation_taken": r10(dep_total),
        }

    port_gain = max(0.0, portfolio - port_basis)
    port_after_tax = portfolio - port_gain * A["tax_invest_gain"]

    # Standard DCF: today's investable proceeds, plus the annual after-tax cash
    # flows, plus the terminal asset sales.  The portfolio balance is *not* added
    # again - it is the accumulation of these same flows.
    npv = proceeds
    npv += sum(c["net"] / (1 + disc) ** (c["year"] - y0) for c in cashflows)
    npv += terminal / (1 + disc) ** (HORIZON_END - y0)

    return {
        "short": short or name[:1],
        "name": name,
        "live_in": live_in,
        "parent_residence": parent_residence,
        "sold_at_inheritance": [k for k, v in sell.items() if v],
        "tax_at_inheritance": {k: r10(v) for k, v in tax0.items() if v is not None},
        "prop19": {k: ({"fmv": r10(v["fmv"]), "fbyv": r10(v["fbyv"]),
                        "allowance": r10(v["allowance"]), "cap": r10(v["cap"]),
                        "new_base": r10(v["new_base"]),
                        "exclusion_applied": v["excluded"]} if v else None)
                   for k, v in p19.items()},
        "sale_at_inheritance": sale_detail,
        "first_year_cashflow": r10(cashflows[0]["net"]),
        "last_year_cashflow": r10(cashflows[-1]["net"]),
        "cumulative_cashflow": r10(sum(c["net"] for c in cashflows)),
        "terminal_sales": term_detail,
        "terminal_portfolio": r10(port_after_tax),
        "total_terminal_wealth": r10(terminal + port_after_tax),
        "npv": r10(npv),
        "cashflows": [{"year": c["year"], "rent": r10(c["rent"]), "opex": r10(c["opex"]),
                       "proptax": r10(c["proptax"]), "income_tax": r10(c["income_tax"]),
                       "housing": r10(c["housing"]), "net": r10(c["net"]),
                       "portfolio_end": r10(c["portfolio_end"])} for c in cashflows],
    }


def build_scenarios(parent_residence="cup", g=A["g_market"], disc=None, label=""):
    suffix = label
    specs = [
        ("A", "Live in Cupertino; rent all three San Francisco units",
         dict(live_in="cup", sell={"cup": False, "sf": False},
              rent_cup=False, rent_sf_units=3)),
        ("B", "Live in San Francisco (vacant unit); rent Cupertino",
         dict(live_in="sf", sell={"cup": False, "sf": False},
              rent_cup=True, rent_sf_units=3)),
        ("C", "Rent both houses; rent equivalent housing",
         dict(live_in=None, sell={"cup": False, "sf": False},
              rent_cup=True, rent_sf_units=3)),
        ("D", "Sell both at inheritance; invest the net proceeds",
         dict(live_in=None, sell={"cup": True, "sf": True},
              rent_cup=False, rent_sf_units=0)),
        ("E", "Live in Cupertino; sell the San Francisco building",
         dict(live_in="cup", sell={"cup": False, "sf": True},
              rent_cup=False, rent_sf_units=0)),
        ("F", "Live in San Francisco; sell Cupertino",
         dict(live_in="sf", sell={"cup": True, "sf": False},
              rent_cup=False, rent_sf_units=3)),
    ]
    out = []
    for tag, title, kw in specs:
        out.append(run_scenario(f"{tag}. {title}{suffix}", short=tag,
                                parent_residence=parent_residence, g=g, disc=disc, **kw))
    return out


# ----------------------------------------------------------------------------
# 9. Main
# ----------------------------------------------------------------------------

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    os.makedirs(os.path.join(root, "data"), exist_ok=True)
    os.makedirs(os.path.join(root, "build"), exist_ok=True)

    base = build_scenarios(parent_residence="cup")

    # sensitivity: flip which house is the parent's principal residence
    flip = build_scenarios(parent_residence="sf", label=" (SF is the parents' home)")

    # sensitivity: house growth x portfolio return, all six scenarios
    grid = []
    for g in (A["g_market_low"], A["g_market"], A["g_market_high"]):
        for inv in (A["g_invest_low"], A["g_invest"], A["g_invest_high"]):
            saved = A["g_invest"]
            A["g_invest"] = inv
            res = build_scenarios(parent_residence="cup", g=g)
            A["g_invest"] = saved
            row = {"g": g, "inv": inv,
                   "wealth": {r["short"]: r["total_terminal_wealth"] for r in res}}
            best = max(res, key=lambda r: r["total_terminal_wealth"])
            row["best"] = best["short"]
            row["best_wealth"] = best["total_terminal_wealth"]
            row["runner_up"] = sorted(res, key=lambda r: -r["total_terminal_wealth"])[1]["short"]
            grid.append(row)

    # inheritance-year sensitivity
    year_sens = []
    for y in (INHERIT_LOW, INHERIT_YEAR, INHERIT_HIGH):
        for p in PROPS:
            b = prop19_new_base(p, y, True if p["key"] == "cup" else False)
            nb_full = fmv(p, y)
            rate = p["eff_rate_reported"] if p["key"] == "cup" else p["published_rate"]
            year_sens.append({
                "year": y,
                "property": p["name"],
                "fmv": r10(nb_full),
                "fbyv": r10(b["fbyv"]),
                "allowance": r10(b["allowance"]),
                "cap": r10(b["cap"]),
                "new_base_excluded": r10(b["new_base"]),
                "tax_excluded": r10(b["new_base"] * rate),
                "new_base_full": r10(nb_full),
                "tax_full": r10(nb_full * rate),
                "annual_saving": r10(nb_full * rate - b["new_base"] * rate),
            })

    # ---- derived figures used on the site --------------------------------
    # (1) Lifetime value of the Prop 19 exclusion on the family home, assuming
    #     the heir occupies it.  Sum of (full-reassessment tax - excluded tax)
    #     over the 21 post-transfer years, each base growing at the Prop 13 cap.
    p19_life = {}
    for p in PROPS:
        inc = prop19_new_base(p, INHERIT_YEAR, True)
        full = prop19_new_base(p, INHERIT_YEAR, False)
        rate = p["eff_rate_reported"] if p["key"] == "cup" else p["published_rate"]
        diff = (full["new_base"] - inc["new_base"]) * rate
        total = 0.0
        for y in range(INHERIT_YEAR, HORIZON_END + 1):
            total += diff * (1 + A["prop13_cap"]) ** (y - INHERIT_YEAR)
        p19_life[p["key"]] = {
            "annual_saving_first_year": r10(diff),
            "twenty_one_year_saving": r10(total),
            "new_base_if_excluded": r10(inc["new_base"]),
            "new_base_if_full": r10(full["new_base"]),
        }

    # (2) Value of the IRC 1014 step-up: the pre-death appreciation that never
    #     meets a capital-gains tax because the basis resets at death.
    gain_escaped = sum(fmv(p, INHERIT_YEAR) - p["fmv_2026"] for p in PROPS)
    stepup = {
        "pre_inheritance_appreciation": r10(gain_escaped),
        "rate_assumed": A["tax_invest_gain"],
        "tax_avoided": r10(gain_escaped * A["tax_invest_gain"]),
    }

    # (3) Federal estate-tax thresholds, 2026 verified and projected forward by
    #     inflation at 2.5%/yr (ASSUMPTION).
    est = []
    for y in (2026, 2030, 2035, 2040, 2045, 2050):
        f = 15_000_000 * (1.025 ** (y - 2026))
        est.append({"year": y, "single": r10(f), "married_portable": r10(f * 2),
                    "basis": "verified 2026 (S03); projected 2026+ at 2.5%/yr" if y > 2026
                             else "verified (S03)"})
    estate = {
        "thresholds": est,
        "top_rate": 0.40,
        "ca_state_estate_tax": 0,
        "annual_gift_exclusion_2026": 19_000,
    }

    # (4) Post-reassessment cash yield on each property, first year.
    yields = {}
    for p in PROPS:
        y1 = INHERIT_YEAR
        if p["key"] == "cup":
            gross = rental_income(p, y1, 1) * (1 - A["management"])
        else:
            gross = rental_income(p, y1, 3) * (1 - A["management"])
        o = opex(p, y1, False)
        tb = prop19_new_base(p, y1, False)["new_base"] * (
            p["eff_rate_reported"] if p["key"] == "cup" else p["published_rate"])
        net = gross - (o["insurance"] + o["water"] + o["electric"] + o["maintenance"]) - tb
        yields[p["key"]] = {
            "gross_rent": r10(gross), "opex": r10(o["insurance"] + o["water"] + o["electric"] + o["maintenance"]),
            "property_tax": r10(tb), "net": r10(net),
            "net_yield_on_value": round(net / fmv(p, y1), 4),
            "value": r10(fmv(p, y1)),
        }

    payload = {
        "meta": {
            "model_version": MODEL_VERSION,
            "build_date": BUILD_DATE,
            "base_year": BASE_YEAR,
            "inherit_year": INHERIT_YEAR,
            "horizon_end": HORIZON_END,
        },
        "assumptions": A,
        "rates": {
            "svc_2025_26_components": SCC_2025_26,
            "svc_rate": SCC_RATE,
            "svc_rate_published_range": "1.08%-1.30% of assessed value",
            "sf_rate": SF_RATE,
            "sf_transfer_tiers": [
                {"from": lo, "to": (None if hi == math.inf else hi), "per_500": round(rate * 500, 4),
                 "pct": round(rate * 100, 4)}
                for lo, hi, rate in SF_TRANSFER_TIERS
            ],
            "svc_transfer": SCC_TRANSFER,
            "homeowners_exemption": HOMEOWNERS_EXEMPTION,
            "sec121_joint": SEC121_JOINT,
        },
        "properties": [
            {**{k: v for k, v in p.items() if not callable(v)}} for p in PROPS
        ],
        "projection": projection_table(),
        "scenarios_parent_cup": base,
        "scenarios_parent_sf": flip,
        "grid": grid,
        "prop19_lifetime": p19_life,
        "stepup": stepup,
        "estate": estate,
        "post_reassessment_yield": yields,
        "inheritance_year_sensitivity": year_sens,
    }

    with open(os.path.join(root, "data", "model.json"), "w") as f:
        json.dump(payload, f, indent=1)

    # ---- human readable report --------------------------------------------
    lines = []
    add = lines.append
    add(f"MODEL REPORT  v{MODEL_VERSION}  {BUILD_DATE}")
    add("=" * 78)
    add(f"Rate used, Cupertino (reported-bill implied): {pct(CUP['eff_rate_reported'],4)}")
    add(f"Rate used, Cupertino (SCC 2025-26 published floor): {pct(SCC_RATE,4)}")
    add(f"Rate used, San Francisco (published FY2025-26): {pct(SF_RATE,6)}")
    add(f"Rate implied by reported SF bill: {pct(SF['eff_rate_reported'],4)}  <-- IRREGULARITY")
    add("")
    add(f"{'Year':<6}{'CUP FMV':>12}{'CUP assd':>12}{'CUP tax':>11}"
        f"{'SF FMV':>12}{'SF assd':>12}{'SF tax':>11}")
    for row in projection_table():
        y = row["year"]
        if y <= INHERIT_YEAR or y % 5 == 0:
            add(f"{y:<6}{row['cup_fmv']:>12,}{row['cup_assessed']:>12,}{row['cup_tax'] or 0:>11,}"
                f"{row['sf_fmv']:>12,}{row['sf_assessed']:>12,}{row['sf_tax'] or 0:>11,}")
    add("")
    add("SCENARIOS  (parents' principal residence = Cupertino)")
    add("-" * 78)
    for s in base:
        add(f"{s['name'][:60]:<62}{s['npv']:>12,}{s['total_terminal_wealth']:>14,}")
    add("")
    add("SCENARIOS  (parents' principal residence = San Francisco)")
    add("-" * 78)
    for s in flip:
        add(f"{s['name'][:60]:<62}{s['npv']:>12,}{s['total_terminal_wealth']:>14,}")
    add("")
    add("INHERITANCE-YEAR SENSITIVITY")
    add("-" * 78)
    for r in year_sens:
        add(f"{r['year']}  {r['property'][:24]:<26} FMV {r['fmv']:>12,}  "
            f"base-excl {r['new_base_excluded']:>12,}  tax {r['tax_excluded']:>10,}  "
            f"| full {r['tax_full']:>10,}")
    add("")
    add("ROBUSTNESS GRID  (terminal after-tax wealth 2065; 'best' = winning scenario)")
    add("-" * 78)
    add(f"{'house g':>9}{'invest r':>10}   {'A':>12}{'B':>12}{'C':>12}{'D':>12}{'E':>12}{'F':>12}  best")
    for r in grid:
        w = r["wealth"]
        add(f"{r['g']*100:>8.0f}%{r['inv']*100:>9.0f}%   "
            + "".join(f"{w[k]:>12,}" for k in "ABCDEF")
            + f"  {r['best']}")

    rep = "\n".join(lines)
    with open(os.path.join(root, "build", "model-report.txt"), "w") as f:
        f.write(rep + "\n")
    print(rep)


if __name__ == "__main__":
    main()
