"""Deterministic model for the anonymised quantitative decision edition.

Reads  : assets/data/inputs.json, assets/data/series.json
Writes : assets/data/model.json

No network access. No randomness. Every published dollar figure is rounded to
the nearest $10 with money10(); every percentage with pct().
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "data"
INPUTS = json.loads((DATA / "inputs.json").read_text(encoding="utf-8"))
SERIES = json.loads((DATA / "series.json").read_text(encoding="utf-8"))

A = INPUTS["property_a"]
B = INPUTS["property_b"]
V = INPUTS["verified_parameters"]
ASM = INPUTS["assumptions"]

INFL = ASM["inflation"]["baseline"]


# ---------------------------------------------------------------- rounding ---
def money10(x: float) -> int:
    """Round to the nearest $10, halves up, as the owner instructed."""
    return int((abs(x) + 5.0) // 10 * 10) * (1 if x >= 0 else -1)


def pct(x: float, places: int = 2) -> float:
    return round(x * 100.0, places)


# ------------------------------------------------------------ tax bill fit ---
def _diagnose(rows, rate: float, infl: float):
    """Split a bill into ad valorem and fixed parts at a chosen rate."""
    base_year = max(int(r["year"]) for r in rows if r.get("bill"))
    implied = []
    for r in rows:
        if not r.get("bill"):
            continue
        implied.append((int(r["year"]),
                        float(r["bill"]) - rate * float(r["assessed"])))
    implied.sort()
    fixed_base = implied[-1][1]
    residuals = []
    worst_year, worst_delta = None, 0.0
    for y, fx in implied:
        pred = rate * float(next(r["assessed"] for r in rows if int(r["year"]) == y)) \
            + fixed_base * (1 + infl) ** (y - base_year)
        actual = float(next(r["bill"] for r in rows if int(r["year"]) == y))
        delta = actual - pred
        residuals.append(delta)
        if abs(delta) > abs(worst_delta):
            worst_year, worst_delta = y, delta
    span = implied[-1][0] - implied[0][0]
    growth = ((implied[-1][1] / implied[0][1]) ** (1 / span) - 1) if span and implied[0][1] > 0 else 0.0
    return {
        "rate": rate,
        "fixed_base": fixed_base,
        "base_year": base_year,
        "implied_fixed_first": implied[0][1],
        "implied_fixed_last": implied[-1][1],
        "implied_fixed_growth": growth,
        "worst_year": worst_year,
        "worst_delta": worst_delta,
        "max_abs_residual": max(abs(d) for d in residuals),
        "n": len(implied),
        "identification_note": "The rate is not fitted from the data. Assessed value and the fixed part of the bill both grow at about 2% a year, so the data cannot separate them: any rate in a wide band fits almost equally well. The rate is therefore taken from published law or stated as an assumption.",
    }


def fit_bill(rows: list[dict], rate: float, infl: float = INFL):
    return _diagnose(rows, rate, infl)


def bill_for(assessed: float, fit: dict, year: int, infl: float = INFL) -> float:
    return fit["rate"] * assessed + fit["fixed_base"] * (1 + infl) ** (year - fit["base_year"])


# --------------------------------------------------------------- projection --
def project_roll(rows: list[dict], value_2026: float, g: float, infl: float,
                 cap: float, horizon: int, fit: dict) -> list[dict]:
    start_year = max(int(r["year"]) for r in rows)
    av = float([r["assessed"] for r in rows if int(r["year"]) == start_year][0])
    out = []
    for k in range(0, horizon + 1):
        year = 2026 + k
        value = value_2026 * (1 + g) ** k
        bill = bill_for(av, fit, year, infl)
        out.append({
            "year": year,
            "value": money10(value),
            "assessed": money10(av),
            "bill": money10(bill),
            "effective_rate": round(bill / av * 100.0, 3) if av else None,
        })
        av *= (1 + cap)
    return out


def roll_table(rows: list[dict], fit: dict, infl: float = INFL) -> list[dict]:
    """The owner's roll with the fitted bill beside the actual bill."""
    out = []
    have = [r for r in rows if r.get("bill")]
    for r in rows:
        y = int(r["year"])
        fitted = bill_for(float(r["assessed"]), fit, y, infl) if have else None
        out.append({
            "year": y,
            "assessed": money10(r["assessed"]),
            "bill": money10(r["bill"]) if r.get("bill") else None,
            "fitted": money10(fitted) if fitted is not None else None,
            "residual": money10(r["bill"] - fitted) if r.get("bill") and fitted is not None else None,
        })
    return out


