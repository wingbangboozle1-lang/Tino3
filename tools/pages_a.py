#!/usr/bin/env python3
"""pages_a.py — dashboard, executive summary, inheritance process, taxes."""

from site_lib import (M, money, plain, pct, src, table, page, write, pager,
                      VERIFIED, REPORTED, ASSUMED, UNVERIFIED, badge)

A = M["assumptions"]
R = M["rates"]
P = {p["key"]: p for p in M["properties"]}
SC = {s["short"]: s for s in M["scenarios_parent_cup"]}
INC2045 = M["meta"]["inherit_year"]


# ================================================================ DASHBOARD
def build_index():
    cup, sf = P["cup"], P["sf"]
    combined_2026 = cup["fmv_2026"] + sf["fmv_2026"]
    combined_2045 = SC["A"]["prop19"]["cup"]["fmv"] + SC["A"]["prop19"]["sf"]["fmv"]
    base26 = cup["fmv_2026"] + sf["fmv_2026"]
    combined_2045_low = base26 * (1 + A["g_market_low"]) ** 19
    combined_2045_high = base26 * (1 + A["g_market_high"]) ** 19
    tax_now = cup["tax_2026"] + sf["tax_2026"]
    tax_after = SC["A"]["tax_at_inheritance"]["cup"] + SC["A"]["tax_at_inheritance"]["sf"]

    ranked = sorted(M["scenarios_parent_cup"], key=lambda s: -s["total_terminal_wealth"])

    kpis = f"""
<div class="grid k4">
  <div class="kpi accent"><div class="label">Combined value, Nov 2026</div>
    <div class="value">{money(combined_2026)}</div>
    <div class="note">Cupertino {money(cup['fmv_2026'])} + San Francisco {money(sf['fmv_2026'])} &middot; owner estimate {REPORTED}</div></div>
  <div class="kpi"><div class="label">Projected value in 2045</div>
    <div class="value">{money(combined_2045)}</div>
    <div class="note">at {pct(A['g_market'],1)}/yr nominal &middot; {ASSUMED}<br>3%/yr case {money(combined_2045_low)} &middot; 5%/yr case {money(combined_2045_high)}</div></div>
  <div class="kpi warn"><div class="label">Property tax, today &rarr; at inheritance</div>
    <div class="value">{money(tax_now)} &rarr; {money(tax_after)}</div>
    <div class="note">Combined annual bill before vs. after reassessment in scenario A. A <strong>{(tax_after/tax_now):.1f}&times;</strong> increase.</div></div>
  <div class="kpi good"><div class="label">Recommended plan</div>
    <div class="value">Scenario F</div>
    <div class="note">Live in the San Francisco building, sell Cupertino. Terminal after-tax wealth in 2065: <strong>{money(SC['F']['total_terminal_wealth'])}</strong></div></div>
</div>"""

    rank_rows = []
    for s in ranked:
        rank_rows.append([
            f"<strong>{s['short']}</strong>",
            s["name"].split(". ", 1)[1],
            (money(s["first_year_cashflow"]), "r"),
            (money(s["tax_at_inheritance"].get("cup", 0) + s["tax_at_inheritance"].get("sf", 0)) if s["tax_at_inheritance"] else "&mdash;", "r"),
            (f"<strong>{money(s['total_terminal_wealth'])}</strong>", "r"),
        ])
    rank_tbl = table(
        ["", "Plan", "After-tax cash flow, first year", "Property tax, first year", "Terminal after-tax wealth, 2065"],
        rank_rows,
        caption=f"All six plans, ranked by terminal after-tax wealth ({INC2045}&ndash;2065). "
                f"Assumes the Cupertino house was the parents' principal residence. A negative first-year "
                f"figure means the plan needs outside cash to run.",
        aligns=["", "", "r", "r", "r"],
    )

    body = f"""
<div class="callout">
<span class="h">What this site answers</span>
<p>Two houses will pass to you through a trust in roughly 2040&ndash;2050: a single-family home in
Cupertino (95014) and a three-unit building in San Francisco's Outer Sunset (94122) that already
produces rent. This site sets out the law that governs the transfer, projects the value, tax and
running costs year by year, and compares six plans for the first twenty years after you inherit.</p>
<p style="margin-bottom:0">Every number carries a source. Figures that could not be checked against an
official source are on the <a href="pages/flagged.html">Flagged for review</a> page rather than being
quietly filled in.</p>
</div>

{kpis}

<h2 id="headline">The headline</h2>
<div class="callout good">
<span class="h">One decision matters more than all the others</span>
<p>Under <strong>Proposition 19</strong> ({src('S01')}) an inherited house keeps the parents'
low property-tax base <em>only</em> if it was <em>their</em> principal residence <em>and</em> you move
into it within one year. Even then, the protected amount is capped at the old base plus
<strong>$1,044,586</strong> ({src('S02')}) &mdash; a cap the Cupertino house passed long ago.</p>
<p style="margin-bottom:0">Projected to 2045, the combined property tax on the two houses goes from
<strong>{money(tax_now)}</strong> a year to <strong>{money(tax_after)}</strong> a year. That single
change, not price appreciation, decides which plan wins.</p>
</div>

<h3>Why the San Francisco building is the one to keep</h3>
<p>Once both houses are reassessed to market value, the two properties behave very differently as
investments. Cupertino becomes a house worth {money(SC['A']['prop19']['cup']['fmv'])} that costs
{money(M['post_reassessment_yield']['cup']['property_tax'])} a year in property tax and returns
{pct(M['post_reassessment_yield']['cup']['net_yield_on_value'],1)} a year net if rented. The San Francisco
building, worth {money(SC['A']['prop19']['sf']['fmv'])}, costs
{money(M['post_reassessment_yield']['sf']['property_tax'])} a year and returns
<strong>{pct(M['post_reassessment_yield']['sf']['net_yield_on_value'],1)}</strong> net, because two
sitting tenancies are protected by San Francisco rent control ({src('S13')}) and the building's
Prop 13 base is still tiny.</p>

{rank_tbl}

<h3>Read this next</h3>
<div class="tiles">
  <a class="tile" href="pages/executive-summary.html"><div class="t">Executive summary</div><div class="d">One page: what happens, what it costs, what to do, and the three things that would change the answer.</div></a>
  <a class="tile" href="pages/inheritance-process.html"><div class="t">Inheritance process, step by step</div><div class="d">From the death certificate and trust administration to the recorded deed, the assessor's claim and the tax filings.</div></a>
  <a class="tile" href="pages/taxes.html"><div class="t">Taxes &amp; law</div><div class="d">Prop 13, Prop 19, the federal estate tax, California's absence of an inheritance tax, step-up basis, transfer tax.</div></a>
  <a class="tile" href="pages/projections.html"><div class="t">Projections 2026&ndash;2065</div><div class="d">Value, assessed value and property tax for both houses, year by year, on three growth assumptions.</div></a>
  <a class="tile" href="pages/decision-analysis.html"><div class="t">Decision analysis</div><div class="d">Six plans, twenty years of cash flow, sensitivity to growth and returns, and what would flip the ranking.</div></a>
  <a class="tile" href="pages/risks.html"><div class="t">Risks &amp; law changes</div><div class="d">What is being proposed in Sacramento and Washington, and how much each change would move the numbers.</div></a>
  <a class="tile" href="pages/cupertino.html"><div class="t">Cupertino 95014</div><div class="d">Assessed-value and tax history, effective rate reconciliation, cost base.</div></a>
  <a class="tile" href="pages/san-francisco.html"><div class="t">San Francisco 94122</div><div class="d">Three units, two tenancies, rent roll, rent-control exposure, cost base.</div></a>
  <a class="tile" href="pages/flagged.html"><div class="t">Flagged for review</div><div class="d">The items that could not be verified against an official source, with what is needed to close each one.</div></a>
</div>

<h2 id="numbers">The numbers that drive everything</h2>
{table(
  ["Figure", "Value", "Basis", "Source"],
  [
    ["Cupertino value, Nov 2026", money(3100000), "Owner estimate", REPORTED],
    ["Cupertino assessed value, 2026", money(550537), "Owner's tax roll history", REPORTED],
    ["Cupertino property tax, 2025-26", money(7003), "25-26 bill (2025 column)", REPORTED],
    ["Cupertino effective rate implied by the bill", pct(cup["eff_rate_reported"], 4), "7207 &divide; 550537", REPORTED],
    ["Santa Clara County published rate, lowest Cupertino-area TRA", pct(R["svc_rate"], 4), "2025-26 rate book, components summed", VERIFIED + " " + src("S09")],
    ["San Francisco value, Nov 2026", money(1800000), "Owner estimate", REPORTED],
    ["San Francisco assessed value, 2025", money(114248), "Owner's tax roll history", REPORTED],
    ["San Francisco property tax, 2025", money(2439), "2025 bill", REPORTED],
    ["San Francisco published rate, FY2025-26", pct(R["sf_rate"], 6), "$1.18268325 per $100", VERIFIED + " " + src("S10")],
    ["Prop 19 parent-child allowance, Feb 2025 &ndash; Feb 2027", money(1044586, exact=True), "BOE LTA 2025/009", VERIFIED + " " + src("S02")],
    ["Federal estate-tax basic exclusion, 2026", money(15000000), "Rev. Proc. 2025-32", VERIFIED + " " + src("S03")],
    ["California estate / inheritance tax", "none", "Prop 6 (1982) repealed it", VERIFIED + " " + src("S06")],
    ["Annual gift exclusion, 2026", money(19000), "Rev. Proc. 2025-32", VERIFIED + " " + src("S03")],
    ["SF documentary transfer tax, $1M&ndash;$5M", "0.75%", "of full consideration", VERIFIED + " " + src("S11")],
    ["SF documentary transfer tax, $5M&ndash;$10M", "2.25%", "of full consideration", VERIFIED + " " + src("S11")],
    ["Homeowners' exemption", money(7000), "off assessed value", VERIFIED + " " + src("S16")],
  ],
  caption="Core figures. &ldquo;Reported&rdquo; means supplied by the owner and not publicly verifiable.",
  aligns=["", "r", "", ""],
)}

<div class="callout warn">
<span class="h">Two figures do not reconcile &mdash; read before relying on them</span>
<p style="margin-bottom:0">The San Francisco tax of {money(2439)} against an assessment of
{money(114248)} implies a <strong>2.13%</strong> effective rate. The City's published rate is
<strong>1.1827%</strong>, which would produce {money(1350)}. The difference is about $1,090 a year.
Either the assessment figure, the tax figure, or both are not what they appear to be.
<a href="pages/flagged.html#sf-rate">Full note and what would settle it &rarr;</a></p>
</div>
"""
    write("index.html", page(
        "Inheritance decision dashboard",
        "Two Bay Area houses passing through a trust in 2040&ndash;2050: the law, the projected costs, and which of six plans to choose.",
        body, rel="", current="index.html"))


