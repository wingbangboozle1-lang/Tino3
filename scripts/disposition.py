#!/usr/bin/env python3
"""Disposition timing and the like-kind exchange question.

Reads  : assets/data/inputs.json, assets/data/model.json
Writes : assets/data/disposition.json

Two brief items that the published edition carried only as register rows are
priced here rather than listed as open questions.

1. A SALE IN THE SAME TAX YEAR AS THE INHERITANCE. Property acquired from a
   decedent takes a basis equal to its fair market value at the date of death
   (or at the alternate valuation date, but only where an estate tax return is
   filed and the executor elects it), so a sale made at that value realises no
   gain and pays no capital gains tax. The ladder below asks the only question
   that then matters: what does it cost to wait, month by month, out to sixty
   months, at each of the three transfer dates the site models? Waiting buys
   appreciation and pays for it with selling costs, property tax on a
   reassessed value, running costs and a lost year of compounding.

2. A LIKE-KIND EXCHANGE UNDER SECTION 1031. The exchange is priced the way the
   statute works, not the way promotional material describes it. It defers the
   tax that a sale would realise; it does not forgive it, the deferred gain
   rides in the replacement property's substituted basis, and it does not stop
   a property-tax reassessment. Both halves are computed here: the tax deferred
   at each holding period, and the return the replacement property would have
   to earn to justify carrying the liability instead of paying it.

Deterministic: no network calls, no randomness, no clock reads. Every rule
implemented here was read from an official publisher; the source ids are
carried into the output so the site can cite them.

Privacy: nothing here names a person, a property, a parcel, a postal code, a
county or a city. Every money figure written to disposition.json is rounded to
the nearest $10 with model.money10(); every percentage with model.pct().
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "data"

INPUTS = json.loads((DATA / "inputs.json").read_text(encoding="utf-8"))
MODEL = json.loads((DATA / "model.json").read_text(encoding="utf-8"))

import model as model_mod  # noqa: E402  (reuse the one published engine and its conventions)

A = INPUTS["property_a"]
ASM = INPUTS["assumptions"]
V = INPUTS["verified_parameters"]

money10 = model_mod.money10
sale_proceeds = model_mod.sale_proceeds
bill_for = model_mod.bill_for

# ------------------------------------------------------------------ rules ---
# Every figure below was read from an official publisher; see the source ids
# carried in SRC_IDS and used by build.py on the disposition page.
SRC_IDS = {
    "basis": "irs_basis",                 # inherited-property basis, incl. the alternate valuation condition
    "statute": "uscode1031",              # 26 U.S.C. 1031
    "form": "irs_i8824",                  # 2026 Instructions for Form 8824 (45 / 180 day rules, personal residence)
    "safe_harbour": "irs_rp2008_16",      # Rev. Proc. 2008-16, the 24-month dwelling-unit safe harbour
    "both_provisions": "irs_rp2005_14",   # Rev. Proc. 2005-14, section 121 applied before section 1031
    "tips": "irs_lke_tips",               # section 1031 limited to real property; property held for sale excluded
    "change_ownership": "rtc60",          # Revenue and Taxation Code section 60
    "exclusion": "rtc63_2",               # the intergenerational exclusion and when it ends
}

# Model conventions, read from the one place the site already publishes them.
HORIZON = int(ASM["horizon_years"])
G = float(ASM["house_growth"]["baseline"])
INFL = float(ASM["inflation"]["baseline"])
EQ = float(ASM["equity_return_nominal_gross"]["baseline"])
DRAG = float(ASM["equity_tax_drag"]["baseline"])
SELL_PCT = float(ASM["selling_cost_pct"]["baseline"])
GAIN_RATE = float(ASM["combined_gain_tax_rate"]["baseline"])
REC_RATE = float(ASM["depreciation_recapture_rate"]["baseline"])
FIXED_GROWTH = float(ASM["fixed_charge_growth"]["baseline"])
EXCLUSION = float(V["section121_exclusion_single"]["value"])
CAP_GROWTH = float(ASM["prop19_cap_growth"]["baseline"])
MAINT_LIVE = float(A["annual_costs"]["maintenance_pct_owner_occupied"]["value"])
MAINT_RENT = float(A["annual_costs"]["maintenance_pct_rental"]["value"])
COST_A_BASE = float(model_mod.COST_A_BASE)
FIT_A = model_mod.FIT_A

INHERIT_YEARS = [int(x) for x in ASM["inheritance_years"]]
WAITS_MONTHS = [0, 6, 12, 18, 24, 36, 60]
HOLDS_YEARS = [0, 2, 5, 10, 20, 30]

# The waiting ladder holds the house empty or occupied by the heir, not let, so
# no depreciation is claimed and the owner-occupied maintenance rate applies.
WAIT_MAINT = MAINT_LIVE
# The repair life the model already uses for residential rental property.
DEPRECIATION_LIFE = 27.5


def value_at(year: int) -> float:
    """The model's house value in a given year, from the 2026 owner estimate."""
    return float(A["estimated_market_value_2026"]) * (1 + G) ** (year - 2026)