# ------------------------------------------------------------------ paths ----
def sale_proceeds(price: float, basis: float, sell_pct: float, gain_rate: float,
                  recapture_rate: float, depreciation: float, exclusion: float = 0.0):
    costs = price * sell_pct
    net_before_tax = price - costs
    total_gain = max(0.0, net_before_tax - basis)
    recapture = min(depreciation, total_gain)
    capital = max(0.0, total_gain - recapture)
    taxable_capital = max(0.0, capital - exclusion)
    tax = taxable_capital * gain_rate + recapture * recapture_rate
    return {
        "price": money10(price),
        "costs": money10(costs),
        "basis": money10(basis),
        "gain": money10(total_gain),
        "recapture": money10(recapture),
        "exclusion": money10(exclusion),
        "tax": money10(tax),
        "net": money10(net_before_tax - tax),
    }


def carrying_costs(value: float, cost_base: float, maint_pct: float, infl: float,
                   horizon: int, start_mult: float = 1.0) -> float:
    tot = 0.0
    for j in range(horizon):
        tot += (cost_base * start_mult + maint_pct * value) * (1 + infl) ** j
    return tot


def tax_path(start_av: float, fit: dict, start_year: int, infl: float,
             horizon: int, cap: float = 0.02) -> float:
    av = start_av
    tot = 0.0
    for j in range(horizon):
        tot += bill_for(av, fit, start_year + j, infl)
        av *= (1 + cap)
    return tot


def run_paths(inherit_year: int, g: float, infl: float, eq: float, drag: float,
              tsy: float, cap_growth: float, sell_pct: float, horizon: int,
              gain_rate: float, rec_rate: float, exclusion: float,
              fixed_growth: float, fit_a: dict, cost_a_base: float,
              maint_live: float, maint_rent: float) -> dict:
    k = inherit_year - 2026
    value_at_death = A["estimated_market_value_2026"] * (1 + g) ** k
    byv = A["roll"][0]["assessed"] * (1 + 0.02) ** k
    cap = V["prop19_value_cap_2025_2027"]["value"] * (1 + cap_growth) ** (inherit_year - 2025)
    # With the exclusion: new taxable value = prior taxable value
    #                     + (market value - prior taxable value - cap)
    taxable_live = byv + max(0.0, value_at_death - (byv + cap))
    taxable_rent = value_at_death

    fit_T = dict(fit_a)
    fit_T["fixed_base"] = fit_a["fixed_base"] * (1 + fixed_growth) ** (inherit_year - fit_a["base_year"])

    terminal_price = value_at_death * (1 + g) ** horizon

    # Path 1 and 2: sell at inheritance, invest
    sale = sale_proceeds(value_at_death, value_at_death, sell_pct, gain_rate, rec_rate, 0.0)
    inv_eq = sale["net"] * (1 + eq - drag) ** horizon
    inv_ts = sale["net"] * (1 + tsy) ** horizon

    # Path 3: live in it for the whole horizon, then sell
    tax_live = tax_path(taxable_live, fit_T, inherit_year, infl, horizon)
    cost_live = carrying_costs(value_at_death, cost_a_base, maint_live, infl, horizon)
    live = sale_proceeds(terminal_price, value_at_death, sell_pct, gain_rate, rec_rate,
                         0.0, exclusion)

    # Path 4: let it out from the start, then sell
    tax_rent = tax_path(taxable_rent, fit_T, inherit_year, infl, horizon)
    cost_rent = carrying_costs(value_at_death, cost_a_base, maint_rent, infl, horizon)
    deprec = min(0.8 * value_at_death, 0.8 * value_at_death / 27.5 * horizon)
    rent_sale = sale_proceeds(terminal_price, value_at_death - deprec, sell_pct,
                              gain_rate, rec_rate, deprec)

    # Path 5: live in it for two years, then let it out for the rest
    tax_h1 = tax_path(taxable_live, fit_T, inherit_year, infl, 2)
    fit_T2 = dict(fit_T)
    fit_T2["fixed_base"] = fit_T["fixed_base"] * (1 + fixed_growth) ** 2
    av_after = taxable_rent * 1.02 ** 2
    tax_h2 = tax_path(av_after, fit_T2, inherit_year + 2, infl, horizon - 2)
    cost_h = carrying_costs(value_at_death, cost_a_base, maint_rent, infl, horizon)
    deprec_h = min(0.8 * value_at_death,
                   0.8 * value_at_death / 27.5 * (horizon - 2))
    hybrid_sale = sale_proceeds(terminal_price, value_at_death - deprec_h, sell_pct,
                                gain_rate, rec_rate, deprec_h, exclusion)

    return {
        "inherit_year": inherit_year,
        "value_at_death": money10(value_at_death),
        "factored_base_year_value": money10(byv),
        "prop19_cap": money10(cap),
        "prop19_excess": money10(max(0.0, value_at_death - (byv + cap))),
        "taxable_if_live": money10(taxable_live),
        "taxable_if_rent": money10(taxable_rent),
        "bill_today_projected": money10(bill_for(byv, fit_a, inherit_year, infl)),
        "bill_if_live_year1": money10(bill_for(taxable_live, fit_T, inherit_year, infl)),
        "bill_if_rent_year1": money10(bill_for(taxable_rent, fit_T, inherit_year, infl)),
        "terminal_price": money10(terminal_price),
        "paths": {
            "sell_equities": {"terminal": money10(inv_eq), "outflow": 0,
                              "start": sale["net"], "sale": sale},
            "sell_treasury": {"terminal": money10(inv_ts), "outflow": 0,
                              "start": sale["net"], "sale": sale},
            "live_in": {"terminal": money10(live["net"]),
                        "outflow": money10(tax_live + cost_live),
                        "tax_total": money10(tax_live),
                        "cost_total": money10(cost_live), "sale": live},
            "rent_out": {"terminal": money10(rent_sale["net"]),
                         "outflow": money10(tax_rent + cost_rent),
                         "tax_total": money10(tax_rent),
                         "cost_total": money10(cost_rent),
                         "depreciation": money10(deprec), "sale": rent_sale},
            "live_then_rent": {"terminal": money10(hybrid_sale["net"]),
                               "outflow": money10(tax_h1 + tax_h2 + cost_h),
                               "tax_total": money10(tax_h1 + tax_h2),
                               "cost_total": money10(cost_h),
                               "depreciation": money10(deprec_h),
                               "sale": hybrid_sale},
        },
    }


