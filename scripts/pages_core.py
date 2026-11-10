"""Dashboard, executive summary, properties, property tax."""
from webbuild import exact, DATA, money, pct, table, section, callout, links, link, esc

O = DATA["owner"]
A = DATA["assumptions"]
V = DATA["values"]
D45 = DATA["decisions"]["2045"]
D40 = DATA["decisions"]["2040"]
D50 = DATA["decisions"]["2050"]
REC = DATA["reconcile"]

PAGES = []

# =====================================================================
# DASHBOARD
# =====================================================================
hero = f"""
<div class="hero">
  <div class="eyebrow">Inheritance decision atlas &middot; reviewed 10 Nov 2026</div>
  <h1>Two California houses, one decision.</h1>
  <p class="lede">A house in Cupertino arrives through a trust somewhere between 2040 and 2050.
  Should you live in it, rent it, or sell it and reinvest? This site models the three paths on
  verified local, state and federal rules, using your own utility, tax and rent figures, rounded
  to the nearest $10. Every figure is either linked to an official source or tagged
  <span class="tag unv">UNVERIFIED</span>.</p>
</div>
"""

cards = f"""
<div class="cards">
  <div class="card"><div class="k">Property A &middot; Cupertino</div>
    <div class="v">{money(O['a_value_2026'])}</div>
    <p>Owner estimate, Nov 2026 <span class="tag unv">UNVERIFIED</span><br>
    2026 assessed value {money(O['a_assessed_2026'])} &middot; 2025 tax {money(O['a_tax_2025'])}</p></div>
  <div class="card"><div class="k">Property B &middot; San Francisco</div>
    <div class="v">{money(O['b_value_2026'])}</div>
    <p>3 units, 2 let at {money(O['b_rent_month'])}/mo <span class="tag unv">UNVERIFIED</span><br>
    2025 assessed {money(O['b_assessed_2025'])} &middot; tax {money(O['b_tax_2025'])}</p></div>
  <div class="card"><div class="k">Federal exclusion 2026</div>
    <div class="v">{money(V['fed_excl_2026'])}</div>
    <p>Per person; {money(V['fed_excl_2027'])} in 2027, indexed after that.
    {link('IRS-ESTATE')}</p></div>
  <div class="card"><div class="k">Inheritance window</div>
    <div class="v sm">2040 &ndash; 2050</div>
    <p>Modelled at 2040, 2045 and 2050. Future thresholds are scenarios, not forecasts.</p></div>
  <div class="card win"><div class="k">20-year after-tax leader</div>
    <div class="v">Sell &amp; reinvest</div>
    <p>{money(D45['sell_treasury'])} in nominal 2065 dollars, using the verified 4.88%
    10-year Treasury yield. {link('TREASURY')}</p></div>
</div>
"""

rec = callout("good", "Recommendation in one paragraph", f"""
<p><b>Sell Property A when you inherit it, and reinvest the net proceeds.</b> On the base case
(3.0% appreciation, 3.0% inflation, 4.88% risk-free reinvestment) selling produces
<b>{money(D45['sell_treasury'])}</b> of after-tax wealth twenty years later, against
<b>{money(D45['live_base'])}</b> for living in the house and <b>{money(D45['rows'][4]['terminal'])}</b>
for renting it. Selling also has the least moving parts: the step-up in basis at death means an
immediate sale carries essentially no capital-gains tax, so the outcome depends on one verified
interest rate instead of a 20-year rent forecast. Renting overtakes selling only if Cupertino
values compound at about {pct(D45['crossover_rent'],1)} a year or more <em>and</em> you can let it
for at least {money(D45['breakeven_month'])}/month (2045 dollars). Living in it is the weakest
financial path and needs about {pct(D45['crossover_live'],1)} annual appreciation to break even &mdash;
choose it only if living in Cupertino is worth roughly
{money((D45['sell_treasury']-D45['live_base'])/20)} a year to you.</p>""")

