#!/usr/bin/env python3
"""Mixed ownership paths, the Proposition 19 clawback, opportunity cost, and
distributions behind the headline figures.

Why this module exists
    The site prices five paths, three of which are pure: sell at inheritance,
    live in the house for the whole horizon, or let it out for the whole
    horizon. The owner's brief asks for two things the pure paths cannot
    answer:

      * the paths a household actually takes - live in it for a few years and
        then sell, or live in it and then let it out;
      * the distribution behind every headline, rather than one smooth year
        4% / year 7% line.

What this module adds
    1. MIXED PATHS, priced on the same engine conventions as model.py. "Live in
       it for 5 years, then sell" occupies for five years and sells in year
       five; the net proceeds then compound for the remaining twenty-five. That
       is what the household would actually do, and it is not the same thing as
       selling in year thirty after five years of living.

    2. THE PROPOSITION 19 CLAWBACK. Revenue and Taxation Code section
       63.2(a)(1)(B)-(C) removes the intergenerational exclusion when the
       eligible transferee stops being eligible for the homeowners' exemption
       and requires the base year value established at the change in ownership
       to be enrolled, adjusted annually. For a child who moves in and later
       moves out, the property-tax relief is therefore reversed at the move-out
       - and it is not re-set to the market value at the move-out, it reverts to
       the value at the inheritance. model.py's live_then_rent path quietly
       assumes the favourable reading (the low assessment is kept). Both
       readings are published here, side by side, with the cost of the
       difference.

    3. THE OPPORTUNITY COST OF OCCUPYING THE HOUSE. Living in it produces
       somewhere to live, which has value, and the terminal-value column on the
       decision page does not include it. Each path here is reported twice: as
       an asset terminal, and with the market rent saved during the occupied
       years credited at the horizon. The market rent is still unknown on this
       site, so the credit is reported as unknown and the sensitivity to it is
       shown across a range of rents, each labelled as a scenario, not a quote.

    4. DISTRIBUTIONS. The whole path list is run against the same seeded
       fifty-year block bootstrap of the verified FRED record that the economy
       page uses, and the results are published as deciles and as a histogram of
       the sell-minus-live gap.

Determinism
    random.Random(SEED) with economy.py's seed, same block order, so a rebuild
    is byte-stable. No network access, no clock.

Privacy and rounding
    No name, address, postal code, parcel number, county or city appears here.
    Every money figure written to mixed.json is rounded to the nearest $10 with
    model.money10(); every percentage with model.pct().
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import model as base  # noqa: E402
import economy as econ  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "data"
A, B, V, ASM = base.A, base.B, base.V, base.ASM

INFL = ASM["inflation"]["baseline"]
G = ASM["house_growth"]["baseline"]
EQ = ASM["equity_return_nominal_gross"]["baseline"]
DRAG = ASM["equity_tax_drag"]["baseline"]
SELL_PCT = ASM["selling_cost_pct"]["baseline"]
GAIN = ASM["combined_gain_tax_rate"]["baseline"]
REC = ASM["depreciation_recapture_rate"]["baseline"]
CAP_GROWTH = ASM["prop19_cap_growth"]["baseline"]
FIXED_GROWTH = ASM["fixed_charge_growth"]["baseline"]
HORIZON = int(ASM["horizon_years"])
INHERIT = 2045
EXCLUSION = V["section121_exclusion_single"]["value"]
MAINT_LIVE = A["annual_costs"]["maintenance_pct_owner_occupied"]["value"]
MAINT_RENT = A["annual_costs"]["maintenance_pct_rental"]["value"]

SEED = econ.SEED
DRAWS = econ.DRAWS
BLOCK_YEARS = econ.BLOCK_YEARS

money10 = base.money10
pct = base.pct


# -------------------------------------------------------------- sale charges --
def sale_charge_breakdown(price: float) -> dict:
    """Itemise the published statutory charges on a sale of Property A.

      * COUNTY DOCUMENTARY TRANSFER TAX. Revenue and Taxation Code section
        11911(a) authorises a county tax of 55 cents for each $500 of
        consideration, which is $1.10 per $1,000, i.e. 0.11% of the price.
        Section 11911(b) lets a city add half that rate again, with a credit
        against the county tax; whether a city tax applies to Property A is not
        published on this site because it would name the city, so only the
        county charge is carried and the gap is flagged on the review page.
      * THE $75 INSTRUMENT FEE DOES NOT APPLY. Government Code section
        27388.1(a)(1) charges $75 per recorded real-estate instrument, but
        paragraph (2)(A) exempts any instrument recorded in connection with a
        transfer subject to the documentary transfer tax - which is exactly this
        sale. It is listed as zero with the reason, not omitted, because it is
        the kind of charge a checklist wrongly adds.
      * RECORDING. Government Code section 27361(a) caps the recorder's fee at
        $10 for the first page and $3 for each further page; four pages are
        assumed, so $20.

    The commission, escrow and title charges are quoted by private companies,
    are not published law, and are the remainder of the modelled 5.5% selling
    cost. This function splits that 5.5% into its published and private parts,
    so the owner can see which part is a statute and which part is a quote.
    """
    dt = price / 1000.0 * 1.10
    sb2 = 0.0                       # GOV 27388.1(a)(2)(A): exempt, DT applies
    rec = 10.0 + 3.0 * 3            # GOV 27361(a) caps, four pages
    total = dt + sb2 + rec
    model_cost = price * SELL_PCT
    return {
        "documentary_transfer_tax": money10(dt),
        "instrument_fee_27388_1": money10(sb2),
        "instrument_fee_note": ("Exempt: GOV 27388.1(a)(2)(A) excludes an instrument "
                                "recorded in connection with a transfer subject to the "
                                "documentary transfer tax."),
        "recording_fee_27361": money10(rec),
        "published_total": money10(total),
        "modelled_selling_cost": money10(model_cost),
        "private_closing_costs": money10(model_cost - total),
        "private_share_of_modelled": pct((model_cost - total) / model_cost, 1) if model_cost else None,
        "published_share_of_modelled": pct(total / model_cost, 1) if model_cost else None,
    }


# ------------------------------------------------------------------- one path --
def mixed_path(occupy_years: int, mode: str, inherit_year: int = INHERIT,
               g: float = G, infl: float = INFL, eq: float = EQ, drag: float = DRAG,
               sell_pct: float = SELL_PCT, gain_rate: float = GAIN,
               rec_rate: float = REC, cap_growth: float = CAP_GROWTH,
               horizon: int = HORIZON, clawback: bool = True,
               market_rent: float | None = None, fit_a: dict | None = None,
               cost_a_base: float | None = None,
               maint_live: float = MAINT_LIVE,
               maint_rent: float = MAINT_RENT,
               value_at_death: float | None = None) -> dict:
    """Price one path.

    mode:
      "sell" - sell at the end of the occupied period (year `occupy_years`), then
               invest the net proceeds for the rest of the horizon.
      "rent" - occupy for `occupy_years`, then let the house out to the horizon
               and sell at the end.

    occupy_years = 0 with "sell" is an immediate sale at the inheritance, the
    comparator everything else has to beat. occupy_years = horizon is living in
    it for the whole horizon and selling at the end.

    Property tax:
      * while the heir occupies the home, the Proposition 19 exclusion applies
        where the transfer qualifies (RTC 63.2), so the taxable value is the
        prior taxable value plus the excess over the prior value plus the
        biennially adjusted cap. That is the sheltered value.
      * when the heir lets the home out and never occupied it, the strict rule
        is full reassessment at the change in ownership (the continual-use
        condition in RTC 63.2(a)(1)(B)). model.py's rent_out path takes the same
        strict view.
      * when the heir occupied it and then moves out, `clawback=True` applies
        RTC 63.2(a)(1)(C): the base year value established at the change in
        ownership is enrolled, adjusted annually, from the lien date after the
        move-out. `clawback=False` keeps the low assessment, which is the
        reading model.py's live_then_rent path uses.

    Income tax:
      * basis is the value at death (IRS basis step-up), so gain is measured
        from there;
      * section 121 exclusion of $250,000 applies to a sale of a home the heir
        occupied as a principal residence for two of the last five years
        (Publication 523), which covers every "live then sell" case here;
      * depreciation is claimed only for rented years, over 27.5 years on 80% of
        the value at death (Publication 527), and is recaptured on sale.
    """
    fit_a = fit_a or base.FIT_A
    cost_a_base = base.COST_A_BASE if cost_a_base is None else cost_a_base
    if mode not in ("sell", "rent"):
        raise ValueError(mode)
    occupy_years = max(0, min(int(occupy_years), horizon))

    k = inherit_year - 2026
    if value_at_death is None:
        value_at_death = A["estimated_market_value_2026"] * (1 + g) ** k
    byv = A["roll"][0]["assessed"] * (1 + 0.02) ** k
    cap = V["prop19_value_cap_2025_2027"]["value"] * (1 + cap_growth) ** (inherit_year - 2025)
    sheltered = byv + max(0.0, value_at_death - (byv + cap))
    full = value_at_death

    fit_T = dict(fit_a)
    fit_T["fixed_base"] = (fit_a["fixed_base"]
                           * (1 + FIXED_GROWTH) ** (inherit_year - fit_a["base_year"]))
    rate_fv = eq - drag

    rented_years = 0 if mode == "sell" else horizon - occupy_years
    sold_at = occupy_years if mode == "sell" else horizon

    # ---- year-by-year cash flows -------------------------------------------------
    av = sheltered if occupy_years > 0 else full
    bills, operating, net_cash = [], [], []
    for j in range(sold_at):
        year = inherit_year + j
        occupied = j < occupy_years
        if occupy_years > 0 and not occupied:
            # moved out: exclusion removed (clawback) or kept
            av = (full * (1.02) ** j) if clawback else (av * 1.02)
        tax = base.bill_for(av, fit_T, year, infl)
        maint_pct = maint_live if occupied else maint_rent
        cost = (cost_a_base + maint_pct * value_at_death) * (1 + infl) ** j
        bills.append(tax)
        operating.append(cost)
        rent = 0.0
        if not occupied and mode == "rent" and market_rent:
            rent = market_rent * (1 + infl) ** j
            rented_years = max(rented_years, horizon - occupy_years)
        net_cash.append(rent - tax - cost)
        av *= 1.02
        if occupied:
            pass

    carry_fv = base.fv_stream(net_cash, rate_fv)

    # ---- the sale ----------------------------------------------------------------
    price_at_sale = value_at_death * (1 + g) ** sold_at
    deprec = 0.0
    if mode == "rent" and rented_years:
        deprec = min(0.8 * value_at_death, 0.8 * value_at_death / 27.5 * rented_years)
    occupied_two_of_five = occupy_years > 0 and (sold_at - occupy_years) <= 3
    excl121 = EXCLUSION if occupied_two_of_five else 0.0
    sale = base.sale_proceeds(price_at_sale, value_at_death - deprec, sell_pct,
                              gain_rate, rec_rate, deprec, excl121)

    # net proceeds after a mid-horizon sale compound for the remaining years
    if mode == "sell":
        terminal = (sale["net"] * (1 + rate_fv) ** (horizon - sold_at) + carry_fv)
    else:
        terminal = sale["net"] + carry_fv

    # ---- housing the household does not have to buy -------------------------------
    housing = 0.0
    if market_rent and occupy_years:
        housing = sum(market_rent * (1 + infl) ** j * (1 + rate_fv) ** (horizon - 1 - j)
                      for j in range(occupy_years))

    immediate = base.sale_proceeds(value_at_death, value_at_death, sell_pct,
                                   gain_rate, rec_rate, 0.0)
    immediate_fv = immediate["net"] * (1 + rate_fv) ** horizon

    return {
        "occupy_years": occupy_years,
        "mode": mode,
        "label": _label(occupy_years, mode, horizon),
        "value_at_death": money10(value_at_death),
        "taxable_sheltered": money10(sheltered),
        "taxable_full": money10(full),
        "clawback": bool(clawback and 0 < occupy_years < horizon and mode == "rent"),
        "clawback_year": (inherit_year + occupy_years
                          if clawback and 0 < occupy_years < horizon and mode == "rent" else None),
        "sold_in_year": sold_at,
        "terminal_price": money10(price_at_sale),
        "property_tax_total": money10(sum(bills)),
        "operating_total": money10(sum(operating)),
        "net_cash_fv": money10(carry_fv),
        "sale": sale,
        "depreciation": money10(deprec),
        "exclusion_121": money10(excl121),
        "asset_terminal": money10(terminal),
        "housing_value_fv": money10(housing),
        "opportunity_adjusted": (money10(terminal + housing) if market_rent else None),
        "sell_now_terminal": money10(immediate_fv),
        # positive gap = selling at the inheritance beats this path
        "gap_vs_sell_now": money10(immediate_fv - terminal),
        "gap_vs_sell_now_adjusted": (money10(immediate_fv - terminal - housing)
                                     if market_rent else None),
    }


def _label(occupy_years: int, mode: str, horizon: int) -> str:
    if occupy_years <= 0:
        return ("Let it out from the start, sell at the end" if mode == "rent"
                else "Sell at the inheritance")
    if occupy_years >= horizon:
        return f"Live in it for the whole {horizon} years, then sell"
    if mode == "rent":
        return f"Live in it for {occupy_years} years, then let it out"
    return f"Live in it for {occupy_years} years, then sell"


MIXED_CASES = [
    (0, "sell"), (0, "rent"), (2, "sell"), (2, "rent"), (5, "sell"), (5, "rent"),
    (10, "sell"), (10, "rent"), (15, "sell"), (20, "sell"), (HORIZON, "sell"),
]


def mixed_table(inherit_year: int = INHERIT, **kw) -> list[dict]:
    """Every mixed case, plus the favourable clawback reading for live-then-let."""
    out = []
    for occupy, mode in MIXED_CASES:
        row = mixed_path(occupy, mode, inherit_year=inherit_year, **kw)
        row["reading"] = "strict" if row["clawback"] else ""
        out.append(row)
        if 0 < occupy < HORIZON and mode == "rent":
            alt = mixed_path(occupy, mode, inherit_year=inherit_year,
                             clawback=False, **kw)
            alt["label"] = alt["label"] + " (low assessment kept after move-out)"
            alt["reading"] = "favourable"
            out.append(alt)
    return out


def clawback_cost(inherit_year: int = INHERIT, **kw) -> dict:
    """What the two readings of section 63.2(a)(1)(C) are worth on live-then-let."""
    with_cb = mixed_path(10, "rent", inherit_year=inherit_year, clawback=True, **kw)
    without = mixed_path(10, "rent", inherit_year=inherit_year, clawback=False, **kw)
    fit = dict(base.FIT_A)
    fit["fixed_base"] = (base.FIT_A["fixed_base"]
                         * (1 + FIXED_GROWTH) ** (inherit_year - base.FIT_A["base_year"]))
    return {
        "case": "Live in it for 10 years, then let it out",
        "tax_with_clawback": with_cb["property_tax_total"],
        "tax_without_clawback": without["property_tax_total"],
        "difference": money10(with_cb["property_tax_total"] - without["property_tax_total"]),
        "terminal_with_clawback": with_cb["asset_terminal"],
        "terminal_without_clawback": without["asset_terminal"],
        "terminal_difference": money10(with_cb["asset_terminal"] - without["asset_terminal"]),
        "year_one_bill_after_move_out": money10(base.bill_for(
            with_cb["taxable_full"] * (1.02) ** 10, fit, inherit_year + 10, INFL)),
        "year_one_bill_if_kept": money10(base.bill_for(
            with_cb["taxable_sheltered"] * (1.02) ** 10, fit, inherit_year + 10, INFL)),
        "rule": ("Revenue and Taxation Code section 63.2(a)(1)(C): the base year value "
                 "established at the change in ownership is enrolled, adjusted annually, "
                 "when the eligible transferee no longer qualifies. The strict reading is "
                 "published as the baseline and the favourable one is shown beside it."),
    }


# --------------------------------------------------------------- distributions --
def bootstrap_draws(seed: int = SEED, draws: int = DRAWS) -> list[dict]:
    """Run every path against the same seeded bootstrap the economy page uses.

    Ten-year blocks are drawn with replacement from the windows where both the
    verified California state house price index and the consumer price index
    are present, so house and inflation history move together as they did. The
    first nineteen years set the value at the 2045 inheritance; the next thirty
    are the decision horizon, and the draw's own consumer price path drives
    inflation, property tax and running costs.

    The equity return is not drawn. No official series of forward equity returns
    exists, and drawing it from the last fifty years would import the hindsight
    the site avoids elsewhere. It is held at the published scenario, and the
    sensitivity table on the decision page shows the swing.
    """
    S = base.SERIES
    ch_h, _, _ = econ.annual_changes(S["hpi_a"])
    ch_c, _, _ = econ.annual_changes(S["cpi"])
    shared = sorted(y for y in ch_h if y in ch_c)
    starts = [y for y in shared if y + BLOCK_YEARS - 1 in ch_c]
    hb = [[ch_h[y] for y in range(s, s + BLOCK_YEARS)] for s in starts]
    cb = [[ch_c[y] for y in range(s, s + BLOCK_YEARS)] for s in starts]

    pre_years = INHERIT - 2026
    rng = random.Random(seed)
    out = []
    for _ in range(draws):
        picks = [rng.randrange(len(starts)) for _ in range(5)]
        h50 = [c for b in picks for c in hb[b]]
        c50 = [c for b in picks for c in cb[b]]

        pre = 1.0
        for x in h50[:pre_years]:
            pre *= 1 + x
        post = 1.0
        for x in h50[pre_years:pre_years + HORIZON]:
            post *= 1 + x
        infl_mult = 1.0
        for x in c50[pre_years:pre_years + HORIZON]:
            infl_mult *= 1 + x

        g_hold = post ** (1.0 / HORIZON) - 1.0
        infl_avg = infl_mult ** (1.0 / HORIZON) - 1.0
        infl_use = max(-0.02, infl_avg)   # the model's tax and cost engine needs a rate
        vod = A["estimated_market_value_2026"] * pre

        sell = mixed_path(0, "sell", g=g_hold, infl=infl_use, value_at_death=vod)
        live = mixed_path(HORIZON, "sell", g=g_hold, infl=infl_use, value_at_death=vod)
        live10s = mixed_path(10, "sell", g=g_hold, infl=infl_use, value_at_death=vod)
        live10r = mixed_path(10, "rent", g=g_hold, infl=infl_use, value_at_death=vod)
        out.append({
            "value_at_death": money10(vod),
            "g_inherit": pre ** (1.0 / pre_years) - 1.0,
            "g_hold": g_hold,
            "infl": infl_avg,
            "sell": sell["asset_terminal"],
            "live": live["asset_terminal"],
            "live10_sell": live10s["asset_terminal"],
            "live10_rent": live10r["asset_terminal"],
            "gap_live": money10(sell["asset_terminal"] - live["asset_terminal"]),
            "gap_live10_sell": money10(sell["asset_terminal"] - live10s["asset_terminal"]),
            "gap_live10_rent": money10(sell["asset_terminal"] - live10r["asset_terminal"]),
        })
    return out


def _decile(sorted_vals: list[float], q: float) -> float:
    idx = q * (len(sorted_vals) - 1)
    lo = int(math.floor(idx))
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def distribution_summary(draws: list[dict]) -> dict:
    """Deciles, a histogram, and the shares the decision turns on."""
    keys = [
        ("value_at_death", "Property A value at the 2045 inheritance", "money"),
        ("sell", "Sell at 2045 and invest: value after thirty years", "money"),
        ("live", "Live in it for thirty years, then sell", "money"),
        ("live10_sell", "Live in it for ten years, then sell", "money"),
        ("live10_rent", "Live in it for ten years, then let it out", "money"),
        ("gap_live", "Selling minus living in it for thirty years", "money"),
        ("gap_live10_sell", "Selling minus living ten years then selling", "money"),
        ("gap_live10_rent", "Selling minus living ten years then letting", "money"),
        ("g_hold", "House growth over the thirty-year window", "pct"),
        ("infl", "Inflation over the thirty-year window", "pct"),
    ]
    series = []
    for key, label, unit in keys:
        vals = [d[key] for d in draws]
        s = sorted(vals)
        dec = [_decile(s, i / 10.0) for i in range(11)]
        series.append({
            "key": key, "label": label, "unit": unit,
            "deciles": [money10(x) if unit == "money" else pct(x, 2) for x in dec],
            "min": money10(s[0]) if unit == "money" else pct(s[0], 2),
            "max": money10(s[-1]) if unit == "money" else pct(s[-1], 2),
            "mean": (money10(sum(vals) / len(vals)) if unit == "money"
                     else pct(sum(vals) / len(vals), 2)),
        })

    n = len(draws)
    shares = [
        {"key": "Selling beats living in it for thirty years",
         "value": sum(1 for d in draws if d["gap_live"] > 0) / n},
        {"key": "Selling beats living in it ten years and then selling",
         "value": sum(1 for d in draws if d["gap_live10_sell"] > 0) / n},
        {"key": "Selling beats living ten years and then letting it out",
         "value": sum(1 for d in draws if d["gap_live10_rent"] > 0) / n},
        {"key": "Draws with falling nominal house prices over the thirty years",
         "value": sum(1 for d in draws if d["g_hold"] < 0) / n},
    ]

    gaps = sorted(d["gap_live"] for d in draws)
    lo = gaps[int(0.01 * (n - 1))]
    hi = gaps[int(0.99 * (n - 1))]
    if hi <= lo:
        hi = lo + 10
    width = (hi - lo) / 20.0
    bins = [0] * 20
    for d in draws:
        g = d["gap_live"]
        if g < lo:
            bins[0] += 1
        elif g >= hi:
            bins[-1] += 1
        else:
            bins[min(19, int((g - lo) / width))] += 1
    histogram = {
        "lo": money10(lo), "hi": money10(hi), "bin_width": money10(width),
        "counts": bins,
        "share_above_zero": sum(1 for d in draws if d["gap_live"] > 0) / n,
        "zero_position": (0 - lo) / (hi - lo),
        "note": ("Twenty equal-width bins of selling minus living in it for thirty "
                 "years, truncated at the first and ninety-ninth percentile so one "
                 "extreme draw cannot flatten the shape. Bars to the right of the zero "
                 "line are draws in which selling wins."),
    }
    return {"draws": n, "series": series, "shares": shares, "histogram": histogram}


# --------------------------------------------------------------------- build --
RENT_SCENARIOS = (0, 30_000, 60_000, 90_000, 120_000, 180_000, 240_000, 360_000)


def rent_sensitivity() -> list[dict]:
    """What the opportunity credit is worth at each hypothetical market rent.

    These are scenarios, not rent opinions. No official source publishes a market
    rent for a specific home, and the input that would carry one
    (property_a.rent_income_annual) is still empty.
    """
    rows = []
    for rent0 in RENT_SCENARIOS:
        alloc = []
        for occupy, mode in ((HORIZON, "sell"), (10, "sell"), (10, "rent")):
            r = mixed_path(occupy, mode, market_rent=float(rent0) if rent0 else None)
            alloc.append({
                "label": r["label"],
                "asset_terminal": r["asset_terminal"],
                "opportunity_adjusted": r["opportunity_adjusted"],
                "credit": r["housing_value_fv"],
                "gap_vs_sell_now": r["gap_vs_sell_now"],
                "gap_adjusted": r["gap_vs_sell_now_adjusted"],
            })
        rows.append({"rent": money10(rent0), "paths": alloc})
    return rows


def build() -> dict:
    paths = mixed_table()
    cb = clawback_cost()
    draws = bootstrap_draws()
    dist = distribution_summary(draws)

    by_year = {}
    for year in ASM["inheritance_years"]:
        by_year[str(year)] = [
            {"label": r["label"], "asset_terminal": r["asset_terminal"],
             "gap_vs_sell_now": r["gap_vs_sell_now"],
             "occupy_years": r["occupy_years"], "mode": r["mode"]}
            for r in mixed_table(inherit_year=year)
        ]

    return {
        "meta": {
            "built": "2026-11-15",
            "inherit_year": INHERIT,
            "horizon_years": HORIZON,
            "seed": SEED,
            "draws": DRAWS,
            "block_years": BLOCK_YEARS,
            "rounding": "nearest $10",
            "privacy": ("No name, address, postal code, parcel number, county or city "
                        "name appears in this file or in what it feeds."),
            "rates": {"house_growth": G, "inflation": INFL, "equity": EQ,
                      "drag": DRAG, "sell_pct": SELL_PCT, "gain_rate": GAIN,
                      "recapture_rate": REC, "cap_growth": CAP_GROWTH},
            "market_rent": ("Unknown. property_a.rent_income_annual is empty, so the "
                            "opportunity-adjusted columns are published only as a range "
                            "of rent scenarios."),
        },
        "paths": paths,
        "clawback": cb,
        "distribution": dist,
        "by_year": by_year,
        "rent_sensitivity": rent_sensitivity(),
        "fees_example": {"price": 5_000_000, **sale_charge_breakdown(5_000_000),
                         "note": ("Published statutory charges on a $5,000,000 sale, "
                                  "computed from the statutes at their published rates. "
                                  "Commission, escrow and title charges are not published "
                                  "law; they are the private remainder of the modelled "
                                  "5.5% selling cost.")},
    }


if __name__ == "__main__":
    m = build()
    (DATA / "mixed.json").write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
    print(f"mixed paths: {len(m['paths'])} rows, {m['distribution']['draws']} draws")
    for r in m["paths"]:
        print(f"  {r['label'][:52]:52} terminal {r['asset_terminal']:>13,}  "
              f"vs sell now {r['gap_vs_sell_now']:>13,}")
    print("clawback tax difference:", f"{m['clawback']['difference']:,}",
          "terminal difference:", f"{m['clawback']['terminal_difference']:,}")
    for s in m["distribution"]["shares"]:
        print(f"  {s['key']}: {s['value'] * 100:.1f}%")
    for s in m["distribution"]["series"]:
        print(f"  {s['label']}: " + " ".join(f"{x:,}" for x in s["deciles"]))
    print("fees:", m["fees_example"])