def annuity(present: float, rate: float, years: int) -> float:
    if rate <= 0:
        return present / years
    return present * rate / (1 - (1 + rate) ** (-years))


def breakeven_rent(inherit_year: int, g: float, infl: float, eq: float, drag: float,
                   cap_growth: float, sell_pct: float, horizon: int, gain_rate: float,
                   rec_rate: float, fixed_growth: float, fit_a: dict,
                   cost_a_base: float, maint_rent: float, target: float):
    """Initial annual rent that makes letting the house out match the target."""
    k = inherit_year - 2026
    value_at_death = A["estimated_market_value_2026"] * (1 + g) ** k
    fit_T = dict(fit_a)
    fit_T["fixed_base"] = fit_a["fixed_base"] * (1 + fixed_growth) ** (inherit_year - fit_a["base_year"])

    def rent_terminal(r0: float) -> float:
        cash = 0.0
        av = value_at_death
        for j in range(horizon):
            net = (r0 * (1 + infl) ** j
                   - (cost_a_base + maint_rent * value_at_death) * (1 + infl) ** j
                   - bill_for(av, fit_T, inherit_year + j, infl))
            cash += net * (1 + eq - drag) ** (horizon - 1 - j)
            av *= 1.02
        deprec = min(0.8 * value_at_death, 0.8 * value_at_death / 27.5 * horizon)
        price = value_at_death * (1 + g) ** horizon
        s = sale_proceeds(price, value_at_death - deprec, sell_pct, gain_rate, rec_rate, deprec)
        return cash + s["net"]

    lo, hi = 0.0, 3_000_000.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if rent_terminal(mid) < target:
            lo = mid
        else:
            hi = mid
    return money10((lo + hi) / 2)


def breakeven_return(inherit_year: int, g: float, cap_growth: float, sell_pct: float,
                     horizon: int, gain_rate: float, rec_rate: float, target: float):
    k = inherit_year - 2026
    value_at_death = A["estimated_market_value_2026"] * (1 + g) ** k
    sale = sale_proceeds(value_at_death, value_at_death, sell_pct, gain_rate, rec_rate, 0.0)
    lo, hi = 0.0, 0.60
    for _ in range(300):
        mid = (lo + hi) / 2
        if sale["net"] * (1 + mid) ** horizon < target:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2 * 100.0, 2)