metrics_table = table(
    ["What", "Figure", "Basis", "Kicker", "Source"],
    [
        ["Property A 2025 property tax", money(O['a_tax_2025']),
         "Owner-supplied bill", "Reproduced by the model as " + money(DATA['checked']['a_2025_reproduced']), ["SCC-ASSESSOR"]],
        ["Property A 2025 assessed value", money(O['a_assessed_2025']),
         "Owner-supplied roll", "Implies a 1.335% effective rate", ["RTC-51", "SCC-ASSESSOR"]],
        ["Property B 2025 property tax", money(O['b_tax_2025']),
         "Owner-supplied bill", "Reproduced as " + money(DATA['checked']['b_2025_reproduced']), ["SF-TTC", "SF-PARCEL"]],
        ["Property B 2025 assessed value", money(O['b_assessed_2025']),
         "Owner-supplied roll", "2.135% effective rate is parcel charges, not a rate error (F-04)", ["SF-PARCEL"]],
        ["San Francisco secured tax rate FY2026-27", "1.18162182%",
         "Official adopted rate", "Applies to assessed value, not market value", ["SF-TTC"]],
        ["Santa Clara typical tax-rate area", "$1.1488 per $100",
         "Official county booklet", "1% base + county, school and water bonds", ["SCC-ASSESSOR"]],
        ["Prop 13 cap on assessed value", "2.00% a year",
         "Statute", "Applies only while ownership is unchanged", ["RTC-51"]],
        ["Prop 19 parent-child cap", exact(V['prop19_cap_2025']),
         "BOE, 16 Feb 2025 - 15 Feb 2027", "Added to the transferor's taxable value; residence only", ["BOE-CAP", "BOE-P19"]],
        ["California inheritance or estate tax", "None",
         "Statute since 1982", "No state tax on an inheritance, of any size", ["RTC-13301"]],
        ["Federal estate filing threshold 2026", money(V['fed_excl_2026']),
         "IRS", "Paid by the estate if exceeded, not by you", ["IRS-ESTATE"]],
        ["San Francisco rent increase cap", "1.6%",
         "Rent Board, Mar 2026 - Feb 2027", "Only for rent-controlled units", ["SF-RENT"]],
        ["Average California homeowner premium", exact(V['cdi_avg_premium']),
         "NAIC data via CDI", "Statewide average, not a quote for either house", ["CDI-SIS"]],
        ["10-year Treasury yield, 9 Nov 2026", "4.88%",
         "U.S. Treasury par curve", "The verified reinvestment benchmark", ["TREASURY"]],
        ["CPI-U, 12 months to Sep 2026", "3.7%",
         "BLS", "Core 2.6%; used as an inflation scenario", ["BLS-CPI"]],
    ],
    note="Every row links an official publisher. Owner-supplied amounts are not officially verified; "
         "the model test in the 'Kicker' column shows they are arithmetically consistent with the "
         "official county rates.")

glance = table(
    ["Path for Property A", "What it means", "After-tax wealth 2065 (2045 inheritance)", "What has to be true", "Source"],
    [
        ["<b>Sell, reinvest at 4.88%</b>", "Sell on inheritance, hold Treasuries",
         money(D45['sell_treasury']), "Verified rate; near-zero entry capital-gains tax via step-up", ["TREASURY", "IRS-BASIS"]],
        ["Sell, reinvest in equities at 7%", "Same, equity return assumed",
         money(D45['sell_equity']), "7% nominal return assumption, with real drawdown risk", ["IRS-BASIS"]],
        ["Rent it out", "Keep the house, let it",
         money(D45['rows'][4]['terminal']),
         f"Rent of at least {money(D45['breakeven_month'])}/mo, or {pct(D45['crossover_rent'],1)} appreciation", ["IRS-P527", "RTC-51"]],
        ["Live in it", "Move in, let the San Francisco unit",
         money(D45['live_base']),
         f"Appreciation of about {pct(D45['crossover_live'],1)}/yr, or high personal value", ["IRS-T701", "RTC-51"]],
        ["Live in it with a Prop 19 exclusion", "Only if it was the transferor's home and you occupy it",
         money(D45['rows'][3]['terminal']), "Both parties' principal residence; claim within 3 years",
         ["BOE-P19", "BOE-CAP"]],
    ],
    note="Figures are nominal 2065 dollars, net of selling costs, property tax, running costs and "
         "income/capital-gains tax, for Property A only. Property B is unchanged in every path except "
         "the owner-occupied unit, which becomes rentable if you move out (F-07).")

