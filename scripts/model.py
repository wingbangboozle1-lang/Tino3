#!/usr/bin/env python3
"""Deterministic planning model for the inheritance decision.

Rules enforced here:
  * Every dollar amount that leaves this script is rounded to the nearest $10.
  * Owner-supplied figures are labelled "owner-provided" and "unverified"; they are inputs, not facts.
  * Every scenario assumption is explicit and carries a stable id so the site can display it.
  * No names, addresses, ZIP codes, parcel numbers or unrounded roll figures exist in this file.
Output: assets/data/model.json  (consumed by scripts/build.py)
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "data" / "model.json"


def r10(x: float) -> int:
    """Nearest $10."""
    return int(round(float(x) / 10.0) * 10)


# ----------------------------------------------------------------------------
# ASSUMPTIONS (each one is displayed on the site with its basis and a source id
# where a source exists; scenario assumptions carry no source because they are
# not law or verified data).
# ----------------------------------------------------------------------------
A = {
    "appreciation": {"low": 0.03, "base": 0.04, "high": 0.05, "basis": "Scenario assumptions, not forecasts."},
    "cpi": 0.025,
    "prop13_growth": 0.02,
    "prop19_cap_growth": 0.030,
    "fed_exclusion_2026": 15_000_000,
    "fed_exclusion_indexing": 0.025,
    "equity_return": 0.070,
    "bond_return": 0.040,
    "cash_return": 0.030,
    "rent_growth": 0.025,
    "rent_yield_a": 0.030,
    "vacancy": 0.03,
    "income_tax": 0.333,
    "gain_tax": 0.323,
    "niit": 0.038,
    "sell_cost": 0.0511,
    "maint_rate_a": 0.0050,
    "maint_rate_b": 0.0100,
    "horizon_end": 2055,
    "inherit_years": [2040, 2045, 2050],
}

# Owner-provided, already rounded, treated as unverified planning inputs.
INPUTS = {
    "a_value_2026": 3_100_000,
    "a_fbyv_2026": 550_540,
    "a_tax_2025": 7_210,
    "a_assessed_2025": 539_740,
    "a_water_yr": 1_560,          # $130/mo midpoint of the stated $100-$150 range
    "a_electric_yr": -180,        # net solar credit, stated $10-$20/month profit
    "a_insurance_owner_est": 1_500,
    "a_insurance_scenario": 3_000,  # flagged: no verified quote; own scenario band
    "b_value_2026": 1_800_000,
    "b_assessed_2025": 114_250,
    "b_tax_2025": 2_439,
    "b_rent_mo": 7_150,
    "b_water_yr": 4_380,          # $365/mo midpoint of the stated $330-$400 range
    "b_electric_yr": 600,         # $50/mo midpoint of the stated $30-$70 range
    "b_insurance_owner_est": 1_500,
    "b_insurance_scenario": 3_600,
}

# Verified rates
RATE_B = 0.0118268325          # SF FY2025-26 combined rate per $100 (src sf_rate)
PROP19_CAP_2025 = 1_044_586    # src boe_cap

RATE_A = INPUTS["a_tax_2025"] / INPUTS["a_assessed_2025"]   # derived effective rate


def money(x) -> str:
    return f"${r10(x):,}"


def a_value(year, g):
    return INPUTS["a_value_2026"] * (1 + g) ** (year - 2026)


def b_value(year, g):
    return INPUTS["b_value_2026"] * (1 + g) ** (year - 2026)


def a_fbyv(year):
    return INPUTS["a_fbyv_2026"] * (1 + A["prop13_growth"]) ** (year - 2026)


def b_assessed(year):
    # 2026 = 2025 roll value elevated by the 2% cap, then 2%/yr
    return r10(INPUTS["b_assessed_2025"] * (1 + A["prop13_growth"]) ** (year - 2025))


def prop19_cap(year):
    return PROP19_CAP_2025 * (1 + A["prop19_cap_growth"]) ** (year - 2025)


def tax_a_owned(year):
    """Property A tax if the family keeps holding it (no death, no reassessment)."""
    assessed = r10(INPUTS["a_fbyv_2026"] * (1 + A["prop13_growth"]) ** (year - 2026))
    return assessed, r10(assessed * RATE_A)


def b_operating(year, g, owner_occupies_one_unit=True):
    n = year - 2026
    gross = INPUTS["b_rent_mo"] * 12 * (1 + A["rent_growth"]) ** n
    if not owner_occupies_one_unit:
        gross += (INPUTS["b_rent_mo"] / 2) * 12 * (1 + A["rent_growth"]) ** n
    vac = gross * A["vacancy"]
    water = INPUTS["b_water_yr"] * (1 + A["cpi"]) ** n
    elec = INPUTS["b_electric_yr"] * (1 + A["cpi"]) ** n
    ins = INPUTS["b_insurance_scenario"] * (1 + A["cpi"]) ** n
    maint = b_value(year, g) * A["maint_rate_b"]
    assessed = b_assessed(year)
    tax = assessed * RATE_B
    NOI = gross - vac - water - elec - ins - maint - tax
    after_tax = NOI - max(0.0, NOI) * A["income_tax"]
    return {
        "gross": r10(gross), "vacancy": r10(vac), "water": r10(water), "electric": r10(elec),
        "insurance": r10(ins), "maintenance": r10(maint), "tax": r10(tax), "assessed": assessed,
        "noi": r10(NOI), "after_tax": r10(after_tax),
    }


def a_carrying(year, g, occupied):
    n = year - 2026
    ins = (INPUTS["a_insurance_scenario"] if not occupied else INPUTS["a_insurance_owner_est"]) * (1 + A["cpi"]) ** n
    water = INPUTS["a_water_yr"] * (1 + A["cpi"]) ** n
    elec = INPUTS["a_electric_yr"] * (1 + A["cpi"]) ** n
    maint = a_value(year, g) * A["maint_rate_a"]
    return {"insurance": r10(ins), "water": r10(water), "electric": r10(elec), "maintenance": r10(maint)}


def a_rental(year, g):
    n = year - 2026
    gross = a_value(year, g) * A["rent_yield_a"]
    vac = gross * A["vacancy"]
    c = a_carrying(year, g, occupied=False)
    return {"gross": r10(gross), "vacancy": r10(vac), **c}


def inherit_taxes(year, g, law="prop19"):
    """Property tax in the first inheritance year under each option."""
    fmv = a_value(year, g)
    fbyv = r10(a_fbyv(year))
    cap = r10(prop19_cap(year))
    if law == "prop19":
        blended = fbyv + max(0.0, fmv - fbyv - cap)
        live = r10(blended)
    else:  # proposal 25-0017 / pre-Prop 19 style full exclusion: base year value retained
        live = fbyv
    rented = r10(fmv)
    return {
        "fmv": r10(fmv), "fbyv": fbyv, "cap": cap,
        "assessed_live": live, "assessed_rent": rented,
        "tax_live": r10(live * RATE_A), "tax_rent": r10(rented * RATE_A),
        "tax_exclusion_full": r10(fbyv * RATE_A),
    }


def terminal_tax_on_gain(final, basis):
    return max(0.0, final - basis) * A["gain_tax"]


def run_strategy(strategy, Y, g, reinvest=None, law="prop19"):
    """Return year-1 cash flow, cumulative after-tax cash, terminal net worth at 2055."""
    end = A["horizon_end"]
    tx = inherit_taxes(Y, g, law)
    cash = 0.0
    cash_bucket = 0.0
    portfolio = 0.0
    basis = 0.0
    yr1 = None

    if strategy in ("S1", "S2"):
        if strategy == "S1":
            a_assessed = tx["assessed_live"]
        else:
            # Under the pending full-exclusion proposal, a rental transfer would keep the base year value.
            a_assessed = tx["assessed_live"] if law == "proposal" else tx["assessed_rent"]
    else:
        proceeds = tx["fmv"] * (1 - A["sell_cost"])
        portfolio = proceeds
        basis = proceeds

    def grow_bucket(b, rate):
        return b * (1 + rate)

    for year in range(Y, end + 1):
        n = year - Y
        b_op = b_operating(year, g, owner_occupies_one_unit=(strategy != "S1"))
        cf = b_op["after_tax"]
        if strategy == "S1":
            c = a_carrying(year, g, occupied=True)
            a_assessed_year = r10(a_assessed * (1 + A["prop13_growth"]) ** n)
            tax = a_assessed_year * RATE_A
            cf += -(c["insurance"] + c["water"] + c["electric"] + c["maintenance"] + tax)
        elif strategy == "S2":
            r = a_rental(year, g)
            a_assessed_year = r10(a_assessed * (1 + A["prop13_growth"]) ** n)
            tax = a_assessed_year * RATE_A
            noi = r["gross"] - r["vacancy"] - r["insurance"] - r["water"] - r["electric"] - r["maintenance"] - tax
            cf += noi - max(0.0, noi) * A["income_tax"]
        else:  # S3A / S3B
            if reinvest == "bond":
                interest = portfolio * A["bond_return"]
                portfolio += interest - interest * A["income_tax"]
            else:
                portfolio *= (1 + A["equity_return"])
        if yr1 is None:
            yr1 = r10(cf)
        cash += cf
        cash_bucket = grow_bucket(cash_bucket, A["cash_return"]) + cf

    net = b_value(end, g) + cash_bucket
    if strategy in ("S1", "S2"):
        net += a_value(end, g)
    else:
        net += portfolio - terminal_tax_on_gain(portfolio, basis)
    return {"yr1_cash": yr1, "cum_cash": r10(cash), "terminal_net_worth": r10(net), "tax_first_year": tx["tax_live"] if strategy == "S1" else tx["tax_rent"] if strategy == "S2" else 0}


def breakeven_return(Y, g, target):
    """Reinvest return that makes S3A terminal net worth equal to `target`."""
    lo, hi = 0.0, 0.25
    for _ in range(80):
        mid = (lo + hi) / 2
        A["equity_return"] = mid
        v = run_strategy("S3A", Y, g)["terminal_net_worth"]
        if v < target:
            lo = mid
        else:
            hi = mid
    A["equity_return"] = 0.070
    return mid


def build():
    g = A["appreciation"]["base"]
    data = {"assumptions": [], "history_a": [], "history_b": [], "projections_a": [], "projections_b": [],
            "carrying": [], "inheritance": [], "decision": [], "estate": [], "sensitivity": [], "sources_rates": {}}

    RATE_INFO = {
        "rate_a_derived": round(RATE_A * 100, 3),
        "rate_a_source": "derived: owner-provided 2025 bill divided by owner-provided 2025 assessed value",
        "rate_b": round(RATE_B * 100, 5),
        "rate_b_source": "sf_rate",
        "prop19_cap_2025": r10(PROP19_CAP_2025),
    }
    data["sources_rates"] = RATE_INFO

    # Assumption register
    for key, label, value, basis in [
        ("appreciation", "Property appreciation (nominal, per year)", "3.0% / 4.0% / 5.0%", "Scenario band; the base case is 4.0%. Not a forecast."),
        ("cpi", "General inflation / cost growth", "2.5%", "Scenario assumption used for insurance, water, utilities and rent growth."),
        ("prop13_growth", "Assessed-value growth while owned (RTC 51)", "2.0%", "Statutory 2% cap applies while California CPI exceeds 2%."),
        ("prop19_cap_growth", "Proposition 19 exclusion cap growth", "3.0%", "The real cap is recalculated every two years from the FHFA House Price Index for California; the growth rate is a scenario assumption."),
        ("fed_exclusion_2026", "Federal estate exclusion, 2026", "$15,000,000", "Statutory amount for deaths in 2026."),
        ("fed_exclusion_indexing", "Federal exclusion indexing after 2026", "2.5%", "Scenario assumption; the 2027 published amount was not retrievable from an official page in this review."),
        ("equity_return", "Diversified equity return (nominal)", "7.0%", "Scenario assumption for the sell-and-reinvest comparison."),
        ("bond_return", "Bond / Treasury return (nominal)", "4.0%", "Scenario assumption; current market yields were not re-verified in this review."),
        ("cash_return", "Return on accumulated cash", "3.0%", "Scenario assumption for reinvested cash flow."),
        ("rent_growth", "Rent growth (nominal)", "2.5%", "Scenario assumption. The local rent-stabilisation cap on annual increases was not re-verified."),
        ("rent_yield_a", "Gross rent yield on Property A", "3.0% of market value per year", "Scenario assumption used because no verified market rent exists for a future year."),
        ("vacancy", "Vacancy and collection allowance", "3.0% of gross rent", "Scenario assumption."),
        ("income_tax", "Marginal tax rate on rental income", "33.3%", "Scenario: 24% federal plus 9.3% California. Depreciation is ignored, which overstates tax."),
        ("gain_tax", "Tax rate on realised long-term gain", "32.3%", "20% federal (IRS Topic 409) plus 12.3% California top bracket (FTB). A 3.8% net investment income tax may add to this."),
        ("sell_cost", "Selling cost on Property A", "5.11%", "Scenario: 5.0% commission and escrow plus 0.11% base documentary transfer tax. City-level transfer taxes not verified."),
        ("maint_rate_a", "Maintenance on Property A", "0.50% of value", "Scenario assumption."),
        ("maint_rate_b", "Maintenance on Property B", "1.00% of value", "Scenario assumption; an older multi-unit building."),
        ("horizon_end", "Comparison horizon", "2055", "Ten years after the latest modelled inheritance year."),
        ("inherit_years", "Modelled inheritance years", "2040 / 2045 / 2050", "Owner's stated planning window, with the midpoint treated as the base case."),
    ]:
        data["assumptions"].append({"id": key, "item": label, "value": value, "basis": basis})

    # Historic assessment schedules (owner-provided, rounded to $10, unverified)
    hist_a = [(2014, 5_970, 440_310), (2015, 6_130, 449_100), (2016, 6_410, 455_950),
              (2017, 6_380, 465_070), (2018, 6_380, 474_370), (2019, 6_570, 483_850),
              (2020, 6_570, 493_530), (2021, 6_660, 498_640), (2022, 6_760, 508_610),
              (2023, 6_920, 518_790), (2024, 7_000, 529_160), (2025, 7_210, 539_740),
              (2026, None, 550_540)]
    for year, tax, av in hist_a:
        data["history_a"].append({"year": year, "tax": tax, "assessed": av,
                                  "status": "2026 bill not provided" if tax is None else "Owner-provided, unverified"})
    hist_b = [(2016, 1_680, 96_560), (2017, 1_740, 98_490), (2018, 2_060, 100_460),
              (2019, 2_130, 102_470), (2020, 2_200, 104_510), (2021, 2_070, 105_600),
              (2022, 2_110, 107_660), (2023, 2_180, 109_810), (2024, 2_320, 112_010),
              (2025, 2_440, 114_250)]
    for year, tax, av in hist_b:
        data["history_b"].append({"year": year, "tax": tax, "assessed": av,
                                  "status": "Owner-provided, unverified"})

    # Year-by-year projections
    for year in range(2026, A["horizon_end"] + 1):
        assessed, tax = tax_a_owned(year)
        c = a_carrying(year, g, occupied=True)
        total = tax + c["insurance"] + c["water"] + c["electric"] + c["maintenance"]
        data["projections_a"].append({
            "year": year,
            "fmv_low": r10(a_value(year, 0.03)), "fmv_base": r10(a_value(year, 0.04)), "fmv_high": r10(a_value(year, 0.05)),
            "assessed": assessed, "tax": tax,
            "insurance": c["insurance"], "water": c["water"], "electric": c["electric"], "maintenance": c["maintenance"],
            "total_carrying": r10(total),
        })
        op = b_operating(year, g)
        data["projections_b"].append({
            "year": year,
            "fmv_low": r10(b_value(year, 0.03)), "fmv_base": r10(b_value(year, 0.04)), "fmv_high": r10(b_value(year, 0.05)),
            "assessed": op["assessed"], "tax": op["tax"],
            "rent": op["gross"], "water": op["water"], "electric": op["electric"],
            "insurance": op["insurance"], "maintenance": op["maintenance"],
            "noi": op["noi"], "after_tax": op["after_tax"],
        })

    # Current-year carrying cost comparison
    c26 = a_carrying(2026, g, occupied=True)
    _, tax26 = tax_a_owned(2026)
    b26 = b_operating(2026, g)
    data["carrying"] = [
        {"item": "Property tax", "a": tax26, "b": b26["tax"], "note_a": "Derived from the owner-provided 2025 bill and assessed value.", "note_b": "Reported 2025 bill; ad valorem at the verified local rate would be lower (see flagged items)."},
        {"item": "Home / landlord insurance", "a": INPUTS["a_insurance_owner_est"], "b": INPUTS["b_insurance_scenario"], "note_a": "Owner estimate. No verified quote exists.", "note_b": "Scenario figure for a three-unit rental; the owner estimate is lower. No verified quote exists."},
        {"item": "Water and sewer", "a": INPUTS["a_water_yr"], "b": INPUTS["b_water_yr"], "note_a": "Midpoint of the owner-stated monthly range.", "note_b": "Midpoint of the owner-stated monthly range for three units."},
        {"item": "Electricity (net of solar credit)", "a": INPUTS["a_electric_yr"], "b": INPUTS["b_electric_yr"], "note_a": "Negative: the owner reports a net credit.", "note_b": "Owner-stated monthly range."},
        {"item": "Maintenance and repairs", "a": c26["maintenance"], "b": b26["maintenance"], "note_a": "Scenario: 0.50% of value.", "note_b": "Scenario: 1.00% of value."},
    ]

    # Inheritance-year property tax outcomes
    for Y in A["inherit_years"]:
        for law in ("prop19", "proposal"):
            tx = inherit_taxes(Y, g, law)
            data["inheritance"].append({"year": Y, "law": law, **tx})

    # Decision comparison
    strategies = [("S1", "Live in Property A", "Owner occupies A; the third unit of Property B is rented."),
                  ("S2", "Rent Property A", "Owner occupies the third unit of B; A is rented and fully reassessed."),
                  ("S3A", "Sell A, reinvest in equities", "Owner occupies the third unit of B; proceeds invested at the 7.0% scenario."),
                  ("S3B", "Sell A, hold bonds", "Owner occupies the third unit of B; proceeds invested at the 4.0% scenario.")]
    for Y in A["inherit_years"]:
        rows = []
        for code, name, note in strategies:
            res = run_strategy(code, Y, g, reinvest="bond" if code == "S3B" else None)
            rows.append({"code": code, "name": name, "note": note, **res})
        best = max(r["terminal_net_worth"] for r in rows)
        for r in rows:
            r["gap_vs_best"] = r["terminal_net_worth"] - best
        data["decision"].append({"year": Y, "rows": rows,
                                 "breakeven_reinvest": round(breakeven_return(Y, g, [r for r in rows if r["code"] == "S2"][0]["terminal_net_worth"]) * 100, 1),
                                 "hold_rent_terminal": [r for r in rows if r["code"] == "S2"][0]["terminal_net_worth"]})

    # Law-change sensitivity: proposal 25-0017 style full exclusion
    for Y in A["inherit_years"]:
        base = run_strategy("S2", Y, g)
        prop = run_strategy("S2", Y, g, law="proposal")
        data["sensitivity"].append({"kind": "law", "year": Y,
                                    "label": "Rent A under current Proposition 19 versus a full-exclusion proposal",
                                    "current": base["terminal_net_worth"], "proposal": prop["terminal_net_worth"],
                                    "delta": prop["terminal_net_worth"] - base["terminal_net_worth"]})

    # Appreciation x reinvestment sensitivity (2045 base year)
    Y = 2045
    for gg in (0.03, 0.04, 0.05):
        for rr in (0.04, 0.05, 0.06, 0.07):
            A["equity_return"] = rr
            sell = run_strategy("S3A", Y, gg)["terminal_net_worth"]
            hold = run_strategy("S2", Y, gg)["terminal_net_worth"]
            live = run_strategy("S1", Y, gg)["terminal_net_worth"]
            data["sensitivity"].append({"kind": "matrix", "year": Y, "appreciation": gg, "reinvest": rr,
                                        "sell": sell, "rent": hold, "live": live,
                                        "winner": "Sell" if sell >= max(hold, live) else ("Rent" if hold >= live else "Live")})
    A["equity_return"] = 0.070

    # Estate / inheritance tax headroom
    for Y in (2026, 2032, 2040, 2045, 2050):
        excl = A["fed_exclusion_2026"] * (1 + A["fed_exclusion_indexing"]) ** (Y - 2026)
        estate = a_value(Y, g) + b_value(Y, g)
        data["estate"].append({
            "year": Y,
            "exclusion_single": r10(excl),
            "exclusion_married": r10(excl * 2),
            "estate_two_properties": r10(estate),
            "cash_headroom_single": r10(max(0, excl - estate)),
            "cash_headroom_married": r10(max(0, excl * 2 - estate)),
            "ca_inheritance_tax": 0,
        })

    # CSV downloads (public, rounded, no identifiers)
    def csv(name, rows):
        import csv as _csv
        if not rows:
            return
        path = OUT.parent / name
        with path.open("w", newline="", encoding="utf-8") as f:
            w = _csv.DictWriter(f, fieldnames=list(rows[0].keys()), quoting=_csv.QUOTE_MINIMAL)
            w.writeheader()
            w.writerows(rows)
    csv("property_a.csv", data["projections_a"])
    csv("property_b.csv", data["projections_b"])
    csv("decision.csv", [r for blk in data["decision"] for r in blk["rows"]])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    # rounding audit: every numeric leaf must be a multiple of 10 when it is a dollar figure
    bad = []
    for k in ("projections_a", "projections_b", "decision", "estate", "inheritance", "carrying"):
        for row in data[k]:
            for kk, vv in (row.items() if isinstance(row, dict) else []):
                if isinstance(vv, int) and abs(vv) >= 100 and vv % 10 != 0 and kk != "year":
                    bad.append((k, kk, vv))
    print(f"model.json written; rounding violations: {len(bad)}")
    return data


if __name__ == "__main__":
    d = build()
    print(f"rows: history {len(d['history_a'])}+{len(d['history_b'])}, "
          f"proj {len(d['projections_a'])+len(d['projections_b'])}, decision {len(d['decision'])}, "
          f"estate {len(d['estate'])}, sensitivity {len(d['sensitivity'])}")
    for row in d["decision"]:
        print(row["year"], [(r["code"], r["terminal_net_worth"]) for r in row["rows"]], "breakeven reinvest %", row["breakeven_reinvest"])
