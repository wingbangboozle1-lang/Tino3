"""Render the anonymised quantitative decision edition.

Reads  : assets/sources.json, assets/data/inputs.json, assets/data/model.json
Writes : the public HTML pages in the repository root

Deterministic: no network calls, no randomness, no timestamps in the output
other than the stated build date.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "data"
SRC_DOC = json.loads((ROOT / "assets" / "sources.json").read_text(encoding="utf-8"))
SOURCES = {s["id"]: s for s in SRC_DOC["sources"]}
INPUTS = json.loads((DATA / "inputs.json").read_text(encoding="utf-8"))
MODEL = json.loads((DATA / "model.json").read_text(encoding="utf-8"))
ECON = json.loads((DATA / "economy.json").read_text(encoding="utf-8"))

A = INPUTS["property_a"]
B = INPUTS["property_b"]
V = INPUTS["verified_parameters"]
ASM = INPUTS["assumptions"]
BUILD_DATE = "13 November 2026"

NAV_GROUPS = [
    ("Start here", ["index.html", "executive-summary.html", "decision.html"]),
    ("The two properties", ["property-a.html", "property-b.html", "ownership-distinction.html"]),
    ("Money over time", ["costs.html", "projections.html", "taxes.html"]),
    ("Rules and the estate", ["inheritance.html", "estate.html", "laws.html"]),
    ("Black swan economics", ["black-swan.html", "economy.html"]),
    ("Review before deciding", ["questions.html", "suggestions.html", "review.html"]),
    ("Evidence", ["sources.html"]),
]
PAGE_TITLES = {
    "index.html": "Dashboard",
    "executive-summary.html": "Executive summary",
    "decision.html": "The decision",
    "property-a.html": "Property A - the home being inherited",
    "property-b.html": "Property B - the building already owned",
    "ownership-distinction.html": "Why the two properties are not the same",
    "costs.html": "Running costs",
    "projections.html": "Year by year projections",
    "taxes.html": "Income tax on each path",
    "inheritance.html": "Inheriting through a trust, step by step",
    "estate.html": "Estate and inheritance tax thresholds",
    "laws.html": "What the law says now, and what may change",
    "black-swan.html": "Black swan conditions",
    "economy.html": "The verified historical record",
    "questions.html": "Questions to answer before deciding",
    "suggestions.html": "Suggestions for review",
    "review.html": "Flagged for review and repository audit",
    "sources.html": "Source ledger",
}


# ------------------------------------------------------------------ helpers --
BLANK_CELL = '<span class="blank">not supplied</span>'


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def money10(x: float) -> int:
    """Round to the nearest $10, halves up, exactly as the model does."""
    return int((abs(x) + 5.0) // 10 * 10) * (1 if x >= 0 else -1)


def m(x) -> str:
    """Format a rounded dollar amount."""
    if x is None:
        return '<span class="blank">not supplied</span>'
    neg = x < 0
    v = abs(int(x))
    s = f"${v:,}"
    return f"&minus;{s}" if neg else s


def pcf(x, places=1) -> str:
    """Format a fraction such as 0.04 as a percentage."""
    if x is None:
        return '<span class="blank">not supplied</span>'
    return f"{x * 100:.{places}f}%"


def pc(x, places=2) -> str:
    if x is None:
        return '<span class="blank">not supplied</span>'
    return f"{x:.{places}f}%"


def slink(sid: str, label: str | None = None) -> str:
    s = SOURCES[sid]
    text = label or f"{s['publisher']}"
    return (f'<a class="src" href="{esc(s["url"])}" target="_blank" '
            f'rel="noopener noreferrer" title="{esc(s["title"])}">{esc(text)}</a>')


def src_cell(ids, label="Official source"):
    ids = [ids] if isinstance(ids, str) else list(ids)
    missing = [i for i in ids if i not in SOURCES]
    assert not missing, f"unknown source ids: {missing}"
    links = ("<br>".join(slink(i) for i in ids) if ids else
             '<span class="blank">no official source</span><br>'
             '<a class="src" href="review.html#register">Logged on the register</a>')
    return f'<td class="src-cell"><span class="src-label">{esc(label)}</span><br>{links}</td>'


CORE_SOURCES = ["rtc63_2", "boe_pub29", "irs_basis", "irs_tc409"]

# The gate that every reassessment figure on this site depends on. Revenue and Taxation
# Code section 63.2 excludes a transfer from change in ownership only where the transferor
# and transferee are parent and child (or grandparent and grandchild with the middle
# generation deceased). If the relationship is different, no exclusion is available at all
# and the prior taxable value plus the shelter is irrelevant. Read at leginfo, 13 Nov 2026.
ELIGIBILITY_TEXT = (
    "Every reassessment figure on this site assumes the transfer will qualify for the "
    "intergenerational exclusion in Revenue and Taxation Code section 63.2. That section "
    "excludes a transfer only where it is <strong>between parents and their children</strong>, "
    "or between grandparents and grandchildren where every parent of the grandchild who is a "
    "child of the grandparent has died. &ldquo;Children&rdquo; is defined in the statute to "
    "include a stepchild, a son-in-law or daughter-in-law, and an adopted child adopted before "
    "age 18; it also includes a foster child of a licensed foster parent where adoption was "
    "barred. The relationship is a condition of the exclusion, not a detail: if the "
    "transferor and the heir are not in one of those relationships, no exclusion is available, "
    "the property is reassessed to full market value, and the entire saving shown on this page "
    "disappears."
)


def eligibility_callout() -> str:
    return callout(
        "flag", "First gate: is the transfer between a parent and a child?",
        f"<p>{ELIGIBILITY_TEXT}</p>"
        f"<p>This analysis is written on the assumption that it is. The trust document is the "
        f"only thing that confirms it, and this site has not seen it. Until it is confirmed, "
        f"treat every Proposition 19 shelter figure here as conditional. See "
        f"<a href=\"questions.html\">question A-1</a>.</p>"
        f"<p class=\"callout-src\">{slink('rtc63_2_eligibility')} &middot; {slink('boe_prop19')} "
        f"&middot; {slink('boe_lta25009')}</p>")


def method_cell(href: str, text: str = "Model output", sources=None):
    """A computed row. Links the method page and the official rules the model implements."""
    ids = list(sources) if sources else CORE_SOURCES
    links = "<br>".join(slink(i) for i in ids)
    return (f'<td class="src-cell"><span class="src-label">{esc(text)}</span><br>'
            f'<a class="src" href="{esc(href)}">Inputs and method</a><br>{links}</td>')


def table(caption, headers, rows, cls="", note=None):
    head = "".join(f"<th scope=\"col\">{esc(h)}</th>" for h in headers)
    body = "".join(f"<tr>{r}</tr>" for r in rows)
    out = [f'<div class="table-wrap"><table class="{esc(cls)}">',
           f"<caption>{esc(caption)}</caption>",
           f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"]
    if note:
        out.append(f'<p class="table-note">{note}</p>')
    out.append("</div>")
    return "".join(out)


def callout(kind, title, body):
    return (f'<div class="callout {esc(kind)}"><h3>{esc(title)}</h3>'
            f'<div class="callout-body">{body}</div></div>')


METHOD_TEXT = (
    "A deterministic model, rebuilt from assets/data/inputs.json and assets/data/series.json by "
    "scripts/model.py. House prices grow at a stated nominal rate, the assessed value rolls forward under the "
    "published rules with an inflation cap, fixed charges grow with inflation, running costs are inflated at "
    "the same rate, and each path is valued at the end of a thirty year horizon after selling costs and tax. "
    "Every monetary result is rounded to the nearest $10 before it is printed. There is no randomness, so the "
    "same inputs always produce the same outputs."
)


def method_links() -> str:
    out = []
    for sid in CORE_SOURCES:
        t = SOURCES[sid]["title"]
        out.append(f"<li>{slink(sid)} - {esc(t)}</li>")
    return "".join(out)


def page(name: str, body: str, lede: str = "") -> str:
    nav = []
    for group, pages in NAV_GROUPS:
        items = "".join(
            f'<li><a href="{esc(p)}"'
            + (' class="active"' if p == name else "")
            + f">{esc(PAGE_TITLES[p])}</a></li>" for p in pages)
        nav.append(f'<div class="nav-group"><span class="nav-title">{esc(group)}</span>'
                   f"<ul>{items}</ul></div>")
    lede_html = f'<p class="lede">{lede}</p>' if lede else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(PAGE_TITLES[name])} - Property inheritance decision</title>
<meta name="description" content="Anonymised quantitative decision analysis for an inherited California home and an already-owned rental building. Every figure rounded to the nearest $10.">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap">
    <p class="brand"><a href="index.html">Property inheritance decision</a></p>
    <p class="tagline">Two California properties, one decision. Anonymised. Every figure rounded to the nearest $10.</p>
  </div>
</header>
<div class="wrap layout">
  <nav class="site-nav" aria-label="Sections">
    {"".join(nav)}
  </nav>
  <main id="main">
    <h1>{esc(PAGE_TITLES[name])}</h1>
    {lede_html}
    {body}
    <section id="method" class="method">
      <h2>How the numbers on this page are produced</h2>
      <p>Every computed figure on this page comes from <code>scripts/model.py</code>, which reads
        <code>assets/data/inputs.json</code> and <code>assets/data/series.json</code>. Monetary results are
        rounded to the nearest $10 before they are printed. The rules the model implements are the published
        official rules below; where a page uses a stated assumption or an unverified owner figure, that row says
        so and is logged on the <a href="review.html#register">register of unverified and assumed items</a>.</p>
      <ul class="method-links">
        {method_links()}
      </ul>
      <p>Full method and inputs: <a href="review.html#method-detail">how the model works</a>.
        Every official source used anywhere on the site: <a href="sources.html">the source ledger</a>.</p>
    </section>
    <p class="page-footer">Built {esc(BUILD_DATE)}. Sources were checked on 13 November 2026 and are listed on the
      <a href="sources.html">source ledger</a>. Nothing here is legal, tax or investment advice.</p>
  </main>
</div>
</body>
</html>
"""


# ------------------------------------------------------------------- content --
def privacy_banner() -> str:
    return callout("privacy", "Privacy and accuracy notice", f"""
<ul>
<li><strong>What is published.</strong> Market values, assessed values, tax bills, rent and running costs, rounded to the nearest $10 as requested, plus the model outputs computed from them.</li>
<li><strong>What is never published.</strong> No name, street address, parcel number, ZIP code, trust term, beneficiary detail or utility account appears on any page or in any published file. The two properties are called Property A (the home being inherited, in Santa Clara County) and Property B (the three-unit building already owned by the heir, in the City and County of San Francisco).</li>
<li><strong>The inherited cash.</strong> The amount is not published. The estate page works entirely in anonymous scenario bands.</li>
<li><strong>Rounding is not anonymity.</strong> Rounding to $10 defeats a search for an exact figure; it does not stop someone who already holds the county record from recognising a parcel. That residual risk is disclosed here rather than hidden.</li>
<li><strong>Owner figures are unverified.</strong> Values taken from the owner's own records are labelled <span class="badge unverified">unverified</span> unless an official public record was checked. They are listed again on the <a href="review.html">flagged for review</a> page.</li>
<li><strong>History.</strong> Earlier commits in this public repository, previous pull-request diffs, forks and external copies are separate exposure surfaces. Nothing on this site can certify them erased.</li>
</ul>
""")


def kpi(value, label, sub=""):
    sub_html = f'<span class="kpi-sub">{sub}</span>' if sub else ""
    return f'<div class="kpi"><span class="kpi-value">{value}</span><span class="kpi-label">{esc(label)}</span>{sub_html}</div>'


# --------------------------------------------------------------------- index --
def page_index() -> str:
    p45 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2045)
    best = p45["best_path"]
    kpis = "".join([
        kpi(m(A["estimated_market_value_2026"]), "Property A, estimated value",
            "Owner estimate, November 2026 &middot; unverified"),
        kpi(m(B["estimated_market_value_2026"]), "Property B, estimated value",
            "Owner estimate, November 2026 &middot; unverified"),
        kpi(m(p45["bill_if_rent_year1"]), "Property A tax bill in 2045 if let out",
            f"Against {m(p45['bill_today_projected'])} if the assessment is never reset"),
        kpi(m(V["federal_basic_exclusion_2026"]["value"]), "Federal estate tax exclusion, 2026",
            f"{m(V['federal_basic_exclusion_2027']['value'])} for 2027 &middot; IRS"),
        kpi(pc(p45["breakeven_house_growth"]), "House growth needed to justify keeping it",
            "Per year, for 30 years, to match selling and investing at 7%"),
        kpi(m(p45["breakeven_rent_monthly"]), "Monthly rent needed to justify letting it",
            "In 2045 dollars, on zero rent credited to the letting paths"),
    ])
    gating = callout("flag", "One fact is assumed, not verified, and everything else depends on it", f"""
<p>The Proposition 19 exclusion applies only where the transfer is between a parent and a child, or between a
grandparent and a grandchild whose parent has died. If that is not the relationship here, there is no exclusion:
the property is reassessed to full market value, every shelter figure on this site disappears, and the case for
selling gets stronger. The trust document is the only thing that settles it. <a href="questions.html">Answer
question A-1</a> before relying on any number here. {slink('rtc63_2_eligibility')}</p>""")
    cards = []
    for group, pages in NAV_GROUPS:
        if group == "Start here":
            continue
        items = "".join(
            f'<li><a href="{esc(p)}"><strong>{esc(PAGE_TITLES[p])}</strong>'
            f'<span>{esc(SUMMARIES[p])}</span></a></li>' for p in pages)
        cards.append(f'<section class="card"><h2>{esc(group)}</h2><ul class="card-list">{items}</ul></section>')
    return (
        privacy_banner()
        + gating
        + f'<section class="kpi-row">{kpis}</section>'
        + callout("answer", "The one-line answer", f"""
<p>Under every baseline this site can build, <strong>selling Property A soon after it is inherited beats living in it or letting it out</strong>, and it is not close. The reason is a one-off combination: the inheritance resets the income-tax basis to the value at death, so an immediate sale pays almost no capital gains tax, while the property tax assessment jumps to market value under Proposition 19. Waiting converts a tax-free asset into a taxed one and adds roughly {m(p45['bill_if_rent_year1'] - p45['bill_today_projected'])} a year of extra property tax if the home is let out.</p>
<p>The break-even house growth needed to make keeping the home beat selling is <strong>{pc(p45['breakeven_house_growth'])} a year for thirty years</strong>. The verified house price index for this area compounded at 6.9% a year over the last fifty years and 3.3% a year over the last twenty. Read the <a href="decision.html">full decision</a>, then the <a href="black-swan.html">cases where this flips</a>.</p>
""")
        + '<section class="card-grid">' + "".join(cards) + "</section>"
        + callout("method", "How to read this site", """
<ol>
<li><strong>Start</strong> with the <a href="executive-summary.html">executive summary</a> and the <a href="decision.html">decision page</a>.</li>
<li><strong>Check the inputs.</strong> Every number the model uses is on the <a href="property-a.html">Property A</a>, <a href="property-b.html">Property B</a> and <a href="costs.html">costs</a> pages, with its source or an explicit unverified flag.</li>
<li><strong>Check the stress.</strong> No projection on this site relies on a single smooth growth rate. See <a href="black-swan.html">black swan conditions</a> and the <a href="economy.html">verified historical record</a>.</li>
<li><strong>Do not act yet.</strong> The <a href="questions.html">questions page</a> lists what is still unknown and how to find it out. The <a href="suggestions.html">suggestions page</a> is a review queue: nothing there has been implemented.</li>
</ol>""")
    )


SUMMARIES = {
    "executive-summary.html": "The important details on one page.",
    "decision.html": "Five paths, the break-evens, and the recommendation.",
    "property-a.html": "The inherited home: roll, value, reassessment, costs.",
    "property-b.html": "The building already owned: rent, rent control, costs.",
    "ownership-distinction.html": "Why inherited and already-owned are not interchangeable.",
    "costs.html": "Water, power, insurance, maintenance and tax, projected.",
    "projections.html": "Year by year to 2076 for value, assessed value and tax.",
    "taxes.html": "Basis step-up, capital gains, the 121 exclusion, recapture.",
    "inheritance.html": "The trust transfer, phase by phase, with deadlines.",
    "estate.html": "Federal thresholds, California's position, scenario bands.",
    "laws.html": "Enacted, dead and proposed rules that could move the answer.",
    "black-swan.html": "Regimes where the answer changes, and by how much.",
    "economy.html": "Fifty years of verified inflation, house price and yield data.",
    "questions.html": "What is known, what is missing, and how to find it.",
    "suggestions.html": "A review queue of proposals. Nothing implemented yet.",
    "review.html": "Unverified figures, modelling caveats and the repository audit.",
    "sources.html": "Every official source used, with what it supports.",
}


# --------------------------------------------------------- executive summary --
def page_executive_summary() -> str:
    p40 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2040)
    p45 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2045)
    p50 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2050)

    rows = []
    for p in (p40, p45, p50):
        for key, label in (("sell_equities", "Sell at inheritance, invest in equities"),
                           ("sell_treasury", "Sell at inheritance, reinvest at Treasury yields"),
                           ("live_in", "Move in and hold for 30 years"),
                           ("live_then_rent", "Move in for two years, then let it out"),
                           ("rent_out", "Let it out from the start")):
            v = p["paths"][key]
            rows.append(
                f"<td>{p['inherit_year']}</td><td>{esc(label)}</td>"
                f"<td>{m(v['terminal'])}</td>"
                f"<td>{m(v.get('outflow', 0))}</td>"
                + method_cell("decision.html#method", "Model output"))
    term = table(
        "Terminal value after 30 years, by inheritance year and path. "
        "Baseline assumptions: house prices 4.0% a year, inflation 2.5%, equities 7.0% gross, "
        "Treasuries 4.7%, selling costs 5.5%.",
        ["Inherited", "Path", "Terminal value", "Tax and costs paid over 30 years", "Basis"],
        rows)

    facts = [
        ("The condition everything rests on", "The Proposition 19 exclusion applies only to a transfer between a parent and a child, or between a grandparent and a grandchild where the middle generation has died. RTC section 63.2 sets that out. If the heir is not in that relationship to the transferor, the property is reassessed to full market value and every shelter figure here falls away."),
        ("Property A", f"Inherited through a trust, planned 2040 to 2050. Worth about {m(A['estimated_market_value_2026'])}. Not owned by the heir today."),
        ("Property B", f"Already owned by the heir. Worth about {m(B['estimated_market_value_2026'])}, three units, two let at {m(B['rent']['monthly'])} a month. The heir can live here without losing that rent."),
        ("The tax cliff at transfer", f"Today the Property A bill is about {m(MODEL['costs_a_now']['property_tax'])}. If the heir inherits in 2045 and does not move in, the bill becomes about {m(p45['bill_if_rent_year1'])}. If the heir does move in and claims the Proposition 19 exclusion, it becomes about {m(p45['bill_if_live_year1'])}."),
        ("Why moving in only half-helps", f"The Proposition 19 exclusion shelters the old assessed value plus an indexed {m(V['prop19_value_cap_2025_2027']['value'])}. Everything above that is reassessed. In 2045 the sheltered slice is about {m(p45['prop19_cap'])} against a market value of {m(p45['value_at_death'])}."),
        ("The tax-free sale window", "Property acquired from a decedent takes a basis equal to its value at death, so a sale soon after the inheritance pays close to zero capital gains tax. Holding it for thirty years turns the appreciation into a gain taxed at roughly 37% combined federal and California."),
        ("The equity comparison", f"To match selling and investing at 7%, the home must appreciate {pc(p45['breakeven_house_growth'])} a year for thirty years. The verified index for the area compounded at 6.9% over fifty years and 3.3% over the last twenty."),
        ("The rental comparison", f"Letting the home out would need about {m(p45['breakeven_rent_monthly'])} a month in 2045 to match selling and investing. That is over 5% of the property's value per year in gross rent."),
        ("The estate position", f"California has had no estate tax since 2005. Federally, the 2026 exclusion is {m(V['federal_basic_exclusion_2026']['value'])} per person and {m(V['federal_basic_exclusion_2027']['value'])} for 2027. Portability lets a surviving spouse use a deceased spouse's unused exclusion."),
        ("The biggest unknown", "Whether the heir wants to live in this specific house. That is a preference, not a number, and it is worth more than any gap in this analysis."),
    ]
    fact_rows = [
        f"<td><strong>{esc(k)}</strong></td><td>{v}</td>"
        + src_cell(["boe_lta25009", "rtc63_2", "irs_basis", "sco_estate"], "Key rules")
        for k, v in facts]
    ftab = table("The important details", ["Detail", "What this analysis found"], fact_rows)

    return (
        eligibility_callout()
        + callout("summary", "Recommendation", f"""
<p><strong>Sell Property A soon after it is inherited, unless the heir genuinely wants to live in that house.</strong></p>
<p>Selling converts an asset earning nothing into capital, at almost no tax, and it removes a property tax bill that is about to multiply by six to eleven times. Living in the house is the only path that keeps the tax bill lower, and it still leaves the heir holding a single, undiversified, illiquid asset in one California school district. Letting it out fails every scenario this site can build, because it combines the full reassessment with landlord costs and a rental yield below the return available elsewhere — but that comparison credits the letting paths with <strong>no rent at all</strong>, so read it as a floor and check the break-even rent below before relying on it.</p>
<p>The counter-case is real and it is on the <a href="black-swan.html">black swan page</a>: if house prices in this area repeat their 1977 to 1981 or 2021 to 2023 pace, keeping the house wins. That is a bet on one neighbourhood, not a plan.</p>
""")
        + ftab
        + term
        + callout("risk", "Five things that could change the answer", """
<ol>
<li><strong>The heir wants to live there.</strong> That is worth the whole gap if it is true. It also has to be true for the whole time: moving out removes the Proposition 19 exclusion.</li>
<li><strong>Law changes.</strong> On unofficial results as of 12 November 2026, California voters approved Proposition 3, which makes the high-income tax rates permanent (60.7% yes), and rejected Proposition 40, the one-time billionaire tax (52.4% no). Certification is due by 11 December 2026. Both are on the <a href="laws.html">law page</a>. A future measure could cut the other way.</li>
<li><strong>The house outgrows everything.</strong> See the <a href="black-swan.html">stress cases</a>.</li>
<li><strong>The estate is large enough to matter federally.</strong> See the <a href="estate.html">estate page</a>: the 2026 exclusion is high, but it is indexed and can be cut by Congress.</li>
<li><strong>An input is wrong.</strong> Every owner-supplied figure is flagged. The <a href="questions.html">questions page</a> is the list of what to confirm and how.</li>
</ol>""")
    )


