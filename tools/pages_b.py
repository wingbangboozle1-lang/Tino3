#!/usr/bin/env python3
"""pages_b.py — property profiles, operating costs, projections."""

from site_lib import (M, money, plain, pct, src, table, page, write, pager,
                      VERIFIED, REPORTED, ASSUMED, UNVERIFIED, badge)

A = M["assumptions"]
R = M["rates"]
P = {p["key"]: p for p in M["properties"]}
SC = {s["short"]: s for s in M["scenarios_parent_cup"]}


def growth(base, rate, years):
    return base * (1 + rate) ** years


# =========================================================== CUPERTINO
CUP_HISTORY = [
    (2026, None, None, 550537, 0.02),
    (2025, 7207, 0.029, 539743, 0.02),
    (2024, 7003, 0.012, 529161, 0.02),
    (2023, 6917, 0.024, 518786, 0.02),
    (2022, 6755, 0.014, 508614, 0.02),
    (2021, 6662, 0.015, 498642, 0.01),
    (2020, 6565, None, 493530, 0.02),
    (2019, 6565, 0.028, 483854, 0.02),
    (2018, 6383, None, 474368, 0.02),
    (2017, 6383, -0.005, 465067, 0.02),
    (2016, 6414, 0.046, 455949, 0.015),
    (2015, 6130, 0.028, 449101, 0.02),
    (2014, 5965, None, 440305, 0.005),
]


