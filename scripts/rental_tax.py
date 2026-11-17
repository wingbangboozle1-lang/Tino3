#!/usr/bin/env python3
"""The letting path of Property A, priced the way the tax rules actually work.

Reads  : assets/data/inputs.json, assets/data/model.json
Writes : assets/data/rental_tax.json

Why this module exists
----------------------
Every other path on the site is priced after tax. The letting path is not.
`rent_carry_fv` in scripts/model.py credits gross rent and deducts the property
tax and the running costs, and then charges no income tax on what is left. It
also reduces the sale basis by thirty years of depreciation and charges
recapture on that depreciation at sale, while never allowing the depreciation
as a deduction against the rent. So the published letting path is generous in
one direction (the rent is untaxed) and harsh in the other (a deduction that
was never taken is recaptured), and neither direction is stated anywhere.

The rent input is empty, so the published baseline is not wrong - it simply
carries cost and no income, which is the conservative case. But the break-even
rent the site publishes is computed on that untaxed basis, and the moment a
written rent opinion is entered the path will be overstated by the whole of the
income tax on the rent. This module closes that before it is needed.

What is modelled
----------------
For the 2045 inheritance over the model's thirty-year horizon, the letting path
is rebuilt year by year:

  rent                 grows with the modelled inflation rate
  running costs        grow with the modelled inflation rate
  property tax         reassessed at the date-of-death value, then capped at 2%
  depreciation         80% of the value (the model's building ratio) over 27.5
                       years on the straight-line method, mid-month convention,
                       land excluded - the terms of section 168
  taxable result       rent less running costs less property tax less
                       depreciation

Then five statutory treatments of that result, each one an official rule rather
than a modelling choice:

  untaxed              the convention the model uses today. Kept so the size of
                       the correction is visible.
  ordinary_usable      the year's result, positive or negative, hits the
                       heir's return at the combined ordinary rate. This needs
                       passive income to absorb it or, federally only, real
                       estate professional status.
  passive_suspended    a loss is suspended under section 469 and carried
                       forward; net income is taxed when it arises; every
                       suspended dollar is allowed in full in the year the heir
                       disposes of the entire interest to an unrelated party in
                       a fully taxable transaction.
  passive_allowance    as above, except the first $25,000 of loss each year is
                       deductible under section 469(i) because the heir
                       actively participates and modified adjusted gross income
                       is inside the phase-out.
  section 199A         as passive_suspended, except that where a year is net
                       positive and the safe harbour is met, 20% of it is
                       deducted before tax.

The rate is the household's own, and it is not supplied, so every case is run
at three stated combined ordinary rates rather than at one invented figure. The
lowest is the combined rate the site already publishes for gains; it is shown
as the floor of the grid, not because rent is taxed at it.

Determinism, rounding and privacy
---------------------------------
No randomness, no network access, no wall-clock input. Every dollar written out
is rounded to the nearest $10 with the root model's own money10(). No name,
street address, postal code, parcel identifier, city or county name, rent
estimate, income figure or filing status is added here: the rent input is the
same empty input the root model uses, and every rate in the grid is labelled a
stated scenario.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "data"
sys.path.insert(0, str(ROOT / "scripts"))

import model as base  # noqa: E402  (the root edition's model, for identical constants)

A = base.A
ASM = base.ASM
money10 = base.money10
bill_for = base.bill_for
sale_proceeds = base.sale_proceeds

FIT_A = base.FIT_A
COST_A_BASE = base.COST_A_BASE

MODEL = json.loads((DATA / "model.json").read_text(encoding="utf-8"))

INHERIT_YEAR = 2045
HORIZON = int(ASM["horizon_years"])
G = float(ASM["house_growth"]["baseline"])
INFL = float(ASM["inflation"]["baseline"])
EQ = float(ASM["equity_return_nominal_gross"]["baseline"])
DRAG = float(ASM["equity_tax_drag"]["baseline"])
CAP_GROWTH = float(ASM["prop19_cap_growth"]["baseline"])
SELL_PCT = float(ASM["selling_cost_pct"]["baseline"])
GAIN_RATE = float(ASM["combined_gain_tax_rate"]["baseline"])
REC_RATE = float(ASM["depreciation_recapture_rate"]["baseline"])
FIXED_GROWTH = float(ASM["fixed_charge_growth"]["baseline"])
MAINT_RENT = float(A["annual_costs"]["maintenance_pct_rental"]["value"])

# Section 168: residential rental property is 27.5-year property recovered on the
# straight-line method with the mid-month convention. Land is not depreciable, which
# is why the model's 80% building ratio is applied to the value first.
MACRS_YEARS = 27.5
BUILDING_RATIO = 0.80
# Section 469(i): the special allowance for a rental real estate loss against
# nonpassive income, before its modified adjusted gross income phase-out.
ALLOWANCE = 25_000.0
# Section 199A(a): the deduction is 20% of qualified business income.
QBI_RATE = 0.20

# Stated combined ordinary rates. None of these is the household's rate; the
# household has not supplied one. They are the rungs of a sensitivity.
RATE_LOW = 0.371     # the combined gain rate the site already publishes
RATE_MID = 0.503     # 37% federal top ordinary + 13.3% California top
RATE_HIGH = 0.551    # the two above + the 1% section 17043 surcharge + 3.8% NIIT

P45 = next(p for p in MODEL["paths"] if p["inherit_year"] == INHERIT_YEAR)
TARGET = float(P45["paths"]["sell_equities"]["terminal"])


def depreciation_schedule(building: float, years: int) -> list[float]:
    """MACRS straight-line over 27.5 years, land already excluded.

    An equal amount each year until the building is recovered, so a thirty-year
    let exhausts the building part-way through the twenty-eighth year. The total
    over the horizon equals the model's own `deprec` term, which is what keeps
    the basis reduction and the recapture charge consistent with the rest of the
    site.
    """
    annual = building / MACRS_YEARS
    out: list[float] = []
    remaining = building
    for _ in range(years):
        take = min(annual, remaining)
        out.append(take)
        remaining -= take
    return out


def letting(rent0: float, treatment: str, rate: float, qbi: bool = False,
            allowance: float = 0.0, want_rows: bool = False,
            release: bool = True) -> dict:
    """One letting path, end to end, under one statutory treatment.

    `release` is False for the case in which the suspended losses are never
    allowed: the heir keeps the property until death, or the disposition is not
    of the entire interest to an unrelated party in a fully taxable transaction.
    Publication 925 is explicit about the death case - the losses are allowed
    only to the extent they exceed the step-up in the transferee's basis, and a
    date-of-death step-up to full market value wipes them out.
    """
    k = INHERIT_YEAR - 2026
    value = float(A["estimated_market_value_2026"]) * (1 + G) ** k
    building = BUILDING_RATIO * value
    deprec = depreciation_schedule(building, HORIZON)
    maint_rent = MAINT_RENT

    fit_T = dict(FIT_A)
    fit_T["fixed_base"] = FIT_A["fixed_base"] * (1 + FIXED_GROWTH) ** (
        INHERIT_YEAR - FIT_A["base_year"])

    rate_fv = EQ - DRAG
    av = value                      # reassessed at the date-of-death value
    fv_cash = 0.0
    suspended = 0.0
    tax_nominal = 0.0
    rows: list[dict] = []

    for j in range(HORIZON):
        year = INHERIT_YEAR + j
        rent = rent0 * (1 + INFL) ** j
        opex = (COST_A_BASE + maint_rent * value) * (1 + INFL) ** j
        ptax = bill_for(av, fit_T, year, INFL)
        av *= 1.02
        dep = deprec[j]

        pre_tax_cash = rent - opex - ptax
        taxable = pre_tax_cash - dep

        tax = 0.0
        allowed_now = 0.0
        qbi_deduction = 0.0
        if treatment == "untaxed":
            # The convention the model uses today: the rent is never taxed and the
            # depreciation is never allowed, but the basis still falls and the
            # recapture is still charged at sale.
            tax = 0.0
        elif taxable >= 0:
            # Net rental income is taxed when it arises. Section 469 does not defer
            # income; it defers losses.
            qbi_deduction = QBI_RATE * taxable if qbi else 0.0
            tax = max(0.0, taxable - qbi_deduction) * rate
        elif treatment == "ordinary_usable":
            tax = taxable * rate           # negative: a refund against other income
        elif treatment == "passive_allowance":
            loss = -taxable
            allowed_now = min(allowance, loss)
            tax = -allowed_now * rate
            suspended += loss - allowed_now
        else:                              # passive_suspended
            suspended += -taxable

        net_cash = pre_tax_cash - tax
        fv_cash += net_cash * (1 + rate_fv) ** (HORIZON - 1 - j)
        tax_nominal += tax
        if want_rows:
            rows.append({
                "year": year,
                "rent": money10(rent),
                "opex": money10(opex),
                "property_tax": money10(ptax),
                "depreciation": money10(dep),
                "taxable": money10(taxable),
                "allowed_now": money10(allowed_now),
                "suspended_added": money10(max(0.0, -taxable - allowed_now)),
                "tax": money10(tax),
                "suspended_balance": money10(suspended),
                "after_tax_cash": money10(net_cash),
            })

    total_dep = sum(deprec)
    price = value * (1 + G) ** HORIZON
    sale = sale_proceeds(price, value - total_dep, SELL_PCT, GAIN_RATE, REC_RATE,
                         total_dep)

    # Section 469(g): on a complete disposition of the entire interest, in a
    # transaction where all gain or loss is recognised, to a person who is not
    # related, every suspended loss still unused is allowed in full that year. It
    # is an ordinary deduction, so its value is the rate. Where the released
    # amount exceeds the year's income it becomes a net operating loss carryforward
    # rather than a refund; this model assumes it is absorbed, and says so.
    released = 0.0
    if release and treatment in ("passive_suspended", "passive_allowance"):
        released = suspended * rate

    terminal = fv_cash + sale["net"] + released
    return {
        "terminal": money10(terminal),
        "fv_cash": money10(fv_cash),
        "sale_net": money10(sale["net"]),
        "released_tax_saving": money10(released),
        "suspended_at_exit": money10(suspended),
        "depreciation_total": money10(total_dep),
        "recapture_tax": money10(sale["recapture"] * REC_RATE),
        "tax_nominal": money10(tax_nominal),
        "rows": rows,
    }


def breakeven_rent(treatment: str, rate: float, qbi: bool = False,
                   allowance: float = 0.0, release: bool = True) -> float:
    """The initial annual rent at which the letting path matches the best path."""
    lo, hi = 0.0, 5_000_000.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if letting(mid, treatment, rate, qbi, allowance, release=release)["terminal"] < TARGET:
            lo = mid
        else:
            hi = mid
    return money10((lo + hi) / 2)


CASES = (
    # (key, label, treatment, rate, qbi, allowance, note)
    ("untaxed", "As the model computes it today: the rent is never taxed",
     "untaxed", RATE_LOW, False, 0.0,
     "The convention every letting figure on this site uses. It is shown so the size "
     "of the correction below is visible, not because it is the law."),
    ("ordinary_low", "Every year's result hits the return, at the site's combined gain rate",
     "ordinary_usable", RATE_LOW, False, 0.0,
     "Needs passive income to absorb a loss or, federally only, real estate "
     "professional status. The rate is the floor of this grid, not the rate on rent."),
    ("ordinary_mid", "Every year's result hits the return, at the top ordinary rate",
     "ordinary_usable", RATE_MID, False, 0.0,
     "37% federal top ordinary plus 13.3% California top. The most favourable "
     "treatment a loss can get, and the least likely to be available."),
    ("ordinary_high", "Every year's result hits the return, at the top rate with both surcharges",
     "ordinary_usable", RATE_HIGH, False, 0.0,
     "The two above, plus the 1% section 17043 surcharge above $1,000,000 and the "
     "3.8% net investment income tax."),
    ("suspended_low", "A loss is suspended and freed on a complete sale, at the site's combined gain rate",
     "passive_suspended", RATE_LOW, False, 0.0,
     "Section 469 carries the loss forward and allows it all in the year the whole "
     "interest is sold to a stranger."),
    ("suspended_mid", "A loss is suspended and freed on a complete sale, at the top ordinary rate",
     "passive_suspended", RATE_MID, False, 0.0,
     "The treatment California applies to every rental, because California does not "
     "have the federal real estate professional exception."),
    ("suspended_high", "A loss is suspended and freed on a complete sale, at the top rate with both surcharges",
     "passive_suspended", RATE_HIGH, False, 0.0,
     "The same treatment, priced at the highest combined rate in this grid."),
    ("allowance_mid", "As suspended, but the first $25,000 of loss each year is deductible",
     "passive_allowance", RATE_MID, False, ALLOWANCE,
     "The section 469(i) special allowance, if the heir actively participates and "
     "modified adjusted gross income survives the phase-out. $25,000 and $150,000 "
     "have never been indexed."),
    ("qbi_mid", "As suspended, but 20% of a net positive year is deducted",
     "passive_suspended", RATE_MID, True, 0.0,
     "The section 199A deduction, if the rental real estate enterprise meets the "
     "250-hour safe harbour and keeps the records that safe harbour demands."),
    ("never_released_mid", "As suspended, but the losses are never allowed at all",
     "passive_suspended", RATE_MID, False, 0.0,
     "What happens if the heir keeps the property until death, or disposes of it "
     "in a way section 469(g) does not recognise. Publication 925 allows the "
     "suspended losses at death only to the extent they exceed the step-up in the "
     "transferee's basis, and a step-up to full market value leaves nothing."),
)

HEADLINE = "suspended_mid"


def year_one_components() -> dict:
    """The three deductions a letting year carries, in the first year of the let.

    Published because the middle figure is the line that decides which set of
    rules governs: below it the letting is a tax loss every year and section 469
    decides what happens to that loss, and above it the rent is simply taxed.
    """
    k = INHERIT_YEAR - 2026
    value = float(A["estimated_market_value_2026"]) * (1 + G) ** k
    building = BUILDING_RATIO * value
    fit_T = dict(FIT_A)
    fit_T["fixed_base"] = FIT_A["fixed_base"] * (1 + FIXED_GROWTH) ** (
        INHERIT_YEAR - FIT_A["base_year"])
    opex = COST_A_BASE + MAINT_RENT * value
    ptax = bill_for(value, fit_T, INHERIT_YEAR, INFL)
    dep = building / MACRS_YEARS
    return {
        "running_costs": money10(opex),
        "property_tax": money10(ptax),
        "depreciation": money10(dep),
        "cash_cost_annual": money10(opex + ptax),
        "cash_cost_monthly": money10((opex + ptax) / 12.0),
        "tax_loss_threshold_annual": money10(opex + ptax + dep),
        "tax_loss_threshold_monthly": money10((opex + ptax + dep) / 12.0),
    }


def build() -> dict:
    value = float(P45["value_at_death"])
    building = BUILDING_RATIO * float(A["estimated_market_value_2026"]) * (1 + G) ** (
        INHERIT_YEAR - 2026)
    deprec = depreciation_schedule(building, HORIZON)

    cases = []
    for key, label, treatment, rate, qbi, allowance, note in CASES:
        release = key != "never_released_mid"
        be = breakeven_rent(treatment, rate, qbi, allowance, release)
        zero = letting(0.0, treatment, rate, qbi, allowance, release=release)
        cases.append({
            "key": key,
            "label": label,
            "treatment": treatment,
            "rate": rate,
            "qbi": qbi,
            "allowance": allowance,
            "note": note,
            "breakeven_rent_annual": be,
            "breakeven_rent_monthly": money10(be / 12.0),
            "terminal_at_zero_rent": zero["terminal"],
            "gap_to_best_at_zero_rent": money10(TARGET - zero["terminal"]),
            "tax_nominal_at_zero_rent": zero["tax_nominal"],
            "suspended_at_exit_zero_rent": zero["suspended_at_exit"],
            "released_tax_saving_zero_rent": zero["released_tax_saving"],
            "recapture_tax": zero["recapture_tax"],
            "best_path_unchanged": True,
        })

    headline = next(c for c in cases if c["key"] == HEADLINE)
    _, _, h_tr, h_rate, h_qbi, h_all, _ = next(
        c for c in CASES if c[0] == HEADLINE)
    rows = letting(headline["breakeven_rent_annual"], h_tr, h_rate, h_qbi, h_all,
                   want_rows=True)["rows"]
    shown = [rows[j] for j in list(range(10)) + list(range(14, HORIZON, 5))]
    if rows[-1] not in shown:
        shown.append(rows[-1])

    base_case = next(c for c in cases if c["key"] == "untaxed")
    taxed = [c for c in cases if c["key"] != "untaxed"]
    span = [c["breakeven_rent_annual"] for c in taxed]
    gap_span = [c["terminal_at_zero_rent"] for c in cases]

    return {
        "meta": {
            "edition": "The letting path, priced the way the tax rules work",
            "inherit_year": INHERIT_YEAR,
            "horizon_years": HORIZON,
            "rounding": "nearest $10",
            "deterministic": True,
            "rent_input": None,
            "rent_input_note": (
                "The letting path's rent input is empty, exactly as it is in the "
                "root model, so no market rent is invented here. Every figure below "
                "that depends on a rent is either a break-even solved for, or is "
                "stated at the empty input, which is the site's conservative case."),
            "rate_note": (
                "The three combined ordinary rates are stated scenarios, not the "
                "household's rate. The household's marginal rate was not supplied, "
                "so it is not assumed; the low rung is the combined rate this site "
                "already publishes for gains and is carried only as the floor of "
                "the grid."),
            "sources": ["uscode168", "irs_p925", "ftb_3801", "irs_niit_qa",
                        "irs_qbi", "irs_rp1938", "irs_tc559", "ftb_rates",
                        "rtc17043", "irs_2027"],
        },
        "value_at_death": money10(value),
        "building_basis": money10(building),
        "depreciation": {
            "building_ratio": BUILDING_RATIO,
            "years": MACRS_YEARS,
            "annual": money10(building / MACRS_YEARS),
            "total_over_horizon": money10(sum(deprec)),
            "year_one": money10(deprec[0]),
            "exhausted_in_year": next(
                (i + 1 for i, d in enumerate(deprec) if d < building / MACRS_YEARS - 1),
                HORIZON),
        },
        "target": money10(TARGET),
        "year_one": year_one_components(),
        "cases": cases,
        "headline_case": HEADLINE,
        "headline_rows": shown,
        "spread": {
            # The low and high are taken over the taxed cases only. The untaxed
            # convention is the thing being corrected, so it is published beside
            # the range rather than inside it.
            "breakeven_low": money10(min(span)),
            "breakeven_high": money10(max(span)),
            "published_untaxed_breakeven": base_case["breakeven_rent_annual"],
            "uplift_vs_untaxed": money10(max(span) - base_case["breakeven_rent_annual"]),
            "terminal_low": money10(min(gap_span)),
            "terminal_high": money10(max(gap_span)),
        },
    }


if __name__ == "__main__":
    out = build()
    (DATA / "rental_tax.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"rental_tax.json written: {len(out['cases'])} cases, "
          f"{len(out['headline_rows'])} year rows")
    for c in out["cases"]:
        print(f"  {c['key']:<16} rate {c['rate']:.3f}  break-even rent "
              f"{c['breakeven_rent_annual']:>10,}  terminal@0 "
              f"{c['terminal_at_zero_rent']:>12,}")
