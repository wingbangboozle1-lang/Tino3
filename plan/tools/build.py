#!/usr/bin/env python3
"""Render the cross-check edition (static HTML, no scripts) from model.py and sources.py.

Run:  python plan/tools/build.py [output_dir]     (default: plan/)
All links are relative, so the edition can be moved to any directory.
"""
from __future__ import annotations
import html, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import model as M                      # noqa: E402
from sources import SOURCES            # noqa: E402

OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE.parent
CHECKED = "10 November 2026"

NAV = [("index.html", "Overview"), ("summary.html", "Executive summary"), ("properties.html", "Properties and costs"),
       ("projections.html", "Projections 2026-2050"), ("decision.html", "Decision analysis"),
       ("taxes.html", "Taxes and thresholds"), ("steps.html", "Inheritance steps"), ("laws.html", "Law watch"),
       ("flagged.html", "Flagged for Review"), ("sources.html", "Sources")]

e = html.escape


def usd(v):
    v = int(v)
    return ("&minus;$" if v < 0 else "$") + f"{abs(v):,}"


def off(v):
    """Exact official amount (exempt from the $10 rounding check)."""
    return f'<span data-official="1">${int(v):,}</span>'


def pc(v, d=2):
    return f"{v:.{d}f}%"


BADGE = {"off": ("b-off", "official"), "own": ("b-own", "owner-provided"), "calc": ("b-calc", "calculated"),
         "flag": ("b-flag", "flagged"), "blank": ("b-blank", "blank: unverified")}


def b(kind):
    c, t = BADGE[kind]
    return f'<span class="badge {c}">{t}</span>'


def src(*ids):
    out = []
    for i in ids:
        pub, title, url, status, _ = SOURCES[i]
        mark = {"excerpt": " &dagger;", "lookup": " (look-up)", "repo": ""}.get(status, "")
        out.append(f'<a href="{e(url)}" rel="noopener">{e(pub)}: {e(title)}{mark}</a>')
    return "".join(out)


def R(*cells, s, flag=False, num=()):
    return dict(cells=cells, s=s, flag=flag, num=num)


