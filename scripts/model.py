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
TSY_SHORT = ASM["treasury_short_yield_nominal"]["baseline"]


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


def depreciation_schedule(value: float, horizon: int, share: float = 0.8,
                          life: float = 27.5) -> list[float]:
    """Annual depreciation on the improvements: straight line over 27.5 years.

    80% of the value is treated as improvements and the rest as land, which
    is not depreciable. The schedule stops when the improvements are fully
    depreciated, so a horizon longer than the recovery period does not keep
    generating a deduction. The total over the horizon equals
    min(share * value, share * value / life * horizon), which is what the sale
    figures have always used, so the basis at sale is unchanged.
    """
    remaining = share * value
    annual = remaining / life
    out = []
    for _ in range(horizon):
        take = min(annual, remaining)
        out.append(take)
        remaining -= take
    return out


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


def run_paths(inherit_year: int, g: float, infl: float, eq: float, drag: float,
              tsy: float, cap_growth: float, sell_pct: float, horizon: int,
              gain_rate: float, rec_rate: float, exclusion: float,
              fixed_growth: float, fit_a: dict, cost_a_base: float,
              maint_live: float, maint_rent: float,
              rent_income: float | None = None) -> dict:
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

    # Path 4: let it out from the start, then sell
    bills_rent = annual_bills(taxable_rent, fit_T, inherit_year, infl, horizon)
    tax_rent = sum(bills_rent)
    cost_rent = carrying_costs(value_at_death, cost_a_base, maint_rent, infl, horizon)
    dep_sched = depreciation_schedule(value_at_death, horizon)
    deprec = sum(dep_sched)
    rent_sale = sale_proceeds(terminal_price, value_at_death - deprec, sell_pct,
                              gain_rate, rec_rate, deprec)
    # The depreciation deduction is claimed every year it is available, and it
    # reduces ordinary income tax. The model previously reduced the basis at
    # sale - and so charged the recapture tax - without ever crediting the
    # annual deduction that offsets it. That made the letting path look worse
    # than it is, and it made a property kept empty look better than the same
    # property let, which is the wrong way round. The shield is credited here
    # at the same rate the recapture is charged.
    dep_shield = [d * rec_rate for d in dep_sched]
    rent_cash = rent_accumulated(horizon)
    # Net rental cash: gross rent less the same tax and running costs, compounded.
    rent_carry_fv = fv_stream(
        [rent0 * (1 + infl) ** j - bills_rent[j]
         - (cost_a_base + maint_rent * value_at_death) * (1 + infl) ** j
         + dep_shield[j]
         for j in range(horizon)], rate_fv)

    # Path 6: phased investing - sell at inheritance, park the sale proceeds in short-term
    # Treasuries for the parking period (24-36 months), then phase into equities for the
    # remainder of the horizon. This is the crash-entry softener: it tests whether keeping the
    # proceeds out of equities through the first market shock (1929/2008 style) and buying in
    # afterwards improves the terminal value versus going fully into equities on day one.
    # Phased investing, through the one canonical engine. The parking length is
    # the owner's instruction (24 to 36 months; the baseline is the midpoint).
    # The engine is the same one the black-swan entry-timing table uses, so the
    # headline figure and the stress table measure one thing.
    phase_eng = phased_engine(
        sale["net"], horizon * 12,
        int(ASM["phased_investing_park_months"]["baseline"]),
        int(ASM["phased_equity_phase_months"]["value"]),
        TSY_SHORT, eq - drag)
    phase_terminal = money10(phase_eng["terminal"])

    # Path 5: live in it for two years, then let it out for the rest
    bills_h1 = annual_bills(taxable_live, fit_T, inherit_year, infl, 2)
    tax_h1 = sum(bills_h1)
    fit_T2 = dict(fit_T)
    fit_T2["fixed_base"] = fit_T["fixed_base"] * (1 + fixed_growth) ** 2
    av_after = taxable_rent * 1.02 ** 2
    bills_h2 = annual_bills(av_after, fit_T2, inherit_year + 2, infl, horizon - 2)
    tax_h2 = sum(bills_h2)
    cost_h = carrying_costs(value_at_death, cost_a_base, maint_rent, infl, horizon)
    # The property is lived in for the first two years and let only after
    # that, so no depreciation is claimed until it is actually placed in
    # service. The schedule therefore covers the letting years only, and the
    # shield is applied to those years and not to the two lived-in years.
    dep_sched_h = depreciation_schedule(value_at_death, horizon - 2)
    deprec_h = sum(dep_sched_h)
    dep_shield_h = [0.0, 0.0] + [d * rec_rate for d in dep_sched_h]
    # No Section 121 exclusion on the hybrid path. Publication 523 requires
    # the owner to have used the home as a residence for at least 24 months of
    # the 5 years before the sale. On this path the heir moves out after two
    # years and lets the property for the remaining twenty-eight, so at the
    # sale the 5-year window contains no residence at all and the exclusion
    # does not apply. The model previously applied it here.
    hybrid_sale = sale_proceeds(terminal_price, value_at_death - deprec_h, sell_pct,
                                gain_rate, rec_rate, deprec_h)
    hybrid_cash = rent_accumulated(horizon - 2)
    # Net rental cash for the years let: gross rent (hybrid_cash, already compounded) less the
    # tax and running costs of every year of the horizon, compounded at the same rate.
    hybrid_out_fv = fv_stream(
        [(bills_h1 + bills_h2)[j] + (cost_a_base + maint_rent * value_at_death) * (1 + infl) ** j
         - dep_shield_h[j]
         for j in range(horizon)], rate_fv)
    hybrid_carry_fv = hybrid_cash - hybrid_out_fv

    # Path 7: retain the house without occupying it and without letting it out.
    # The brief asks for this comparison explicitly, so it is priced rather than
    # described. Three things make it different from every other path:
    #   * no occupancy means no Proposition 19 shelter and no homestead
    #     exemption, so the property is reassessed to full value, the same
    #     treatment the letting path receives;
    #   * a property held for personal use is not used in a trade or business,
    #     so no depreciation is allowable and there is no recapture on sale;
    #   * no Section 121 exclusion is available on the eventual sale, because
    #     the property was never the heir's principal residence.
    # The vacant maintenance rate is a stated assumption: the higher of the
    # two rates on file, because a vacant property has no occupant doing the
    # small repairs.
    bills_vac = annual_bills(taxable_rent, fit_T, inherit_year, infl, horizon)
    tax_vac = sum(bills_vac)
    cost_vac = carrying_costs(value_at_death, cost_a_base, maint_rent, infl, horizon)
    vac_sale = sale_proceeds(terminal_price, value_at_death, sell_pct, gain_rate, rec_rate, 0.0)
    vac_carry_fv = fv_stream(
        [bills_vac[j] + (cost_a_base + maint_rent * value_at_death) * (1 + infl) ** j
         for j in range(horizon)], rate_fv)

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
            "live_in": {"terminal": money10(live["net"] - live_carry_fv),
                        "outflow": money10(tax_live + cost_live),
                        "carry_fv": money10(live_carry_fv),
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
                                "parked_at_park_end": money10(phase_eng["parked_at_park_end"]),
                                "equity_at_park_end": money10(phase_eng["equity"]),
                                "park_months": phase_eng["park_months"],
                                "phase_months": phase_eng["phase_months"]},
            "retain_vacant": {"terminal": money10(vac_sale["net"] - vac_carry_fv),
                               "outflow": money10(tax_vac + cost_vac),
                               "carry_fv": money10(vac_carry_fv),
                               "tax_total": money10(tax_vac),
                               "cost_total": money10(cost_vac),
                               "sale": vac_sale},
            "live_then_rent": {"terminal": money10(hybrid_sale["net"] + hybrid_carry_fv),
                               "outflow": money10(tax_h1 + tax_h2 + cost_h),
                               "carry_fv": money10(hybrid_carry_fv),
                               "tax_total": money10(tax_h1 + tax_h2),
                               "cost_total": money10(cost_h),
                               "rent_income_total": money10(hybrid_cash),
                               "depreciation": money10(deprec_h),
                               "sale": hybrid_sale},
        },
    }