PAGES.append(("index.html", "Dashboard", f"""
<h1>Dashboard</h1>
<p class="lede">Start here. Five numbers, one recommendation, and the evidence behind it.</p>
{cards}
{rec}
{section("The figures that drive the decision", metrics_table,
         sub="Verified rules and charges first, owner estimates second.")}
{section("Three paths, side by side", glance,
         sub="One inheritance year (2045) and one twenty-year horizon, so the comparison is like for like.")}
<section>
  <h2>Explore</h2>
  <div class="grid">
    <a class="tile" href="executive-summary.html"><b>Executive summary</b><span>The full case, the caveats, and the three things to do next.</span></a>
    <a class="tile" href="property-tax.html"><b>Property tax</b><span>Prop 13, Prop 19, and forward assessed values to 2055.</span></a>
    <a class="tile" href="decision-analysis.html"><b>Decision analysis</b><span>Break-even rent, break-even appreciation, sensitivities.</span></a>
    <a class="tile" href="inheritance-process.html"><b>Inheritance process</b><span>Step by step, with the deadlines that carry penalties.</span></a>
    <a class="tile" href="flagged-for-review.html"><b>Flagged for review</b><span>Everything unverified, with what would settle it.</span></a>
    <a class="tile" href="sources.html"><b>Source library</b><span>24 official links and exactly what each one supports.</span></a>
  </div>
</section>
{callout("warn", "Privacy position", '<p>No names, street addresses, parcel numbers, trust or beneficiary identifiers appear anywhere on this site. The two houses are called Property A and Property B and the ZIP codes were removed. The money figures you supplied are published because the analysis is unusable without them. Read the <a href="privacy.html">privacy page</a> for exactly what was withheld.</p>')}
""", "index.html", "Dashboard for the inherited-property decision: sell, rent or live in the Cupertino house."))

# =====================================================================
# EXECUTIVE SUMMARY
# =====================================================================
findings = [
    ["1", "Two different tax systems", "The step-up in basis sets your <em>income-tax</em> cost; Proposition 13 sets your <em>property-tax</em> bill. A trust changes neither by itself.",
     "Plan the two separately.", ["IRS-BASIS", "RTC-51"]],
    ["2", "Property A probably gets no Prop 19 relief",
     "Prop 19's parent-child exclusion only covers a residence used by <em>both</em> the parent and the child, and only up to taxable value plus " +
     exact(V['prop19_cap_2025']) + ". A rented house, or a house you do not occupy, is fully reassessed to market value.",
     "Budget the full reassessment, and claim the exclusion only if the facts fit.", ["BOE-P19", "BOE-CAP"]],
    ["3", "Property B is where Prop 19 is worth real money",
     "On a " + money(O['b_value_2026']) + " building with a " + money(O['b_assessed_2025']) + " assessed value, an exclusion would cap the new taxable value near " +
     money(O['b_value_2026'] - V['prop19_cap_2025']) + " instead of " + money(O['b_value_2026']) + ". The catch: you must occupy it and file within the deadlines.",
     "Confirm which house is the transferor's principal residence, in writing, now.", ["BOE-P19", "BOE-CAP"]],
    ["4", "No California inheritance tax, at any size",
     "Revenue and Taxation Code 13301 forbids the state and every local government from taxing an inheritance, an estate or any transfer by reason of death.",
     "Do not budget a state death tax. Budget the income tax on what the assets later earn.", ["RTC-13301"]],
    ["5", "The federal threat is the estate, not you",
     "A federal estate tax applies only if the gross estate exceeds " + money(V['fed_excl_2026']) + " in 2026 (" + money(V['fed_excl_2027']) +
     " in 2027, indexed after). It is computed on, and paid by, the estate.",
     "Get the total estate value, including cash and retirement accounts, before assuming no exposure.", ["IRS-ESTATE", "IRS-2027"]],
    ["6", "Property A costs about " + money(DATA['proj_a'][0]['tax']) + " a year in tax today and grows",
     "The model reproduces the 2025 bills to within $10 on both houses, so the forward numbers use the same mechanics.",
     "Use the projections page, not a rule of thumb.", ["SCC-ASSESSOR", "SF-TTC"]],
    ["7", "The running costs are smaller than the tax",
     f"Insurance, water, electricity and repairs together are about {money(DATA['costs_a'][0]['total'])} a year on Property A in 2026, against "
     f"{money(DATA['proj_a'][0]['tax'])} of property tax. On Property B they are about {money(DATA['costs_b'][0]['total'])} a year.",
     "Property tax, not utilities, is the recurring cost that decides this.", ["CDI-SIS", "SFPUC"]],
    ["8", "The solar credit is a lease on time",
     "Net energy metering is closed to new enrolments; systems interconnected after 15 Apr 2023 earn export credits at avoided-cost value, not retail. A legacy 20-year NEM term ends around the inheritance window.",
     "Ask the utility for the system's tariff vintage and term end date (F-05).", ["CPUC-NEM"]],
    ["9", "Selling promptly is the cheapest exit",
     "With a step-up in basis, a sale in the months after death produces almost no taxable gain. Every year you hold as a rental, depreciation lowers your basis and converts part of the gain into 25%-rate recapture.",
     "Decide inside the first year, not the first decade.", ["IRS-BASIS", "IRS-T409", "IRS-P527"]],
    ["10", "Renting has a high bar",
     f"Renting Property A beats selling only above roughly {money(D45['breakeven_month'])}/month in 2045 dollars, or if values compound at "
     f"{pct(D45['crossover_rent'],1)} or more a year.",
     "Get two written rental appraisals before choosing this path.", ["RTC-51", "IRS-P527"]],
    ["11", "Living there is a lifestyle purchase",
     f"Living in the house forgoes the portfolio: about {money((D45['sell_treasury'] - D45['live_base']) / 20)} a year of after-tax wealth at the base case. It also frees the San Francisco owner unit to let, worth about {money(DATA['rent_a']['unit_rent_b'])}/month, which is already counted.",
     "Choose it for the life, not the money.", ["TREASURY", "SF-RENT"]],
    ["12", "The decision is robust to most unknowns",
     f"Selling wins at 2.0%, 3.0% and 4.0% appreciation and at 2.5% and 3.7% inflation. Renting only catches up at about {pct(D45['crossover_rent'],1)} a year, and living in it at about {pct(D45['crossover_live'],1)}.",
     f"Anchor on the {pct(D45['crossover_rent'],1)} threshold: it is the single number to watch.", ["TREASURY", "BLS-CPI"]],
]