def fit_at(year: int) -> dict:
    """The Property A bill model with its fixed charges rolled to `year`."""
    fit = dict(FIT_A)
    fit["fixed_base"] = FIT_A["fixed_base"] * (1 + FIXED_GROWTH) ** (year - FIT_A["base_year"])
    return fit


def byv_at(year: int) -> float:
    """The factored base year value: today's roll grown at the 2% cap."""
    return float(A["roll"][0]["assessed"]) * (1 + 0.02) ** (year - 2026)


def cap_at(year: int) -> float:
    """The Proposition 19 shelter amount, indexed at the model's rate."""
    return float(V["prop19_value_cap_2025_2027"]["value"]) * (1 + CAP_GROWTH) ** (year - 2025)


def taxable_if_live(year: int) -> float:
    byv = byv_at(year)
    return byv + max(0.0, value_at(year) - (byv + cap_at(year)))


# ------------------------------------------------------------ sale timing ---
def sale_timing_row(inherit_year: int, wait_months: int) -> dict:
    """One rung of the waiting ladder: sell `wait_months` after the inheritance.

    The basis is the value at the date of death, so the taxable gain is only
    the appreciation that happens after the inheritance, less the selling costs.
    During the wait the heir owns a reassessed house: the exclusion under
    section 63.2 is a claim the heir makes by moving in and filing, so a holder
    who is waiting to sell is modelled on the full reassessed value.
    """
    v0 = value_at(inherit_year)
    fit_t = fit_at(inherit_year)
    price = v0 * (1 + G) ** (wait_months / 12.0)
    sale = sale_proceeds(price, v0, SELL_PCT, GAIN_RATE, REC_RATE, 0.0, 0.0)

    share = wait_months / 12.0
    # Reassessed at the transfer: the bill the model already publishes for a
    # holder who does not take the exclusion.
    bill_year = bill_for(v0, fit_t, inherit_year, INFL)
    property_tax = bill_year * share
    running = (COST_A_BASE + WAIT_MAINT * v0) * share
    wait_cost = property_tax + running

    rate = EQ - DRAG
    years_left = HORIZON - share
    terminal = float(sale["net"]) * (1 + rate) ** years_left - wait_cost * (1 + rate) ** years_left
    return {
        "inherit_year": inherit_year,
        "wait_months": wait_months,
        "wait_label": ("the same tax year as the inheritance" if wait_months == 0
                       else f"{wait_months} months"),
        "value_at_death": money10(v0),
        "price": money10(price),
        "basis": money10(v0),
        "selling_costs": money10(sale["costs"]),
        "gain": money10(sale["gain"]),
        "tax": money10(sale["tax"]),
        "net_proceeds": money10(sale["net"]),
        "property_tax_during_wait": money10(property_tax),
        "running_cost_during_wait": money10(running),
        "wait_cost": money10(wait_cost),
        "terminal": money10(terminal),
    }