# ------------------------------------------------------ phased investing ---
# One canonical implementation of the owner's instruction: park the sale
# proceeds in 3-month to 2-year Treasuries for 24 to 36 months after the
# inheritance, then phase into equities.
#
# Before this consolidation four implementations of this path existed, each
# with its own Treasury assumption and its own mechanic, so the dashboard
# headline, the decision paths, the sensitivity grid and the black-swan
# entry-timing table were measuring different things under one label. The
# engine below is the only mechanic; every published phased figure comes
# from it.

# The crash-at-entry sequence used by the stress test. This is a STATED
# SCENARIO, not a historical return: no official series goes back to the
# 1929 crash and no agency publishes a forward market path. The page that
# uses it says so in the same words.
CRASH_SCENARIO = (-0.40, -0.20, -0.10)


def _monthly_rate(annual: float) -> float:
    """Effective monthly rate implied by an annual effective rate."""
    return (1.0 + annual) ** (1.0 / 12.0) - 1.0


def phased_engine(net: float, total_months: int, park_months: int, phase_months: int,
                  tsy_short: float, eq_net_annual: float,
                  crash_annual: tuple | None = None, lump: bool = False) -> dict:
    """The single monthly engine behind every published phased-investing figure.

    Mechanics:
      * the net sale proceeds sit in short Treasuries for `park_months`;
      * over the following `phase_months` the balance is drawn down into
        equities in equal monthly amounts. Each purchase is a share of the
        balance then held, so the interest earned while parked is invested
        along with the principal and the balance reaches zero when the
        phase ends;
      * money not yet invested keeps earning the Treasury rate;
      * equities earn the net equity rate from the month they are bought.

    `lump=True` puts the whole balance into equities in month one, which is
    the comparator for the phased path.

    `crash_annual` is an optional tuple of annual equity returns applied to
    the first years of the horizon, then the baseline net equity rate.
    """
    total_months = max(0, int(total_months))
    park_months = max(0, min(int(park_months), total_months))
    phase_months = max(0, min(int(phase_months), total_months - park_months))
    phase_start = park_months + 1
    phase_end = park_months + phase_months

    m_tsy = _monthly_rate(tsy_short)
    m_eq = _monthly_rate(eq_net_annual)

    crash_monthly: list[float] = []
    for r in (crash_annual or ()):
        crash_monthly.extend([_monthly_rate(r)] * 12)

    treasury = 0.0 if lump else float(net)
    equity = float(net) if lump else 0.0
    parked_at_park_end = 0.0

    for month in range(1, total_months + 1):
        m = m_eq
        if crash_monthly and month <= len(crash_monthly):
            m = crash_monthly[month - 1]
        if not lump:
            treasury *= (1 + m_tsy)
        equity *= (1 + m)
        if not lump and phase_start <= month <= phase_end:
            months_left = phase_end - month + 1
            contribution = treasury / months_left
            treasury -= contribution
            equity += contribution
        if month == park_months and park_months > 0:
            parked_at_park_end = treasury

    return {
        "terminal": treasury + equity,
        "treasury": treasury,
        "equity": equity,
        "parked_at_park_end": parked_at_park_end,
        "park_months": park_months,
        "phase_months": phase_months,
    }