def table(caption, headers, rows, num=()):
    h = "".join(f'<th scope="col">{x}</th>' for x in list(headers) + ["Official source"])
    body = []
    for r in rows:
        cls = ' class="flag"' if r["flag"] else ""
        nums = set(num) | set(r["num"])
        tds = "".join(f'<td class="n">{c}</td>' if k in nums else f"<td>{c}</td>" for k, c in enumerate(r["cells"]))
        body.append(f'<tr{cls}>{tds}<td class="src">{src(*r["s"])}</td></tr>')
    return (f'<div class="tw"><table><caption>{caption}</caption><thead><tr>{h}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def page(fname, title, lead, body):
    cur = ' aria-current="page"'
    nav = "".join(f'<a href="{h}"{cur if h == fname else ""}>{e(t)}</a>' for h, t in NAV)
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>{e(title)} | Inherited-home plan, cross-check edition</title>
<link rel="stylesheet" href="assets/style.css"></head>
<body><a class="skip" href="#main">Skip to content</a><div class="shell">
<aside class="side"><p class="brand">Inherited-home plan<small>Independent cross-check edition &middot; official inputs only</small></p>
<nav aria-label="Sections">{nav}</nav>
<p class="back">Main dashboard: <a href="../index.html">open the main edition</a></p></aside>
<main id="main"><p class="eyebrow">Checked {CHECKED} &middot; amounts rounded to $10 &middot; no personal data</p>
<h1>{title}</h1><p class="lead">{lead}</p>
{body}
<footer>Planning information, not legal, tax or investment advice. Property A and Property B are placeholders; no names, addresses, parcel numbers or postal codes are published. &dagger; = official text seen only as a search excerpt (flagged). Built by <a href="tools/build.py">tools/build.py</a> from <a href="tools/model.py">tools/model.py</a>; data in <a href="data/model.json">data/model.json</a>.</footer>
</main></div></body></html>
"""
    (OUT / fname).write_text(doc, encoding="utf-8")


# --------------------------------------------------------------------------------------
o = M.main()
t, rt, hp, asm = o["today"], o["rates"], o["hpi"], o["assumptions"]
D = {(d["T"], d["g"]): d for d in o["decisions"]}
GL, GB, GH = M.G_LOW, M.G_BASE, M.G_HIGH
d45, d40, d50 = D[(2045, GB)], D[(2040, GB)], D[(2050, GB)]
PA = {r["year"]: r for r in o["projection_a"]}
PB = {r["year"]: r for r in o["projection_b"]}
g_star = M.bisect(lambda g: M.wealth(2045, g, M.R10Y)[1] - M.wealth(2045, g, M.R10Y)[0], 0.0, 0.10)
G_STAR = pc(g_star * 100)
sell_wins = sum(1 for d in o["decisions"] if d["diff_pre"] < 0) + sum(1 for d in o["decisions"] if d["diff_post"] < 0)
N_CASES = 2 * len(o["decisions"])
SG = ("fred_hpi",)
SP19 = ("boe_p19", "boe_cap", "boe_guid")

# ------------------------------- recommendation (shared) -------------------------------
REC = f"""<div class="rec"><h2>Recommended plan</h2>
<ol class="steps">
<li><b>Now, while the owner is alive: change nothing about title.</b> Property passing at death gets a new income-tax basis equal to its value at the date of death, so the gain built up over the owner's lifetime is never taxed. The houses alone are {usd(t['room_ab'])} under the 2026 federal exclusion; California has no estate or inheritance tax.</li>
<li><b>Keep Property B.</b> Net rent is {pc(t['b_yield_keep'])} of its value today, or {pc(t['b_yield_full'])} if it is reassessed at inheritance. Even then, net rent plus the lowest house-price growth tested ({pc(t['b_yield_full'] + GL*100)} together) is above the {pc(asm['r10y']*100)} 10-year Treasury yield, and the third unit is the heir's home.</li>
<li><b>Property A, default: sell within the first year after inheritance and reinvest.</b> In that window the sale is almost free of capital-gains tax, and it removes a property-tax bill that jumps from {usd(d45['tax_keep'])} to between {usd(d45['tax_live'])} and {usd(d45['tax_full'])} a year (2045, base case). Before income tax, selling beats living in the house by {usd(-d45['diff_pre'])} over ten years.</li>
<li><b>Switch to &ldquo;keep and rent out&rdquo; only if</b> a written rent estimate at that time is above about {pc(d45['be_yield_vs_sell'])} of the house's value per year ({usd(d45['be_rent_vs_sell_2026'])} a month in today's dollars for 2045). No verified market rent exists today, so this cell is deliberately blank.</li>
<li><b>Switch to &ldquo;live in it&rdquo; only if</b> you expect the house to appreciate faster than about {G_STAR} a year, or your tax rate on interest income is above about {pc(d45['t_star'],0)} and the sale money would sit in taxable bonds. Then move in and file the Proposition 19 claim and homeowners' exemption within one year.</li>
<li><b>If still undecided nine months after the death, move in and file.</b> The exclusion cannot be claimed later, while the option to sell stays open.</li>
</ol>
<p class="small">The call is close: selling wins {sell_wins} of the {N_CASES} cases tested (three inheritance years, three appreciation rates, before and after tax). The numbers are on the <a href="decision.html">decision page</a>; everything that could not be verified is on the <a href="flagged.html">Flagged for Review page</a>.</p></div>"""

# ------------------------------------- index -------------------------------------------
kp = f"""<div class="kpis">
<div class="kpi"><span>Federal estate exclusion, 2026</span><b>{off(M.EXCL[2026])}</b><p>{off(M.EXCL[2027])} for 2027. California: no estate or inheritance tax.</p></div>
<div class="kpi"><span>Cash that could still pass tax-free</span><b>{usd(t['room_ab'])}</b><p>2026, one exclusion, both properties counted. {usd(t['room_a'])} if only Property A is in the estate.</p></div>
<div class="kpi"><span>Property A tax after inheritance</span><b>{usd(t['a_tax_live'])} &ndash; {usd(t['a_tax_full'])}</b><p>Per year at today's value: lived in / not lived in. The owner pays {usd(t['a_tax_keep'])}.</p></div>
<div class="kpi"><span>Property B net rent</span><b>{usd(t['b_net_keep'])}</b><p>Per year before maintenance and income tax. {usd(t['b_net_full'])} if reassessed at inheritance.</p></div>
<div class="kpi"><span>Rent needed to beat selling A</span><b>{pc(d45['be_yield_vs_sell'])} of value</b><p>{usd(d45['be_rent_vs_sell_2026'])} a month in today's dollars (2045 base case). Actual market rent: blank, unverified.</p></div>
<div class="kpi"><span>Return needed to beat living in A</span><b>{pc(d45['r_star'])}</b><p>After-tax yearly return on the sale money. 10-year Treasury on 9 Nov 2026: {pc(asm['r10y']*100)} before tax.</p></div>
</div>"""
cards = "".join(f'<a href="{h}"><b>{e(tt)}</b><span>{d}</span></a>' for h, tt, d in [
    ("summary.html", "Executive summary", "The answer, the numbers behind it and what would change it."),
    ("properties.html", "Properties and costs", "Inputs, tax-rate make-up, today's running costs."),
    ("projections.html", "Projections 2026-2050", "Year-by-year value, assessed value, tax, insurance, water, electricity, maintenance."),
    ("decision.html", "Decision analysis", "Live in, rent out, or sell and reinvest: ten-year comparison and break-evens."),
    ("taxes.html", "Taxes and thresholds", "Federal, state and local taxes, the tax-free threshold and the room left under it."),
    ("steps.html", "Inheritance steps", "What the successor trustee and the heir file, and by when."),
    ("laws.html", "Law watch", "Pending and recent changes and what each would do to the numbers."),
    ("flagged.html", "Flagged for Review", "Unverified values, assumptions, repository irregularities, differences from the main edition."),
    ("sources.html", "Sources", "Every official page used, what it supports, and whether it was read in full."),
])
idx_rows = [
    R("Federal estate-tax exclusion, deaths in 2026", off(M.EXCL[2026]), b("off"), s=("irs_estate",), num=(1,)),
    R("Federal estate-tax exclusion, deaths in 2027", off(M.EXCL[2027]), b("off"), s=("irs_2027",), num=(1,)),
    R("California estate or inheritance tax", "None", b("off"), s=("sco", "rtc_13301"), num=(1,)),
    R("Proposition 19 family-home amount (to 15 Feb 2027)", off(M.CAP_2025_27), b("off"), s=("boe_cap",), num=(1,)),
    R("Property A tax today (owner's assessed value)", usd(t["a_tax_keep"]), b("calc"), s=("coa_rates", "boe_infl"), num=(1,)),
    R("Property A tax if inherited now and lived in", usd(t["a_tax_live"]), b("calc"), s=SP19, num=(1,)),
    R("Property A tax if inherited now and not lived in", usd(t["a_tax_full"]), b("calc"), s=("boe_p19", "coa_rates"), num=(1,)),
    R("Property B rent, two units, per year", usd(t["b_rent"]), b("own"), s=("cityb_rentlearn",), num=(1,)),
    R("Property B tax today / if reassessed at market value", f"{usd(t['b_tax_keep'])} / {usd(t['b_tax_full'])}", b("calc"), s=("cityb_tax", "boe_guid"), num=(1,)),
    R("10-year Treasury yield, 9 Nov 2026", pc(asm["r10y"] * 100), b("off"), s=("treasury",), num=(1,)),
    R("California house-price growth, last 20 / 30 years", f"{pc(hp['y20'])} / {pc(hp['y30'])} a year", b("calc"), s=SG, num=(1,)),
]
page("index.html", "Overview",
     "A second, independent pass over the inheritance decision for two California homes: should the heir live in Property A, rent it out, or sell it and reinvest? This edition uses only figures read on official pages plus the owner's own figures, and solves for break-evens instead of assuming what it cannot verify.",
     f"""<div class="note"><b>How this relates to the main dashboard.</b> The <a href="../index.html">main edition</a> answers the same question with scenario assumptions (a 7% equity return, a 3% rent yield, a 33.3% tax rate). This cross-check replaces each of those with an official figure or a break-even, and reconciles the two on the <a href="flagged.html">Flagged for Review page</a>. Both reach the same default for Property A (sell in the first year) and both find the margin thin.</div>
{kp}{REC}
<h2>Headline numbers</h2>{table("Key figures and where they come from", ["Item", "Value", "Basis"], idx_rows)}
<h2>Sections</h2><div class="cards">{cards}</div>""")

# ------------------------------------- summary -----------------------------------------
sum_rows = [
    R("1. Estate tax on the two homes", f"None expected. Combined value {usd(M.A['market_2026'] + M.B['market_2026'])} against a {off(M.EXCL[2026])} exclusion.",
      f"{usd(t['room_ab'])} of cash and investments could be added in 2026 before any federal estate tax; above that the rate is 40%.", s=("irs_estate", "usc_2001")),
    R("2. State death taxes", "None.", "California may not impose an estate, inheritance or gift tax; changing that would need a statewide vote.", s=("sco", "rtc_13301")),
    R("3. Income tax on inheriting", "None on the inheritance itself.", "Basis resets to date-of-death value, so a sale soon after death has little or no taxable gain. Later rent, interest and gains are taxable.", s=("irs_basis", "ftb_inh")),
    R("4. Property A property tax", f"{usd(d45['tax_keep'])} becomes {usd(d45['tax_live'])} (lived in) or {usd(d45['tax_full'])} (not lived in) in 2045.",
      f"The owner's low assessed value does not pass on intact. Living there saves {usd(d45['prop19_saving'])} a year, not the whole difference.", s=SP19),
    R("5. Property B property tax", f"{usd(t['b_tax_keep'])} becomes {usd(t['b_tax_full'])} at today's value if B is in the estate.",
      f"Rented units cannot keep the old assessed value. Net rent falls from {usd(t['b_net_keep'])} to {usd(t['b_net_full'])} a year.", s=("boe_guid", "cityb_tax")),
    R("6. Sell A versus live in A", f"Before tax, selling is ahead by {usd(-d45['diff_pre'])} after ten years; taxed at the top federal rate, living in is ahead by {usd(d45['diff_post'])}.",
      f"Break-even: an after-tax return of {pc(d45['r_star'])} a year on the sale money, or a tax rate of about {pc(d45['t_star'],0)} on interest.", s=("treasury", "fred_hpi", "irs_2027")),
    R("7. Rent out A", f"Needs {usd(d45['be_rent_vs_live_2026'])} a month (today's dollars) to beat living in it and {usd(d45['be_rent_vs_sell_2026'])} to beat selling.",
      "Market rent is not verified, so the comparison is a threshold, not a forecast.", s=("boe_p19", "treasury", "hud_fmr"), flag=True),
    R("8. Running costs", f"Property A {usd(t['a_total'])} a year today; Property B nets {usd(t['b_net_keep'])} a year.",
      "Before maintenance, which the owner did not quantify and no official source prices.", s=("coa_rates", "cityb_tax", "fomc"), flag=True),
]
chg_rows = [
    R("A written rent estimate for Property A", f"Above {pc(d45['be_yield_vs_sell'])} of value a year", "Keep A as a rental instead of selling", s=("irs_414", "boe_p19")),
    R("Your view of house-price growth", f"Above about {G_STAR} a year", "Keep A (live in or rent) instead of selling", s=SG),
    R("Your tax rate on interest income", f"Above about {pc(d45['t_star'],0)}", "Living in A beats selling into taxable bonds", s=("irs_2027", "treasury")),
    R("Treasury yields at the time", f"Below about {pc(d45['r_star'])} after tax", "Living in A beats selling", s=("treasury",)),
    R("Cash and investments in the estate", f"Above {usd(t['room_ab'])} (2026, one exclusion)", "Federal estate tax at 40% on the excess; a married couple's unused exclusion can be carried over", s=("irs_estate", "usc_2001")),
    R("A change to the family-home rules", "Not pending: the 2026 repeal initiative failed", "Would let the heir keep the owner's assessed value; see Law watch", s=("sos_memo",)),
]
page("summary.html", "Executive summary",
     "Eight findings, one recommendation, and the six things that would change it. Every figure links to the official page it rests on.",
     f"""{table("Findings", ["Finding", "Number", "What it means"], sum_rows)}{REC}