def build_cupertino():
    p = P["cup"]
    rows = []
    for year, tax, tchg, assd, achg in CUP_HISTORY:
        implied = (tax / assd) if tax else None
        rows.append([
            str(year),
            (money(tax) if tax else "not yet billed", "r"),
            (("+" if tchg and tchg > 0 else "") + pct(tchg, 1) if tchg is not None else "&mdash;", "r"),
            (money(assd), "r"),
            (("+" if achg > 0 else "") + pct(achg, 1), "r"),
            (pct(implied, 3) if implied else "&mdash;", "r"),
            REPORTED,
        ])

    body = f"""
<div class="grid k3">
  <div class="kpi accent"><div class="label">Estimated value, Nov 2026</div><div class="value">{money(p['fmv_2026'])}</div>
    <div class="note">Owner estimate {REPORTED}</div></div>
  <div class="kpi"><div class="label">Assessed value, 2026</div><div class="value">{money(p['assessed_2026'])}</div>
    <div class="note">Assessor roll history {REPORTED}</div></div>
  <div class="kpi warn"><div class="label">Assessment gap</div><div class="value">{money(p['fmv_2026']-p['assessed_2026'])}</div>
    <div class="note">{((p['fmv_2026']/p['assessed_2026'])-1)*100:.0f}% below estimated market value</div></div>
</div>

<p class="lede">A single-family home in ZIP 95014. Its assessed value has risen almost exactly at the
Proposition 13 ceiling of 2% a year for twelve years, which is what you would expect of a long-held
principal residence that has never changed ownership. That history is itself evidence that the
assessment has not been reset since the current owners acquired it.</p>

<h2>Assessed value and tax history</h2>
{table(
  ["Year", "Property tax", "Change", "Assessed value", "Change", "Implied effective rate", "Basis"],
  rows,
  caption="As supplied from the owner's own tax bills. The implied rate is the bill divided by the assessed "
          "value, which is not the same as the county's published rate.",
  aligns=["", "r", "r", "r", "r", "r", ""],
)}

<h2>The rate question</h2>
<p>The bill and the assessment in each year imply an effective rate of about
<strong>{pct(p['eff_rate_reported'],4)}</strong>. The published components for Cupertino-area tax rate areas
in the Santa Clara County 2025-26 rate book sum to <strong>{pct(R['svc_rate'],4)}</strong> ({src('S09')}).</p>
{table(
  ["Component", "Rate per $100", "Applies"],
  [[k, f"{v:.5f}", "Every parcel in the tax rate area"] for k, v in R["svc_2025_26_components"].items()]
  + [["<strong>Total</strong>", (f"<strong>{R['svc_rate']*100:.5f}</strong>", "r"), "&mdash;"]],
  caption="Santa Clara County 2025-26 rate components attributed to the Cupertino area (S09).",
  aligns=["", "r", ""],
)}
<p>The {pct(p['eff_rate_reported']-R['svc_rate'],4)} difference is about
{money((p['eff_rate_reported']-R['svc_rate'])*p['assessed_2026'])} a year on the 2026 base. Two explanations
fit: the parcel's tax rate area carries a bond series not captured in the component list above, or the bills
include fixed direct assessments on top of the ad valorem tax. Both are common. Neither can be confirmed
without the parcel's tax rate area number, which is not published here for privacy reasons.
<a href="flagged.html#cup-rate">Flagged item 2 &rarr;</a></p>

<h2>What the house becomes after inheritance</h2>
{table(
  ["", "2040", "2045", "2050"],
  [
    ["Market value (4%/yr projection)", (money(growth(p["fmv_2026"], 0.04, 14)), "r"),
     (money(growth(p["fmv_2026"], 0.04, 19)), "r"), (money(growth(p["fmv_2026"], 0.04, 24)), "r")],
    ["Parents' Prop 13 base", (money(growth(p["assessed_2026"], 0.02, 14)), "r"),
     (money(growth(p["assessed_2026"], 0.02, 19)), "r"), (money(growth(p["assessed_2026"], 0.02, 24)), "r")],
    ["Property tax while the parents own it", (money(growth(p["tax_2026"], 0.02, 14)), "r"),
     (money(growth(p["tax_2026"], 0.02, 19)), "r"), (money(growth(p["tax_2026"], 0.02, 24)), "r")],
    ["Property tax if you move in and claim the exclusion",
     (money(M["inheritance_year_sensitivity"][0]["tax_excluded"]), "r"),
     (money(M["inheritance_year_sensitivity"][2]["tax_excluded"]), "r"),
     (money(M["inheritance_year_sensitivity"][4]["tax_excluded"]), "r")],
    ["Property tax if the exclusion does not apply",
     (money(M["inheritance_year_sensitivity"][0]["tax_full"]), "r"),
     (money(M["inheritance_year_sensitivity"][2]["tax_full"]), "r"),
     (money(M["inheritance_year_sensitivity"][4]["tax_full"]), "r")],
  ],
  caption="Projected. Inheritance-year sensitivity for the Cupertino house.",
  aligns=["", "r", "r", "r"],
)}

<h2>Running costs</h2>
{table(
  ["Item", "2026", "Basis", "Source"],
  [
    ["Property tax", money(p["tax_2026"]), "2025-26 bill", REPORTED],
    ["Water", money(p["water_month"] * 12) + " / yr", f"${p['water_month']}/month", REPORTED],
    ["Electricity", "net credit " + money(-p["electric_month"] * 12) + " / yr", f"about &minus;${-p['electric_month']}/month after solar credit", REPORTED],
    ["Insurance", money(p["insurance_2026"]) + " / yr", "Statewide benchmark used as a floor; owner estimated $1,500. Not a quote.", UNVERIFIED + " " + src("S15")],
    ["Maintenance and repair", money(p["fmv_2026"] * p["maintenance_pct"]) + " / yr", "0.30% of value", ASSUMED],
    ["<strong>Total, excluding property tax</strong>",
     ("<strong>" + money(p["water_month"] * 12 - p["electric_month"] * 12 + p["insurance_2026"] + p["fmv_2026"] * p["maintenance_pct"]) + " / yr</strong>", "r"),
     "", ""],
  ],
  caption="Annual ownership cost if occupied by you.",
  aligns=["", "r", "", ""],
)}

<div class="callout warn">
<span class="h">The solar credit is not a permanent feature</span>
<p style="margin-bottom:0">The owner reports that the array usually produces a net credit of roughly
$10&ndash;$20 a month. That depends entirely on which net-metering tariff the system is on. California has
moved newer interconnections to a different tariff structure with much lower export compensation. A system
interconnected years ago may keep its original tariff, but the terms are not transferable in every case and
change with the utility's filed rates. The model therefore treats the credit as a small offset in the near
term and does not compound it. <a href="flagged.html#solar">Flagged item 5 &rarr;</a></p>
</div>

<h2>Privacy note</h2>
<p>No street address, parcel number, owner name, or tax rate area is published on this site. ZIP code and
value band are the finest granularity used. The owner-supplied bill history is reproduced as an index of
years and amounts only.</p>
"""
    write("pages/cupertino.html", page(
        "Cupertino &mdash; 95014",
        "A single-family home assessed well below market value, with a bill history that implies a higher effective rate than the published county rate.",
        body, rel="../", current="pages/cupertino.html"))


