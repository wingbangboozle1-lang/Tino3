"""Deterministic estate-liquidity and borrowing engine.

Reads  : assets/data/inputs.json, assets/data/model.json, assets/data/mixed.json
Writes : assets/data/liquidity.json

Answers one question the pure-path model does not: if the estate owes federal
estate tax, how is that tax paid, when, and what does each way of paying it
cost? It also prices the two-person household case, which the model otherwise
runs on single-filer assumptions throughout.

Deterministic: no network calls, no randomness, no clock reads. Every rule
implemented here was read from an official source; the source ids are carried
into the output so the site can cite them.

Privacy: nothing in this file or its output names a person, a property, a
parcel, a postal code, a county or a city, and no estate size is either stored
or published. The estate's own size is deliberately unknown to this engine: it
works in anonymous bands of the amount above the exclusion, and the household
applies its own number privately.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "data"

INPUTS = json.loads((DATA / "inputs.json").read_text(encoding="utf-8"))
MODEL = json.loads((DATA / "model.json").read_text(encoding="utf-8"))
MIXED = json.loads((DATA / "mixed.json").read_text(encoding="utf-8"))

V = INPUTS["verified_parameters"]
ASM = INPUTS["assumptions"]

# ------------------------------------------------------------------ rules ---
# Every figure below was read from an official publisher; see the source ids.
ESTATE_TAX_RATE = 0.40                 # top federal rate, Instructions for Form 706
DUE_MONTHS = 9                         # estate tax return and tax due, 9 months after death
FILE_EXTENSION_MONTHS = 6              # automatic extension of time to file, Form 4768
PAY_EXTENSION_MAX_YEARS = 10           # extension of time to pay for reasonable cause
UNDERPAYMENT_RATE = 0.07               # published for the fourth quarter of 2026
FED_SHORT_TERM = 0.04                  # published for the fourth quarter of 2026
UNDERPAYMENT_LOW = 0.03                # lowest quarterly underpayment rate published 2022-2026
UNDERPAYMENT_HIGH = 0.08               # highest quarterly underpayment rate published 2022-2026
MORTGAGE_RATE = 0.0711                 # 30-year fixed average, week of 12 November 2026
MORTGAGE_LOW = 0.0598                  # lowest weekly average published in 2026
MORTGAGE_HIGH = 0.0740                 # highest weekly average published in 2026
DAYS = 365                             # section 6622 compounds daily; a 365-day year is used
JOINT_121 = V["section121_exclusion_joint"]["value"]
SINGLE_121 = V["section121_exclusion_single"]["value"]
TREASURY_SHORT = ASM["treasury_short_yield_nominal"]["baseline"]
EXCESS_BANDS = [1_000_000, 2_500_000, 5_000_000, 10_000_000, 20_000_000]
TERMS = [1, 3, 5, 10]


def r10(x: float) -> int:
    """Round to the nearest $10, the site's publication convention."""
    return int(round(x / 10.0)) * 10


def daily_year(rate: float) -> float:
    """One year of daily compounding at a nominal annual rate (section 6622)."""
    return (1.0 + rate / DAYS) ** DAYS


def balloon(total: float, rate: float, years: int) -> tuple[int, int]:
    """Tax paid in one sum at the end of the deferral.  Returns (paid, interest)."""
    f = daily_year(rate) ** years
    paid = total * f
    return r10(paid), r10(paid - total)


def instalments(total: float, rate: float, years: int) -> tuple[int, int]:
    """Tax retired by equal annual instalments, interest compounding daily on the balance.

    The instalment is the level annual payment that clears the balance over the term at
    the effective annual rate implied by daily compounding, so the tax really is paid
    off rather than rolled forward.  Returns (total paid, interest).
    """
    f = daily_year(rate)
    eff = f - 1.0
    if eff <= 0:
        return r10(total), 0
    per = total * eff / (1.0 - f ** (-years))
    balance = total
    paid = 0.0
    for year in range(years):
        balance *= f
        pay = balance if year == years - 1 else min(per, balance)
        balance -= pay
        paid += pay
    return r10(paid), r10(paid - total)


def forgone(total: float, years: int) -> int:
    """Return the estate would have earned on the same cash at the model's short yield."""
    return r10(total * ((1.0 + TREASURY_SHORT) ** years - 1.0))