<h2>What would change the recommendation</h2>{table("Switch points (2045 inheritance, base case)", ["If this", "Is", "Then"], chg_rows)}
<p class="small">Base case: house prices grow {pc(GB*100)} a year (midpoint of the 20-year and 30-year California figures), other costs grow 2% a year, and sale proceeds earn the 10-year Treasury yield. Low and high cases are on the decision page.</p>""")

# ------------------------------------ properties ---------------------------------------
in_rows = [
    R("Market value, November 2026", usd(M.A["market_2026"]), usd(M.B["market_2026"]), b("own"), "Owner estimate. No appraisal seen.", s=("irs_basis",), flag=True, num=(1, 2)),
    R("Assessed value used here", usd(M.A["assessed_2026"]) + " (2026)", usd(M.B["assessed_2025"]) + " (2025)", b("own"), "Rounded to $10,000 for privacy. Year-to-year changes in the owner's history match the state factors.", s=("boe_infl", "boe_infl26"), num=(1, 2)),
    R("Latest tax bill provided (2025)", usd(M.A["bill"]), usd(M.B["bill"]), b("own"), "Bills not seen. The 2026 bill for Property A was not provided.", s=("coa_rates", "cityb_tax"), flag=True, num=(1, 2)),
    R("Use", "Single-family home, owner-occupied, rooftop solar", "Three livable units: two rented, one free for an owner", b("own"), "", s=("boe_guid",)),
    R("Rent received", "None", f"{usd(M.B['rent_month'])} a month for two units", b("own"), "Leases not seen.", s=("cityb_rentlearn",), num=(1, 2)),
    R("Water", f"{usd(M.A['water_month'][0])} &ndash; {usd(M.A['water_month'][1])} a month", f"{usd(M.B['water_month'][0])} &ndash; {usd(M.B['water_month'][1])} a month (all three units)", b("own"), "No official rate was matched to either bill.", s=("cpuc_water",), flag=True, num=(1, 2)),
    R("Electricity", "About zero; solar credit of $10 &ndash; $20 a month", "$30 &ndash; $70 a month", b("own"), "Depends on the solar tariff staying in place (see Law watch).", s=("cpuc_nem",), num=(1, 2)),
    R("Insurance", usd(M.A["insurance"]) + " a year", usd(M.B["insurance"]) + " a year", b("own") + b("flag"), "Owner is unsure. No quote or official premium for either home was obtained; a rented building needs a landlord policy, not a homeowners policy.", s=("cdi_tool", "cdi_guide"), flag=True, num=(1, 2)),
    R("Maintenance", "", "", b("blank"), "No figure provided and no official source prices it. Left blank; not included in any total.", s=("irs_414",), flag=True),
]
rate_rows = [R(e(n), f"{v:.5f}", s=("coa_rates",), num=(1,)) for n, v in M.RATE_A_PARTS]
rate_rows.append(R("<b>Total used for Property A</b>", f"<b>{rt['a_pct']:.5f}</b>", s=("coa_rates",), num=(1,), flag=True))
bound_rows = [
    R("Low: only the 1% levy scales with value", "1.00000%", usd(t["a_tax_full_low"]), "Everything else on the bill treated as fixed charges.", s=("coa_rates",), num=(1, 2)),
    R("Used: rate-book composite", pc(rt["a_pct"], 5), usd(t["a_tax_full"]), f"Leaves {usd(rt['fixed_a'])} of the 2025 bill as fixed charges.", s=("coa_rates",), num=(1, 2), flag=True),
    R("High: the whole bill scales with value", pc(rt["a_high_pct"], 3), usd(t["a_tax_full_high"]), "2025 bill divided by assessed value.", s=("coa_rates",), num=(1, 2)),
]
cost_rows = [
    R("Property tax", usd(t["a_tax_keep"]), usd(t["b_tax_keep"]), b("calc"), s=("coa_rates", "cityb_tax"), num=(1, 2)),
    R("Insurance", usd(t["a_ins"]), usd(t["b_ins"]), b("own") + b("flag"), s=("cdi_tool",), num=(1, 2), flag=True),
    R("Water", usd(t["a_water"]), usd(t["b_water"]), b("own"), s=("cpuc_water",), num=(1, 2)),
    R("Electricity (negative = credit)", usd(t["a_elec"]), usd(t["b_elec"]), b("own"), s=("cpuc_nem",), num=(1, 2)),
    R("Maintenance", "", "", b("blank"), s=("irs_414",), num=(1, 2), flag=True),
    R("<b>Total running cost before maintenance</b>", f"<b>{usd(t['a_total'])}</b>", f"<b>{usd(t['b_tax_keep'] + t['b_ins'] + t['b_water'] + t['b_elec'])}</b>", b("calc"), s=("coa_rates", "cityb_tax"), num=(1, 2)),
    R("Rent received", usd(0), usd(t["b_rent"]), b("own"), s=("cityb_rentlearn",), num=(1, 2)),
    R("<b>Net per year before maintenance and income tax</b>", f"<b>{usd(-t['a_total'])}</b>", f"<b>{usd(t['b_net_keep'])}</b>", b("calc"), s=("irs_414",), num=(1, 2)),
]
bq_rows = [
    R("Tax rate published for fiscal year 2026-27", pc(rt["b_pct"], 8), b("off"), s=("cityb_tax",), num=(1,)),
    R("Rate x assessed value", usd(rt["b_advalorem"]), b("calc"), s=("cityb_tax",), num=(1,)),
    R("Bill the owner reported for 2025", usd(M.B["bill"]), b("own"), s=("cityb_tax",), num=(1,)),
    R("Difference: direct charges and special assessments, not itemised", usd(rt["fixed_b"]), b("flag"), s=("cityb_tax",), num=(1,), flag=True),
]
page("properties.html", "Properties and costs",
     "What the owner supplied, how the tax bills break down against the published rates, and what each home costs to run today. Owner figures are labelled; nothing here was taken from a parcel record.",
     f"""{table("Inputs", ["Item", "Property A", "Property B", "Basis", "Note"], in_rows)}
