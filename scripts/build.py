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
       ("decision.html", "Decision analysis"), ("projections.html", "Year-by-year projections"),
       ("property-a.html", "Property A"), ("property-b.html", "Property B"),
       ("taxes.html", "Tax, thresholds, law watch"), ("inheritance.html", "Inheritance steps"),
       ("review.html", "Flagged for review"), ("audit.html", "Independent verification"),
       ("sources.html", "Source library")]

SHORT = {"Internal Revenue Service": "IRS", "California State Board of Equalization": "BOE",
         "California Legislative Information": "CA code", "California Franchise Tax Board": "FTB",
         "California Public Utilities Commission": "CPUC", "California Department of Insurance": "CDI",
         "California Legislative Analyst's Office": "LAO", "California Secretary of State": "CA SOS",
         "California State Controller": "CA Controller", "U.S. Department of the Treasury": "US Treasury",
         "Federal Retirement Thrift Investment Board": "TSP", "U.S. Department of Housing and Urban Development": "HUD",
         "Federal Reserve Bank of St. Louis (data: Federal Housing Finance Agency)": "FHFA index"}
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
         "fred_hpi_a": "Area A", "fred_hpi_b": "Area B", "hud_fmr": "Fair Market Rents"}

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
         "C": ("b-c", "Computed"), "U": ("b-u", "Unverified")}
LEGEND = ('<p class="legend">' + "".join(f'<span class="b {c}">{t}</span>' for c, t in BADGE.values()) +
          ' Verified = the figure was read in text from the official publisher\'s own domain on 10 November 2026; the source library says whether the whole page was opened or an excerpt was read. Owner-supplied = taken from the '
          'owner\'s records, not independently checked. Assumption = a scenario input. Computed = arithmetic on the '
          'rows above. Unverified = no official confirmation, so the value is blank.</p>')