def sale_timing() -> dict:
    rows = []
    by_year = {}
    for year in INHERIT_YEARS:
        year_rows = [sale_timing_row(year, w) for w in WAITS_MONTHS]
        base = year_rows[0]["terminal"]
        for r in year_rows:
            r["vs_immediate"] = money10(r["terminal"] - base)
            r["vs_immediate_per_year"] = (money10((r["terminal"] - base) / (r["wait_months"] / 12.0))
                                          if r["wait_months"] else 0)
            r["tax_share_of_price"] = round(100.0 * r["tax"] / r["price"], 2) if r["price"] else 0.0
        rows.extend(year_rows)
        by_year[str(year)] = year_rows

    # The published summary, read from the rows rather than typed.
    base_year = 2045 if 2045 in INHERIT_YEARS else INHERIT_YEARS[0]
    rows_45 = by_year[str(base_year)]
    by_wait = {r["wait_months"]: r for r in rows_45}
    return {
        "inherit_years": INHERIT_YEARS,
        "waits_months": WAITS_MONTHS,
        "rows": rows,
        "by_year": by_year,
        "base_year": base_year,
        "summary": {
            "same_year_tax": by_wait[0]["tax"],
            "same_year_net": by_wait[0]["net_proceeds"],
            "same_year_gain": by_wait[0]["gain"],
            "twelve_month_tax": by_wait[12]["tax"],
            "twelve_month_cost": by_wait[12]["vs_immediate"],
            "twelve_month_cost_per_year": by_wait[12]["vs_immediate_per_year"],
            "twenty_four_month_tax": by_wait[24]["tax"],
            "twenty_four_month_cost": by_wait[24]["vs_immediate"],
            "twenty_four_month_cost_per_year": by_wait[24]["vs_immediate_per_year"],
            "sixty_month_cost": by_wait[60]["vs_immediate"],
            "sixty_month_cost_per_year": by_wait[60]["vs_immediate_per_year"],
            "months_of_waiting_before_tax": next((r["wait_months"] for r in rows_45
                                                  if r["tax"] > 0), None),
        },
        "note": (
            "The basis is the value at the date of death, so the only gain a wait "
            "creates is the appreciation after the inheritance, and selling costs "
            "are charged on the higher price too. Every row is measured at the same "
            "horizon as the rest of the site: the thirtieth year after the "
            "inheritance, so a later sale has less time to compound."
        ),
        "src": [SRC_IDS["basis"], SRC_IDS["exclusion"]],
    }