findings_t = table(["#", "Finding", "Detail", "What it means for you", "Source"],
                   [[f[0], f"<b>{f[1]}</b>", f[2], f[3], f[4]] for f in findings])

stack = table(
    ["Level", "What it taxes", "Rate or threshold", "Applies here?", "Source"],
    [
        ["Federal estate tax", "The right to transfer property at death", money(V['fed_excl_2026']) + " exclusion (2026)",
         "Only if the total estate exceeds the exclusion", ["IRS-ESTATE"]],
        ["Federal capital gains", "Gain above the stepped-up basis", "20% top rate plus 3.8% NIIT", "Yes, on any gain after death", ["IRS-T409"]],
        ["Federal depreciation recapture", "Depreciation you claimed on a rental", "25% maximum on unrecaptured 1250 gain", "Yes, if you rent then sell", ["IRS-T409", "IRS-P527"]],
        ["Federal home-sale exclusion", "Gain on a main home", money(V['sec121_single']) + " single / " + money(V['sec121_joint']) + " joint", "Only if you live there 2 of the last 5 years", ["IRS-T701"]],
        ["California inheritance or estate tax", "An inheritance or a death transfer", "None", "Never", ["RTC-13301"]],
        ["California income tax on rent", "Net rental income", "1% to 12.3%, plus 1% above $1,000,000", "Yes, as ordinary income", ["FTB-RATES"]],
        ["California income tax on gain", "Capital gain", "Same brackets as ordinary income", "Yes, no preferential rate", ["FTB-RATES"]],
        ["Local property tax", "Assessed value", "1% plus voter bonds; 2% annual cap", "Yes, reset to market on inheritance", ["RTC-51", "SCC-ASSESSOR", "SF-TTC"]],
        ["Local transfer of ownership", "A death transfer held in trust", "Statement due within 150 days", "Yes; penalty up to $5,000", ["RTC-480"]],
    ],
    note="Rounded display; statutory amounts control filings. The 40% top federal estate-tax rate is not quoted "
         "here because it was not re-verified from an official page in this review (F-13).")

next_steps = f"""
<ol>
<li><b>Get the estate inventory, in writing.</b> Total value of everything in the trust &mdash; both houses,
cash, brokerage, retirement accounts &mdash; as of the most recent statement. Without it, the
{money(V['fed_excl_2026'])} federal test cannot be run. Expected result: the two houses alone leave
{money(DATA['estate'][0]['headroom'])} of headroom in 2026, but the cash is the unknown.</li>
<li><b>Ask the trustee which house is the transferor's principal residence.</b> That single fact
decides whether the {exact(V['prop19_cap_2025'])} Prop 19 exclusion is available on Property B, which is
worth roughly {money(O['b_value_2026'] - O['b_assessed_2025'] - V['prop19_cap_2025'])} of taxable value in the first year alone.</li>
<li><b>Order two opinions in the inheritance year:</b> a date-of-death appraisal (it is your basis and the
assessor's new value) and, if you are considering renting, two written rental appraisals. Then pick
the path within twelve months of death.</li>
</ol>
"""

