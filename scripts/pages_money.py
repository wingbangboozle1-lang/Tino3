"""Property tax, running costs, taxes and estate, projections."""
from webbuild import exact, DATA, money, pct, table, section, callout, links, link, esc

O = DATA["owner"]
A = DATA["assumptions"]
V = DATA["values"]
D45 = DATA["decisions"]["2045"]
D40 = DATA["decisions"]["2040"]
D50 = DATA["decisions"]["2050"]
REC = DATA["reconcile"]

PAGES = []


def ymap(rows):
    return {r["year"]: r for r in rows}


PA, PB = ymap(DATA["proj_a"]), ymap(DATA["proj_b"])
CA, CB = ymap(DATA["costs_a"]), ymap(DATA["costs_b"])
SAMPLE = [2026, 2030, 2035, 2040, 2045, 2050, 2055]

# =====================================================================
# PROPERTY TAX
# =====================================================================
build_table = table(
    ["Component of the bill", "How it is set", "Property A", "Property B", "Source"],
    [
        ["General levy", "1% of assessed value, constitutionally fixed", "1.000%", "1.000%", ["RTC-51", "SCC-ASSESSOR"]],
        ["Voter-approved debt", "Bonds passed by local voters, recalculated each year", "About 0.149%", "About 0.182%", ["SCC-ASSESSOR", "SF-TTC"]],
        ["Ad valorem total", "General levy plus voter debt", "1.1488%", "1.18162182%", ["SCC-ASSESSOR", "SF-TTC"]],
        ["Parcel taxes and direct charges", "Fixed dollar amounts, separately authorised", "About " + money(DATA['a_flat']) + "/yr", "About " + money(DATA['b_flat']) + "/yr", ["SF-PARCEL"]],
        ["Annual increase in assessed value", "Lesser of 2% or the change in the California CPI", "2.00%", "2.00%", ["RTC-51"]],
        ["Homeowners' exemption", "Owner-occupied principal residence only", money(V['scc_ho_exempt']) + " of assessed value", "&mdash;", ["SCC-ASSESSOR"]],
        ["When it resets", "Change in ownership, including a death transfer", "At death", "At death", ["SCC-ASSESSOR", "RTC-480"]],
    ],
    note="Parcel charges are carried as a single flat figure derived from the owner's bills; for Property B "
         "the five named parcel taxes sum to " + exact(V['sf_parcel_2025']) + " and roughly $260 of the residual is "
         "unexplained (F-04).")

proj_a_t = table(["Year", "Market value (3.0%)", "Assessed value", "Flat charges", "Property tax", "Effective rate", "Source"],
                 [[str(y), money(PA[y]['market']), money(PA[y]['assessed']), money(PA[y]['flat_charge']),
                   money(PA[y]['tax']), pct(PA[y]['effective_rate']), ["RTC-51", "SCC-ASSESSOR"]] for y in SAMPLE],
                 note="Pre-inheritance path: ownership unchanged, so the 2% cap keeps applying. Market value is "
                      "not the assessed value and never has been.")
proj_b_t = table(["Year", "Market value (3.0%)", "Assessed value", "Flat charges", "Property tax", "Effective rate", "Source"],
                 [[str(y), money(PB[y]['market']), money(PB[y]['assessed']), money(PB[y]['flat_charge']),
                   money(PB[y]['tax']), pct(PB[y]['effective_rate']), ["RTC-51", "SF-TTC"]] for y in SAMPLE],
                 note="San Francisco flat charges inflate; the ad valorem part is pinned to the 2% cap for as long as "
                      "ownership does not change.")

