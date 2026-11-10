"""Page content. Each function returns (slug, title, lead, body_html)."""
from __future__ import annotations

from sitekit import NAV, RETRIEVED, SOURCES, STATUS, cards, chip, esc, money, pct, src, table

OPT = {"live": "Live in Property A", "rent": "Rent Property A out",
       "sell_stocks": "Sell Property A, invest in a stock index fund",
       "sell_treasuries": "Sell Property A, invest in U.S. Treasuries"}

# ----------------------------------------------------------------------------- flags
# (id, group, item, why it is flagged, what to do, [sources])
FLAGS = [
    ("F-01", "Values left blank", "Home insurance premium for Property A", "The Department of Insurance publishes premiums only through an interactive tool. This session could not operate it, so no official figure was confirmed.", "Run the tool for the home's location, age and coverage amount, then get three written quotes.", ["CDI-TOOL"]),
    ("F-02", "Values left blank", "Rental-building insurance premium for Property B", "No official premium survey covers a landlord policy on a three-unit building. The state tool covers homeowner, condominium, renter and earthquake policies only, and the national regulators' report defines its dwelling fire category as owner-occupied.", "Ask a licensed broker for landlord quotes on a three-unit building with liability and loss-of-rent cover.", ["CDI-TOOL", "NAIC-HO"]),
    ("F-03", "Values left blank", "Statewide average homeowner premium", "The averages quoted by comparison sites (about $1,660 from the regulators' report and about $2,340 from a state data call) were not found on a page this session could read.", "Read the state average tables in the regulators' report before relying on either figure.", ["NAIC-HO", "CDI-DATA"]),
    ("F-04", "Values left blank", "Market rent for Property A", "The owner gave no rent estimate and the federal Fair Market Rent page could not be read. The model uses a $6,000 a month placeholder and reports the rent at which renting would catch up with selling.", "Get a written rental estimate from two local property managers.", ["HUD-FMR"]),
    ("F-05", "Unverified assumptions", "Rent for the third unit of Property B", "Assumed equal to the average of the two rented units ($3,580 a month). Nobody has priced the unit.", "Get a rental estimate; check whether the unit can lawfully be let.", ["SF-RENT"]),
    ("F-06", "Unverified assumptions", "Repair and maintenance budgets", "The owner gave no amounts and no official benchmark exists. The model uses 0.5% of value a year for Property A and 1.0% for Property B.", "Replace with the last five years of actual repair spending.", ["IRS-T414"]),
    ("F-07", "Unverified assumptions", "Property A tax rate and fixed charges", "The parcel's tax rate area was deliberately not looked up, because a parcel lookup would identify the home. A 1.20% rate plus about $800 of fixed charges reproduces the owner's latest bill within 1%.", "Read the rate and the direct charges from the bill.", ["LAO-250017", "BOE-LTA2602"]),
    ("F-08", "Unverified assumptions", "Property B fixed charges of about $1,100", "The owner's bill is about $1,100 more than the official rate applied to the assessed value. The individual charges were not itemised.", "Read the direct charges and special assessments section of the bill.", ["SF-TAX"]),
    ("F-09", "Unverified assumptions", "Solar credit on Property A", "Net metering lasts 20 years from the date the system was connected. That date is unknown, so the credit is counted only until 2039 and left blank afterwards.", "Find the permission-to-operate date on the utility account.", ["CPUC-NEM"]),
    ("F-10", "Facts to confirm", "Type of trust", "The step-up in tax basis is assumed. It does not apply to assets of an irrevocable trust that are outside the taxable estate, and a second step-up may be lost on assets held in a bypass trust after the first parent's death.", "Ask the trust's attorney which kind of trust holds each property and whether it should be updated.", ["IRS-RR232", "IRS-P551"]),
    ("F-11", "Facts to confirm", "Which home is the parents' principal residence", "The partial property-tax exclusion applies only to the home that is the parent's principal residence and becomes the heir's within one year. The plan assumes that home is Property A and that no unit of Property B qualifies.", "Confirm which property carries the Homeowners' Exemption today.", ["BOE-LTA2626", "BOE-P19"]),
    ("F-12", "Facts to confirm", "Rent rules that apply to Property B", "Whether the building is covered by the rent increase limit depends on its construction date, which this session does not know. Owner move-in rules were seen only on unofficial sites.", "Confirm coverage and the rules for occupying the third unit with the Rent Board.", ["SF-RENT"]),
    ("F-13", "Unverified assumptions", "The heir's tax rates", "The heir's income is unknown. The model uses 37.1% on rent and interest, 27.8% on Treasury interest, 28.1% on dividends and 34.1% on large one-time gains.", "Have a tax adviser rerun the model with the heir's real brackets.", ["IRS-RP2635", "FTB-RATES", "IRS-T559"]),
    ("F-14", "Unverified assumptions", "Stock market return of 7.0% a year", "No official body publishes an expected stock return. Official anchors are the 10-year Treasury yield and one year of Thrift Savings Plan results.", "Read the result at 5.0% and 9.0% as well; the break-even return is reported.", ["UST-YIELD", "TSP-RET"]),
    ("F-15", "Unverified assumptions", "Selling costs of 6.0%", "Only the county transfer tax, $1.10 per $1,000, is official. Commission, escrow and preparation costs are assumed.", "Ask two listing agents for a written net sheet.", ["SCC-DTT"]),
    ("F-16", "Values left blank", "Federal limit on deducting state and local taxes", "The current limit and its scheduled drop in 2030 were seen only on unofficial sites, so no figure is published here.", "Confirm on the IRS page before counting any deduction for property tax.", ["IRS-OBBB"]),
    ("F-17", "Facts to confirm", "California trust return thresholds", "The thresholds come from the 2019 edition of the state booklet.", "Confirm in the booklet for the year of death.", ["FTB-541"]),
    ("F-18", "Facts to confirm", "November 2026 ballot results", "Results are unofficial until the Secretary of State certifies them, due by 11 December 2026.", "Recheck Propositions 3 and 42 after certification.", ["SOS-RESULTS"]),
    ("F-19", "Facts to confirm", "February 2027 adjustment of the $1 million amount", "The next figure is not published yet. The California index fell 0.20% over the year to mid-2026, and the sources read do not say whether the amount can fall.", "Check the Board of Equalization letter in February or March 2027.", ["BOE-LTA2509", "FHFA-HPI"]),
    ("F-20", "Facts to confirm", "Size of the cash and investments to be inherited", "The owner described it only as considerable. The plan therefore reports how much room is left under the federal exclusion, not a tax bill.", "Add up every asset the parents own, including retirement accounts and life insurance.", ["IRS-706"]),
    ("F-21", "Unverified assumptions", "Federal exclusion after 2027", "The law indexes the exclusion for inflation. Later years are projected at 2.4% a year; the indexing formula was not read.", "Use each year's IRS revenue procedure when it is published.", ["IRS-RP2635", "SSA-TR"]),
    ("F-22", "Unverified assumptions", "Share of each property's value that is building", "Depreciation needs the building share of value. 30% for Property A and 40% for Property B are assumed.", "Use the land and improvement split from the date-of-death appraisal.", ["IRS-P551"]),
    ("I-01", "Irregularities in the owner's records", "Property B bill is about 2.1% of assessed value", "The official rate is 1.18%. The gap is consistent with about $1,100 of flat charges, which matter a great deal on a low assessed value.", "No action beyond F-08.", ["SF-TAX"]),
    ("I-02", "Irregularities in the owner's records", "One year of Property B's assessed values rose slightly less than the official factor", "The difference is under $50. Every other year matches the official factor.", "Compare that year with the bill; likely a transcription slip.", ["BOE-LTA2602"]),
    ("I-03", "Irregularities in the owner's records", "Property A shows the same bill amount in consecutive years, twice", "Assessed value rose in each of those years, so the bill should have changed.", "Compare with the original bills.", ["BOE-LTA2602"]),
    ("I-04", "Irregularities in the owner's records", "Property B's bill jumped by about $320 in one year and fell in another", "A step of that size on a small bill usually means a flat charge was added or removed.", "Read the direct charges on the bills for those years.", ["SF-TAX"]),
    ("I-05", "Irregularities in the owner's records", "2026 figures are incomplete", "No 2026 bill was supplied for either property and no 2026 assessed value for Property B. Both are projected.", "Add the 2026 bills when they arrive.", ["SF-TAX"]),
    ("R-01", "Irregularities in this repository", "Assessed values rounded to $10 still identify a parcel", "Until this integration the live site listed both assessed-value histories rounded to $10. Assessment rolls are public records, and a value that precise can be matched to one parcel and from there to an address and an owner. This edition publishes rounded levels instead and computes every projection from them.", "Owner decision: keep the privacy rounding, or restore exact figures knowing the risk.", ["GH-REPO", "BOE-LTA2602"]),
    ("R-02", "Irregularities in this repository", "Earlier commits still hold exact figures and postal codes", "This repository is public. A normal update cannot remove what earlier commits and pull requests contain.", "Only the owner can make the repository private or delete and recreate it.", ["GH-REPO"]),
    ("R-03", "Irregularities in this repository", "Two publishers deploy the same site", "GitHub's branch build and the Actions workflow both publish. The setting could not be changed with the credentials available. The repository root is now kept identical to the packaged site, so both publish the same pages.", "Owner: set the Pages source to GitHub Actions only.", ["GH-REPO"]),
    ("R-04", "Irregularities in this repository", "The previous edition described initiative 25-0017 as a live proposal", "The Secretary of State recorded on 18 May 2026 that it failed to qualify.", "Corrected on Law changes.", ["SOS-FAIL", "LAO-250017"]),
    ("R-05", "Irregularities in this repository", "The previous edition used a property tax rate of 1.18268325% for Property B", "The rate published for fiscal year 2026-27 is 1.18162182%.", "Corrected in the model.", ["SF-TAX"]),
    ("R-06", "Irregularities in this repository", "The previous edition predated or omitted several developments", "Missing: the 2027 federal exclusion, the November 2026 ballot results, the September 2026 appeal ruling on the Empty Homes Tax and the August 2026 guidance on multi-unit buildings.", "Added on Law changes and Tax thresholds.", ["IRS-IR133", "SOS-RESULTS", "SF-EHT", "BOE-LTA2626"]),
    ("R-07", "Irregularities in this repository", "Insurance averages in earlier editions came from comparison sites", "Those are not official sources.", "Removed; see F-01 to F-03.", ["CDI-TOOL"]),
    ("R-08", "Irregularities in this repository", "Several sessions claimed the same shared files at once", "At least three sessions claimed the packaging and verification scripts within one minute, and other pull requests were still open when this edition merged.", "Recorded on the coordination board.", ["GH-REPO"]),
]