<h2>Running costs today (2026, per year)</h2>{table("Annual costs", ["Item", "Property A", "Property B", "Basis"], cost_rows)}
<h2>Property A: what the tax rate is made of</h2>
<p class="small">The county publishes one rate per levy and a different total for each tax rate area. The owner's tax rate area was not confirmed, so the composite below is the best match to the levies that serve the home's school, college and special districts, and it is flagged. Check it against the rate lines on the bill.</p>
{table("Rates per $100 of assessed value, fiscal year 2025-26", ["Levy", "Rate"], rate_rows)}
{table("Why it matters: Property A tax if reassessed at today's market value", ["Assumption", "Rate on value", "Tax per year", "Note"], bound_rows)}
<h2>Property B: the bill is larger than rate x value</h2>{table("Reconciling the reported bill", ["Line", "Amount", "Basis"], bq_rows)}
<p class="small">Almost half of the Property B bill is not explained by the published rate. The tax collector states that bills add direct charges and special assessments to the rate-based tax; the bill's own lines would confirm what they are. The model carries the difference forward as a fixed charge growing 2% a year.</p>""")

# ------------------------------------ projections --------------------------------------
pa1 = [R(y, usd(r["market_low"]), usd(r["market_base"]), usd(r["market_high"]), usd(r["assessed_keep"]), usd(r["tax_keep"]),
         usd(r["tax_live"]), usd(r["tax_full"]), s=("fred_hpi", "boe_infl", "boe_guid")) for y, r in PA.items()]
pa2 = [R(y, usd(r["tax_keep"]), usd(r["insurance"]), usd(r["water"]), usd(r["electricity"]), usd(r["total_keep"]), usd(r["maintenance_index"]),
         s=("coa_rates", "fomc", "cdi_tool")) for y, r in PA.items()]
pb1 = [R(y, usd(r["market_low"]), usd(r["market_base"]), usd(r["market_high"]), usd(r["assessed_keep"]), usd(r["tax_keep"]), usd(r["tax_full"]),
         s=("fred_hpi", "cityb_tax", "boe_guid")) for y, r in PB.items()]
pb2 = [R(y, usd(r["rent"]), usd(r["tax_keep"]), usd(r["insurance"]), usd(r["water"]), usd(r["electricity"]), usd(r["net_keep"]), usd(r["net_full"]),
         usd(r["maintenance_index"]), s=("cityb_rentlearn", "cityb_tax", "fomc")) for y, r in PB.items()]
basis_rows = [
    R("House value, low case", pc(GL * 100) + " a year", "California all-transactions index, 2006 Q2 to 2026 Q2", s=SG, num=(1,)),
    R("House value, high case", pc(GH * 100) + " a year", "Same index, 1996 Q2 to 2026 Q2", s=SG, num=(1,)),
    R("House value, base case", pc(GB * 100) + " a year", "Midpoint of the two. Statewide, not local: flagged.", s=SG, num=(1,), flag=True),
    R("Assessed value while ownership is unchanged", "2% a year", "Maximum yearly factor; applied in 9 of the last 12 years", s=("boe_infl",), num=(1,)),
    R("Proposition 19 amount", "Grows with house prices, stepped every two years", "Next official figure due February 2027", s=("boe_cap",), num=(1,)),
    R("Insurance, water, electricity, fixed charges", "2% a year", "Federal Reserve longer-run inflation goal. California premiums may rise faster: flagged.", s=("fomc",), num=(1,), flag=True),
    R("Rent from sitting tenants, Property B", pc(asm["rent_growth"] * 100, 1) + " a year", "Rent Board formula: 60% of inflation. Applies only if the building is covered: flagged.", s=("cityb_rentlearn", "cityb_laws"), num=(1,), flag=True),
    R("Maintenance", "", "No starting figure. The last column of each cost table shows what $1,000 of today's maintenance spending becomes.", s=("fomc",), flag=True),
]
page("projections.html", "Projections 2026-2050",
     "Year-by-year house value, assessed value, property tax, insurance, water, electricity and maintenance for both homes. These are scenarios built from official growth figures, not forecasts.",
     f"""{table("What drives each column", ["Column", "Growth used", "Where it comes from"], basis_rows)}
<h2>Property A</h2>
{table("Property A: value, assessed value and property tax", ["Year", "Value, low", "Value, base", "Value, high", "Assessed value, no transfer", "Tax, no transfer", "Tax if inherited that year, lived in", "Tax if inherited that year, not lived in"], pa1, num=range(1, 8))}
<p class="small">&ldquo;No transfer&rdquo; is the bill while the current owner keeps the home. The two right-hand columns show the first-year bill if the home passed to a child in that year under today's rules, at the base-case value.</p>
{table("Property A: running costs while the current owner keeps it", ["Year", "Property tax", "Insurance", "Water", "Electricity (credit)", "Total before maintenance", "Maintenance: what $1,000 today becomes"], pa2, num=range(1, 7))}
<h2>Property B</h2>
{table("Property B: value, assessed value and property tax", ["Year", "Value, low", "Value, base", "Value, high", "Assessed value, no transfer", "Tax, no transfer", "Tax if reassessed that year"], pb1, num=range(1, 7))}
{table("Property B: rent and running costs", ["Year", "Rent, two units", "Property tax, no transfer", "Insurance", "Water", "Electricity", "Net before maintenance", "Net if reassessed that year", "Maintenance: what $1,000 today becomes"], pb2, num=range(1, 9))}
<p class="small">Downloads: <a href="data/projection_a.csv">projection_a.csv</a>, <a href="data/projection_b.csv">projection_b.csv</a>.</p>""")

# ------------------------------------- decision ----------------------------------------
opt_rows = [
    R("Live in A", "Heir moves into A within a year; the third unit of B is rented out.", f"Tax on A: owner's value plus whatever exceeds it by more than the family-home amount. Homeowners' exemption of {off(M.HOE)}.", s=SP19 + ("boe_hoe",)),
    R("Rent out A", "Heir lives in B's third unit; A is let.", "A is reassessed at full market value. Rent is taxable; the building can be depreciated.", s=("boe_p19", "irs_414", "irs_p527")),
    R("Sell A and reinvest", "Heir lives in B's third unit; A is sold in the first year.", "Basis is date-of-death value, so little or no gain. County transfer tax of 55 cents per $500. Proceeds earn the 10-year Treasury yield.", s=("irs_basis", "rtc_11911", "treasury")),
]
y1_rows = [
    R("Value of Property A", usd(d45["value"]), usd(d45["value"]), usd(d45["value"]), s=SG, num=(1, 2, 3)),
    R("Property tax on A", usd(d45["tax_live"]), usd(d45["tax_full"]), usd(0), s=SP19 + ("coa_rates",), num=(1, 2, 3)),
    R("Insurance, water, electricity on A", usd(d45["cost_live"] - d45["tax_live"]), usd(d45["cost_rent"] - d45["tax_full"]) + " (insurance only; tenant pays utilities)", usd(0), s=("fomc", "cdi_tool"), num=(1, 2, 3), flag=True),
    R("Rent from B's third unit", usd(d45["unit3"]), usd(0), usd(0), s=("cityb_rentlearn",), num=(1, 2, 3), flag=True),
    R("Rent from A", usd(0), "blank: unverified", usd(0), s=("hud_fmr",), num=(1, 2, 3), flag=True),
    R("Interest on sale proceeds", usd(0), usd(0), usd(d45["interest"]), s=("treasury", "rtc_11911"), num=(1, 2, 3)),
    R("<b>Cash in the first year, before maintenance and income tax</b>", f"<b>{usd(d45['net_live'])}</b>", f"<b>rent &minus; {usd(d45['cost_rent'])}</b>", f"<b>{usd(d45['interest'])}</b>", s=("irs_414",), num=(1, 2, 3)),
]