def sensitivity(target_year: int):
    """Terminal value of each path across a growth/return grid."""
    rows = []
    for g in (ASM["house_growth"]["low"], ASM["house_growth"]["baseline"],
              ASM["house_growth"]["high"]):
        for eq in (ASM["equity_return_nominal_gross"]["low"],
                   ASM["equity_return_nominal_gross"]["baseline"],
                   ASM["equity_return_nominal_gross"]["high"]):
            res = run_paths(
                inherit_year=target_year, g=g, infl=ASM["inflation"]["baseline"],
                eq=eq, drag=ASM["equity_tax_drag"]["baseline"],
                tsy=ASM["treasury_yield_nominal"]["baseline"],
                cap_growth=ASM["prop19_cap_growth"]["baseline"],
                sell_pct=ASM["selling_cost_pct"]["baseline"],
                horizon=ASM["horizon_years"],
                gain_rate=ASM["combined_gain_tax_rate"]["baseline"],
                rec_rate=ASM["depreciation_recapture_rate"]["baseline"],
                exclusion=V["section121_exclusion_single"]["value"],
                fixed_growth=INFL,
                fit_a=FIT_A,
                cost_a_base=COST_A_BASE,
                maint_live=A["annual_costs"]["maintenance_pct_owner_occupied"]["value"],
                maint_rent=A["annual_costs"]["maintenance_pct_rental"]["value"])
            terms = {k: v["terminal"] for k, v in res["paths"].items()}
            best = max(terms, key=terms.get)
            rows.append({"house_growth": pct(g, 1), "equity_return": pct(eq, 1),
                         **{k: v for k, v in terms.items()}, "best": best})
    return rows


def breakeven_house_growth(inherit_year: int, eq: float, drag: float, cap_growth: float,
                           sell_pct: float, horizon: int, gain_rate: float,
                           rec_rate: float, exclusion: float, maint_live: float):
    """House growth at which living in the home matches selling and investing."""
    def live_gap(g: float) -> float:
        res = run_paths(inherit_year=inherit_year, g=g, infl=ASM["inflation"]["baseline"],
                        eq=eq, drag=drag, tsy=ASM["treasury_yield_nominal"]["baseline"],
                        cap_growth=cap_growth, sell_pct=sell_pct, horizon=horizon,
                        gain_rate=gain_rate, rec_rate=rec_rate, exclusion=exclusion,
                        fixed_growth=ASM["fixed_charge_growth"]["baseline"], fit_a=FIT_A,
                        cost_a_base=COST_A_BASE, maint_live=maint_live,
                        maint_rent=A["annual_costs"]["maintenance_pct_rental"]["value"])
        return res["paths"]["live_in"]["terminal"] - res["paths"]["sell_equities"]["terminal"]
    lo, hi = 0.0, 0.30
    if live_gap(hi) < 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if live_gap(mid) < 0:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2 * 100.0, 2)



# --------------------------------------------------------------- replays ----
def growth_path(values: dict, first: int, last: int) -> dict:
    out = {}
    for y in range(first, last + 1):
        a, b = str(y - 1), str(y)
        if a in values and b in values and values[a]:
            out[y] = values[b] / values[a] - 1.0
    return out


