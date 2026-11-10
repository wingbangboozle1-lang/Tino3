#!/usr/bin/env python3
"""md_summary.py — writes EXECUTIVE-SUMMARY.md from data/model.json.

Kept in the build so the Markdown and the website can never drift apart.
"""

import os
from site_lib import M, ROOT

A = M["assumptions"]
R = M["rates"]
P = {p["key"]: p for p in M["properties"]}
SC = {s["short"]: s for s in M["scenarios_parent_cup"]}
SC_SF = {s["short"]: s for s in M["scenarios_parent_sf"]}
PL = M["prop19_lifetime"]


def m(x):
    if x is None:
        return "—"
    neg = x < 0
    return ("−$" if neg else "$") + f"{abs(int(round(x / 10.0) * 10)):,}"


def build():
    ranked = sorted(M["scenarios_parent_cup"], key=lambda s: -s["total_terminal_wealth"])
    cup, sf = P["cup"], P["sf"]
    tax_now = cup["tax_2026"] + sf["tax_2026"]
    tax_after = SC["A"]["tax_at_inheritance"]["cup"] + SC["A"]["tax_at_inheritance"]["sf"]
    combined_45 = SC["A"]["prop19"]["cup"]["fmv"] + SC["A"]["prop19"]["sf"]["fmv"]

    L = []
    a = L.append
    a("# Executive summary — Cupertino and San Francisco house inheritance")
    a("")
    a(f"**Internal working document.** Model v{M['meta']['model_version']}, built "
      f"{M['meta']['build_date']}. All currency rounded to the nearest $10 except where a "
      f"statutory amount is quoted verbatim. No personal identifying information is included. "
      f"Not legal, tax or investment advice.")
    a("")
    a("---")
    a("")
    a("## 1. What is being inherited")
    a("")
    a("| Property | ZIP | Estimated value, Nov 2026 | Assessed value | Current property tax | Basis |")
    a("|---|---|---|---|---|---|")
    a(f"| Cupertino single-family home | 95014 | {m(cup['fmv_2026'])} | {m(cup['assessed_2026'])} (2026) "
      f"| {m(cup['tax_2026'])} (2025-26) | owner estimate / tax bills |")
    a(f"| San Francisco 3-unit building (Outer Sunset) | 94122 | {m(sf['fmv_2026'])} | {m(sf['assessed_2025'])} (2025) "
      f"| {m(sf['tax_2025'])} (2025) | owner estimate / tax bills |")
    a("")
    a(f"Two of the three San Francisco units are let for {m(7150)} a month combined; the third is vacant, "
      f"which is what makes it possible to live there without displacing a tenant. A cash inheritance "
      f"accompanies the real estate.")
    a("")
    a("The brief does not say which house is the parents' principal residence. **That single fact decides "
      "which house can keep a low property-tax base.** The base case assumes Cupertino; every result is "
      "also produced with the assumption reversed.")
    a("")
    a("## 2. The law that governs the transfer")
    a("")
    a("| Question | Answer | Verified against |")
    a("|---|---|---|")
    a(f"| Is an inheritance taxable in California? | No state estate tax and no state inheritance tax. | "
      f"LAO, California's Tax System: A Primer (S06); FTB bill analysis SB 378 (S07) |")
    a(f"| Is there a federal estate tax? | Yes, above {m(15_000_000)} per person for 2026 "
      f"({m(30_000_000)} for a married couple with portability), at 40%. | IRS IR-2025-103, Rev. Proc. 2025-32 (S03) |")
    a(f"| Does the property-tax base pass to the child? | Only for the parents' principal residence, only if "
      f"the child moves in within one year, and only up to the base plus $1,044,586 for transfers from "
      f"16 February 2025 to 15 February 2027. | BOE Prop 19 guidance (S01); BOE LTA 2025/009 (S02) |")
    a(f"| Does the San Francisco rental qualify? | No. Prop 19 removed the exclusion for any property that "
      f"is not a principal residence. | BOE Prop 19 guidance (S01) |")
    a(f"| Is the gain taxed when the child sells? | No, to the extent of the step-up: basis becomes "
      f"date-of-death value. | IRS Publication 551 (S04), Publication 559 (S18) |")
    a(f"| How much advance appreciation escapes capital gains? | {m(M['stepup']['pre_inheritance_appreciation'])} "
      f"between 2026 and 2045 on these two houses, equal to about {m(M['stepup']['tax_avoided'])} of tax at a "
      f"37.1% blended rate. | model |")
    a(f"| Is Prop 19 being repealed? | No. The 2026 repeal initiative failed to qualify; the Secretary of State "
      f"recorded the failure on 18 May 2026. | CA Secretary of State memo 26138 (S12) |")
    a("")
    a("**Three consequences drive everything else:**")
    a("")
    a("1. The San Francisco rental receives no property-tax relief at all — it is reassessed to market value.")
    a(f"2. Cupertino's base is {m(cup['assessed_2026'])} against a value of {m(cup['fmv_2026'])}. The Prop 19 "
      f"allowance of roughly $1.04M is nowhere near that gap, so moving in saves money but does not restore "
      f"the parents' bill.")
    a("3. Nothing is automatic. The relief is claimed on Form BOE-19-P, within three years, and it fails if "
      "the child does not occupy the house within one year and claim the homeowners' exemption.")
    a("")
    a("## 3. What it costs after inheritance")
    a("")
    a(f"Combined property tax goes from {m(tax_now)} a year today to **{m(tax_after)} a year** once both "
      f"houses are reassessed in 2045 — a {(tax_after / tax_now):.1f}-fold increase. Running costs on top: "
      f"water, electricity, insurance and maintenance.")
    a("")
    a("Once reassessed, the two properties stop behaving alike:")
    a("")
    a("| 2045, at 4%/yr | Cupertino | San Francisco |")
    a("|---|---|---|")
    a(f"| Value | {m(SC['A']['prop19']['cup']['fmv'])} | {m(SC['A']['prop19']['sf']['fmv'])} |")
    a(f"| Property tax after reassessment | {m(M['post_reassessment_yield']['cup']['property_tax'])} "
      f"| {m(M['post_reassessment_yield']['sf']['property_tax'])} |")
    a(f"| Gross rent if let | {m(M['post_reassessment_yield']['cup']['gross_rent'])} "
      f"| {m(M['post_reassessment_yield']['sf']['gross_rent'])} |")
    a(f"| Net cash yield on value | {M['post_reassessment_yield']['cup']['net_yield_on_value'] * 100:.2f}% "
      f"| {M['post_reassessment_yield']['sf']['net_yield_on_value'] * 100:.2f}% |")
    a("")
    a("The San Francisco building returns roughly four times as much on a house worth a little over half as "
      "much. That ratio, not price appreciation, is what decides the plan.")
    a("")
    a("## 4. The six plans")
    a("")
    a("| Plan | After-tax cash flow, year 1 | Property tax, year 1 | Terminal after-tax wealth, 2065 |")
    a("|---|---|---|---|")
    for s in ranked:
        name = s["name"].split(". ", 1)[1]
        pt = s["tax_at_inheritance"].get("cup", 0) + s["tax_at_inheritance"].get("sf", 0)
        a(f"| **{s['short']}.** {name} | {m(s['first_year_cashflow'])} | {m(pt) if pt else '—'} "
          f"| **{m(s['total_terminal_wealth'])}** |")
    a("")
    a("Method: 2045–2065, identical assumptions, all annual cash flows invested at "
      f"{A['g_invest'] * 100:.0f}% nominal, terminal sale of any remaining house at 2065 with 5% selling "
      "costs, transfer tax, capital-gains tax and depreciation recapture, then the portfolio liquidated and "
      "taxed on unrealised gains.")
    a("")
    a("## 5. Recommendation")
    a("")
    a(f"**Plan F — live in the San Francisco building, sell Cupertino at inheritance, invest the proceeds.**")
    a("")
    a(f"Terminal after-tax wealth in 2065 of **{m(SC['F']['total_terminal_wealth'])}**, against "
      f"{m(SC['A']['total_terminal_wealth'])} for living in Cupertino and keeping both, and "
      f"{m(SC['D']['total_terminal_wealth'])} for selling both and renting.")
    a("")
    a("Why:")
    a("")
    a(f"- Selling Cupertino immediately after death triggers almost no capital-gains tax: the basis steps up "
      f"to {m(SC['F']['sale_at_inheritance']['cup']['price'])}, so the tax is "
      f"{m(SC['F']['sale_at_inheritance']['cup']['capital_gains_tax'])}. The frictions are 5% of selling "
      f"costs and {m(SC['F']['sale_at_inheritance']['cup']['transfer_tax'])} of Santa Clara County transfer "
      f"tax, leaving {m(SC['F']['sale_at_inheritance']['cup']['net'])} to invest.")
    a(f"- It keeps the asset that actually produces cash: {M['post_reassessment_yield']['sf']['net_yield_on_value'] * 100:.1f}% "
      f"net after reassessment, supported by two rent-controlled tenancies whose rents are real money.")
    a("- It avoids the low-yield, high-tax asset entirely. Occupying Cupertino costs "
      f"{m(SC['A']['tax_at_inheritance']['cup'])} a year in property tax on a house that produces nothing.")
    a("- Housing is still free: occupying the vacant unit costs only the rent forgone on that one unit, not "
      "market rent on a whole house.")
    a("")
    a("**Robustness.** Across nine combinations of house-price growth (3%, 4%, 5%) and portfolio return "
      "(4%, 6%, 8%), Plan F ranks first in eight and second in one — it loses only at a 4% portfolio return, "
      "where keeping and renting Cupertino edges ahead.")
    a("")
    a("**It is not a recommendation to hold cash.** Plan F leaves roughly 76% in a diversified portfolio and "
      "24% in one three-unit Bay Area building. Concentration is a real cost the model does not price.")
    a("")
    a("## 6. What would change the answer")
    a("")
    a("| Change | Effect |")
    a("|---|---|")
    a("| Portfolio returns 4% rather than 6% over 20 years | Keeping and renting Cupertino overtakes Plan F. "
      "This is the only single change in the tested range that reverses the ranking. |")
    a("| Bay Area prices grow 5% rather than 4% | The gap narrows; Plan F still leads. |")
    a(f"| The parents' principal residence is actually the San Francisco house | Results move by a few hundred "
      f"thousand dollars; Plan F still leads ({m(SC_SF['F']['total_terminal_wealth'])}). |")
    a("| California repeals the step-up in basis (proposed in 2024, not enacted) | Plan F weakens materially, "
      "because it depends on selling at a stepped-up basis. |")
    a("| You do not want to be a landlord at all | The only plan that avoids tenants entirely is D, and it "
      f"costs about {m(SC['F']['total_terminal_wealth'] - SC['D']['total_terminal_wealth'])} of terminal "
      f"wealth. |")
    a("")
    a("## 7. What to do before 2040")
    a("")
    a("1. **Establish which house is the parents' principal residence, in writing.** The homeowners' exemption "
      "record on each parcel is the cleanest evidence. Every property-tax projection here depends on it.")
    a("2. **Do not take the houses as a lifetime gift.** A gift carries over the parents' basis and forfeits "
      f"the step-up, costing roughly {m(M['stepup']['tax_avoided'])} in avoidable tax on the 2026–2045 "
      "appreciation alone.")
    a("3. **Review the trust instrument** for who takes title and whether a sub-trust holds the San Francisco "
      "building. It determines how fast the deed can be recorded, and the deed starts the assessor's clock.")
    a("4. **Get real insurance quotes for both ZIP codes.** The largest unresolved cost in the model.")
    a("5. **Confirm the actual ad valorem rate on each parcel.** Both owner-supplied tax series imply "
      "effective rates that differ from the published ones; the San Francisco difference is material.")
    a("6. **Decide the occupancy question on paper now.** The one-year move-in deadline and the BOE-19-P "
      "filing are the two that cannot be missed.")
    a("")
    a("## 8. Flagged items, in one place")
    a("")
    a("| Item | Severity | Why it matters |")
    a("|---|---|---|")
    a("| SF reported tax implies 2.13% effective rate vs 1.1827% published | Material | If the true ad "
      "valorem rate is 2.13%, every post-inheritance San Francisco tax figure is understated by roughly 45%. |")
    a("| Cupertino reported tax implies 1.309% vs 1.117% summed components | Low | About $1,060 a year at the "
      "2026 base; probably an uncaptured bond series. |")
    a("| Which house is the parents' residence is unstated | High | Moves the Prop 19 exclusion between "
      "properties; does not change the ranking. |")
    a("| Insurance estimates unverified, likely understated | High | Largest unresolved cost input. |")
    a("| Solar net-metering tariff unverified | Medium | The credit is not modelled as permanent. |")
    a("| 4% growth and 6% return are assumptions, not verified | High | Most consequential unverified inputs; "
      "stress-tested and disclosed. |")
    a("| Prop 19 allowance beyond Feb 2027 not yet published | Medium | Assumed 3.5%/yr to 2045. |")
    a("| Market rent for the vacant SF unit assumed | Low | Affects plans A and B only. |")
    a("| Statewide insurance benchmark is second-hand | Medium | The CDI data file was not opened; every "
      "insurance row is labelled unverified. |")
    a("| Future property-tax rates held constant | Medium | Every post-inheritance tax figure would rise "
      "with new bond debt. |")
    a("| Santa Clara transfer-tax rate and no Cupertino city tax | Low | $7,180 on a $6.5M sale; stated as "
      "unverified rather than asserted. |")
    a("| Pending estate/wealth-tax bills not checked | Low | No figure depends on it. |")
    a("")
    a("Full detail, with the source behind each and what would close it, is on the **Flagged for review** "
      "page of the site.")
    a("")
    a("## 9. Sources")
    a("")
    from sources import SOURCES
    a(f"{len(SOURCES)} primary sources, all official: California State Board of Equalization (Prop 19 guidance and "
      "LTA 2025/009), Internal Revenue Service (Rev. Proc. 2025-32, Publications 551 and 559, Topic 701, "
      "net investment income tax), California Legislative Analyst's Office, California Franchise Tax Board, "
      "California Legislative Information (Revenue and Taxation Code §§51 and 218, and the text of Prop 19), "
      "California Secretary of State, County of Santa Clara Controller-Treasurer, City and County of San "
      "Francisco (Controller, Assessor-Recorder, Rent Board), California Department of Insurance, and the "
      "Federal Housing Finance Agency.")
    a("")
    a("The full register, with a statement of what each source establishes, is in `data/sources.json` and on "
      "the site's Sources page. Every figure on every page carries a reference chip back to it.")
    a("")
    a("---")
    a("")
    a(f"*Rebuild with `python3 tools/model.py && python3 tools/build_site.py`. "
      f"Model inputs are in a single dictionary at the top of `tools/model.py`, each labelled as verified, "
      f"reported by the owner, or an assumption.*")

    out = os.path.join(ROOT, "EXECUTIVE-SUMMARY.md")
    with open(out, "w") as f:
        f.write("\n".join(L) + "\n")
    return out