# ========================================================= EXECUTIVE SUMMARY
def build_exec():
    ranked = sorted(M["scenarios_parent_cup"], key=lambda s: -s["total_terminal_wealth"])
    cup = P["cup"]
    pl = M["prop19_lifetime"]

    body = f"""
<div class="toc"><strong>Contents</strong>
<ol>
<li><a href="#situation">The situation</a></li>
<li><a href="#law">The law that governs the transfer</a></li>
<li><a href="#cost">What the houses cost to own</a></li>
<li><a href="#options">The six plans</a></li>
<li><a href="#rec">Recommendation</a></li>
<li><a href="#flip">What would change the answer</a></li>
<li><a href="#todo">What to do before 2040</a></li>
</ol></div>

<h2 id="situation">1. The situation</h2>
<p>Two residential properties in the San Francisco Bay Area will pass to the next generation through a
trust, most likely between 2040 and 2050:</p>
<ul>
<li><strong>Cupertino, ZIP 95014.</strong> A single-family home, estimated at
{money(cup['fmv_2026'])} in November 2026, assessed by Santa Clara County at {money(cup['assessed_2026'])}
with a 2025-26 tax bill of {money(cup['tax_2026'])}. Rooftop solar.</li>
<li><strong>San Francisco, Outer Sunset, ZIP 94122.</strong> A three-unit building, estimated at
{money(P['sf']['fmv_2026'])}, assessed at {money(P['sf']['assessed_2025'])} in 2025 with a tax bill of
{money(P['sf']['tax_2025'])}. Two units are let for a combined {money(7150)} a month; the third is vacant.</li>
</ul>
<p>Alongside the real estate comes a cash inheritance large enough that estate-tax thresholds need to be
watched. The analysis below is built to answer one question: <strong>live in one of them, rent them out,
or sell and invest?</strong></p>

<div class="callout warn">
<span class="h">A fact the analysis depends on, which the brief does not state</span>
<p style="margin-bottom:0">Proposition 19 relief attaches only to the property that was the
<em>transferor's</em> principal residence. The brief does not say which house the parents live in. The
base case assumes <strong>Cupertino</strong>. Every result is also run with the assumption reversed; the
difference is shown in section 6 and on the <a href="decision-analysis.html">decision analysis</a> page.
Confirming this single fact is worth more than any other input.</p>
</div>

<h2 id="law">2. The law that governs the transfer</h2>
<h3>Property tax &mdash; Proposition 13 and Proposition 19</h3>
<p>Proposition 13 does three things. It caps the general levy at <strong>1%</strong> of full cash value
&mdash; evidenced by the county rate books, each of which states &ldquo;1% Maximum Tax Levy 1.00000&rdquo; for
every tax rate area ({src('S09')} {src('S10')}). It limits annual assessed-value growth to <strong>2%</strong>
({src('S17')}). And it reassesses to market value only on a change in ownership or new construction.
Inheritance <em>is</em> a change in ownership, so the default is a reassessment to market value.</p>
<p>Proposition 19 ({src('S01')}), effective for transfers on or after 16 February 2021, provides the only
relief available to a child. It applies to a principal residence, requires the child to make it their own
principal residence within one year and claim the homeowners' exemption, and caps the protected amount at
the parent's factored base year value plus an inflation-adjusted allowance &mdash;
<strong>{money(1044586, exact=True)}</strong> for transfers between February 2025 and
February 2027 ({src('S02')}). Anything above that cap is added back to the taxable value.</p>
<p>Three consequences follow, and they drive the whole analysis:</p>
<ol>
<li><strong>The rental building in San Francisco gets no relief at all.</strong> Prop 19 deleted the old
parent-child exclusion for property other than a principal residence.</li>
<li><strong>Cupertino's cap is long exceeded.</strong> Its base is {money(cup['assessed_2026'])} against a
value of {money(cup['fmv_2026'])} &mdash; a gap of {money(cup['fmv_2026']-cup['assessed_2026'])}, roughly
five times the allowance. Moving in saves {money(pl['cup']['annual_saving_first_year'])} a year but does not
restore the old bill.</li>
<li><strong>The claim is not automatic.</strong> It is Form BOE-19-P, filed with the county assessor within
three years of the transfer or before the property is sold.</li>
</ol>

<h3>Estate and inheritance tax</h3>
<p><strong>California imposes no estate tax and no inheritance tax.</strong> The state's inheritance and gift
tax was repealed by Proposition 6 in June 1982, and the residual "pick-up" tax produces no revenue for
decedents dying after 2004 ({src('S06')}). A state estate tax would need a constitutional amendment approved
by voters ({src('S07')}).</p>
<p>The only death tax that can apply is federal. For 2026 the basic exclusion amount is
<strong>{money(15000000)}</strong> per person, up from {money(13990000)} for 2025, with a 40% rate above it
({src('S03')}). A married couple can shelter {money(30000000)} if a portability election is made on a timely
return.</p>
<p class="muted">Whether the {money(15000000)} level holds through the 2040s depends on future legislation. The
IRS publishes the figure one year at a time; it publishes no long-range schedule. The projection on this site
indexes the verified 2026 figure at an assumed inflation rate and says so.</p>
<p>Indexed at 2.5% a year, the single-person exclusion reaches roughly {money(M['estate']['thresholds'][4]['single'])}
by 2045. The two houses alone are projected at {money(SC['A']['prop19']['cup']['fmv']+SC['A']['prop19']['sf']['fmv'])}
that year, so the estate can absorb about {money(M['estate']['thresholds'][4]['single'] - (SC['A']['prop19']['cup']['fmv']+SC['A']['prop19']['sf']['fmv']))}
of cash before a federal return is required. <a href="taxes.html#estate">Full threshold table &rarr;</a></p>

<h3>Capital gains &mdash; the step-up is the single largest tax lever</h3>
<p>Property acquired from a decedent takes a basis equal to fair market value at the date of death
({src('S18')}). The appreciation that accrued during the parents' ownership is never taxed. On these two
houses, the growth between 2026 and 2045 alone is {money(M['stepup']['pre_inheritance_appreciation'])};
taxed at the assumed 37.1% blended rate that is <strong>{money(M['stepup']['tax_avoided'])}</strong> of tax
that does not arise, simply because you inherit rather than receive a gift.</p>
<p>This has a direct planning consequence: <strong>do not ask for the houses to be transferred during the
parents' lifetime.</strong> A lifetime gift carries over the parents' basis and forfeits the step-up.</p>

<h2 id="cost">3. What the houses cost to own</h2>
<p>Today's combined property tax is {money(cup['tax_2026']+P['sf']['tax_2026'])} a year. After
reassessment in 2045 it is projected at {money(SC['A']['tax_at_inheritance']['cup']+SC['A']['tax_at_inheritance']['sf'])}
in the plan where you occupy Cupertino &mdash; a {(SC['A']['tax_at_inheritance']['cup']+SC['A']['tax_at_inheritance']['sf'])/(cup['tax_2026']+P['sf']['tax_2026']):.1f}-fold rise.</p>
{table(
  ["", "Cupertino 95014", "San Francisco 94122", "Basis"],
  [
    ["Water", "$100&ndash;$150 / month", "$330&ndash;$400 / month (three units)", "Owner observation " + REPORTED],
    ["Electricity", "net credit, about &minus;$15 / month", "$30&ndash;$70 / month", "Owner observation " + REPORTED],
    ["Insurance", money(2340) + " / yr (modelled floor)", money(2340) + " / yr (modelled floor)", "CDI statewide average " + VERIFIED + " " + src("S15")],
    ["Maintenance", "0.30% of value / yr", "0.85% of value / yr", "Modelling assumption " + ASSUMED],
    ["Property tax 2026", money(cup["tax_2026"]), money(P["sf"]["tax_2026"]), "Owner bills " + REPORTED],
    ["Property tax at inheritance (2045, plan A)", money(SC["A"]["tax_at_inheritance"]["cup"]), money(SC["A"]["tax_at_inheritance"]["sf"]), "Model"],
  ],
  caption="Annual ownership costs. The owner's own estimate of $1,500/yr for insurance is far below the "
          "statewide average and is discussed on the flagged page.",
  aligns=["", "r", "r", ""],
)}
<p class="muted">Detail, including the utility rate structure and the insurance-market context, is on
<a href="operating-costs.html">Operating costs</a>.</p>

<h2 id="options">4. The six plans</h2>
<p>Each plan is run from 2045 to 2065. Every annual net cash flow &mdash; rent received, less property tax,
insurance, water, electricity, maintenance, income tax, and (where no inherited house is occupied) market
rent for equivalent housing &mdash; is invested at an assumed 6% nominal. At 2065 any remaining house is sold
and the portfolio liquidated, both after tax.</p>
"""

    rows = []
    for s in ranked:
        mark = "hl" if s["short"] == "F" else ""
        rows.append(([
            f"<strong>{s['short']}</strong>", s["name"].split(". ", 1)[1],
            (money(s["first_year_cashflow"]), "r"),
            (money(s["tax_at_inheritance"].get("cup", 0) + s["tax_at_inheritance"].get("sf", 0)), "r"),
            (f"<strong>{money(s['total_terminal_wealth'])}</strong>", "r"),
        ], mark))

    body += table(
        ["", "Plan", "First-year after-tax cash flow", "First-year property tax", "Terminal after-tax wealth, 2065"],
        rows,
        caption="Ranked by terminal after-tax wealth. Cupertino treated as the parents' principal residence.",
        aligns=["", "", "r", "r", "r"],
    )

    body += f"""
<h2 id="rec">5. Recommendation</h2>
<div class="callout good">
<span class="h">Plan F &mdash; live in the San Francisco building, sell Cupertino at inheritance, invest the proceeds</span>
<p>Terminal after-tax wealth in 2065: <strong>{money(SC['F']['total_terminal_wealth'])}</strong>, against
{money(SC['A']['total_terminal_wealth'])} for living in Cupertino and keeping both, and
{money(SC['D']['total_terminal_wealth'])} for selling both and renting.</p>
<p style="margin-bottom:0">It ranks first in eight of the nine growth-and-return combinations tested, and
second in the ninth.</p>
</div>
<p><strong>Why it wins.</strong> The reasoning is not "San Francisco is a better market". It is that after
reassessment the Cupertino house becomes a poor financial asset while the San Francisco building stays a
good one:</p>
<ul>
<li>Cupertino, inhabited, costs {money(SC['A']['tax_at_inheritance']['cup'])} a year in property tax on a
house that produces no income. Rented, it yields {pct(M['post_reassessment_yield']['cup']['net_yield_on_value'],1)}
net on value.</li>
<li>The San Francisco building yields {pct(M['post_reassessment_yield']['sf']['net_yield_on_value'],1)} net
after its own reassessment, because two of its three units are long-standing tenancies whose rent stream is
real cash, and because a three-unit building worth less than the Cupertino house can carry rent that is
nearly as large.</li>
<li>Selling Cupertino immediately after death costs almost nothing in capital gains &mdash; the step-up
resets the basis to {money(SC['F']['sale_at_inheritance']['cup']['price'])} &mdash; so the only frictions are
about 5% in selling costs and {money(SC['F']['sale_at_inheritance']['cup']['transfer_tax'])} of county
transfer tax.</li>
<li>You still need somewhere to live. Occupying the San Francisco building's vacant unit costs only the
rent you forgo on that one unit, not market rent on a whole house.</li>
</ul>
<p><strong>What it is not.</strong> This is not a recommendation to be all-cash. Plan F leaves you with a
{money(SC['F']['sale_at_inheritance']['cup']['net'])} portfolio plus a rent-producing building &mdash;
roughly {pct(SC['F']['sale_at_inheritance']['cup']['net']/(SC['F']['sale_at_inheritance']['cup']['net']+SC['A']['prop19']['sf']['fmv']),0)}
invested, {pct(SC['A']['prop19']['sf']['fmv']/(SC['F']['sale_at_inheritance']['cup']['net']+SC['A']['prop19']['sf']['fmv']),0)}
in Bay Area residential property.</p>

<h2 id="flip">6. What would change the answer</h2>
{table(
  ["If this changes", "Effect on the ranking", "How far", "Where"],
  [
    ["The parents actually live in San Francisco, not Cupertino",
     "Plans B and F improve further; A and E get worse",
     "F rises to " + money(M['scenarios_parent_sf'][5]['total_terminal_wealth']),
     '<a href="decision-analysis.html#flip">Decision analysis</a>'],
    ["The portfolio earns 4% rather than 6%",
     "Keeping and renting Cupertino (B) overtakes F",
     "B " + money(M['grid'][3]['wealth']['B']) + " vs F " + money(M['grid'][3]['wealth']['F']),
     '<a href="decision-analysis.html#grid">Robustness grid</a>'],
    ["Bay Area house prices grow 5% rather than 4%",
     "The gap narrows but F still leads",
     "F " + money(M['grid'][6]['wealth']['F']) + " vs B " + money(M['grid'][6]['wealth']['B']),
     '<a href="decision-analysis.html#grid">Robustness grid</a>'],
    ["You are unwilling to be a landlord at all",
     "F is the only plan that both avoids that and keeps a house",
     "&mdash;",
     '<a href="decision-analysis.html">Decision analysis</a>'],
    ["Prop 19 is repealed before the transfer",
     "Cupertino keeps an unlimited exclusion only if you still move in; the gap narrows",
     "Up to " + money(pl['cup']['twenty_one_year_saving']) + " over 21 years",
     '<a href="risks.html">Risks &amp; law changes</a>'],
  ],
  caption="Sensitivity summary. The recommendation survives every single-variable change tested; "
          "only a sustained low portfolio return reverses it.",
  aligns=["", "", "r", ""],
)}

<h2 id="todo">7. What to do before 2040</h2>
<ol>
<li><strong>Establish, in writing, which house is the parents' principal residence.</strong> It is the
assumption on which the entire property-tax analysis rests. A homeowners' exemption on the county roll is
the cleanest evidence ({src('S16')}).</li>
<li><strong>Do not take the houses as a lifetime gift.</strong> A gift forfeits the step-up in basis
({src('S18')}) and would cost roughly {money(M['stepup']['tax_avoided'])} in avoidable capital-gains tax on
the 2026&ndash;2045 appreciation alone.</li>
<li><strong>Review the trust instrument.</strong> Whether the trust or the beneficiary takes title, whether
there is a sub-trust for the San Francisco building, and who is trustee all affect how quickly the deed can
be recorded &mdash; and the deed is what starts the assessor's clock.</li>
<li><strong>Get real insurance quotes for both ZIP codes.</strong> This is the largest unresolved number in
the cost model. See <a href="flagged.html#insurance">flagged item 4</a>.</li>
<li><strong>Confirm the actual tax rate on each parcel.</strong> Both owner-supplied tax series imply
effective rates that differ from the published rates. See
<a href="flagged.html#sf-rate">flagged items 1 and 2</a>.</li>
<li><strong>Decide the occupancy question now, on paper.</strong> If Plan F is the intention, the one-year
move-in clock and the BOE-19-P filing are the two deadlines that cannot be missed. They are steps 12 and 15
of the <a href="inheritance-process.html">inheritance process</a>.</li>
</ol>

<hr>
<p class="muted"><strong>Scope and limits.</strong> Projections use an assumed {pct(A['g_market'],1)} nominal
annual appreciation for Bay Area houses and {pct(A['g_invest'],1)} for a diversified portfolio. Neither is a
forecast and neither is sourced &mdash; they are disclosed assumptions, stress-tested on the decision analysis
page. Tax law is as published on {M['meta']['build_date']}. This document is not legal, tax or investment
advice.</p>
"""
    write("pages/executive-summary.html", page(
        "Executive summary",
        "What is being inherited, what the law does to it, what it costs, which of six plans wins and by how much.",
        body, rel="../", current="pages/executive-summary.html"))