def run_phased_path(inherit_year: int, g: float, infl: float, eq: float, drag: float,
                    tsy_short: float, horizon: int, sell_pct: float, gain_rate: float,
                    rec_rate: float, exclusion: float, fixed_growth: float, fit_a: dict,
                    cost_a_base: float, maint_live: float, maint_rent: float,
                    rent_income: float | None, park_months: int, phase_months: int,
                    crash_annual: tuple | None = None) -> dict:
    """Sell at inheritance, park the net proceeds in short Treasuries (3M-2Y),
    then phase into equities by equal monthly amounts.

    The point of the path is entry-risk sequencing: instead of putting the
    whole sale proceeds into equities at a single moment - which could be the
    top before a 1929- or 2008-style crash - the money earns a short-Treasury
    yield while it is phased in, so part of the portfolio is never exposed to
    an equity drawdown and the equity purchases are spread across prices.

    Returns the terminal value and the net sale proceeds, both rounded to the
    nearest $10.
    """
    k = inherit_year - 2026
    value_at_death = A["estimated_market_value_2026"] * (1 + g) ** k
    sale = sale_proceeds(value_at_death, value_at_death, sell_pct, gain_rate, rec_rate, 0.0)
    eng = phased_engine(sale["net"], horizon * 12, park_months, phase_months,
                        tsy_short, eq - drag, crash_annual)
    return {
        "terminal": money10(eng["terminal"]),
        "net_proceeds": money10(sale["net"]),
        "treasury_portion": money10(eng["treasury"]),
        "equity_portion": money10(eng["equity"]),
        "parked_at_park_end": money10(eng["parked_at_park_end"]),
        "park_months": eng["park_months"],
        "phase_months": eng["phase_months"],
    }