def flag_note(*ids) -> str:
    return " ".join(f'<a class="flag" href="review.html#{i}">{i}</a>' for i in ids)


# ----------------------------------------------------------------------------- pages

def p_index(M):
    s = M["scenarios"]["2045"]
    o = s["options"]
    be = M["break_even"]["2045"]
    fy = o["live"]["first_year"]
    carry = (fy["property_tax"] + fy["insurance"] + fy["maintenance"] + fy["water"]) / s["a_value"]
    body = cards([
        ("Best plan on the numbers", "Sell, then reinvest", "Sell Property A soon after inheriting it and invest the proceeds. Keep Property B."),
        ("20-year result, sell and buy a stock index fund", money(o["sell_stocks"]["wealth_today"]), "Inheritance in 2045, in today's dollars"),
        ("20-year result, live in Property A", money(o["live"]["wealth_today"]), f"{money(o['live']['wealth_today'] - o['sell_stocks']['wealth_today'])} against selling, in today's dollars"),
        ("20-year result, rent Property A out", money(o["rent"]["wealth_today"]), f"Rent would have to reach {money(be['rent_equals_sell_treasuries'])} a month in today's dollars to match Treasuries"),
        ("Federal estate exclusion", "$15,000,000", "Per person in 2026; $15,480,000 in 2027. California has no estate or inheritance tax."),
        ("Room left under one exclusion", money(M["estate"][0]["headroom_one"]), "After both properties at today's estimates"),
    ])
    body += f"""
<div class="note"><b>The short answer.</b> Inherited property takes a new tax basis equal to its value at death, so selling soon afterwards produces almost no income tax. Keeping Property A costs about {pct(carry, 1)} of its value every year in property tax, insurance and upkeep and earns nothing unless someone pays rent. In every case tested, selling and reinvesting ends with more money than living in the house or renting it out. Living in it is still a reasonable choice if the heir wants that home: the page <a href="decision.html">Live, rent or sell</a> shows what that choice costs.</div>
<div class="note warn"><b>Before relying on any figure:</b> {len([f for f in FLAGS if f[0][0] == 'F'])} inputs are unverified or still to be confirmed. They are listed on <a href="review.html">Flagged for Review</a>, each with the official page to check.</div>
<h2>Sections</h2>
<div class="tiles">"""
    blurbs = {
        "executive-summary.html": "The findings in one page.",
        "decision.html": "The three options compared on the same 20-year horizon.",
        "projections.html": "Value, assessed value, property tax, upkeep, utilities and insurance for every year to 2055.",
        "property-a.html": "The single-family home: inputs, costs and what changes at inheritance.",
        "property-b.html": "The three-unit building: rent, costs and what changes at inheritance.",
        "insurance.html": "What official sources do and do not say about premiums.",
        "taxes.html": "How much can pass before tax, and how much room is left.",
        "law-changes.html": "Changes decided or under discussion, and what each does to the plan.",
        "inheritance.html": "The steps after a death, in order, with deadlines.",
        "review.html": "Everything unverified, uncertain or irregular.",
        "sources.html": "Every official source used, with how it was checked.",
        "method.html": "Assumptions, the model and how personal data is kept out.",
    }
    for href, label in NAV[1:]:
        body += f'<a class="tile" href="{href}"><b>{esc(label)}</b><span>{blurbs[href]}</span></a>'
    body += "</div>"
    return ("index.html", "Dashboard", "A plan for one home expected to be inherited through a trust between 2040 and 2050, with a second rental property kept in view.", body)


def scen_rows(s):
    rows = []
    for k in ("sell_stocks", "sell_treasuries", "rent", "live"):
        o = s["options"][k]
        ids = {"live": ["BOE-LTA2626", "BOE-LTA2509"], "rent": ["BOE-P19", "IRS-P527"],
               "sell_stocks": ["IRS-INHERIT", "SCC-DTT"], "sell_treasuries": ["IRS-INHERIT", "UST-YIELD"]}[k]
        fy = o["first_year"]
        if k.startswith("sell"):
            first = money(fy.get("dividends_after_tax", fy.get("interest_after_tax"))) + " reinvested"
            cum = "Reinvested"
        else:
            first, cum = money(o["first_year_cash"]), money(o["cumulative_cash"])
        rows.append(([OPT[k], first, cum, money(o["wealth"]), money(o["wealth_today"]), money(o["gap_to_best"])], "model", ids))
    return rows