# ======================================================= INHERITANCE PROCESS
def build_process():
    steps = [
        ("Death of the trustor",
         "Obtain 12&ndash;15 certified copies of the death certificate. Everything downstream needs them.",
         "Immediately", "County recorder / vital records", "&mdash;",
         "Order more copies than you think you need; banks, the assessor and the recorder each keep one."),
        ("Confirm the trustee and read the trust",
         "Identify the successor trustee, the distribution standard, and whether the real property passes outright or into a continuing sub-trust. A continuing trust can mean the property never vests in you personally, which changes the assessor's analysis.",
         "Within days", "The trust instrument", "Attorney review $2,000&ndash;$6,000",
         "This is the step that most often changes the answer. A trust that holds the property for 20 more years is treated differently from an outright distribution."),
        ("Serve the statutory notice",
         "The trustee serves notice on heirs and beneficiaries under Probate Code &sect;16061.7, starting a 120-day contest window.",
         "Within 60 days of notice of the trust becoming irrevocable", "Probate Code &sect;16061.7", "$0&ndash;$500",
         "A trust administration that skips this can be reopened later."),
        ("Marshal the assets",
         "Inventory the real property, the cash and the securities. Establish values as of the date of death &mdash; that date fixes both the capital-gains basis and the estate-tax value.",
         "Within 3&ndash;6 months", "IRS Form 706 instructions; " + src("S18"), "Appraisal $500&ndash;$1,500 per house",
         "Use a licensed appraiser, not a Zestimate. The date-of-death value is the number the IRS and the county both look at."),
        ("File the federal estate-tax return, if required",
         "Form 706 is due nine months after death (extendable six months). A return is required only if the gross estate exceeds the basic exclusion amount &mdash; $15,000,000 for 2026 (" + src("S03") + "). File anyway if a portability election is wanted.",
         "9 months after death", "IRS " + src("S03"), "Preparer $3,000&ndash;$15,000",
         "Portability preserves a deceased spouse's unused exclusion. It is only available if an election is made on a timely return."),
        ("Pay the California income tax on income earned during administration",
         "The trust or estate files a California fiduciary return (Form 541) for income received after death. California has no separate estate tax (" + src("S06") + ").",
         "April 15 of the following year", "FTB " + src("S06"), "Preparer $500&ndash;$2,000",
         "Rental income received between death and distribution belongs to the estate, not to you."),
        ("Obtain a taxpayer identification number for the trust",
         "Form SS-4. Needed before any bank, broker or tenant will deal with the trustee.",
         "Before the first transaction", "IRS", "$0", ""),
        ("Settle the cash inheritance",
         "Distribute cash and securities. Re-register accounts. Record the date-of-death value of every security &mdash; that becomes the new basis.",
         "Per the trust terms", "Broker / bank", "$0&ndash;$1,000",
         "Securities also step up in basis at death. Do not sell before the transfer if you can avoid it."),
        ("Prepare and record the deed",
         "The trustee executes a deed transferring title to the beneficiary (or to the continuing trust). The deed is recorded in the county where the property sits &mdash; Santa Clara County for Cupertino, San Francisco for the Outer Sunset building.",
         "Before any sale or refinance", "County recorder", "Recording $100&ndash;$300; SF adds $10 per deed subject to transfer tax",
         "Recording is what tells the assessor a change in ownership has happened. It starts every clock below."),
        ("Deed transfers inside a trust are not a sale",
         "A transfer from a trust to a beneficiary is generally exempt from documentary transfer tax, and is exempt from reassessment only to the extent Prop 19 allows. The exemption claim is made by affidavit at recording.",
         "At recording", src("S11") + " (transfer tax exemptions)", "$0",
         "Do not assume the transfer tax exemption also means a property tax exemption. They are separate questions decided by separate offices."),
        ("File the change-of-ownership statement",
         "The assessor mails a questionnaire after recording. Return it. Non-response lets the assessor reassess on the best information available, usually the sale price of a comparable.",
         "Within 45 days of the assessor's request", "County assessor", "$0",
         "Answering it is not optional in practice; a missed response is how people end up with an inflated base."),
        ("File BOE-19-P &mdash; the Prop 19 parent-child exclusion claim",
         "Only if the property was the parents' principal residence <em>and</em> you will occupy it. The form claims the exclusion and is the single most valuable document in the file: on the Cupertino house it is worth " + money(M['prop19_lifetime']['cup']['annual_saving_first_year']) + " a year at 2045 values, or " + money(M['prop19_lifetime']['cup']['twenty_one_year_saving']) + " over 21 years.",
         "Within 3 years for transfers on or after 16 Feb 2021, or before sale to a third party, whichever is earlier", src("S01") + " " + src("S02"), "$0",
         "File it even if you think it will be denied. A denial is appealable; an unfiled claim simply does not exist."),
        ("File BOE-266 &mdash; the homeowners' exemption",
         "The $7,000 exemption (" + src("S16") + ") is available only on an owner-occupied principal residence and only if claimed. It is worth about $90 a year; more importantly, granting it is how the assessor documents that you occupy the house, which is a condition of the Prop 19 exclusion.",
         "By February 15 to get the full year; within 1 year of transfer for Prop 19 purposes", src("S16"), "$0",
         "The exemption is not automatic and does not transfer from the seller or the parent."),
        ("Move in within one year",
         "If you are claiming the exclusion, you must actually make the house your principal residence within one year of the transfer and claim the homeowners' or disabled veterans' exemption.",
         "Within 12 months of the transfer date", src("S01"), "&mdash;",
         "This is the requirement that most claims fail on. Changing your mind in year two undoes the exclusion prospectively."),
        ("Review the assessor's determination",
         "The assessor issues a notice of the new base-year value. Check the arithmetic, the allowance applied, and the effective date.",
         "When received", "County assessor", "$0",
         "If the exclusion was applied at the wrong allowance period, the error compounds for as long as you own the house."),
        ("Appeal if the value is wrong",
         "An assessment appeal must be filed with the county assessment appeals board between July 2 and December 31 for the following lien date, or within 60 days of a supplemental assessment notice.",
         "Narrow statutory window", "County assessment appeals board", "$30&ndash;$500 filing fee",
         "The window is short and it is not extended for any reason."),
        ("If selling: order the payoff and title work",
         "A sale within a few months of death is the cheapest possible exit, because the basis has just stepped up and the gain is close to zero (" + src("S18") + ").",
         "At listing", "Title company", "Title and escrow $3,000&ndash;$8,000",
         "Selling before the BOE-19-P claim is filed is permitted, but it ends the exclusion claim."),
        ("If selling: pay the documentary transfer tax",
         "Santa Clara County charges $0.55 per $500 of consideration, plus city tax where one exists (Cupertino imposes none). San Francisco's rate is tiered on the entire consideration and is far higher: 0.75% from $1M to $5M, 2.25% from $5M to $10M (" + src("S11") + ").",
         "At recording", src("S11"), "See the transfer-tax table on the taxes page",
         "The tier applies to the whole price, not to the slice above the threshold. A sale at $5.1M costs three times as much transfer tax as a sale at $4.9M."),
        ("If retaining: re-benchmark rents and insurance",
         "For the San Francisco building, the annual allowable increase is set each year by the Rent Board (" + src("S13") + "). Insurance should be re-quoted annually in a market that has repriced sharply.",
         "Annually", src("S13") + " " + src("S15"), "&mdash;",
         "Rent-controlled tenancies cannot be reset to market while they continue; only vacancy decontrol resets them."),
        ("If retaining: schedule the next 5 years of capital work",
         "A three-unit building built before 1979 will need roof, sewer, electrical and seismic attention on a predictable cycle. Budget 0.85% of value annually.",
         "Ongoing", "Modelling assumption", money(15300) + " in 2026 on the San Francisco building",
         "Deferring this work is the most common way a rental becomes a loss."),
    ]

    rows = []
    for i, (name, what, when, auth, cost, note) in enumerate(steps, 1):
        rows.append([
            (f"<strong>{i}</strong>", "c"), f"<strong>{name}</strong>",
            f"{what}<br><small class='muted'>{note}</small>" if note else what,
            when, auth, (cost, "r"),
        ])

    body = f"""
<div class="callout">
<span class="h">How to read this page</span>
<p style="margin-bottom:0">Twenty steps, in the order they happen. Steps 1&ndash;10 are common to every
plan. Steps 11&ndash;14 are the ones that decide how much property tax you pay for as long as you own the
houses. Steps 15&ndash;20 split by what you decide to do.</p>
</div>

<p class="lede">The single most important thing on this page: <strong>the assessor does not wait for you.</strong>
Recording the deed starts a clock, and every relief available to you is claimed on a form that you must file.
Nothing is automatic.</p>

<div class="callout warn">
<span class="h">A note on the &ldquo;Authority&rdquo; column below</span>
<p style="margin-bottom:0">Only the items carrying an <span class="srclink">Sxx</span> chip were checked against
the publisher's own document. Bare statutory references &mdash; such as Probate Code &sect;16061.7 &mdash; are
given as legal signposts so you know which provision to read, <strong>not</strong> as verified evidence that the
text says what is summarised here. Cost figures in the last column are planning allowances, not quotes.</p>
</div>

<h2>Step by step</h2>
{table(
  ["#", "Stage", "What happens and why it matters", "Deadline", "Authority", "Typical cost"],
  rows,
  caption="Trust administration and property transfer sequence.",
  aligns=["c", "", "", "", "", "r"],
)}

<h2 id="clock">The four clocks that actually run</h2>
{table(
  ["Clock", "Length", "What it is for", "Consequence of missing it"],
  [
    ["Homeowners' exemption claim", "By 15 February for the full-year exemption", "Establishes occupancy and saves $7,000 of assessed value", "Exemption granted only from the following year, or not at all " + src("S16")],
    ["Move-in", "12 months from the transfer date", "Makes the house your principal residence for Prop 19", "The entire exclusion is lost; the house is reassessed to market value " + src("S01")],
    ["BOE-19-P claim", "3 years from the transfer, or before sale", "Claims the Prop 19 exclusion", "The exclusion is lost for the whole ownership period " + src("S01")],
    ["Assessment appeal", "2 July &ndash; 31 December, or 60 days after a supplemental notice", "Challenges the assessor's valuation", "The value stands for that lien date " + src("S16")],
  ],
  caption="These are statutory deadlines. No deadline is extended for hardship.",
  aligns=["", "", "", ""],
)}

<h2 id="costs">What the process itself costs</h2>
{table(
  ["Item", "Low", "High", "Notes"],
  [
    ["Trust and estate attorney", money(2500), money(15000), "Scales with the number of sub-trusts and whether a 706 is needed"],
    ["Appraisals, two houses", money(1000), money(3000), "Required for the date-of-death basis"],
    ["Form 706 preparation", money(3000), money(15000), "Only if a return is due or portability is elected"],
    ["Deed preparation and recording", money(200), money(900), "Per parcel"],
    ["Title insurance (on a later sale)", money(3000), money(8000), "Paid by the seller in Bay Area practice"],
    ["Selling costs, if selling", "5.0% of price", "5.0% of price", "Modelling assumption " + ASSUMED],
  ],
  caption="Order-of-magnitude costs in 2026 dollars. These are planning allowances, not quotes.",
  aligns=["", "r", "r", ""],
)}
<p class="muted">The cost figures in this table are planning allowances rather than verified prices; no
official source publishes a schedule of legal fees. They are marked as assumptions and are excluded from
the projection model, which models the transfer as cashless apart from selling costs and transfer tax.</p>

<h2 id="documents">The document file to build now</h2>
<ul>
<li>Certified death certificates &mdash; order 15.</li>
<li>The executed trust instrument, all amendments, and any schedule of assets.</li>
<li>Both property tax bills, most recent two years.</li>
<li>Both grant deeds, and any prior deeds showing the chain of title.</li>
<li>Homeowners' exemption records for whichever house is the parents' principal residence.</li>
<li>The solar interconnection agreement and net-metering tariff for the Cupertino house.</li>
<li>Both insurance policies, with the replacement-cost worksheets.</li>
<li>The two San Francisco leases, and the rent history for each tenancy.</li>
<li>Date-of-death brokerage and bank statements.</li>
</ul>
"""
    write("pages/inheritance-process.html", page(
        "Inheritance process, step by step",
        "Trust administration to recorded deed to assessor claim: the twenty steps, the four statutory deadlines, and what each one costs.",
        body, rel="../", current="pages/inheritance-process.html"))