# ====================================================== SAN FRANCISCO
SF_HISTORY = [
    (2025, 2439, 0.053, 114248, 0.02),
    (2024, 2315, 0.062, 112008, 0.02),
    (2023, 2179, 0.034, 109814, 0.02),
    (2022, 2107, 0.020, 107662, 0.02),
    (2021, 2066, -0.059, 105595, 0.01),
    (2020, 2197, 0.030, 104513, 0.02),
    (2019, 2134, 0.035, 102465, 0.02),
    (2018, 2061, 0.184, 100456, 0.02),
    (2017, 1740, 0.039, 98488, 0.02),
    (2016, 1675, 0.016, 96557, 0.015),
]


def build_sf():
    p = P["sf"]
    rows = []
    for year, tax, tchg, assd, achg in SF_HISTORY:
        implied = tax / assd
        rows.append([
            str(year), (money(tax), "r"),
            (("+" if tchg > 0 else "") + pct(tchg, 1), "r"),
            (money(assd), "r"),
            (("+" if achg > 0 else "") + pct(achg, 1), "r"),
            (pct(implied, 3), "r"), REPORTED,
        ])

    body = f"""
<div class="grid k4">
  <div class="kpi accent"><div class="label">Estimated value, Nov 2026</div><div class="value">{money(p['fmv_2026'])}</div>
    <div class="note">Owner estimate {REPORTED}</div></div>
  <div class="kpi"><div class="label">Assessed value, 2025</div><div class="value">{money(p['assessed_2025'])}</div>
    <div class="note">{pct(p['assessed_2025']/p['fmv_2026'],1)} of estimated value</div></div>
  <div class="kpi good"><div class="label">Rent, two units</div><div class="value">{money(7150)}/mo</div>
    <div class="note">{money(85800)} a year {REPORTED}</div></div>
  <div class="kpi"><div class="label">Gross yield on value</div><div class="value">{(85800/p['fmv_2026'])*100:.1f}%</div>
    <div class="note">Two units only; a third is vacant</div></div>
</div>

<p class="lede">A three-unit building in the Outer Sunset. Two units are let for a combined $7,150 a month;
the third is vacant, which is what makes it possible to live there without displacing a tenant. Its assessed
value is <strong>{pct(p['assessed_2025']/p['fmv_2026'],1)} of estimated market value</strong> &mdash; a
Proposition 13 base set decades ago &mdash; which is why the current tax bill is so small.</p>

<h2>Assessed value and tax history</h2>
{table(
  ["Year", "Property tax", "Change", "Assessed value", "Change", "Implied effective rate", "Basis"],
  rows,
  caption="As supplied from the owner's own tax bills.",
  aligns=["", "r", "r", "r", "r", "r", ""],
)}

<div class="callout bad">
<span class="h">This table contradicts the City's published rate &mdash; and the contradiction is material</span>
<p>The implied effective rate is consistently <strong>{pct(p['eff_rate_reported'],2)}</strong>. San Francisco's
published FY2025-26 secured rate is <strong>{pct(R['sf_rate'],6)}</strong> ({src('S10')}). At the published
rate, a {money(p['assessed_2025'])} assessment produces a bill of
<strong>{money(p['assessed_2025']*R['sf_rate'])}</strong>, not {money(p['tax_2025'])}.</p>
<p style="margin-bottom:0">Three possibilities, none of which can be resolved from the documents available:
the assessed-value column may be land only, the tax column may be a combined bill for more than one parcel,
or the figures may come from different properties. Until it is resolved, the model uses the
<em>published rate</em> for any post-inheritance projection and treats the reported bill as the current cash
cost. <a href="flagged.html#sf-rate">Flagged item 1 &rarr;</a></p>
</div>

<p class="muted">One technical point on the homeowners' exemption, since it affects every plan in which you
occupy the building: Revenue and Taxation Code &sect;218(c)(2) treats a multiple-dwelling unit occupied by an
owner as their principal residence as a qualifying &ldquo;dwelling&rdquo;, and a two-dwelling unit as two
separate single-family dwellings ({src('S16')}). The model therefore applies the full {money(7000)} exemption
to the building when you occupy a unit. If the assessor instead prorates it to one of three units, the
difference is about {money(7000 * R['sf_rate'] * 2 / 3)} a year &mdash; immaterial to any conclusion here.</p>

<h2>Rent roll</h2>
{table(
  ["Unit", "Status", "Monthly rent", "Annual rent", "Notes", "Source"],
  [
    ["1", "Let", "part of " + money(7150), "part of " + money(85800), "Rent-controlled tenancy; annual increase capped at 1.6% for 2026-27", REPORTED + " " + src("S13")],
    ["2", "Let", "part of " + money(7150), "part of " + money(85800), "Rent-controlled tenancy", REPORTED + " " + src("S13")],
    ["3", "Vacant", "&mdash; (assumed " + money(p["rent_vacant_month"]) + " if let)", money(p["rent_vacant_month"] * 12) + " modelled", "Vacant unit. Letting it adds rent; occupying it costs the forgone rent and nothing else", ASSUMED],
    ["<strong>Total if all three let</strong>", "", ("<strong>" + money(7150 + p["rent_vacant_month"]) + "/mo</strong>", "r"),
     ("<strong>" + money((7150 + p["rent_vacant_month"]) * 12) + "/yr</strong>", "r"), "", ""],
  ],
  caption="Rent roll. The market rent for the vacant unit is an assumption, not a reported figure.",
  aligns=["", "", "r", "r", "", ""],
)}

<h2>Rent control, and why it matters to the decision</h2>
<p>The two sitting tenancies are the reason this building is worth keeping. Under the San Francisco Rent
Ordinance the annual allowable increase is set each year at 60% of the change in Bay Area CPI
({src('S21')}), and for the year beginning 1 March 2026 it is <strong>1.6%</strong> ({src('S13')}). That is
far below market rent growth, so the gap between the sitting rents and market widens every year &mdash; but
the sitting rents are real cash that a house cannot produce.</p>
<p>Three structural points:</p>
<ul>
<li><strong>Rent increases are capped, but so is your ability to reset them.</strong> Rents reset to market
only on vacancy, or under a Rent Board petition for capital improvement or operating-cost passthrough.</li>
<li><strong>Owner move-in is a recognised ground for recovery of possession</strong>, which is what makes it
possible to occupy a let unit. Relocation payments are payable to a displaced tenant &mdash; for notices served
between 1 March 2026 and 28 February 2027 that is <strong>$8,245 per tenant</strong>, capped at
<strong>$24,733 per unit</strong>, plus $5,497 where the household includes an elderly or disabled tenant or a
minor child ({src('S13')}). The owner must then occupy for a minimum period.</li>
<li><strong>The vacant unit is the cheapest way to occupy.</strong> Using it costs the rent you forgo on one
unit. Displacing a tenant costs up to {money(24733, exact=True)} in relocation per unit, a legal process, and the rent on
that unit anyway.</li>
</ul>
<p class="muted">The rent-control mechanics above are structural, not priced into the model. The model lets the
two sitting tenancies escalate at 1.6% a year and the third unit at 3.0%, which is itself an assumption.</p>

<h2>What the building becomes after inheritance</h2>
{table(
  ["", "2040", "2045", "2050"],
  [
    ["Market value (4%/yr projection)", (money(growth(p["fmv_2026"], 0.04, 14)), "r"),
     (money(growth(p["fmv_2026"], 0.04, 19)), "r"), (money(growth(p["fmv_2026"], 0.04, 24)), "r")],
    ["Prop 13 base if it stays in the family", (money(growth(p["assessed_2026"], 0.02, 14)), "r"),
     (money(growth(p["assessed_2026"], 0.02, 19)), "r"), (money(growth(p["assessed_2026"], 0.02, 24)), "r")],
    ["Property tax if it stays in the family", (money(growth(p["tax_2026"], 0.02, 14)), "r"),
     (money(growth(p["tax_2026"], 0.02, 19)), "r"), (money(growth(p["tax_2026"], 0.02, 24)), "r")],
    ["Property tax after inheritance (reassessed to market)",
     (money(M["inheritance_year_sensitivity"][1]["tax_full"]), "r"),
     (money(M["inheritance_year_sensitivity"][3]["tax_full"]), "r"),
     (money(M["inheritance_year_sensitivity"][5]["tax_full"]), "r")],
    ["Multiple of the current bill",
     (f"{(M['inheritance_year_sensitivity'][1]['tax_full']/growth(p['tax_2026'],0.02,14)):.0f}&times;", "r"),
     (f"{(M['inheritance_year_sensitivity'][3]['tax_full']/growth(p['tax_2026'],0.02,19)):.0f}&times;", "r"),
     (f"{(M['inheritance_year_sensitivity'][5]['tax_full']/growth(p['tax_2026'],0.02,24)):.0f}&times;", "r")],
  ],
  caption="Projected. Prop 19 gives no relief for a rental building.",
  aligns=["", "r", "r", "r"],
)}

<h2>Running costs as landlord</h2>
{table(
  ["Item", "Monthly", "Annual", "Basis", "Source"],
  [
    ["Water (whole building)", money(p["water_month"]), money(p["water_month"] * 12), "Owner observation of a $330&ndash;$400 range", REPORTED],
    ["Electricity (common areas and owner-paid)", money(p["electric_month"]), money(p["electric_month"] * 12), "Owner observation of a $30&ndash;$70 range", REPORTED],
    ["Insurance (landlord policy)", money(p["insurance_2026"] / 12), money(p["insurance_2026"]), "Statewide benchmark used as a floor; owner estimated $1,500. Not a quote.", UNVERIFIED + " " + src("S15")],
    ["Maintenance and repair", money(p["fmv_2026"] * p["maintenance_pct"] / 12), money(p["fmv_2026"] * p["maintenance_pct"]), "0.85% of value &mdash; three units, pre-1979 building", ASSUMED],
    ["<strong>Total, excluding property tax</strong>",
     ("<strong>" + money((p["water_month"] + p["electric_month"]) + p["insurance_2026"] / 12 + p["fmv_2026"] * p["maintenance_pct"] / 12) + "</strong>", "r"),
     ("<strong>" + money((p["water_month"] + p["electric_month"]) * 12 + p["insurance_2026"] + p["fmv_2026"] * p["maintenance_pct"]) + "</strong>", "r"),
     "", ""],
  ],
  caption="Annual operating cost, landlord basis.",
  aligns=["", "r", "r", "", ""],
)}

<h2>Privacy note</h2>
<p>No street address, block or lot number, unit identifier, tenant detail, or owner name appears on this site.
Rent is disclosed only as a two-unit aggregate.</p>
"""
    write("pages/san-francisco.html", page(
        "San Francisco &mdash; 94122",
        "A three-unit Outer Sunset building: two rent-controlled tenancies, one vacant unit, and a Prop 13 base at 6% of market value.",
        body, rel="../", current="pages/san-francisco.html"))