def tbl(caption, headers, rows, cls=""):
    hd = "".join(f'<th scope="col">{h}</th>' for h in list(headers) + ["Basis", "Official source"])
    body = []
    for row in rows:
        cells, basis, src = row[0], row[1], row[2]
        rc = row[3] if len(row) > 3 else ""
        tds = "".join(f'<td class="{c[0]}">{c[1]}</td>' if isinstance(c, tuple) else f"<td>{c}</td>" for c in cells)
        bc, bt = BADGE[basis]
        body.append(f'<tr class="{rc}">{tds}<td><span class="b {bc}">{bt}</span></td><td>{src}</td></tr>')
    return (f'<div class="table-wrap"><table class="{cls}"><caption>{caption}</caption><thead><tr>{hd}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def page(name, title, eyebrow, h1, lead, body):
    cur = 'aria-current="page" '
    nav = "".join(f'<a {cur if href == name else ""}href="{href}"><span>{i:02d}</span>{label}</a>'
                  for i, (href, label) in enumerate(NAV, 1))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Inherited-home decision dashboard: sell, rent or move in. Official sources, anonymised.">
<meta name="referrer" content="no-referrer"><meta name="robots" content="noindex">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self'; img-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
<title>{title} &middot; Inheritance decision dashboard</title><link rel="stylesheet" href="assets/style.css"></head><body>
<a class="skip" href="#main">Skip to content</a>
<aside><a class="brand" href="index.html">Inheritance decision dashboard<small>Property A and Property B</small></a>
<div class="nav-label">PAGES</div><nav aria-label="Main navigation">{nav}</nav>
<div class="aside-note">Anonymised. Dollar figures rounded to $10. Reviewed 10 November 2026.</div></aside>
<main id="main"><div class="top"><span>{eyebrow}</span><span>Reviewed 10 Nov 2026</span></div>
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
PRIV = ('<div class="privacy"><strong>Privacy.</strong> Properties are Property A (a single-family home in County A) and '
        'Property B (a small multi-unit building in City B). People are [GRANTOR], [SUCCESSOR_TRUSTEE] and [BENEFICIARY]. '
        'Assessment-roll values and tax bills are public records that can be matched to a parcel, so they appear here only '
        'in generalised form: assessed values to the nearest $10,000 and bills to the nearest $100. '
        'Every other figure is rounded to the nearest $10.</div>')
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
<div class="card"><div class="k">Federal estate tax room, 2045</div><div class="v">{usd(E45['room_single_base'])}</div><p>Other assets one person could leave tax-free after both homes. Scenario: see the tax page.</p></div>
</div>
{tbl("Inheritance in 2045, house prices rising 4% a year, result ten years later", ["Option", "Wealth after 10 years", "In today's dollars", "Behind the best by", "Cash in the first year", "Property A tax, first year"], rows)}
{LEGEND}
<section><h2>Five facts that could change the answer</h2>
<p>These are not known from the records supplied. Each one is on the <a href="review.html">Flagged for Review</a> page.</p>
<ol>
<li><strong>Who holds title to Property B today.</strong> If it passes in the same estate, its tax resets as well: from about {usd(BR45['tax_keep'])} to {usd(BR45['tax_reset'])} a year in 2045.</li>
<li><strong>Which home is the parents' principal residence.</strong> Only that home can carry the Proposition 19 exclusion, and only if a child moves in within a year.</li>
<li><strong>Whether the trust is revocable.</strong> The tax-free sale depends on the home being part of the taxable estate at death.</li>
<li><strong>How much cash and securities are in the estate.</strong> Federal estate tax starts above the exclusion; the two homes use part of it.</li>
<li><strong>Insurance premiums.</strong> No official figure or quote could be confirmed. The ranking does not change at three times the owner's guess.</li>
</ol></section>
<section><h2>Where to look</h2><div class="cards">
<div class="card"><div class="k">Start here</div><p><a href="executive-summary.html">Executive summary</a>: every important number with its source.</p></div>
<div class="card"><div class="k">The reasoning</div><p><a href="decision.html">Decision analysis</a>: results for 2040, 2045 and 2050, break-even points and all assumptions.</p></div>
<div class="card"><div class="k">The numbers</div><p><a href="projections.html">Year-by-year projections</a> to 2060 for value, assessed value, tax and running costs.</p></div>
<div class="card"><div class="k">The rules</div><p><a href="taxes.html">Tax, thresholds and law watch</a>, and the <a href="inheritance.html">inheritance steps</a> with deadlines.</p></div>
<div class="card"><div class="k">What is not settled</div><p><a href="review.html">Flagged for Review</a> and the <a href="audit.html">independent verification</a> of the earlier edition.</p></div>
<div class="card"><div class="k">Second opinion</div><p><a href="plan/index.html">Independent cross-check</a>: a separate model by another session, built only from official figures and break-evens. It reaches the same default.</p></div>
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
 (["Property B, if in the same estate", f"tax rises from {usd(BR45['tax_keep'])} to {usd(BR45['tax_reset'])} in 2045", "In a multi-unit building only the unit that was the parent's home and becomes the child's home can be excluded."], "C", S("boe_lta26026", "cityb_rate", asm=True)),
 (["Federal estate tax", "$15,000,000 per person in 2026; $15,480,000 in 2027", "A married couple can use two exclusions, but only if the first estate files Form 706 on time to elect it. Tax above the exclusion is 40%."], "V", S("irs_estate", "irs_2027", "irs_i706")),
 (["Room for cash under the exclusion", f"{usd(E45['room_single_base'])} in 2045 for one person", f"Scenario exclusion {usd(E45['exclusion'])} less both homes at {usd(E45['homes_base'])}. The cash amount itself was not supplied."], "C", S("irs_estate", "irs_rp2532", asm=True, flag=True)),
 (["California and local death taxes", "None", "No state estate or inheritance tax return since 2005. Cities and counties are barred from imposing one."], "V", S("sco_estate", "rtc13301")),
 (["Insurance", BLANK, "No official premium figure or insurer quote was confirmed for either property. The owner's guesses are used as placeholders; tripling them does not change the ranking."], "U", S("cdi_compare", flag=True)),
 (["Law under discussion", "The initiative to repeal the 2021 inheritance rules failed for lack of signatures", f"It would have restored the pre-2021 exclusion. If a later measure did so, Property A's 2045 tax would be {usd(LAW['tax_restored'])}. Selling would still come out ahead."], "V", S("sos_memo", "lao_250017", "sos_measures")),
 (["Deadlines after a death", "60 days, 150 days, 9 months, 1 year, 3 years", "Trustee notice; change in ownership statement; Form 706; homeowners' exemption; exclusion claim."], "V", S("prob16061_7", "rtc480", "irs_i706", "boe_prop19")),
]
body = f"""{tbl("Important details", ["Topic", "Finding", "What it means"], rows)}{LEGEND}
<section><h2>The plan in order</h2><ol>
<li><strong>Now.</strong> Confirm the trust is revocable and holds title; confirm who owns Property B; confirm which home carries the parents' homeowners' exemption. Do not move either property into an LLC.</li>
<li><strong>At the inheritance.</strong> Get a date-of-death appraisal. File the change in ownership statement within 150 days. File Form 706 within nine months if the estate is near the exclusion or a spouse survives.</li>
<li><strong>Decide within the first year.</strong> Sell, unless living in the home is worth about {usd(B45['live_cost_month_today'])} a month in today's dollars to the family. If moving in, occupy within one year and file both claims.</li>
<li><strong>Reinvest.</strong> A stock index fund has the higher expected result. Treasuries at today's yield finish ahead of renting when house prices grow 4% a year or less. A mix sits between the two.</li>
<li><strong>Keep Property B.</strong> Its low assessed value and steady rent make it the better property to hold, provided it is not reassessed in the same estate.</li>
</ol></section>{PRIV}"""
PAGES["executive-summary.html"] = page("executive-summary.html", "Executive summary", "Executive summary", "What matters, in one table",
                                       "Each row states a finding, the number behind it, and the official source.", body)

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
sens = [([x["case"], N(x["sell_stock"]), N(x["sell_treasury"]), N(x["rent"]), N(x["live"]), x["winner"]], "C",
         S("lao_250017" if "25-0017" in x["case"] else ("cdi_compare" if "Insurance" in x["case"] else "hud_fmr"), asm=True)) for x in M["sens"]]
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
<li><strong>Concentration.</strong> Keeping the home leaves most of the family's wealth in two houses in one region. Selling spreads it.</li>
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