def build() -> dict:
    out: dict = {}

    out["meta"] = {
        "built_from": "scripts/liquidity.py",
        "deterministic": True,
        "rounding": "every dollar figure rounded to the nearest $10",
        "privacy": ("No estate size, no name, no property, no parcel, no postal code, no county and no "
                    "city. The engine works in anonymous bands of the amount above the exclusion."),
    }

    out["clock"] = {
        "estate_tax_rate": ESTATE_TAX_RATE,
        "due_months_after_death": DUE_MONTHS,
        "file_extension_months": FILE_EXTENSION_MONTHS,
        "pay_extension_max_years": PAY_EXTENSION_MAX_YEARS,
        "underpayment_rate": UNDERPAYMENT_RATE,
        "federal_short_term_rate": FED_SHORT_TERM,
        "underpayment_low": UNDERPAYMENT_LOW,
        "underpayment_high": UNDERPAYMENT_HIGH,
        "rate_formula": "federal short-term rate plus 3 percentage points",
        "compounding": "daily",
        "src": ["irs_filing_eg", "irs_i4768", "irs_interest", "uscode6621", "uscode6622"],
        "interest_runs_from": ("the original due date, whether or not an extension of time to file or "
                               "to pay has been granted"),
        "interest_src": ["irs_i4768", "uscode6601"],
    }

    # 1. The tax itself, in anonymous bands of the amount above the exclusion.
    bands = []
    for excess in EXCESS_BANDS:
        tax = excess * ESTATE_TAX_RATE
        row = {
            "excess": r10(excess),
            "tax": r10(tax),
            "tax_rate": ESTATE_TAX_RATE,
            "due_months": DUE_MONTHS,
            "terms": [],
        }
        for years in TERMS:
            paid_b, int_b = balloon(tax, UNDERPAYMENT_RATE, years)
            paid_i, int_i = instalments(tax, UNDERPAYMENT_RATE, years)
            gave_up = forgone(tax, years)
            lo_b, _ = balloon(tax, UNDERPAYMENT_LOW, years)
            hi_b, _ = balloon(tax, UNDERPAYMENT_HIGH, years)
            row["terms"].append({
                "years": years,
                "balloon_paid": paid_b,
                "balloon_interest": int_b,
                "instalment_paid": paid_i,
                "instalment_interest": int_i,
                "return_given_up": gave_up,
                "deferral_advantage": r10(gave_up - int_i),
                "balloon_low": lo_b,
                "balloon_high": hi_b,
            })
        row["src"] = ["irs_estate", "irs_i706", "irs_interest", "uscode6621", "uscode6622"]
        bands.append(row)
    out["excess_bands"] = bands

    # 2. What the house itself can create, at each inheritance year.
    excl = {e["year"]: e["amount"] for e in MODEL["exclusion_projection"]}
    at_inheritance = []
    for path in MODEL["paths"]:
        year = path["inherit_year"]
        value = path["value_at_death"]
        at_inheritance.append({
            "inherit_year": year,
            "exclusion_projected": r10(excl[year]),
            "exclusion_basis": "mechanical indexation at the modelled inflation rate; not law and not a forecast",
            "house_value_at_death": r10(value),
            "house_share_of_exclusion": round(value / excl[year], 4),
            "tax_if_house_is_the_excess": r10(value * ESTATE_TAX_RATE),
            "tax_share_of_house": ESTATE_TAX_RATE,
            "couple_exclusion_projected": r10(2 * excl[year]),
            "couple_excess_allowance_over_single": r10(excl[year]),
            "src": ["irs_estate", "ssa_trustees", "irs_i706"],
        })
    out["at_inheritance"] = at_inheritance

    # 3. Borrowing against the property instead of selling it.
    anchor = 1_000_000
    borrowing = []
    for years in TERMS:
        interest = anchor * MORTGAGE_RATE * years
        borrowing.append({
            "years": years,
            "principal": r10(anchor),
            "rate": MORTGAGE_RATE,
            "interest": r10(interest),
            "interest_low": r10(anchor * MORTGAGE_LOW * years),
            "interest_high": r10(anchor * MORTGAGE_HIGH * years),
            "total_paid": r10(anchor + interest),
        })
    out["borrowing"] = {
        "principal": r10(anchor),
        "rate": MORTGAGE_RATE,
        "rate_low": MORTGAGE_LOW,
        "rate_high": MORTGAGE_HIGH,
        "rate_basis": ("The published 30-year fixed mortgage average for the week of 12 November 2026; "
                       "the low and high are the lowest and highest weekly averages published in 2026"),
        "method": ("Interest only, on a constant balance, with no amortisation and no deduction assumed "
                   "for the interest - which is the conservative reading"),
        "rows": borrowing,
        "src": ["fred_mortgage"],
        "limit": ("A rate for the 2040s is not published and is not forecast here. The interest is a "
                  "carrying cost only: it says nothing about what the borrowed money earns, and nothing "
                  "about whether the lender will lend against a property held in trust."),
    }

    # 4. The two-person household case, on the income tax side.
    #    Every mixed path already priced by the model is repriced with the joint exclusion.
    joint_rows = []
    for p in MIXED["paths"]:
        sale = p["sale"]
        gain = sale.get("gain", 0)
        excl_used = p.get("exclusion_121", 0) or 0
        tax_single = sale.get("tax", 0)
        taxable_single = max(0.0, gain - excl_used)
        rate = (tax_single / taxable_single) if taxable_single > 0 else 0.0
        # The exclusion is only in play where the single-filer case already claimed it: a
        # property that is not the owner's main home at the date of sale gets no exclusion,
        # joint return or not.  Doubling the amount there would invent a relief.
        if excl_used > 0:
            tax_joint = max(0.0, gain - JOINT_121) * rate
        else:
            tax_joint = tax_single
        joint_rows.append({
            "occupy_years": p["occupy_years"],
            "mode": p["mode"],
            "label": p["label"],
            "gain": r10(gain),
            "exclusion_single": r10(excl_used),
            "exclusion_joint": r10(JOINT_121) if p["mode"] == "sell" else 0,
            "tax_single": r10(tax_single),
            "tax_joint": r10(tax_joint),
            "saving": r10(tax_single - tax_joint),
            "both_spouses_must_occupy": p["mode"] == "sell" and p["occupy_years"] >= 2,
            "net_single": r10(sale.get("net", 0)),
            "net_joint": r10(sale.get("net", 0) + (tax_single - tax_joint)),
        })
    out["joint_case"] = {
        "single_exclusion": SINGLE_121,
        "joint_exclusion": JOINT_121,
        "rule": ("Either spouse may meet the ownership test, but both spouses must meet the use test "
                 "individually: each must have lived in the home for at least 24 months of the 5 years "
                 "before the sale."),
        "gain_tax_rate": ASM["combined_gain_tax_rate"]["baseline"],
        "rows": joint_rows,
        "src": ["irs_tc701", "irs_p523"],
        "limit": ("Only the exclusion amount changes. Depreciation recapture, which the letting paths "
                  "carry, is not reduced by the section 121 exclusion, so the letting rows move by less "
                  "than the living rows."),
    }

    # 5. Where the cash can come from.  Qualitative, one official rule each.
    out["cash_sources"] = [
        {"source": "Cash and marketable assets already in the estate",
         "rule": "Pays the tax at the due date. No interest runs. Nothing has to be sold at a forced date.",
         "cost": "The return those assets would otherwise have earned.",
         "src": ["irs_filing_eg"]},
        {"source": "Sell the house",
         "rule": ("A sale soon after death carries almost no capital gains tax, because property acquired "
                  "from a decedent takes a basis equal to its value at death."),
         "cost": "Selling costs, modelled on this site at 5.5% of the price, plus the loss of the house.",
         "src": ["irs_basis", "irs_tc701"]},
        {"source": "Borrow against the house or against Property B",
         "rule": ("Keeps the asset and raises the cash. Nothing in the Code requires the estate to sell "
                  "before it borrows."),
         "cost": ("Interest at the lender's rate, published averages for which are on the source ledger. "
                  "This site assumes no tax deduction for that interest."),
         "src": ["fred_mortgage"]},
        {"source": "Extension of time to pay, section 6161(a)(2)",
         "rule": ("A discretionary extension for reasonable cause, granted one year at a time for up to "
                  "10 years, and only for the amount of the cash shortage. It is not an extension of "
                  "time to file, and interest runs from the due date regardless."),
         "cost": "Interest at the underpayment rate, compounded daily, from the original due date.",
         "src": ["irs_i4768", "uscode6601", "uscode6622"]},
        {"source": "Installment payment for a closely held business, section 6166",
         "rule": ("A 5-year deferral followed by up to 10 annual installments, but only where an interest "
                  "in a closely held business exceeds 35% of the adjusted gross estate. Interest on the "
                  "2-percent portion runs at 2%; interest on the rest runs at 45% of the underpayment rate."),
         "cost": ("Interest at 2% on the 2-percent portion and at 45% of the underpayment rate on the rest. "
                  "A home occupied as a personal residence is not an interest in a closely held business on "
                  "the face of the statute, so this site does not assume the election is available."),
         "src": ["uscode6166", "uscode6601"]},
    ]

    out["estate_exclusions"] = [
        {"inherit_year": row["inherit_year"],
         "one_exclusion": row["exclusion_projected"],
         "two_exclusions": row["couple_exclusion_projected"],
         "difference": row["couple_excess_allowance_over_single"],
         "src": ["irs_estate", "irs_whatsnew", "rp_2022_32"]}
        for row in at_inheritance
    ]

    return out


def main() -> None:
    out = build()
    (DATA / "liquidity.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote assets/data/liquidity.json "
          f"({len(out['excess_bands'])} bands, {len(out['at_inheritance'])} inheritance years, "
          f"{len(out['joint_case']['rows'])} joint-case rows)")


if __name__ == "__main__":
    main()
