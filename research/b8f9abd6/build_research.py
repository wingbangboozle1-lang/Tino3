"""Build the RES-LAW / RES-PROC research module (session arena-b8f9abd6).

Deterministic, standard-library only. Writes:
  law_watch.json, inheritance_process.json, estate_threshold_projection.csv,
  estate_tax_examples.csv, law-watch.html

Privacy: this module contains NO owner-supplied figures, ZIP codes, addresses, names
or parcel data. It holds public law, official citations and clearly labelled
illustrative arithmetic on round hypothetical numbers only.

Verification convention:
  status = "verified"   -> the stated value/rule was read in the linked official page on CHECKED
  status = "unverified" -> could not be confirmed from an official page; value left blank
  Scenario/projection columns are model outputs, never presented as official values.
"""
import csv, json, html
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKED = "2026-11-10"

def r10(x):
    """Round to the nearest $10 (half away from zero) per the owner's display rule."""
    return int((abs(x) + 5) // 10 * 10) * (1 if x >= 0 else -1)

# ---------------------------------------------------------------- RES-LAW
LAW = [
 # Federal transfer tax
 dict(id="L01", level="Federal", topic="Estate tax basic exclusion (2026 deaths)",
      rule="$15,000,000 filing threshold / basic exclusion for decedents dying in 2026.",
      status="verified", status_as_of="In force",
      impact="An estate (all assets incl. both houses, cash, securities) at or below this amount owes no federal estate tax.",
      source="IRS — Estate tax (filing threshold table)",
      url="https://www.irs.gov/businesses/small-businesses-self-employed/estate-tax"),
 dict(id="L02", level="Federal", topic="Working Families Tax Cuts (P.L. 119-21) set the 2026 amount",
      rule="P.L. 119-21, signed July 4, 2025, amended IRC §2010(c)(3) to a $15,000,000 basic exclusion for 2026.",
      status="verified", status_as_of="Enacted law; no scheduled sunset stated on the IRS page",
      impact="Replaces the pre-2026 expectation that the exclusion would roughly halve. Future Congresses can still amend it.",
      source="IRS — What's new, Estate and gift tax",
      url="https://www.irs.gov/businesses/small-businesses-self-employed/whats-new-estate-and-gift-tax"),
 dict(id="L03", level="Federal", topic="Estate tax exclusion (2027 deaths) and annual gift exclusion",
      rule="$15,480,000 basic exclusion for 2027 deaths; annual gift exclusion $20,000 for 2027 (up from $19,000 in 2026). IR-2026-133, Nov. 5, 2026; Rev. Proc. 2026-35.",
      status="verified", status_as_of="Published Nov. 5, 2026",
      impact="Confirms the exclusion is inflation-indexed after 2026 (+3.2% for 2027). Basis for the 2028–2050 scenario projection.",
      source="IRS — IR-2026-133 (2027 inflation adjustments)",
      url="https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2027-taxpayers-continue-to-benefit-from-the-working-families-tax-cuts"),
 dict(id="L04", level="Federal", topic="Estate tax rate above the exclusion",
      rule="Unified rate schedule tops out at 40% on taxable amounts over $1,000,000 (Form 706 Table A). With an exclusion above $1M, each dollar over the exclusion is taxed at 40%.",
      status="verified", status_as_of="In force",
      impact="Tax = 40% x (taxable estate - available exclusion) when the estate exceeds the exclusion.",
      source="IRS — Instructions for Form 706 (07/2026), Table A",
      url="https://www.irs.gov/instructions/i706"),
 dict(id="L05", level="Federal", topic="Portability (DSUE) for married couples",
      rule="A surviving spouse can receive the deceased spouse's unused exclusion only if elected on a timely filed Form 706 (simplified late-election relief: Rev. Proc. 2022-32).",
      status="verified", status_as_of="In force",
      impact="Can roughly double the shelter for the second death (2 x $15,000,000 in 2026 terms) — but only if Form 706 is filed at the first death.",
      source="IRS — Estate tax page; Instructions for Form 706 (portability)",
      url="https://www.irs.gov/instructions/i706"),
 dict(id="L06", level="Federal", topic="Step-up in basis for inherited property",
      rule="Basis of inherited property is generally fair market value on the date of death (or alternate valuation date if elected on Form 706), whether or not Form 706 is filed.",
      status="verified", status_as_of="In force",
      impact="Selling an inherited house soon after death produces little or no capital gain; most of the decades of appreciation is never taxed as income.",
      source="IRS — Gifts & inheritances FAQ",
      url="https://www.irs.gov/faqs/interest-dividends-other-types-of-income/gifts-inheritances/gifts-inheritances"),
 dict(id="L07", level="Federal", topic="Irrevocable grantor trust caution (Rev. Rul. 2023-2)",
      rule="The §1014 basis adjustment generally does not apply to assets of an irrevocable grantor trust that are not included in the deceased grantor's gross estate.",
      status="verified", status_as_of="Published IRB 2023-16",
      impact="Have counsel confirm the trust type. A revocable living trust (included in the estate) is the usual vehicle that keeps the step-up.",
      source="IRS — Internal Revenue Bulletin 2023-16, Rev. Rul. 2023-2",
      url="https://www.irs.gov/irb/2023-16_IRB"),
 dict(id="L08", level="Federal", topic="Home-sale gain exclusion (IRC §121)",
      rule="Up to $250,000 ($500,000 joint) of gain on a main home excluded if owned and used as a residence 24 of the last 60 months.",
      status="verified", status_as_of="In force",
      impact="Relevant if an heir lives in an inherited house for 2+ years, then sells after it appreciates beyond the stepped-up basis.",
      source="IRS — Topic no. 701, Sale of your home",
      url="https://www.irs.gov/taxtopics/tc701"),
 dict(id="L09", level="Federal", topic="Long-term capital gain rates",
      rule="0% / 15% / 20% by taxable income (2025 thresholds listed on page); unrecaptured §1250 gain up to 25%; NIIT may also apply.",
      status="verified", status_as_of="In force",
      impact="Applies to gain above the stepped-up basis when a house or reinvested portfolio is sold.",
      source="IRS — Topic no. 409, Capital gains and losses",
      url="https://www.irs.gov/taxtopics/tc409"),
 dict(id="L10", level="Federal", topic="Pending: full repeal of estate tax (S.587 / H.R.1301, 119th Congress)",
      rule="Death Tax Repeal Act bills would repeal the estate and GST taxes.",
      status="verified", status_as_of="Introduced 02/13/2025; referred to committee; no further action shown",
      impact="Not law. If ever enacted, federal estate tax exposure would disappear; plan on current law.",
      source="Congress.gov — S.587 all actions",
      url="https://www.congress.gov/bill/119th-congress/senate-bill/587/all-info"),
 dict(id="L11", level="Federal", topic="Pending: House companion H.R.1301",
      rule="Death Tax Repeal Act (House).",
      status="verified", status_as_of="Introduced 02/13/2025; referred to Ways and Means; no further action shown",
      impact="Not law. Monitor only.",
      source="Congress.gov — H.R.1301 all actions",
      url="https://www.congress.gov/bill/119th-congress/house-bill/1301/all-info"),
 # State
 dict(id="L12", level="State (CA)", topic="California estate / inheritance tax",
      rule="No California estate tax return is required for decedents dying on or after January 1, 2005; inheritance tax applies only to deaths before June 8, 1982.",
      status="verified", status_as_of="In force",
      impact="No state-level death tax on the inheritance.",
      source="California State Controller — California Estate Tax",
      url="https://www.sco.ca.gov/ardtax_estate_tax.html"),
 dict(id="L13", level="State (CA)", topic="Proposition 19 parent-child exclusion (R&TC §63.2)",
      rule="Only the transferor's principal residence qualifies; it must become the child's principal residence within 1 year; homeowners' exemption must be filed within 1 year; claim within 3 years or before transfer to a third party. New taxable value = taxable value + (market value - (taxable value + $1M as adjusted)) when market value exceeds that sum.",
      status="verified", status_as_of="In force since Feb 16, 2021",
      impact="The decisive property-tax rule for the inherited home: moving in preserves part of the low base; renting or holding vacant triggers full reassessment to market value.",
      source="California Legislative Information — R&TC §63.2",
      url="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=63.2"),
 dict(id="L14", level="State (CA)", topic="Prop 19 exclusion amount (current period)",
      rule="$1,044,586 for transfers Feb 16, 2025 – Feb 15, 2027 (adjusted every other year by FHFA California HPI; up 2.15% from $1,022,600).",
      status="verified", status_as_of="Next adjustment due for transfers from Feb 16, 2027 (not yet published at check)",
      impact="Grows with California house prices, so it will be larger by 2040–2050, but the formula still taxes everything above taxable value + exclusion.",
      source="BOE — News Release NR 25-02 (LTA 2025/009)",
      url="https://www.boe.ca.gov/news/2025/nr-25-02.htm"),
 dict(id="L15", level="State (CA)", topic="Prop 13 annual inflation factor",
      rule="Base year values rise by CCPI change capped at 2%; 2026 roll factor 1.02 (CCPI +3.307%, capped).",
      status="verified", status_as_of="2026 lien date",
      impact="Assessed value of a home not reassessed grows at most 2%/yr; full 2% applied in 2017–2020 and 2022–2026 rolls.",
      source="BOE — Letter To Assessors No. 2026/002",
      url="https://www.boe.ca.gov/proptaxes/pdf/lta26002.pdf"),
 dict(id="L16", level="State (CA)", topic="Homeowners' exemption",
      rule="$7,000 reduction in taxable value for an owner-occupied principal residence; one-time claim on BOE-266; file by February 15 for full-year exemption.",
      status="verified", status_as_of="In force",
      impact="Required within 1 year to keep the Prop 19 exclusion (see L13). Worth about $7,000 x local rate per year.",
      source="BOE — Homeowners' Exemption",
      url="https://www.boe.ca.gov/proptaxes/homeowners_exemption.htm"),
 dict(id="L17", level="State (CA)", topic="Failed 2026 initiative to repeal Prop 19 inheritance rules (No. 25-0017)",
      rule="Would have restored pre-Prop 19 parent-child exclusions from Jan 1, 2027. Petition failed: signatures filed were below the number required (SOS memo #26138, May 18, 2026).",
      status="verified", status_as_of="Failed — not on Nov 3, 2026 ballot",
      impact="Prop 19 rules remain in force. Treat any future repeal attempt as upside only, not a planning assumption.",
      source="CA Secretary of State — CC/ROV Memorandum #26138",
      url="https://elections.cdn.sos.ca.gov/ccrov/2026/may/26138jh.pdf"),
 dict(id="L18", level="State (CA)", topic="LAO fiscal analysis of No. 25-0017",
      rule="LAO: measure would reverse most Prop 19 changes; revenue loss ~ $1B/yr initially rising to ~ $2B/yr.",
      status="verified", status_as_of="Oct 22, 2025 analysis",
      impact="Shows the scale of revenue at stake, a reason repeal is politically difficult.",
      source="Legislative Analyst's Office — A.G. File No. 25-0017",
      url="https://lao.ca.gov/BallotAnalysis/Initiative/2025-017"),
 dict(id="L19", level="State (CA)", topic="Initiatives now circulating",
      rule="SOS list of initiatives cleared for circulation (checked 2026-11-10) shows five measures (26-0001 to 26-0005); none concerns Prop 19 or inherited-property reassessment.",
      status="verified", status_as_of="As of check date",
      impact="No active Prop 19 change in the pipeline. Re-check before the 2028 cycle.",
      source="CA Secretary of State — Initiatives cleared for circulation",
      url="https://www.sos.ca.gov/elections/ballot-measures/initiative-and-referendum-status/initiatives-referenda-cleared-circulation"),
 dict(id="L20", level="State (CA)", topic="Nov 3, 2026 — Prop 3 (permanent high-income tax rates)",
      rule="Makes Prop 30 higher income-tax rates on high incomes permanent instead of expiring in 2031. Unofficial result: Yes 60.6% (as of Nov 9, 2026; certification by Dec 11, 2026).",
      status="verified", status_as_of="Passing (unofficial)",
      impact="CA income tax applies to profits from selling property and investments; higher top brackets continue for large sale gains and portfolio income after 2030.",
      source="CA SOS — Statewide ballot measure results; LAO analysis (Voter Guide)",
      url="https://electionresults.sos.ca.gov/returns/ballot-measures"),
 dict(id="L21", level="State (CA)", topic="Nov 3, 2026 — Prop 40 (one-time billionaire tax)",
      rule="One-time tax on certain taxpayers. Unofficial result: No 52.8%.",
      status="verified", status_as_of="Failing (unofficial)",
      impact="No direct effect on this household's decision.",
      source="CA SOS — Statewide ballot measure results",
      url="https://electionresults.sos.ca.gov/returns/ballot-measures"),
 dict(id="L22", level="State (CA)", topic="Nov 3, 2026 — Prop 42 (bars new state personal-property taxes)",
      rule="Prohibits new state taxes on ownership of financial assets or other personal property and limits retroactive taxes. Unofficial result: Yes 51.6%.",
      status="verified", status_as_of="Passing (unofficial)",
      impact="If certified, a future state wealth tax on stock/savings holdings would be barred — modestly favours the sell-and-reinvest path.",
      source="CA Voter Guide — LAO analysis of Prop 42",
      url="https://voterguide.sos.ca.gov/propositions/42/analysis.htm"),
 dict(id="L23", level="State (CA)", topic="Nov 3, 2026 — Prop 43 (2/3 vote for voter-initiated local special taxes)",
      rule="Legislative constitutional amendment. Unofficial result: No 57.3%.",
      status="verified", status_as_of="Failing (unofficial)",
      impact="Local parcel taxes can still be passed by citizen initiative at current thresholds — fixed charges on property tax bills may keep rising.",
      source="CA SOS — Statewide ballot measure results",
      url="https://electionresults.sos.ca.gov/returns/ballot-measures"),
 # Local
 dict(id="L24", level="Local (county/city)", topic="Documentary transfer tax on inheritance",
      rule="Documentary transfer tax does not apply to a deed transferring realty by reason of death, outright or in trust (R&TC §11930).",
      status="verified", status_as_of="In force",
      impact="Distributing the house from the trust to the heir triggers no county/city transfer tax; a later sale does.",
      source="California Legislative Information — R&TC §11930",
      url="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=11930"),
 dict(id="L25", level="Local (county/city)", topic="County documentary transfer tax rate on a sale",
      rule="County rate $0.55 per $500 of consideration (= $1.10 per $1,000); a city in that county may levy half that amount, credited against the county tax. Charter-city rates (e.g., San Francisco) are set locally and are not covered by this row.",
      status="verified", status_as_of="In force",
      impact="On a sale, budget the county rate at minimum; SF's own rate schedule must be checked separately (not verified here).",
      source="California Legislative Information — R&TC §11911",
      url="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=11911"),
 dict(id="L26", level="State (CA, utility)", topic="Rooftop solar NEM legacy period",
      rule="NEM 2.0 customers may stay on NEM 2.0 for 20 years from interconnection (D.14-03-041); new interconnections since Apr 15, 2023 take the Net Billing Tariff, whose export credits are usually lower than retail rates.",
      status="verified", status_as_of="In force",
      impact="A system interconnected before 2023 loses NEM terms ~20 years after interconnection — likely before a 2040–2050 inheritance. Do not assume today's ~$0 electric bill / monthly credit continues.",
      source="CPUC — Net Energy Metering and Net Billing",
      url="https://www.cpuc.ca.gov/nem/"),
]

# ---------------------------------------------------------------- RES-PROC
STEPS = [
 dict(step=1, phase="Before death (now to 2040s)", when="Now", who="Parent(s) / counsel",
      action="Confirm the house is titled in the trust and that the trust is revocable (included in the gross estate) so the date-of-death step-up applies.",
      form="Trust instrument, recorded deed", basis="IRC §1014 via IRS FAQ; Rev. Rul. 2023-2",
      url="https://www.irs.gov/irb/2023-16_IRB"),
 dict(step=2, phase="Before death", when="Ongoing", who="Parent(s)",
      action="Keep the house as the parent's principal residence with the homeowners' exemption on file — Prop 19 only covers a 'family home' eligible for the exemption through the transferor's ownership and occupation.",
      form="BOE-266 (already on file)", basis="R&TC §63.2(e)(5)",
      url="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=63.2"),
 dict(step=3, phase="Before death", when="Annually, optional", who="Parent(s)",
      action="Use annual-exclusion gifts of cash ($19,000 per recipient in 2026; $20,000 in 2027) to reduce a taxable estate. Avoid gifting the house itself: gifted property does not receive the date-of-death basis.",
      form="Form 709 if over the exclusion", basis="IR-2026-133; IRS inheritance FAQ",
      url="https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2027-taxpayers-continue-to-benefit-from-the-working-families-tax-cuts"),
 dict(step=4, phase="Day 0 – 60", when="Within 60 days of death", who="Successor trustee",
      action="Trust becomes irrevocable. Serve the statutory notification by trustee on every beneficiary and heir.",
      form="Notification by trustee", basis="Probate Code §16061.7(f)",
      url="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=PROB&sectionNum=16061.7"),
 dict(step=5, phase="Day 0 – 60", when="Promptly", who="Successor trustee",
      action="Obtain an EIN for the estate/trust (free on IRS.gov) for bank accounts and income tax filings.",
      form="Form SS-4", basis="IRS — Information for executors",
      url="https://www.irs.gov/businesses/small-businesses-self-employed/information-for-executors"),
 dict(step=6, phase="Day 0 – 150", when="As of date of death", who="Successor trustee + appraiser",
      action="Obtain a date-of-death fair-market-value appraisal of each property — it sets the heir's stepped-up basis and the Prop 19 market-value test.",
      form="Qualified appraisal", basis="IRS inheritance FAQ; R&TC §63.2(d)",
      url="https://www.irs.gov/faqs/interest-dividends-other-types-of-income/gifts-inheritances/gifts-inheritances"),
 dict(step=7, phase="Day 0 – 180", when="120 days after notice", who="Beneficiaries",
      action="Trust-contest window closes 120 days after notice is served (or 60 days after a requested copy of the trust is delivered, if later).",
      form="—", basis="Probate Code §16061.8",
      url="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=PROB&sectionNum=16061.8"),
 dict(step=8, phase="Day 0 – 150", when="Within 150 days of death", who="Trustee",
      action="File a change in ownership statement (death of real property owner) with the assessor/recorder in each county where the decedent owned real property. Late filing after the assessor's written request is penalised (greater of $100 or 10% of new-base taxes, capped).",
      form="BOE-502-D", basis="R&TC §480(b)",
      url="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=480"),
 dict(step=9, phase="Year 1", when="Within 1 year of transfer", who="Heir (child)",
      action="DECISION POINT — to keep part of the parent's low taxable value, move in and make the house the heir's principal residence, and file the homeowners' exemption, both within one year.",
      form="BOE-266", basis="R&TC §63.2(a)(1)(A)-(B); BOE Prop 19 page",
      url="https://www.boe.ca.gov/prop19/"),
 dict(step=10, phase="Year 1 – 3", when="Within 3 years, or before a sale to a third party", who="Heir",
      action="File the Prop 19 parent-child exclusion claim with the county assessor.",
      form="BOE-19-P", basis="R&TC §63.2(f)(1)(A)",
      url="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=63.2"),
 dict(step=11, phase="Month 9", when="9 months after death (extension via Form 4768)", who="Executor / trustee",
      action="File Form 706 if the gross estate plus adjusted taxable gifts exceeds the year-of-death filing threshold, or to elect portability for a surviving spouse; pay any estate tax.",
      form="Form 706; Form 4768", basis="Instructions for Form 706",
      url="https://www.irs.gov/instructions/i706"),
 dict(step=12, phase="Month 9 – 10", when="30 days after the Form 706 due date", who="Executor",
      action="If Form 706 is required, report estate-tax values to the IRS and beneficiaries (consistent basis reporting).",
      form="Form 8971 + Schedule A", basis="Instructions for Form 706",
      url="https://www.irs.gov/instructions/i706"),
 dict(step=13, phase="Distribution", when="After debts/taxes settled", who="Trustee",
      action="Record a trustee's deed distributing the house to the heir. No documentary transfer tax applies to a transfer by reason of death.",
      form="Trustee's deed", basis="R&TC §11930",
      url="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=11930"),
 dict(step=14, phase="Tax years after death", when="Annual", who="Trustee / heir",
      action="File the decedent's final Form 1040 and the trust/estate's Form 1041 for income earned during administration (e.g., rent).",
      form="Form 1040, Form 1041", basis="IRS — Information for executors (Pub. 559)",
      url="https://www.irs.gov/businesses/small-businesses-self-employed/information-for-executors"),
 dict(step=15, phase="If selling", when="Year of sale", who="Heir or trustee",
      action="Report the sale on Schedule D / Form 8949 using the stepped-up basis; gain over basis is taxable (federal rates per Topic 409; CA taxes it as income).",
      form="Schedule D, Form 8949", basis="IRS inheritance FAQ; Topic 409",
      url="https://www.irs.gov/taxtopics/tc409"),
]

# ---------------------------------------------------------------- Projections
OFFICIAL = {2026: 15_000_000, 2027: 15_480_000}
RATES = {"low_2.0pct": 0.020, "mid_2.5pct": 0.025, "high_3.2pct": 0.032}

def scenario(year, rate):
    return OFFICIAL[year] if year in OFFICIAL else OFFICIAL[2027] * (1 + rate) ** (year - 2027)

def write_projection():
    rows = []
    for y in range(2026, 2051):
        row = {"year": y,
               "official_basic_exclusion": OFFICIAL.get(y, ""),
               "official_source": "https://www.irs.gov/businesses/small-businesses-self-employed/estate-tax" if y == 2026 else
                                  ("https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2027-taxpayers-continue-to-benefit-from-the-working-families-tax-cuts" if y == 2027 else ""),
               "official_status": "verified" if y in OFFICIAL else "unverified (not yet published)"}
        for k, r in RATES.items():
            row[f"scenario_{k}"] = r10(scenario(y, r))
        row["scenario_married_portability_mid"] = r10(2 * scenario(y, RATES["mid_2.5pct"]))
        row["stress_half_exclusion_mid"] = r10(0.5 * scenario(y, RATES["mid_2.5pct"]))
        rows.append(row)
    with open(HERE / "estate_threshold_projection.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    return rows

def write_examples():
    """Illustrative only: hypothetical taxable-estate sizes, not the owner's estate."""
    rows = []
    for y in (2026, 2027, 2040, 2045, 2050):
        ex = scenario(y, RATES["mid_2.5pct"])
        for estate in (10_000_000, 15_000_000, 20_000_000, 25_000_000, 30_000_000, 40_000_000):
            single = max(0.0, estate - ex) * 0.40
            married = max(0.0, estate - 2 * ex) * 0.40
            rows.append({"year_of_death": y,
                         "exclusion_basis": "official" if y in OFFICIAL else "scenario 2.5%/yr from 2027",
                         "hypothetical_taxable_estate": estate,
                         "exclusion_single": r10(ex),
                         "headroom_single": r10(ex - estate),
                         "federal_estate_tax_single": r10(single),
                         "federal_estate_tax_married_with_portability": r10(married),
                         "california_estate_or_inheritance_tax": 0,
                         "rate_source": "https://www.irs.gov/instructions/i706",
                         "ca_source": "https://www.sco.ca.gov/ardtax_estate_tax.html"})
    with open(HERE / "estate_tax_examples.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    return rows

PROP19_EXAMPLE = {
    "label": "Hypothetical round numbers — NOT the owner's property",
    "taxable_value_before_transfer": 400_000,
    "market_value_at_transfer": 2_500_000,
    "exclusion_amount": 1_044_586,
    "rule": "R&TC §63.2(d): if market value >= taxable value + exclusion, new taxable value = taxable value + (market value - taxable value - exclusion)",
}
PROP19_EXAMPLE["new_taxable_value_if_heir_moves_in"] = r10(
    PROP19_EXAMPLE["taxable_value_before_transfer"] +
    max(0, PROP19_EXAMPLE["market_value_at_transfer"] - PROP19_EXAMPLE["taxable_value_before_transfer"] - PROP19_EXAMPLE["exclusion_amount"]))
PROP19_EXAMPLE["new_taxable_value_if_not_principal_residence"] = r10(PROP19_EXAMPLE["market_value_at_transfer"])

# ---------------------------------------------------------------- HTML
def money(v):
    return "" if v == "" else f"${v:,.0f}"

def table(headers, rows):
    h = "".join(f"<th scope='col'>{html.escape(x)}</th>" for x in headers)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<div class='scroll'><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>"

def link(url, text="source"):
    return f"<a href='{html.escape(url)}' rel='noopener noreferrer'>{html.escape(text)}</a>"

def write_html(proj, ex):
    law_rows = [[l["id"], html.escape(l["level"]), html.escape(l["topic"]), html.escape(l["rule"]),
                 html.escape(l["status_as_of"]), html.escape(l["impact"]),
                 f"<span class='{l['status']}'>{l['status']}</span>", link(l["url"], l["source"])] for l in LAW]
    step_rows = [[str(s["step"]), html.escape(s["phase"]), html.escape(s["when"]), html.escape(s["who"]),
                  html.escape(s["action"]), html.escape(s["form"]), html.escape(s["basis"]), link(s["url"])] for s in STEPS]
    proj_rows = [[str(p["year"]), money(p["official_basic_exclusion"]) or "<em>blank — not yet published</em>",
                  money(p["scenario_low_2.0pct"]), money(p["scenario_mid_2.5pct"]), money(p["scenario_high_3.2pct"]),
                  money(p["scenario_married_portability_mid"]), money(p["stress_half_exclusion_mid"]),
                  link(p["official_source"]) if p["official_source"] else link("https://www.irs.gov/instructions/i706", "method: Form 706")]
                 for p in proj if p["year"] in (2026, 2027, 2030, 2035, 2040, 2045, 2050)]
    ex_rows = [[str(e["year_of_death"]), html.escape(e["exclusion_basis"]), money(e["hypothetical_taxable_estate"]),
                money(e["exclusion_single"]), money(e["headroom_single"]), money(e["federal_estate_tax_single"]),
                money(e["federal_estate_tax_married_with_portability"]), "$0", link(e["rate_source"], "Form 706 Table A")]
               for e in ex if e["year_of_death"] in (2026, 2045)]
    p = PROP19_EXAMPLE
    p19 = [["Taxable value before transfer (hypothetical)", money(p["taxable_value_before_transfer"])],
           ["Market value at transfer (hypothetical)", money(p["market_value_at_transfer"])],
           ["Exclusion amount (Feb 2025 – Feb 2027, official)", money(p["exclusion_amount"])],
           ["New taxable value if heir moves in within 1 year", money(p["new_taxable_value_if_heir_moves_in"])],
           ["New taxable value if not heir's principal residence", money(p["new_taxable_value_if_not_principal_residence"])]]
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer"><title>Law watch &amp; inheritance process — research module</title>
<style>
body{{font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1f2937;background:#f8fafc}}
header,main{{max-width:1200px;margin:auto;padding:16px}} header{{border-bottom:1px solid #e5e7eb}}
h1{{font-size:1.5rem;margin:.2rem 0}} h2{{margin-top:2rem;font-size:1.2rem}}
.scroll{{overflow-x:auto;background:#fff;border:1px solid #e5e7eb;border-radius:8px}}
table{{border-collapse:collapse;width:100%;font-size:.88rem}} th,td{{padding:6px 8px;border-bottom:1px solid #f1f5f9;text-align:left;vertical-align:top}}
th{{background:#f1f5f9;position:sticky;top:0}} .verified{{color:#166534;font-weight:600}} .unverified{{color:#b91c1c;font-weight:600}}
.note{{background:#fff7ed;border:1px solid #fed7aa;padding:10px;border-radius:8px}}
</style></head><body>
<header><p><a href="../../index.html">← Dashboard</a></p>
<h1>Law watch &amp; step-by-step trust inheritance process</h1>
<p>Research module RES-LAW / RES-PROC · session arena-b8f9abd6 · checked {CHECKED}. Contains public law only — no owner figures, addresses, ZIP codes or names. Dollar outputs rounded to the nearest $10; statutory amounts shown exactly as published.</p></header>
<main>
<p class="note">Status key: <span class="verified">verified</span> = rule read on the linked official page on {CHECKED}. Scenario and stress columns are projections, not official values. Not legal or tax advice.</p>
<h2>1. Current law and pending changes (federal, state, local)</h2>
{table(["ID","Level","Topic","Rule","Status","Why it matters","Check","Official source"], law_rows)}
<h2>2. Federal estate-tax exclusion, 2026–2050</h2>
<p>Official values exist only for 2026 and 2027. Later years are blank in the official column and projected at 2.0%, 2.5% and 3.2%/yr (3.2% = the official 2026→2027 step). Stress = Congress halves the exclusion (hypothetical).</p>
{table(["Year","Official exclusion","Scenario 2.0%","Scenario 2.5%","Scenario 3.2%","Married + portability (2.5%)","Stress: half (2.5%)","Source"], proj_rows)}
<h2>3. How much estate before tax applies — illustrative estate sizes</h2>
<p>Hypothetical taxable estates (not the owner's). Tax = 40% × amount over the exclusion. California levies $0 estate or inheritance tax. Full 2026–2050 grid in <code>estate_tax_examples.csv</code>.</p>
{table(["Year","Exclusion basis","Taxable estate","Exclusion (single)","Headroom (+) / excess (−)","Federal tax (single)","Federal tax (married, portability)","CA tax","Source"], ex_rows)}
<h2>4. Prop 19 formula — worked example on round hypothetical numbers</h2>
{table(["Item","Amount"], p19)}
<p>Source: {link("https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=63.2", "R&TC §63.2(d)")}, {link("https://www.boe.ca.gov/news/2025/nr-25-02.htm", "BOE NR 25-02")}.</p>
<h2>5. Step-by-step: inheriting a California house through a trust</h2>
{table(["#","Phase","Deadline","Who","Action","Form","Legal basis","Official source"], step_rows)}
</main></body></html>
"""
    (HERE / "law-watch.html").write_text(doc)

def main():
    (HERE / "law_watch.json").write_text(json.dumps({"checked": CHECKED, "session": "arena-b8f9abd6", "rows": LAW}, indent=1) + "\n")
    (HERE / "inheritance_process.json").write_text(json.dumps({"checked": CHECKED, "session": "arena-b8f9abd6", "steps": STEPS, "prop19_example": PROP19_EXAMPLE}, indent=1) + "\n")
    proj = write_projection(); ex = write_examples(); write_html(proj, ex)
    print(f"built: {len(LAW)} law rows, {len(STEPS)} steps, {len(proj)} projection years, {len(ex)} example rows")

if __name__ == "__main__":
    main()