# ------------------------------------------------------------------------------------------------ property A
hist = [("2015", "1.998%", "1.998%"), ("2016", "1.525%", "1.525%"), ("2017 to 2020", "2.000% each year", "2.000% each year"),
        ("2021", "1.036%", "1.036%"), ("2022 to 2026", "2.000% each year", "2.000% each year")]
rows = [
 (["Market value, November 2026", N(M["inputs"]["a_value"]), "Owner's estimate. An appraisal at the date of death sets the tax basis."], "O", S("irs_basis")),
 (["Assessed value, 2026", "about " + usd(M["inputs"]["a_av_2026"]), "Generalised to the nearest $10,000 for privacy."], "O", S("boe_lta26002")),
 (["Tax bill, 2025", "about " + usd(M["inputs"]["a_bill_2025"]), "Generalised to the nearest $100. The 2026 bill was not supplied."], "O", S("cnty_a_rates", flag=True)),
 (["Tax rate for the property's tax rate area", BLANK, "County A's rates run from 1.126% to 1.241%. The bill's tax rate area is needed. The model uses 1.18%."], "U", S("cnty_a_rates", flag=True)),
 (["Water", "$1,500 a year", "Midpoint of the owner's $100 to $150 a month."], "O", S("irs_p527")),
 (["Electricity", "&minus;$180 a year", "Solar. The owner reports a credit of $10 to $20 a month. The older solar tariffs last 20 years from connection; the connection date was not supplied."], "O", S("cpuc_nem", flag=True)),
 (["Home insurance premium", BLANK, "The owner's guess is $1,500 a year. No official figure or quote confirms it. The state's survey tool gives sample premiums, not quotes."], "U", S("cdi_compare", flag=True)),
 (["Maintenance", N(NOW_A["maintenance"]), "1.0% of an assumed building value. The owner says this home costs less to maintain than Property B."], "A", S("irs_p527", asm=True)),
 (["Total running cost, 2026", N(NOW_A["total_cost"]), "Property tax, the insurance guess, water, electricity credit and maintenance."], "C", S("boe_lta26002", asm=True)),
]
hrows = [([y, ("n", f), ("n", o), "Matches"], "V", S("boe_lta26002")) for y, f, o in hist]
p19 = [([str(y), N(AFTER[y]["fmv"]), N(AFTER[y]["base"]), N(AFTER[y]["amount"]), N(AFTER[y]["live"]), N(AFTER[y]["rent"]), N(AFTER[y]["saving"])], "C",
        S("rtc63_2", "boe_lta25009", asm=True)) for y in (2040, 2045, 2050)]