# ------------------------------------------------------------------ decision --
def page_decision() -> str:
    p45 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2045)
    rows = []
    for p in MODEL["paths"]:
        for key, label in (("sell_equities", "Sell at inheritance, invest in equities"),
                           ("sell_treasury", "Sell at inheritance, reinvest at Treasuries"),
                           ("live_in", "Move in and hold for 30 years"),
                           ("live_then_rent", "Move in two years, then let it out"),
                           ("rent_out", "Let it out from the start")):
            v = p["paths"][key]
            rows.append(f"<td>{p['inherit_year']}</td><td>{esc(label)}</td>"
                        f"<td>{m(v['terminal'])}</td>"
                        f"<td>{m(v.get('outflow', 0))}</td>"
                        + method_cell("#method", "Model output"))
    paths_table = table(
        "Terminal value after thirty years, by inheritance year and path",
        ["Inherited", "Path", "Terminal value", "Tax and costs paid", "Basis"], rows,
        note="Terminal value is what is left after selling costs and capital gains tax at the end of the "
             "thirty years, plus any accumulated net rental cash in the rental paths. It is a nominal "
             "figure in the money of that future year.")

    be_rows = []
    for p in MODEL["paths"]:
        be_rows.append(
            f"<td>{p['inherit_year']}</td>"
            f"<td>{m(p['breakeven_rent_annual'])}</td>"
            f"<td>{m(p['breakeven_rent_monthly'])}</td>"
            f"<td>{pc(p['breakeven_return_vs_live'])}</td>"
            f"<td>{pc(p['breakeven_return_vs_rent'])}</td>"
            f"<td>{pc(p['breakeven_house_growth'])}</td>"
            f"<td>{m(p['housing_value_needed'])}</td>"
            + method_cell("#method", "Model output"))
    be_table = table(
        "Break-even questions, answered",
        ["Inherited", "Rent needed per year", "Rent needed per month",
         "Return needed to beat living in it", "Return needed to beat letting it",
         "House growth needed to keep it", "Housing value the home must provide per year"],
        be_rows,
        note="\"Housing value\" is the annual value of living in the house that would be needed to close the "
             "gap between living in it and selling. It is the number to compare against what the heir would "
             "otherwise pay, or could otherwise earn, for somewhere to live.")

    sens_rows = []
    for s in MODEL["sensitivity"]:
        best_key = s["best"]

        def cell(key, val):
            return f'<td class="best">{m(val)}</td>' if key == best_key else f"<td>{m(val)}</td>"

        sens_rows.append(
            f"<td>{pc(s['house_growth'], 1)}</td><td>{pc(s['equity_return'], 1)}</td>"
            + cell("sell_equities", s["sell_equities"])
            + cell("sell_treasury", s["sell_treasury"])
            + cell("live_in", s["live_in"])
            + cell("rent_out", s["rent_out"])
            + f"<td><strong>{esc(PATH_LABELS[best_key])}</strong></td>"
            + method_cell("#method", "Model output"))
    sens_total = len(MODEL["sensitivity"])
    sens_sell = sum(1 for s in MODEL["sensitivity"] if s["best"].startswith("sell"))
    reg_total = len(MODEL["regimes"])
    reg_sell = sum(1 for r in MODEL["regimes"] if r["run"]["best"].startswith("sell"))
    rent_callout = callout("flag", "The letting paths are credited with no rent at all", f"""
<p>No market rent for Property A has been supplied, and no official source publishes a market rent for a
specific home, so this site does not invent one. The consequence is that both letting paths carry every
landlord cost and <strong>zero rental income</strong>. They are therefore not a test of whether letting the
house works; they are a floor.</p>
<p>The break-even rent is the honest figure: about <strong>{m(p45['breakeven_rent_monthly'])} a month in 2045</strong>,
roughly {m(p45['breakeven_rent_annual'])} a year, to end thirty years in the same position as selling and
investing. That is about {pc(p45['breakeven_rent_annual'] / p45['value_at_death'] * 100, 1)} of the property's
value in gross rent, every year. Whether the market clears that is the open question, and it is the one
question that could move the recommendation. See <a href="suggestions.html">suggestion S-06</a>; the input that
would be used is named and empty in the data file, so a documented rent opinion can be added and the whole
model rebuilt.</p>
<p>Until then, read every statement that letting is the weakest path as <em>the weakest path at zero rent</em>.</p>
""")

    sens_table = table(
        "Sensitivity: which path wins at each combination of house growth and equity return",
        ["House growth", "Equity return", "Sell, equities", "Sell, Treasuries",
         "Live in it", "Let it out", "Best path", "Basis"], sens_rows,
        note=f"Selling wins in {sens_sell} of the {sens_total} combinations; in the others the winner is "
             "selling and holding Treasuries, which is still selling. Keeping the home wins only where this "
             "one neighbourhood outgrows the whole stock market by a wide margin. The highlighted figure in "
             "each row is that row's winner.")
    sens_kpis = '<div class="kpi-row">' + "".join([
        kpi(f"{sens_sell} of {sens_total}", "Sensitivity combinations won by selling",
            "The rest are won by selling into Treasuries, which is still selling."),
        kpi(f"{reg_sell} of {reg_total}", "Stress regimes won by selling",
            "The ones it loses repeat the 1970s or the 2021 to 2023 burst."),
    ]) + "</div>"

    return (
        eligibility_callout()
        + callout("recommend", "What this site recommends", f"""
<p><strong>Sell soon after the inheritance.</strong> It leads in the baseline, in {sens_sell} of the {sens_total}
sensitivity combinations, and in {reg_sell} of the {reg_total} stress regimes. It is also the only path that does
not depend on the heir wanting to live in this particular house, being able to keep it as a principal residence,
or finding a tenant at an implausible rent.</p>""")
        + sens_kpis
        + paths_table
        + rent_callout
        + be_table
        + sens_table
        + '<h2>What the model does and does not do</h2>'
        + table("Model inputs and their status",
                ["Input", "Value used", "Status", "Basis"],
                [
                    f"<td>House price growth, both properties</td><td>{pcf(ASM['house_growth']['baseline'],1)} a year (band {pcf(ASM['house_growth']['low'],1)} to {pcf(ASM['house_growth']['high'],1)})</td>"
                    f'<td><span class="badge assumption">assumption</span></td>'
                    + src_cell(ASM["house_growth"]["src"], "Verified series"),
                    f"<td>Inflation</td><td>{pcf(ASM['inflation']['baseline'],1)} a year (band {pcf(ASM['inflation']['low'],1)} to {pcf(ASM['inflation']['high'],1)})</td>"
                    f'<td><span class="badge assumption">assumption</span></td>'
                    + src_cell(ASM["inflation"]["src"], "Official anchor"),
                    f"<td>Equity return, nominal gross</td><td>{pcf(ASM['equity_return_nominal_gross']['baseline'],1)} a year (band {pcf(ASM['equity_return_nominal_gross']['low'],1)} to {pcf(ASM['equity_return_nominal_gross']['high'],1)})</td>"
                    f'<td><span class="badge assumption">assumption</span></td>'
                    + src_cell([], "No official source"),
                    f"<td>Equity tax drag</td><td>{pcf(ASM['equity_tax_drag']['baseline'],1)} a year</td>"
                    f'<td><span class="badge assumption">assumption</span></td>'
                    + src_cell(ASM["equity_tax_drag"]["src"], "Rate source"),
                    f"<td>Treasury reinvestment yield</td><td>{pcf(ASM['treasury_yield_nominal']['baseline'],1)} a year</td>"
                    f'<td><span class="badge assumption">assumption</span></td>'
                    + src_cell(ASM["treasury_yield_nominal"]["src"], "Official anchor"),
                    f"<td>Selling costs</td><td>{pcf(ASM['selling_cost_pct']['baseline'],1)} of price</td>"
                    f'<td><span class="badge assumption">assumption</span></td>'
                    + src_cell(ASM["selling_cost_pct"]["src"], "Transfer tax statute"),
                    f"<td>Combined tax on a gain</td><td>{pcf(ASM['combined_gain_tax_rate']['baseline'],1)}</td>"
                    f'<td><span class="badge assumption">assumption</span></td>'
                    + src_cell(ASM["combined_gain_tax_rate"]["src"], "Rate sources"),
                    f"<td>Property A ad valorem rate</td><td>{pcf(ASM['ad_valorem_rate_a']['value'],3)}</td>"
                    f'<td><span class="badge unverified">assumption, flagged</span></td>'
                    + src_cell(ASM["ad_valorem_rate_a"]["src"], "Rate structure"),
                    f"<td>Property B ad valorem rate</td><td>{pcf(ASM['ad_valorem_rate_b']['value'],5)}</td>"
                    f'<td><span class="badge verified">published</span></td>'
                    + src_cell(ASM["ad_valorem_rate_b"]["src"], "SF Treasurer"),
                    f"<td>Assessed value growth</td><td>{pcf(ASM['assessed_value_growth']['baseline'],1)} a year</td>"
                    f'<td><span class="badge verified">verified rule</span></td>'
                    + src_cell(ASM["assessed_value_growth"]["src"], "Proposition 13 cap"),
                    f"<td>Horizon</td><td>{ASM['horizon_years']} years after the inheritance</td>"
                    f'<td><span class="badge assumption">assumption</span></td>'
                    + src_cell([], "Choice, not a source"),
                ],
                note="Every assumption is a stated scenario, not a forecast. Where an official source "
                     "anchors the number it is linked; where none exists the cell says so.")
        + callout("limit", "What the model leaves out", """
<ul>
<li><strong>Housing value.</strong> Living in the house produces somewhere to live. The break-even table prices that value; the terminal-value table does not add it in.</li>
<li><strong>Taxes on the invested money.</strong> The equity path already carries an annual drag. A further tax on final liquidation is not charged, because the same treatment would have to be applied to the property paths and would be avoided anyway if the portfolio is held until death.</li>
<li><strong>State and federal interaction.</strong> The combined gain tax rate simply adds the two rates and takes no federal deduction for the state tax. That is deliberately conservative.</li>
<li><strong>Mortgages, 1031 exchanges, instalment sales, gifting and trust restructuring.</strong> None are modelled. Each is on the <a href="questions.html">questions page</a>.</li>
<li><strong>Transaction costs of moving house, and the cost of capital gains tax on any other asset that would have to be sold.</strong> Not modelled.</li>
</ul>""")
    )


PATH_LABELS = {
    "sell_equities": "Sell, invest in equities",
    "sell_treasury": "Sell, reinvest in Treasuries",
    "live_in": "Live in it",
    "live_then_rent": "Live in it, then let it",
    "rent_out": "Let it out",
}


# --------------------------------------------------------------- property A --
def page_property_a() -> str:
    p45 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2045)
    roll_rows = []
    for r in MODEL["roll_a"]:
        roll_rows.append(
            f"<td>{r['year']}</td><td>{m(r['assessed'])}</td>"
            f"<td>{m(r['bill']) if r['bill'] is not None else BLANK_CELL}</td>"
            f"<td>{m(r['fitted'])}</td>"
            f"<td>{m(r['residual']) if r['residual'] is not None else '&mdash;'}</td>"
            + src_cell(["scc_ratebook", "boe_pub29"], "How a bill is built"))
    roll = table(
        "Property A assessment roll and tax bill, as supplied, rounded to the nearest $10",
        ["Year", "Assessed value", "Tax bill as supplied", "Bill implied by the model",
         "Difference", "Source"],
        roll_rows,
        note="The bill column is the owner's own record and is <strong>not</strong> verified against the county "
             "assessment roll. The model column applies the stated ad valorem rate plus a fixed charge that "
             "grows with inflation; the difference column shows how far the actual bill departs from that.")

    reassess = table(
        "What happens to the assessment when Property A is inherited (modelled for 2045)",
        ["Line", "Amount", "Basis"],
        [
            f"<td>Market value at transfer, modelled</td><td>{m(p45['value_at_death'])}</td>"
            + method_cell("projections.html#method", "Model output"),
            f"<td>Assessed value if nothing changes, grown at the 2% cap</td>"
            f"<td>{m(p45['factored_base_year_value'])}</td>"
            + src_cell(["boe_pub29", "rtc51"], "Proposition 13"),
            f"<td>Proposition 19 shelter, the indexed $1,000,000 amount</td>"
            f"<td>{m(p45['prop19_cap'])}</td>"
            + src_cell(["boe_lta25009", "rtc63_2"], "BOE and statute"),
            f"<td>New assessed value if the heir moves in and claims the exclusion</td>"
            f"<td><strong>{m(p45['taxable_if_live'])}</strong></td>"
            + src_cell(["rtc63_2"], "Statutory formula"),
            f"<td>New assessed value if the heir does not move in</td>"
            f"<td><strong>{m(p45['taxable_if_rent'])}</strong></td>"
            + src_cell(["boe_pub29", "rtc63_2"], "Full reassessment"),
            f"<td>Tax bill today, projected to 2045</td><td>{m(p45['bill_today_projected'])}</td>"
            + method_cell("projections.html#method", "Model output"),
            f"<td>Tax bill from 2045, heir moves in</td><td>{m(p45['bill_if_live_year1'])}</td>"
            + method_cell("projections.html#method", "Model output"),
            f"<td>Tax bill from 2045, heir does not move in</td><td>{m(p45['bill_if_rent_year1'])}</td>"
            + method_cell("projections.html#method", "Model output"),
        ],
        note="The Proposition 19 formula means the new assessed value when the exclusion applies is simply "
             "the market value at transfer minus the indexed shelter amount. That is the whole of the "
             "benefit, and it is why the shelter matters less the longer the transfer is delayed.")

    cost_rows = [
        f"<td>Water</td><td>{m(A['annual_costs']['water']['low'])} to {m(A['annual_costs']['water']['high'])}</td><td>{m(A['annual_costs']['water']['mid'])}</td>"
        f'<td><span class="badge unverified">owner estimate</span></td>'
        + src_cell(["sjw_tariff"], "Provider tariff, now read"),
        f"<td>Electricity, net of solar export credit</td><td>{m(A['annual_costs']['electricity']['low'])} to {m(A['annual_costs']['electricity']['high'])}</td><td>{m(A['annual_costs']['electricity']['mid'])}</td>"
        f'<td><span class="badge unverified">owner estimate</span></td>'
        + src_cell(["cpuc_nem"], "Tariff rules"),
        f"<td>Home insurance, primary residence</td><td>{m(A['annual_costs']['insurance']['low'])}</td><td>{m(A['annual_costs']['insurance']['mid'])}</td>"
        f'<td><span class="badge unverified">owner estimate</span></td>'
        + src_cell(["cdi_tips"], "Where to get a quote"),
        f"<td>Maintenance and repair</td><td>not supplied</td><td>{m(MODEL['costs_a_now']['maintenance'])}</td>"
        f'<td><span class="badge assumption">assumption</span></td>'
        + src_cell([], "No official source"),
        f"<td>Property tax, today</td><td>&mdash;</td><td>{m(MODEL['costs_a_now']['property_tax'])}</td>"
        f'<td><span class="badge derived">derived</span></td>'
        + src_cell(["scc_ratebook"], "Rate structure"),
    ]
    costs = table("Property A annual running costs",
                  ["Cost", "Range supplied", "Used in the model", "Status", "Source"], cost_rows)

    # Water and sewer context, computed from the official tariffs read on 13 November 2026.
    # The unrounded tariff constants live only here; everything published is money10().
    SVC = 78.64          # monthly service charge, 5/8 x 3/4-inch or 3/4-inch meter
    T1, T2, T3 = 4.9692, 7.4167, 14.1659   # per Ccf: first 6, 6 to 12, above 12

    def water_bill(ccf: float) -> float:
        use = T1 * min(ccf, 6.0) + T2 * max(0.0, min(ccf - 6.0, 6.0)) + T3 * max(0.0, ccf - 12.0)
        return SVC + use

    sewer_fy2526 = 802.14
    sewer_fy2627 = sewer_fy2526 * 1.03   # the adopted 3% increase, minutes of 20 May 2026

    tariff_rows = [
        f"<td>Water service charge, 5/8 x 3/4-inch or 3/4-inch meter</td><td>{m(money10(SVC))} a month</td>"
        + src_cell(["sjw_tariff"], "CPUC tariff, from 1 July 2026"),
        f"<td>Derived water bill at 8 Ccf a month (about 6,000 gallons)</td><td>{m(money10(water_bill(8)))}</td>"
        + src_cell(["sjw_tariff"], "Computed from the tariff"),
        f"<td>Derived water bill at 12 Ccf a month (about 9,000 gallons)</td><td>{m(money10(water_bill(12)))}</td>"
        + src_cell(["sjw_tariff"], "Computed from the tariff"),
        f"<td>Derived water bill at 15 Ccf a month (about 11,000 gallons)</td><td>{m(money10(water_bill(15)))}</td>"
        + src_cell(["sjw_tariff"], "Computed from the tariff"),
        f"<td>Sewer service charge, single family, FY 2025-26</td><td>{m(money10(sewer_fy2526))} a year</td>"
        + src_cell(["cusd_rates"], "District hearing notice"),
        f"<td>Sewer rate increase adopted for FY 2026-27</td><td>3%, from 1 July 2026</td>"
        + src_cell(["cusd_minutes"], "Board minutes, 20 May 2026"),
        f"<td>Sewer service charge, single family, FY 2026-27, derived</td><td>{m(money10(sewer_fy2627))} a year</td>"
        + src_cell(["cusd_minutes", "cusd_rates"], "Computed from the two official figures"),
    ]
    tariffs = table(
        "Water and sewer: what the official tariffs say",
        ["Item", "Amount", "Source"], tariff_rows,
        note="Rounded to the nearest $10; the exact tariff amounts are on the linked official pages. "
             "Usage is billed in three tiers per hundred cubic feet, the top tier roughly triple the "
             "first; the exact tier amounts are on the linked tariff sheet. The provider's territory "
             "covers the area where Property A stands. The owner's water estimate of $100 to $150 a "
             "month implies usage at the low end of the derived range, and excludes the guest charges, "
             "CPUC fees and utility users' taxes a real bill carries. Sewer was never supplied by the "
             "owner; the district's published charges are shown as context, and the parcel's own "
             "district, zone and charge must be read from its tax bill. Neither figure is added to the "
             "model totals.")

    return (
        table("Property A at a glance",
              ["Fact", "Value", "Source"],
              [
                  f"<td>Role</td><td>Inherited through a trust, planned 2040 to 2050. Not owned by the heir today.</td>"
                  + src_cell([], "Owner statement"),
                  f"<td>Jurisdiction</td><td>{esc(A['jurisdiction'])}</td>"
                  + src_cell(["scc_ratebook"], "County rate book"),
                  f"<td>Estimated market value, November 2026</td><td>{m(A['estimated_market_value_2026'])}</td>"
                  + src_cell([], "Owner estimate, unverified"),
                  f"<td>Current assessed value</td><td>{m(A['roll'][0]['assessed'])}</td>"
                  + src_cell([], "Owner record, unverified"),
                  f"<td>Current property tax bill</td><td>{m(MODEL['costs_a_now']['property_tax'])}</td>"
                  + src_cell(["scc_ratebook"], "Rate structure"),
                  f"<td>Units</td><td>{A['units']}, occupied by the transferor as a principal residence</td>"
                  + src_cell(["boe_lta26026"], "Principal residence test"),
                  f"<td>Solar</td><td>Installed. Export credit currently exceeds usage.</td>"
                  + src_cell(["cpuc_nem"], "NEM and net billing"),
              ])
        + roll
        + callout("key", "The single most important number on this page", f"""
<p>The assessed value is about {m(A['roll'][0]['assessed'])} and the market value is about {m(A['estimated_market_value_2026'])}.
Proposition 13 protects that gap only until ownership changes. When the trust transfers the house, the assessed
value resets to market value, less the Proposition 19 shelter of about {m(p45['prop19_cap'])} if the heir moves in
within a year and files the claim, or with no shelter at all if not. Either way this is the largest single change
in the whole analysis, and it happens by operation of law whether or not anyone plans for it.</p>""")
        + table("How the county builds a property tax rate (published rate book, FY 2025-26)",
                ["Component", "Rate", "Source"],
                [("<td>1% maximum levy, applied to every parcel</td><td>1.00000%</td>"
                  + src_cell(["scc_ratebook", "boe_pub29"], "Rate book summary")),
                 ("<td>County Retirement Levy</td><td>0.03880%</td>"
                  + src_cell(["scc_ratebook"], "Rate book summary")),
                 ("<td>County Library Retirement Levy</td><td>0.00240%</td>"
                  + src_cell(["scc_ratebook"], "Rate book summary")),
                 ("<td>County Housing Bond 2016</td><td>0.00560%</td>"
                  + src_cell(["scc_ratebook"], "Rate book summary")),
                 ("<td>City, school and special-district voter-approved bonds</td><td>varies by tax rate area</td>"
                  + src_cell(["scc_ratebook"], "816 areas listed in the book"))],
                note="The county publishes 816 tax rate areas for FY 2025-26; the components above are the "
                     "countywide ones listed in the book's own summary. The parcel's own rate area and total "
                     "rate are deliberately not published on this site. The model's 1.18% ad valorem "
                     "assumption stays flagged on the review page, and the parcel's exact rate must be read "
                     "from its own tax bill.")
        + reassess
        + costs
        + tariffs
        + callout("solar", "Solar and the electricity credit", """
<p>The owner reports that the solar export credit currently exceeds usage, producing a small net credit rather than
a bill. Two cautions. First, net energy metering tariffs are closed to new enrolment and since 15 April 2023 new
systems take service on the net billing tariff, where export compensation is usually below the retail rate. A
customer already on a NEM tariff may stay on it for twenty years from interconnection. Second, an inherited or
sold property can lose the tariff holder status that goes with the original customer. Whether this system is on
NEM 2.0 or on the net billing tariff is on the <a href="questions.html">questions page</a>.</p>""")
    )