p19 = table(
    ["Question", "Answer", "Source"],
    [
        ["Who can use the parent-child exclusion", "Only for a <b>principal residence</b> transferred from a parent to a child (or grandparent to grandchild where the parents are deceased), and the child must also use it as a principal residence.", ["BOE-P19"]],
        ["How much value is protected", "The transferor's taxable value plus an adjusted $1,000,000. For transfers from 16 Feb 2025 to 15 Feb 2027 that adjusted amount is " + exact(V['prop19_cap_2025']) + ".", ["BOE-CAP"]],
        ["What happens above the cap", "The excess is added to the taxable value. New taxable value = market value &minus; " + exact(V['prop19_cap_2025']) + " (in the current adjustment period).", ["BOE-P19"]],
        ["What about a second home or a rental", "The exclusion for other real property was <b>eliminated</b> by Prop 19. A rented house is fully reassessed to market value at death.", ["BOE-P19"]],
        ["Deadlines", "Homeowners' or disabled veterans' exemption within <b>1 year</b>; the exclusion claim within <b>3 years</b> or before a transfer to a third party.", ["BOE-P19"]],
        ["Change in ownership statement", "The trustee must file it within <b>150 days</b> after the date of death. Penalty for not filing on request is the greater of $100 or 10% of the new tax, capped at $5,000.", ["RTC-480"]],
        ["When the reassessment takes effect", "As of the date of death, not the date the property is distributed to you.", ["SCC-ASSESSOR"]],
    ],
    note="The $1,044,586 figure is the <em>current</em> adjustment period. The BOE re-indexes it every two years; "
         "the amount that will apply in 2040-2050 is not published and is modelled as inflating at 3.0% (F-02).")

p19_math = table(
    ["Scenario", "Market value at inheritance", "Taxable value after reassessment", "Property tax, first year", "Source"],
    [
        ["Property A, full reassessment (base case)", money(D45['market_T']), money(D45['market_T']), money(D45['market_T'] * V['scc_advalorem'] + DATA['a_flat'] * 1.03 ** 19), ["SCC-ASSESSOR", "RTC-51"]],
        ["Property A, if a Prop 19 exclusion applied", money(D45['market_T']), money(D45['rows'][3]['base_T']), money(D45['rows'][3]['base_T'] * V['scc_advalorem'] + DATA['a_flat'] * 1.03 ** 19), ["BOE-CAP", "BOE-P19"]],
        ["Property B, full reassessment (if you do not occupy)", money(O['b_value_2026']), money(O['b_value_2026']), money(O['b_value_2026'] * V['sf_advalorem'] + DATA['b_flat']), ["SF-TTC", "RTC-51"]],
        ["Property B, exclusion claimed and you occupy", money(O['b_value_2026']), money(O['b_value_2026'] - V['prop19_cap_2025']), money((O['b_value_2026'] - V['prop19_cap_2025']) * V['sf_advalorem'] + DATA['b_flat']), ["BOE-CAP", "BOE-P19"]],
    ],
    note="Illustrative first-year bills at today's rates, before the Homeowners' Exemption. The exclusion is "
         "worth far more on Property B because its taxable value is so far below market.")

PAGES.append(("property-tax.html", "Property tax", f"""
<h1>Property tax</h1>
<p class="lede">This is the recurring cost that decides the case. It is set by two numbers nobody controls
&mdash; the assessed value and the county's rate &mdash; and by one event you can plan for: the reassessment at death.</p>

{section("How the bill is built", build_table, sub="Both counties, component by component.")}

{section("Property A: assessed value and tax, if nothing changes", proj_a_t,
         sub="The pre-inheritance path. Nothing here is a forecast of the market; the assessed value follows the 2% cap.")}

{section("Property B: assessed value and tax, if nothing changes", proj_b_t)}

{callout("bad", "What happens to Property A at death", f'''<p>Because a rented or non-occupied house does not
qualify for the Prop 19 parent-child exclusion, the assessor resets Property A's taxable value to its market
value on the date of death. At a 2045 inheritance that is a jump from about <b>{money(PA[2045]['assessed'])}</b> to about
<b>{money(D45['market_T'])}</b>, and the annual bill moves from about <b>{money(PA[2045]['tax'])}</b> to
<b>{money(D45['market_T'] * V['scc_advalorem'] + DATA['a_flat'] * 1.03 ** 19)}</b>. That difference &mdash;
roughly {money(D45['market_T'] * V['scc_advalorem'] + DATA['a_flat'] * 1.03 ** 19 - PA[2045]['tax'])} a year &mdash; is the price of
keeping the house instead of selling it.</p>''')}

{section("Proposition 19, precisely", p19,
         sub="The exclusion is narrow, capped, and deadline-driven. Most inherited rentals get nothing.")}

{section("The exclusion, priced", p19_math,
         sub="Same rules, four fact patterns. The difference is entirely about occupancy and which house was the home.")}

{section("Other mechanics to expect", table(
    ["Mechanic", "What it means for you", "Source"],
    [
        ["Supplemental assessment", "A separate bill for the difference between the old and new taxable value, prorated to the months left in the fiscal year. It is not usually escrowed or paid at closing.", ["SCC-ASSESSOR", "SF-TTC"]],
        ["Escape assessment", "If the reassessment is late, the county can bill prior years. An installment plan over four years exists in San Francisco.", ["SF-TTC"]],
        ["Appeal window", "Santa Clara County: informal review 1 July to 1 August; formal appeal 2 July to 15 September. A supplemental or escape assessment has 60 days.", ["SCC-ASSESSOR"]],
        ["Decline in value", "If the market falls below the factored base, the assessor must reduce the value temporarily; the base still grows 2% a year underneath.", ["SCC-ASSESSOR"]],
        ["Homeowners' Exemption", money(V['scc_ho_exempt']) + " of assessed value, worth about $70 to $80 a year, for an owner-occupied principal residence. Recording a deed or a trust transfer terminates it.", ["SCC-ASSESSOR"]],
    ],
    note="Budget the supplemental bill in the first year after death; it is the most commonly missed cash call."))}
""", "property-tax.html", "Proposition 13 and 19 mechanics, assessed values and property tax projections."))