body = f"""
<section><h2>What is known</h2>{tbl("Property A: inputs and current running cost", ["Item", "Value", "Note"], rows)}{LEGEND}</section>
<section><h2>Assessment history checked against the state factors</h2>
<p>The owner's assessed values for 2014 to 2026 were compared, year by year, with the inflation factors the Board of Equalization publishes. Every year matches to within one dollar.
That means no new construction and no reassessment is hidden in the record. Dollar values are not shown here because roll values identify a parcel.</p>
{tbl("Year-over-year change in assessed value", ["Year", "State factor", "Owner's record", "Result"], hrows)}
<p>Two irregularities in the owner's tax-bill record are on the Flagged for Review page: in two places the same tax amount is entered for consecutive years although the assessed value rose 2%.</p></section>
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
 (["Assessed value, 2025", "about " + usd(M["inputs"]["b_av_2025"]), "Generalised to the nearest $10,000. The 2026 value was not supplied."], "O", S("boe_lta26002", flag=True)),
 (["Tax bill, 2025", "about " + usd(M["inputs"]["b_bill_2025"]), "Generalised to the nearest $100."], "O", S("cityb_rate")),
 (["City B tax rate, fiscal year 2025-26", P(M["verified"]["rate_b_2025"], 5), "Applied to assessed value."], "V", S("cityb_res447")),
 (["City B tax rate, fiscal year 2026-27", P(M["verified"]["rate_b_2026"], 5), "Current year. Used for every projection."], "V", S("cityb_rate")),
 (["Fixed charges on the bill", "about " + usd(M["fixed"]["b"]), "The bill is about 80% more than rate times assessed value. The difference is fixed charges; the line items were not supplied."], "C", S("cityb_rate", flag=True)),
 (["Rent, two units", "$7,150 a month", "The third unit is available to the family at no loss of rent."], "O", S("cityb_rent")),
 (["Allowed rent increase, March 2026 to February 2027", ("n", "1.6%"), "For sitting tenants in covered units: 60% of the regional price index. A new tenancy may start at any rent."], "V", S("cityb_rent")),
 (["Rent Board fee", "about $60 a unit a year", "Charged on family-occupied units too unless an exemption is filed."], "V", S("cityb_rentfee")),
 (["Water, whole building", "$4,380 a year", "Midpoint of the owner's $330 to $400 a month."], "O", S("irs_p527")),
 (["Electricity", "$600 a year", "Midpoint of the owner's $30 to $70 a month."], "O", S("irs_p527")),
 (["Landlord insurance premium", BLANK, "The owner's guess is $1,500 a year. A multi-unit rental needs a landlord policy; no official figure or quote confirms the price."], "U", S("cdi_compare", flag=True)),
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
body = f"""
<section><h2>What is known</h2>{tbl("Property B: inputs and current income", ["Item", "Value", "Note"], rows)}{LEGEND}
<p>The owner's assessed values for 2016 to 2025 follow the state factors in every year but one, where the rise was slightly below the factor. The year is reported to the owner privately.
One year's tax bill rose about 18% and another fell about 6% while the assessed value moved 2% and 1%. Fixed charges, not value, explain moves of that kind; the bills' line items would confirm it.</p></section>
<section><h2>If Property B passes in the same estate</h2>
<p>The records supplied do not say who holds title. If the parents do, the building changes ownership at the same death and is reassessed. In a multi-unit building the family-home exclusion covers only the unit that was the parent's principal residence and becomes the child's.
The table shows the building reassessed in full. If the current owner is already the heir, none of this applies.</p>
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
 (["Rate above the exclusion", ("n", "40%"), "The published credit of $5,945,800 on $15,000,000 corresponds to a 40% top rate. The rate table itself was not opened."], "V", S("irs_i706", flag=True)),
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
 (["Proposition 42, November 2026", "Voted on 3 November 2026. Result not certified.", "Would bar new state taxes on personal property, including financial assets, and certain retroactive taxes.", BLANK], "U", S("sos_measures", flag=True)),
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
<p>If Property B is already owned by the heir, it is not in the estate and the room is larger by its value.</p></section>
<section><h2>Law changes under discussion</h2>{tbl("Law watch", ["Item", "Status on 10 November 2026", "What it would change", "Effect on this decision"], watch)}</section>{PRIV}"""
PAGES["taxes.html"] = page("taxes.html", "Tax, thresholds, law watch", "Tax and law", "Rules, thresholds and what may change",
                           "Federal, state and local. Each rule was read on the official publisher's site.", body)

# ------------------------------------------------------------------------------------------------ inheritance
steps = [
 (["1", "Now", "Confirm the trust is revocable and that the deed to each property names the trust.", "[GRANTOR]", "The basis resets only for property in the taxable estate."], "V", S("irs_rr2023_2")),
 (["2", "Now", "Establish who holds title to Property B and which home carries the parents' homeowners' exemption.", "[GRANTOR], [BENEFICIARY]", "Decides which property is reassessed and which can be excluded."], "V", S("boe_lta26026", flag=True)),
 (["3", "Now", "Keep both properties out of any LLC. If there are several children, let the trustee distribute unequally.", "[GRANTOR]", "An LLC ends the exclusion. A swap between siblings is reassessed."], "V", S("boe_lta26026")),
 (["4", "Now", "If married, plan for the first death: Form 706 must be filed to keep the first spouse's unused exclusion.", "[GRANTOR]", "Without the election the second exclusion is lost."], "V", S("irs_estate", "irs_i706")),
 (["5", "Day of death", "The trust becomes irrevocable. For property tax the date of death is the date of change in ownership.", "[SUCCESSOR_TRUSTEE]", "All deadlines below run from this date."], "V", S("boe_prop19")),
 (["6", "Within 60 days", "Send the trustee's notification to every beneficiary and heir.", "[SUCCESSOR_TRUSTEE]", "Required when a revocable trust becomes irrevocable."], "V", S("prob16061_7")),
 (["7", "Promptly", "Order a written appraisal of each property as of the date of death.", "[SUCCESSOR_TRUSTEE]", "Sets the tax basis and the value used for reassessment."], "V", S("irs_basis")),
 (["8", "Within 150 days", "File the change in ownership statement with the assessor of each county.", "[SUCCESSOR_TRUSTEE]", "A penalty follows if a written request goes unanswered for 90 days."], "V", S("rtc480")),
 (["9", "Within 9 months", "File Form 706 if the estate exceeds the exclusion, or to elect the unused exclusion for a surviving spouse. Pay any tax.", "[SUCCESSOR_TRUSTEE]", "Form 4768 extends the filing date by six months."], "V", S("irs_i706")),
 (["10", "Decide early", "Choose: sell, rent or move in. A sale close to the date of death has almost no gain.", "[BENEFICIARY]", "Growth after the death is taxable when sold."], "V", S("irs_basis")),
 (["11", "If moving in: within 1 year", "Occupy the home as the principal residence and file the homeowners' exemption claim.", "[BENEFICIARY]", "Miss it and the exclusion applies only from the year of filing."], "V", S("boe_prop19", "rtc63_2")),
 (["12", "If moving in: within 3 years", "File the parent-child exclusion claim, and in any case before a sale to a third party.", "[BENEFICIARY]", "Or within six months of a supplemental assessment notice."], "V", S("boe_prop19", "rtc63_2")),
 (["13", "After the assessor acts", "Expect a supplemental tax bill for the reassessed value. Late instalments carry a 10% penalty.", "[BENEFICIARY]", "Budget for it: the first bills arrive months later."], "V", S("cityb_rate", "cnty_a_rates")),
 (["14", "On distribution", "Record the deed from the trust to the heir. No transfer tax is due on a transfer by reason of death.", "[SUCCESSOR_TRUSTEE]", "State the exemption on the deed."], "V", S("rtc11930")),
 (["15", "If selling", "Sell, pay the 0.11% county transfer tax, and report the sale with the date-of-death value as basis.", "[BENEFICIARY]", "Reported on Schedule D and Form 8949."], "V", S("rtc11911", "irs_basis")),
 (["16", "If renting", "Start depreciation from the date-of-death value of the building. Keep the land value separate.", "[BENEFICIARY]", "27.5 years; taxed back at up to 25% on sale."], "V", S("irs_p527", "irs_tc409")),
 (["17", "If living there, later", "Stay two years before any sale to keep the home-sale exclusion. Tell the assessor on moving out.", "[BENEFICIARY]", "Moving out ends the property tax exclusion."], "V", S("irs_tc701", "boe_prop19")),
]
body = f"""{tbl("From today to the years after the inheritance", ["Step", "When", "What to do", "Who", "Why it matters"], steps)}{LEGEND}
<section><h2>What a trust does and does not do</h2><ul>
<li>A revocable trust avoids probate and keeps the property in the taxable estate, which is what resets the basis.</li>
<li>A trust does not prevent reassessment. The assessor looks through the trust to the people who benefit.</li>
<li>A trust does not shelter anything from the federal estate tax. The exclusion does that.</li>
</ul>
<p>The official names and numbers of the county forms, and the trust's own income tax filing during administration, were not verified in this session; they are on the Flagged for Review page.</p></section>{PRIV}"""
PAGES["inheritance.html"] = page("inheritance.html", "Inheritance steps", "Inheritance by trust", "Step by step, with deadlines",
                                 "What to do now, at the death, and in the three years that follow.", body)

