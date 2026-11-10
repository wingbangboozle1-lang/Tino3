#!/usr/bin/env python3
"""pages_c.py — decision analysis, risks, sources, flagged."""

import json
from site_lib import (M, money, plain, pct, src, table, page, write, pager,
                      VERIFIED, REPORTED, ASSUMED, UNVERIFIED, badge)
from sources import SOURCES

A = M["assumptions"]
R = M["rates"]
P = {p["key"]: p for p in M["properties"]}
SC = {s["short"]: s for s in M["scenarios_parent_cup"]}
SC_SF = {s["short"]: s for s in M["scenarios_parent_sf"]}


# ======================================================= DECISION ANALYSIS
def build_decision():
    ranked = sorted(M["scenarios_parent_cup"], key=lambda s: -s["total_terminal_wealth"])

    rows = []
    for s in ranked:
        rows.append(([
            f"<strong>{s['short']}</strong>",
            s["name"].split(". ", 1)[1],
            (money(s["tax_at_inheritance"].get("cup", 0) + s["tax_at_inheritance"].get("sf", 0)) if s["tax_at_inheritance"] else "&mdash;", "r"),
            (money(s["first_year_cashflow"]), "r"),
            (money(s["cumulative_cashflow"]), "r"),
            (money(sum(v["net"] for v in s["terminal_sales"].values())) if s["terminal_sales"] else "&mdash;", "r"),
            (money(s["terminal_portfolio"]), "r"),
            (f"<strong>{money(s['total_terminal_wealth'])}</strong>", "r"),
        ], "hl" if s["short"] == "F" else ""))

    # cash flow detail for A and F
    det = []
    for yr in (2045, 2050, 2055, 2060, 2065):
        a = next(c for c in SC["A"]["cashflows"] if c["year"] == yr)
        f = next(c for c in SC["F"]["cashflows"] if c["year"] == yr)
        det.append([str(yr),
                    (money(a["rent"]), "r"), (money(a["opex"]), "r"), (money(a["proptax"]), "r"), (money(a["net"]), "r"),
                    (money(f["rent"]), "r"), (money(f["opex"]), "r"), (money(f["proptax"]), "r"), (money(f["net"]), "r")])

    # robustness grid
    grid_rows = []
    for r in M["grid"]:
        w = r["wealth"]
        grid_rows.append([
            pct(r["g"], 0), pct(r["inv"], 0),
            (money(w["A"]), "r"), (money(w["B"]), "r"), (money(w["C"]), "r"),
            (money(w["D"]), "r"), (money(w["E"]), "r"), (f"<strong>{money(w['F'])}</strong>", "r"),
            (f"<strong>{r['best']}</strong>", "c"),
        ])

    # prop19 detail per scenario
    p19_rows = []
    for s in M["scenarios_parent_cup"]:
        for k in ("cup", "sf"):
            v = s["prop19"].get(k)
            if not v:
                continue
            p19_rows.append([
                s["short"], "Cupertino" if k == "cup" else "San Francisco",
                (money(v["fmv"]), "r"), (money(v["fbyv"]), "r"), (money(v["cap"]), "r"),
                (money(v["new_base"]), "r"),
                badge("applied", "ok") if v["exclusion_applied"] else badge("not applied", "unv"),
            ])

    body = f"""
<p class="lede">Six plans, each run from 2045 to 2065 on identical assumptions. The only things that change are
which house you occupy, which house you let, and which you sell. Everything else &mdash; growth, inflation,
returns, tax rates &mdash; is held constant so the comparison is clean.</p>

<div class="callout">
<span class="h">Method, in one paragraph</span>
<p style="margin-bottom:0">Each year, rent received is reduced by property tax, insurance, water, electricity,
maintenance and income tax. Where you do not occupy an inherited house, market rent for an equivalent house is
subtracted, so every plan buys the same standard of housing. The resulting annual cash flow is invested at
{pct(A['g_invest'],1)} nominal; the 2% income component is taxed each year. At 2065 any remaining house is sold
with 5% selling costs, documentary transfer tax, capital gains on the post-inheritance gain and depreciation
recapture, and the portfolio is liquidated and taxed on unrealised gains. The result is a single number:
after-tax wealth at the end of 2065.</p>
</div>

<h2 id="results">Results</h2>
{table(
  ["", "Plan", "Property tax, first year", "After-tax cash flow, first year", "Cumulative cash flow 2045&ndash;2065",
   "Terminal house sales, net", "Invested portfolio at 2065", "Terminal after-tax wealth"],
  rows,
  caption="All six plans. Cupertino treated as the parents' principal residence. Sorted by terminal after-tax wealth.",
  aligns=["", "", "r", "r", "r", "r", "r", "r"],
)}
<p class="muted">A negative &ldquo;invested portfolio&rdquo; is not a debt: it is the cumulative amount of
outside cash the plan requires, because property tax and running costs exceed the rent it collects. Plan A
needs about {money(-SC['A']['cumulative_cashflow'])} of outside funding over twenty years.</p>
<div class="callout">
<span class="h">Why the ranking uses terminal wealth rather than a discounted present value</span>
<p style="margin-bottom:0">A present-value ranking depends entirely on the discount rate chosen, and this model
already assumes the alternative is a portfolio earning {pct(A['g_invest'],1)}. Discounting at that same rate
makes every plan's present value collapse into a restatement of its terminal wealth, so nothing is added.
Discounting at a lower rate would silently assume you could borrow at that rate to fund the negative
cash-flow years. Terminal after-tax wealth is the one number that needs no such choice, so it is the ranking
metric throughout. The present values are still computed and stored in the model file for audit.</p>
</div>

<h3>The same table, explained</h3>
<dl>
<dt><strong>A. Live in Cupertino, rent all three San Francisco units</strong></dt>
<dd>The plan the brief implies. It preserves the Prop 19 exclusion on Cupertino &mdash;
{money(M['prop19_lifetime']['cup']['annual_saving_first_year'])} a year of tax avoided &mdash; and it captures
the full rent on the San Francisco building. But the combined property tax of
{money(SC['A']['tax_at_inheritance']['cup'] + SC['A']['tax_at_inheritance']['sf'])} exceeds the net rent, so
the plan runs a cash deficit of about {money(-SC['A']['first_year_cashflow'])} a year from day one.</dd>

<dt><strong>B. Live in San Francisco, rent Cupertino</strong></dt>
<dd>Cupertino loses its exclusion because you do not occupy it, so its tax rises by
{money(M['prop19_lifetime']['cup']['annual_saving_first_year'])}. In exchange, Cupertino produces rent and you
occupy a unit in a building you already own. This is the best plan if the portfolio return turns out low,
because it keeps both houses appreciating.</dd>

<dt><strong>C. Rent both, rent somewhere else</strong></dt>
<dd>Worst of the six. You pay market rent for housing, lose the exclusion on both houses, and pay tax on both
rent streams. Renting equivalent housing at a 3% gross yield is structurally worse than owning it.</dd>

<dt><strong>D. Sell both, invest, rent</strong></dt>
<dd>Cleanest balance sheet and the lowest concentration risk, but it ranks fifth. The reason is not tax &mdash;
selling at death is nearly tax-free &mdash; it is that you convert two appreciating assets into a taxable
portfolio while taking on a rent liability that grows every year.</dd>

<dt><strong>E. Live in Cupertino, sell San Francisco</strong></dt>
<dd>Gives up the highest-yielding asset in the portfolio. Fourth of six.</dd>

<dt><strong>F. Live in San Francisco, sell Cupertino</strong></dt>
<dd>First of six. Sells the low-yield, tax-heavy asset at a stepped-up basis ({src('S18')}) with almost no
capital-gains consequence ({money(SC['F']['sale_at_inheritance']['cup']['capital_gains_tax'])} of tax on a
{money(SC['F']['sale_at_inheritance']['cup']['price'])} sale, the residue being California's 0.11% county
transfer tax), keeps the building that produces cash, and occupies the vacant unit so housing costs nothing
beyond the rent forgone on that one unit.</dd>
</dl>

<h2 id="detail">Year-by-year cash flow, plans A and F</h2>
{table(
  ["Year", "A rent", "A costs", "A property tax", "A net", "F rent", "F costs", "F property tax", "F net"],
  det,
  caption="Selected years. &ldquo;Costs&rdquo; is insurance, water, electricity and maintenance. Income tax is "
          "zero in both plans in these years because depreciation and operating costs absorb the rental income.",
  aligns=["", "r", "r", "r", "r", "r", "r", "r", "r"],
)}
<p>Plan A's net position deteriorates because operating costs are tied to market value (maintenance) and to
construction inflation (insurance), while rent is capped: two of the three San Francisco tenancies are
rent-controlled and escalate at 1.6% a year. Plan F stays positive far longer because it carries only one
building and has {money(SC['F']['sale_at_inheritance']['cup']['net'])} working for it.</p>

<h2 id="prop19">The Proposition 19 position in each plan</h2>
<p class="muted">The cap in this table is the parents' factored base year value plus the biennially adjusted
allowance ({src('S01')} {src('S02')}). The exclusion applies only where the house was the transferor's principal
residence and the transferee moves in within one year and claims the homeowners' exemption ({src('S16')}).</p>
{table(
  ["Plan", "Property", "Market value 2045", "Parents' base", "Cap (base + allowance)", "New taxable value", "Exclusion"],
  p19_rows,
  caption="Whether the exclusion applies, and what it is worth, in each plan. It applies only where the house "
          "was the parents' principal residence <em>and</em> you occupy it within one year.",
  aligns=["", "", "r", "r", "r", "r", ""],
)}
<p>Notice what this table makes plain: the exclusion is worth having, but it is worth
{money(M['prop19_lifetime']['cup']['annual_saving_first_year'])} a year &mdash; not the difference between a
${plain(SC['A']['tax_at_inheritance']['cup'])} and a ${plain(P['cup']['tax_2026'])} bill. Prop 19 does not
restore the parents' tax level on a house this far below market value. The allowance is simply too small
relative to the gap.</p>

<h2 id="grid">Robustness: nine combinations of growth and return</h2>
<p class="muted">The growth rates tested span the range implied by the FHFA California house price index
({src('S14')}); the return rates span a conventional 60/40 expected range. Neither is a published forecast,
because no official body publishes one.</p>
{table(
  ["House growth", "Portfolio return", "A", "B", "C", "D", "E", "F", "Winner"],
  grid_rows,
  caption="Terminal after-tax wealth in 2065. The recommendation is not an artefact of one set of assumptions.",
  aligns=["", "", "r", "r", "r", "r", "r", "r", "c"],
)}
<div class="callout good">
<span class="h">What the grid shows</span>
<p style="margin-bottom:0">Plan F wins <strong>eight of nine</strong> combinations. It loses only at a 4%
portfolio return &mdash; the case where keeping and renting Cupertino (B) edges ahead, because the house's own
appreciation does more work than the investments. No combination makes selling both and renting (D) the best
answer, and no combination makes renting both houses (C) competitive.</p>
</div>

<h2 id="flip">If the parents actually live in San Francisco</h2>
<p>The base case assumes Cupertino is the parents' principal residence. If it is the other way round, the
Prop 19 exclusion attaches to the San Francisco building instead, and the ranking shifts:</p>
{table(
  ["Plan", "Terminal wealth, Cupertino is the home", "Terminal wealth, San Francisco is the home", "Change"],
  [[k, (money(SC[k]["total_terminal_wealth"]), "r"),
    (money(SC_SF[k]["total_terminal_wealth"]), "r"),
    (money(SC_SF[k]["total_terminal_wealth"] - SC[k]["total_terminal_wealth"]), "r")]
   for k in sorted(SC, key=lambda x: -SC_SF[x]["total_terminal_wealth"])],
  caption="The same six plans with the occupancy assumption reversed.",
  aligns=["", "r", "r", "r"],
)}
<p>The effect is modest &mdash; a few hundred thousand dollars on a twenty-million-dollar outcome &mdash; and
the winner does not change. That is a useful result: <strong>the recommendation does not depend on resolving
the occupancy question</strong>, even though the property-tax projection does.</p>

<h2 id="judgement">What the model cannot tell you</h2>
<ul>
<li><strong>Whether you want to be a landlord.</strong> Plan F still leaves one building with two tenants.
If the answer is no, plan D is the only plan that avoids it entirely, and it costs roughly
{money(SC['F']['total_terminal_wealth'] - SC['D']['total_terminal_wealth'])} in terminal wealth.</li>
<li><strong>Concentration.</strong> Plan F puts
{pct(SC['A']['prop19']['sf']['fmv'] / (SC['A']['prop19']['sf']['fmv'] + SC['F']['sale_at_inheritance']['cup']['net']), 0)}
of the estate into one three-unit building in one ZIP code. Diversification has a value the model does not
price.</li>
<li><strong>Liquidity and optionality.</strong> A portfolio can be partly sold; a house cannot.</li>
<li><strong>Sentiment.</strong> The family home may be worth more to you than the numbers say. That is a
legitimate input the model cannot accept.</li>
<li><strong>Future tax law.</strong> Every rate in this model is today's rate.
<a href="risks.html">See the risk register &rarr;</a></li>
</ul>
"""
    write("pages/decision-analysis.html", page(
        "Decision analysis",
        "Six plans, twenty years of after-tax cash flow, nine growth-and-return combinations, and the reasoning behind the recommendation.",
        body, rel="../", current="pages/decision-analysis.html"))


