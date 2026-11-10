"""Projection and decision model for the inherited-property plan.

Pure standard-library Python. Every figure that leaves this module for publication is rounded
to the nearest $10. Inputs are read from plan/data/inputs_public.json, whose roll-derived
figures are privacy-rounded. An owner can re-run the same model offline on exact figures:

    python plan/model/model.py --inputs private/inputs.json --out private/model_outputs.json

(`private/` is git-ignored; nothing in it is ever published.)

Nothing in here is a verified fact. Rules of law used by the model are listed, with their official
sources, in plan/data/facts.json; everything else is a labelled assumption in
plan/data/assumptions.json.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_INPUTS = ROOT / "plan" / "data" / "inputs_public.json"
PUBLIC_OUT = ROOT / "plan" / "data" / "model_outputs.json"


def r10(x: float) -> int:
    """Round to the nearest $10 (half away from zero)."""
    return int((abs(x) + 5) // 10 * 10) * (1 if x >= 0 else -1)


def grow(x: float, rate: float, years: int) -> float:
    return x * (1 + rate) ** years


# --------------------------------------------------------------------------- rules of law

def prop19_addon(inp: dict, transfer_year: int, hpi: float) -> float:
    """The '$1 million' amount in force for a transfer in `transfer_year`.

    BOE Letter to Assessors 2025/009: $1,044,586 applies to transfers from 16 Feb 2025 to
    15 Feb 2027; it is then adjusted every second 16 February by the California House Price
    Index change for the single prior calendar year. `hpi` is the assumed yearly change.
    """
    first = inp["tax"]["prop19_next_adjustment_year"]
    steps = 0 if transfer_year < first else (transfer_year - first) // 2 + 1
    return inp["tax"]["prop19_addon_now"] * (1 + hpi) ** steps


def prop19_family_home_value(fbyv: float, market: float, addon: float) -> float:
    """New taxable value when the heir keeps the family home as a principal residence.

    BOE Prop 19 FAQ and LTA 2026/026: the excluded amount is the factored base year value plus
    the adjusted $1 million; any market value above that is added to the factored base year value.
    """
    return fbyv + max(0.0, market - (fbyv + addon))


def estate_exclusion(inp: dict, year: int) -> float:
    """Basic exclusion amount. 2026 and 2027 are published by the IRS; later years are projected
    at the model's inflation assumption because the amount is indexed for inflation."""
    known = {int(k): v for k, v in inp["tax"]["estate_exclusion"].items()}
    if year in known:
        return known[year]
    last = max(known)
    return known[last] * (1 + inp["economy"]["inflation"]) ** (year - last)


# --------------------------------------------------------------------------- status quo

def status_quo(inp: dict, last_year: int = 2055, hpi: float | None = None) -> list[dict]:
    """Year-by-year projection while the current owners keep both properties (no transfer)."""
    e, a, b = inp["economy"], inp["property_a"], inp["property_b"]
    hpi = e["home_appreciation"] if hpi is None else hpi
    y0 = inp["base_year"]
    rows = []
    for y in range(y0, last_year + 1):
        n = y - y0
        infl = (1 + e["inflation"]) ** n
        va, vb = grow(a["market_value"], hpi, n), grow(b["market_value"], hpi, n)
        ava = grow(a["assessed_value_base_year"], e["prop13_factor"], n)
        avb = grow(b["assessed_value_base_year"], e["prop13_factor"], n)
        tax_a = (ava - a["homeowners_exemption"]) * a["ad_valorem_rate"] + a["fixed_charges"] * infl
        tax_b = avb * b["ad_valorem_rate"] + b["fixed_charges"] * infl
        rent_b = b["rent_two_units_monthly"] * 12 * (1 + e["rent_control_share_of_cpi"] * e["inflation"]) ** n
        rows.append({
            "year": y,
            "a_value": r10(va), "a_assessed": r10(ava), "a_tax": r10(tax_a),
            "a_maintenance": r10(va * a["maintenance_pct_of_value"]),
            "a_water": r10(a["water"] * infl),
            "a_electricity": r10(a["electricity_credit"]) if y < inp["inheritance_years"][0] else None,
            "a_insurance": r10(a["insurance"] * infl),
            "b_value": r10(vb), "b_assessed": r10(avb), "b_tax": r10(tax_b),
            "b_maintenance": r10(vb * b["maintenance_pct_of_value"]),
            "b_water": r10(b["water"] * infl),
            "b_electricity": r10(b["electricity"] * infl),
            "b_insurance": r10(b["insurance"] * infl),
            "b_rent": r10(rent_b),
            "addon": r10(prop19_addon(inp, y, hpi)),
            "estate_exclusion": r10(estate_exclusion(inp, y)),
        })
    return rows