# --------------------------------------------------------------- exchange ---
def exchange_row(inherit_year: int, hold_years: int) -> dict:
    """Sell versus exchange after holding the house `hold_years` from the inheritance.

    The exchange is priced on the statute's own terms:

      * the property is sold either way - in a deferred exchange the
        relinquished property is transferred to a buyer through a qualified
        intermediary - so the same selling costs come off the top in both
        columns;
      * what the exchange changes is the tax. Recognised gain is zero on a
        clean exchange (no boot, no cash out), so the tax a sale would have
        realised stays in the replacement property as a substituted basis
        under section 1031(d);
      * that is a deferral, not a forgiveness: the gain is still there and is
        taxed when the replacement is disposed of, unless it is still held at
        death.
    """
    v0 = value_at(inherit_year)
    fit_t = fit_at(inherit_year)
    value = v0 * (1 + G) ** hold_years
    deprec = min(0.8 * v0, 0.8 * v0 / DEPRECIATION_LIFE * hold_years)

    sell = sale_proceeds(value, v0 - deprec, SELL_PCT, GAIN_RATE, REC_RATE, deprec, 0.0)
    # The exchange: same price, same costs, no tax recognised now.
    exchanged_costs = sell["costs"]
    capital_if_sold = float(sell["net"])
    capital_if_exchanged = float(sell["price"]) - exchanged_costs
    tax_deferred = float(sell["tax"])

    years_left = HORIZON - hold_years
    rate = EQ - DRAG
    if years_left > 0 and capital_if_exchanged > 0:
        # Headline break-even: the gain is never taxed at all, which is what happens
        # if the replacement property is still held at death. Both sides are then
        # measured pre-tax at the horizon, so this is the most the deferral can buy.
        required_return = (capital_if_sold / capital_if_exchanged) ** (1.0 / years_left) * (1 + rate) - 1
        handicap = rate - required_return
    else:
        required_return = None
        handicap = None

    # The temporary case: BOTH sides are liquidated on the same day at the horizon,
    # so the deferral is only the time value of the tax. The replacement carries the
    # substituted basis of section 1031(d); no further depreciation is claimed on it,
    # which is generous to the exchange, because claiming it would create more
    # recapture. The equity side is taxed on its gain at the horizon too, which the
    # rest of the site does not do - it measures an estate held until death - so this
    # is published as a second, symmetric case rather than as the headline.
    required_if_sold = None
    handicap_if_sold = None
    # Section 1031(d) sets the replacement's basis by reference to the basis of the
    # property given up, so the commission paid on the way out is not added to it. The
    # basis is therefore capped at the capital actually reinvested, which denies the
    # exchange any benefit from a phantom loss on the costs.
    basis_carried = min(v0 - deprec, capital_if_exchanged)
    if years_left > 0 and capital_if_exchanged > 0:
        equity_gross = capital_if_sold * (1 + rate) ** years_left
        equity_net = equity_gross - max(0.0, equity_gross - capital_if_sold) * GAIN_RATE

        def terminal_if_sold(re: float) -> float:
            price = capital_if_exchanged * (1 + re) ** years_left
            res = sale_proceeds(price, basis_carried, SELL_PCT, GAIN_RATE, REC_RATE, 0.0, 0.0)
            return float(res["net"])

        lo, hi = -0.10, 0.30
        if terminal_if_sold(hi) > equity_net:
            for _ in range(200):
                mid = (lo + hi) / 2.0
                if terminal_if_sold(mid) < equity_net:
                    lo = mid
                else:
                    hi = mid
            required_if_sold = (lo + hi) / 2.0
            handicap_if_sold = rate - required_if_sold

    # Safe harbour availability, read from Rev. Proc. 2008-16 section 4.02(1)(a):
    # the dwelling unit must be owned for at least the 24 months before the exchange.
    safe_harbour = hold_years >= 2

    # Property tax: what the intergenerational exclusion is worth on this house at
    # the year of the exchange, and what an exchange loses. The excluded roll grows
    # at the 2% cap; the reassessed value is the market value in that year, which is
    # what the replacement property would be enrolled at.
    fit_n = fit_at(inherit_year + hold_years)
    excluded_roll = taxable_if_live(inherit_year) * 1.02 ** hold_years
    bill_excluded = bill_for(excluded_roll, fit_n, inherit_year + hold_years, INFL)
    bill_full = bill_for(value, fit_n, inherit_year + hold_years, INFL)

    # The exclusion's own roll grows at the 2% cap while a reassessed value grows with the
    # market, so the shelter given up widens every year. Summed over the years left in the
    # horizon, on the same bill model the property pages publish.
    shelter_cumulative = 0.0
    for j in range(1, max(0, years_left) + 1):
        y = inherit_year + hold_years + j
        fit_y = fit_at(y)
        excl = taxable_if_live(inherit_year) * 1.02 ** (hold_years + j)
        full = v0 * (1 + G) ** (hold_years + j)
        shelter_cumulative += bill_for(full, fit_y, y, INFL) - bill_for(excl, fit_y, y, INFL)

    return {
        "inherit_year": inherit_year,
        "hold_years": hold_years,
        "value_at_exchange": money10(value),
        "adjusted_basis": money10(v0 - deprec),
        "depreciation": money10(deprec),
        "selling_costs": money10(exchanged_costs),
        "gain": money10(sell["gain"]),
        "recapture": money10(sell["recapture"]),
        "tax_if_sold": money10(sell["tax"]),
        "net_if_sold": money10(capital_if_sold),
        "tax_deferred_by_exchange": money10(tax_deferred),
        "capital_if_exchanged": money10(capital_if_exchanged),
        "deferred_share_of_capital": round(100.0 * tax_deferred / capital_if_exchanged, 2)
        if capital_if_exchanged else 0.0,
        "years_left": years_left,
        "required_return_pct": round(required_return * 100.0, 2) if required_return is not None else None,
        "handicap_pp": round(handicap * 100.0, 2) if handicap is not None else None,
        "required_return_if_sold_pct": round(required_if_sold * 100.0, 2)
        if required_if_sold is not None else None,
        "handicap_if_sold_pp": round(handicap_if_sold * 100.0, 2)
        if handicap_if_sold is not None else None,
        "deferral_upside": money10(tax_deferred * ((1 + rate) ** years_left - 1))
        if years_left > 0 else 0,
        "safe_harbour_available": safe_harbour,
        "bill_if_excluded": money10(bill_excluded),
        "bill_if_reassessed": money10(bill_full),
        "annual_shelter_lost": money10(bill_full - bill_excluded),
        "shelter_lost_over_years_left": money10(shelter_cumulative),
    }


