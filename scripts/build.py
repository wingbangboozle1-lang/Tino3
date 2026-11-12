#!/usr/bin/env python3
"""Render the public pages from assets/data/model.json and assets/sources.json.

Every table row ends with a Basis badge and at least one link to an official publisher.
Values that could not be confirmed from an official source are left blank and listed on review.html.
"""
from __future__ import annotations
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M = json.loads((ROOT / "assets" / "data" / "model.json").read_text(encoding="utf-8"))
SRC = json.loads((ROOT / "assets" / "sources.json").read_text(encoding="utf-8"))["sources"]

NAV = [("index.html", "Overview"), ("executive-summary.html", "Executive summary"),
       ("questions.html", "Questions and answers"), ("suggestions.html", "Suggestions and paths"),
       ("decision.html", "Decision analysis"), ("projections.html", "Year-by-year projections"),
       ("black-swans.html", "Conditions and history"), ("stress.html", "Stress tests"),
       ("property-a.html", "Property A"), ("property-b.html", "Property B"),
       ("taxes.html", "Tax, thresholds, law watch"), ("inheritance.html", "Inheritance steps"),
       ("review.html", "Flagged for review"), ("audit.html", "Independent verification"),
       ("sources.html", "Source library")]

# Navigation is grouped so a reader sees the shape of the site: start here (what is settled and what
# is not), one decision, one black-swan section in two parts, two properties, the rules, the evidence.
NAV_GROUPS = [("Start here", 0, 4), ("The decision", 4, 6), ("Black swans", 6, 8),
              ("The properties", 8, 10), ("Tax and process", 10, 12), ("Evidence", 12, 15)]

SHORT = {"Internal Revenue Service": "IRS", "California State Board of Equalization": "BOE",
         "California Legislative Information": "CA code", "California Franchise Tax Board": "FTB",
         "California Public Utilities Commission": "CPUC", "California Department of Insurance": "CDI",
         "California Legislative Analyst's Office": "LAO", "California Secretary of State": "CA SOS",
         "California State Controller": "CA Controller", "U.S. Department of the Treasury": "US Treasury",
         "Federal Retirement Thrift Investment Board": "TSP", "U.S. Department of Housing and Urban Development": "HUD",
         "Federal Reserve Bank of St. Louis (data: Federal Housing Finance Agency)": "FHFA index",
         "Federal Reserve History": "Fed History",
         "Board of Governors of the Federal Reserve System": "Federal Reserve",
         "U.S. Government Publishing Office (GovInfo)": "US Code (GPO)",
         "Bureau of Labor Statistics": "BLS", "Congressional Budget Office": "CBO",
         "Social Security Administration": "SSA",
         "Federal Reserve Bank of St. Louis (data: Board of Governors)": "FRED (Fed funds)",
         "Federal Reserve Bank of St. Louis (data: Bureau of Labor Statistics)": "FRED (BLS)",
         "Federal Reserve Bank of St. Louis (data: Freddie Mac)": "FRED (Freddie Mac)",
         "Federal Reserve Bank of St. Louis (data: U.S. Treasury)": "FRED (Treasury)",
         "Federal Reserve Bank of St. Louis (data: Nasdaq)": "FRED Nasdaq",
         "Federal Reserve Bank of St. Louis (data: Board of Governors of the Federal Reserve System)": "FRED 10-yr",
         "U.S. Bureau of Labor Statistics": "BLS",
         "Federal Reserve History (Federal Reserve System)": "Fed History",
         "Federal Reserve Bank of New York (Liberty Street Economics)": "NY Fed"}
LABEL = {"irs_estate": "Estate tax thresholds", "irs_2027": "2027 amounts", "irs_rp2635": "Rev. Proc. 2026-35",
         "irs_whatsnew": "What's new", "irs_rp2532": "Rev. Proc. 2025-32", "irs_i706": "Form 706 instructions",
         "irs_basis": "Inherited basis", "irs_rr2023_2": "Rev. Rul. 2023-2", "irs_tc409": "Capital gains",
         "irs_tc559": "Net investment income tax", "irs_tc701": "Sale of your home", "irs_p925": "Passive losses",
         "irs_p527": "Rental property", "sco_estate": "Estate tax", "rtc13301": "RTC 13301", "boe_prop19": "Proposition 19",
         "boe_lta25009": "Letter 2025/009", "boe_lta26026": "Letter 2026/026", "rtc63_2": "RTC 63.2",
         "boe_lta26002": "Letter 2026/002", "rtc480": "RTC 480", "prob16061_7": "Probate 16061.7", "rtc11911": "RTC 11911",
         "rtc11930": "RTC 11930", "cnty_a_recorder": "Transfer tax", "cnty_a_rates": "Tax rate book",
         "cityb_rate": "Secured tax rate", "cityb_res447": "Rate resolution", "cityb_transfer": "Transfer tax table",
         "cityb_rent": "Rent increases", "cityb_rentfee": "Rent Board fee", "lao_250017": "Initiative 25-0017",
         "sos_measures": "2026 measures", "sos_memo": "Initiative failed", "ftb_cg": "Capital gains", "ftb_rates": "Rate schedules", "cpuc_nem": "Net metering",
         "cdi_compare": "Premium survey", "treasury_cmt": "Yield curve", "tsp_returns": "Index fund returns",
         "fred_hpi_a": "Area A", "fred_hpi_b": "Area B", "hud_fmr": "Fair Market Rents",
         "fed_2goal": "2% inflation goal", "ssa_trustees": "Trustees' assumptions", "cbo_outlook": "Budget outlook",
         "frh_oil": "Oil shock", "frh_1987": "Crash of 1987", "frh_recession": "Great Recession",
         "fed_mpr2001": "MPR Feb 2001", "bls_cpi": "CPI Oct 2026", "sos_results": "Election results",
         "fred_fedfunds": "Fed funds rate", "fred_unrate": "Unemployment rate", "fred_mortgage": "Mortgage rates",
         "fred_casthpi": "House prices, state", "fred_usthpi": "House prices, US", "fred_dgs10": "10-year Treasury yield",
         "bls_ted2022": "CPI, June 2022", "bls_mlr100": "CPI, 100 years", "bls_btn11": "Inflation periods",
         "fedhist_1929": "Crash of 1929", "fedhist_greatinflation": "The Great Inflation",
         "fedhist_greatrecession": "The Great Recession", "nyfed_covid": "COVID-19 and the Fed",
         "fred_ussthpi": "US house price index", "fred_nasdaqcom": "NASDAQ Composite",
         "uscode3124": "31 USC 3124", "uscode102": "26 USC 102", "irs_rmd_faq": "RMD FAQ",
         "cdi_tips": "Finding insurance", "cdi_fairplan": "FAIR Plan"}

e = html.escape


def a(sid):
    s = SRC[sid]
    pub = SHORT.get(s["publisher"], s["publisher"])
    return f'<a href="{e(s["url"])}" target="_blank" rel="noopener noreferrer">{e(pub)} &middot; {e(LABEL[sid])}</a>'


ASM = '<a href="decision.html#assumptions">Assumptions</a>'
FLG = '<a href="review.html">Flagged</a>'


def S(*ids, asm=False, flag=False):
    return "".join(a(i) for i in ids) + (ASM if asm else "") + (FLG if flag else "")


def usd(v):
    v = int(round(float(v)))
    assert v % 10 == 0, v
    return f"&minus;${abs(v):,}" if v < 0 else f"${v:,}"


def N(v):
    return ("n", usd(v))


def P(x, d=1):
    return ("n", f"{x * 100:.{d}f}%")


BLANK = ("blank", "Not verified &ndash; left blank")
BADGE = {"V": ("b-v", "Verified"), "O": ("b-o", "Owner-supplied"), "A": ("b-a", "Assumption"),
         "C": ("b-c", "Computed"), "U": ("b-u", "Unverified"), "X": ("b-x", "Your choice"),
         "S": ("b-c", "Status")}
LEGEND = ('<p class="legend">' + "".join(f'<span class="b {c}">{t}</span>' for c, t in BADGE.values()) +
          ' Verified = the figure was read in text from the official publisher\'s own domain between 10 and 12 November 2026; the source library says whether the whole page was opened or an excerpt was read. Owner-supplied = taken from the '
          'owner\'s records, not independently checked. Assumption = a scenario input. Computed = arithmetic on the '
          'rows above. Unverified = no official confirmation, so the value is blank. On owner-supplied, assumed and computed rows the link points to the official rule or data series the row rests on; it does not confirm the value.</p>')