# --------------------------------------------------------------------------- scenarios

def scenario_set(inp: dict, t: int, hpi: float | None = None, stock: float | None = None,
                 rent_a: float | None = None, rent_third_unit: bool = True) -> dict:
    """Compare what the heir can do with Property A for an inheritance in year `t`.

    In every option the heir has one home: Property A in LIVE, the unrented unit of Property B
    otherwise. The two rented units of Property B behave identically in every option, so they are
    reported once (`b_common`) and left out of the comparison.
    """
    e, a, b, tx = inp["economy"], inp["property_a"], inp["property_b"], inp["tax"]
    hpi = e["home_appreciation"] if hpi is None else hpi
    stock = e["stock_return"] if stock is None else stock
    rent_a_m = a["market_rent_monthly"] if rent_a is None else rent_a
    y0, n_h, pi = inp["base_year"], inp["horizon_years"], e["inflation"]
    k0 = t - y0

    va_t, vb_t = grow(a["market_value"], hpi, k0), grow(b["market_value"], hpi, k0)
    fbyv_t = grow(a["assessed_value_base_year"], e["prop13_factor"], k0)
    addon = prop19_addon(inp, t, hpi)
    tv_live = prop19_family_home_value(fbyv_t, va_t, addon)
    tv_full = va_t
    side_rate = e["treasury_return"] * (1 - tx["treasury_interest_rate"])

    def infl(y):
        return (1 + pi) ** (y - y0)

    def a_costs(y, taxable_value_t, owner_occupied):
        j = y - t
        tv = grow(taxable_value_t, e["prop13_factor"], j)
        hox = a["homeowners_exemption"] if owner_occupied else 0
        tax = (tv - hox) * a["ad_valorem_rate"] + a["fixed_charges"] * infl(y)
        ins = a["insurance"] * infl(y)
        maint = grow(a["market_value"], hpi, y - y0) * a["maintenance_pct_of_value"]
        return tax, ins, maint

    def b_costs(y):
        j = y - t
        tax = grow(vb_t, e["prop13_factor"], j) * b["ad_valorem_rate"] + b["fixed_charges"] * infl(y)
        ins = b["insurance"] * infl(y)
        maint = grow(b["market_value"], hpi, y - y0) * b["maintenance_pct_of_value"]
        util = (b["water"] + b["electricity"]) * infl(y)
        return tax, ins, maint, util

    years = list(range(t, t + n_h))
    v_end = grow(a["market_value"], hpi, t + n_h - y0)
    sale_end = v_end * (1 - e["selling_cost"])
    rent_ctl = 1 + e["rent_control_share_of_cpi"] * pi

    out = {"year": t, "a_value": r10(va_t), "b_value": r10(vb_t), "a_fbyv": r10(fbyv_t),
           "addon": r10(addon), "a_taxable_live": r10(tv_live), "a_taxable_full": r10(tv_full),
           "a_tax_live_first": None, "a_tax_full_first": None, "options": {}}

    def finish(name, flows, terminal_asset, detail):
        side = 0.0
        for f in flows:
            side = side * (1 + side_rate) + f
        wealth = terminal_asset + side
        deflator = infl(t + n_h)
        out["options"][name] = {
            "first_year_cash": r10(flows[0]),
            "cumulative_cash": r10(sum(flows)),
            "terminal_asset": r10(terminal_asset),
            "wealth": r10(wealth),
            "wealth_today": r10(wealth / deflator),
            "raw_wealth": wealth,
            **detail,
        }

    # ---- LIVE: heir occupies A; B's third unit can be let ------------------------------------
    flows, first = [], {}
    third0 = b["third_unit_rent_monthly"] * 12 * infl(t)
    for y in years:
        tax, ins, maint = a_costs(y, tv_live, True)
        water = a["water"] * infl(y)
        f = -(tax + ins + maint + water)
        extra = 0.0
        if rent_third_unit:
            rent3 = third0 * rent_ctl ** (y - t) * (1 - e["vacancy"])
            bt, bi, bm, _ = b_costs(y)
            dep3 = vb_t * b["building_share"] / 3 / tx["depreciation_years"]
            taxable3 = max(0.0, rent3 - (bt + bi + bm) / 3 - dep3)
            extra = rent3 - tx["ordinary_rate"] * taxable3
        f += extra
        flows.append(f)
        if y == t:
            first = {"property_tax": r10(tax), "insurance": r10(ins), "maintenance": r10(maint),
                     "water": r10(water), "third_unit_rent_after_tax": r10(extra)}
            out["a_tax_live_first"] = r10(tax)
    gain = sale_end - va_t
    live_terminal = sale_end - tx["terminal_gain_rate"] * max(0.0, gain - tx["home_sale_exclusion"])
    finish("live", flows, live_terminal, {"first_year": first})

    # ---- RENT: heir occupies B's unit; A is let ---------------------------------------------
    flows, first, suspended, dep_total = [], {}, 0.0, 0.0
    dep_a = va_t * a["building_share"] / tx["depreciation_years"]
    rent0 = rent_a_m * 12 * infl(t)
    for y in years:
        tax, ins, maint = a_costs(y, tv_full, False)
        rent = rent0 * (1 + pi) ** (y - t) * (1 - e["vacancy"])
        taxable = rent - tax - ins - maint - dep_a
        dep_total += dep_a
        if taxable < 0:
            suspended += -taxable
            income_tax = 0.0
        else:
            used = min(suspended, taxable)
            suspended -= used
            income_tax = tx["ordinary_rate"] * (taxable - used)
        f = rent - tax - ins - maint - income_tax
        flows.append(f)
        if y == t:
            first = {"rent": r10(rent), "property_tax": r10(tax), "insurance": r10(ins),
                     "maintenance": r10(maint), "income_tax": r10(income_tax),
                     "depreciation": r10(dep_a)}
            out["a_tax_full_first"] = r10(tax)
    gain_total = sale_end - (va_t - dep_total)
    recapture = min(dep_total, max(0.0, gain_total))
    other_gain = max(0.0, gain_total - recapture - suspended)
    rent_terminal = sale_end - tx["recapture_rate"] * recapture - tx["terminal_gain_rate"] * other_gain
    finish("rent", flows, rent_terminal, {"first_year": first})

    # ---- SELL: heir occupies B's unit; A is sold in year t and the proceeds invested ----------
    proceeds = va_t * (1 - e["selling_cost"])
    d = e["stock_dividend_yield"]
    value, basis = proceeds, proceeds
    for _ in years:
        div_net = value * d * (1 - tx["dividend_rate"])
        value = value * (1 + stock - d) + div_net
        basis += div_net
    stock_terminal = value - tx["terminal_gain_rate"] * max(0.0, value - basis)
    finish("sell_stocks", [0.0] * n_h, stock_terminal,
           {"first_year": {"net_proceeds": r10(proceeds), "selling_costs": r10(va_t - proceeds),
                           "dividends_after_tax": r10(proceeds * d * (1 - tx["dividend_rate"]))}})
    bond_terminal = proceeds * (1 + side_rate) ** n_h
    finish("sell_treasuries", [0.0] * n_h, bond_terminal,
           {"first_year": {"net_proceeds": r10(proceeds), "selling_costs": r10(va_t - proceeds),
                           "interest_after_tax": r10(proceeds * side_rate)}})

    # ---- Property B, identical in every option ------------------------------------------------
    bt, bi, bm, bu = b_costs(t)
    rent_b = b["rent_two_units_monthly"] * 12 * rent_ctl ** k0
    out["b_common"] = {"rent": r10(rent_b), "property_tax": r10(bt), "insurance": r10(bi),
                       "maintenance": r10(bm), "utilities": r10(bu),
                       "net_before_income_tax": r10(rent_b - bt - bi - bm - bu),
                       "tax_before_transfer": r10(grow(b["assessed_value_base_year"], e["prop13_factor"], k0)
                                                  * b["ad_valorem_rate"] + b["fixed_charges"] * infl(t))}
    best = max(out["options"], key=lambda k: out["options"][k]["raw_wealth"])
    out["best"] = best
    for k, o in out["options"].items():
        o["gap_to_best"] = r10(o["raw_wealth"] - out["options"][best]["raw_wealth"])
    return out