def gname(g):
    return {GL: f"Low {pc(GL*100)}", GB: f"Base {pc(GB*100)}", GH: f"High {pc(GH*100)}"}[g]


w_rows = []
for T in M.T_YEARS:
    for g in (GL, GB, GH):
        d = D[(T, g)]
        win0 = "Live in" if d["diff_pre"] > 0 else "Sell"
        win1 = "Live in" if d["diff_post"] > 0 else "Sell"
        w_rows.append(R(T, gname(g), usd(d["value"]), usd(d["sell_pre"]), usd(d["live_pre"]), win0, usd(d["sell_post"]), usd(d["live_post"]), win1,
                        s=("treasury", "fred_hpi", "irs_2027"), num=(2, 3, 4, 6, 7)))
be_rows = []
for T in M.T_YEARS:
    for g in (GL, GB, GH):
        d = D[(T, g)]
        ts = pc(d["t_star"], 0) if d["t_star"] is not None else ("any rate: living in is already ahead" if d["diff_pre"] > 0 else "no rate up to 60%: selling stays ahead")
        be_rows.append(R(T, gname(g), pc(d["r_star"]), ts,
                         f"{usd(d['be_rent_vs_live_2026'])} ({pc(d['be_yield_vs_live'])})", f"{usd(d['be_rent_vs_sell_2026'])} ({pc(d['be_yield_vs_sell'])})",
                         usd(d["one_pct_selling_cost"]), s=("treasury", "boe_p19", "fred_hpi"), num=(2, 3, 4, 5, 6)))
bb_rows = [
    R("Net rent today, old assessed value", usd(t["b_net_keep"]), pc(t["b_yield_keep"]) + " of value", s=("cityb_tax", "cityb_rentlearn"), num=(1, 2)),
    R("Net rent if reassessed at inheritance", usd(t["b_net_full"]), pc(t["b_yield_full"]) + " of value", s=("boe_guid", "cityb_tax"), num=(1, 2)),
    R("Plus house-price growth, low to high case", "", f"{pc(GL*100)} to {pc(GH*100)} a year", s=SG, num=(1, 2)),
    R("Plus the third unit as the heir's home", usd(t["unit3_year"]) + " a year of rent not paid", "assumed equal to the average rented unit", s=("cityb_rentlearn",), num=(1, 2), flag=True),
    R("Alternative: sell B, hold 10-year Treasuries", usd(t["b_treasury_income"]) + " a year", pc(asm["r10y"] * 100) + ", no growth", s=("treasury", "rtc_11911"), num=(1, 2)),
]
page("decision.html", "Decision analysis",
     "Live in Property A, rent it out, or sell it and reinvest: the first year in dollars, the ten-year outcome, and the break-even points. Property B is kept in every option.",
     f"""{REC}
<h2>The three options</h2>{table("How each option is defined", ["Option", "What the heir does", "Tax treatment"], opt_rows)}
<h2>First year after a 2045 inheritance (base case)</h2>{table("Year-one cash view", ["Line", "Live in A", "Rent out A", "Sell A"], y1_rows)}
<p class="small">Living in A costs {usd(d45['cost_live'])} a year to carry and frees a unit worth {usd(d45['unit3'])} in rent. Selling turns the same asset into {usd(d45['interest'])} of interest. Renting it out wins only if the rent clears the thresholds below.</p>
<h2>Ten years on: sell versus live in</h2>
{table("Wealth from Property A ten years after inheritance", ["Inheritance year", "House-price growth", "Value at inheritance", "Sell, before tax", "Live in, before tax", "Ahead", "Sell, taxed at 37%", "Live in, taxed at 37%", "Ahead"], w_rows)}
<p class="small">&ldquo;Sell&rdquo; is the sale price less county transfer tax, compounding at the 10-year Treasury yield. &ldquo;Live in&rdquo; is the house value ten years later plus the third-unit rent less A's running costs, reinvested at the same yield. &ldquo;Taxed at 37%&rdquo; applies the top federal rate to interest and to the third-unit rent, as an upper bound; the heir's real bracket is unknown. Brokerage, maintenance and state income tax are not included.</p>
<h2>Break-even points</h2>
{table("What it takes for each option to win", ["Inheritance year", "House-price growth", "After-tax return at which selling equals living in", "Tax rate on interest above which living in wins", "Monthly rent for A to beat living in (today's dollars; % of value a year)", "Monthly rent for A to beat selling (today's dollars; % of value a year)", "Each 1% of selling cost"], be_rows)}
<p class="small">Read across: with base-case growth and a 2045 inheritance, selling wins unless the sale money would earn less than {pc(d45['r_star'])} a year after tax. Renting A out beats living in it once the rent passes {usd(d45['be_rent_vs_live_2026'])} a month in today's dollars, and beats selling once it passes {usd(d45['be_rent_vs_sell_2026'])}. Download: <a href="data/decisions.csv">decisions.csv</a>.</p>
<h2>Property B: keep it</h2>{table("Property B as an investment (today's figures)", ["Line", "Per year", "Return"], bb_rows)}
<p class="small">Even after reassessment, net rent plus the low-case growth rate ({pc(t['b_yield_full'] + GL*100)}) is above the Treasury yield, before counting the heir's own unit.</p>""")

# -------------------------------------- taxes ------------------------------------------
tx_rows = [
    R("Federal estate tax", f"Only on the part of the estate above {off(M.EXCL[2026])} (2026) or {off(M.EXCL[2027])} (2027), per person", "40% on the excess", "Not on the homes alone", s=("irs_estate", "irs_2027", "usc_2001")),
    R("California estate tax", "None for deaths on or after 1 January 2005", "0", "None", s=("sco",)),
    R("California inheritance or gift tax", "Prohibited by a voter initiative", "0", "None", s=("rtc_13301",)),
    R("Income tax on receiving the inheritance", "An inheritance is not income", "0", "None", s=("ftb_inh", "irs_basis")),
    R("Capital-gains tax on a later sale", "Gain above date-of-death value only", "Federal 0%, 15% or 20%; California taxes gains as ordinary income", "Near zero if sold soon after death", s=("irs_basis", "irs_409", "ftb_cg")),
    R("Home-sale exclusion", "Owned and lived in for 24 months of the last 5 years", f"Up to {off(250000)} of gain excluded ({off(500000)} joint)", "Available only if the heir lives in A", s=("irs_701",)),
    R("Net investment income tax", f"Income above {off(200000)} single or {off(250000)} joint", "3.8% on rent, interest and gains", "Likely relevant once rent and interest are added", s=("irs_559",)),
    R("Income tax on rent", "All rent is taxable; expenses and depreciation are deductible", "Federal up to 37%; California 9.3% from " + off(72724) + " of taxable income (single, 2025)", "Applies to Property B today and to A if rented", s=("irs_414", "irs_2027", "ftb_rates")),
    R("Property-tax reassessment", "Change in ownership at death", "Market value, unless the family-home exclusion applies", f"Property A: {usd(t['a_tax_keep'])} to {usd(t['a_tax_live'])} or {usd(t['a_tax_full'])} a year at today's value", s=SP19),
    R("County transfer tax on a sale", "Sale of real property", "55 cents per $500 of price", f"{usd(d45['transfer_tax'])} on a 2045 sale of A", s=("rtc_11911",)),
    R("Inherited retirement accounts", "Most non-spouse heirs", "Account emptied by the end of the 10th year; withdrawals are taxable", "Applies if the money includes retirement accounts", s=("irs_ira",)),
]
hr_rows = [R(h["year"], off(h["exclusion"]) if h["year"] in M.EXCL else usd(h["exclusion"]), usd(h["a"]), usd(h["b"]), usd(h["room_a"]), usd(h["room_ab"]), usd(h["room_ab_high"]), usd(h["room_ab_two"]),
             s=("irs_estate", "irs_2027") if h["year"] in M.EXCL else ("irs_2027", "fomc", "fred_hpi"), flag=h["year"] not in M.EXCL, num=range(1, 8)) for h in o["headroom"]]