# ================================================================ TAXES
def build_taxes():
    pl = M["prop19_lifetime"]
    est = M["estate"]

    # Prop 19 allowance periods (verified, S02)
    allowance_rows = [
        ["16 Feb 2021 &ndash; 15 Feb 2023", money(1000000), "Original statutory amount", VERIFIED + " " + src("S02")],
        ["16 Feb 2023 &ndash; 15 Feb 2025", money(1022600, exact=True), "First biennial adjustment", VERIFIED + " " + src("S02")],
        ["16 Feb 2025 &ndash; 15 Feb 2027", f"<strong>{money(1044586, exact=True)}</strong>", "FHFA California HPI +2.15% for 2024", VERIFIED + " " + src("S02")],
        ["16 Feb 2027 onwards", "not yet published", "Next adjustment February 2027", UNVERIFIED],
    ]

    est_rows = [[str(t["year"]), (money(t["single"]), "r"), (money(t["married_portable"]), "r"), t["basis"],
                 (money(max(0, t["single"] - (SC["A"]["prop19"]["cup"]["fmv"] if t["year"] == 2045 else 0))), "r")]
                for t in est["thresholds"]]

    body = f"""
<div class="toc"><strong>Contents</strong>
<ol>
<li><a href="#prop13">Property tax: Proposition 13</a></li>
<li><a href="#prop19">Property tax: Proposition 19 and inherited houses</a></li>
<li><a href="#estate">Estate and inheritance tax</a></li>
<li><a href="#gains">Capital gains, step-up basis and the home-sale exclusion</a></li>
<li><a href="#transfer">Documentary transfer tax</a></li>
<li><a href="#income">Income tax on rent</a></li>
</ol></div>

<h2 id="prop13">1. Property tax: Proposition 13</h2>
<p>Proposition 13 does three things:</p>
<ul>
<li>caps the general levy at <strong>1% of full cash value</strong>. This one lives in article XIII A of the
state constitution rather than in the statute, so the evidence here is the county rate books, which state
&ldquo;1% Maximum Tax Levy 1.00000&rdquo; for every tax rate area ({src('S09')} {src('S10')});</li>
<li>limits annual increases in assessed value to <strong>2%</strong> through an inflation factor at Revenue and
Taxation Code &sect;51(a)(1)(D), which provides that the increase shall in no event exceed 2% of the prior
year's value ({src('S17')});</li>
<li>reassesses to market value only on a <strong>change in ownership</strong> or new construction.</li>
</ul>
<p class="muted">Section 51 also makes the taxable value the <em>lesser</em> of the factored base year value and
current full cash value. That is the mechanical basis for a Proposition 8 temporary decline, which this model
never assumes and which is noted on the <a href="projections.html">projections page</a>.</p>
<p>The 1% is a cap, not a total. Voter-approved bond debt is added on top, and every parcel sits in a tax
rate area that determines which bonds apply. That is why two houses of equal value in the same county can
have different bills.</p>

<h3>Published rates</h3>
{table(
  ["Jurisdiction", "Rate applied to assessed value", "What it includes", "Source"],
  [
    ["Santa Clara County &mdash; Cupertino-area tax rate areas",
     pct(R["svc_rate"], 4),
     "1.00000 base + 0.03880 county retirement + Cupertino Elem 2001/2012/2024, El Camino Hospital 2003, Foothill-De Anza 1999, Fremont Union High 2008/2014/2018, SCVWD State Water Project",
     VERIFIED + " " + src("S09")],
    ["Santa Clara County &mdash; county-wide residential range",
     "1.08% &ndash; 1.30%",
     "Varies by tax rate area (816 areas in FY2025-26)", VERIFIED + " " + src("S09")],
    ["City and County of San Francisco",
     pct(R["sf_rate"], 6),
     "Combined secured rate for FY2025-26, $1.18268325 per $100. Includes Charter set-asides of $0.0250 Library, $0.0400 Children's Fund, $0.0250 Open Space per $100",
     VERIFIED + " " + src("S10")],
  ],
  caption="Rates are per $100 of assessed value, converted to percentages.",
  aligns=["", "r", "", ""],
)}

<div class="callout warn">
<span class="h">Reconciling the two owner-supplied bills against the published rates</span>
<p>The Cupertino bill implies <strong>{pct(P['cup']['eff_rate_reported'],4)}</strong>; the published component
list for Cupertino-area rate areas sums to <strong>{pct(R['svc_rate'],4)}</strong>. A difference of
{pct(P['cup']['eff_rate_reported']-R['svc_rate'],4)} on a {money(P['cup']['assessed_2026'])} base is about
{money((P['cup']['eff_rate_reported']-R['svc_rate'])*P['cup']['assessed_2026'])} a year. The gap is plausibly
one or more bond series not captured in the component list above.</p>
<p style="margin-bottom:0">The San Francisco bill implies <strong>{pct(P['sf']['eff_rate_reported'],4)}</strong>
against a published <strong>{pct(R['sf_rate'],6)}</strong>. At the published rate the bill would be
{money(P['sf']['assessed_2025']*R['sf_rate'])} rather than {money(P['sf']['tax_2025'])}. San Francisco does
impose fixed direct charges and special assessments, but they are dollar amounts per parcel, not a 0.95-point
add-on to the ad valorem rate. This one is not explained by the published documents.
<a href="flagged.html#sf-rate">See the flagged page &rarr;</a></p>
</div>

<h2 id="prop19">2. Property tax: Proposition 19 and inherited houses</h2>
<p>Proposition 19 ({src('S20')}) took effect for intergenerational transfers on <strong>16 February 2021</strong>.
It replaced Propositions 58 and 193. The change is summarised by the Board of Equalization as follows
({src('S01')}):</p>
{table(
  ["", "Before: Prop 58 / 193", "Now: Prop 19"],
  [
    ["Principal residence", "Principal residence of the transferor only; no value limit; residence and homesite", "Principal residence of <strong>both</strong> transferor and transferee; value limit of current taxable value plus the adjusted allowance"],
    ["Other real property", "Transferor lifetime limit of $1,000,000 of factored base year value", "<strong>Exclusion eliminated</strong> &mdash; rentals, second homes and commercial property are reassessed to market value"],
    ["Grandparent&ndash;grandchild", "Parent of the grandchild must be deceased", "No change"],
    ["Filing period", "Claim within 3 years or before transfer to a third party", "Homeowners' exemption within 1 year; exclusion claim within 3 years or before transfer to a third party"],
    ["Implementing statute", "Revenue and Taxation Code &sect;63.1", "Revenue and Taxation Code &sect;63.2"],
  ],
  caption="Prop 19 compared with the law it replaced (source: State Board of Equalization).",
  aligns=["", "", ""],
)}

<h3>The allowance, and how it is adjusted</h3>
<p>The allowance is adjusted every second 16 February by the prior calendar year's change in the FHFA House
Price Index for California ({src('S20')} &sect;2.1(c)(4)). The published values are:</p>
{table(["Transfer period", "Allowance added to the base", "Why", "Source"], allowance_rows,
       caption="Intergenerational transfer exclusion, adjusted $1,000,000 amount.",
       aligns=["", "r", "", ""])}

<h3>The formula</h3>
<p>Where the fair market value at the date of transfer exceeds the parent's factored base year value plus the
allowance, the excess is added to the base:</p>
<p class="mono" style="background:#f4f7f9;padding:12px 14px;border-radius:8px;border:1px solid var(--line)">
new taxable value = parent's factored base year value + max(0, market value &minus; (base + allowance))</p>
<p>Which simplifies, when the cap is exceeded, to <strong>market value minus the allowance</strong>. That is
why the allowance is the only number that matters for a high-value Bay Area house.</p>

<h3>Applied to these two houses, at 2045 values</h3>
{table(
  ["Line", "Cupertino 95014", "San Francisco 94122"],
  [
    ["Market value at transfer (2045 projection)", (money(SC["A"]["prop19"]["cup"]["fmv"]), "r"), (money(SC["A"]["prop19"]["sf"]["fmv"]), "r")],
    ["Parents' factored base year value (2%/yr from 2026)", (money(SC["A"]["prop19"]["cup"]["fbyv"]), "r"), (money(SC["A"]["prop19"]["sf"]["fbyv"]), "r")],
    ["Allowance (indexed at 3.5%/yr)", (money(SC["A"]["prop19"]["cup"]["allowance"]), "r"), (money(SC["A"]["prop19"]["sf"]["allowance"]), "r")],
    ["Cap = base + allowance", (money(SC["A"]["prop19"]["cup"]["cap"]), "r"), (money(SC["A"]["prop19"]["sf"]["cap"]), "r")],
    ["New taxable value if the exclusion applies and you move in", (f"<strong>{money(SC['A']['prop19']['cup']['new_base'])}</strong>", "r"), (f"<strong>{money(SC['B']['prop19']['sf']['new_base'])}</strong>", "r")],
    ["New taxable value if the exclusion does not apply", (money(SC["B"]["prop19"]["cup"]["new_base"]), "r"), (money(SC["A"]["prop19"]["sf"]["new_base"]), "r")],
    ["Annual property tax, exclusion applied", (money(pl["cup"]["new_base_if_excluded"] * P["cup"]["eff_rate_reported"]), "r"), (money(pl["sf"]["new_base_if_excluded"] * R["sf_rate"]), "r")],
    ["Annual property tax, no exclusion", (money(pl["cup"]["new_base_if_full"] * P["cup"]["eff_rate_reported"]), "r"), (money(pl["sf"]["new_base_if_full"] * R["sf_rate"]), "r")],
    ["Annual saving from the exclusion", (f"<strong>{money(pl['cup']['annual_saving_first_year'])}</strong>", "r"), (f"<strong>{money(pl['sf']['annual_saving_first_year'])}</strong>", "r")],
    ["Saving over 21 years, base growing at the Prop 13 cap", (f"<strong>{money(pl['cup']['twenty_one_year_saving'])}</strong>", "r"), (f"<strong>{money(pl['sf']['twenty_one_year_saving'])}</strong>", "r")],
  ],
  caption="Worked application. The exclusion applies to whichever house was the parents' principal residence and "
          "which you occupy within one year; both columns show the position if that house is the one you take.",
  aligns=["", "r", "r"],
)}
<p class="muted">The San Francisco column assumes the exclusion is available for that building. It is only
available if the building &mdash; not Cupertino &mdash; was the parents' principal residence
(<a href="flagged.html#occupancy">flagged item 3</a>).</p>

<h3>What disqualifies a claim</h3>
<ul>
<li>The house was not the transferor's principal residence.</li>
<li>You do not make it your principal residence within one year, or you do not claim the homeowners'
exemption ({src('S01')}).</li>
<li>The claim is filed after three years, or after the property is sold.</li>
<li>The property is a rental on the date of transfer. Prop 19 removed the exclusion for everything other
than a principal residence and certain family farms.</li>
</ul>

<h2 id="estate">3. Estate and inheritance tax</h2>
<div class="callout good">
<span class="h">California: no estate tax, no inheritance tax</span>
<p style="margin-bottom:0">Proposition 6 (June 1982) eliminated California's inheritance and gift tax. The
residual state "pick-up" tax produced no revenue for decedents dying after 2004, and the LAO states plainly
that "California does not currently impose any estate taxes on estates of decedents dying after 2004"
({src('S06')}). The Franchise Tax Board confirms that the Revenue and Taxation Code bars the state from
imposing estate and gift taxes without a voter-approved constitutional amendment ({src('S07')}).</p>
</div>
<p>The only death tax that can reach a California resident is the <strong>federal</strong> estate tax.</p>

<h3>Federal thresholds</h3>
{table(
  ["Year", "Basic exclusion, one person", "Married couple with portability", "Basis", "Estate value left before any federal tax (2045 houses deducted)"],
  [[r[0], r[1], r[2], r[3], (r[4] if r[0] == "2045" else "&mdash;")] for r in est_rows],
  caption="2026 is verified (S03). Later years index the verified $15,000,000 at an assumed 2.5%/yr and are "
          "projections, not law.",
  aligns=["", "r", "r", "", "r"],
)}
<p>The federal rate above the exclusion is <strong>40%</strong> ({src('S03')}). The annual gift exclusion for
2026 is {money(19000)} per recipient; gifts within it never touch the lifetime exclusion.</p>

<h3>What this means for an inheritance that includes "a considerable amount of money"</h3>
<ul>
<li>On current law and a 2026 death, nothing is due until the estate exceeds
<strong>{money(15000000)}</strong> for a single person or {money(30000000)} for a married couple with
portability.</li>
<li>The two houses are projected at {money(SC['A']['prop19']['cup']['fmv'] + SC['A']['prop19']['sf']['fmv'])}
in 2045. Against an indexed single-person exclusion of
{money(M['estate']['thresholds'][4]['single'])}, that leaves roughly
<strong>{money(M['estate']['thresholds'][4]['single'] - (SC['A']['prop19']['cup']['fmv'] + SC['A']['prop19']['sf']['fmv']))}</strong>
of cash before a return is required.</li>
<li>An <strong>inheritance</strong> is not income. Nothing is reported on your 1040 simply because you
received cash or property. What is taxed later is the income those assets produce and the gain on assets
sold after the step-up.</li>
<li>Two planning points that are worth more than the tax: <strong>elect portability</strong> on a timely
Form 706 even when no tax is due, and <strong>do not gift the houses</strong> during life
(<a href="#gains">see below</a>).</li>
</ul>

<h2 id="gains">4. Capital gains, step-up basis, and the home-sale exclusion</h2>
<p>Property acquired from a decedent has a basis equal to its fair market value at the date of death
({src('S18')}). Everything the parents' estate gained is erased for income-tax purposes.</p>
{table(
  ["", "Amount", "What it means"],
  [
    ["Appreciation between 2026 and 2045 that never meets a capital-gains tax", (money(M["stepup"]["pre_inheritance_appreciation"]), "r"), "Both houses, 4%/yr projection"],
    ["Blended rate assumed on realised long-term gain", (pct(M["stepup"]["rate_assumed"], 1), "r"), "Federal 20% + 3.8% NIIT + California 13.3%"],
    ["Tax avoided because the basis steps up", (f"<strong>{money(M['stepup']['tax_avoided'])}</strong>", "r"), "On the 2026&ndash;2045 appreciation alone"],
  ],
  caption="Value of the step-up. The gain accrued before 2026 is erased too, and is not included here.",
  aligns=["", "r", ""],
)}

<h3>If you later sell a house you have lived in</h3>
<p>Up to <strong>$250,000</strong> of gain ($500,000 on a joint return) can be excluded if you owned and used
the house as your main home for at least 24 of the last 60 months ({src('S05')}). Because the basis has
already stepped up, the gain to be sheltered is usually modest.</p>

<h3>If you later sell a house you have rented</h3>
<p>Depreciation taken while letting the property reduces the basis and is recaptured on sale. The model
charges 25% federal on the recaptured amount plus California tax on it as ordinary income, and the blended
rate on the rest.</p>

<h2 id="transfer">5. Documentary transfer tax</h2>
{table(
  ["Entire consideration or value", "Rate per $500", "Effective rate on the whole price"],
  [[("<$250,000" if t["from"] == 100 else money(t["from"]) + " &ndash; " + (money(t["to"]) if t["to"] else "and above")),
    f"${t['per_500']:.2f}", (pct(t["pct"] / 100, 4), "r")] for t in R["sf_transfer_tiers"]],
  caption="San Francisco documentary transfer tax. The tier's rate applies to the entire consideration, not to "
          "the slice above the threshold (" + src("S11") + ").",
  aligns=["", "r", "r"],
)}
<p><strong>Santa Clara County</strong> charges the standard $0.55 per $500 of consideration set under the
Documentary Transfer Tax Act ({src('S23')}), i.e. 0.11%. {UNVERIFIED} &mdash; the county's current adopted rate
and the absence of any Cupertino city transfer tax were not read from the county's or city's own fee schedule;
the 0.11% figure is the statutory default used in the model. A {money(SC['F']['sale_at_inheritance']['cup']['price'])} sale of the Cupertino house
therefore carries {money(SC['F']['sale_at_inheritance']['cup']['transfer_tax'])} of transfer tax; the San
Francisco building at the same price would carry
{money(SC['F']['sale_at_inheritance']['cup']['price'] * 0.0225)}.</p>
<div class="callout warn">
<span class="h">The cliff at $5,000,000</span>
<p style="margin-bottom:0">A San Francisco sale at $4,990,000 is taxed at 0.75%, or about $37,430. A sale at
$5,000,000 is taxed at 2.25%, or $112,500. One dollar of price costs $75,070 of tax. Projected values put the
Outer Sunset building above $5,000,000 by about 2052 &mdash; which matters if you plan to sell it later rather
than at inheritance.</p>
</div>

<h2 id="income">6. Income tax on rent</h2>
<p>Rental income is taxable. The model assumes a blended marginal rate of 45.1% on net positive rental income
(federal 32% + 3.8% net investment income tax ({src('S19')}) + California 9.3%), with no benefit taken for
passive losses, which are generally suspended at higher income levels. Depreciation is modelled on a 27.5-year
straight line applied to the building portion only, and California is <em>assumed</em> to conform.</p>
<div class="callout warn">
<span class="h">What is verified here and what is not</span>
<p style="margin-bottom:0">The 3.8% net investment income tax and its thresholds are verified ({src('S19')}),
including the rule that a gain excluded under the home-sale provision is not net investment income. The
45.1% marginal stack, the 27.5-year period and the state-conformity assumption are <strong>modelling
choices</strong>, not verified outcomes for your situation. They are stated here rather than buried because
they affect the rental plans more than they affect plan F.</p>
</div>
"""
    write("pages/taxes.html", page(
        "Taxes &amp; law",
        "Proposition 13, Proposition 19 and the $1,044,586 allowance, the federal estate tax, California's absence of an inheritance tax, step-up basis and transfer tax.",
        body, rel="../", current="pages/taxes.html"))
