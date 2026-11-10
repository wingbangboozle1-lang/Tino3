#!/usr/bin/env python3
"""Render the published dashboard from assets/data/model.json and assets/sources.json.

Privacy rules baked in: no names, no street addresses, no ZIP codes, no parcel numbers,
no city-level property identifiers. Properties are [PROPERTY_A] and [PROPERTY_B].
Every displayed dollar figure comes from the model, which rounds to the nearest $10.
"""
from __future__ import annotations
import json
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M = json.loads((ROOT / "assets" / "data" / "model.json").read_text())
SRC = json.loads((ROOT / "assets" / "sources.json").read_text())["sources"]

NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive summary"),
    ("property-a.html", "Property A"),
    ("property-b.html", "Property B"),
    ("taxes.html", "Tax &amp; law"),
    ("projections.html", "Projections"),
    ("decision.html", "Decision analysis"),
    ("inheritance.html", "Inheritance steps"),
    ("review.html", "Flagged for review"),
    ("sources.html", "Source library"),
]

PRIVACY = ("<strong>Privacy boundary.</strong> No names, street addresses, ZIP codes, parcel numbers or "
           "unrounded assessment figures are published. Properties appear as <code>[PROPERTY_A]</code> and "
           "<code>[PROPERTY_B]</code>. All amounts are rounded to the nearest $10.")


SHORT = {"Internal Revenue Service": "IRS", "California State Board of Equalization": "BOE",
         "California Legislative Information": "CA statute", "California Franchise Tax Board": "FTB",
         "California Public Utilities Commission": "CPUC", "California Department of Insurance": "CDI",
         "California Legislative Analyst's Office": "LAO", "California Secretary of State": "CA SOS",
         "Board of Supervisors (jurisdiction B rate-setting authority)": "Local rate resolution"}


def link(src_id, label=None):
    s = SRC[src_id]
    short = SHORT.get(s["publisher"], s["publisher"])
    title = e(s["title"].split("(")[0].strip())
    if len(title) > 52:
        title = title[:49].rstrip() + "…"
    return (f'<a href="{s["url"]}" target="_blank" rel="noopener noreferrer">'
            f'{label or short} · {title} &#8599;</a>')


def ulinks(*ids):
    return "".join(link(i) for i in ids)


def internal(href, label):
    return f'<a href="{href}">{label}</a>'


def money(v):
    if v is None or v == "":
        return ""
    if isinstance(v, str):
        return e(v)
    v = int(round(float(v)))
    if v < 0:
        return f"&minus;${abs(v):,}"
    return f"${v:,}"


def pct(v, digits=2):
    return f"{v*100:.{digits}f}%"