cc_rows = [R(usd(c["cash"]), usd(c["gross"]), usd(c["over"]), usd(c["tax"]), usd(c["tax_two"]), s=("irs_estate", "usc_2001"), num=range(0, 5)) for c in o["cash_cases"]]
eh_rows = [R(y, off(v), s=("irs_2027",) if y == 2027 else ("irs_estate",), num=(1,)) for y, v in M.EXCL_HISTORY]
p19_rows = [
    R("Who qualifies", "A home that was the parent's principal residence and becomes the child's principal residence", s=("boe_p19",)),
    R("How much is protected", f"The parent's taxable value plus {off(M.CAP_2025_27)} (to 15 February 2027; adjusted every two years)", s=("boe_cap",)),
    R("If market value is higher than that", "The excess is added to the taxable value", s=("boe_guid",)),
    R("Property A today", f"Value {usd(M.A['market_2026'])}; protected {usd(M.r10(M.A['assessed_2026'] + M.CAP_2025_27))}; new taxable value {usd(t['a_taxable_live'])}; tax {usd(t['a_tax_live'])} instead of {usd(t['a_tax_full'])}", s=SP19),
    R("Deadlines", "Move in and file the homeowners' exemption within 1 year; file the claim within 3 years or before selling to a third party", s=("boe_p19", "boe_hoe")),
    R("If the heir later moves out", "The exclusion is removed and the date-of-death market value, with yearly factors, is enrolled", s=("boe_guid",)),
    R("Rented or multi-unit property", "Only the unit the parent lived in can qualify; the rest is reassessed", s=("boe_guid",)),
    R("Property B", f"No exclusion unless a unit was the parent's principal residence; tax {usd(t['b_tax_keep'])} to {usd(t['b_tax_full'])} at today's value", s=("boe_guid", "cityb_tax"), flag=True),
]
page("taxes.html", "Taxes and thresholds",
     "Which federal, state and local taxes touch the inheritance, where the tax-free threshold sits, and how much room is left under it now and later.",
     f"""{table("Taxes that can apply", ["Tax", "When it applies", "Rate or amount", "Effect here"], tx_rows)}
<h2>Room under the federal exclusion</h2>
<p class="small">The amount of money in the inheritance was not given. The table shows how much cash and investments could be added to the homes before federal estate tax starts. Years after 2027 index the exclusion at 2% a year, which is an assumption: Congress has reset the figure several times.</p>
{table("Headroom by year of death", ["Year", "Exclusion per person", "Property A", "Property B", "Room if only A is in the estate", "Room with A and B", "Room with A and B, high house prices", "Room with A and B, two exclusions (married, portability elected)"], hr_rows)}
{table("If death occurred in 2026: estate tax at different amounts of money", ["Cash and investments", "Estate with both homes", "Amount over one exclusion", "Tax at 40%", "Tax with two exclusions"], cc_rows)}
<p class="small">Arithmetic only: no debts, expenses, deductions or lifetime gifts are included. The annual gift exclusion is {off(19000)} per recipient for 2026 and {off(20000)} for 2027.</p>
<h2>How the family-home rule works</h2>{table("Proposition 19 in practice", ["Point", "Rule and effect"], p19_rows)}
<h2>Exclusion history</h2>{table("Federal filing threshold by year of death", ["Year", "Amount"], eh_rows)}""")

# -------------------------------------- steps ------------------------------------------
st_rows = [
    R("Now", "Owner and attorney", "Confirm both homes are titled in the revocable trust and that the trust names a successor trustee.", "A trust that becomes irrevocable at death triggers the notice duties below; assets in the taxable estate get the new basis.", s=("prob_16061", "irs_basis")),
    R("Now", "Owner", "Do not move the homes into an irrevocable trust or out of the estate without advice.", "Assets outside the gross estate may not get a new basis at death.", s=("irs_rr2023",), flag=True),
    R("Now", "Owner", "Keep the homeowners' exemption on Property A and records showing it is the principal residence.", "The family-home exclusion needs the home to be the parent's principal residence.", s=("boe_p19", "boe_hoe")),
    R("Now", "Owner", "Keep the solar interconnection date and tariff paperwork.", "Existing net-metering customers keep their tariff for a limited period; newer rules pay less for exports.", s=("cpuc_nem",), flag=True),
    R("At death", "Successor trustee", "Obtain death certificates; take over the trust; open an account in the trust's name.", "Administration starts.", s=("prob_16061",)),
    R("Within 60 days", "Successor trustee", "Serve the trustee notification on every beneficiary and heir.", "Required by statute when the trust becomes irrevocable.", s=("prob_16061",)),
    R("First months", "Successor trustee", "Get a written appraisal of each home as of the date of death.", "Sets the income-tax basis and the value for any estate return.", s=("irs_basis",)),
    R("First months", "Successor trustee", "Get a tax identification number for the trust or estate; file Form 1041 for any year with more than $600 of gross income.", "Rent received after death is the trust's income until distributed.", s=("irs_1041",)),
    R("Within 150 days", "Successor trustee or heir", "File the change in ownership statement with each county assessor.", "Late filing after a written request costs $100 or 10% of the tax, whichever is greater.", s=("rtc_480",)),
    R("Within 9 months", "Executor or trustee", "File Form 706 if the gross estate plus lifetime gifts is above the exclusion, or to pass a spouse's unused exclusion on.", "A six-month extension is available.", s=("irs_estate", "irs_i706"), flag=True),
    R("Within 1 year", "Heir, if living in A", "Move in; file the homeowners' exemption and the parent-child exclusion claim.", f"Worth {usd(d45['prop19_saving'])} a year in 2045; cannot be claimed later.", s=("boe_p19", "boe_hoe", "boe_forms")),
    R("Within 1 year", "Heir, if selling A", "Sell while value is close to the date-of-death appraisal.", "Little or no capital gain; inherited property counts as long-term.", s=("irs_basis", "irs_409")),
    R("On sale", "Seller", "Pay county transfer tax at closing.", "55 cents per $500 of price.", s=("rtc_11911",)),
    R("After reassessment", "Owner of record", "Expect supplemental tax bills; pay regular installments by 10 December and 10 April.", "10% penalty if late.", s=("coa_rates", "cityb_tax")),
    R("Ongoing, Property B", "Heir as landlord", "Existing tenancies continue; register in the housing inventory and hold a rent increase licence before raising rent.", "Annual increase limited to 1.6% through February 2027 if the building is covered.", s=("cityb_rentlearn", "cityb_rent", "cityb_laws")),
    R("Ongoing", "Heir", "Replace the insurance on each home with a policy in the new owner's name; use a landlord policy for a rented building.", "Compare premiums with the state's survey tool.", s=("cdi_guide", "cdi_tool")),
    R("Years 1 to 10", "Heir", "Empty any inherited retirement account by the end of the 10th year.", "Withdrawals are taxable income.", s=("irs_ira",)),
    R("After 2 years in A", "Heir, if living in A", "The home-sale exclusion becomes available on gain since the date of death.", f"Up to {off(250000)} ({off(500000)} joint).", s=("irs_701",)),
]
page("steps.html", "Inheritance steps",
     "What happens, in order, when a home held in a revocable trust passes to a child in California: who acts, by when, and what it protects. Placeholders stand in for every person.",
     f"""{table("Step by step", ["When", "Who", "Action", "Why it matters"], st_rows)}
<p class="small">[OWNER] = the parent who holds the homes in trust. [SUCCESSOR_TRUSTEE] = the person the trust names to take over. [HEIR] = the child who inherits. A California attorney and a tax adviser should confirm each step against the trust document, which was not reviewed.</p>""")