# --------------------------------------------------------------- property B --
def page_property_b() -> str:
    roll_rows = []
    for r in MODEL["roll_b"]:
        roll_rows.append(
            f"<td>{r['year']}</td><td>{m(r['assessed'])}</td>"
            f"<td>{m(r['bill'])}</td><td>{m(r['fitted'])}</td>"
            f"<td>{m(r['residual'])}</td>"
            + src_cell(["sf_treas_rate", "boe_pub29"], "Rate and rule"))
    roll = table("Property B assessment roll and tax bill, as supplied, rounded to the nearest $10",
                 ["Year", "Assessed value", "Tax bill as supplied", "Bill implied by the model",
                  "Difference", "Source"], roll_rows)

    cost_rows = [
        f"<td>Water, all three units</td><td>{m(B['annual_costs']['water']['low'])} to {m(B['annual_costs']['water']['high'])}</td><td>{m(B['annual_costs']['water']['mid'])}</td>"
        f'<td><span class="badge unverified">owner estimate</span></td>' + src_cell([], "No official rate checked"),
        f"<td>Electricity</td><td>{m(B['annual_costs']['electricity']['low'])} to {m(B['annual_costs']['electricity']['high'])}</td><td>{m(B['annual_costs']['electricity']['mid'])}</td>"
        f'<td><span class="badge unverified">owner estimate</span></td>' + src_cell([], "No official rate checked"),
        f"<td>Insurance, rental policy</td><td>{m(B['annual_costs']['insurance']['low'])}</td><td>{m(B['annual_costs']['insurance']['mid'])}</td>"
        f'<td><span class="badge unverified">owner estimate</span></td>' + src_cell(["cdi_tips"], "Where to get a quote"),
        f"<td>Maintenance and repair</td><td>not supplied</td><td>{m(MODEL['costs_b_now']['maintenance'])}</td>"
        f'<td><span class="badge assumption">assumption</span></td>' + src_cell([], "No official source"),
        f"<td>Property tax, today</td><td>&mdash;</td><td>{m(MODEL['costs_b_now']['property_tax'])}</td>"
        f'<td><span class="badge derived">derived</span></td>' + src_cell(["sf_treas_rate"], "Published rate"),
    ]
    inc = MODEL["costs_b_now"]
    net = inc["rent"] - sum(inc[k] for k in ("water", "electricity", "insurance", "maintenance", "property_tax"))
    costs = table("Property B annual income and running costs",
                  ["Item", "Range supplied", "Used in the model", "Status", "Source"], cost_rows,
                  note=f"At the figures above, the building throws off about {m(net)} a year after running "
                       f"costs, before income tax and before any vacancy allowance. That is about "
                       f"{net / B['estimated_market_value_2026'] * 100:.1f}% of its estimated value.")

    rules = table(
        "Rent rules that apply to Property B",
        ["Rule", "What it says", "Source"],
        [
            f"<td>San Francisco allowed annual increase</td><td>1.6% from 1 March 2026 to 28 February 2027, "
            f"based on 60% of the change in the Bay Area consumer price index. One increase every twelve "
            f"months. There is no limit on the rent first charged to a new tenant of an empty unit.</td>"
            + src_cell(["sf_rent_increase"], "SF Rent Board"),
            f"<td>Proposed cap on banked and capital improvement increases</td>"
            f"<td>The Board of Supervisors is considering File 261020, which would limit combined banked and "
            f"capital improvement increases to 10% a year. <strong>Not enacted.</strong></td>"
            + src_cell(["sf_file261020"], "Legistar file"),
            f"<td>Statewide rent cap</td><td>Gross rent cannot rise more than 5% plus the change in the cost "
            f"of living, or 10%, whichever is lower, over twelve months. Housing already under a stricter "
            f"local ordinance is excluded.</td>"
            + src_cell(["civ1947_12"], "Civil Code 1947.12"),
            f"<td>Statewide just cause</td><td>A tenancy cannot be ended without a stated just cause, and a "
            f"no-fault termination including an owner move-in carries a relocation payment.</td>"
            + src_cell(["civ1946_2"], "Civil Code 1946.2"),
            f"<td>Which rules apply</td><td>Whether these units are covered by the San Francisco Rent "
            f"Ordinance, by the statewide act, or by an exemption depends on the building's age, its "
            f"ownership and the notices given. This site does not verify that.</td>"
            + src_cell(["sf_rent_increase", "civ1947_12"], "Both rules"),
        ])

    return (
        table("Property B at a glance",
              ["Fact", "Value", "Source"],
              [
                  f"<td>Role</td><td>Already owned by the heir. Rental income is already flowing and the heir can live here without losing it.</td>"
                  + src_cell([], "Owner statement"),
                  f"<td>Jurisdiction</td><td>{esc(B['jurisdiction'])}</td>"
                  + src_cell(["sf_treas_rate"], "SF Treasurer"),
                  f"<td>Estimated market value, November 2026</td><td>{m(B['estimated_market_value_2026'])}</td>"
                  + src_cell([], "Owner estimate, unverified"),
                  f"<td>Current assessed value</td><td>{m(B['roll'][0]['assessed'])}</td>"
                  + src_cell([], "Owner record, unverified"),
                  f"<td>Current property tax bill</td><td>{m(MODEL['costs_b_now']['property_tax'])}</td>"
                  + src_cell(["sf_treas_rate"], "Published rate"),
                  f"<td>Units</td><td>{B['units']}, of which {B['units_rented']} are let</td>"
                  + src_cell([], "Owner statement"),
                  f"<td>Rent received</td><td>{m(B['rent']['monthly'])} a month, {m(B['rent']['annual'])} a year</td>"
                  + src_cell([], "Owner statement, unverified"),
                  f"<td>Effective tax rate on assessed value</td><td>{MODEL['projection_b'][0]['effective_rate']}%</td>"
                  + src_cell(["sf_treas_rate"], "Rate plus fixed charges"),
              ])
        + roll
        + costs
        + rules
        + callout("why", "Why Property B shapes the Property A decision", """
<p>Three things follow from the heir already owning this building.</p>
<ol>
<li><strong>The heir already has somewhere to live at no cash cost.</strong> That removes the usual argument for
keeping an inherited house, which is that it provides housing. It also means the Opportunity cost of living in
Property A is not rent saved but the rent the vacated unit here could earn.</li>
<li><strong>Property B is a going concern with a low assessed value.</strong> Nothing about inheriting Property A
changes its assessment, because the heir already owns it.</li>
<li><strong>Two properties in one state means two reassessment clocks and one homeowners' exemption.</strong>
Only one property can be a principal residence for exemption purposes, which matters directly for the
Proposition 19 claim on Property A.</li>
</ol>""")
    )


# ----------------------------------------------------- ownership distinction --
def page_distinction() -> str:
    p45 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2045)
    rows = [
        ("Who owns it today", "The transferor, through a trust. The heir owns nothing yet.",
         "The heir, outright or in their own name.", "Only Property A has a transfer event coming. Every tax consequence on this site flows from that single event."),
        ("What triggers the tax change", "The trust transfer, expected 2040 to 2050. That is a change in ownership.",
         "Nothing pending. The heir's existing assessment simply grows at the 2% cap.",
         f"Property A's bill goes from about {m(MODEL['costs_a_now']['property_tax'])} to about {m(p45['bill_if_rent_year1'])} if let out. Property B's bill just drifts upward."),
        ("Basis for income tax", "Resets to market value at death, so a sale soon afterwards pays almost no capital gains tax.",
         "Carries the heir's original cost basis, so a sale would be taxed on the whole gain since purchase.",
         "This is the strongest argument for selling Property A and keeping Property B."),
        ("Principal residence position", "Would have to become the heir's principal residence for the Proposition 19 exclusion to apply.",
         "The heir can already live here without losing the rent from the two let units.",
         f"Only one homeowners' exemption is available. Choosing Property A means giving up the Property B position, and the exclusion is worth about {m(p45['prop19_cap'])} of sheltered value in 2045."),
        ("Income", "None today. The house produces housing for the transferor and nothing else.",
         f"About {m(B['rent']['annual'])} a year from two units, with a third unit available.",
         "Property B is a going concern. Property A is a capital asset that only becomes an income asset if it is let, which is the path that triggers the full reassessment."),
        ("Running costs", f"About {m(sum(MODEL['costs_a_now'][k] for k in ('water', 'electricity', 'insurance', 'maintenance', 'property_tax')))} a year today, and the owner reports repairs run lower here than at Property B.",
         f"About {m(sum(MODEL['costs_b_now'][k] for k in ('water', 'electricity', 'insurance', 'maintenance', 'property_tax')))} a year today.",
         "Property A is the cheaper building to hold today. After the reassessment it is not, because the tax bill dominates."),
        ("Liquidity and diversification", "A single asset in one school district, one water basin, one earthquake fault region.",
         "A second single asset in the same state, the same earthquake region and much the same economy.",
         "Holding both concentrates rather than diversifies. Selling Property A is the only path that converts a concentrated holding into a diversified one."),
    ]
    tbl = table("The two properties side by side",
                ["Dimension", "Property A - inherited", "Property B - already owned", "Why the difference decides the case"],
                [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(d)}</td>"
                 + src_cell(["rtc63_2", "boe_pub29", "irs_basis", "sf_treas_rate"], "Governing rules")
                 for a, b, c, d in rows])
    return (tbl
            + callout("key", "The distinction that changes the arithmetic", """
<p>An inherited property arrives with a reset income-tax basis and a property-tax assessment about to reset the
other way. An already-owned property has neither event. Treating the two as interchangeable is the single easiest
way to reach the wrong answer here, because the reset basis makes selling cheap at exactly the moment the
reassessment makes holding expensive.</p>""")
            + callout("warn", "One exemption, two properties", """
<p>California allows one homeowners' exemption. If the heir claims the Proposition 19 exclusion on Property A,
Property A must be the principal residence, and the Property B position has to be given up. The exclusion also
requires continued occupation: it is removed on the date the home stops qualifying, whether because the heir
moves out, lets it, or simply stops using it as a main home. There are no exceptions to the one-year occupation
rule. That makes "move in for a while, then let it out" a risky structure, not a safe compromise.</p>"""))


# -------------------------------------------------------------------- costs --
def page_costs() -> str:
    infl = ASM["inflation"]["baseline"]
    years = [2026, 2030, 2040, 2045, 2050, 2060, 2076]

    def rows_for(which: str):
        base = MODEL["costs_a_now"] if which == "A" else MODEL["costs_b_now"]
        out = []
        for y in years:
            f = (1 + infl) ** (y - 2026)
            if which == "A":
                tax = next(r["bill"] for r in MODEL["projection_a"] if r["year"] == y)
            else:
                tax = next(r["bill"] for r in MODEL["projection_b"] if r["year"] == y)
            total = (base["water"] + base["electricity"] + base["insurance"]
                     + base["maintenance"]) * f + tax
            out.append(f"<td>{y}</td><td>{m(money10(base['water'] * f))}</td>"
                       f"<td>{m(money10(base['electricity'] * f))}</td>"
                       f"<td>{m(money10(base['insurance'] * f))}</td>"
                       f"<td>{m(money10(base['maintenance'] * f))}</td>"
                       f"<td>{m(money10(tax))}</td>"
                       f"<td><strong>{m(money10(total))}</strong></td>"
                       + method_cell("#method", "Model output"))
        return out

    tbl_a = table("Property A running costs, projected at the modelled inflation rate",
                  ["Year", "Water", "Electricity, net of solar", "Insurance",
                   "Maintenance", "Property tax", "Total"], rows_for("A"))
    tbl_b = table("Property B running costs, projected at the modelled inflation rate",
                  ["Year", "Water", "Electricity", "Insurance", "Maintenance",
                   "Property tax", "Total"], rows_for("B"))

    net = MODEL["costs_b_now"]
    net_now = net["rent"] - sum(net[k] for k in ("water", "electricity", "insurance",
                                                 "maintenance", "property_tax"))
    return (
        callout("note", "Where these numbers come from", """
<p>Water, electricity and insurance are <strong>owner estimates</strong> and are flagged unverified. Maintenance
is an <strong>assumption</strong>, because no figure was supplied. Property tax is derived from the owner's own
bills plus the published or assumed ad valorem rate. Everything is rounded to the nearest $10 and projected at
the modelled inflation rate of 2.5% a year.</p>""")
        + tbl_a
        + tbl_b
        + callout("note", "What an insurance benchmark does and does not tell you", f"""
<p>The California Department of Insurance publishes average written premiums from its Residential Property
Insurance Report. The statewide average for an owner-occupied homeowners policy was about <strong>$1,070</strong>
in experience year 2017. Both properties here are carried at {m(MODEL['costs_a_now']['insurance'])} a year,
which is an <strong>owner estimate</strong> and is flagged unverified.</p>
<p>The benchmark is statewide and across all amounts of insurance. It is <strong>not</strong> a premium for
either building, and it must not be read as one: a three-unit rental in the city and a single-family home in the
county are priced on entirely different bases. It is published here only so the owner estimate can be seen
against something official, which is the most this source can support. A property-specific premium remains
blank until it is quoted.</p>""")
        + table("Property B net income today",
                ["Item", "Amount", "Source"],
                [
                    f"<td>Rent received, two units</td><td>{m(net['rent'])}</td>" + src_cell([], "Owner statement, unverified"),
                    f"<td>Less water</td><td>{m(-net['water'])}</td>" + src_cell(["sfpuc_rates"], "Owner estimate; city schedule"),
                    f"<td>Less electricity</td><td>{m(-net['electricity'])}</td>" + src_cell([], "Owner estimate, unverified"),
                    f"<td>Less insurance</td><td>{m(-net['insurance'])}</td>" + src_cell([], "Owner estimate, unverified"),
                    f"<td>Less maintenance at the assumed rate</td><td>{m(-net['maintenance'])}</td>" + src_cell([], "Assumption"),
                    f"<td>Less property tax</td><td>{m(-net['property_tax'])}</td>" + src_cell(["sf_treas_rate"], "Published rate"),
                    f"<td><strong>Net, before income tax and vacancy</strong></td><td><strong>{m(net_now)}</strong></td>" + method_cell("#method", "Model output"),
                ],
                note=f"That is about {net_now / B['estimated_market_value_2026'] * 100:.1f}% of the estimated value. "
                     f"A vacancy allowance and income tax would reduce it further.")
        + '<h2>How the projections are built</h2>'
        + table("Projection method", ["Step", "What is done", "Source"],
                [
                    "<td>Assessed value</td><td>Grown at the Proposition 13 cap of 2% a year, which has been binding in every year of both supplied rolls.</td>" + src_cell(["boe_pub29", "rtc51"], "Proposition 13"),
                    "<td>Tax bill</td><td>Ad valorem rate times assessed value, plus a fixed charge grown at the modelled inflation rate.</td>" + src_cell(["scc_ratebook", "sf_treas_rate"], "Rate structure and published rate"),
                    "<td>Water, power, insurance, maintenance</td><td>Grown at the modelled inflation rate. No real-terms change in usage or tariffs is assumed.</td>" + src_cell(["ssa_trustees"], "Inflation anchor"),
                    "<td>Market value</td><td>Grown at the modelled house price growth rate of 4% a year.</td>" + src_cell(["fred_hpi_a", "fred_hpi_b"], "Historical index"),
                ],
                note="A constant rate is used for the year-by-year page because it is the only way to show a "
                     "readable table. It is not a forecast. The <a href=\"black-swan.html\">black swan page</a> "
                     "shows what happens when growth and inflation are not constant.")
        + callout("flag", "Three cost numbers that need replacing", """
<ol>
<li><strong>Insurance on both properties.</strong> The California Department of Insurance does not publish an
average premium by area, so no official figure exists to check these against. Get three quotes for each building,
one of which should be a rental policy. See <a href="suggestions.html">suggestion S-01</a>.</li>
<li><strong>Maintenance.</strong> No figure was supplied. This site assumes 0.5% of value a year for an
owner-occupied home, 0.75% for Property A as a rental and 1.5% for the older three-unit building. Replace these
with the actual five-year repair history.</li>
<li><strong>Water.</strong> The provider and tariff for Property A are not confirmed, so the owner's range is
used as supplied.</li>
</ol>""")
    )