# =====================================================================
# OPERATING COSTS
# =====================================================================
a_cost = table(["Year", "Insurance", "Water", "Electricity (net)", "Repairs", "Total", "Source"],
               [[str(y), money(CA[y]['insurance']), money(CA[y]['water']),
                 ("&minus;" if CA[y]['electricity'] < 0 else "") + money(abs(CA[y]['electricity'])),
                 money(CA[y]['maintenance']), "<b>" + money(CA[y]['total']) + "</b>",
                 ["CDI-SIS", "SFPUC", "CPUC-NEM", "COMPUTED"]] for y in SAMPLE],
               note="Excludes property tax. Electricity is a net credit because of the solar array; that is the "
                    "owner's observation and it is tariff-dependent (F-05).")
b_cost = table(["Year", "Insurance", "Water", "Electricity", "Repairs", "Total", "Source"],
               [[str(y), money(CB[y]['insurance']), money(CB[y]['water']), money(CB[y]['electricity']),
                 money(CB[y]['maintenance']), "<b>" + money(CB[y]['total']) + "</b>",
                 ["CDI-SIS", "SFPUC", "BLS-CPI", "COMPUTED"]] for y in SAMPLE],
               note="Water covers all three units. Repairs are assumed at 1.00% of value a year on an older "
                    "three-unit building, which is higher than the single-family assumption for Property A.")

sf = table(["Year", "Gross rent", "Vacancy 5%", "Management 8%", "Property tax", "Insurance", "Water", "Electricity", "Repairs", "Net before income tax", "Source"],
           [[str(y), money(r['gross']), money(r['vacancy']), money(r['management']), money(r['property_tax']),
             money(r['insurance']), money(r['water']), money(r['electricity']), money(r['maintenance']),
             "<b>" + money(r['net']) + "</b>", ["SF-RENT", "SF-TTC", "SFPUC", "COMPUTED"]]
            for y, r in [(r['year'], r) for r in DATA['sf_pl']] if y in SAMPLE],
           note="Rent grows at the 1.6% Rent Ordinance cap; vacancy and management are assumptions; income tax on "
                "the net is not deducted here (it is in the decision analysis).")