def p_decision(M):
    b = ""
    b += "<h2>What each option means</h2>"
    b += table(["Option", "What happens", "Rule applied"], [
        (["Live in Property A", "The heir makes it a principal residence within one year and files two claims. The spare unit of Property B is let.",
          "Taxable value becomes the old assessed value plus any market value above that value and the adjusted $1 million. The exclusion ends if the heir moves out."], "verified", ["BOE-LTA2626", "BOE-P19"]),
        (["Rent Property A out", "The heir lives in the spare unit of Property B and lets Property A.",
          "A rental does not qualify for the exclusion, so the whole home is reassessed at market value as of the date of death."], "verified", ["BOE-P19"]),
        (["Sell Property A", "The heir lives in the spare unit of Property B, sells Property A in the year of inheritance and invests what is left after selling costs.",
          "Basis is generally the fair market value at the date of death, so only the change in value after death is taxable."], "verified", ["IRS-INHERIT", "IRS-P551"], "F-10"),
        (["Property B in every option", "Two units stay let. The building is reassessed at market value at inheritance.",
          "Each unit of a multi-unit building qualifies separately, and only a unit that was the parent's principal residence can qualify."], "verified", ["BOE-LTA2626"], "F-11"),
    ])
    b += "<h2>Results when the heir lives in Property A or in the spare unit of Property B</h2>"
    b += "<p>Each table follows one inheritance year for 20 years. Yearly cash is saved at the after-tax Treasury rate. At the end the house or portfolio is valued as if sold, after tax, so the options are compared on the same footing.</p>"
    for t in ("2040", "2045", "2050"):
        s = M["scenarios"][t]
        b += table(["Option", "Cash in first year", "Cash over 20 years", "Value after 20 years", "The same in today's dollars", "Gap to best"],
                   scen_rows(s), caption=f"Inheritance in {t}. Property A is then worth about {money(s['a_value'])}.", cls="nums")
    b += "<h2>Results when the heir needs a house like Property A anyway</h2>"
    b += "<p>Here the alternative to living in Property A is to sell it and rent a similar house, paying the rent out of the invested proceeds. Property B is fully let in both cases.</p>"
    rows = []
    for t in ("2040", "2045", "2050"):
        n = M["needs_home"][t]
        for k, label, ids in (("sell_stocks", "Sell, buy a stock index fund, rent a similar house", ["IRS-INHERIT", "TSP-RET"]),
                              ("sell_treasuries", "Sell, buy Treasuries, rent a similar house", ["IRS-INHERIT", "UST-YIELD"]),
                              ("live", "Live in Property A", ["BOE-LTA2626", "IRS-T701"])):
            rows.append(([t, label, money(n[k]["first_year_cash"]), money(n[k]["wealth_today"])], "model", ids, "F-04"))
    b += table(["Inheritance year", "Option", "Housing cost in first year", "Value after 20 years, today's dollars"], rows, cls="nums")
    b += "<h2>Break-even points</h2><p>These do not depend on the unverified figure they solve for.</p>"
    rows = []
    for t in ("2040", "2045", "2050"):
        be = M["break_even"][t]
        rows.append(([t, f"{be['stock_return_sell_equals_live']}%", f"{be['stock_return_sell_equals_live_needs_home']}%",
                      money(be["rent_equals_sell_treasuries"]) + " a month", money(be["rent_equals_sell_stocks"]) + " a month"], "model",
                     ["UST-YIELD", "BOE-P19"]))
    b += table(["Inheritance year", "Stock return at which selling only ties with living in Property A", "The same, if the heir would otherwise rent a similar house",
                "Rent for Property A, in today's dollars, at which renting ties with Treasuries", "Rent at which renting ties with a stock index fund"], rows, cls="nums")
    b += f"<h2>What changes the answer</h2><p>Inheritance in {M['sensitivity_year']}, value after 20 years in today's dollars.</p>"
    rows = [([x["case"], money(x["sell_stocks"]), money(x["sell_treasuries"]), money(x["rent"]), money(x["live"]), OPT[x["best"]]],
             "model", ["FHFA-HPI", "UST-YIELD"]) for x in M["sensitivity"]]
    b += table(["Case", "Sell, stock index fund", "Sell, Treasuries", "Rent out", "Live in", "Best"], rows, cls="nums")
    rows = [([x["case"], money(x["sell_stocks"]), money(x["sell_treasuries"]), money(x["live"]), OPT[x["best"]]], "model", ["FHFA-HPI", "UST-YIELD"])
            for x in M["needs_home_sensitivity"]]
    b += table(["Case, heir needs a similar house", "Sell, stock index fund", "Sell, Treasuries", "Live in", "Best"], rows, cls="nums")
    s = M["scenarios"]["2045"]
    bc = s["b_common"]
    b += "<h2>Why the numbers come out this way</h2>"
    b += table(["Driver", "Figure for an inheritance in 2045", "Why it matters"], [
        (["Tax on selling", "Almost none", "The basis resets to the value at death. Selling costs are the main loss."], "verified", ["IRS-INHERIT"], "F-10"),
        (["Selling costs", money(s["options"]["sell_stocks"]["first_year"]["selling_costs"]), "6.0% of the price, of which the county transfer tax is 0.11%."], "assumption", ["SCC-DTT"], "F-15"),
        (["Property tax if the heir lives in Property A", money(s["a_tax_live_first"]) + " in the first year", f"Taxable value of {money(s['a_taxable_live'])} after an exclusion of {money(s['addon'])} on top of the old assessed value."], "model", ["BOE-LTA2626", "BOE-LTA2509"]),
        (["Property tax if Property A is rented or left empty", money(s["a_tax_full_first"]) + " in the first year", f"Taxable value resets to the full {money(s['a_taxable_full'])}."], "model", ["BOE-P19"]),
        (["Rent Property A could earn", money(s["options"]["rent"]["first_year"]["rent"]) + " in the first year", "After 5% vacancy. Property tax, insurance and upkeep absorb nearly all of it."], "assumption", ["HUD-FMR"], "F-04"),
        (["Property B property tax", f"{money(bc['tax_before_transfer'])} before, {money(bc['property_tax'])} after", "The whole building is reassessed while rents stay limited, so its yearly surplus falls to about " + money(bc["net_before_income_tax"]) + " before income tax."], "model", ["BOE-LTA2626", "SF-TAX", "SF-RENT"], "F-12"),
    ])
    b += """<div class="note"><b>Reading the result.</b> Selling and buying a stock index fund comes first in every case tested, and selling into Treasuries alone beats keeping the house in the base case. The margin nearly disappears in the least favourable combination tested: house prices rising 4.9% a year, stocks returning 5.0% and an heir who would otherwise rent a similar house. Living in Property A beats Treasuries when home prices rise near their 35-year average or a similar house rents for well above the placeholder. Renting Property A out never comes first. The gap between selling and living in the house is the price of choosing that home; that is a personal decision, not an error.</div>
<div class="note warn"><b>Timing.</b> The house is reassessed from the date of death, so each month between death and sale costs roughly one twelfth of the yearly figures above. The one-year deadline to move in also runs from the date of death. Decide early.</div>"""
    return ("decision.html", "Live, rent or sell", "The three choices for Property A, compared over 20 years for an inheritance in 2040, 2045 or 2050.", b)