# ======================================================= OPERATING COSTS
def build_opex():
    cup, sf = P["cup"], P["sf"]
    y = M["post_reassessment_yield"]

    rows = []
    for yr in (2026, 2030, 2035, 2040, 2045, 2050, 2055, 2060, 2065):
        n = yr - 2026
        infl = (1 + A["g_cpi"]) ** n
        ins = (1 + A["g_cpi"] + A["insurance_loading"]) ** n
        cup_v = (cup["water_month"] * 12 + cup["electric_month"] * 12) * infl + cup["insurance_2026"] * ins + growth(cup["fmv_2026"], A["g_market"], n) * cup["maintenance_pct"]
        sf_v = (sf["water_month"] * 12 + sf["electric_month"] * 12) * infl + sf["insurance_2026"] * ins + growth(sf["fmv_2026"], A["g_market"], n) * sf["maintenance_pct"]
        cls = "hl" if yr == 2045 else ""
        rows.append(([str(yr), (money(cup_v), "r"), (money(sf_v), "r"), (money(cup_v + sf_v), "r")], cls))

    body = f"""
<p class="lede">Property tax is the largest cost, but it is not the only one. This page sets out what the two
houses cost to run, separately from tax, and shows how much of the reported figure is verified and how much
is an allowance.</p>

<div class="legend">
  <span><span class="dot" style="background:#0f6b4f"></span> {VERIFIED} checked against an official source</span>
  <span><span class="dot" style="background:#14507a"></span> {REPORTED} supplied by the owner</span>
  <span><span class="dot" style="background:#b45309"></span> {ASSUMED} modelling assumption</span>
  <span><span class="dot" style="background:#a3182a"></span> {UNVERIFIED} could not be confirmed</span>
</div>

<h2>Water</h2>
{table(
  ["", "Cupertino 95014", "San Francisco 94122", "Notes"],
  [
    ["Monthly", "$100 &ndash; $150", "$330 &ndash; $400", "The San Francisco figure covers all three units"],
    ["Monthly, midpoint used", money(cup["water_month"]), money(sf["water_month"]), "Modelling midpoint of the reported range"],
    ["Annual", money(cup["water_month"] * 12), money(sf["water_month"] * 12), ""],
    ["Who pays when let", "Tenant, typically, for a single-family house", "Owner &mdash; typically the landlord carries water on a multi-unit building", "Assumption"],
    ["Source", REPORTED, REPORTED, "Owner observation. No official rate schedule is attached because the retail water provider for each parcel is not confirmed."],
  ],
  caption="Water cost.",
  aligns=["", "r", "r", ""],
)}
<p class="muted">Water rates in the Bay Area have been rising faster than headline inflation as agencies fund
pipe replacement and supply resilience. The model escalates water at the general inflation assumption of
{pct(A['g_cpi'],1)}; a faster rate of increase would raise costs in the out-years but does not change the
ranking of the plans. {UNVERIFIED} for both ZIP codes: the retail water provider and its current tariff were
not confirmed from an official rate schedule.</p>

<h2>Electricity</h2>
{table(
  ["", "Cupertino 95014", "San Francisco 94122", "Notes"],
  [
    ["Monthly", "net credit of about $10 &ndash; $20", "$30 &ndash; $70", "Cupertino has rooftop solar"],
    ["Monthly, midpoint used", "&minus;" + money(-cup["electric_month"]), money(sf["electric_month"]), ""],
    ["Annual", "&minus;" + money(-cup["electric_month"] * 12), money(sf["electric_month"] * 12), "A credit, not a cost"],
    ["Source", REPORTED, REPORTED, "Owner observation"],
  ],
  caption="Electricity cost.",
  aligns=["", "r", "r", ""],
)}
<div class="callout warn">
<span class="h">Do not model the solar credit as a permanent income stream</span>
<p style="margin-bottom:0">Whether an array earns export credit, and how much, depends on the net-metering
tariff it is on. California has moved new interconnections onto a materially less generous tariff; systems
interconnected earlier generally stay on their original tariff, but the terms depend on the utility's filed
tariffs and on continuity of the account. The model carries the credit at its reported value escalated with
inflation and no more. {UNVERIFIED} &mdash; the tariff for this system was not confirmed.
<a href="flagged.html#solar">Flagged item 5 &rarr;</a></p>
</div>

<h2>Insurance</h2>
{table(
  ["", "Cupertino 95014", "San Francisco 94122"],
  [
    ["Owner's estimate", "$1,500 / yr", "$1,500 / yr"],
    ["California statewide average, all homeowners forms (2025 experience year)", money(2340) + " / yr", money(2340) + " / yr"],
    ["California FAIR Plan dwelling-fire average", money(2918, exact=True) + " / yr", money(2918, exact=True) + " / yr"],
    ["Modelled allowance in this analysis", money(2340) + " / yr", money(2340) + " / yr"],
    ["Basis", UNVERIFIED + " " + src("S15"), UNVERIFIED + " " + src("S15")],
  ],
  caption="Insurance. The Department of Insurance publishes premium information at statewide and company level "
          "only; no ZIP-level official average exists. The statewide figure itself is second-hand (see S15), so "
          "every row in this table is unverified.",
  aligns=["", "r", "r"],
)}
<p>Two things point the same way. The owner's $1,500 estimate is below the statewide average for an ordinary
homeowners policy, and these are not ordinary homes: a $3,100,000 house in Cupertino and a three-unit
pre-1979 building in San Francisco both require dwelling limits far above the average. On the other hand,
neither property sits in a high fire-hazard severity zone &mdash; the Outer Sunset is a fog belt and Cupertino's
flatlands are not wildland-urban interface &mdash; so neither should be pushed into the FAIR Plan, whose
dwellings average roughly {money(2918, exact=True)} a year.</p>
<p>The model uses the statewide average as a floor, which is a compromise: too high if a good admitted-market
quote exists, too low if the dwelling limits require a specialty policy.
<strong>This is the largest unresolved number in the cost model.</strong>
<a href="flagged.html#insurance">Flagged item 4 &rarr;</a></p>

<h2>Maintenance and repair</h2>
{table(
  ["", "Cupertino 95014", "San Francisco 94122", "Reasoning"],
  [
    ["Rate used", pct(cup["maintenance_pct"], 2) + " of value", pct(sf["maintenance_pct"], 2) + " of value", "Assumption"],
    ["2026 amount", money(cup["fmv_2026"] * cup["maintenance_pct"]), money(sf["fmv_2026"] * sf["maintenance_pct"]), ""],
    ["2045 amount", money(growth(cup["fmv_2026"], A["g_market"], 19) * cup["maintenance_pct"]), money(growth(sf["fmv_2026"], A["g_market"], 19) * sf["maintenance_pct"]), ""],
    ["Why the difference", "Single family; solar already installed; fewer systems to service", "Three units; pre-1979 construction; roof, sewer, electrical and seismic work on a shorter cycle; tenant-turnover costs", "Owner also reports San Francisco costs more"],
  ],
  caption="Maintenance allowance. Tied to value rather than to a fixed dollar amount so it tracks "
          "construction cost inflation.",
  aligns=["", "r", "r", ""],
)}

<h2>Combined running cost, excluding property tax</h2>
{table(["Year", "Cupertino", "San Francisco", "Combined"], rows,
       caption="Costs escalated at " + pct(A["g_cpi"],1) + " for utilities and maintenance inputs, and at "
               "that rate plus 2 points for insurance. 2045 is the projected inheritance year.",
       aligns=["", "r", "r", "r"])}

<h2>The number that decides the plan: net yield after reassessment</h2>
<p>Once both houses are reassessed to market value, the question is not what they are worth but what they
return. This table is the core of the decision analysis:</p>
{table(
  ["", "Cupertino 95014", "San Francisco 94122"],
  [
    ["Value, 2045 projection", (money(y["cup"]["value"]), "r"), (money(y["sf"]["value"]), "r")],
    ["Gross rent if let", (money(y["cup"]["gross_rent"]), "r"), (money(y["sf"]["gross_rent"]), "r")],
    ["Operating costs excluding tax", ("&minus;" + money(y["cup"]["opex"]), "r"), ("&minus;" + money(y["sf"]["opex"]), "r")],
    ["Property tax at full reassessment", ("&minus;" + money(y["cup"]["property_tax"]), "r"), ("&minus;" + money(y["sf"]["property_tax"]), "r")],
    ["Net cash yield", (f"<strong>{money(y['cup']['net'])}</strong>", "r"), (f"<strong>{money(y['sf']['net'])}</strong>", "r")],
    ["Net yield on value", (f"<strong>{pct(y['cup']['net_yield_on_value'],2)}</strong>", "r"), (f"<strong>{pct(y['sf']['net_yield_on_value'],2)}</strong>", "r")],
  ],
  caption="Net cash return after reassessment, first year of ownership. Before income tax.",
  aligns=["", "r", "r"],
)}
<p>The San Francisco building returns roughly four times as much, on a house worth little more than half as
much. That single ratio is why the recommendation is to keep it and monetise Cupertino.</p>
"""
    write("pages/operating-costs.html", page(
        "Operating costs",
        "Water, electricity, insurance and maintenance for both houses, separated into verified, reported and assumed, with the net-yield comparison that drives the decision.",
        body, rel="../", current="pages/operating-costs.html"))


