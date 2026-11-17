"""Keep-and-borrow path: take the cash out of Property A without selling the house.

Reads  : assets/data/inputs.json, assets/data/model.json
Writes : assets/data/borrow.json

The pure-path model runs five choices, four of them assume the house is kept or
sold, and the improvement register left one gap: the carrying cost of borrowing
was priced on the estate liquidity page, but the path itself was never run. This
engine runs it. A cash-out refinance or a home equity line answers a question
selling answers only by destroying the asset: how does the heir get the money out
of a house they intend to keep?

Method, stated so it can be checked:

  * Every path is priced at the same three transfer years (2040, 2045, 2050), the
    same horizon and the same assumptions as the model on the other pages. The
    living-path terminal is read straight out of assets/data/model.json, so the
    two can never disagree: this engine adds a financing overlay to that terminal
    rather than recomputing it.
  * overlay(r) = loan x (1+r)^H  -  future value at r of every annual payment
                 -  the balance still owing at the horizon.
    r is the after-tax portfolio return the site already uses (equity gross less
    the tax drag); the payments are the amortising payments at the published
    mortgage average. So the overlay is exactly what the borrowed money is worth
    at the horizon once it has paid for itself, and it is negative whenever the
    money earns less than the loan charges.
  * The hurdle return is the r that makes the overlay zero. Because the loan is a
    lump sum received at once and the repayments are a stream, the hurdle sits at
    the loan rate itself when the amortisation term equals the horizon - which is
    the check that the arithmetic is right, and it is reported on the page.
  * No income tax is charged on the loan proceeds. Borrowed money is not income,
    and this site does not model a deduction for the interest either: Publication
    936 allows a deduction for interest on a home equity loan or line only where
    the funds were used to buy, build or substantially improve the home that
    secures the loan, and caps home acquisition debt at $750,000 for mortgages
    taken out after 15 December 2017. Investing the proceeds is neither.
  * No property tax consequence: under Revenue and Taxation Code section 62(c)(1)
    the creation, assignment, termination or reconveyance of a security interest is
    not a change in ownership, so borrowing does not trigger a reassessment and,
    unlike renting the home out, does not disturb the Proposition 19 analysis.

Deterministic: no network calls, no randomness, no clock reads. Published dollar
figures are rounded to the nearest $10. Nothing here names a person, a property, a
street, a parcel, a postal code, a county or a city. The loan-to-value rungs are
stated scenarios, not offers: no lender price, no underwriting answer and no credit
decision is published or assumed, and the amount a real lender would advance on a
property held in a trust is a question for the lender and the trustee.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
DATA = ROOT / "assets" / "data"

INPUTS = json.loads((DATA / "inputs.json").read_text(encoding="utf-8"))
MODEL = json.loads((DATA / "model.json").read_text(encoding="utf-8"))

A = INPUTS["property_a"]
B = INPUTS["property_b"]
V = INPUTS["verified_parameters"]
ASM = INPUTS["assumptions"]

HORIZON = int(ASM["horizon_years"])
R_EQ = ASM["equity_return_nominal_gross"]["baseline"] - ASM["equity_tax_drag"]["baseline"]
TSY_SHORT = ASM["treasury_short_yield_nominal"]["baseline"]
SELL_PCT = ASM["selling_cost_pct"]["baseline"]
HOUSE_G = ASM["house_growth"]["baseline"]

# --- published rates, each read at the publisher's own page on 17 November 2026 -----
# 30-year fixed average, Freddie Mac weekly series as published on FRED. The low and
# high are the extremes of the same published series inside calendar 2026.
RATE_LOW = 0.0598        # week of 26 February 2026, the lowest 2026 weekly average
RATE_NOW = 0.0711        # week of 12 November 2026, the latest published observation
RATE_HIGH = 0.0740       # weeks of 8 and 15 October 2026, the highest 2026 weekly average
# The index a variable-rate line is priced off. Board of Governors H.15 prime rate.
RATE_PRIME = 0.0700      # published daily, unchanged 1 October to 9 November 2026
RATE_RUNGS = [
    {"key": "low", "rate": RATE_LOW, "label": "5.98%",
     "basis": "the lowest weekly average published in 2026 (week of 26 February 2026)"},
    {"key": "now", "rate": RATE_NOW, "label": "7.11%",
     "basis": "the latest published weekly average (week of 12 November 2026)"},
    {"key": "high", "rate": RATE_HIGH, "label": "7.40%",
     "basis": "the highest weekly average published in 2026 (weeks of 8 and 15 October 2026)"},
]
LTV_RUNGS = [0.40, 0.60, 0.80]
TERM_RUNGS = [15, 20, 30]
SHOCK = [-0.40, 0.25, 0.10]   # the stated sequence used on the black-swan page
SRC = ["fred_mortgage", "fred_prime", "irs_p936", "rtc62", "uscode1701j3"]


def r10(x: float) -> int:
    """Round to the nearest $10, the site's publication convention."""
    return int((abs(x) + 5.0) // 10 * 10) * (1 if x >= 0 else -1)


def pc(x: float, places: int = 2) -> float:
    return round(x * 100, places)


def monthly_rate(annual: float) -> float:
    """Monthly rate that compounds to the published effective annual average."""
    return (1.0 + annual) ** (1 / 12.0) - 1.0


def payment_monthly(principal: float, annual: float, term_years: int) -> float:
    i = monthly_rate(annual)
    n = term_years * 12
    if i <= 0:
        return principal / n
    return principal * i / (1.0 - (1.0 + i) ** -n)


def balance_after(principal: float, annual: float, term_years: int, years: int) -> float:
    """Outstanding balance after `years`, on a fully amortising schedule."""
    i = monthly_rate(annual)
    n = term_years * 12
    m = min(years * 12, n)
    p = payment_monthly(principal, annual, term_years)
    if i <= 0:
        return max(0.0, principal - p * m)
    grow = (1.0 + i) ** m
    return max(0.0, principal * grow - p * (grow - 1.0) / i)


def fv_stream(amounts: list[float], rate: float) -> float:
    """Future value at the horizon of a year-end cash-flow stream, same convention as the model."""
    n = len(amounts)
    if rate == 0:
        return float(sum(amounts))
    return float(sum(a * (1.0 + rate) ** (n - 1 - j) for j, a in enumerate(amounts)))


def portfolio_path(loan: float, pays: list[float], rate: float,
                   returns: list[float] | None = None) -> tuple[float, float, int | None]:
    """Terminal portfolio value, its minimum, and the first year it goes negative.

    The borrowed cash is invested and every annual payment is drawn from it, so this
    is a self-funded schedule: a negative year means the household must find the
    payment somewhere else, which is the risk the page flags.
    """
    bal = float(loan)
    low = float(loan)
    shortfall: int | None = None
    for j, pay in enumerate(pays):
        r = returns[j] if (returns and j < len(returns)) else rate
        bal = bal * (1.0 + r) - pay
        low = min(low, bal)
        if bal < 0 and shortfall is None:
            shortfall = j + 1
    return bal, low, shortfall


def overlay(loan: float, pays: list[float], rate: float, balance_h: float) -> float:
    return loan * (1.0 + rate) ** len(pays) - fv_stream(pays, rate) - balance_h


def hurdle(loan: float, pays: list[float], balance_h: float) -> float:
    """The after-tax portfolio return at which borrowing is value-neutral."""
    lo, hi = -0.10, 0.60
    f = lambda r: overlay(loan, pays, r, balance_h)
    if f(lo) > 0 or f(hi) < 0:
        return float("nan")
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def case(loan: float, rate: float, term_years: int, interest_only: bool = False) -> dict:
    """One financing overlay on the living path."""
    if interest_only:
        pay = loan * rate
        n_pay = HORIZON
        balance = loan                      # never amortised: the line is interest only
        interest = pay * n_pay
    else:
        pmt = payment_monthly(loan, rate, term_years)
        pay = pmt * 12
        n_pay = min(term_years, HORIZON)     # an amortising loan stops being paid when it is repaid
        balance = balance_after(loan, rate, term_years, HORIZON)
        interest = pay * n_pay + balance - loan
    pays = [pay] * n_pay + [0.0] * (HORIZON - n_pay)
    end, low, shortfall = portfolio_path(loan, pays, R_EQ)
    end_shock, low_s, shortfall_s = portfolio_path(
        loan, pays, R_EQ,
        returns=[SHOCK[j] if j < len(SHOCK) else R_EQ for j in range(HORIZON)])
    # The overlay is what the borrowed money is worth at the horizon once the
    # repayments have been drawn from it AND the balance still owing is settled.
    ov = end - balance
    ov_shock = end_shock - balance
    return {
        "loan": r10(loan),
        "annual_payment": r10(pay),
        "monthly_payment": r10(pmt if not interest_only else pay / 12.0),
        "years_paid": n_pay,
        "total_interest": r10(interest),
        "balance_at_horizon": r10(balance),
        "portfolio_terminal": r10(end),
        "portfolio_minimum": r10(low),
        "first_shortfall_year": shortfall,
        "overlay_invested": r10(ov),
        "overlay_parked": r10(overlay(loan, pays, TSY_SHORT, balance)),
        "overlay_shock": r10(ov_shock),
        "shock_vs_baseline": r10(ov_shock - ov),
        "portfolio_minimum_shock": r10(low_s),
        "first_shortfall_year_shock": shortfall_s,
        "cost_if_spent": r10(fv_stream(pays, R_EQ) + balance - loan),
        "hurdle_return_pct": pc(hurdle(loan, pays, balance)),
        "interest_only": interest_only,
        "term_years": term_years,
    }


def build() -> dict:
    out: dict = {}
    out["meta"] = {
        "engine": "keep-and-borrow overlay on the living path",
        "horizon_years": HORIZON,
        "after_tax_portfolio_return_pct": pc(R_EQ),
        "parking_yield_pct": pc(TSY_SHORT),
        "house_growth_pct": pc(HOUSE_G),
        "rounding": "nearest $10",
        "deterministic": True,
    }
    out["rates"] = {
        "source": ["fred_mortgage", "fred_prime"],
        "rungs": [{"label": x["label"], "basis": x["basis"], "rate_pct": pc(x["rate"])}
                  for x in RATE_RUNGS],
        "prime_pct": pc(RATE_PRIME),
        "prime_basis": ("the prime rate published by the Board of Governors (H.15), unchanged "
                        "at 7.00 percent from 1 October to 9 November 2026. A home equity line is "
                        "quoted as prime plus a margin; the margin is a lender term, is not "
                        "published, and is not assumed here."),
        "mortgage_note": ("the three fixed rungs are the published 30-year fixed averages for "
                          "2026, not offers. A cash-out refinance on a specific property is priced "
                          "by a lender, and this site has no quote."),
    }
    out["ltv_rungs"] = [{"ltv_pct": pc(x), "label": f"{pc(x, 0):.0f}% of value"} for x in LTV_RUNGS]

    years_out = []
    for p in MODEL["paths"]:
        year = p["inherit_year"]
        value_at_death = p["value_at_death"]
        live = p["paths"]["live_in"]
        sell = p["paths"]["sell_equities"]
        live_sale_net = live["sale"]["net"]
        carry = live["carry_fv"]
        live_terminal = live["terminal"]
        sell_terminal = sell["terminal"]
        rungs = []
        for ltv in LTV_RUNGS:
            loan = ltv * value_at_death
            for rung in RATE_RUNGS:
                c = case(loan, rung["rate"], HORIZON)
                c["ltv_pct"] = pc(ltv, 0)
                c["ltv_label"] = f"{pc(ltv, 0):.0f}%"
                c["rate_pct"] = pc(rung["rate"])
                c["rate_label"] = rung["label"]
                c["rate_basis"] = rung["basis"]
                c["terminal_borrow"] = r10(live_terminal + c["overlay_invested"])
                c["gap_vs_live"] = r10(c["overlay_invested"])
                c["gap_vs_sell"] = r10(live_terminal + c["overlay_invested"] - sell_terminal)
                c["cash_released_vs_sale"] = r10(loan - sell["sale"]["costs"] - sell["sale"]["tax"])
                c["payment_vs_tax_multiple"] = round(c["annual_payment"] / p["bill_if_live_year1"], 1) \
                    if p["bill_if_live_year1"] else None
                rungs.append(c)
            # the interest-only line at the published prime
            c = case(loan, RATE_PRIME, HORIZON, interest_only=True)
            c["ltv_pct"] = pc(ltv, 0)
            c["ltv_label"] = f"{pc(ltv, 0):.0f}%"
            c["rate_pct"] = pc(RATE_PRIME)
            c["rate_label"] = "7.00% prime, interest only"
            c["rate_basis"] = ("a line priced at the published prime with no margin, interest only, "
                               "balance unchanged to the horizon")
            c["terminal_borrow"] = r10(live_terminal + c["overlay_invested"])
            c["gap_vs_live"] = r10(c["overlay_invested"])
            c["gap_vs_sell"] = r10(live_terminal + c["overlay_invested"] - sell_terminal)
            c["cash_released_vs_sale"] = r10(loan - sell["sale"]["costs"] - sell["sale"]["tax"])
            c["payment_vs_tax_multiple"] = round(c["annual_payment"] / p["bill_if_live_year1"], 1) \
                if p["bill_if_live_year1"] else None
            rungs.append(c)
        # amortisation-term rungs at the middle loan-to-value and the current rate
        terms = []
        for t in TERM_RUNGS:
            c = case(LTV_RUNGS[1] * value_at_death, RATE_NOW, t)
            c["term_years"] = t
            c["terminal_borrow"] = r10(live_terminal + c["overlay_invested"])
            c["gap_vs_live"] = r10(c["overlay_invested"])
            c["gap_vs_sell"] = r10(live_terminal + c["overlay_invested"] - sell_terminal)
            terms.append(c)
        years_out.append({
            "inherit_year": year,
            "value_at_death": value_at_death,
            "terminal_price": p["terminal_price"],
            "bill_if_live_year1": p["bill_if_live_year1"],
            "terminal_live": live_terminal,
            "terminal_sell": sell_terminal,
            "sell_costs": sell["sale"]["costs"],
            "sell_tax": sell["sale"]["tax"],
            "sale_net_at_horizon": live_sale_net,
            "carry_fv": carry,
            "horizon_year": year + HORIZON,
            "rungs": rungs,
            "term_rungs": terms,
        })
    out["years"] = years_out

    # Property B: the same overlay applied to the building the heir already owns, to
    # show that the arithmetic does not depend on which house carries the lien.
    b_value = B["estimated_market_value_2026"]
    out["property_b_note"] = {
        "value_2026": r10(b_value),
        "loan_at_60": r10(0.60 * b_value),
        "annual_payment": r10(payment_monthly(0.60 * b_value, RATE_NOW, HORIZON) * 12),
        "rent_now": r10(B["rent"]["annual"]),
        "payment_vs_rent_multiple": round(payment_monthly(0.60 * b_value, RATE_NOW, HORIZON) * 12
                                          / B["rent"]["annual"], 2),
        "src": ["fred_mortgage"],
    }

    out["rules"] = {
        "no_income_tax_on_proceeds": {
            "text": ("Loan proceeds are not income, so taking cash out does not start a tax bill; "
                     "the basis step-up at death is unaffected and the gain on a later sale is "
                     "measured from the same stepped-up basis. The selling cost the model charges "
                     "the sell path - 5.5 percent of the price in the baseline, which is the whole "
                     "of its outflow at inheritance because the gain at that date is nil - is the "
                     "cash a borrow path keeps."),
            "src": ["irs_basis", "irs_p523"],
        },
        "no_reassessment": {
            "text": ("Revenue and Taxation Code section 62(c)(1): a change in ownership does not "
                     "include the creation, assignment, termination or reconveyance of a security "
                     "interest, or the substitution of a trustee under a security instrument. "
                     "Borrowing against the home therefore does not trigger reassessment, and does "
                     "not disturb the Proposition 19 shelter the way renting the home out can."),
            "src": ["rtc62"],
        },
        "interest_not_deductible": {
            "text": ("Publication 936 (2025): interest on home equity loans and lines is deductible "
                     "only if the borrowed funds are used to buy, build or substantially improve the "
                     "taxpayer's home that secures the loan, and home acquisition debt taken out "
                     "after 15 December 2017 is limited to $750,000. Cash taken out to invest is "
                     "outside both. Whether any part of the interest is deductible as investment "
                     "interest against investment income is a question for the preparer; this site "
                     "assumes none, which is the conservative reading."),
            "src": ["irs_p936"],
        },
        "estate_tax_unaffected": {
            "text": ("Nothing on this page reduces federal estate tax. The tax is computed on the "
                     "estate as it stands at the date of death, and a loan the heir takes after the "
                     "transfer is the heir's obligation, not the decedent's; the borrowed cash then "
                     "sits in the heir's own wealth. A debt already registered against the property "
                     "at the date of death is a different question, and it belongs to the attorney "
                     "with the Form 706 deduction rules, not to this page."),
            "src": ["irs_i706", "irs_estate"],
        },
        "lender_limits": {
            "text": ("The federal rule that protects the transfer itself is 12 U.S.C. 1701j-3(d): a "
                     "due-on-sale clause may not be exercised on a transfer to a relative resulting "
                     "from the borrower's death, or where the borrower's children become owners, for "
                     "a loan on residential property with fewer than five dwelling units. That "
                     "protects an existing loan from acceleration; it does not oblige any lender to "
                     "advance new money, and whether a lender will lend against a property held in a "
                     "trust is a question for the lender and the trustee."),
            "src": ["uscode1701j3"],
        },
    }
    out["stress_note"] = (
        "The stated three-year sequence on this page is the same one the black-swan page uses - "
        "minus 40 percent, plus 25 percent, plus 10 percent, then the baseline net return - applied "
        "to the invested portfolio annually. It is a stress, not a forecast, and it is not a dated "
        "replay. The house price is not shocked in this table; the regime runs on the black-swan "
        "page do that, and they already put the living path behind the selling path before any "
        "financing overlay is added."
    )
    out["limitation"] = {
        "not_an_offer": ("Loan-to-value rungs of 40, 60 and 80 percent are stated scenarios. No "
                         "official source publishes what a lender would advance against this "
                         "property, and this site does not assume a quote exists."),
        "no_underwriting": ("Debt-to-income limits, mortgage insurance, prepayment penalties, "
                            "closing costs and whether a trust-held property is eligible at all are "
                            "not modelled. Closing costs on a refinance are the one number a lender "
                            "must supply before any figure here means anything."),
        "cash_flow": ("The overlay funds the payment from the borrowed money itself. If the "
                      "household spends the proceeds, the payment has to come from income, and the "
                      "cost of the money column is the honest figure to read instead."),
    }
    return out


def main() -> None:
    out = build()
    (DATA / "borrow.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                                      encoding="utf-8")
    rows = sum(len(y["rungs"]) for y in out["years"])
    print(f"Wrote assets/data/borrow.json: {len(out['years'])} transfer years, {rows} financing rungs")
    for y in out["years"]:
        mid = next(r for r in y["rungs"] if r["ltv_pct"] == 60 and r["rate_pct"] == 7.11)
        print(f"  {y['inherit_year']}: loan {mid['loan']:,}/yr payment {mid['annual_payment']:,} "
              f"overlay {mid['overlay_invested']:,} hurdle {mid['hurdle_return_pct']}% "
              f"shortfall year {mid['first_shortfall_year']}")


if __name__ == "__main__":
    main()