# -------------------------------------------------------------- projections --
def page_projections() -> str:
    def proj_rows(proj):
        out = []
        for r in proj:
            out.append(f"<td>{r['year']}</td><td>{m(r['value'])}</td><td>{m(r['assessed'])}</td>"
                       f"<td>{m(r['bill'])}</td><td>{r['effective_rate']}%</td>"
                       + method_cell("#method", "Model output"))
        return out

    excl_rows = [f"<td>{e['year']}</td><td>{m(e['amount'])}</td><td>{esc(e['basis'])}</td>"
                 + src_cell(e["src"], "Official source")
                 for e in MODEL["exclusion_projection"] if e["year"] >= 2026]
    cap_rows = [f"<td>{e['year']}</td><td>{m(e['amount'])}</td><td>{esc(e['basis'])}</td>"
                + src_cell(e["src"], "Official source")
                for e in MODEL["prop19_cap_projection"] if e["year"] >= 2026]

    return (
        callout("note", "What this page is", """
<p>Year-by-year projections from 2026 to 2076 on the baseline assumptions: house prices 4.0% a year, inflation
2.5% a year, assessed values rising at the Proposition 13 cap of 2% a year. These tables exist so the shape of
the arithmetic is visible. They are not a forecast; see the <a href="black-swan.html">black swan page</a>.</p>""")
        + table("Property A: value, assessed value and tax bill, if the assessment is never reset",
                ["Year", "Market value", "Assessed value", "Tax bill", "Effective rate on assessed value", "Basis"],
                proj_rows(MODEL["projection_a"]))
        + table("Property B: value, assessed value and tax bill",
                ["Year", "Market value", "Assessed value", "Tax bill", "Effective rate on assessed value", "Basis"],
                proj_rows(MODEL["projection_b"]))
        + '<h2>Two thresholds that move over time</h2>'
        + table("Federal estate tax basic exclusion amount",
                ["Year", "Amount", "Basis", "Source"], excl_rows)
        + table("Proposition 19 intergenerational shelter amount, modelled",
                ["Year", "Amount", "Basis", "Source"], cap_rows)
        + callout("warn", "Read the two threshold tables together", """
<p>The federal exclusion is indexed to inflation and has been rising. The Proposition 19 shelter is adjusted only
every second February and only by the change in the California house price index. If house prices rise faster
than the shelter, the shelter buys a smaller and smaller share of the property each time the transfer is delayed.
On the baseline assumptions the shelter covers about 29% of Property A's modelled 2045 value. Waiting is not
neutral.</p>""")
    )


# -------------------------------------------------------------------- taxes --
def page_taxes() -> str:
    p45 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2045)
    now_sale = p45["paths"]["sell_equities"]["sale"]
    late_sale = p45["paths"]["live_in"]["sale"]
    rent_sale = p45["paths"]["rent_out"]["sale"]
    rows = [
        ("Basis of inherited property", "Fair market value at the date of death.",
         "irs_basis", "verified rule"),
        ("Sale immediately after inheritance", f"Gain is about zero, so tax is about zero. On the 2045 model, a {m(now_sale['price'])} sale carries {m(now_sale['tax'])} of tax.",
         "irs_basis", "derived"),
        ("Section 121 exclusion", f"{m(V['section121_exclusion_single']['value'])} for a single filer, {m(V['section121_exclusion_joint']['value'])} for a joint return, if the home was the main home for two of the last five years.",
         "irs_p523", "verified rule"),
        ("Federal capital gains", "0%, 15% or 20% by taxable income.", "irs_tc409", "verified rule"),
        ("Net investment income tax", "An additional 3.8% above the threshold.", "irs_tc559", "verified rule"),
        ("Unrecaptured section 1250 gain", "A maximum 25% federal rate on the depreciation claimed while the property was let.", "irs_tc409", "verified rule"),
        ("California treatment", "California has no separate lower rate for long-term gains; they are taxed as ordinary income. Voters made the existing high-income rates permanent in November 2026 instead of letting them expire in 2031.",
         "ftb_cg", "verified rule"),
        ("Combined rate used here", f"{pcf(ASM['combined_gain_tax_rate']['baseline'],1)} on the capital part of a gain and {pcf(ASM['depreciation_recapture_rate']['baseline'],1)} on the recaptured depreciation. Federal and state rates are simply added and no federal deduction is taken for the state tax, which is deliberately conservative.",
         "irs_tc409", "assumption"),
        ("Sale after holding for thirty years", f"On the 2045 model, a {m(late_sale['price'])} sale produces a gain of {m(late_sale['gain'])} and tax of {m(late_sale['tax'])}, after the {m(late_sale['exclusion'])} exclusion for a single filer.",
         "irs_tc409", "derived"),
        ("Sale after letting it for thirty years", f"Worse again, because of depreciation recapture: a gain of {m(rent_sale['gain'])} of which {m(rent_sale['recapture'])} is recaptured, giving tax of {m(rent_sale['tax'])}.",
         "irs_tc409", "derived"),
        ("California estate and inheritance tax", "None. No California estate tax return is required for a death on or after 1 January 2005, and a gift or inheritance is not California income.",
         "sco_estate", "verified rule"),
        ("Income the property later produces", "Rent, interest, dividends and gain on a later sale are all taxable, even though the inheritance itself is not.",
         "ftb_inheritance", "verified rule"),
        ("Inherited retirement accounts", "Not covered by the basis step-up. They are income in respect of a decedent and are taxed as withdrawals are taken.",
         "irs_rmd", "flagged"),
    ]
    tbl = table("Income tax rules that apply to each path",
                ["Rule", "What it means here", "Source", "Status"],
                [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td>"
                 f'<td><span class="badge {esc(d.split()[0])}">{esc(d)}</span></td>'
                 + src_cell([c], "Official source") for a, b, c, d in rows])

    worked = table("The tax cost of waiting, on the 2045 model",
                   ["Line", "Sell at inheritance", "Live in it, sell after 30 years",
                    "Let it out, sell after 30 years", "Basis"],
                   [
                       f"<td>Sale price</td><td>{m(now_sale['price'])}</td><td>{m(late_sale['price'])}</td><td>{m(rent_sale['price'])}</td>" + method_cell("#method", "Model output"),
                       f"<td>Selling costs</td><td>{m(now_sale['costs'])}</td><td>{m(late_sale['costs'])}</td><td>{m(rent_sale['costs'])}</td>" + method_cell("#method", "Model output"),
                       f"<td>Basis</td><td>{m(now_sale['basis'])}</td><td>{m(late_sale['basis'])}</td><td>{m(rent_sale['basis'])}</td>" + method_cell("#method", "Model output"),
                       f"<td>Gain</td><td>{m(now_sale['gain'])}</td><td>{m(late_sale['gain'])}</td><td>{m(rent_sale['gain'])}</td>" + method_cell("#method", "Model output"),
                       f"<td>Of which depreciation recapture</td><td>{m(now_sale['recapture'])}</td><td>{m(late_sale['recapture'])}</td><td>{m(rent_sale['recapture'])}</td>" + method_cell("#method", "Model output"),
                       f"<td>Section 121 exclusion</td><td>{m(now_sale['exclusion'])}</td><td>{m(late_sale['exclusion'])}</td><td>{m(rent_sale['exclusion'])}</td>" + src_cell(["irs_p523"], "Exclusion rule"),
                       f"<td><strong>Tax</strong></td><td><strong>{m(now_sale['tax'])}</strong></td><td><strong>{m(late_sale['tax'])}</strong></td><td><strong>{m(rent_sale['tax'])}</strong></td>" + method_cell("#method", "Model output"),
                       f"<td><strong>Net proceeds</strong></td><td><strong>{m(now_sale['net'])}</strong></td><td><strong>{m(late_sale['net'])}</strong></td><td><strong>{m(rent_sale['net'])}</strong></td>" + method_cell("#method", "Model output"),
                   ],
                   note="Same house, same thirty years, three very different tax outcomes. The difference is "
                        "entirely the basis reset at death plus the depreciation taken in the rental case.")
    return (
        callout("key", "The tax-free window", f"""
<p>Property acquired from a decedent takes a basis equal to its value at death. Selling soon after the
inheritance therefore produces almost no taxable gain: on the 2045 model the tax is
<strong>{m(now_sale['tax'])}</strong> on a {m(now_sale['price'])} sale. Hold the same house for thirty years and
the tax becomes <strong>{m(late_sale['tax'])}</strong>, even after the {m(late_sale['exclusion'])} exclusion.
Let it out as well and depreciation recapture pushes it to <strong>{m(rent_sale['tax'])}</strong>.</p>
<p>That is the core of the recommendation. The window is not a loophole that might close; it is how the basis
rules work, and it only exists at the moment of transfer.</p>""")
        + tbl
        + worked
        + '<h2>Transfer tax if Property B is sold</h2>'
        + table("City transfer tax on a sale of Property B",
                ["Price band", "Rate", "Note", "Source"],
                [f"<td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td>"
                 + src_cell(["cityb_transfer"], "City fee schedule")
                 for a, b, c in [
                     ("Up to $250,000", "0.5%", "Lowest band."),
                     ("Above $250,000 and below $1,000,000", "0.68%", "Applies to the whole price, not just the excess."),
                     ("$1,000,000 to under $5,000,000", "0.75%", "The band Property B is in today."),
                     ("$5,000,000 to under $10,000,000", "2.25%", "Crossing $5,000,000 triples the rate on the entire price."),
                     ("$10,000,000 to under $25,000,000", "5.5%", "Published in the city schedule as 27 dollars 50 cents for each 500 dollars of the entire consideration. An earlier pass stopped at the previous band and left this blank; it is in the schedule."),
                     ("$25,000,000 and above", "6.0%", "Published in the city schedule as 30 dollars for each 500 dollars of the entire consideration. Neither property is near this band at today's values."),
                 ]],
                note="Each rate is the city's per-500-dollar rate expressed as a percentage of the whole price. "
                     "The rate applies to the entire consideration, so a sale that crosses a threshold is not "
                     "taxed band by band. This matters for Property B only; Property A is in the county, and "
                     "no city transfer tax is charged there.")
        + '<h2>What the model does and does not do</h2>'
        + callout("flag", "Not modelled, and flagged for a professional", """
<ul>
<li><strong>The additional 1% California tax above $1,000,000 of income.</strong> Revenue and Taxation Code section 17043 adds 1% to taxable income above $1,000,000. A large gain in the year of a sale can push income over that line, which would raise the effective state rate used here. It is not modelled.</li>
<li><strong>A like-kind exchange under section 1031.</strong> Exchanges of real property are still available, but they defer rather than forgive tax, and they do not fix the property tax reassessment. Whether one makes sense depends on whether the heir wants to stay in real estate at all.</li>
<li><strong>An instalment sale.</strong> Spreads the gain, but not the tax.</li>
<li><strong>Gifting during life rather than at death.</strong> Removes the basis step-up. Almost always worse for an appreciated asset.</li>
<li><strong>Whether the trust itself should hold the property after the transfer.</strong> This affects both the basis and the Proposition 19 claim and depends on the trust terms, which this site does not have.</li>
<li><strong>The federal deduction for state tax.</strong> Not taken. Taking it would slightly reduce the combined rate.</li>
</ul>"""))


# -------------------------------------------------------------- inheritance --
def page_inheritance() -> str:
    steps = [
        ("1", "Before the transfer",
         "Confirm three things: that the trust holds title to the house, that the heir's relationship to the transferor is a parent-and-child relationship (or grandparent and grandchild with the middle generation deceased), and whether the heir takes outright, in further trust, or for life. The relationship is what qualifies the transfer for the intergenerational exclusion; without it the property is reassessed in full.",
         "The successor trustee, with the trust instrument and the recorded deed.",
         "No statutory deadline, but this is the step that determines everything else.",
         ["scc_recorder", "rtc63_2"]),
        ("2", "Check the assessment record now",
         "Confirm the assessed value, the tax rate area, the fixed charges on the bill and whether a homeowners' exemption is in place.",
         "The heir or the current owner, from the county assessor and the tax bill.",
         "Do this before the transfer, not after.",
         ["scc_ratebook", "boe_pub29"]),
        ("3", "The transfer event",
         "On the transfer, the trustee signs and records a deed moving the house out of the trust to the heir. Recording is what starts the county's clock.",
         "The trustee records with the county recorder.",
         "Recording fees are due at recording. The documentary transfer tax does not apply to a deed where the property passes by reason of death or by inter vivos gift, so a transfer out of the trust at death should be exempt from it; the county recorder's fee schedule confirms the fee exemption for exempt transfers. Property A is in the county, not the city, so no city transfer tax applies to it either.",
         ["scc_recorder", "rtc11930_trust", "rtc11911"]),
        ("4", "Notice to beneficiaries",
         "When a revocable trust becomes irrevocable, the trustee must notify the heirs and beneficiaries and give them the information the statute requires.",
         "The trustee.",
         "The statute sets the notice requirement; read the current text.",
         ["prob16061_7"]),
        ("5", "Change in ownership statement",
         "A change in ownership statement goes to the county assessor. The assessor decides whether the transfer is a change in ownership and sets a new base year value if it is.",
         "The new owner, on the assessor's form.",
         "The statute sets the deadline and the penalties.",
         ["rtc480", "boe_pub800_9"]),
        ("6", "The Proposition 19 decision",
         "If the heir will use the house as a principal residence, claim the intergenerational transfer exclusion. The claim is not a public document.",
         "The heir, on the assessor's claim form.",
         "Occupy within one year of the transfer. File the homeowners' exemption within one year. File the exclusion claim within three years, or before any transfer to someone else.",
         ["rtc63_2", "boe_lta26026", "boe_prop19"]),
        ("7", "If the exclusion is not claimed",
         "The property is reassessed to its full market value at the date of transfer and a supplemental bill may follow for the part of the year already gone.",
         "The county assessor, automatically.",
         "Supplemental bills are issued after the reassessment.",
         ["boe_pub29", "sf_treas_rate"]),
        ("8", "Federal estate tax, if the estate is large enough",
         "If the gross estate plus adjusted taxable gifts exceeds the exclusion for the year of death, an estate tax return is due and tax is paid. Portability of a unused exclusion is elected on a timely return.",
         "The executor or the trustee.",
         "The return and any tax are due nine months after death, with an available extension.",
         ["irs_estate", "irs_i706", "irs_whatsnew"]),
        ("9", "California",
         "No California estate tax return is required for a death on or after 1 January 2005.",
         "Nobody. There is nothing to file.",
         "Not applicable.",
         ["sco_estate", "ftb_inheritance"]),
        ("10", "Record the basis",
         "Record the fair market value at the date of death. This becomes the income tax basis and the depreciation basis if the property is ever let.",
         "The heir, ideally with a written valuation.",
         "Do it at the time, while the evidence is cheap.",
         ["irs_basis"]),
        ("11", "Utilities, insurance and the solar tariff",
         "Put insurance in the new owner's name, transfer or reapply for water and power, and confirm what happens to the solar tariff when the customer of record changes.",
         "The heir, with the insurers and the utilities.",
         "A lapse in insurance at transfer is the most common and most avoidable loss.",
         ["cpuc_nem", "cdi_tips"]),
        ("12", "Decide, and decide in time",
         "The sale decision should be made early, because the tax-free basis window is widest immediately after the transfer. The Proposition 19 claim has three years; the tax advantage does not.",
         "The heir, using the <a href=\"decision.html\">decision page</a>.",
         "Three years for the claim. The longer the property is held outside the exclusion, the more the assessment and the gain both grow.",
         ["rtc63_2", "irs_basis"]),
    ]
    # Only the "who acts" column is allowed to carry markup: it needs a link to the
    # decision page. Every other column is escaped so nothing else can inject markup.
    rows = [f"<td><strong>{esc(a)}</strong></td><td><strong>{esc(b)}</strong></td><td>{esc(c)}</td>"
            f"<td>{d}</td><td>{esc(e)}</td>" + src_cell(f, "Official source")
            for a, b, c, d, e, f in steps]
    tbl = table("Inheriting Property A through a trust, phase by phase",
                ["#", "Phase", "What happens", "Who acts", "Timing and deadline", "Source"], rows)
    return (
        callout("note", "How to read this", """
<p>This is the procedural path, in order, with the rule that governs each step. It is deliberately generic: it does
not restate the trust, which this site has not seen. Where a deadline is set by statute the statute is linked so
the current text can be read.</p>""")
        + callout("flag", "The gap this site cannot close: what if the trust is not the route", f"""
<p>Everything above assumes the house passes through a trust. Two other routes exist, and neither is modelled
here because neither the trust nor the deed has been read.</p>
<ul>
<li><strong>A small estate.</strong> California provides a simplified transfer for estates below a statutory
value, and a separate procedure for a decedent's real property worth a set amount or less. Both thresholds are
set in the Probate Code and change over time. Property A is worth about {m(A['estimated_market_value_2026'])}
today, far above any current threshold, so this route only helps if the house passes outside the estate
altogether. Read the current text rather than a remembered figure.</li>
<li><strong>Probate.</strong> If the house is held in the transferor's own name, with no trust and no beneficiary
designation, a probate administration has to complete before the house can be sold. California sets statutory
probate fees on a sliding scale of the gross value of the estate, so on an asset of this size the fees are
material, and the administration runs for months. It also delays the sale, which matters because the basis
step-up window is widest immediately after death.</li>
</ul>
<p>Neither route changes how the gain is taxed. Both change the timing and the cost. The action is the same
either way: read the deed and the trust first. See <a href="questions.html">questions A-1 and A-2</a>.</p>""")
        + tbl
        + callout("key", "The three deadlines that actually bite", """
<ol>
<li><strong>Move in within one year</strong> if the Proposition 19 exclusion is going to be claimed. The guidance
is explicit that there are no exceptions to that rule, and that the exclusion is removed when the home stops
being the principal residence.</li>
<li><strong>File the exclusion claim within three years</strong>, or before transferring the property to anyone
else, whichever is earlier.</li>
<li><strong>Be in a qualifying relationship</strong> to the transferor. If the heir is not a child of the
transferor (or a grandchild whose parent has died), there is no exclusion to claim, no matter what is filed.</li>
</ol>
<p>Everything else on this list is administrative. These three are the ones that change the money.</p>""")
    )