def p_summary(M):
    s = M["scenarios"]["2045"]
    o, bc, e = s["options"], s["b_common"], M["estate"]
    rows = [
        (["Best plan", "Sell Property A soon after inheriting it and invest the proceeds; keep Property B and let all the units the heir does not occupy.", "Highest 20-year result in every case tested."], "model", ["IRS-INHERIT", "BOE-P19"]),
        (["Value after 20 years, sell and buy a stock index fund", money(o["sell_stocks"]["wealth_today"]), "Inheritance in 2045, today's dollars, 7.0% a year assumed."], "model", ["IRS-INHERIT"], "F-14"),
        (["Value after 20 years, sell and buy Treasuries", money(o["sell_treasuries"]["wealth_today"]), "4.8% a year before tax."], "model", ["UST-YIELD", "SSA-TR"]),
        (["Value after 20 years, rent Property A out", money(o["rent"]["wealth_today"]), "$6,000 a month placeholder rent."], "model", ["BOE-P19"], "F-04"),
        (["Value after 20 years, live in Property A", money(o["live"]["wealth_today"]), "Includes rent from the spare unit of Property B."], "model", ["BOE-LTA2626"], "F-05"),
        (["Property tax on Property A today", money(M["status_quo"][0]["a_tax"]), "Rebuilt from an assessed value of about $550,000; within 1% of the owner's latest bill."], "model", ["BOE-LTA2602"], "F-07"),
        (["Property tax on Property A in 2045 if the heir lives there", money(s["a_tax_live_first"]), "Partial exclusion applies."], "model", ["BOE-LTA2626", "BOE-LTA2509"]),
        (["Property tax on Property A in 2045 otherwise", money(s["a_tax_full_first"]), "Full reassessment."], "model", ["BOE-P19"]),
        (["Property tax on Property B in 2045", f"{money(bc['tax_before_transfer'])} before inheritance, {money(bc['property_tax'])} after", "A rental cannot keep the old assessed value."], "model", ["BOE-P19", "SF-TAX"]),
        (["Federal estate tax exclusion", "$15,000,000 in 2026; $15,480,000 in 2027", "Per person. A surviving spouse can also use the first spouse's unused amount if a return is filed."], "verified", ["IRS-ESTATE", "IRS-IR133", "IRS-706"]),
        (["Room under one exclusion after both properties", f"{money(e[0]['headroom_one'])} today; about {money(e[5]['headroom_one'])} in 2045", "Tax is 40% of anything above the exclusion."], "model", ["IRS-706"], "F-20"),
        (["California and local death taxes", "None", "State law bars the state and every city and county from taxing an inheritance."], "verified", ["CA-RTC13301", "SCO-ESTATE"]),
        (["Home insurance, Property A", "—", "No official premium could be confirmed. The owner's $1,500 a year guess is used as a labelled assumption."], "unverified", ["CDI-TOOL"], "F-01"),
        (["Rental-building insurance, Property B", "—", "No official source covers this type of policy."], "unverified", ["CDI-TOOL", "NAIC-HO"], "F-02"),
    ]
    b = table(["Finding", "Figure", "Note"], rows)
    b += """<h2>What the heir should know now</h2>
<ul>
<li><b>The move-in rule is strict.</b> To keep part of Property A's low assessed value the heir must make it a principal residence within one year of the death, with no exceptions, and must stay. Moving out later triggers the full reassessed value, measured as of the date of death.</li>
<li><b>Property B is reassessed whatever happens.</b> Its property tax rises about elevenfold while rents stay limited. Its surplus after inheritance is small; review its future separately.</li>
<li><b>The solar credit will not last.</b> Net metering ends 20 years after the system was connected, which is before or during the inheritance window.</li>
<li><b>The trust type decides the income tax.</b> The plan assumes the properties are in the taxable estate and receive a new basis at death. Confirm it.</li>
<li><b>Nothing proposed today changes the plan.</b> The initiative to restore the old inheritance rules failed to qualify in May 2026. Bills to repeal the federal estate tax have not moved since February 2025.</li>
</ul>"""
    return ("executive-summary.html", "Executive summary", "The findings, the figures behind them and how firm each one is.", b)


def p_projections(M):
    sq = M["status_quo"]
    b = "<p>These tables assume the current owners keep both properties, so the 2% yearly cap on assessed value keeps running. Home prices rise 3.5% a year and other costs 2.4% a year. The owner's roll figures are privacy-rounded: see <a href=\"method.html\">Method and privacy</a>.</p>"
    rows = [([str(r["year"]), money(r["a_value"]), money(r["a_assessed"]), money(r["a_tax"]), money(r["a_maintenance"]), money(r["a_water"]),
              money(r["a_electricity"]), money(r["a_insurance"])], "model", ["BOE-LTA2602", "FHFA-HPI", "SSA-TR"]) for r in sq]
    b += "<h2>Property A while the current owners keep it</h2>"
    b += table(["Year", "Market value", "Assessed value", "Property tax", "Repairs and maintenance", "Water", "Electricity", "Home insurance"], rows, cls="nums")
    b += f"<p>Electricity is the owner-reported net credit while net metering lasts and is left blank from 2040 {flag_note('F-09')}. Insurance starts from the owner's guess {flag_note('F-01')}. Maintenance is an assumption {flag_note('F-06')}.</p>"
    rows = [([str(r["year"]), money(r["b_value"]), money(r["b_assessed"]), money(r["b_tax"]), money(r["b_maintenance"]), money(r["b_water"]),
              money(r["b_electricity"]), money(r["b_insurance"]), money(r["b_rent"])], "model", ["BOE-LTA2602", "SF-TAX", "SF-RENT"]) for r in sq]
    b += "<h2>Property B while the current owners keep it</h2>"
    b += table(["Year", "Market value", "Assessed value", "Property tax", "Repairs and maintenance", "Water, three units", "Electricity", "Rental-building insurance", "Rent, two units"], rows, cls="nums")
    b += f"<p>Rent rises at 60% of inflation, the formula the Rent Board uses for covered units {flag_note('F-12')}. Insurance starts from the owner's guess {flag_note('F-02')}.</p>"
    ai = M["after_inheritance"]
    rows = [([str(r["year"]), money(r["a_value"]), money(r["taxable_live"]), money(r["tax_live"]), money(r["taxable_full"]), money(r["tax_full"]), money(r["saving"])],
             "model", ["BOE-LTA2626", "BOE-LTA2509", "BOE-P19"]) for r in ai["rows"]]
    b += f"<h2>Property A after an inheritance in {ai['year']}</h2>"
    b += table(["Year", "Market value", "Taxable value if the heir lives there", "Property tax", "Taxable value if rented or empty", "Property tax", "Yearly saving from living there"], rows, cls="nums")
    rows = [([str(r["year"]), money(r["addon"]), money(r["estate_exclusion"])], "verified" if r["year"] <= 2027 else "model",
             ["BOE-LTA2509", "IRS-IR133"] if r["year"] <= 2027 else ["BOE-LTA2509", "IRS-RP2635"]) for r in sq if r["year"] in (2026, 2027, 2030, 2035, 2040, 2045, 2050, 2055)]
    b += "<h2>Two thresholds that move every year</h2>"
    b += table(["Year", "The $1 million amount for a family home", "Federal estate exclusion per person"], rows, cls="nums")
    b += f"<p>Figures after 2027 are projections {flag_note('F-19', 'F-21')}. The official amount for a family home is $1,044,586; the table shows it rounded to $10. It is adjusted every second February by one year's change in the California House Price Index.</p>"
    return ("projections.html", "Year-by-year projections", "House value, assessed value, property tax, upkeep, utilities and insurance for each year from 2026 to 2055.", b)


