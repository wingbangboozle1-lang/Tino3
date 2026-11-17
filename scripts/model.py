"""Deterministic model for the anonymised quantitative decision edition.

Reads  : assets/data/inputs.json, assets/data/series.json
Writes : assets/data/model.json

No network access. No randomness. Every published dollar figure is rounded to
the nearest $10 with money10(); every percentage with pct().
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "data"
sys.path.insert(0, str(ROOT / "scripts"))

import edition  # noqa: E402  (the edition's build date, shared with the page builder)
import episodes as EP  # noqa: E402  (reads its own verbatim CSVs, no network, no randomness)
INPUTS = json.loads((DATA / "inputs.json").read_text(encoding="utf-8"))
SERIES = json.loads((DATA / "series.json").read_text(encoding="utf-8"))

A = INPUTS["property_a"]
B = INPUTS["property_b"]
V = INPUTS["verified_parameters"]
ASM = INPUTS["assumptions"]

INFL = ASM["inflation"]["baseline"]
TSY_SHORT = ASM["treasury_short_yield_nominal"]["baseline"]
# The ONE canonical phased-investing configuration: every phased path on the site
# (dashboard path, decision paths, stress table, historical backtest) parks sale
# proceeds in 3-month-to-2-year Treasuries at TSY_SHORT for PARK_MONTHS, then buys
# equities in equal monthly pieces of the original proceeds over PHASE_MONTHS.
# Earlier editions had three implementations with three yield keys; the
# consolidation keeps this edition's single parking-yield key (the one the
# treasury_short_yield_nominal basis text already names) and one engine.
PARK_TSY = TSY_SHORT
PARK_MONTHS = int(ASM["phased_park_months"]["value"])
PHASE_MONTHS = int(ASM["phased_equity_phase_months"]["value"])


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


def annual_bills(start_av: float, fit: dict, start_year: int, infl: float,
                 horizon: int, cap: float = 0.02) -> list:
    """Year-by-year property tax bills, the assessed value rolling forward at the cap."""
    av = start_av
    out = []
    for j in range(horizon):
        out.append(bill_for(av, fit, start_year + j, infl))
        av *= (1 + cap)
    return out


def tax_path(start_av: float, fit: dict, start_year: int, infl: float,
             horizon: int, cap: float = 0.02) -> float:
    return sum(annual_bills(start_av, fit, start_year, infl, horizon, cap))


def fv_stream(amounts: list, rate: float) -> float:
    """Future value at the end of the horizon of year-end cash flows, compounded at rate.

    Same convention as the rental cash in run_paths and the break-even rent: a cash flow in
    year j (0-based) is compounded for the years that remain after it.
    """
    n = len(amounts)
    return sum(a * (1 + rate) ** (n - 1 - j) for j, a in enumerate(amounts))


def monthly_phase(net: float, park_months: int, phase_months: int, total_months: int,
                  tsy: float, eq: float, drag: float,
                  equity_monthly=None, tsy_monthly=None):
    """The single canonical phased-investing engine.

    The net proceeds sit in short Treasuries for `park_months` months, then move
    into equities in equal monthly purchases of the ORIGINAL proceeds over
    `phase_months` months. Purchases execute at the START of the month and earn
    that month's return; both balances then accrue monthly at (1+annual)^(1/12)-1.
    An immediate entry (park 0, phase 1) therefore compounds the equity return for
    the full horizon, exactly like the dashboard's sell-and-invest path.
    `equity_monthly(month)` / `tsy_monthly(month)` may override either monthly
    return (synthetic crash sequences, historical realized-return backtests).
    Returns (treasury balance, equity balance) at the end of `total_months`.
    """
    m_tsy = (1 + tsy) ** (1 / 12.0) - 1.0
    m_eq = (1 + eq - drag) ** (1 / 12.0) - 1.0
    phase_start = park_months + 1
    phase_end = park_months + phase_months
    chunk = net / phase_months if phase_months else 0.0
    treasury = float(net)
    equity = 0.0
    for month in range(1, total_months + 1):
        if phase_start <= month <= phase_end:
            treasury -= chunk
            equity += chunk
        r_eq = equity_monthly(month) if equity_monthly else m_eq
        r_ts = tsy_monthly(month) if tsy_monthly else m_tsy
        treasury *= (1 + r_ts)
        equity *= (1 + r_eq)
    return treasury, equity


def run_paths(inherit_year: int, g: float, infl: float, eq: float, drag: float,
              tsy: float, cap_growth: float, sell_pct: float, horizon: int,
              gain_rate: float, rec_rate: float, exclusion: float,
              fixed_growth: float, fit_a: dict, cost_a_base: float,
              maint_live: float, maint_rent: float,
              rent_income: float | None = None,
              imputed_rent: float | None = None) -> dict:
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
    # The base year moves with the fixed base. bill_for() grows the fixed charge from
    # fit["base_year"], so the pre-grown fixed_base above MUST be paired with base_year
    # set to the inheritance year. Earlier editions pre-grew fixed_base but left
    # base_year at the roll's base year, so the fixed charge was grown twice - once to
    # the inheritance year and again from the base year to each billed year. That
    # double-growth inflated every post-inheritance bill on the keeping paths (by
    # about $880 in the first inheritance year of the baseline) and contradicted the
    # single-growth convention used everywhere else (bill_today_projected, roll_table,
    # project_roll, historical_replay all grow the fixed charge once, from the base
    # year). Fixed 2026-11-17 after independent recomputation of the bills.
    fit_T["base_year"] = inherit_year

    terminal_price = value_at_death * (1 + g) ** horizon

    # Path 1 and 2: sell at inheritance, invest
    sale = sale_proceeds(value_at_death, value_at_death, sell_pct, gain_rate, rec_rate, 0.0)
    inv_eq = sale["net"] * (1 + eq - drag) ** horizon
    inv_ts = sale["net"] * (1 + tsy) ** horizon

    # Carrying outflows (property tax and running costs) are real cash paid out of the
    # heir's wealth on every path that keeps or lets the house. They are compounded at the
    # same after-tax equity return as the sell paths, and deducted from the terminal value.
    # Before this was done, the living and letting paths reported these costs but did not
    # charge them, which overstated both paths and understated every break-even.
    rate_fv = eq - drag

    # Path 3: live in it for the whole horizon, then sell
    bills_live = annual_bills(taxable_live, fit_T, inherit_year, infl, horizon)
    tax_live = sum(bills_live)
    cost_live = carrying_costs(value_at_death, cost_a_base, maint_live, infl, horizon)
    live = sale_proceeds(terminal_price, value_at_death, sell_pct, gain_rate, rec_rate,
                         0.0, exclusion)
    live_carry_fv = fv_stream(
        [bills_live[j] + (cost_a_base + maint_live * value_at_death) * (1 + infl) ** j
         for j in range(horizon)], rate_fv)

    # Rental income. The original model charged every landlord cost to the rental paths
    # and credited none of the rent, which made them structurally incapable of winning.
    # Rent is entered as an input (assets/data/inputs.json, property_a.rent_income_annual)
    # and grown with the modelled inflation rate; it is accumulated at the equity
    # after-tax rate, the same convention the break-even rent calculation already used.
    rent0 = float(rent_income or 0.0)

    def rent_accumulated(years: int) -> float:
        tot = 0.0
        for j in range(years):
            tot += rent0 * (1 + infl) ** j * (1 + eq - drag) ** (years - 1 - j)
        return tot

    # Imputed rent on the living paths: the housing the heir consumes by occupying
    # the house instead of living in Property B and letting the vacant unit. The
    # input (property_a.imputed_rent) is empty unless a documented rent
    # opinion is supplied, so the published baseline credits zero and does not
    # move. When set, it is credited gross over the years of occupancy, the same
    # convention as the letting path's rent, and it is not taxable income because
    # it is never received as cash.
    imp0 = float(imputed_rent or 0.0)

    def imputed_fv(years: int, compound_after: int = 0) -> float:
        tot = 0.0
        for j in range(years):
            tot += imp0 * (1 + infl) ** j * (1 + eq - drag) ** (years - 1 - j)
        return tot * (1 + eq - drag) ** compound_after

    # Path 4: let it out from the start, then sell
    bills_rent = annual_bills(taxable_rent, fit_T, inherit_year, infl, horizon)
    tax_rent = sum(bills_rent)
    cost_rent = carrying_costs(value_at_death, cost_a_base, maint_rent, infl, horizon)
    deprec = min(0.8 * value_at_death, 0.8 * value_at_death / 27.5 * horizon)
    rent_sale = sale_proceeds(terminal_price, value_at_death - deprec, sell_pct,
                              gain_rate, rec_rate, deprec)
    rent_cash = rent_accumulated(horizon)
    # Net rental cash: gross rent less the same tax and running costs, compounded.
    rent_carry_fv = fv_stream(
        [rent0 * (1 + infl) ** j - bills_rent[j]
         - (cost_a_base + maint_rent * value_at_death) * (1 + infl) ** j
         for j in range(horizon)], rate_fv)

    # Path 6: phased investing - sell at inheritance, park the net sale proceeds in
    # short-term (3M-2Y) Treasuries for the parking period (the owner's 24-36 month
    # band, baseline 30 months), then phase into equities by equal monthly purchases
    # of the original proceeds over the canonical phase window. This is the canonical
    # monthly implementation with the one canonical parking yield - the same engine
    # that produces the stress table and the historical backtest on the black-swan
    # page, so the dashboard headline is the path the stress table tests.
    phase_years = PARK_MONTHS / 12.0
    invest_years = max(0.0, horizon - phase_years)
    _treasury, _equity = monthly_phase(
        sale["net"], PARK_MONTHS, PHASE_MONTHS, horizon * 12, PARK_TSY, eq, drag)
    phase_terminal = _treasury + _equity
    parked = sale["net"] * (1 + PARK_TSY) ** phase_years

    # Path 5: live in it for two years, then let it out for the rest
    bills_h1 = annual_bills(taxable_live, fit_T, inherit_year, infl, 2)
    tax_h1 = sum(bills_h1)
    fit_T2 = dict(fit_T)
    fit_T2["fixed_base"] = fit_T["fixed_base"] * (1 + fixed_growth) ** 2
    av_after = taxable_rent * 1.02 ** 2
    bills_h2 = annual_bills(av_after, fit_T2, inherit_year + 2, infl, horizon - 2)
    tax_h2 = sum(bills_h2)
    cost_h = carrying_costs(value_at_death, cost_a_base, maint_rent, infl, horizon)
    deprec_h = min(0.8 * value_at_death,
                   0.8 * value_at_death / 27.5 * (horizon - 2))
    hybrid_sale = sale_proceeds(terminal_price, value_at_death - deprec_h, sell_pct,
                                gain_rate, rec_rate, deprec_h, exclusion)
    hybrid_cash = rent_accumulated(horizon - 2)
    # Net rental cash for the years let: gross rent (hybrid_cash, already compounded) less the
    # tax and running costs of every year of the horizon, compounded at the same rate.
    hybrid_out_fv = fv_stream(
        [(bills_h1 + bills_h2)[j] + (cost_a_base + maint_rent * value_at_death) * (1 + infl) ** j
         for j in range(horizon)], rate_fv)
    hybrid_carry_fv = hybrid_cash - hybrid_out_fv

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
            # Sell paths: the only cost after inheritance is the sale itself, already netted
            # from the proceeds. Its amount is reported as the cost paid.
            "sell_equities": {"terminal": money10(inv_eq),
                              "outflow": money10(sale["costs"] + sale["tax"]),
                              "carry_fv": 0,
                              "start": sale["net"], "sale": sale},
            "sell_treasury": {"terminal": money10(inv_ts),
                              "outflow": money10(sale["costs"] + sale["tax"]),
                              "carry_fv": 0,
                              "start": sale["net"], "sale": sale},
            # Holding paths: the terminal value is the sale net less the compounded future
            # value of every year's property tax and running costs (carry_fv).
            "live_in": {"terminal": money10(live["net"] - live_carry_fv + imputed_fv(horizon)),
                        "outflow": money10(tax_live + cost_live),
                        "carry_fv": money10(live_carry_fv),
                        "imputed_credit": money10(imputed_fv(horizon)),
                        "tax_total": money10(tax_live),
                        "cost_total": money10(cost_live), "sale": live},
            "rent_out": {"terminal": money10(rent_sale["net"] + rent_carry_fv),
                         "outflow": money10(tax_rent + cost_rent),
                         "carry_fv": money10(rent_carry_fv),
                         "tax_total": money10(tax_rent),
                         "cost_total": money10(cost_rent),
                         "rent_income_total": money10(rent_cash),
                         "depreciation": money10(deprec), "sale": rent_sale},
            "sell_then_phase": {"terminal": money10(phase_terminal), "outflow": 0,
                                "start": sale["net"], "sale": sale,
                                "parked": money10(parked),
                                "park_months": PARK_MONTHS,
                                "phase_months": PHASE_MONTHS,
                                "invest_years": invest_years},
            "live_then_rent": {"terminal": money10(hybrid_sale["net"] + hybrid_carry_fv
                                                   + imputed_fv(2, horizon - 2)),
                               "outflow": money10(tax_h1 + tax_h2 + cost_h),
                               "carry_fv": money10(hybrid_carry_fv),
                               "imputed_credit": money10(imputed_fv(2, horizon - 2)),
                               "tax_total": money10(tax_h1 + tax_h2),
                               "cost_total": money10(cost_h),
                               "rent_income_total": money10(hybrid_cash),
                               "depreciation": money10(deprec_h),
                               "sale": hybrid_sale},
        },
    }


def run_phased_path(inherit_year: int, g: float, infl: float, eq: float, drag: float,
                    tsy_short: float, horizon: int, sell_pct: float, gain_rate: float,
                    rec_rate: float, exclusion: float, fixed_growth: float, fit_a: dict,
                    cost_a_base: float, maint_live: float, maint_rent: float,
                    rent_income: float | None, park_months: int, phase_months: int) -> dict:
    """Sell at inheritance, park the net proceeds in short Treasuries (3M-2Y) for
    park_months, then phase into equities by equal monthly purchases of the original
    proceeds over phase_months. The point of the path is entry-risk sequencing: the
    money earns a short-Treasury yield while it is phased in, so part of the
    portfolio is never exposed to an equity drawdown and the equity purchases are
    spread across prices. Delegates to the one canonical monthly engine; returns the
    terminal value and the net sale proceeds, both rounded to the nearest $10.
    """
    k = inherit_year - 2026
    value_at_death = A["estimated_market_value_2026"] * (1 + g) ** k
    sale = sale_proceeds(value_at_death, value_at_death, sell_pct, gain_rate, rec_rate, 0.0)
    net = sale["net"]

    total_months = horizon * 12
    park_months = max(0, min(int(park_months), total_months))
    phase_months = max(0, min(int(phase_months), total_months - park_months))
    treasury, equity = monthly_phase(net, park_months, phase_months, total_months,
                                     tsy_short, eq, drag)

    return {
        "terminal": money10(treasury + equity),
        "net_proceeds": money10(net),
        "treasury_portion": money10(treasury),
        "equity_portion": money10(equity),
        "park_months": park_months,
        "phase_months": phase_months,
    }


def phased_stress(proceeds: float) -> dict:
    """The black-swan entry-timing stress table, computed by the canonical engine.

    Six cases: immediate equity versus 24- or 36-month Treasury parking plus a
    12-month monthly phase-in, each with and without a synthetic crash at entry.
    The crash sequence is stated, not historical: -40% in year one, +25% in year
    two, +10% in year three, then the baseline net equity return. The parking
    yield is the one canonical 3M-2Y parking scenario. The dated historical
    counterpart is crash_entry_backtest() below.
    """
    horizon = ASM["horizon_years"]
    baseline_net = ASM["equity_return_nominal_gross"]["baseline"] - ASM["equity_tax_drag"]["baseline"]
    shock_returns = [-0.40, 0.25, 0.10]

    def run(wait_months: int, shock: bool) -> float:
        def em(month):
            year = (month - 1) // 12
            annual = shock_returns[year] if (shock and year < len(shock_returns)) else baseline_net
            return (1 + annual) ** (1 / 12.0) - 1.0
        # The immediate comparator buys the whole proceeds in month 1 (phase window
        # of one month). The earlier edition spread even the "immediate" comparator
        # over 12 months, which understated the opportunity cost of phasing.
        phase = 1 if wait_months == 0 else PHASE_MONTHS
        treasury, equity = monthly_phase(
            proceeds, wait_months, phase, horizon * 12, PARK_TSY,
            ASM["equity_return_nominal_gross"]["baseline"],
            ASM["equity_tax_drag"]["baseline"], equity_monthly=em)
        return treasury + equity

    direct = {False: run(0, False), True: run(0, True)}
    cases = [
        ("Immediate equity; no shock", 0, False, "Reference case"),
        ("Immediate equity; synthetic crash-at-entry stress", 0, True,
         "Shared stylized stress; not a dated replay"),
        ("Treasuries 24 months, then phase to equities over 12 months; no shock", 24, False,
         "No-crash opportunity-cost case"),
        ("Treasuries 24 months, then phase to equities over 12 months; synthetic crash stress",
         24, True, "Shared stylized stress; not a dated replay"),
        ("Treasuries 36 months, then phase to equities over 12 months; no shock", 36, False,
         "No-crash opportunity-cost case"),
        ("Treasuries 36 months, then phase to equities over 12 months; synthetic crash stress",
         36, True, "Shared stylized stress; not a dated replay"),
    ]
    rows = []
    for label, wait, shock, context in cases:
        amount = run(wait, shock)
        rows.append({"label": label, "wait_months": wait, "shock": shock,
                     "terminal": money10(amount),
                     "difference": money10(amount - direct[shock]),
                     "reading": context})
    band = ASM["treasury_short_yield_nominal"]
    return {"parking_yield": pct(PARK_TSY, 1), "parking_yield_low": pct(band["low"], 1),
            "parking_yield_high": pct(band["high"], 1), "equity_baseline": pct(baseline_net, 1),
            "park_months_baseline": PARK_MONTHS, "phase_months": PHASE_MONTHS,
            "horizon_years": horizon, "rows": rows}


def crash_entry_backtest(proceeds: float) -> dict:
    """Dated historical backtest of crash-entry timing with realized annual returns.

    For each entry year, applies the realized S&P 500 total return (dividends
    reinvested) and the realized 3-month Treasury bill return of every following
    year, from the NYU Stern (Damodaran) historical returns table, to the same
    hypothetical 2045 net sale proceeds. Annual returns are spread evenly across
    the twelve months of their year so the canonical monthly phase-in can be
    modelled exactly. Gross returns: no tax drag, costs, fees or withdrawals.
    Entry at the start of the entry calendar year, which approximates a
    peak-of-market entry but is not a day-level replay. The 1929 episode uses the
    S&P composite that predates the 1957 500-stock index; the publisher labels
    the whole column "S&P 500 (includes dividends)". An academic series, not a
    government publication.
    """
    sp = SERIES["sp500_tr"]["values"]
    tb = SERIES["tbill3"]["values"]
    last_year = max(int(k) for k in sp)
    episodes = [
        (1929, "Crash entry 1929",
         "Great Depression entry: -8.3% in 1929, then -25.1%, -43.8% and -8.6% in the next three years"),
        (2000, "Crash entry 2000",
         "Dot-com peak entry: three consecutive negative years, 2000 to 2002"),
        (2008, "Crash entry 2008",
         "Financial-crisis entry: -36.6% in the first year"),
    ]
    paths = [("Immediate equity at entry", 0, 1),
             ("Treasuries 24 months, then phase over 12 months", 24, 12),
             ("Treasuries 36 months, then phase over 12 months", 36, 12)]

    def run(park, phase, months, entry):
        def em(month):
            r = sp[str(entry + (month - 1) // 12)]
            return (1 + r / 100.0) ** (1 / 12.0) - 1.0

        def tm(month):
            r = tb[str(entry + (month - 1) // 12)]
            return (1 + r / 100.0) ** (1 / 12.0) - 1.0

        treasury, equity = monthly_phase(proceeds, park, phase, months,
                                         PARK_TSY, PARK_TSY, 0.0,
                                         equity_monthly=em, tsy_monthly=tm)
        return treasury + equity

    out_episodes = []
    wins_10 = 0
    for entry, label, context in episodes:
        full_years = min(30, last_year - entry + 1)
        rows = []
        terminals = {}
        for months, tag in ((120, "10-year"), (full_years * 12, f"{full_years}-year")):
            base = run(0, 1, months, entry)
            for path, park, phase in paths:
                amount = run(park, phase, months, entry)
                terminals[(tag, path)] = money10(amount)
                rows.append({"horizon": tag, "path": path, "park_months": park,
                             "phase_months": phase, "terminal": money10(amount),
                             "difference_vs_immediate": money10(amount - base)})
        out_episodes.append({"entry_year": entry, "label": label, "context": context,
                             "window_end": entry + full_years - 1,
                             "full_horizon_years": full_years, "rows": rows})
        if terminals[("10-year", paths[1][0])] > terminals[("10-year", paths[0][0])]:
            wins_10 += 1
    return {"proceeds": money10(proceeds), "episodes": out_episodes,
            "phased_wins_at_10_years": wins_10,
            "record_end_year": last_year,
            "note": ("Realized annual returns from an academic source (NYU Stern, "
                     "Damodaran), spread evenly across the months of each year; "
                     "gross of taxes, costs and fees; applied to the same hypothetical "
                     "2045 net sale proceeds as the synthetic stress table. Terminal "
                     "values are rounded to $10.")}


def annuity_fv(future_gap: float, rate: float, years: int) -> float:
    """Level year-end payment whose future value after `years` equals `future_gap`.

    The gap is already a future value (money at the end of the horizon), so the payment is
    future_gap * r / ((1 + r)^n - 1). The present-value form r / (1 - (1+r)^-n) overstated it
    by about (1 + r)^n and was retired here.
    """
    if rate <= 0:
        return future_gap / years
    return future_gap * rate / ((1 + rate) ** years - 1)


def breakeven_rent(inherit_year: int, g: float, infl: float, eq: float, drag: float,
                   cap_growth: float, sell_pct: float, horizon: int, gain_rate: float,
                   rec_rate: float, fixed_growth: float, fit_a: dict,
                   cost_a_base: float, maint_rent: float, target: float):
    """Initial annual rent that makes letting the house out match the target."""
    k = inherit_year - 2026
    value_at_death = A["estimated_market_value_2026"] * (1 + g) ** k
    fit_T = dict(fit_a)
    fit_T["fixed_base"] = fit_a["fixed_base"] * (1 + fixed_growth) ** (inherit_year - fit_a["base_year"])
    # base_year moves with the pre-grown fixed base (one growth from the roll's base
    # year, not two); see the note in run_paths. Fixed 2026-11-17.
    fit_T["base_year"] = inherit_year

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
    """Annual return that, earned on the sale proceeds, reaches `target` after the horizon.

    Solved in closed form, so a negative figure is possible: it means the sale proceeds
    would still reach the target if they lost that much every year. None means no return
    can reach it (a non-positive target).
    """
    k = inherit_year - 2026
    value_at_death = A["estimated_market_value_2026"] * (1 + g) ** k
    sale = sale_proceeds(value_at_death, value_at_death, sell_pct, gain_rate, rec_rate, 0.0)
    if target <= 0 or sale["net"] <= 0:
        return None
    return round(((target / sale["net"]) ** (1.0 / horizon) - 1.0) * 100.0, 2)


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
                maint_rent=A["annual_costs"]["maintenance_pct_rental"]["value"],
                rent_income=RENT_INCOME,
                imputed_rent=IMPUTED_RENT)
            terms = {k: v["terminal"] for k, v in res["paths"].items()}
            phased = run_phased_path(
                inherit_year=target_year, g=g, infl=ASM["inflation"]["baseline"], eq=eq,
                drag=ASM["equity_tax_drag"]["baseline"], tsy_short=PARK_TSY,
                horizon=ASM["horizon_years"],
                sell_pct=ASM["selling_cost_pct"]["baseline"],
                gain_rate=ASM["combined_gain_tax_rate"]["baseline"],
                rec_rate=ASM["depreciation_recapture_rate"]["baseline"],
                exclusion=V["section121_exclusion_single"]["value"],
                fixed_growth=INFL, fit_a=FIT_A, cost_a_base=COST_A_BASE,
                maint_live=A["annual_costs"]["maintenance_pct_owner_occupied"]["value"],
                maint_rent=A["annual_costs"]["maintenance_pct_rental"]["value"],
                rent_income=RENT_INCOME,
                park_months=PARK_MONTHS,
                phase_months=PHASE_MONTHS)
            terms["sell_phased"] = phased["terminal"]
            best = max(terms, key=terms.get)
            rows.append({"house_growth": pct(g, 1), "equity_return": pct(eq, 1),
                         **{k: v for k, v in terms.items()}, "best": best})
    return rows


def sensitivity_fine():
    """Best path across a fine grid of house growth and equity return.

    A what-if map: for each combination it prices every path at a 2045
    inheritance and names the winner. Computed by the same model as the
    published pages; no randomness, no invented inputs.
    """
    rows = []
    for g in (i / 100.0 for i in range(0, 10)):
        cells = []
        for eq in (i / 100.0 for i in range(3, 11)):
            res = run_paths(inherit_year=2045, g=g, infl=ASM["inflation"]["baseline"],
                            eq=eq, drag=ASM["equity_tax_drag"]["baseline"],
                            tsy=ASM["treasury_yield_nominal"]["baseline"],
                            cap_growth=ASM["prop19_cap_growth"]["baseline"],
                            sell_pct=ASM["selling_cost_pct"]["baseline"],
                            horizon=ASM["horizon_years"],
                            gain_rate=ASM["combined_gain_tax_rate"]["baseline"],
                            rec_rate=ASM["depreciation_recapture_rate"]["baseline"],
                            exclusion=V["section121_exclusion_single"]["value"],
                            fixed_growth=INFL, fit_a=FIT_A, cost_a_base=COST_A_BASE,
                            maint_live=A["annual_costs"]["maintenance_pct_owner_occupied"]["value"],
                            maint_rent=A["annual_costs"]["maintenance_pct_rental"]["value"],
                            rent_income=RENT_INCOME,
                            imputed_rent=IMPUTED_RENT)
            terms = {k: v["terminal"] for k, v in res["paths"].items()}
            best = max(terms, key=terms.get)
            cells.append({"eq": pct(eq, 0), "best": best})
        rows.append({"g": pct(g, 0), "cells": cells})
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
                        maint_rent=A["annual_costs"]["maintenance_pct_rental"]["value"],
                        rent_income=RENT_INCOME,
                        imputed_rent=IMPUTED_RENT)
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
            "src": ["frh_great_inflation", "fred_cpi", "fred_gs10"],
            "derived": True,
            "cpi": pct(avg_growth(cpi_v, 1977, 1981), 1),
            "house": pct(avg_growth(hpi_a, 1977, 1981), 1),
            "treasury": round(avg_level(gs10_v, 1977, 1981), 2),
            "window": "1977-1981 averages computed from the verified series",
        },
        {
            "key": "slump",
            "name": "A long house price slump",
            "analogue": "1989-1996 in the California state record",
            "src": ["fred_casthpi", "fred_cpi"],
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
            "src": ["fred_casthpi", "fred_gs10", "frh_great_recession"],
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
        maint_rent=A["annual_costs"]["maintenance_pct_rental"]["value"],
        rent_income=RENT_INCOME,
        imputed_rent=IMPUTED_RENT)
    phased = run_phased_path(
        inherit_year=2045, g=g, infl=infl, eq=ASM["equity_return_nominal_gross"]["baseline"],
        drag=ASM["equity_tax_drag"]["baseline"], tsy_short=PARK_TSY,
        horizon=horizon, sell_pct=ASM["selling_cost_pct"]["baseline"],
        gain_rate=ASM["combined_gain_tax_rate"]["baseline"],
        rec_rate=ASM["depreciation_recapture_rate"]["baseline"],
        exclusion=V["section121_exclusion_single"]["value"],
        fixed_growth=ASM["fixed_charge_growth"]["baseline"], fit_a=FIT_A, cost_a_base=COST_A_BASE,
        maint_live=A["annual_costs"]["maintenance_pct_owner_occupied"]["value"],
        maint_rent=A["annual_costs"]["maintenance_pct_rental"]["value"],
        rent_income=RENT_INCOME,
        park_months=PARK_MONTHS,
        phase_months=PHASE_MONTHS)
    cpi_mult = (1 + infl) ** horizon
    paths = {k: v["terminal"] for k, v in res["paths"].items()}
    paths["sell_phased"] = phased["terminal"]
    return {
        "terminal": {k: v["terminal"] for k, v in res["paths"].items()},
        "terminal_real": {k: money10(v["terminal"] / cpi_mult) for k, v in res["paths"].items()},
        "outflow": {k: v.get("outflow", 0) for k, v in res["paths"].items()},
        "phased_terminal": phased["terminal"],
        "phased_net_proceeds": phased["net_proceeds"],
        "value_at_death": res["value_at_death"],
        "bill_if_live_year1": res["bill_if_live_year1"],
        "bill_if_rent_year1": res["bill_if_rent_year1"],
        "best": max(paths, key=lambda k: paths[k]),
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


# --------------------------------------------------- parcel tax, Property B --
def prop_h_schedule() -> dict:
    """Official terms and inflation-scenario projection of the parcel tax passed on the preliminary count
    in Property B's city at the November 2026 election (Proposition H).

    The terms were read from the measure's own legal text (the Business and Tax
    Regulations Code Article 18 it adds) and from the transit agency's official
    parcel-tax page, both on the publisher's own domain, on 2026-11-15. The
    publisher is a city body and is not named or linked on the public site,
    because the jurisdiction identifies the properties, so the published rows
    point at the review register instead. The band that applies to the parcel is
    not determined: the building area was not supplied. Nothing here touches
    Property A, which sits in a different jurisdiction.
    """
    ph = B["parcel_tax_approved_2026"]
    base = ph["multifamily_base_2027_28"]
    infl_lo = ASM["inflation"]["low"]
    infl_mid = ASM["inflation"]["baseline"]
    infl_hi = ASM["inflation"]["high"]
    rows = []
    # Fiscal years 2027-28 (unadjusted, the official amount) to 2041-42, the last
    # year before the tax expires on 30 June 2042. Dollar amounts adjust each
    # 31 December from 2027, first affecting fiscal year 2028-29 (SEC. 1804(b)),
    # by the local all-items Consumer Price Index published by the federal
    # statistics agency. The three columns are the site's inflation band.
    for start in range(2027, 2042):
        n = start - 2027
        fy = f"{start}-{str(start + 1)[2:]}"
        if n == 0:
            rows.append({"fy": fy, "adjustments": 0, "official": True,
                         "low": base, "baseline": base, "high": base})
        else:
            rows.append({"fy": fy, "adjustments": n, "official": False,
                         "low": money10(base * (1 + infl_lo) ** n),
                         "baseline": money10(base * (1 + infl_mid) ** n),
                         "high": money10(base * (1 + infl_hi) ** n)})
    totals = {k: money10(sum(r[k] for r in rows))
              for k in ("low", "baseline", "high")}
    return {
        "approved": ph["approved"],
        "status": ph["status"],
        "first_fiscal_year": ph["first_fiscal_year"],
        "expires": ph["expires"],
        "base": base,
        "rate_over_5000_sqft": ph["multifamily_rate_over_5000_sqft"],
        "max_tax": ph["multifamily_max"],
        "pass_through_share": ph["pass_through_share"],
        "pass_through_unit_cap": ph["pass_through_unit_cap_annual"],
        "pass_through_units": B["units_rented"],
        "pass_through_max_total": money10(B["units_rented"] * ph["pass_through_unit_cap_annual"]),
        "pass_through_cutoff": ph["pass_through_base_rent_cutoff"],
        "senior_reduction_per_occupied_unit": ph["senior_reduction_per_occupied_unit"],
        "band_determined": ph["band_determined"],
        "band_note": ph["band_note"],
        "source_note": ph["source_note"],
        "rows": rows,
        "totals_to_expiry": totals,
    }


# -------------------------------------------------------- imputed rent ------
def imputed_rent_level_cases(p45: dict, infl: float, eq: float, drag: float,
                             g: float, cap_growth: float, sell_pct: float,
                             horizon: int, gain_rate: float, rec_rate: float,
                             levels=(0, 5000, 10000, 20000, 30000)) -> dict:
    """What each stated monthly imputed rent would do to the 2045 living path.

    The levels are stated scenarios, not estimates: no market rent or rent
    opinion for Property A has been supplied, so the real input
    (property_a.imputed_rent) stays empty and the published baseline is
    the zero row. Each level is credited gross to the living path over the whole
    horizon, grown with inflation and accumulated at the after-tax equity return,
    the same convention as the letting path's rent; it is not taxable income
    because it is never received as cash. The return column is the annual return
    the sale proceeds would then need to match living in the house.
    """
    live0 = p45["paths"]["live_in"]["terminal"]
    sell = p45["paths"]["sell_equities"]["terminal"]
    rows = []
    for monthly in levels:
        annual = monthly * 12.0
        uplift = 0.0
        for j in range(horizon):
            uplift += annual * (1 + infl) ** j * (1 + eq - drag) ** (horizon - 1 - j)
        live = money10(live0 + uplift)
        req = breakeven_return(2045, g, cap_growth, sell_pct, horizon,
                               gain_rate, rec_rate, live)
        rows.append({
            "monthly": monthly,
            "annual": money10(annual),
            "uplift": money10(uplift),
            "live_terminal": live,
            "sell_terminal": sell,
            "gap": money10(live - sell),
            "return_required": req,
            "best": "live_in" if live > sell else "sell_equities",
        })
    return {
        "input_annual": IMPUTED_RENT,
        "inherit_year": 2045,
        "rows": rows,
        "housing_value_needed": p45["housing_value_needed"],
        "breakeven_rent_monthly": p45["breakeven_rent_monthly"],
    }


# ------------------------------------------------------------------ main ----
FIT_A = fit_bill(A["roll"], ASM["ad_valorem_rate_a"]["value"])
FIT_B = fit_bill(B["roll"], ASM["ad_valorem_rate_b"]["value"])
# Rent used in the letting paths. None unless the owner supplies a figure, so the site
# never invents a market rent: with no rent the letting paths carry cost and no income,
# which is the conservative case, and it is labelled as such everywhere it is shown.
RENT_INCOME = A.get("rent_income_annual", {}).get("value") \
    if isinstance(A.get("rent_income_annual"), dict) else None
# Imputed rent credited to the living paths. None unless the owner supplies a
# documented rent opinion, for the same reason as RENT_INCOME above: the site
# never invents a rent figure. The stated-level sensitivity published on the
# what-if page shows what any entered level would do.
IMPUTED_RENT = A.get("imputed_rent", {}).get("value") \
    if isinstance(A.get("imputed_rent"), dict) else None
COST_A_BASE = (A["annual_costs"]["water"]["mid"] + A["annual_costs"]["electricity"]["mid"]
               + A["annual_costs"]["insurance"]["mid"])
COST_B_BASE = (B["annual_costs"]["water"]["mid"] + B["annual_costs"]["electricity"]["mid"]
               + B["annual_costs"]["insurance"]["mid"])



# ---------------------------------------------------------------------------
# Section 17043 surcharge sensitivity, and the projections distribution.
#
# Both functions are APPENDED deliberately: earlier sessions own the body of
# main() and concurrent edits to it are the main source of merge conflicts.
# main() calls them through _append_extras() at the end of this file.
# ---------------------------------------------------------------------------
CA_SURCHARGE = ASM.get("ca_1pct_surcharge", {})
GAIN_RATE = ASM["combined_gain_tax_rate"]


def form540_surcharge(gain: float, other_income: float, threshold: float,
                      top_rate: float = 0.123) -> dict:
    """The 1% computed the way the Form 540 instructions compute it.

    Read from the 2025 Instructions for Form 540, line 62 (ledger entry
    `ftb_540_instructions_2025`). The line 62 worksheet is:

        1. taxable income from Form 540, line 19
        2. less $(1,000,000)
        3. subtotal
        4. tax rate 1%
        5. the tax: line 3 multiplied by line 4, entered on line 62

    Two consequences the flat-rate version on this page got wrong, both in the
    taxpayer's favour against a flat application to the whole gain:

    * The 1% reaches only the slice of *taxable income* above the threshold. If
      the gain plus all other taxable income stays under the threshold, the tax
      is zero, whatever the size of the gain.
    * Taxable income is cumulative. A gain lands on top of whatever else the
      household already earns in the year of sale, so the position of the gain
      relative to the threshold decides most of the answer, not its size alone.

    The bracket tax is computed on the same cumulative income so that the two
    layers can be priced against each other. `top_rate` is the top printed
    bracket on the current schedule (12.3%); it is applied flat to all taxable
    income, which OVERSTATES the bracket tax and is stated as such on the page.
    That direction is deliberate: it cannot make the surcharge look larger than
    it is.
    """
    ti = max(0.0, gain) + max(0.0, other_income)
    over = max(0.0, ti - threshold)
    # The part of the 1% that is actually caused by the gain: the gain can only be
    # taxed on the slice of itself that lands above the threshold, and it can never
    # be taxed on more than its own size. `over` above includes the slice created by
    # other income, which the household owes whether or not it sells the house.
    attributable = min(max(0.0, gain), over)
    return {
        "taxable_income": money10(ti),
        "above_threshold": money10(over),
        "surcharge": money10(over * 0.01),
        "surcharge_on_gain": money10(attributable * 0.01),
        "bracket_tax": money10(ti * top_rate),
        "state_total": money10(over * 0.01 + ti * top_rate),
    }


def surcharge_sensitivity(year: int = 2045) -> dict:
    """What the section 17043 1% does to the one sale the site recommends.

    The gain tax rate is a point assumption elsewhere in the model. This function
    re-runs the sale that decides the recommendation - sell at inheritance, where
    the basis step-up makes the gain about zero - and then re-runs the two paths
    that DO carry a large taxable gain 30 years later, at the rate without the
    surcharge and at the rate with it. The point is to show that the surcharge
    changes the size of the tax on the late-sale and letting paths, and does not
    change whether selling at inheritance wins.

    The flat comparison in `rows` is an UPPER BOUND on the surcharge: it applies
    the one-point difference to the entire gain. The `worksheet` block below it
    computes the same tax the way the Form 540 line 62 instructions do, on the
    slice of cumulative taxable income above the threshold, across a range of
    other taxable income. Read together, the two say: the direction is certain,
    the magnitude is a ceiling, and for a modest household income the surcharge
    is a fraction of what the ceiling implies.
    """
    p = next(x for x in MAIN_RESULT["paths"] if x["inherit_year"] == year)
    low, high = float(GAIN_RATE["low"]), float(GAIN_RATE["high"])
    rc_low = high - 0.01
    rows = []
    for key, label in (("sell_equities", "Sell at inheritance, invest in equities"),
                       ("sell_treasury", "Sell at inheritance, hold Treasuries"),
                       ("live_in", "Live in it, sell after 30 years"),
                       ("rent_out", "Let it out, sell after 30 years"),
                       ("live_then_rent", "Live in it 2 years, then let it out")):
        path = p["paths"][key]
        s_high = path["sale"]
        base = dict(price=s_high["price"], basis=s_high["basis"])
        s_low = sale_proceeds(base["price"], base["basis"], ASM["selling_cost_pct"]["baseline"],
                              low, rc_low, (path.get("depreciation") or 0) / 1.0,
                              V["section121_exclusion_single"]["value"])
        rows.append({
            "key": key, "label": label,
            "gain": s_high["gain"],
            "tax_without_surcharge": s_low["tax"],
            "tax_with_surcharge": s_high["tax"],
            "difference": s_high["tax"] - s_low["tax"],
            "terminal_with_surcharge": path["terminal"],
        })
    # ---- the same tax computed on the Form 540 worksheet, not on the whole gain ----
    # `other_income` stands in for every other item on the return: wages, interest,
    # rent, pensions. It is an assumption, not a figure from the household, so it is
    # published as a range of scenarios like the imputed rent and insurance bands.
    low, high = float(GAIN_RATE["low"]), float(GAIN_RATE["high"])
    threshold = int(CA_SURCHARGE.get("threshold", 1_000_000))
    scenarios = ASM.get("form540_other_income", {}).get(
        "scenarios", [0, 250_000, 1_000_000, 2_000_000])
    worksheet = []
    for key, label in (("sell_equities", "Sell at inheritance"),
                       ("live_in", "Live in it, sell after 30 years"),
                       ("rent_out", "Let it out, sell after 30 years")):
        path = p["paths"][key]
        gain = float(path["sale"]["gain"])
        rungs = []
        for other in scenarios:
            w = form540_surcharge(gain, other, threshold)
            # the bracket part of this tax, at the same cumulative income, priced on
            # the two published California layers: 12.3% top bracket, then this 1%
            rungs.append({
                "other_income": money10(other),
                "label": ("No other taxable income" if other == 0
                          else f"${other:,.0f} of other taxable income"),
                **w,
            })
        worksheet.append({
            "key": key, "label": label,
            "gain": money10(gain),
            "flat_upper_bound": money10(gain * (high - low)),
            "rungs": rungs,
        })
    return {
        "year": year,
        "surcharge_rate": float(CA_SURCHARGE.get("value", 0.01)),
        "threshold": threshold,
        "threshold_indexed": bool(CA_SURCHARGE.get("threshold_indexed", False)),
        "rate_without": low, "rate_with": high,
        "rows": rows,
        "worksheet": worksheet,
        "worksheet_scenarios": scenarios,
        "recommendation_unchanged": (
            p["paths"]["sell_equities"]["terminal"] > p["paths"]["live_in"]["terminal"]),
    }


def projections_distribution(span: int = 30) -> dict:
    """The block-bootstrap range for the inherited property's value, one year at a time.

    Reads the bootstrap already computed in economy.py (assets/data/economy.json):
    ten-year blocks drawn from the California state-level all-transactions record,
    resampled 2,000 times from a fixed seed so the file is byte-stable. Nothing new
    is estimated here; it only re-expresses the published distribution as a per-year
    band so a reader can see the range beside the single line.

    Re-expresses the band the bootstrap module already writes - it publishes a
    per-year p05/p50/p95 path under bootstrap.chart.years, and nothing is estimated
    here. An earlier edition looked for per-year growth paths under a key the
    bootstrap module never writes, which left this function publishing an empty
    list beside the real distribution; it now reads the key the data actually has,
    and says so if the band is absent rather than silently returning nothing.
    """
    econ = json.loads((DATA / "economy.json").read_text(encoding="utf-8"))
    chart = econ.get("bootstrap", {}).get("chart", {})
    start = A["estimated_market_value_2026"]
    years = chart.get("years") or []
    out = {"start_value": money10(start), "span": span,
           "source": "assets/data/economy.json, bootstrap.chart.years (the seeded 2,000-path resample)",
           "bands": [], "draws": chart.get("draws"),
           "basis": (f"The same resample the projections page draws, restated one year at a time: p05, p50 and "
                     f"p95 of the resampled value, with the model's constant-rate line beside it. "
                     f"{chart.get('note', '')}").strip()}
    for row in years[:span]:
        out["bands"].append({"year": int(row["year"]), "p05": money10(row["p05"]),
                             "p50": money10(row["p50"]), "p95": money10(row["p95"]),
                             "constant": money10(row["constant"])})
    return out


def imputed_rent_breakeven(gap: float, infl: float, rate: float, horizon: int) -> float:
    """First-year rent avoided, growing with inflation, whose accumulation at `rate` equals `gap`.

    `gap` is the terminal-wealth shortfall of living in the home against selling and investing
    (sell path minus live path, both at the horizon). Read as: the housing a comparable home would
    cost, if the heir lived there instead, at which living and selling end level. Rent avoided is
    not taxed, consistent with the letting paths.
    """
    factor = sum((1 + infl) ** j * (1 + rate) ** (horizon - 1 - j) for j in range(horizon))
    return gap / factor


def roll_audit() -> dict:
    """Line-by-line audit of the two published roll tables.

    Answers four questions with arithmetic only, and admits what it cannot answer:

      1. Does each year's owner-supplied growth percentage reproduce from the row
         above it? (Yes, everywhere.)
      2. Does the assessed value ever exceed the Proposition 13 2% cap? (No.)
      3. How much of each bill is fixed charges rather than ad valorem tax? The
         model's bill fit assumes the fixed part grows with inflation; the bills
         themselves say it has moved at a very different pace, and it is a large
         share of the bill, so the 2% cap does not bound the whole bill.
      4. Can the ad valorem rate be identified from the bills? (No - assessed value
         and the fixed part both grow at about 2%, so the rate and the fixed part
         trade off almost exactly. The rate is a published-law figure, not a fit.)
    """
    rA, rB = ASM["ad_valorem_rate_a"]["value"], ASM["ad_valorem_rate_b"]["value"]

    def audit(rows: list[dict], rate: float, cap: float = 0.02) -> dict:
        have = sorted([r for r in rows if r.get("bill")], key=lambda r: r["year"])
        fixed, cap_breach, growth_ok = [], [], []
        prev = None
        for r in rows:  # newest-first in the file
            if prev is not None:
                g = r["assessed"] / prev["assessed"] - 1
                if g > cap + 1e-9:
                    cap_breach.append({"year": prev["year"], "growth_pct": round(g * 100, 3)})
                if r.get("bill") and prev.get("bill"):
                    growth_ok.append({
                        "year": prev["year"],
                        "assessed_pct": round(g * 100, 2),
                        "bill_pct": round((r["bill"] / prev["bill"] - 1) * 100, 2),
                    })
            prev = r
        for r in have:
            fx = r["bill"] - rate * r["assessed"]
            fixed.append({"year": r["year"], "bill": money10(r["bill"]),
                          "assessed": money10(r["assessed"]),
                          "ad_valorem": money10(rate * r["assessed"]),
                          "fixed": money10(fx),
                          "fixed_pct": round(fx / r["bill"] * 100, 1)})
        y0, y1 = fixed[0]["year"], fixed[-1]["year"]
        # Compare the SAME years on both properties, so a rate change and a
        # different window length cannot be mistaken for a trend.
        shared = sorted({f["year"] for f in fixed} & {f["year"] for f in
                         (fixed if y1 - y0 <= 6 else fixed)})
        fmap = {f["year"]: f["fixed"] for f in fixed}
        w0, w1 = (2020, 2025) if 2020 in fmap and 2025 in fmap else (y0, y1)
        g_shared = ((fmap[w1] / fmap[w0]) ** (1 / (w1 - w0)) - 1) if fmap.get(w0) else None
        g_full = ((fixed[-1]["fixed"] / fixed[0]["fixed"]) ** (1 / (y1 - y0)) - 1)
        return {
            "rate_used": rate,
            "base_year": y1,
            "fixed": fixed,
            "fixed_share_latest_pct": fixed[-1]["fixed_pct"],
            "fixed_share_first_pct": fixed[0]["fixed_pct"],
            "window": [y0, y1],
            "fixed_growth_full_pct": round(g_full * 100, 2),
            "fixed_growth_2020_2025_pct": round(g_shared * 100, 2) if g_shared is not None else None,
            "cap_breaches": cap_breach,
            "year_pairs_checked": len(growth_ok),
            "assumption_used_pct": round(ASM["fixed_charge_growth"]["baseline"] * 100, 2),
            "max_bound_share_pct": round((1 - fixed[-1]["fixed"] / fixed[-1]["bill"]) * 100, 1),
        }

    return {"property_a": audit(A["roll"], rA), "property_b": audit(B["roll"], rB)}


def imputed_rent_sensitivity(year: int = 2045) -> dict:
    """What the living path is worth if the roof it provides is given a value.

    The published baseline credits the living path with NOTHING for the shelter it
    provides, while charging it every cost of owning. That is deliberately
    conservative, and it is also a bias: it makes living look worse than it is by
    the value of the housing consumed. This function re-runs the living path with
    the housing credited at 0%, 50%, 75% and 100% of the SAME market rent that
    would make the letting path break even. Both paths then use one piece of
    evidence, which is the only way the comparison is fair.

    The result is a sensitivity, not a new headline: the published recommendation
    still rests on the zero-credit case.
    """
    p = next(x for x in MAIN_RESULT["paths"] if x["inherit_year"] == year)
    rent_annual = float(p["breakeven_rent_annual"])
    base_terminal = p["paths"]["live_in"]["terminal"]
    sell = p["paths"]["sell_equities"]["terminal"]
    horizon = 30
    rate = ASM["equity_return_nominal_gross"]["baseline"] - ASM["equity_tax_drag"]["baseline"]
    rows = []
    for share in (0.0, 0.5, 0.75, 1.0):
        credit = 0.0
        for j in range(horizon):
            credit += rent_annual * share * (1 + INFL) ** j * (1 + rate) ** (horizon - 1 - j)
        rows.append({
            "share": share,
            "annual_credit": money10(rent_annual * share),
            "credit_fv": money10(credit),
            "terminal": money10(base_terminal + credit),
            "gap_to_sell": money10(sell - (base_terminal + credit)),
            "living_wins": (base_terminal + credit) > sell,
        })
    return {"year": year, "rent_annual": money10(rent_annual),
            "rent_monthly": money10(rent_annual / 12),
            "publish_zero": True, "rows": rows}


MAIN_RESULT = {}



# ---------------------------------------------------------------------------
# Insurance band and encumbrance cases. Appended by the 16 November session on
# the owner's instruction to replace round-number assumptions with ranges, and
# to make the debt assumption in the comparison explicit instead of silent.
# Neither function changes a published input: they re-run the same engine at
# other values and report what moves.
# ---------------------------------------------------------------------------
INSURANCE_A = A["annual_costs"]["insurance"]
INSURANCE_B = B["annual_costs"]["insurance"]


def _base_args() -> dict:
    """The published baseline arguments, assembled exactly as main() assembles them."""
    return dict(
        g=ASM["house_growth"]["baseline"], infl=INFL,
        eq=ASM["equity_return_nominal_gross"]["baseline"],
        drag=ASM["equity_tax_drag"]["baseline"],
        tsy=ASM["treasury_yield_nominal"]["baseline"],
        cap_growth=ASM["prop19_cap_growth"]["baseline"],
        sell_pct=ASM["selling_cost_pct"]["baseline"], horizon=ASM["horizon_years"],
        gain_rate=ASM["combined_gain_tax_rate"]["baseline"],
        rec_rate=ASM["depreciation_recapture_rate"]["baseline"],
        exclusion=V["section121_exclusion_single"]["value"],
        fixed_growth=ASM["fixed_charge_growth"]["baseline"], fit_a=FIT_A,
        maint_live=A["annual_costs"]["maintenance_pct_owner_occupied"]["value"],
        maint_rent=A["annual_costs"]["maintenance_pct_rental"]["value"],
        rent_income=RENT_INCOME, imputed_rent=IMPUTED_RENT)


def _rerun(year: int, cost_a_base: float) -> dict:
    return run_paths(inherit_year=year, cost_a_base=cost_a_base, **_base_args())


def insurance_and_encumbrance_cases(year: int = 2045) -> dict:
    """Re-run every path at each rung of the insurance band, and at four debt-service levels.

    Insurance is a carrying cost, so it lands on the paths that keep the building
    and not on the path that sells it. The point of publishing the whole band is to
    show how much of the recommendation that cost carries - and how much a mortgage
    would, if one exists. Nothing here is an estimate of the household's own premium
    or balance: the rungs are the published statewide average for the policy form,
    the owner's figure, and a stated upper scenario.
    """
    base = next(x for x in MAIN_RESULT["paths"] if x["inherit_year"] == year)
    mid = float(INSURANCE_A["mid"])
    rungs = [("official floor, 2017 statewide average for the form",
              float(INSURANCE_A["low"]), "cdi_homeowners_avg"),
             ("owner's estimate, the published baseline", mid, "owner"),
             ("stated upper scenario", float(INSURANCE_A["high"]), "scenario")]
    KEYS = ("sell_equities", "sell_treasury", "live_in", "live_then_rent", "rent_out")
    rows = []
    for label, amount, kind in rungs:
        res = _rerun(year, COST_A_BASE + (amount - mid))
        term = {k: res["paths"][k]["terminal"] for k in KEYS}
        best = max(term, key=lambda k: term[k])
        rows.append({
            # The official rung is printed as the published figure, verbatim; the
            # owner's figure and the stated scenario are rounded like every other
            # dollar amount on the site.
            "label": label,
            "annual": money10(amount) if kind in ("owner", "scenario") else int(amount),
            "kind": kind,
            "terminals": term, "best": best,
            "live_gap": money10(term["live_in"] - base["paths"]["live_in"]["terminal"]),
            "sell_live_gap": money10(term["sell_equities"] - term["live_in"]),
            "letting_gap": money10(term["sell_equities"] - term["rent_out"]),
        })
    band_spread = money10(float(INSURANCE_A["high"]) - float(INSURANCE_A["low"]))
    # The whole band, measured on the model rather than approximated: the low rung and
    # the high rung are both run above, so the difference between them IS the cost of
    # being wrong about insurance, and the gap is what it would have to close.
    gap_live = base["paths"]["sell_equities"]["terminal"] - base["paths"]["live_in"]["terminal"]
    band_effect = rows[0]["terminals"]["live_in"] - rows[-1]["terminals"]["live_in"]
    share_of_gap = round(100.0 * band_effect / gap_live, 2) if gap_live else None

    # Encumbrance cases. The principal is borne on every path - a sale pays it off out
    # of the proceeds, a holder pays it off over time - so what the model can price is
    # the cost of carrying it: interest and the payment stream. These rows add a stated
    # monthly payment to the keeping paths and leave the sale paths alone, which is the
    # effect of a mortgage on the RANKING, not on the wealth of either party.
    debt_rows = []
    for monthly in (0, 500, 1000, 2000):
        extra = monthly * 12.0
        res = _rerun(year, COST_A_BASE + extra) if extra else base
        term = {k: res["paths"][k]["terminal"] for k in KEYS}
        best = max(term, key=lambda k: term[k])
        debt_rows.append({
            "monthly": money10(monthly), "annual": money10(extra),
            "terminals": term, "best": best,
            "live_delta": money10(term["live_in"] - base["paths"]["live_in"]["terminal"]),
            "letting_delta": money10(term["rent_out"] - base["paths"]["rent_out"]["terminal"]),
        })
    return {
        "inherit_year": year,
        "horizon_years": ASM["horizon_years"],
        "band": {"low": money10(INSURANCE_A["low"]), "mid": money10(INSURANCE_A["mid"]),
                 "high": money10(INSURANCE_A["high"]), "spread": band_spread,
                 "effect_on_live": money10(band_effect),
                 "official_floor": int(V["cdi_ho_owner_occupied_avg_2017"]["value"]),
                 "official_floor_year": 2017,
                 "landlord_official_floor": int(V["cdi_df_rental_landlord_avg_2017"]["value"]),
                 "b_low": money10(INSURANCE_B["low"]), "b_mid": money10(INSURANCE_B["mid"]),
                 "b_high": money10(INSURANCE_B["high"])},
        "rows": rows,
        "gap_live_at_baseline": money10(gap_live),
        "band_share_of_gap": share_of_gap,
        "debt_rows": debt_rows,
        "encumbrance_stated": bool(A.get("encumbrance", {}).get("stated_by_owner")),
        "note": ("Insurance is charged to the keeping paths only, so a higher premium "
                 "widens the gap in favour of selling rather than narrowing it. Debt "
                 "service is charged the same way for the same reason."),
    }

# ------------------------------------------------- keep and borrow (R-3) ----
# The last path the brief asks for that the model did not run: keep the home, take
# cash out against the equity instead of selling it, and invest that cash. The estate
# liquidity page priced the carrying cost of borrowing; this prices the path.
#
# Conventions, stated so the arithmetic can be checked line by line:
#   * the loan is level-payment, monthly, at the nominal annual rate divided by
#     twelve, which is how a published mortgage average is quoted and applied;
#   * the cash raised is invested on the same after-tax equity assumption every
#     other path uses, and the debt service is deducted as a compounded outflow at
#     that same rate - the fv_stream convention the carrying costs already use;
#   * no tax deduction is taken for the interest. Publication 936 (2025) states that
#     interest on a home equity loan or line of credit is deductible only where the
#     borrowed funds buy, build or substantially improve the home that secures the
#     loan, so money borrowed to buy securities earns none;
#   * the loan does not change the property tax: Revenue and Taxation Code section
#     62(c)(1) excludes the creation of a security interest from change in ownership,
#     so this path carries exactly the living path's tax bill and no bill of its own.


def _amortise(principal: float, annual_rate: float, years: int) -> dict:
    """Level monthly payment on a fixed-rate loan, with the balance run out year by year."""
    n = years * 12
    i = annual_rate / 12.0
    pay = principal / n if i <= 0 else principal * i / (1.0 - (1.0 + i) ** (-n))
    bal = principal
    interest = 0.0
    yearly = []
    for y in range(years):
        start = bal
        for _ in range(12):
            intr = bal * i
            princ = min(max(pay - intr, 0.0), bal)
            bal -= princ
            interest += intr
        yearly.append({"year": y + 1, "start": start, "end": bal})
    return {"payment_month": pay, "payment_year": pay * 12.0,
            "total_paid": pay * 12.0 * years, "total_interest": interest,
            "balance_at_end": max(bal, 0.0), "yearly": yearly}


def _live_raw(inherit_year: int, *, g: float, infl: float, eq: float, drag: float,
              cap_growth: float, sell_pct: float, gain_rate: float, rec_rate: float,
              exclusion: float, fixed_growth: float, fit_a: dict, cost_a_base: float,
              maint_live: float, imputed_rent: float = 0.0,
              maint_growth: float | None = None, maint_on_value_growth: bool = False) -> dict:
    """The living path, unrounded, with the upkeep assumption exposed as a dial.

    Mirrors the living case in run_paths() and is asserted against it, so the two
    cannot drift. `maint_growth` overrides the rate at which the maintenance and
    repair allowance - and only that allowance - is grown; water, power and
    insurance keep the modelled inflation rate. `maint_on_value_growth` charges the
    percentage against the house value of each year instead of its value at
    inheritance, which is what "a percentage of value" means if the value is the
    current one.
    """
    horizon = ASM["horizon_years"]
    k = inherit_year - 2026
    value_at_death = A["estimated_market_value_2026"] * (1 + g) ** k
    byv = A["roll"][0]["assessed"] * (1 + 0.02) ** k
    cap = V["prop19_value_cap_2025_2027"]["value"] * (1 + cap_growth) ** (inherit_year - 2025)
    taxable_live = byv + max(0.0, value_at_death - (byv + cap))
    fit_t = dict(fit_a)
    fit_t["fixed_base"] = fit_a["fixed_base"] * (1 + fixed_growth) ** (inherit_year - fit_a["base_year"])
    # The base year moves with the pre-grown fixed base, exactly as run_paths() does it
    # (fixed on 2026-11-17 for double growth of the fixed charge). This replica must follow
    # the parent or the assertion below fails, which is what it is there for.
    fit_t["base_year"] = inherit_year
    terminal_price = value_at_death * (1 + g) ** horizon
    bills = annual_bills(taxable_live, fit_t, inherit_year, infl, horizon)
    sale = sale_proceeds(terminal_price, value_at_death, sell_pct, gain_rate, rec_rate, 0.0, exclusion)
    mg = infl if maint_growth is None else maint_growth
    rate_fv = eq - drag
    stream = []
    for j in range(horizon):
        house_value = value_at_death * ((1 + g) ** j if maint_on_value_growth else 1.0)
        stream.append(bills[j] + cost_a_base * (1 + infl) ** j + maint_live * house_value * (1 + mg) ** j)
    carry_fv = fv_stream(stream, rate_fv)
    imp = 0.0
    if imputed_rent:
        imp = sum(float(imputed_rent) * (1 + infl) ** j * (1 + rate_fv) ** (horizon - 1 - j)
                  for j in range(horizon))
    return {"inherit_year": inherit_year, "value_at_death": value_at_death,
            "taxable_live": taxable_live, "terminal_price": terminal_price, "bills": bills,
            "carry_stream": stream, "sale": sale, "carry_fv": carry_fv, "imputed": imp,
            "horizon": horizon, "terminal": sale["net"] - carry_fv + imp}


def _live_base(year: int) -> dict:
    """The published baseline arguments for one living-path run, assembled once."""
    args = _base_args()
    return dict(g=args["g"], infl=args["infl"], eq=args["eq"], drag=args["drag"],
                cap_growth=args["cap_growth"], sell_pct=args["sell_pct"],
                gain_rate=args["gain_rate"], rec_rate=args["rec_rate"],
                exclusion=args["exclusion"], fixed_growth=args["fixed_growth"],
                fit_a=args["fit_a"], cost_a_base=COST_A_BASE,
                maint_live=args["maint_live"], imputed_rent=args["imputed_rent"])


def keep_and_borrow_cases(year: int = 2045) -> dict:
    """Keep the home and take cash out against the equity: does it beat selling?

    One case at each loan-to-value rung, at the published mortgage rate band, plus
    the same cash staged through the canonical Treasury-parking path, plus the
    synthetic crash entry, plus the fee band. The living-path baseline is asserted
    against run_paths() so this function cannot drift from the rest of the site.
    """
    args = _base_args()
    base = _live_base(year)
    horizon = ASM["horizon_years"]
    live = _live_raw(year, **base)
    check = run_paths(inherit_year=year, cost_a_base=COST_A_BASE,
                      **{k: v for k, v in args.items() if k != "imputed_rent"})["paths"]["live_in"]["terminal"]
    assert money10(live["terminal"]) == check, (
        f"living-path replication drifted from run_paths: {money10(live['terminal'])} vs {check}")

    sale = sale_proceeds(live["value_at_death"], live["value_at_death"], args["sell_pct"],
                         args["gain_rate"], args["rec_rate"], 0.0)
    sell_terminal = sale["net"] * (1 + args["eq"] - args["drag"]) ** horizon

    rate = ASM["borrow_rate"]
    fee = ASM["borrow_fee_pct"]
    term = int(ASM["borrow_term_years"]["value"])
    rungs = list(ASM["borrow_ltv_rungs"]["value"])

    def case(ltv: float, r: float, f: float, mode: str = "immediate") -> dict:
        principal = ltv * live["value_at_death"]
        fees = f * principal
        net_cash = principal - fees
        loan = _amortise(principal, r, term)
        if mode == "shock":
            seq = [-0.40, 0.25, 0.10]
            acc = 1.0
            for y in range(horizon):
                acc *= (1 + (seq[y] if y < len(seq) else args["eq"] - args["drag"]))
            grown = net_cash * acc
        elif mode == "staged":
            _treasury, _equity = monthly_phase(net_cash, PARK_MONTHS, PHASE_MONTHS, horizon * 12,
                                               PARK_TSY, args["eq"], args["drag"])
            grown = _treasury + _equity
        else:
            grown = net_cash * (1 + args["eq"] - args["drag"]) ** horizon
        pay_fv = fv_stream([loan["payment_year"]] * horizon, args["eq"] - args["drag"])
        balance = loan["balance_at_end"] if term > horizon else 0.0
        terminal = live["terminal"] - pay_fv + grown - balance
        return {"mode": mode, "ltv": ltv, "rate": r, "fee_pct": f, "principal": principal,
                "fees": fees, "net_cash": net_cash, "payment_month": loan["payment_month"],
                "payment_year": loan["payment_year"], "total_paid": loan["total_paid"],
                "total_interest": loan["total_interest"], "balance_at_end": balance,
                "cash_grown": grown, "payments_fv": pay_fv, "terminal": terminal,
                "vs_sell": terminal - sell_terminal,
                "vs_live": terminal - live["terminal"]}

    rows = [case(l, rate["baseline"], fee["baseline"]) for l in rungs]
    staged = [case(l, rate["baseline"], fee["baseline"], "staged") for l in rungs]
    shocked = [case(l, rate["baseline"], fee["baseline"], "shock") for l in rungs]
    # The same leveraged position, uninvested: the cash left in a cheque account
    # earning nothing, which is what a borrower who never invests actually holds.
    idle = []
    for l in rungs:
        c = case(l, rate["baseline"], fee["baseline"])
        c2 = dict(c)
        c2["cash_grown"] = c["net_cash"]
        c2["terminal"] = live["terminal"] - c["payments_fv"] + c["net_cash"] - c["balance_at_end"]
        c2["vs_sell"] = c2["terminal"] - sell_terminal
        c2["vs_live"] = c2["terminal"] - live["terminal"]
        c2["mode"] = "idle"
        idle.append(c2)
    rate_runs = {tag: [case(l, rate[tag] if tag != "mid" else rate["baseline"], fee["baseline"])
                       for l in rungs] for tag in ("low", "high")}
    fee_runs = [case(rungs[-1], rate["baseline"], f) for f in (fee["low"], fee["baseline"], fee["high"])]
    balance_path = _amortise(rows[1]["principal"], rate["baseline"], term)["yearly"]

    # Two thresholds, both solved rather than asserted.
    # 1. Against selling: is there ANY after-tax equity return at which keeping the
    #    house and borrowing against it matches selling it? Tested across -2% to +30%
    #    a year. It cannot cross, because a lender advances a share of the value while
    #    a sale realises the whole of it less costs, and both sums then compound at the
    #    same rate; the loan adds a bill the sale does not carry.
    def gap_sell(ret: float, idx: int = 1) -> float:
        c = case(rungs[idx], rate["baseline"], fee["baseline"])
        grown = c["net_cash"] * (1 + ret) ** horizon
        pay_fv = fv_stream([c["payment_year"]] * horizon, ret)
        return (live["terminal"] + grown - pay_fv - c["balance_at_end"]
                - sale["net"] * (1 + ret) ** horizon)

    sell_band = {"low": money10(gap_sell(-0.02)), "high": money10(gap_sell(0.30)),
                 "crosses": gap_sell(-0.02) * gap_sell(0.30) <= 0}

    # 2. Against simply living there without borrowing: the return the borrowed cash
    #    has to earn for the leveraged keep to beat the unleveraged keep. This one does
    #    cross, and where it crosses is close to the loan rate, which is the whole
    #    point of the exercise.
    def gap_live(ret: float, idx: int = 1) -> float:
        c = case(rungs[idx], rate["baseline"], fee["baseline"])
        grown = c["net_cash"] * (1 + ret) ** horizon
        pay_fv = fv_stream([c["payment_year"]] * horizon, ret)
        return grown - pay_fv - c["balance_at_end"]

    lo, hi = -0.02, 0.40
    breakeven = None
    if gap_live(lo) * gap_live(hi) <= 0:
        for _ in range(120):
            mid = (lo + hi) / 2
            if gap_live(lo) * gap_live(mid) <= 0:
                hi = mid
            else:
                lo = mid
        breakeven = (lo + hi) / 2
    return {
        "inherit_year": year, "horizon_years": horizon, "term_years": term,
        "value_at_death": money10(live["value_at_death"]),
        "live_terminal": money10(live["terminal"]),
        "sell_terminal": money10(sell_terminal),
        "gap_sell_minus_live": money10(sell_terminal - live["terminal"]),
        "rate": rate["baseline"], "rate_low": rate["low"], "rate_high": rate["high"],
        "rate_basis": rate["basis"], "rate_src": rate.get("src", []),
        "fee_pct": fee["baseline"], "fee_low": fee["low"], "fee_high": fee["high"],
        "fee_basis": fee["basis"], "ltv_rungs": rungs,
        "after_tax_equity": pct(args["eq"] - args["drag"], 2),
        "negative_carry": pct(rate["baseline"] - (args["eq"] - args["drag"]), 2),
        "deduction_rule": ASM["borrow_interest_deduction"]["rule"],
        "deduction_src": ASM["borrow_interest_deduction"]["src"],
        "property_tax_rule": ASM["borrow_property_tax_rule"]["rule"],
        "property_tax_src": ASM["borrow_property_tax_rule"]["src"],
        "rows": [_fmt_borrow(c) for c in rows],
        "staged_rows": [_fmt_borrow(c) for c in staged],
        "shock_rows": [_fmt_borrow(c) for c in shocked],
        "idle_rows": [_fmt_borrow(c) for c in idle],
        "rate_rows": {tag: [_fmt_borrow(c) for c in rs] for tag, rs in rate_runs.items()},
        "fee_rows": [_fmt_borrow(c) for c in fee_runs],
        "balance_path": [{"after_years": r["year"], "balance": money10(r["end"])}
                         for r in balance_path if r["year"] in (5, 10, 15, 20, 25, 30)],
        "breakeven_vs_live": (pct(breakeven, 2) if breakeven is not None else None),
        "breakeven_vs_live_note": (
            "The after-tax equity return at which the middle rung (the second-highest loan-to-value "
            "scenario) stops being a worse way to hold the same house than simply living in it. It is solved "
            "by bisection, and it sits a little above the loan rate because the payment schedule amortises "
            "the balance while the cash is invested as one lump at the start."),
        "sell_band": sell_band,
    }


def _fmt_borrow(c: dict) -> dict:
    return {"mode": c["mode"], "ltv": c["ltv"], "rate": c["rate"], "fee_pct": c["fee_pct"],
            "principal": money10(c["principal"]), "fees": money10(c["fees"]),
            "net_cash": money10(c["net_cash"]), "payment_month": money10(c["payment_month"]),
            "payment_year": money10(c["payment_year"]), "total_paid": money10(c["total_paid"]),
            "total_interest": money10(c["total_interest"]),
            "balance_at_end": money10(c["balance_at_end"]), "cash_grown": money10(c["cash_grown"]),
            "payments_fv": money10(c["payments_fv"]), "terminal": money10(c["terminal"]),
            "vs_sell": money10(c["vs_sell"]), "vs_live": money10(c["vs_live"])}


def _upkeep_series() -> list:
    """The published federal household-upkeep record, read from the registered values."""
    out = []
    y = 2015
    while True:
        v = V.get(f"bls_ce_upkeep_owner_{y}", {}).get("value")
        if v is None:
            break
        out.append({"year": y, "value": int(v)})
        y += 1
    return out


def _upkeep_measured_growth() -> float:
    series = _upkeep_series()
    if len(series) < 2:
        return 0.0
    span = series[-1]["year"] - series[0]["year"]
    return (series[-1]["value"] / series[0]["value"]) ** (1.0 / span) - 1.0


def maintenance_evidence() -> dict:
    """What owners actually spend on upkeep, from the official record, as a cross-check.

    The model carries maintenance as a percentage of value, grown with inflation,
    because no quote was supplied for either building. This reads the Business
    Release Cycle series the Bureau of Labor Statistics Consumer Expenditure
    Surveys publish for homeowners - maintenance, repairs, insurance and other
    expenses of an owned dwelling - and asks it two questions: is the level
    plausible for a house of this value, and is inflation the right growth rate to
    project it with? The line bundles insurance with upkeep and averages every house
    size in the country, so it is an upper bound on maintenance alone, and both
    limits are printed with it rather than after it.
    """
    series = _upkeep_series()
    lo, hi = series[0], series[-1]
    span = hi["year"] - lo["year"]
    cagr = (hi["value"] / lo["value"]) ** (1.0 / span) - 1.0
    cpi = SERIES["cpi"]["values"]
    cpi_cagr = (float(cpi[str(hi["year"])]) / float(cpi[str(lo["year"])])) ** (1.0 / span) - 1.0
    infl = ASM["inflation"]["baseline"]
    a_val = A["estimated_market_value_2026"]
    b_val = B["estimated_market_value_2026"]
    own = A["annual_costs"]["maintenance_pct_owner_occupied"]["value"]
    rent = A["annual_costs"]["maintenance_pct_rental"]["value"]
    b_rate = B["annual_costs"]["maintenance_pct"]["value"]
    ins_a = A["annual_costs"]["insurance"]["mid"]
    ins_b = B["annual_costs"]["insurance"]["mid"]
    return {"series": series, "span_years": span, "start_year": lo["year"], "end_year": hi["year"],
            "start_value": lo["value"], "end_value": hi["value"],
            "measured_growth": pct(cagr, 2), "cpi_growth_same_span": pct(cpi_cagr, 2),
            "model_growth": pct(infl, 2), "ratio_to_model_growth": round(cagr / infl, 2),
            "allowance_a_live": money10(a_val * own), "allowance_a_rent": money10(a_val * rent),
            "allowance_b": money10(b_val * b_rate), "national_mean": int(hi["value"]),
            "ratio_a_live": round((a_val * own + ins_a) / hi["value"], 2),
            "ratio_a_rent": round((a_val * rent + ins_a) / hi["value"], 2),
            "ratio_b": round((b_val * b_rate + ins_b) / hi["value"], 2),
            "housing_2025": money10(V["bls_ce_housing_all_cu_2025"]["value"]),
            "operations_2025": money10(V["bls_ce_household_operations_2025"]["value"]),
            "measured_growth_fraction": cagr,
            "src": ["bls_cex_ownmaint", "bls_cesan2025", "bls_cpi_annual"]}


def maintenance_growth_cases(year: int = 2045) -> dict:
    """Re-run the living path with upkeep inflating faster than CPI.

    The published record grows about three times as fast as the model's inflation
    assumption. If that keeps running, a thirty-year hold costs more than the
    baseline says. Two dials are tested: the rate at which the allowance grows, and
    whether the percentage is charged on the value at inheritance (the model's
    convention) or on the value of each year.
    """
    base = _live_base(year)
    measured = _upkeep_measured_growth()
    rungs = sorted(set(list(ASM["maintenance_growth_cases"]["value"]) + [round(measured, 4)]))
    baseline = _live_raw(year, **base)
    rows = []
    for mg in rungs:
        c = _live_raw(year, **{**base, "maint_growth": mg})
        label = ("the modelled inflation rate" if abs(mg - base["infl"]) < 1e-9 else
                 ("the measured 2015-2024 record" if abs(mg - measured) < 5e-5 else "stated rung"))
        rows.append({"growth": pct(mg, 2), "label": label, "carry_fv": money10(c["carry_fv"]),
                     "terminal": money10(c["terminal"]),
                     "vs_base": money10(c["terminal"] - baseline["terminal"]),
                     "on_current_value": False})
    for mg, tag in ((base["infl"], "at the modelled inflation rate"),
                    (measured, "at the measured rate")):
        c = _live_raw(year, **{**base, "maint_growth": mg, "maint_on_value_growth": True})
        rows.append({"growth": pct(mg, 2), "label": f"charged on the house value each year, {tag}",
                     "carry_fv": money10(c["carry_fv"]), "terminal": money10(c["terminal"]),
                     "vs_base": money10(c["terminal"] - baseline["terminal"]), "on_current_value": True})
    return {"inherit_year": year, "baseline_terminal": money10(baseline["terminal"]),
            "measured_growth": pct(measured, 2), "rows": rows,
            "src": ASM["maintenance_growth_cases"].get("src", [])}


def _append_extras(out: dict) -> dict:
    """Run after main() has built `out`, without editing main()'s body."""
    global MAIN_RESULT
    MAIN_RESULT = out
    out["surcharge_sensitivity"] = surcharge_sensitivity(2045)
    out["projections_distribution"] = projections_distribution(30)
    out["roll_audit"] = roll_audit()
    out["imputed_rent"] = imputed_rent_sensitivity(2045)
    out["cost_cases"] = insurance_and_encumbrance_cases(2045)
    out["maintenance_evidence"] = maintenance_evidence()
    out["maintenance_growth_cases"] = maintenance_growth_cases(2045)
    out["borrow_cases"] = keep_and_borrow_cases(2045)
    return out


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
        "meta": {"built": edition.BUILD_DATE_ISO, "rounding": "nearest $10",
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
        "phased": [],
        "regimes": [],
        "replay": historical_replay(30),
        "estate": estate_scenarios(),
        "exclusion_projection": exclusion_projection(),
        "prop19_cap_projection": prop19_cap_projection(),
        "sensitivity": sensitivity(2045),
        "sensitivity_fine": sensitivity_fine(),
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
                        maint_live=maint_live, maint_rent=maint_rent,
                        rent_income=RENT_INCOME,
                        imputed_rent=IMPUTED_RENT)
        t_eq = res["paths"]["sell_equities"]["terminal"]
        res["breakeven_rent_annual"] = breakeven_rent(
            year, g, infl, eq, drag, cap_growth, sell_pct, horizon, gain_rate,
            rec_rate, infl, FIT_A, COST_A_BASE, maint_rent, t_eq)
        res["breakeven_rent_monthly"] = money10(res["breakeven_rent_annual"] / 12)
        gap_live = res["paths"]["sell_equities"]["terminal"] - res["paths"]["live_in"]["terminal"]
        res["imputed_rent_breakeven_annual"] = money10(
            imputed_rent_breakeven(gap_live, infl, eq - drag, horizon))
        res["imputed_rent_breakeven_monthly"] = money10(res["imputed_rent_breakeven_annual"] / 12)
        res["breakeven_return_vs_live"] = breakeven_return(
            year, g, cap_growth, sell_pct, horizon, gain_rate, rec_rate,
            res["paths"]["live_in"]["terminal"])
        res["breakeven_return_vs_rent"] = breakeven_return(
            year, g, cap_growth, sell_pct, horizon, gain_rate, rec_rate,
            res["paths"]["rent_out"]["terminal"])
        res["housing_value_needed"] = money10(annuity_fv(
            t_eq - res["paths"]["live_in"]["terminal"], eq - drag, horizon))
        res["breakeven_house_growth"] = breakeven_house_growth(
            year, eq, drag, cap_growth, sell_pct, horizon, gain_rate, rec_rate,
            V["section121_exclusion_single"]["value"], maint_live)
        res["best_path"] = max(res["paths"], key=lambda k: res["paths"][k]["terminal"])
        out["paths"].append(res)
        phased = run_phased_path(
            inherit_year=year, g=g, infl=infl, eq=eq, drag=drag, tsy_short=PARK_TSY,
            horizon=horizon, sell_pct=sell_pct, gain_rate=gain_rate, rec_rate=rec_rate,
            exclusion=V["section121_exclusion_single"]["value"],
            fixed_growth=ASM["fixed_charge_growth"]["baseline"], fit_a=FIT_A, cost_a_base=COST_A_BASE,
            maint_live=maint_live, maint_rent=maint_rent, rent_income=RENT_INCOME,
            park_months=PARK_MONTHS,
            phase_months=PHASE_MONTHS)
        phased["inherit_year"] = year
        out["phased"].append(phased)

    p45 = next(p for p in out["paths"] if p["inherit_year"] == 2045)
    proceeds45 = p45["paths"]["sell_equities"]["sale"]["net"]
    out["phased_stress"] = phased_stress(proceeds45)
    out["backtest"] = crash_entry_backtest(proceeds45)

    # Parcel tax approved in Property B's city (official terms, publisher
    # withheld for privacy) and the stated-level imputed-rent sensitivity on the
    # living paths (levels are scenarios; the real input is empty).
    out["prop_h"] = prop_h_schedule()
    out["imputed_rent_levels"] = imputed_rent_level_cases(
        p45, infl, eq, drag, g, cap_growth, sell_pct, horizon, gain_rate, rec_rate)

    for regime in regime_stress():
        out["regimes"].append({**regime, "run": run_regime(regime, horizon)})

    # Real historical entry-timing replays (1929, 2000, 2008, 2020). Deterministic:
    # the module reads the verbatim official CSVs in assets/data/episodes and never
    # downloads, interpolates or invents a value.
    out["episodes"] = EP.build()

    # Extras are attached by the appended block at the end of this file, so that
    # concurrent sessions editing main() do not collide with new sections.
    _append_extras(out)
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