# --------------------------------------- laws ------------------------------------------
lw_rows = [
    R("Federal estate exclusion", "In force", f"{off(M.EXCL[2026])} for 2026; {off(M.EXCL[2027])} for 2027, indexed yearly.", f"Room for {usd(t['room_ab'])} of other assets today. The figure was {off(5490000)} in 2017 and {off(11180000)} in 2018: Congress can move it either way.", s=("irs_estate", "irs_2027")),
    R("Bills to repeal the federal estate tax (S.587, H.R.1301)", "Introduced 13 February 2025; no further action recorded", "Would end the federal estate tax.", "No effect on the homes alone, which are already under the exclusion; would matter only if the money exceeds the headroom.", s=("congress_s587", "congress_hr1301")),
    R("Initiative to repeal the Proposition 19 inheritance rules", "Failed 18 May 2026: too few signatures", "Would have let children keep a parent's assessed value again.", f"Had it passed, Property A's tax after inheritance would stay near {usd(d45['tax_keep'])} in 2045 instead of {usd(d45['tax_live'])} to {usd(d45['tax_full'])}.", s=("sos_memo", "boe_p19")),
    R("Proposition 19 family-home amount", "Next adjustment 16 February 2027", f"Now {off(M.CAP_2025_27)}; moves with the California house-price index.", "Each extra $100,000 protected saves about " + usd(M.r10(100000 * M.RATE_A)) + " a year on Property A.", s=("boe_cap",)),
    R("State guidance on Proposition 19", "Issued 3 August 2026", "Confirms the one-year move-in rule, removal of the exclusion on moving out, and that only the parent's unit in a multi-unit building qualifies.", "Removes any doubt that Property B's rented units are reassessed.", s=("boe_guid",)),
    R("Assessed-value factor", "1.02 for the 2026 roll", "Yearly increase capped at 2%.", "Keeps the owner's tax on Property A near " + usd(t["a_tax_keep"]) + " while ownership is unchanged.", s=("boe_infl26", "boe_infl"), flag=True),
    R("City B rent increase limit", "1.6% from 1 March 2026 to 28 February 2027", "Set each year at 60% of regional inflation.", f"Holds rent growth on sitting tenants below cost growth; Property B's rent rises about {usd(M.r10(t['b_rent'] * 0.016))} this year.", s=("cityb_rent", "cityb_rentlearn")),
    R("City B proposal, Board of Supervisors File No. 261020", "Proposed; not enacted (notice posted 9 November 2026)", "Would cap combined banked and capital-improvement increases at 10% a year.", "Limits catching up on skipped increases after inheriting Property B.", s=("cityb_rentlearn",)),
    R("Solar billing", "Net billing tariff for applications since 15 April 2023; older net-metering tariffs closed to new customers", "Export credits under the new tariff are usually below the retail rate.", "Property A's credit of $10 to $20 a month depends on its existing tariff; a legacy period applies and its end date for this home is not known.", s=("cpuc_nem",), flag=True),
    R("California death taxes", "None; prohibited", "A new state estate or inheritance tax would need voter approval, since the ban was enacted by initiative.", "No effect unless voters change it.", s=("rtc_13301", "sco")),
    R("Statewide ballot of 3 November 2026", "Results not checked on an official page", "", "Left blank. The failed initiative above was not on it.", s=("sos_memo",), flag=True),
]
page("laws.html", "Law watch",
     "Rules that are pending, recently changed or regularly adjusted, and what each one does to the numbers on this site.",
     f"""{table("Pending and recent changes", ["Item", "Status on " + CHECKED, "What it does", "Effect on this plan"], lw_rows)}
<p class="small">Recheck this page at least once a year and at the time of inheritance. The exclusion, the family-home amount, the rent limit and the tax rates are all republished annually by the sources linked above.</p>""")