def p_property_a(M):
    r = M["status_quo"][0]
    s = M["scenarios"]["2045"]
    b = table(["Item", "Figure", "Note"], [
        (["Type and place", "Single-family home, Santa Clara County", "City, postal code and address are withheld."], "owner", ["SCC-DTT"]),
        (["Market value, November 2026", "$3,100,000", "The owner's estimate, not an appraisal."], "owner", ["IRS-INHERIT"]),
        (["Assessed value, 2026", "About $550,000", "Privacy-rounded. The owner's 13-year series rises by exactly the official factor every year."], "owner", ["BOE-LTA2602"], "R-01"),
        (["Property tax, latest bill", "About $7,200", "Privacy-rounded. About 1.3% of assessed value, because fixed charges are included."], "owner", ["BOE-LTA2602"], "F-07"),
        (["Water", "$100 to $150 a month", "$1,500 a year at the midpoint."], "owner", ["IRS-T414"]),
        (["Electricity", "Credit of $10 to $20 a month", "Solar under net metering. The 20-year term ends on a date not yet known."], "owner", ["CPUC-NEM"], "F-09"),
        (["Home insurance", "—", "Owner's guess: about $1,500 a year. Not confirmed."], "unverified", ["CDI-TOOL"], "F-01"),
        (["Repairs and maintenance", "—", "No figure supplied. Model assumption: 0.5% of value, " + money(r["a_maintenance"]) + " in 2026."], "unverified", ["IRS-T414"], "F-06"),
        (["Rent it could earn", "—", "No figure supplied. Model placeholder: $6,000 a month."], "unverified", ["HUD-FMR"], "F-04"),
    ])
    b += "<h2>Yearly cost of keeping the house in 2026</h2>"
    b += table(["Cost", "2026"], [
        (["Property tax", money(r["a_tax"])], "model", ["BOE-LTA2602"], "F-07"),
        (["Repairs and maintenance", money(r["a_maintenance"])], "assumption", ["IRS-T414"], "F-06"),
        (["Water", money(r["a_water"])], "owner", ["IRS-T414"]),
        (["Electricity", money(r["a_electricity"])], "owner", ["CPUC-NEM"], "F-09"),
        (["Home insurance", money(r["a_insurance"])], "assumption", ["CDI-TOOL"], "F-01"),
        (["Total", money(r["a_tax"] + r["a_maintenance"] + r["a_water"] + r["a_electricity"] + r["a_insurance"])], "model", ["BOE-LTA2602"]),
    ], cls="nums")
    b += "<h2>What changes at inheritance</h2>"
    b += table(["Rule", "Effect on Property A"], [
        (["A death is a change in ownership, even through a trust", "The home is reassessed as of the date of death unless an exclusion applies."], "verified", ["BOE-P19", "BOE-LTA2626"]),
        (["Family home exclusion", "If it was the parent's principal residence and becomes the heir's within one year, the taxable value is the old assessed value plus any market value above that value and the adjusted $1 million."], "verified", ["BOE-LTA2626", "BOE-P19"], "F-11"),
        (["The $1 million amount", "$1,044,586 for transfers from 16 February 2025 to 15 February 2027, then adjusted every second year."], "verified", ["BOE-LTA2509"], "F-19"),
        (["If the heir later moves out", "The exclusion ends, and the market value at the date of death, raised by the yearly factor since then, is enrolled from the next 1 January."], "verified", ["BOE-LTA2626"]),
        (["Example for 2045", f"Market value {money(s['a_value'])}; taxable value {money(s['a_taxable_live'])} if the heir lives there, {money(s['a_taxable_full'])} if not."], "model", ["BOE-LTA2626", "BOE-LTA2509"]),
        (["Holding the home in a company", "A transfer to a limited liability company, even one owned only by the heir, ends the exclusion and the Homeowners' Exemption."], "verified", ["BOE-LTA2626"]),
        (["Solar", "Net metering lasts 20 years from connection. A 2025 bill that at first targeted this term was amended and has not passed."], "verified", ["CPUC-NEM", "CA-AB942"], "F-09"),
    ])
    return ("property-a.html", "Property A", "The home expected to be inherited. Figures the owner supplied, what official sources confirm and what is still blank.", b)


def p_property_b(M):
    r = M["status_quo"][0]
    s = M["scenarios"]["2045"]
    bc = s["b_common"]
    net = r["b_rent"] - r["b_tax"] - r["b_maintenance"] - r["b_water"] - r["b_electricity"] - r["b_insurance"]
    b = table(["Item", "Figure", "Note"], [
        (["Type and place", "Three-unit building, City and County of San Francisco", "Neighbourhood, postal code and address are withheld."], "owner", ["SF-TAX"]),
        (["Market value, November 2026", "$1,800,000", "The owner's estimate, not an appraisal."], "owner", ["IRS-INHERIT"]),
        (["Units", "Three; two let, one not let", "The owner reports the third unit could be a principal residence without losing rent."], "owner", ["BOE-LTA2626"], "F-12"),
        (["Rent, two units", "$7,150 a month", "$85,800 a year."], "owner", ["SF-RENT"]),
        (["Assessed value", "About $120,000", "Privacy-rounded; about 7% of market value."], "owner", ["BOE-LTA2602"], "R-01"),
        (["Property tax, latest bill", "About $2,400", "Privacy-rounded; about 2.1% of assessed value."], "owner", ["SF-TAX"], "I-01"),
        (["Property tax rate, fiscal year 2026-27", "1.18162182%", "Applied to assessed value; direct charges are added."], "verified", ["SF-TAX"]),
        (["Water, three units", "$330 to $400 a month", "$4,380 a year at the midpoint."], "owner", ["IRS-T414"]),
        (["Electricity", "$30 to $70 a month", "$600 a year at the midpoint."], "owner", ["IRS-T414"]),
        (["Rental-building insurance", "—", "Owner's guess: about $1,500 a year. Not confirmed."], "unverified", ["CDI-TOOL"], "F-02"),
        (["Repairs and maintenance", "—", "No figure supplied. Model assumption: 1.0% of value, " + money(r["b_maintenance"]) + " in 2026."], "unverified", ["IRS-T414"], "F-06"),
    ])
    b += "<h2>Yearly income and cost, today and after an inheritance in 2045</h2>"
    b += table(["Line", "2026", "2045, first year after inheritance"], [
        (["Rent, two units", money(r["b_rent"]), money(bc["rent"])], "model", ["SF-RENT"], "F-12"),
        (["Property tax", money(-r["b_tax"]), money(-bc["property_tax"])], "model", ["BOE-P19", "SF-TAX"]),
        (["Repairs and maintenance", money(-r["b_maintenance"]), money(-bc["maintenance"])], "assumption", ["IRS-T414"], "F-06"),
        (["Water and electricity", money(-(r["b_water"] + r["b_electricity"])), money(-bc["utilities"])], "owner", ["IRS-T414"]),
        (["Insurance", money(-r["b_insurance"]), money(-bc["insurance"])], "assumption", ["CDI-TOOL"], "F-02"),
        (["Surplus before income tax", money(net), money(bc["net_before_income_tax"])], "model", ["BOE-P19", "SF-TAX"]),
    ], cls="nums")
    b += "<h2>Rules that shape Property B</h2>"
    b += table(["Rule", "Effect on Property B"], [
        (["Rental property gets no inheritance exclusion", "The building is reassessed at market value as of the date of death."], "verified", ["BOE-P19"]),
        (["Each unit is judged separately", "Only a unit that was the parent's own principal residence, and becomes the heir's within one year, can keep its share of the old value."], "verified", ["BOE-LTA2626"], "F-11"),
        (["Allowed rent increase", "1.6% from 1 March 2026 to 28 February 2027, set at 60% of the regional price index."], "verified", ["SF-RENT"], "F-12"),
        (["Empty Homes Tax", "Not collected. A trial court blocked it in 2024 and the Court of Appeal upheld that on 11 September 2026. It could return if a higher court reverses."], "verified", ["SF-EHT"]),
        (["Transfer tax on a sale", "$3.75 per $500 of the whole price for $1,000,000 up to $5,000,000; $11.25 per $500 from $5,000,000."], "verified", ["SF-FEES"]),
        (["Rental income", "Taxable; depreciation, repairs and operating costs are deductible. Buildings are depreciated over 27.5 years."], "verified", ["IRS-T414", "IRS-P527"]),
    ])
    return ("property-b.html", "Property B", "The rental building kept in view. Its tax position changes sharply at inheritance whatever is done with Property A.", b)