def historical_replay(span: int = 30):
    """Replay every full window of the real record."""
    cpi_v = SERIES["cpi"]["values"]
    hpi_a = SERIES["hpi_a"]["values"]
    hpi_b = SERIES["hpi_b"]["values"]
    gs10 = SERIES["gs10"]["values"]
    rows = []
    first = max(int(min(cpi_v)), int(min(hpi_a)) + 1)
    last = min(int(max(cpi_v)), int(max(hpi_a)), int(max(gs10)))
    for start in range(first, last - span + 2):
        end = start + span - 1
        if str(end) not in cpi_v or str(end) not in hpi_a or str(end) not in gs10:
            continue
        cpi_g = growth_path(cpi_v, start, end)
        hpi_g = growth_path(hpi_a, start, end)
        hpi_gb = growth_path(hpi_b, start, end)
        gs = {y: gs10[str(y)] / 100.0 for y in range(start, end + 1) if str(y) in gs10}
        if len(cpi_g) < span - 1 or len(hpi_g) < span - 1 or len(gs) < span - 1:
            continue
        val = A["estimated_market_value_2026"]
        for y in range(start, end + 1):
            if y in hpi_g:
                val *= (1 + hpi_g[y])
        val_b = B["estimated_market_value_2026"]
        for y in range(start, end + 1):
            if y in hpi_gb:
                val_b *= (1 + hpi_gb[y])
        cpi_mult = 1.0
        for y in range(start, end + 1):
            if y in cpi_g:
                cpi_mult *= (1 + cpi_g[y])
        bond_mult = 1.0
        for y in range(start, end + 1):
            if y in gs:
                bond_mult *= (1 + gs[y])
        # property tax bill on the inherited home if it had been reassessed at
        # the start of the window and held for the whole window
        av = A["estimated_market_value_2026"]
        tax_reset = 0.0
        for y in range(start, end + 1):
            tax_reset += bill_for(av, FIT_A, 2026 + (y - start), INFL)
            av *= 1.02
        av2 = A["roll"][0]["assessed"]
        tax_kept = 0.0
        for y in range(start, end + 1):
            tax_kept += bill_for(av2, FIT_A, 2026 + (y - start), INFL)
            av2 *= 1.02
        rows.append({
            "start": start, "end": end,
            "a_value": money10(val),
            "a_value_real": money10(val / cpi_mult),
            "b_value": money10(val_b),
            "b_value_real": money10(val_b / cpi_mult),
            "cpi_multiple": round(cpi_mult, 2),
            "cpi_cagr": round(cpi_mult ** (1 / span) * 100 - 100, 2),
            "a_cagr": round((val / A["estimated_market_value_2026"]) ** (1 / span) * 100 - 100, 2),
            "bond_multiple": round(bond_mult, 2),
            "bond_cagr": round(bond_mult ** (1 / span) * 100 - 100, 2),
            "down_years_a": sum(1 for y in hpi_g.values() if y < 0),
            "worst_year_a": pct(min(hpi_g.values()), 1),
            "best_year_a": pct(max(hpi_g.values()), 1),
            "tax_if_reset": money10(tax_reset),
            "tax_if_kept": money10(tax_kept),
        })
    return rows


def regime_stress():
    cpi_v = SERIES["cpi"]["values"]
    hpi_a = SERIES["hpi_a"]["values"]
    gs10_v = SERIES["gs10"]["values"]

    def avg_growth(series, a, b):
        g = growth_path(series, a, b)
        vals = list(g.values())
        return sum(vals) / len(vals) if vals else 0.0

    def avg_level(series, a, b):
        vals = [series[str(y)] for y in range(a, b + 1) if str(y) in series]
        return sum(vals) / len(vals) if vals else 0.0

    regimes = [
        {
            "key": "stagflation",
            "name": "Great Inflation repeat",
            "analogue": "1965-1982, described by the Federal Reserve as the defining macroeconomic period of the second half of the twentieth century",
            "src": ["frh_great_inflation", "fred_cpi", "fred_gs10", "fred_hpi_a"],
            "derived": True,
            "cpi": pct(avg_growth(cpi_v, 1977, 1981), 1),
            "house": pct(avg_growth(hpi_a, 1977, 1981), 1),
            "treasury": round(avg_level(gs10_v, 1977, 1981), 2),
            "window": "1977-1981 averages computed from the verified series",
        },
        {
            "key": "slump",
            "name": "A long house price slump",
            "analogue": "1989-1996 in Property A's metropolitan area",
            "src": ["fred_hpi_a", "fred_hpi_b", "fred_cpi"],
            "derived": True,
            "cpi": pct(avg_growth(cpi_v, 1990, 1996), 1),
            "house": pct(avg_growth(hpi_a, 1990, 1996), 1),
            "treasury": round(avg_level(gs10_v, 1990, 1996), 2),
            "window": "1990-1996 averages computed from the verified series",
        },
        {
            "key": "crash",
            "name": "A financial crisis crash",
            "analogue": "2007-2011",
            "src": ["fred_hpi_a", "fred_hpi_b", "fred_gs10", "frh_great_recession"],
            "derived": True,
            "cpi": pct(avg_growth(cpi_v, 2007, 2011), 1),
            "house": pct(avg_growth(hpi_a, 2007, 2011), 1),
            "treasury": round(avg_level(gs10_v, 2007, 2011), 2),
            "window": "2007-2011 averages computed from the verified series",
        },
        {
            "key": "burst",
            "name": "A fast inflation burst then a rate shock",
            "analogue": "2021-2023",
            "src": ["fred_cpi", "fred_gs10", "nyfed_covid"],
            "derived": True,
            "cpi": pct(avg_growth(cpi_v, 2021, 2023), 1),
            "house": pct(avg_growth(hpi_a, 2021, 2023), 1),
            "treasury": round(avg_level(gs10_v, 2021, 2023), 2),
            "window": "2021-2023 averages computed from the verified series",
        },
        {
            "key": "flat",
            "name": "House prices flat for the whole horizon",
            "analogue": "None. A stress case, not a historical analogue.",
            "src": [],
            "derived": False,
            "cpi": 2.5, "house": 0.0, "treasury": 4.7,
            "window": "Hypothetical",
        },
        {
            "key": "deflation",
            "name": "Low inflation and falling nominal house prices",
            "analogue": "None. A stress case, not a historical analogue.",
            "src": [],
            "derived": False,
            "cpi": 0.5, "house": -1.0, "treasury": 2.0,
            "window": "Hypothetical",
        },
    ]
    return regimes