# ================================================================= RISKS
def build_risks():
    body = f"""
<p class="lede">A projection twenty years out is a statement about assumptions, not about the future. This page
separates the risks that would change the <em>numbers</em> from the ones that would change the
<em>ranking</em>, and records what is currently being proposed in Sacramento and Washington.</p>

<h2>Law changes: what is actually happening</h2>

<h3>Proposition 19 repeal &mdash; failed, and not pending</h3>
<div class="callout">
<p>A third attempt to repeal Prop 19's inheritance provisions was circulated as
<em>"Repeals voter-enacted changes to property tax rules for transfers between family members"</em> (summary
date 6 November 2025). On <strong>18 May 2026</strong> the Secretary of State recorded that the petition had
<strong>failed</strong>: the number of signatures filed across all counties was below the requirement
({src('S12')}).</p>
<p style="margin-bottom:0">Nothing is therefore pending. Prop 19 remains fully in force, and the analysis
throughout this site uses current law. A future repeal would restore the pre-2021 rules, under which the
parent's principal residence could pass with no value limit and no residency requirement &mdash; but it would
not, by itself, restore the exclusion for the San Francisco rental, because the old Prop 58/193 regime for
other real property was itself capped at $1,000,000 of factored base year value.</p>
</div>

<h3>Ending the step-up in basis at the state level &mdash; proposed, not enacted</h3>
<div class="callout warn">
<p>The Governor's 2024-25 budget package proposed ending the step-up in basis for inherited assets
<em>for California income tax purposes</em>, for inheritances received after 1 July 2024. The Legislative
Analyst's Office scored it as raising a few hundred million dollars a year ({src('S08')}).</p>
<p style="margin-bottom:0">It was not enacted. It matters here more than any other proposal on this page: the
step-up is worth roughly {money(M['stepup']['tax_avoided'])} on the 2026&ndash;2045 appreciation alone, and a
state-level repeal would make Plan F materially less attractive than the model shows, because Plan F depends
on selling at a stepped-up basis.</p>
</div>

<h3>The federal estate tax</h3>
<p>The 2025 federal law set the basic exclusion at {money(15000000)} per person from 2026 and removed the
scheduled sunset, indexing it for inflation thereafter ({src('S03')}). "Permanent" here means only that it has
no expiry date; a future Congress can change it. A reduction back toward half that level would put the
projected 2045 estate &mdash; {money(SC['A']['prop19']['cup']['fmv'] + SC['A']['prop19']['sf']['fmv'])} in
houses plus cash &mdash; within reach of a federal tax at 40%.</p>

<h3>A California estate or wealth tax &mdash; not enacted</h3>
<p>California imposes no estate, inheritance or wealth tax ({src('S06')} {src('S07')}). Proposals for each have
been introduced in earlier legislative sessions and none has been enacted; a state estate tax would require a
constitutional amendment approved by the voters, because the Revenue and Taxation Code currently bars one.
{UNVERIFIED} &mdash; the status of any bill in the current session was not checked against the Legislature's
bill database, so this entry is recorded as unverified rather than asserted.</p>

<h3>Insurance market and the FAIR Plan</h3>
<p>The FAIR Plan has grown sharply and has levied assessments on member insurers after major wildfire losses
({src('S15')}). Two consequences for these properties: premiums should be expected to keep rising faster than
inflation, and a property that is currently insurable in the admitted market may not stay that way. Neither
house is in a high fire-hazard severity zone, which is protective, but a single repricing event can double a
premium. The model escalates insurance at CPI plus two points, which may prove optimistic.</p>

<h3>Rent control &mdash; with a live proposal</h3>
<p>The San Francisco Rent Ordinance caps annual increases on the two sitting tenancies at 1.6% for 2026-27
({src('S13')}). There is also a <strong>specific proposal pending</strong>: on 9 November 2026 the Rent Board
posted notice that the Board of Supervisors is considering File No. 261020, which would temporarily limit the
combined amount of banked and capital-improvement increases that may be imposed on rent-controlled units to
<strong>10% per year</strong>. The notice itself states the legislation has <em>not</em> been enacted
({src('S13')}).</p>
<p>Anything that further tightens rent control reduces the rent stream that makes the San Francisco building
the better asset. That would weaken Plan F and strengthen the case for selling both.</p>
<p class="muted">The model assumes the two sitting tenancies escalate at 1.6% indefinitely. That is
conservative: a vacant unit can be reset to market, and banked increases are available within the
ordinance's rules.</p>

<h2>Risk register</h2>
{table(
  ["Risk", "Likelihood", "Effect on the numbers", "Effect on the ranking", "Monitoring"],
  [
    ["Parents' principal residence turns out to be the San Francisco house",
     "Unknown &mdash; a fact, not a risk", "Moves the Prop 19 exclusion between properties",
     "No change &mdash; F still wins", "Homeowners' exemption record on each parcel " + src("S16")],
    ["Portfolio returns 4% rather than 6% over 20 years",
     "Plausible", "Lowers every plan's terminal wealth",
     "<strong>Reverses</strong> F and B", "The robustness grid on the decision page"],
    ["Bay Area house prices grow 3% rather than 4%",
     "Plausible", "Lowers terminal wealth materially", "No change &mdash; F still wins", "FHFA HPI " + src("S14")],
    ["State-level repeal of step-up basis",
     "Low at present", "Raises the tax on selling Cupertino at inheritance",
     "Weakens F and D; favours holding", "LAO publications " + src("S08")],
    ["Prop 19 repeal passes",
     "Failed in 2026", "Reduces Cupertino's post-inheritance tax",
     "Strengthens A and E", "Secretary of State initiative status " + src("S12")],
    ["Insurance repricing or non-renewal",
     "Moderate", "Raises annual costs by thousands per year", "No effect at these magnitudes", "Annual re-quote " + src("S15")],
    ["A sitting tenant vacates",
     "Moderate over 20 years", "Raises rent to market &mdash; increases income", "Strengthens both hold plans", "Lease files"],
    ["Major capital item (roof, sewer, seismic) on the San Francisco building",
     "High over 20 years", "A one-off cost of $50,000&ndash;$300,000, not modelled", "Small", "Inspection before the transfer"],
    ["Federal estate exemption reduced",
     "Low &ndash; moderate", "40% of the excess over the exclusion", "No change", "IRS annually " + src("S03")],
    ["Property tax rate rises as new bonds pass",
     "High", "Every post-inheritance tax figure rises proportionally", "No change", "County rate book annually " + src("S09") + " " + src("S10")],
  ],
  caption="Risk register. Likelihood judgements are editorial; the effects are modelled or reasoned.",
  aligns=["", "", "", "", ""],
)}

<h2>What would make the recommendation wrong</h2>
<ol>
<li><strong>A sustained low return on capital.</strong> Below roughly 5% nominal on a diversified portfolio,
keeping and renting Cupertino overtakes selling it. This is the only single-variable change in the tested range
that reverses the ranking.</li>
<li><strong>A decision not to be a landlord at all.</strong> Then the choice is between D and E, and the
differences among the remaining plans are small relative to the value of not having tenants.</li>
<li><strong>Information not in evidence.</strong> If the San Francisco building needs seismic or sewer work
that has not been done, or if a tenancy is not in fact rent-controlled, the yield that justifies keeping it
disappears.</li>
</ol>
"""
    write("pages/risks.html", page(
        "Risks and pending law changes",
        "What is being proposed in Sacramento and Washington, what has already failed, and how much each change would move the numbers.",
        body, rel="../", current="pages/risks.html"))