def p_insurance(M):
    b = table(["Question", "What was found", "Note"], [
        (["Does the state publish premiums?", "Yes, through the Homeowners Insurance Comparison Tool.", "It covers homeowner, condominium, renter and earthquake policies for sample homes in sample postal codes."], "verified", ["CDI-TOOL"]),
        (["Premium for a primary-residence policy on Property A", "—", "The tool is interactive and could not be operated by this session. No figure is published here."], "unverified", ["CDI-TOOL"], "F-01"),
        (["Premium for a rental policy on Property B", "—", "The tool has no landlord or rental-building category. The regulators' national report defines its dwelling fire category as one-family and owner-occupied."], "unverified", ["CDI-TOOL", "NAIC-HO"], "F-02"),
        (["Are the tool's premiums a quote?", "No.", "They are for hypothetical homes. An exact premium needs an agent, broker or insurer."], "verified", ["CDI-TOOL"]),
        (["Wildfire surcharges", "15% to over 300%", "Applied by many insurers in higher-risk areas and not included in the tool's premiums."], "verified", ["CDI-TOOL"]),
        (["Earthquake cover", "Separate", "Earthquake premiums are not in the regulators' homeowner data."], "verified", ["NAIC-HO"]),
        (["State average homeowner premium", "—", "Seen only on unofficial sites."], "unverified", ["NAIC-HO"], "F-03"),
        (["Owner's guess, each property", "About $1,500 a year", "Not confirmed. Likely low for a three-unit rental building."], "owner", ["CDI-TOOL"], "F-01"),
        (["Figure used in the model", "$1,500 a year in 2026, rising 2.4% a year", "A placeholder. Each extra $1,000 a year lowers every keep-the-house result by $1,000 a year and does not change the ranking."], "assumption", ["CDI-TOOL", "SSA-TR"], "F-01"),
    ])
    b += """<h2>How to replace the blanks</h2>
<ol>
<li>Open the state comparison tool, choose the county and city, the type of cover, the age of the home and the coverage amount, and note the range of premiums.</li>
<li>Ask a licensed broker for three quotes for Property A as an owner-occupied home, with replacement cost matched to rebuilding cost rather than market value.</li>
<li>Ask for three landlord quotes for Property B as a three-unit building, with liability and loss-of-rent cover.</li>
<li>Ask each insurer about wildfire surcharges and price earthquake cover separately.</li>
<li>Requote when the property changes hands: a policy in a parent's or trust's name does not automatically continue for an heir, and a change from owner-occupied to rented needs a different policy.</li>
</ol>"""
    return ("insurance.html", "Insurance", "What official sources confirm about premiums for a primary residence and for a rental building, and what they do not.", b)


def p_taxes(M):
    b = "<h2>How much can pass before tax</h2>"
    b += table(["Level", "Amount allowed before tax", "Note"], [
        (["Federal, deaths in 2024", "$13,610,000", "Filing threshold for the estate tax return."], "verified", ["IRS-ESTATE"]),
        (["Federal, deaths in 2025", "$13,990,000", ""], "verified", ["IRS-ESTATE"]),
        (["Federal, deaths in 2026", "$15,000,000", "Set by Public Law 119-21 and adjusted for inflation afterwards."], "verified", ["IRS-ESTATE", "IRS-NEW", "IRS-706"]),
        (["Federal, deaths in 2027", "$15,480,000", "Published 5 November 2026."], "verified", ["IRS-IR133", "IRS-RP2635"]),
        (["Federal rate above the exclusion", "40%", "Top rate of the unified schedule, reached at $1,000,000 of taxable amount."], "verified", ["IRS-706"]),
        (["Married couples", "Up to two exclusions", "The survivor can use the first spouse's unused amount only if an estate tax return is filed for the first death."], "verified", ["IRS-ESTATE", "IRS-706"]),
        (["Gifts during life, per recipient per year", "$19,000 in 2026; $20,000 in 2027", "Larger gifts use up the lifetime exclusion. A gift carries the giver's basis, so it loses the reset at death."], "verified", ["IRS-IR133", "IRS-RP2635", "IRS-P551"]),
        (["California", "No estate or inheritance tax", "No California estate tax return for deaths on or after 1 January 2005."], "verified", ["SCO-ESTATE", "CA-RTC13301"]),
        (["City and county", "None allowed", "State law bars any political subdivision from taxing an inheritance."], "verified", ["CA-RTC13301"]),
    ])
    b += "<h2>Room left under the federal exclusion</h2><p>Both properties are counted at projected market value. Everything else the parents own, including cash, investments, retirement accounts and life insurance, must fit in the room shown.</p>"
    rows = [([str(r["year"]), money(r["exclusion"]), money(r["properties"]), money(r["headroom_one"]), money(r["headroom_two"])],
             "model", ["IRS-ESTATE", "IRS-IR133", "FHFA-HPI"], "F-21" if r["projected"] else "F-20") for r in M["estate"]]
    b += table(["Year of death", "Exclusion per person", "Both properties", "Room left with one exclusion", "Room left with two exclusions"], rows, cls="nums")
    b += "<p>Each $1,000,000 above the available exclusion costs $400,000 in federal estate tax, due nine months after the death.</p>"
    b += "<h2>Property tax rules</h2>"
    b += table(["Rule", "Detail"], [
        (["Yearly cap on assessed value", "Assessed value rises by an inflation factor of at most 2%. The factor was 2% in every year from 2022-23 to 2026-27."], "verified", ["BOE-LTA2602"]),
        (["Family home passed to a child", "Excluded up to the old assessed value plus the adjusted $1 million, if it was the parent's principal residence and becomes the child's within one year."], "verified", ["BOE-P19", "BOE-LTA2626"]),
        (["Other property passed to a child", "No exclusion. Reassessed at market value."], "verified", ["BOE-P19"]),
        (["Claims to file", "Homeowners' Exemption claim within one year; exclusion claim within three years or before a sale to a third party."], "verified", ["BOE-P19", "BOE-LTA2626"]),
        (["Homeowners' Exemption", "$7,000 off the taxable value of an owner-occupied principal residence."], "verified", ["BOE-HOX"]),
        (["Rate, Property B", "1.18162182% for fiscal year 2026-27, plus direct charges."], "verified", ["SF-TAX"]),
        (["Rate, Property A", "—"], "unverified", ["LAO-250017"], "F-07"),
    ])
    b += """<h3>Check a family-home reassessment</h3>
<form class="calc" id="p19" onsubmit="return false">
<label for="p19-mv">Market value at the date of death</label><input id="p19-mv" type="number" value="5959750" step="10">
<label for="p19-bv">Assessed value just before the death</label><input id="p19-bv" type="number" value="801250" step="10">
<label for="p19-add">The adjusted $1 million amount in force</label><input id="p19-add" type="number" value="1473490" step="10">
<label for="p19-rate">Property tax rate, percent</label><input id="p19-rate" type="number" value="1.2" step="0.01">
<output id="p19-out"></output>
</form>
<p>The calculation runs in the browser. Nothing typed here is sent anywhere.</p>"""
    b += "<h2>Income tax rules that drive the decision</h2>"
    b += table(["Rule", "Detail"], [
        (["Basis of inherited property", "Generally the fair market value at the date of death, whether or not an estate tax return is filed."], "verified", ["IRS-INHERIT", "IRS-P551"], "F-10"),
        (["Community property", "When either spouse dies, the whole of the community property generally takes the new basis, if at least half is included in the estate."], "verified", ["IRS-P551"]),
        (["Irrevocable trust outside the estate", "No new basis at death."], "verified", ["IRS-RR232"], "F-10"),
        (["Federal rate on long-term gains", "0%, 15% or 20% by income. For 2027 the 15% rate ends at $563,200 of taxable income for a single filer and $633,600 for a joint return."], "verified", ["IRS-T409", "IRS-RP2635"]),
        (["Net investment income tax", "3.8% on rent, interest, dividends and gains once income passes $200,000, or $250,000 for a joint return."], "verified", ["IRS-T559"]),
        (["California", "Gains are taxed as ordinary income. The 2025 schedule tops out at 12.3%, with a further 1% above $1,000,000."], "verified", ["FTB-CG", "FTB-RATES"]),
        (["Sale of a main home", "Up to $250,000 of gain is excluded, $500,000 on a joint return, after two years of ownership and use in the last five."], "verified", ["IRS-T701"]),
        (["Rental income", "Taxable after expenses and depreciation. A rental building is depreciated over 27.5 years; depreciation taken is taxed at up to 25% on sale."], "verified", ["IRS-T414", "IRS-P527", "IRS-T409"]),
        (["Deducting property tax", "—"], "unverified", ["IRS-OBBB"], "F-16"),
    ])
    return ("taxes.html", "Tax thresholds", "The amount that can be inherited before tax at federal, state and local level, the room left, and the rules behind the model.", b)