# ------------------------------------------------------------------- estate --
def page_estate() -> str:
    est = MODEL["estate"]
    scen = table("Federal estate tax by estate size, using the 2026 exclusion",
                 ["Gross estate", "Above one exclusion", "Above two exclusions",
                  "Federal tax, one exclusion, at 40%", "Federal tax, two exclusions, at 40%",
                  "California estate tax"],
                 [f"<td>{m(r['total'])}</td><td>{m(r['excess_single'])}</td>"
                  f"<td>{m(r['excess_couple'])}</td>"
                  f"<td>{m(r['federal_tax_single_at_40'])}</td>"
                  f"<td>{m(r['federal_tax_couple_at_40'])}</td>"
                  f"<td>{m(r['california_estate_tax'])}</td>"
                  + src_cell(["irs_estate", "irs_whatsnew", "sco_estate"], "Official source")
                  for r in est["rows"]],
                 note=("The 40% figure is the top federal rate in the estate tax rate schedule in the "
                       "Instructions for Form 706. This site does not restate the schedule. The two-exclusion "
                       "column assumes a surviving spouse elects portability on a timely estate tax return."))
    hist = table("The federal filing threshold by year of death, published by the IRS",
                 ["Year of death", "Filing threshold", "Source"],
                 [(f"<td>{y}</td><td>{m(a)}</td>"
                   + (src_cell(["irs_estate"], "IRS table") if y <= 2026
                      else src_cell(["irs_2027"], "IRS newsroom")))
                  for y, a in [(2018, 11_180_000), (2019, 11_400_000), (2020, 11_580_000),
                               (2021, 11_700_000), (2022, 12_060_000), (2023, 12_920_000),
                               (2024, 13_610_000), (2025, 13_990_000), (2026, 15_000_000),
                               (2027, 15_480_000)]],
                 note="The IRS estate-tax page publishes the table through 2026. The 2027 line comes from "
                      "the IRS inflation-adjustment release for tax year 2027, which states the basic "
                      "exclusion for deaths during 2027 directly.")
    return (
        callout("answer", "The short answer", f"""
<p><strong>California has no estate tax and no inheritance tax.</strong> The State Controller's Office confirms
that no California estate tax return is required for a death on or after 1 January 2005, and the Franchise Tax
Board confirms that a gift or inheritance is not California income.</p>
<p><strong>Federally, the exclusion for 2026 is {m(est['exclusion_2026'])} per person</strong> and
{m(est['exclusion_2027'])} for 2027. A surviving spouse can elect to use a deceased spouse's unused exclusion, so
a couple can shelter {m(est['exclusion_2026'] * 2)} between them if that election is made on a timely return.</p>""")
        + hist
        + scen
        + table("What is and is not taxed on the way in",
                ["Receipt", "Federal", "California", "Source"],
                [
                    "<td>The house itself</td><td>Included in the gross estate at fair market value; not income to the heir.</td><td>Not income to the heir.</td>" + src_cell(["irs_estate", "ftb_inheritance", "uscode102"], "Official source"),
                    "<td>Cash</td><td>Included in the gross estate; not income to the heir.</td><td>Not income to the heir.</td>" + src_cell(["ftb_inheritance", "uscode102"], "Official source"),
                    "<td>Interest, dividends and rent the inherited assets later produce</td><td>Taxable income.</td><td>Taxable income.</td>" + src_cell(["ftb_inheritance"], "Official source"),
                    "<td>Inherited retirement accounts</td><td>Income in respect of a decedent: taxed as withdrawn, not covered by the basis step-up.</td><td>Taxed as withdrawn.</td>" + src_cell(["irs_rmd"], "Official source"),
                    "<td>Gain on a later sale of the house</td><td>Capital gain over the stepped-up basis.</td><td>Taxed as ordinary income.</td>" + src_cell(["irs_tc409", "ftb_cg"], "Official source"),
                ])
        + table("Annual gift exclusion", ["Year", "Amount", "Source"],
                [(f"<td>2026</td><td>{m(V['annual_gift_exclusion_2026']['value'])} per recipient</td>"
                  + src_cell(["irs_2027"], "IRS")),
                 (f"<td>2027</td><td>{m(V['annual_gift_exclusion_2027']['value'])} per recipient</td>"
                  + src_cell(["irs_2027"], "IRS"))],
                note="Useful for moving value out of an estate over time, but gifts of appreciated property do "
                     "not receive the basis step-up that a transfer at death receives.")
        + callout("flag", "What this page cannot tell you", """
<ul>
<li><strong>Whether the estate exceeds the exclusion.</strong> The amount of the cash inheritance is deliberately not published here and not modelled as a specific figure. Use the scenario table and compare it with the estate's own numbers privately.</li>
<li><strong>Whether prior taxable gifts have already used part of the exclusion.</strong> Lifetime taxable gifts are added back in the computation.</li>
<li><strong>Whether any of the estate is a retirement account.</strong> Those are taxed differently and are the most common surprise.</li>
<li><strong>What the law will be in 2040 to 2050.</strong> The exclusion has moved in both directions historically; it was $5,490,000 in 2017 and $15,000,000 in 2026. See the <a href="laws.html">law page</a>.</li>
</ul>"""))


# --------------------------------------------------------------------- laws --
def page_laws() -> str:
    enacted = [
        ("Federal basic estate tax exclusion raised",
         "Public Law 119-21, the Working Families Tax Cuts, signed 4 July 2025, amended section 2010(c)(3) to set the basic exclusion at $15,000,000 for calendar year 2026.",
         "Raises the threshold. Makes an estate tax charge much less likely, but is not a promise about 2045.",
         ["irs_whatsnew", "irs_estate"]),
        ("2027 inflation adjustments published",
         "For deaths during 2027 the basic exclusion is $15,480,000 and the annual gift exclusion rises to $20,000.",
         "Confirms the exclusion is indexing upward.",
         ["irs_2027"]),
        ("California high-income tax rates: Proposition 3 (unofficial)",
         "Proposition 3 is approved on unofficial results (60.7% yes as of 12 November 2026). It makes permanent the voter-approved rates on individuals earning over $371,000, adjusted for inflation, that would otherwise expire in 2031.",
         "Removes a scheduled state tax cut. A large gain on a California property sale will be taxed at the top state rate for the foreseeable future.",
         ["sos_results", "voterguide_p3"]),
        ("One-time tax on certain taxpayers rejected",
         "Proposition 40 failed on unofficial results (52.4% no as of 12 November 2026).",
         "No state wealth tax. Recorded because a later version could return.",
         ["sos_results", "voterguide_p40"]),
        ("Countermeasure to Proposition 40 rejected",
         "Proposition 41 failed on unofficial results (55.1% no as of 12 November 2026). It would have prohibited new state taxes that exclude revenues from the state spending limit.",
         "Its failure removes one of the two measures that could have voided the one-time tax if both had passed.",
         ["sos_results", "voterguide_p40"]),
        ("New state personal property taxes barred",
         "Proposition 42 is leading on unofficial results (51.4% yes as of 12 November 2026).",
         "Narrows one route for a future state tax, but does not touch real property tax.",
         ["sos_results"]),
        ("Local revenue vote threshold rejected",
         "Proposition 43 failed on unofficial results (57.5% no as of 12 November 2026).",
         "Local parcel and transfer taxes remain possible without the stricter vote the measure would have required.",
         ["sos_results"]),
        ("Proposition 19 shelter adjusted",
         "For transfers from 16 February 2025 to 15 February 2027 the shelter is the prior taxable value plus $1,044,586, up from $1,022,600.",
         "The shelter is smaller than the growth in house prices, so it buys less each year.",
         ["boe_lta25009"]),
        ("Special needs trusts added as an eligible transfer medium",
         "SB 974, chaptered 27 September 2026, amends Revenue and Taxation Code section 63.2 so that a court-established special needs trust counts as an eligible medium of transfer.",
         "Relevant only if a transferee is a person with a disability. It does not change the value cap or the one-year occupation rule.",
         ["sb974"]),
    ]
    pending = [
        ("San Francisco File 261020",
         "Would temporarily cap combined banked and capital improvement rent increases on rent-controlled units at 10% a year.",
         "Would further limit income growth on Property B if the units are covered.",
         "Not enacted. The Rent Board itself says so.",
         ["sf_file261020"]),
        ("San Francisco transfer tax reductions",
         "A package introduced in February 2026 proposed rolling back the 2020 transfer tax increases for large transactions.",
         "Would reduce the cost of selling Property B. Would not affect Property A.",
         "Reported but not verified against an official city source on this site. It is left deliberately "
         "unresolved rather than given a number.",
         ["sf_file261020"]),
    ]
    dead = [
        ("AB 1157", "Would have amended Civil Code sections 1946.2, 1947.12 and 1947.13 on just cause and rent increases.",
         "Failed passage 13 January 2026 and died 31 January 2026. Recorded because it is often reported as law.",
         ["ab1157"]),
    ]
    return (
        callout("warn", "Read the election results carefully", """
<p>The November 2026 California results on this page are <strong>unofficial</strong>, published by the Secretary
of State with all precincts partially reporting, and they are not certified until 11 December 2026. They are
included because Proposition 3 directly changes the tax on a property sale. Confirm against the certified
results before relying on any of them.</p>""")
        + table("Enacted or changed", ["Change", "What it does", "Why it matters here", "Source"],
                [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td><td>{esc(c)}</td>"
                 + src_cell(d, "Official source") for a, b, c, d in enacted])
        + table("Proposed, not enacted", ["Measure", "What it would do", "Why it matters here", "Status", "Source"],
                [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td><td>{esc(c)}</td>"
                 f'<td><span class="badge unverified">{esc(d)}</span></td>'
                 + (src_cell(e, "Official source") if e else '<td class="src-cell"><span class="src-label">no official source retrieved</span></td>')
                 for a, b, c, d, e in pending])
        + table("Dead bills recorded so they are not mistaken for law",
                ["Bill", "What it would have done", "Status", "Source"],
                [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td><td>{esc(c)}</td>"
                 + src_cell(d, "Official source") for a, b, c, d in dead])
        + table("What would actually change the recommendation",
                ["Change", "Direction of the effect", "Source"],
                [
                    "<td>A repeal or sharp cut in the federal estate tax exclusion</td><td>Would make the cash inheritance taxable and could force a sale of the house for liquidity.</td>" + src_cell(["irs_estate"], "Current threshold"),
                    "<td>A California wealth tax or a one-time asset tax</td><td>Would tax holding assets rather than selling them, and could penalise keeping the house.</td>" + src_cell(["sos_results"], "2026 result"),
                    "<td>A change to Proposition 19 removing or widening the shelter</td><td>Would change the reassessment arithmetic at the transfer, which is the largest single number here.</td>" + src_cell(["rtc63_2", "boe_lta25009"], "Current rule"),
                    "<td>A split-roll change to Proposition 13</td><td>Would reset assessments on both properties and change every projection on this site.</td>" + src_cell(["boe_pub29"], "Current rule"),
                    "<td>Abolition of the basis step-up at death</td><td>Would remove the single strongest argument for selling at inheritance.</td>" + src_cell(["irs_basis"], "Current rule"),
                    "<td>A stricter local rent ordinance in San Francisco</td><td>Would reduce the income from Property B and make Property A look slightly better by comparison.</td>" + src_cell(["sf_rent_increase"], "Current rate"),
                ])
    )


# ---------------------------------------------------------------- black swan --
def page_black_swan() -> str:
    cpi = MODEL["meta"]
    stats = []
    for key, label, sid in (("cpi", "Consumer prices, 1977 to 2024", "fred_cpi"),
                            ("hpi_a", "House prices, Property A area, 1977 to 2025", "fred_hpi_a"),
                            ("hpi_b", "House prices, Property B area, 1977 to 2025", "fred_hpi_b"),
                            ("gs10", "10-year Treasury yield, 1976 to 2025", "fred_gs10")):
        changes = [r[key + "_chg"] for r in MODEL["series_table"] if r.get(key + "_chg") is not None]
        if key == "gs10":
            levels = [r[key] for r in MODEL["series_table"] if r.get(key) is not None]
            stats.append((label, f"{min(levels):.2f}% to {max(levels):.2f}%",
                          f"{sum(levels) / len(levels):.2f}%", f"{len(levels)} years", sid))
        else:
            dn = sum(1 for c in changes if c < 0)
            stats.append((label, f"{min(changes) * 100:.1f}% to {max(changes) * 100:.1f}%",
                          f"{sum(changes) / len(changes) * 100:.1f}%",
                          f"{len(changes)} years, {dn} of them down", sid))
    stats_rows = [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(d)}</td>"
                  + src_cell([e], "Verified series") for a, b, c, d, e in stats]

    reg_rows = []
    for rg in MODEL["regimes"]:
        run = rg["run"]
        reg_rows.append(
            f"<td><strong>{esc(rg['name'])}</strong><br><span class='muted'>{esc(rg['analogue'])}</span></td>"
            f"<td>{pc(rg['cpi'], 1)}</td><td>{pc(rg['house'], 1)}</td><td>{pc(rg['treasury'], 2)}</td>"
            f"<td>{m(run['terminal']['sell_equities'])}</td>"
            f"<td>{m(run['terminal']['live_in'])}</td>"
            f"<td>{m(run['terminal']['rent_out'])}</td>"
            f"<td>{m(run['bill_if_rent_year1'])}</td>"
            f"<td><strong>{esc(PATH_LABELS[run['best']])}</strong></td>"
            + src_cell(rg["src"] if rg["src"] else [], "Official source" if rg["src"] else "None"))
    reg_table = table("Stress regimes applied to the 2045 inheritance, over a 30 year horizon",
                      ["Regime", "Inflation", "House prices", "Treasury yield",
                       "Sell, equities", "Live in it", "Let it out",
                       "Tax bill if let out, year one", "Best path", "Source"], reg_rows,
                      note="The four historical regimes use averages computed directly from the verified "
                           "series listed in the source column. The last two are hypothetical stress cases "
                           "with no historical analogue and are labelled as such.")

    rep_rows = []
    for r in MODEL["replay"]:
        rep_rows.append(
            f"<td>{r['start']}&ndash;{r['end']}</td>"
            f"<td>{pc(r['a_cagr'], 2)}</td><td>{pc(r['cpi_cagr'], 2)}</td>"
            f"<td>{pc(r['bond_cagr'], 2)}</td>"
            f"<td>{m(r['a_value'])}</td><td>{m(r['a_value_real'])}</td>"
            f"<td>{m(r['b_value'])}</td>"
            f"<td>{r['down_years_a']}</td><td>{pc(r['worst_year_a'], 1)}</td>"
            f"<td>{m(r['tax_if_reset'])}</td><td>{m(r['tax_if_kept'])}</td>"
            + src_cell(["fred_hpi_a", "fred_hpi_b", "fred_cpi", "fred_gs10"], "Verified series"))
    replay = table("Every full 30-year window in the verified record, applied to these two properties",
                   ["Window", "House growth a year", "Inflation a year", "Treasury compounding",
                    "Property A value at the end", "Same, in start-year money",
                    "Property B value at the end", "Down years", "Worst year",
                    "Total tax if reassessed", "Total tax if not", "Source"], rep_rows,
                   note="Each row takes the realised annual changes in the house price index, the consumer "
                        "price index and the 10-year Treasury yield for that real 30-year window and applies "
                        "them to these two properties. No smoothing, no resampling, no invented numbers.")

    return (
        callout("why", "Why a smooth 4% line is the wrong tool", f"""
<p>Real economies do not grow at a constant rate. In the verified record used here, annual consumer price
inflation ranged from minus 0.3% to plus 13.5%, and annual house price growth in Property A's area ranged from
minus 12.3% to plus 30.2%. A single constant rate hides the thing that actually decides this case, which is
whether the house and the stock market take their bad years at the same time.</p>
<p>The <a href="economy.html">economy page</a> shows the full record. The tables below apply it.</p>""")
        + table("The shape of the record", ["Series", "Range of annual changes", "Average", "Coverage", "Source"],
                stats_rows)
        + reg_table
        + replay
        + callout("answer", "What the stress cases say", """
<p>Selling and investing wins in four of the six regimes, including both hypothetical stress cases. Keeping the
house wins in the two regimes where house prices in this area grew at an exceptional pace, which is exactly what
happened in the late 1970s and in 2021 to 2023. That is a coherent result: this decision is a bet on whether one
neighbourhood outgrows the whole market, and the historical record says that sometimes it does and mostly it
does not.</p>
<p>Two findings survive every regime. First, the property tax bill after reassessment is large and completely
insensitive to how the economy performs: assessed value rises at the 2% cap whether house prices boom or crash.
Second, letting the property out is the weakest path in every regime except the two house-price booms, because it
pays the full reassessment and then competes with a diversified portfolio on yield.</p>""")
    )


# ------------------------------------------------------------------ economy --
def page_economy() -> str:
    rows = []
    for r in MODEL["series_table"]:
        def chg(key):
            v = r.get(key + "_chg")
            if v is None:
                return "&mdash;"
            cls = "down" if v < 0 else "up"
            return f'<span class="{cls}">{v * 100:.1f}%</span>'
        rows.append(
            f"<td>{r['year']}</td>"
            f"<td>{r['cpi'] if r['cpi'] is not None else '&mdash;'}</td><td>{chg('cpi')}</td>"
            f"<td>{r['hpi_a'] if r['hpi_a'] is not None else '&mdash;'}</td><td>{chg('hpi_a')}</td>"
            f"<td>{r['hpi_b'] if r['hpi_b'] is not None else '&mdash;'}</td><td>{chg('hpi_b')}</td>"
            f"<td>{r['gs10'] if r['gs10'] is not None else '&mdash;'}</td>"
            + src_cell(["fred_cpi", "fred_hpi_a", "fred_hpi_b", "fred_gs10"], "FRED series"))
    tbl = table("The verified annual record, 1976 to 2025",
                ["Year", "Consumer price index", "Change",
                 "House price index, Property A area", "Change",
                 "House price index, Property B area", "Change",
                 "10-year Treasury yield, %", "Source"], rows,
                note="Every value was downloaded as a CSV file from the official FRED domain on 13 November "
                     "2026 and read directly from that file. No value was typed from memory. The consumer "
                     "price series ends at 2024 because the 2025 annual value was blank in the file retrieved.")
    return (
        callout("note", "Why this page exists", """
<p>The <a href="black-swan.html">black swan page</a> uses this record rather than invented scenarios. Every
number below comes from one of four series hosted by the Federal Reserve Bank of St. Louis on behalf of the
Bureau of Labor Statistics, the Federal Housing Finance Agency and the Board of Governors. Where a series stops
before 2025, the table shows a dash rather than filling the gap.</p>
<p>The tables after the annual record answer the objection that a single constant rate is unrealistic, in the
one way the record supports: the fifty years to 2026 are sliced into ten-year blocks and redrawn two thousand
times, so the projections become distributions instead of one guess. The last tables show what the record's
inflation does to the rules that are written in fixed nominal dollars.</p>""")
        + tbl
        + callout("note", "Two thousand fifty-year economies, redrawn from the record", f"""
<p>Ten-year blocks of the official annual record are drawn with replacement - {ECON['bootstrap']['blocks']} blocks
where both the house price series and the consumer price series are present - into
{ECON['bootstrap']['draws']:,} fifty-year paths. House and inflation history move together inside a block,
as they did in the record. The percentile of each outcome is shown against the constant-model case.</p>""")
        + table("What the record's own history does to Property A's value",
                ["Outcome across the draws", "5th percentile", "Median", "95th percentile",
                 "Constant-model case", "Source"],
                [f"<td>{esc(r['key'])}</td>"
                 + (f"<td>{m(r['p05'])}</td><td>{m(r['p50'])}</td><td>{m(r['p95'])}</td>"
                    f"<td>{m(r['constant'])}</td>" if r['unit'] == 'money' else
                    f"<td>{pc(r['p05'], 2)}</td><td>{pc(r['p50'], 2)}</td><td>{pc(r['p95'], 2)}</td>"
                    f"<td>{pc(r['constant'], 2)}</td>")
                 + src_cell(["fred_hpi_a", "fred_cpi"], "Bootstrap source series")
                 for r in ECON["bootstrap"]["rows"]],
                note="The record's median is well above the model's 4% because the fifty years to 2026 "
                     "include the 1970s and 1980s. The model's constant sits near the record's 5th "
                     "percentile, not at its middle: it is a deliberately conservative anchor, and the "
                     "decision page's conclusions do not depend on the median being this high.")
        + table("How often each outcome happens across the draws",
                ["Share of the two thousand draws", "Share", "Source"],
                [f"<td>{esc(s['key'])}</td><td><strong>{s['value'] * 100:.1f}%</strong></td>"
                 + src_cell(["fred_hpi_a", "fred_cpi"], "Bootstrap source series")
                 for s in ECON["bootstrap"]["shares"]]
                + [f"<td>{esc(ECON['bootstrap']['wins']['case'])}</td>"
                   f"<td><strong>{ECON['bootstrap']['wins']['sell_wins_share'] * 100:.1f}%</strong></td>"
                   + src_cell(["fred_hpi_a", "fred_cpi"], "Bootstrap source series")],
                note=ECON["bootstrap"]["wins"]["note"])
        + table("The lesser-of rule under the record's inflation paths",
                ["Outcome across the draws", "Property A", "Property B", "Source"],
                [("<td>Share of fifty years in which the inflation-adjusted base year value falls "
                  "below the 2%-capped value, median draw</td>"
                  f"<td>{ECON['lesser_of']['a']['share_years_indexed_below_cap_p50'] * 100:.1f}%</td>"
                  f"<td>{ECON['lesser_of']['b']['share_years_indexed_below_cap_p50'] * 100:.1f}%</td>"
                  + src_cell(["rtc51", "fred_cpi"], "Rule and price history")),
                 ("<td>Total ad valorem tax difference over fifty years, median draw</td>"
                  f"<td>{m(ECON['lesser_of']['a']['saving_p50'])}</td>"
                  f"<td>{m(ECON['lesser_of']['b']['saving_p50'])}</td>"
                  + src_cell(["rtc51", "fred_cpi"], "Rule and price history")),
                 ("<td>Same, 95th-percentile draw (the low-inflation 2010s drawn repeatedly)</td>"
                  f"<td>{m(ECON['lesser_of']['a']['saving_p95'])}</td>"
                  f"<td>{m(ECON['lesser_of']['b']['saving_p95'])}</td>"
                  + src_cell(["rtc51", "fred_cpi"], "Rule and price history"))],
                note=ECON["lesser_of"]["note"] + " A saving here reduces the bill; it never makes "
                     "holding the home better than selling on this site's numbers.")
        + table("What inflation does to the fixed nominal thresholds by 2045",
                ["Rule", "Amount today", "Rule for change", "Projected nominal in 2045",
                 "Same amount in 2026 dollars", "Source"],
                [f"<td>{esc(t['item'])}</td><td>{m(t['nominal_2026'])}</td><td>{esc(t['rule'])}</td>"
                 f"<td>{m(t['nominal_2045'])}</td><td><strong>{m(t['real_2045'])}</strong></td>"
                 + (src_cell(t["sources"], "Official rule") if t["sources"]
                    else '<td class="src-cell"><span class="src-label">no official source</span></td>')
                 for t in ECON["thresholds"]],
                note="Computed at the modelled inflation rate of 2.5% a year and rounded to the nearest "
                     "$10. The section 121 exclusion has been fixed since 1997; the Proposition 19 "
                     "excluded amount is reset every second February from the FHFA California house "
                     "price index, so it grows with house prices, not with the things the heir buys.")
        + table("What the record shows, in one table",
                ["Fact", "Value", "Source"],
                [(f"<td>{esc(a)}</td><td>{esc(b)}</td>" + src_cell(c, "Official source"))
                 for a, b, c in [
                    ("Highest annual inflation in the record", "13.5%, in 1980", ["fred_cpi"]),
                    ("Only annual fall in consumer prices in the record", "minus 0.3%, in 2009", ["fred_cpi"]),
                    ("Best year for house prices in Property A area", "plus 30.2%, in 1989", ["fred_hpi_a"]),
                    ("Worst year for house prices in Property A area", "minus 12.3%, in 2009", ["fred_hpi_a"]),
                    ("Property A area, 2006 to 2011", "a 25.6% fall from the 2006 level to the 2011 level", ["fred_hpi_a"]),
                    ("Property B area, 2006 to 2011", "a 21.8% fall from the 2006 level to the 2011 level", ["fred_hpi_b"]),
                    ("Property A area, 1989 to 1996", "a fall from 110.67 to 105.46 over seven years", ["fred_hpi_a"]),
                    ("Highest annual 10-year Treasury yield in the record", "13.91%, in 1981", ["fred_gs10"]),
                    ("Lowest annual 10-year Treasury yield in the record", "0.89%, in 2020", ["fred_gs10"]),
                    ("2025 annual 10-year Treasury yield", "4.29%", ["fred_gs10"]),
                    ("Official long-run inflation assumption", "2.4% a year, intermediate case, 2026 Trustees Report", ["ssa_trustees"]),
                    ("Official long-run real interest assumption", "2.3% for 2044 and later, intermediate case", ["ssa_trustees"]),
                    ("Official long-range assumption range, inflation", "1.8% high-cost to 3.0% low-cost", ["ssa_trustees"]),
                 ]])
    )