# -------------------------------------- flagged ----------------------------------------
fl_rows = [
    R("F-01", "Market rent of Property A", "blank", "No official figure for this home. The model reports break-even rents instead. Get a written estimate from a licensed property manager at the time.", s=("hud_fmr",)),
    R("F-02", "Insurance premium, both homes", f"{usd(M.A['insurance'])} each (owner estimate)", "Owner is unsure. No quote and no official premium obtained; the state survey tool is interactive and was not queried. A rented three-unit building needs a landlord policy.", s=("cdi_tool", "cdi_guide")),
    R("F-03", "Maintenance", "blank", "Owner gave no figure (only that A costs less than B). Not in any total.", s=("irs_414",)),
    R("F-04", "Property A tax rate area", pc(rt["a_pct"], 4) + " used", f"Not confirmed for the parcel. Plausible range 1.000% to {pc(rt['a_high_pct'],3)}; effect on a reassessed bill today {usd(t['a_tax_full_low'])} to {usd(t['a_tax_full_high'])}.", s=("coa_rates",)),
    R("F-05", "Property A fixed charges", usd(rt["fixed_a"]), "Derived as bill minus rate x value; not itemised from the bill.", s=("coa_rates",)),
    R("F-06", "Property B bill versus published rate", usd(rt["fixed_b"]) + " unexplained", f"Bill is {pc(rt['b_implied_pct'])} of assessed value against a published rate of {pc(rt['b_pct'],4)}. Probably direct charges; confirm on the bill.", s=("cityb_tax",)),
    R("F-07", "Property B tax history", "Two odd years", "In the owner's history one year's tax rose about 18% while assessed value rose 2%, and one year's assessed value rose slightly less than the state factor. Neither is explained.", s=("boe_infl", "cityb_tax")),
    R("F-08", "Property A 2026 tax bill", "blank", "Not provided. The 2026 figure here is calculated from the 2026 assessed value.", s=("coa_rates", "boe_infl26")),
    R("F-09", "Market values", f"{usd(M.A['market_2026'])} and {usd(M.B['market_2026'])}", "Owner estimates; no appraisal. Every projection scales with them.", s=("irs_basis",)),
    R("F-10", "Is Property B part of the inheritance, and did the parent live in one unit?", "Unknown", "Shown both ways. If B is in the estate and no unit was the parent's home, all of it is reassessed.", s=("boe_guid",)),
    R("F-11", "Is Property B covered by the rent ordinance?", "Unknown", "Depends on the construction date (on or before 13 June 1979). Rent growth of 60% of inflation assumes it is.", s=("cityb_laws",)),
    R("F-12", "Rent for B's third unit", usd(t["unit3"]) + " a month assumed", "Set equal to the average of the two rented units. Not a quote.", s=("cityb_rentlearn",)),
    R("F-13", "Amount of money in the inheritance", "blank", "Not given. Headroom tables show how much fits under the exclusion.", s=("irs_estate",)),
    R("F-14", "Federal exclusion after 2027", "Indexed at 2% a year", "Assumption. The statute indexes it to inflation; Congress has changed the base several times.", s=("irs_2027", "fomc")),
    R("F-15", "House-price growth", f"{pc(GL*100)} / {pc(GB*100)} / {pc(GH*100)}", "From a statewide index, not the two neighbourhoods. One-year change to 2026 Q2 was only " + pc(hp["y1"]) + ".", s=SG),
    R("F-16", "Cost inflation", "2% a year", "Federal Reserve goal, used as a neutral assumption. Insurance and utilities in California may rise faster.", s=("fomc",)),
    R("F-17", "The heir's income-tax bracket", "blank", "Unknown. Results are shown before tax and at the top federal rate, with the break-even rate.", s=("irs_2027", "ftb_rates")),
    R("F-18", "Selling costs", "blank", "Brokerage and escrow fees are negotiable and have no official figure; only the county transfer tax is included. Each 1% is shown on the decision page.", s=("rtc_11911",)),
    R("F-19", "Solar tariff and legacy period", "Unknown", "The interconnection date and tariff were not provided; the 20-year legacy period was seen only in a search excerpt.", s=("cpuc_nem",)),
    R("F-20", "City B transfer tax", "blank", "The city's own transfer-tax page could not be opened. Matters only if Property B is sold.", s=("rtc_11911",)),
    R("F-21", "State income tax on Treasury interest; depreciation on a rented Property A", "Not modelled", "Neither was verified on an official page read in full, so neither is used.", s=("irs_p527", "ftb_cg")),
    R("F-22", "Sources seen only as search excerpts", "6 sources marked &dagger;", "Form 706 instructions, Publication 527, Revenue Ruling 2023-2, two state letters to assessors, H.R.1301. Statements resting on them are flagged where used.", s=("irs_i706", "irs_p527", "irs_rr2023", "boe_infl26", "boe_forms", "congress_hr1301")),
    R("F-23", "Privacy: jurisdiction is inferable", "Disclosure", "Pages name no place, but the local tax-rate and rent sources identify the county and city to anyone who opens them. Earlier commits in the repository history contain more detail than this site and cannot be removed without rewriting history; that is the owner's decision.", s=("coa_rates", "cityb_tax", "gh_prs")),
]
rc_rows = [
    R("C-01", "Federal exclusion for 2027", "Treated as unverified (short link returned 404)", f"Verified: {off(M.EXCL[2027])} on the full news-release address", "Use the verified figure.", s=("irs_2027",)),
    R("C-02", "City B tax rate", "1.18268325% (fiscal year 2025-26 resolution)", "1.18162182% (fiscal year 2026-27, tax collector)", "Both are correct for their years; the difference on Property B is about one dollar a year.", s=("cityb_tax",)),
    R("C-03", "Return on sale proceeds", "7.0% equities / 4.0% bonds, yields not re-verified", f"{pc(asm['r10y']*100)} 10-year Treasury on 9 November 2026, plus a break-even", "The main edition's sell result leans on the 7% assumption; at the Treasury yield selling still leads before tax, by less.", s=("treasury",)),
    R("C-04", "Rent for Property A", "3.0% of value a year (assumed)", f"Blank; break-even {pc(d45['be_yield_vs_sell'])} to beat selling", "The assumed 3.0% is above the break-even, which is why the main edition ranks renting close to selling. No verified rent supports either.", s=("hud_fmr",)),
    R("C-05", "Rent growth, Property B", "2.5% a year", f"{pc(asm['rent_growth']*100,1)} a year (60% of inflation); 1.6% this year", "Main edition overstates rent growth if the building is rent-controlled.", s=("cityb_rent", "cityb_rentlearn")),
    R("C-06", "House-price growth", "3% / 4% / 5% (assumed)", f"{pc(GL*100)} / {pc(GB*100)} / {pc(GH*100)} (state index, 20 and 30 years)", "Similar centre; the official range is wider.", s=SG),
    R("C-07", "Tax rate on income", "33.3% assumed", "Before tax and at 37%, with the break-even rate", "Bracket unknown in both.", s=("irs_2027", "ftb_rates")),
    R("C-08", "Repeal initiative", "Not found among qualified measures", "Confirmed failed on 18 May 2026", "Same conclusion, now with the official memorandum.", s=("sos_memo",)),
    R("C-09", "Recommendation for Property A", "Sell at inheritance; margin thin", "Sell in the first year by default; two switch tests; margin thin", "The two editions agree.", s=("irs_basis", "treasury")),
]
rp_rows = [
    R("R-01", "Several sessions published competing editions on the same day", "The site was replaced four times on 10 November 2026 (pull requests 17 to 24) and a further replacement is open (23). Conclusions differed between editions.", "Keep one main edition; treat this cross-check as a second opinion only.", s=("gh_prs",)),
    R("R-02", "Earlier commits contain unrounded figures and postal codes", "Current files are sanitised; Git history is not.", "Owner to decide whether to rewrite history.", s=("gh_prs",)),
    R("R-03", "Two publishers", "The site is built both from the branch root and by a workflow artifact; the setting could not be changed by a session (403).", "Both now carry the same allow-list; owner can switch the Pages source to Actions.", s=("gh_prs",)),
    R("R-04", "Open stale pull requests", "Numbers 7, 14, 16 and 23 were open when this was written.", "Close or merge deliberately.", s=("gh_prs",)),
    R("R-05", "About fifty retired paths are kept as withdrawal notices", "They prevent old pages being served but clutter the repository.", "Remove once caches have expired.", s=("gh_prs",)),
]
page("flagged.html", "Flagged for Review",
     "Everything that could not be confirmed on an official page, every assumption the model needs, where this cross-check differs from the main edition, and irregularities found in the repository. None of these blocks publication; all need a human decision.",
     f"""<div class="note warn"><b>Rule applied.</b> A value is shown as verified only if the official page was opened and read on {CHECKED}. Where no official source exists the cell is blank and the model works around it. Owner-provided figures are used as given and labelled.</div>
<h2>Unverified values and assumptions</h2>{table("Flag register", ["ID", "Item", "Value used", "Why flagged and what to do"], fl_rows)}
<h2>Differences from the main edition</h2>{table("Reconciliation", ["ID", "Item", "Main edition", "This cross-check", "Result"], rc_rows)}
<h2>Repository irregularities</h2>{table("Repository review", ["ID", "Finding", "Detail", "Suggested action"], rp_rows)}""")

# -------------------------------------- sources ----------------------------------------
STAT = {"read": "Read in full", "excerpt": "Search excerpt only &dagger; (flagged)", "lookup": "Look-up link; no value taken", "repo": "Repository evidence"}
so_rows = [R(e(v[0]), e(v[1]), STAT[v[3]], f'<span data-official="1">{e(v[4])}</span>', s=(k,), flag=v[3] != "read") for k, v in SOURCES.items()]
n_read = sum(1 for v in SOURCES.values() if v[3] == "read")
page("sources.html", "Sources",
     f"{len(SOURCES)} sources: {n_read} official pages read in full on {CHECKED}, and the rest marked for what they are. Each line says what the source supports.",
     f"""{table("Source ledger", ["Publisher", "Document", "Status", "What it supports"], so_rows)}
<p class="small">Machine-readable copy: <a href="data/sources.json">data/sources.json</a>. Owner-provided figures have no official source and are labelled wherever they appear.</p>""")

(OUT / "data").mkdir(exist_ok=True)
(OUT / "data" / "sources.json").write_text(json.dumps(
    {k: dict(publisher=v[0], title=v[1], url=v[2], status=v[3], supports=v[4]) for k, v in SOURCES.items()}, indent=1) + "\n")
print(f"built {len(NAV)} pages into {OUT}")