PAGES.append(("operating-costs.html", "Running costs", f"""
<h1>Running costs</h1>
<p class="lede">Insurance, water, power and repairs, projected to 2055. Together they are smaller than the
property tax on both houses &mdash; but two of them are volatile for reasons worth understanding.</p>

<div class="cards">
  <div class="card"><div class="k">Property A, 2026</div><div class="v">{money(DATA['costs_a'][0]['total'])}</div>
    <p>All running costs for the year, before property tax of {money(DATA['proj_a'][0]['tax'])}</p></div>
  <div class="card"><div class="k">Property B, 2026</div><div class="v">{money(DATA['costs_b'][0]['total'])}</div>
    <p>Three units, all utilities, before property tax of {money(DATA['proj_b'][0]['tax'])}</p></div>
  <div class="card"><div class="k">Property B net rent, 2026</div><div class="v win">{money(DATA['sf_pl'][0]['net'])}</div>
    <p>After vacancy, management, tax and running costs; before income tax</p></div>
</div>

{section("Property A running costs", a_cost,
         sub="Water is escalated from the SFPUC's adopted water steps; electricity is a net credit that is modelled as shrinking in value.")}

{section("Property B running costs", b_cost, sub="Older three-unit building, higher repair load.")}

{section("Property B income and expense", sf,
         sub="The rental you already own is the benchmark the Cupertino decision has to beat.")}

{section("Insurance: what is actually known", table(
    ["Item", "Figure", "Status", "Source"],
    [
        ["California average homeowner premium (NAIC data reported by CDI)", exact(V['cdi_avg_premium']) + " a year", '<span class="tag ver">VERIFIED</span> statewide average', ["CDI-SIS"]],
        ["U.S. average for comparison", "$1,512 a year", '<span class="tag ver">VERIFIED</span>', ["CDI-SIS"]],
        ["Recent rate filings, insurers covering about a third of homes", "About 6.9%", '<span class="tag ver">VERIFIED</span>', ["CDI-2026"]],
        ["FAIR Plan residential policies (market stress indicator)", "677,449", '<span class="tag ver">VERIFIED</span>', ["CDI-SIS"]],
        ["Owner estimate, Property A", money(O['a_insurance_year']) + " a year", '<span class="tag unv">UNVERIFIED</span> estimate', ["OWNER"]],
        ["Owner estimate, Property B (landlord policy, 3 units)", money(O['b_insurance_year']) + " a year", '<span class="tag unv">UNVERIFIED</span> estimate', ["OWNER"]],
        ["Actual quotes for either address", '<span class="tag gap">BLANK</span>', "Not obtainable without an address and a broker; left blank by rule", ["CDI-SIS"]],
        ["Escalation used in the model", "6.0% a year", '<span class="tag asm">ASSUMPTION</span>', ["CDI-2026"]],
    ],
    note="A statewide average is not a quote. A house with a seven-figure replacement cost will not insure for "
         "the average premium, and a three-unit rental needs a landlord form, not a homeowners form. Both "
         "figures are stress-tested in the decision analysis."))}

{section("Water", f'''
<p>San Francisco water rates rose 7.0% on 1 July 2026 and are scheduled to rise another 7.0% on 1 July 2027;
sewer rates rose 15.0% and are scheduled to rise 14.5%. The SFPUC puts the average single-family combined
water-and-sewer bill at <b>$189 a month</b> in fiscal 2027 and <b>$212</b> in fiscal 2028 {link('SFPUC')}.</p>
<p>Property B's owner-supplied range of $330 to $400 a month for three units is consistent with three
households sharing a bill of that order. Property A's $100 to $150 a month is plausible for a single
house with irrigation, but Cupertino is not an SFPUC customer, so that range is carried as supplied and
escalated at 6.0% &mdash; between the water and sewer steps (F-08).</p>
''')}

{section("Electricity and the solar credit", f'''
<p>Property A generates a small net credit today. The confidence of that credit depends on which net-metering
tariff the array is on. The CPUC has closed the original net energy metering tariffs to new enrolments:
systems applying after 15 April 2023 take the net billing tariff under decision D.22-12-056, which pays for
exported power at a value-of-generation rate rather than the retail rate {link('CPUC-NEM')}.</p>
<p>Two consequences the projection does not capture. First, a legacy net-metering term runs for a fixed
period from interconnection, so a system installed in the 2010s or 2020s may reach the end of its term
around the inheritance window &mdash; at which point the credit becomes an export payment and the annual
electricity cost probably turns positive. Second, the CPUC's tariffs are not fixed for 30 years; they are
relitigated. The model keeps the owner's net credit and inflates it, which is the optimistic case
<span class="tag asm">ASSUMPTION</span>. The solar system's tariff vintage and term end date are item F-05.</p>
''')}

{section("Repairs and maintenance", f'''
<p>Both figures are assumptions proportional to market value: 0.50% a year for the single-family house and
1.00% for the older three-unit building, which matches the owner's own observation that the Cupertino house
needs less work. On today's values that is {money(O['a_value_2026'] * A['a_maint_pct'])} and
{money(O['b_value_2026'] * A['b_maint_pct'])} a year. A roof, a sewer lateral or a foundation repair arrives as a
lump, not as a percentage; treat these as a sinking fund and hold a reserve.</p>
''')}
""", "operating-costs.html", "Insurance, water, electricity, repairs and the San Francisco rent roll."))