def p_law(M):
    b = table(["Change", "Where it stands", "Effect on the plan"], [
        (["Federal estate exclusion raised to $15,000,000 for 2026 and indexed", "In force. $15,480,000 for 2027.", "Raises the room for the cash part of the inheritance. Any later Congress can change it."], "verified", ["IRS-NEW", "IRS-IR133"]),
        (["Bills to repeal the federal estate tax (S.587 and H.R.1301)", "Introduced 13 February 2025 and referred to committee. No action since.", "None unless enacted. The headroom table already shows the tax is unlikely to apply to the properties alone."], "verified", ["CONG-S587", "CONG-HR1301"]),
        (["Initiative 25-0017 to restore the old parent-to-child property tax rules", "Failed to qualify for the ballot, recorded 18 May 2026.", "The current rules stay. Had it passed, a child could have kept the low assessed value on the home without living there, and on up to $1 million of other property."], "verified", ["SOS-FAIL", "LAO-250017"]),
        (["Next adjustment of the $1 million family-home amount", "Due for transfers from 16 February 2027; not yet published.", "Sets the exclusion for the next two years. The model raises it by 3.5% every second year."], "verified", ["BOE-LTA2509"], "F-19"),
        (["Guidance on family-home transfers, August 2026", "Issued as Letter to Assessors 2026/026.", "Confirms no exceptions to the one-year move-in rule, unit-by-unit treatment of multi-unit buildings and loss of the exclusion on a transfer to a company."], "verified", ["BOE-LTA2626"]),
        (["Proposition 3, making the higher California rates on large incomes permanent", "Unofficial result: 60.6% yes. Certification due by 11 December 2026.", "Without it those rates would have ended in 2031, before the inheritance window. With it, a large gain or large rental income in 2040 to 2050 is taxed at up to 12.3% plus 1% above $1,000,000."], "verified", ["SOS-RESULTS", "SOS-P3"], "F-18"),
        (["Proposition 42, barring new state taxes on owning personal property", "Unofficial result: 51.6% yes. Certification due by 11 December 2026.", "Lowers the risk that sale proceeds held as investments face a state wealth tax."], "verified", ["SOS-RESULTS", "SOS-P42"], "F-18"),
        (["Proposition 40, a one-time tax on certain taxpayers", "Unofficial result: 52.8% no.", "No effect."], "verified", ["SOS-RESULTS"], "F-18"),
        (["Proposition 43, limiting voters' ability to raise local revenue", "Unofficial result: 57.3% no.", "Local parcel charges on both bills can still be added by voters."], "verified", ["SOS-RESULTS"], "F-18"),
        (["AB 942 on solar customers", "Amended in July 2025 so that it no longer adds the net metering section; in a Senate committee since 29 August 2025.", "The 20-year net metering term is unchanged."], "verified", ["CA-AB942", "CPUC-NEM"]),
        (["Empty Homes Tax on vacant units in buildings of three or more units", "Blocked in 2024; the Court of Appeal upheld the block on 11 September 2026.", "The unlet third unit of Property B owes nothing now. Watch for a reversal or a replacement measure."], "verified", ["SF-EHT"]),
        (["Allowed rent increase for covered units", "1.6% from 1 March 2026.", "Rents on Property B grow more slowly than its costs, most of all after reassessment."], "verified", ["SF-RENT"], "F-12"),
        (["Assessed-value inflation factor for 2026-27", "2%, the cap.", "Assessed values keep rising 2% a year while ownership is unchanged."], "verified", ["BOE-LTA2602"]),
    ])
    return ("law-changes.html", "Law changes", "Changes decided or under discussion as of " + RETRIEVED + ", and what each does to the decision.", b)


def p_inheritance(M):
    b = table(["Step", "When", "What to do"], [
        (["1", "Now", "Confirm the trust type, that each deed is titled in the trust and which home carries the Homeowners' Exemption. Find the solar connection date."], "verified", ["CRT-SCC", "IRS-RR232"], "F-10"),
        (["2", "At the death", "The successor trustee takes over. Assets properly held in the trust pass without probate; the trustee needs the trust document and death certificates."], "verified", ["CRT-SELF", "CRT-SCC"]),
        (["3", "Within 60 days", "The trustee serves the required notification on every beneficiary and heir once the trust becomes irrevocable."], "verified", ["CA-PROB16061"]),
        (["4", "First weeks", "Get an employer identification number for the trust and written date-of-death appraisals of both properties. The appraisals set the new tax basis."], "verified", ["IRS-1041", "IRS-INHERIT"]),
        (["5", "Within 150 days", "File a change in ownership statement with the assessor in each county. Late filing after a written request brings a penalty."], "verified", ["CA-RTC480"]),
        (["6", "Within 1 year", "If keeping Property A as a home: move in and file the Homeowners' Exemption claim. A late claim gives relief only from the year it is filed."], "verified", ["BOE-P19", "BOE-LTA2626"]),
        (["7", "Within 3 years, and before any sale", "File the claim for the parent-to-child exclusion for Property A."], "verified", ["BOE-P19", "BOE-LTA2626"]),
        (["8", "Within 9 months", "If the estate exceeds the exclusion, or a spouse survives and wants the unused exclusion, file the federal estate tax return and pay any tax. A six-month filing extension is available."], "verified", ["IRS-706"]),
        (["9", "After the return", "Where an estate tax return is required, beneficiaries receive a statement of the value to use as basis."], "verified", ["IRS-706", "IRS-P551"]),
        (["10", "Each tax year", "File the trust's federal income tax return if it has any taxable income or gross income of $600 or more, and the California return where required."], "verified", ["IRS-1041", "FTB-541"], "F-17"),
        (["11", "Months after the death", "Expect supplemental property tax bills for the reassessment. Unpaid instalments carry a 10% penalty."], "verified", ["SF-TAX"]),
        (["12", "When selling Property A", "Report the sale with the date-of-death value as basis. County transfer tax is $0.55 per $500 of value."], "verified", ["IRS-INHERIT", "SCC-DTT"]),
        (["13", "If letting any unit", "Report rent and expenses each year and keep depreciation records."], "verified", ["IRS-T414"]),
        (["14", "At the end", "The trustee pays debts and distributes or continues to manage the assets as the trust directs."], "verified", ["CRT-SCC"]),
    ])
    b += '<div class="note warn"><b>Two clocks start at the date of death.</b> The one-year move-in period for the family-home exclusion, and the nine-month estate tax deadline. Neither waits for the trust to be distributed.</div>'
    return ("inheritance.html", "Trust process", "The steps after a parent's death when property is held in a living trust, in order, with the deadline for each.", b)