# =============================================================== SOURCES
def build_sources():
    rows = []
    for s in SOURCES:
        rows.append([
            f'<a id="{s["id"]}"></a><strong>{s["id"]}</strong>',
            s["publisher"],
            f'<a href="{s["url"]}" rel="noopener">{s["title"]}</a>',
            s["type"],
            s["proves"],
            badge("verified", "ok") if s["verified"] else badge("unverified", "unv"),
        ])
    body = f"""
<p class="lede">Every citation on this site resolves to an entry in this register. Each entry states, narrowly,
what the source supports &mdash; not a summary of the document, but the specific proposition relied on.</p>

<div class="callout">
<span class="h">Verification standard</span>
<p style="margin-bottom:0"><strong>Verified</strong> means the page or document was read directly from the
publisher on {M['meta']['build_date']} and the quoted rule, rate or figure appears in it. Anything that could
not be matched is on the <a href="flagged.html">Flagged for review</a> page and is not presented as fact
anywhere else on this site. Owner-supplied figures are labelled <em>reported</em> and are never described as
verified. Modelling inputs are labelled <em>assumption</em>.</p>
</div>

<h2>Register</h2>
{table(
  ["Ref", "Publisher", "Document", "Type", "What it establishes", "Status"],
  rows,
  caption=f"{len(SOURCES)} sources.",
  aligns=["", "", "", "", "", ""],
)}

<h2>Sources deliberately not used</h2>
<ul>
<li><strong>Automated valuation estimates</strong> (Zillow, Redfin and similar). They are not official, they
carry error bands that are large relative to the tax differences being discussed, and they cannot be cited for
an assessed value.</li>
<li><strong>Blog posts and law-firm marketing pages</strong> describing Prop 19. Several were read while
locating the underlying rules; where they agreed with the Board of Equalization, the Board's own guidance is
cited instead.</li>
<li><strong>County assessor parcel records.</strong> Not used, because publishing a parcel identifier would
compromise the anonymity requirement.</li>
</ul>

<h2>How to re-verify this site</h2>
<ol>
<li>Every table row carries a <span class="srclink">Sxx</span> chip. Click it to reach the register entry,
then the source itself.</li>
<li>Every calculated figure is produced by <span class="mono">tools/model.py</span>, committed in the
repository. Run <span class="mono">python3 tools/model.py</span> and compare
<span class="mono">data/model.json</span> against the published tables.</li>
<li>The assumptions are in a single dictionary at the top of that file, each one labelled and commented.</li>
</ol>
"""
    write("pages/sources.html", page(
        "Source register",
        "Every citation used on this site, with what each source establishes and when it was checked.",
        body, rel="../", current="pages/sources.html"))