PAGES.append(("executive-summary.html", "Executive summary", f"""
<h1>Executive summary</h1>
<p class="lede">The whole case on one page: what the law actually says, what the numbers actually are,
what to do, and what could change the answer.</p>

{callout("good", "The recommendation", f'''
<p><b>Sell Property A on inheritance and reinvest the net proceeds; do not make Property A your home
and do not treat renting it as the default.</b> At a 2045 inheritance the after-tax position twenty
years later is {money(D45['sell_treasury'])} from selling into Treasuries, {money(D45['rows'][4]['terminal'])}
from renting at an indicative {money(D45['rent_base_month'])}/month, and {money(D45['live_base'])}
from living in it. The ordering holds at 2%, 3% and 4% appreciation. Renting only wins if you clear
{money(D45['breakeven_month'])}/month <em>and</em> values compound near {pct(D45['crossover_rent'],1)}; living in it
only wins if you value the address at roughly {money((D45['sell_treasury'] - D45['live_base']) / 20)} a year.</p>''')}

{section("Twelve findings", findings_t,
         sub="Each one is a rule or a computed result, with the official page that supports it.")}

{section("The tax stack at a glance", stack,
         sub="Local, state and federal, in the order they bite when a death transfer happens.")}

<section>
  <h2>The numbers you asked for</h2>
  <div class="cards">
    <div class="card"><div class="k">Property A tax, 2026</div><div class="v">{money(DATA['proj_a'][0]['tax'])}</div>
      <p>On an assessed value of {money(DATA['proj_a'][0]['assessed'])}</p></div>
    <div class="card"><div class="k">Property A tax, 2045 if inherited</div><div class="v">{money(D45['rows'][0]['base_T'] * V['scc_advalorem'] + DATA['a_flat'] * 1.03 ** 19)}</div>
      <p>Assessed value resets to about {money(D45['market_T'])}</p></div>
    <div class="card"><div class="k">Property A market value, 2045</div><div class="v">{money(D45['market_T'])}</div>
      <p>3.0% a year from {money(O['a_value_2026'])} <span class="tag asm">ASSUMPTION</span></p></div>
    <div class="card"><div class="k">Property B net rent, 2026</div><div class="v">{money(DATA['sf_pl'][0]['net'])}</div>
      <p>Gross {money(DATA['sf_pl'][0]['gross'])} less vacancy, management, tax and running costs</p></div>
    <div class="card"><div class="k">Net proceeds if sold in 2045</div><div class="v">{money(D45['market_T'] * (1 - A['selling_cost']))}</div>
      <p>After 6.0% selling costs <span class="tag asm">ASSUMPTION</span>, near-zero capital-gains tax</p></div>
    <div class="card"><div class="k">Break-even rent, 2045</div><div class="v">{money(D45['breakeven_month'])}</div>
      <p>Monthly rent at which letting the house matches selling it</p></div>
  </div>
</section>

{section("What to do next", next_steps, sub="Three actions, in this order, and none of them cost anything yet.")}

{callout("warn", "What this is not", '''<p>This is a planning model built from published rules and the figures you
supplied. It is not an appraisal, a tax return, a title opinion, or fiduciary advice. The two market values
are estimates; the insurance premiums are estimates; the maintenance, vacancy, management and equity-return
inputs are assumptions. Anything that is not sourced or computed is listed on the
<a href="flagged-for-review.html">Flagged for review</a> page, and nothing has been filled in by guesswork.</p>''')}
""", "executive-summary.html", "Executive summary of the inherited-property decision, with sources."))