def run_regime(regime: dict, horizon: int):
    g = regime["house"] / 100.0
    infl = regime["cpi"] / 100.0
    tsy = regime["treasury"] / 100.0
    res = run_paths(
        inherit_year=2045, g=g, infl=infl,
        eq=ASM["equity_return_nominal_gross"]["baseline"],
        drag=ASM["equity_tax_drag"]["baseline"], tsy=tsy,
        cap_growth=ASM["prop19_cap_growth"]["baseline"],
        sell_pct=ASM["selling_cost_pct"]["baseline"], horizon=horizon,
        gain_rate=ASM["combined_gain_tax_rate"]["baseline"],
        rec_rate=ASM["depreciation_recapture_rate"]["baseline"],
        exclusion=V["section121_exclusion_single"]["value"],
        fixed_growth=ASM["fixed_charge_growth"]["baseline"], fit_a=FIT_A, cost_a_base=COST_A_BASE,
        maint_live=A["annual_costs"]["maintenance_pct_owner_occupied"]["value"],
        maint_rent=A["annual_costs"]["maintenance_pct_rental"]["value"])
    cpi_mult = (1 + infl) ** horizon
    return {
        "terminal": {k: v["terminal"] for k, v in res["paths"].items()},
        "terminal_real": {k: money10(v["terminal"] / cpi_mult) for k, v in res["paths"].items()},
        "outflow": {k: v.get("outflow", 0) for k, v in res["paths"].items()},
        "value_at_death": res["value_at_death"],
        "bill_if_live_year1": res["bill_if_live_year1"],
        "bill_if_rent_year1": res["bill_if_rent_year1"],
        "best": max(res["paths"], key=lambda k: res["paths"][k]["terminal"]),
    }


# ------------------------------------------------------------ estate tax ----
def estate_scenarios():
    excl_2026 = V["federal_basic_exclusion_2026"]["value"]
    rows = []
    for total in [5_000_000, 10_000_000, 15_000_000, 20_000_000, 25_000_000,
                  30_000_000, 40_000_000, 50_000_000]:
        t_single = max(0, total - excl_2026)
        t_couple = max(0, total - 2 * excl_2026)
        rows.append({
            "total": money10(total),
            "excess_single": money10(t_single),
            "excess_couple": money10(t_couple),
            "federal_tax_single_at_40": money10(t_single * 0.40),
            "federal_tax_couple_at_40": money10(t_couple * 0.40),
            "california_estate_tax": 0,
        })
    return {"exclusion_2026": excl_2026,
            "exclusion_2027": V["federal_basic_exclusion_2027"]["value"],
            "rows": rows}


def exclusion_projection():
    rows = [{"year": 2026, "amount": V["federal_basic_exclusion_2026"]["value"],
             "basis": "Published by the IRS in the filing-threshold table",
             "src": ["irs_estate"]}]
    rows.append({"year": 2027, "amount": V["federal_basic_exclusion_2027"]["value"],
                 "basis": "Published by the IRS (IR-2026-133, 5 November 2026)",
                 "src": ["irs_2027"]})
    amount = float(V["federal_basic_exclusion_2027"]["value"])
    for y in range(2028, 2056):
        amount *= (1 + INFL)
        rows.append({"year": y, "amount": money10(amount),
                     "basis": "Mechanical indexation at the modelled inflation rate. Not law and not a forecast.",
                     "src": ["ssa_trustees"]})
    return rows