# =====================================================================
# TAXES AND ESTATE
# =====================================================================
estate_t = table(["Year", "Federal exclusion (indexed from 2027)", "Combined market value of both houses", "Headroom before the houses alone use it up", "Source"],
                 [[str(e['year']), money(e['exemption']), money(e['combined_property']), money(e['headroom']), ["IRS-2027", "COMPUTED"]]
                  for e in DATA['estate'] if e['year'] in (2026, 2027, 2030, 2035, 2040, 2045, 2050, 2055)],
                 note="Exclusion after 2027 is modelled at the CPI assumption, because the statute indexes it. The cash "
                      "and any retirement accounts in the estate are NOT included &mdash; that figure is blank (F-01).")

sale_calc = table(
    ["Line", "Amount", "Rule", "Source"],
    [
        ["Market value at death (2045, base case)", money(D45['market_T']), "3.0% appreciation assumption", ["FHFA-HPI", "COMPUTED"]],
        ["Your basis", money(D45['market_T']), "Fair market value on the date of death", ["IRS-BASIS"]],
        ["Selling costs at 6.0%", "&minus;" + money(D45['market_T'] * A['selling_cost']), "Assumption: commission, escrow, transfer tax, title", ["COMPUTED"]],
        ["Net proceeds", money(D45['market_T'] * (1 - A['selling_cost'])), "Value less costs", "COMPUTED"],
        ["Taxable capital gain", "About $0", "Sale at basis: no gain, so no 20% rate and no 3.8% NIIT", ["IRS-T409", "IRS-BASIS"]],
        ["California income tax on the gain", "About $0", "No gain to tax", ["FTB-RATES"]],
        ["Property tax saved by selling", money(D45['market_T'] * V['scc_advalorem'] + DATA['a_flat'] * 1.03 ** 19) + " a year", "The reassessed bill you never pay", ["RTC-51"]],
        ["Supplemental assessment still owed", money(D45['market_T'] * V['scc_advalorem'] * 0.5), "Roughly half a year at the new value, prorated to the date of death", ["SCC-ASSESSOR"]],
    ],
    note="This is why an early decision matters: the same house sold after ten years of letting has a large gain, "
         "part of it taxed at the 25% recapture rate.")