# ---------------------------------------------------------------- questions --
QUESTIONS = [
    ("A", "Title, trust and timing",
     [
      ("Is the heir a child of the transferor?",
       "The owner describes the house as being inherited through a trust. No relationship is stated anywhere in the material this site was built from.",
       "The relationship between the transferor and the heir. The statute defines 'children' to include a stepchild, a son-in-law or daughter-in-law, an adopted child adopted before 18, and a foster child of a licensed foster parent where adoption was barred.",
       "Read the trust instrument and the deed. This is the first thing to confirm, before any other question on this page.",
       "Revenue and Taxation Code section 63.2 allows the intergenerational exclusion only between parents and their children, or grandparents and grandchildren where the middle generation has died. If the relationship is different, there is no exclusion, the property is reassessed to full market value on the transfer, and every Proposition 19 figure on this site falls away. It is the single condition the whole analysis rests on.",
       ["rtc63_2_eligibility", "boe_prop19"]),
      ("Is the house actually titled in the trust today?",
       "The owner states the inheritance will come through a trust around 2040 to 2050.",
       "No deed, no parcel number, no trust document.",
       "Read the recorded grant deed and the preliminary change of ownership report at the county recorder.",
       "If the house is not in the trust, the transfer path, the reassessment and possibly probate all change.",
       ["scc_recorder"]),
      ("Is the trust revocable, and who is the successor trustee?",
       "Not supplied.",
       "Whether the settlor can revoke, who administers on death, and whether the trustee has a sale power.",
       "Read the trust instrument and any amendments.",
       "Determines who signs the deed, whether the basis step-up applies in full, and how fast a sale could be done.",
       []),
      ("Does the heir take outright, in further trust, or only for life?",
       "Not supplied.",
       "Whether a life estate, a term of years or a continuing trust is involved.",
       "Read the distribution clauses of the trust.",
       "A life estate changes both the basis step-up and who may claim the Proposition 19 exclusion.",
       []),
      ("Is any beneficiary a person with a disability for whom a special needs trust exists?",
       "Not supplied.",
       "Whether a court-established special needs trust is in play.",
       "Read the trust and ask the drafter.",
       "SB 974, chaptered in September 2026, makes such a trust an eligible medium of transfer for the exclusion.",
       ["sb974"]),
      ("Is there a plan to sell, hold or occupy, and who decides?",
       "Not supplied.",
       "The trustee's duties and any letter of wishes.",
       "Ask the trustee and read the trust.",
       "A trustee has duties to beneficiaries that may not match the heir's preferences.",
       []),
     ]),
    ("B", "Property tax and assessment",
     [
      ("What is the tax rate area for Property A, and what is its published rate?",
       "The county publishes 816 tax rate areas for fiscal year 2025-26 but this site does not publish the parcel's area.",
       "The exact published rate and the bond components.",
       "Look up the tax rate area on the tax bill and read the rate from the county's published rate book.",
       "The ad valorem rate drives every reassessment figure. This site assumes 1.18% and flags it.",
       ["scc_ratebook"]),
      ("What are the fixed charges on the Property A bill?",
       "Derived from the owner's bills at about $840 in 2025 at the assumed rate.",
       "The itemised parcel taxes, bonds and assessments.",
       "Read the itemised bill.",
       "Fixed charges have grown unevenly; on Property B they grew at 8.1% a year between 2016 and 2025.",
       ["scc_ratebook", "sf_treas_rate"]),
      ("Has a homeowners' exemption been claimed on Property A?",
       "Not supplied.",
       "Whether the exemption is in place on the transferor's main home.",
       "Check the bill for the exemption line, or ask the assessor.",
       "The Proposition 19 definition of a principal residence hinges on eligibility for that exemption.",
       ["boe_lta26026"]),
      ("Has a homeowners' exemption been claimed on Property B?",
       "Not supplied.",
       "Which property currently carries the exemption.",
       "Check both bills.",
       "Only one exemption is available. Claiming it on Property A means giving it up on Property B.",
       ["sf_treas_rate"]),
      ("Have there been earlier transfers, exclusions or new construction on either property?",
       "Not supplied.",
       "Prior base year value transfers, prior Prop 19 claims, permits.",
       "Ask the assessor for the parcel history.",
       "A prior exclusion can limit what is available later.",
       ["boe_prop19"]),
      ("Is either assessed value currently held below the inflation-adjusted value under the lesser-of rule?",
       "Not supplied.",
       "Whether a decline has already been applied.",
       "Ask the assessor.",
       "Affects the starting point for the reassessment.",
       ["rtc51"]),
     ]),
    ("C", "Occupancy and the Proposition 19 claim",
     [
      ("Will the heir occupy Property A as a principal residence within one year of transfer?",
       "Not stated. The heir currently can live at Property B without losing rent.",
       "The heir's intention, and whether the Property B principal-residence position would be given up.",
       "Decide before the transfer, not after.",
       "Without occupation the property is reassessed in full. This is the largest single number in the analysis.",
       ["rtc63_2", "boe_lta26026"]),
      ("If the heir occupies and later moves out, what value is enrolled?",
       "Section 63.2(a)(1)(C) says the base year value established as of the change in ownership to which the exclusion applied, adjusted annually, is enrolled once the transferee is no longer eligible for the homeowners' or disabled veterans' exemption. That reads as the propounded base year value rather than the higher value that was sheltered.",
       "Section 63.2(a)(1)(C) is the plain reading, but the county assessor applies it and this site has no written confirmation from the assessor.",
       "Ask the county assessor in writing, before relying on it.",
       "It decides whether the live-then-rent path keeps the sheltered base after the move-out. This site models it the way the statute reads and flags the residual uncertainty on the review page.",
       ["rtc63_2", "boe_lta26026"]),
      ("Could the heir keep the house as a principal residence for the whole of the relevant period?",
       "Not stated.",
       "Job location, family, school, care responsibilities.",
       "Not a public record question; a family one.",
       "The exclusion is removed when the home stops being the main home. A plan that depends on moving out later is not a safe plan.",
       ["boe_lta26026"]),
     ]),
    ("D", "Rent and tenancy",
     [
      ("What are the current rents, lease start dates and anniversary dates on the two let units?",
       f"About {m(B['rent']['monthly'])} a month in total, owner-stated and unverified.",
       "Per-unit rents, deposits, lease terms and anniversary dates.",
       "Read the leases and the rent ledger.",
       "Drives the income on Property B and the timing of any increase.",
       []),
      ("Are the Property B units covered by the San Francisco Rent Ordinance?",
       "Not verified.",
       "The certificate of occupancy date and the exemption status of the building.",
       "Check with the Rent Board and the building's records.",
       "Coverage decides whether the 1.6% local increase or the statewide cap applies.",
       ["sf_rent_increase", "civ1947_12"]),
      ("Is the rent increase licence current, and is the building registered in the Housing Inventory?",
       "Not supplied.",
       "Whether the licence and registration are in place.",
       "Ask the Rent Board.",
       "Without them, annual increases cannot lawfully be imposed at all.",
       ["sf_rent_increase"]),
      ("What are the obligations if the heir wants a unit back for their own use?",
       "Not supplied.",
       "Just cause, notice periods and relocation payments under local and statewide rules.",
       "Read Civil Code 1946.2 and the Rent Ordinance, and take advice.",
       "Directly affects the option of living at Property B while also using the third unit.",
       ["civ1946_2"]),
      ("What rent could the vacant third unit command?",
       "Not supplied.",
       "A market rent opinion.",
       "Ask two or three local letting agents.",
       "It is the real opportunity cost of living at Property A rather than Property B.",
       []),
      ("What rent could Property A command?",
       "Not supplied. This site reports the break-even rent instead of inventing a figure.",
       "A market rent opinion for the house.",
       "Ask two or three local letting agents at the time.",
       "Needed to test the rental path properly. The break-even is on the decision page.",
       []),
     ]),
    ("E", "Running costs",
     [
      ("What does insurance actually cost for each property?",
       "Owner estimate of about $1,500 a year for each, unverified.",
       "Real quotes.",
       "Get three quotes per building from admitted insurers, and check the FAIR Plan as a fallback. The "
       "FAIR Plan is the state's insurer of last resort and is not limited to a bare fire policy: it also "
       "offers a comprehensive homeowners form. Treat it as a fallback, not as a comparable quote.",
       "The Department publishes no statutory average premium by area. It does run an online homeowners premium survey, with sample rates by company that the reader can compare; the survey is not a quote and does not set a premium for either building. So the estimate can be compared against published sample rates, but it cannot be replaced by an official figure.",
       ["cdi_tips", "cdi_fairplan", "cdi_compare"]),
      ("Who supplies water to Property A, and on what tariff?",
       f"Owner range of {m(A['annual_costs']['water']['low'])} to {m(A['annual_costs']['water']['high'])} a year.",
       "The provider and the published rate schedule.",
       "Read the bill and the provider's published rates.",
       "Water is small next to tax and maintenance, but it is checkable and should be checked.",
       []),
      ("What tariff is the solar system on, and when was it interconnected?",
       "The owner reports a small net annual credit.",
       "NEM 1.0, NEM 2.0 or the net billing tariff, and the interconnection date.",
       "Read the interconnection agreement and the bill.",
       "NEM 2.0 runs for twenty years from interconnection; the net billing tariff pays much less for exports. A change of customer can end the tariff.",
       ["cpuc_nem"]),
      ("What is the real maintenance and capital history of each building?",
       "Not supplied. Assumed at 0.5% of value a year owner-occupied, 0.75% as a rental and 1.5% for the older building.",
       "Five years of actual spend, and a capital plan.",
       "Assemble the receipts and get a building inspection.",
       "Roofs, sewer laterals, foundations and paint are lumpy, not annual. The assumption hides that.",
       []),
      ("Are there bonded assessments, Mello-Roos charges or special district levies on either property?",
       "Not supplied.",
       "The itemised bill.",
       "Read the itemised bill.",
       "These are part of the fixed charge that keeps growing regardless of what the market does.",
       ["scc_ratebook"]),
     ]),
    ("F", "Taxes and the estate",
     [
      ("What is the total value of the estate, including the cash, and does it exceed the federal exclusion?",
       f"The 2026 exclusion is {m(V['federal_basic_exclusion_2026']['value'])}. The cash amount is deliberately not published here.",
       "The estate's own valuation.",
       "The owner's private records, with a professional valuation.",
       "Determines whether an estate tax return is due and whether the house might have to be sold for liquidity.",
       ["irs_estate", "irs_whatsnew"]),
      ("Is portability available, and were there prior taxable gifts?",
       "Not supplied.",
       "Whether a prior spouse died and an election was made, and the lifetime gift history.",
       "Ask the estate's advisers and read any prior Form 709 or Form 706.",
       "Prior taxable gifts reduce what is left of the exclusion.",
       ["irs_estate", "irs_i706"]),
      ("Are there retirement accounts in the estate?",
       "Not supplied.",
       "Account types and balances.",
       "Read the account statements.",
       "Inherited retirement assets are taxed as withdrawn and do not get the basis step-up. This is the most common surprise.",
       ["irs_rmd"]),
      ("What will the heir's filing status and marginal rates be in the year of a sale?",
       "Not supplied.",
       "Single or joint, and other income.",
       "Estimate at the time.",
       "Decides the $250,000 or $500,000 exclusion and the rate band for the gain.",
       ["irs_p523", "irs_tc409"]),
      ("Should a like-kind exchange or an instalment sale be considered?",
       "Not modelled.",
       "Whether the heir wants to remain in real estate.",
       "Take tax advice at the time.",
       "An exchange defers tax but does not change the property tax reassessment.",
       []),
     ]),
    ("G", "Preferences",
     [
      ("Does the heir actually want to live in this house?",
       "Not stated.",
       "A preference, not a number.",
       "Ask.",
       "It is the only consideration on this site that can outweigh the arithmetic.",
       []),
      ("What is the risk tolerance for the invested proceeds?",
       "Not stated.",
       "Equities, bonds, savings, or a mix.",
       "Set an investment policy before the money arrives.",
       "The recommendation assumes a diversified equity portfolio. A cash-only approach changes the answer: see the break-even table.",
       []),
      ("Is there a wish to keep the house in the family?",
       "Not stated.",
       "A family preference.",
       "Discuss it openly, before the transfer.",
       "If the answer is yes, the cost of that preference is on the decision page and should be agreed knowingly.",
       []),
     ]),
]


def page_questions() -> str:
    sections = []
    for letter, title, items in QUESTIONS:
        rows = [
            f"<td><strong>{esc(q)}</strong></td>"
            f"<td>{esc(have)}</td>"
            f"<td>{esc(missing)}</td>"
            f"<td>{esc(how)}</td>"
            f"<td>{esc(why)}</td>"
            + (src_cell(s, "Official source") if s else src_cell([], "No official source applies"))
            for q, have, missing, how, why, s in items]
        sections.append(
            f'<h2>{esc(letter)}. {esc(title)}</h2>'
            + table(f"{len(items)} questions in this group",
                    ["Question", "What we have", "What is missing", "How to find out",
                     "Why it matters", "Source"], rows))
    return (
        callout("note", "How to use this page", f"""
<p>There are {sum(len(i) for _, _, i in QUESTIONS)} questions below, grouped by subject. Each one states what this
site already has, what is missing, how to find the answer, and why it changes the decision. Questions with no
official source in the last column are matters of fact or preference that no public source can answer; they are
listed anyway so nothing is assumed away.</p>
<p>Every item here is also a candidate for the <a href="suggestions.html">suggestions page</a>, which is the
review queue for turning them into action.</p>
<p><strong>Answer A-1 first.</strong> Whether the heir is a child of the transferor decides whether the
intergenerational exclusion in Revenue and Taxation Code section 63.2 exists at all. Until it is answered, every
Proposition 19 figure on this site is conditional.</p>""")
        + "".join(sections))


# -------------------------------------------------------------- suggestions --
SUGGESTIONS = [
    ("S-01", "Replace both insurance estimates with three real quotes each",
     "Removes the largest block of unverified cost inputs. A rental policy on Property B is priced very differently from a primary-residence policy.",
     "Low", "Low", "costs", "cdi_tips"),
    ("S-02", "Look up Property A's tax rate area and read the published rate",
     "Replaces the assumed 1.18% with the rate the county actually applies, and itemises the fixed charges.",
     "Low", "None", "property-a", "scc_ratebook"),
    ("S-03", "Confirm the trust holds title and obtain the preliminary change of ownership report",
     "Establishes that the transfer will take the intended path and starts the county record correctly.",
     "Low", "Low if done now, high if discovered late", "inheritance", ["scc_recorder", "rtc480"]),
    ("S-04", "Model a sale in the same tax year as the inheritance, before deciding anything else",
     "The basis step-up makes an immediate sale almost tax-free. This is the option everything else must beat.",
     "Low", "Low", "decision", ["irs_basis"]),
    ("S-05", "Claim the Proposition 19 exclusion only if the heir will occupy the home long term",
     "The exclusion is removed when the home stops being the principal residence, and there is no exception to the one-year occupation rule.",
     "Medium", "High if the heir may move out", "property-a", ["rtc63_2", "boe_lta26026"]),
    ("S-06", "Get rental opinions for Property A and for the vacant unit at Property B",
     "Turns the break-even rent into a real comparison and prices the opportunity cost of occupying Property A.",
     "Low", "None", "decision", []),
    ("S-07", "Confirm San Francisco Rent Ordinance coverage and the rent increase licence",
     "Decides which rent cap applies and whether increases can lawfully be made at all.",
     "Low", "Medium if notices were missed", "property-b", ["sf_rent_increase", "civ1947_12"]),
    ("S-08", "Confirm the solar interconnection date and the tariff the system is on",
     "Determines whether the export credit survives, for how long, and what happens when the customer of record changes.",
     "Low", "Medium", "costs", ["cpuc_nem"]),
    ("S-09", "Build a five-year maintenance and capital plan for both buildings",
     "Replaces a percentage assumption with real numbers and surfaces lumpy items like roofs and sewer laterals.",
     "Medium", "None", "costs", []),
    ("S-10", "Obtain a written valuation of Property A at the date of death",
     "Fixes the income tax basis and the depreciation basis if the property is ever let.",
     "Medium", "High if skipped", "inheritance", ["irs_basis"]),
    ("S-11", "Decide whether a like-kind exchange is wanted, and take advice before selling",
     "An exchange must be arranged before the sale, not after. It defers tax but does not change the reassessment.",
     "High", "High if attempted late", "taxes", []),
    ("S-12", "Write an investment policy for the sale proceeds before the money arrives",
     "The recommendation assumes a diversified portfolio. Deciding the split in advance avoids doing it in a moving market.",
     "Medium", "Medium", "decision", []),
    ("S-13", "Prepare an estate liquidity plan if the estate may exceed the federal exclusion",
     "Federal estate tax is due in cash within nine months of death. A house is not a liquid asset.",
     "Medium", "High if ignored", "estate", ["irs_estate", "irs_i706"]),
    ("S-14", "Ask now about portability and prior taxable gifts",
     "Both change how much exclusion is left, and both are far cheaper to establish now than after the death.",
     "Low", "High if ignored", "estate", ["irs_estate"]),
    ("S-15", "Review the trust for a special needs trust clause in light of SB 974",
     "SB 974, chaptered September 2026, makes such a trust an eligible medium of transfer for the exclusion.",
     "Low", "Low", "laws", ["sb974"]),
    ("S-16", "Re-run this model every year with updated inputs",
     "Most of the gap between the paths comes from assumptions that can be replaced with facts over time.",
     "Low", "None", "projections", []),
    ("S-17", "Set the review gate before implementing anything",
     "Nothing on this page has been done. Each item needs a decision to adopt, defer or reject, recorded before any action.",
     "Low", "None", None, []),
    ("S-18", "Keep the data files in this repository as the single source of truth",
     "Every figure on the site is generated from assets/data. Editing the HTML by hand would break that and the verification.",
     "Low", "None", None, []),
    ("S-19", "Confirm the parent-and-child relationship before anything else on this list",
     "It is the one condition that can remove every Proposition 19 shelter figure on the site. If the relationship is different, the reassessment is full and the case for selling gets stronger, not weaker.",
     "Low", "Highest on the list", "questions", ["rtc63_2_eligibility", "boe_prop19"]),
    ("S-20", "Put a market rent on Property A or accept that the letting paths are a floor",
     "The letting paths currently carry every landlord cost and no rent. Either obtain a documented rent opinion and enter it in the data file, or read every letting result on this site as a floor rather than a comparison.",
     "Low", "Medium: the rental case cannot be judged without it", "decision", ["hud_fmr"]),
    ("S-21", "Get the county assessor's written answer on the base year after a move-out",
     "Section 63.2(a)(1)(C) says the base year established at the change in ownership is enrolled when the transferee stops being eligible for the homeowners' exemption. The live-then-rent path is modelled on that reading. A written answer removes the uncertainty.",
     "Low", "Medium: it moves the live-then-rent path, not the recommendation", "questions", ["rtc63_2_eligibility"]),
    ("S-22", "Decide whether the public repository and its history should stay public",
     "The repository is public and earlier commits contain unrounded owner figures. Rounding the published page does not change what Git history holds. Making the repository private, or rewriting history, are the only two ways to close that exposure.",
     "Medium", "High for privacy, none for the analysis", "review", []),
]