# ============================================================ PROJECTIONS
def build_projections():
    proj = M["projection"]
    rows = []
    for r in proj:
        y = r["year"]
        cls = "hl" if y in (2040, 2045, 2050) else ("dim" if y > 2045 else "")
        rows.append(([
            str(y),
            (money(r["cup_fmv"]), "r"), (money(r["cup_assessed"]), "r"), (money(r["cup_tax"]), "r"),
            (money(r["sf_fmv"]), "r"), (money(r["sf_assessed"]), "r"), (money(r["sf_tax"]), "r"),
        ], cls))

    cases = []
    for label, g in (("3% (low)", 0.03), ("4% (base)", 0.04), ("5% (high)", 0.05)):
        for yr in (2030, 2040, 2045, 2050, 2060, 2065):
            n = yr - 2026
            cases.append([
                label if yr == 2030 else "", str(yr),
                (money(growth(P["cup"]["fmv_2026"], g, n)), "r"),
                (money(growth(P["sf"]["fmv_2026"], g, n)), "r"),
                (money(growth(P["cup"]["fmv_2026"], g, n) + growth(P["sf"]["fmv_2026"], g, n)), "r"),
            ])

    body = f"""
<p class="lede">Two things grow at different speeds and in opposite directions. Market value moves with the
housing market; assessed value is pinned to the Proposition 13 ceiling of 2% a year and cannot exceed it
absent a change in ownership. The gap between the two columns is the tax the heirs will eventually pay.</p>

<div class="callout">
<span class="h">What the columns mean</span>
<p style="margin-bottom:0"><strong>Market value</strong> is a projection on an assumed growth rate, not a
forecast and not a verified figure. <strong>Assessed value</strong> is the parents' Proposition 13 base,
compounding at the statutory 2% cap ({src('S17')}). <strong>Property tax</strong> is the owners' reported
2026 bill compounded at the same 2%. No row here is a valuation you can rely on &mdash; they exist to
show the shape of the problem.</p>
</div>

<h2>Year by year, 2026&ndash;2065</h2>
{table(
  ["Year", "Cupertino value", "Cupertino assessed", "Cupertino tax", "San Francisco value", "San Francisco assessed", "San Francisco tax"],
  rows,
  caption="Base case: " + pct(A["g_market"],1) + " market growth, 2% Prop 13 cap. Highlighted rows are the "
          "starts of the inheritance window. Rows after 2045 show the tax the parents would pay if nothing "
          "changed; they are not the tax you would pay after inheriting.",
  aligns=["", "r", "r", "r", "r", "r", "r"],
)}

<h2>Three growth cases</h2>
{table(["", "Year", "Cupertino", "San Francisco", "Combined"], cases,
       caption="Market value under the three assumptions tested. The base case is 4.0%, which sits below the "
               "five-year appreciation reported by the FHFA California house price index (" + src("S14") + ") and "
               "above the most recent twelve months.",
       aligns=["", "", "r", "r", "r"])}

<h2>The inheritance-year question</h2>
<p>The brief puts the inheritance somewhere between 2040 and 2050. Everything that matters scales with that
date, because market value compounds and the Prop 13 base barely moves.</p>
{table(
  ["Year", "Property", "Market value", "Parents' base", "Prop 19 allowance", "Tax if you move in and claim", "Tax if fully reassessed", "Annual saving"],
  [[str(r["year"]), r["property"], (money(r["fmv"]), "r"), (money(r["fbyv"]), "r"),
    (money(r["allowance"]), "r"), (money(r["tax_excluded"]), "r"), (money(r["tax_full"]), "r"),
    (f"<strong>{money(r['annual_saving'])}</strong>", "r")]
   for r in M["inheritance_year_sensitivity"]],
  caption="Inheritance-year sensitivity. For San Francisco the exclusion only applies if that building was the "
          "parents' principal residence, which the base case assumes it was not &mdash; hence the identical "
          "figures in the two tax columns.",
  aligns=["", "", "r", "r", "r", "r", "r", "r"],
)}

<div class="callout warn">
<span class="h">The allowance is doing all the work, and it is not guaranteed</span>
<p style="margin-bottom:0">The Prop 19 allowance is index-linked to the FHFA California house price index and
adjusted every second February ({src('S02')}). The model assumes it grows 3.5% a year, reaching
{money(M["inheritance_year_sensitivity"][2]["allowance"])} by 2045. If it instead tracked general inflation,
the allowance would be materially smaller and every post-inheritance tax figure on this page would be higher.
This is an assumption with a visible effect; it is listed as such on the flagged page.</p>
</div>

<h2>What the model does not project</h2>
<ul>
<li><strong>Refinancing or borrowing.</strong> Both houses are assumed owned outright.</li>
<li><strong>Capital improvement.</strong> Nothing is added to either basis, and no work is assumed beyond the
maintenance allowance.</li>
<li><strong>Special assessments or Mello-Roos.</strong> Neither parcel is known to carry one, and neither is
confirmed to be free of one.</li>
<li><strong>Changes in the tax rate itself.</strong> Bond debt retires and new bonds are issued; the rate is
held at its current level plus nothing.</li>
<li><strong>Proposition 8 declines.</strong> If a property's market value falls below its factored base year
value, the assessor may temporarily reduce the assessment. The model never assumes a decline, which
overstates tax in any downturn.</li>
</ul>
"""
    write("pages/projections.html", page(
        "Projections 2026&ndash;2065",
        "Market value, assessed value and property tax for both houses, year by year, plus the inheritance-year sensitivity that decides everything.",
        body, rel="../", current="pages/projections.html"))