PAGES.append(("taxes-estate.html", "Taxes & estate", f"""
<h1>Taxes &amp; estate</h1>
<p class="lede">Three governments, three different questions. California asks nothing when you inherit.
Washington asks whether the <em>estate</em> is large enough to file. Your own income tax starts only when the
asset earns or is sold.</p>

{section("The three levels, in plain terms", table(
    ["Level", "Question it asks", "Answer for this estate", "Source"],
    [
        ["California", "Does the state tax an inheritance, an estate, or a transfer by reason of death?", "<b>No.</b> Revenue and Taxation Code 13301 forbids it, for the state and for every local government, at any size.", ["RTC-13301"]],
        ["Federal (transfer)", "Is the gross estate, plus lifetime taxable gifts, above the exclusion?", money(V['fed_excl_2026']) + " for 2026 and " + money(V['fed_excl_2027']) + " for 2027, indexed after. The two houses alone are far below it.", ["IRS-ESTATE", "IRS-2027"]],
        ["Federal (income)", "Did you realise a gain, or receive income?", "Only on sale above the stepped-up basis, on rent, and on recapture of depreciation.", ["IRS-BASIS", "IRS-T409"]],
        ["Local", "What is the assessed value now?", "Resets to market value at death; then the 2% cap resumes.", ["RTC-51", "SCC-ASSESSOR"]],
        ["Retirement accounts", "Were pre-tax dollars inherited?", "Potentially the largest single tax item in the estate and outside the scope of this model. <span class='tag gap'>BLANK &mdash; confirm</span>", ["IRS-ESTATE"]],
    ]))}

{callout("warn", "The inheritance amount you mentioned", '''<p>There is no California threshold to cross: no
state inheritance or estate tax exists, so no amount of inherited money triggers a state penalty. The only
threshold that matters is the federal one, and it applies to the <em>whole estate before it is divided</em>,
not to what any one person receives. The two houses are worth about ''' + money(O['a_value_2026'] + O['b_value_2026']) + ''' today,
which leaves ''' + money(V['fed_excl_2026'] - O['a_value_2026'] - O['b_value_2026']) + ''' of headroom in 2026. Cash,
brokerage and retirement accounts have to be added to that before the question is answered &mdash; and that
figure is not in this project (F-01).</p>''')}

{section("Estate headroom, projected", estate_t,
         sub="If the exclusion keeps being indexed and the houses keep appreciating, the gap widens over time.")}

{section("If you sell in 2045: the arithmetic", sale_calc,
         sub="A prompt sale is the cheapest exit in the tax code, and it is only available early.")}

{section("Rules that decide the size of the bill", table(
    ["Rule", "What it does", "Where it bites here", "Source"],
    [
        ["Step-up in basis", "Your basis becomes fair market value on the date of death, so pre-death appreciation is never taxed.", "Makes an early sale nearly tax-free.", ["IRS-BASIS"]],
        ["Long-term treatment", "Inherited property is treated as long-term regardless of how briefly you held it.", "No short-term ordinary rates.", ["IRS-BASIS", "IRS-T409"]],
        ["Capital gains rates", "0%, 15% or 20% by income, plus 3.8% net investment income tax above the thresholds.", "Applies to growth after the death.", ["IRS-T409"]],
        ["Unrecaptured section 1250", "Depreciation taken on a rental is recaptured at a maximum 25%.", "Every year of letting converts part of the gain.", ["IRS-T409", "IRS-P527"]],
        ["Depreciation", "The building (not the land) is written off over 27.5 years straight-line.", "Creates the deduction now and the recapture later.", ["IRS-P527"]],
        ["Section 121 exclusion", money(V['sec121_single']) + " single, " + money(V['sec121_joint']) + " joint, if you owned and lived in it 2 of the last 5 years.", "Only helps the live-in path.", ["IRS-T701"]],
        ["California treatment of gain", "No preferential rate: gains are ordinary income, 1% to 12.3%, plus 1% above $1,000,000.", "Makes California gains expensive if the house is held and then sold.", ["FTB-RATES"]],
    ]))}

{section("What this model does not tax", f'''
<p>Four omissions are deliberate, because including them would require facts that are not available:
passive-activity loss limits on rental real estate; state and federal alternative minimum taxes; the
interaction of a large one-off gain with the rest of your income in that year; and any estate or income tax
on retirement accounts. Each of these can move a year's bill materially. They are listed on the
<a href="flagged-for-review.html">flagged</a> page rather than quietly assumed away.</p>
''')}
""", "taxes-estate.html", "Federal, California and local tax treatment of the inheritance and the properties."))

# =====================================================================
# PROJECTIONS
# =====================================================================
proj_full_a = table(["Year", "Market value", "Assessed value", "Property tax", "Insurance", "Water", "Electricity", "Repairs", "Total carrying cost", "Source"],
                    [[str(y), money(PA[y]['market']), money(PA[y]['assessed']), money(PA[y]['tax']),
                      money(CA[y]['insurance']), money(CA[y]['water']),
                      ("&minus;" if CA[y]['electricity'] < 0 else "") + money(abs(CA[y]['electricity'])),
                      money(CA[y]['maintenance']),
                      "<b>" + money(PA[y]['tax'] + CA[y]['total']) + "</b>",
                      ["RTC-51", "SCC-ASSESSOR", "CDI-SIS", "SFPUC", "COMPUTED"]] for y in range(2026, 2056)],
                    note="All thirty years. Pre-inheritance basis: ownership unchanged, 2% cap on assessed value, 3.0% "
                         "appreciation on market value.")