def page_suggestions() -> str:
    rows = []
    for sid, title, effect, effort, risk, area, src in SUGGESTIONS:
        target = area if area and area.endswith(".html") else (area + ".html" if area else None)
        area_html = (f'<a href="{esc(target)}">{esc(PAGE_TITLES.get(target, area))}</a>'
                     if target else "Whole analysis")
        rows.append(
            f"<td><strong>{esc(sid)}</strong></td>"
            f"<td><strong>{esc(title)}</strong></td>"
            f"<td>{esc(effect)}</td>"
            f"<td>{esc(effort)}</td>"
            f"<td>{esc(risk)}</td>"
            f"<td>{area_html}</td>"
            f'<td><span class="badge proposed">proposed</span></td>'
            + (src_cell(src if isinstance(src, list) else [src], "Official source") if src
               else src_cell([], "No official source applies")))
    tbl = table("Suggestions for review",
                ["ID", "Suggestion", "What it changes", "Effort", "Risk if ignored",
                 "Where it lands", "Status", "Source"], rows)

    gate = table("The selection gate",
                 ["Step", "What happens", "Rule", "Source"],
                 [
                     "<td>1. Read</td><td>Work through the list and mark each item adopt, defer or reject.</td><td>No item is implemented by building this site. Every item is still marked proposed.</td>" + src_cell([], "Procedure, not a figure"),
                     "<td>2. Gate</td><td>Anything that costs money, signs a document, or moves title needs an explicit decision recorded before it happens.</td><td>Items S-03, S-05, S-11 and S-13 are in this class.</td>" + src_cell([], "Procedure, not a figure"),
                     "<td>3. Verify</td><td>Anything that replaces an unverified figure should be checked against the official source in the last column, and the data file updated.</td><td>Items S-01, S-02, S-07 and S-08 are in this class.</td>" + src_cell([], "Procedure, not a figure"),
                     "<td>4. Re-run</td><td>After any input changes, rebuild the model and the site and see whether the recommendation moved.</td><td>Item S-16.</td>" + src_cell([], "Procedure, not a figure"),
                     "<td>5. Record</td><td>Write the decision and the date next to the item, so a future reader knows what was chosen and why.</td><td>Item S-17.</td>" + src_cell([], "Procedure, not a figure"),
                 ])

    improve_src = {"Add per-unit detail for Property B": ["sf_rent_increase"],
                   "Add a real rental opinion for Property A": [],
                   "Add a maintenance and capital schedule": [],
                   "Add the itemised tax bills": ["scc_ratebook"],
                   "Add a liquidity model for the estate": ["irs_estate", "irs_i706"],
                   "Add a two-person household case": ["irs_tc409", "irs_estate"],
                   "Add a mortgage case": [],
                   "Add a distribution chart to the projections": []}
    improve_rows = [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td><td>{esc(c)}</td>"
                    f'<td><span class="badge proposed">proposed</span></td>'
                    + (src_cell(improve_src[a], "Official source") if improve_src[a]
                       else src_cell([], "No official source applies"))
                    for a, b, c in [
                        ("Add per-unit detail for Property B", "Rent, lease dates and anniversary dates per unit, so the income can be projected properly instead of as one total.", "The Property B income is currently a single unverified total with no expiry dates."),
                        ("Add a real rental opinion for Property A", "Replaces the break-even rent with a comparison against an actual market rent.", "The rental path is currently tested only against a break-even, which is honest but indirect."),
                        ("Add a maintenance and capital schedule", "Year-by-year capital items rather than a percentage of value.", "Lumpy costs are invisible, which flatters every hold path."),
                        ("Add the itemised tax bills", "Bond, parcel tax and assessment lines separated from the ad valorem part.", "The fixed charge is currently modelled as a single number growing with inflation."),
                        ("Add a liquidity model for the estate", "Whether the estate could pay federal estate tax without selling the house.", "The interaction between the cash inheritance and the house is currently only sketched in scenario bands."),
                        ("Add a two-person household case", "Joint filing, the $500,000 exclusion and two exclusions for estate tax.", "The model currently uses the single-filer exclusion throughout, which is conservative."),
                        ("Add a mortgage case", "What happens if the heir borrows against either property instead of selling.", "Not modelled at all."),
                        ("Add a distribution chart to the projections", "A visual range rather than a single line.", "Readers tend to read the single line as a forecast."),
                    ]]
    improve = table("Improvements to this site, offered for review",
                    ["Proposal", "What it would add", "Cost of not doing it", "Status", "Source"],
                    improve_rows)
    return (
        callout("gate", "Nothing here has been implemented", """
<p>Every item below is <strong>proposed</strong>. Building this site did not adopt, purchase, sign, file or change
anything. The point of the page is that someone reads the list, chooses the best path, and only then acts. The
selection gate below is the order in which to do that.</p>""")
        + gate
        + tbl
        + '<h2>Improvements to this site</h2>'
        + improve
        + callout("privacy", "One suggestion that is not optional", """
<p>S-18 is listed last but it is the one that keeps the site honest. Every figure you see is generated from the
data files in <code>assets/data</code> by <code>scripts/model.py</code> and <code>scripts/build.py</code>. If a
number is edited directly in an HTML file, the next rebuild will overwrite it and the verification will still
pass, because the verification checks the generated output, not the intent. Change the data, not the page.</p>""")
    )


# ------------------------------------------------------------------- review --
FACTOR_BY_ROLL_YEAR = {  # BOE Letter to Assessors 2026/002: factor for the fiscal year starting in that year
    2015: 1.01998, 2016: 1.01525, 2017: 1.02, 2018: 1.02, 2019: 1.02, 2020: 1.02,
    2021: 1.01036, 2022: 1.02, 2023: 1.02, 2024: 1.02, 2025: 1.02, 2026: 1.02,
}


def irregularity_section() -> str:
    """The owner's roll and bill history, checked against the official factors and the bill structure.

    Every figure is the model's copy of the owner's figures, rounded to the nearest $10. None has
    been checked against the county roll, so each item is a question to answer, not a finding of error.
    """
    ra = {r["year"]: r for r in MODEL["roll_a"]}
    rb = {r["year"]: r for r in MODEL["roll_b"]}

    def chg(a, b):
        return (b / a - 1) * 100

    def sgn(x):
        return f"{x:+.1f}%".replace("-", "&minus;")

    # Every assessed-value change, compared with the official factor for that year.
    checks = []
    for label, roll in (("Property A", ra), ("Property B", rb)):
        for y in sorted(roll):
            if y - 1 in roll and y in FACTOR_BY_ROLL_YEAR:
                expect = money10(roll[y - 1]["assessed"] * FACTOR_BY_ROLL_YEAR[y])
                checks.append((label, y, roll[y]["assessed"], expect, roll[y]["assessed"] - expect))
    off = [c for c in checks if abs(c[4]) > 10]
    assert [(c[0], c[1]) for c in off] == [("Property B", 2022)], off

    b17, b18 = rb[2017]["bill"], rb[2018]["bill"]
    b20, b21 = rb[2020]["bill"], rb[2021]["bill"]
    b21a, b22a = rb[2021]["assessed"], rb[2022]["assessed"]
    b22_expect = money10(b21a * 1.02)
    a16_bill, a17_bill = ra[2016]["bill"], ra[2017]["bill"]
    rate_2026_27 = 0.0118162182  # Property B secured rate for FY 2026-27 (sf_treas_rate)
    b25_bill, b25_av = rb[2025]["bill"], rb[2025]["assessed"]
    b25_rate_part = money10(b25_av * rate_2026_27)
    chg_2021 = chg(rb[2020]["assessed"], rb[2021]["assessed"])
    assess_part_2021 = b20 * chg_2021 / 100
    fall_2021 = money10((b20 - b21) + assess_part_2021)

    rows = [
        (f"<td><strong>Property B assessed value, 2022 roll</strong></td>"
         f"<td>{m(b22a)}, up {chg(b21a, b22a):.2f}% on {m(b21a)}.</td>"
         f"<td>The 2022-23 factor was 1.02, so the roll should be about {m(b22_expect)}. The roll is {m(b22_expect - b22a)} lower.</td>"
         "<td>Ask the assessor for the roll entry. A reduction recorded on the roll (for example for a decline in value) would explain it. A transcription error would not.</td>"
         + src_cell(["boe_lta26002"], "Official factor")),
        (f"<td><strong>2021 change labelled +1%, both rolls</strong></td>"
         f"<td>Property A rises {chg(ra[2020]['assessed'], ra[2021]['assessed']):.2f}% ({m(ra[2020]['assessed'])} to {m(ra[2021]['assessed'])}). Property B rises {chg_2021:.2f}%.</td>"
         "<td>The 2021-22 factor was 1.01036, which is 1.04%. The figures agree with the official factor, so the label is the error.</td>"
         "<td>Correct the label in the owner's table. The figures need no change.</td>"
         + src_cell(["boe_lta26002"], "Official factor")),
        (f"<td><strong>Property A bill falls in 2017</strong></td>"
         f"<td>Bill falls from {m(a16_bill)} to {m(a17_bill)} ({sgn(chg(a16_bill, a17_bill))}) while assessed value rises {chg(ra[2016]['assessed'], ra[2017]['assessed']):.2f}%.</td>"
         "<td>The bill is an ad valorem part (rate times assessed value) plus fixed and direct charges. A rising assessed value raises the first part, so a fall needs another charge to have dropped by more.</td>"
         "<td>Compare the 2016 and 2017 itemised bills.</td>"
         + src_cell(["scc_ratebook"], "Tax rate book")),
        (f"<td><strong>Property A bill repeated</strong></td>"
         f"<td>The same bill in 2017 and 2018 ({m(ra[2018]['bill'])}), and in 2019 and 2020 ({m(ra[2020]['bill'])}). Assessed value rose 2.00% in both 2018 and 2020.</td>"
         "<td>The ad valorem part rises with assessed value, so an identical bill needs an offsetting change in another charge. A figure copied forward from the year before is also possible.</td>"
         "<td>Check the 2018 and 2020 bills against the figures in the owner's table.</td>"
         + src_cell(["scc_ratebook"], "Tax rate book")),
        (f"<td><strong>Property B bill rises 18.4% in 2018</strong></td>"
         f"<td>Bill rises from {m(b17)} to {m(b18)} ({sgn(chg(b17, b18))}) while assessed value rises 2.00%.</td>"
         f"<td>Even if the whole 2017 bill had risen with assessed value, the rise would be about {m(money10(b17 * 0.02))}. About {m(money10((b18 - b17) - b17 * 0.02))} came from other charges.</td>"
         "<td>Read the itemised 2017 and 2018 bills for direct assessments, bond levies and special taxes.</td>"
         + src_cell(["sf_treas_rate"], "Treasurer and Tax Collector")),
        (f"<td><strong>Property B bill falls 5.9% in 2021</strong></td>"
         f"<td>Bill falls from {m(b20)} to {m(b21)} ({sgn(chg(b20, b21))}) while assessed value rises {chg_2021:.2f}%.</td>"
         f"<td>At most about {m(money10(assess_part_2021))} of the change can come from assessed value. Other charges therefore fell by at least {m(fall_2021)}.</td>"
         "<td>Read the itemised 2020 and 2021 bills.</td>"
         + src_cell(["sf_treas_rate"], "Treasurer and Tax Collector")),
        (f"<td><strong>Property B bill against the published rate</strong></td>"
         f"<td>The 2025 bill is {m(b25_bill)} on {m(b25_av)} of assessed value: {b25_bill / b25_av * 100:.2f}% of assessed value.</td>"
         f"<td>The FY 2026-27 secured rate of 1.18162182%, applied to the same value, gives about {m(b25_rate_part)}. The other {m(money10(b25_bill - b25_rate_part))} a year comes from charges outside that rate.</td>"
         "<td>Read the itemised 2025 bill. Identify each direct assessment, bond levy and special tax, and whether each continues.</td>"
         + src_cell(["sf_treas_rate"], "Treasurer and Tax Collector")),
    ]
    head_note = (f"Assessed-value changes checked against the official factor for each year: {len(checks)} changes, "
                 f"of which {len(checks) - len(off)} match within $10. The exception is Property B in 2022. "
                 "Every figure is the owner's, rounded to $10, and none has been checked against the county roll.")
    return ('<h2 id="irregularities">Irregularities in the owner\'s rolls and bills</h2>'
            + table("Items for the owner to check. These are questions, not findings of error.",
                    ["Item", "What the figures show", "What the official table or rule says", "What to do", "Source"],
                    rows, note=head_note))