def prop19_cap_projection():
    rows = [{"year": 2026, "amount": V["prop19_value_cap_2025_2027"]["value"],
             "basis": "Published for transfers 16 February 2025 to 15 February 2027",
             "src": ["boe_lta25009"]}]
    cap = float(V["prop19_value_cap_2025_2027"]["value"])
    for y in range(2027, 2056):
        cap *= (1 + ASM["prop19_cap_growth"]["baseline"])
        rows.append({"year": y, "amount": money10(cap),
                     "basis": "Modelled indexation at the assumed rate. The real amount is set every second February from the California House Price Index and is not published in advance.",
                     "src": ["boe_lta25009"]})
    return rows


# ------------------------------------------------------------------ main ----
FIT_A = fit_bill(A["roll"], ASM["ad_valorem_rate_a"]["value"])
FIT_B = fit_bill(B["roll"], ASM["ad_valorem_rate_b"]["value"])
COST_A_BASE = (A["annual_costs"]["water"]["mid"] + A["annual_costs"]["electricity"]["mid"]
               + A["annual_costs"]["insurance"]["mid"])
COST_B_BASE = (B["annual_costs"]["water"]["mid"] + B["annual_costs"]["electricity"]["mid"]
               + B["annual_costs"]["insurance"]["mid"])