def crash_entry_comparison(inherit_year: int, g: float, infl: float, eq: float, drag: float,
                           tsy_short: float, horizon: int, sell_pct: float, gain_rate: float,
                           rec_rate: float, exclusion: float, fixed_growth: float, fit_a: dict,
                           cost_a_base: float, maint_live: float, maint_rent: float,
                           rent_income: float | None, park_months: int, phase_months: int,
                           crash_annual: tuple = CRASH_SCENARIO) -> dict:
    """Sequence-of-returns comparison: lump-sum equity entry versus phased entry.

    Both paths sell Property A at inheritance and invest the same net proceeds.
    The lump-sum path is fully exposed from month 1. The phased path parks in
    short Treasuries for park_months, then draws the balance into equities over
    phase_months. During the crash years both equity paths earn the stated
    crash sequence; Treasuries earn tsy_short throughout. This isolates the
    sequencing benefit of phasing: money not yet in equities avoids the
    drawdown and is deployed at lower prices.

    The crash sequence is CRASH_SCENARIO - annual equity returns of -40%,
    then -20%, then -10%, then the baseline net equity rate. These are
    STATED SCENARIOS, not official figures: no data series goes back to 1929
    and no official source publishes a forward crash path.
    """
    k = inherit_year - 2026
    value_at_death = A["estimated_market_value_2026"] * (1 + g) ** k
    sale = sale_proceeds(value_at_death, value_at_death, sell_pct, gain_rate, rec_rate, 0.0)
    net = sale["net"]
    total_months = horizon * 12

    lump = phased_engine(net, total_months, 0, 0, tsy_short, eq - drag,
                         crash_annual, lump=True)
    phased = phased_engine(net, total_months, park_months, phase_months,
                            tsy_short, eq - drag, crash_annual)

    lump_terminal = money10(lump["terminal"])
    phased_terminal = money10(phased["terminal"])
    return {
        "net_proceeds": money10(net),
        "lump_sum_equities": lump_terminal,
        "phased_terminal": phased_terminal,
        # Computed from the published figures, not from the unrounded ones, so
        # the advantage a reader sees is exactly the difference of the two
        # terminal values printed beside it.
        "phased_advantage": phased_terminal - lump_terminal,
        "crash_years": len(crash_annual or ()),
        "crash_annual_returns": [round(r, 4) for r in (crash_annual or ())],
        "park_months": phased["park_months"],
        "phase_months": phased["phase_months"],
    }