proj_full_b = table(["Year", "Market value", "Assessed value", "Property tax", "Running costs", "Total carrying cost", "Source"],
                    [[str(y), money(PB[y]['market']), money(PB[y]['assessed']), money(PB[y]['tax']),
                      money(CB[y]['total']), "<b>" + money(PB[y]['tax'] + CB[y]['total']) + "</b>",
                      ["RTC-51", "SF-TTC", "COMPUTED"]] for y in range(2026, 2056)],
                    note="Property B is assumed to stay in the family and keep its current use; only the tax and cost "
                         "lines are projected, not the decision.")

scen = table(["Appreciation", "Property A market value 2045", "Property A property tax 2045", "Comment", "Source"],
             [["2.0% a year", money(O['a_value_2026'] * 1.02 ** 19), money(O['a_value_2026'] * 1.02 ** 19 * V['scc_advalorem'] + DATA['a_flat'] * 1.03 ** 19), "Lower than the long-run California average", ["FHFA-HPI", "COMPUTED"]],
              ["3.0% a year (base)", money(D45['market_T']), money(D45['market_T'] * V['scc_advalorem'] + DATA['a_flat'] * 1.03 ** 19), "Model base case", ["FHFA-HPI"]],
              ["4.0% a year", money(O['a_value_2026'] * 1.04 ** 19), money(O['a_value_2026'] * 1.04 ** 19 * V['scc_advalorem'] + DATA['a_flat'] * 1.03 ** 19), "Above the recent one-year reading", ["FHFA-HPI", "COMPUTED"]]],
             note="FHFA's California all-transactions index was up 0.9% over the year to 2026Q2, so 3% is already an "
                  "optimistic central case, not a conservative one. That cuts against holding the house.")

PAGES.append(("projections.html", "Projections", f"""
<h1>Projections, 2026 to 2055</h1>
<p class="lede">Every year, both houses, on stated assumptions. The assessed value follows statute; the market
value follows an assumption; the running costs follow the owner's figures and published escalation.</p>

{callout("warn", "Read this first", '''<p>The assessed-value and property-tax columns are arithmetic on published
rules and are reliable to the same degree as the 2025 reconciliation. The market-value column is an assumption
&mdash; 3.0% a year &mdash; and nothing more. No projection of this length is a forecast, and the decision
analysis is built so that the conclusion does not depend on it.</p>''')}

{section("Assumptions on one line", table(
    ["Assumption", "Value used", "Why", "Status"],
    [
        ["Property appreciation", "3.0% a year", "Between the 2026 one-year reading (+0.9%) and longer-run California averages", ["FHFA-HPI"]],
        ["General inflation", "3.0% a year", "CPI-U was 3.7% over the year to September 2026; core 2.6%", ["BLS-CPI"]],
        ["Water escalation", "6.0% a year", "Between the adopted 7.0% water and 15.0% sewer steps", ["SFPUC"]],
        ["Electricity escalation", "4.4% a year", "The CPI electricity component, 12 months to September 2026", ["BLS-CPI"]],
        ["Insurance escalation", "6.0% a year", "Recent filings of about 6.9%", ["CDI-2026"]],
        ["Rent escalation (Property B)", "1.6% a year", "The Rent Ordinance cap in force", ["SF-RENT"]],
        ["Repairs, Property A / B", "0.50% / 1.00% of value", "Assumption, calibrated to the owner's observation", "COMPUTED"],
        ["Selling costs", "6.0%", "Commission, escrow, title, transfer tax", "COMPUTED"],
    ], note=None))}

{section("Property A, year by year", proj_full_a,
         sub="Carrying cost is property tax plus insurance, water, electricity and repairs. It excludes income tax and financing.")}

{section("Property B, year by year", proj_full_b)}

{section("Property A under three appreciation rates", scen,
         sub="The tax column is the one that matters, because the assessed value resets to market when you inherit.")}

<section>
  <h2>Download the data</h2>
  <p>The tables above are generated from these files, which are published so the arithmetic can be checked:</p>
  <p>{', '.join(f'<a href="data/{f}">{f}</a>' for f in ['property_a_projection.csv', 'property_b_projection.csv', 'property_a_operating_costs.csv', 'property_b_operating_costs.csv', 'sf_rental_pl.csv', 'estate_headroom.csv', 'model_outputs.json'])}</p>
</section>
""", "projections.html", "Year-by-year projections of value, assessed value, property tax and running costs."))