def p_review(M):
    b = "<p>Nothing on this page blocks the plan. Each item says why it is flagged, what would settle it and where the official answer lives.</p>"
    groups = []
    for f in FLAGS:
        if f[1] not in groups:
            groups.append(f[1])
    for g in groups:
        b += f"<h2>{esc(g)}</h2>"
        rows = []
        for fid, grp, item, why, todo, ids in FLAGS:
            if grp != g:
                continue
            status = "unverified" if grp in ("Values left blank", "Facts to confirm") else ("assumption" if grp == "Unverified assumptions" else "owner" if grp.startswith("Irregularities in the owner") else "verified")
            rows.append(([f'<span id="{fid}"><b>{fid}</b></span>', esc(item), esc(why), esc(todo)], status, ids))
        b += table(["ID", "Item", "Why it is flagged", "What to do"], rows)
    return ("review.html", "Flagged for Review", "Every value that could not be confirmed from an official source, every assumption that carries weight and every irregularity found.", b)


def p_sources(M):
    rows = []
    for sid, (pub, title, url, how) in SOURCES.items():
        status = "unverified" if how.startswith("Official starting point") else "verified"
        rows.append(([f"<code>{sid}</code>", esc(pub), f'<a href="{esc(url)}" rel="noopener">{esc(title)}</a>', esc(how), RETRIEVED], status, [sid]))
    b = table(["Code", "Publisher", "Document", "How it was checked", "Date"], rows)
    b += "<p>Only official publishers are listed: government agencies, courts, the legislature, and the national association of state insurance regulators. Commercial sites were used to find pages and never as evidence.</p>"
    return ("sources.html", "Sources", f"{len(SOURCES)} official sources, each with the way this review checked it.", b)


def p_method(M):
    i, e, t = M["inputs"], M["inputs"]["economy"], M["inputs"]["tax"]
    b = "<h2>Assumptions</h2>"
    b += table(["Assumption", "Value", "Basis"], [
        (["General inflation", pct(e["inflation"]), "The intermediate long-range price assumption of the Social Security Trustees."], "assumption", ["SSA-TR"]),
        (["Home price growth", f"{pct(e['home_appreciation'])}; tested at {pct(e['home_appreciation_low'])} and {pct(e['home_appreciation_high'])}", "The two metropolitan indexes rose 442% and 414% from 1991 to mid-2026, about 4.9% and 4.8% a year, but only 2.3% and 1.0% a year over the last five years."], "assumption", ["FHFA-HPI"]),
        (["Yearly rise in assessed value", pct(e["prop13_factor"]), "The cap, which applied in nine of the last ten years."], "assumption", ["BOE-LTA2602"]),
        (["Rent growth, Property B", "60% of inflation", "The Rent Board formula for covered units."], "assumption", ["SF-RENT"], "F-12"),
        (["Treasury return", pct(e["treasury_return"]), "The 10-year yield was 4.88% on 9 November 2026; the Trustees' long-range nominal yield is 4.8%."], "assumption", ["UST-YIELD", "SSA-TR"]),
        (["Stock index return", f"{pct(e['stock_return'])}; tested at {pct(e['stock_return_low'])} and {pct(e['stock_return_high'])}", "No official forecast exists. The federal employees' stock index fund returned 12.09% in the year to October 2026."], "assumption", ["TSP-RET"], "F-14"),
        (["Selling costs", pct(e["selling_cost"]), "County transfer tax of 0.11% plus assumed commission and closing costs."], "assumption", ["SCC-DTT"], "F-15"),
        (["Vacancy", pct(e["vacancy"]), "Allowance for empty weeks between tenants."], "assumption", ["IRS-T414"], "F-04"),
        (["Tax on rent and interest", pct(t["ordinary_rate"]), "24% federal, 3.8% net investment income tax, 9.3% California."], "assumption", ["IRS-RP2635", "IRS-T559", "FTB-RATES"], "F-13"),
        (["Tax on Treasury interest", pct(t["treasury_interest_rate"]), "As above without California tax."], "assumption", ["IRS-RP2635", "IRS-T559"], "F-13"),
        (["Tax on dividends", pct(t["dividend_rate"]), "15% federal, 3.8%, 9.3% California."], "assumption", ["IRS-T409", "FTB-RATES"], "F-13"),
        (["Tax on a large one-time gain", pct(t["terminal_gain_rate"]), "20% federal, 3.8%, 10.3% California."], "assumption", ["IRS-T409", "FTB-RATES"], "F-13"),
        (["Gain excluded on selling a main home", money(t["home_sale_exclusion"]), "Single-filer amount; $500,000 on a joint return."], "verified", ["IRS-T701"]),
    ])
    b += """<h2>How the comparison works</h2>
<ol>
<li>Values, assessed values and costs are projected year by year from 2026.</li>
<li>In the year of inheritance each option is started: live in Property A, rent it out, or sell it and invest.</li>
<li>For 20 years every option's yearly cash, after tax, is added to a savings pot that earns the after-tax Treasury rate. Shortfalls are taken from the same pot.</li>
<li>At the end the house or portfolio is valued as if sold, after selling costs and tax, and added to the pot.</li>
<li>Totals are also shown in today's dollars by removing 2.4% a year of inflation.</li>
</ol>
<p>The model leaves out mortgage debt, the heir's other income, earthquake risk, major one-off repairs, and the difference in comfort between the two homes. It treats every option as taxed on sale at the end, which understates any asset the heir would hold for life.</p>
<h2>How personal data is kept out</h2>
<ul>
<li>No names, addresses, parcel numbers, postal codes, neighbourhoods or account numbers appear, and no parcel was looked up.</li>
<li>Assessed values and tax bills are public records. A figure rounded to $10 can still be matched to one parcel, so those series are shown as rounded levels: about $550,000 and $120,000 of assessed value, about $7,200 and $2,400 of tax. Every projection is calculated from the rounded levels.</li>
<li>The effect is small. Re-running the model on the owner's exact figures changes no yearly figure by more than $100 and no 20-year result by more than $1,000, and the ranking is the same.</li>
<li>Every amount is a multiple of $10.</li>
</ul>
<h2>Reproducing the figures</h2>
<p>The model, its inputs and the page generator are in the <code>plan</code> folder of the repository. <code>python plan/model/build_site.py</code> rebuilds every page; <code>python scripts/verify.py</code> checks sources, links, rounding and the privacy rules. An owner can run the model on exact figures offline by putting them in the git-ignored <code>private</code> folder.</p>"""
    return ("method.html", "Method and privacy", "The assumptions, the way the options are compared and how personal information is kept off this site.", b)


PAGES = [p_index, p_summary, p_decision, p_projections, p_property_a, p_property_b, p_insurance,
         p_taxes, p_law, p_inheritance, p_review, p_sources, p_method]