def exchange_case() -> dict:
    year = 2045 if 2045 in INHERIT_YEARS else INHERIT_YEARS[0]
    rows = [exchange_row(year, n) for n in HOLDS_YEARS]
    # The two reliefs cannot both be held. The intergenerational exclusion under section
    # 63.2 is conditioned on the home being the transferee's principal residence; the
    # dwelling-unit safe harbour in Rev. Proc. 2008-16 is conditioned on renting the unit
    # at a fair rental for 14 days or more in each of two 12-month periods with personal
    # use no more than the greater of 14 days or 10% of the rental days; and Rev. Proc.
    # 2005-14 section 2.05 states that section 1031 does not apply to property used
    # solely as a personal residence. Living in the home and exchanging the home are
    # therefore competing uses of the same two years.
    conflict = {
        "statement": (
            "The property-tax relief and the exchange compete for the same years. Claiming "
            "the intergenerational exclusion means making the home the principal residence; "
            "qualifying a dwelling unit for an exchange means renting it at a fair rental "
            "and keeping personal use to the greater of 14 days or 10% of the rental days "
            "in each of two 12-month periods. A household cannot do both with the same two "
            "years, and a home used solely as a personal residence does not qualify at all."
        ),
        "src": ["rtc63_2", "irs_rp2008_16", "irs_rp2005_14"],
    }
    by_hold = {r["hold_years"]: r for r in rows}
    at_death = by_hold[0]
    return {
        "inherit_year": year,
        "holds": HOLDS_YEARS,
        "rows": rows,
        "at_inheritance": {
            "tax_deferred": at_death["tax_deferred_by_exchange"],
            "gain": at_death["gain"],
            "handicap_pp": at_death["handicap_pp"],
            "required_return_pct": at_death["required_return_pct"],
            "verdict": (
                "Nothing to defer. The basis is the value at the date of death, so the "
                "gain on a sale at that value is zero and there is no tax for an "
                "exchange to postpone. The replacement property would have to match the "
                "modelled equity return exactly for the exchange to break even."
            ),
        },
        "first_year_with_safe_harbour": 2,
        "conflict": conflict,
        "property_tax": {
            "inherit_year": year,
            "bill_if_excluded": by_hold[0]["bill_if_excluded"],
            "bill_if_reassessed": by_hold[0]["bill_if_reassessed"],
            "annual_shelter_lost": by_hold[0]["annual_shelter_lost"],
        },
        "src": [SRC_IDS["statute"], SRC_IDS["form"], SRC_IDS["safe_harbour"],
                SRC_IDS["both_provisions"], SRC_IDS["tips"],
                SRC_IDS["change_ownership"], SRC_IDS["exclusion"]],
    }