# =============================================================== FLAGGED
def build_flagged():
    items = [
        ("sf-rate", "San Francisco owner-reported tax does not reconcile with the City's published rate",
         "Material",
         f"The 2025 bill of {money(2439)} against an assessed value of {money(114248)} implies an effective rate "
         f"of <strong>{pct(P['sf']['eff_rate_reported'],2)}</strong>. San Francisco's published FY2025-26 secured "
         f"rate is <strong>{pct(R['sf_rate'],6)}</strong> ({src('S10')}), which on that assessment produces "
         f"<strong>{money(P['sf']['assessed_2025']*R['sf_rate'])}</strong>. The gap is about "
         f"{money(2439 - P['sf']['assessed_2025']*R['sf_rate'])} a year.",
         "The assessed-value column may be land only; the tax column may cover more than one parcel; or the two "
         "series may not come from the same property. San Francisco does impose fixed direct charges and special "
         "assessments, but those are dollar amounts per parcel, not a 0.95-point addition to the ad valorem rate.",
         "Post-inheritance projections use the <em>published</em> rate; the reported bill is used only for the "
         "current cash cost. If the true ad valorem rate is closer to 2.13%, every San Francisco tax figure after "
         "inheritance in this analysis is understated by roughly 45%."),
        ("cup-rate", "Cupertino owner-reported tax implies a rate above the published component sum",
         "Low",
         f"The bill of {money(7207)} against an assessment of {money(550537)} implies "
         f"<strong>{pct(P['cup']['eff_rate_reported'],4)}</strong>. The Santa Clara County 2025-26 rate book "
         f"components attributable to Cupertino-area tax rate areas sum to {pct(R['svc_rate'],4)} "
         f"({src('S09')}).",
         "The most likely explanation is a bond series in the parcel's specific tax rate area that was not "
         "captured when the components were summed, or fixed direct assessments added to the ad valorem tax.",
         "The reported rate is used for Cupertino projections, because the bill is direct evidence of what this "
         "parcel actually pays. The difference is about "
         f"{money((P['cup']['eff_rate_reported']-R['svc_rate'])*P['cup']['assessed_2026'])} a year at the 2026 base."),
        ("occupancy", "Which house is the parents' principal residence is not stated",
         "High",
         "Proposition 19 relief attaches only to the <em>transferor's</em> principal residence "
         f"({src('S01')}). The brief describes both houses but does not say where the parents live.",
         "The base case assumes Cupertino. Every scenario is also run with the assumption reversed, and both "
         "sets of results are published.",
         "The property-tax projections change materially; the plan ranking does not. Resolve it from the "
         "homeowners' exemption record on each parcel roll " + src('S16') + "."),
        ("insurance", "Insurance estimates are unverified and likely understated",
         "High",
         f"The owner estimates $1,500 a year for each property. The Department of Insurance's 2025 "
         f"experience-year statewide average is {money(2340)} across all homeowners forms ({src('S15')}). "
         "No official ZIP-level premium exists for either 95014 or 94122.",
         "A $3,100,000 single-family house and a three-unit pre-1979 building both need dwelling limits far "
         "above the state average; but neither sits in a high fire-hazard severity zone, which suppresses the "
         "premium relative to the FAIR Plan average.",
         f"The model uses {money(2340)} as a floor. This is the largest unresolved cost input. It moves annual "
         "cash flow but not the ranking. Obtain quotes."),
        ("solar", "Solar net-metering tariff for the Cupertino house is unverified",
         "Medium",
         "The owner reports that electricity is usually a net credit of about $10&ndash;$20 a month.",
         "Whether an array earns export credit, and at what rate, depends on the tariff it was interconnected "
         "under and on the utility's filed rates. California has moved newer interconnections onto materially "
         "less generous terms.",
         "The model carries the credit at its reported value and does not compound it into a growing benefit. "
         "A tariff change would make Cupertino cost slightly more to occupy."),
        ("appreciation", "The long-run appreciation rate is an assumption, not a verified figure",
         "High",
         "The model assumes " + pct(A['g_market'],1) + " nominal annual appreciation for Bay Area houses and "
         + pct(A['g_invest'],1) + " for a diversified portfolio.",
         "The FHFA California house price index (" + src('S14') + ") publishes <em>past</em> change; the FHFA "
         "does not forecast. No official body publishes a 2045 house-price forecast, so any figure here would "
         "be invention.",
         "Both rates are disclosed, stress-tested at 3%/5% and 4%/8%, and the results of all nine combinations "
         "are published on the decision analysis page. They are the most consequential unverified inputs on "
         "this site."),
        ("prop19-index", "Projection of the Prop 19 allowance beyond February 2027",
         "Medium",
         "The verified allowance is " + money(1044586, exact=True) + " for transfers from 16 February 2025 to 15 February "
         "2027 " + src('S02') + ". The next adjustment was not published at the time of writing.",
         "The statute indexes the allowance to the FHFA California HPI every second February " + src('S20') +
         ". The model assumes 3.5% a year from 2026.",
         "A lower indexation rate shrinks the allowance and raises every post-inheritance tax on Cupertino. At "
         "general inflation (" + pct(A['g_cpi'],1) + ") the 2045 allowance would be materially smaller."),
        ("rent", "Market rent for the vacant San Francisco unit is assumed",
         "Low",
         "The two let units produce $7,150 a month " + REPORTED + ". The vacant unit is modelled at "
         + money(P['sf']['rent_vacant_month']) + " a month " + ASSUMED + ".",
         "No source establishes the achievable rent for the third unit. The assumption simply applies the same "
         "per-unit rate as the two tenancies.",
         "Affects the income from letting the third unit, and therefore plans A and B. Does not affect plan F, "
         "which occupies that unit."),
        ("rates-future", "Future property tax rates are held constant",
         "Medium",
         "The model applies today's rate to future assessed values. It does not assume new bonds pass or old "
         "ones retire.",
         "Voter-approved debt is the variable part of the rate and it changes every year " + src('S09') + " " +
         src('S10') + ".",
         "Every post-inheritance tax figure would rise with a higher rate. The ranking is unaffected because "
         "the same rate applies in every plan."),
        ("cdi", "The statewide insurance premium benchmark is second-hand",
         "Medium",
         f"The analysis uses {money(2340)} a year as a floor for each property's insurance premium, described as "
         "the California Department of Insurance's 2025 experience-year statewide average " + src('S15') + ".",
         "The Department's own consumer pages publish premium survey tools and complaint studies rather than a "
         "single published average. The $2,340 figure appears in summaries of the Department's residential data "
         "call. The underlying Department data file was not opened during this review, so the figure is repeated "
         "from secondary reporting of an official series.",
         "Every insurance row on the site is labelled unverified, and the owner's $1,500 estimate is shown "
         "alongside rather than replaced. Quotes are the only way to close this."),
        ("scc-transfer", "Santa Clara County transfer-tax rate and the absence of a Cupertino city tax",
         "Low",
         "The model charges 0.11% ($0.55 per $500) on a Cupertino sale, described as the standard rate under the "
         "Documentary Transfer Tax Act " + src('S23') + ".",
         "The Act authorises the tax; the county's currently adopted rate, and the city of Cupertino's fee "
         "schedule, were not read from those agencies' own published schedules for this review.",
         f"The effect is {money(7180, exact=False)} on a "
         f"{money(SC['F']['sale_at_inheritance']['cup']['price'])} sale &mdash; immaterial, but stated as "
         f"unverified rather than asserted."),
        ("wealth-tax", "Status of estate and wealth tax proposals in the current legislative session",
         "Low",
         "The site states that California has no estate or inheritance tax, which is verified " + src('S06') +
         " " + src('S07') + ", and that proposals have been introduced in earlier sessions.",
         "The status of any bill in the current two-year session was not checked against the Legislature's bill "
         "database. The claim that none has been enacted is supported by the statute being unchanged, not by a "
         "search of pending bills.",
         "No figure on the site depends on this. It is recorded so the risk page does not overstate what was "
         "checked."),
    ]

    rows = []
    for anchor, title, severity, what, why, effect in items:
        kind = {"High": "unv", "Material": "unv", "Medium": "as", "Low": "rep"}[severity]
        rows.append([
            f'<a id="{anchor}"></a><strong>{title}</strong>',
            badge(severity, kind),
            what, why, effect,
        ])

    body = f"""
<p class="lede">{len(items)} items could not be resolved to an official source. Not one of them is silently
filled in: each is either labelled on the page where it appears or excluded from the figures. No item blocks
the publication of this analysis, and none changes the recommended plan &mdash; but two of them
(<a href="#sf-rate">the San Francisco rate</a> and <a href="#insurance">insurance</a>) could change the
absolute numbers substantially.</p>

<div class="callout warn">
<span class="h">How these are handled</span>
<p style="margin-bottom:0">A figure that cannot be verified is either (a) kept but explicitly labelled
<em>reported</em> or <em>assumption</em> wherever it appears, or (b) left out and the row marked blank. No value
has been inferred, interpolated or back-solved to make a table look complete.</p>
</div>

<h2>Register</h2>
{table(["Item", "Severity", "What does not reconcile", "Most likely explanation", "How the analysis handles it"],
       rows,
       caption="Ordered as they appear in the analysis.",
       aligns=["", "", "", "", ""])}

<h2>What would close each item</h2>
<ol>
<li><a href="#sf-rate">San Francisco rate</a> &mdash; the parcel's actual secured tax bill for two consecutive
years, showing the rate, the net taxable assessed value, and each direct charge as separate lines.</li>
<li><a href="#cup-rate">Cupertino rate</a> &mdash; the tax rate area printed on the bill, which maps to a single
line in the county's rate book.</li>
<li><a href="#occupancy">Occupancy</a> &mdash; the homeowners' exemption history on each parcel.</li>
<li><a href="#insurance">Insurance</a> &mdash; two written quotes per property, with the dwelling limit stated.</li>
<li><a href="#solar">Solar</a> &mdash; the net-metering tariff name and the interconnection date on the
utility account.</li>
<li><a href="#appreciation">Appreciation</a> &mdash; not closable. It is a forecast; the range is published
instead.</li>
<li><a href="#prop19-index">Prop 19 allowance</a> &mdash; the Board of Equalization letter to assessors issued
each February of an odd year.</li>
<li><a href="#rent">Vacant-unit rent</a> &mdash; two comparable rental listings in the same ZIP code.</li>
<li><a href="#rates-future">Future rates</a> &mdash; not closable; the county rate book is published annually.</li>
<li><a href="#scc-transfer">County transfer tax</a> &mdash; the Santa Clara County fee schedule and the city
of Cupertino's current fee schedule at the recorder.</li>
<li><a href="#wealth-tax">Pending legislation</a> &mdash; a search of the Legislature's bill database for
estate and wealth tax measures in the current session.</li>
</ol>
"""
    write("pages/flagged.html", page(
        "Flagged for review",
        "The ten items that could not be matched to an official source, what is most likely going on, and what would settle each one.",
        body, rel="../", current="pages/flagged.html"))