def main() -> dict:
    horizon = ASM["horizon_years"]
    g = ASM["house_growth"]["baseline"]
    infl = ASM["inflation"]["baseline"]
    eq = ASM["equity_return_nominal_gross"]["baseline"]
    drag = ASM["equity_tax_drag"]["baseline"]
    tsy = ASM["treasury_yield_nominal"]["baseline"]
    cap_growth = ASM["prop19_cap_growth"]["baseline"]
    sell_pct = ASM["selling_cost_pct"]["baseline"]
    gain_rate = ASM["combined_gain_tax_rate"]["baseline"]
    rec_rate = ASM["depreciation_recapture_rate"]["baseline"]
    maint_live = A["annual_costs"]["maintenance_pct_owner_occupied"]["value"]
    maint_rent = A["annual_costs"]["maintenance_pct_rental"]["value"]

    out = {
        "meta": {"built": "2026-11-13", "rounding": "nearest $10",
                 "horizon_years": horizon, "deterministic": True,
                 "inflation_assumption": infl, "house_growth_assumption": g,
                 "equity_assumption": eq, "equity_drag": drag,
                 "treasury_assumption": tsy, "selling_cost": sell_pct,
                 "gain_tax_rate": gain_rate, "recapture_rate": rec_rate},
        "fit": {
            "a": {k: (v if not isinstance(v, float) else round(v, 6))
                  for k, v in FIT_A.items()},
            "b": {k: (v if not isinstance(v, float) else round(v, 6))
                  for k, v in FIT_B.items()},
        },
        "roll_a": roll_table(A["roll"], FIT_A),
        "roll_b": roll_table(B["roll"], FIT_B),
        "projection_a": project_roll(A["roll"], A["estimated_market_value_2026"],
                                     g, infl, 0.02, 50, FIT_A),
        "projection_b": project_roll(B["roll"], B["estimated_market_value_2026"],
                                     g, infl, 0.02, 50, FIT_B),
        "paths": [],
        "regimes": [],
        "replay": historical_replay(30),
        "estate": estate_scenarios(),
        "exclusion_projection": exclusion_projection(),
        "prop19_cap_projection": prop19_cap_projection(),
        "sensitivity": sensitivity(2045),
        "costs_a_now": {
            "water": money10(A["annual_costs"]["water"]["mid"]),
            "electricity": money10(A["annual_costs"]["electricity"]["mid"]),
            "insurance": money10(A["annual_costs"]["insurance"]["mid"]),
            "maintenance": money10(maint_live * A["estimated_market_value_2026"]),
            "property_tax": money10(bill_for(A["roll"][0]["assessed"], FIT_A, 2026, infl)),
        },
        "costs_b_now": {
            "water": money10(B["annual_costs"]["water"]["mid"]),
            "electricity": money10(B["annual_costs"]["electricity"]["mid"]),
            "insurance": money10(B["annual_costs"]["insurance"]["mid"]),
            "maintenance": money10(B["annual_costs"]["maintenance_pct"]["value"]
                                   * B["estimated_market_value_2026"]),
            "property_tax": money10(bill_for(B["roll"][0]["assessed"], FIT_B, 2026, infl)),
            "rent": money10(B["rent"]["annual"]),
        },
        "series_table": build_series_table(),
    }

    for year in ASM["inheritance_years"]:
        res = run_paths(inherit_year=year, g=g, infl=infl, eq=eq, drag=drag, tsy=tsy,
                        cap_growth=cap_growth, sell_pct=sell_pct, horizon=horizon,
                        gain_rate=gain_rate, rec_rate=rec_rate,
                        exclusion=V["section121_exclusion_single"]["value"],
                        fixed_growth=ASM["fixed_charge_growth"]["baseline"], fit_a=FIT_A, cost_a_base=COST_A_BASE,
                        maint_live=maint_live, maint_rent=maint_rent)
        t_eq = res["paths"]["sell_equities"]["terminal"]
        res["breakeven_rent_annual"] = breakeven_rent(
            year, g, infl, eq, drag, cap_growth, sell_pct, horizon, gain_rate,
            rec_rate, infl, FIT_A, COST_A_BASE, maint_rent, t_eq)
        res["breakeven_rent_monthly"] = money10(res["breakeven_rent_annual"] / 12)
        res["breakeven_return_vs_live"] = breakeven_return(
            year, g, cap_growth, sell_pct, horizon, gain_rate, rec_rate,
            res["paths"]["live_in"]["terminal"])
        res["breakeven_return_vs_rent"] = breakeven_return(
            year, g, cap_growth, sell_pct, horizon, gain_rate, rec_rate,
            res["paths"]["rent_out"]["terminal"])
        res["housing_value_needed"] = money10(annuity(
            t_eq - res["paths"]["live_in"]["terminal"], eq - drag, horizon))
        res["breakeven_house_growth"] = breakeven_house_growth(
            year, eq, drag, cap_growth, sell_pct, horizon, gain_rate, rec_rate,
            V["section121_exclusion_single"]["value"], maint_live)
        res["best_path"] = max(res["paths"], key=lambda k: res["paths"][k]["terminal"])
        out["paths"].append(res)

    for regime in regime_stress():
        out["regimes"].append({**regime, "run": run_regime(regime, horizon)})

    (DATA / "model.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def build_series_table():
    years = sorted(set(list(SERIES["cpi"]["values"]) + list(SERIES["hpi_a"]["values"])
                       + list(SERIES["hpi_b"]["values"]) + list(SERIES["gs10"]["values"])))
    rows = []
    prev = {}
    for y in years:
        row = {"year": int(y)}
        for key, blk in (("cpi", SERIES["cpi"]), ("hpi_a", SERIES["hpi_a"]),
                         ("hpi_b", SERIES["hpi_b"]), ("gs10", SERIES["gs10"])):
            val = blk["values"].get(y)
            row[key] = val
            if val is not None and key in prev and prev[key]:
                row[key + "_chg"] = round(val / prev[key] - 1, 4)
            else:
                row[key + "_chg"] = None
            if val is not None:
                prev[key] = val
        rows.append(row)
    return rows


if __name__ == "__main__":
    m = main()
    print("fit A:", {k: (round(v, 5) if isinstance(v, float) else v) for k, v in m["fit"]["a"].items()})
    print("fit B:", {k: (round(v, 5) if isinstance(v, float) else v) for k, v in m["fit"]["b"].items()})
    print("costs A:", m["costs_a_now"])
    print("costs B:", m["costs_b_now"])
    for p in m["paths"]:
        print("==== inherit", p["inherit_year"], "value", p["value_at_death"],
              "byv", p["factored_base_year_value"], "cap", p["prop19_cap"])
        print("   bill today(proj)", p["bill_today_projected"],
              "| live", p["bill_if_live_year1"], "| rent", p["bill_if_rent_year1"])
        for k, v in p["paths"].items():
            print("   ", k, "terminal", v["terminal"], "outflow", v.get("outflow"))
        print("   breakeven rent/yr", p["breakeven_rent_annual"],
              "| monthly", p["breakeven_rent_monthly"])
        print("   breakeven return vs live", p["breakeven_return_vs_live"],
              "| vs rent", p["breakeven_return_vs_rent"])
        print("   housing value needed/yr", p["housing_value_needed"],
              "| best", p["best_path"])
    print("replay rows:", len(m["replay"]))
    for r in m["replay"][:3]:
        print("  ", r)
    for rg in m["regimes"]:
        print("  regime", rg["key"], rg["cpi"], rg["house"], rg["treasury"], "best", rg["run"]["best"])
    print("sensitivity:")
    for s in m["sensitivity"]:
        print("  ", s)