def tbl(caption, headers, rows, cls=""):
    hd = "".join(f'<th scope="col">{h}</th>' for h in list(headers) + ["Basis", "Official source"])
    body = []
    for row in rows:
        cells, basis, src = row[0], row[1], row[2]
        rc = row[3] if len(row) > 3 else ""
        tds = "".join(f'<td class="{c[0]}">{c[1]}</td>' if isinstance(c, tuple) else f"<td>{c}</td>" for c in cells)
        bc, bt = BADGE[basis]
        attr = ' data-basis="choice"' if basis == "X" else ""
        body.append(f'<tr class="{rc}"{attr}>{tds}<td><span class="b {bc}">{bt}</span></td><td>{src}</td></tr>')
    return (f'<div class="table-wrap"><table class="{cls}"><caption>{caption}</caption><thead><tr>{hd}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def page(name, title, eyebrow, h1, lead, body):
    cur = 'aria-current="page" '
    links = []
    for group, start, stop in NAV_GROUPS:
        links.append(f'<div class="nav-group">{group}</div>')
        links.extend(f'<a {cur if href == name else ""}href="{href}"><span>{i:02d}</span>{label}</a>'
                     for i, (href, label) in enumerate(NAV, 1) if start < i <= stop)
    nav = "".join(links)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Inherited-home decision dashboard: sell, rent or move in. Official sources, anonymised.">
<meta name="referrer" content="no-referrer"><meta name="robots" content="noindex">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self'; img-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
<title>{title} &middot; Inheritance decision dashboard</title><link rel="stylesheet" href="assets/style.css"></head><body>
<a class="skip" href="#main">Skip to content</a>
<aside><a class="brand" href="index.html">Inheritance decision dashboard<small>Property A and Property B</small></a>
<nav aria-label="Main navigation">{nav}</nav>
<div class="aside-note">Anonymised. Dollar figures rounded to $10. Reviewed 10 to 12 November 2026.</div></aside>
<main id="main"><div class="top"><span>{eyebrow}</span><span>Reviewed 10 to 12 Nov 2026</span></div>
<div class="hero"><div class="eyebrow">{eyebrow}</div><h1>{h1}</h1><p>{lead}</p></div>
{body}
<footer><span>Planning analysis, not legal, tax or investment advice. Confirm with an estate attorney and a tax preparer before acting.</span><span>No names, addresses, ZIP codes or parcel numbers are published.</span></footer></main></body></html>
"""


def blk(y, g=0.04):
    return next(b for b in M["decision"] if b["year"] == y and abs(b["g"] - g) < 1e-9)


def opt(b, k):
    return next(r for r in b["rows"] if r["option"] == k)


AFTER = {x["year"]: x for x in M["after"]}
B45 = blk(2045)
SELL, TRE, RENT, LIVE = (opt(B45, k) for k in ("sell_stock", "sell_treasury", "rent", "live"))
A45 = AFTER[2045]
NOW_A, NOW_B = M["now"]["a"], M["now"]["b"]
BE = M["breakeven"]
LAW = M["law"]
BR45 = next(x for x in M["b_reset"] if x["year"] == 2045)
E45 = next(x for x in M["estate"] if x["year"] == 2045)

# Owner statement, 11 November 2026: Property B is already owned by the beneficiary, not by
# the parents. Under that statement Property B is not part of the decedent's taxable estate, so
# the federal exclusion is consumed by Property A and the cash only. The statement is
# owner-supplied: no deed was seen, so it changes the framing shown here and adds one computed
# room figure, but it does not remove the contingency tables (flag FL-01).
def r10(x):
    return int(round(float(x) / 10.0) * 10)


EX2045 = 15_480_000 * 1.025 ** 18                     # same arithmetic as the model's estate rows
A2045 = M["inputs"]["a_value"] * 1.04 ** 19
B2045 = M["inputs"]["b_value"] * 1.04 ** 19
assert abs(r10(EX2045 - (A2045 + B2045)) - E45["room_single_base"]) <= 10, "estate-room arithmetic drifted from the model"
B_VALUE_2045 = r10(B2045)
# Built from the published figures so the page adds up exactly: room (both homes) + Property B = room (statement).
ROOM_B_OWNED = E45["room_single_base"] + B_VALUE_2045  # one person's room in 2045 if the statement holds
assert abs(r10(EX2045 - A2045) - ROOM_B_OWNED) <= 10, "statement room drifted from exclusion less Property A"
PRIV = ('<div class="privacy"><strong>Privacy.</strong> Properties are Property A (a single-family home in County A) and '
        'Property B (a small multi-unit building in City B). People are [GRANTOR], [SUCCESSOR_TRUSTEE] and [BENEFICIARY]. '
        f'Assessment-roll values and tax bills are published at the precision the owner chose: {M["privacy"]["description"]}. '
        'That is the owner\'s instruction of 12 November 2026. Rounding to $10 protects against a search for an exact figure, '
        'but a roll value that close to the assessed roll, together with a 2% growth chain going back to 2014, can still be '
        'matched to a parcel by someone who is looking. The stronger protection is tier 2 (nearest $1,000) or tier 3 '
        '(nearest $10,000); <a href="suggestions.html#privacy">the privacy choice</a> sets out the trade-off and how to change it. '
        'Every other figure is rounded to the nearest $10.</div>')
PART1 = ('<div class="part-band"><strong>Black swans, part 1 of 2 &mdash; conditions and history.</strong> '
         'What the baseline assumes, fifty years of official inflation data, and the amounts that do not rise with '
         'inflation. Part 2 re-runs the inheritance decision against verified episodes: '
         '<a href="stress.html">stress tests</a>.</div>')
PART2 = ('<div class="part-band"><strong>Black swans, part 2 of 2 &mdash; stress tests.</strong> '
         'The verified episodes and the inheritance decision re-run under each of them. Part 1 sets out the baseline '
         'and the fifty-year record it contradicts: <a href="black-swans.html">conditions and history</a>.</div>')
PAGES = {}

# ------------------------------------------------------------------------------------------------ overview
rows = [([r["name"], N(r["wealth"]), N(r["wealth_today"]), N(r["gap"]), N(r["first_cash"]), N(r["tax_first"])], "C",
         S("irs_basis", "boe_prop19", asm=True), "best" if r["gap"] == 0 else "") for r in B45["rows"]]
body = f"""
<div class="answer"><p><strong>Best plan on these numbers: sell Property A soon after inheriting it, reinvest the proceeds, and keep Property B.</strong></p>
<p>Inheriting in 2045 with house prices rising 4% a year, selling and holding a stock index fund ends ten years later with {usd(SELL['wealth'])}.
Renting the home out ends with {usd(RENT['wealth'])} and moving in ends with {usd(LIVE['wealth'])}. All three are after every tax and selling cost.</p>
<p>Two rules drive this. First, the property tax resets when the home is inherited. Today's bill is about {usd(NOW_A['property_tax'])} a year. In 2045 it becomes
{usd(LIVE['tax_first'])} if a child moves in and {usd(RENT['tax_first'])} if the home is rented. Second, the sale is nearly tax-free, because the tax basis resets to the value at death.</p></div>
<div class="cards">
<div class="card win"><div class="k">Best option</div><div class="v">Sell and reinvest</div><p>Ahead of renting by {usd(-RENT['gap'])} and of moving in by {usd(-LIVE['gap'])} after ten years.</p></div>
<div class="card"><div class="k">Property A tax, 2045</div><div class="v">{usd(LIVE['tax_first'])}</div><p>If a child moves in. {usd(RENT['tax_first'])} if rented. {usd(LAW['tax_restored'])} if nothing changed.</p></div>
<div class="card"><div class="k">Cost of living in A</div><div class="v">{usd(B45['live_cost_month_today'])} a month</div><p>In today's dollars, compared with selling. That is the price of choosing the home over the money.</p></div>
<div class="card"><div class="k">Federal estate tax room, 2045</div><div class="v">{usd(E45['room_single_base'])}</div><p>Other assets one person could leave tax-free after both homes. The owner states Property B is already the heir's; under that statement the room is {usd(ROOM_B_OWNED)}. Scenario: see the tax page.</p></div>
</div>
{tbl("Inheritance in 2045, house prices rising 4% a year, result ten years later", ["Option", "Wealth after 10 years", "In today's dollars", "Behind the best by", "Cash in the first year", "Property A tax, first year"], rows)}
{LEGEND}
<section><h2>Five facts that could change the answer</h2>
<p>These are not known from the records supplied. Each one is on the <a href="review.html">Flagged for Review</a> page.</p>
<ol>
<li><strong>Who holds title to Property B today.</strong> The owner states the building is already owned by the beneficiary; the deed was not seen. Under that statement it is outside the estate and its tax does not reset. If the deed shows the parents instead, the tax resets as well: from about {usd(BR45['tax_keep'])} to {usd(BR45['tax_reset'])} a year in 2045.</li>
<li><strong>Which home is the parents' principal residence.</strong> Only that home can carry the Proposition 19 exclusion, and only if a child moves in within a year.</li>
<li><strong>Whether the trust is revocable.</strong> The tax-free sale depends on the home being part of the taxable estate at death.</li>
<li><strong>How much cash and securities are in the estate.</strong> Federal estate tax starts above the exclusion; under the owner's statement about Property B, only Property A and the cash use part of it.</li>
<li><strong>Insurance premiums.</strong> No official figure or quote could be confirmed. The ranking does not change at three times the owner's guess.</li>
</ol></section>
<section><h2>Where to look</h2>
<h3 class="grp">Start here</h3>
<div class="cards">
<div class="card"><div class="k">The answer</div><p><a href="executive-summary.html">Executive summary</a>: the decision, every important number with its source, and what would change it.</p></div>
<div class="card"><div class="k">What is not settled</div><p><a href="questions.html">Questions and answers</a>: 35 questions, each with what is known, what is missing and the step that closes it.</p></div>
<div class="card"><div class="k">What to change</div><p><a href="suggestions.html">Suggestions and paths</a>: four paths and sixteen suggestions, with effort and privacy cost, to choose before anything changes.</p></div>
</div>
<h3 class="grp">The decision</h3>
<div class="cards">
<div class="card"><div class="k">The reasoning</div><p><a href="decision.html">Decision analysis</a>: results for 2040, 2045 and 2050, break-even points and every assumption.</p></div>
<div class="card"><div class="k">The numbers</div><p><a href="projections.html">Year-by-year projections</a> to 2060: market value, assessed value, property tax and running costs.</p></div>
</div>
<h3 class="grp">Black swans &mdash; one section, two pages</h3>
<div class="cards">
<div class="card"><div class="k">Part 1 &middot; Conditions and history</div><p><a href="black-swans.html">Fifty years of official inflation data</a>, the baseline it contradicts, and the amounts that do not rise with inflation.</p></div>
<div class="card"><div class="k">Part 2 &middot; Stress tests</div><p><a href="stress.html">1929, 1965&ndash;82, 2000&ndash;02, 2007&ndash;09 and 2020 episodes</a> re-run against the 2045 inheritance, and what would have to change for the answer to move.</p></div>
</div>
<h3 class="grp">The two properties</h3>
<div class="cards">
<div class="card"><div class="k">Property A</div><p><a href="property-a.html">The home to inherit</a>: inputs, the assessment history against the state factors, and what the inheritance does to the assessed value.</p></div>
<div class="card"><div class="k">Property B</div><p><a href="property-b.html">The rented building already owned</a>: rent, the capped increases, running costs, and the reassessment exposure if it were in the same estate.</p></div>
</div>
<h3 class="grp">Rules and process</h3>
<div class="cards">
<div class="card"><div class="k">The rules</div><p><a href="taxes.html">Tax, thresholds and law watch</a>: federal, California and local, with the estate-tax room year by year.</p></div>
<div class="card"><div class="k">The process</div><p><a href="inheritance.html">Inheritance steps</a>: nineteen steps from today to the years after the death, with every deadline.</p></div>
</div>
<h3 class="grp">Evidence and open items</h3>
<div class="cards">
<div class="card"><div class="k">What is not settled</div><p><a href="review.html">Flagged for Review</a>: values left blank because no official source confirms them, plus the privacy disclosures.</p></div>
<div class="card"><div class="k">How it was checked</div><p><a href="audit.html">Independent verification</a>: what an independent pass corrected, and how the arithmetic was re-checked.</p></div>
<div class="card"><div class="k">Every source</div><p><a href="sources.html">Source library</a>: each document, the words relied on, and how it was checked.</p></div>
</div>
</section>
<section><h2>Three editions in one repository</h2>
<p>This dashboard is one of three editions kept side by side. They answer the same question with separate models, so their figures differ; each page states which model it comes from. Do not mix a number from one edition with a table in another.</p>
<div class="cards">
<div class="card win"><div class="k">This edition &middot; 15 pages</div><p>The pages in the menu. One model, one source ledger of {len(SRC)} entries, re-checked line by line on 11 and 12 November 2026. Act on these numbers.</p></div>
<div class="card"><div class="k">Cross-check &middot; 10 pages</div><p><a href="plan/index.html">A second model</a> built from official figures only, leaving unverifiable inputs blank and reporting break-evens instead. It reaches the same default: sell and keep Property B.</p></div>
<div class="card"><div class="k">50-year suite &middot; 12 pages</div><p><a href="analysis/index.html">2026&ndash;2076 schedules</a>, a 1977&ndash;2026 state cycle replay with decline-in-value relief, a 60/40 Treasury barbell and the ownership-asymmetry tables.</p></div>
</div></section>{PRIV}"""
PAGES["index.html"] = page("index.html", "Overview", "Overview", "Sell, rent or move in?",
                           "A costed answer for a home expected to be inherited through a trust between 2040 and 2050, "
                           "with a second, rented property kept in view. Every rule links to its official publisher.", body)

# ------------------------------------------------------------------------------------------------ executive summary
rows = [
 (["Best plan", "Sell Property A after inheriting, reinvest, keep Property B", f"Selling and holding a stock index fund ends at {usd(SELL['wealth'])}; renting at {usd(RENT['wealth'])}; moving in at {usd(LIVE['wealth'])}. Inheritance in 2045, measured in 2055, after all taxes."], "C", S("irs_basis", "boe_prop19", asm=True)),
 (["Why the sale is cheap", "Tax basis resets to the value at death", "A sale soon after the death produces almost no taxable gain. Decades of growth are never taxed."], "V", S("irs_basis")),
 (["Condition for that reset", "The home must be in the taxable estate", "True for a trust that stayed revocable. Not true for an irrevocable trust kept outside the estate."], "V", S("irs_rr2023_2")),
 (["Property A tax today", f"about {usd(NOW_A['property_tax'])} a year", "Assessed value about $550,000 against a market value of $3,100,000."], "O", S("boe_lta26002", asm=True)),
 (["Property A tax in 2045, a child moves in", f"{usd(LIVE['tax_first'])} a year", f"Assessed value becomes {usd(A45['live'])}: market value less the Proposition 19 amount."], "C", S("rtc63_2", "boe_lta25009", asm=True)),
 (["Property A tax in 2045, rented", f"{usd(RENT['tax_first'])} a year", f"A rental home gets no exclusion. Assessed value becomes the full {usd(A45['fmv'])}."], "C", S("boe_prop19", asm=True)),
 (["What the exclusion is worth", f"{usd(A45['saving'])} a year in 2045", "The tax on the Proposition 19 amount. It needs a child to live there as a principal residence and file two claims on time."], "C", S("boe_prop19", "boe_lta25009", asm=True)),
 (["Rent does not carry the home", f"{usd(RENT['first_cash'])} cash in the first year", f"After tax, on a home worth {usd(A45['fmv'])}. The reset property tax takes more than half of the rent."], "C", S("irs_p527", asm=True)),
 (["Break-even points", f"{BE['stock_return']}% stock return; {BE['house_growth']}% house growth", f"Renting beats selling only if stocks return less than {BE['stock_return']}% a year, or the house grows about as fast as stocks. The rent would have to be {usd(BE['rent_month'])} a month in 2026 dollars."], "C", S("treasury_cmt", "fred_hpi_a", asm=True)),
 (["Price of living in Property A", f"{usd(B45['live_cost_month_today'])} a month in today's dollars", "The gap between moving in and the best alternative, spread over ten years. A lifestyle choice, costed."], "C", S("irs_tc701", asm=True)),
 (["Property B, if in the same estate", f"tax rises from {usd(BR45['tax_keep'])} to {usd(BR45['tax_reset'])} in 2045", "In a multi-unit building only the unit that was the parent's home and becomes the child's home can be excluded. The owner states Property B is already owned by the beneficiary; if the deed confirms it, none of this applies."], "C", S("boe_lta26026", "cityb_rate", asm=True, flag=True)),
 (["Federal estate tax", "$15,000,000 per person in 2026; $15,480,000 in 2027", "A married couple can use two exclusions, but only if the first estate files Form 706 on time to elect it. Tax above the exclusion is 40%."], "V", S("irs_estate", "irs_2027", "irs_i706")),
 (["Room for cash under the exclusion", f"{usd(E45['room_single_base'])} in 2045 for one person", f"Scenario exclusion {usd(E45['exclusion'])} less both homes at {usd(E45['homes_base'])}. Under the owner's statement that Property B is already the heir's, the room is {usd(ROOM_B_OWNED)} instead. The cash amount itself was not supplied."], "C", S("irs_estate", "irs_rp2532", asm=True, flag=True)),
 (["Estate tax above the threshold", "40 cents of every dollar over the room", "An estate $5,000,000 above the room would owe about $2,000,000 before credits. The tax falls on the estate, not on the heir, and is due with Form 706 nine months after the death. California and its cities impose none."], "C", S("irs_estate", "irs_i706", "rtc13301")),
 (["California and local death taxes", "None", "No state estate or inheritance tax return since 2005. Cities and counties are barred from imposing one."], "V", S("sco_estate", "rtc13301")),
 (["Is the inheritance itself income?", "No", "Property acquired by inheritance is not gross income. Income the property produces afterwards is taxable, and a later sale is a capital gain measured from the value at the date of death."], "V", S("uscode102")),
 (["Inherited retirement accounts, if any", "Ten years to empty", "For an owner who died after 2019 a non-spouse beneficiary must generally distribute the whole account within ten years; each withdrawal is ordinary income. Whether any account exists was not supplied (Q-06)."], "V", S("irs_rmd_faq", flag=True)),
 (["What the transfer itself costs", "No death tax and no transfer tax", "A transfer by reason of death is exempt from documentary transfer tax, outright or in trust. What remains is the professional work: appraisal, trustee and attorney fees, recording. Those fees were not quoted."], "V", S("rtc11930", "rtc480")),
 (["Insurance: what is available", "The FAIR Plan, capped at $3,000,000", "The state's insurer of last resort is open to every homeowner, but its maximum for all coverages combined is below Property A's current estimated value, and it covers fire, lightning, explosion and smoke only. No premium is verified for either property."], "V", S("cdi_tips", "cdi_fairplan", flag=True)),
 (["Property tax and assessment history", f"Published to the nearest $10, 2014 to 2026", "The full table is on the Property A page, with the published state factor beside each year. Percentage changes are computed before rounding, so they are exact at any privacy setting."], "O", S("boe_lta26002")),
 (["Insurance", BLANK, "No official premium figure or insurer quote was confirmed for either property. The owner's guesses are used as placeholders; tripling them does not change the ranking."], "U", S("cdi_compare", flag=True)),
 (["Law under discussion", "The initiative to repeal the 2021 inheritance rules failed for lack of signatures", f"It would have restored the pre-2021 exclusion. If a later measure did so, Property A's 2045 tax would be {usd(LAW['tax_restored'])}. Selling would still come out ahead."], "V", S("sos_memo", "lao_250017", "sos_measures")),
 (["State tax on financial assets", "The one-time state tax on certain taxpayers was rejected in the unofficial count", "Results on 10 November 2026: Proposition 40 rejected with 52.6% no; Proposition 42 ahead with 51.5% yes. Certification due 11 December 2026."], "V", S("sos_results")),
 (["Black-swan stress tests", "Selling stays first in every stress case tested", "Stocks at 4.0% a year, inflation at 4.0% a year, or a flat decade for house prices: the ranking holds. A lost decade only moves the proceeds from the stock fund to Treasuries."], "C", S("frh_recession", "boe_lta26002", "fred_casthpi", asm=True)),
 (["Black swan stress tests", "Selling the home wins in 5 of 7 historical analogues; renting wins only when equities flatline", "The sale at the inheritance is robust; the reinvestment vehicle depends on the regime. Treasuries win when yields clear inflation (1970s analogues) or when stocks crash at the inheritance."], "A", S("bls_btn11", "fedhist_greatrecession", asm=True)),
 (["Deadlines after a death", "60 days, 150 days, 9 months, 1 year, 3 years", "Trustee notice; change in ownership statement; Form 706; homeowners' exemption; exclusion claim."], "V", S("prob16061_7", "rtc480", "irs_i706", "boe_prop19")),
]
body = f"""{tbl("Important details", ["Topic", "Finding", "What it means"], rows)}{LEGEND}
<section><h2>The plan in order</h2><ol>
<li><strong>Now.</strong> Confirm the trust is revocable and holds title; confirm the deed matches the owner's statement that Property B is already owned by the beneficiary; confirm which home carries the parents' homeowners' exemption. Do not move either property into an LLC.</li>
<li><strong>At the inheritance.</strong> Get a date-of-death appraisal. File the change in ownership statement within 150 days. File Form 706 within nine months if the estate is near the exclusion or a spouse survives.</li>
<li><strong>Decide within the first year.</strong> Sell, unless living in the home is worth about {usd(B45['live_cost_month_today'])} a month in today's dollars to the family. If moving in, occupy within one year and file both claims.</li>
<li><strong>Reinvest.</strong> A stock index fund has the higher expected result. Treasuries at today's yield finish ahead of renting when house prices grow 4% a year or less. A mix sits between the two.</li>
<li><strong>Keep Property B.</strong> Its low assessed value and steady rent make it the better property to hold, provided it is not reassessed in the same estate.</li>
</ol></section>{PRIV}"""
PAGES["executive-summary.html"] = page("executive-summary.html", "Executive summary", "Executive summary", "What matters, in one table",
                                       "Each row states a finding, the number behind it, and the official source.", body)

# ------------------------------------------------------------------------------------------------ questions
# The information register. Every row states what is settled, what is not, and the concrete step that
# would settle it. Values that no official source confirms are never filled in.
OFF = '<em>Answered &middot; official source</em>'
OWN = '<em>Answered &middot; your records</em>'
PART = '<em>Partly answered</em>'
OPEN_R = '<em>Open &middot; your records</em>'
OPEN_P = '<em>Open &middot; needs a professional</em>'
OPEN_T = '<em>Open &middot; only at the death</em>'
OPEN_L = '<em>Open &middot; depends on future law</em>'

q_money = [
 ("Q-01", "How much can be inherited before a federal tax applies?",
  OFF + "<br>Not a limit on what you may receive",
  f"$15,000,000 per person for a death in 2026, $15,480,000 in 2027, indexed after. Tax above it is 40 cents on the dollar and is charged to the estate, not to the heir. One person's room in 2045 is {usd(E45['room_single_base'])} if both homes are in the estate, or {usd(ROOM_B_OWNED)} under your statement that Property B is already yours.",
  "Nothing, for 2026 and 2027. For later years the index is a scenario: the tax page shows $13,819,960 and $17,612,290 as the 2045 range, not a forecast.",
  "Every $100,000 of estate above the room costs the estate $40,000."),
 ("Q-02", "Is the inheritance itself income to me?",
  OFF,
  "No. Gross income does not include property acquired by inheritance. Income the property produces afterwards is taxable, and a later sale is a capital gain measured from the value at the date of death.",
  "Nothing. The one exception to check is retirement accounts (Q-06), where the money is taxed as it is withdrawn.",
  "If any part were income, the effective amount received would be lower by the income tax on it."),
 ("Q-03", "Is there a California inheritance or estate tax?",
  OFF,
  "No. No California estate tax return has been required for deaths since 1 January 2005, and state law bars cities and counties from imposing a death tax.",
  "Nothing. Watch the law-watch table for any bill that would create one.",
  "A 5% state tax on a $5,000,000 inheritance would be $250,000; none is now levied."),
 ("Q-04", "What does the transfer itself cost?",
  PART,
  "No county documentary transfer tax is due on a transfer by reason of death, outright or in trust. There is no inheritance tax. What remains is the cost of the work: appraisal, trustee and attorney fees, recording fees, and any probate if the trust does not cover the property.",
  "The fees themselves. Ask the trustee's attorney for a fee schedule and the county for the current recording fee, and record the answer here. Nothing in the plan depends on the estimate, but the first-year cash figure does.",
  "A probate for a $3,100,000 home, if the trust failed to cover it, would be slow and expensive; the trust is the protection."),
 ("Q-05", "How much cash and securities are in the estate?",
  OPEN_R,
  "Not supplied. Under your statement the federal room in 2045 is large enough for the cash only if the estate is worth less than the room shown.",
  "Read the trustee's schedule of assets, or the latest statement from each account. Write the total in one line; it converts the room figure into a tax figure. This is the single most valuable missing number.",
  "Room of $1,000,000 used up costs $400,000 of estate tax; room of $1,000,000 spare costs nothing."),
 ("Q-06", "Are there retirement accounts, and how are they taxed?",
  OPEN_R,
  "Not known whether any exist. If they do, a non-spouse beneficiary of an account whose owner died after 2019 must generally empty it within ten years, and each withdrawal is ordinary income. The account is also part of the estate for the federal threshold.",
  "Ask the trustee for the beneficiary designations. If accounts exist, the ten-year window matters more than the tax rate: it can push a beneficiary into a higher bracket.",
  "Spreading withdrawals over ten years rather than one is often the whole difference; a tax preparer should model it."),
 ("Q-07", "Is the trust revocable?",
  OPEN_P,
  "Not supplied, and it decides the tax basis. A revocable trust's assets are in the taxable estate, so the basis resets to the value at death and a sale just after the death produces almost no gain. An irrevocable trust outside the estate carries the old, low basis.",
  "Read the trust instrument with the attorney who drafted it. Ask one question: are the assets included in the grantor's gross estate? Record the answer and the date.",
  "Without the reset, the gain since the parents bought could be taxed at about 36%. That alone can erase the margin between selling and renting."),
 ("Q-08", "Who holds title to Property B today?",
  OPEN_R,
  "You state it is already owned by the heir. No deed was seen. If that is right, the building is outside the estate: its tax does not reset and it does not use the federal room. If the parents still hold it, its tax resets at the death.",
  "Order a copy of the deed or a trustee's certification of title from the county recorder. Ten minutes and a small fee; it settles the largest single contingency in this analysis.",
  f"If the parents hold it, its tax rises from about {usd(BR45['tax_keep'])} to {usd(BR45['tax_reset'])} a year in 2045, and the federal room shrinks by its value of {usd(B_VALUE_2045)}."),
 ("Q-09", "Which home is the parents' principal residence?",
  OPEN_R,
  "Not stated. Only a home that was the parent's principal residence can carry the parent-child exclusion, and only if a child then lives in it. The homeowners' exemption record shows which home has been claimed.",
  "Look for the homeowners' exemption on each property tax bill, or ask the assessor which property carries it. One line in a letter settles it.",
  "If the home to inherit was a second home, the exclusion is unavailable and moving in costs the same tax as renting."),
 ("Q-10", "Have there been large gifts in recent years?",
  OPEN_R,
  "Not supplied. Taxable gifts use the same lifetime exclusion as the estate, so they reduce the room available at death.",
  "Ask whether any Form 709 gift tax return was filed, and for the total of gifts above the annual exclusion. The annual exclusion is $19,000 per recipient for 2026 and $20,000 for 2027.",
  "Gifts of $1,000,000 in total reduce the room by $1,000,000, which can cost $400,000 in estate tax."),
 ("Q-11", "Will a spouse survive, and will portability be elected?",
  OPEN_T,
  "Not knowable now. If a spouse survives, the first estate must file Form 706 on time to pass its unused exclusion to the survivor, even when no tax is due. Otherwise the second exclusion is lost.",
  "Put the election in the estate plan now and in the trustee's checklist. It is a filing decision, not a property decision, but it doubles the room.",
  "Losing one exclusion can cost 40% of everything above a single exclusion."),
 ("Q-12", "Is there a mortgage or other debt on either property?",
  OPEN_R,
  "The model assumes neither is encumbered. A mortgage would reduce the estate for tax but has to be paid, or the property sold to pay it.",
  "Ask for the latest loan statements and any liens. Record the balance and the rate. A fixed low rate is an asset; a floating rate is the risk the 1981 record warns about.",
  "A $500,000 balance at 6% costs $30,000 a year in interest and reduces the estate by $500,000."),
]

q_a = [
 ("Q-13", "What will Property A be worth at the death?",
  OPEN_T,
  f"Not knowable. The projections run 3%, 4% and 5% a year. At 4% the home is worth {usd(A45['fmv'])} in 2045. The local index rose 5.3% a year since 1995 but was flat over the last four quarters.",
  "Nothing until the date of death, when an appraisal sets both the basis and the reassessment. Keep the appraisal instruction in the trustee's file.",
  f"Each $1,000,000 of value changes the property tax after reassessment by about {usd(11800)} a year and the federal room one for one."),
 ("Q-14", "Will the parent-child exclusion apply?",
  PART,
  "The rule is settled: the home must have been the parent's principal residence, it must become the child's principal residence within one year, the child must claim the homeowners' exemption within one year, and the exclusion must be claimed within three years or before a sale. Whether it will apply to this family depends on Q-09 and Q-16.",
  "Confirm the two facts (Q-09 and Q-16) and put both deadlines in the trustee's checklist. The claim form is not published by us; ask the assessor for it.",
  f"Without it, the first-year tax after the death is {usd(RENT['tax_first'])} instead of {usd(LIVE['tax_first'])}."),
 ("Q-15", "How large is the exclusion amount at the death?",
  OFF + " &middot; growth modelled",
  "For transfers up to 15 February 2027 the amount is " + usd(M["verified"]["prop19_amount"]) + ", the published figure rounded to the nearest $10. It is adjusted every second year by one year's change in the house price index. At 4% growth the model uses " + usd(A45['amount']) + " in 2045.",
  "The 2027 adjustment will be published by the Board of Equalization; keep the source bookmarked and re-read it every two years. The rule is verified; only the future amount is a scenario.",
  "If the amount grows more slowly than house prices, the taxable remainder grows: the exclusion loses value against the home every year."),
 ("Q-16", "Does someone have to move in?",
  PART,
  "Yes, for the exclusion: a child must occupy the home as a principal residence within one year of the transfer. This is a decision only the family can make, and it is worth " + usd(A45['saving']) + " a year in 2045.",
  "Decide before the death which child, if any, would move in, and write it into the trust's distribution plan. If nobody would, plan on the rental or sale path and stop counting the exclusion.",
  f"Choosing not to occupy costs {usd(A45['saving'])} a year in property tax; the decision page prices the whole lifestyle choice at {usd(B45['live_cost_month_today'])} a month."),
 ("Q-17", "What are the deadlines to claim?",
  OFF,
  "Homeowners' exemption: file within one year of the transfer. Exclusion claim: file within three years, or before the property is sold or transferred to a third party. A late claim works only from the year it is filed.",
  "Nothing; the dates are fixed. Put them in the trustee's calendar the day the death certificate is issued.",
  "A missed claim is a pure loss: roughly the annual saving above, repeated until the property changes hands."),
 ("Q-18", "What will home insurance cost?",
  OPEN_P,
  "Unverified for both properties, and left blank rather than guessed. The state's premium survey publishes sample premiums for new business, not quotes, and lists no landlord policy type; the insurer of last resort, the FAIR Plan, is available to every homeowner but its maximum for all coverages combined is $3,000,000, below Property A's current estimated value.",
  "Get three quotes: one for Property A as a principal residence with wildfire cover, and one for Property B as a rental (a landlord policy). Record the premiums, the deductibles and any wildfire surcharge here. This is the second most valuable missing number.",
  "Tripling your guess does not change the ranking, but a real quote changes the running-cost totals and could change the rent-versus-sell margin at the low end."),
 ("Q-19", "What are the fixed charges on each tax bill?",
  PART,
  "Derived, not read: $840 a year on Property A and $1,090 on Property B, being the part of each bill that the rate times the assessed value does not explain. The line items were not supplied.",
  "Take the current bill for each property and copy the charges other than the general levy: debt service, special assessments, fees. They matter because they do not shrink when the assessed value resets.",
  "If the fixed charges are larger, the post-inheritance tax is larger by the same amount every year."),
 ("Q-20", "When does the solar credit end?",
  OPEN_R,
  "Your record shows a credit of $10 to $20 a month. The older net-metering tariffs run 20 years from the date of connection; the connection date was not supplied.",
  "Find the interconnection date on the utility bill or the net-metering agreement. Add 20 years. After that date the electricity line moves from a credit to a cost.",
  f"The projections carry the credit to 2060; if it ends earlier, add roughly {usd(600)} to {usd(1_200)} a year of running cost from that year."),
 ("Q-21", "What does water cost?",
  OWN + " &middot; rate not verified",
  "Your figure: $100 to $150 a month for Property A, and $330 to $400 a month for the whole of Property B. Published tariffs for the serving districts were not read in this edition.",
  "Read the current tariff sheet from each water supplier and multiply by the metered use on a bill. The supplier's own schedule is the official source; add it to the source library when you have it.",
  "Each extra $10 a month is $120 a year: small against the property tax, large over thirty years."),
 ("Q-22", "Which tax rate area applies to Property A?",
  PART,
  "Not known: the bill does not show it. The county's published rates for 2025-26 run from 1.126% to 1.241%. The model uses 1.18%, inside that range.",
  "The rate area is printed on the bill or available from the assessor by parcel. Once known, replace the 1.18% assumption and re-run the model.",
  "The difference between 1.126% and 1.241% is $230 a year today and about $1,500 a year after reassessment in 2045."),
 ("Q-23", "Will the tax really rise only 2% a year until the death?",
  OFF + " &middot; with one check",
  "Yes while ownership does not change: the assessed value may rise by the lower of 2% or the published inflation factor, and 2% has been the binding figure every year since 2022. Your own record matches the published factors in every year to within one basis point.",
  "Nothing. The one thing that would break it is new construction, a change of ownership, or a decline-in-value reduction, none of which appears in the record.",
  "If the property were reassessed early, today's tax would rise into the range shown on the property page."),
 ("Q-24", "What does owning Property A cost after the inheritance?",
  PART,
  "Computed: property tax after reassessment, insurance (your guess, unverified), water, the solar credit and maintenance, year by year to 2060 on the projections page. First-year total after an inheritance in 2045 is in the executive summary.",
  "Three real inputs would replace the estimates: an insurance quote, the water tariff, and a contractor's view of deferred maintenance. The rest is arithmetic.",
  "Every $1,000 a year of cost is about $8,500 over ten years at the model's after-tax return."),
]

q_b = [
 ("Q-25", "Does the rent ordinance cover Property B?",
  OPEN_R,
  "Not known: it depends on when the building was first occupied for residential use. Covered units have capped annual increases and restrictions on eviction; a new tenancy may start at any rent. The 2026-27 allowed increase is 1.6%.",
  "Ask the Rent Board, in writing, whether the building is covered, quoting the date of first occupancy from the building record. Keep the answer with the deed.",
  "If covered, rent growth is capped; the plan already assumes 1.5% a year, so the ranking does not change."),
 ("Q-26", "Is the third unit legal and rentable?",
  OPEN_R,
  "Not supplied. The plan values it at $3,580 a month if the family moves out, equal to the average of the two rented units, and treats it as free housing while occupied.",
  "Check the building permit history for the third unit and any accessory-dwelling rules. A unit that cannot legally be rented changes the income line, not the property-tax line.",
  "About $42,960 a year of gross rent, or roughly $30,000 after costs and tax."),
 ("Q-27", "Is the building insured as a rental?",
  OPEN_P,
  "Unverified. A landlord policy differs from a homeowners policy: it covers the structure and loss of rent, not the tenant's belongings. The state's survey lists no landlord type, so only a broker can price it.",
  "Ask the current insurer for the declarations page. If the building is insured as an owner-occupied home, the cover may be wrong for rented units.",
  "A gap in cover is the one cost that cannot be recovered after the event."),
 ("Q-28", "What rent increase is allowed this year?",
  OFF,
  "1.6% for 1 March 2026 to 28 February 2027 for sitting tenants in covered units: 60% of the regional price index. The model uses 1.5% a year because that is the same formula at 2.5% inflation.",
  "Nothing. Re-read the Rent Board page each year; the rate is republished annually.",
  "Rent growth of 1% a year instead of 1.5% reduces Property B's net income by about 6% over ten years."),
 ("Q-29", "What does the Rent Board charge?",
  OFF,
  "About $60 a unit a year, charged on owner-occupied units too unless an exemption is filed.",
  "Ask whether the exemption has been filed for the unit the family occupies. It is a small amount, but it is annual.",
  "About $180 a year for three units."),
 ("Q-30", "Is a vacancy tax in force?",
  PART + " &middot; unverified",
  "Reported struck down on appeal in September 2026, but only in secondary reports; the opinion was not read. No official confirmation is recorded, so nothing is modelled.",
  "Read the appellate opinion on the court's own site, or the city attorney's summary. If a tax exists, add it as a cost on the vacant or family-occupied unit.",
  "A tax of $1,000 a unit a year would cost about $1,000 to $2,000 depending on occupancy."),
]

q_d = [
 ("Q-31", "What return should the money be assumed to earn?",
  PART + " &middot; assumption",
  "7.0% a year for a stock index fund is a scenario, not a forecast; no long-run official average was read. The 10-year Treasury yielded 4.88% on 9 November 2026, verified. Renting beats selling only if stocks return under 4.7%.",
  "Decide the assumption you are willing to plan on, and write it down. The sensitivity table shows the answer at 5%, 6%, 7% and 8%.",
  "At 5% instead of 7%, selling still leads; the margin narrows to about $1,000,000 over ten years."),
 ("Q-32", "What is living in the home worth to the family?",
  OPEN_R,
  f"A decision, not a fact. The model prices it at {usd(B45['live_cost_month_today'])} a month in today's dollars compared with the best alternative, and it is the most expensive option in every case tested.",
  "Decide before the death, while there is no pressure. Record the decision and the reason on this page's companion, the suggestions page.",
  "Choosing to live there is rational if the family values it above that monthly figure; the arithmetic does not make the choice, it prices it."),
 ("Q-33", "What if house prices grow more slowly, or faster?",
  OFF + " &middot; scenario grid",
  "Selling leads in all nine combinations of inheritance year (2040, 2045, 2050) and growth (3%, 4%, 5%). Renting overtakes only at about 7.0% growth a year, or if stocks return under 4.7%.",
  "Nothing further. Re-run the grid when the Treasury yield moves by more than a percentage point.",
  "The ranking, not the margin, is what the grid tests; the margin moves by about $1,000,000 across the growth range."),
 ("Q-34", "What would change the recommendation?",
  OFF + " &middot; computed break-evens",
  "Four things: a stock return below 4.7%, house growth above 7.0%, a market rent above $14,250 a month, or a law that restored the pre-2021 exclusion. Insurance at three times the guess does not change it.",
  "Watch those four numbers. Each is printed with the page that computes it.",
  "Any one of them flips the ranking; none is close today except the Treasury comparison, which is thin."),
 ("Q-35", "What if the law changes before 2045?",
  OPEN_L,
  "The initiative to repeal the 2021 rules failed for lack of signatures and was not on the 3 November 2026 ballot. If a later measure restored the old rule, Property A's 2045 tax would be lower and renting and moving in would each gain several hundred thousand dollars over ten years. Selling would still finish first.",
  "Re-read the law-watch table twice a year, and at each election. Three items matter: the parent-child exclusion, the basis reset and the federal exclusion.",
  "A change to the basis reset is the one that could reverse the ranking; none is verified as pending."),
]

def qtable(rows, caption):
    return tbl(caption, ["No.", "Question", "Status", "Answer today", "Missing, and how to find it", "If the answer is different"], rows)


# Each question carries the official page that bears on it, so a reader can check the rule even when
# the household-specific answer is still missing.
QSRC = {
 "Q-01": ("irs_estate", "irs_2027"), "Q-02": ("uscode102",), "Q-03": ("sco_estate", "rtc13301"),
 "Q-04": ("rtc11930", "rtc480"), "Q-05": ("irs_estate",), "Q-06": ("irs_rmd_faq",),
 "Q-07": ("irs_rr2023_2", "irs_basis"), "Q-08": ("boe_lta26026", "cityb_rate"), "Q-09": ("boe_prop19",),
 "Q-10": ("irs_estate", "irs_2027"), "Q-11": ("irs_i706",), "Q-12": ("irs_estate",),
 "Q-13": ("fred_hpi_a",), "Q-14": ("rtc63_2", "boe_prop19"), "Q-15": ("boe_lta25009",),
 "Q-16": ("rtc63_2",), "Q-17": ("rtc63_2", "boe_prop19"), "Q-18": ("cdi_tips", "cdi_compare"),
 "Q-19": ("cnty_a_rates", "cityb_rate"), "Q-20": ("cpuc_nem",), "Q-21": ("irs_p527",),
 "Q-22": ("cnty_a_rates",), "Q-23": ("boe_lta26002",), "Q-24": ("irs_p527", "boe_lta26002"),
 "Q-25": ("cityb_rent",), "Q-26": ("cityb_rent",), "Q-27": ("cdi_compare",), "Q-28": ("cityb_rent",),
 "Q-29": ("cityb_rentfee",), "Q-30": ("cityb_rate",), "Q-31": ("treasury_cmt", "tsp_returns"),
 "Q-32": ("irs_tc701",), "Q-33": ("fred_hpi_a",), "Q-34": ("treasury_cmt", "irs_p925"),
 "Q-35": ("sos_memo", "lao_250017"),
}


def qrows(rows):
    out = []
    for r in rows:
        out.append((r, "S" if r[2].startswith("<em>Answered") else "X", S(*QSRC[r[0]])))
    return out


counts = {"official": 0, "open": 0}
for r in q_money + q_a + q_b + q_d:
    if "Open" in r[2]:
        counts["open"] += 1
counts["official"] = len(q_money + q_a + q_b + q_d) - counts["open"]

body = f"""
<div class="note"><strong>What this page is.</strong> {len(q_money + q_a + q_b + q_d)} questions, in the order they have to be answered.
Each one states what is settled today and links the official page that settles it, what is still missing, the concrete step that would
find it, and what changes if the answer comes back differently. Nothing here is inferred: where a household fact is unknown, the answer
says so and the figure stays blank. Questions marked <span class="b b-x">Your choice</span> need a decision rather than research.</div>
<div class="cards">
<div class="card"><div class="k">Answered from an official source</div><div class="v">{counts['official']}</div><p>Rules, thresholds and deadlines that are settled law, each linked to its publisher.</p></div>
<div class="card"><div class="k">Still open</div><div class="v">{counts['open']}</div><p>Household facts, professional opinions or future events. Each has a named step that would close it.</p></div>
<div class="card"><div class="k">Blocking today</div><div class="v">2</div><p>Q-07 (is the trust revocable) and Q-08 (who holds title to Property B). Both are answered by one document each.</p></div>
</div>

<section><h2>If you do only three things</h2>
<ol>
<li><strong>Read the trust and the deed (Q-07, Q-08).</strong> These two documents decide whether the sale is nearly tax-free and whether the rental building is reassessed. One afternoon with a scanner.</li>
<li><strong>Get three insurance quotes (Q-18).</strong> Homeowners with wildfire cover for Property A, landlord cover for Property B. Then the running-cost tables stop relying on a guess.</li>
<li><strong>Write down the cash total (Q-05).</strong> One number converts the federal room on the tax page into a tax bill or a zero.</li>
</ol></section>

<section><h2>Money, tax and title at the death</h2>
{qtable(qrows(q_money), "Questions about the estate, the tax and the title")}</section>

<section><h2>Property A: the home to inherit</h2>
{qtable(qrows(q_a), "Questions about the home, its tax and the exclusion")}</section>

<section><h2>Property B: the rented building</h2>
{qtable(qrows(q_b), "Questions about the building already owned")}</section>

<section><h2>The decision itself</h2>
{qtable(qrows(q_d), "Questions about the choice between selling, renting and moving in")}</section>

<section><h2>What cannot be known now</h2>
<p>Some of the most important inputs do not exist yet, and no amount of research will produce them early: the value of the home on the
date of death, the exclusion amount in that year, the law in that year, the stock and house market of the following decade, and the
family's circumstances. The plan handles them the only way that is honest: it shows a range, states the break-even point at which the
answer changes, and re-runs itself each year. Anything else would be a forecast dressed up as a fact.</p>
<p>The next page turns these open questions into a short list of suggestions, with the effort and the privacy cost of each, so a path can
be chosen before anything is changed: <a href="suggestions.html">suggestions and paths</a>.</p></section>{PRIV}"""
PAGES["questions.html"] = page("questions.html", "Questions and answers", "Questions and answers",
                               "What we know, what we do not, and how to find out",
                               "Every question that has to be answered before the decision can be made, with its status, the official rule behind it, and the step that closes it.", body)


# ------------------------------------------------------------------------------------------------ suggestions
DONE = '<span class="pill now">Done in this edition</span>'
CALL = '<span class="pill you">Your call</span>'
REC = '<span class="pill you">Needs records you hold</span>'
PRO = '<span class="pill pro">Needs a professional</span>'
LATER = '<span class="pill later">Later / optional</span>'

paths = [
 (["P-1", "Act on today's numbers", "Read the summary and the decision page; treat the unverified items as blanks and decide at the death.",
   "None", "Nothing new", "Leaves the trust, the deed, the insurance premium and the cash total unknown until the year they matter most.",
   "Acceptable only because the ranking does not depend on them; the margin does."], "X", '<a href="executive-summary.html">Executive summary</a>'),
 (["P-2", "Close the three gaps first", "Read the trust and the deed (Q-07, Q-08), get three insurance quotes (Q-18), and write down the cash total (Q-05). Then re-read the decision page.",
   "Two to four weeks, mostly waiting", "The two documents and a broker", "Basis step-up, Property B's ownership, the real premium, the estate-tax figure.",
   "Future law, future prices, the family's choice about living there.",
   "<strong>Recommended.</strong> Each of the three is one document or one phone call, and each moves a number that is currently a blank."], "X", '<a href="questions.html">Questions and answers</a>'),
 (["P-3", "Publish at maximum privacy", "Set the privacy tier to 3: roll values to the nearest $10,000, everything else unchanged.",
   "One command, one rebuild", "The roll tables lose their last digits", "The strongest available protection against matching a parcel; the analysis does not change at all.",
   "The property and tax tables no longer show the year-by-year bill with precision.",
   "Choose this if the $10 figures feel too close to the record. <a href=\"#privacy\">See the trade-off.</a>"], "X", '<a href="review.html">Privacy disclosures</a>'),
 (["P-4", "Professional review before the window", "Estate attorney to confirm the trust and portability; a tax preparer to model the inherited accounts and the 2045 rate; an appraiser for a baseline.",
   "Fees quoted by each; ask for them", "Three professionals", "The legal questions the model cannot answer, and the fee numbers that are blank today.",
   "Everything that depends on the law of the 2040s.",
   "Do this by 2035, not at the death. It is the only path that closes Q-06, Q-11 and Q-12."], "X", '<a href="inheritance.html">Inheritance steps</a>'),
]
prow = [(p[0], p[1], p[2]) for p in paths]

sug = [
 ("S-01", "Read the trust instrument and the deed; record two facts: is the trust revocable, and who holds title to Property B.",
  "Two of the largest numbers in the analysis turn on them: the basis step-up and the reassessment of the rental.", "One afternoon",
  "None: the documents stay private.", REC),
 ("S-02", "Get three real insurance quotes: homeowners with wildfire cover for Property A, landlord cover for Property B.",
  "The only running cost that is entirely unverified. The state publishes samples, not quotes, and lists no landlord product.", "Two or three calls",
  "None; quotes are not published, only the rounded premium is.", PRO),
 ("S-03", "Write the value of the cash and securities in the estate on one line, and keep it with the trust.",
  "Converts the federal room from an abstract figure into either a tax bill or a zero.", "Ten minutes",
  "Publish only the rounded total, or nothing.", REC),
 ("S-04", "Choose the precision of the roll tables, and change it whenever you want.",
  "The brief asks for $10 figures; that is the least protective setting. The setting is now a switch, not a rewrite.", "One command",
  "Tier 1 (now) leaves a close fingerprint; tier 3 removes it.", DONE),
 ("S-05", "Replace the derived fixed charges ($840 and $1,090) with the line items on the two current bills.",
  "Fixed charges do not shrink when an assessed value resets, so they stay in every projection.", "One hour",
  "None; only totals are published.", REC),
 ("S-06", "Decide, now and in writing, whether any family member would move into Property A.",
  "It decides whether the parent-child exclusion is worth planning for, and it changes how the trust should distribute the home.", "A family conversation",
  "None.", CALL),
 ("S-07", "Model the inherited retirement accounts, if any, across the ten-year distribution window.",
  "A non-spouse beneficiary must generally empty an inherited account within ten years; the tax rate on that can exceed the property tax question.", "An hour with a preparer",
  "Publish only percentages and rounded amounts.", PRO),
 ("S-08", "Add a liquidity plan for any federal estate tax: which asset pays it, and how, within the nine months.",
  "The tax is due with Form 706 nine months after the death, and the estate may be almost entirely land.", "A paragraph in the estate plan",
  "None.", PRO),
 ("S-09", "Keep a dated law watch, re-read twice a year (February and November), on three items only.",
  "The exclusion amount, the parent-child exclusion and the basis reset are the only rules that can move the ranking.", "Twenty minutes twice a year",
  "None.", LATER),
 ("S-10", "Re-run the model once a year with the current Treasury yield and the published factors.",
  "The Treasury yield is the thinnest margin in the analysis: renting and Treasuries finish close together.", "One command, five minutes",
  "None.", DONE),
 ("S-11", "Retire the two cross-check editions, or label every figure with its edition on every page.",
  "Three editions with three models invite mixing numbers that were never meant to be compared.", "A decision, then an hour",
  "None.", CALL),
 ("S-12", "Deal with the repository history: rewrite it, or make the repository private.",
  "Earlier commits contain finer figures and location detail. No setting on the website can remove them.", "An hour with git, or a repository setting",
  "This is the only measure that removes the historical figures.", CALL),
 ("S-13", "Add the water and electricity tariffs to the source library, from the serving utilities' published schedules.",
  "Water and electricity are the last running costs resting only on your estimate.", "An hour",
  "The utility's schedule names no household.", LATER),
 ("S-14", "Add a printable one-page brief for the trustee and the attorney.",
  "The people who will act in the twelve-month window need one page, not fifteen.", "An hour",
  "Uses the same rounded figures.", LATER),
 ("S-15", "Model a middle path: sell Property A and buy a smaller home in the same region with part of the proceeds.",
  "The current comparison is all-or-nothing: the whole value in one house, or none in housing.", "Half a day of model work",
  "None.", LATER),
 ("S-16", "Put every document in one folder now: trust, deed, both tax bills, both policies, the solar agreement.",
  "The twelve-month window after a death should not be spent looking for paperwork.", "An afternoon",
  "Keep the folder private; publish nothing from it.", REC),
]
srow = [([s[0], s[1], s[2], s[3], s[4], s[5]], "X", '<a href="questions.html">Questions and answers</a>') for s in sug]

tiers = [
 (["Tier 1 &middot; now", "Nearest $10", "A search for an exact roll value does not match. That is all it protects: a value within a few dollars of the record, with a 2% chain back to 2014, is still a close fingerprint for anyone who knows what to look for.",
   "The full table as the brief asks for it.", "Set in <code>assets/privacy.json</code>."], "X", '<a href="review.html">Privacy disclosures</a>'),
 (["Tier 2", "Nearest $1,000", "A roll value among roughly 100 in the same range; the growth chain still narrows it.", "Year-by-year detail, to the nearest thousand.", "<code>python3 scripts/privacy_tier.py 2</code>"], "X", '<a href="review.html">Privacy disclosures</a>'),
 (["Tier 3", "Nearest $10,000", "A roll value among roughly 1,000 in the same range. The previous edition published at this level.", "The analysis, unchanged; the last digits of the tables.", "<code>python3 scripts/privacy_tier.py 3</code>"], "X", '<a href="review.html">Privacy disclosures</a>'),
]
trow = [(t[0], t[1], t[2]) for t in tiers]

body = f"""
<div class="note"><strong>How this page works.</strong> These are suggestions, not changes. Each one states what it fixes, what it costs
in time, and what it does to privacy. Nothing on the site changes unless you choose it, apart from the two items marked
<span class="pill now">Done in this edition</span>, which are described at the foot of the page. Read the paths first, pick one, then work
down the list.</div>

<section><h2>Choose a path before changing anything</h2>
<p>There are four sensible paths. They differ in how much is settled before the decision is made, not in what is recommended: every path
ends in the same default, sell Property A and keep Property B, because the ranking does not depend on the missing numbers. What the
missing numbers change is the size of the margin and the tax bill.</p>
{tbl("The four paths", ["No.", "Path", "What you do", "Time and cost", "Who is involved", "What it settles", "What it leaves open", "Verdict"], prow)}
<p class="small">If no path is chosen, the site stays as it is: the last row of the decision page remains the recommendation, and the
flagged page remains the list of what is not known. That is a legitimate choice, and P-1 is exactly that.</p></section>

<section><h2>Suggestion register</h2>
<p>Sixteen suggestions, ordered by what they are worth. The first three are the same three gaps as above, in the order I would close them.</p>
{tbl("Suggestions, with effort, privacy effect and status", ["No.", "Suggestion", "Problem it solves", "Effort", "Effect on privacy", "Status"], srow)}</section>

<section id="privacy"><h2>The privacy choice</h2>
<p>The brief asks for property tax and assessment tables at $10 precision, so that figures cannot be traced back to the source. That is the
setting in force now. It is worth being exact about what it does: rounding to $10 removes the exact match, and nothing more. A roll value
within a few dollars of the record, published with a 2% growth chain, is a strong identifier to anyone who can search the county roll.
The stronger protection is rounding to $1,000 or $10,000, which costs the last digits of a table but none of the analysis.</p>
{tbl("Precision settings", ["Setting", "Roll values shown", "What it protects", "What it costs", "How to switch"], trow)}
<p>The setting lives in <code>assets/privacy.json</code>, is committed with the site, and is read by the model, so the pages and the
checks always reproduce the same figures. It does not reach into repository history: earlier commits and pull-request diffs may still
contain finer figures, which no setting on the website can change (S-12).</p></section>

<section><h2>Decision gates</h2>
<div class="gate"><h3>Gate 1 &middot; now, no spending</h3>
<p>Read the trust and the deed; confirm which home carries the homeowners' exemption; decide whether anyone would move in; put the
documents in one folder. All of it is free, and it closes the two questions that block the analysis.</p></div>
<div class="gate"><h3>Gate 2 &middot; before 2035</h3>
<p>Professional review of the trust, the portability election and any inherited accounts; three insurance quotes at that year's prices,
renewed every three years; a baseline appraisal so the eventual date-of-death value has a reference point.</p></div>
<div class="gate"><h3>Gate 3 &middot; the twelve months after the death</h3>
<p>Appraisal, change in ownership statement within 150 days, homeowners' exemption within one year, exclusion claim within three years or
before a sale, Form 706 within nine months if the estate is near the threshold or a spouse survives. Then the decision, with real
numbers instead of scenarios.</p></div>
<div class="gate"><h3>Gate 4 &middot; every year</h3>
<p>Re-read three law-watch items, update the Treasury yield, re-run the model, and re-read the break-even table. If any of the four
break-evens is crossed, the ranking changes and this page should be read again.</p></div></section>

<section><h2>What was done in this edition</h2>
<ul>
<li><strong>Two new sections:</strong> this page, and <a href="questions.html">questions and answers</a> with {len(q_money + q_a + q_b + q_d)} items.</li>
<li><strong>Roll tables published:</strong> the full property tax and assessment history for both properties, at the precision you asked for,
with percentage changes computed before rounding so they are exact at any setting.</li>
<li><strong>The privacy tier became a switch</strong> rather than a rewrite, with the trade-off stated on every page.</li>
<li><strong>Four sources added</strong> and re-read on 12 November 2026: 26 U.S.C. 102 (an inheritance is not income), the IRS required-minimum-distribution
FAQ (the ten-year rule), and two Department of Insurance pages (the FAIR Plan's $3,000,000 maximum for all coverages combined, and the
premium comparison tools).</li>
<li><strong>Two gaps in the earlier edition closed:</strong> the treatment of inherited retirement accounts and the treatment of the inheritance itself as income.</li>
</ul></section>

<section><h2>What I would do first</h2>
<ol>
<li><strong>This week:</strong> S-01 and S-03. Two documents and one number.</li>
<li><strong>This month:</strong> S-02. Three insurance quotes, written down.</li>
<li><strong>This year:</strong> S-06 and S-16. The family decision and the folder.</li>
<li><strong>Before 2035:</strong> P-4. The professional review, with the fees asked for in writing.</li>
</ol></section>{PRIV}"""
PAGES["suggestions.html"] = page("suggestions.html", "Suggestions and paths", "Suggestions", "What to change, and in what order",
                                 "Four paths, sixteen suggestions, and the privacy trade-off, so a route can be chosen before anything is implemented.", body)


# ------------------------------------------------------------------------------------------------ decision
sec = []
for y in (2040, 2045, 2050):
    b = blk(y)
    rows = [([r["name"], N(r["wealth"]), N(r["wealth_today"]), N(r["gap"]), N(r["asset"]), N(r["cash_total"]), N(r["first_cash"]), N(r["tax_first"])],
             "C", S("irs_basis", "rtc63_2", "irs_tc409", asm=True), "best" if r["gap"] == 0 else "") for r in b["rows"]]
    sec.append(tbl(f"Inheritance in {y}: sale proceeds {usd(b['start'])}; results in {y + 10}",
                   ["Option", "Wealth after 10 years", "In today's dollars", "Behind the best by", "Asset after tax", "Cash over 10 years", "Cash, first year", "Property A tax, first year"], rows))
grid = []
for y in (2040, 2045, 2050):
    for g in (0.03, 0.04, 0.05):
        b = blk(y, g)
        w = {r["option"]: r for r in b["rows"]}
        best = max(b["rows"], key=lambda r: r["wealth"])
        grid.append(([str(y), P(g, 0), N(w["sell_stock"]["wealth"]), N(w["sell_treasury"]["wealth"]), N(w["rent"]["wealth"]), N(w["live"]["wealth"]),
                      best["name"], N(b["live_cost_month_today"])], "C", S("fred_hpi_a", "treasury_cmt", asm=True)))
matrix = [([P(x["g"], 0), P(x["rs"], 0), N(x["sell"]), N(x["rent"]), N(x["live"]), x["winner"]], "C", S("fred_hpi_a", "tsp_returns", asm=True),
           "" if x["winner"] == "Sell" else "best") for x in M["matrix"]]
def sens_src(case):
    if "25-0017" in case:
        return ("lao_250017",)
    if "Insurance" in case:
        return ("cdi_compare",)
    if "Stocks return" in case:
        return ("tsp_returns", "treasury_cmt")
    if "Inflation runs" in case:
        return ("boe_lta26002", "fed_2goal")
    if "House prices" in case:
        return ("fred_hpi_a",)
    return ("hud_fmr",)


sens = [([x["case"], N(x["sell_stock"]), N(x["sell_treasury"]), N(x["rent"]), N(x["live"]), x["winner"]], "C",
         S(*sens_src(x["case"]), asm=True)) for x in M["sens"]]
brk = [
 (["Stock return at which renting equals selling", P(BE["stock_return"] / 100), "Below this, renting the home wins. The assumption is 7.0%; the 10-year Treasury yields 4.88% today."], "C", S("treasury_cmt", "tsp_returns", asm=True)),
 (["House price growth at which renting equals selling", P(BE["house_growth"] / 100), "The home must appreciate about as fast as stocks return. The local index averaged 5.7% a year since 1995."], "C", S("fred_hpi_a", asm=True)),
 (["Rent at which renting equals a stock fund", N(BE["rent_month"]), "A month, in 2026 dollars. The assumption is $6,500."], "C", S("hud_fmr", asm=True)),
 (["Rent at which renting equals Treasuries", N(BE["rent_month_vs_treasury"]), "A month, in 2026 dollars. Renting and Treasuries are close; a stock fund is not."], "C", S("treasury_cmt", asm=True)),
 (["House price growth at which renting equals Treasuries", P(BE["house_growth_vs_treasury"] / 100), "Above this, keeping the home as a rental beats selling into Treasuries. The cross-check edition puts this switch at about 4.9%."], "C", S("treasury_cmt", "fred_hpi_a", asm=True)),
]
asm_rows = [([x["item"], x["value"], x["reason"]], "A", S(*x["src"])) for x in M["assumptions"]]
body = f"""
<div class="answer"><p><strong>Sell Property A after inheriting it and reinvest. Keep Property B and keep living in its third unit.</strong></p>
<p>Selling leads in all nine combinations of inheritance year and house price growth tested below. Renting the home overtakes it only if the home appreciates about as fast as stocks return.</p></div>
<section><h2>How the options are compared</h2>
<p>Each option starts on the day Property A is inherited and ends ten years later. At the end everything is turned into cash and every tax is paid, so a house and a portfolio are measured the same way.
Cash received or paid along the way earns the same after-tax return as the stock fund ({B45['r_eq']}% a year in the base case).</p>
<ul>
<li><strong>Sell.</strong> The home is sold at its inherited value less 5.11% selling cost. Because the tax basis equals the value at death, no gain is taxed. The proceeds go into a stock index fund or into Treasuries.</li>
<li><strong>Rent.</strong> The home is reassessed to full market value. Rent, less property tax, insurance, maintenance and vacancy, is taxed after depreciation. The family stays in Property B's third unit.</li>
<li><strong>Move in.</strong> The Proposition 19 exclusion applies. The family pays the running costs and rents out Property B's third unit. Up to $500,000 of later gain is excluded on sale.</li>
</ul></section>
<section><h2>Results by inheritance year</h2><p>House prices rising 4% a year. The best option in each table is shaded.</p>{"".join(sec)}{LEGEND}</section>
<section><h2>Every year and growth rate</h2>
{tbl("Wealth ten years after the inheritance", ["Inherited in", "House growth", "Sell, stock fund", "Sell, Treasuries", "Rent", "Move in", "Best", "Monthly cost of moving in, today's dollars"], grid)}</section>
<section><h2>Why selling wins</h2><ol>
<li><strong>The sale is almost tax-free.</strong> The basis resets to the value at death, so the gain built up over the parents' lifetime is never taxed. Waiting ten years to sell turns later growth into a taxable gain at about 36%.</li>
<li><strong>The low property tax cannot be kept.</strong> Under current law the assessed value rises from about {usd(A45['base'])} to {usd(A45['live'])} if a child moves in, or {usd(A45['rent'])} if the home is rented (2045). Tax follows.</li>
<li><strong>The rent is small against the value.</strong> First-year rent of {usd(RENT['rent_first'])} loses {usd(RENT['tax_first'])} to the reset property tax. After insurance, maintenance and income tax, {usd(RENT['first_cash'])} is left: under 1% of the home's value. The sale proceeds in Treasuries at 4.88% earn several times that.</li>
<li><strong>Concentration.</strong> Keeping the home leaves a large sum in two properties in one region. Selling spreads it.</li>
</ol></section>
<section><h2>When the answer changes</h2>
{tbl("Break-even points, inheritance in 2045", ["Test", "Break-even", "Reading"], brk)}
{tbl("House price growth against stock return, inheritance in 2045", ["House growth", "Stock return", "Sell, stock fund", "Rent", "Move in", "Best"], matrix)}
{tbl("Other changes, inheritance in 2045, 4% house growth", ["Change", "Sell, stock fund", "Sell, Treasuries", "Rent", "Move in", "Best"], sens)}
<p>Moving in is the most expensive option in every case tested. It is still a reasonable choice if the family wants the home: the table above prices that choice at about {usd(B45['live_cost_month_today'])} a month in today's dollars.
If the family does move in, staying at least two years before any sale keeps the $500,000 exclusion available.</p></section>
<section id="assumptions"><h2>Assumptions</h2><p>Scenario inputs, not forecasts. The official reference beside each one supports the method or the starting figure, not the future value.</p>
{tbl("Assumption register", ["Item", "Value used", "Reason"], asm_rows)}</section>
<p>Download the figures: <a href="assets/data/decision.csv">decision.csv</a>, <a href="assets/data/model.json">model.json</a>.</p>{PRIV}"""
PAGES["decision.html"] = page("decision.html", "Decision analysis", "Decision analysis", "Sell and reinvest comes out ahead",
                              "Three options, three inheritance years, three growth rates. All compared after tax, on the same footing.", body)

# ------------------------------------------------------------------------------------------------ black swan stress tests
STRESS = M["stress"]
SX = M["stress_extras"]

hist = [
 (["1929-1932, Great Depression", "The Dow peaked at 381.17 on 3 September 1929 and closed at 41.22 on 8 July 1932, 89% below its peak; it did not regain its pre-crash high until 23 November 1954."], "V", S("fedhist_1929")),
 (["1965-1982, the Great Inflation", "CPI inflation ran at about 1% in 1964, exceeded 12% with unemployment above 7% in 1974, and peaked in March 1980 at close to 15% (14.8% over 12 months)."], "V", S("fedhist_greatinflation", "bls_mlr100")),
 (["1973-1976, first oil shock", "CPI 12-month reached 12.3% in December 1974; energy up 33.7% in September 1974."], "V", S("bls_btn11")),
 (["1977-1982, second oil shock", "CPI 12-month reached 14.8% in March 1980; energy up 47.1% the same month."], "V", S("bls_btn11")),
 (["2005-2008, pre-crisis inflation", "CPI 12-month reached 5.6% in July 2008; energy up 34.8% in September 2005."], "V", S("bls_btn11")),
 (["2000-2002, dot-com bust", "NASDAQ Composite fell from 5,048.62 on 10 March 2000 to 1,114.11 on 9 October 2002, about 78% below its peak."], "V", S("fred_nasdaqcom")),
 (["2007-2009, Great Recession", "Real GDP fell 4.3% (2007Q4 to 2009Q2); unemployment peaked at 10% in October 2009; home prices fell about 30% on average (mid-2006 to mid-2009); the S&P 500 fell 57% (October 2007 to March 2009); household and nonprofit net worth fell from about 69 trillion dollars to 55 trillion dollars."], "V", S("fedhist_greatrecession")),
 (["2007-2012, national house prices", "FHFA all-transactions index: 380.31 in January 2007 fell to 308.14 in April 2012, about 19% (computed from the published series table)."], "C", S("fred_ussthpi")),
 (["2020, COVID-19 crash", "The S&P 500 fell 34% from its February 2020 high by 23 March 2020; market-wide circuit breakers halted trading three times in March 2020."], "V", S("nyfed_covid")),
 (["2021-2022, inflation surge", "CPI 12-month reached 9.1% in June 2022, the largest 12-month increase since November 1981; December 2021 reading was 7.0%."], "V", S("bls_ted2022", "bls_btn11")),
 (["10-year Treasury yield, 1981 peak vs today", "15.84% on 30 September 1981 (FRED DGS10); 4.88% on 9 November 2026. High-inflation regimes carried high yields; deflation regimes carried yields near zero."], "V", S("fred_dgs10", "treasury_cmt")),
]

ANALOG = {"S0": S("treasury_cmt", asm=True),
          "S1": S("fedhist_greatinflation", "bls_btn11", asm=True),
          "S2": S("fedhist_1929", asm=True),
          "S3": S("fred_nasdaqcom", asm=True),
          "S4": S("fedhist_greatrecession", "fred_ussthpi", asm=True),
          "S5": S("fred_dgs10", "fedhist_greatinflation", asm=True),
          "S6": S("fred_hpi_a", asm=True)}

def cell_pct(v):
    return v if isinstance(v, str) else f"{v:.1f}%" if isinstance(v, float) else f"{v}%"

srows = []
for s in STRESS:
    srows.append(([s["name"], f'{s["inflation"]}%', cell_pct(s["house"]), cell_pct(s["stocks"]), f'{s["treasury"]}%',
                   N(s["sell_stock"]), N(s["sell_treasury"]), N(s["rent"]), N(s["live"]), s["winner"]],
                  "A", ANALOG[s["id"]], "best" if s["winner_key"] == "sell_stock" else ""))
short = {"Sell A, buy a stock index fund", "Sell A, buy Treasuries", "Keep A and rent it out", "Move into A"}
trows = [([s["name"].split(" (")[0], N(s["sell_stock_today"]), N(s["sell_treasury_today"]), N(s["rent_today"]), N(s["live_today"])],
          "C", ANALOG[s["id"]]) for s in STRESS]
erows = [([str(x["year"]), x["inflation"], N(x["home_sale_single"]), N(x["home_sale_joint"])], "C",
          S("irs_tc701", asm=True)) for x in SX["exclusion_real"]]
prow = [([x["inflation"]] + [f'{x[y]:.2f}' for y in ("2030", "2040", "2050", "2060")], "C",
         S("bls_btn11", "bls_mlr100", asm=True)) for x in SX["purchasing_power"]]
s4 = next(s for s in STRESS if s["id"] == "S4")
s2 = next(s for s in STRESS if s["id"] == "S2")
s3 = next(s for s in STRESS if s["id"] == "S3")
s1 = next(s for s in STRESS if s["id"] == "S1")
s5 = next(s for s in STRESS if s["id"] == "S5")
TODAY_HDR = "Purchasing power of one 2026 unit of money (1.00 = full value)"
stress_notes = [("S0", STRESS[0]["note"], "treasury_cmt"),
                ("S1", s1["note"], "fedhist_greatinflation"),
                ("S2", s2["note"], "fedhist_1929"),
                ("S3", s3["note"], "fred_nasdaqcom"),
                ("S4", s4["note"], "fedhist_greatrecession"),
                ("S5", s5["note"], "fred_dgs10"),
                ("S6", next(x for x in STRESS if x["id"] == "S6")["note"], "fred_hpi_a")]
notes_html = "<ul>" + "".join(
    f'<li><strong>{sid}.</strong> {note} Winner on this model: <strong>{next(x for x in STRESS if x["id"] == sid)["winner"]}</strong>.</li>'
    for sid, note, _ in stress_notes) + "</ul>"

body = f"""{PART2}
<div class="answer"><p><strong>Selling Property A and reinvesting wins in 5 of the 7 historical analogues; renting wins only when equities flatline for a decade. Moving in never wins. The reinvestment vehicle, however, depends on the regime.</strong></p>
<p>Over 2040-2060 the economy will not move in a straight line. The official record contains a depression, two inflationary oil shocks, a dot-com collapse, a housing crash, a pandemic crash and a 9.1% inflation print. This page re-runs the 2045 inheritance decision under the shapes of seven real episodes. The sale decision itself is robust; the vehicle and the margin are not.</p></div>

<section><h2>Why this section exists</h2>
<p>The inheritance is expected between 2040 and 2050, and the projections on this site run to 2060 - a horizon of 10 to 35 years, and a working lifetime of 50. Over that length, growth and inflation are never consistent: the base case here (2.5% inflation, 4% house growth, 7% stock return) is a central scenario, not a forecast. Every figure below that is not from an official publisher is computed scenario arithmetic from that grid, and is labelled as such.</p></section>

<section><h2>What the official record shows</h2>
{tbl("Verified episodes that define the stress cases", ["Episode", "What the official record shows"], hist)}{LEGEND}</section>

<section><h2>Stress tests applied to the 2045 inheritance</h2>
<p>Method. The market value at the 2045 inheritance, the tax basis reset, the Proposition 19 rule, the 2% assessed-value cap, the 10-year comparison window, and every tax rate are identical to the assumptions on the decision page. Only the post-inheritance economy is swapped: inflation (which drives costs), house price growth after 2045, stock returns, and the 10-year Treasury yield. Every option is sold and taxed at the end of the window, so the options remain comparable. House and stock cells marked <em>path</em> apply the year-by-year sequence of the historical analogue (crash first, recovery after); the 2045 market value itself is anchored to the baseline path. Computed rows; the official link on each row identifies the historical analogue it emulates.</p>
{tbl("Results ten years after a 2045 inheritance", ["Scenario", "Inflation", "Houses", "Stocks", "10-yr Treasury", "Sell, stock fund", "Sell, Treasuries", "Rent", "Move in", "Best"], srows)}{LEGEND}
{notes_html}
<p>S4 year-by-year: houses {", ".join(f"{x:+.0%}" for x in M["stress_meta"]["gfc_house"])}; stocks {", ".join(f"{x:+.0%}" for x in M["stress_meta"]["gfc_stock"])}.</p>
</section>

<section><h2>The same results in today's dollars</h2>
{tbl("Wealth deflated to 2026 purchasing power at each scenario's own inflation", ["Scenario", "Sell, stock fund", "Sell, Treasuries", "Rent", "Move in"], trows)}
<p>A nominal winner can still be a real loser: at 6% inflation (S1) a dollar buys about 0.56 of its 2045 value ten years later. Constant-dollar comparisons are how a 2040 decision should be judged.</p></section>

<section><h2>The silent risks: statutory amounts that do not rise with inflation</h2>
<p>Some of the most important numbers in this plan are fixed by statute and are not indexed for inflation. Their real value erodes every year.</p>
{tbl("Real (inflation-adjusted) value of the IRC 121 home-sale gain exclusion, $250,000 single / $500,000 joint", ["Year", "Assumed inflation", "Single return", "Joint return"], erows)}
{tbl(TODAY_HDR, ["Average inflation", "2030", "2040", "2050", "2060"], prow)}
<p>The federal estate exclusion IS indexed (chained CPI), so its real value is broadly preserved, subject to Congress: see the scenario table on the tax page. The Proposition 19 amount is indexed too, but only by one year of house price change every second year, so it grows more slowly than house prices and erodes slowly. The IRC 121 exclusion is not indexed at all: at 8% inflation the joint exclusion is worth under $120,000 in 2045 and under $80,000 in 2050, against $500,000 today.</p></section>

<section><h2>What changes - and what does not</h2>
<ol>
<li><strong>The decision to sell survives.</strong> Selling and reinvesting wins or nearly ties in all seven analogues; moving into the home is last in every one of them. The sale also monetises the tax-basis reset, which no later regime can reverse.</li>
<li><strong>The vehicle depends on the regime.</strong> Treasuries win when yields are high enough to clear inflation (S1 at 8.0%, S5 at 8.5%) and when stocks crash at the inheritance (S4); equities win in baseline and boom conditions (S0, S6); renting wins only in flat-equity analogues (S2 by {usd(s2['rent'] - s2['sell_treasury'])}, S3 by {usd(s3['rent'] - s3['sell_treasury'])} - both under 5% of the comparison base).</li>
<li><strong>Treasuries are not a hedge against high inflation at today's yield.</strong> At 4.88% with 6-9% inflation, each dollar in Treasuries loses 1-4% of real value a year. The S1 and S5 results assume the Treasury yield <em>rises with inflation</em>, as it did in the 1970s-80s; at today's 4.88% held constant, renting and equities win S1 clearly.</li>
<li><strong>Timing the sale matters less than not being forced at the bottom.</strong> S4 shows a −45% crash landing on the inheritance: the stock leg ends ten years later at only {usd(s4['sell_stock'])}, behind Treasuries at {usd(s4['sell_treasury'])}, and renting nearly ties selling. An inheritance landing mid-crash is the one case for holding the home 1-2 years and selling into the recovery.</li>
<li><strong>Nominal rents lag inflation by construction.</strong> Sitting-tenant increases are 60% of the regional index (1.5% at the assumed 2.5% inflation), so real rent declines every year in nominal-terms; that is the structural weakness of the rent option in an inflation regime.</li>
<li><strong>Concentration is itself a black swan amplifier.</strong> Both properties are in one region; a local shock hits value, rent demand and insurance availability at once (insurance has repriced nationally after the 2023-2025 wildfire and storm losses - no quote is verified here; the flagged page lists premium uncertainty). Selling converts one regional, single-asset exposure into a diversified portfolio.</li>
</ol></section>

<section><h2>Fifty years, three regimes</h2>
<p>1965-1982 rewarded rent and real assets; 1983-2000 rewarded houses and stocks together; 2000-2009 punished stocks and then housing; 2020-2022 punished everything except nominal cash yield. A plan that is optimal in exactly one of those regimes is not robust. The diversified answer the numbers keep favouring: sell A at the inheritance (the basis reset is certain; everything else is contingent), reinvest in a mix weighted to equities with a Treasury ballast sized to the then-current yield, keep Property B for its rent, and revisit the split every two years as the regime reveals itself.</p></section>

<section><h2>Black-swan playbook for the inheritance window</h2>
<ol>
<li><strong>Get the date-of-death appraisal first.</strong> Every downstream figure - basis reset, Proposition 19 amount, federal estate calculation - keys off it.</li>
<li><strong>Do not be a forced seller into a crash.</strong> The first 12-24 months are the riskiest time to sell a home into an air pocket. If the 2040-2050 economy prints a black swan, the fallback is to rent A temporarily (the model prices this) rather than sell at the trough.</li>
<li><strong>File the exclusion claims on time.</strong> One year to occupy, three years to claim (or before a sale). A missed deadline is a pure loss of roughly {usd(A45['saving'])} a year.</li>
<li><strong>Elect portability on Form 706 if a spouse survives</strong>, even with no tax due - the second exclusion is forfeited otherwise, and a black swan later can not be unwound.</li>
<li><strong>Stress the insurance, not the premium guess.</strong> Rebuild costs have repriced; get quotes at renewal and after any remodel; a lapse or underinsured total loss is the one unrecoverable black swan for the house itself.</li>
<li><strong>Keep 1-2 years of Property A running costs liquid</strong> at the inheritance so a forced sale is never required.</li>
<li><strong>Re-run this page's arithmetic every two years</strong> - the scenario grid, the Treasury yield and the tax thresholds all move; the conclusions should be re-earned, not inherited.</li>
<li><strong>Keep the fixed-rate bias.</strong> No debt is modeled in this plan; if any is ever added to A or B, fix the rate - 1981 showed what floating does to a stretched landlord.</li>
<li><strong>Two-year residency before any later sale of A</strong> if the family moves in, to keep the (unindexed) $500,000 joint home-sale exclusion available - worth about {usd(SX['exclusion_real'][4]['home_sale_joint'])} in 2045 at 2.5% inflation, far less in a high-inflation regime.</li>
</ol></section>

<section><h2>What this page is not</h2>
<p>Not a forecast, and not a timing tool. S4's year-by-year path is constructed from the verified magnitudes of the 2008 analogue, not from any prediction that 2045 will repeat it. The scenarios are deliberately wide on both sides. What the analysis supports is qualitative but firm: the sale at the inheritance is robust to every regime in the official record; the destination of the proceeds is regime-dependent and should be set with the yields and prices then in front of you.</p></section>
{PRIV}"""
PAGES["stress.html"] = page("stress.html", "Black swan stress tests", "Black swan stress tests", "What happens when the economy stops cooperating",
                           "Verified 1929, 1970s, 2000 and 2008 episodes re-run against the 2045 inheritance; the amounts that do not rise with inflation; and what changes and what does not.", body)


# ------------------------------------------------------------------------------------------------ projections
ra = [([str(r["year"]), N(r["value_low"]), N(r["value_base"]), N(r["value_high"]), N(r["assessed"]), N(r["property_tax"]), N(r["insurance"]),
        N(r["water"]), N(r["electricity"]), N(r["maintenance"]), N(r["total_cost"])], "C", S("boe_lta26002", "cnty_a_rates", asm=True)) for r in M["proj_a"]]
rb = [([str(r["year"]), N(r["value_low"]), N(r["value_base"]), N(r["value_high"]), N(r["assessed"]), N(r["property_tax"]), N(r["rent"]), N(r["insurance"]),
        N(r["water"]), N(r["electricity"]), N(r["maintenance"]), N(r["net_income"])], "C", S("boe_lta26002", "cityb_rate", "cityb_rent", asm=True)) for r in M["proj_b"]]
aft = []
for y in (2040, 2045, 2050):
    x = AFTER[y]
    rr = [([str(r["year"]), N(r["value"]), N(r["assessed_unchanged"]), N(r["tax_unchanged"]), N(r["assessed_live"]), N(r["tax_live"]),
            N(r["assessed_rent"]), N(r["tax_rent"])], "C", S("rtc63_2", "boe_lta25009", "boe_lta26002", asm=True)) for r in x["rows"]]
    aft.append(tbl(f"Property A after an inheritance in {y}: Proposition 19 amount {usd(x['amount'])}",
                   ["Year", "Market value", "Assessed, no change", "Tax, no change", "Assessed, child moves in", "Tax, child moves in", "Assessed, rented", "Tax, rented"], rr))
body = f"""
<section><h2>Property A while nothing changes</h2>
<p>No death, no sale. Assessed value rises 2% a year; market value is shown at 3%, 4% and 5%. Insurance is the owner's guess, carried forward with inflation, and is not verified.
Electricity is the owner's reported solar credit; the credit is not guaranteed beyond the 20-year period of the solar tariff.</p>
{tbl("Property A, 2026 to 2060", ["Year", "Value at 3%", "Value at 4%", "Value at 5%", "Assessed value", "Property tax", "Insurance", "Water", "Electricity", "Maintenance", "Total running cost"], ra)}</section>
<section><h2>Property B while nothing changes</h2>
<p>Two rented units. Rent rises 1.5% a year, the capped rate for sitting tenants at 2.5% inflation. Net income is rent less a 5% vacancy allowance and all costs shown, before income tax.</p>
{tbl("Property B, 2026 to 2060", ["Year", "Value at 3%", "Value at 4%", "Value at 5%", "Assessed value", "Property tax", "Rent, two units", "Insurance", "Water", "Electricity", "Maintenance", "Net income"], rb)}</section>
<section><h2>Property A after the inheritance</h2>
<p>The assessed value resets in the year of death. House prices rise 4% a year. The first two money columns show what the tax would have been had nothing changed.</p>{"".join(aft)}{LEGEND}</section>
<p>Download: <a href="assets/data/property_a.csv">property_a.csv</a>, <a href="assets/data/property_b.csv">property_b.csv</a>.</p>{PRIV}"""
PAGES["projections.html"] = page("projections.html", "Year-by-year projections", "Projections", "Value, assessed value, tax and costs by year",
                                 "From 2026 to 2060 while nothing changes, and for the ten years after an inheritance in 2040, 2045 or 2050.", body)

# ------------------------------------------------------------------------------------------------ black-swan conditions
bs = {x["case"]: x for x in M["sens"]}
BS_STOCK = bs["Stocks return 4.0% a year instead of 7.0%"]
BS_INFL = bs["Inflation runs 4.0% a year instead of 2.5%"]
BS_FLAT = bs["House prices do not rise for ten years"]
base_rows = [
 (["Inflation used for costs", "2.5% a year", "Scenario. The Federal Reserve aims for 2% (PCE); the Social Security Trustees assume 2.4% CPI-W long-run with a 1.8% to 3.0% band; CBO projects inflation consistent with 2% from 2027."], "A",
  S("fed_2goal", "ssa_trustees", "cbo_outlook", asm=True)),
 (["House price growth", "3% / 4% / 5% a year", "Scenario band. The official local index averaged about 5.3% to 5.7% a year since 1995 but was flat to slightly down over its last four quarters."], "A",
  S("fred_hpi_a", "fred_hpi_b", asm=True)),
 (["Stock index fund return", "7.0% a year", "Scenario, not a forecast. One official 12-month figure is 12.09%. Below the 4.7% break-even, renting wins instead."], "A",
  S("tsp_returns", "treasury_cmt", asm=True, flag=True)),
 (["Treasury alternative", "4.88% a year", "The 10-year par yield on 9 November 2026, held constant in every case."], "V", S("treasury_cmt")),
 (["Property tax cap", "2% a year at most", "State law. The factor was the full 2% for 2026-27 because the state index rose 3.307%."], "V", S("boe_lta26002")),
 (["Rent growth, Property B sitting tenants", "1.5% a year", "The published formula: 60% of the regional price index. The allowed increase is 1.6% from 1 March 2026."], "V", S("cityb_rent")),
 (["Federal estate exclusion after 2027", "2.5% a year", "Scenario. The amount is indexed by law; the future index is unknown. The 2026 and 2027 amounts are verified."], "A",
  S("irs_rp2532", "irs_2027", asm=True)),
]
ccpi = [
 (["1976-77", "6.250%", "1.02"], "V", S("boe_lta26002")),
 (["1980-81", "17.316%", "1.02"], "V", S("boe_lta26002")),
 (["1982-83", "11.137%", "1.02"], "V", S("boe_lta26002")),
 (["1990-91", "4.758%", "1.02"], "V", S("boe_lta26002")),
 (["1995-96", "1.194%", "1.0119"], "V", S("boe_lta26002")),
 (["2000-01", "3.214%", "1.02"], "V", S("boe_lta26002")),
 (["2010-11", "&minus;0.237%", "0.99763"], "V", S("boe_lta26002")),
 (["2014-15", "0.454%", "1.00454"], "V", S("boe_lta26002")),
 (["2021-22", "1.036%", "1.01036"], "V", S("boe_lta26002")),
 (["2022-23", "5.561%", "1.02"], "V", S("boe_lta26002")),
 (["2023-24", "7.274%", "1.02"], "V", S("boe_lta26002")),
 (["2025-26", "2.514%", "1.02"], "V", S("boe_lta26002")),
 (["2026-27", "3.307%", "1.02"], "V", S("boe_lta26002")),
 (["1976-77 to 2026-27, assessment years above the cap", "40 of 51 years", "Cap usually binding"], "C", S("boe_lta26002")),
]
episodes = [
 (["1973-75", "An embargo and production cuts nearly quadrupled the price of oil between 1973 and January 1974; the shock fed the inflation of the 1970s."], "V", S("frh_oil")),
 (["1976-83", "The state price index rose more than 6% every assessment year, peaking at 17.316% in 1980-81, while assessed values were capped at 2% a year."], "V", S("boe_lta26002")),
 (["1979-82", "The monthly federal funds average peaked at 19.10% in June 1981; unemployment peaked at 10.8% in November and December 1982."], "V", S("fred_fedfunds", "fred_unrate")),
 (["1981", "The 30-year mortgage rate peaked at 18.63% in the week of 9 October 1981."], "V", S("fred_mortgage")),
 (["1987", "The Dow fell 22.6% in a single session on 19 October 1987, the largest one-day percentage decline in history; circuit-breaker rules followed."], "V", S("frh_1987")),
 (["2000", "The Nasdaq fell nearly 40% for the year while the broadest stock indexes fell more than 10%."], "V", S("fed_mpr2001")),
 (["2007-09", "Real GDP fell 4.3%; unemployment peaked at 10.0% in October 2009; the S&amp;P 500 fell 57%; policy rates were cut to a range of 0 to 0.25%."], "V", S("frh_recession")),
 (["2006-12 housing", "The state house price index fell 41% from 2006Q3 to 2012Q1; the national index fell 19% from 2007Q1 to 2012Q2 (computed from the published series)."], "C", S("fred_casthpi", "fred_usthpi")),
 (["2020", "Unemployment reached 14.8% in April 2020; the 10-year Treasury yield fell to 0.52% on 4 August 2020."], "V", S("fred_unrate", "fred_dgs10")),
 (["2021-23", "The state index rose 5.561% in 2022-23 and 7.274% in 2023-24; the 30-year mortgage rate reached 7.79% in October 2023."], "V", S("boe_lta26002", "fred_mortgage")),
 (["2026", "Monthly consumer inflation swung from minus 0.4% in June to plus 0.6% in September and plus 0.4% in October 2026. October 2025 data do not exist: BLS did not collect them because of a lapse in appropriations."], "V", S("bls_cpi")),
 (["2026-56", "Federal debt is projected to rise from 101% of GDP in 2026 to 175% by 2056; the deficit reaches 6.7% of GDP by 2036 and interest alone 6.9% of GDP by 2056."], "V", S("cbo_outlook")),
]
stress = [
 (["Stocks return 4.0% a year instead of 7.0%", "Below the 4.7% break-even; the official precedents are the 2000 Nasdaq fall of nearly 40% and the 57% S&amp;P 500 fall of 2007-09.",
   f"Best option: {BS_STOCK['winner']}. Ten years later: selling into Treasuries {usd(BS_STOCK['sell_treasury'])}, renting {usd(BS_STOCK['rent'])}, the stock fund {usd(BS_STOCK['sell_stock'])}."], "C",
  S("fed_mpr2001", "frh_recession", "treasury_cmt", asm=True)),
 (["Inflation runs 4.0% a year instead of 2.5%", "Costs, fixed charges and maintenance rise faster; the 2% assessment cap then binds every year; the rent cap stays at 60% of the index.",
   f"Best option: {BS_INFL['winner']}. Renting falls to {usd(BS_INFL['rent'])} from {usd(RENT['wealth'])} in the base case; the sale is unchanged."], "C",
  S("boe_lta26002", "fed_2goal", asm=True)),
 (["House prices do not rise for ten years", "A flat decade; the state index also fell 41% in 2006-12, so flat is not the worst case tested by history.",
   f"Best option: {BS_FLAT['winner']}. Selling ends at {usd(BS_FLAT['sell_stock'])} against {usd(BS_FLAT['rent'])} for renting and {usd(BS_FLAT['live'])} for moving in."], "C",
  S("fred_casthpi", asm=True)),
 (["A repeat of the 2006-12 housing bust", "The state index fell 41% peak to trough; the national index fell 19%.",
   "A bust would cut the sale price and the rental value together. Selling soon after the inheritance fixes the date-of-death value before any decline; renting carries the reset tax through the whole fall."], "A",
  S("fred_casthpi", "fred_usthpi", asm=True)),
 (["Mortgage rates return toward their 1981 peak", "The 30-year rate reached 18.63% in 1981 and 7.79% in 2023; the policy rate ranged from 0.07% (2011) to 19.10% (1981).",
   "Higher mortgage rates cool housing demand. Neither property is modelled with debt; any existing loan would have to be repaid from a sale and is flagged for the owner."], "V",
  S("fred_mortgage", "fred_fedfunds", flag=True)),
 (["The federal estate exclusion is halved", "A future Congress could lower it; the model also tests the pre-2021 rules being restored.",
   f"Room for other assets in 2045 falls from {usd(E45['room_single_base'])} to {usd(E45['room_single_half'])} for one person. The sell, rent and move-in ranking does not change."], "C",
  S("irs_estate", "irs_whatsnew", asm=True)),
 (["The 2021 inheritance rules are repealed", "A failed initiative would have restored the pre-2021 exclusion; a similar measure can be filed again.",
   f"Property A's 2045 tax would be {usd(LAW['tax_restored'])} instead of {usd(LAW['tax_live_current'])} if a child moved in. Selling still finishes first."], "C",
  S("sos_memo", "lao_250017", asm=True)),
 (["State tax on financial assets", "Unofficial results on 10 November 2026: Proposition 40, a one-time tax on certain taxpayers, was rejected with 52.6% no; Proposition 42 was ahead with 51.5% yes.",
   "Certification is due 11 December 2026. As counted, the one-time state tax was rejected and a bar on new state personal-property taxes was ahead."], "V",
  S("sos_results")),
 (["A crash immediately after selling", "Black Monday: minus 22.6% in one session in 1987.",
   f"The break-even stock return is {BE['stock_return']}% over ten years: below it, renting wins. Sequencing risk is the reason proceeds are spread, not left in one fund on one day."], "C",
  S("frh_1987", "treasury_cmt", asm=True)),
]
body = f"""{PART1}
<section><h2>Why this page exists</h2>
<p>The rest of this site projects one smooth path: house prices at 3%, 4% or 5% a year, costs at 2.5%, stocks at 7%.
That is a baseline, not a forecast. Over any fifty-year period, growth and inflation are never smooth.
This page records (1) what the baseline assumes and which official body agrees with it, (2) what actually happened over the last fifty years on official data, and (3) how the plan responds if it happens again.
Nothing here changes the recommendation; the stress cases show how much would have to change before it moved.</p></section>
<section><h2>What the baseline assumes</h2>
{tbl("Baseline inputs and their official anchors", ["Item", "Value used on this site", "Why"], base_rows)}{LEGEND}</section>
<section><h2>Fifty years of official inflation data</h2>
<p>The state board publishes the consumer-price factor used to cap assessed-value increases. It is the longest official inflation series this site relies on, and it is not smooth:
the index rose more than 6% a year from 1976-77 through 1982-83, peaked at 17.316% in 1980-81, fell to minus 0.237% in 2010-11, and ran at 7.274% as recently as 2023-24.
The 2% cap on assessed values bound in 40 of the 51 assessment years from 1976-77 to 2026-27 (counted from the official factor table).
Note also the gap in official statistics: because of the federal lapse in appropriations in autumn 2025, October 2025 prices were never collected, so the 2026-27 factor was calculated from August 2024 to August 2025 instead.</p>
{tbl("Selected assessment years: state price index and assessed-value factor", ["Assessment year", "Index change", "Assessed-value factor"], ccpi)}{LEGEND}</section>
<section><h2>What actually happened: the official record</h2>
<p>Every figure below was read on the publisher's own site. Percent changes marked as computed are arithmetic on the published series.</p>
{tbl("Fifty years of economic extremes, as official sources record them", ["Episode", "What the official record shows"], episodes)}{LEGEND}</section>
<section><h2>Stress cases for this plan</h2>
<p>Each case changes one input and leaves every other assumption exactly as the base case; the figures are model outputs for an inheritance in 2045 measured in 2055, after all taxes.
These are stress tests, not forecasts.</p>
{tbl("Black-swan stress cases and what they do to the decision", ["Stress case", "Built from", "Result in the model"], stress)}{LEGEND}
<p>The pattern across the whole table: <strong>selling soon after the inheritance stays the first choice in every stress case tested.</strong>
What changes is what you sell into. A lost decade for stocks (4.0% a year) moves the money from the stock fund to Treasuries, not back into the rental.
The only thing that reverses the ranking is a set of conditions together, not any single shock: see the break-even points on the <a href="decision.html">decision page</a>.
The independent <a href="plan/index.html">cross-check edition</a> reaches the same conclusion from official figures alone.</p></section>
<section><h2>What is not modelled</h2><ul>
<li><strong>Sequence risk inside the ten years.</strong> The model applies one average return a year. A crash in year one and a boom in year nine produce the same average but a different experience; Black Monday and 2008 show the size of single-year moves.</li>
<li><strong>Insurance premiums.</strong> No official premium or quote could be confirmed; tripling the owner's guess does not change the ranking, and that test is on the decision page.</li>
<li><strong>Disasters.</strong> No flood, fire or earthquake risk premium is modelled for either property; insurance is flagged until quotes exist.</li>
<li><strong>Any debt on the properties.</strong> The model assumes both properties are unencumbered; the records supplied do not say. Flagged for the owner.</li>
</ul></section>{PRIV}"""
PAGES["black-swans.html"] = page("black-swans.html", "Black-swan conditions", "Black-swan conditions",
                                 "Growth and inflation are never smooth",
                                 "Fifty years of official data, the baseline it contradicts, and how the plan holds up when it happens again.",
                                 body)

# ------------------------------------------------------------------------------------------------ property A

# Roll history at the owner's chosen precision. Percentages are computed from the owner's own
# figures, so they do not change when the privacy tier changes.
def money(x):
    return ("blank", "Not supplied") if x is None else N(x)


def pct_cell(x):
    return ("n", "&mdash;") if x is None else ("n", f"{x:+.2f}%")


def roll_rows(hist, note):
    out = []
    for r in hist:
        check = "Not read" if r["factor"] is None and r["assessed_pct"] is None else (
            "Matches" if r["match"] is True else ("Differs" if r["match"] is False else "Not checked"))
        out.append(([str(r["year"]), money(r["bill"]), N(r["assessed"]), pct_cell(r["bill_pct"]),
                     pct_cell(r["assessed_pct"]), ("n", "&mdash;") if r["factor"] is None else ("n", f'{r["factor"]:.3f}%'),
                     check], "O", S("boe_lta26002", flag=(r["match"] is False)), "irregular" if r["match"] is False else ""))
    return out


rows = [
 (["Market value, November 2026", N(M["inputs"]["a_value"]), "Owner's estimate. An appraisal at the date of death sets the tax basis."], "O", S("irs_basis")),
 (["Assessed value, 2026", N(M["inputs"]["a_av_2026"]), f'Owner\'s record, at the owner\'s chosen precision ({M["privacy"]["description"]}).'], "O", S("boe_lta26002")),
 (["Tax bill, 2025", N(M["inputs"]["a_bill_2025"]), "Owner's record, same precision. The 2026 bill was not supplied."], "O", S("cnty_a_rates", flag=True)),
 (["Tax rate for the property's tax rate area", BLANK, "County A's rates run from 1.126% to 1.241%. The bill's tax rate area is needed. The model uses 1.18%."], "U", S("cnty_a_rates", flag=True)),
 (["Water", "$1,500 a year", "Midpoint of the owner's $100 to $150 a month."], "O", S("irs_p527")),
 (["Electricity", "&minus;$180 a year", "Solar. The owner reports a credit of $10 to $20 a month. The older solar tariffs last 20 years from connection; the connection date was not supplied."], "O", S("cpuc_nem", flag=True)),
 (["Home insurance premium", BLANK, "The owner's guess is $1,500 a year. No official figure or quote confirms it. The state's survey tool gives sample premiums, not quotes."], "U", S("cdi_compare", flag=True)),
 (["Maintenance", N(NOW_A["maintenance"]), "1.0% of an assumed building value. The owner says this home costs less to maintain than Property B."], "A", S("irs_p527", asm=True)),
 (["Total running cost, 2026", N(NOW_A["total_cost"]), "Property tax, the insurance guess, water, electricity credit and maintenance."], "C", S("boe_lta26002", asm=True)),
]
hrows = roll_rows(M["roll_a"], "A")
p19 = [([str(y), N(AFTER[y]["fmv"]), N(AFTER[y]["base"]), N(AFTER[y]["amount"]), N(AFTER[y]["live"]), N(AFTER[y]["rent"]), N(AFTER[y]["saving"])], "C",
        S("rtc63_2", "boe_lta25009", asm=True)) for y in (2040, 2045, 2050)]
body = f"""
<section><h2>What is known</h2>{tbl("Property A: inputs and current running cost", ["Item", "Value", "Note"], rows)}{LEGEND}</section>
<section><h2>Tax and assessment history, 2014 to 2026</h2>
<p>The owner's record, year by year. The bill and the assessment are published at the owner's chosen precision
({M["privacy"]["description"]}); the percentage changes are computed from the owner's record once, so they do not move when the
precision setting changes. The state factor column is the inflation factor the Board of Equalization published for that year, which
caps the rise at 2% unless there is a change in ownership or new construction.</p>
{tbl("Property A: property tax and tax assessment by year", ["Year", "Property tax", "Tax assessment", "Change in bill", "Change in assessment", "State factor", "Check"], hrows)}
<p>Every year's assessment change matches the published state factor to within one basis point. That means no new construction
and no reassessment is hidden in the record. Two irregularities in the bill column are on the
<a href="review.html">Flagged for Review</a> page: in two places the same tax amount is entered for consecutive years although the
assessed value rose 2%. Both are marked <em>Differs</em> above, and neither affects any projection, which is built from the
assessment and the rate rather than from the bills.</p>
<p class="small">Reading the table: 2017 is the one year the bill fell while the assessment rose. 2018 repeats 2017's bill.
2019 and 2020 repeat each other in the same way. A change in the fixed charges on the bill, or a bill entered twice, would
explain both; the line items would settle it (question Q-19).</p></section>
<section><h2>What the inheritance does to the assessed value</h2>
<p>If a child moves in, the new assessed value is the old one plus whatever market value exceeds the old value and the Proposition 19 amount together. With this home that is simply market value less the amount.
If the home is rented, it is assessed at full market value. The amount grows by one year's house price change every second year.</p>
{tbl("Property A at the inheritance, house prices rising 4% a year", ["Inherited in", "Market value", "Assessed before", "Proposition 19 amount", "Assessed, child moves in", "Assessed, rented", "Yearly tax saved by moving in"], p19)}
<p>If the child later moves out, the home is taxed on its market value at the date of inheritance, factored forward. The saving ends; it is not clawed back.</p></section>{PRIV}"""
PAGES["property-a.html"] = page("property-a.html", "Property A", "Property A", "The home expected to be inherited",
                                "A single-family home in County A with solar, held in a trust. Low assessed value today; that value does not survive the inheritance.", body)

# ------------------------------------------------------------------------------------------------ property B
rows = [
 (["Market value, November 2026", N(M["inputs"]["b_value"]), "Owner's estimate."], "O", S("irs_basis")),
 (["Assessed value, 2025", N(M["inputs"]["b_av_2025"]), f'Owner\'s record, at the owner\'s chosen precision ({M["privacy"]["description"]}). The 2026 value was not supplied.'], "O", S("boe_lta26002", flag=True)),
 (["Tax bill, 2025", N(M["inputs"]["b_bill_2025"]), "Owner's record, same precision."], "O", S("cityb_rate")),
 (["City B tax rate, fiscal year 2025-26", P(M["verified"]["rate_b_2025"], 5), "Applied to assessed value."], "V", S("cityb_res447")),
 (["City B tax rate, fiscal year 2026-27", P(M["verified"]["rate_b_2026"], 5), "Current year. Used for every projection."], "V", S("cityb_rate")),
 (["Fixed charges on the bill", "about " + usd(M["fixed"]["b"]), "The bill is about 80% more than rate times assessed value. The difference is fixed charges; the line items were not supplied."], "C", S("cityb_rate", flag=True)),
 (["Rent, two units", "$7,150 a month", "The third unit is available to the family at no loss of rent."], "O", S("cityb_rent")),
 (["Allowed rent increase, March 2026 to February 2027", ("n", "1.6%"), "For sitting tenants in covered units: 60% of the regional price index. A new tenancy may start at any rent."], "V", S("cityb_rent")),
 (["Rent Board fee", "about $60 a unit a year", "Charged on family-occupied units too unless an exemption is filed."], "V", S("cityb_rentfee")),
 (["Water, whole building", "$4,380 a year", "Midpoint of the owner's $330 to $400 a month."], "O", S("irs_p527")),
 (["Electricity", "$600 a year", "Midpoint of the owner's $30 to $70 a month."], "O", S("irs_p527")),
 (["Landlord insurance premium", BLANK, "The owner's guess is $1,500 a year. No official figure or quote confirms it."], "U", S("cdi_compare", flag=True)),
 (["Maintenance", N(NOW_B["maintenance"]), "1.5% of an assumed building value."], "A", S("irs_p527", asm=True)),
 (["Net income, 2026, before income tax", N(NOW_B["net_income"]), "Rent less 5% vacancy, tax, the insurance guess, water, electricity and maintenance."], "C", S("cityb_rate", "cityb_rent", asm=True)),
 (["Whether the rent ordinance covers the building", BLANK, "Depends on the date of first occupancy. No parcel or address lookup was performed."], "U", S("cityb_rent", flag=True)),
]
reset = [([str(x["year"]), N(x["value"]), N(x["tax_keep"]), N(x["tax_reset"]), N(x["increase"]), N(x["rent"]), N(x["net_keep"]), N(x["net_reset"])], "C",
          S("boe_lta26026", "cityb_rate", asm=True)) for x in M["b_reset"]]
ttx = [
 (["Below $1,000,000", ("n", "0.68%"), "Above $250,000."], "V", S("cityb_transfer")),
 (["$1,000,000 to under $5,000,000", ("n", "0.75%"), "Where Property B sits today and, at 4% growth, until about 2052."], "V", S("cityb_transfer")),
 (["$5,000,000 to under $10,000,000", ("n", "2.25%"), "The rate applies to the whole price. At 4% growth the value crosses this line around 2053; the tax on a sale triples."], "V", S("cityb_transfer")),
 (["Transfer at death", "Exempt", "No documentary transfer tax on a transfer by reason of death, outright or in trust."], "V", S("rtc11930")),
]
brows = roll_rows(M["roll_b"], "B")
body = f"""
<section><h2>What is known</h2>{tbl("Property B: inputs and current income", ["Item", "Value", "Note"], rows)}{LEGEND}</section>
<section><h2>Tax and assessment history, 2016 to 2025</h2>
<p>Same presentation as Property A. Percentages are computed from the owner's record once, so they are the same at any privacy tier.
Every assessment change with a published state factor beside it matches that factor; 2016 cannot be checked because the record begins
that year. One bill fell about 6% and one rose about 18% while the assessment moved less, which a change in fixed charges would explain.</p>
{tbl("Property B: property tax and tax assessment by year", ["Year", "Property tax", "Tax assessment", "Change in bill", "Change in assessment", "State factor", "Check"], brows)}</section>
<section><h2>If Property B passes in the same estate</h2>
<p>The owner states (11 November 2026) that the building is already owned by the beneficiary; the deed was not seen, so the question stays flagged (FL-01). If instead the parents hold title, the building changes ownership at the same death and is reassessed. In a multi-unit building the family-home exclusion covers only the unit that was the parent's principal residence and becomes the child's.
Under the owner's statement none of this applies; the table is kept as the contingency case.</p>
{tbl("Property B reassessed at market value, house prices rising 4% a year", ["Year", "Market value", "Tax, no change", "Tax, reassessed", "Increase", "Rent, two units", "Net income, no change", "Net income, reassessed"], reset)}</section>
<section><h2>If Property B is ever sold</h2>{tbl("City B transfer tax on a sale", ["Price", "Rate on the whole price", "Note"], ttx)}</section>{PRIV}"""
PAGES["property-b.html"] = page("property-b.html", "Property B", "Property B", "The rented building to keep",
                                "A small multi-unit building in City B. Two units rented, one available to the family. Very low assessed value.", body)

# ------------------------------------------------------------------------------------------------ taxes
hist_ex = [(2011, 5_000_000), (2012, 5_120_000), (2013, 5_250_000), (2014, 5_340_000), (2015, 5_430_000), (2016, 5_450_000), (2017, 5_490_000),
           (2018, 11_180_000), (2019, 11_400_000), (2020, 11_580_000), (2021, 11_700_000), (2022, 12_060_000), (2023, 12_920_000),
           (2024, 13_610_000), (2025, 13_990_000), (2026, 15_000_000)]
thr = [([str(y), N(v), N(2 * v)], "V", S("irs_estate")) for y, v in hist_ex] + [(["2027", N(15_480_000), N(30_960_000)], "V", S("irs_2027", "irs_rp2635"))]
fed = [
 (["Estate tax exclusion", "$15,000,000 (2026); $15,480,000 (2027)", "Per person. Set by Public Law 119-21 and indexed for inflation from 2027."], "V", S("irs_estate", "irs_2027", "irs_whatsnew", "irs_rp2532")),
 (["Rate above the exclusion", ("n", "40%"), "Marginal rate. The 2026 instructions publish a basic credit of $5,945,800 for a $15,000,000 exclusion, which is exactly $345,800 plus 40% of the excess over $1,000,000; the rate table itself was not opened (FL-16)."], "V", S("irs_i706", flag=True)),
 (["Two exclusions for a married couple", "Only by election", "The first estate must file Form 706 on time to pass the unused amount to the survivor, even if no tax is due."], "V", S("irs_estate", "irs_i706")),
 (["Form 706 due date", "9 months after death", "Form 4768 gives an automatic 6-month extension to file."], "V", S("irs_i706")),
 (["Annual gift exclusion", "$19,000 (2026); $20,000 (2027)", "Per recipient. Larger gifts use up the lifetime exclusion."], "V", S("irs_2027")),
 (["Basis of an inherited home", "Fair market value at death", "Selling for more than that value is a taxable gain. Selling near it is not."], "V", S("irs_basis")),
 (["Trust type", "Revocable: basis resets", "Assets of an irrevocable trust that are outside the taxable estate keep the old basis."], "V", S("irs_rr2023_2")),
 (["Long-term capital gain", "0%, 15% or 20%", "Depreciation taken on a rental is taxed at up to 25% when sold."], "V", S("irs_tc409")),
 (["Net investment income tax", ("n", "3.8%"), "On rents and gains above $250,000 of income on a joint return, $200,000 single."], "V", S("irs_tc559")),
 (["Sale of a main home", "$250,000 or $500,000 excluded", "Needs two years of ownership and use in the five years before the sale."], "V", S("irs_tc701")),
 (["Rental depreciation", "27.5 years", "On the building only. An inherited rental starts again from the value at death."], "V", S("irs_p527")),
 (["Rental losses", "Passive", "Usable against other rental income. The $25,000 allowance against other income phases out above $100,000."], "V", S("irs_p925")),
 (["State tax on Treasury interest", "None", "Obligations of the United States, and the interest on them, are exempt from state and local tax. The exemption does not extend to estate or inheritance tax, and gain on a sale is decided under the federal code."], "V", S("uscode3124", "treasury_cmt")),
]
st = [
 (["California estate or inheritance tax", "None", "No return for deaths since 2005."], "V", S("sco_estate")),
 (["City or county death tax", "Not allowed", "State law bars any political subdivision from imposing one."], "V", S("rtc13301")),
 (["California tax on capital gains", "Ordinary rates, up to 12.3%", "No lower rate for gains."], "V", S("ftb_cg", "ftb_rates")),
 (["Assessed value while owned", "Up 2% a year at most", "The cap has been reached every year since 2022."], "V", S("boe_lta26002")),
 (["Family-home exclusion", "Parent's home to child's home", "The child must live there within one year and file for the homeowners' exemption within one year."], "V", S("boe_prop19", "rtc63_2")),
 (["Exclusion limit", "Old assessed value plus $1,044,590", "For transfers to 15 February 2027. Value above the limit is added to the assessed value."], "V", S("boe_lta25009")),
 (["How the limit grows", "One year's index change every second year", "The amount rose from $1,000,000 in 2021 to $1,022,600 in 2023 and $1,044,590 in 2025."], "V", S("boe_lta25009")),
 (["Rental or second home", "No exclusion", "Reassessed at full market value at the date of death."], "V", S("boe_prop19")),
 (["Multi-unit building", "One unit only", "Only the unit that was the parent's principal residence can qualify."], "V", S("boe_lta26026")),
 (["Property held in an LLC", "No exclusion", "Even a single-member LLC. Moving an excluded home into an LLC ends the exclusion."], "V", S("boe_lta26026")),
 (["Several children", "One occupant is enough", "A trustee allowed to distribute unequally can give the home to one child. Swaps between siblings afterwards are reassessed."], "V", S("boe_lta26026")),
 (["Claim deadline", "3 years, or before a sale", "Or six months after a supplemental assessment notice. A late claim works only from the year it is filed."], "V", S("rtc63_2", "boe_lta26026")),
 (["Transfer tax on a sale, County A", ("n", "0.11%"), "Three cities in the county add a further 0.33%; confirm on the recorder's page."], "V", S("rtc11911", "cnty_a_recorder")),
 (["Transfer tax at death", "Exempt", "Applies to the transfer from the trust to the heir."], "V", S("rtc11930")),
]
est = [([str(x["year"]), N(x["exclusion"]), N(x["exclusion_couple"]), N(x["homes_base"]), N(x["room_single_low"]), N(x["room_single_base"]), N(x["room_single_high"]),
         N(x["room_couple_base"]), N(x["room_single_half"])], "C",
        S("irs_estate", "irs_2027", "irs_rp2532", asm=True)) for x in M["estate"]]
watch = [
 (["Federal estate exclusion", "Law. $15,000,000 for 2026, indexed after.", "A future Congress could lower it.", f"At half the scenario amount, room for other assets in 2045 falls from {usd(E45['room_single_base'])} to {usd(E45['room_single_half'])} for one person. The decision between selling, renting and moving in does not change."], "C", S("irs_whatsnew", "irs_rp2532", asm=True)),
 (["Initiative to repeal the 2021 inheritance rules (analysed as 25-0017)", "Failed. The Secretary of State recorded on 18 May 2026 that it lacked the signatures to qualify. It was not on the 3 November 2026 ballot.", "Would have restored the pre-2021 rule from 2027, including for transfers since 2021: inherited homes fully excluded, other property on the first $1 million of assessed value. A similar measure could be filed again.", f"If such a rule were enacted, Property A's 2045 tax would be {usd(LAW['tax_restored'])} instead of {usd(LAW['tax_live_current'])} or {usd(LAW['tax_rent_current'])}. Renting and moving in each gain about $600,000 to $700,000 over ten years. Selling still finishes first."], "C", S("sos_memo", "lao_250017", "sos_measures", asm=True)),
 (["Proposition 42, November 2026", "Voted on 3 November 2026. Unofficial count on 10 November 2026: 51.5% yes. Certification due 11 December 2026.", "Would bar new state taxes on personal property, including financial assets, and certain retroactive taxes.", "As counted, it would constrain future state taxes on financial assets; it does not change this decision."], "V", S("sos_results", "sos_measures")),
 (["Proposition 40, November 2026: one-time tax on certain taxpayers", "Rejected in the unofficial count on 10 November 2026: 52.6% no. Certification due 11 December 2026.", "A one-time state tax on certain taxpayers, wide enough to reach investment income.", "None, as counted. A similar measure can be filed again."], "V", S("sos_results")),
 (["City B rent legislation, File No. 261020", "Proposed 9 November 2026; not enacted.", "Would limit combined banked and capital-improvement rent increases on covered units to 10% a year.", "The model already grows sitting-tenant rent at 1.5% a year rather than banked stacks; no change to the ranking."], "V", S("cityb_rent")),
 (["Proposition 19 amount", "Law. Next adjustment February 2027.", "Rises by one year's house price change every second year, so it grows more slowly than house prices.", f"Modelled. The amount is {usd(A45['amount'])} in 2045 at 4% growth."], "C", S("boe_lta25009", asm=True)),
 (["Basis reset at death", "Law. No pending change was verified.", "If the reset were limited, a sale after inheriting would be taxed on the gain since the parents bought.", BLANK], "U", S("irs_basis", flag=True)),
 (["Solar tariff", "Law. 20 years from connection for older systems.", "After that the home moves to the current tariff and the bill credit shrinks.", BLANK], "U", S("cpuc_nem", flag=True)),
 (["City B rent increases", "Law. 1.6% for March 2026 to February 2027.", "Set each year at 60% of the regional price index.", "Modelled at 1.5% a year for sitting tenants."], "V", S("cityb_rent")),
 (["City B vacancy tax", "Reported struck down on appeal in September 2026.", "Read only in secondary reports; the court's opinion was not opened.", BLANK], "U", S("cityb_rate", flag=True)),
]
body = f"""
<section><h2>Federal rules</h2>{tbl("Federal estate, gift and income tax rules that bear on the decision", ["Rule", "Figure", "Note"], fed)}{LEGEND}</section>
<section><h2>State and local rules</h2>{tbl("California and local rules", ["Rule", "Figure", "Note"], st)}</section>
<section><h2>Federal estate tax: threshold history</h2>
<p>There is one threshold that matters: the federal one. California has none and local governments may not create one.</p>
{tbl("Federal estate tax filing threshold by year of death", ["Year", "One person", "Couple, if elected"], thr)}</section>
<section><h2>How much room is left for cash and investments</h2>
<p>The exclusion covers everything in the estate: both homes, cash, securities and earlier taxable gifts. The amount of cash was not supplied, so the table shows the room left after the two homes.
The 2026 and 2027 exclusions are the published amounts. From 2030 the exclusion is a scenario: $15,480,000 rising 2.5% a year. The last column cuts it in half to test a change of law. A negative number means estate tax would be due at 40% on that amount even with no other assets.</p>
{tbl("Room under the federal exclusion after both homes", ["Year of death", "Exclusion, one person", "Exclusion, couple", "Both homes at 4%", "Room, one person, 3%", "Room, one person, 4%", "Room, one person, 5%", "Room, couple, 4%", "Room if the exclusion is halved"], est)}
<p>The table assumes both homes are in the estate, the conservative reading. The owner states (11 November 2026) that Property B is already owned by the beneficiary, so it is not part of the decedent's taxable estate <a href="https://www.irs.gov/businesses/small-businesses-self-employed/estate-tax" target="_blank" rel="noopener noreferrer">IRS &middot; Estate tax thresholds</a>. If the deed confirms the statement, one person's room in 2045 is {usd(ROOM_B_OWNED)} instead of {usd(E45['room_single_base'])}, larger by Property B's 2045 value of {usd(B_VALUE_2045)}. The statement is owner-supplied; no deed was seen (flag FL-01).</p>
<p><strong>What happens above the threshold.</strong> Each dollar of taxable estate above the exclusion costs the estate 40 cents. An estate $5,000,000 over the room would owe about $2,000,000 before credits. The tax is levied on the estate, not on the person who receives the property, and it is due with Form 706 nine months after the death; California and its cities add nothing. Because the exclusion is indexed and the room depends on house prices and on the cash balance, the comparison that matters in the year of death is the published exclusion against the date-of-death values, not today's numbers.</p></section>
<section><h2>Law changes under discussion</h2>{tbl("Law watch", ["Item", "Status on 10 November 2026", "What it would change", "Effect on this decision"], watch)}</section>{PRIV}"""
PAGES["taxes.html"] = page("taxes.html", "Tax, thresholds, law watch", "Tax and law", "Rules, thresholds and what may change",
                           "Federal, state and local. Each rule was read on the official publisher's site.", body)

# ------------------------------------------------------------------------------------------------ inheritance
steps = [
 (["1", "Now", "Confirm the trust is revocable and that the deed to each property names the trust.", "[GRANTOR]", "The basis resets only for property in the taxable estate."], "V", S("irs_rr2023_2")),
 (["2", "Now", "Confirm the deed matches the owner's statement that Property B is already owned by the beneficiary, and which home carries the parents' homeowners' exemption.", "[GRANTOR], [BENEFICIARY]", "Decides which property is reassessed and which can be excluded."], "V", S("boe_lta26026", flag=True)),
 (["3", "Now", "Keep both properties out of any LLC. If there are several children, let the trustee distribute unequally.", "[GRANTOR]", "An LLC ends the exclusion. A swap between siblings is reassessed."], "V", S("boe_lta26026")),
 (["4", "Now", "If married, plan for the first death: Form 706 must be filed to keep the first spouse's unused exclusion.", "[GRANTOR]", "Without the election the second exclusion is lost."], "V", S("irs_estate", "irs_i706")),
 (["5", "Day of death", "The trust becomes irrevocable. For property tax the date of death is the date of change in ownership.", "[SUCCESSOR_TRUSTEE]", "All deadlines below run from this date."], "V", S("boe_prop19")),
 (["6", "Within 60 days", "Send the trustee's notification to every beneficiary and heir.", "[SUCCESSOR_TRUSTEE]", "Required when a revocable trust becomes irrevocable."], "V", S("prob16061_7")),
 (["7", "Promptly", "Order a written appraisal of each property as of the date of death.", "[SUCCESSOR_TRUSTEE]", "Sets the tax basis and the value used for reassessment."], "V", S("irs_basis")),
 (["8", "Immediately", "Tell both insurers. Confirm the policy still covers the home while the trust or the estate holds it, and that Property B is insured as a rental, not as an owner-occupied home.", "[SUCCESSOR_TRUSTEE]", "A lapse or the wrong policy form is the one loss no later step can undo."], "U", S("cdi_tips", flag=True)),
 (["9", "Within 150 days", "File the change in ownership statement with the assessor of each county.", "[SUCCESSOR_TRUSTEE]", "A penalty follows if a written request goes unanswered for 90 days."], "V", S("rtc480")),
 (["9", "Within 9 months", "File Form 706 if the estate exceeds the exclusion, or to elect the unused exclusion for a surviving spouse. Pay any tax.", "[SUCCESSOR_TRUSTEE]", "Form 4768 extends the filing date by six months."], "V", S("irs_i706")),
 (["10", "Within 10 years of the death", "Empty any inherited retirement account within ten years, and spread the withdrawals. Each withdrawal is ordinary income.", "[BENEFICIARY]", "A non-spouse beneficiary may generally not stretch the account over a lifetime. Ask a preparer to model the brackets."], "V", S("irs_rmd_faq")),
 (["11", "Decide early", "Choose: sell, rent or move in. A sale close to the date of death has almost no gain.", "[BENEFICIARY]", "Growth after the death is taxable when sold."], "V", S("irs_basis")),
 (["12", "If moving in: within 1 year", "Occupy the home as the principal residence and file the homeowners' exemption claim.", "[BENEFICIARY]", "Miss it and the exclusion applies only from the year of filing."], "V", S("boe_prop19", "rtc63_2")),
 (["13", "If moving in: within 3 years", "File the parent-child exclusion claim, and in any case before a sale to a third party.", "[BENEFICIARY]", "Or within six months of a supplemental assessment notice."], "V", S("boe_prop19", "rtc63_2")),
 (["14", "After the assessor acts", "Expect a supplemental tax bill for the reassessed value. Late instalments carry a 10% penalty.", "[BENEFICIARY]", "Budget for it: the first bills arrive months later."], "V", S("cityb_rate", "cnty_a_rates")),
 (["15", "On distribution", "Record the deed from the trust to the heir. No transfer tax is due on a transfer by reason of death.", "[SUCCESSOR_TRUSTEE]", "State the exemption on the deed."], "V", S("rtc11930")),
 (["16", "If selling", "Sell, pay the 0.11% county transfer tax, and report the sale with the date-of-death value as basis.", "[BENEFICIARY]", "Reported on Schedule D and Form 8949."], "V", S("rtc11911", "irs_basis")),
 (["17", "If renting", "Start depreciation from the date-of-death value of the building. Keep the land value separate.", "[BENEFICIARY]", "27.5 years; taxed back at up to 25% on sale."], "V", S("irs_p527", "irs_tc409")),
 (["18", "If living there, later", "Stay two years before any sale to keep the home-sale exclusion. Tell the assessor on moving out.", "[BENEFICIARY]", "Moving out ends the property tax exclusion."], "V", S("irs_tc701", "boe_prop19")),]
steps = [([str(i)] + list(r[0][1:]), r[1], r[2]) for i, r in enumerate(steps, 1)]
body = f"""{tbl("From today to the years after the inheritance", ["Step", "When", "What to do", "Who", "Why it matters"], steps)}{LEGEND}
<section><h2>What a trust does and does not do</h2><ul>
<li>A revocable trust keeps the property in the taxable estate, which is what resets the basis.</li>
<li>A trust does not prevent reassessment. The assessor looks through the trust to the people who benefit.</li>
<li>A revocable trust does not take property out of the federal taxable estate. The exclusion is what shelters it.</li>
</ul>
<p>The official names and numbers of the county forms, and the trust's own income tax filing during administration, were not verified in this session; they are on the Flagged for Review page.</p></section>{PRIV}"""
PAGES["inheritance.html"] = page("inheritance.html", "Inheritance steps", "Inheritance by trust", "Step by step, with deadlines",
                                 "What to do now, at the death, and in the three years that follow.", body)

# ------------------------------------------------------------------------------------------------ flagged for review
fl = [
 ("FL-01", "Who holds title to Property B", "The owner states (11 November 2026) that the building is already owned by the beneficiary; the deed was not seen. Title decides whether the building is reassessed at the same death and whether it is in the decedent's estate.", "The current deed or trust schedule", "boe_lta26026"),
 ("FL-02", "Which home is the parents' principal residence", "Only that home can be excluded, and only one unit of a multi-unit building.", "Homeowners' exemption shown on the tax bill", "boe_prop19"),
 ("FL-03", "Whether the trust is revocable", "The basis reset depends on it.", "The trust document", "irs_rr2023_2"),
 ("FL-04", "Cash, securities, earlier taxable gifts, marital status", "The owner says the cash may exceed the exclusion. No amount was supplied, so the room is shown without it.", "A list of assets and gift tax returns", "irs_estate"),
 ("FL-05", "Home insurance premium, Property A", "The owner's guess of $1,500 a year is unconfirmed. The state survey tool is interactive and gives samples, not quotes.", "Two written quotes at replacement cost", "cdi_compare"),
 ("FL-06", "Landlord insurance premium, Property B", "The owner's guess of $1,500 a year is unconfirmed.", "Two written landlord-policy quotes", "cdi_compare"),
 ("FL-07", "Market rent for Property A", "The $6,500 a month is an assumption. The federal rent dataset documentation was opened on 11 November 2026, but area values were deliberately not retrieved (location privacy).", "A written rental analysis; a broker rent survey", "hud_fmr"),
 ("FL-08", "Tax rate area of Property A", "The rate is printed on the bill. Only the county-wide range was verified.", "The bill's tax rate area and rate", "cnty_a_rates"),
 ("FL-09", "Fixed charges on both tax bills", "Property B's bill is about 80% above rate times value. One year's bill rose about 18% and another fell about 6% with no matching change in value.", "The line items on each bill", "cityb_rate"),
 ("FL-10", "Duplicate tax amounts in Property A's record", "Two pairs of consecutive years carry the same tax amount although the assessed value rose 2%. The cause is not known.", "The bills for those years", "boe_lta26002"),
 ("FL-11", "One year of Property B's assessed value", "It rose slightly less than the state factor. The year is reported to the owner privately.", "The assessor's roll history", "boe_lta26002"),
 ("FL-12", "2026 figures", "No 2026 tax bill for Property A and no 2026 assessed value or bill for Property B were supplied.", "The 2026-27 bills", "boe_lta26002"),
 ("FL-13", "Solar connection date and tariff", "The 20-year period decides when the electricity credit ends.", "The utility's interconnection letter", "cpuc_nem"),
 ("FL-14", "Whether the rent ordinance covers Property B", "Depends on the date of first occupancy and the legal unit count. No parcel lookup was performed.", "Certificate of occupancy; Rent Board record", "cityb_rent"),
 ("FL-15", "Result of the 3 November 2026 measures", "Results are not certified; certification is due 11 December 2026. The unofficial count on 10 November 2026 had Proposition 42 ahead with 51.5% yes and Proposition 40 rejected with 52.6% no.", "The certified statement of vote", "sos_results"),
 ("FL-24", "Any mortgage or debt on either property", "The model assumes both properties are unencumbered. A loan would have to be repaid from a sale, or would reduce the room under the federal exclusion.", "Loan statements or the trustee's schedule of assets", "irs_estate"),
 ("FL-25", "Privacy precision of the roll tables", "At the owner's instruction of 12 November 2026 the roll values and bills are published to the nearest $10. That is close enough to the county record that a reader who knows the record could match it; the tier can be raised to $1,000 or $10,000 with one command.", "The owner's choice of tier", "boe_lta26002"),
 ("FL-26", "Whether any retirement account is in the estate", "Not supplied. If one exists the ten-year distribution rule applies and the withdrawals are ordinary income; nothing is modelled for it.", "The beneficiary designations", "irs_rmd_faq"),
 ("FL-27", "Insurance cover above $3,000,000", "The FAIR Plan, the insurer of last resort, caps a residential risk at $3,000,000 for all coverages combined, which is below Property A's current estimated value. Whether the admitted market will write the full value is not known.", "A broker's placement note and a Difference in Conditions quote", "cdi_tips"),
 ("FL-28", "Water, electricity and solar dates", "Both properties' water and electricity figures are the owner's estimates; no tariff was read, and the solar interconnection date that sets the 20-year credit period was not supplied.", "Two utility bills, the net-metering agreement and the suppliers' tariff sheets", "cpuc_nem"),
 ("FL-29", "The value of the inherited cash", "The brief says the inheritance includes a considerable amount of money that may exceed the federal threshold. No figure was given, so the tax tables show the room and not the tax.", "One total, kept private; only the rounded total need be published", "irs_estate"),
 ("FL-30", "Professional fees at the death", "Appraisal, trustee, attorney and recording costs are described but not quoted. They are the only transfer costs that remain once the death taxes are ruled out.", "Written fee schedules from the trustee's attorney and an appraiser", "irs_estate"),
 ("FL-16", "The 40% estate tax rate", "Derived from the published credit amount. The rate table was not opened.", "Table A in the Form 706 instructions", "irs_i706"),
 ("FL-18", "Long-run stock return", "7.0% is an assumption. Only a 12-month official figure was read.", "The fund's long-run return table", "tsp_returns"),
 ("FL-19", "City B vacancy tax", "Reported struck down on appeal in September 2026 by secondary sources only.", "The Court of Appeal opinion", "cityb_rate"),
 ("FL-20", "Pending bills on the basis reset", "None was verified. Treated as hypothetical.", "A search of current federal bills", "irs_basis"),
 ("FL-21", "County form names and the trust's tax filing", "The steps cite the statutes. Form numbers and the trust's income tax return were not verified.", "The assessor's forms page; a tax preparer", "rtc480"),
 ("FL-22", "Building share of value, bedrooms, condition", "Drive depreciation and maintenance. Assumed.", "The assessor's land and improvement split; an inspection", "irs_p527"),
 ("FL-23", "Sources read as excerpts", "Twelve sources were read as excerpts served from the official domain, not as whole documents. They are marked in the source library.", "Open each link", "irs_i706"),
]
rows = [([i, item, why, BLANK, fix], "U", S(src)) for i, item, why, fix, src in fl]
body = f"""<div class="note"><strong>Nothing on this page blocks the plan.</strong> These are the items that could not be confirmed from an official source, or that only the owner can settle.
Each value is left blank rather than estimated. The list is ordered by how much each item could change the answer.</div>
{tbl("Flagged for Review", ["No.", "Item", "Why it is flagged", "Value", "What settles it"], rows)}{LEGEND}
<section><h2>Four privacy disclosures</h2><ul>
<li><strong>Repository history.</strong> Earlier commits in this public repository contain exact figures and location details, and earlier pull-request titles named jurisdictions. This edition cannot remove them. Rewriting the history or making the repository private is the owner's decision (suggestion S-12).</li>
<li><strong>Jurisdictions.</strong> The pages name only County A and City B, but the official local links identify them to anyone who opens one. Dropping the local sources would remove that, at the cost of unsourced local rates.</li>
<li><strong>Roll values at $10.</strong> The property tax and assessment tables now publish the county record rounded to the nearest $10, as instructed on 12 November 2026. The honest reading of that setting: it defeats a search for an exact number, and it does not defeat a search by someone who has the record. The growth chain from 2014 is itself a fingerprint. Tier 2 ($1,000) or tier 3 ($10,000) is materially stronger; the setting is a committed file, and the switch is one command (suggestions page, "the privacy choice").</li>
<li><strong>What is deliberately not published.</strong> No name, street address, postal code, parcel number, utility account, employer, or the amount of the cash inheritance. People appear as [GRANTOR], [SUCCESSOR_TRUSTEE] and [BENEFICIARY]. The site has no forms, no scripts, no analytics and no remote assets, so nothing on it can collect anything from a reader.</li>
</ul></section>{PRIV}"""
PAGES["review.html"] = page("review.html", "Flagged for review", "Flagged for review", "Unverified, unknown or irregular",
                            f"{len(fl)} open items with the official page that bears on each, and four privacy disclosures.", body)

# ------------------------------------------------------------------------------------------------ audit
corr = [
 ("C-01", "Federal exclusion for 2027", "Marked not verified because a shortened web address returned an error; later years were indexed from 2026.", "$15,480,000, read on the IRS release at its full address. Annual gift exclusion $20,000.", "irs_2027"),
 ("C-02", "City B tax rate", "1.18162182% was replaced by 1.18268325% as a correction.", "Both are real. 1.18268325% was fiscal year 2025-26; 1.18162182% is fiscal year 2026-27 and is used from 2026.", "cityb_rate"),
 ("C-03", "Property B tax bill", "Projected as rate times assessed value, about $1,380 for 2026, although the bill is about $2,400.", "Rate times value plus about $1,100 of fixed charges, in every year.", "cityb_rate"),
 ("C-04", "Property A tax after reassessment", "The whole bill divided by assessed value, 1.336%, was applied to multi-million reassessed values.", "1.18% on value plus fixed charges of about $830. The earlier method overstated the 2045 tax by about $10,000 a year.", "cnty_a_rates"),
 ("C-05", "Growth of the Proposition 19 amount", "3% every year, giving about $1,886,640 in 2045.", f"One year's index change every second year, as the rule is written: {usd(A45['amount'])} in 2045.", "boe_lta25009"),
 ("C-06", "End-of-period comparison", "A kept house was counted at full market value with no selling cost or tax; the stock portfolio's gain was taxed.", "Every option is sold and taxed at the end.", "irs_tc409"),
 ("C-07", "Depreciation on the rental", "Ignored, which the earlier edition noted overstated the tax.", "Deducted over 27.5 years from the value at death, and taxed back on sale.", "irs_p527"),
 ("C-08", "Rent for Property A", "3.0% of value, about $7,750 a month.", "$6,500 a month, with the break-even rent reported so the result does not rest on it.", "hud_fmr"),
 ("C-09", "Rent growth in Property B", "2.5% a year; the cap was not checked.", "1.5% a year for sitting tenants: 60% of 2.5% inflation, per the published formula.", "cityb_rent"),
 ("C-10", "Property B at the same death", "Assessed value rose 2% a year through and after the inheritance.", "Shown both ways. If the parents hold title, the building is reassessed except for one qualifying unit.", "boe_lta26026"),
 ("C-11", "Comparison period", "Every case ended in 2055, so an inheritance in 2050 was judged over five years.", "Ten years after each inheritance year.", "irs_basis"),
 ("C-12", "Roll values in public files", "Assessment histories were published to the nearest $10, and one bill to the dollar.", "Generalised to the nearest $10,000 and $100, then republished at the owner's instruction on 12 November 2026 (C-13).", "boe_lta26002"),
 ("C-13", "Property tax and assessment tables", "The year-by-year bills and assessments were withheld altogether, on the view that any published roll figure identifies a parcel.", "Published in full at the precision the owner chose on 12 November 2026 (nearest $10), with the published state factor beside each year and the percentage changes computed before rounding. The setting is a committed file, so it can be raised to $1,000 or $10,000 without touching the analysis.", "boe_lta26002"),
]
CB = {"C-01": "V", "C-02": "V", "C-03": "C", "C-04": "C", "C-05": "V", "C-06": "C", "C-07": "V", "C-08": "A", "C-09": "V", "C-10": "V", "C-11": "C", "C-12": "C", "C-13": "C"}
rows = [([i, item, old, new], CB[i], S(src)) for i, item, old, new, src in corr]
repo = [
 ("Published pages", "Thirteen pages are generated from one model and one source ledger. A stale page fails the build."),
 ("Retired pages and data files", "Paths used by earlier editions hold withdrawal notices with no figures. The build fails if any other tracked file appears."),
 ("Source ledger", "Each source records how it was checked: opened, or read as an excerpt served from the official domain."),
 ("Checks", "Every factual table row must link to an official publisher; a row that records a choice must link to the reasoning behind it. Dollar amounts must be multiples of $10. City names, postal codes, parcel numbers and e-mail addresses fail the build."),
 ("Publishing", "The site is served from the main branch. Both publishing paths carry the same sanitised files. Earlier sessions report that the setting itself could not be changed with the available permissions."),
 ("Repository history", "Earlier commits contain exact figures and location details. Not rewritten. Needs the owner's decision."),
 ("Pull requests from other sessions", "Three pull requests (#23, #25 and #34) would each have replaced this edition with a model that predates the corrections listed above. They were closed without merging on 11 November 2026; their branches remain for reference. The substantive additions in #34 - a 40-window historical replay and an insurance framework - are covered by the two black-swan pages and by the sensitivity cases on the decision page, including insurance at three times the owner's guess."),
]
rlist = "<ul>" + "".join(f"<li><strong>{area}.</strong> {finding}</li>" for area, finding in repo) + "</ul>"
body = f"""
<section><h2>What this page is</h2>
<p>A second session re-checked the edition published earlier the same day, line by line, against the official sources. Twelve items were corrected. The largest effects came from C-04, C-05 and C-06.
The earlier edition's source work was sound: its quotations matched the official pages wherever they were re-opened.</p>
{tbl("Corrections to the earlier edition", ["No.", "Item", "Earlier edition", "This edition"], rows)}{LEGEND}</section>
<section><h2>What the 11 November 2026 pass added</h2>
<p>Twelve sources in the ledger were opened or re-opened on the publisher's own domain on 11 November 2026: the IRS estate page and the 2027 inflation release, the Proposition 19 page and Letters 2025/009 and 2026/002, Revenue and Taxation Code section 63.2, the local secured-tax page, the rent-increase page, the Treasury yield table, the inherited-basis FAQ, the HUD dataset documentation and the Federal Reserve inflation-goal FAQ. Every quoted figure matched what was already published; no number changed. Fifteen sources were added for the new <a href="black-swans.html">black-swan conditions</a> page (Federal Reserve, Federal Reserve History, BLS, CBO, SSA, the state election results service and six FRED series), the source library now holds {len(SRC)} entries, and three stress cases were added to the model: stocks at 4.0% a year, inflation at 4.0% a year, and a flat decade for house prices. Selling still finishes first in all three. The law watch gained the unofficial 3 November 2026 ballot results and a pending local rent measure, and the flagged list gained one item: any debt on the properties.</p></section>
<section><h2>Second pass, 11 November 2026</h2>
<p>A third session re-checked this edition on 11 November 2026 before publishing it. Thirteen ledger entries were re-opened on the publishers' own domains: the IRS estate page, the 2026 Form 706 instructions, the 2027 inflation release, the Proposition 19 page and Letter 2025/009, Revenue and Taxation Code sections 63.2 and 13301, the local secured-tax page, the local rent-increase page, the Department of Insurance premium-survey page, the Secretary of State's initiative memorandum and its unofficial election results, and the Treasury yield table. The figures already published matched in every case; no number changed.</p>
<p>Three things were added or corrected. First, a gap: the state-tax treatment of Treasury interest had been left as an unverified assumption (FL-17). It is now read in 31 U.S.C. 3124 on the U.S. Government Publishing Office's own site, which exempts Treasury obligations and their interest from state and local tax but expressly not from an estate or inheritance tax; the flag is closed and the rule appears on the tax page. Second, the 40% estate-tax rate is now tied to the published 2026 credit of $5,945,800, which is exactly $345,800 plus 40% of the excess over $1,000,000; the rate table itself is still not opened, so FL-16 stays open. Third, a stale count on this page (58 sources) was replaced by a number the build computes.</p>
<p>The arithmetic was re-checked independently of the renderer: all 35 projection years for each property were recomputed from the model's own formulas (tax = rate x assessed value plus fixed charges; running costs summed; assessed value capped at 2%), the estate-room rows were recomputed from the exclusion less both homes, and the 2045 reassessment was recomputed from the Proposition 19 formula. Every published figure agreed to the nearest $10. The page structure was also changed: the menu is now grouped into five sections, the two black-swan pages are labelled as parts 1 and 2 of one section instead of appearing twice under different names, and the overview states which of the three editions in this repository a reader is looking at.</p></section>
<section><h2>Third pass in this edition: 12 November 2026</h2>
<p>This session re-opened, on the publishers' own domains, the documents behind the figures that decide the answer: the IRS estate tax
threshold page (the 2026 threshold of $15,000,000 and the portability election), the IRS 2027 inflation release ($15,480,000 and the
$20,000 gift exclusion), the Board of Equalization's Proposition 19 comparison charts (the value limit, the one-year occupancy and
homeowners' exemption condition, the three-year claim), the State Controller's estate tax page (no California return for deaths since
1 January 2005), Revenue and Taxation Code sections 480 and 63.2 (the 150-day change in ownership statement; the one-year occupancy and
claim), and the IRS inherited-basis FAQ. Every figure already published matched.</p>
<p><strong>Four sources were added.</strong> 26 U.S.C. 102, read in full on the Government Publishing Office's site, settles a gap the
earlier edition left: property acquired by inheritance is not gross income, although the income from it is. The IRS required-minimum-distribution
FAQ settles the second: for an owner who died after 2019 a non-spouse beneficiary must generally empty an inherited account within ten
years. Two Department of Insurance pages were added for the insurance question: the department's top-ten guidance, which states that the
FAIR Plan is open to every homeowner and that its maximum for all coverages combined is $3,000,000, and the 2019 release that establishes
the plan as the insurer of last resort.</p>
<p><strong>Two pages are new.</strong> <a href="questions.html">Questions and answers</a> lists 35 questions with their status, the
official rule behind each, the step that would close each one, and what changes if the answer differs. <a href="suggestions.html">Suggestions
and paths</a> sets out four paths and sixteen suggestions with effort and privacy cost. The navigation was regrouped to put both under
"Start here".</p>
<p><strong>One setting changed.</strong> The owner instructed on 12 November 2026 that the property tax and assessment history be published
at $10 precision. It is now published in full, at that precision, on both property pages, with percentage changes computed before rounding.
The trade-off is stated on every page and on this page's privacy disclosures; the precision is a committed setting, not a rewrite.</p>
<p><strong>What was checked by hand and what was not.</strong> Every projection row was recomputed from the model's own formulas after the
precision change and agreed to the nearest $10. The arithmetic of the estate room, the reassessment and the break-evens was re-run by the
model and asserted in the build. Not done: no insurer was contacted, no address or parcel lookup was made, no water or electricity tariff
was read, and no statute not named above was opened in this session.</p></section>
<section><h2>Repository review</h2><p>Findings from reading the repository itself. These are observations, not sourced facts.</p>{rlist}</section>
<section><h2>How this edition relates to the cross-check</h2>
<p>A separate <a href="plan/index.html">cross-check edition</a> was built by another session with its own model and its own source ledger. It leaves unverifiable inputs blank and reports break-evens.
Both reach the same default: sell Property A in the first year and keep Property B. The cross-check compares selling with Treasuries only and finds that margin thin; this edition agrees
(renting and Treasuries finish close together) and adds the stock index fund, which leads in every case tested at a 7% return.
The cross-check's reconciliation table describes the edition that preceded this one; items it raised about the 2027 exclusion, the City B rate, the Treasury yield, rent growth and the failed initiative are adopted here.</p></section>
<section><h2>What was not done</h2><ul>
<li>No address, parcel or owner lookup was made in any public record.</li>
<li>No insurer was contacted and no quote was obtained.</li>
<li>Pages were checked by build rules and by reading the generated files, not in a browser.</li>
</ul></section>{PRIV}"""
PAGES["audit.html"] = page("audit.html", "Independent verification", "Independent verification", "What a second check changed",
                           "Twelve corrections to the earlier edition, each with the official source that settles it.", body)

# ------------------------------------------------------------------------------------------------ sources
rows = []
for sid, s in SRC.items():
    how = s["checked"]
    basis = "U" if how.startswith("NOT") else "V"
    rows.append(([f"<code>{sid}</code>", e(s["publisher"]), e(s["title"]), "<br>".join(e(v) for v in s["verifies"]), e(how)], basis, a(sid)))
body = f"""<p>{len(SRC)} official sources. The exact words relied on are stored with each source in <a href="assets/sources.json">sources.json</a>.
Local sources name the jurisdiction in their web address; the pages refer to it as County A or City B.</p>
{tbl("Source library", ["Id", "Publisher", "Document", "What it supports", "How it was checked (10 to 12 November 2026)"], rows)}{LEGEND}{PRIV}"""
PAGES["sources.html"] = page("sources.html", "Source library", "Source library", "Every source, and how it was checked",
                             "Open any link to check the figure yourself.", body)

for name, text in PAGES.items():
    (ROOT / name).write_text(text, encoding="utf-8")

# Plain-text executive summary kept in the repository
(ROOT / "EXECUTIVE_SUMMARY.md").write_text(f"""# Executive summary

Reviewed 10 to 12 November 2026. Anonymised: Property A (single-family home, County A), Property B (small multi-unit building, City B).
Every dollar figure is rounded to the nearest $10. Assessment-roll values and tax bills are published at the owner's chosen precision
({M["privacy"]["description"]}); percentage changes are computed before rounding. Planning analysis, not legal, tax or investment advice.

**Best plan on these numbers: sell Property A soon after inheriting it, reinvest, and keep Property B.**

Inheritance in 2045, house prices rising 4% a year, measured ten years later after all taxes and selling costs:

| Option | Wealth after 10 years | Behind the best by |
|---|---|---|
| Sell, stock index fund | ${SELL['wealth']:,} | $0 |
| Sell, Treasuries | ${TRE['wealth']:,} | ${-TRE['gap']:,} |
| Rent the home out | ${RENT['wealth']:,} | ${-RENT['gap']:,} |
| Move in | ${LIVE['wealth']:,} | ${-LIVE['gap']:,} |

- The sale is almost tax-free: the tax basis resets to the value at death, provided the trust is revocable.
- The low property tax does not survive. About ${NOW_A['property_tax']:,} a year today becomes ${LIVE['tax_first']:,} if a child moves in and ${RENT['tax_first']:,} if rented (2045).
- Renting wins only if stocks return under {BE['stock_return']}% a year or the home appreciates about {BE['house_growth']}% a year.
- Living in the home costs about ${B45['live_cost_month_today']:,} a month in today's dollars compared with selling.
- The inheritance itself is not income to the heir (26 U.S.C. 102); income from the property, and a later sale, are taxed.
- An inherited retirement account, if there is one, must generally be emptied within ten years and each withdrawal is ordinary income.
- Federal estate tax: $15,000,000 per person in 2026 and $15,480,000 in 2027; California has none and its cities may not impose one.
- Above the exclusion the estate pays 40 cents for every dollar: an estate $5,000,000 over the room owes about $2,000,000 before credits. The tax is on the estate, not on the heir, and is due with Form 706 nine months after the death.
- The owner states Property B is already owned by the heir, so under that statement it sits outside the decedent's estate; if it were in the same estate its tax would reset: ${BR45['tax_keep']:,} to ${BR45['tax_reset']:,} a year in 2045.
- Under that same statement one person's estate-tax room in 2045 is ${ROOM_B_OWNED:,} instead of ${E45['room_single_base']:,}, larger by Property B's 2045 value of ${B_VALUE_2045:,}. The deed was not seen (FL-01).
- Insurance premiums are unverified and left blank. The FAIR Plan, the state's insurer of last resort, caps a residential risk at $3,000,000 for all coverages combined, below Property A's current value; tripling the owner's guess does not change the ranking.
- Property tax and assessment: the full history, 2014 to 2026 for Property A and 2016 to 2025 for Property B, is published at $10 precision on the property pages, with the published state factor beside each year.
- Black swans, part 1 (black-swans.html): the baseline's official anchors, fifty years of state inflation data, and the fixed amounts whose real value erodes.
- Black swans, part 2 (stress.html): stock returns at 4.0%, inflation at 4.0% or a flat decade for house prices - selling still finishes first, and a lost decade only moves the proceeds to Treasuries. Verified 1929, 1965-82, 2000-02, 2007-09 and 2020 episodes re-run against the 2045 inheritance: the sale decision holds in 5 of 7 analogues, and only the reinvestment vehicle changes with the regime.
- New on 12 November 2026: a page of 35 questions with their status and the step that closes each one (questions.html), and a page of four paths and sixteen suggestions with effort and privacy cost (suggestions.html).
- Sources: {len(SRC)} official documents, four added on 12 November 2026 (26 U.S.C. 102; the IRS RMD FAQ; two Department of Insurance pages on insurance availability). The figures behind the decision were re-opened on the publishers' sites that day; none changed.

Site: index.html. Open questions: questions.html. Options: suggestions.html. Open items: review.html. How it was checked: audit.html. Sources: sources.html.
""", encoding="utf-8")

print(f"built {len(PAGES)} pages")