# =====================================================================
# PROPERTIES
# =====================================================================
a_hist = [
    (2026, "", 550_537, 0.02), (2025, 7_207, 539_743, 0.029), (2024, 7_003, 529_161, 0.012),
    (2023, 6_917, 518_786, 0.024), (2022, 6_755, 508_614, 0.014), (2021, 6_662, 498_642, 0.015),
    (2020, 6_565, 493_530, 0.0), (2019, 6_565, 483_854, 0.028), (2018, 6_383, 474_368, 0.0),
    (2017, 6_383, 465_067, -0.005), (2016, 6_414, 455_949, 0.046), (2015, 6_130, 449_101, 0.028),
    (2014, 5_965, 440_305, 0.0),
]
b_hist = [
    (2025, 2_439, 114_248, 0.053), (2024, 2_315, 112_008, 0.062), (2023, 2_179, 109_814, 0.034),
    (2022, 2_107, 107_662, 0.02), (2021, 2_066, 105_595, -0.059), (2020, 2_197, 104_513, 0.03),
    (2019, 2_134, 102_465, 0.035), (2018, 2_061, 100_456, 0.184), (2017, 1_740, 98_488, 0.039),
    (2016, 1_675, 96_557, 0.016),
]

a_rows = []
for y, tax, assessed, chg in a_hist:
    eff = (tax / assessed) if tax else None
    a_rows.append([str(y), f'<span class="num">{money(tax) if tax else "&mdash;"}</span>',
                   f'<span class="num">{money(assessed)}</span>',
                   f'<span class="num">{pct(chg,1) if chg else "&mdash;"}</span>',
                   f'<span class="num">{pct(eff) if eff else "&mdash;"}</span>', "OWNER"])
b_rows = []
for y, tax, assessed, chg in b_hist:
    b_rows.append([str(y), f'<span class="num">{money(tax)}</span>', f'<span class="num">{money(assessed)}</span>',
                   f'<span class="num">{pct(chg,1)}</span>', f'<span class="num">{pct(tax/assessed)}</span>', "OWNER"])

recon = table(
    ["Line", "Property A (2025)", "Property B (2025)", "Source"],
    [
        ["Owner-supplied assessed value", money(REC['a']['assessed']), money(REC['b']['assessed']), "OWNER"],
        ["Official ad valorem rate", pct(REC['a']['advalorem_rate'], 4), pct(REC['b']['advalorem_rate'], 4), ["SCC-ASSESSOR", "SF-TTC"]],
        ["Ad valorem component", money(REC['a']['advalorem_dollars']), money(REC['b']['advalorem_dollars']), ["RTC-51"]],
        ["Residual = observed bill minus ad valorem", money(REC['a']['residual']), money(REC['b']['residual']), "COMPUTED"],
        ["Named official parcel charges identified", "&mdash;", exact(V['sf_parcel_2025']), ["SF-PARCEL"]],
        ["Model reproduces the observed bill", f"<b>{money(DATA['checked']['a_2025_reproduced'])}</b> vs {money(O['a_tax_2025'])}",
         f"<b>{money(DATA['checked']['b_2025_reproduced'])}</b> vs {money(O['b_tax_2025'])}", "COMPUTED"],
        ["Effective rate on assessed value", pct(REC['a']['observed_effective']), pct(REC['b']['observed_effective']), "COMPUTED"],
    ],
    note="The model carries the residual as a flat annual charge that inflates with CPI. Every forward "
         "tax figure on this site is built this way, so the arithmetic tracks the owner's real bills.")