# ------------------------------------------------------------------------------------------------ flagged for review
fl = [
 ("FL-01", "Who holds title to Property B", "Not stated in the records. Decides whether the building is reassessed at the same death and whether it is in the estate.", "Current deed or trust schedule", "boe_lta26026"),
 ("FL-02", "Which home is the parents' principal residence", "Only that home can be excluded, and only one unit of a multi-unit building.", "Homeowners' exemption shown on the tax bill", "boe_prop19"),
 ("FL-03", "Whether the trust is revocable", "The basis reset depends on it.", "The trust document", "irs_rr2023_2"),
 ("FL-04", "Cash, securities, earlier taxable gifts, marital status", "The owner says the cash may exceed the exclusion. No amount was supplied, so the room is shown without it.", "A list of assets and gift tax returns", "irs_estate"),
 ("FL-05", "Home insurance premium, Property A", "The owner's guess of $1,500 a year is unconfirmed. The state survey tool is interactive and gives samples, not quotes.", "Two written quotes at replacement cost", "cdi_compare"),
 ("FL-06", "Landlord insurance premium, Property B", "The owner's guess of $1,500 a year is unconfirmed and is likely low for a multi-unit rental.", "Two written landlord-policy quotes", "cdi_compare"),
 ("FL-07", "Market rent for Property A", "The $6,500 a month is an assumption. The federal rent table for the area was not opened.", "A written rental analysis; the federal table", "hud_fmr"),
 ("FL-08", "Tax rate area of Property A", "The rate is printed on the bill. Only the county-wide range was verified.", "The bill's tax rate area and rate", "cnty_a_rates"),
 ("FL-09", "Fixed charges on both tax bills", "Property B's bill is about 80% above rate times value. One year's bill rose about 18% and another fell about 6% with no matching change in value.", "The line items on each bill", "cityb_rate"),
 ("FL-10", "Duplicate tax amounts in Property A's record", "Two pairs of consecutive years carry the same tax amount although the assessed value rose 2%. Probably a copying error.", "The bills for those years", "boe_lta26002"),
 ("FL-11", "One year of Property B's assessed value", "It rose slightly less than the state factor. The year is reported to the owner privately.", "The assessor's roll history", "boe_lta26002"),
 ("FL-12", "2026 figures", "No 2026 tax bill for Property A and no 2026 assessed value or bill for Property B were supplied.", "The 2026-27 bills", "boe_lta26002"),
 ("FL-13", "Solar connection date and tariff", "The 20-year period decides when the electricity credit ends.", "The utility's interconnection letter", "cpuc_nem"),
 ("FL-14", "Whether the rent ordinance covers Property B", "Depends on the date of first occupancy and the legal unit count. No parcel lookup was performed.", "Certificate of occupancy; Rent Board record", "cityb_rent"),
 ("FL-15", "Result of the 3 November 2026 measures", "Results are not certified. Proposition 42 bears on future state taxes on financial assets.", "The certified statement of vote", "sos_measures"),
 ("FL-16", "The 40% estate tax rate", "Derived from the published credit amount. The rate table was not opened.", "Table A in the Form 706 instructions", "irs_i706"),
 ("FL-17", "State tax on Treasury interest", "Assumed exempt. Not re-verified in this session.", "Franchise Tax Board guidance", "ftb_rates"),
 ("FL-18", "Long-run stock return", "7.0% is an assumption. Only a 12-month official figure was read.", "The fund's long-run return table", "tsp_returns"),
 ("FL-19", "City B vacancy tax", "Reported struck down on appeal in September 2026 by secondary sources only.", "The Court of Appeal opinion", "cityb_rate"),
 ("FL-20", "Pending bills on the basis reset", "None was verified. Treated as hypothetical.", "A search of current federal bills", "irs_basis"),
 ("FL-21", "County form names and the trust's tax filing", "The steps cite the statutes. Form numbers and the trust's income tax return were not verified.", "The assessor's forms page; a tax preparer", "rtc480"),
 ("FL-22", "Building share of value, bedrooms, condition", "Drive depreciation and maintenance. Assumed.", "The assessor's land and improvement split; an inspection", "irs_p527"),
 ("FL-23", "Sources read as excerpts", "Twelve sources were read as excerpts served from the official domain, not as whole documents. They are marked in the source library.", "Open each link", "irs_i706"),
 ("FL-24", "Privacy of the repository's history", "Earlier commits in this public repository contain exact figures and location details. This edition cannot remove them.", "The owner's decision on rewriting history or making the repository private", "irs_basis"),
 ("FL-25", "Jurisdictions visible through source links", "The pages name County A and City B, but the official local links identify them to anyone who opens one.", "The owner's decision on whether to drop local sources", "cityb_rate"),
]
rows = [([i, item, why, BLANK, fix], "U", S(src)) for i, item, why, fix, src in fl]
body = f"""<div class="note"><strong>Nothing on this page blocks the plan.</strong> These are the items that could not be confirmed from an official source, or that only the owner can settle.
Each value is left blank rather than estimated. The list is ordered by how much each item could change the answer.</div>
{tbl("Flagged for Review", ["No.", "Item", "Why it is flagged", "Value", "What settles it"], rows)}{LEGEND}{PRIV}"""
PAGES["review.html"] = page("review.html", "Flagged for review", "Flagged for review", "Unverified, unknown or irregular",
                            "Twenty-five open items with the official page that bears on each.", body)

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
 ("C-12", "Roll values in public files", "Assessment histories were published to the nearest $10, and one bill to the dollar.", "Generalised to the nearest $10,000 and $100. Year-over-year changes are shown as percentages.", "boe_lta26002"),
]
rows = [([i, item, old, new], "V", S(src)) for i, item, old, new, src in corr]
repo = [
 ("R-01", "Published pages", "Eleven pages are generated from one model and one source ledger. A stale page fails the build.", "boe_lta26002"),
 ("R-02", "Retired pages and data files", "Paths used by earlier editions hold withdrawal notices with no figures. The build fails if any other tracked file appears.", "irs_basis"),
 ("R-03", "Source ledger", "Each source now records how it was checked: opened, read as an official excerpt, or carried forward from the earlier edition.", "irs_estate"),
 ("R-04", "Checks", "Every table row must link to an official publisher. Dollar amounts must be multiples of $10. City names, ZIP codes, parcel numbers and e-mail addresses fail the build.", "rtc13301"),
 ("R-05", "Publishing", "The site is served from the main branch. Both publishing paths carry the same sanitised files. Earlier sessions report that the setting itself could not be changed with the available permissions.", "sos_measures"),
 ("R-06", "Repository history", "Earlier commits contain exact figures and location details. Not rewritten. Needs the owner's decision.", "irs_basis"),
 ("R-07", "Open pull requests from other sessions", "Left untouched. They contain earlier editions and are not part of this site.", "irs_basis"),
]
rrows = [([i, area, finding], "V", S(src)) for i, area, finding, src in repo]
body = f"""
<section><h2>What this page is</h2>
<p>A second session re-checked the edition published earlier the same day, line by line, against the official sources. Twelve items were corrected. The largest effects came from C-04, C-05 and C-06.
The earlier edition's source work was sound: its quotations matched the official pages wherever they were re-opened.</p>
{tbl("Corrections to the earlier edition", ["No.", "Item", "Earlier edition", "This edition"], rows)}{LEGEND}</section>
<section><h2>Repository review</h2>{tbl("State of the repository", ["No.", "Area", "Finding"], rrows)}</section>
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
{tbl("Source library", ["Id", "Publisher", "Document", "What it supports", "How it was checked on 10 November 2026"], rows)}{LEGEND}{PRIV}"""
PAGES["sources.html"] = page("sources.html", "Source library", "Source library", "Every source, and how it was checked",
                             "Open any link to check the figure yourself.", body)

for name, text in PAGES.items():
    (ROOT / name).write_text(text, encoding="utf-8")

# Plain-text executive summary kept in the repository
(ROOT / "EXECUTIVE_SUMMARY.md").write_text(f"""# Executive summary

Reviewed 10 November 2026. Anonymised: Property A (single-family home, County A), Property B (small multi-unit building, City B).
Dollar figures are rounded to the nearest $10. Planning analysis, not legal, tax or investment advice.

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
- Federal estate tax: $15,000,000 per person in 2026 and $15,480,000 in 2027; California has none.
- If Property B is in the same estate its tax resets too: ${BR45['tax_keep']:,} to ${BR45['tax_reset']:,} a year in 2045.
- Insurance premiums are unverified and left blank; tripling the owner's guess does not change the ranking.

Site: index.html. Open items: review.html. Sources: sources.html.
""", encoding="utf-8")
print(f"built {len(PAGES)} pages")