def needs_home_set(inp: dict, t: int, hpi: float | None = None, stock: float | None = None,
                   rent_a: float | None = None) -> dict:
    """Second framing: the heir needs a family home like Property A.

    LIVE keeps Property A as that home. SELL sells it, invests the proceeds and pays rent for a
    comparable home out of the portfolio every year (rent is paid from after-tax money). Property B
    is fully let in both options, so it drops out of the comparison.
    """
    e, a, tx = inp["economy"], inp["property_a"], inp["tax"]
    hpi = e["home_appreciation"] if hpi is None else hpi
    stock = e["stock_return"] if stock is None else stock
    rent_a_m = a["market_rent_monthly"] if rent_a is None else rent_a
    y0, n_h, pi = inp["base_year"], inp["horizon_years"], e["inflation"]
    k0 = t - y0
    va_t = grow(a["market_value"], hpi, k0)
    fbyv_t = grow(a["assessed_value_base_year"], e["prop13_factor"], k0)
    tv_live = prop19_family_home_value(fbyv_t, va_t, prop19_addon(inp, t, hpi))
    side_rate = e["treasury_return"] * (1 - tx["treasury_interest_rate"])
    deflator = (1 + pi) ** (t + n_h - y0)

    side, first_cost = 0.0, 0.0
    for y in range(t, t + n_h):
        infl = (1 + pi) ** (y - y0)
        tv = grow(tv_live, e["prop13_factor"], y - t)
        cost = ((tv - a["homeowners_exemption"]) * a["ad_valorem_rate"] + a["fixed_charges"] * infl
                + a["insurance"] * infl + grow(a["market_value"], hpi, y - y0) * a["maintenance_pct_of_value"]
                + a["water"] * infl)
        side = side * (1 + side_rate) - cost
        first_cost = cost if y == t else first_cost
    sale_end = grow(a["market_value"], hpi, t + n_h - y0) * (1 - e["selling_cost"])
    live = sale_end - tx["terminal_gain_rate"] * max(0.0, sale_end - va_t - tx["home_sale_exclusion"]) + side

    proceeds = va_t * (1 - e["selling_cost"])
    rent0 = rent_a_m * 12 * (1 + pi) ** k0
    d = e["stock_dividend_yield"]
    value, basis, bond = proceeds, proceeds, proceeds
    for j in range(n_h):
        rent = rent0 * (1 + pi) ** j
        div_net = value * d * (1 - tx["dividend_rate"])
        value = value * (1 + stock - d) + div_net
        basis += div_net
        gain_frac = max(0.0, 1 - basis / value) if value > 0 else 0.0
        gross = rent / (1 - tx["dividend_rate"] * gain_frac)
        basis -= gross * (basis / value) if value > 0 else 0.0
        value -= gross
        bond = bond * (1 + side_rate) - rent
    stocks = value - tx["terminal_gain_rate"] * max(0.0, value - basis)
    res = {"year": t,
           "live": {"wealth": r10(live), "wealth_today": r10(live / deflator), "first_year_cash": r10(-first_cost)},
           "sell_stocks": {"wealth": r10(stocks), "wealth_today": r10(stocks / deflator), "first_year_cash": r10(-rent0)},
           "sell_treasuries": {"wealth": r10(bond), "wealth_today": r10(bond / deflator), "first_year_cash": r10(-rent0)},
           "first_year_rent": r10(rent0), "raw": {"live": live, "sell_stocks": stocks, "sell_treasuries": bond}}
    res["best"] = max(res["raw"], key=res["raw"].get)
    return res