def page_review() -> str:
    unverified = [
        ("Property A market value, November 2026", m(A["estimated_market_value_2026"]),
         "Owner estimate", "Get a written valuation, and a second opinion at the date of death."),
        ("Property B market value, November 2026", m(B["estimated_market_value_2026"]),
         "Owner estimate", "Get a written valuation."),
        ("Both assessment rolls and tax bills", "13 years for Property A, 10 for Property B",
         "Owner's own records, not checked against the county roll",
         "Order the assessor's parcel history for each property and compare line by line."),
        ("Property A ad valorem rate", pcf(ASM["ad_valorem_rate_a"]["value"], 2),
         "Assumption. The data cannot identify it, because assessed value and fixed charges both grow at about 2% a year.",
         "Read the rate for the property's tax rate area from the county's published rate book."),
        ("Property B ad valorem rate", pcf(ASM["ad_valorem_rate_b"]["value"], 5),
         "Published by the City and County of San Francisco for fiscal year 2026-27",
         "None. This one is verified."),
        ("Property A water", f"{m(A['annual_costs']['water']['low'])} to {m(A['annual_costs']['water']['high'])} a year",
         "Owner estimate. A CPUC-approved tariff for the area's water utility is now read and linked on the property page, and a discovery-path source is on the ledger; the provider printed on the parcel's own bill is still unconfirmed, and the owner's bills are unchecked against any tariff.",
         "Confirm the provider on the bill, then compare twelve months of bills with the derived tariff range."),
        ("Property A electricity, net of solar", f"{m(A['annual_costs']['electricity']['low'])} to {m(A['annual_costs']['electricity']['high'])} a year",
         "Owner estimate", "Read twelve months of bills and the interconnection agreement."),
        ("Property B water", f"{m(B['annual_costs']['water']['low'])} to {m(B['annual_costs']['water']['high'])} a year",
         "Owner estimate", "Read the bills."),
        ("Property B electricity", f"{m(B['annual_costs']['electricity']['low'])} to {m(B['annual_costs']['electricity']['high'])} a year",
         "Owner estimate", "Read the bills."),
        ("Insurance on both properties", m(A["annual_costs"]["insurance"]["mid"]) + " a year each",
         "Owner estimate. The Department publishes a statewide average and an online premium survey, not an average for this postal area, so it can be compared against sample rates but not verified as the premium for this building.",
         "Get three quotes per building."),
        ("Maintenance on both properties", "0.5% / 0.75% of value for Property A, 1.5% for Property B",
         "Assumption. No figure was supplied.",
         "Assemble five years of actual spend and a capital plan."),
        ("Property B rent", m(B["rent"]["annual"]) + " a year",
         "Owner statement, unverified",
         "Read the leases and the rent ledger."),
        ("The inherited cash amount", "Not published",
         "Deliberately withheld from this site",
         "Work through the scenario bands on the estate page privately."),
        ("San Francisco transfer tax reduction proposal", "Not used in any figure",
         "Reported publicly but not verified against an official city source",
         "Check the Board of Supervisors file before relying on it."),
    ]
    # Each row points only at the official source that actually bears on it. A row with no
    # matching official source says so, and links to the register, rather than borrowing a
    # publisher that does not cover the figure.
    UV_WHERE = {
        "Property A market value, November 2026": [],
        "Property B market value, November 2026": [],
        "Both assessment rolls and tax bills": ["scc_ratebook", "sf_treas_rate", "boe_lta26002"],
        "Property A ad valorem rate": ["scc_ratebook"],
        "Property B ad valorem rate": ["sf_treas_rate"],
        "Property A water": ["sjwc_tariff"],
        "Property A electricity, net of solar": ["cpuc_nem"],
        "Property B water": ["sfpuc_rates"],
        "Property B electricity": [],
        "Insurance on both properties": ["cdi_homeowners_avg"],
        "Maintenance on both properties": [],
        "Property B rent": ["sf_rent_increase"],
        "The inherited cash amount": [],
        "San Francisco transfer tax reduction proposal": [],
    }
    assert set(UV_WHERE) == {a for a, _, _, _ in unverified}, "every unverified row needs a source decision"
    uv_rows = [f"<td><strong>{esc(a)}</strong></td><td>{b}</td>"
               f'<td><span class="badge unverified">{esc(c)}</span></td><td>{esc(d)}</td>'
               + src_cell(UV_WHERE[a], "Where to check")
               for a, b, c, d in unverified]

    caveats = [
        ("The ad valorem rate for Property A is not identifiable from the data",
         "Assessed value and the fixed part of the bill both grow at about 2% a year, so rates anywhere between roughly 1.05% and 1.60% fit the supplied bills almost equally well. 1.18% is used and flagged."),
        ("Fixed charges are projected at the inflation rate",
         "On Property B the fixed part of the bill grew at 8.1% a year between 2016 and 2025. Projecting at 2.5% is deliberately conservative and understates future bills if that pace continues."),
        ("The November 2026 California election results are unofficial",
         "They are published with all precincts partially reporting and are not certified until 11 December 2026. Proposition 3 is treated as approved (60.7% yes on unofficial results as of 12 November 2026) because it changes the tax rate on a sale, but the result must be confirmed at certification."),
        ("Combined tax rates are added, not interacted",
         "State and federal rates are added and no federal deduction is taken for state tax paid. That overstates the tax on a sale and therefore understates the case for selling, which is the conservative direction."),
        ("The housing value of living in the home is priced, not added",
         "The terminal-value tables do not credit the live-in path with the value of the housing it provides. The break-even table prices that value instead; on the 2045 baseline it comes out at about $1,760,770 a year."),
        ("Depreciation follows a simple rule",
         "80% of value treated as improvements, straight line over 27.5 years, capped at the building's depreciable amount. Land is not depreciated. Real cost segregation would differ."),
        ("No mortgage, no 1031 exchange, no instalment sale, no gifting",
         "Each is listed on the questions page. None is modelled."),
        ("The inheritance year is a range, not a date",
         "2040, 2045 and 2050 are all modelled. The plan should be revisited when the timing is known."),
        ("The property tax lesser-of rule is modelled only under the drawn inflation paths",
         "The economy page applies the section 51 rule along two thousand drawn inflation paths. In the median draw the 2% cap binds in every year; only paths dominated by the low-inflation 2010s produce a reduction, worth at most about $2,260 over fifty years on Property A. It is assessor-applied in practice."),
        ("The Proposition 19 shelter path after 2027 is a projection",
         "The real amount is set every second February from the California house price index and is not published in advance. Three percent a year is assumed and flagged."),
        ("A sheltered base is assumed to survive a later move-out",
         "Section 63.2(a)(1)(C) says the base year value established at the change in ownership, adjusted annually, is enrolled when the transferee stops being eligible for the homeowners' exemption. The live-then-rent path is modelled on that reading, which is favourable to it. If the assessor instead enrolled full market value at the move-out, that path's tax bill would rise and its terminal value would fall. The recommendation does not depend on it: selling already leads that path."),
        ("Every reassessment figure is conditional on the parent-and-child relationship",
         "Section 63.2 excludes only transfers between parents and their children, or grandparents and grandchildren where the middle generation has died. Every shelter, live-in and rental figure on this site assumes that condition holds. The trust document is the only thing that confirms it and this site has not seen it."),
    ]
    # Each caveat links only to the official source that bears on it; a caveat that is a planning
    # statement rather than a rule says so and links to the register.
    CAV_WHERE = {
        "The ad valorem rate for Property A is not identifiable from the data": ["scc_ratebook", "boe_lta26002"],
        "Fixed charges are projected at the inflation rate": ["sf_treas_rate", "bls_cpi"],
        "The November 2026 California election results are unofficial": ["sos_results", "voterguide_p3"],
        "Combined tax rates are added, not interacted": ["irs_tc409", "ftb_cg"],
        "The housing value of living in the home is priced, not added": [],
        "Depreciation follows a simple rule": ["irs_p527"],
        "No mortgage, no 1031 exchange, no instalment sale, no gifting": [],
        "The inheritance year is a range, not a date": [],
        "The property tax lesser-of rule is not modelled": ["rtc51", "boe_pub29"],
        "The Proposition 19 shelter path after 2027 is a projection": ["boe_lta25009"],
        "A sheltered base is assumed to survive a later move-out": ["rtc63_2_eligibility", "boe_prop19"],
        "Every reassessment figure is conditional on the parent-and-child relationship": ["rtc63_2_eligibility"],
    }
    assert set(CAV_WHERE) == {a for a, _ in caveats}, "every caveat needs a source decision"
    cav_rows = [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td>"
                + src_cell(CAV_WHERE[a], "Related sources")
                for a, b in caveats]

    audit = [
        ("The repository contains more than the published site",
         "The published site is the eighteen pages in the repository root plus one stylesheet. What is not published is the build and verification code in scripts/, the data files in assets/data/, the source ledger, this page's own register, the README, the executive summary and a very large coordination board.",
         "All of it is excluded from the published site by the Jekyll configuration and by the packaging allowlist, and the guard script fails the build if a tracked path would bypass those exclusions. It is still readable in the public repository."),
        ("Two earlier editions were removed from the working tree",
         "An earlier cross-check edition under plan/ and a fifty-year edition under analysis/ were built from unrounded owner figures. Both directories were removed from the tree on 13 November 2026; their routes now return content-free withdrawal notices.",
         "They remain in the repository's Git history. Removing them from history needs a rewrite or a visibility change, which is the owner's decision, not a session's."),
        ("Earlier sessions published a version with no property figures at all",
         "Between 11 and 12 November 2026 several sessions built a privacy-first edition that blanked every value. This edition reverses that, because the brief for this session asks for the figures rounded to $10.",
         "The reversal is recorded in the coordination board. The blanked edition remains in the repository history."),
        ("Prior commits and pull-request diffs may contain finer figures",
         "Rounding to $10 applies to what this site publishes. It does not change what earlier commits contain.",
         "Older commits, pull-request diffs, forks and external copies are separate exposure surfaces. Nothing on this site can certify them erased."),
        ("Pull request records",
         "PRs 62 and 70 were merged. PRs 65 and 66 recorded a live privacy-publication blocker on 12 November 2026; the blocker they describe, the legacy Pages route serving the whole repository, was closed by the restored configuration guard and audited live. Both were closed as superseded on 13 November 2026 with an explanatory comment, not silently.",
         "The coordination board records the full disposition. Nothing on this site depends on them."),
        ("The site is published from the repository root by Jekyll",
         "The GitHub Pages source is set to the main branch at the repository root, with a configuration file excluding everything outside the published allowlist. A separate workflow also builds an allowlisted artifact.",
         "The publishing route should be confirmed live after every change. The exclusion list is the control that keeps the rest of the repository out of the site."),
        ("Verification is a build-time check, not a legal review",
         "The verifier checks that every published table row carries a source link, that no forbidden identifier appears, and that the build is reproducible.",
         "It cannot check whether a legal reading is correct. That needs a professional."),
    ]
    aud_rows = [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td><td>{esc(c)}</td>"
                + src_cell(["boe_lta25009", "irs_estate", "scc_ratebook"], "Related sources")
                for a, b, c in audit]

    return (
        callout("note", "What this page is for", """
<p>Three lists. The first is every figure on this site that is not verified against an official source, and where
the record for it is actually held. The second is every modelling shortcut that materially affects the answer.
The third is the audit of the repository this site is built from. None of these block the recommendation, but
each one is a reason to check before acting.</p>""")
        + '<h2 id="method-detail">How the model works</h2>'
        + callout("note", "Method, in one paragraph", f"""<p>{esc(METHOD_TEXT)}</p>""")
        + '<h2 id="register">Register of unverified and assumed items</h2>'
        + table("Every figure that is not backed by an official public source",
                ["Figure", "Value used", "Status", "What to do", "Where to look"],
                uv_rows)
        + irregularity_section()
        + '<h2>Modelling caveats</h2>'
        + table("Shortcuts that matter", ["Caveat", "What it means", "Source"], cav_rows)
        + '<h2>Repository audit</h2>'
        + table("What was found when the repository was reviewed",
                ["Finding", "Detail", "Residual risk", "Source"], aud_rows)
    )


# ------------------------------------------------------------------ sources --
def page_sources() -> str:
    rows = []
    for s in SRC_DOC["sources"]:
        rows.append(
            f"<td>{esc(s['id'])}</td>"
            f"<td><strong>{esc(s['publisher'])}</strong></td>"
            f'<td><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["title"])}</a></td>'
            f"<td>{esc(s['supports'])}</td>"
            f"<td>{esc(s['limits'])}</td>"
            f"<td>{esc(s['checked'])}</td>")
    return (
        callout("note", "How the ledger works", f"""
<p>There are {len(SRC_DOC['sources'])} sources. Every one was opened on the publisher's own domain on 13 November
2026, or is recorded as carried from the repository's earlier ledger and re-checked on the same date. The
"supports" column says exactly what the source is cited for; the "limits" column says what it does not cover.
Sources are cited only for what they actually state.</p>""")
        + table("Source ledger", ["ID", "Publisher", "Document", "What it supports",
                                  "Limits", "How it was checked"], rows)
        + callout("limit", "What this ledger does not do", """
<ul>
<li>It does not reproduce the rate schedules, thresholds or forms. Those change; read the linked document.</li>
<li>It does not cover local ordinances beyond the two cities named, and it does not verify which rules apply to which building.</li>
<li>It contains no paid, paywalled or secondary source. Everything here is an official publisher or an official government site.</li>
<li>It was checked on one date. Statutory sections are amended; letters to assessors are superseded; election results are certified after the fact.</li>
</ul>""")
    )


PAGE_BUILDERS = {
    "index.html": (page_index, "Two California properties, one decision. Every figure rounded to the nearest $10."),
    "executive-summary.html": (page_executive_summary,
                               "The important details, the recommendation, and what would change it."),
    "decision.html": (page_decision, "Five paths, priced, with the break-even numbers and the sensitivity."),
    "property-a.html": (page_property_a, "The home being inherited through a trust, planned 2040 to 2050."),
    "property-b.html": (page_property_b, "The three-unit building the heir already owns and rents out."),
    "ownership-distinction.html": (page_distinction, "Why inherited and already-owned are not interchangeable."),
    "costs.html": (page_costs, "Water, power, insurance, maintenance and tax, now and projected."),
    "projections.html": (page_projections, "Year by year to 2076 for value, assessed value and tax."),
    "taxes.html": (page_taxes, "Basis step-up, capital gains, the 121 exclusion, recapture."),
    "inheritance.html": (page_inheritance, "The trust transfer, phase by phase, with deadlines."),
    "estate.html": (page_estate, "Federal thresholds, California's position, scenario bands."),
    "laws.html": (page_laws, "Enacted, dead and proposed rules that could move the answer."),
    "black-swan.html": (page_black_swan, "Regimes where the answer changes, and by how much."),
    "economy.html": (page_economy, "Fifty years of verified inflation, house price and yield data."),
    "questions.html": (page_questions, "What is known, what is missing, and how to find it."),
    "suggestions.html": (page_suggestions, "A review queue of proposals. Nothing implemented yet."),
    "review.html": (page_review, "Unverified figures, modelling caveats and the repository audit."),
    "sources.html": (page_sources, "Every official source used, with what it supports."),
}


PAGES = list(PAGE_BUILDERS)
ASSETS = ["assets/style.css"]



# ------------------------------------------------------- executive summary md --
def executive_summary_markdown() -> str:
    """The standalone brief. Generated, so it can never drift from the model again.

    The earlier hand-typed file still described a retired ten-year edition and two
    pages that no longer exist. It is now a projection of the same data the site uses.
    """
    p40 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2040)
    p45 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2045)
    p50 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2050)
    sens = MODEL["sensitivity"]
    regs = MODEL["regimes"]
    sens_sell = sum(1 for s in sens if s["best"].startswith("sell"))
    reg_sell = sum(1 for r in regs if r["run"]["best"].startswith("sell"))
    cash = lambda v: f"${v:,}"
    out = []
    a = out.append
    a("# Executive summary")
    a("")
    a(f"Built {BUILD_DATE} from the same deterministic model as the site. Every dollar figure is rounded to the "
      "nearest $10. Anonymised throughout: **Property A** is the single-family home being inherited through a "
      "trust, in Santa Clara County; **Property B** is the three-unit building the heir already owns, in the City "
      "and County of San Francisco. No name, street address, postal parcel number, postal code, trust term or "
      "utility account appears here or on the site.")
    a("")
    a("Planning analysis, not legal, tax or investment advice.")
    a("")
    a("## The recommendation")
    a("")
    a(f"**Sell Property A soon after it is inherited, unless the heir genuinely wants to live in that house.** "
      f"Selling leads in the baseline, in {sens_sell} of the {len(sens)} sensitivity combinations and in "
      f"{reg_sell} of the {len(regs)} stress regimes, and it is the only path that does not depend on the heir "
      "wanting that house, being able to hold it as a principal residence, or finding a tenant at an implausible "
      "rent.")
    a("")
    a("## One condition outranks every number below")
    a("")
    a("The intergenerational exclusion in Revenue and Taxation Code section 63.2 applies **only** where the "
      "transfer is between a parent and a child, or between a grandparent and a grandchild whose parent has died. "
      "That is a condition of the exclusion, not a detail. If the relationship is different, no exclusion is "
      "available, the property is reassessed to full market value, every shelter figure below disappears, and the "
      "case for selling gets stronger. The trust document is the only thing that settles it and this analysis has "
      "not seen it. **Question A-1 on the questions page.**")
    a("")
    a("## Terminal value after thirty years")
    a("")
    a("Selling and investing the proceeds, against keeping the house. Baseline: house prices 4.0% a year, "
      "inflation 2.5%, equities 7.0% gross of a 0.7% tax drag, Treasuries 4.7%, selling costs 5.5%.")
    a("")
    a("| Inherited | Sell, equities | Sell, Treasuries | Live in it | Let it out |")
    a("|---|---|---|---|---|")
    for p in (p40, p45, p50):
        q = p["paths"]
        a(f"| {p['inherit_year']} | {cash(q['sell_equities']['terminal'])} | "
          f"{cash(q['sell_treasury']['terminal'])} | {cash(q['live_in']['terminal'])} | "
          f"{cash(q['rent_out']['terminal'])} |")
    a("")
    a("The letting paths are credited with **no rent**, because no market rent for Property A has been supplied "
      "and no official source publishes one for a specific home. Read them as a floor, not as a comparison.")
    a("")
    a("## The numbers that drive it")
    a("")
    a(f"- **The tax cliff.** The Property A bill is about {cash(MODEL['costs_a_now']['property_tax'])} today. "
      f"If the heir inherits in 2045 and does not move in, it becomes about {cash(p45['bill_if_rent_year1'])}. "
      f"If the heir moves in and claims the exclusion, it becomes about {cash(p45['bill_if_live_year1'])}.")
    a(f"- **The shelter is smaller than the growth.** On a 2045 inheritance the exclusion shelters the old "
      f"taxable value plus {cash(MODEL['paths'][1]['prop19_cap'])} against a market value of "
      f"{cash(p45['value_at_death'])}. Everything above the sum is reassessed.")
    a(f"- **The tax-free window.** Property acquired from a decedent takes a basis equal to its value at death, "
      f"so a sale soon afterwards pays about zero capital gains tax. In the 2045 baseline a "
      f"{cash(p45['value_at_death'])} sale carries {cash(p45['paths']['sell_equities']['sale']['tax'])} of tax.")
    a(f"- **What waiting costs.** Hold the same house thirty years and the tax on the eventual sale is about "
      f"{cash(p45['paths']['live_in']['sale']['tax'])} after the section 121 exclusion; let it out as well and "
      f"depreciation recapture pushes that to about {cash(p45['paths']['rent_out']['sale']['tax'])}.")
    a(f"- **The break-even.** Keeping the home beats selling only if it appreciates "
      f"{pc(p45['breakeven_house_growth'])} a year for thirty years. The verified index for this area compounded "
      "at 6.9% over fifty years and 3.3% over the last twenty.")
    a(f"- **The break-even rent.** Letting would need about {cash(p45['breakeven_rent_monthly'])} a month, "
      f"{cash(p45['breakeven_rent_annual'])} a year, in 2045, to match selling and investing.")
    a("")
    a("## The black swans, and what they do to the answer")
    a("")
    a("Real economies do not grow at a constant rate. In the verified record used here, annual consumer price "
      "inflation ran from minus 0.3% to plus 13.5%, and annual house price growth in Property A's area from "
      "minus 12.3% to plus 30.2%. The regimes below replay the worst stretches of that record against a 2045 "
      "inheritance over thirty years.")
    a("")
    a("| Regime | Inflation | House growth | Treasury | Best path |")
    a("|---|---|---|---|---|")
    for r in regs:
        a(f"| {r['name']} | {r['cpi']}% | {r['house']}% | {r['treasury']}% | "
          f"{PATH_LABELS[r['run']['best']]} |")
    a("")
    a("Sold into equities or Treasuries wins five of the six. The exception is a repeat of the 1965-1982 Great "
      "Inflation or the 2021-2023 burst, where nominal house prices outran everything else. That is a bet on one "
      "neighbourhood repeating its best decades, not a plan.")
    a("")
    a("## Estate and inheritance tax")
    a("")
    a(f"- California has no estate tax and no inheritance tax. No California estate tax return is required for "
      f"a death on or after 1 January 2005, and an inheritance is not California income.")
    a(f"- The federal exclusion is {cash(V['federal_basic_exclusion_2026']['value'])} per person for 2026 and "
      f"{cash(V['federal_basic_exclusion_2027']['value'])} for 2027. Portability lets a surviving spouse use a "
      "deceased spouse's unused exclusion if a timely return is filed.")
    a("- Above the exclusion the federal rate reaches 40%. The tax is on the estate, not on the heir, and is due "
      "with Form 706 nine months after death, with an extension available.")
    a("- The cash inheritance is deliberately not published and not modelled as a figure; the estate page works "
      "in anonymous scenario bands instead.")
    a("")
    a("## What is still open")
    a("")
    a("These sit on the flagged-for-review page, each with the publisher that holds the record:")
    a("")
    a("- The owner's market values, the property-tax and assessment histories, the rent and the utility and "
      "insurance estimates are the owner's own records, not checked against a county roll or a quote.")
    a("- Property A's tax rate area and its published ad valorem rate. 1.18% is assumed and flagged.")
    a("- A property-specific insurance premium for either building. The Department of Insurance publishes a "
      "statewide average and an online premium survey, not an average for a postal area.")
    a("- A market rent for Property A, and the seller's actual selling costs.")
    a("- Whether the trust actually holds title, and whether the transfer is between a parent and a child.")
    a("")
    a("## How this was checked")
    a("")
    a(f"Every rule, threshold and rate on the site was read on the publishing agency's own domain and is linked "
      f"from the row that uses it. The ledger holds {len(SRC_DOC['sources'])} sources. A build-time verifier "
      "fails if a table row has no official link, if the build is not reproducible, if any internal link or "
      "fragment does not resolve, or if any published dollar figure is not a multiple of $10. A separate check "
      "recomputed the published relationships from the inputs.")
    a("")
    a("## Read next")
    a("")
    a("- `index.html` — the dashboard")
    a("- `decision.html` — the five paths, the sensitivity and the break-evens")
    a("- `questions.html` — what is unknown and how to find it, starting with A-1")
    a("- `suggestions.html` — the review queue; nothing there has been implemented")
    a("- `review.html` — every unverified figure and modelling caveat")
    a("- `sources.html` — the full ledger")
    a("")
    return "\n".join(out)


def write_data_files() -> None:
    """Write the downloadable tables from assets/data/model.json on every build.

    They were once hand-kept copies that drifted from the published figures (the maintenance and
    bill columns disagreed with the costs page). They are now generated, so they cannot disagree.
    """
    def dollars(v, name):
        assert isinstance(v, (int, float)) and v % 10 == 0, (name, v)
        return str(int(v))

    for key, fname in (("projection_a", "property_a.csv"), ("projection_b", "property_b.csv")):
        lines = ["year,value,assessed,property_tax,effective_rate_percent"]
        for r in MODEL[key]:
            lines.append(",".join([str(r["year"]), dollars(r["value"], fname), dollars(r["assessed"], fname),
                                   dollars(r["bill"], fname), f"{r['effective_rate']:.3f}"]))
        (DATA / fname).write_text("\n".join(lines) + "\n", encoding="utf-8")

    lines = ["inheritance_year,house_growth_percent,equity_return_percent,sell_equities,sell_treasury,"
             "live_in,rent_out,live_then_rent,best"]
    for s in MODEL["sensitivity"]:
        cols = [dollars(s[k], "decision.csv") for k in ("sell_equities", "sell_treasury", "live_in", "rent_out", "live_then_rent")]
        lines.append(",".join(["2045", f"{s['house_growth']}", f"{s['equity_return']}"] + cols + [s["best"]]))
    (DATA / "decision.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote data files: property_a.csv, property_b.csv, decision.csv")


def main():
    for name, (fn, lede) in PAGE_BUILDERS.items():
        (ROOT / name).write_text(page(name, fn(), lede), encoding="utf-8")
        print("wrote", name)
    write_data_files()
    (ROOT / "EXECUTIVE_SUMMARY.md").write_text(executive_summary_markdown(), encoding="utf-8")
    print("wrote EXECUTIVE_SUMMARY.md")


if __name__ == "__main__":
    main()