def property_b_comparison(inherit_year: int = 2045) -> dict:
    """What the already-owned Property B contributes to the same horizon.

    The brief asks for the already-owned property to be compared alongside
    Property A rather than described in prose. This prices it on the same
    30-year horizon and the same conventions as the Property A paths:

      * the market value grows at the same house-growth assumption;
      * the assessed value grows at the 2% Proposition 13 cap;
      * the rent is the owner's own figure for the two let units, grown with
        inflation. It is an owner statement, not a verified lease, and it is
        labelled that way wherever it appears;
      * the running costs are the owner's own figures, the maintenance at the
        stated percentage of value;
      * the sale at the end of the horizon is priced on the heir's own
        original cost basis, which the site does not have, so no capital gain
        is computed on the sale. The terminal value is therefore the market
        value at the end of the horizon plus the accumulated net rent, less
        the tax and running costs.

    The missing basis is disclosed rather than assumed, because assuming a
    purchase price the owner never supplied would be inventing the figure
    that most changes the answer.
    """
    g = ASM["house_growth"]["baseline"]
    infl = ASM["inflation"]["baseline"]
    eq = ASM["equity_return_nominal_gross"]["baseline"]
    drag = ASM["equity_tax_drag"]["baseline"]
    horizon = ASM["horizon_years"]
    rate_fv = eq - drag

    k = inherit_year - 2026
    value_at_inherit = B["estimated_market_value_2026"] * (1 + g) ** k
    value_at_end = value_at_inherit * (1 + g) ** horizon
    assessed_start = float(B["roll"][0]["assessed"]) * (1 + 0.02) ** k
    fit_T = dict(FIT_B)
    fit_T["fixed_base"] = FIT_B["fixed_base"] * (1 + INFL) ** (inherit_year - FIT_B["base_year"])

    bills = annual_bills(assessed_start, fit_T, inherit_year, infl, horizon)
    tax_total = sum(bills)

    rent0 = float(B["rent"]["annual"])
    cost_base = COST_B_BASE
    maint_pct = B["annual_costs"]["maintenance_pct"]["value"]
    # Maintenance follows the same convention as the Property A paths: a
    # percentage of the value at the start of the horizon, inflated each year.
    # A building's upkeep tracks its condition and its running cost, not the
    # market value it happens to be carrying, so tying maintenance to a
    # growing market value would manufacture a drag that the owner would not
    # actually bear.
    costs, rents = [], []
    for j in range(horizon):
        costs.append((cost_base + maint_pct * value_at_inherit) * (1 + infl) ** j)
        rents.append(rent0 * (1 + infl) ** j)
    cost_total = sum(costs)
    rent_total = sum(rents)

    # Carrying cost and rent, each compounded at the same after-tax equity
    # rate the Property A paths use, so the two properties' cash flows are
    # compared on one convention.
    carry_fv = fv_stream([bills[j] + costs[j] for j in range(horizon)], rate_fv)
    rent_fv = fv_stream(rents, rate_fv)

    # The same terminal-value convention as the Property A paths: the property
    # is sold at the end of the horizon, the selling cost is deducted, and the
    # compounded carrying cost is charged. One thing is missing, and it is
    # missing because the input is missing, not because it is small: the
    # heir's original cost basis for Property B is not supplied and is not
    # published, so the capital gain on the eventual sale cannot be computed.
    # The gain is therefore reported as not computed rather than assumed away.
    selling_cost = value_at_end * ASM["selling_cost_pct"]["baseline"]
    terminal = value_at_end - selling_cost - carry_fv + rent_fv

    return {
        "inherit_year": inherit_year,
        "horizon_years": horizon,
        "value_at_inherit": money10(value_at_inherit),
        "value_at_end": money10(value_at_end),
        "assessed_at_inherit": money10(assessed_start),
        "bill_year_one": money10(bills[0]),
        "bill_at_end": money10(bills[-1]),
        "tax_total": money10(tax_total),
        "cost_total": money10(cost_total),
        "rent_total": money10(rent_total),
        "carry_fv": money10(carry_fv),
        "rent_fv": money10(rent_fv),
        "selling_cost": money10(selling_cost),
        "capital_gain_tax": None,
        "terminal": money10(terminal),
        "rent_annual": money10(rent0),
        "rent_basis": B["rent"]["basis"],
        "rent_verified": B["rent"]["verified"],
        "basis_note": ("The heir's original cost basis for Property B is not supplied and is not "
                       "published, so the capital gain on the eventual sale cannot be computed and "
                       "is left blank rather than assumed. The terminal value is the market value "
                       "at the end of the horizon, less the selling cost, less the compounded tax "
                       "and running costs, plus the compounded rent."),
    }