def bisect(fn, lo, hi, iters=60):
    flo = fn(lo)
    for _ in range(iters):
        mid = (lo + hi) / 2
        fm = fn(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def break_evens(inp: dict, t: int) -> dict:
    """Two numbers that do not depend on the unverified assumptions they solve for."""
    def gap_stock(rate):
        s = scenario_set(inp, t, stock=rate)["options"]
        return s["sell_stocks"]["raw_wealth"] - s["live"]["raw_wealth"]

    def gap_rent(rent):
        s = scenario_set(inp, t, rent_a=rent)["options"]
        return s["rent"]["raw_wealth"] - s["sell_treasuries"]["raw_wealth"]

    def gap_rent_stock(rent):
        s = scenario_set(inp, t, rent_a=rent)["options"]
        return s["rent"]["raw_wealth"] - s["sell_stocks"]["raw_wealth"]

    def gap_stock_home(rate):
        s = needs_home_set(inp, t, stock=rate)["raw"]
        return s["sell_stocks"] - s["live"]

    res = {}
    res["stock_return_sell_equals_live"] = round(bisect(gap_stock, 0.0, 0.20) * 100, 1)
    res["stock_return_sell_equals_live_needs_home"] = round(bisect(gap_stock_home, 0.0, 0.20) * 100, 1)
    y_infl = (1 + inp["economy"]["inflation"]) ** (t - inp["base_year"])
    for key, fn in (("rent_equals_sell_treasuries", gap_rent), ("rent_equals_sell_stocks", gap_rent_stock)):
        if fn(0) > 0:
            res[key] = 0
        elif fn(60000) < 0:
            res[key] = None
        else:
            res[key] = r10(bisect(fn, 0, 60000))
        res[key + "_in_year_dollars"] = None if res[key] is None else r10(res[key] * y_infl)
    return res


def estate_headroom(inp: dict, years: list[int]) -> list[dict]:
    a, b, e = inp["property_a"], inp["property_b"], inp["economy"]
    rows = []
    for y in years:
        n = y - inp["base_year"]
        props = grow(a["market_value"] + b["market_value"], e["home_appreciation"], n)
        excl = estate_exclusion(inp, y)
        rows.append({"year": y, "exclusion": r10(excl), "two_exclusions": r10(2 * excl),
                     "properties": r10(props), "headroom_one": r10(excl - props),
                     "headroom_two": r10(2 * excl - props),
                     "tax_per_million_over": r10(1_000_000 * inp["tax"]["estate_rate"]),
                     "projected": y not in {int(k) for k in inp["tax"]["estate_exclusion"]}})
    return rows


def run(inp: dict) -> dict:
    e = inp["economy"]
    res = {"inputs": inp, "status_quo": status_quo(inp), "scenarios": {}, "needs_home": {},
           "break_even": {}, "sensitivity": [], "after_inheritance": {}}
    for t in inp["inheritance_years"]:
        res["scenarios"][str(t)] = scenario_set(inp, t)
        nh = needs_home_set(inp, t)
        nh.pop("raw")
        res["needs_home"][str(t)] = nh
        res["break_even"][str(t)] = break_evens(inp, t)
    mid = inp["inheritance_years"][len(inp["inheritance_years"]) // 2]
    cases = [("Base case", {}),
             ("Home prices rise 2.0% a year", {"hpi": e["home_appreciation_low"]}),
             ("Home prices rise 4.9% a year", {"hpi": e["home_appreciation_high"]}),
             ("Stocks return 5.0% a year", {"stock": e["stock_return_low"]}),
             ("Stocks return 9.0% a year", {"stock": e["stock_return_high"]}),
             ("Property A rents for $4,500 a month", {"rent_a": 4500}),
             ("Property A rents for $9,000 a month", {"rent_a": 9000}),
             ("Home prices rise 4.9% and stocks return 5.0%", {"hpi": e["home_appreciation_high"], "stock": e["stock_return_low"]}),
             ("Third unit of Property B left empty", {"rent_third_unit": False})]
    for label, kw in cases:
        s = scenario_set(inp, mid, **kw)
        res["sensitivity"].append({"case": label, "best": s["best"],
                                   **{k: v["wealth_today"] for k, v in s["options"].items()}})
    res["sensitivity_year"] = mid
    res["needs_home_sensitivity"] = []
    for label, kw in cases[:-1]:
        nh = needs_home_set(inp, mid, **kw)
        res["needs_home_sensitivity"].append({"case": label, "best": nh["best"],
                                              **{k: nh[k]["wealth_today"] for k in ("live", "sell_stocks", "sell_treasuries")}})
    res["estate"] = estate_headroom(inp, [2026, 2027, 2030, 2035, 2040, 2045, 2050])

    # Year-by-year view after an inheritance in the middle year, for each use of Property A.
    y0, a = inp["base_year"], inp["property_a"]
    sc = res["scenarios"][str(mid)]
    rows = []
    for y in range(mid, mid + 11):
        j, infl = y - mid, (1 + e["inflation"]) ** (y - y0)
        tv_l = grow(sc["a_taxable_live"], e["prop13_factor"], j)
        tv_f = grow(sc["a_taxable_full"], e["prop13_factor"], j)
        fixed = a["fixed_charges"] * infl
        rows.append({"year": y, "a_value": r10(grow(a["market_value"], e["home_appreciation"], y - y0)),
                     "taxable_live": r10(tv_l), "tax_live": r10((tv_l - a["homeowners_exemption"]) * a["ad_valorem_rate"] + fixed),
                     "taxable_full": r10(tv_f), "tax_full": r10(tv_f * a["ad_valorem_rate"] + fixed),
                     "saving": r10((tv_f - tv_l + a["homeowners_exemption"]) * a["ad_valorem_rate"])})
    res["after_inheritance"] = {"year": mid, "rows": rows}
    for s in res["scenarios"].values():
        for o in s["options"].values():
            o.pop("raw_wealth", None)
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", default=str(PUBLIC_INPUTS))
    ap.add_argument("--out", default=str(PUBLIC_OUT))
    args = ap.parse_args()
    inp = json.loads(Path(args.inputs).read_text(encoding="utf-8"))
    res = run(copy.deepcopy(inp))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print(f"model written to {args.out}")


if __name__ == "__main__":
    main()