PAGES.append(("properties.html", "Properties", f"""
<h1>Properties</h1>
<p class="lede">Two assets, described only by place, county and number. Names, street addresses, parcel
numbers and ZIP codes are withheld (see <a href="privacy.html">privacy</a>).</p>

<div class="cards">
  <div class="card top"><div class="k">Property A</div><div class="v sm">Cupertino, Santa Clara County</div>
    <p>Single-family house with owned solar. Market value {money(O['a_value_2026'])} <span class="tag unv">UNVERIFIED</span>.
    Expected through a trust, 2040&ndash;2050.</p></div>
  <div class="card top"><div class="k">Property B</div><div class="v sm">San Francisco, Outer Sunset</div>
    <p>Three livable units, two let at {money(O['b_rent_month'])}/mo combined, one occupied by the family.
    Market value {money(O['b_value_2026'])} <span class="tag unv">UNVERIFIED</span>.</p></div>
</div>

{section("Property A &mdash; roll history as supplied by the owner", table(
    ["Year", "Property tax", "Tax assessment", "Tax change", "Effective rate", "Status"],
    a_rows,
    note="Owner-supplied, displayed rounded to the nearest $10 as required. The 2026 tax cell is blank "
         "because the 2026 bill was not supplied; the 2026 assessment is the owner's figure. The "
         "effective rate is a computed cross-check, not an official figure.", caption="Property A, 2014-2026"),
    sub="Assessed value rises about 2% a year, which is the Prop 13 cap doing its job.")}

{section("Property B &mdash; roll history as supplied by the owner", table(
    ["Year", "Property tax", "Tax assessment", "Tax change", "Effective rate", "Status"],
    b_rows,
    note="Owner-supplied, rounded to the nearest $10. Two irregularities are flagged rather than explained: "
         "the 2018 tax jump of 18.4% against a 2% assessment change, and the 2021 tax fall of 5.9% against "
         "a 1% assessment rise (F-03). "
         "Neither matches a rate change and both need the actual bills.", caption="Property B, 2016-2025"),
    sub="A 2.1% effective rate on a 1.18% official rate looks wrong until you add the parcel taxes.")}

{section("Reconciling the bills against the official rates", recon,
         sub="This is the test that makes the forward projections credible: the same formula has to reproduce the past.")}

{section("What is known, estimated, and missing", table(
    ["Item", "Property A", "Property B", "Status", "Source"],
    [
        ["Market value, Nov 2026", money(O['a_value_2026']), money(O['b_value_2026']), '<span class="tag unv">UNVERIFIED</span> owner estimate', "OWNER"],
        ["Assessed value", money(O['a_assessed_2026']) + " (2026)", money(O['b_assessed_2025']) + " (2025)", '<span class="tag unv">UNVERIFIED</span> owner', "OWNER"],
        ["Annual property tax", money(O['a_tax_2025']) + " (2025)", money(O['b_tax_2025']) + " (2025)", '<span class="tag unv">UNVERIFIED</span> owner', "OWNER"],
        ["Ad valorem rate applied", "1.1488% typical area", "1.18162182%", '<span class="tag ver">VERIFIED</span>', ["SCC-ASSESSOR", "SF-TTC"]],
        ["Insurance premium", money(O['a_insurance_year']) + "/yr", money(O['b_insurance_year']) + "/yr", '<span class="tag unv">UNVERIFIED</span> estimate', ["CDI-SIS"]],
        ["Water", money(O['a_water_month']) + "/mo (mid of $100-150)", money(O['b_water_month']) + "/mo (mid of $330-400)", '<span class="tag unv">UNVERIFIED</span> owner', ["SFPUC"]],
        ["Electricity", "Net credit, " + money(O['a_electric_month']) + "/mo", money(O['b_electric_month']) + "/mo", '<span class="tag unv">UNVERIFIED</span> owner', ["CPUC-NEM"]],
        ["Gross rent", "Not let &mdash; blank", money(O['b_rent_month']) + "/mo", '<span class="tag unv">UNVERIFIED</span> owner', "OWNER"],
        ["Market rent if let", '<span class="tag gap">BLANK</span> no official quote', "n/a", "Left blank by rule; a derived indicative figure is used and labelled", "OWNER"],
        ["Repairs and maintenance", "Assumed 0.50% of value", "Assumed 1.00% of value", '<span class="tag asm">ASSUMPTION</span>', "COMPUTED"],
        ["Square footage, beds, baths, year built", "Not supplied", "Not supplied", '<span class="tag gap">BLANK</span>', ["OWNER"]],
        ["Cash and other assets in the estate", '<span class="tag gap">BLANK</span>', '<span class="tag gap">BLANK</span>', "Required for the federal test", ["IRS-ESTATE"]],
    ],
    note="Nothing in the BLANK rows has been filled in from comparable sales, listing sites or guesswork."))}

{callout("warn", "The one input that would change the most", '''<p>Which of the two houses is the
transferor's principal residence. If it is Property B and you occupy it after the death, Proposition 19
can hold its taxable value near the transferor's base plus the adjusted cap instead of resetting to
market. On today's numbers that is roughly ''' + money(O['b_value_2026'] - O['b_assessed_2025'] - V['prop19_cap_2025']) + ''' of
taxable value, or about ''' + money((O['b_value_2026'] - O['b_assessed_2025'] - V['prop19_cap_2025']) * V['sf_advalorem']) + ''' a year of
property tax at the San Francisco rate. It is not a certainty, it requires occupancy, and it requires
filing on time. See <a href="property-tax.html">property tax</a>.</p>''')}
""", "properties.html", "Property A and Property B facts, roll history and bill reconciliation."))