def conditions() -> list:
    """What has to be true for an exchange to be available at all."""
    return [
        {"condition": "The property is real property, held for use in a trade or business or "
                      "for investment - not property held primarily for sale, and not a home "
                      "used solely as a personal residence",
         "authority": "26 U.S.C. 1031(a)(1), (a)(2); 2026 Instructions for Form 8824",
         "src": "uscode1031"},
        {"condition": "The replacement is identified in writing within 45 days of the transfer "
                      "and received within 180 days, or by the due date of the return including "
                      "extensions, whichever is earlier",
         "authority": "26 U.S.C. 1031(a)(3); 2026 Instructions for Form 8824, Lines 5 and 6",
         "src": "irs_i8824"},
        {"condition": "Where the property is a dwelling unit the heir also uses personally, the "
                      "safe harbour needs 24 months of ownership and, in each of the two "
                      "12-month periods, 14 days or more of renting at a fair rental with "
                      "personal use no more than the greater of 14 days or 10% of the rental days",
         "authority": "Rev. Proc. 2008-16, section 4.02",
         "src": "irs_rp2008_16"},
        {"condition": "Any cash or non-like-kind property received is taxed as boot, to the "
                      "extent of the gain; no loss is recognised on an exchange",
         "authority": "26 U.S.C. 1031(b), (c)",
         "src": "uscode1031"},
        {"condition": "The replacement takes the old basis, reduced by money received and "
                      "increased by gain recognised, so the deferred gain is carried forward "
                      "rather than wiped out",
         "authority": "26 U.S.C. 1031(d)",
         "src": "uscode1031"},
        {"condition": "Where both the home exclusion and the exchange could apply, the "
                      "exclusion is applied first, and gain attributable to depreciation after "
                      "6 May 1997 cannot be excluded but can be deferred",
         "authority": "Rev. Proc. 2005-14, sections 4.02(1) and 4.02(2); section 121(d)(6)",
         "src": "irs_rp2005_14"},
        {"condition": "A transfer to a third party ends the intergenerational exclusion, and an "
                      "exchange is a change in ownership, so the replacement is enrolled at its "
                      "own full value",
         "authority": "Revenue and Taxation Code sections 60 and 63.2",
         "src": "rtc60"},
    ]


def frictions() -> list:
    """What the exchange costs that the table above cannot price."""
    return [
        "A qualified intermediary, exchange documents and legal review, none of which is "
        "quoted here because no quote exists for this household.",
        "The 45-day and 180-day clocks run from the transfer of the relinquished property and "
        "do not stop for a market in which nothing suitable is available. If the deadlines are "
        "missed the exchange fails and the transfer is a sale, with the tax due in that year.",
        "The replacement must be of like kind and in the United States: real property in the "
        "United States and real property outside it are not like kind (26 U.S.C. 1031(h)).",
        "Exchanging keeps the capital in one asset, in one market, with the management that "
        "comes with it - the opposite of what the sell-and-diversify path buys.",
        "The commission and other costs of the transfer out are not deductible and are not "
        "added to the replacement's basis: section 1031(d) sets that basis by reference to "
        "the basis of the property given up, so the costs are paid with no tax offset.",
        "An exchange between related parties carries a two-year look-forward: if either side "
        "disposes within two years, the deferral is unwound (26 U.S.C. 1031(f)).",
    ]


def main() -> dict:
    out = {
        "meta": {
            "horizon_years": HORIZON,
            "inherit_years": INHERIT_YEARS,
            "rounding": "Every published dollar figure is rounded to the nearest $10.",
            "conventions": {
                "house_growth": G,
                "inflation": INFL,
                "equity_return_gross": EQ,
                "equity_tax_drag": DRAG,
                "selling_cost_pct": SELL_PCT,
                "combined_gain_rate": GAIN_RATE,
                "recapture_rate": REC_RATE,
                "depreciation_life_years": DEPRECIATION_LIFE,
                "depreciable_share": 0.8,
            },
            "src_ids": sorted(set(SRC_IDS.values())),
        },
        "basis_rule": {
            "rule": "The basis of property inherited from a decedent is generally its fair "
                    "market value on the date of the decedent's death, whether or not an "
                    "estate tax return is filed; the alternate valuation date applies only "
                    "if the executor files Form 706 and elects it on that return.",
            "src": "irs_basis",
        },
        "sell_timing": sale_timing(),
        "exchange": exchange_case(),
        "conditions": conditions(),
        "frictions": frictions(),
    }
    (DATA / "disposition.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print("wrote assets/data/disposition.json")
    return out


if __name__ == "__main__":
    main()