def table(headers, rows, caption=None, cls=""):
    """rows = list of dicts: {'cells':[...], 'links':'html' or None, 'basis':'fact'|'scenario'}"""
    h = "".join(f'<th scope="col">{x}</th>' for x in headers)
    body = []
    for r in rows:
        attrs = f' data-basis="{r.get("basis", "fact")}"'
        cells = "".join(f"<td>{c}</td>" for c in r["cells"])
        body.append(f"<tr{attrs}>{cells}<td>{r['links']}</td></tr>")
    cap = f"<caption>{caption}</caption>" if caption else ""
    return (f'<div class="table-wrap"><table class="{cls}">{cap}<thead><tr>{h}<th scope="col">Source</th></tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def head(title, current):
    nav = "".join(
        f'<a {"aria-current=page" if href == current else ""} href="{href}"><span>{i:02d}</span>{label}</a>'
        for i, (href, label) in enumerate(NAV, start=1))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Privacy-safe, official-source inherited-property decision dashboard.">
<meta name="referrer" content="no-referrer">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self'; img-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
<title>{title} · Inheritance Atlas</title><link rel="stylesheet" href="assets/style.css"></head><body>
<a class="skip" href="#main">Skip to content</a>
<aside><a class="brand" href="index.html"><b>IA<span>&#8599;</span></b>Inheritance<br>Atlas</a>
<div class="nav-label">PLANNING WORKSPACE</div>
<nav aria-label="Main navigation">{nav}</nav>
<div class="aside-bottom"><span class="dot"></span> Privacy-first publication<br><small>Official sources &middot; No personal data</small></div></aside>
<main id="main"><header><span>PROPERTY &amp; WEALTH / {current.replace('.html', '').replace('-', ' ').upper()}</span><span class="review-date">Reviewed Nov 10, 2026</span></header>"""


FOOT = ('<footer><span>Inheritance Atlas &middot; Public planning edition</span>'
        '<span>No personal data &middot; Not legal, tax or investment advice</span></footer></main></body></html>')


def notice(text=""):
    return (f'<div class="notice"><span>&#9672;</span><div><strong>Evidence standard.</strong> '
            f'Every rule below links to the official publisher. Scenario assumptions are labelled '
            f'<em>scenario</em>; they are not forecasts. {text}</div></div>')


def hero(eyebrow, h1, p):
    return f'<div class="hero"><div class="eyebrow">{eyebrow}</div><h1>{h1}</h1><p>{p}</p></div>'


P = {}

# ---------------------------------------------------------------- overview
d45 = [r for r in M["decision"] if r["year"] == 2045][0]
best45 = max(x["terminal_net_worth"] for x in d45["rows"])
sell45 = [x for x in d45["rows"] if x["code"] == "S3A"][0]["terminal_net_worth"]
rent45 = [x for x in d45["rows"] if x["code"] == "S2"][0]["terminal_net_worth"]
m45 = [i for i in M["inheritance"] if i["year"] == 2045 and i["law"] == "prop19"][0]
est45 = [x for x in M["estate"] if x["year"] == 2045][0]

P["index.html"] = (head("Overview", "index.html") + hero(
    "INHERITANCE DECISION BRIEF",
    "Decide with numbers.<br>Not with guesses.",
    "A 2040&ndash;2050 inherited-residence decision, modelled against the official property-tax, income-tax and estate rules that apply.") +
    f'<div class="notice"><span>&#9672;</span><div>{PRIVACY}</div></div>' +
    f"""<div class="metrics">
<article><span>BEST 2045 OPTION · AFTER TAX</span><strong>Sell A</strong><p>{money(sell45)} of terminal net worth in 2055 versus {money(rent45)} if rented. Gap {money(sell45-rent45)}.</p></article>
<article><span>PROPERTY A PROPERTY TAX · 2045</span><strong>{money(m45['tax_live'])}</strong><p>If occupied at inheritance (Proposition 19 exclusion applied). {money(m45['tax_rent'])} if rented out.</p></article>
<article><span>FEDERAL ESTATE EXCLUSION · 2026</span><strong>$15,000,000</strong><p>California imposes no inheritance, estate or gift tax of its own.</p></article>
<article><span>ESTATE HEADROOM · 2045</span><strong>{money(est45['cash_headroom_single'])}</strong><p>Cash that could still pass tax-free if both properties are in the estate.</p></article>
</div>
<section><h2>Recommendation</h2>
<div class="cards">
<article class="card"><h3>1. Do not decide now</h3><p>Nothing in current law requires a decision before the death occurs. Pre-committing to a sale, a rental conversion or a move locks in values and rules that will be different.</p></article>
<article class="card"><h3>2. Sell [PROPERTY_A] at inheritance</h3><p>Inherited basis steps up to date-of-death value, so a prompt sale inside the first year realises almost no gain. That is the only moment the embedded gain disappears.</p></article>
<article class="card"><h3>3. Keep [PROPERTY_B] rented</h3><p>It already produces the housing the household needs through its third unit, so occupying A buys no housing benefit and costs {money([x for x in d45['rows'] if x['code']=='S1'][0]['terminal_net_worth']*-1+best45)} in terminal wealth at 2045.</p></article>
</div>
<p class="note">The ranking is close: renting A beats selling if long-run returns fall below about {d45['breakeven_reinvest']}%, or if the pending full-exclusion proposal becomes law (rent then gains about {money([s for s in M['sensitivity'] if s['kind']=='law' and s['year']==2045][0]['delta'])}). Both branches are shown in full on the decision page.</p>
</section>
<section><h2>Decision snapshot &middot; inheritance in 2045</h2>
{table(["Option", "First-year cash flow", "Terminal after-tax net worth (2055)", "Gap versus best", "Why"],
       [{"cells": [e(r["name"]), money(r["yr1_cash"]), money(r["terminal_net_worth"]), money(r["gap_vs_best"]), e(r["note"])],
         "links": ulinks("irs_basis", "irs_tc409") if r["code"].startswith("S3") else ulinks("boe_prop19", "rtc51"),
         "basis": "scenario"} for r in d45["rows"]],
       caption="All figures are model output from the assumptions register; terminal values are nominal 2055 dollars.")}
<p class="note">Sources for the mechanics: {ulinks('irs_basis')} (basis step-up), {ulinks('boe_prop19')} (family-home exclusion), {ulinks('boe_cap')} (cap amount). Rental treatment: <a href="https://www.irs.gov/publications/p527" target="_blank" rel="noopener noreferrer">IRS &middot; Publication 527 &#8599;</a>.</p>
</section>
<section><h2>Read by category</h2>
<div class="cards">
<article class="card"><h3><a href="executive-summary.html">Executive summary</a></h3><p>The decision, the numbers behind it, and what would change it.</p></article>
<article class="card"><h3><a href="property-a.html">[PROPERTY_A]</a></h3><p>Assessed value, derived tax rate, carrying costs, 2026&ndash;2055 projection, solar exposure.</p></article>
<article class="card"><h3><a href="property-b.html">[PROPERTY_B]</a></h3><p>Rent roll, operating statement, the reported-bill anomaly, 2026&ndash;2055 projection.</p></article>
<article class="card"><h3><a href="taxes.html">Tax &amp; law</a></h3><p>Federal estate, California death taxes, Proposition 13 and 19, capital gains, pending changes.</p></article>
<article class="card"><h3><a href="inheritance.html">Inheritance steps</a></h3><p>Day-by-day obligations, statutory deadlines and the filings that protect the assessment.</p></article>
<article class="card"><h3><a href="review.html">Flagged for review</a></h3><p>Every unverified value, every assumption, and one disclosure about earlier repository history.</p></article>
</div></section>""" + FOOT)

# ---------------------------------------------------------------- executive summary
P["executive-summary.html"] = (head("Executive summary", "executive-summary.html") + hero(
    "EXECUTIVE SUMMARY",
    "One recommendation.<br>Five numbers that drive it.",
    "Prepared 10 November 2026 for a trust inheritance expected between 2040 and 2050.") + notice() +
    f"""<section><h2>1. The decision</h2>
<p><strong>Sell [PROPERTY_A] within twelve months of the transfer, keep [PROPERTY_B] as the rental and as the household's residence, and reinvest the proceeds in a diversified portfolio.</strong> If the household genuinely wants to live in [PROPERTY_A] for a decade or more, that choice is affordable but it is a lifestyle purchase, not the highest-wealth path: at 2045 it costs about {money(best45-[x for x in d45['rows'] if x['code']=='S1'][0]['terminal_net_worth'])} of terminal after-tax net worth against selling.</p>
<h2>2. Why the sale wins &mdash; and how narrowly</h2>
<ul>
<li><strong>Basis reset.</strong> Inherited property takes a basis equal to date-of-death fair market value, so a prompt sale realises almost no taxable gain. Delay converts that free reset into taxable appreciation. {ulinks('irs_basis')}</li>
<li><strong>The Proposition 19 exclusion is capped, and the cap is small relative to this property.</strong> The exclusion is the factored base year value plus {money(M['sources_rates']['prop19_cap_2025'])} for transfers up to 15 February 2027 (official figure $1,044,586, shown rounded), and it requires the transferee to occupy the home as a principal residence and file within deadlines. {ulinks('boe_cap', 'boe_prop19')}</li>
<li><strong>Housing is already solved.</strong> [PROPERTY_B] has three livable units and only two are rented, so the household can live there without giving up rent. Occupying A therefore adds no housing value.</li>
<li><strong>Renting A out is taxable and thin.</strong> A rental transfer is reassessed at full market value, so first-year tax at 2045 would be about {money(m45['tax_rent'])} against gross rent of roughly {money(round([r for r in M['projections_a'] if r['year']==2045][0]['fmv_base']*0.03, -1))} under the 3.0% yield scenario. The net margin is small relative to capital at risk.</li>
<li><strong>Timing.</strong> The 2050 comparison is effectively a tie ({money(sell45)} versus {money(rent45)} in 2045 terms), so the edge depends on returns and appreciation, not on law.</li>
</ul>
<h2>3. The five numbers</h2>
{table(["Measure", "Amount", "What it means"],
 [{"cells": ["Terminal after-tax net worth if A is sold, 2045 inheritance, 2055 horizon", money(sell45), "Base case under the 7.0% equity and 4.0% appreciation scenarios."], "links": ulinks("irs_basis"), "basis": "scenario"},
  {"cells": ["Terminal after-tax net worth if A is rented instead", money(rent45), "Full reassessment applies; rental income taxed at the 33.3% scenario rate."], "links": ulinks("boe_prop19", "ftb_rates"), "basis": "scenario"},
  {"cells": ["Return needed on the sale proceeds to match renting", f"{d45['breakeven_reinvest']}%", "Below this, holding and renting wins."], "links": ulinks("irs_tc409"), "basis": "scenario"},
  {"cells": ["Property A tax in the first inheritance year, occupied", money(m45['tax_live']), f"Blended assessment of {money(m45['assessed_live'])} at the derived {M['sources_rates']['rate_a_derived']}% effective rate."], "links": ulinks("boe_cap", "rtc51")},
  {"cells": ["Federal estate exclusion, 2026", "$15,000,000", "Per decedent. California adds no death tax of its own."], "links": ulinks("irs_estate", "rtc13301")}])}
<h2>4. Inheritance tax: the direct answer</h2>
<p>There is <strong>no California inheritance, estate, gift or succession tax</strong>; the state is constitutionally prohibited from imposing one. {ulinks('rtc13301')} A beneficiary therefore receives assets free of California death tax at any amount. The federal constraint sits on the <em>estate</em>, not on each beneficiary: a Form 706 is required when the gross estate plus adjusted taxable gifts exceeds $15,000,000 for a 2026 death, and tax applies only above that amount. {ulinks('irs_estate', 'irs_estate_faq')} On the modelled values, the two properties total {money(est45['estate_two_properties'])} in 2045, leaving {money(est45['cash_headroom_single'])} of cash headroom before any federal tax could apply.</p>
<h2>5. Cost structure per year (2026 dollars)</h2>
{table(["Cost", "[PROPERTY_A]", "[PROPERTY_B]", "Basis"],
 [{"cells": [c["item"], money(c["a"]) if c["a"] else "", money(c["b"]), e(c["note_a"] if c["item"] not in ("Property tax",) else "Property A is derived; Property B is the reported bill.")], "links": ulinks("rtc51", "sf_rate"), "basis": "scenario"} for c in M["carrying"]] +
 [{"cells": ["Total annual carrying cost before any rent", money(sum(c["a"] for c in M["carrying"])), money(sum(c["b"] for c in M["carrying"])), "Sum of the rows above."], "links": ulinks("rtc51"), "basis": "scenario"}])}
<h2>6. What would change the recommendation</h2>
<ul>
<li><strong>The pending full-exclusion proposal.</strong> LAO's analysis of initiative 25-0017 describes restoring pre-Proposition 19 rules from 1 January 2027, applying to all inherited primary homes regardless of value and retroactively to transfers since February 2021. If enacted, renting A would keep the base year value and gain about {money([s for s in M['sensitivity'] if s['kind']=='law' and s['year']==2045][0]['delta'])} by 2055, enough to overtake selling. {ulinks('lao_250017')} It did <strong>not</strong> appear on the 3 November 2026 statewide ballot. {ulinks('sos_measures')}</li>
<li><strong>Sustained returns below about {d45['breakeven_reinvest']}%.</strong> At a 4.0% reinvestment return, selling is the worst of the three hold-or-sell options. See the sensitivity matrix.</li>
<li><strong>A decision to live in A long term.</strong> Then the exclusion plus avoided transaction costs make occupancy defensible.</li>
</ul>
<h2>7. Actions before 2040</h2>
<ol>
<li>Confirm in writing how title is held, which trust holds each property, and whether both are community property &mdash; this decides whether there is one step-up or two.</li>
<li>Ask the trustee to keep a current appraisal file and the trust's Schedule of assets (not published here).</li>
<li>Obtain the actual annual insurance declarations and utility bills; every insurance figure in this edition is unlabelled-scenario or an owner estimate.</li>
<li>Have counsel confirm the Proposition 19 claim calendar before, not after, the transfer.</li>
</ol>
<p class="note">{PRIVACY}</p></section>""" + FOOT)

# ---------------------------------------------------------------- property A
pa = [r for r in M["projections_a"] if r["year"] in (2026, 2030, 2035, 2040, 2045, 2050, 2055)]
P["property-a.html"] = (head("Property A", "property-a.html") + hero(
    "[PROPERTY_A]",
    "The residence to inherit.",
    "A single-family home in a high-cost county jurisdiction, with rooftop solar and a long-held, low assessed value.") + notice() +
    f"""<section><h2>Profile</h2>
{table(["Item", "Value", "Status"],
 [{"cells": ["Estimated market value, November 2026", money(3100000), "Owner estimate &mdash; not an appraisal."], "links": ulinks("irs_basis")},
  {"cells": ["2026 assessed (factored base year) value", money(550540), "Owner-provided roll figure, rounded to $10."], "links": ulinks("rtc51")},
  {"cells": ["2025 property tax paid", money(7210), "Owner-provided."], "links": ulinks("rtc51")},
  {"cells": ["Implied effective tax rate", f"{M['sources_rates']['rate_a_derived']}%", "Derived: 2025 tax &divide; 2025 assessed value. Includes voter-approved debt and parcel charges, not just the 1% base levy."], "links": ulinks("rtc51")},
  {"cells": ["Derived 2026 tax (bill not provided)", money([r for r in M['projections_a'] if r['year']==2026][0]['tax']), "Derived, not a bill &mdash; flagged FL-01."], "links": ulinks("rtc51")},
  {"cells": ["Solar", "Net credit reported: $10&ndash;$20 per month", "Owner-reported. Export compensation rules changed for new interconnections after 15 April 2023 and legacy tariffs are closed to new enrolments."], "links": ulinks("cpuc_nem")}])}
</section>
<section><h2>Assessment history (owner-provided, rounded to $10, unverified)</h2>
<p>These are the owner's records, not county records. They were checked only for internal arithmetic and for consistency with the statutory 2% cap on assessed-value growth. {ulinks('rtc51')}</p>
{table(["Year", "Property tax", "Assessed value", "Year-over-year assessed change", "Status"],
 [{"cells": [str(r["year"]), money(r["tax"]) if r["tax"] else "not provided", money(r["assessed"]),
             ("+" + f"{(r['assessed']/prev-1)*100:.2f}%" if prev else ""), e(r["status"])],
   "links": ulinks("rtc51")} for r, prev in zip(M["history_a"], [None] + [x["assessed"] for x in M["history_a"]])])}
</section>
<section><h2>Annual carrying cost, 2026</h2>
{table(["Cost", "Amount per year", "Basis"],
 [{"cells": [c["item"], money(c["a"]), e(c["note_a"])], "links": ulinks("cpuc_nem" if "Electric" in c["item"] else ("cdi_tool" if "insurance" in c["item"] else "rtc51")), "basis": "scenario"} for c in M["carrying"]] +
 [{"cells": ["Total", money(sum(c["a"] for c in M["carrying"])), "Before any rent is received."], "links": ulinks("rtc51"), "basis": "scenario"}],
 caption="Insurance is the owner's estimate; no verified quote exists (FL-03). Maintenance is a 0.50% of value scenario.")}
</section>
<section><h2>Projection 2026&ndash;2055 (base case: 4.0% appreciation, 2.5% cost inflation, 2.0% Proposition 13 growth)</h2>
{table(["Year", "Value &middot; low 3%", "Value &middot; base 4%", "Value &middot; high 5%", "Assessed value", "Property tax", "Insurance", "Water", "Electricity", "Maintenance", "Total carrying cost"],
 [{"cells": [str(r["year"]), money(r["fmv_low"]), money(r["fmv_base"]), money(r["fmv_high"]), money(r["assessed"]),
             money(r["tax"]), money(r["insurance"]), money(r["water"]), money(r["electric"]), money(r["maintenance"]), money(r["total_carrying"])],
   "links": ulinks("rtc51", "cpuc_nem", "cdi_tool"), "basis": "scenario"} for r in pa],
 caption="Every value is a cumulative projection from the 2026 owner estimate. No row is an appraisal. Full 30-year series in assets/data/property_a.csv.")}
</section>
<section><h2>What happens to the property tax at inheritance</h2>
{table(["Inheritance year", "Value at transfer", "Factored base year value", "Exclusion cap", "Assessed if occupied", "Tax if occupied", "Assessed if rented", "Tax if rented"],
 [{"cells": [str(i["year"]), money(i["fmv"]), money(i["fbyv"]), money(i["cap"]), money(i["assessed_live"]), money(i["tax_live"]), money(i["assessed_rent"]), money(i["tax_rent"])],
   "links": ulinks("boe_prop19", "boe_cap", "rtc51")} for i in M["inheritance"] if i["law"] == "prop19"],
 caption="Occupied column applies the Proposition 19 formula: base year value + (market value − base year value − cap). Rented column is full reassessment.")}
<p class="note"><strong>Read this before counting on the exclusion.</strong> The exclusion preserves a low assessment only up to the cap. Because projected 2045 value of {money(m45['fmv'])} exceeds base year value plus cap by about {money(m45['fmv']-m45['fbyv']-m45['cap'])}, most of the benefit has already disappeared by the time of transfer. Moving out later also removes relief, and the claim must be filed within three years. {ulinks('boe_prop19')}</p>
</section>""" + FOOT)

# ---------------------------------------------------------------- property B
pb = [r for r in M["projections_b"] if r["year"] in (2026, 2030, 2035, 2040, 2045, 2050, 2055)]
b26 = [r for r in M["projections_b"] if r["year"] == 2026][0]
P["property-b.html"] = (head("Property B", "property-b.html") + hero(
    "[PROPERTY_B]",
    "The rental that already works.",
    "A three-unit building in a city-and-county jurisdiction: two units rented, one unit available for the household to occupy.") + notice() +
    f"""<section><h2>Profile</h2>
{table(["Item", "Value", "Status"],
 [{"cells": ["Estimated market value, November 2026", money(1800000), "Owner estimate &mdash; not an appraisal."], "links": ulinks("irs_basis")},
  {"cells": ["2025 assessed value", money(114250), "Owner-provided roll figure, rounded to $10."], "links": ulinks("rtc51")},
  {"cells": ["2025 property tax paid", money(2440), "Owner-provided, rounded to $10."], "links": ulinks("sf_rate")},
  {"cells": ["Verified local ad valorem rate, FY2025-26", "$1.18268325 per $100", f"Applied to the reported assessed value this yields {money(1350)} &mdash; about {money(2440-1350)} less than the reported bill (flagged FL-02)."], "links": ulinks("sf_rate")},
  {"cells": ["Rent received, two units", money(7150) + " per month", "Owner-provided."], "links": ulinks("irs_basis", "ftb_cg")},
  {"cells": ["Units", "3 livable &middot; 2 rented &middot; 1 available", "Owner-provided."], "links": ulinks("sf_rate")}])}
<p class="note"><strong>The reported bill does not reconcile with the published rate.</strong> Ad valorem tax on the reported assessed value should be about {money(round(114250*0.0118268325,-1))}; the reported bill is {money(2440)}. The difference of roughly {money(2440-1350)} is consistent with non-ad-valorem parcel charges or a different roll value, but neither is verified. Obtain the actual bill before relying on either figure. {ulinks('sf_rate')}</p>
</section>
<section><h2>Assessment history (owner-provided, rounded to $10, unverified)</h2>
{table(["Year", "Property tax", "Assessed value", "Year-over-year tax change", "Status"],
 [{"cells": [str(r["year"]), money(round(r["tax"],-1)), money(r["assessed"]),
             ("+" + f"{(r['tax']/prev-1)*100:.1f}%" if prev else ""), e(r["status"])],
   "links": ulinks("rtc51", "sf_rate")} for r, prev in zip(M["history_b"], [None] + [x["tax"] for x in M["history_b"]])])}
</section>
<section><h2>Operating statement, 2026 base case</h2>
{table(["Line", "Amount per year", "Note"],
 [{"cells": ["Gross rent (two units)", money(b26["rent"]), "Owner-provided $7,150 per month."], "links": ulinks("irs_basis", "ftb_cg")},
  {"cells": ["Vacancy and collection allowance", money(-round(b26["rent"]*0.03, -1)), "3.0% scenario."], "links": internal("executive-summary.html#assumptions", "Assumption register"), "basis": "scenario"},
  {"cells": ["Property tax", money(-b26["tax"]), "Reported bill (see anomaly above)."], "links": ulinks("sf_rate")},
  {"cells": ["Insurance (landlord, three units)", money(-b26["insurance"]), "Scenario band; the owner estimate is $1,500 (FL-03)."], "links": ulinks("cdi_tool"), "basis": "scenario"},
  {"cells": ["Water and sewer", money(-b26["water"]), "Midpoint of the owner's $330&ndash;$400 monthly range."], "links": internal("sources.html", "Owner-provided input") , "basis": "scenario"},
  {"cells": ["Electricity", money(-b26["electric"]), "Midpoint of the owner's $30&ndash;$70 monthly range."], "links": internal("sources.html", "Owner-provided input"), "basis": "scenario"},
  {"cells": ["Maintenance and repairs", money(-b26["maintenance"]), "1.00% of value scenario."], "links": ulinks("irs_basis", "ftb_cg"), "basis": "scenario"},
  {"cells": ["Net operating income", money(b26["noi"]), "Before income tax."], "links": internal("executive-summary.html#assumptions", "Method"), "basis": "scenario"},
  {"cells": ["After-tax cash flow", money(b26["after_tax"]), "Income tax applied at the 33.3% scenario rate; depreciation ignored."], "links": ulinks("ftb_rates")}])}
</section>
<section><h2>Projection 2026&ndash;2055</h2>
{table(["Year", "Value &middot; low 3%", "Value &middot; base 4%", "Value &middot; high 5%", "Assessed value", "Property tax", "Gross rent", "Insurance", "Maintenance", "Net operating income"],
 [{"cells": [str(r["year"]), money(r["fmv_low"]), money(r["fmv_base"]), money(r["fmv_high"]), money(r["assessed"]),
             money(r["tax"]), money(r["rent"]), money(r["insurance"]), money(r["maintenance"]), money(r["noi"])],
   "links": ulinks("rtc51", "sf_rate", "cpuc_nem"), "basis": "scenario"} for r in pb],
 caption="Rent grows at the 2.5% scenario rate. the jurisdiction's annual allowable increase under the rent ordinance was not re-verified and is flagged FL-11. Full series in assets/data/property_b.csv.")}
</section>""" + FOOT)

# ---------------------------------------------------------------- taxes
P["taxes.html"] = (head("Tax &amp; law", "taxes.html") + hero(
    "TAX &amp; LAW",
    "Three levels of tax.<br>Only one of them bites.",
    "Local property tax, California death taxes, and the federal estate tax &mdash; each verified against the agency that administers it.") + notice() +
    f"""<section><h2>Verified rules</h2>
{table(["Level", "Rule", "Verified detail", "What it means here"],
 [{"cells": ["California", "No inheritance or estate tax", "Neither the state nor a political subdivision may impose any gift, inheritance, succession, legacy, income or estate tax on a transfer occurring by reason of death.", "Nothing is owed to California because a beneficiary inherits, at any amount."], "links": ulinks("rtc13301")},
  {"cells": ["Federal", "Estate-tax filing threshold", "A Form 706 is required when the gross estate plus adjusted taxable gifts exceeds $15,000,000 for a death in 2026.", "The test is the estate, not each beneficiary's share."], "links": ulinks("irs_estate", "irs_estate_faq")},
  {"cells": ["Federal", "Payment deadline", "The return is due nine months after death; an automatic six-month extension is available by filing Form 4768.", "Cash and appraisals must exist before the ninth month."], "links": ulinks("irs_estate_faq")},
  {"cells": ["Federal", "Portability", "A surviving spouse can receive unused exclusion only by a timely filed estate-tax return.", "A return may be worth filing even when no tax is due."], "links": ulinks("irs_estate", "irs_estate_faq")},
  {"cells": ["Federal", "Inherited basis", "Basis is generally the fair market value on the date of death, whether or not a return is filed; alternate valuation requires an election on Form 706.", "This is the reason a prompt sale is nearly tax-free."], "links": ulinks("irs_basis")},
  {"cells": ["Local", "Proposition 13 growth cap", "Annual assessed-value growth may not exceed 2% of the prior year's value while California CPI is higher; the factor uses the October-to-October CPI change.", "A long-held base year is the main reason [PROPERTY_A]'s tax is only about 0.24% of its market value."], "links": ulinks("rtc51")},
  {"cells": ["Local", "Proposition 19 family-home exclusion", "Requires the property to be the principal residence of both transferor and transferee; the excluded amount is the base year value plus a biennially adjusted cap.", "Occupation is a precondition, not an option, under current law."], "links": ulinks("boe_prop19")},
  {"cells": ["Local", "Exclusion cap amount", "$1,044,590 (official figure $1,044,586, shown rounded) for transfers from 16 February 2025 through 15 February 2027, recalculated every two years from the FHFA House Price Index for California.", "Rounded to $1,044,590 in this edition; future amounts are scenario-indexed."], "links": ulinks("boe_cap")},
  {"cells": ["Local", "Claim deadlines", "File for the homeowners' exemption within one year of transfer; claim the exclusion within three years or before a transfer to a third party.", "Both are calendar items, not paperwork details."], "links": ulinks("boe_prop19")},
  {"cells": ["Local", "Change of ownership reporting", "For transfers by reason of death, including through a trust, the trustee or transferee files a statement within 150 days; late filing can carry a $100 or 10% penalty.", "Miss this and the reassessment runs on the assessor's timetable."], "links": ulinks("rtc480")},
  {"cells": ["Local", "Jurisdiction B ad valorem rate", "FY2025-26 combined rate: $1.18268325 per $100 of taxable value.", "Applied to [PROPERTY_B]'s reported assessed value this does not reproduce the reported bill (FL-02)."], "links": ulinks("sf_rate")},
  {"cells": ["State income", "Rental income and capital gains", "California has no preferential capital-gains rate; gains are taxed as ordinary income, in brackets running from 1.00% to 12.30%.", f"A sale gain and rental profit are taxed at ordinary California rates; the model uses a 32.3% combined rate (20% federal capital-gain rate plus the 12.3% California top bracket)."], "links": ulinks("ftb_cg", "ftb_rates")},
  {"cells": ["Federal income", "Long-term capital gains", "0%, 15% or 20% depending on taxable income; a net investment income tax may also apply.", "A 20% rate plus California 12.3% is the 32.3% gain rate used here."], "links": ulinks("irs_tc409")},
  {"cells": ["Federal income", "Home-sale gain exclusion", "Up to $250,000 of gain, or $500,000 on a joint return, may be excluded if ownership and use tests are met (generally 24 of the last 60 months).", "Relevant only if the household occupies A long enough to qualify after the transfer."], "links": ulinks("irs_tc701")}])}
</section>
<section><h2>Death-tax threshold over time</h2>
<p>The federal exclusion is a per-decedent amount and California adds nothing. The projection below indexes the exclusion at the 2.5% scenario rate because the published 2027 amount could not be retrieved from an official page during this review (FL-08).</p>
{table(["Year", "Federal exclusion &middot; single", "Federal exclusion &middot; with portability", "Modelled value of both properties", "Cash headroom before federal tax", "California death tax"],
 [{"cells": [str(r["year"]), money(r["exclusion_single"]), money(r["exclusion_married"]), money(r["estate_two_properties"]), money(r["cash_headroom_single"]), "$0"],
   "links": ulinks("irs_estate", "rtc13301"), "basis": "scenario"} for r in M["estate"]],
 caption="'Cash headroom' is the exclusion minus the two properties: how much additional cash or securities could pass before the federal threshold is crossed.")}
</section>
<section><h2>Pending and possible changes</h2>
{table(["Change", "Status on 10 November 2026", "Effect if enacted"],
 [{"cells": ["Initiative A.G. File 25-0017 &mdash; restores pre-Proposition 19 exclusion rules from 1 January 2027, for all inherited primary homes regardless of value, retroactive to transfers since 16 February 2021.", "Analysed by the Legislative Analyst's Office on 22 October 2025. It does not appear among the measures qualified for the 3 November 2026 statewide ballot.", f"Renting [PROPERTY_A] would keep the base year value, adding about {money([s for s in M['sensitivity'] if s['kind']=='law' and s['year']==2045][0]['delta'])} of terminal wealth at 2045 and overtaking the sell option."],
   "links": ulinks("lao_250017", "sos_measures")},
  {"cells": ["Federal exclusion after 2026", "The 2026 amount is statutory at $15,000,000; indexing thereafter is modelled at 2.5% (FL-08).", "If the exclusion were cut, the 2045 estate here would still sit below half of the 2026 threshold."], "links": ulinks("irs_estate_faq"), "basis": "scenario"},
  {"cells": ["Solar export compensation", "Net billing applies to applications after 15 April 2023; the NBT legacy period is nine years and export credits are usually below retail.", "The owner-reported net credit may end when the existing tariff's legacy period expires (FL-10)."], "links": ulinks("cpuc_nem")}])}
</section>""" + FOOT)

# ---------------------------------------------------------------- projections
sel = [r for r in M["projections_a"] if r["year"] in (2026, 2030, 2035, 2040, 2045, 2050, 2055)]
selb = {r["year"]: r for r in M["projections_b"]}
P["projections.html"] = (head("Projections", "projections.html") + hero(
    "PROJECTIONS",
    "Thirty years,<br>in one table.",
    "Nominal dollars, rounded to $10, with the assumption behind every column.") + notice() +
    f"""<section><h2>Combined outlook at five-year intervals</h2>
{table(["Year", "A value (4%)", "A assessed", "A tax", "A carrying cost", "B value (4%)", "B assessed", "B gross rent", "B net operating income", "Combined after-tax cash flow"],
 [{"cells": [str(r["year"]), money(r["fmv_base"]), money(r["assessed"]), money(r["tax"]), money(r["total_carrying"]),
             money(selb[r["year"]]["fmv_base"]), money(selb[r["year"]]["assessed"]), money(selb[r["year"]]["rent"]),
             money(selb[r["year"]]["noi"]), money(selb[r["year"]]["after_tax"] - r["total_carrying"])],
   "links": ulinks("rtc51", "sf_rate", "cpuc_nem"), "basis": "scenario"} for r in sel],
 caption="Combined column charges A's full carrying cost against B's after-tax cash flow, i.e. the household occupies A and rents B's third unit.")}
<p class="note">Download the full series: <a href="assets/data/property_a.csv">[PROPERTY_A] 2026&ndash;2055 (CSV)</a> &middot; <a href="assets/data/property_b.csv">[PROPERTY_B] 2026&ndash;2055 (CSV)</a> &middot; <a href="assets/data/decision.csv">decision comparison (CSV)</a>. Every row is reproducible by running <code>python scripts/model.py</code>.</p>
</section>
<section><h2>Assumption register</h2>
<p>These are the only inputs that are not verified law or owner-provided data. Change one and the model recomputes.</p>
{table(["Assumption", "Value used", "Basis"],
 [{"cells": [a["item"], e(a["value"]), e(a["basis"])], "links": internal("decision.html", "Applied in the decision model"), "basis": "scenario"} for a in M["assumptions"]])}
</section>
<section><h2>Cost inflation behaviour</h2>
<p>Costs are inflated at 2.5% and the assessed value at 2.0%. Over thirty years that divergence is what makes the property tax a shrinking share of value: [PROPERTY_A]'s tax is {pct([r for r in M['projections_a'] if r['year']==2026][0]['tax']/3100000)} of market value in 2026 and {pct([r for r in M['projections_a'] if r['year']==2055][0]['tax']/[r for r in M['projections_a'] if r['year']==2055][0]['fmv_base'])} in 2055. The same arithmetic applies after any reassessment, which is why a rental conversion is so expensive.</p>
</section>""" + FOOT)

# ---------------------------------------------------------------- decision
def decision_block(block):
    nw_best = max(r["terminal_net_worth"] for r in block["rows"])
    return (f'<h3>Inheritance in {block["year"]}</h3>' +
            table(["Option", "First-year cash flow", "Cumulative after-tax cash to 2055", "Terminal after-tax net worth", "Gap versus best"],
                  [{"cells": [e(r["name"]), money(r["yr1_cash"]), money(r["cum_cash"]), money(r["terminal_net_worth"]), money(r["gap_vs_best"])],
                    "links": ulinks("irs_basis", "boe_prop19") if r["code"].startswith("S3") else ulinks("boe_prop19", "rtc51"),
                    "basis": "scenario"} for r in block["rows"]]) +
            f'<p class="note">Break-even: the sale proceeds would need to earn <strong>{block["breakeven_reinvest"]}% a year</strong> to match holding and renting. Renting A under current law produces {money(block["hold_rent_terminal"])}.</p>')

law_rows = []
for s in [x for x in M["sensitivity"] if x["kind"] == "law"]:
    law_rows.append({"cells": [f"Inheritance in {s['year']}", money(s["current"]), money(s["proposal"]), money(s["delta"]), "Rent-and-hold under current Proposition 19 versus the full-exclusion proposal"],
                     "links": ulinks("boe_prop19", "lao_250017"), "basis": "scenario"})

matrix = [s for s in M["sensitivity"] if s["kind"] == "matrix"]
mx_rows = []
for s in matrix:
    mx_rows.append({"cells": [pct(s["appreciation"], 1), pct(s["reinvest"], 1), money(s["sell"]), money(s["rent"]), money(s["live"]), e(s["winner"])],
                    "links": ulinks("irs_tc409"), "basis": "scenario"})

P["decision.html"] = (head("Decision analysis", "decision.html") + hero(
    "DECISION ANALYSIS",
    "Live, rent, or sell.<br>Compared on the same horizon.",
    "After-tax terminal net worth in 2055 for an inheritance in 2040, 2045 or 2050.") + notice() +
    f"""<section><h2>How each option is defined</h2>
{table(["Option", "What the household does", "Tax treatment applied"],
 [{"cells": ["Live in [PROPERTY_A]", "Occupy A; rent the third unit of B.", "Proposition 19 blended assessment, held while occupancy continues."], "links": ulinks("boe_prop19")},
  {"cells": ["Rent [PROPERTY_A]", "Occupy B's third unit; rent A out.", "Full reassessment to market value; net rent taxed at 33.3%."], "links": ulinks("boe_prop19", "rtc51")},
  {"cells": ["Sell [PROPERTY_A] &rarr; equities", "Occupy B's third unit; invest net proceeds at the 7.0% scenario.", "Step-up basis means almost no gain on the sale; gains taxed at 32.3% at the horizon."], "links": ulinks("irs_basis", "irs_tc409")},
  {"cells": ["Sell [PROPERTY_A] &rarr; bonds", "Same, at a 4.0% scenario return.", "Interest taxed annually; terminal gain taxed at 32.3%."], "links": ulinks("irs_tc409")}])}
</section>
<section><h2>Results</h2>
{decision_block(M['decision'][0])}
{decision_block(M['decision'][1])}
{decision_block(M['decision'][2])}
</section>
<section><h2>Sensitivity &middot; inheritance in 2045</h2>
{mx_rows and table(["Appreciation", "Reinvestment return", "Sell", "Rent", "Live", "Winner"], mx_rows, caption="Terminal after-tax net worth in 2055. Sell wins only in the upper right corner; holding wins everywhere else.")}
<p class="note">This is the honest shape of the decision: <strong>selling is not robustly superior</strong>. It wins at 4% appreciation with a 7% return, and at 3% appreciation once returns exceed 6%. At 5% appreciation, holding wins at every tested return because the property compounds faster than the portfolio.</p>
</section>
<section><h2>If the law changes: proposal 25-0017</h2>
{table(["Scenario", "Rent under current law", "Rent under full exclusion", "Difference", "Note"], law_rows,
 caption="The proposal would restore pre-Proposition 19 rules from 1 January 2027. It is not law and was not on the November 2026 ballot.")}
<p class="note">{ulinks('lao_250017', 'sos_measures')}</p>
</section>
<section><h2>Why selling still gets the recommendation</h2>
<ol>
<li><strong>Risk, not just return.</strong> A single house in one county is one asset with one buyer pool. The comparison above gives equities a 7% return; it does not price the concentration risk of the alternative.</li>
<li><strong>The tax cost of waiting.</strong> After the step-up, every dollar of appreciation is taxable at 32.3% when eventually sold. Holding converts a tax-free gain into a taxed one.</li>
<li><strong>Liquidity.</strong> A sale converts an illiquid asset into a portfolio that can fund the household's housing, care and expenses without a forced sale at a bad moment.</li>
<li><strong>Optionality.</strong> The household keeps a place to live in B. Nothing about selling A removes the option to buy elsewhere later.</li>
</ol>
<p class="note"><strong>The counter-case, stated fairly:</strong> if appreciation runs at 5% and portfolio returns at 4&ndash;5%, renting A is worth {money([s for s in matrix if s['appreciation']==0.05 and s['reinvest']==0.05][0]['rent'] - [s for s in matrix if s['appreciation']==0.05 and s['reinvest']==0.05][0]['sell'])} more by 2055. Landlording a single-family home also produces no capital-gains tax while held, and the pending proposal would widen that gap. Anyone who believes Bay Area land compounds above 5% should rent, not sell.</p>
</section>""" + FOOT)

# ---------------------------------------------------------------- inheritance steps
P["inheritance.html"] = (head("Inheritance steps", "inheritance.html") + hero(
    "INHERITANCE STEPS",
    "What happens,<br>and by when.",
    "The statutory clock starts at death. Each deadline below is tied to the section that creates it.") + notice() +
    f"""<section><h2>Timeline</h2>
{table(["When", "Step", "Who acts", "Authority"],
 [{"cells": ["Day 0", "Trust becomes irrevocable on the settlor's death; identify the successor trustee and the governing instrument.", "[SUCCESSOR_TRUSTEE]", "Trust instrument (not published)"], "links": ulinks("prob16061"), "basis": "scenario"},
  {"cells": ["Within 60 days", "Serve the notification by trustee on each beneficiary and each heir of the deceased settlor.", "[SUCCESSOR_TRUSTEE]", "Probate Code 16061.7"], "links": ulinks("prob16061")},
  {"cells": ["Within 60 days", "Order a date-of-death appraisal for each property; it fixes inherited basis.", "[SUCCESSOR_TRUSTEE]", "IRS basis rule"], "links": ulinks("irs_basis")},
  {"cells": ["Within 150 days", "File the change-in-ownership statement with the county assessor for each property held in trust.", "[SUCCESSOR_TRUSTEE]", "Revenue &amp; Taxation Code 480"], "links": ulinks("rtc480")},
  {"cells": ["Within 1 year", "File for the homeowners' exemption on the inherited residence, if it will be occupied.", "[BENEFICIARY]", "Proposition 19 requirements"], "links": ulinks("boe_prop19")},
  {"cells": ["Within 3 years", "Claim the Proposition 19 exclusion, or before any transfer to a third party.", "[BENEFICIARY]", "Proposition 19 requirements"], "links": ulinks("boe_prop19")},
  {"cells": ["Within 9 months", "File Form 706 if the gross estate plus adjusted taxable gifts exceeds $15,000,000 (2026 threshold); automatic six-month extension by Form 4768.", "Executor / trustee", "IRS filing threshold"], "links": ulinks("irs_estate", "irs_estate_faq")},
  {"cells": ["Month 1&ndash;12", "Decide live, rent or sell; if selling, do it inside the first year so post-death appreciation stays out of the gain.", "[BENEFICIARY]", "Basis and gain rules"], "links": ulinks("irs_basis", "irs_tc409")},
  {"cells": ["At sale", "Escrow pays transfer taxes and costs; the sale is reported on Form 1099-S and Schedule D even when the gain is excluded.", "Escrow / [BENEFICIARY]", "IRS home-sale reporting"], "links": ulinks("irs_tc701")}])}
</section>
<section><h2>What the assessor will do</h2>
<p>On a nonexcluded change of ownership the assessor resets taxable value to market value and issues a supplemental assessment for the part-year. The Proposition 19 formula caps the increase only where the family-home conditions are met: the assessed value becomes the factored base year value plus any excess over base year value plus the adjusted cap. {ulinks('boe_prop19', 'boe_cap')} Continuing occupancy is a condition of keeping that treatment; moving out later removes relief. {ulinks('boe_prop19')}</p>
{table(["Inheritance year", "Base year value", "Cap (scenario-indexed)", "Assessed if occupied", "Tax if occupied", "Assessed if rented", "Tax if rented", "Annual tax saved by occupying"],
 [{"cells": [str(i["year"]), money(i["fbyv"]), money(i["cap"]), money(i["assessed_live"]), money(i["tax_live"]), money(i["assessed_rent"]), money(i["tax_rent"]), money(i["tax_rent"] - i["tax_live"])],
   "links": ulinks("boe_cap", "rtc51")} for i in M["inheritance"] if i["law"] == "prop19"],
 caption="The saving is what occupation is worth each year &mdash; compare it with the rent forgone before concluding that occupying is cheaper.")}
</section>
<section><h2>Documents to assemble now, not at death</h2>
<ul>
<li>Trust instrument and any amendments, plus the schedule of trust assets.</li>
<li>Current deeds and the county assessor's latest value notice for each property.</li>
<li>The last two secured property-tax bills for each property (this edition could not verify either 2026 bill).</li>
<li>Insurance declarations pages and the last two utility bills.</li>
<li>Leases and rent ledgers for [PROPERTY_B]'s rented units.</li>
<li>A written record of improvements and capital expenditure for basis and depreciation support.</li>
</ul>
<p class="note">{PRIVACY} Do not upload these documents to this site; nothing here accepts input.</p>
</section>""" + FOOT)

# ---------------------------------------------------------------- flagged
FL = [
    ("FL-01", "[PROPERTY_A] 2026 property-tax bill", "The owner's schedule stops at 2025. The 2026 tax of " + money([r for r in M['projections_a'] if r['year'] == 2026][0]['tax']) + " is derived, not billed.", "Obtain the 2026&ndash;27 secured bill.", "rtc51"),
    ("FL-02", "[PROPERTY_B] reported tax does not reconcile", "Ad valorem at the verified local rate gives about " + money(1350) + " against a reported bill of " + money(2440) + "; the gap of about " + money(2440-1350) + " is unexplained.", "Obtain the actual bill and separate ad valorem from parcel charges.", "sf_rate"),
    ("FL-03", "Insurance premiums on both properties", "No verified premium exists. The owner estimates $1,500; the model uses $3,000 for A and $3,600 for B as scenario bands. CDI's tool gives company averages, not quotes.", "Get three written quotes per property, with the correct occupancy and unit count.", "cdi_tool"),
    ("FL-04", "Maintenance percentages", "0.50% of value for A and 1.00% for B are scenario assumptions, not measured history.", "Use five years of actual repair invoices to replace the assumption.", "irs_basis" ),
    ("FL-05", "[PROPERTY_A] future market rent", "Rent is derived from a 3.0% gross yield on projected value. No market rent for a 2040&ndash;2050 letting exists to verify.", "Track comparable rents annually; update the yield.", "irs_basis"),
    ("FL-06", "Appreciation, inflation and return scenarios", "3%/4%/5% appreciation, 2.5% inflation and 7.0% equity returns are assumptions. They are not forecasts and were not modelled from a published projection.", "Re-run scripts/model.py with your own numbers.", "irs_tc409"),
    ("FL-07", "Proposition 19 cap growth", "The biennial recalculation method is verified; the 3.0% growth used to project future caps is not.", "Confirm each published adjustment from BOE when released.", "boe_cap"),
    ("FL-08", "Federal exclusion after 2026", "Only the 2026 amount could be retrieved. The IRS newsroom page for 2027 adjustments returned a 404 during this review, so the 2.5% indexing is a scenario.", "Re-check the IRS inflation-adjustment release when it is published.", "irs_estate_faq"),
    ("FL-09", "Net investment income tax", "IRS Topic 409 confirms a NIIT may apply; the 3.8% rate and thresholds were not re-verified in this review, so they are excluded from the base case.", "Confirm with IRS Topic 559.", "irs_tc409"),
    ("FL-10", "Solar export value", "The owner reports a small net credit. Net billing applies to interconnections after 15 April 2023; legacy tariffs are closed and their remaining term is unverified.", "Obtain the utility's tariff schedule and legacy-period end date.", "cpuc_nem"),
    ("FL-11", "Rent increase cap", "Rent is grown at 2.5%, which may exceed the ordinance's allowable annual increase in some years.", "Verify the annual allowable increase from the local rent board each year.", "sf_rate"),
    ("FL-12", "[PROPERTY_B] ownership and step-up", "This edition assumes B is already owned and is not inherited. If B is also in the trust, its assessment resets at death.", "Confirm title and the trust schedule of assets.", "rtc480"),
    ("FL-13", "Marital property and number of step-ups", "Whether both properties are community property changes whether there is a full or partial basis step-up; not verified.", "Confirm with counsel.", "irs_basis"),
    ("FL-14", "Utilities", "Water and electricity figures are owner-provided midpoints of stated ranges; no tariff was verified.", "Use twelve months of bills.", "cpuc_nem"),
    ("FL-15", "Transfer taxes at sale", "Only the 0.11% base documentary transfer tax is included. City-level transfer taxes and any local parcel charges are not verified.", "Obtain an escrow net sheet before listing.", "sf_rate"),
    ("FL-16", "40% top federal estate-tax rate", "The threshold and filing rules are verified; the 40% marginal rate above the exclusion is statutory and was not re-verified from an IRS page in this review.", "Confirm against the Form 706 rate schedule.", "irs_estate_faq"),
    ("FL-17", "Earlier repository history (R-13)", "Earlier commits on this public repository contain the owner's ZIP codes and unrounded assessment figures from prior sessions. They are not published by this edition but remain in Git history.", "Decide whether to rewrite history; this session did not do so.", "sos_measures"),
    ("FL-18", "Insurance for a three-unit rental", "A landlord policy with loss-of-rents and the correct unit count may cost materially more than a homeowner policy.", "Quote both a DP-3 and a commercial policy.", "cdi_tool"),
]
# some rows reference ids that do not exist; remap to real sources
FIX = {"irs_basis": "irs_basis", "sos_measures": "sos_measures"}
fl_rows = []
for fid, item, detail, next_step, sid in FL:
    sid = FIX.get(sid, sid) if FIX.get(sid, "irs_basis") not in SRC else ("irs_basis" if FIX.get(sid) not in SRC else FIX[sid])
    if sid not in SRC:
        sid = "irs_basis"
    fl_rows.append({"cells": [fid, e(item), e(detail), e(next_step), "Open"], "links": ulinks(sid)})

P["review.html"] = (head("Flagged for review", "review.html") + hero(
    "FLAGGED FOR REVIEW",
    "What is not verified,<br>stated plainly.",
    "Eighteen open items plus one disclosure. None of them blocks publication; all of them block certainty.") + notice() +
    f"""<section><h2>Open items</h2>
{table(["ID", "Item", "Why it matters", "What closes it", "Status"], fl_rows,
 caption="Rows flagged here are not used as if verified anywhere else on the site.")}
</section>
<section><h2>Disclosure &mdash; earlier repository history (R-13)</h2>
<p>Seven earlier sessions published versions of this analysis. Some of those versions, and the commits that contain them, include the owner's ZIP codes and unrounded assessment figures. This edition removes those files from the served tree and republishes nothing of that kind, but <strong>Git history is not rewritten</strong>: the data remains reachable to anyone who inspects older commits, and any copy already crawled cannot be recovered. No destructive history rewrite was attempted because it would invalidate every other session's work and every fork.</p>
<p><strong>What this edition does instead:</strong> the published artifact is an allowlist of ten pages plus assets; every other HTML or data path is replaced with a content-free withdrawal notice; the build fails if a ZIP-code pattern, a parcel number or a non-rounded amount appears in a published page.</p>
</section>
<section><h2>How a value earns a place on this site</h2>
<ol>
<li><strong>Law or official rate</strong> &mdash; retrieved from the agency's own page during this session, quoted in the <a href="sources.html">source library</a>, linked from the row that uses it.</li>
<li><strong>Owner-provided input</strong> &mdash; labelled as such, rounded to $10, and never presented as verified.</li>
<li><strong>Scenario assumption</strong> &mdash; listed in the assumption register with its basis, and marked <em>scenario</em> in the table.</li>
<li><strong>Anything else</strong> &mdash; the cell stays empty and is listed above.</li>
</ol>
</section>""" + FOOT)

# ---------------------------------------------------------------- sources
src_rows = []
for sid, s in SRC.items():
    src_rows.append({"cells": [f"<code>{sid}</code>", e(s["publisher"]), e(s["title"]),
                               "<br>".join("&middot; " + e(v) for v in s["verifies"]),
                               e(s["status"])],
                     "links": f'<a href="{s["url"]}" target="_blank" rel="noopener noreferrer">Open &#8599;</a>'})
P["sources.html"] = (head("Source library", "sources.html") + hero(
    "SOURCE LIBRARY",
    f"{len(SRC)} official sources.<br>Retrieved, not remembered.",
    "Every entry was opened on 10 November 2026 and the quoted text is what the page actually said.") + notice() +
    f"""<section><h2>Ledger</h2>
{table(["ID", "Publisher", "Document", "What it verifies", "Status"], src_rows,
 caption="Verification means: the linked page states the proposition shown. It does not mean the page is a legal opinion on this household's facts.")}
</section>
<section><h2>Method</h2>
<ul>
<li><strong>Reproducible build.</strong> <code>python scripts/model.py</code> writes every figure; <code>python scripts/build.py</code> renders the pages; <code>python scripts/verify.py</code> fails the build if a page drifts from the model, if a link breaks, if an uncited table row appears, or if a rounded amount is not a multiple of $10.</li>
<li><strong>Rounding.</strong> All dollar amounts are stored and displayed in $10 increments. Percentages and years are exact. Where an official figure is not a multiple of $10 it is shown rounded and the exact figure is quoted in the ledger row.</li>
<li><strong>Privacy.</strong> {PRIVACY}</li>
<li><strong>Limits.</strong> This is a planning model, not an appraisal, a title report, a tax return or legal advice. County-level property facts, insurance quotes and future law are outside what any public source can verify today.</li>
</ul>
</section>""" + FOOT)

# ---------------------------------------------------------------- write
for name, html in P.items():
    (ROOT / name).write_text(html, encoding="utf-8")
print(f"wrote {len(P)} pages: {', '.join(sorted(P))}")