def phased_entry_timing(inherit_year: int = 2045) -> dict:
    """The entry-timing comparison published on the black-swan page.

    Every row is priced by the one canonical engine, at the same modelled
    sale proceeds, with one Treasury assumption and one crash scenario. The
    table has three parts:

      * `rows` - the parking length the owner named (24, 30 and 36 months),
        each with and without the stated crash-at-entry sequence, against an
        immediate equity entry in the same market case;
      * `yield_rows` - the same baseline parking length priced at the low,
        baseline and high points of the official 3-month-to-2-year Treasury
        curve, so the reader sees what the yield assumption is worth;
      * `comparators` - the immediate-entry figures the differences are
        measured against.

    The crash sequence is CRASH_SCENARIO, a stated scenario, not a historical
    return.
    """
    g = ASM["house_growth"]["baseline"]
    infl = ASM["inflation"]["baseline"]
    eq = ASM["equity_return_nominal_gross"]["baseline"]
    drag = ASM["equity_tax_drag"]["baseline"]
    horizon = ASM["horizon_years"]
    sell_pct = ASM["selling_cost_pct"]["baseline"]
    gain_rate = ASM["combined_gain_tax_rate"]["baseline"]
    rec_rate = ASM["depreciation_recapture_rate"]["baseline"]
    tsy = ASM["treasury_short_yield_nominal"]
    parks = [ASM["phased_investing_park_months"][k] for k in ("low", "baseline", "high")]
    phase_months = int(ASM["phased_equity_phase_months"]["value"])
    crash = tuple(ASM["phased_crash_scenario"]["annual_returns"])

    k = inherit_year - 2026
    value_at_death = A["estimated_market_value_2026"] * (1 + g) ** k
    sale = sale_proceeds(value_at_death, value_at_death, sell_pct, gain_rate, rec_rate, 0.0)
    net = sale["net"]
    total_months = horizon * 12

    def immediate(crash_on: bool, rate: float) -> float:
        eng = phased_engine(net, total_months, 0, 0, rate, eq - drag,
                             crash if crash_on else None, lump=True)
        return eng["terminal"]

    def phased(park: int, crash_on: bool, rate: float) -> float:
        eng = phased_engine(net, total_months, park, phase_months, rate, eq - drag,
                             crash if crash_on else None)
        return eng["terminal"]

    rows = []
    for park in parks:
        for crash_on in (False, True):
            amount = phased(park, crash_on, tsy["baseline"])
            comparator = immediate(crash_on, tsy["baseline"])
            amount10 = money10(amount)
            comparator10 = money10(comparator)
            rows.append({
                "park_months": int(park),
                "phase_months": phase_months,
                "crash": crash_on,
                "tsy": tsy["baseline"],
                "terminal": amount10,
                "immediate": comparator10,
                # Difference of the published figures, so the column can be
                # checked by hand against the two columns beside it.
                "difference": amount10 - comparator10,
            })

    base_park = int(ASM["phased_investing_park_months"]["baseline"])
    yield_rows = []
    for label in ("low", "baseline", "high"):
        rate = tsy[label]
        for crash_on in (False, True):
            amount = phased(base_park, crash_on, rate)
            comparator = immediate(crash_on, rate)
            amount10 = money10(amount)
            comparator10 = money10(comparator)
            yield_rows.append({
                "label": label,
                "tsy": rate,
                "crash": crash_on,
                "terminal": amount10,
                "immediate": comparator10,
                "difference": amount10 - comparator10,
            })

    comparators = {
        "no_crash": money10(immediate(False, tsy["baseline"])),
        "crash": money10(immediate(True, tsy["baseline"])),
    }
    return {
        "inherit_year": inherit_year,
        "net_proceeds": money10(net),
        "horizon_years": horizon,
        "park_months": parks,
        "phase_months": phase_months,
        "tsy": tsy,
        "crash_annual_returns": [round(r, 4) for r in crash],
        "rows": rows,
        "yield_rows": yield_rows,
        "comparators": comparators,
    }


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

    # The same depreciation treatment as the published letting path: the
    # annual deduction is credited against tax, and the basis is reduced by
    # the same amount at sale, so the recapture is charged on the same
    # depreciation. Before this, the break-even rent was solved against a
    # model that charged the recapture and credited no shield, so the
    # published break-even rent did not match the published path.
    dep_sched = depreciation_schedule(value_at_death, horizon)
    dep_shield = [d * rec_rate for d in dep_sched]

    def rent_terminal(r0: float) -> float:
        cash = 0.0
        av = value_at_death
        for j in range(horizon):
            net = (r0 * (1 + infl) ** j
                   - (cost_a_base + maint_rent * value_at_death) * (1 + infl) ** j
                   - bill_for(av, fit_T, inherit_year + j, infl)
                   + dep_shield[j])
            cash += net * (1 + eq - drag) ** (horizon - 1 - j)
            av *= 1.02
        deprec = sum(dep_sched)
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
                rent_income=RENT_INCOME)
            # res["paths"] already carries the canonical phased path, so this
            # grid does not price a second, differently-assumed version of it.
            terms = {k: v["terminal"] for k, v in res["paths"].items()}
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
                            rent_income=RENT_INCOME)
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
                        rent_income=RENT_INCOME)
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
        maint_rent=A["annual_costs"]["maintenance_pct_rental"]["value"],
        rent_income=RENT_INCOME)
    # The phased path comes from res["paths"], which uses the canonical
    # engine. No second, differently-assumed copy is computed here.
    phased = res["paths"]["sell_then_phase"]
    cpi_mult = (1 + infl) ** horizon
    paths = {k: v["terminal"] for k, v in res["paths"].items()}
    return {
        "terminal": {k: v["terminal"] for k, v in res["paths"].items()},
        "terminal_real": {k: money10(v["terminal"] / cpi_mult) for k, v in res["paths"].items()},
        "outflow": {k: v.get("outflow", 0) for k, v in res["paths"].items()},
        "phased_terminal": phased["terminal"],
        "phased_net_proceeds": phased["start"],
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


# ------------------------------------------------------------------ main ----
FIT_A = fit_bill(A["roll"], ASM["ad_valorem_rate_a"]["value"])
FIT_B = fit_bill(B["roll"], ASM["ad_valorem_rate_b"]["value"])
# Rent used in the letting paths. None unless the owner supplies a figure, so the site
# never invents a market rent: with no rent the letting paths carry cost and no income,
# which is the conservative case, and it is labelled as such everywhere it is shown.
RENT_INCOME = A.get("rent_income_annual", {}).get("value") \
    if isinstance(A.get("rent_income_annual"), dict) else None
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
        "phased": [],
        "crash_entry": [],
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
                        rent_income=RENT_INCOME)
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
        res["housing_value_needed"] = money10(annuity_fv(
            t_eq - res["paths"]["live_in"]["terminal"], eq - drag, horizon))
        res["breakeven_house_growth"] = breakeven_house_growth(
            year, eq, drag, cap_growth, sell_pct, horizon, gain_rate, rec_rate,
            V["section121_exclusion_single"]["value"], maint_live)
        res["best_path"] = max(res["paths"], key=lambda k: res["paths"][k]["terminal"])
        out["paths"].append(res)
        phased = run_phased_path(
            inherit_year=year, g=g, infl=infl, eq=eq, drag=drag, tsy_short=TSY_SHORT,
            horizon=horizon, sell_pct=sell_pct, gain_rate=gain_rate, rec_rate=rec_rate,
            exclusion=V["section121_exclusion_single"]["value"],
            fixed_growth=ASM["fixed_charge_growth"]["baseline"], fit_a=FIT_A, cost_a_base=COST_A_BASE,
            maint_live=maint_live, maint_rent=maint_rent, rent_income=RENT_INCOME,
            park_months=ASM["phased_investing_park_months"]["baseline"],
            phase_months=ASM["phased_equity_phase_months"]["value"])
        phased["inherit_year"] = year
        out["phased"].append(phased)
        crash = crash_entry_comparison(
            inherit_year=year, g=g, infl=infl, eq=eq, drag=drag, tsy_short=TSY_SHORT,
            horizon=horizon, sell_pct=sell_pct, gain_rate=gain_rate, rec_rate=rec_rate,
            exclusion=V["section121_exclusion_single"]["value"],
            fixed_growth=ASM["fixed_charge_growth"]["baseline"], fit_a=FIT_A, cost_a_base=COST_A_BASE,
            maint_live=maint_live, maint_rent=maint_rent, rent_income=RENT_INCOME,
            park_months=ASM["phased_investing_park_months"]["baseline"],
            phase_months=ASM["phased_equity_phase_months"]["value"])
        crash["inherit_year"] = year
        out["crash_entry"].append(crash)

    out["phased_timing"] = phased_entry_timing(2045)
    out["property_b"] = property_b_comparison(2045)
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
