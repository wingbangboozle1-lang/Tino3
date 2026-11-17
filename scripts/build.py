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
SERIES = json.loads((DATA / "series.json").read_text(encoding="utf-8"))
MIXED = json.loads((DATA / "mixed.json").read_text(encoding="utf-8"))
LIQ = json.loads((DATA / "liquidity.json").read_text(encoding="utf-8"))
BORROW = json.loads((DATA / "borrow.json").read_text(encoding="utf-8"))
PRECOMMIT = INPUTS.get("precommit", {"rules": [], "household_goals": [], "review_gates": [], "meta": {}})

A = INPUTS["property_a"]
B = INPUTS["property_b"]
V = INPUTS["verified_parameters"]
ASM = INPUTS["assumptions"]
# The edition date lives in one module so the model metadata and the page footers
# cannot drift apart. It is a constant, not the clock, so a rebuild is byte-stable.
from edition import BUILD_DATE_TEXT, SOURCES_CHECKED_FROM, SOURCES_CHECKED_TO  # noqa: E402
BUILD_DATE = BUILD_DATE_TEXT

# The phased-investing figures are computed by the model's one monthly engine, so the
# stress table on the black-swan page and the dashboard path cannot drift apart again.
import model as model_mod  # noqa: E402
import print_budget as print_budget_mod  # noqa: E402

NAV_GROUPS = [
    ("Start here", ["index.html", "precommit.html", "executive-summary.html", "decision.html",
                    "decision-rules.html",
                    "what-if.html", "briefing.html"]),
    ("The two properties", ["property-a.html", "property-b.html", "ownership-distinction.html"]),
    ("Money over time", ["costs.html", "projections.html", "taxes.html",
                  "keep-and-borrow.html"]),
    ("Rules and the estate", ["inheritance.html", "timeline.html", "estate.html", "liquidity.html",
                    "laws.html"]),
    ("Black swan economics", ["black-swan.html", "economy.html"]),
    ("Review before deciding", ["questions.html", "suggestions.html", "review.html"]),
    ("Evidence", ["glossary.html", "sources.html"]),
]
PAGE_TITLES = {
    "index.html": "Dashboard",
    "precommit.html": "Decide before you read the numbers",
    "what-if.html": "What-if cases",
    "decision-rules.html": "Decision rules and investment policy (unsigned draft)",
    "executive-summary.html": "Executive summary",
    "decision.html": "The decision",
    "briefing.html": "Attorney & CPA briefing sheet (one page, printable)",
    "property-a.html": "Property A - the home being inherited",
    "property-b.html": "Property B - the building already owned",
    "ownership-distinction.html": "Why the two properties are not the same",
    "costs.html": "Running costs",
    "projections.html": "Year by year projections",
    "taxes.html": "Income tax on each path",
    "inheritance.html": "Inheriting through a trust, step by step",
    "estate.html": "Estate and inheritance tax thresholds",
    "liquidity.html": "Estate liquidity and borrowing",
    "keep-and-borrow.html": "Keep the house, take the cash",
    "laws.html": "What the law says now, and what may change",
    "black-swan.html": "Black swan conditions",
    "economy.html": "The verified historical record",
    "questions.html": "Questions to answer before deciding",
    "suggestions.html": "Suggestions for review",
    "review.html": "Flagged for review and repository audit",
    "glossary.html": "Glossary of terms",
    "timeline.html": "Deadlines and key dates",
    "sources.html": "Source ledger",
}


# ------------------------------------------------------------------ helpers --
BLANK_CELL = '<span class="blank">not supplied</span>'

# Deferral terms published on the liquidity page, longest first is not used: the page
# prints them in the order below so the reader can watch the cost grow with the term.
TERMS_LIQ = [1, 3, 5, 10]

# Lines of a blank estate-inventory worksheet. Every cell the household fills in stays
# private: nothing here carries a value, and nothing here is ever published.
INVENTORY_ITEMS = [
    "The home being inherited (Property A)",
    "Any other real property",
    "Cash, chequing and savings",
    "Marketable securities",
    "Retirement accounts",
    "Life insurance",
    "Business interests",
    "Personal property and vehicles",
    "Debts, mortgages and other liabilities",
    "Prior taxable gifts already made (these reduce the exclusion)",
]

# The largest tax the joint return saves anywhere in the model, read from the data rather
# than typed, so the executive summary cannot drift from the liquidity engine.
JOINT_121_MAX_SAVING = max(r["saving"] for r in LIQ["joint_case"]["rows"])


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


SELL_KEYS = ("sell_equities", "sell_treasury")


def regime_facts() -> dict:
    """Stress-regime results, read from the model so the prose cannot drift from the numbers."""
    regs = MODEL["regimes"]
    sell = [r for r in regs if r["run"]["best"] in SELL_KEYS]
    keep = [r for r in regs if r["run"]["best"] == "live_in"]
    let_ = [r for r in regs if r["run"]["best"] in ("rent_out", "live_then_rent")]
    lowest_let = [r for r in regs
                  if min(r["run"]["terminal"], key=r["run"]["terminal"].get) == "rent_out"]
    return {
        "n": len(regs), "sell": len(sell), "keep": keep, "let": len(let_),
        "lowest_let": len(lowest_let),
        "keep_names": "; ".join(r["name"] for r in keep) or "none",
    }


RF = regime_facts()


def ret_cell(x) -> str:
    """A break-even return. Negative means selling beats the alternative even if the sale proceeds lose that much a year."""
    if x is None:
        return '<span class="blank">not reachable</span>'
    if x < 0:
        return f"{x:.2f}% a year (negative: the sale still wins if the proceeds lose this much a year)"
    return f"{x:.2f}% a year"


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
    """A computed row. Links the method page and the official sources that bear on the row.

    ``sources=None`` keeps the historical blanket CORE_SOURCES set for any call site that
    has not been attributed yet. ``sources=[]`` is an explicit decision that the row has no
    official source of its own (an owner figure, a stated scenario, a household rule or a
    private quote): the cell then says so and links the register instead of implying
    official backing. Per-row attribution is the rule; the blanket set is the fallback."""
    ids = CORE_SOURCES if sources is None else list(sources)
    if ids:
        links = "<br>".join(slink(i) for i in ids)
    else:
        links = ('<span class="blank">no official source</span><br>'
                 '<a class="src" href="review.html#register">Logged on the register</a>')
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


# ---------------------------------------------------------------- charts ------
# The published site carries no script element, so every chart is built from
# divs and the values are printed beside it in text. The chart is a reading aid
# for a table, never the only place a number appears.


def _num(x) -> str:
    """A money figure for chart axis labels and printed values."""
    return f"{x:,}"


def fan_chart(title: str, sub: str, unit: str, rows: list[dict], note: str) -> str:
    """Decile fan chart: one row per decile across three compared series.

    rows = [{"label": "p10", "values": [("sell", 123, "Sell"), ...]}, ...]
    Bars are scaled to the largest absolute value in the whole chart, so the
    three series are compared on one axis rather than three.
    """
    peak = max((abs(v) for r in rows for _, v, _ in r["values"]), default=1) or 1
    body = []
    for r in rows:
        bars = []
        for cls, v, name in r["values"]:
            width = abs(v) / peak * 100.0
            label = f"{_num(v)}" if unit == "money" else f"{v:.2f}%"
            bars.append(f'<div class="track" title="{esc(name)} {esc(label)}">'
                        f'<div class="fill {cls}" style="width:{width:.1f}%"></div></div>')
        vals = " / ".join(
            (f"{_num(v)}" if unit == "money" else f"{v:.2f}%") for _, v, _ in r["values"])
        body.append(f'<div class="lbl">{esc(r["label"])}</div>' + "".join(bars)
                    + f'<div class="val">{vals}</div>')
    cols = 1 + len(rows[0]["values"]) + 1
    legend = "".join(f'<span><i class="swatch {esc(cls)}"></i>{esc(name)}</span>'
                     for cls, _, name in rows[0]["values"])
    return (f'<div class="chart"><h3>{esc(title)}</h3><p class="chart-sub">{sub}</p>'
            f'<div class="fan" style="grid-template-columns:92px repeat({len(rows[0]["values"])}, 1fr) 150px">'
            + "".join(body) + "</div>"
            f'<div class="chart-legend">{legend}</div>'
            f'<p class="chart-sub" style="margin:8px 0 0">{note}</p></div>')


def histogram(title: str, sub: str, counts: list[int], lo: int, hi: int,
              zero_pos: float, share: float, note: str) -> str:
    """Histogram of one distribution, with the zero line drawn on it."""
    peak = max(counts) or 1
    bars = []
    n = len(counts)
    for i, c in enumerate(counts):
        centre = (i + 0.5) / n
        cls = "win" if centre > zero_pos else "lose"
        h = c / peak * 100.0
        bars.append(f'<div class="bar {cls}" style="height:{h:.1f}%" '
                    f'title="{c} draws"></div>')
    zero = max(0.0, min(100.0, zero_pos * 100.0))
    axis = (f'<div class="hist-axis"><span>{_num(lo)}</span>'
            f'<span>zero at {_num(0)}</span><span>{_num(hi)}</span></div>')
    return (f'<div class="chart"><h3>{esc(title)}</h3><p class="chart-sub">{sub}</p>'
            f'<div class="hist">{"".join(bars)}'
            f'<div class="hist-zero" style="left:{zero:.1f}%"></div></div>{axis}'
            f'<div class="chart-legend">'
            f'<span><i class="swatch sell"></i>Selling ahead</span>'
            f'<span><i class="swatch zero"></i>Zero line</span>'
            f'<span><i class="swatch live"></i>Keeping the home ahead</span></div>'
            f'<p class="chart-sub" style="margin:8px 0 0">{note} '
            f'Selling is ahead in <strong>{share*100:.1f}%</strong> of the draws.</p></div>')


def meter_chart(title: str, sub: str, rows: list[tuple[str, int, str]], note: str) -> str:
    """Horizontal bars for a handful of named values on one scale."""
    peak = max((abs(v) for _, v, _ in rows), default=1) or 1
    body = []
    for name, v, cls in rows:
        width = abs(v) / peak * 100.0
        body.append(f'<div>{esc(name)}</div><div class="track">'
                    f'<div class="fill {cls}" style="width:{width:.1f}%"></div></div>'
                    f'<div class="val">{_num(v)}</div>')
    return (f'<div class="chart"><h3>{esc(title)}</h3><p class="chart-sub">{sub}</p>'
            f'<div class="meter">{"".join(body)}</div>'
            f'<p class="chart-sub" style="margin:8px 0 0">{note}</p></div>')


def decision_strip(headline: str, answer: str, confidence: str, confidence_label: str,
                   built: str, changed_by: list[str]) -> str:
    """The first screen: the answer, how sure it is, when it was computed, what moves it."""
    items = "".join(f"<li>{c}</li>" for c in changed_by)
    return f"""<section class="decision-strip">
<h2>{esc(headline)}</h2>
<p class="answer-line">{answer}</p>
<p class="meta-line">Confidence: <span class="confidence {esc(confidence)}">{esc(confidence_label)}</span>
 &middot; Computed {esc(built)} from the inputs on this site &middot; It moves only if one of these changes:</p>
<ul class="change-list">{items}</ul>
</section>"""


METHOD_TEXT = (
    "A deterministic model, rebuilt from assets/data/inputs.json and assets/data/series.json by "
    "scripts/model.py. House prices grow at a stated nominal rate, the assessed value rolls forward under the "
    "published rules with an inflation cap, fixed charges grow with inflation, running costs are inflated at "
    "the same rate, and each path is valued at the end of a thirty year horizon after selling costs and tax. "
    "On the paths that keep or let the house, every year's property tax and running costs are deducted at their "
    "compounded future value at the after-tax equity return, so the living and letting paths bear the same cash costs "
    "that the sell paths are spared. "
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
<body class="{'print-brief-page' if name == 'briefing.html' else ''}">
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
  <main id="main" class="{'print-brief' if name == 'briefing.html' else ''}">
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
    <p class="page-footer">Built {esc(BUILD_DATE)}. Sources were last checked between
    {esc(SOURCES_CHECKED_FROM)} and {esc(SOURCES_CHECKED_TO)};
      each entry's own check date is listed on the
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
<li><strong>What is never published.</strong> No name, street address, parcel number, ZIP code, county or city name, trust term, beneficiary detail or utility account appears on any page or in any published file. The two properties are called Property A (the home being inherited) and Property B (the three-unit building already owned by the heir). Their county and city are deliberately withheld: like the parcel, they identify the properties, so official county and city pages are not linked from the public site either.</li>
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
def distribution_section(dist: dict, sell_share: float) -> str:
    """The dashboard's distribution chart: deciles of the resampled histories."""
    by_key = {s["key"]: s for s in dist["series"]}
    sell = by_key["sell"]
    live = by_key["live"]
    mid = by_key["live10_sell"]
    rows = []
    for i in range(11):
        rows.append({
            "label": "p100" if i == 10 else f"p{i*10}",
            "values": [("sell", sell["deciles"][i], "Sell and invest"),
                       ("live", live["deciles"][i], "Live in it 30 years"),
                       ("mid", mid["deciles"][i], "Live 10 years, then sell")],
        })
    chart = fan_chart(
        "Thirty years later: the range of outcomes, not one line",
        f"Deciles of {dist['draws']} resampled fifty-year histories of the verified record: the "
        f"California house price index and consumer prices drawn together in ten-year blocks, "
        f"each draw run through the same model. Bars and printed values are the same figures.",
        "money", rows,
        "The bottom of each distribution is a bad run: house prices compounding at about 2.8% a "
        "year while the sell path still earns the modelled equity return. The top is a good one. "
        "The point is the shape: the two distributions overlap below p60 and separate above it.")
    hist = histogram(
        "How often selling wins, and by how much",
        "The sell-minus-keep gap over the same draws. Positive means selling at the inheritance "
        "left the household ahead after thirty years.",
        dist["histogram"]["counts"], dist["histogram"]["lo"], dist["histogram"]["hi"],
        dist["histogram"]["zero_position"], sell_share, dist["histogram"]["note"])
    return ('<section id="distribution"><h2>The whole range, not the headline number</h2>'
            f'<p>Every headline on this site is one number from one set of assumptions. The charts '
            f'below replace the single line with the distribution: {dist["draws"]} resampled '
            f'histories of the verified record, each one put through the same model. Walk the '
            f'<a href="projections.html#fan">year-by-year fan chart</a> as well, and read the method '
            f'on the <a href="economy.html">economy page</a>.</p>'
            + chart + hist + "</section>")


# --------------------------------------------------------------------- chart --
def dist_chart(chart: dict, title: str) -> str:
    """A CSS-only range chart. No script, so the geometry is written at build time.

    Each row is one year: a shaded p05-p95 band, a median tick, and a marker for
    the single constant-rate line the rest of the site uses. The axis is shared
    across rows so the bands are comparable down the page. The numbers are also
    in the table beneath it, so the chart is not the only way to read them.
    """
    if not chart or not chart.get("years"):
        return ""
    # Round the axis top like every other published figure. The gate checks
    # this, and it is right to: the axis label is a published number.
    top = money10(max(y["p95"] for y in chart["years"]) * 1.02)
    rows, ticks = [], [0]
    years = chart["years"]
    step = max(1, len(years) // 10)
    for i, y in enumerate(years):
        lo = 100.0 * y["p05"] / top
        hi = 100.0 * y["p95"] / top
        med = 100.0 * y["p50"] / top
        const = 100.0 * y["constant"] / top
        rows.append(
            f'<div class="chart-year">{y["year"]}</div>'
            f'<div class="chart-track" role="img" aria-label="{y["year"]}: low '
            f'{m(y["p05"])}, middle {m(y["p50"])}, high {m(y["p95"])}, constant-rate line {m(y["constant"])}">'
            f'<span class="chart-band" style="--lo:{lo:.2f};--hi:{hi:.2f}"></span>'
            f'<span class="chart-const" style="--c:{const:.2f}"></span>'
            f'<span class="chart-med" style="--m:{med:.2f}"></span>'
            f'</div>')
        if i % step == 0 or i == len(years) - 1:
            ticks.append(i)
    labels = "".join(
        f'<span>{years[i]["year"]}: {m(years[i]["p05"])}</span>' if j == 0 else
        f'<span style="text-align:center">{years[i]["year"]}</span>' if j == len(ticks) - 1 else
        f'<span>{years[i]["year"]}</span>'
        for j, i in enumerate(ticks))
    return (
        f'<div class="chart"><h3>{esc(title)}</h3>'
        f'<p class="chart-note">{esc(chart["note"])}</p>'
        f'<div class="chart-rows">{"".join(rows)}</div>'
        f'<div class="chart-axis"><span></span><span>'
        f'start {m(chart["start_value"])} &rarr; axis top {m(top)}</span></div>'
        f'<div class="chart-key">'
        f'<span><i class="k-band"></i>5th to 95th percentile of 2,000 resampled paths</span>'
        f'<span><i class="k-med"></i>middle path</span>'
        f'<span><i class="k-const"></i>the model\'s single constant rate</span>'
        f'</div></div>')


def page_index() -> str:
    p45 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2045)
    best = p45["best_path"]
    # What staging costs when no crash arrives: the phased terminal against immediate
    # investment, both computed by the one monthly engine.
    phase_cost = (p45["paths"]["sell_equities"]["terminal"]
                  - p45["paths"]["sell_then_phase"]["terminal"])
    # The keep-and-borrow rung the dashboard quotes, read from the same engine output.
    by45 = next(y for y in BORROW["years"] if y["inherit_year"] == 2045)
    bmid = _borrow_pick(by45, 60, 7.11)
    bcheap = _borrow_pick(by45, 60, 5.98)
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
        kpi(m(p45["paths"]["sell_then_phase"]["terminal"]), "Phased path: sell, park in Treasuries, then equities",
            f"{ASM['phased_park_months']['value']} months in short-term Treasuries after inheritance, then equal "
            f"monthly purchases over {ASM['phased_equity_phase_months']['value']} months - softens 1929/2008 crash entry. "
            f"Reinvestment risk sits on both sides: the {m(phase_cost)} gap against investing at once is what "
            f"staging costs if the crash does <em>not</em> come, and the parking yield is an assumption that may "
            f"not be available in 2045."),
        kpi(f"{EPI['winners']['phase'] + EPI['winners']['park34']} of {len(EPI['episodes'])}",
            "Real crashes where waiting beat investing on day one",
            "Replayed with published monthly prices for 1929, 2000, 2008 and 2020 - not a synthetic sequence"),
        kpi(m(bmid["overlay_invested"]), "Keep the house, take the cash: what a loan costs over 30 years",
            f"60% of value ({m(bmid['loan'])}) released at the published mortgage average of "
            f"{pc(bmid['rate_pct'])} and invested at the model's after-tax return, so the money earns "
            f"{pc(BORROW['meta']['after_tax_portfolio_return_pct'])} against a hurdle of "
            f"{pc(bmid['hurdle_return_pct'])}. Borrowing only pays at a cheaper loan: at "
            f"{pc(bcheap['rate_pct'])}, 2026's lowest published weekly average, the same rung is worth "
            f"{m(bcheap['overlay_invested'])}. See <a href=\"keep-and-borrow.html\">the keep-and-borrow page</a>."),
    ])
    gating = callout("flag", "One fact is assumed, not verified, and everything else depends on it", f"""
<p>The Proposition 19 exclusion applies only where the transfer is between a parent and a child, or between a
grandparent and a grandchild whose parent has died. If that is not the relationship here, there is no exclusion:
the property is reassessed to full market value, every shelter figure on this site disappears, and the case for
selling gets stronger. The trust document is the only thing that settles it. <a href="questions.html">Answer
question A-1</a> before relying on any number here. {slink('rtc63_2_eligibility')}</p>""")
    regs = MODEL["regimes"]
    keep_regs = [r for r in regs if r["run"]["best"] == "live_in"]
    keep_names = "; ".join(r["name"] for r in keep_regs) or "none"
    sens = MODEL["sensitivity"]
    eq_vals = sorted(set(x["equity_return"] for x in sens))
    tsy_wins = sum(1 for x in sens if x["best"] == "sell_treasury")
    wwc = callout("flag", "What would change the answer", f"""
<ol class="change-list">
<li><strong>The Proposition 19 exclusion does not apply.</strong> Then the property is reassessed in full, every shelter figure on this site falls away, and selling gets stronger. <a href="questions.html">Question A-1</a> settles it.</li>
<li><strong>House prices in this area grow faster than {pc(p45['breakeven_house_growth'])} a year for thirty years.</strong> Then keeping the home matches selling at a 7% return. <a href="what-if.html#threshold-growth">Break-even case</a>.</li>
<li><strong>Market rent reaches {m(p45['breakeven_rent_monthly'])} a month in 2045 dollars.</strong> Then letting the home out matches selling. <a href="what-if.html#threshold-rent">Break-even case</a>.</li>
<li><strong>A regime like the one in the stress cases recurs.</strong> Keeping the home wins in {len(keep_regs)} of {len(regs)} stress regimes: {esc(keep_names)}. <a href="black-swan.html">Black swan conditions</a>.</li>
<li><strong>The crash arrives before the sale proceeds are invested.</strong> Replaying the real 1929, 2000 and 2008 records, parking the proceeds for 24-36 months and phasing into equities beat investing on day one; in the 2020 record it lost. <a href="black-swan.html#real-replays">Real entry-timing replays</a>.</li>
<li><strong>The heir genuinely wants to live in the house.</strong> The one-line recommendation is conditional on that. The <a href="precommit.html#imputed">imputed-rent break-even</a> prices what that preference has to be worth.</li>
<li><strong>Moving out after moving in.</strong> The Proposition 19 exclusion is removed when the heir stops qualifying, and the model now costs that at about {m(MIXED['clawback']['difference'])} of extra property tax over thirty years. <a href="decision.html">Mixed paths</a>.</li>
<li><strong>The housing the house provides is worth close to its full market rent to the heir.</strong> The published comparison credits the living path with no housing at all. Credited at about {pc(100.0)} of market rent, living and selling come level; below that, selling wins. <a href="decision.html#imputed-rent">The rent living does not pay itself</a>.</li>
<li><strong>Property B's fixed charges keep growing at their own pace.</strong> The model assumes {pcf(ASM['fixed_charge_growth']['baseline'])} a year; the audited record is {pcf(ASM['fixed_charge_growth']['high'])} over nine years, and those charges are {esc(str(MODEL['roll_audit']['property_b']['fixed_share_latest_pct']))}% of that bill. The 2% cap cannot bound them. <a href="review.html#roll-audit">Roll audit</a>.</li></ol>
<p class="muted">Two candidates were tested for this edition and do <em>not</em> belong on that list, which is why
they are recorded as ruled out rather than as open questions. The insurance premium at Property A, taken across
its whole published band, moves the thirty-year living figure by {m((MODEL.get('cost_cases') or {}).get('band', {}).get('effect_on_live', 0))} - about
{(MODEL.get('cost_cases') or {}).get('band_share_of_gap', 0)}% of the gap between selling and living. And no debt
service the model was given - each $1,000 a month of payment costs the keeping paths about
{m(next((-r['live_delta'] for r in (MODEL.get('cost_cases') or {}).get('debt_rows', []) if r.get('monthly') == 1000), 0))} -
ever puts keeping the house ahead of selling it, because a house sold in the year of inheritance carries no
payment stream. Both are on the <a href="costs.html#insurance-band">insurance band</a> and the
<a href="decision.html#debt">debt section</a>, and both are on the <a href="what-if.html">what-if page</a> as
levers 4 and 5.</p>""")
    cards = []
    for group, pages in NAV_GROUPS:
        if group == "Start here":
            continue
        items = "".join(
            f'<li><a href="{esc(p)}"><strong>{esc(PAGE_TITLES[p])}</strong>'
            f'<span>{esc(SUMMARIES[p])}</span></a></li>' for p in pages)
        cards.append(f'<section class="card"><h2>{esc(group)}</h2><ul class="card-list">{items}</ul></section>')
    # ---- the first screen: the answer, how sure, when, and what moves it -----------
    dist = MIXED["distribution"]
    sell_share = next(s["value"] for s in dist["shares"]
                      if s["key"].startswith("Selling beats living in it for thirty"))
    sens_sell = sum(1 for x in sens if x["best"].startswith("sell"))
    confidence = ("high" if sell_share >= 0.9 and sens_sell == len(sens) else
                  "medium" if sell_share >= 0.75 else "low")
    confidence_label = {"high": "high", "medium": "moderate", "low": "low"}[confidence]
    first_screen = decision_strip(
        "The answer, first",
        f"Sell Property A soon after it is inherited. Living in it, letting it out, and every mixed "
        f"version of those two end behind selling in the baseline and in "
        f"{sell_share*100:.0f}% of {dist['draws']} resampled histories of the "
        f"verified record, on the <a href=\"#distribution\">distribution section</a>. The one "
        f"exception the household controls is "
        f"whether it wants to live in this particular house.",
        confidence, confidence_label, BUILD_DATE,
        [f'<strong>The transfer is not parent-to-child.</strong> Then there is no Proposition 19 '
         f'exclusion, the property is reassessed in full, and selling wins by more. '
         f'<a href="questions.html">Question A-1</a>.',
         f'<strong>Market rent clears {m(p45["breakeven_rent_monthly"])} a month in 2045 dollars.</strong> '
         f'Then letting it out matches selling. <a href="precommit.html">The pre-commitment rule P-5</a>.',
         f'<strong>House prices grow faster than {pc(p45["breakeven_house_growth"])} a year for thirty '
         f'years.</strong> Then keeping it matches selling at a 7% return. '
         f'<a href="what-if.html#threshold-growth">Break-even</a>.',
         f'<strong>The household decides it wants to live there.</strong> That is a legitimate reason, '
         f'and it is the one input no model can price. <a href="precommit.html">Rule P-3</a>.'])

    return (
        first_screen
        + callout("answer", "The one-line answer", f"""
<p>Under every baseline this site can build, <strong>selling Property A soon after it is inherited beats living in it or letting it out</strong>, and it is not close. The reason is a one-off combination: the inheritance resets the income-tax basis to the value at death, so an immediate sale pays almost no capital gains tax, while the property tax assessment jumps to market value under Proposition 19. Waiting converts a tax-free asset into a taxed one and adds roughly {m(p45['bill_if_rent_year1'] - p45['bill_today_projected'])} a year of extra property tax if the home is let out.</p>
<p>The break-even house growth needed to make keeping the home beat selling is <strong>{pc(p45['breakeven_house_growth'])} a year for thirty years</strong>. The verified California state house price index compounded at 6.4% a year over the fifty years to 2025 and 2.6% a year over the last twenty. Read the <a href="decision.html">full decision</a>, then the <a href="black-swan.html">cases where this flips</a>.</p>
<p class="reinvest"><strong>Reinvestment risk beside the headline.</strong> Selling and investing assumes the proceeds can be reinvested at the modelled equity return. Inheriting into a 1929- or 2008-style crash means buying equities at the top. The phased path on the black-swan page parks the proceeds in short-term Treasuries for 24-36 months, then moves them into stocks, which softens crash-entry risk - at the cost of missing out while equities rally. On the 2045 baseline the proceeds could lose {pc(-p45['breakeven_return_vs_live'])} a year and selling would still match living, so the case for selling does not need a high return. <a href="what-if.html#threshold-return">Break-even case</a>.</p>
""")
        + f'<section class="kpi-row">{kpis}</section>'
        + distribution_section(dist, sell_share)
        + '<h2>The three checks that come before any number</h2>'
        + gating
        + wwc
        + '<section class="card-grid">' + "".join(cards) + "</section>"
        + callout("method", "How to read this site", """
<ol>
<li><strong>Start</strong> with the <a href="executive-summary.html">executive summary</a> and the <a href="decision.html">decision page</a>.</li>
<li><strong>Check the inputs.</strong> Every number the model uses is on the <a href="property-a.html">Property A</a>, <a href="property-b.html">Property B</a> and <a href="costs.html">costs</a> pages, with its source or an explicit unverified flag.</li>
<li><strong>Check the stress.</strong> No projection on this site relies on a single smooth growth rate. See <a href="black-swan.html">black swan conditions</a> and the <a href="economy.html">verified historical record</a>.</li>
<li><strong>Do not act yet.</strong> The <a href="questions.html">questions page</a> lists what is still unknown and how to find it out. The <a href="suggestions.html">suggestions page</a> is a review queue: every item in it still needs a decision, and the decision and date columns are empty.</li>
</ol>""")
    )


SUMMARIES = {
    "precommit.html": "Write the rules down first, so the projection cannot pick the answer.",
    "executive-summary.html": "The important details on one page.",
    "decision.html": "Five paths, the break-evens, and the recommendation.",
    "briefing.html": "Print-ready attorney and CPA discussion sheet.",
    "property-a.html": "The inherited home: roll, value, reassessment, costs.",
    "property-b.html": "The building already owned: rent, rent control, costs.",
    "ownership-distinction.html": "Why inherited and already-owned are not interchangeable.",
    "costs.html": "Water, power, insurance, maintenance and tax, projected.",
    "projections.html": "Year by year to 2076 for value, assessed value and tax.",
    "taxes.html": "Basis step-up, capital gains, the 121 exclusion, recapture.",
    "keep-and-borrow.html": "Cash out of the house without selling it, priced against selling.",
    "inheritance.html": "The trust transfer, phase by phase, with deadlines.",
    "what-if.html": "One lever at a time, with each case linked.",
    "estate.html": "Federal thresholds, California's position, scenario bands.",
    "laws.html": "Enacted, dead and proposed rules that could move the answer.",
    "black-swan.html": "Regimes where the answer changes, and by how much.",
    "economy.html": "Fifty years of verified inflation, house price and yield data.",
    "questions.html": "What is known, what is missing, and how to find it.",
    "suggestions.html": "A review queue of proposals, with a decision and date column for each one.",
    "review.html": "Unverified figures, modelling caveats and the repository audit.",
    "glossary.html": "Plain-language terms with official citations.",
    "timeline.html": "The deadlines and key dates that shape the inheritance decision.",
    "sources.html": "Every official source used, with what it supports.",
    "liquidity.html": "The nine-month payment clock, what deferring costs, and the two-person case.",
}


def exec_episode_table() -> str:
    """One compact table of the real entry-timing replays, for the summary page."""
    rows = []
    for e in EPI["episodes"]:
        s = e["strategies"]
        rows.append(
            f"<td><strong>{esc(e['name'])}</strong></td><td>{esc(e['entry'])} to {esc(e['exit'])}</td>"
            f"<td>{m(s['lump']['real_today'])}</td><td>{m(s['phase']['real_today'])}</td>"
            f"<td>{m(s['phase']['vs_lump'])}</td>"
            + method_cell("black-swan.html#real-replays", "Real monthly prices", e["src"]))
    return table(
        "Selling and reinvesting into a crash: what the real record says",
        ["Episode", "Window", "Invest on day one", "Park 30 months, then phase in over 12",
         "Phasing ahead by", "Basis"],
        rows,
        note="The same capital in every row, restated in October 2026 purchasing power, replayed against the "
             "published monthly prices of the actual 1929, 2000, 2008 and 2020 episodes. Waiting beat day-one "
             "investing in three of the four. Full method, the 24 and 36 month results and the honest "
             "counter-cases are on the black swan page.")


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
                + method_cell("decision.html#method", "Model output", sources=["fred_casthpi", "fred_gs10", "damodaran_histret"]))
    term = table(
        "Terminal value after 30 years, by inheritance year and path. "
        "Baseline assumptions: house prices 4.0% a year, inflation 2.5%, equities 7.0% gross, "
        "Treasuries 4.7%, selling costs 5.5%.",
        ["Inherited", "Path", "Terminal value", "Carrying tax and running costs over 30 years (sell paths: cost of sale)", "Basis"],
        rows)

    facts = [
        ("The condition everything rests on", "The Proposition 19 exclusion applies only to a transfer between a parent and a child, or between a grandparent and a grandchild where the middle generation has died. RTC section 63.2 sets that out. If the heir is not in that relationship to the transferor, the property is reassessed to full market value and every shelter figure here falls away."),
        ("Property A", f"Inherited through a trust, planned 2040 to 2050. Worth about {m(A['estimated_market_value_2026'])}. Not owned by the heir today."),
        ("Property B", f"Already owned by the heir. Worth about {m(B['estimated_market_value_2026'])}, three units, two let at {m(B['rent']['monthly'])} a month. The heir can live here without losing that rent."),
        ("The tax cliff at transfer", f"Today the Property A bill is about {m(MODEL['costs_a_now']['property_tax'])}. If the heir inherits in 2045 and does not move in, the bill becomes about {m(p45['bill_if_rent_year1'])}. If the heir does move in and claims the Proposition 19 exclusion, it becomes about {m(p45['bill_if_live_year1'])}."),
        ("Why moving in only half-helps", f"Proposition 19 does not freeze the old assessment: it limits the new one to the prior factored base year "
             f"value plus an indexed amount - {m(V['prop19_value_cap_2025_2027']['value'])} for a transfer between "
             f"16 February 2025 and 15 February 2027, adjusted again by statute on 16 February 2027. Everything "
             f"above that is reassessed. In 2045 the sheltered slice is about {m(p45['prop19_cap'])} against a market value of {m(p45['value_at_death'])}."),
        ("The tax-free sale window", "Property acquired from a decedent takes a basis equal to its value at death, so a sale soon after the inheritance pays close to zero capital gains tax. Holding it for thirty years turns the appreciation into a gain taxed at roughly 37% combined federal and California."),
        ("The equity comparison", f"To match selling and investing at 7%, the home must appreciate {pc(p45['breakeven_house_growth'])} a year for thirty years. The verified California state index compounded at 6.4% over fifty years and 2.6% over the last twenty."),
        ("The rental comparison", f"Letting the home out would need about {m(p45['breakeven_rent_monthly'])} a month in 2045 to match selling and investing. That is over 5% of the property's value per year in gross rent."),
        ("The estate position", f"California has had no estate tax since 2005. Federally, the 2026 exclusion is {m(V['federal_basic_exclusion_2026']['value'])} per person and {m(V['federal_basic_exclusion_2027']['value'])} for 2027. Portability lets a surviving spouse use a deceased spouse's unused exclusion. If a band of tax were owed, the <a href=\"liquidity.html\">liquidity page</a> now runs the keep-and-borrow case end to end: borrowing the band's tax against the kept house on a fully amortising 30-year fixed loan is dearer than selling and paying from the proceeds at every published band, and the largest band is beyond what one property's sale can self-fund."),
        ("The biggest unknown", "Whether the heir wants to live in this specific house. That is a preference, not a number, and it is worth more than any gap in this analysis."),
        ("Mixed paths", f"Living there for a while and then selling is the closest of the mixed paths, and it still ends behind an immediate sale: five years of occupancy followed by a sale leaves {m(next(x for x in MIXED['paths'] if x['occupy_years'] == 5 and x['mode'] == 'sell')['gap_vs_sell_now'])} less than selling at the inheritance. The table is on the <a href=\"decision.html\">decision page</a>."),
        ("The clawback nobody models", f"Moving out after claiming the Proposition 19 exclusion is not free. On the live-then-let path the exclusion is removed and the change-of-ownership base year value is enrolled, which costs about {m(MIXED['clawback']['difference'])} of extra property tax over thirty years against the reading in which the low assessment survives. Both readings are now published."),
        ("How often it holds", f"Over {MIXED['distribution']['draws']} resampled histories of the verified record, selling beats living in the house in {next(s['value'] for s in MIXED['distribution']['shares'] if s['key'].startswith('Selling beats living in it for thirty'))*100:.1f}% of them, and beats living there ten years and then selling in {next(s['value'] for s in MIXED['distribution']['shares'] if s['key'].startswith('Selling beats living in it ten years'))*100:.1f}%. The distribution is on the <a href=\"index.html#distribution\">dashboard</a> and the <a href=\"projections.html#fan\">projections page</a>."),
        ("What a sale actually costs the state", f"The transfer tax and recording fees the brief asked to have priced come to {m(MIXED['fees_example']['published_total'])} on a {m(MIXED['fees_example']['price'])} sale, about {MIXED['fees_example']['published_share_of_modelled']}% of the modelled 5.5% selling cost. The other {MIXED['fees_example']['private_share_of_modelled']}% is commission, escrow and title, which are private quotes rather than statutes. The itemisation is on the <a href=\"taxes.html\">taxes page</a>."),
        ("The repeal that did not happen", "The initiative that would have undone most of Proposition 19 failed to qualify for the November 2026 ballot, so the shelter arithmetic above is current law rather than law about to change. A replacement measure can be filed at any time; the Secretary of State's qualification dashboard is the official page that would show it."),
        ("The pre-commitment rule", "Before reading any projection, the household should write down what would make it choose each path. That register, with its decision columns empty, is on the <a href=\"precommit.html\">pre-commitment page</a>. Without it a single projection can be made to justify any path."),
    ]
    # Per-row source map for the dashboard's fact table: each fact links only to the
    # official document that bears on it. An owner figure, a preference or a household
    # procedure has no official source and is sent to the register instead of being
    # dressed in the four core links (the defect logged open by arena/1c788435-tino3).
    FACT_SOURCES = {
        "The condition everything rests on": ["rtc63_2", "boe_prop19"],
        "Property A": [],
        "Property B": [],
        "The tax cliff at transfer": ["boe_pub29", "rtc63_2"],
        "Why moving in only half-helps": ["rtc63_2", "boe_lta25009"],
        "The tax-free sale window": ["irs_basis", "irs_tc409"],
        "The equity comparison": ["fred_casthpi", "fred_gs10"],
        "The rental comparison": [],
        "The estate position": ["sco_estate", "irs_estate", "irs_2027"],
        "The biggest unknown": [],
        "Mixed paths": ["fred_casthpi", "fred_gs10"],
        "The clawback nobody models": ["rtc63_2"],
        "How often it holds": ["fred_casthpi", "fred_gs10", "damodaran_histret"],
        "What a sale actually costs the state": ["rtc11911", "rtc11930"],
        "The repeal that did not happen": ["sos_initiative_status"],
        "The pre-commitment rule": [],
    }
    assert set(FACT_SOURCES) == {k for k, _ in facts}, "every fact row needs a source decision"
    fact_rows = [
        f"<td><strong>{esc(k)}</strong></td><td>{v}</td>"
        + src_cell(FACT_SOURCES[k], "Key rules")
        for k, v in facts]
    ftab = table("The important details", ["Detail", "What this analysis found"], fact_rows)

    return (
        eligibility_callout()
        + callout("summary", "Recommendation", f"""
<p><strong>Sell Property A soon after it is inherited, unless the heir genuinely wants to live in that house.</strong></p>
<p>Selling converts an asset earning nothing into capital, at almost no tax, and it removes a property tax bill that is about to multiply by six to eleven times. Living in the house is the only path that keeps the tax bill lower, and it still leaves the heir holding a single, undiversified, illiquid asset in one California school district. Letting it out fails every scenario this site can build, because it combines the full reassessment with landlord costs and a rental yield below the return available elsewhere — but that comparison credits the letting paths with <strong>no rent at all</strong>, so read it as a floor and check the break-even rent below before relying on it.</p>
<p>The counter-case is real and it is on the <a href="black-swan.html">black swan page</a>: keeping the house wins in {len(RF['keep'])} of the {RF['n']} stress regimes, namely {esc(RF['keep_names'])}. That is a bet on one neighbourhood, not a plan.</p>
""")
        + ftab
        + term
        + exec_episode_table()
        + callout("risk", "Five things that could change the answer", """
<ol>
<li><strong>The heir wants to live there.</strong> That is worth the whole gap if it is true. It also has to be true for the whole time: moving out removes the Proposition 19 exclusion.</li>
<li><strong>Law changes.</strong> On unofficial results as of 16 November 2026 (7:12 p.m.; counting continues), California voters approved Proposition 3, which makes the high-income tax rates permanent (60.8% yes), and rejected Proposition 40, the one-time billionaire tax (52.2% no). Certification is due by 11 December 2026. Both are on the <a href="laws.html">law page</a>. A future measure could cut the other way.</li>
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
                           ("sell_then_phase", f"Sell at inheritance, park in short-term Treasuries for "
                                               f"{ASM['phased_park_months']['value']} months, then phase into equities "
                                               f"over {ASM['phased_equity_phase_months']['value']} months"),
                           ("live_in", "Move in and hold for 30 years"),
                           ("live_then_rent", "Move in two years, then let it out"),
                           ("rent_out", "Let it out from the start")):
            v = p["paths"][key]
            rows.append(f"<td>{p['inherit_year']}</td><td>{esc(label)}</td>"
                        f"<td>{m(v['terminal'])}</td>"
                        f"<td>{m(v.get('outflow', 0))}</td>"
                        + method_cell("#method", "Model output", sources=["fred_casthpi", "fred_gs10", "damodaran_histret"]))
    paths_table = table(
        "Terminal value after thirty years, by inheritance year and path",
        ["Inherited", "Path", "Terminal value", "Carrying tax and running costs (sell paths: cost of sale)", "Basis"], rows,
        note="Terminal value is what is left at the end of the thirty years. On the sell paths it is the sale "
             "proceeds after selling costs, grown at the return shown. On the living and letting paths it is the "
             "sale after selling costs and capital gains tax, less the compounded future value of every year's "
             "property tax and running costs (and, for letting, plus the net rent). The column "
             "\"Carrying tax and running costs\" is their nominal total; on the sell paths it is the cost of the "
             "sale at inheritance, already netted from the proceeds. Nominal figures in the money of that future year.")

    be_rows = []
    for p in MODEL["paths"]:
        be_rows.append(
            f"<td>{p['inherit_year']}</td>"
            f"<td>{m(p['breakeven_rent_annual'])}</td>"
            f"<td>{m(p['breakeven_rent_monthly'])}</td>"
            f"<td>{ret_cell(p['breakeven_return_vs_live'])}</td>"
            f"<td>{ret_cell(p['breakeven_return_vs_rent'])}</td>"
            f"<td>{pc(p['breakeven_house_growth'])}</td>"
            f"<td>{m(p['housing_value_needed'])}</td>"
            + method_cell("#method", "Model output", sources=["fred_casthpi"]))
    be_table = table(
        "Break-even questions, answered",
        ["Inherited", "Rent needed per year", "Rent needed per month",
         "Return needed to beat living in it", "Return needed to beat letting it",
         "House growth needed to keep it", "Housing value the home must provide per year"],
        be_rows,
        note="\"Housing value\" is the level annual value of living in the house that would be needed to close the "
             "gap between living in it and selling, after the living path's own tax and running costs. It is the number "
             "to compare against what the heir would otherwise pay, or could otherwise earn, for somewhere to live. "
             "A negative return means the sale proceeds beat the alternative even if they lose that much a year. "
             "\"Not reachable\" means the letting path has a negative terminal value even with zero rent, so no return on "
             "the sale proceeds can match it. The living path is currently credited with no imputed rent at all: "
             "the stated-level cases for that comparison are lever 3 on the "
             "<a href=\"what-if.html#imputed-0\">what-if page</a>.")

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
            + method_cell("#method", "Model output", sources=["fred_casthpi", "fred_gs10", "damodaran_histret"]))
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
            f"Not won by selling: {RF['keep_names']}."),
    ]) + "</div>"

    # ------------------------------------------------------------------ what-if map --
    best_short = {
        "sell_equities": "Sell\u2192equities",
        "sell_treasury": "Sell\u2192Treasuries",
        "sell_then_phase": "Sell\u2192phase",
        "live_in": "Live in",
        "rent_out": "Let out",
        "live_then_rent": "Live\u2192rent",
    }
    eq_cols = [c["eq"] for c in MODEL["sensitivity_fine"][0]["cells"]]
    eq_headers = [f"{float(eq):.0f}%" for eq in eq_cols]
    what_rows = []
    for r in MODEL["sensitivity_fine"]:
        cells = [f"<td><strong>{float(r['g']):.0f}%</strong></td>"]
        for c in r["cells"]:
            label = best_short[c["best"]]
            cls = "best" if c["best"].startswith("sell") else ""
            cells.append(f"<td class=\"{cls}\" title=\"{esc(label)} wins\">{esc(label)}</td>")
        what_rows.append("".join(cells))
    whatif_map = table(
        "What-if map: which path wins at each house-growth / equity-return combination (2045 inheritance)",
        ["House growth"] + eq_headers, what_rows,
        note="Each cell prices all six paths at that combination and names the winner. Sell\u2192phase is the "
             "phased-investing path: sale proceeds park in short-term Treasuries for the canonical 30 months (the "
             "owner's 24-36 month band), then buy equities in equal monthly pieces over the following 12 months, "
             "the same canonical monthly path the black-swan page stress-tests and back-tests. Cells where a "
             "sell path wins are shaded. All figures come from scripts/model.py; change "
             "assets/data/inputs.json and rebuild to explore other assumptions. "
             + method_cell("#method", "Model output", sources=["fred_casthpi", "fred_gs10"]))

    return (
        eligibility_callout()
        + imputed_rent_section()
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
        + mixed_section()
        + reinvestment_section()
        + debt_section()
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
                    f"<td>Property B ad valorem rate</td><td>{pcf(ASM['ad_valorem_rate_b']['value'],2)}</td>"
                    f'<td><span class="badge verified">published</span></td>'
                    + src_cell(ASM["ad_valorem_rate_b"]["src"], "Published rate; publisher withheld for privacy"),
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
<li><strong>Mortgages and other encumbrances, 1031 exchanges, instalment sales, gifting and trust restructuring.</strong> None is assumed away silently: the debt assumption is stated and priced per $1,000 a month of payment in <a href="#debt">Debt, occupancy, capital costs and liquidity</a>, and the rest are on the <a href="questions.html">questions page</a> and the <a href="suggestions.html">suggestion queue</a>.</li>
<li><strong>Borrowing against the house instead of selling it.</strong> Now a priced path, not an omission: <a href="keep-and-borrow.html">keep-and-borrow</a> runs cash-out rungs at 40, 60 and 80 percent of value against the published mortgage averages, on the same transfer years, horizon and tax layers as every row above, and states the hurdle return the borrowed money has to beat.</li>
<li><strong>Transaction costs of moving house, and the cost of capital gains tax on any other asset that would have to be sold.</strong> Not modelled.</li>
</ul>""")
    )




# ------------------------------------------------------- insurance and debt --
# Two sections added on the owner's instruction of 16 November 2026: a round-number
# cost assumption is replaced by a range with an evidence class at each end, and the
# silence about debt in the comparison is replaced by an explicit statement of the
# assumption, what it does to each path, and what no model can price.

def _rung(r):
    """Model labels arrive lower-case (they are keys as much as prose); pages print them as cells."""
    label = (r or {}).get("label") or ""
    return (label[0].upper() + label[1:]) if label else ""


def insurance_band_section() -> str:
    """The insurance band, its two published anchors, and what the whole band is worth."""
    cc = MODEL.get("cost_cases") or {}
    band = cc.get("band", {})
    rung = _rung
    rows = []
    for r in cc.get("rows", []):
        term = r["terminals"]
        rows.append(
            f"<td>{esc(rung(r))}</td>"
            f"<td>${r['annual']:,}</td>"
            f"<td>{m(term['sell_equities'])}</td>"
            f"<td>{m(term['live_in'])}</td>"
            f"<td>{m(term['rent_out'])}</td>"
            f"<td>{m(r['live_gap'])}</td>"
            f"<td><strong>{esc(PATH_LABELS[r['best']])}</strong></td>"
            + (src_cell([r["kind"]], "Published figure") if r["kind"] in SOURCES
               else method_cell("review.html#register", "Owner figure or stated scenario", sources=[])))
    band_tbl = table(
        "Every path re-run at each rung of the Property A insurance band (2045 inheritance, thirty years)",
        ["Insurance carried", "A year", "Sell and invest", "Live in it", "Let it out",
         "Change to the living path", "Best path", "Basis"],
        rows,
        note="Selling is charged nothing, because a house sold at the inheritance pays no premium "
             "after that. That is the whole shape of this table: a higher premium makes keeping the "
             "house worse, never better, so the band moves the size of the gap and not its direction.")

    a_ins = A["annual_costs"]["insurance"]
    b_ins = B["annual_costs"]["insurance"]
    srcs = table(
        "The insurance figures, and what each end of the band rests on",
        ["Figure", "Amount", "What it is", "Source"],
        [
            f"<td>Statewide average written premium, owner-occupied homeowners form, "
            f"experience year {band.get('official_floor_year', 2017)}</td>"
            f"<td>${band.get('official_floor', 1074):,} a year</td>"
            f"<td>The published figure the low end of Property A's band is taken from. It averages "
            f"every policy on the form across every amount of insurance in the state.</td>"
            + src_cell(["cdi_homeowners_avg"], "Department of Insurance table"),
            f"<td>Statewide average written premium, dwelling fire (rental dwelling or landlord, "
            f"up to 4 units) form, experience year 2017</td>"
            f"<td>${band.get('landlord_official_floor', 519):,} a year</td>"
            f"<td>The published figure the low end of Property B's band is taken from. A three-unit "
            f"building is on this form family; five or more units would leave it and be written "
            f"commercially.</td>"
            + src_cell(["cdi_df_rental"], "Department of Insurance table"),
            f"<td>Property A band carried by the model</td>"
            f"<td>{m(a_ins['low'])} to {m(a_ins['high'])} a year, {m(a_ins['mid'])} used</td>"
            f"<td>Owner's estimate in the middle, published averages at the floor, a stated upper "
            f"scenario at the ceiling.</td>"
            + method_cell("review.html#register", "Band, owner estimate flagged", sources=["cdi_homeowners_avg"]),
            f"<td>Property B band carried by the model</td>"
            f"<td>{m(b_ins['low'])} to {m(b_ins['high'])} a year, {m(b_ins['mid'])} used</td>"
            f"<td>Same construction. Property B's insurance is not charged to any Property A path, "
            f"because this building is already owned and already let; it enters the comparison only "
            f"through the value of the housing the household would consume by living there.</td>"
            + method_cell("review.html#register", "Band, owner estimate flagged", sources=["cdi_df_rental"]),
            f"<td>What the whole band is worth on the living path</td>"
            f"<td>{m(band.get('effect_on_live', 0))} of terminal value</td>"
            f"<td>The difference between the bottom and the top of the band, run through thirty years "
            f"of the model. Against the {m(cc.get('gap_live_at_baseline', 0))} gap between selling and "
            f"living, that is {cc.get('band_share_of_gap', 0)}%.</td>"
            + method_cell("#method", "Model output", sources=["cdi_homeowners_avg", "cdi_df_rental"]),
            "<td>Share of California dwelling fire and owner-occupied exposures carrying $1,000,000 or "
            "more of insurance, 2023</td><td>8.4%</td>"
            f"<td>The reason the published average is treated as a floor rather than an estimate: "
            f"Property A's value puts it in a small minority of exposures, and the report states that "
            f"average premium rises with the amount of insurance.</td>"
            + src_cell(["naic_hmr_2023"], "NAIC report, Table 3"),
            "<td>Combined dwelling coverage limit, the state's insurer of last resort</td>"
            "<td>$3,000,000</td>"
            f"<td>Raised from 1.5 million by order of the Insurance Commissioner, effective 1 April "
            f"2020. Property A's owner-estimated value of {m(A['estimated_market_value_2026'])} is above "
            f"that limit, so if cover cannot be placed in the standard market the shortfall is not a "
            f"pricing question but an availability one.</td>"
            + src_cell(["cdi_fairplan"], "Department of Insurance order"),
        ],
        note="No figure in this table is a quote for either building. The two official averages are "
             "statewide and are computed as written premium divided by house-years of exposure; the "
             "owner's figures are what the household has been paying or expects to pay; the upper "
             "scenario is a stated test, not an estimate.")
    return ('<h2 id="insurance-band">Insurance: the band, and what it is worth</h2>'
            + callout("note", "Why this replaced a single number", f"""
<p>The owner's brief asks for ranges in place of round-number assumptions. Insurance was the one
running cost carried as a single figure at both properties - {m(a_ins['mid'])} a year each, the same
number for a primary residence and for a three-unit rental, which cannot both be right. It is now a
band, and each end says where it came from: the published statewide average for the matching policy
form at the bottom, the owner's figure in the middle, and a stated upper scenario at the top.</p>
<p>The band matters less than it looks. Run through thirty years of the model, the whole spread from
floor to ceiling moves the living path's terminal value by {m(band.get('effect_on_live', 0))} against
a selling-versus-living gap of {m(cc.get('gap_live_at_baseline', 0))} - about
{cc.get('band_share_of_gap', 0)}% of it. Insurance is therefore <strong>not</strong> a load-bearing
assumption on this decision, and getting three quotes is about the size of the bill, not about which
path to choose. The quotes still have to be obtained: they are what turns a band into a number.</p>""")
            + srcs + band_tbl)


def debt_section() -> str:
    """Debt, occupancy, capital costs and liquidity: what the comparison carries."""
    cc = MODEL.get("cost_cases") or {}
    enc = A.get("encumbrance", {})
    rows = [
        ("Mortgage, deed of trust or other lien on either building",
         f"<span class=\"badge unverified\">{esc('not supplied')}</span> &mdash; both properties are "
         f"modelled free and clear, and that is an assumption, not a fact. Nothing in the material this "
         f"site was built from states whether anything is registered against either parcel.",
         "The balance owed at the date of transfer, the payment, the rate and whether any assessment or "
         "tax lien is outstanding.",
         ["uscode1701j3", "irs_basis"]),
        ("What an encumbrance does to the sale path",
         "Nothing to the ranking, and everything to the amount. A sale pays the balance out of the "
         "proceeds, so the sum invested falls by exactly that much; the income-tax basis is the fair "
         "market value at the date of death whether or not debt sits on the property, so the near-zero "
         "gain on an immediate sale is unaffected.",
         "The lender's payoff statement dated at or near the transfer.",
         ["irs_basis"]),
        ("What an encumbrance does to the keeping paths",
         "It is the one input here that only makes keeping worse. Each stated monthly payment is "
         "modelled below: at $1,000 a month the living path loses $1,311,830 of terminal value and "
         "the sale path loses nothing, because a house sold in the year of inheritance carries no "
         "payment stream.",
         "The amortisation schedule and the interest portion of it, which is the part that is a real "
         "cost rather than a transfer between pockets.",
         []),
        ("Whether the lender could call the loan due on the transfer",
         "For a loan on a building of fewer than five dwelling units, federal law stops a lender "
         "exercising a due-on-sale clause on a transfer to a relative resulting from the borrower's "
         "death, or on a transfer where the borrower's spouse or children become owners. Property A is "
         "one unit and Property B is three, so both are inside that limit if they are encumbered at all.",
         "The note and deed of trust, to confirm the loan is residential and the transfer is the "
         "protected kind. The statute limits acceleration; it does not decide who must pay.",
         ["uscode1701j3"]),
        ("Occupancy changes",
         "Priced. Living there and later letting it out is its own path, because the Proposition 19 "
         "exclusion falls away when the home stops being the heir's principal residence and the "
         "assessor re-enrols the change-of-ownership value; both readings of that rule are published on "
         "the decision page rather than assumed away.",
         "Nothing further: this one is a question of what the household intends, which the "
         "pre-commitment register asks it to write down before the figures are read.",
         ["rtc63_2_eligibility", "boe_prop19"]),
        ("Capital and repair costs",
         "Priced as a percentage of value and written out year by year in the five-year capital plan on "
         "the running-costs page, which lists the components an allowance of that size has to cover.",
         "Five years of actual spend and a licensed inspection, which is what turns the percentage into "
         "a schedule.",
         []),
        ("Liquidity",
         "Priced end to end: a federal estate tax is payable in cash nine months after death, so an estate "
         "whose wealth is in two buildings has to sell something or borrow. The estate liquidity page runs "
         "both routes for each anonymous band of the amount above the exclusion - keep the house and borrow "
         "the band's tax against it on a fully amortising 30-year fixed loan, or sell and pay from the "
         "proceeds - and finds borrowing dearer at every published band, with the largest band beyond what "
         "one property's sale can self-fund.",
         "The estate inventory and the liquid balance outside the trust, which are kept off this site by "
         "the household's own instruction.",
         ["irs_i706", "irs_estate", "fred_mortgage"]),
    ]
    body = []
    for item, status, needed, srcs in rows:
        cell = (src_cell(srcs, "Official source") if srcs
                else method_cell("review.html#register", "No official source applies", sources=[]))
        body.append(f"<td><strong>{esc(item)}</strong></td><td>{status}</td><td>{esc(needed)}</td>" + cell)
    tbl = table("What the comparison carries, and what it does not",
                ["Element", "Status in this edition", "What is still needed", "Basis"], body,
                note="Every row states its own condition. A row that says 'priced' is computed by the "
                     "model from the inputs on this site; a row that says 'not supplied' is a gap in the "
                     "record, and the model is running on the assumption named in it.")

    debt_rows = []
    for r in cc.get("debt_rows", []):
        term = r["terminals"]
        debt_rows.append(
            f"<td>{m(r['monthly'])} a month</td><td>{m(r['annual'])} a year</td>"
            f"<td>{m(term['sell_equities'])}</td><td>{m(term['live_in'])}</td>"
            f"<td>{m(term['rent_out'])}</td><td>{m(r['live_delta'])}</td>"
            f"<td><strong>{esc(PATH_LABELS[r['best']])}</strong></td>"
            + method_cell("#method", "Model output", sources=["fred_casthpi", "fred_gs10"]))
    per_1000 = next((-r["live_delta"] for r in cc.get("debt_rows", [])
                     if r.get("monthly") == 1000), 0)
    cases = ""
    if debt_rows:
        cases = ('<h3>If there is a payment to carry: what $500, $1,000 and $2,000 a month does</h3>'
                 + table("Stated debt-service levels added to the keeping paths (2045 inheritance, thirty years)",
                         ["Payment", "A year", "Sell and invest", "Live in it", "Let it out",
                          "Change to the living path", "Best path", "Basis"], debt_rows,
                         note=f"These are stated scenarios, not estimates: no balance, rate or payment "
                              f"for either property has been supplied, so nothing here pretends to know "
                              f"whether either building is encumbered. What the table shows is the direction "
                              f"and the rate: the first $1,000 a month of payment a holder would take on "
                              f"costs the living path {m(per_1000)} of terminal value, and the sale path "
                              f"nothing. A mortgage therefore never turns keeping the house into the better "
                              f"choice; it only makes it worse, and the household's own capacity to carry "
                              f"the payment is a second-order question the model does not ask."))
    return ('<h2 id="debt">Debt, occupancy, capital costs and liquidity</h2>'
            + callout("note", "Why this section exists", f"""
<p>The comparison the owner asked for is to carry taxes, debt, occupancy changes, capital costs and
liquidity. Taxes, occupancy, capital costs and liquidity are all priced somewhere in this edition; debt
was not - it simply was not mentioned, which is the worst way for a model to make an assumption, because
a reader cannot see it. This section states the assumption in the open: <strong>both buildings are
modelled free and clear, because no encumbrance was reported either way</strong>. It also prices what
an encumbrance would do, per $1,000 a month of payment, so the household can read its own balance off
the table without the model guessing at it: each $1,000 a month of payment carried while the house is
kept is {m(per_1000)} of terminal value, and nothing at all on the sale path.</p>
<p>The direction of the effect is worth stating plainly, because it is counter-intuitive and it favours
the recommendation. Debt reduces what a sale puts in the bank, but it also reduces what keeping the
building is worth, by more: the holder pays the interest as well as the principal, and pays it out of
money that would otherwise have been invested. So an encumbrance never makes keeping the house the better
choice; it can only make it worse. That is why the ranking below does not change at any payment level.</p>""")
            + tbl + cases)


def reinvestment_section() -> str:
    """Reinvestment risk, printed beside the staging headline rather than under it."""
    p45 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2045)
    imm = p45["paths"]["sell_equities"]["terminal"]
    ph = p45["paths"]["sell_then_phase"]["terminal"]
    tres = p45["paths"]["sell_treasury"]["terminal"]
    stress = MODEL["phased_stress"]
    bt = MODEL["backtest"]
    rows = []
    for r in stress["rows"]:
        rows.append(f"<td>{esc(r['label'])}</td><td>{m(r['terminal'])}</td>"
                    f"<td>{m(r['difference'])}</td><td>{esc(r['reading'])}</td>"
                    + method_cell("black-swan.html", "Model output", sources=["fred_cpiaucns", "fred_tb3ms", "fred_nasdaq"]))
    stress_tbl = table(
        "The staging choice, priced on the same engine as the headline",
        ["Case", "What the money becomes", "Difference from the same case without staging",
         "What the case is", "Basis"], rows,
        note=f"Parking yield {stress['parking_yield']}% a year (band "
             f"{stress['parking_yield_low']}% to {stress['parking_yield_high']}%), the single "
             f"canonical assumption every phased figure on the site uses. The synthetic crash is a "
             f"stated sequence, not a dated replay; the dated replays are on the black swan page.")
    per_stage = {
        "at_once": imm,
        "phased": ph,
        "treasuries": tres,
    }
    meter = meter_chart(
        "Immediate, staged, or parked: the same proceeds on the baseline",
        "No crash in this case. The staged path is the price of insurance against one.",
        [("Invest everything at once", imm, ""),
         ("Park 30 months, then phase over 12", ph, ""),
         ("Park it and leave it in Treasuries", tres, "bad")],
        "The middle bar is the recommendation's staging option and the third is the safe but "
        "low-return version of it.")
    return ('<h2>Reinvestment risk, beside the staging number</h2>'
            + callout("flag", "The other side of the staged-entry trade", f"""
<p>Every staged figure on this site is a <em>risk</em> result, not a free improvement. On the
2045 baseline the sale proceeds are {m(imm)} if invested at once and {m(ph)} if parked in
short-term Treasuries for {ASM['phased_park_months']['value']} months and then phased in over
{ASM['phased_equity_phase_months']['value']} - a cost of <strong>{m(imm - ph)}</strong> paid as
insurance against inheriting into a 1929- or 2008-style peak. When the crash does come, the same
staging is worth more than it cost; the dated replays on the
<a href="black-swan.html#real-replays">black swan page</a> show it winning in three of four
episodes and losing in the 2020 one.</p>
<p>Two assumptions carry that result and neither is guaranteed. The parking yield - currently
{ASM['treasury_short_yield_nominal']['baseline']*100:.1f}% a year, band
{ASM['treasury_short_yield_nominal']['low']*100:.1f}% to
{ASM['treasury_short_yield_nominal']['high']*100:.1f}% - is a stated scenario, not a published
forward rate, and short Treasury yields in 2045 may be far lower. And the proceeds have to be
<em>reinvested</em> on a written policy, which is a decision the household makes at the worst
possible moment unless it writes one in advance (<a href="precommit.html">rule P-2</a>).</p>""")
            + meter
            + stress_tbl)


def mixed_section() -> str:
    """Mixed paths, the Prop 19 clawback, and the opportunity cost of living in it.

    The pure paths tell the household what happens if it commits to one thing for
    thirty years. Almost nobody does. This section prices the paths a household
    actually takes, and it prices the two things the pure paths leave out: the
    property-tax clawback when the heir moves out, and the housing value of the
    years the heir lives in the house.
    """
    paths = MIXED["paths"]
    cb = MIXED["clawback"]
    h = MIXED["distribution"]["histogram"]
    sell_share = next(s["value"] for s in MIXED["distribution"]["shares"]
                      if s["key"].startswith("Selling beats living in it for thirty"))

    rows = []
    for r in paths:
        if r["occupy_years"] == 0 and r["mode"] == "sell":
            continue                     # the comparator is on the table above
        terminal = r["asset_terminal"]
        gap = r["gap_vs_sell_now"]
        opened = '<td class="best">' if gap <= 0 else "<td>"
        rows.append(
            f"<td>{esc(r['label'])}</td>"
            f"<td>{r['occupy_years']} years</td>"
            f"<td>{m(r['property_tax_total'])}</td>"
            f"<td>{m(r['terminal_price'])}</td>"
            f"{opened}{m(terminal)}</td>"
            f"<td>{m(gap)}</td>"
            + method_cell("precommit.html#method", "Model output", sources=["fred_casthpi", "fred_gs10"]))
    mixed_tbl = table(
        "Mixed paths: what happens if the household does one thing and then another",
        ["Path", "Years occupied", "Property tax paid over the period", "Sale price at the end",
         "Terminal value", "Selling at the inheritance leaves this much more", "Basis"],
        rows,
        note="A positive figure in the last column means selling at the inheritance left the "
             "household ahead of that mixed path; a negative one would mean the mixed path won. "
             "No mixed path gets close in the baseline: the inheritance-step-up sale is hard to "
             "beat on these inputs. Every row carries every cost including the section 121 "
             "exclusion where the heir occupied the house for two of the last five years, and "
             "depreciation recapture where it was let.")

    gap_rows = []
    for i in range(11):
        gap_rows.append({"label": "p100" if i == 10 else f"p{i*10}",
                         "values": [("sell", path_decile(i, "gap_live"), "Sell minus live 30 years"),
                                    ("mid", path_decile(i, "gap_live10_sell"),
                                     "Sell minus live 10 years then sell")]})
    gap_chart = fan_chart(
        "How much selling is worth over keeping it, across the record",
        "Deciles of the gap, over the same resampled histories. Positive means selling wins.",
        "money", gap_rows,
        "The two distributions sit mostly to the right of zero, and the extremes are wide: in the "
        "worst draw the household that kept the house is ahead by a quarter of a billion dollars in "
        "nominal 2075 money, because house prices there compounded near the top of the record. That "
        "tail is why the recommendation is a share of draws and not a certainty.")

    hist = histogram(
        "Every draw, selling against living in it for thirty years",
        "The same gap as the chart above, as a histogram. Each bar is one twentieth of the range.",
        h["counts"], h["lo"], h["hi"], h["zero_position"], sell_share, h["note"])

    clawback_rows = [
        ("Property tax paid over the thirty years, strict reading of section 63.2(a)(1)(C)",
         m(cb["tax_with_clawback"])),
        ("Property tax paid if the low assessment survives the move-out",
         m(cb["tax_without_clawback"])),
        ("Extra property tax the clawback costs, over the thirty years", m(cb["difference"])),
    ]
    claw_rows = [f"<td>{esc(a)}</td><td><strong>{esc(b)}</strong></td>"
                 + method_cell("review.html#register", "Model output, condition unverified", sources=["rtc63_2"])
                 for a, b in clawback_rows]
    claw_tbl = table(
        "The Proposition 19 clawback: what moving out costs on the live-then-let path",
        ["Line", "Amount", "Basis"], claw_rows,
        note=esc(cb["rule"]) + " The model now prices both readings. The existing live-then-rent "
             "figure on the table above uses the favourable one; the difference is shown here so "
             "neither reading is silent. Year one's bill after the move-out is "
             f"{m(cb['year_one_bill_after_move_out'])} on the strict reading against "
             f"{m(cb['year_one_bill_if_kept'])} if the low assessment survives.")

    return (
        '<h2>Mixed paths: what households actually do</h2>'
        + callout("note", "Why pure paths are not enough", """
<p>The five paths above assume the household commits to one thing for thirty years. That is a
useful way to price the extremes, and it is not what anybody does. A household may live in the
house for five years and then sell, or live in it and later let it out. Those paths are priced
here on the same engine and the same conventions, so &ldquo;how long would we have to live there
before it pays?&rdquo; is answerable rather than rhetorical.</p>""")
        + mixed_tbl
        + claw_tbl
        + callout("warn", "The two things the pure paths leave out", """
<p><strong>Living in it has value.</strong> The terminal-value columns on this page do not credit
the years the heir spends housed. The <a href="precommit.html#method">imputed-rent table</a> on
the pre-commitment page prices that benefit across a range of market rents, and the rent needed to
close the gap is in the break-even table above.</p>
<p><strong>The property-tax relief can be taken back.</strong> Moving out is not free: section
63.2(a)(1)(C) enrols the change-of-ownership base year value once the heir stops qualifying. The
clawback table prices it. It does not change the recommendation, but it moves the live-then-let
path by six figures and it would be a mistake to model that path without it.</p>""")
        + gap_chart + hist
    )


def path_decile(i: int, key: str) -> int:
    s = next(x for x in MIXED["distribution"]["series"] if x["key"] == key)
    return s["deciles"][i]


PATH_LABELS = {
    "sell_equities": "Sell, invest in equities",
    "sell_treasury": "Sell, reinvest in Treasuries",
    "sell_then_phase": "Sell, park in Treasuries, then phase into equities",
    "live_in": "Live in it",
    "live_then_rent": "Live in it, then let it",
    "rent_out": "Let it out",
}


# ------------------------------------------------------ pre-commit register --
def page_precommit() -> str:
    """The rules written down before the figures are read.

    The owner asked for this explicitly: agree in writing what would make the
    household choose each path before the figures arrive, so the outcome is not
    reverse-engineered from one projection. The page therefore states the test
    for each path first, and puts the numbers second - and the decision column
    is empty on purpose, because no path has been chosen.
    """
    p45 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2045)
    rules = PRECOMMIT["rules"]
    goals = PRECOMMIT["household_goals"]
    gates = PRECOMMIT["review_gates"]

    blank = '<span class="blank">not yet decided</span>'
    rule_rows = []
    for r in rules:
        by = esc(r["decided_by"]) if r["decided_by"] else blank
        on = esc(r["decided_on"]) if r["decided_on"] else blank
        rule_rows.append(
            f"<td><strong>{esc(r['id'])}</strong></td>"
            f"<td><strong>{esc(r['path'])}</strong></td>"
            f"<td>{esc(r['decides_if'])}</td>"
            f"<td>{esc(r['would_override_if'])}</td>"
            f"<td>{on}</td><td>{by}</td>"
            # A household rule that quotes or turns on the exclusion statute links that
            # statute; every other rule is a preference with no official publisher.
            + method_cell("review.html#register", "Household rule, not a figure",
                          sources=["rtc63_2"] if any(
                              k in (r["decides_if"] + " " + r["would_override_if"])
                              for k in ("63.2", "exclusion", "clawback")) else []))
    rule_table = table(
        "The pre-commitment register: what decides each path, written before the figures",
        ["Rule", "Path", "The household chooses this path if...", "...but this would override it",
         "Decided on", "Decided by", "Where the figure is"],
        rule_rows,
        note="The two decision columns are deliberately empty. No path has been chosen. Fill them in "
             "by hand when the household decides, with the date, and keep the rule beside the decision "
             "so a future reader can see whether the rule was followed or changed. " + esc(PRECOMMIT.get(
                 "meta", {}).get("draft_note", "")) or None)

    goal_rows = []
    for g in goals:
        goal_rows.append(
            f"<td><strong>{esc(g['id'])}</strong></td><td><strong>{esc(g['goal'])}</strong></td>"
            f"<td>{esc(g['definition'])}</td>"
            f"<td>{g['priority']}</td>"
            f'<td><span class="blank">not yet agreed</span></td>'
            + method_cell("review.html#register", "Household objective, not a figure", sources=[]))
    goal_table = table(
        "The household's own objectives, in priority order",
        ["Goal", "Objective", "What it means in this decision", "Priority", "Agreed on"],
        goal_rows,
        note="A financial model cannot rank these. A stated preference to keep a home in the family "
             "is legitimate and can outweigh a six-figure difference; the point of writing it down "
             "first is that the figures are then tested against the preference instead of the other "
             "way round.")

    gate_rows = []
    for g in gates:
        gate_rows.append(
            f"<td><strong>{esc(g['id'])}</strong></td><td>{esc(g['when'])}</td>"
            f"<td>{esc(g['what'])}</td>"
            f'<td><span class="badge assumption">not yet held</span></td>'
            + method_cell("review.html#register", "Procedure, not a figure", sources=[]))
    gate_table = table(
        "The gates: what must be true before any step is taken",
        ["Gate", "When", "What has to be true", "Status", "Source"], gate_rows,
        note="Each gate is a stop, not a task. Nothing on this site has been signed, filed or "
             "implemented, so every gate is still open.")

    # ---- the numbers the rules refer to, printed after the rules -----------------
    rent_rows = []
    for point in MIXED["rent_sensitivity"]:
        cells = []
        for p in point["paths"]:
            adj = p["opportunity_adjusted"]
            shown = m(adj) if adj is not None else m(p["asset_terminal"])
            cells.append(f"<td>{shown}</td>")
        rent_rows.append(f"<td>{m(point['rent'])} a year</td>" + "".join(cells)
                         + method_cell("#method", "Scenario, not a quote", sources=[]))
    rent_table = table(
        "The imputed-rent test: what living in the house has to be worth",
        ["Assumed market rent", "Live in it 30 years, then sell: value including the rent saved",
         "Live in it 10 years, then sell", "Live in it 10 years, then let it out"],
        rent_rows,
        note="Each column adds the market rent saved while the heir occupies the house, compounded at "
             "the same after-tax return as every other cash flow, to the path's terminal value. No "
             "official source publishes a market rent for a specific home and the input is still "
             "empty, so these are scenarios across a range, not a rent opinion. Compare the 30-year "
             f"column with selling at the inheritance, which is {m(p45['paths']['sell_equities']['terminal'])} "
             "in the same money.")

    be_rows = []
    for b in MIXED["rent_breakeven"]:
        be_rows.append(
            f"<td>{esc(b['label'])}</td><td>{m(b['annual_rent'])}</td>"
            f"<td>{m(b['monthly_rent'])}</td>"
            f"<td>{pcf(b['share_of_value_at_death'], 1)} of the value at death</td>"
            + method_cell("review.html#register", "Model output, rent unverified", sources=[]))
    be_table = '<h2 id="imputed">What living there has to be worth</h2>' + table(
        "The imputed-rent break-even: the market rent at which occupying the house matches selling",
        ["Path", "Rent needed per year", "Rent needed per month", "As a share of the value at death",
         "Basis"], be_rows,
        note="This answers &ldquo;we would live there, so what does that have to be worth?&rdquo;. The "
             "figure is the whole-house market rent at which the housing the household gets from living "
             "there closes the entire gap against selling at the inheritance and investing the proceeds. "
             "Compare it with what renting this house would actually cost. It is high because the "
             "comparator is a tax-free sale of a single asset compounded at 7% for thirty years. It is "
             "not an argument that the house could not command that rent, and it is not a rent opinion.")

    return (
        callout("flag", "Read this page before any other page", f"""
<p>This page is the household's own rulebook, and it is meant to be read <em>before</em> the
projections. The owner's instruction was explicit: agree in writing what would make the household
choose each path <strong>before the figures arrive</strong>, so the outcome cannot be
reverse-engineered from whichever projection is shown first. Read the rules below, fill in the two
decision columns when the household decides, and only then read the numbers.</p>
<p>Nothing here has been decided. The register is a testing rule, not a recommendation, and the
recommendation on the <a href="decision.html">decision page</a> is what the model says
<em>after</em> the test, not instead of it.</p>""")
        + rule_table
        + goal_table
        + callout("note", "Why the rules come before the numbers", """
<p>A single projection can be made to support almost any path, because it depends on a handful of
assumptions that nobody can verify: house prices over thirty years, the return on the reinvested
money, market rent, and the cost of holding the building. Writing the rule down first changes the
question from &ldquo;which path does this projection favour?&rdquo; to &ldquo;does the evidence clear
the bar the household set in advance?&rdquo;. That is the only defence against choosing a path and
then finding the assumptions that justify it.</p>""")
        + be_table
        + rent_table
        + callout("method", "How the test is applied", """
<ol>
<li><strong>Clear the first gate.</strong> Answer question A-1 on the <a href="questions.html">questions
page</a>: is the transfer between a parent and a child? If it is not, the Proposition 19 exclusion does
not exist and the rules below are re-read with a full reassessment.</li>
<li><strong>State the goals</strong> in the order they actually matter to the household, not in the
order the model ranks them.</li>
<li><strong>Set the rules</strong> - the conditions under which each path is the chosen one.</li>
<li><strong>Only then read the projections</strong>, and ask whether they clear the rules, not whether
they look favourable.</li>
<li><strong>Record the decision and its date</strong> beside the rule, and re-read the rules every year
at gate RG-3.</li>
</ol>""")
        + gate_table
    )


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
            + src_cell(["boe_pub29"], "How a bill is built; local rate withheld"))
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
            + method_cell("projections.html#method", "Model output", sources=["fred_casthpi"]),
            f"<td>Assessed value if nothing changes, grown at the 2% cap</td>"
            f"<td>{m(p45['factored_base_year_value'])}</td>"
            + src_cell(["boe_pub29", "rtc51"], "Proposition 13"),
            f"<td>Proposition 19: the indexed amount added to the prior factored base year value</td>"
            f"<td>{m(p45['prop19_cap'])}</td>"
            f"<td>Published as {m(V['prop19_value_cap_2025_2027']['value'])} for a transfer between 16 February "
            f"2025 and 15 February 2027, adjusted by statute every two years and next on 16 February 2027. The "
            f"figure in this row is that official amount projected forward to the modelled transfer year at the "
            f"assumed adjustment rate: a projection of an official figure, not one.</td>"
            + src_cell(["boe_lta25009", "boe_prop19", "rtc63_2"], "BOE table and statute"),
            f"<td>New assessed value if the heir moves in and claims the exclusion</td>"
            f"<td><strong>{m(p45['taxable_if_live'])}</strong></td>"
            + src_cell(["rtc63_2"], "Statutory formula"),
            f"<td>New assessed value if the heir does not move in</td>"
            f"<td><strong>{m(p45['taxable_if_rent'])}</strong></td>"
            + src_cell(["boe_pub29", "rtc63_2"], "Full reassessment"),
            f"<td>Tax bill today, projected to 2045</td><td>{m(p45['bill_today_projected'])}</td>"
            + method_cell("projections.html#method", "Model output", sources=["boe_pub29", "rtc51"]),
            f"<td>Tax bill from 2045, heir moves in</td><td>{m(p45['bill_if_live_year1'])}</td>"
            + method_cell("projections.html#method", "Model output", sources=["rtc63_2", "boe_lta25009"]),
            f"<td>Tax bill from 2045, heir does not move in</td><td>{m(p45['bill_if_rent_year1'])}</td>"
            + method_cell("projections.html#method", "Model output", sources=["rtc63_2", "boe_pub29"]),
        ],
        note="The statute enrols the inherited home at the transferor's factored base year value plus the "
             "indexed amount, and adds to that the excess of the market value over the two; the rows above are "
             "those three terms, so the new assessed value is the prior value plus everything the market value "
             "puts above the sheltered ceiling. That is the whole of the benefit, and it is why the shelter buys "
             "less the longer the transfer is delayed: the ceiling grows on a two-year statutory schedule while "
             "the market value of the house does not wait for it. The exclusion has never covered a rental "
             "building as such - before 2021 it reached $1,000,000 of \"other property\", and Proposition 19 "
             "removed that too, which is why Property B has no carry-forward to model.")

    cost_rows = [
        f"<td>Water</td><td>{m(A['annual_costs']['water']['low'])} to {m(A['annual_costs']['water']['high'])}</td><td>{m(A['annual_costs']['water']['mid'])}</td>"
        f'<td><span class="badge unverified">owner estimate</span></td>'
        + src_cell([], "Owner estimate, unverified"),
        f"<td>Electricity, net of solar export credit</td><td>{m(A['annual_costs']['electricity']['low'])} to {m(A['annual_costs']['electricity']['high'])}</td><td>{m(A['annual_costs']['electricity']['mid'])}</td>"
        f'<td><span class="badge unverified">owner estimate</span></td>'
        + src_cell(["cpuc_nem"], "Tariff rules"),
        f"<td>Home insurance, primary residence</td>"
        f"<td>{m(A['annual_costs']['insurance']['low'])} to {m(A['annual_costs']['insurance']['high'])} a year</td>"
        f"<td>{m(A['annual_costs']['insurance']['mid'])}</td>"
        f'<td><span class="badge unverified">owner estimate, now in a band</span></td>'
        + src_cell(["cdi_homeowners_avg", "cdi_tips"], "Published average for the form; where to quote"),
        f"<td>Mortgage, deed of trust or lien at the transfer</td><td>{BLANK_CELL}</td>"
        f"<td>none: modelled free and clear</td>"
        f'<td><span class="badge assumption">not supplied</span></td>'
        + src_cell(["uscode1701j3"], "What an encumbrance changes; publisher's rule"),
        f"<td>Maintenance and repair</td><td>not supplied</td><td>{m(MODEL['costs_a_now']['maintenance'])}</td>"
        f'<td><span class="badge assumption">assumption</span></td>'
        + src_cell([], "No official source"),
        f"<td>Property tax, today</td><td>&mdash;</td><td>{m(MODEL['costs_a_now']['property_tax'])}</td>"
        f'<td><span class="badge derived">derived</span></td>'
        + src_cell([], "Local rate withheld for privacy"),
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

    # Water and sewer tariffs are withheld from the public edition for privacy:
    # provider and district names, and their web addresses, would identify the area.
    tariffs = (
        '<section class="withheld"><h3>Water and sewer: withheld for privacy</h3>'
        '<p>The official water and sewer tariffs for this property are not published here, because the '
        "provider and district names and their web addresses would identify the area. The owner's water "
        'estimate in the costs table above stays marked unverified. Confirm the provider and the charges '
        "from the parcel's own bill.</p></section>"
    )

    return (
        table("Property A at a glance",
              ["Fact", "Value", "Source"],
              [
                  f"<td>Role</td><td>Inherited through a trust, planned 2040 to 2050. Not owned by the heir today.</td>"
                  + src_cell([], "Owner statement"),
                  f"<td>Jurisdiction</td><td>{esc(A['jurisdiction'])}</td>"
                  + src_cell([], "Withheld for privacy"),
                  f"<td>Estimated market value, November 2026</td><td>{m(A['estimated_market_value_2026'])}</td>"
                  + src_cell([], "Owner estimate, unverified"),
                  f"<td>Current assessed value</td><td>{m(A['roll'][0]['assessed'])}</td>"
                  + src_cell([], "Owner record, unverified"),
                  f"<td>Current property tax bill</td><td>{m(MODEL['costs_a_now']['property_tax'])}</td>"
                  + src_cell([], "Local rate withheld for privacy"),
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
        + table("How a property tax rate is built (state law and the county's published rate book, FY 2025-26)",
                ["Component", "Rate", "Source"],
                [("<td>1% maximum levy, applied to every parcel</td><td>1.00000%</td>"
                  + src_cell(["boe_pub29"], "State law summary")),
                 ("<td>County Retirement Levy</td><td>0.03880%</td>"
                  + src_cell([], "Official county rate book withheld for privacy")),
                 ("<td>County Library Retirement Levy</td><td>0.00240%</td>"
                  + src_cell([], "Official county rate book withheld for privacy")),
                 ("<td>County Housing Bond 2016</td><td>0.00560%</td>"
                  + src_cell([], "Official county rate book withheld for privacy")),
                 ("<td>City, school and special-district voter-approved bonds</td><td>varies by tax rate area</td>"
                  + src_cell([], "Official county rate book withheld for privacy"))],
                note="The county publishes 816 tax rate areas for FY 2025-26; the components above are the "
                     "countywide ones listed in the book's own summary. The book is an official published "
                     "document, but its web address names the jurisdiction, so it is not linked on the public "
                     "site and its rows are registered instead. The parcel's own rate area and total "
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
    ph = MODEL["prop_h"]
    roll_rows = []
    for r in MODEL["roll_b"]:
        roll_rows.append(
            f"<td>{r['year']}</td><td>{m(r['assessed'])}</td>"
            f"<td>{m(r['bill'])}</td><td>{m(r['fitted'])}</td>"
            f"<td>{m(r['residual'])}</td>"
            + src_cell(["boe_pub29"], "Rule; local rate withheld for privacy"))
    roll = table("Property B assessment roll and tax bill, as supplied, rounded to the nearest $10",
                 ["Year", "Assessed value", "Tax bill as supplied", "Bill implied by the model",
                  "Difference", "Source"], roll_rows,
                 note="The state rule behind the fitted column is linked. The local secured rate behind it is "
                      "withheld from the public site for privacy; the parcel's own bill is the controlling record.")

    cost_rows = [
        f"<td>Water, all three units</td><td>{m(B['annual_costs']['water']['low'])} to {m(B['annual_costs']['water']['high'])}</td><td>{m(B['annual_costs']['water']['mid'])}</td>"
        f'<td><span class="badge unverified">owner estimate</span></td>' + src_cell([], "No official rate checked"),
        f"<td>Electricity</td><td>{m(B['annual_costs']['electricity']['low'])} to {m(B['annual_costs']['electricity']['high'])}</td><td>{m(B['annual_costs']['electricity']['mid'])}</td>"
        f'<td><span class="badge unverified">owner estimate</span></td>' + src_cell([], "No official rate checked"),
        f"<td>Insurance, rental policy</td>"
        f"<td>{m(B['annual_costs']['insurance']['low'])} to {m(B['annual_costs']['insurance']['high'])} a year</td>"
        f"<td>{m(B['annual_costs']['insurance']['mid'])}</td>"
        f'<td><span class="badge unverified">owner estimate, now in a band</span></td>'
        + src_cell(["cdi_df_rental", "cdi_tips"], "Published average for the landlord form; where to quote"),
        f"<td>Mortgage, deed of trust or lien on the building</td><td>{BLANK_CELL}</td>"
        f"<td>none: modelled free and clear</td>"
        f'<td><span class="badge assumption">not supplied</span></td>'
        + src_cell(["uscode1701j3"], "A loan on fewer than five units is inside the federal rule"),
        f"<td>Maintenance and repair</td><td>not supplied</td><td>{m(MODEL['costs_b_now']['maintenance'])}</td>"
        f'<td><span class="badge assumption">assumption</span></td>' + src_cell([], "No official source"),
        f"<td>Property tax, today</td><td>&mdash;</td><td>{m(MODEL['costs_b_now']['property_tax'])}</td>"
        f'<td><span class="badge derived">derived</span></td>' + src_cell([], "Local rate withheld for privacy"),
        f"<td>Parcel tax passed November 2026 on the preliminary count (not yet certified), first due fiscal year {esc(ph['first_fiscal_year'])}</td>"
        f"<td>{m(ph['base'])} a year for a multifamily parcel up to 5,000 sq ft; more if the building area "
        f"is larger ({ph['rate_over_5000_sqft']} a sq ft over 5,000, capped at {m(ph['max_tax'])})</td>"
        f"<td>not added to any total: the band is not determined</td>"
        f'<td><span class="badge unverified">band not determined</span></td>'
        + src_cell([], "Official city documents withheld for privacy"),
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
            f"<td>The city's rent ordinance: allowed annual increase</td><td>1.6% from 1 March 2026 to 28 February 2027, "
            f"based on 60% of the change in the regional consumer price index. One increase every twelve "
            f"months. There is no limit on the rent first charged to a new tenant of an empty unit.</td>"
            + src_cell([], "Official city page withheld for privacy"),
            f"<td>Proposed cap on banked and capital improvement increases</td>"
            f"<td>A city ordinance file would limit combined banked and "
            f"capital improvement increases to 10% a year. <strong>Not enacted.</strong></td>"
            + src_cell([], "Official file not linked for privacy"),
            f"<td>Statewide rent cap</td><td>Gross rent cannot rise more than 5% plus the change in the cost "
            f"of living, or 10%, whichever is lower, over twelve months. Housing already under a stricter "
            f"local ordinance is excluded.</td>"
            + src_cell(["civ1947_12"], "Civil Code 1947.12"),
            f"<td>Statewide just cause</td><td>A tenancy cannot be ended without a stated just cause, and a "
            f"no-fault termination including an owner move-in carries a relocation payment.</td>"
            + src_cell(["civ1946_2"], "Civil Code 1946.2"),
            f"<td>Which rules apply</td><td>Whether these units are covered by the city's Rent "
            f"Ordinance, by the statewide act, or by an exemption depends on the building's age, its "
            f"ownership and the notices given. This site does not verify that.</td>"
            + src_cell(["civ1947_12"], "Statewide rule"),
        ])

    ph_terms = table(
        "Parcel tax passed in Property B's city, November 2026, on the preliminary count (Proposition H): official terms",
        ["Term", "What the measure says", "Source"],
        [
            f"<td>Status</td><td>Passed at the election held on 3 November 2026 on the preliminary count, not yet "
            f"certified, so it is not yet final. The local returns were still preliminary when these terms were "
            f"read on 15 November 2026 (about 900 ballots left to count) and were re-checked on 16 November 2026 "
            f"against the official preliminary results; the department of elections may take up to 30 days to "
            f"certify the result.</td>"
            + src_cell([], "Official city documents withheld for privacy"),
            "<td>What it is</td><td>An annual parcel tax on real property in Property B's city, funding "
            "public transit operations, for fifteen years.</td>"
            + src_cell([], "Official city documents withheld for privacy"),
            f"<td>First levy and expiry</td><td>First due for fiscal year {esc(ph['first_fiscal_year'])} on "
            f"the property tax bill mailed in the fall of 2027, paid in the same two installments as the "
            f"ordinary property tax. It expires on 30 June 2042 by its own terms.</td>"
            + src_cell([], "Official city documents withheld for privacy"),
            f"<td>Rate on a multifamily residential parcel</td><td>Building area up to 5,000 sq ft: "
            f"{m(ph['base'])} a year for the first fiscal year. Above 5,000 sq ft: {m(ph['base'])} plus "
            f"{ph['rate_over_5000_sqft']} a square foot, capped at {m(ph['max_tax'])} a parcel.</td>"
            + src_cell([], "Official city documents withheld for privacy"),
            "<td>Inflation adjustment</td><td>All dollar amounts adjust each year, first on 31 December "
            "2027, by the change in the local all-items consumer price index published by the federal "
            "statistics agency; per-square-foot amounts round down to the nearest tenth of a cent and other "
            "amounts down to the nearest dollar.</td>"
            + src_cell([], "Official city documents withheld for privacy"),
            f"<td>Tenant pass-through</td><td>On a rent-controlled unit the landlord may pass through up to "
            f"50% of the tax, capped at {m(ph['pass_through_unit_cap'])} a unit a year, and not at all if "
            f"the base rent was set on or after 1 June {esc(ph['pass_through_cutoff'][:4])}. On the two let "
            f"units that is at most {m(ph['pass_through_max_total'])} a year, if the units qualify.</td>"
            + src_cell([], "Official city documents withheld for privacy"),
            f"<td>Senior owner-occupant reduction</td><td>An owner aged 65 or older before 1 July of the "
            f"fiscal year who occupies a unit as a principal residence gets {m(ph['senior_reduction_per_occupied_unit'])} "
            f"off for each such unit, by application; the tax cannot go below zero.</td>"
            + src_cell([], "Official city documents withheld for privacy"),
            "<td>Which band applies here</td><td>Not determined. The tax depends on the parcel's building "
            "area, which was not supplied.</td>"
            + src_cell([], "Logged on the register"),
        ],
        note="The publisher of these terms is a city body. It is not named or linked on the public site, "
             "because the jurisdiction identifies the properties; the terms were read on the publisher's own "
             "domain on 15 November 2026 and are logged on the review register.")

    ph_rows = []
    for r in ph["rows"]:
        ph_rows.append(f"<td>{esc(r['fy'])}</td>"
                       f"<td>{m(r['low'])}</td><td>{m(r['baseline'])}</td><td>{m(r['high'])}</td>"
                       + src_cell([], "Official city documents withheld for privacy"))
    ph_rows.append(
        f"<td><strong>Total to expiry, fifteen years</strong></td>"
        f"<td>{m(ph['totals_to_expiry']['low'])}</td>"
        f"<td>{m(ph['totals_to_expiry']['baseline'])}</td>"
        f"<td>{m(ph['totals_to_expiry']['high'])}</td>"
        + method_cell("#method", "Model output", sources=[]))
    ph_schedule = table(
        "Property B parcel tax by fiscal year, at the modelled inflation band",
        ["Fiscal year", "At 1.8% inflation", "At 2.5% inflation", "At 3.0% inflation", "Source"],
        ph_rows,
        note="The first row is the official amount for the first fiscal year, published verbatim; every "
             "later row is that amount adjusted by the measure's own inflation rule at one of the three "
             "inflation rates this site uses. The band that applies to the parcel is not determined, so no "
             "figure in this table is added to the running-cost totals anywhere on this site. Nothing here "
             "touches Property A, which sits in a different jurisdiction.")

    return (
        table("Property B at a glance",
              ["Fact", "Value", "Source"],
              [
                  f"<td>Role</td><td>Already owned by the heir. Rental income is already flowing and the heir can live here without losing it.</td>"
                  + src_cell([], "Owner statement"),
                  f"<td>Jurisdiction</td><td>{esc(B['jurisdiction'])}</td>"
                  + src_cell([], "Withheld for privacy"),
                  f"<td>Estimated market value, November 2026</td><td>{m(B['estimated_market_value_2026'])}</td>"
                  + src_cell([], "Owner estimate, unverified"),
                  f"<td>Current assessed value</td><td>{m(B['roll'][0]['assessed'])}</td>"
                  + src_cell([], "Owner record, unverified"),
                  f"<td>Current property tax bill</td><td>{m(MODEL['costs_b_now']['property_tax'])}</td>"
                  + src_cell([], "Local rate withheld for privacy"),
                  f"<td>Units</td><td>{B['units']}, of which {B['units_rented']} are let</td>"
                  + src_cell([], "Owner statement"),
                  f"<td>Rent received</td><td>{m(B['rent']['monthly'])} a month, {m(B['rent']['annual'])} a year</td>"
                  + src_cell([], "Owner statement, unverified"),
                  f"<td>Effective tax rate on assessed value</td><td>{MODEL['projection_b'][0]['effective_rate']}%</td>"
                  + src_cell([], "Computed from the owner's bills"),
              ])
        + roll
        + costs
        + rules
        + ph_terms
        + ph_schedule
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
                 + src_cell(["rtc63_2", "boe_pub29", "irs_basis"], "Governing rules")
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
def capital_plan_section() -> str:
    """The five-year maintenance and capital plan the brief asks for.

    The model charges maintenance as a percentage of value, which spreads a
    roof over thirty years and hides the fact that a roof arrives in one year.
    This section republishes the same money as a schedule: the percentage,
    converted into a five-year budget for each path, and the component list a
    contractor actually quotes against. No component cost is invented - the
    schedule says which items are unquoted and what the allowance has to cover,
    because a made-up roof price would be worse than an honest blank.

    The allowance for Property A is the owner-occupied rate; the rental rate is
    shown beside it because the same house costs more to keep when a tenant
    lives in it and a landlord pays for turnover.
    """
    a = INPUTS["property_a"]["estimated_market_value_2026"]
    b = INPUTS["property_b"]["estimated_market_value_2026"]
    own = INPUTS["property_a"]["annual_costs"]["maintenance_pct_owner_occupied"]["value"]
    rental = INPUTS["property_a"]["annual_costs"]["maintenance_pct_rental"]["value"]
    b_rate = INPUTS["property_b"]["annual_costs"]["maintenance_pct"]["value"]
    infl = INPUTS["assumptions"]["inflation"]["baseline"]
    growth = INPUTS["assumptions"]["house_growth"]["baseline"]

    def five_year_budget(value: float, rate: float, label: str) -> list[str]:
        rows = []
        total = 0.0
        for i in range(5):
            amt = money10(value * rate * ((1 + infl) ** i))
            total += amt
            rows.append(f"<td>{2026 + i}</td><td>{m(money10(value * ((1 + growth) ** i)))}</td>"
                        f"<td>{pcf(rate, 2)}</td><td>{m(amt)}</td><td>{m(total)}</td>"
                        + method_cell("#method", "Assumption, no quote", sources=[]))
        return rows

    a_rows = five_year_budget(a, own, "Property A, owner-occupied")
    b_rows = five_year_budget(b, b_rate, "Property B")
    plan = table(
        "The five-year maintenance allowance, year by year, as the model charges it",
        ["Year", "Value the percentage is applied to", "Rate", "Allowance that year",
         "Cumulative five-year budget", "Basis"],
        a_rows + b_rows,
        note="The model charges maintenance as a percentage of value, which is the only defensible way to "
             "project it without quotes. Read as a budget, that is the money available to spend. It is a "
             "sinking fund, not a schedule of works: the percentage does not know when the roof is due.")

    comps = table(
        "The components the allowance has to cover, and which of them are quoted",
        ["Component", "Typical interval", "Quoted for either property?", "What the allowance has to absorb"],
        [
            "<td>Roof covering and flashings</td><td>20 to 30 years</td><td>No quote</td>"
            "<td>The largest single item in most five-year windows. A replacement landing inside the window "
            "can consume several years of the allowance at once.</td>"
            + method_cell("#method", "Assumption, no quote", sources=[]),
            "<td>Exterior paint and siding</td><td>7 to 10 years</td><td>No quote</td>"
            "<td>Predictable and deferrable, which is what makes it the usual casualty of a tight year.</td>"
            + method_cell("#method", "Assumption, no quote", sources=[]),
            "<td>Water heater</td><td>10 to 15 years</td><td>No quote</td>"
            "<td>Emergency replacement; cannot be deferred and does not improve value.</td>"
            + method_cell("#method", "Assumption, no quote", sources=[]),
            "<td>Furnace and ductwork</td><td>15 to 25 years</td><td>No quote</td>"
            "<td>An efficiency-driven replacement is larger than a like-for-like repair.</td>"
            + method_cell("#method", "Assumption, no quote", sources=[]),
            "<td>Solar inverter and monitoring</td><td>10 to 15 years</td><td>No quote</td>"
            "<td>Property A has solar. The panels outlast the inverter, so an inverter replacement is likely "
            "inside a long hold and the net electricity benefit in the projection does not include it.</td>"
            + method_cell("#method", "Assumption, no quote", sources=[]),
            "<td>Windows and doors</td><td>20 to 30 years</td><td>No quote</td>"
            "<td>Usually deferred to sale, which means a buyer discounts for it instead of the owner paying for it.</td>"
            + method_cell("#method", "Assumption, no quote", sources=[]),
            "<td>Unit turnover: paint, flooring, appliances (Property B only)</td><td>On vacancy</td><td>No quote</td>"
            "<td>This is why a rental carries a higher rate than an owner-occupied home. It is also the item "
            "the letting path is most sensitive to, because it arrives when the tenant leaves, not on a schedule.</td>"
            + method_cell("#method", "Assumption, no quote", sources=[]),
        ],
        note="A list of what the allowance is for, not a quote for any of it. No component cost is published "
             "because none has been quoted, and a fabricated roof price would be worse than a blank.")

    rental_rows = []
    for path, label in (("live_in", "Live in Property A for thirty years"),
                        ("live_then_rent", "Live in it, then let it"),
                        ("rent_out", "Let Property A for thirty years")):
        p45 = {x["inherit_year"]: x for x in MODEL["paths"]}[2045]
        terminal = p45["paths"][path]["terminal"]
        rental_rows.append(
            f"<td>{label}</td><td>{pcf(own, 2)}</td><td>{pcf(rental, 2)}</td>"
            f"<td>{m(money10(a * (rental - own)))} a year, rising with inflation</td>"
            f"<td>{m(money10(a * (rental - own) * 5))} over five years</td><td>{m(terminal)}</td>"
            + method_cell("#method", "Model output", sources=[]))
    switch = table(
        "What the same house costs to keep when a tenant lives in it",
        ["Path", "Owner-occupied rate", "Rental rate used by this site",
         "Difference in the first year", "Difference over five years", "Terminal value at 2045"],
        rental_rows,
        note=f"A house costs more to keep when it is let: turnover, longer hours of use and a landlord's "
             f"obligations. Moving from {pcf(own, 2)} to {pcf(rental, 2)} of value is the assumption "
             f"this site makes, and it is unverified. If it is too low, the letting path is flattered; if it "
             f"is too high, occupying and then letting looks worse than it is.")

    return ('<h2 id="capital">The five-year maintenance and capital plan</h2>'
            + callout("flag", "A percentage of value is a budget, not a plan", f"""
<p>The brief asks for a five-year maintenance and capital plan. The model has maintenance as
{pcf(own, 2)} of value a year for an owner-occupied home and {pcf(b_rate, 2)} for the three-unit
building, growing with inflation. That is the right shape for a thirty-year projection and the wrong shape for
planning five years of work, because a roof is not spread evenly. Below, the same money is written as a
five-year budget, and the components it has to cover are listed with their typical intervals. Nothing in the
component list is priced: nothing has been quoted, so a figure would be invented.</p>""")
            + plan
            + comps
            + switch)


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
                       + method_cell("#method", "Model output", sources=["boe_pub29", "rtc51"]))
        return out

    tbl_a = table("Property A running costs, projected at the modelled inflation rate",
                  ["Year", "Water", "Electricity, net of solar", "Insurance",
                   "Maintenance", "Property tax", "Total"], rows_for("A"))
    tbl_b = table("Property B running costs, projected at the modelled inflation rate",
                  ["Year", "Water", "Electricity", "Insurance", "Maintenance",
                   "Property tax", "Total"], rows_for("B"),
                  note="Not included in this table: the parcel tax passed on the preliminary count (not yet certified) in Property B's city at the "
                       "November 2026 election, first levied for fiscal year 2027-2028 and expiring 30 June "
                       "2042. Its band depends on the parcel's building area, which was not supplied, so it "
                       "is published as a schedule on the Property B page and is not added to these totals.")

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
<p>Two official series exist. The <strong>NAIC Homeowners Insurance Report</strong> (2023 data, published July
2026) is the state-level statistical series regulators use: average premium is written premium divided by written
exposures in house-years, as reported to statistical agents, for the dwelling fire and homeowners policy forms
separately. {slink('naic_hmr_2023')} The California Department of Insurance publishes its own statewide average
written premium for each policy form, and the newest year of the series read for this site, experience year 2017,
gives <strong>$1,074</strong> for an owner-occupied homeowners multi-peril policy {slink('cdi_homeowners_avg')}
and <strong>$519</strong> for the form the Department describes as a rental dwelling or landlord policy on up to
four units {slink('cdi_df_rental')} - the form family a three-unit building like Property B is written on. The
owner-occupied average for that form has itself risen from <strong>$620</strong> in 2001, so a statewide average
is a moving thing as well as a blended one. Until this edition neither building's insurance was compared with
anything: both were carried at a single {m(MODEL['costs_a_now']['insurance'])} figure, which is the middle of a
band now rather than the whole assumption.</p>
<p>Neither series is a premium for either building and neither must be read as one: a three-unit rental in the
city is written on a dwelling fire form and a single-family home in the county on a homeowners form, at entirely
different amounts of insurance. The NAIC report itself warns that average premium rises with the amount of
insurance and that dwelling fire premiums are generally lower than homeowners package premiums because the
coverage is more limited. A statewide average therefore <strong>understates</strong> a high-value home. The
report's own by-state averages sit in Table 4 (page 30 onward) and Table 5 (page 135). Those pages were
re-tried on 16 November 2026 and are still not machine-readable in this build, so no average-premium figure from
them is published here, under the rule that nothing is inferred or copied second-hand. A premium for either
building remains blank until it is quoted: what the published form averages can do is bound an assumption, not
replace it.</p>
<p>One coverage limit is worth the adviser's attention: the California FAIR Plan, the state's insurer of last
resort, caps a residential dwelling policy at <strong>$3,000,000 combined</strong> (official CDI figure). Property A's
owner-estimated value is $3,100,000, and that estimate is itself unverified. If standard-market cover cannot be
placed for either building, cover above the cap would be needed and its cost is unknown until quoted. No premium
for either building appears on this site; both remain owner estimates flagged unverified.</p>""")
        + table("Insurance market context, officially published",
                ["Item", "Published figure", "Source"],
                [
                    "<td>California dwelling fire policies, 2023 (the form a landlord policy is written on)</td>"
                    "<td>329,584.8 house-years, 3.1% of the state market</td>" + src_cell(["naic_hmr_2023"], "NAIC report, Table 1"),
                    "<td>California owner-occupied homeowners policies, 2023</td>"
                    "<td>6,237,525.5 house-years, 58.8% of the state market</td>" + src_cell(["naic_hmr_2023"], "NAIC report, Table 1"),
                    "<td>California dwelling fire and owner-occupied policies carrying $1,000,000 or more of insurance, 2023</td>"
                    "<td>8.4% of exposures. Property A sits above this band, so statewide averages understate it.</td>" + src_cell(["naic_hmr_2023"], "NAIC report, Table 3"),
                    "<td>Statewide average premiums by form and amount of insurance</td>"
                    "<td>Table 4 (dwelling fire and owner-occupied, page 30 onward) and Table 5 (tenant and condominium, page 135) are the official by-state averages. Those pages were not machine-readable in this build, so the figures are left blank here and flagged, not inferred.</td>" + src_cell(["naic_hmr_2023"], "NAIC report, Tables 4 and 5"),
                    "<td>California statewide average, owner-occupied homeowners policy, experience year 2017</td>"
                    "<td>$1,074 a year, quoted as published</td>" + src_cell(["cdi_homeowners_avg"], "Department of Insurance report"),
                    "<td>California statewide average, rental dwelling or landlord policy on up to 4 units, experience year 2017</td>"
                    "<td>$519 a year, quoted as published; this is the form family Property B's policy belongs to</td>"
                    + src_cell(["cdi_df_rental"], "Department of Insurance report"),
                    "<td>The same owner-occupied series at its first published year, 2001</td>"
                    "<td>$620 a year, so this statewide average rose about 73% over sixteen years</td>"
                    + src_cell(["cdi_homeowners_avg"], "Department of Insurance report"),
                ],
                note="These are market-wide published figures, not quotes and not estimates for either building. "
                     "The owner estimate used in the model is flagged unverified and should be replaced with "
                     "quotes; the published form averages bound it, which is the most an official series can do "
                     "for a property nobody has quoted.")
        + table("Property B net income today",
                ["Item", "Amount", "Source"],
                [
                    f"<td>Rent received, two units</td><td>{m(net['rent'])}</td>" + src_cell([], "Owner statement, unverified"),
                    f"<td>Less water</td><td>{m(-net['water'])}</td>" + src_cell([], "Owner estimate; city schedule withheld for privacy"),
                    f"<td>Less electricity</td><td>{m(-net['electricity'])}</td>" + src_cell([], "Owner estimate, unverified"),
                    f"<td>Less insurance</td><td>{m(-net['insurance'])}</td>" + src_cell([], "Owner estimate, unverified"),
                    f"<td>Less maintenance at the assumed rate</td><td>{m(-net['maintenance'])}</td>" + src_cell([], "Assumption"),
                    f"<td>Less property tax</td><td>{m(-net['property_tax'])}</td>" + src_cell([], "Local rate withheld for privacy"),
                    f"<td><strong>Net, before income tax and vacancy</strong></td><td><strong>{m(net_now)}</strong></td>" + method_cell("#method", "Model output", sources=[]),
                ],
                note=f"That is about {net_now / B['estimated_market_value_2026'] * 100:.1f}% of the estimated value. "
                     f"A vacancy allowance and income tax would reduce it further.")
        + '<h2>How the projections are built</h2>'
        + table("Projection method", ["Step", "What is done", "Source"],
                [
                    "<td>Assessed value</td><td>Grown at the Proposition 13 cap of 2% a year, which has been binding in every year of both supplied rolls.</td>" + src_cell(["boe_pub29", "rtc51"], "Proposition 13"),
                    "<td>Tax bill</td><td>Ad valorem rate times assessed value, plus a fixed charge grown at the modelled inflation rate.</td>" + src_cell(["boe_pub29"], "Rule; local rates withheld for privacy"),
                    "<td>Water, power, insurance, maintenance</td><td>Grown at the modelled inflation rate. No real-terms change in usage or tariffs is assumed.</td>" + src_cell(["ssa_trustees"], "Inflation anchor"),
                    "<td>Market value</td><td>Grown at the modelled house price growth rate of 4% a year.</td>" + src_cell(["fred_casthpi"], "Historical index"),
                ],
                note="A constant rate is used for the year-by-year page because it is the only way to show a "
                     "readable table. It is not a forecast. The <a href=\"black-swan.html\">black swan page</a> "
                     "shows what happens when growth and inflation are not constant.")
        + insurance_band_section()
        + capital_plan_section()
        + callout("flag", "Three cost numbers that need replacing", """
<ol>
<li><strong>Insurance on both properties.</strong> This was one round number at each building - the same number
for a primary residence and for a three-unit rental, which cannot both be right - and it is now a band, floored
by the Department's published statewide average for the matching policy form and capped by a stated scenario: see
<a href="#insurance-band">Insurance: the band, and what it is worth</a>. The industry benchmark is the NAIC
Homeowners Insurance Report, whose by-state averages for the correct forms sit in Table 4, beyond the pages this
build can read, so they are left blank rather than copied from a secondary source. No official source publishes a
premium for this postal area or for either building. Get three quotes for each building, one of which should be a
landlord policy. See <a href="suggestions.html">suggestion S-01</a>.</li>
<li><strong>Maintenance.</strong> No figure was supplied. This site assumes 0.5% of value a year for an
owner-occupied home, 0.75% for Property A as a rental and 1.5% for the older three-unit building. Replace these
with the actual five-year repair history. The <a href="#capital">five-year capital plan</a> above writes the
same allowance out year by year and lists the components it has to cover.</li>
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
                       + method_cell("#method", "Model output", sources=["boe_pub29", "rtc51"]))
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
        + dist_chart(ECON["bootstrap"].get("chart", {}),
                     "Property A value, one year at a time: 2,000 resampled paths against the single line")
        + callout("note", "Why there is a band and a line", """
<p>The tables below are one line: 4.0% a year, every year. The chart above is the same property value drawn
from the seeded block-bootstrap on the <a href="economy.html">historical record</a> page, which resamples the
actual ten-year runs of California house prices and consumer prices instead of assuming they repeat. The band
is wide, and the single line sits inside it rather than at its middle. Neither is a forecast; the chart's
purpose is to stop a single line being read as one.</p>
<p>The band is a 5th-to-95th percentile interval, so one path in ten ends outside it on each side. The
distribution is skewed: the middle path is well above the constant line at the far end, because the bootstrap
includes the high-growth decades of the record, while the low end is limited by how far a house price can
fall.</p>""")
        + fan_section()        + table("Property A: value, assessed value and tax bill, if the assessment is never reset",
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
def fan_section() -> str:
    """Year-by-year fan chart: the constant 4% line against the resampled record.

    Three series on one axis: the value at the inheritance, the value after a
    thirty-year hold, and the value the sale proceeds reach if they are invested
    instead. The point of putting them together is that the holder's upside tail
    and the seller's downside tail are both real, and only the shape shows it.
    """
    series = {s["key"]: s for s in MIXED["distribution"]["series"]}
    vod, live, sell = series["value_at_death"], series["live"], series["sell"]
    const_2045 = next((x["value"] for x in MODEL["projection_a"] if x["year"] == 2045), 0)
    rows = []
    for i in range(11):
        rows.append({
            "label": "p100" if i == 10 else f"p{i*10}",
            "values": [("sell", sell["deciles"][i], "Sell and invest"),
                       ("live", live["deciles"][i], "Live in it 30 years"),
                       ("band", vod["deciles"][i], "Value at the 2045 inheritance")],
        })
    chart = fan_chart(
        "After thirty years, by decile of the verified record",
        f"The constant 4% a year gives {m(const_2045)} at the 2045 inheritance. The "
        f"{MIXED['distribution']['draws']} resampled histories put the value at the inheritance "
        f"anywhere from {m(vod['deciles'][0])} to {m(vod['deciles'][10])}, and the thirty-year "
        f"outcome for either path across a much wider band.",
        "money", rows,
        "Read the tails, not the middle. In the bottom decile the household that lived in the house "
        "is close to the household that sold, because house prices there did badly while the sale "
        "proceeds still earned the modelled equity return. In the top decile keeping the house wins "
        "by more than a hundred million nominal dollars. The median favours selling in every "
        "comparison, and the spread is why the answer is published as a share of draws.")
    return ('<section id="fan"><h2>Year by year, with the record\'s own variation</h2>'
            f'<p>The tables on this page use one constant growth rate so the arithmetic is legible. '
            f'That is not what the record looks like: annual house price growth in the California '
            f'record has run from minus 20.0% to plus 25.3%. The fan below redraws both paths using '
            f'{MIXED["distribution"]["draws"]} resampled fifty-year histories of the verified '
            f'series, drawn in ten-year blocks so house prices and consumer prices move together as '
            f'they did. The method is the <a href="economy.html">economy page</a>\'s.</p>'
            + chart + "</section>")


def sale_charges_section() -> str:
    """The published statutory charges on a sale of Property A, itemised.

    The owner's brief asks for the transfer tax and recording fees to be priced
    into the sell path rather than living inside a single 5.5% assumption. They
    are small - together about 0.11% of the price - and the honest finding is
    that almost all of the modelled 5.5% is private charges, not statute. The
    section says so instead of implying the statutes explain the 5.5%.
    """
    f = MIXED["fees_example"]
    rows = [
        ("County documentary transfer tax (Revenue and Taxation Code 11911(a): "
         "$0.55 per $500 of consideration, i.e. 0.11% of the price)",
         m(f["documentary_transfer_tax"]), ["rtc11911"]),
        ("City documentary transfer tax (section 11911(b): up to half the county rate again, "
         "with a credit against the county tax)",
         "not modelled: whether a city tax applies to this property is withheld for privacy",
         []),
        ("$75 instrument fee (Government Code 27388.1)",
         f"{m(0)} &mdash; exempt, because 27388.1(a)(2)(A) excludes an instrument recorded in "
         f"connection with a transfer subject to the documentary transfer tax", ["gov27388_1"]),
        ("Recording the deed (Government Code 27361(a): up to $10 for the first page and $3 for "
         "each further page; four pages assumed)",
         m(f["recording_fee_27361"]), ["gov27361"]),
        ("<strong>Published statutory charges in total</strong>",
         f"<strong>{m(f['published_total'])}</strong>", []),
        ("Commission, escrow, title and the other private closing charges "
         "(the remainder of the modelled 5.5%)",
         f"{m(f['private_closing_costs'])} &mdash; a private quote, not a statute", []),
        ("<strong>Modelled total selling cost on the same price</strong>",
         f"<strong>{m(f['modelled_selling_cost'])}</strong>", ["rtc11911"]),
    ]
    out = []
    for a, b, srcs in rows:
        cell = (src_cell(srcs, "Official source") if srcs
                else method_cell("review.html#register", "Private cost or deliberate omission", sources=[]))
        out.append(f"<td>{a}</td><td>{b}</td>" + cell)
    tbl = table(
        "What a sale actually owes the state and the county, itemised on a $5,000,000 price",
        ["Charge", "Amount", "Source"], out,
        note="Every statutory charge here is computed from the published rate, and the section "
             "numbers are printed so the arithmetic can be checked. The finding is the split: "
             f"{f['published_share_of_modelled']}% of the modelled selling cost is statute and "
             f"{f['private_share_of_modelled']}% is a private quote. The 5.5% assumption is "
             "therefore a market-cost assumption, not a tax assumption, and it is unverified "
             "wherever it appears.")
    return ('<h2>The transfer tax and recording fees on the sell path</h2>'
            + callout("note", "Priced, and smaller than the assumption it sits inside", f"""
<p>The sell path carries a 5.5% selling cost. The brief asked for the transfer tax and the
recording fees to be priced into that path explicitly rather than left inside the percentage, so
they are itemised below. On a {m(f['price'])} sale they come to {m(f['published_total'])} in total,
about {f['published_share_of_modelled']}% of the modelled selling cost. The other
{f['private_share_of_modelled']}% is commission, escrow and title - quoted by private companies,
not set by statute, and the part of the assumption that needs three real quotes before it is
relied on.</p>
<p>One charge that checklists routinely add does <strong>not</strong> apply. The $75 fee on
recorded real-estate instruments is expressly excluded where the instrument is recorded in
connection with a transfer subject to the documentary transfer tax, which a sale is. It is listed
as zero with the reason, because deleting it silently would hide the verification.</p>""")
            + tbl)


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
                       f"<td>Sale price</td><td>{m(now_sale['price'])}</td><td>{m(late_sale['price'])}</td><td>{m(rent_sale['price'])}</td>" + method_cell("#method", "Model output", sources=["fred_casthpi"]),
                       f"<td>Selling costs</td><td>{m(now_sale['costs'])}</td><td>{m(late_sale['costs'])}</td><td>{m(rent_sale['costs'])}</td>" + method_cell("#method", "Model output", sources=[]),
                       f"<td>Basis</td><td>{m(now_sale['basis'])}</td><td>{m(late_sale['basis'])}</td><td>{m(rent_sale['basis'])}</td>" + method_cell("#method", "Model output", sources=["irs_basis"]),
                       f"<td>Gain</td><td>{m(now_sale['gain'])}</td><td>{m(late_sale['gain'])}</td><td>{m(rent_sale['gain'])}</td>" + method_cell("#method", "Model output", sources=["irs_basis", "irs_tc409"]),
                       f"<td>Of which depreciation recapture</td><td>{m(now_sale['recapture'])}</td><td>{m(late_sale['recapture'])}</td><td>{m(rent_sale['recapture'])}</td>" + method_cell("#method", "Model output", sources=["irs_tc409"]),
                       f"<td>Section 121 exclusion</td><td>{m(now_sale['exclusion'])}</td><td>{m(late_sale['exclusion'])}</td><td>{m(rent_sale['exclusion'])}</td>" + src_cell(["irs_p523"], "Exclusion rule"),
                       f"<td><strong>Tax</strong></td><td><strong>{m(now_sale['tax'])}</strong></td><td><strong>{m(late_sale['tax'])}</strong></td><td><strong>{m(rent_sale['tax'])}</strong></td>" + method_cell("#method", "Model output", sources=["irs_tc409", "ftb_cg", "rtc17043"]),
                       f"<td><strong>Net proceeds</strong></td><td><strong>{m(now_sale['net'])}</strong></td><td><strong>{m(late_sale['net'])}</strong></td><td><strong>{m(rent_sale['net'])}</strong></td>" + method_cell("#method", "Model output", sources=["irs_basis", "irs_tc409"]),
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
        + sale_charges_section()
        + '<h2>Transfer tax if Property B is sold</h2>'
        + table("City transfer tax on a sale of Property B",
                ["Price band", "Rate", "Note", "Source"],
                [f"<td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td>"
                 + src_cell([], "City fee schedule withheld for privacy")
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
        + '<h2>The 1% surcharge above $1,000,000, computed</h2>'
        + surcharge_block()
        + '<h2>What the model does and does not do</h2>'
        + callout("flag", "Not modelled, and flagged for a professional", """
<ul>
<li><strong>A like-kind exchange under section 1031.</strong> Exchanges of real property are still available, but they defer rather than forgive tax, and they do not fix the property tax reassessment. Whether one makes sense depends on whether the heir wants to stay in real estate at all.</li>
<li><strong>An instalment sale.</strong> Spreads the gain, but not the tax.</li>
<li><strong>Gifting during life rather than at death.</strong> Removes the basis step-up. Almost always worse for an appreciated asset.</li>
<li><strong>Whether the trust itself should hold the property after the transfer.</strong> This affects both the basis and the Proposition 19 claim and depends on the trust terms, which this site does not have.</li>
<li><strong>The federal deduction for state tax.</strong> Not taken. Taking it would slightly reduce the combined rate.</li>
</ul>"""))


# -------------------------------------------------------------- inheritance --
# --------------------------------------------------- section 17043 surcharge --
def surcharge_block() -> str:
    """The 1% surcharge, read from the statute and the FTB schedules, then computed.

    An earlier edition said this tax was "not modelled". That was wrong in a way
    worth recording: the 13.3% California rate already in the model is 12.3% top
    bracket plus this 1%, so it was modelled all along and the page misdescribed
    its own arithmetic. Worse, the arithmetic it described would have been the
    wrong way round: the surcharge is a flat 1% above $1,000,000 for every filing
    status, not a bracket that a joint return doubles.
    """
    ss = MODEL.get("surcharge_sensitivity") or {}
    if not ss.get("rows"):
        return ""
    rows = []
    for r in ss["rows"]:
        rows.append(
            f"<td>{esc(r['label'])}</td><td>{m(r['gain'])}</td>"
            f"<td>{m(r['tax_without_surcharge'])}</td><td>{m(r['tax_with_surcharge'])}</td>"
            f"<td>{m(r['difference'])}</td>"
            + method_cell("#method", "Model output", sources=["rtc17043", "ftb_540_instructions_2025"]))
    tbl = table("What the surcharge does to the tax on each path, 2045 inheritance",
                ["Path", "Taxable gain", "Tax at the rate without it",
                 "Tax at the rate with it", "Surcharge effect", "Basis"],
                rows,
                note="The two rates are the ones in the inputs file: "
                     f"{pcf(ss['rate_without'], 1)} without the surcharge and "
                     f"{pcf(ss['rate_with'], 1)} with it. Both are applied to the whole gain, "
                     "which is more conservative than a Form 540 computation, where the surcharge "
                     "reaches only the part of taxable income above the threshold.")
    return (
        callout("key", "The 1% is not a bracket, and it is already in every figure on this site", f"""
<p>Revenue and Taxation Code section 17043 imposes an additional <strong>1%</strong> on taxable income above
<strong>$1,000,000</strong>. Two features of the statute matter here, and both are easy to get backwards:</p>
<ul>
<li><strong>It ignores filing status.</strong> Subsection (c) switches off the credit rules (section 17039), the
filing-status and bracket-recomputation rules (section 17041) and the joint-return rules (section 17045). The
threshold is therefore <strong>$1,000,000 for a single filer and $1,000,000 for a joint return</strong>, not
$2,000,000.</li>
<li><strong>It is not indexed.</strong> The statute sets a flat dollar amount with no inflation adjustment, while
the brackets around it are indexed every year. Over a forty-year horizon the threshold reaches less and less
income in today's money.</li>
</ul>
<p>The published 2025 Form 540 rate schedules end at <strong>{pcf(0.123, 1)}</strong> on all three
filing-status schedules. Add the statute's 1% and the California layer is
<strong>{pcf(0.133, 1)}</strong> - which is exactly the state rate this model has been using, so the surcharge
was never missing from the numbers. What was missing was the statement that it is there, and the check that
its arithmetic was described the right way round. Both are corrected here.</p>""")
        + tbl
        + callout("note", "Does it change the recommendation?", f"""
<p>No, and the table says why. On the path this site recommends - sell at inheritance - the basis step-up
leaves a gain of about zero, so a tax on gain has nothing to tax and the surcharge's effect is
<strong>{m(next((r['difference'] for r in ss['rows'] if r['key'] == 'sell_equities'), 0))}</strong>. The
surcharge bites on the two paths that hold the property for thirty years and then sell into a large gain. It
makes those paths worse, so it pushes in the same direction as the recommendation rather than against it.
The model's own check: selling at inheritance still beats living in it after thirty years is
<strong>{'true' if ss.get('recommendation_unchanged') else 'false'}</strong>.</p>
<p><strong>A limit on this.</strong> This is a sensitivity on one assumption, computed the same conservative
way as the rest of the model: the rate is applied to the entire gain. A real Form 540 would apply the top
bracket and the surcharge only to the slices of income that fall in them, and would deduct the gain basis and
allowable expenses first. A CPA should compute the actual year-of-sale return; the direction of the result is
robust, the magnitude is an upper bound.</p>""")
        + table("The two rates, and where each comes from",
                ["Layer", "Rate", "Applies to", "Source"],
                [f"<td>Federal long-term capital gain, top</td><td>{pcf(0.20, 1)}</td>"
                 f"<td>Net capital gain above the top threshold</td>" + src_cell(["irs_tc409"], "Official source"),
                 f"<td>Net investment income tax</td><td>{pcf(0.038, 1)}</td>"
                 f"<td>Investment income above the statutory threshold</td>"
                 + src_cell(["irs_tc559"], "Official source"),
                 f"<td>California top marginal bracket, 2025 and 2026 schedules</td><td>{pcf(0.123, 1)}</td>"
                 f"<td>Taxable income above the top bracket start, indexed annually; the 2026 schedule shows the same structure</td>"
                 + src_cell(["ftb_rates", "ftb_rates_2026", "ftb_sched_ca_540"], "Official source"),
                 f"<td>California additional tax, section 17043</td><td>{pcf(0.01, 1)}</td>"
                 f"<td>Taxable income above $1,000,000, not indexed, every filing status; "
                 f"the 2025 Form 540 booklet reports it on line 62 as the Behavioral Health Services Tax</td>"
                 + src_cell(["rtc17043", "ftb_540_instructions_2025"], "Official source"),
                 f"<td><strong>Combined rate in the model</strong></td>"
                 f"<td><strong>{pcf(ss['rate_with'], 1)}</strong></td>"
                 f"<td>The whole gain, with no federal deduction for state tax taken</td>"
                 + method_cell("#method", "Model output", sources=["irs_tc409", "ftb_rates_2026", "rtc17043"])],
                note="The top California bracket is indexed every year, so its start rises; section 17043's "
                     "threshold does not. The model applies the combined rate to the entire gain, which "
                     "overstates the tax rather than understating it.")
        + surcharge_worksheet_section())



def surcharge_worksheet_section() -> str:
    """The 1% computed the way the Form 540 instructions compute it.

    Added after the owner asked for the official Form 540 instructions to be read and
    the sensitivity value updated. The table above prices the surcharge as a flat
    one-point difference on the entire gain. That is an upper bound. The form's own
    line 62 worksheet works on the slice of *taxable income* above $1,000,000, so the
    figure the household would actually enter depends on what else the return carries
    in the year of sale. Both are published side by side rather than replacing one
    with the other, because the ceiling is the honest worst case and the worksheet is
    the honest number.
    """
    ss = MODEL.get("surcharge_sensitivity") or {}
    ws = ss.get("worksheet") or []
    if not ws:
        return ""
    rows = []
    for block in ws:
        for r in block["rungs"]:
            rows.append(
                f"<td>{esc(block['label'])}</td><td>{m(block['gain'])}</td>"
                f"<td>{esc(r['label'])}</td><td>{m(r['taxable_income'])}</td>"
                f"<td>{m(r['above_threshold'])}</td><td>{m(r['surcharge'])}</td>"
                + method_cell("#method", "Model output", sources=["ftb_540_instructions_2025", "rtc17043"]))
    marginal = table(
        "The line 62 worksheet on the same three sales",
        ["Path", "Taxable gain", "Other taxable income in the year of sale",
         "Taxable income (line 19)", "Above $1,000,000 (line 2 to 3)",
         "1% under line 62 (line 5)", "Basis"],
        rows,
        note=("Four assumed levels of other income stand in for the rest of the return, because the "
              "surcharge is computed on total taxable income and not on the gain alone. They are "
              "scenarios, not figures from the household. The line 62 arithmetic is: taxable income, "
              "less $(1,000,000), times 1%. A gain under the threshold carries no surcharge at all, "
              "however large it is - which is the single most useful thing the worksheet shows."))

    caused = table(
        "How much of the 1% the gain actually causes",
        ["Path", "Worst case: 1% on the whole gain", "1% caused by the gain, no other income",
         "1% caused by the gain, $1,000,000 of other income", "Verdict"],
        [f"<td>{esc(b['label'])}</td><td>{m(b['flat_upper_bound'])}</td>"
         f"<td>{m(b['rungs'][0]['surcharge_on_gain'])}</td>"
         f"<td>{m(b['rungs'][2]['surcharge_on_gain'])}</td>"
         + f"<td>{'Nothing to tax' if b['gain'] == 0 else 'The ceiling holds'}</td>"
         + method_cell("#method", "Model output", sources=["rtc17043", "ftb_540_instructions_2025"]) for b in ws],
        note=("The middle and right columns count only the part of the surcharge that disappears if "
              "the house is not sold. Other income above the threshold attracts the 1% whether or not "
              "a sale happens, so charging that part to the sale would overstate what the decision "
              "costs. On a sale at inheritance the gain is about zero and so is the surcharge: there "
              "is nothing above the threshold for the gain to push there."))

    other_mid = ss['worksheet_scenarios'][2] if len(ss.get('worksheet_scenarios') or []) > 2 else 1000000
    return (
        '<h2>The same tax, computed the way Form 540 computes it</h2>'
        + callout("key", "What the Form 540 instructions actually say", f"""
<p>The instruction for <strong>line 62</strong> of Form 540 does not describe a rate applied to a gain.
It gives a five-step worksheet: taxable income from line 19, less $(1,000,000), multiplied by 1%.
The form's name for the tax is the <strong>Behavioral Health Services Tax</strong>; the statute behind it is
Revenue and Taxation Code section 17043, which is what the model has always used. Three things follow,
and they change the sensitivity rather than the recommendation:</p>
<ul>
<li><strong>It is a tax on total taxable income, not on the sale.</strong> A gain of
{m(ws[1]['gain'])} that lands on a return with no other income is taxed on
{m(ws[1]['rungs'][0]['above_threshold'])} of income above the line. The same gain on a return already
carrying {m(other_mid)} of taxable income is taxed on {m(ws[1]['rungs'][2]['above_threshold'])}.</li>
<li><strong>A gain below the threshold carries none of it.</strong> The first block of the table above
is the path this site recommends. The basis step-up leaves a gain of
{m(ws[0]['gain'])}, so there is nothing above the threshold for the 1% to reach, and the
surcharge is <strong>{m(ws[0]['flat_upper_bound'])}</strong> under the flat ceiling and
<strong>{m(ws[0]['rungs'][0]['surcharge_on_gain'])}</strong> on the worksheet. The only surcharge that
appears in that block is the {m(ws[0]['rungs'][-1]['surcharge'])} which the household's other income
would owe in any case, and which is therefore not a cost of selling.</li>
<li><strong>The flat figure in the earlier table is a ceiling, and it holds.</strong>
{m(ws[1]['flat_upper_bound'])} is the most the one point can ever cost on that gain. The worksheet
reaches it as soon as other taxable income has already filled the space below the threshold, and it
cannot exceed it, because the gain can only be taxed on that part of itself which lands above the
threshold. With no other income a slice of the gain itself sits below the line and escapes the point, so
the true cost is <strong>{m(ws[1]['rungs'][0]['surcharge_on_gain'])}</strong>, not
{m(ws[1]['flat_upper_bound'])}.</li>
</ul>""")
        + marginal
        + caused
        + callout("flag", "Two limits on this worksheet, stated rather than buried", f"""
<ul>
<li><strong>The bracket tax beside it is a flat approximation.</strong> The worksheet columns price the
1% exactly, but the state total in the model applies the top printed bracket of {pcf(12.3, 1)} to all
taxable income instead of walking the published schedule, which overstates the bracket tax. It does not
affect the 1%, which is correctly a flat rate on the slice above the threshold. A prepared return would
use the {pcf(12.3, 1)} bracket only on the top slice, as the schedules printed for each filing status
require.</li>
<li><strong>California does not conform to every federal change.</strong> The Schedule CA (540)
instructions state on their face that the Revenue and Taxation Code generally does not conform to the One
Big Beautiful Bill Act, and the line 7a instruction confirms California taxes long and short term capital
gains as regular income with no special rate. A year-of-sale return must be prepared on that year's forms;
the figures here are a planning calculation, not a return.</li>
</ul>"""))


def page_inheritance() -> str:
    steps = [
        ("1", "Before the transfer",
         "Confirm three things: that the trust holds title to the house, that the heir's relationship to the transferor is a parent-and-child relationship (or grandparent and grandchild with the middle generation deceased), and whether the heir takes outright, in further trust, or for life. The relationship is what qualifies the transfer for the intergenerational exclusion; without it the property is reassessed in full.",
         "The successor trustee, with the trust instrument and the recorded deed.",
         "No statutory deadline, but this is the step that determines everything else.",
         ["rtc63_2"]),
        ("2", "Check the assessment record now",
         "Confirm the assessed value, the tax rate area, the fixed charges on the bill and whether a homeowners' exemption is in place.",
         "The heir or the current owner, from the county assessor and the tax bill.",
         "Do this before the transfer, not after.",
         ["boe_pub29"]),
        ("3", "The transfer event",
         "On the transfer, the trustee signs and records a deed moving the house out of the trust to the heir. Recording is what starts the county's clock.",
         "The trustee records with the county recorder.",
         "Recording fees are due at recording. The documentary transfer tax does not apply to a deed where the property passes by reason of death or by inter vivos gift, so a transfer out of the trust at death should be exempt from it; the county recorder's fee schedule confirms the fee exemption for exempt transfers. Property A is in the county, not the city, so no city transfer tax applies to it either.",
         ["rtc11930_trust", "rtc11911"]),
        ("4", "Notice to beneficiaries",
         "When a revocable trust becomes irrevocable, the trustee must notify the heirs and beneficiaries and give them the information the statute requires.",
         "The trustee.",
         "The statute sets the notice requirement; read the current text.",
         ["prob16061_7"]),
        ("5", "Change in ownership statement",
         "A change in ownership statement goes to the county assessor. The assessor decides whether the transfer is a change in ownership and sets a new base year value if it is.",
         "The new owner, on the assessor's form.",
         "For a transfer on death, the statement is due within 150 days after the death under RTC section 480(b), or with the inventory and appraisal if the estate is probated. Other changes in ownership are due within 90 days under section 480(a).",
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
         ["boe_pub29"]),
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
        + callout("method", "If the estate does exceed the exclusion", f"""
<p>The threshold is only half the question. Federal estate tax is due <strong>in cash, nine months after the
date of death</strong>, and a six-month extension of time to file is not an extension of time to pay. A house is
not a liquid asset. The <a href="liquidity.html">estate liquidity page</a> prices what the tax is in anonymous
bands, what deferring one, three, five and ten years costs at the published underpayment rate, and what each
route to raising the cash costs - including borrowing against the property instead of selling it.</p>
<p class="callout-src">{slink('irs_filing_eg')} &middot; {slink('irs_i4768')} &middot; {slink('irs_interest')}</p>""")
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
<li><strong>How the tax would be paid if it is owed.</strong> That is a separate question from how much it is, and it is answered on the <a href="liquidity.html">estate liquidity page</a>.</li>
<li><strong>Whether prior taxable gifts have already used part of the exclusion.</strong> Lifetime taxable gifts are added back in the computation.</li>
<li><strong>Whether any of the estate is a retirement account.</strong> Those are taxed differently and are the most common surprise.</li>
<li><strong>What the law will be in 2040 to 2050.</strong> The exclusion has moved in both directions historically; it was $5,490,000 in 2017 and $15,000,000 in 2026. See the <a href="laws.html">law page</a>.</li>
</ul>"""))


# ---------------------------------------------------------------- liquidity --
def page_liquidity() -> str:
    clock = LIQ["clock"]
    bands = LIQ["excess_bands"]
    years_rows = LIQ["at_inheritance"]
    borrow = LIQ["borrowing"]
    joint = LIQ["joint_case"]

    head = callout("answer", "The nine-month clock", f"""
<p>Federal estate tax is <strong>{pcf(clock['estate_tax_rate'], 0)} of the amount above the exclusion</strong>, and it is
due <strong>{clock['due_months_after_death']} months after the date of death</strong>. A six-month extension of time to
<em>file</em> the return is available on request, but it is not an extension of time to <em>pay</em>: interest runs on
anything unpaid from the original due date, whether or not an extension was granted.</p>
<p>The interest rate is not a penalty rate and not a fixed one. It is the <strong>federal short-term rate plus three
percentage points</strong>, set every quarter, and it compounds daily. The rate published for the fourth quarter of
2026 is {pcf(clock['underpayment_rate'], 0)}, on a federal short-term rate of {pcf(clock['federal_short_term_rate'], 0)}.
The published range across 2022 to 2026 runs from {pcf(clock['underpayment_low'], 0)} to
{pcf(clock['underpayment_high'], 0)}.</p>
<p class="callout-src">{slink('irs_filing_eg')} &middot; {slink('irs_i4768')} &middot; {slink('irs_interest')}
&middot; {slink('uscode6621')} &middot; {slink('uscode6622')} &middot; {slink('uscode6601')}</p>""")

    tax_table = table(
        "The tax itself, in anonymous bands of the amount above the exclusion",
        ["Amount above the exclusion", "Federal estate tax at 40%", "Due", "Source"],
        [(f"<td>{m(b['excess'])}</td><td>{m(b['tax'])}</td>"
          f"<td>Within {b['due_months']} months of the date of death</td>"
          + src_cell(b["src"])) for b in bands],
        note=("The estate's own size is deliberately not published and not modelled as a figure. Read down the "
              "first column for the band that matches the estate and read across: the tax is 40% of it. "
              "California adds nothing - it has no estate tax and no inheritance tax."))

    defer_tables = []
    for years in TERMS_LIQ:
        rows = []
        for b in bands:
            t_ = next(x for x in b["terms"] if x["years"] == years)
            rows.append(
                f"<td>{m(b['excess'])}</td><td>{m(b['tax'])}</td>"
                f"<td>{m(t_['balloon_paid'])}<br><span class='sub'>interest {m(t_['balloon_interest'])}</span></td>"
                f"<td>{m(t_['instalment_paid'])}<br><span class='sub'>interest {m(t_['instalment_interest'])}</span></td>"
                f"<td>{m(t_['return_given_up'])}</td>"
                f"<td>{m(t_['deferral_advantage'])}</td>"
                + src_cell(["irs_i4768", "irs_interest", "uscode6622"]))
        defer_tables.append(table(
            f"What deferring {years} year{'s' if years > 1 else ''} costs, under section 6161(a)(2)",
            ["Amount above the exclusion", "Tax", "Paid in one sum at the end",
             "Paid in equal annual instalments", "Return the same cash would have earned",
             "Net advantage of deferring", "Source"],
            rows,
            note=("The last two columns are the trade. Deferring keeps the cash invested at the short Treasury "
                  "yield this site assumes; the deferral is worth it only where the return given up exceeds the "
                  "interest charged. Interest compounds daily at the published underpayment rate. "
                  "A section 6161(a)(2) extension is discretionary, is granted one year at a time for up to ten "
                  "years, and is granted only for the amount of the actual cash shortage.")))

    house_table = table(
        "What the house itself can create, at each inheritance year",
        ["Inherited", "Projected exclusion, one person", "Projected exclusion, a couple with portability",
         "House value at that date", "The house as a share of one exclusion",
         "Tax if the house were the whole amount above the exclusion", "Source"],
        [(f"<td>{r['inherit_year']}</td><td>{m(r['exclusion_projected'])}</td>"
          f"<td>{m(r['couple_exclusion_projected'])}</td><td>{m(r['house_value_at_death'])}</td>"
          f"<td>{pcf(r['house_share_of_exclusion'])}</td>"
          f"<td>{m(r['tax_if_house_is_the_excess'])}</td>"
          + src_cell(r["src"])) for r in years_rows],
        note=("The projected exclusions are mechanical indexation of the published 2026 amount at the modelled "
              "inflation rate. They are not law and not a forecast: the exclusion is set by statute and has moved "
              "in both directions. The last column is the largest tax the house can by itself create, if it were "
              "the only thing in the estate above the exclusion."))

    cash_table = table(
        "Where the cash can come from, and what each route costs",
        ["Route", "The rule", "What it costs", "Source"],
        [(f"<td>{esc(c['source'])}</td><td>{esc(c['rule'])}</td><td>{esc(c['cost'])}</td>"
          + src_cell(c["src"])) for c in LIQ["cash_sources"]],
        note=("Nothing here requires a sale. But a house is not a liquid asset, and the tax is due in cash on a "
              "fixed date, so the decision about which route to use has to be made before the date arrives rather "
              "than during the nine months."))

    borrow_table = table(
        f"Borrowing {m(borrow['principal'])} instead of selling, at the published mortgage average",
        ["Term", "Rate", "Interest, at the published average", "Low", "High", "Principal plus interest", "Source"],
        [(f"<td>{r['years']} year{'s' if r['years'] > 1 else ''}</td><td>{pcf(r['rate'], 2)}</td>"
          f"<td>{m(r['interest'])}</td><td>{m(r['interest_low'])}</td><td>{m(r['interest_high'])}</td>"
          f"<td>{m(r['total_paid'])}</td>" + src_cell(borrow["src"])) for r in borrow["rows"]],
        note=(f"{esc(borrow['method'])}. {esc(borrow['rate_basis'])}. {esc(borrow['limit'])}"))

    # The keep-and-borrow case, end to end (the "Add a mortgage case" register item,
    # implemented this edition). The carrying-cost table above prices interest only,
    # on a constant balance. This section runs both complete routes - keep the house
    # and borrow the band's tax against it, or sell it and pay the tax out of the
    # proceeds - on the same path engine the decision page uses, so the comparison is
    # between two complete futures rather than between a cost and a silence.
    kb = MODEL.get("mortgage_case") or {}
    kb_rows = kb.get("rows", [])
    smallest = kb_rows[0] if kb_rows else {}
    largest = kb_rows[-1] if kb_rows else {}
    kb_head = callout("method", "The keep-and-borrow case, run end to end", f"""
<p>The interest rows above price the carrying cost of borrowed money. This case answers the question that table
cannot: <strong>if the estate owes one of the published bands, is it cheaper to keep the house and borrow the
band's tax against it, or to sell the house and pay the tax out of the proceeds?</strong> Both routes are run
end to end on the same engine that prices every path on the <a href="decision.html">decision page</a>, over the
same thirty-year horizon, at the 2045 model.</p>
<p>The findings, in order:</p>
<ul>
<li><strong>Borrowing never becomes the better route at any published band.</strong> At the modelled return the
payment stream compounds to about {smallest['fv_payments'] / smallest['tax']:.1f} times the
principal in future value: even the smallest band's loan costs {m(smallest['fv_payments'])} of terminal value against a
{m(kb['gap_live_at_baseline'])} selling-versus-living gap. The mortgage decision is therefore about liquidity,
risk and the household's own circumstances - not about which route leaves more.</li>
<li><strong>The largest published band is the one the sale route cannot self-fund.</strong> The projected net
proceeds at the 2045 model are {m(kb['net_sale_proceeds'])}, and that band's tax is {m(largest['tax'])}, so the
shortfall would have to come from other assets or from a loan secured by both buildings - about
{pcf(largest['ltv_both'], 1)} of their combined projected value. That conversation has to happen before the
nine-month date arrives, not during it.</li>
<li><strong>The loan-to-value arithmetic is published, not assumed away.</strong> The two largest bands exceed
the projected value of Property A alone, so borrowing against that one property cannot raise them.</li>
</ul>
<p class="callout-src">{slink('fred_mortgage')} &middot; {slink('irs_estate')} &middot; {slink('irs_i706')}</p>""")

    kb_loan_table = table(
        f"The loan itself, band by band: a 30-year fixed loan at {pcf(kb['rate'], 2)}, amortising over the whole horizon",
        ["Tax to raise", "Monthly payment", "Total paid over 30 years", "Of which interest",
         "Loan against Property A's projected value", "Loan against both buildings' projected value",
         "What the payments would have earned instead", "Source"],
        [(f"<td>{m(r['tax'])}</td><td>{m(r['monthly_payment'])}</td>"
          f"<td>{m(r['total_paid'])}</td><td>{m(r['total_interest'])}</td>"
          f"<td>{pcf(r['ltv_a'], 1)}</td><td>{pcf(r['ltv_both'], 1)}</td>"
          f"<td>{m(r['fv_payments'])}<br><span class='sub'>at the band's low {m(r['fv_payments_low'])} and high {m(r['fv_payments_high'])}</span></td>"
          + src_cell(kb["src"], "Published rate and rules")) for r in kb_rows],
        note=(f"The loan is {esc(kb['method'])}. The rate is {esc(kb['rate_basis'])}. The last column is the "
              f"future value of the same payment stream at the model's after-tax equity return: what the money "
              f"would have been worth if it had never left the portfolio. The loan-to-value columns compare "
              f"each band's loan with the properties' projected values at the 2045 model "
              f"({m(kb['value_at_death_a'])} for Property A alone and {m(kb['value_at_death_both'])} for both "
              f"together); they are arithmetic, not a statement that any lender would lend. {esc(kb['limit'])}"))

    kb_route_rows = []
    for r in kb_rows:
        flag = "" if r["sale_covers_tax"] else "<br><span class='sub'>proceeds cannot cover the tax</span>"
        kb_route_rows.append(
            f"<td>{m(r['tax'])}</td>"
            f"<td>{m(r['route_keep_live'])}</td><td>{m(r['route_keep_rent'])}</td>"
            f"<td>{m(r['route_sell_pay'])}{flag}</td>"
            f"<td><strong>{esc(r['best_route'])}</strong></td>"
            + method_cell("#method", "Model output", sources=kb["src"]))
    kb_route_table = table(
        "The two complete routes, band by band: keep the house and borrow, or sell it and pay (2045 inheritance)",
        ["Tax to raise", "Keep it, live in it, borrow", "Keep it, let it out, borrow",
         "Sell it and pay from the proceeds", "Better route at this band", "Basis"],
        kb_route_rows,
        note=(f"The keep routes are the decision page's keeping paths less the future value of the loan "
              f"payments; the sale route is the sell-and-invest path with the band's tax paid out of the "
              f"proceeds at the end of the first year. {esc(kb['sale_route_timing'])}. The keep-and-let "
              f"column credits no rent, because no rent opinion exists, so it is a floor exactly as the "
              f"letting path is everywhere else on this site. {esc(kb['note'])}"))

    exclusions_table = table(
        "Two exclusions instead of one, on the estate side",
        ["Inherited", "One exclusion", "Two exclusions with portability", "Extra that passes free", "Source"],
        [(f"<td>{r['inherit_year']}</td><td>{m(r['one_exclusion'])}</td><td>{m(r['two_exclusions'])}</td>"
          f"<td>{m(r['difference'])}</td>" + src_cell(r["src"])) for r in LIQ["estate_exclusions"]],
        note=("Portability is not automatic. It requires a timely estate tax return making the election, and the "
              "amount carried over is the deceased spouse's unused exclusion. The projected figures are mechanical "
              "indexation at the modelled inflation rate, not law."))

    joint_table = table(
        "The two-person household case, on the income tax side",
        ["Path", "Gain at sale", "Exclusion, single", "Exclusion, joint",
         "Tax, single", "Tax, joint", "What the joint return saves",
         "Do both spouses have to live there?", "Source"],
        [(f"<td>{esc(r['label'])}</td><td>{m(r['gain'])}</td><td>{m(r['exclusion_single'])}</td>"
          f"<td>{m(r['exclusion_joint'])}</td><td>{m(r['tax_single'])}</td><td>{m(r['tax_joint'])}</td>"
          f"<td>{m(r['saving'])}</td>"
          f"<td>{'Yes - both must meet the use test' if r['both_spouses_must_occupy'] else 'No exclusion is available on this path'}</td>"
          + src_cell(joint["src"])) for r in joint["rows"]],
        note=("The model elsewhere runs on single-filer assumptions throughout, which is the conservative case. "
              + esc(joint["rule"]) + " " + esc(joint["limit"])))

    limits = callout("flag", "What this page cannot tell you", f"""
<ul>
<li><strong>Whether the estate owes anything at all.</strong> The estate's size is not published and not modelled.
Read the bands and apply the estate's own number privately.</li>
<li><strong>Whether prior taxable gifts have already used part of the exclusion.</strong> Lifetime taxable gifts are
added back in the computation, so the published exclusion is the most the estate can shelter, not necessarily what it
will shelter. <a href="estate.html">Question F on the questions page</a>.</li>
<li><strong>Whether the section 6166 installment election is available.</strong> It requires an interest in a
closely held business exceeding 35% of the adjusted gross estate. A home occupied as a personal residence is not
that on the face of the statute, so this site does not assume the election - but if any part of the estate is an
operating business, ask the attorney before assuming it is not.</li>
<li><strong>Whether a lender will lend against a property held in trust.</strong> That is a question for the lender
and the trustee, and the answer decides whether the borrowing rows above are available at all. The loan-to-value
columns in the keep-and-borrow tables are arithmetic, not underwriting: the two largest published bands exceed
Property A's projected value alone, so they would need both buildings as collateral or other assets besides.</li>
<li><strong>What borrowing costs when it is not forced by a tax bill.</strong> The rows above price borrowing to meet
the nine-month clock, band by band. Borrowing to take the cash out anyway, while keeping the home - the discretionary
case, where the money is invested rather than paid to a tax authority - is a different question with a different
answer, and it is run end to end on the <a href="keep-and-borrow.html">keep-and-borrow page</a>: loan-to-value
rungs, amortisation terms, an interest-only line and the hurdle return the borrowed money has to beat.</li>
<li><strong>What any of these rates will be in the 2040s.</strong> Every rate on this page is the published rate
today, or a published range. None of them is a forecast.</li>
<li><strong>Whether interest on borrowed money is deductible.</strong> This site assumes no deduction, which is the
conservative reading. The actual answer depends on what the borrowing is secured by and what it is used for.</li>
<li><strong>What is in the estate.</strong> The <a href="#inventory">blank inventory at the foot of this page</a> is
deliberately empty. Filling it in is the household's work, and it stays private.</li>
</ul>""")

    inventory = table(
        "A blank private estate inventory to complete off this site",
        ["Item", "Where it is held", "How it is titled", "Value at the date of death",
         "Income-tax basis", "How fast it can become cash", "Notes", "Source"],
        [(f"<td><strong>{esc(item)}</strong></td>" + BLANK_CELL * 6
          + src_cell([], "No official source applies")) for item in INVENTORY_ITEMS],
        note=("Print this and fill it in by hand, or keep it in a private file that is never committed to this "
              "repository. Nothing typed here should ever appear on a public page: the whole point of the "
              "inventory is that it exists somewhere the site cannot publish. Two rows do the most work - the "
              "row for prior taxable gifts, because gifts are added back in computing the exclusion, and the "
              "row for how fast each asset can become cash, because the tax is due on a fixed date and a house "
              "is not a liquid asset."))

    return (head + tax_table + "".join(defer_tables) + house_table + cash_table
            + borrow_table + kb_head + kb_loan_table + kb_route_table
            + exclusions_table + joint_table + limits
            + '<h2 id="inventory">The private estate inventory</h2>' + inventory)


# --------------------------------------------------------- keep and borrow --
def _borrow_pick(block, ltv_pct, rate_pct=None, interest_only=None):
    """Find one financing rung in a transfer-year block, by its stated rungs."""
    for r in block["rungs"]:
        if r["ltv_pct"] != ltv_pct:
            continue
        if interest_only is not None and bool(r["interest_only"]) != bool(interest_only):
            continue
        if rate_pct is not None and abs(r["rate_pct"] - rate_pct) > 1e-9:
            continue
        return r
    raise KeyError((ltv_pct, rate_pct, interest_only))


BORROW_SRC = ["fred_mortgage", "fred_prime", "irs_p936", "rtc62"]


def page_keep_and_borrow() -> str:
    years = BORROW["years"]
    y45 = next(y for y in years if y["inherit_year"] == 2045)
    mid = _borrow_pick(y45, 60, 7.11)
    cheap = _borrow_pick(y45, 60, 5.98)
    dear = _borrow_pick(y45, 60, 7.40)
    line = _borrow_pick(y45, 60, interest_only=True)
    meta = BORROW["meta"]
    rate_now = mid["rate_pct"]

    head = callout("answer", "What borrowing instead of selling is worth", f"""
<p><strong>The path exists, it is priced, and on this model it does not win.</strong> A cash-out refinance
at {mid['ltv_label']} of the home's value at a 2045 transfer releases <strong>{m(mid['loan'])}</strong> of
cash while the heir keeps living in the house, keeps the sheltered assessed value and pays no income tax on
the release. What it costs is the spread between the loan rate and what the borrowed money earns: at the
published mortgage average of {pc(rate_now)} and the model's after-tax portfolio return of
{pc(meta['after_tax_portfolio_return_pct'])} a year, the overlay is <strong>{m(mid['overlay_invested'])}</strong>
over {meta['horizon_years']} years - a loss, not a gain.</p>
<p><strong>What would change that answer is one number: the hurdle.</strong> Borrowing pays for itself only if
the borrowed money earns more than {pc(mid['hurdle_return_pct'])} a year after tax. At the lowest mortgage
average published in 2026 ({pc(cheap['rate_pct'])}) the same rung turns <em>positive</em> by
{m(cheap['overlay_invested'])}; at the highest ({pc(dear['rate_pct'])}) it loses {m(abs(dear['overlay_invested']))}.
So the question this page answers is not "should the heir borrow" but "can the household put the money to work
at better than the loan charges it". Almost certainly not, after tax, which is why every rung here sits behind
the selling path - between {m(min(abs(r['gap_vs_sell']) for r in y45['rungs']))} and
{m(max(abs(r['gap_vs_sell']) for r in y45['rungs']))} behind at a 2045 transfer.</p>
<p>The reason to read this page anyway is the reason nobody models: a household that needs cash and does not
want to sell into whatever market it inherits into. Borrowing releases {m(mid['cash_released_vs_sale'])} more
cash than a sale would on the same day, because a sale pays the {m(y45['sell_costs'])} selling cost and a loan
pays none of it - and the tax on the release is nil on both paths, because the basis was already stepped up to
the value at the date of death.</p>
<p><strong>Do not read this page as the other borrowing case, which is also published.</strong> The estate
liquidity page runs what happens when a band of tax has to be paid within nine months and the household borrows
against the kept house instead of selling to raise the money - a fully amortising 30-year loan at the published
average, set against selling and paying that same band out of the proceeds, and it is dearer at every published
band. That is forced borrowing, and its comparator is a sale under a deadline. This page is discretionary
borrowing: no bill is due, the household wants the cash and the house, and the money is invested. The two cases
share the loan arithmetic and reach the same conclusion, but they answer different questions and neither is the
other's evidence.</p>
<p class="callout-src">{slink('fred_mortgage')} &middot; {slink('irs_p936')} &middot; {slink('rtc62')}
&middot; {slink('irs_basis')}</p>""")

    method = callout("note", "How this page is computed, so it can be checked", f"""
<p>This is not a second model. The terminal value of the living path, its property-tax stream, the stepped-up
basis and the selling cost are all read straight out of <code>assets/data/model.json</code>, the same file the
dashboard, the decision page and the mixed-path page use. On top of that terminal this engine adds one overlay:</p>
<p style="font-family:var(--mono)"><code>overlay = loan &times; (1 + r)<sup>{meta['horizon_years']}</sup>
&minus; the future value at r of every annual payment &minus; the balance still owed at year
{meta['horizon_years']}</code></p>
<p>r is the after-tax portfolio return the whole site uses ({pc(meta['after_tax_portfolio_return_pct'])}:
the gross equity assumption less the tax drag). The payment is the amortising payment at the published mortgage
average, computed monthly from a rate compounded monthly and paid annually. A loan whose term equals the horizon
is repaid exactly, so its balance term is nil, and the hurdle it implies sits at its own rate - which is the
arithmetic check that the engine is right: at {pc(rate_now)} the hurdle is {pc(mid['hurdle_return_pct'])}, the
difference being the timing of annual payments against monthly compounding.</p>
<p>Nothing on this page is an offer. Loan-to-value rungs of 40, 60 and 80 percent are stated scenarios; the rates
are the averages the publishers themselves state, not a quote for this household. The loan in the model's own
forced-borrowing case, on the <a href="liquidity.html">estate liquidity page</a> and as lever 6 of the
<a href="what-if.html">what-if page</a>, is sized to a tax band rather than to a share of the value, which is why
the two sets of figures do not line up row for row; both are charged against the same living-path terminal from
<code>model.json</code>, and both treat the interest as non-deductible.</p>
<p class="callout-src">{slink('fred_mortgage')} &middot; {slink('fred_prime')}</p>""")

    cash_rows = []
    for r in y45["rungs"]:
        cash_rows.append(
            f"<td>{esc(r['ltv_label'])} of value</td><td>{pc(r['rate_pct'])}</td>"
            f"<td>{esc(r['rate_basis'])}</td>"
            f"<td>{m(r['loan'])}</td><td>{m(r['monthly_payment'])}</td><td>{m(r['annual_payment'])}</td>"
            f"<td>{r['payment_vs_tax_multiple']}&times; the first-year tax bill</td>"
            f"<td>{m(r['cash_released_vs_sale'])}</td>"
            + src_cell(BORROW_SRC, "Published rate series"))
    cash_table = table(
        "The cash and the bill: a 2045 transfer, thirty-year horizon",
        ["Loan-to-value", "Rate", "What that rate is", "Cash released", "Payment a month",
         "Payment a year", "Cash-flow burden", "Cash kept against selling now", "Source"],
        cash_rows,
        note=(f"The first-year property tax bill on the living path is {m(y45['bill_if_live_year1'])}, which is "
              "why the last-but-one column matters: a payment sized on market value is not sized on the sheltered "
              "assessment. The cash kept against selling is the loan amount less the selling cost and the tax a "
              "sale would pay at that date - on the model a sale at inheritance pays no income tax, so this "
              "column is the loan less the "
              f"{m(y45['sell_costs'])} selling cost."))

    worth_rows = []
    for r in y45["rungs"]:
        worth_rows.append(
            f"<td>{esc(r['ltv_label'])}</td><td>{pc(r['rate_pct'])}"
            f"{' (interest only)' if r['interest_only'] else ''}</td>"
            f"<td>{m(r['total_interest'])}</td><td>{m(r['balance_at_horizon'])}</td>"
            f"<td>{m(r['overlay_invested'])}</td><td>{m(r['overlay_parked'])}</td>"
            f"<td>&minus;{m(r['cost_if_spent'])}</td><td>{pc(r['hurdle_return_pct'])}</td>"
            + src_cell(BORROW_SRC, "Computed from the published rates"))
    worth_table = table(
        "What the borrowed money is worth at the horizon: a 2045 transfer, 2075",
        ["Loan-to-value", "Rate", "Interest paid over the term", "Still owed at the horizon",
         "Overlay if invested at the model's after-tax return",
         "Overlay if parked in short Treasuries at the site's parking yield",
         "Cost if the money is spent instead of invested", "Hurdle return that makes it level", "Source"],
        worth_rows,
        note=("Read the last two columns together with the two overlay columns. An overlay is what the loan is "
              "worth on top of the living path, positive or negative. Parked in the short Treasuries this site "
              "uses for the phased path, every rung loses money, because the parking yield is below the loan "
              "rate. Spent rather than invested, the loss is the cost of the money column, which is the honest "
              "figure for a household that borrows to consume. The hurdle is the after-tax portfolio return at "
              "which the overlay is exactly zero."))

    year_rows = []
    for y in years:
        r = _borrow_pick(y, 60, 7.11)
        year_rows.append(
            f"<td>{y['inherit_year']}</td><td>{m(y['value_at_death'])}</td>"
            f"<td>{m(r['loan'])}</td><td>{m(r['annual_payment'])}</td>"
            f"<td>{m(r['overlay_invested'])}</td>"
            f"<td>{m(r['terminal_borrow'])}</td><td>{m(y['terminal_live'])}</td>"
            f"<td>{m(y['terminal_sell'])}</td><td>{m(r['gap_vs_sell'])}</td>"
            + src_cell(BORROW_SRC, "Model output at the published rates"))
    year_table = table(
        "The same choice at the three transfer dates the model runs, at 60% of value and the published average rate",
        ["Transfer year", "Value at the date of death", "Cash released", "Payment a year",
         "Financing overlay over 30 years", "Keep-and-borrow terminal", "Keep, unlevered terminal",
         "Sell-and-invest terminal", "Keep-and-borrow against selling", "Source"],
        year_rows,
        note=("Every column is computed at the same horizon, from the same assumptions, at the same three "
              "transfer dates as the dashboard and the decision page, so the ranking can be read straight "
              "across. Borrowing does not change which path wins; it changes how much cash the keeping path "
              "can produce and how much it pays for the privilege."))

    term_rows = []
    for t in y45["term_rungs"]:
        term_rows.append(
            f"<td>{t['term_years']} years</td><td>{m(t['annual_payment'])}</td>"
            f"<td>{t['years_paid']} of the {meta['horizon_years']}</td>"
            f"<td>{m(t['total_interest'])}</td><td>{m(t['balance_at_horizon'])}</td>"
            f"<td>{m(t['overlay_invested'])}</td><td>{pc(t['hurdle_return_pct'])}</td>"
            f"<td>{('year ' + str(t['first_shortfall_year'])) if t['first_shortfall_year'] else 'never'}</td>"
            + src_cell(["fred_mortgage"], "Published rate series"))
    term_table = table(
        "Shorter term, heavier bill, less interest: 60% of value at the published average rate, 2045 transfer",
        ["Amortisation term", "Payment a year", "Years actually paid", "Interest paid",
         "Owed at the horizon", "Overlay if invested", "Hurdle return", "Self-funding runs out", "Source"],
        term_rows,
        note=("A fifteen-year amortisation costs {int15_} of interest against {int30_} on a thirty-year one, "
              "and needs {pay15_} a year instead of {pay30_}. The portfolio that is supposed to fund it is empty "
              "by year {short15_}, while the thirty-year schedule holds out until year {short30_}. So the "
              "shorter term is cheaper and less affordable at the same time. Both rows are the same engine: the "
              "payments stop when the loan is repaid and the portfolio then compounds untouched to the horizon."
              ).format(int15_=m(y45["term_rungs"][0]["total_interest"]),
                       int30_=m(y45["term_rungs"][-1]["total_interest"]),
                       pay15_=m(y45["term_rungs"][0]["annual_payment"]),
                       pay30_=m(y45["term_rungs"][-1]["annual_payment"]),
                       short15_=y45["term_rungs"][0]["first_shortfall_year"],
                       short30_=y45["term_rungs"][-1]["first_shortfall_year"]))

    stress_rows = []
    for y in years:
        for ltv in (40, 60, 80):
            r = _borrow_pick(y, ltv, 7.11)
            stress_rows.append(
                f"<td>{y['inherit_year']}</td><td>{esc(r['ltv_label'])}</td>"
                f"<td>{m(r['overlay_invested'])}</td><td>{m(r['overlay_shock'])}</td>"
                f"<td>{m(r['shock_vs_baseline'])}</td>"
                f"<td>{('year ' + str(r['first_shortfall_year_shock'])) if r['first_shortfall_year_shock'] else 'never'}</td>"
                f"<td>{('year ' + str(r['first_shortfall_year'])) if r['first_shortfall_year'] else 'never'}</td>"
                + src_cell(["fred_mortgage"], "Stated scenario, published rate"))
    stress_table = table(
        "The stated crash sequence applied to the borrowed money, then compared with itself",
        ["Transfer year", "Loan-to-value", "Overlay, no shock", "Overlay under the stated sequence",
         "What the sequence costs", "Self-funding runs out, shocked", "Self-funding runs out, baseline",
         "Source"],
        stress_rows,
        note=BORROW["stress_note"])

    rules_rows = []
    for key, label in (("no_income_tax_on_proceeds", "No income tax on the release of cash"),
                       ("no_reassessment", "Borrowing does not trigger a reassessment"),
                       ("interest_not_deductible", "The interest is not treated as deductible"),
                       ("estate_tax_unaffected", "Estate tax is untouched by this path"),
                       ("lender_limits", "What a lender may and may not do")):
        r = BORROW["rules"][key]
        rules_rows.append(f"<td><strong>{esc(label)}</strong></td><td>{esc(r['text'])}</td>"
                          + src_cell(r["src"], "Official source"))
    rules_table = table("The five rules this path rests on, each read at its publisher",
                        ["Rule", "What it says, and why it matters here", "Source"], rules_rows)

    b = BORROW["property_b_note"]
    bnote = callout("note", "The same arithmetic on the building the heir already owns", f"""
<p>Nothing about the overlay is specific to the inherited house. A {m(b['loan_at_60'])} cash-out at
{pc(7.11)} against a {m(b['value_2026'])} building costs {m(b['annual_payment'])} a year in payments, which is
{b['payment_vs_rent_multiple']}&times; the {m(b['rent_now'])} of annual rent the building currently collects. That
is the comparison worth making before any borrowing is discussed: the rent covers the payment almost exactly,
but the payment also repays principal while the rent does not, and a rental building's cash-out is a different
risk profile from a home the heir lives in. Property B's own leases, units and local rules are unresolved
questions, not inputs - see the <a href="property-b.html">Property B page</a>.</p>
<p class="callout-src">{slink('fred_mortgage')}</p>""")

    limits = callout("flag", "What this page cannot tell you", f"""
<ul>
<li><strong>Whether any lender will do this.</strong> The rungs are stated loan-to-value scenarios, not
quotations. {esc(BORROW['limitation']['not_an_offer'])} {esc(BORROW['limitation']['no_underwriting'])}</li>
<li><strong>Whether the proceeds are actually invested.</strong> {esc(BORROW['limitation']['cash_flow'])}</li>
<li><strong>What the interest costs after tax.</strong> Publication 936 allows a deduction only where the money
was used to buy, build or substantially improve the home securing the loan, and caps home acquisition debt at
$750,000 for mortgages taken out after 15 December 2017. Cash taken out to invest is outside that. Whether any
part of it is deductible as investment interest is a question for the preparer, and this page assumes none.</li>
<li><strong>Whether the property can be pledged at all while it sits in a trust.</strong> That is a question for
the trustee and the lender, and it is the same question the estate liquidity page raises for paying estate tax
by borrowing.</li>
<li><strong>Any of the future rates.</strong> Every rate on this page is a published average for 2026, read on
17 November 2026, not a forecast for the 2040s. The ranking of the paths does not turn on the rate: it turns on
the spread between the rate and the return, and on the fact that a kept house still carries its own bill.</li>
</ul>""")

    return (head + method + cash_table + worth_table + year_table + term_table + stress_table
            + rules_table + bnote + limits
            + table("What to do with this page",
                    ["Step", "Action", "Why", "Source"],
                    ["<td>1</td><td>Decide whether the household would borrow at all, and write the rule for it "
                     "before reading the tables below.</td>"
                     "<td>Rule <a href=\"precommit.html\">P-7</a> on the pre-commitment register now covers this "
                     "path, and its decision columns are deliberately blank: a rule written after the numbers are "
                     "read is not a rule. The rule it has to satisfy is the hurdle, not the payment.</td>"
                     + src_cell([], "Procedure, not a figure"),
                     "<td>2</td><td>If the answer might be yes, get one written lender indication, with the "
                     "closing costs in it.</td><td>Every figure here is a published average. One page from a "
                     "lender turns the whole table into a real comparison.</td>"
                     + src_cell([], "No official source applies"),
                     "<td>3</td><td>Ask the accountant what the interest would be, given what the money is used "
                     "for.</td><td>The deductibility of the interest is the only term on this page that could "
                     "move the overlay by a material amount, and it depends on the use of the proceeds.</td>"
                     + src_cell(["irs_p936"], "Official source"),
                     "<td>4</td><td>Rebuild the model after any of the inputs change.</td>"
                     "<td>This page reads the same model as every other; a changed input moves it with the rest "
                     "of the site and cannot drift.</td>"
                     + src_cell(["irs_basis"], "Method, and the rule the rebuild re-tests"),
                     ]))


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
         "Proposition 3 is approved on unofficial results (60.8% yes as of 16 November 2026, 7:12 p.m.). It makes permanent the voter-approved rates on individuals earning over $371,000, adjusted for inflation, that would otherwise expire in 2031.",
         "Removes a scheduled state tax cut. A large gain on a California property sale will be taxed at the top state rate for the foreseeable future.",
         ["sos_results", "voterguide_p3"]),
        ("One-time tax on certain taxpayers rejected",
         "Proposition 40 failed on unofficial results (52.2% no as of 16 November 2026, 7:12 p.m.).",
         "No state wealth tax. Recorded because a later version could return.",
         ["sos_results", "voterguide_p40"]),
        ("Countermeasure to Proposition 40 rejected",
         "Proposition 41 failed on unofficial results (55.2% no as of 16 November 2026, 7:12 p.m.). It would have prohibited new state taxes that exclude revenues from the state spending limit.",
         "Its failure removes one of the two measures that could have voided the one-time tax if both had passed.",
         ["sos_results", "voterguide_p40"]),
        ("New state personal property taxes barred",
         "Proposition 42 is ahead on unofficial results (51.2% yes as of 16 November 2026, 7:12 p.m.). The margin is close and counting continues, so the outcome is not final.",
         "Narrows one route for a future state tax, but does not touch real property tax.",
         ["sos_results"]),
        ("Local revenue vote threshold rejected",
         "Proposition 43 failed on unofficial results (57.7% no as of 16 November 2026, 7:12 p.m.).",
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
        ("A city parcel tax passed in November 2026 on the preliminary count (Property B's city)",
         "Voters passed, on the preliminary count not yet certified, a fifteen-year parcel tax funding public transit operations. First levy fiscal year 2027-2028 on the fall 2027 bill; expires 30 June 2042; dollar amounts adjust each 31 December from 2027 by the local all-items consumer price index. A multifamily parcel up to 5,000 sq ft pays $249 in the first year; above that $249 plus $0.195 a sq ft, capped at $50,000. Rent-controlled tenants can be charged up to 50% of the tax, capped at $65 a unit a year, where the base rent was set before 1 June 2027. Senior owner-occupants get $249 off per occupied unit, by application. Official terms read on 15 November 2026; local returns were still preliminary.",
         "Adds a fixed charge to Property B of about $4,460 in total across the fifteen years at the modelled inflation rate, less any tenant pass-through of up to $130 a year on the two let units if they qualify. No figure from it is added to any total on this site until the parcel's building area fixes the band. It matters to the household budget only through mid-2042: still live for the first two years after a 2040 inheritance, already expired for the 2045 and 2050 cases, and never touching Property A.",
         []),
        ("A regional sales tax passed at the same election on the preliminary count",
         "A fourteen-year half-cent sales tax in four of the five counties covered by the measure and a full cent in Property B's city, passed at the same election on the returns of 3 November 2026.",
         "Sales tax is consumption tax. It is not an input to any figure on this site, but it raises the cost of living in both jurisdictions and should be in the household budget.",
         []),
    ]
    pending = [
        ("A city measure capping banked and capital-improvement rent increases",
         "Would temporarily cap combined banked and capital improvement rent increases on rent-controlled units at 10% a year.",
         "Would further limit income growth on Property B if the units are covered.",
         "Not enacted. Not verified against an official source on the public site, because the official file names the jurisdiction.",
         []),
        ("City transfer tax reductions",
         "A package introduced in February 2026 proposed rolling back the 2020 transfer tax increases for large transactions.",
         "Would reduce the cost of selling Property B. Would not affect Property A.",
         "Reported but not verified against an official city source on the public site. It is left deliberately "
         "unresolved rather than given a number.",
         []),
        ("Five initiatives cleared for circulation (none amends Proposition 19)",
         "The Secretary of State's status page dated 20 October 2026 lists five initiatives cleared for circulation: ballot-procedure changes (one would add a 5% tax on income over $10 million to fund elections), a constitutional-revision route, a constitutional amendment creating a strategic implementation board, a repeal of the top-two primary law, and a food sales-tax exemption. None of them amends the inheritance or reassessment rules.",
         "Re-checked for a replacement to the failed Proposition 19 repeal. No replacement is pending, eligible or cleared on the page, so the shelter arithmetic is not expected to change from this list.",
         "Not enacted. Cleared for circulation only; none is circulating with 25% of signatures on the page. Read on 17 November 2026.",
         ["sos_cleared_circulation"]),
    ]
    dead = [
        ("AB 1157", "Would have amended Civil Code sections 1946.2, 1947.12 and 1947.13 on just cause and rent increases.",
         "Failed passage 13 January 2026 and died 31 January 2026. Recorded because it is often reported as law.",
         ["ab1157"]),
        ("The Proposition 19 repeal initiative (A.G. File No. 25-0017)",
         "Would have reinstated most of the pre-2021 rules from 1 January 2027, including for transfers "
         "since February 2021: a principal residence to a child regardless of value or continued "
         "occupation, and $1 million of other property. The Legislative Analyst estimated the revenue "
         "cost at around $1 billion a year at first, growing to around $2 billion.",
         "Failed to qualify for the November 2026 ballot. The Secretary of State's memorandum of "
         "18 May 2026 records that the signatures filed were fewer than the number of qualified voters "
         "required. This is the measure that would have removed the shelter arithmetic on this page; "
         "it is recorded as dead so it is not mistaken for law, and it can be filed again.",
         ["lao_250017", "lao_250017_status"]),
    ]
    return (
        callout("warn", "Read the election results carefully", """
<p>The November 2026 California results on this page are <strong>unofficial</strong>, published by the Secretary
of State with all 23,860 precincts partially reporting as of 16 November 2026, 7:12 p.m. Vote-by-mail,
provisional and other ballots continue to be processed and counted during the canvass, and the results are not
certified until 11 December 2026. They are
included because Proposition 3 directly changes the tax on a property sale. Confirm against the certified
results before relying on any of them.</p>
<p><strong>The measure that would have mattered most did not reach the ballot.</strong> The initiative to
repeal most of Proposition 19's inheritance changes failed to qualify, so the shelter arithmetic on this
site is current law rather than a law about to change. The failure memo and the Secretary of State's live
qualification dashboard are both linked below; the dashboard is the page to re-read every year at review
gate RG-3, because a replacement measure can be filed at any time.</p>""")
        + table("Enacted or changed", ["Change", "What it does", "Why it matters here", "Source"],
                [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td><td>{esc(c)}</td>"
                 + src_cell(d, "Official source" if d else "Official city documents withheld for privacy")
                 for a, b, c, d in enacted])
        + table("Proposed, not enacted", ["Measure", "What it would do", "Why it matters here", "Status", "Source"],
                [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td><td>{esc(c)}</td>"
                 f'<td><span class="badge unverified">{esc(d)}</span></td>'
                 + src_cell(e, "Official source" if e else "No official source retrieved")
                 for a, b, c, d, e in pending])
        + table("Dead bills recorded so they are not mistaken for law",
                ["Bill", "What it would have done", "Status", "Source"],
                [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td><td>{esc(c)}</td>"
                 + src_cell(d, "Official source") for a, b, c, d in dead])
        + callout("method", "How this page is kept current", """
<p>The owner asked for the official federal, state and local authorities to be rechecked periodically and
for enacted changes to be kept apart from proposals. The rule this page follows: an entry is
<strong>enacted</strong> only when a statute, a chaptered bill or a certified election result supports it,
<strong>proposed</strong> only while a live official filing supports it, and <strong>dead</strong> once the
publisher records that it failed. Nothing is moved between those groups on the strength of a news report.
The recheck happens at review gate RG-3 on the <a href="precommit.html">pre-commitment page</a>: once a
year, in the same month, re-open the links below and record whether anything moved.</p>""")
        + table("What would actually change the recommendation",
                ["Change", "Direction of the effect", "Source"],
                [
                    "<td>A repeal or sharp cut in the federal estate tax exclusion</td><td>Would make the cash inheritance taxable and could force a sale of the house for liquidity.</td>" + src_cell(["irs_estate"], "Current threshold"),
                    "<td>A California wealth tax or a one-time asset tax</td><td>Would tax holding assets rather than selling them, and could penalise keeping the house.</td>" + src_cell(["sos_results"], "2026 result"),
                    "<td>A change to Proposition 19 removing or widening the shelter</td><td>Would change the reassessment arithmetic at the transfer, which is the largest single number here.</td>" + src_cell(["rtc63_2", "boe_lta25009"], "Current rule"),
                    "<td>A split-roll change to Proposition 13</td><td>Would reset assessments on both properties and change every projection on this site.</td>" + src_cell(["boe_pub29"], "Current rule"),
                    "<td>Abolition of the basis step-up at death</td><td>Would remove the single strongest argument for selling at inheritance.</td>" + src_cell(["irs_basis"], "Current rule"),
                    "<td>A stricter local rent ordinance in the city</td><td>Would reduce the income from Property B and make Property A look slightly better by comparison.</td>" + src_cell([], "Official city page withheld for privacy"),
                ])
    )


# ---------------------------------------------------------------- black swan --
def page_black_swan() -> str:
    cpi = MODEL["meta"]
    stats = []
    for key, label, sid in (("cpi", "Consumer prices, 1976 to 2024", "fred_cpi"),
                            ("hpi_a", "House prices, California state record, 1976 to 2025", "fred_casthpi"),
                            ("gs10", "10-year Treasury yield, 1975 to 2025", "fred_gs10")):
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
                  + (src_cell([e], "Verified series") if e else src_cell([], "Official series withheld for privacy"))
                  for a, b, c, d, e in stats]

    reg_rows = []
    for rg in MODEL["regimes"]:
        run = rg["run"]
        reg_rows.append(
            f"<td><strong>{esc(rg['name'])}</strong><br><span class='muted'>{esc(rg['analogue'])}</span></td>"
            f"<td>{pc(rg['cpi'], 1)}</td><td>{pc(rg['house'], 1)}</td><td>{pc(rg['treasury'], 2)}</td>"
            f"<td>{m(run['terminal']['sell_equities'])}</td>"
            f"<td>{m(run['terminal']['sell_then_phase'])}</td>"
            f"<td>{m(run['terminal']['live_in'])}</td>"
            f"<td>{m(run['terminal']['rent_out'])}</td>"
            f"<td>{m(run['bill_if_rent_year1'])}</td>"
            f"<td><strong>{esc(PATH_LABELS[run['best']])}</strong></td>"
            + src_cell(rg["src"] if rg["src"] else [], "Official source" if rg["src"] else "None"))
    reg_table = table("Stress regimes applied to the 2045 inheritance, over a 30 year horizon",
                      ["Regime", "Inflation", "House prices", "Treasury yield",
                       "Sell, equities", "Sell, park then equities", "Live in it", "Let it out",
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
            + src_cell(["fred_casthpi", "fred_cpi", "fred_gs10"], "Verified series"))
    replay = table("Every full 30-year window in the verified record, applied to these two properties",
                   ["Window", "House growth a year", "Inflation a year", "Treasury compounding",
                    "Property A value at the end", "Same, in start-year money",
                    "Property B value at the end", "Down years", "Worst year",
                    "Total tax if reassessed", "Total tax if not", "Source"], rep_rows,
                   note="Each row takes the realised annual changes in the house price index, the consumer "
                        "price index and the 10-year Treasury yield for that real 30-year window and applies "
                        "them to these two properties. Both properties grow with the same California "
                         "state-level index: the metropolitan-area series were withdrawn from the published "
                         "edition because the index publisher's own metadata crosswalks the placeholders to "
                         "their metropolitan areas. No smoothing, no resampling, no invented numbers.")

    return (
        callout("why", "Why a smooth 4% line is the wrong tool", f"""
<p>Real economies do not grow at a constant rate. In the verified record used here, annual consumer price
inflation ranged from minus 0.3% to plus 13.5%, and annual house price growth in the California state record ranged from
minus 20.0% to plus 25.3%. A single constant rate hides the thing that actually decides this case, which is
whether the house and the stock market take their bad years at the same time.</p>
<p>The <a href="economy.html">economy page</a> shows the full record. The tables below apply it.</p>""")
        + table("The shape of the record", ["Series", "Range of annual changes", "Average", "Coverage", "Source"],
                stats_rows)
        + reg_table
        + replay
        + '<h2 id="real-replays">Entry timing in the real record: 1929, 2000, 2008 and 2020</h2>'
        + page_real_replays()
        + '<h2>Synthetic stress case, kept for comparison</h2>'
        + page_phased_stress()
        + callout("answer", "What the stress cases say", f"""
<p>Selling and investing wins in {RF['sell']} of the {RF['n']} regimes. Keeping the house wins only in: {esc(RF['keep_names'])}. Where house
prices grew at an exceptional pace, keeping the house can win; that is a bet on one local market outgrowing the
state-wide record, and the historical record says that sometimes it does and mostly it does not.</p>
<p>Two findings survive every regime. First, the property tax bill after reassessment is large and completely
insensitive to how the economy performs: assessed value rises at the 2% cap whether house prices boom or crash.
Second, letting the property out from the start is the lowest-valued path in {RF['lowest_let']} of the {RF['n']} regimes, because it
pays the full reassessment and the running costs, and then competes with a diversified portfolio on yield.</p>""")
    )


# ------------------------------------------ real historical entry replays --
EPI = MODEL["episodes"]


def epi_cell(v):
    """A real-today dollar amount with its drift from the lump-sum case."""
    return f"{m(v)}"


def page_real_replays() -> str:
    short = {"lump": "Invest on day one",
             "phase": "Park 30 months, then phase in",
             "park34": "Park 34 months, then invest"}

    def strat(key):
        return short.get(key, EPI["strategies"][key]["name"])

    ep_rows = []
    for e in EPI["episodes"]:
        s = e["strategies"]
        best = e["best"]
        def cell(key):
            amount = m(s[key]["real_today"])
            return f"<td class='best'>{amount}</td>" if key == best else f"<td>{amount}</td>"
        ep_rows.append(
            f"<td><strong>{esc(e['name'])}</strong><br><span class='muted'>{esc(e['entry'])} to {esc(e['exit'])}</span></td>"
            f"<td>{e['months']}</td>"
            + cell("lump") + cell("phase") + cell("park34")
            + f"<td><strong>{esc(strat(best))}</strong></td>"
            + f"<td>{m(s['phase']['vs_lump'])}</td>"
            + src_cell(e["src"], "Verified series"))
    ep_table = table(
        "The same inheritance replayed against the real price records",
        ["Episode", "Months held", "Invest on day one", "Park 30 months, then phase in over 12",
         "Park 34 months, then invest", "Best in this episode", "Phasing ahead of day one by", "Source"],
        ep_rows,
        note="All three columns start with the same capital: $1,000,000 of October 2026 purchasing power, converted "
             "back to the entry month with the published consumer price index. Every column is then restated in "
             "October 2026 purchasing power, so the columns can be compared with each other. The best column is in bold.")

    park_rows = []
    for r in EPI["park_sensitivity"]:
        park_rows.append(
            f"<td>{esc(r['name'])}</td><td>{r['park_months']} months</td>"
            f"<td>{m(r['phase_real_today'])}</td><td>{m(r['lump_real_today'])}</td>"
            f"<td>{m(r['gap'])}</td><td><strong>{esc(r['best_label'])}</strong></td>"
            + src_cell(r["src"], "Verified series"))
    park_table = table(
        "Both ends of the owner's 24-36 month window, and the midpoint",
        ["Episode", "Parking period", "Park, then phase in", "Invest on day one",
         "Phasing ahead of day one by", "Best", "Source"],
        park_rows,
        note="The phase-in is twelve equal monthly purchases in every row. The 30-month row is the same case as "
             "the table above; it is repeated here so each episode can be read across the window.")

    off_rows = []
    for r in EPI["offset_sensitivity"]:
        label = {0: "At the peak", 12: "Twelve months later", 24: "Twenty-four months later"}[r["offset_months"]]
        off_rows.append(
            f"<td>{esc(r['name'])}</td><td>{esc(label)}</td><td>{esc(r['entry'])}</td>"
            f"<td>{m(r['lump_real_today'])}</td><td>{m(r['phase_real_today'])}</td>"
            f"<td>{m(r['gap'])}</td><td><strong>{esc(r['best_label'])}</strong></td>"
            + src_cell(r["src"], "Verified series"))
    off_table = table(
        "What if the inheritance does not land exactly on the peak?",
        ["Episode", "Entry moved", "Entry month", "Invest on day one", "Park, then phase in",
         "Phasing ahead of day one by", "Best", "Source"],
        off_rows,
        note="This is the honest test of the idea. Nobody knows a peak is a peak until years later. Moving the "
             "entry forward by one and two years shows how much of the result depends on the crash starting almost "
             "immediately. Rows where the best is day-one investing are the rows that matter most.")

    inv_rows = []
    for r in EPI["inverse_sensitivity"]:
        label = {0: "Straight away", 12: "12 months later", 24: "24 months later",
                 36: "36 months later"}.get(r["crash_offset_months"], str(r["crash_offset_months"]))
        inv_rows.append(
            f"<td>{esc(r['name'])}</td><td>{esc(label)}</td><td>{r['horizon_months']}</td>"
            f"<td>{m(r['lump_real_today'])}</td><td>{m(r['phase_real_today'])}</td>"
            f"<td>{m(r['gap'])}</td>"
            f"<td><strong>{esc('Park 30 months, then phase in' if r['best']=='phase' else 'Invest on day one')}</strong></td>"
            + src_cell(r["src"], "Verified series"))
    inv_table = table(
        "The realistic unlucky case: inherit first, crash arrives later",
        ["Episode", "Crash begins", "Months compared", "Invest on day one",
         "Park 30 months, then phase in", "Phasing ahead of day one by", "Best", "Source"],
        inv_rows,
        note="Here the money is inherited at the episode's peak but the crash is aligned to start a fixed number "
             "of months afterwards, so the parking window no longer lands on the fall. The comparison never runs "
             "past the end of the episode's own price record, so later offsets have shorter horizons; the "
             "horizon is shown. A short horizon is part of the point: it is not long enough to smooth a crash out.")

    winners = EPI["winners"]
    phase_better = EPI["phase_better_than_lump"]
    worst = next(e for e in EPI["episodes"] if e["key"] == EPI["worst_phase_gap_key"])
    src_rows = []
    for key, s in EPI["series"].items():
        src_rows.append(
            f"<td><strong>{esc(s['title'])}</strong></td><td>{esc(s['publisher'])}</td>"
            f"<td>{esc(s['units'])}</td><td>{esc(s['coverage'])}</td>"
            + src_cell([s["src"]], "Verified series"))
    src_table = table(
        "Every series behind the replays, and what each one is",
        ["Series", "Who publishes it", "Units", "Coverage", "Source"], src_rows)

    return (
        callout("key", "Real crashes, real prices, no invented percentages", f"""
<p>The earlier version of this test used an invented crash: {pcf(-0.40, 0)} then {pcf(0.25, 0)} then {pcf(0.10, 0)}.
It is kept on this page as a stress case, but it was never evidence. This section replaces it with the real
thing: the published monthly price of an index through the actual 1929, 2000, 2008 and 2020 episodes, and the
published short-term cash rate for every month the money is waiting.</p>
<p>The question is the owner's question. If the sale proceeds arrive just before a crash, does parking them in
short-term Treasuries for 24-36 months and then phasing into equities beat investing everything on day one? On
the recorded crashes the answer is <strong>yes in {len(phase_better)} of {len(EPI['episodes'])} episodes for the
phased path</strong> and <strong>yes in {winners['phase'] + winners['park34']} of {len(EPI['episodes'])} for at
least one of the two waiting strategies</strong>. But it is not free and it is not automatic, and the tables below
show exactly where it stops working.</p>""")
        + ep_table
        + callout("answer", "What the real replays say", f"""
<ul>
<li><strong>The 1929 case is not close.</strong> The Dow Jones average was worth
{epi_cell(next(e for e in EPI['episodes'] if e['key']=='1929')['strategies']['lump']['real_today'])} in today's
money to a buyer who invested everything at the September 1929 peak, and
{epi_cell(next(e for e in EPI['episodes'] if e['key']=='1929')['strategies']['phase']['real_today'])} for the same
money parked for thirty months and then phased in. The parked money bought the index after the fall; the day-one
money bought it before.</li>
<li><strong>Waiting works when the crash comes early and the recovery is slow.</strong> That is 1929, 2000 and,
more mildly, 2008.</li>
<li><strong>Waiting loses when the crash is over before the parking period ends.</strong> In the 2020 episode the
market had recovered before a 24-month park was complete, and phasing in cost
{m(-worst['strategies']['phase']['vs_lump'])} of today's purchasing power against investing on day one.</li>
<li><strong>Parking longer is not better.</strong> The 34-month parked column beats the 30-month phased column in
three of the four episodes, because it buys at the bottom with the whole balance rather than dribbling in as
prices recover. That is a result of these four crashes, not a rule: it depends entirely on when the trough falls.</li>
</ul>""")
        + park_table
        + callout("flag", "The honest limit: nobody inherits at the peak", f"""
<p>The rows above assume the money arrives in the month before the crash. That is the best possible case for
parking, and it is not a forecast. The table below moves the entry forward by one and two years and re-runs the
same comparison. Once the entry lands after the fall, waiting has nothing to protect the money from, and it starts
to cost: in the 2008 episode an heir who inherited twelve months later, in October 2008, would have been
{m(-next(r for r in EPI['offset_sensitivity'] if r['key']=='2008' and r['offset_months']==12)['gap'])} better off
investing everything immediately.</p>
<p>So the phased path is best understood as <strong>insurance against one specific bad luck</strong> - inheriting
into the first year of a long bear market - paid for in the years when that luck does not happen. The price of that
insurance is visible in the 2020 rows and in the later-entry rows.</p>""")
        + off_table
        + inv_table
        + src_table
        + callout("method", "How these replays were computed, and what they leave out", f"""
<ol>
<li><strong>Verbatim data.</strong> Each series was downloaded from the publisher's own CSV endpoint on 15 November
2026 and stored unchanged in <code>assets/data/episodes/</code>. If a month the replay needs is missing, the module
stops with an error rather than interpolating. The provenance note beside the data lists every series.</li>
<li><strong>The three strategies.</strong> Day one: the whole amount buys the index at the entry month's close.
Phased: the amount earns the published short cash rate for {EPI['park_months']} months, then buys the index in
{EPI['phase_months']} equal monthly purchases. Parked: the same, but the whole balance buys in after
{EPI['late_park_months']} months. Nothing is sold at any point, so all three end holding the same index at the exit
month and differ only in how many units the money bought.</li>
<li><strong>Purchasing power, not nominal dollars.</strong> Each column is restated in October 2026 purchasing
power using the published consumer price index. Comparing nominal dollars across a 1929-1959 window would make the
1929 result look larger for no reason other than inflation.</li>
<li><strong>What is deliberately left out.</strong> Dividends are excluded from every column, which understates all
three results and understates day-one investing most, because it is in the market longest. No tax is charged on the
waiting interest. No fund fee, bid-offer spread, Treasury bill purchase friction or advisory fee is charged. The
indexes are not the portfolio an heir would actually hold. The 1929 equity series is a 30-stock price average that
changed composition, and the 2000, 2008 and 2020 series is the Nasdaq Composite, a technology-weighted index.</li>
<li><strong>Not a backtest of this decision.</strong> These episodes are history, not a forecast, and a future
inheritance will not arrive on a 1929 or a 2008 schedule. The point is to size the entry risk, not to predict it.</li>
</ol>
<p>Sources: {slink('fred_djia_1929')} &middot; {slink('fred_nasdaq')} &middot; {slink('fred_tb3ms')} &middot;
{slink('fred_callmoney')} &middot; {slink('fred_cpiaucns')} &middot; event context {slink('fedhist_1929')} &middot;
{slink('fedhist_greatrecession')}</p>"""))


# ------------------------------------------------ phased entry stress test --
def page_phased_rows() -> str:
    ps = MODEL["phased_stress"]
    rows = []
    for r in ps["rows"]:
        srcs = (["fedhist_1929", "fedhist_greatrecession"] if r["shock"]
                else ["ssa_trustees", "fred_gs10"])
        rows.append(f"<td><strong>{esc(r['label'])}</strong></td><td>{r['wait_months']} months</td>"
                    f"<td>{esc(ps['parking_yield'])}%</td><td>{m(r['terminal'])}</td>"
                    f"<td>{m(r['difference'])}</td><td>{esc(r['reading'])}</td>"
                    + method_cell("#phased-method", "Illustrative model", srcs))
    short = ASM["treasury_short_yield_nominal"]
    return table("2045 sale-proceeds entry-timing stress test (30-year nominal terminal value)",
                 ["Path", "Treasury wait", "Parking yield", "Terminal value",
                  "Difference vs immediate entry in same market case", "Reading", "Method and sources"], rows,
                 note=f"Rounded to $10. The parking yield is the model's one canonical 3-month-to-2-year Treasury "
                      f"parking scenario, {esc(ps['parking_yield'])}% (band {esc(ps['parking_yield_low'])}% to "
                      f"{esc(ps['parking_yield_high'])}%), not a current quote. The immediate comparator buys the "
                      f"whole proceeds in month 1, so its no-shock terminal equals the dashboard's sell-and-invest "
                      f"headline. One canonical monthly engine, a "
                      f"{esc(str(ps['park_months_baseline']))}-month park (owner band 24-36) and a "
                      f"{esc(str(ps['phase_months']))}-month phase-in, produces every phased figure on this site.")


def page_backtest() -> str:
    bt = MODEL["backtest"]
    rows = []
    for ep in bt["episodes"]:
        fed = {"1929": "fedhist_1929", "2008": "fedhist_greatrecession"}.get(str(ep["entry_year"]))
        for r in ep["rows"]:
            srcs = ["damodaran_histret"] + ([fed] if fed else [])
            rows.append(
                f"<td><strong>{ep['entry_year']}</strong> entry<br><span class='muted'>{r['horizon']} window, "
                f"{ep['entry_year']}&ndash;{ep['window_end']}</span></td>"
                f"<td>{esc(r['path'])}</td><td>{m(r['terminal'])}</td>"
                f"<td>{m(r['difference_vs_immediate'])}</td>"
                + src_cell(srcs, "Realized returns; academic source"))
    return table("Dated historical backtest: the returns that actually followed three crash entries",
                 ["Entry and window", "Path", "Terminal value", "Difference vs immediate entry", "Source"], rows,
                 note=f"Rounded to $10. Applies the realized annual S&amp;P 500 total return (dividends reinvested) "
                      f"and the realized 3-month Treasury bill return of every year after the entry year to the same "
                      f"hypothetical 2045 net sale proceeds; annual returns are spread evenly across the twelve "
                      f"months of their year. Gross of taxes, costs and fees; an academic series, not a government "
                      f"publication. The 2000 and 2008 windows end at {bt['record_end_year']} where the record ends. "
                      f"Entry at the start of the entry year approximates a peak entry but is not a day-level replay.")


def page_phased_stress() -> str:
    ps = MODEL["phased_stress"]
    bt = MODEL["backtest"]
    win = bt["phased_wins_at_10_years"]
    return callout("key", "What this test does and does not say", f"""
<p>It tests the requested choice: after a hypothetical 2045 inheritance and sale, keep proceeds in short-dated Treasuries for 24 or 36 months, then move equal monthly portions into equities over the following 12 months. It compares that path with investing immediately.</p>
<p>Two tests run side by side. The <strong>synthetic stress</strong> assumes a stylized crash at entry (a -40% equity year, then +25%, then +10%, then the baseline {esc(ps['equity_baseline'])}% net nominal equity return); it is a scenario, not history. The <strong>dated backtest</strong> applies the returns that actually followed the 1929, 2000 and 2008 entries. In {win} of 3 dated crash entries the phased path ended its first decade ahead of immediate entry; in the synthetic no-shock case, phasing costs between {m(ps['rows'][2]['difference'])} and {m(ps['rows'][4]['difference'])} of terminal value. Phasing is insurance whose premium is the no-crash opportunity cost, not a free lunch.</p>
<p>The parking yield is the model's one canonical 3-month-to-2-year Treasury parking scenario ({esc(ps['parking_yield'])}%, band {esc(ps['parking_yield_low'])}%-{esc(ps['parking_yield_high'])}%), stated, not a forecast. This backtest uses annual total returns so it can reach the 1929 entry and count dividends; the monthly replay further down this page re-runs the 2000, 2008 and 2020 entry months with official FRED monthly data (a price index without dividends), so the two tables test the same idea at two granularities and two data sources. The actual bill/note yield, reinvestment rates, taxes on interest, transaction costs and the chosen equity allocation must be refreshed with a fiduciary before implementation.</p>""") + page_phased_rows() + page_backtest() + f"""
<section id="phased-method">
<h2>Interpretation and reinvestment risk</h2>
<ul>
<li>Waiting reduces the dollars exposed to an immediate crash, but it does not eliminate market risk: equity purchases still face subsequent losses.</li>
<li>With no crash, waiting has an opportunity cost if equities outperform the parking yield. The no-shock rows make that cost visible rather than showing only the favorable case.</li>
<li>Short Treasuries mature frequently. If market yields are lower at maturity, proceeds must be reinvested at lower rates; if rates rise, existing notes' market value can fall before maturity. Neither future yield nor ladder is known today.</li>
<li>Every phased figure on this site comes from one canonical monthly engine and one parking-yield assumption - the same engine behind the dashboard's phased headline path.</li>
<li>All terminal values omit estate-level investment tax details, a personalized asset allocation, withdrawals, fees beyond the model's stated drag, and changes in future law. Ask the CPA and investment fiduciary to rerun with an actual sale estimate and current Treasury quotes.</li>
</ul>
<p>Official event context: {slink('fedhist_1929')} &middot; {slink('fedhist_greatrecession')}. Parking-yield band basis: {slink('ssa_trustees')} &middot; {slink('fred_gs10')}. Backtest return series: {slink('damodaran_histret')}.</p>
</section>"""


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
            f"<td>{r['gs10'] if r['gs10'] is not None else '&mdash;'}</td>"
            + src_cell(["fred_cpi", "fred_casthpi", "fred_gs10"], "FRED series"))
    tbl = table("The verified annual record, 1975 to 2025",
                ["Year", "Consumer price index", "Change",
                 "House price index, California (state-level)", "Change",
                 "10-year Treasury yield, %", "Source"], rows,
                note="Every value was downloaded as a CSV file from the official FRED domain and read directly "
                     "from that file; the state-level house price series was re-read there on 15 November 2026. No "
                     "value was typed from memory. Both property placeholders now grow with this one state-level "
                     "series: the two metropolitan-area series were withdrawn from the published edition because "
                     "the index publisher's own metadata crosswalks the placeholders to their metropolitan areas. "
                     "The consumer price series ends at 2024 because the 2025 annual value was blank in the file "
                     "retrieved.")
    return (
        callout("note", "Why this page exists", """
<p>The <a href="black-swan.html">black swan page</a> uses this record rather than invented scenarios. Every
number below comes from one of three series hosted by the Federal Reserve Bank of St. Louis on behalf of the
Bureau of Labor Statistics, the Federal Housing Finance Agency and the Board of Governors; the market-return
series used on the black-swan page comes from the academic ledger and is cited there. Where a series stops
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
                 + src_cell(["fred_cpi"], "Bootstrap source series; house-price series withheld for privacy")
                 for r in ECON["bootstrap"]["rows"]],
                note="The record's median is well above the model's 4% because the fifty years to 2026 "
                     "include the 1970s and 1980s. The model's constant sits near the record's 5th "
                     "percentile, not at its middle: it is a deliberately conservative anchor, and the "
                     "decision page's conclusions do not depend on the median being this high.")
        + table("How often each outcome happens across the draws",
                ["Share of the two thousand draws", "Share", "Source"],
                [f"<td>{esc(s['key'])}</td><td><strong>{s['value'] * 100:.1f}%</strong></td>"
                 + src_cell(["fred_cpi"], "Bootstrap source series; house-price series withheld for privacy")
                 for s in ECON["bootstrap"]["shares"]]
                + [f"<td>{esc(ECON['bootstrap']['wins']['case'])}</td>"
                   f"<td><strong>{ECON['bootstrap']['wins']['sell_wins_share'] * 100:.1f}%</strong></td>"
                   + src_cell(["fred_cpi"], "Bootstrap source series; house-price series withheld for privacy")],
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
                    ("Best year for house prices in the California state record", "plus 25.3%, in 1977", ["fred_casthpi"]),
                    ("Worst year for house prices in the California state record", "minus 20.0%, in 2008", ["fred_casthpi"]),
                    ("California, 2006 to 2011", "a 39.8% fall from the 2006 annual level to the 2011 annual level", ["fred_casthpi"]),
                    ("California, 1989 to 1996", "a fall from 211.04 to 201.60 over seven years", ["fred_casthpi"]),
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
      ("Is either building encumbered at the transfer, and on what terms?",
       "Nothing. The material this site was built from does not say whether a mortgage, deed of trust, tax "
       "lien or assessment lien is registered against either property, so both are modelled free and clear "
       "and the decision page says so.",
       "The payoff balance at the date of transfer, the monthly payment, the interest portion of it, and "
       "whether any special assessment or unpaid tax is attached to the parcel.",
       "Ask the lender for a payoff statement dated near the transfer, and read the recorded deed of trust; "
       "the county recorder's index shows every lien of record. For the assessment lien, read the bond "
       "or district's own schedule.",
       "It is the one gap that changes the cash flow of every keeping path. A sale pays the balance out of "
       "the proceeds, so the sum invested simply falls; a holder pays the balance over time with interest "
       "on top, and that interest is a cost the sale path never incurs. The decision page prices each $1,000 "
       "a month of payment at about $1,311,830 of terminal value on the living path and nothing on the sale "
       "path. Federal law also settles the question nobody asks first: a lender cannot accelerate a loan on "
       "a building of fewer than five units merely because the property passes to a relative at the "
       "borrower's death.",
       ["uscode1701j3", "irs_basis"]),
      ("Is the house actually titled in the trust today?",
       "The owner states the inheritance will come through a trust around 2040 to 2050.",
       "No deed, no parcel number, no trust document.",
       "Read the recorded grant deed and the preliminary change of ownership report at the county recorder.",
       "If the house is not in the trust, the transfer path, the reassessment and possibly probate all change.",
       []),
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
       []),
      ("What are the fixed charges on the Property A bill?",
       "Derived from the owner's bills at about $840 in 2025 at the assumed rate.",
       "The itemised parcel taxes, bonds and assessments.",
       "Read the itemised bill.",
       "Fixed charges have grown unevenly; on Property B they grew at 8.1% a year between 2016 and 2025.",
       []),
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
       []),
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
      ("Are the Property B units covered by the city's Rent Ordinance?",
       "Not verified.",
       "The certificate of occupancy date and the exemption status of the building.",
       "Check with the Rent Board and the building's records.",
       "Coverage decides whether the 1.6% local increase or the statewide cap applies.",
       ["civ1947_12"]),
      ("Is the rent increase licence current, and is the building registered in the Housing Inventory?",
       "Not supplied.",
       "Whether the licence and registration are in place.",
       "Ask the Rent Board.",
       "Without them, annual increases cannot lawfully be imposed at all.",
       []),
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
       f"An owner estimate of {m(A['annual_costs']['insurance']['mid'])} a year at each building, now carried "
       f"as a band rather than a point: {m(A['annual_costs']['insurance']['low'])} to "
       f"{m(A['annual_costs']['insurance']['high'])} for Property A and {m(B['annual_costs']['insurance']['low'])} "
       f"to {m(B['annual_costs']['insurance']['high'])} for Property B. The two floors are published figures - the "
       f"statewide average written premium for the matching policy form in the Department's own table - and the "
       f"two ceilings are stated scenarios.",
       "Real quotes, which are the only thing that turns either band into a number.",
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
       []),
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
    ("H", "Borrowing instead of selling",
     [
      ("If the household would not sell, would it borrow - and at what spread over the loan rate?",
       "The keep-and-borrow page now prices the path on published rates: a 60% cash-out at a 2045 transfer "
       "releases the cash and costs about the difference between the loan rate and what the money earns.",
       "A written lender indication: amount advanced, rate, term, whether payments are interest-only, and the "
       "closing costs. And the household's own rule: what the borrowed money would be used for, and where the "
       "repayment comes from.",
       "Ask one lender for a written indication and ask the trustee whether the trust permits a lien at all. "
       "Then write the spread rule into the investment policy before the money is offered.",
       "It is the only path that gives the household cash without a sale, without an income-tax event and "
       "without a reassessment - and the only one whose cost is a rate the household does not control. On the "
       "model's numbers the borrowed money must earn more than the loan charges after tax; at the published "
       "mortgage average it does not, and at 2026's lowest published weekly average it does. That is the whole "
       "decision in one comparison.",
       ["fred_mortgage", "irs_p936", "rtc62"]),
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
    ("S-01", "Replace both insurance bands with three real quotes each",
     "Insurance was the last owner-supplied cost carried as a single round number, and it is now a band: "
     "published statewide averages for the matching policy form at the floor, the owner's figure in the middle, "
     "a stated scenario at the ceiling. Quotes are still needed, because they are what turns a band into a "
     "number - and because a three-unit rental policy and a primary-residence policy are priced on different "
     "forms and cannot share a figure. The whole band moves the living path by under 1% of the gap to selling, "
     "so this closes a gap in the record rather than changing the recommendation.",
     "Low", "Low", "costs", "cdi_tips"),
    ("S-02", "Look up Property A's tax rate area and read the published rate",
     "Replaces the assumed 1.18% with the rate the county actually applies, and itemises the fixed charges.",
     "Low", "None", "property-a", []),
    ("S-03", "Confirm the trust holds title and obtain the preliminary change of ownership report",
     "Establishes that the transfer will take the intended path and starts the county record correctly.",
     "Low", "Low if done now, high if discovered late", "inheritance", ["rtc480"]),
    ("S-04", "Model a sale in the same tax year as the inheritance, before deciding anything else",
     "The basis step-up makes an immediate sale almost tax-free. This is the option everything else must beat.",
     "Low", "Low", "decision", ["irs_basis"]),
    ("S-05", "Claim the Proposition 19 exclusion only if the heir will occupy the home long term",
     "The exclusion is removed when the home stops being the principal residence, and there is no exception to the one-year occupation rule.",
     "Medium", "High if the heir may move out", "property-a", ["rtc63_2", "boe_lta26026"]),
    ("S-06", "Get rental opinions for Property A and for the vacant unit at Property B",
     "Turns the break-even rent into a real comparison and prices the opportunity cost of occupying Property A.",
     "Low", "None", "decision", []),
    ("S-07", "Confirm Rent Ordinance coverage and the rent increase licence",
     "Decides which rent cap applies and whether increases can lawfully be made at all.",
     "Low", "Medium if notices were missed", "property-b", ["civ1947_12"]),
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
     "Each item in the first table needs a decision to adopt, defer or reject, recorded before any action. Both tables carry a Decision column and a Date column for exactly this; they are empty until the household fills them in.",
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
    ("S-23", "Sign the pre-commitment register before reading any projection",
     "The rules that decide each path, and the household's own priorities, are written down on the pre-commitment page. Filling in the two decision columns before reading the numbers is what stops a single projection from choosing the answer.",
     "Low", "High: without it the model can justify any path", "precommit", [])
    ,
    ("S-24", "Have a California property tax lawyer confirm the clawback reading in writing",
     "Section 63.2(a)(1)(C) enrols the change-of-ownership base year value when the heir stops qualifying, and this site now prices a six-figure cost for that. The live-then-let path moves by more than any other single input here, and the statute has not been applied by a court on these facts as far as this repository knows.",
     "Medium", "Medium: it moves the live-then-let path, not the headline", "decision", ["rtc63_2_eligibility", "boe_lta26026"])
    ,
    ("S-25", "Obtain one written rent opinion and enter it, replacing the scenario range",
     "The imputed-rent table prices the housing the household gets from living there across a range of hypothetical rents. One documented rent opinion replaces the range with a figure and closes the last open input in the model.",
     "Low", "Medium: the living path is the only one whose value is not measured", "precommit", ["hud_fmr"])
    ,
    ("S-26", "Re-read the Secretary of State's initiative dashboard every year at gate RG-3",
     "The Proposition 19 repeal initiative failed to qualify in May 2026, which is why the shelter arithmetic is current law. A replacement can be filed at any time, and the dashboard is the official page that records whether it has.",
     "Low", "Medium: a repeal would remove the shelter and change the arithmetic", "laws", ["sos_initiative_status"])
    ,
    ("S-27", "Decide whether a city transfer tax applies before relying on the 5.5% sale cost",
     "Only the county documentary transfer tax is modelled. Section 11911(b) lets a city add half the county rate again, and whether it applies to this property cannot be published without naming the city. The difference is small in dollars but it is an unverified part of the sale cost.",
     "Low", "Low", "taxes", ["rtc11911"])
    ,
    ("S-28", "Disclose whether either building is encumbered, and on what payment",
     "The comparison is meant to carry debt alongside taxes, occupancy, capital costs and liquidity; nothing in "
     "the record says whether anything is registered against either parcel, so both are modelled free and clear. "
     "The decision page now prices each stated payment level, so one payoff statement is enough to place the "
     "household on the right row of that table. It changes the size of every keeping path's bill and never its "
     "ranking, which is exactly why the assumption needed to be visible rather than silent.",
     "Low", "Medium: it is the only modelled input the household can answer from a single letter", "decision", ["uscode1701j3"])
    ,
    ("S-29", "Take one written lender indication before treating any borrowing figure as real",
     "The keep-and-borrow page now prices the path against published mortgage averages and a stated "
     "loan-to-value ladder, which is the most a model can do without a quote. One written indication - amount, "
     "rate, term, whether the payments are interest-only, and the closing costs - converts the whole table from "
     "a scenario into a comparison, and answers the two questions this site cannot: whether a lender will advance "
     "against a property held in a trust, and what it charges for doing so.",
     "Low", "Medium: the path cannot be adopted without it", "keep-and-borrow", ["fred_mortgage", "irs_p936"])
    ,
    ("S-30", "Write the borrowing rule into the investment policy, before any loan is taken",
     "A cash-out refinance is the one path in this analysis that converts a timing problem into a cash-flow "
     "problem: the payment is due whether or not the market cooperates, and the model shows the invested "
     "proceeds running dry inside the horizon on the heavier rungs. The policy should therefore say what the "
     "borrowed money may be used for, what repayment source is committed, and at what spread over the loan rate "
     "the household would refuse to borrow at all.",
     "Low", "High if the loan is taken before the rule is written", "keep-and-borrow", ["fred_prime"])
    ,
    ("S-22", "Decide whether the public repository and its history should stay public",
     "The repository is public and earlier commits contain unrounded owner figures. Rounding the published page does not change what Git history holds. Making the repository private, or rewriting history, are the only two ways to close that exposure.",
     "Medium", "High for privacy, none for the analysis", "review", []),
]


def page_suggestions() -> str:
    # The owner's instruction: "create a section dedicated for suggestions so someone can review
    # suggestions and choose the best path before implementing any changes", and "write the decision
    # and the date next to the item, so a future reader knows what was chosen and why". Both tables
    # therefore carry a Decision column and a Date column, left empty for the household to complete
    # by hand. Nothing on this page can be decided by the model.
    blank_dec = '<span class="blank">not yet decided</span>'
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
            f"<td>{blank_dec}</td><td>{blank_dec}</td>"
            + (src_cell(src if isinstance(src, list) else [src], "Official source") if src
               else src_cell([], "No official source applies")))
    tbl = table("Suggestions for review",
                ["ID", "Suggestion", "What it changes", "Effort", "Risk if ignored",
                 "Where it lands", "Status", "Decision (adopt / defer / reject)",
                 "Date decided", "Source"], rows,
                note="The two decision columns are deliberately empty. Building this site cannot obtain a "
                     "quote, read a roll, sign a document or move title, so no item on this list has been "
                     "acted on. Write the decision and the date beside each item - adopt, defer or reject, "
                     "and why - so a future reader can see what was chosen and on what basis.")

    gate = table("The selection gate",
                 ["Step", "What happens", "Rule", "Source"],
                 [
                     "<td>1. Read</td><td>Work through the list and mark each item adopt, defer or reject.</td><td>Every item in the first table is an action only the household and its advisers can take, and none has been taken. The second table below is different: it records which improvements to the site itself have already been built in this edition.</td>" + src_cell([], "Procedure, not a figure"),
                     "<td>2. Gate</td><td>Anything that costs money, signs a document, or moves title needs an explicit decision recorded before it happens.</td><td>Items S-03, S-05, S-11 and S-13 are in this class.</td>" + src_cell([], "Procedure, not a figure"),
                     "<td>3. Verify</td><td>Anything that replaces an unverified figure should be checked against the official source in the last column, and the data file updated.</td><td>Items S-01, S-02, S-07 and S-08 are in this class.</td>" + src_cell([], "Procedure, not a figure"),
                     "<td>4. Re-run</td><td>After any input changes, rebuild the model and the site and see whether the recommendation moved.</td><td>Item S-16.</td>" + src_cell([], "Procedure, not a figure"),
                     "<td>5. Record</td><td>Write the decision and the date next to the item, so a future reader knows what was chosen and why.</td><td>Item S-17. The Decision and Date columns on both tables are where that is written.</td>" + src_cell([], "Procedure, not a figure"),
                 ])

    # Status per proposal. The owner asked for a section where suggestions can be
    # reviewed and chosen before anything is implemented; this map is the record of
    # what the 16 November 2026 build actually did, so a reader can see which items
    # are still open rather than assuming the whole list is untouched.
    improve_status = {
        "Model a sale in the same tax year as the inheritance": ("done", "Implemented: the model's pure sell path is a sale in the same tax year as the inheritance itself, and the taxes page prices it - about zero income tax on the 2045 model, because the basis steps up to the date-of-death value and property acquired from a decedent is treated as held long-term whatever the actual holding period. Register item S-04's analysis therefore exists; the S-row stays proposed for the owner to adopt."),
        "Add a distribution chart to the projections": ("done", "Implemented: decile fan charts on the dashboard and the projections page, a histogram of the sell-minus-keep gap on the dashboard and the decision page, and the same distributions behind every headline share."),
        "Add a real rental opinion for Property A": ("open", "Still open. The site now publishes the rent at which occupying and letting each match selling, which is the closest substitute available without a rent opinion."),
        "Add a real rental opinion for Property A (imputed rent)": ("done", "Implemented as a range of rent scenarios plus a solved break-even, because no rent opinion exists yet."),
        "Add the itemised tax bills": ("open", "Still open: needs the parcel's own bill, which is not on the site."),
        "Add a liquidity model for the estate": ("done", "Implemented on the estate liquidity page: the nine-month payment clock, the tax in anonymous bands, what deferring one, three, five and ten years costs at the published underpayment rate compounded daily, and the five routes to raise the cash."),
        "Add a two-person household case": ("done", "Implemented on the estate liquidity page: two exclusions with portability at each inheritance year, and the joint section 121 exclusion repriced against every mixed path. The pure-path model still runs on single-filer assumptions, which is the conservative case."),
        "Add a mortgage case": ("done", "Implemented twice over, on two different questions, and both are published. Borrowing to pay a band of estate tax while keeping Property A runs end to end inside the model (scripts/model.py, keep_and_borrow_cases) and is published on the estate liquidity page and as lever 6 of the what-if page: a fully amortising 30-year fixed loan at the published rate against the keeping paths, compared with selling and paying the same band out of the proceeds - dearer at every published band, and the largest band is beyond what one property's sale can self-fund. Borrowing to take the cash out with no bill forcing it is a separate engine and page (scripts/borrow.py, keep-and-borrow.html): 40, 60 and 80 percent loan-to-value at the published 2026 mortgage averages, an interest-only line at the published prime rate, 15/20/30-year amortisation rungs, the stated crash sequence applied to the borrowed money, and the hurdle return each rung must beat. What remains open is evidence, not modelling: no lender quotation exists (suggestion S-29)."),
        "Add per-unit detail for Property B": ("open", "Still open."),
        "Add a maintenance and capital schedule": ("open", "Still open."),
        "Model mixed paths, not only the three pure choices": ("done", "Implemented: eleven mixed cases priced on their own engine, with the Proposition 19 clawback and the imputed-rent break-even."),
        "Write the rules down before reading any projection": ("done", "Implemented: the pre-commitment register, with its decision columns deliberately empty."),
        "Put the answer and what would change it on the first screen": ("done", "Implemented: the dashboard opens with the answer, a confidence label, the build date and the three checks that would move it."),
        "Price the transfer tax and recording fees into the sell path": ("done", "Implemented: itemised on the taxes page, with the $75 instrument fee shown as exempt and the reason given."),
        "Distinguish enacted changes from proposals": ("done", "Implemented on the law page, with a stated rule for moving an item between the three groups and an annual recheck gate."),
    }
    improve_src = {"Add a real rental opinion for Property A (imputed rent)": ["hud_fmr"],
                   "Model mixed paths, not only the three pure choices": ["rtc63_2_eligibility"],
                   "Model a sale in the same tax year as the inheritance": ["irs_basis"],
                   "Write the rules down before reading any projection": [],
                   "Put the answer and what would change it on the first screen": [],
                   "Price the transfer tax and recording fees into the sell path": ["rtc11911", "gov27388_1"],
                   "Distinguish enacted changes from proposals": ["sos_initiative_status"],
                   "Add per-unit detail for Property B": [],
                   "Add a real rental opinion for Property A": [],
                   "Add a maintenance and capital schedule": [],
                   "Add the itemised tax bills": [],
                   "Add a liquidity model for the estate": ["irs_estate", "irs_i706", "irs_interest", "uscode6166"],
                   "Add a two-person household case": ["irs_tc701", "irs_estate"],
                   "Add a mortgage case": ["fred_mortgage", "fred_prime", "irs_p936", "rtc62"],
                   "Add a distribution chart to the projections": []}
    def improve_badge(a: str) -> str:
        state = improve_status.get(a, ("proposed", ""))
        return (f'<span class="badge verified">done</span>'
                f'<br><span class="small">{esc(state[1])}</span>'
                if state[0] == "done" else
                f'<span class="badge proposed">open</span>'
                + (f'<br><span class="small">{esc(state[1])}</span>' if state[1] else ""))

    improve_rows = [f"<td><strong>{esc(pid)}</strong></td>"
                    f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td><td>{esc(c)}</td>"
                    f"<td>{improve_badge(a)}</td>"
                    f"<td>{blank_dec}</td><td>{blank_dec}</td>"
                    + (src_cell(improve_src[a], "Official source") if improve_src[a]
                       else src_cell([], "No official source applies"))
                    for pid, a, b, c in [
                        ("P-01", "Add per-unit detail for Property B", "Rent, lease dates and anniversary dates per unit, so the income can be projected properly instead of as one total.", "The Property B income is currently a single unverified total with no expiry dates."),
                        ("P-02", "Add a real rental opinion for Property A", "Replaces the break-even rent with a comparison against an actual market rent.", "The rental path is currently tested only against a break-even, which is honest but indirect."),
                        ("P-03", "Add a maintenance and capital schedule", "Year-by-year capital items rather than a percentage of value.", "Lumpy costs are invisible, which flatters every hold path."),
                        ("P-04", "Add the itemised tax bills", "Bond, parcel tax and assessment lines separated from the ad valorem part.", "The fixed charge is currently modelled as a single number growing with inflation."),
                        ("P-05", "Add a liquidity model for the estate", "Whether the estate could pay federal estate tax without selling the house.", "The interaction between the cash inheritance and the house is currently only sketched in scenario bands."),
                        ("P-06", "Add a two-person household case", "Joint filing, the $500,000 exclusion and two exclusions for estate tax.", "The model currently uses the single-filer exclusion throughout, which is conservative."),
                        ("P-07", "Add a mortgage case", "The keep-and-borrow case run end to end: for each band, a fully amortising 30-year fixed loan charged to the keeping paths and set against the sell route that pays the same band's tax out of the proceeds - and, beside it, the discretionary case, where no tax bill forces the borrowing and the cash is invested instead.", "Was not modelled at all; now priced twice, on the liquidity page and lever 6 for the forced case and on its own page for the discretionary one. The open item is a lender's written indication, not the arithmetic (S-29)."),
                        ("P-08", "Add a distribution chart to the projections", "A visual range rather than a single line.", "Readers tend to read the single line as a forecast."),
                        ("P-09", "Add a real rental opinion for Property A (imputed rent)", "Prints the market rent at which living there, and at which letting it out, match selling at the inheritance.", "Without it the housing value of living there is a preference rather than a number."),
                        ("P-10", "Model mixed paths, not only the three pure choices", "Live for a period and then sell, or live and then let, with the Proposition 19 clawback priced.", "The pure paths overstate how bad a short occupancy is and understate what moving out costs."),
                        ("P-11", "Write the rules down before reading any projection", "The household's own test for each path and its priorities, recorded before the figures are read.", "Without it a single projection can be made to justify any path."),
                        ("P-12", "Put the answer and what would change it on the first screen", "A decision strip with the answer, a confidence label, the build date and the three checks that would move it.", "Readers arrive at the recommendation without knowing how conditional it is."),
                        ("P-13", "Price the transfer tax and recording fees into the sell path", "The statutory charges itemised, with the published and private parts separated.", "The 5.5% selling cost is mistaken for a tax figure when most of it is a private quote."),
                        ("P-14", "Distinguish enacted changes from proposals", "A stated rule and an annual recheck gate for the law page, with the failed Proposition 19 repeal recorded as dead.", "A proposal gets treated as law, or a dead measure keeps distorting the arithmetic."),
                        ("P-15", "Model a sale in the same tax year as the inheritance", "Prices the immediate sale before anything else is decided, with the stepped-up basis and the long-term treatment inherited property receives. Restored here after the renumbering pass on a branch that predated it.", "Without it the comparison does not start from the option everything else has to beat."),
                    ]]
    improve = table("Improvements to this site, offered for review",
                    ["ID", "Proposal", "What it would add", "Cost of not doing it", "Status",
                     "Decision (adopt / defer / reject)", "Date decided", "Source"],
                    improve_rows,
                    note="A done badge means the improvement was built into this edition of the site and "
                         "is verified by the build; it does not mean the underlying decision was made for "
                         "the household. An open item still needs a decision, which is recorded in the two "
                         "empty columns.")
    return (
        callout("gate", "Nothing on the first list has been acted on", """
<p>Every item in the <strong>first table</strong> is <strong>proposed</strong>. Building this site did not adopt,
purchase, sign, file or change anything: it cannot obtain a quote, read a roll, or move title. The point of the
page is that someone reads the list, chooses the best path, and only then acts. The selection gate below is the
order in which to do that.</p>
<p>The <strong>second table</strong> is different in kind. It lists improvements to the site itself, and records
which of them have already been built into this edition, so that a reader can tell an open question about the
household's decision apart from a finished piece of analysis. A built item is not a decision made for the
household; the household's own decisions are still blank.</p>""")
        + gate
        + tbl
        + '<h2>Improvements to this site</h2>'
        + improve
        + callout("privacy", "One suggestion that is not optional", """
<p>S-18 is the one item on the list that cannot be deferred, because it is the one that keeps the site honest.
Every figure you see is generated from the data files in <code>assets/data</code> by <code>scripts/model.py</code>
and <code>scripts/build.py</code>. If a number is edited directly in an HTML file, the next rebuild will overwrite
it and the verification will still pass, because the verification checks the generated output, not the intent.
Change the data, not the page.</p>""")
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
    rate_2026_27 = 0.0118162182  # Property B secured rate for FY 2026-27 (publisher withheld on the public site)
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
         + src_cell([], "County rate book withheld for privacy")),
        (f"<td><strong>Property A bill repeated</strong></td>"
         f"<td>The same bill in 2017 and 2018 ({m(ra[2018]['bill'])}), and in 2019 and 2020 ({m(ra[2020]['bill'])}). Assessed value rose 2.00% in both 2018 and 2020.</td>"
         "<td>The ad valorem part rises with assessed value, so an identical bill needs an offsetting change in another charge. A figure copied forward from the year before is also possible.</td>"
         "<td>Check the 2018 and 2020 bills against the figures in the owner's table.</td>"
         + src_cell([], "County rate book withheld for privacy")),
        (f"<td><strong>Property B bill rises 18.4% in 2018</strong></td>"
         f"<td>Bill rises from {m(b17)} to {m(b18)} ({sgn(chg(b17, b18))}) while assessed value rises 2.00%.</td>"
         f"<td>Even if the whole 2017 bill had risen with assessed value, the rise would be about {m(money10(b17 * 0.02))}. About {m(money10((b18 - b17) - b17 * 0.02))} came from other charges.</td>"
         "<td>Read the itemised 2017 and 2018 bills for direct assessments, bond levies and special taxes.</td>"
         + src_cell([], "Official rate page withheld for privacy")),
        (f"<td><strong>Property B bill falls 5.9% in 2021</strong></td>"
         f"<td>Bill falls from {m(b20)} to {m(b21)} ({sgn(chg(b20, b21))}) while assessed value rises {chg_2021:.2f}%.</td>"
         f"<td>At most about {m(money10(assess_part_2021))} of the change can come from assessed value. Other charges therefore fell by at least {m(fall_2021)}.</td>"
         "<td>Read the itemised 2020 and 2021 bills.</td>"
         + src_cell([], "Official rate page withheld for privacy")),
        (f"<td><strong>Property B bill against the published rate</strong></td>"
         f"<td>The 2025 bill is {m(b25_bill)} on {m(b25_av)} of assessed value: {b25_bill / b25_av * 100:.2f}% of assessed value.</td>"
         f"<td>At the FY 2026-27 combined secured rate of about 1.18%, applied to the same value, the ad valorem part is about {m(b25_rate_part)}. The other {m(money10(b25_bill - b25_rate_part))} a year comes from charges outside that rate. The full-precision published rate is withheld from the public site for privacy.</td>"
         "<td>Read the itemised 2025 bill. Identify each direct assessment, bond levy and special tax, and whether each continues.</td>"
         + src_cell([], "Official rate page withheld for privacy")),
    ]
    head_note = (f"Assessed-value changes checked against the official factor for each year: {len(checks)} changes, "
                 f"of which {len(checks) - len(off)} match within $10. The exception is Property B in 2022. "
                 "Every figure is the owner's, rounded to $10, and none has been checked against the county roll.")
    return ('<h2 id="irregularities">Irregularities in the owner\'s rolls and bills</h2>'
            + table("Items for the owner to check. These are questions, not findings of error.",
                    ["Item", "What the figures show", "What the official table or rule says", "What to do", "Source"],
                    rows, note=head_note))


# ------------------------------------------------------------- recheck log ---
def recheck_section() -> str:
    """The 16 November 2026 official-source recheck, published so the reader can repeat it.

    Each row records what was read again, whether the site's figure still matches the
    document, and what could not be checked at all. Nothing here is asserted that was
    not read on the publisher's own domain on the date shown.
    """
    rows = [
        ("Federal estate and gift amounts for 2027",
         "Rev. Proc. 2026-35 was opened in full and read at source. Section 3.44 states the 2027 basic "
         "exclusion as $15,480,000 and section 3.46(1) states the 2027 annual gift exclusion as $20,000. "
         "Both match the figures this site models. The earlier ledger note recorded the section 3.44 "
         "sentence as taken from a search excerpt; it is now taken from the document itself.",
         ["irs_rp2635"]),
        ("Proposition 19 shelter amount and its next adjustment",
         "The Board's own comparison table and filing-requirements checklist were read again. The amount "
         "applicable to a transfer between 16 February 2025 and 15 February 2027 is $1,044,586, and the "
         "Board states the next biennial adjustment falls due on 16 February 2027. The site's projection of "
         "the allowance forward at an assumed rate is therefore anchored on the right starting figure, and "
         "the 2027 update is a known future date rather than a guess.",
         ["boe_prop19", "boe_lta25009"]),
        ("The 1% surcharge above one million dollars",
         "Revenue and Taxation Code section 17043 was read again from the statute: an additional 1% on the "
         "portion of taxable income above $1,000,000, imposed in addition to other taxes in Part 10, with "
         "the credit provisions, the filing-status recomputation and the joint-return provisions "
         "disapplied. That is what the model's combined rate assumes, so the sensitivity that uses it is "
         "unchanged.",
         ["rtc17043"]),
        ("Statewide insurance averages, by policy form",
         "Two tables were read directly from the insurance department's own published files for the first "
         "time on this site: the owner-occupied homeowners multi-peril series, whose newest year gives "
         "$1,074 for experience year 2017, and the rental dwelling and landlord series, which gives $519 "
         "for the same year. Both figures are now the floors of the two insurance bands, and both are "
         "quoted as published. The department's later Part I workbook, which extends the same measures to "
         "2023, is a spreadsheet and could not be read by this build: that is recorded as a limit, not "
         "filled in.",
         ["cdi_homeowners_avg", "cdi_df_rental"]),
        ("Industry averages by state and by amount of insurance",
         "The industry report was re-read. Tables 1 to 3 are machine-readable and the three California rows "
         "this site publishes were confirmed against them, including the 8.4% share of exposures carrying "
         "$1,000,000 or more of insurance. Tables 4 and 5, the by-state averages, begin beyond the pages "
         "this build can read, so they remain blank and flagged here rather than copied from a secondary "
         "summary - the same disposition an earlier session recorded, now independently reproduced.",
         ["naic_hmr_2023"]),
        ("Residual-market coverage limit",
         "The order that raised the state's insurer of last resort from a 1.5 million dollar combined "
         "dwelling limit to $3,000,000, effective 1 April 2020, was read again on the department's own "
         "page. Property A's owner-estimated value exceeds that limit, which is why the coverage-availability "
         "warning stays on the costs page.",
         ["cdi_fairplan"]),
        ("What a lender may do when the borrower dies",
         "The federal statute on due-on-sale clauses was read at source, subsection (d) in full, from the "
         "2024 edition of the United States Code. The exemptions this site now cites - a transfer to a "
         "relative resulting from the borrower's death, a transfer where the borrower's children become "
         "owners, and a transfer into an inter vivos trust in which the borrower remains a beneficiary - are "
         "quoted from it, together with the limit of the protection: buildings of fewer than five dwelling "
         "units.",
         ["uscode1701j3"]),
        ("Figures this session could not check at all",
         "Three. The ad valorem rate used for Property B is published by a city body whose web address names "
         "the jurisdiction, so it is not linked here and remains flagged; the local parcel tax is recorded on "
         "the register with its result pending certification; and the rate area for Property A is withheld "
         "for the same crosswalk reason, which is why the site runs an assumed rate with a diagnostic band "
         "instead. Each is a known hole, not a silent one.",
         []),
    ]
    body = []
    for item, detail, srcs in rows:
        cell = (src_cell(srcs, "Official source") if srcs
                else method_cell("review.html#register", "Withheld for privacy, logged on the register", sources=[]))
        body.append(f"<td><strong>{esc(item)}</strong></td><td>{detail}</td>" + cell)
    return ('<h2 id="recheck">Official-source recheck, 16 November 2026</h2>'
            + callout("note", "Why this is published", """
<p>The brief asks for the authorities to be re-checked periodically and for enacted changes to be told apart
from proposals. This is that re-check, recorded as a table rather than as a claim, so a reader can open the
same document and see the same sentence. Two things follow from doing it in the open: where a figure was
previously taken from a summary or a search excerpt, this says so and says whether the document itself has
now been read; and where a document could not be read at all, the row is left blank rather than filled with
an inference.</p>""")
            + table("What was re-read, and what it showed", ["Figure or rule", "What the source says today", "Source"], body))


PRINT_BUDGET: dict | None = None


def print_budget_section() -> str:
    """The measured length of the printable brief, published as an estimate.

    No browser is available in this environment, so the printed pagination of the
    one-page brief cannot be looked at. What can be done is to measure it: the
    geometry is read out of the stylesheet the brief is actually printed with,
    and the content is measured against it. The estimate is deliberately
    pessimistic. The browser check remains open and is recorded below.
    """
    global PRINT_BUDGET
    css = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
    # The whole rendered page is measured, not just the brief's body: the page
    # template supplies the title, and the title is printed.
    PRINT_BUDGET = print_budget_mod.measure(
        page("briefing.html", page_briefing(),
             PAGE_BUILDERS["briefing.html"][1]), css)
    fills = PRINT_BUDGET["fills"]
    verdict = ("is estimated to fit on one letter-size page"
               if PRINT_BUDGET["fits_one_page"]
               else "is estimated NOT to fit on one letter-size page")
    est_source = ('<td><a href="review.html#register">Measured by the build, '
                  'not an official source</a></td>')
    # The figure for the brief as it was published before this check is a
    # recorded measurement, not a remembered one: it was taken from the
    # committed file with this same estimator and is kept in the repository so
    # the claim can be reproduced.
    before = json.loads((ROOT / "assets" / "data" / "print_budget_before.json").read_text(encoding="utf-8"))
    return (
        '<h2 id="print-budget">Does the one-page brief actually fit on one page?</h2>'
        + callout("note", "A measurement, and what it is not", f"""
<p>The brief is published as a one-page sheet, and the page title, the menu and the print
toolbar all say so. That claim had never been checked, because no browser is available in the
build environment. This session measured it instead.</p>
<p>The brief's printed height is estimated at <strong>{fills:.0%} of one letter-size sheet</strong>
({PRINT_BUDGET['estimated_height_pt']:.0f}pt against {PRINT_BUDGET['capacity_pt']:.0f}pt of usable page
height), across {PRINT_BUDGET['sections']} sections set in {PRINT_BUDGET['grid_rows']} rows of a
two-column grid at {PRINT_BUDGET['font_pt']}pt with {PRINT_BUDGET['margin_in']}in margins. It
{verdict}.</p>
<p><strong>How the measurement works, and why it is an estimate.</strong> The geometry is read out of
<code>assets/style.css</code> rather than repeated here, so changing the print rules changes the
estimate and the two cannot drift apart. The estimate assumes a pessimistic average character
width, does not allow for margins between blocks collapsing, and adds a safety margin to the
total, so it runs long rather than short. It is still a model of a browser, not a browser.</p>
<p><strong>What changed because of it.</strong> The brief as published before this check was estimated
at {before['fills']:.0%} of a sheet ({before['estimated_height_pt']:.0f}pt against
{before['capacity_pt']:.0f}pt): it would have run onto a second page while claiming to be one page. It
is now at {fills:.0%}. Four changes brought it inside the sheet, and none of them removed a figure, a question or
a caveat. The seven sections were re-ordered so that the two longest sit side by side in the two-column
grid instead of beside short ones, which is what a two-column layout is for, and so that the sheet reads
in the order an adviser would want: the decision, the questions to ask, the options and their risks,
what is not known, the mixed paths, the timing, the glossary. The print type was set from 7.4pt to 7.1pt
with tighter spacing. The screen lede was removed from the printed sheet, because the title already says
what the document is. And the section text was shortened.</p>
<p><strong>What is still open.</strong> Nobody has seen the printed sheet. Open
<code>briefing.html</code> in a browser, print it, and check that it is one page and that the type is
legible at {PRINT_BUDGET['font_pt']}pt. The build now fails if the estimate ever exceeds a sheet
again, so an edit that breaks the promise is caught before it is published.</p>""")
        + table("What the estimate is made of",
                ["Measure", "Value", "Where it comes from"], [
                    "<td><strong>Estimated printed height</strong></td>"
                    + "<td>" + f"{PRINT_BUDGET['estimated_height_pt']:.0f}pt</td>" + est_source,
                    "<td><strong>Usable page height</strong></td>"
                    + "<td>" + f"{PRINT_BUDGET['capacity_pt']:.0f}pt (letter, "
                      f"{PRINT_BUDGET['margin_in']}in margins)</td>" + est_source,
                    "<td><strong>Share of one sheet</strong></td>"
                    + "<td>" + f"{fills:.0%}</td>" + est_source,
                    "<td><strong>Body type</strong></td>"
                    + "<td>" + f"{PRINT_BUDGET['font_pt']}pt, about "
                      f"{PRINT_BUDGET['chars_per_line']:.0f} characters to a line</td>" + est_source,
                    "<td><strong>Structure</strong></td>"
                    + "<td>" + f"{PRINT_BUDGET['sections']} sections in {PRINT_BUDGET['grid_rows']} rows "
                      f"of a two-column grid</td>" + est_source,
                    "<td><strong>Verdict</strong></td>"
                    + "<td>" + ("estimated to fit on one page"
                                if PRINT_BUDGET["fits_one_page"]
                                else "estimated NOT to fit") + "</td>" + est_source,
                    "<td><strong>Before this check</strong></td>"
                    + "<td>" + f"{before['fills']:.0%} of a sheet, at {before['font_pt']}pt, measured "
                      f"from commit {esc(before['measured_commit'])} with this same estimator"
                      "</td>" + est_source,
                ],
                note="This is an estimate computed from the shipped stylesheet and the brief's own "
                     "content. It is checked at build time and the build fails if it exceeds a sheet, "
                     "but it is not a substitute for printing the page and looking at it."))


def recheck_17nov_section() -> str:
    """The second independent re-check, 17 November 2026.

    Every row was opened on the publisher's own domain in this session and the figure on
    the site was compared with the document. Nothing in this table changed a model input,
    a published figure or the recommendation; the point of publishing it is that a reader
    can open the same document and see the same sentence, and can tell which figures have
    been confirmed by a human reading and which have not.
    """
    rows = [
        ("Estate tax filing threshold, 2026 death",
         "The Internal Revenue Service's own filing-threshold table still ends at 2026, and the 2026 "
         "figure is $15,000,000. The table and the page's statement that a return is required where the "
         "gross estate plus adjusted taxable gifts and specific gift tax exemption exceeds the "
         "threshold for the year of death are unchanged.",
         ["irs_estate"]),
        ("Basic exclusion and annual gift exclusion, 2027",
         "News release IR-2026-133 of 5 November 2026, summarising Revenue Procedure 2026-35, states "
         "that estates of decedents who die during 2027 have a basic exclusion amount of $15,480,000, "
         "up from $15,000,000 for 2026, and that the annual gift exclusion rises to $20,000 for 2027 "
         "from $19,000 for 2026. Both figures on the estate and dashboard pages match.",
         ["irs_2027"]),
        ("Proposition 19 value cap and the next adjustment date",
         "Letter to Assessors 2025/009 was read in full. The $1 million amount is adjusted to "
         "$1,044,586 for transfers from 16 February 2025 through 15 February 2027; the preceding "
         "amounts were $1,022,600 and $1,000,000; and the letter states the next adjustment occurs in "
         "February 2027. The adjustment is driven by the FHFA California house price index, not by the "
         "consumer price index, which is why the cap is projected forward on a house-price rate.",
         ["boe_lta25009"]),
        ("Proposition 19 eligibility, the one-year rule and the clawback",
         "Revenue and Taxation Code section 63.2(a)(1) was read in full again: the transfer must be of "
         "a principal residence of an eligible transferor, between parents and their children or between "
         "grandparents and their grandchildren with the qualifying parents deceased; it must become the "
         "principal residence of the transferee within one year; the transferee must file for the "
         "homeowners' or disabled veterans' exemption within a year; and under (a)(1)(C) the base year "
         "value established at the change in ownership, adjusted annually, shall be enrolled once the "
         "eligible transferee no longer qualifies. This is the arithmetic the model implements and the "
         "reading the site publishes as a question for counsel.",
         ["rtc63_2"]),
        ("The additional 1% tax above one million dollars",
         "Section 17043 was read again from the statute. Subdivision (a) imposes an additional tax of "
         "1 percent on the portion of taxable income in excess of $1,000,000; subdivision (c) switches "
         "off the credit provisions, the filing-status and bracket recomputation, and the joint-return "
         "provisions. The published combined rate of 37.1% is built on this and on the current-year "
         "state schedules, and the surcharge sensitivity that uses it is unchanged.",
         ["rtc17043"]),
        ("An inheritance is not income",
         "The Franchise Tax Board's gifts and inheritance page states that if a gift or inheritance is "
         "received it is not included in income, while income the gift or inheritance later produces - "
         "interest, dividends, rental income and gain on a real property sale - is taxable. The page "
         "carries a last-updated date of 24 September 2025 and is unchanged.",
         ["ftb_inheritance"]),
        ("California estate and inheritance tax",
         "The State Controller's Office states that for decedents dying on or after 1 January 2005 there "
         "is no longer a requirement to file a California estate tax return, and that the California "
         "generation-skipping transfer tax does not apply to transfers after 31 December 2004. The "
         "estate page's California position is unchanged.",
         ["sco_estate"]),
        ("California's top marginal rate for the current year",
         "The 2026 California tax rate schedules were read again. Schedule X charges 12.30 percent over "
         "$768,213, Schedule Y 12.30 percent over $1,536,426, and Schedule Z 12.30 percent over "
         "$1,044,771. The site's combined-rate row cites the 2025 and 2026 schedules together, and the "
         "bracket starts it registers are unchanged.",
         ["ftb_rates_2026"]),
        ("Statewide rent increase cap",
         "Civil Code section 1947.12 was read again. Subdivision (a)(1) caps an increase over any "
         "12-month period at 5 percent plus the percentage change in the cost of living, or 10 percent, "
         "whichever is lower, of the lowest gross rental rate charged in the preceding 12 months; "
         "subdivision (a)(2) limits a continuing tenancy to two increments in that period; and "
         "subdivision (b) exempts the initial rate of a new tenancy.",
         ["civ1947_12"]),
        ("Long-range inflation and interest assumptions",
         "Table II.C1 of the 2026 OASDI Trustees Report was read at source (the page is dated 9 June "
         "2026). The annual percentage change in the Consumer Price Index is 2.4 percent under the "
         "intermediate assumptions, 3.0 percent low-cost and 1.8 percent high-cost; the annual trust "
         "fund new-issue real interest rate for 2044 and later is 2.3 percent intermediate, 2.8 percent "
         "low-cost and 1.8 percent high-cost. These are the figures the model uses for its inflation "
         "band and its discount-rate band.",
         ["ssa_trustees"]),
        ("Interest on an unpaid estate tax",
         "The published quarterly rates still show 7 percent for underpayment and 4 percent for the "
         "federal short-term rate in the fourth quarter of 2026, and a published range of 3 percent to "
         "8 percent across 2022 to 2026. The liquidity page's deferral arithmetic uses the same rates.",
         ["irs_interest"]),
        ("What a lender may do when the borrower dies",
         "Subsection (d) of the federal due-on-sale statute was read again in full. For a lien on "
         "residential real property containing fewer than five dwelling units, a lender may not exercise "
         "its option upon, among other transfers, \"a transfer to a relative resulting from the death of "
         "a borrower\", or a transfer where the spouse or children of the borrower become owners. The "
         "decision page's statement of the limit on acceleration matches the subsection.",
         ["uscode1701j3"]),
        ("The rate anchors the borrowing and parking paths are priced on",
         "Four published series were re-read on 17 November 2026. The IRS quarterly interest page still shows 7 "
         "percent for underpayments and a 4 percent federal short-term rate for the fourth quarter of 2026, a 6 "
         "percent quarter in the middle of 2026, and no first-quarter 2027 row at all - so the liquidity page's "
         "rate is the current published one, not a stale one. The Freddie Mac 30-year weekly average, read as the "
         "whole of calendar 2026, is 7.11 percent for the week of 12 November with 5.98 percent (26 February) and "
         "7.40 percent (8 and 15 October) as the year's low and high, which are the three rungs the keep-and-borrow "
         "page now prices. The Treasury par yield curve's latest published row, 16 November 2026, is 4.34 percent "
         "at three months and 4.83 percent at two years, both inside the 3.5 to 5.0 percent band the phased path "
         "parks in, and the 13 November row a previous session recorded (4.32 and 4.88) still matched. The "
         "published prime rate is 7.00 percent on every business day from 1 October through 9 November 2026.",
         ["irs_interest", "fred_mortgage", "treasury_cmt", "fred_prime"]),
        ("What interest on money taken out of a home is deductible against",
         "Publication 936 (2025) was read at source on 17 November 2026 for the first time on this site. It states "
         "that interest on home equity loans and lines of credit is deductible only where the borrowed funds were "
         "used to buy, build or substantially improve the home that secures the loan, and it caps home acquisition "
         "debt at $750,000 for mortgages taken out after 15 December 2017 ($1,000,000 for those taken out between "
         "13 October 1987 and 16 December 2017). That is the authority for this site assuming no deduction on the "
         "keep-and-borrow path, where the money is invested rather than spent on the house.",
         ["irs_p936"]),
        ("Whether granting a lien over the home is a change in ownership",
         "Revenue and Taxation Code section 62 was read in full on the publisher's own domain on 17 November 2026, "
         "including subdivision (c), which an earlier partial read had quoted from memory: a change in ownership "
         "does not include the creation, assignment, termination or reconveyance of a security interest, or the "
         "substitution of a trustee under a security instrument. Borrowing against the inherited home therefore "
         "does not by itself reassess it, which is why the keep-and-borrow page can hold the Proposition 19 "
         "shelter constant while it changes everything else about the position.",
         ["rtc62"]),
        ("The November 2026 ballot measures, still unofficial",
         "The Secretary of State's ballot-measures page was re-read on 17 November 2026 at its 16 November 2026, "
         "7:12 p.m. update: all 23,860 precincts partially reporting, results still labelled unofficial, "
         "certification still due 11 December 2026. Proposition 3 stands at 60.8 percent yes (60.7 percent on the "
         "14 November read), Proposition 40 at 52.2 percent no, Proposition 41 at 55.2 percent no, Proposition 42 "
         "at 51.2 percent yes and Proposition 43 at 57.7 percent no. Every dated figure on the laws page and the "
         "dashboard was moved to this read; nothing became law in the window, so the enacted-versus-proposed "
         "labels are unchanged.",
         ["sos_results"]),
        ("Capital gains treatment in California",
         "The Franchise Tax Board's capital-gains page was re-read: 'California does not have a lower rate for "
         "capital gains. All capital gains are taxed as ordinary income.' The page states it was last updated 28 "
         "January 2026. That is the treatment the model's combined rate assumes when it applies ordinary-income "
         "rates to the whole gain.",
         ["ftb_cg"]),
        ("The 1% surcharge as the return itself reports it",
         "For the first time the official 2025 Form 540 instructions were read at source beside the statute. Line "
         "62, named the Behavioral Health Services Tax in that booklet, subtracts $1,000,000 from the line 19 "
         "amount and applies 1 percent to the remainder. The statute is the authority and the booklet shows how "
         "the return reports it; both now sit beside the sensitivity table on the taxes page.",
         ["ftb_540_instructions_2025"]),
        ("Figures this session could not check at all",
         "Three, unchanged. The ad valorem rate for Property B is published by a city body whose web "
         "address names the jurisdiction, so it is not linked here and stays flagged; the local parcel "
         "tax result is on the register with certification pending; and the rate area for Property A is "
         "withheld for the same crosswalk reason, which is why the site runs an assumed rate with a "
         "diagnostic band instead. Each is a known hole, not a silent one.",
         []),
    ]
    body = []
    for item, detail, srcs in rows:
        cell = (src_cell(srcs, "Official source") if srcs
                else method_cell("review.html#register", "Withheld for privacy, logged on the register", sources=[]))
        body.append(f"<td><strong>{esc(item)}</strong></td><td>{detail}</td>" + cell)
    return ('<h2 id="recheck-2">Official-source recheck, 17 November 2026</h2>'
            + callout("note", "Why there are two re-check tables", """
<p>This is the second independent pass, and it is published separately from the 16 November table
rather than merged into it, so that a reader can see what each session actually opened and when. The
method is the same: every figure below was read on the publisher's own domain in this session, and
the published figure was compared with the document.</p>
<p><strong>No figure changed.</strong> Every value the site already carried matched its source, so no
model input, no published table and no recommendation moved. Where a document could not be opened at
all, the row says so instead of being filled in.</p>""")
            + table("What was re-read on 17 November 2026, and what it showed",
                    ["Figure or rule", "What the source says today", "Source"], body,
                    note="A re-check that changes nothing is still worth publishing: it is the only way a "
                         "reader can tell the difference between a figure a human has checked against the "
                         "document and one that has been carried forward unchecked."))


def history_audit_section() -> str:
    """The Git-history privacy audit, published as counts only.

    Deliberately value-free: the page states how many file versions carry the shape of
    an identifier, never what any of them are. Reprinting a postal code or a place name
    here to 'disclose' it would create the exposure it is supposed to describe.
    """
    rows = [
        ("Street address", "0", "0", "Never committed in any reachable commit."),
        ("Parcel or assessor number", "0", "0", "Never committed in any reachable commit."),
        ("Telephone number", "0", "0", "Never committed in any reachable commit."),
        ("Person-name pattern", "0", "0", "Never committed in any reachable commit."),
        ("Personal mail-service address, in file content", "0", "0",
         "Zero after the audit was corrected on 17 November 2026 to agree with the tree guard: the two "
         "matches it used to report in the current tree were both GitHub service addresses quoted in the "
         "privacy documentation, not personal addresses. The personal address in this repository is in "
         "Git's commit identities, not in any file: 172 of 482 commits carry an author address that is "
         "not the GitHub noreply address, three distinct addresses in all, and 165 carry one as committer. "
         "That is a rewrite of commit metadata, not of file content, and the runbook covers it."),
        ("Postal code, in a prefixed form", "14", "0",
         "Superseded file versions only."),
        ("Postal code, bare", "87", "0",
         "Superseded file versions and the archive directories, which are never published."),
        ("Place name at property level", "246", "0",
         "Superseded file versions and archive material, plus every early version written before the county "
         "and city names were withdrawn. One commit message matches. None of it is in the deployable artifact."),
        ("Place name anywhere, including inside a web address", "266", "0",
         "The same versions, counted with the wider pattern that also catches a host name."),
        ("County or city name", "730", "0",
         "The widest class. Every version written before the jurisdiction names were withdrawn, including "
         "superseded sections of the coordination board."),
        ("Location-specific source host", "675", "0",
         "Links to county and city publishers, whose web addresses name the jurisdiction. Withdrawn from the "
         "published site; still in the history."),
        ("Withdrawn metropolitan series identifier", "198", "0",
         "The FHFA and FRED metropolitan series and their codes, withdrawn from the published edition on "
         "15 November 2026 because they crosswalked the placeholders to their metropolitan areas."),
        ("Metro phrasing attached to a placeholder", "82", "0",
         "The prose form of the same crosswalk."),
        ("Dollar amount that is not a multiple of ten", "242", "1",
         "Superseded versions hold the pre-rounding figures. In the current tracked tree one file still does: "
         "the coordination board, whose older sessions' sections quote unrounded model output and published "
         "aggregate data. It is excluded from the published site by the Jekyll configuration and the packaging "
         "allowlist, and it is a public file of this repository. Every page and every data file the site "
         "publishes is clean, and the board is the residue the history rewrite would also have to take."),
    ]
    body = [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(d)}</td>"
            + f'<td><a href="review.html#register">Logged in the register</a></td>' for a, b, c, d in rows]
    return (
        '<h2 id="history-audit">Privacy audit of this repository\'s own history</h2>'
        + callout("privacy", "What the history audit found, and what it did not do", """
<p>The published site is scanned on every build for names, street addresses, postal codes, parcel numbers,
telephone numbers, email addresses, property-level place names and the county and city names, and for any dollar
figure that is not a
multiple of ten. That scan covers the deployable artifact, not the Git history behind it.</p>
<p>A separate read-only audit therefore walks every commit reachable in this repository and counts how many file
versions carry the <em>shape</em> of each identifier. It reports counts only. It does not print a matching value,
because publishing the value in order to disclose it would recreate exactly the exposure being disclosed.</p>
<p><strong>The measurement below was taken on 17 November 2026 over the complete history in a full clone: 482
commits from 10 to 17 November 2026, 1,869 distinct file versions.</strong> The current tracked tree is clean on
every identifier class. No street address, parcel number, telephone number or personal mail-service address has
ever been committed in any file. Postal codes, place names, the two jurisdiction names, the jurisdiction
publishers' web addresses and the withdrawn metropolitan series identifiers did appear in superseded file
versions and in archive material, none of which is part of the published artifact. One amount class still has a
match in the current tree, and it is a single file: this repository's coordination board.</p>
<p>Two things about the numbers are worth stating because they changed since the last measurement on 16 November.
The audit now treats a GitHub service address the way the tracked-tree guard already does, so the two
documentation matches it used to report are no longer counted as personal; and it takes its list of exempt
official amounts from the publication gate instead of keeping a copy of its own, which had drifted and was
counting three statutory recording fees as exposure. Counts that moved, moved because the measuring was corrected,
not because the history changed. A session cannot rewrite the history: it can only measure it honestly, which is
what this table is for.</p>
<p>Cleaning the history is a different operation from cleaning the site: it needs a rewrite and a force-push of a
public branch, which invalidates every clone, every open pull request and every fork, and cannot recall copies
already downloaded. That is the owner's decision, it is recorded as an open item, and the procedure and its costs
are written up for the owner. Until that decision is taken, this page states the exposure rather than claiming it
has been removed.</p>""")
        + table("File versions whose content matches each identifier class, measured 17 November 2026",
                ["Identifier class", "File versions in history", "Files in the current tracked tree",
                 "What that means", "Basis"], body,
                note="Counts are an upper bound. A file version can match because the rule itself is being "
                     "described, or because an official documentary quote contains a non-round amount, as well as "
                     "because a real identifier is present. Address, parcel and telephone classes are the ones "
                     "with zero in both columns.")
        + f"""<section id="history-audit-method">
<h3>How the history audit works</h3>
<ul>
<li><code>scripts/privacy_scrub_audit.py</code> runs <code>git log --all</code> and <code>git log --name-only</code>,
reads every distinct file version, and tests it against the same identifier patterns the live publication gate
uses. It writes nothing and changes nothing.</li>
<li>The amount class is evaluated by calling the live gate's own money test, so a rounded figure is never
counted and a pre-rounding figure always is, and the exemption for verbatim official amounts cannot drift from
the exemption the site actually applies.</li>
<li>The count needs a complete clone. A shallow checkout silently under-reports: this repository's Arena clones
arrive shallow, so <code>git fetch --unshallow origin</code> is run before the audit, and the audit says in its
own header when the history it read was incomplete.</li>
<li>The audit knows its own limits. It reads file content, not commit metadata: the author and committer
addresses Git stores on each commit are outside its patterns, and those carry an address in 172 of the 482
commits that no file has ever held. It cannot see pull-request diffs, forks, or copies outside this repository,
and it cannot certify that a deleted object is unreachable on the hosting service.</li>
</ul>
</section>"""
    )


# --------------------------------------------- roll and bill line-by-line audit --
def roll_audit_section() -> str:
    """What the two roll tables do and do not prove, computed rather than asserted."""
    ra = MODEL.get("roll_audit") or {}
    if not ra:
        return ""
    pa, pb = ra["property_a"], ra["property_b"]

    def fixed_rows(p: dict, label: str) -> list[str]:
        out = []
        for f in p["fixed"]:
            out.append(
                f"<td>{label}</td><td>{f['year']}</td><td>{m(f['bill'])}</td>"
                f"<td>{m(f['assessed'])}</td><td>{m(f['ad_valorem'])}</td>"
                f"<td>{m(f['fixed'])}</td><td>{f['fixed_pct']}%</td>"
                + method_cell("#method", "Model output", sources=["boe_pub29", "rtc51"]))
        return out

    def finding(n, title, body, status):
        return f'<div class="callout {status}"><div class="callout-title">R-{n}. {esc(title)}</div>{body}</div>'

    return (
        '<h2 id="roll-audit">Line-by-line audit of the two roll tables</h2>'
        + callout("note", "What was checked, and what could not be", """
<p>The two tables on the Property A and Property B pages are the owner's own records. This audit re-derives
every number in them with arithmetic only. It does not compare them with the county's roll, because that
record is held by the county, whose name and pages are deliberately withheld from this public site; ordering
the assessor's parcel history is a task for the owner, and it is the first item on the list below.</p>""")
        + finding("1", "Every published year-over-year percentage reproduces exactly",
                  f"""<p>Each row's assessed value and bill were divided by the row above it. The resulting
percentages match the owner's published changes in all {pa['year_pairs_checked']} Property A pairs and all
{pb['year_pairs_checked']} Property B pairs. No transcription error was found in either table.</p>""",
                  "good")
        + finding("2", "The assessed value never exceeds the Proposition 13 cap",
                  f"""<p>No year in either table grows faster than 2%. Property A grew 2.0% in ten of eleven
pairs and 1.0% and 1.5% in two others; Property B grew 2.0% in eight of nine. This is what a long-held
base-year value looks like, and it is consistent with the Proposition 13 cap having bound in every year
shown. Property A's assessment of {m(pa['fixed'][-1]['assessed'])} on a house valued near
{m(A['estimated_market_value_2026'])} is the single largest number in the analysis: it is the shelter.</p>""",
                  "good")
        + finding("3", "The 2% cap does not bound the whole bill, and on Property B it bounds barely half of it",
                  f"""<p>Only the <em>ad valorem</em> part of a property tax bill is limited by the cap. The rest -
fixed charges, special assessments and district levies - is set separately. Splitting each bill at the stated
ad valorem rate shows the fixed part is <strong>{pa['fixed_share_latest_pct']}%</strong> of Property A's bill
and <strong>{pb['fixed_share_latest_pct']}%</strong> of Property B's. The arithmetic ceiling follows: the cap
can bound at most <strong>{pa['max_bound_share_pct']}%</strong> of Property A's bill and
<strong>{pb['max_bound_share_pct']}%</strong> of Property B's.</p>
<p>This matters most on the property the heir already owns. Property B's fixed charges rose from
{m(pb['fixed'][0]['fixed'])} in {pb['fixed'][0]['year']} to {m(pb['fixed'][-1]['fixed'])} in
{pb['fixed'][-1]['year']}, which is <strong>{pb['fixed_growth_full_pct']}% a year</strong> over that window -
and the jump happened in one year, {pb['fixed'][2]['year']}, when the fixed part rose by
{m(pb['fixed'][2]['fixed'] - pb['fixed'][1]['fixed'])}. The bill in that year rose
<strong>{round((pb['fixed'][2]['bill'] / pb['fixed'][1]['bill'] - 1) * 100, 1)}%</strong> on an assessed value that rose 2.0%.</p>""",
                  "flag")
        + finding("4", "Reporting the growth in two windows gives two different answers, and both are true",
                  f"""<p>The recent window is calm: over 2020-2025 the fixed part grew
<strong>{pb['fixed_growth_2020_2025_pct']}%</strong> a year on Property B and
<strong>{pa['fixed_growth_2020_2025_pct']}%</strong> on Property A. The long window is not:
<strong>{pb['fixed_growth_full_pct']}%</strong> a year on Property B and
<strong>{pa['fixed_growth_full_pct']}%</strong> on Property A. One of these is a level and one is a step, and
the site publishes both so neither can be presented alone. A single growth rate chosen from the recent window
would quietly assume the step never repeats.</p>""",
                  "flag")
        + finding("5", "The model's fixed-charge assumption sits between the two properties, not above both",
                  f"""<p>The model grows the fixed part at <strong>{pa['assumption_used_pct']}%</strong> a year,
slightly above Property A's eleven-year average of {pa['fixed_growth_full_pct']}% and well below Property B's
nine-year average of {pb['fixed_growth_full_pct']}%. It is stated in the inputs file as deliberately conservative. The effect is
that every projected bill on this site is more likely to be too low than too high, and Property B's bills are
the ones most exposed, because it carries the larger fixed share. <strong>Not corrected in the model in this
pass</strong>, because changing an assumption moves every published figure and the owner should choose the
rate; the exposure is published instead.</p>""",
                  "flag")
        + finding("6", "The ad valorem rate cannot be identified from these bills, and the site must not pretend otherwise",
                  f"""<p>The stated rate for Property A is {pcf(ASM['ad_valorem_rate_a']['value'], 2)}. With
it, the fixed part of the bill works out between {m(min(f['fixed'] for f in pa['fixed']))} and
{m(max(f['fixed'] for f in pa['fixed']))} across thirteen years: it does not trend, so the rate is consistent
with the bills. But that is a test the rate passes, not a test that identifies it. Assessed value grows at
2% and so does the bill, so a higher rate paired with a lower fixed part fits almost as well. The honest
statement, which the inputs file now carries, is that the rate is a published-law figure and the fixed part is
the residual.</p>""",
                  "flag")
        + finding("7", "The audit is of arithmetic, not of the county's record",
                  f"""<p>Six findings above can be established from the tables alone. None of them confirms that
the tables match the assessor's roll, that the bills were paid, or that either property's tax rate area is the
one assumed. Those need the county record and are listed as open questions on the
<a href="questions.html">questions page</a>.</p>""",
                  "note")
        + table("The fixed and ad valorem parts of each bill, re-derived",
                ["Property", "Year", "Bill", "Assessed value", "Ad valorem at the stated rate",
                 "Fixed charges (residual)", "Fixed share", "Basis"],
                fixed_rows(pa, "Property A") + fixed_rows(pb, "Property B"),
                note="The fixed part is the bill minus the rate times the assessed value. It is a residual, so "
                     "an error in the rate appears here in full: this table shows the size of that exposure, "
                     "not a measured fixed charge. Published figures are rounded to the nearest $10, so a "
                     "residual shown as 0 is below the rounding step and not a measured zero.")
    )


# --------------------------------------------------------- assumption register --
ASSUMPTION_LABELS = {
    "ad_valorem_rate_a": ("Property A ad valorem rate", "pct"),
    "ad_valorem_rate_b": ("Property B ad valorem rate", "pct"),
    "fixed_charge_growth": ("Growth of the fixed part of a tax bill", "pct"),
    "house_growth": ("House price growth", "pct"),
    "inflation": ("Consumer price inflation", "pct"),
    "equity_return_nominal_gross": ("Equity return, gross of tax", "pct"),
    "equity_tax_drag": ("Tax drag on a taxable equity account", "pct"),
    "treasury_yield_nominal": ("Treasury yield, 10-year", "pct"),
    "treasury_short_yield_nominal": ("Treasury yield, 3 month to 2 year", "pct"),
    "prop19_cap_growth": ("Growth of the Proposition 19 excluded amount", "pct"),
    "selling_cost_pct": ("Cost of selling a house", "pct"),
    "assessed_value_growth": ("Growth of assessed value", "pct"),
    "combined_gain_tax_rate": ("Combined tax rate on a capital gain", "pct"),
    "depreciation_recapture_rate": ("Rate on recaptured depreciation", "pct"),
    "ca_1pct_surcharge": ("Section 17043 additional tax", "pct"),
    "phased_park_months": ("Months sale proceeds sit in Treasuries first", "int"),
    "phased_equity_phase_months": ("Months over which equities are bought", "int"),
}


def assumption_register() -> str:
    """Every assumption, its baseline, its band, and whether the band is measured.

    The owner's brief asks for ranges rather than round-number points. This table
    is the answer for the model's own knobs: each row now carries a band, names the
    evidence behind it, and says plainly whether that evidence is a measurement, a
    published figure, or a stated scenario. A reader can see which assumptions are
    load-bearing on evidence and which are judgement.
    """
    rows = []
    measured = 0
    for key, (label, kind) in ASSUMPTION_LABELS.items():
        a = ASM.get(key)
        if not isinstance(a, dict):
            continue
        base = a.get("baseline", a.get("value"))
        low, high = a.get("low"), a.get("high")
        band_basis = a.get("band_basis", "")

        def fmt(x):
            if x is None:
                return '<span class="blank">no band</span>'
            return f"{x * 100:.2f}%" if kind == "pct" else f"{int(x)} months"

        if band_basis:
            lower = band_basis.lower()
            srcs = a.get("src") or []
            if "no band" in lower:
                how = "Fixed by statute"
                source = src_cell(srcs, "Official source")
            elif "diagnostic band" in lower:
                how = "Diagnostic, not a measurement"
                source = method_cell("#method", "Bounded by the audit", srcs)
            elif any(k in lower for k in ("measured", "own audited",
                                          "both ends are built from published",
                                          "published for one fiscal year")):
                measured += 1
                how = "Measured from the record"
                source = src_cell(srcs, "Where the band comes from") if srcs else method_cell("#method", sources=[])
            else:
                how = "Stated scenario"
                source = method_cell("#method", "Stated, not sourced", sources=[])
            basis = band_basis
        else:
            how = "Point input"
            basis = a.get("basis", "")
            source = method_cell("#method", sources=[])
        rows.append(
            f"<td><strong>{esc(label)}</strong></td><td>{fmt(base)}</td>"
            f"<td>{fmt(low)}</td><td>{fmt(high)}</td>"
            f'<td><span class="badge {"verified" if how.startswith(("Measured", "Fixed")) else "unverified"}">'
            f"{esc(how)}</span></td><td>{esc(basis)}</td>" + source)
    return (
        callout("key", "Every assumption now carries a band, and the band says what it is", f"""
<p>The first edition of this analysis used round point values: 4% house growth, 7% equities, 5.5% selling costs.
A single point value is read as a forecast even when it is labelled an assumption, and a decision that only
works at one value is not a decision. Every assumption the model uses is listed below with a low and a high
case. <strong>{measured} of them</strong> rest on a measurement or a published figure; the rest are stated
scenarios.</p>
<p>The distinction is the point of the table. A <em>measured</em> band can be checked against the source in the
last column. A <em>stated scenario</em> cannot, and no amount of arithmetic will make it so - the honest
treatment is to publish it as judgement and show how much the answer moves when it is wrong, which the what-if
page and the black-swan page do.</p>""")
        + table("The assumption register",
                ["Assumption", "Baseline", "Low", "High", "Kind", "What the band rests on", "Source"],
                rows,
                note="A blank band is deliberate: where no defensible range exists, none is invented. The two "
                     "assumptions with no band are the statutory surcharge rate, which does not vary, and "
                     "phase-in length, which is published as three separate cases rather than one midpoint.")
    )


# --------------------------------------------------------- imputed rent -------
def imputed_rent_section() -> str:
    """What the living path is worth when the roof it provides is given a value.

    The brief asks for an imputed-rent input on the living paths. The honest way to
    supply one is to state the bias it removes and then show the size of the bias.
    """
    ir = MODEL.get("imputed_rent") or {}
    if not ir.get("rows"):
        return ""
    rows = []
    for r in ir["rows"]:
        share = f"{r['share'] * 100:.0f}%"
        verdict = ("Living wins" if r["living_wins"] else "Selling still wins")
        rows.append(
            f"<td>{share} of market rent</td><td>{m(r['annual_credit'])}</td>"
            f"<td>{m(r['credit_fv'])}</td><td>{m(r['terminal'])}</td>"
            f"<td>{m(r['gap_to_sell'])}</td>"
            f'<td><span class="badge {"verified" if r["living_wins"] else "unverified"}">{verdict}</span></td>'
            + method_cell("#method", "Model output", sources=["fred_casthpi", "fred_gs10", "damodaran_histret"]))
    pct_needed = next((r["share"] for r in ir["rows"] if r["living_wins"]), None)
    return (
        '<h2 id="imputed-rent">The living path, and the rent it does not pay itself</h2>'
        + callout("key", "The published comparison charges the living path for the house and credits it with nothing", f"""
<p>If the heir lives in the house, the heir is also consuming housing. A comparison that charges every cost of
owning and credits none of that consumption makes living look worse than it is by exactly the value of the
roof. This site publishes that version - <strong>zero imputed rent</strong> - because it is the conservative
one, and it says so rather than letting the omission hide inside a table.</p>
<p>The table below prices the omission. The credit used is the same figure the letting path is measured
against, <strong>{m(ir['rent_monthly'])} a month</strong> in {ir['year']} dollars, so both paths are judged on
one piece of evidence instead of two different ones.</p>""")
        + table("The living path with the housing it provides credited at a share of market rent",
                ["Assumption about imputed rent", "Annual credit", "Future value of the credit",
                 "Living path terminal value", "Gap still to close", "Outcome"],
                rows,
                note="The published baseline is the 0% row. Every row charges the same property tax, insurance, "
                     "water, power and maintenance; only the credit for occupying the home changes. Figures are "
                     "2045 dollars, thirty-year horizon, eight-point equity assumption less tax drag.")
        + callout("flag", "What this changes, and what it does not", f"""
<p><strong>It does not change the published recommendation</strong>, but it narrows it in a way worth stating.
Selling still wins unless the housing is credited at about <strong>{'100%' if pct_needed == 1.0 else f'{pct_needed*100:.0f}%'}</strong>
of market rent - that is, unless the heir values living in this particular house at essentially the full
market rent it would fetch. At that point the two paths are level, and the decision stops being financial. A
household that would genuinely pay {m(ir['rent_monthly'])} a month to live there has a different answer from
one that would not, and neither answer is wrong.</p>
<p><strong>What it does not fix.</strong> The credit is still an assumption about what the household would
otherwise pay, and there is still no market rent for the home in the model. Filling both from one written
rental opinion is the way to close it, and it is the first open question on the
<a href="questions.html">questions page</a>.</p>""")
    )


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
        ("Property B ad valorem rate", pcf(ASM["ad_valorem_rate_b"]["value"], 2),
         "Published for the city's secured roll for fiscal year 2026-27; the publisher is not named or linked on the public site for privacy",
         "Confirm against the parcel's own bill; the official page is not linked for privacy."),
        ("Property A water", f"{m(A['annual_costs']['water']['low'])} to {m(A['annual_costs']['water']['high'])} a year",
         "Owner estimate, unverified. The water and sewer tariff comparison is withheld from the public edition for privacy, and the provider printed on the parcel's own bill is unconfirmed.",
         "Confirm the provider on the bill, then compare twelve months of bills with the derived tariff range."),
        ("Property A electricity, net of solar", f"{m(A['annual_costs']['electricity']['low'])} to {m(A['annual_costs']['electricity']['high'])} a year",
         "Owner estimate", "Read twelve months of bills and the interconnection agreement."),
        ("Property B water", f"{m(B['annual_costs']['water']['low'])} to {m(B['annual_costs']['water']['high'])} a year",
         "Owner estimate", "Read the bills."),
        ("Property B electricity", f"{m(B['annual_costs']['electricity']['low'])} to {m(B['annual_costs']['electricity']['high'])} a year",
         "Owner estimate", "Read the bills."),
        ("Insurance on both properties", f"{m(A['annual_costs']['insurance']['mid'])} a year each, inside a band",
         "Owner estimate, now carried as a range rather than a point: the floor of each band is the published statewide average written premium for the matching policy form (the Department's own table, read 16 November 2026), the middle is the owner's figure, and the ceiling is a stated scenario. Neither building has a quote, so no premium is claimed for either. The by-state averages in Table 4 of the industry report were re-checked on 16 November 2026 and are still beyond the pages this build can machine-read, so they are left blank on the costs page rather than copied from a secondary source.",
         "Get three quotes per building, one of which is a landlord policy for Property B; then narrow the band and rebuild."),
        ("Whether either building is encumbered at the transfer", "Modelled free and clear",
         "Not supplied in either direction, and stated as an assumption on the decision page rather than left "
         "out. A balance would reduce the proceeds of a sale and add a payment to every path that keeps the "
         "building; the site prices each stated payment level instead of guessing one. The federal rule on "
         "due-on-sale clauses was read at source and is cited where the assumption is stated.",
         "Ask the lender for a payoff statement dated near the transfer and read the recorder's index for liens."),
        ("Maintenance on both properties", "0.5% / 0.75% of value for Property A, 1.5% for Property B",
         "Assumption. No figure was supplied.",
         "Assemble five years of actual spend and a capital plan."),
        ("Property B rent", m(B["rent"]["annual"]) + " a year",
         "Owner statement, unverified",
         "Read the leases and the rent ledger."),
        ("The inherited cash amount", "Not published",
         "Deliberately withheld from this site",
         "Work through the scenario bands on the estate page privately."),
        ("City transfer tax reduction proposal", "Not used in any figure",
         "Reported publicly but not verified against an official city source on the public site",
         "Check the city's Board of Supervisors file before relying on it."),
        ("City documentary transfer tax on a sale of Property A", "Not modelled",
         "Section 11911(b) lets a city add half the county rate again, with a credit against the "
         "county tax. Whether a city tax applies here cannot be checked without naming the city, so "
         "only the county charge is carried.",
         "Ask the escrow officer for a fee estimate, or look up the city's own schedule privately."),
        ("Commission, escrow and title as a share of the sale price", "The remainder of the modelled 5.5%",
         "A private charge, not a statute. The published statutes come to about 0.11% of the price; "
         "the rest of the 5.5% is a market quote this repository has not obtained.",
         "Get two written listing and escrow estimates."),
        ("Property A market rent, and therefore the imputed-rent credit", "Published only as a range of scenarios",
         "No official source publishes a market rent for a specific home, and the input is empty.",
         "Obtain one documented rent opinion and enter it in the data file."),
        ("Combined recapture rate, corrected from 41.1% to 42.1%",
         "42.1% (was 41.1%)",
         "Arithmetic defect now fixed. Every component is a published rate - 25% federal "
         "unrecaptured section 1250, the 13.3% California top marginal rate and the 3.8% net "
         "investment income tax - and 25 + 13.3 + 3.8 = 42.1. The previous edition published 41.1, "
         "one percentage point below its own stated components. Every figure that depends on "
         "recapture was rebuilt.",
         "No action needed: the correction is in. Have the CPA confirm the components apply on "
         "these facts."),
        ("Mixed paths and the distributions behind the headline",
         "Published on the decision, dashboard and projections pages",
         "Computed by scripts/mixed.py from the published inputs and the same verified series the "
         "economy page uses. The mixed paths carry every cost the pure paths carry; the distributions "
         "resample the verified record and do not forecast.",
         "Read the method section; re-run scripts/mixed.py after any input change."),
        ("Parcel tax on Property B approved November 2026",
         "$249 a year for a multifamily parcel up to 5,000 sq ft, first fiscal year; the band for this parcel "
         "is not determined",
         "The official terms were read from the city's own measure text and the transit agency's own "
         "parcel-tax page on 15 November 2026. The publisher is not named or linked on the public site, "
         "because the jurisdiction identifies the properties. The parcel's building area was not supplied, "
         "so no figure from the measure is added to any total on this site. This closes the earlier register "
         "row that recorded the measure as not located: a local measure cannot be found from the statewide "
         "returns alone, and the earlier pass would not search by letter because that names the jurisdiction; "
         "the text was instead read directly on the publisher's own domain, with the name kept off the site.",
         "Read the building area from the assessor's records or the official parcel lookup when it opens on "
         "1 December 2026, then price the correct band."),
        ("The Proposition 19 clawback on the live-then-let path", "Now priced, both readings",
         "Section 63.2(a)(1)(C) is applied as written, but no court has applied it to these facts in "
         "anything this repository has read. The difference between the two readings is published "
         "rather than assumed away.",
         "Get a written answer from the county assessor, and have counsel confirm the reading."),
    ]
    # Each row points only at the official source that actually bears on it. A row with no
    # matching official source says so, and links to the register, rather than borrowing a
    # publisher that does not cover the figure.
    UV_WHERE = {
        "Property A market value, November 2026": [],
        "Property B market value, November 2026": [],
        "Both assessment rolls and tax bills": ["boe_lta26002"],
        "Property A ad valorem rate": [],
        "Property B ad valorem rate": [],
        "Property A water": [],
        "Property A electricity, net of solar": ["cpuc_nem"],
        "Property B water": [],
        "Property B electricity": [],
        "Insurance on both properties": ["cdi_homeowners_avg", "cdi_df_rental", "naic_hmr_2023", "cdi_fairplan"],
        "Whether either building is encumbered at the transfer": ["uscode1701j3", "irs_basis"],
        "Maintenance on both properties": [],
        "Property B rent": [],
        "The inherited cash amount": [],
        "City transfer tax reduction proposal": [],
        "City documentary transfer tax on a sale of Property A": ["rtc11911"],
        "Commission, escrow and title as a share of the sale price": [],
        "Property A market rent, and therefore the imputed-rent credit": ["hud_fmr"],
        "Parcel tax on Property B approved November 2026": [],
        "The Proposition 19 clawback on the live-then-let path": ["rtc63_2_eligibility", "boe_lta26026"],
        "Combined recapture rate, corrected from 41.1% to 42.1%": ["irs_tc409", "irs_tc559", "ftb_cg", "ftb_rates", "ftb_rates_2026"],
        "Mixed paths and the distributions behind the headline": ["fred_casthpi", "fred_cpi"],
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
         "They are published with all precincts partially reporting and are not certified until 11 December 2026. Proposition 3 is treated as approved (60.8% yes on unofficial results as of 16 November 2026, 7:12 p.m.) because it changes the tax rate on a sale, but the result must be confirmed at certification."),
        ("Combined tax rates are added, not interacted",
         "State and federal rates are added and no federal deduction is taken for state tax paid. That overstates the tax on a sale and therefore understates the case for selling, which is the conservative direction."),
        ("The housing value of living in the home is priced, not added",
         f"The living and letting paths bear their property tax and running costs in the terminal-value tables, "
         f"but are not credited with the housing they provide, and the sell paths are not charged for housing elsewhere. "
         f"The housing-value row prices the difference instead: on the 2045 baseline it is about "
         f"{m(next(p for p in MODEL['paths'] if p['inherit_year'] == 2045)['housing_value_needed'])} a year, a level "
         f"nominal amount. An earlier edition printed a figure about six times larger, because it used the "
         f"present-value form of the annuity on a future-value gap; that is corrected. The what-if page now "
         f"carries stated-level imputed-rent cases for the living path as lever 3: those levels are scenarios, "
         f"the imputed-rent input itself is empty, and the published baseline therefore credits nothing and "
         f"does not move."),
        ("Depreciation follows a simple rule",
         "80% of value treated as improvements, straight line over 27.5 years, capped at the building's depreciable amount. Land is not depreciated. Real cost segregation would differ."),
        ("A new loan is not modelled, borrowing against the house is",
         "Borrowing to take the cash out while keeping the home was an omission until 17 November 2026 and is "
         "now a priced path of its own, with its own engine and page (keep-and-borrow.html): three "
         "loan-to-value rungs at the published 2026 mortgage averages, an interest-only line at the published "
         "prime rate, and the hurdle return each rung has to beat. What remains unmodelled is the rest of the "
         "list - a 1031 exchange, an instalment sale, and gifting - each on the questions page. A loan already "
         "registered against either building at the date of death is a separate gap: nothing in the record says "
         "whether either is encumbered, so the what-if page prices that per $1,000 a month of payment instead "
         "of guessing at a balance."),
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
        ("Both properties are projected with the same state-level house price index",
         "The two metropolitan-area FHFA/FRED series were withdrawn from the published edition because the index publisher's own metadata crosswalks the placeholders to their metropolitan areas (audit finding, remediated 15 November 2026). Both placeholders now grow with the California state-level all-transactions index, which hides metropolitan differences and slightly understates the local boom years the old metro series showed. The recommendation does not depend on that precision; the state record still puts the break-even house growth far above what the record supports."),
        ("Jurisdiction names and their official pages are withheld from the public site",
         "The county and city of the two properties are not named or linked anywhere on the public site, because they identify the properties. Rows that were sourced to a county or city page are registered on this page instead. The public policy figures those pages carried stay, because they are law rather than property data, but a reader combining several of them could infer the jurisdiction; removing them entirely would end the rent, transfer-tax and rate analysis and is the owner's decision. The two metro-area house-price series are withdrawn for the same reason; the published record now uses the state-level California index, whose publisher metadata names no smaller geography."),
        ("Insurance above the insurer-of-last-resort cap",
         "The California FAIR Plan caps a residential dwelling at $3,000,000 combined (official CDI figure). Property A's owner-estimated value is $3,100,000 and is itself unverified, so no coverage conclusion follows from the two figures alone. If standard-market cover cannot be placed for either building, cover above the cap would be needed, its cost is unknown until quoted, and no premium for either building appears on this site."),
        ("The dated equity-entry backtest uses an academic return series",
         "An earlier edition had only the synthetic -40%, +25%, +10% sequence because no verified total-return series was in the repository. The Black Swan page now also backtests the realized 1929, 2000 and 2008 sequences - S&P 500 total return with dividends and the 3-month Treasury bill, from the NYU Stern (Damodaran) table - gross of taxes, costs and fees, with entry at the start of the entry year, so it is not a day-level replay. The synthetic stress remains beside it; treat the backtest as sequencing evidence, not a forecast."),
    ]
    # Each caveat links only to the official source that bears on it; a caveat that is a planning
    # statement rather than a rule says so and links to the register.
    CAV_WHERE = {
        "The ad valorem rate for Property A is not identifiable from the data": ["boe_lta26002"],
        "Fixed charges are projected at the inflation rate": ["bls_cpi"],
        "The November 2026 California election results are unofficial": ["sos_results", "voterguide_p3"],
        "Combined tax rates are added, not interacted": ["irs_tc409", "ftb_cg"],
        "The housing value of living in the home is priced, not added": [],
        "Depreciation follows a simple rule": ["irs_p527"],
        "A new loan is not modelled, borrowing against the house is": ["fred_mortgage", "fred_prime"],
        "The inheritance year is a range, not a date": [],
        "The property tax lesser-of rule is modelled only under the drawn inflation paths": ["rtc51", "boe_pub29", "fred_cpi"],
        "The Proposition 19 shelter path after 2027 is a projection": ["boe_lta25009"],
        "A sheltered base is assumed to survive a later move-out": ["rtc63_2_eligibility", "boe_prop19"],
        "Every reassessment figure is conditional on the parent-and-child relationship": ["rtc63_2_eligibility"],
        "The dated equity-entry backtest uses an academic return series": ["damodaran_histret", "fedhist_1929", "fedhist_greatrecession"],
        "Both properties are projected with the same state-level house price index": ["fred_casthpi"],
        "Insurance above the insurer-of-last-resort cap": ["cdi_fairplan"],
        "Jurisdiction names and their official pages are withheld from the public site": [],
    }
    assert set(CAV_WHERE) == {a for a, _ in caveats}, "every caveat needs a source decision"
    cav_rows = [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td>"
                + src_cell(CAV_WHERE[a], "Related sources")
                for a, b in caveats]

    audit = [
        ("The repository contains more than the published site",
         "The published site is the twenty-two pages in the repository root plus one stylesheet. What is not published is the build and verification code in scripts/, the data files in assets/data/, the source ledger, this page's own register, the README, the executive summary and a very large coordination board.",
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
        ("A location crosswalk existed on the live site, and was remediated on 15 November 2026",
         "An audit on 14 November 2026 found that the black-swan and economy pages linked two FHFA/FRED metropolitan-area house-price series whose publisher metadata identified the metropolitan areas, creating a crosswalk from the placeholders to their metros; the automated privacy gate could not see it because it does not read remote pages. Both placeholders now grow with the California state-level index, the metropolitan links, their series identifiers and metro phrasing are withdrawn from the published edition, and the privacy gate now rejects the identifiers and metro phrasing so the crosswalk cannot return silently.",
         "The withdrawn identifiers and earlier figures remain in Git history and pull-request diffs; removing them is the owner's history decision. An owner-runnable scrub kit is in scripts/history_scrub.py."),
        ("Property A water and sewer figures withdrawn for privacy",
         "Earlier editions linked a water utility's and a sewer district's web addresses, whose names identified the area of Property A. They were visible on the public pages and are now withdrawn. The owner's water estimate stays in the costs table, marked unverified; the parcel's own bill is the source for the provider and the charges.",
         "Earlier editions and their Git history still contain those links. The privacy scanner now checks web addresses for the area's names, so this cannot recur silently."),
        ("Pull request records",
         "PRs 62 and 70 were merged. PRs 65 and 66 recorded a live privacy-publication blocker on 12 November 2026; the blocker they describe, the legacy Pages route serving the whole repository, was closed by the restored configuration guard and audited live. Both were closed as superseded on 13 November 2026 with an explanatory comment, not silently.",
         "The coordination board records the full disposition. Nothing on this site depends on them."),
        ("The site is published from the repository root by Jekyll",
         "The GitHub Pages source is set to the main branch at the repository root, with a configuration file excluding everything outside the published allowlist. A separate workflow also builds an allowlisted artifact.",
         "The publishing route should be confirmed live after every change. The exclusion list is the control that keeps the rest of the repository out of the site.",
         ["gh_pages_docs"]),
        ("Verification is a build-time check, not a legal review",
         "The verifier checks that every published table row carries a source link, that no forbidden identifier appears, and that the build is reproducible.",
         "It cannot check whether a legal reading is correct. That needs a professional."),
        ("Form 706 filing date: verified 15 November 2026",
         "The site gives nine months after death for Form 706 and an automatic six-month extension on Form 4768. An earlier pass flagged the nine-month rule as not re-read. The IRS page 'Filing estate and gift tax returns' was read on the publisher's domain on 15 November 2026 and states that the estate tax return is due nine months after the date of death, with a six-month extension available if requested before the due date and the estimated tax is paid. The rule is verified; the flag is closed.",
         "None from the date itself. The extension of time to pay is separate and discretionary; Part III of Form 4768 requests it.",
         ["irs_filing_eg", "irs_i706", "irs_i4768"]),
        ("Two briefing pages were listed twice in the menu; one has been retired",
         "The one-page Attorney & CPA brief appeared under two labels in the menu. The print-styled brief is kept. The duplicate route is retired and returns a content-free withdrawal notice on the packaged artifact, and a 404 on the Jekyll root publisher.",
         "The menu shows one brief. Nothing in the substance of the brief changed."),
        ("The one-page brief has been measured but not seen",
         "No browser is available in the build environment, so the printed pagination still has not been looked at. What was done instead is a measurement: the print geometry is read out of the stylesheet the brief is printed with and the content is measured against it. The brief as published before this check measured at 128% of a sheet and would have run onto a second page while claiming to be one page; it now measures at 96%. The measurement is a model of a browser, not a browser, and the build fails if it ever exceeds a sheet again.",
         "Open the brief in a browser, print it to PDF, and check that it is one page and that the type is legible, before handing it to an adviser."),
        ("A personal e-mail address appears in commit metadata",
         "Git stores an author address with every commit. Earlier commits (83 of them) carry a personal e-mail address rather than the GitHub no-reply address now in use. It is not on any published page.",
         "Removing it from history needs a rewrite, which is the owner's decision. The runbook at scripts/history_scrub.sh covers the rewrite steps, including an author-address rewrite. For new commits, the account setting that keeps the address private is the owner's to change."),
        ("Pre-rounding history scrub is prepared as a runbook, not run",
         "scripts/history_scrub.sh audits the whole history for the identifier classes the privacy scanner guards and for candidate unrounded figures (found outside the repository, never written to the tree), and can run a git-filter-repo rewrite. The audit on 15 November 2026 found the identifier tokens still present in the visible history and one candidate figure. The scanner's own patterns were split into string fragments so the file text no longer carries any identifier.",
         "The rewrite itself rewrites every ref and needs a force-push to main, so it is the owner's to run or authorise. Until then, earlier commits, pull-request diffs and forks keep what they hold. The runbook carries the full post-rewrite checklist."),
        ("The section 17043 sensitivity table printed percentages ten times too large; corrected 17 November 2026",
         "The taxes page passed numbers that were already percentages (20.0, 3.8, 12.3, 1.0, 37.1 and 36.1) to a formatter that multiplies by 100, so the rate table and the sentences beside it printed 2000.0%, 380.0%, 1230.0%, 100.0%, 3710.0%, 3610.0% and 1330.0% where 20.0%, 3.8%, 12.3%, 1.0%, 37.1%, 36.1% and 13.3% belong. Nine call sites in the build script were corrected on 17 November 2026 and the page was rebuilt.",
         "None on the numbers: the model's own rates and every dollar figure computed from them were always right, and no projection or recommendation changed. Only the printed percentages were wrong, so a reader of the earlier edition could have misread the top combined rate as 3710% instead of 37.1%.",
         ["rtc17043", "ftb_540_instructions_2025", "ftb_rates", "ftb_rates_2026"]),
    ]
    # No blanket fallback: an audit row with no stated sources is a repository finding
    # with no official publisher, and it says so on the register instead of borrowing the
    # Proposition 19 letter and the IRS estate page (the second half of the gap logged
    # open by arena/1c788435-tino3).
    aud_rows = [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td><td>{esc(c)}</td>"
                + src_cell(rest[0] if rest else [], "Related sources")
                for a, b, c, *rest in audit]

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
        + roll_audit_section()
        + assumption_register()
        + '<h2>Modelling caveats</h2>'
        + table("Shortcuts that matter", ["Caveat", "What it means", "Source"], cav_rows)
        + '<h2>Repository audit</h2>'
        + table("What was found when the repository was reviewed",
                ["Finding", "Detail", "Residual risk", "Source"], aud_rows)
        + print_budget_section()
        + recheck_section()
        + recheck_17nov_section()
        + history_audit_section()
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
<p>There are {len(SRC_DOC['sources'])} sources. The date in the last column is when the entry was last read on the
publisher's own domain. The ledger was opened on 13 November 2026 and has since been re-read in stages, most
recently on 17 November 2026, when the figures listed in the
<a href="review.html#recheck-2">17 November recheck table</a> were read from the documents themselves rather than
from any summary of them; the <a href="review.html#recheck">16 November recheck table</a> records the previous
pass. The "supports" column says exactly what
the source is cited for; the "limits" column says what it does not cover. Sources are cited only for what they
actually state, and an official publisher whose name or address would identify one of the two properties is
deliberately not linked here: it is recorded on the register instead.</p>""")
        + table("Source ledger", ["ID", "Publisher", "Document", "What it supports",
                                  "Limits", "How it was checked"], rows)
        + callout("limit", "What this ledger does not do", """
<ul>
<li>It does not reproduce the rate schedules, thresholds or forms. Those change; read the linked document.</li>
<li>It does not cover local ordinances and local measures affecting the two properties, whose official publishers are withheld because naming them would identify the buildings; those are recorded on the register with the date they were read. Nor does it verify which rules apply to which building.</li>
<li>It contains no paid, paywalled or secondary source. Everything here is an official publisher or an official government site.</li>
<li>It was checked on one date. Statutory sections are amended; letters to assessors are superseded; election results are certified after the fact.</li>
</ul>""")
    )


# ------------------------------------------------------------------ timeline --
# ------------------------------------------------------------------- glossary --
def page_glossary() -> str:
    terms = [
        ("Assessed value", "The value the county assessor places on the property for tax bills. Under Proposition 13 it can rise only with inflation (capped at 2% a year) until a change of ownership, when it is reset to market value.",
         ["boe_pub29", "rtc51"]),
        ("Base year value", "The assessed value assigned when the property was acquired or built; the starting point for the 2% annual inflation cap.", ["boe_pub29"]),
        ("Basis step-up", "When someone inherits an asset, its income-tax cost basis is reset to its value at the date of death. A sale soon after inheritance therefore produces little or no capital gains tax.", ["irs_basis"]),
        ("Change in ownership", "A transfer that generally triggers property-tax reassessment unless a statutory exclusion applies; inheritance alone does not establish eligibility for Proposition 19 relief.", ["rtc63_2_eligibility", "boe_pub800_9"]),
        ("Documentary transfer tax", "A county tax on recording a deed that changes ownership. Transfers by reason of death or gift, outright or in trust, are exempt.", ["rtc11930", "rtc11911"]),
        ("Estate tax", "Federal transfer tax calculated on a decedent's taxable estate. It is distinct from income tax owed by a beneficiary and from a state inheritance tax.", ["irs_estate", "irs_i706"]),
        ("Estate tax exclusion", "The amount of an estate that can pass free of federal estate tax. California has no estate tax. The 2026 figure is modelled in scenario bands on the estate page.", ["irs_estate", "irs_2027", "sco_estate", "ftb_inheritance"]),
        ("Fair market value", "A valuation concept used for federal basis purposes. The date-of-death value should be substantiated by an appropriate appraisal or other acceptable evidence.", ["irs_basis"]),
        ("Section 121 exclusion", "Up to $250,000 ($500,000 for a couple) of gain on the sale of a principal residence can be excluded from federal income tax, subject to ownership and use tests.", ["irs_p523"]),
        ("Depreciation recapture", "Depreciation claimed while a property was rented is taxed back when it is sold, at up to 25% federally plus state tax.", ["irs_tc409", "ftb_cg"]),
        ("Net investment income tax (NIIT)", "A 3.8% federal tax on investment income for higher earners, layered on top of capital gains tax.", ["irs_tc559"]),
        ("Portability", "A surviving spouse may be able to use a deceased spouse's unused federal estate-tax exclusion if the required estate-tax return is timely and correctly filed.", ["irs_estate", "irs_i706"]),
        ("Proposition 13", "California's rule that property tax is 1% of assessed value plus voter-approved bonds, with assessed value rising no more than 2% a year until ownership changes.", ["boe_pub29", "rtc51"]),
        ("Proposition 19", "The rule that the parent-child property-tax exclusion now applies only when the child makes the inherited home their principal residence, and caps the new assessed value at the prior factored base year value plus an amount adjusted every two years ($1,044,586 for a transfer between 16 February 2025 and 15 February 2027, next adjusted 16 February 2027). It shelters only the value below that ceiling, and since 1 January 2021 it has not covered rental property at all: the pre-2021 exclusion for $1,000,000 of other property was removed.", ["rtc63_2", "boe_prop19", "boe_lta25009"]),
        ("Proposition 19 parent-child exclusion", "A conditional California change-in-ownership exclusion, limited by statute and generally requiring the eligible transferee to use the transferred home as a principal residence and file a claim.", ["rtc63_2_eligibility", "boe_prop19"]),
        ("Reinvestment risk", "The risk that sale proceeds must be reinvested at lower returns than expected - for example, inheriting just before a stock-market crash and buying equities at the top. The phased-investing path on the black-swan page tests parking proceeds in short-term Treasuries for 24-36 months before buying stocks, with a synthetic stress and a dated backtest of the realized 1929, 2000 and 2008 returns.", ["fred_gs10", "damodaran_histret"]),
        ("Phased investing", "Selling the inherited home, holding the proceeds in 3-month to 2-year Treasury bills for 24-36 months, then buying equities in equal monthly pieces over the following 12 months. It softens the risk of entering the stock market at a 1929- or 2008-style peak; the black-swan page tests it synthetically and against realized returns.", ["fred_gs10", "damodaran_histret"]),
        ("Cash-out refinance", "Replacing the existing mortgage on a property with a larger one and taking the difference in cash. It converts equity into spendable money without a sale, so it triggers no capital-gains tax and, under Revenue and Taxation Code section 62(c)(1), no property-tax reassessment. It does trigger a payment: the keep-and-borrow page prices that payment against what the borrowed money would earn.",
         ["rtc62", "fred_mortgage"]),
        ("Home equity line of credit (HELOC)", "A revolving borrowings facility secured on the home, usually priced at the published prime rate plus a lender's margin and often interest-only while drawing. Interest only means the balance is still owing in full at the horizon, which is why the keep-and-borrow page prices it as a different animal from an amortising loan.",
         ["fred_prime", "irs_p936"]),
        ("Loan-to-value, and why the rung is stated", "The share of the home's value taken as a loan. No official source publishes what a lender would advance against this property, so the site shows 40, 60 and 80 percent as stated scenarios, not as an offer or an underwriting answer.",
         []),
        ("Hurdle return, and negative carry", "The after-tax portfolio return at which borrowed money exactly pays for itself. Below it, borrowing loses value even though the cash arrives; the loss is the negative carry. It is the one number to check before a household borrows to invest.",
         ["fred_mortgage"]),
        ("Encumbrance", "A mortgage, deed of trust, tax lien, assessment lien or other claim registered against "
         "a property. Nothing in the record says whether either building here carries one, so the model runs both "
         "free and clear and the decision page states that as an assumption rather than a fact.",
         []),
        ("Due-on-sale clause", "A loan term letting a lender demand full repayment when the property is "
         "transferred. Federal law stops a lender exercising one on a transfer to a relative resulting from the "
         "borrower's death, or on a transfer where the borrower's children become owners, for a loan on fewer than "
         "five dwelling units. It limits acceleration; it does not decide who has to pay.",
         ["uscode1701j3"]),
        ("Amortisation", "The way a fixed-rate loan is paid off: each level monthly payment covers that month's "
         "interest and retires part of the principal, so the balance falls to zero at the end of the term. The "
         "keep-and-borrow case on the estate liquidity page prices a fully amortising 30-year fixed loan at the "
         "published mortgage average, which over a long horizon costs more than the interest-only carrying cost "
         "shown beside it, because the principal is retired rather than rolled forward.",
         ["fred_mortgage"]),
        ("Dwelling fire and landlord forms", "The policy family a rental house or a building of up to four units is "
         "usually written on, as distinct from the owner-occupied homeowners multi-peril form. The state "
         "insurance department publishes a statewide average written premium for each form, and the two averages "
         "differ by a factor of about three, which is why one number cannot cover both buildings here.",
         ["cdi_df_rental", "cdi_homeowners_avg"]),
        ("Underpayment rate", "The interest rate charged on tax that is paid after its due date: the federal short-term rate plus three percentage points, set every quarter by the IRS and compounded daily. It applies to unpaid estate tax from the original due date, whether or not an extension of time to file was granted.", ["irs_interest", "uscode6621", "uscode6622"]),
        ("Extension of time to pay (section 6161)", "A discretionary extension, granted one year at a time for up to ten years, and only for the amount of the estate's actual cash shortage. It is not an extension of time to file, and interest runs from the original due date in any case.", ["irs_i4768", "uscode6601"]),
        ("Section 6166 instalment election", "A deferral of estate tax for an estate that is largely an interest in a closely held business: payment may be deferred for five years and then made in up to ten equal annual instalments, with interest at 2% on a limited portion and at 45% of the underpayment rate on the rest. It requires the business interest to exceed 35% of the adjusted gross estate, so a home occupied as a personal residence does not qualify on the face of the statute.", ["uscode6166", "uscode6601"]),
        ("Break-even", "The rent, return or house-growth rate at which one path ties another. Below it, selling and investing wins; above it, keeping the home can win.", []),
        ("Horizon", "The 30 years after the inheritance over which each path is valued.", []),
        ("Outflow", "The total property tax and carrying cost paid over the horizon on a path (rental paths also credit rent received).", []),
    ]
    rows = []
    for term, definition, srcs in terms:
        if srcs:
            links = "<br>".join(slink(s) for s in srcs)
        else:
            links = '<span class="blank">plain-language term; not from an official source</span> <a class="src" href="review.html#register">Logged on the register</a>'
        src_td = '<td class="src-cell">' + links + '</td>'
        rows.append(f"<td><strong>{esc(term)}</strong></td><td>{esc(definition)}</td>" + src_td)
    return (
        privacy_banner()
        + table("Glossary of terms", ["Term", "Plain-language meaning", "Source"], rows,
              note="Plain-language definitions, not legal or tax definitions. Where a term is anchored to an official source it is linked; terms marked " + chr(34) + "plain-language term" + chr(34) + " are stated for readability and are not cited to a statute.")
    )


# -------------------------------------------------- adviser briefing sheet --
def page_briefing() -> str:
    p45 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2045)
    value = p45["value_at_death"]
    cash_net = p45["paths"]["sell_equities"]["sale"]["net"]
    summary = f"""
<div class="brief-toolbar"><p><strong>Print / save as PDF:</strong> use your browser's Print command. This sheet is formatted for one letter-size page; its printed length is measured at build time and is reported on the <a href="review.html#print-budget">print budget</a>, which also says what that measurement does and does not establish.</p><p><strong>One-page printable Attorney &amp; CPA Briefing Sheet:</strong> this page is the single briefing sheet; the duplicate briefing-sheet.html was withdrawn on 15 November 2026.</p></div>
<p class="brief-confidential"><strong>Planning brief — placeholders only; no personal names, addresses, parcel IDs, trust terms or account figures.</strong></p>
<div class="brief-grid">
<section><h2>Decision in front of the family</h2>
<p>Property A is expected to pass through a trust around 2040–2050; Property B is already owned by the heir, with two rented units and one available. Do not treat the inherited home as already owned, or assume Property B rent is displaced by living there.</p>
<p>Current model direction: sell Property A soon after inheritance unless the heir genuinely wants to live in it. Conditional, not advice, and dependent on eligibility, title, basis, carrying costs, market rent and updated law. A 2045 illustration: inherited-home value {m(value)}, after-sale proceeds before reinvestment {m(cash_net)}. Model outputs, not appraisals.</p>
</section>
<section><h2>First questions for counsel and tax adviser</h2>
<ol>
<li>Does the trust own the property, and is the transferor-to-beneficiary relationship eligible for the parent-child Proposition 19 exclusion? If not, full reassessment is assumed. {slink('rtc63_2_eligibility')} {slink('boe_prop19')}</li>
<li>What are the trust's distribution, sale, occupancy, debt and trustee powers? Confirm the deed, trust amendments, successor-trustee process and authority to sell.</li>
<li>What is the date-of-death basis and appraisal standard, and the land/building allocation? What is the cash estate, prior taxable gifts, marital portability and Form 706 position? {slink('irs_basis')} {slink('irs_estate')} {slink('irs_i706')}</li>
<li>Which home is the heir's principal residence after transfer, and can the occupancy and claim deadlines be met? Confirm eligibility and filing sequence with the assessor. {slink('boe_lta25009')}</li>
</ol>
</section>
<section><h2>Options and material risks</h2>
<ul><li><strong>Live in Property A:</strong> reassessment shelter only if eligible and the occupancy requirements are met; higher concentration and maintenance exposure.</li><li><strong>Rent Property A:</strong> full reassessment may apply; income, vacancy, repairs, landlord rules and depreciation and recapture need a CPA-grade model.</li><li><strong>Sell and reinvest:</strong> the basis step-up may limit immediate gain, but confirm sale costs and tax. Published transfer tax and recording fees come to {m(MIXED['fees_example']['published_total'])} on a {m(MIXED['fees_example']['price'])} sale, about {MIXED['fees_example']['published_share_of_modelled']}% of the modelled 5.5% selling cost, and the $75 instrument fee does not apply to a sale paying the transfer tax. Reinvestment risk remains: the Black Swan page models 24 and 36-month Treasury parking and phased equity entry on one canonical monthly path, with a synthetic stress test and a dated backtest of 1929, 2000 and 2008. Reinvestment yield may decline at maturity.</li><li><strong>Property B</strong> stays an independent owned asset: include its net operating costs, insurance, rent rules and the available unit in household liquidity planning.</li><li><strong>If the taxable estate may exceed the federal exclusion:</strong> the tax is {pcf(LIQ['clock']['estate_tax_rate'], 0)} of the excess and is due in cash {LIQ['clock']['due_months_after_death']} months after death. An extension to file is not an extension to pay; interest runs from the due date at the federal short-term rate plus three points, compounded daily. Ask whether the section 6166 instalment election is available. <a href='liquidity.html'>Estate liquidity page</a>. {slink('irs_i4768')} {slink('uscode6621')}</li></ul>
</section>
<section><h2>Known / unknown before choosing</h2>
<p><strong>Known from the supplied brief, not independently verified:</strong> owner-reported values, Property B rent and utilities, Property A water and solar estimates, the historic tax rolls. <strong>Unknown:</strong> deed and trust terms, relationship eligibility, insurance quotes, registered liens, property-specific utilities, repairs and capital work, tax-rate areas, Property A market rent, selling costs, the size of the taxable estate, future law.</p>
<p><strong>Two assumptions are banded and tested rather than left as round numbers.</strong> Insurance: each building carries a band floored by the published statewide average for the matching policy form ($1,074 owner-occupied, $519 landlord, newest published year 2017); the whole band moves the thirty-year living figure by under 1% of the gap to selling, so a quote sizes the bill but does not choose the path. Encumbrance: nothing was reported either way, so both are modelled free and clear; $1,000 a month of debt service costs a keeping path about $1,311,830 and the sale path nothing. Counsel's question is what is owed, not whether the transfer triggers repayment: on a building of fewer than five units federal law does not let a lender accelerate because the property passed to a relative at death.</p>
<p>Obtain certified tax bills and assessor records, a title report, the trust, a date-of-death appraisal, insurer quotes for owner-occupied and rental use, utility bills, a property-condition inspection and a local rent opinion. Do not publish source documents or identifiers.</p>
</section>
<section><h2>Mixed paths and the clawback</h2>
<p>Living there for a period then selling is the closest mixed path, and still ends behind an immediate sale by {m(next(x for x in MIXED['paths'] if x['occupy_years'] == 5 and x['mode'] == 'sell')['gap_vs_sell_now'])} after five years. Moving out after claiming the Proposition 19 exclusion removes it: section 63.2(a)(1)(C) enrols the change-of-ownership base year value, costing about {m(MIXED['clawback']['difference'])} of extra property tax over thirty years on the live-then-let path. Both readings are published; ask counsel which applies.</p></section>
<section><h2>Timing / action sequence</h2>
<p>Before transfer: verify trust and deed, relationship eligibility, estate liquidity, insurance. At death: secure the property, contact trustee, assessor and insurer, obtain the date-of-death valuation, inventory expenses, confirm the filing calendar. After transfer: have counsel and CPA calendar the assessor claim deadlines, income and estate returns, insurance endorsements and rental notices; model live, rent and sell with actual quotes before signing or distributing proceeds. Exact dates depend on the transfer and filing facts.</p>
</section>
<section class="brief-glossary"><h2>Glossary</h2>
<p><strong>Basis step-up</strong>: generally resets inherited property tax basis to the date-of-death value, subject to exceptions. <strong>Prop 19 exclusion</strong>: conditional California parent-child reassessment exclusion, subject to statutory value and occupancy rules. <strong>Estate tax</strong>: federal tax on the taxable estate, not a California inheritance tax. <strong>Reinvestment risk</strong>: short-term Treasury proceeds may earn less at maturity. <strong>Encumbrance</strong>: a mortgage, deed of trust or lien; unknown for both buildings, so both are modelled free and clear, with the limit on acceleration set by 12 U.S.C. section 1701j-3(d).</p>
</section>
</div>
<p class="brief-footer">For attorney / CPA discussion only. Laws and projections may change before 2040–2050. Sources and full assumptions: <a href="sources.html">source ledger</a>, <a href="questions.html">question register</a>, <a href="review.html">unverified items</a>, <a href="black-swan.html">phased-investing stress test</a>, <a href="liquidity.html">estate liquidity</a>. No legal, tax or investment advice.</p>
"""
    return summary


# ------------------------------------------------------------ timeline page --
def policy_section() -> str:
    """The written investing policy, which has to exist before the money does.

    The owner's instruction was to write the policy down before the money
    arrives, because a policy written after a sale is a rationalisation of
    whatever was already bought. This is a template of the questions a policy
    has to answer, not a policy: the site cannot write the household's
    tolerance, and any figure it invented for one would be an opinion dressed
    as a rule. Every line is left for the household or its adviser.

    The dates are the household's own gates, which is why they are proposed
    rather than sourced: no statute imposes them.
    """
    rows = []
    for when, item, why, gate in [
        ("Before the sale closes",
         "Target asset allocation, in writing: the percentage in cash, bonds and equities, and the "
         "rebalancing band that will force an adjustment.",
         "The phased entry needs a destination before it starts. Without one, the parking period becomes "
         "a market-timing decision made one month at a time.",
         "Gate RG-5"),
        ("Before the sale closes",
         "The maximum acceptable one-year loss, in dollars, and what the household would do if it "
         "happened.",
         "A policy that has never been tested against a number is a wish. The black swan page shows what "
         "the same portfolios did in 1929, 2000, 2008 and 2020.",
         "Gate RG-5"),
        ("Before the sale closes",
         "Who decides, and who is told. One named decision-maker, one named reviewer, and the date the "
         "review happens.",
         "Two people discovering they disagree after the money has been invested is the most common "
         "failure in household portfolios.",
         "Gate RG-5"),
        ("Before the sale closes",
         "The spending rule: how much may be drawn each year, and what happens in a year when the "
         "portfolio falls.",
         "A draw expressed as a percentage of the portfolio moves with the market; a fixed dollar draw "
         "does not. Choosing which one was meant is easier before the money is spent.",
         "Gate RG-5"),
        ("Before the sale closes",
         "The liquidity floor: how many months of household costs stay in cash or short Treasuries and "
         "are never invested.",
         "This is what stops a bad month becoming a forced sale. The phased plan parks in short "
         "Treasuries for 24 to 36 months, which is longer than the floor needs to be.",
         "Gate RG-5"),
        ("Before the sale closes",
         "The tax constraints: the holding period the household wants to reach, and any loss or gain "
         "that must be realised in a particular year.",
         "Basis and holding period are the only parts of the plan the tax code fixes. Changing the plan "
         "later can move a gain into a worse year.",
         "Gate RG-5"),
        ("At the annual re-run",
         "The review date, and the specific evidence that would justify a change to the allocation.",
         "Without a written trigger, every market move becomes a reason to revisit, which is the same "
         "thing as having no policy.",
         "Gate RG-3"),
    ]:
        rows.append(f"<td>{esc(when)}</td><td><strong>{esc(item)}</strong></td><td>{esc(why)}</td>"
                    f'<td><a href="precommit.html">{esc(gate)}</a></td>'
                    + method_cell("precommit.html", "Household rule, not a figure", sources=[]))
    tbl = table(
        "The written investing policy: what has to be decided before the money arrives",
        ["When it is due", "What the policy must answer", "Why it cannot wait", "Gate", "Status"], rows,
        note="A template, not a policy. Nothing in this table is filled in, because a risk tolerance "
             "invented by a website would be an opinion published as a rule. The gates are the "
             "household's own; no statute imposes them.")
    return ('<h2 id="policy">The written investing policy, before the money arrives</h2>'
            + callout("flag", "Write it down before the sale, not after", f"""
<p>The recommendation on this site is to sell and invest. That creates a second decision the brief did not
ask for but cannot avoid: what the proceeds are invested <em>in</em>, and by what rule. A policy written
after the sale is a description of whatever was bought, not a constraint on it. The six lines below are the
questions the policy has to answer, and they are deliberately left blank.</p>
<p>The phased plan on the <a href="projections.html">projections page</a> parks the proceeds in short
Treasuries for 24 to 36 months and phases into equities over the following 12. That plan is a schedule. It
is not a policy, and it does not answer any of the lines below.</p>""")
            + tbl)


def page_timeline() -> str:
    """Every dated step in order. Each row names its official source or is not on the page."""
    rows_spec = [
        ("Within 60 days after the event requiring the notice",
         "The trustee serves the statutory notification on each beneficiary of the irrevocable trust or portion "
         "and each heir of the deceased settlor, at their last known address. The 60 days run from the event - or "
         "from when the trustee becomes aware of a person entitled to notice who was not known at the event, or "
         "from when a new trustee commences to serve if the office was vacant. No copy is owed to a beneficiary or "
         "heir who cannot be located after reasonable diligence or is unknown to the trustee.",
         "The trustee.", ["prob16061_7"]),
        ("At the transfer of Property A by reason of death, in trust",
         "Exempt from the documentary transfer tax, whether the transfer is outright or in trust. The exemption is "
         "claimed at recording. No city transfer tax applies to Property A.",
         "The trustee, at recording.", ["rtc11930", "rtc11930_trust"]),
        ("Within 150 days after death",
         "Change in ownership statement for a transfer on death, under RTC section 480(b). If the estate is "
         "probated, the statement is filed with the inventory and appraisal instead. The statute also sets the "
         "penalty for not answering the assessor: whichever is greater of $100 or 10% of the tax on the new base "
         "year value, capped at $5,000, if a written request from the assessor goes unanswered for 90 days.",
         "The successor or the trustee, on the assessor's form.", ["rtc480", "boe_pub800_9"]),
        ("Within 9 months after death, if a federal estate tax return is required",
         "Form 706 is due. Filing Form 4768 by that date gives an automatic six-month extension of the filing "
         "date. Part III of the same form is a separate request for more time to pay.",
         "The executor. The portability election is made on this return if the gross estate is above the filing "
         "threshold. An estate not otherwise required to file can still elect portability with a simplified late "
         "return under Rev. Proc. 2022-32, within five years of death.", ["irs_i706", "irs_i4768", "rp_2022_32"]),
        ("Within 1 year after the transfer, if the exclusion is claimed",
         "Occupy the house as the principal residence, and file the homeowners' exemption.",
         "The heir.", ["rtc63_2", "boe_lta26026", "boe_prop19"]),
        ("Within 3 years after the transfer, or before any transfer to someone else",
         "File the Proposition 19 exclusion claim. The claim is not a public document.",
         "The heir, on the assessor's claim form.", ["rtc63_2"]),
        ("After a change in ownership",
         "If the exclusion is not claimed, the property is reassessed to full value and a supplemental bill "
         "may follow for the part of the year already gone.",
         "The county assessor.", ["boe_pub29"]),
        ("Each year, on the state's secured-roll calendar",
         "Secured bills are mailed in October. First installment due 1 November, penalty date 10 December. "
         "Second installment due 1 February, penalty date 10 April. Last day for the current year's taxes 30 June. "
         "A penalty date that falls on a weekend or county holiday moves to the next business day.",
         "The owner of record.", ["boe_pub29"]),
        ("10 December 2026",
         "Last day to pay the first installment of the 2026/27 secured bill without penalty, while the bill is "
         "still on the owner's record. Relevant to Property A only while it is held and before it is inherited.",
         "The owner of record.", ["boe_pub29"]),
        ("11 December 2026",
         "Certification of the November 2026 statewide results. The Secretary of State's unofficial results page "
         "states that results will be certified by 11 December 2026. Until then, every statewide measure "
         "shown on the law-watch page is unofficial.",
         "The Secretary of State certifies the results.", ["sos_results"]),
        ("16 February 2027",
         "The Proposition 19 $1 million amount is next adjusted, from the federal house price index, every other "
         "February 16. The new amount applies to transfers on or after this date. The letter this site relies on "
         "does not state the new amount, so the site does not state it either.",
         "The State Board of Equalization publishes the adjusted amount.", ["boe_lta25009"]),
    ]
    rows = []
    for when, what, who, ids in rows_spec:
        rows.append(f"<td>{esc(when)}</td><td>{esc(what)}</td><td>{esc(who)}</td>" + src_cell(ids, "Official source"))
    tl = table(
        "Deadlines in order",
        ["When", "What must happen", "Who", "Official source"], rows,
        note="Day 0 is the date of death, which is not yet known, so the clocks are shown from it. "
             "A row without an official source is not on this page. The state payment calendar applies to "
             "Property A only while it is held in the trust; after the transfer, the heir's own bills follow the "
             "same calendar. "
             "Every date here is a deadline to check, not advice on when to act.")
    return (
        eligibility_callout()
        + callout("answer", "The next dated item", """
<p>The first installment of the 2026/27 secured bill must be paid, or postmarked, by
<strong>10 December 2026</strong> to avoid penalties. That payment is an obligation only while Property A is still
held. Two other official dates also fall in the next year, and both are listed in the table below:
<strong>11 December 2026</strong>, the statewide certification that the law-watch figures depend on, and
<strong>16 February 2027</strong>, the next Proposition 19 adjustment. The February date sets the shelter amount for
transfers from that day; the 2040s figures on this site use a projected growth rate, because no later amount is
published yet. Everything else is measured from the date of death or the date of transfer.</p>""")
        + '<p class="lede">Read in order. Each row is a legal or tax clock, and each names the official text it comes from.</p>'
        + tl
        + callout("answer", "Which deadlines can move the answer",
"""<p>The three deadlines that can change the recommendation are: (1) whether the parent-child relationship is in place before the transfer, because without it the Proposition 19 shelter disappears; (2) the one-year homeowners' exemption and three-year exclusion-claim windows, because missing them costs the shelter; and (3) the nine-month estate-tax return, because portability is normally lost when no timely return is filed - although an estate not otherwise required to file can use the simplified late election of Rev. Proc. 2022-32 within five years of death. The estate page works entirely in anonymous scenario bands because the inherited cash amount is not published.</p>""")
        + '<h2 id="decision-calendar">The decision calendar, before the death</h2>'
        + callout("key", "Most of these tasks have no statute behind them, and that is the point", """
<p>Everything above is a legal clock that starts at a death. The clocks below start now, and they matter more,
because each one changes a number the decision depends on. None is triggered by a statute; each is triggered
by someone deciding to ask. They are listed with the latest sensible date and what the answer changes.</p>
<p>The dates are planning advice, not law, so they carry no official source. That is the honest status: a
timeline of your own actions cannot be "verified" against an official page, only against your own calendar.</p>""")
        + table("What to settle before the transfer, and what each answer moves",
                ["By when", "What to obtain", "From whom", "What it changes", "Status", "Register"],
                [
                    "<td>Now</td><td>Written confirmation of the parent-child relationship that Revenue and "
                    "Taxation Code section 63.2 requires, and the trust's beneficial-interest terms</td>"
                    "<td>The trustee and the estate attorney</td>"
                    "<td>Every Proposition 19 figure on this site. Without it the property is reassessed in full "
                    "and the case for selling is stronger.</td>"
                    '<td><span class="badge flag">Blocking</span></td>'
                     '<td><a class="src" href="review.html#register">Logged on the register</a></td>',

                    "<td>Now</td><td>The written investment policy for the sale proceeds, before any money "
                    "arrives</td><td>The heir and a fiduciary adviser</td>"
                    "<td>Whether the phased path has a rule to follow at all. A policy written after the money "
                    "lands is written by someone who already knows the market.</td>"
                    '<td><span class="badge flag">Blocking</span></td>'
                     '<td><a class="src" href="review.html#register">Logged on the register</a></td>',

                    "<td>Now</td><td>Whether portability matters: the total estate, prior taxable gifts and "
                    "the 706 history of the first spouse to die</td><td>The estate attorney and CPA</td>"
                    "<td>The estate-tax exposure band on the estate page, and whether a 706 is needed at all.</td>"
                    '<td><span class="badge unverified">Open</span></td>'
                     '<td><a class="src" href="review.html#register">Logged on the register</a></td>',

                    "<td>Before 2040</td><td>Three real insurance quotes for each property, and a rental policy "
                    "quote for Property B</td><td>Licensed brokers</td>"
                    "<td>The largest unverified cost input on both properties.</td>"
                    '<td><span class="badge unverified">Open</span></td>'
                     '<td><a class="src" href="review.html#register">Logged on the register</a></td>',

                    "<td>Before 2040</td><td>A written rental opinion for Property A and for the vacant unit "
                    "at Property B</td><td>Two local letting agents</td>"
                    "<td>Turns the letting paths from a floor into a comparison. Today they credit no rent at all.</td>"
                    '<td><span class="badge unverified">Open</span></td>'
                     '<td><a class="src" href="review.html#register">Logged on the register</a></td>',

                    "<td>Before 2040</td><td>The tax rate area and published rate for Property A; the current "
                    "rate book for Property B's district</td><td>The county assessor's published rate book</td>"
                    "<td>The ad valorem rate, which the bills themselves cannot identify.</td>"
                    '<td><span class="badge unverified">Open</span></td>'
                     '<td><a class="src" href="review.html#register">Logged on the register</a></td>',

                    "<td>Before 2040</td><td>A five-year maintenance and capital plan for both buildings, with "
                    "costs</td><td>A licensed contractor and an inspector</td>"
                    "<td>The maintenance percentage, currently a 0.5% and 0.75% assumption, and the size of the "
                    "first capital call after the transfer.</td>"
                    '<td><span class="badge unverified">Open</span></td>'
                     '<td><a class="src" href="review.html#register">Logged on the register</a></td>',

                    "<td>At death</td><td>A written valuation of Property A as of the date of death</td>"
                    "<td>A licensed appraiser</td>"
                    "<td>The income-tax basis, the estate-tax value and the Proposition 19 claim, all from one "
                    "document.</td>"
                    '<td><span class="badge flag">Deadline</span></td>'
                     '<td><a class="src" href="review.html#register">Logged on the register</a></td>',

                    "<td>Before any sale</td><td>A decision on whether a like-kind exchange is wanted, taken "
                    "with advice and before the property is marketed</td><td>The CPA and a qualified "
                    "intermediary</td>"
                    "<td>Once a sale closes the option is gone. It defers tax; it does not fix the property-tax "
                    "reassessment.</td>"
                    '<td><span class="badge flag">Deadline</span></td>'
                     '<td><a class="src" href="review.html#register">Logged on the register</a></td>',

                    "<td>Each year</td><td>A re-run of this model on updated inputs, and a check of the "
                    "law-watch page</td><td>The heir</td>"
                    "<td>Whether the recommendation has moved. Every figure here is a snapshot of 2026 law.</td>"
                    '<td><span class="badge assumption">Recurring</span></td>'
                     '<td><a class="src" href="review.html#register">Logged on the register</a></td>',
                ],
                note="The first two rows are labelled blocking because nothing below them can be decided without "
                     "them. The rest are open questions with a date attached. A row with no official source is a "
                     "task in the owner's calendar, not a legal requirement, and is marked as such rather than "
                     "given a fabricated citation.")
        + policy_section()        + callout("method", "Why the order matters", """
<ol>
<li>The trust notice (60 days) and the change-in-ownership statement (150 days) are the first two clocks after death.</li>
<li>The federal return, if one is needed, comes at nine months, and Form 4768 is the only automatic way to extend it. An extension of time to file is not an extension of time to pay: see the <a href="liquidity.html">estate liquidity page</a>.</li>
<li>The exclusion claim has a three-year window, but the occupancy and homeowners' exemption steps are one year.
Missing the one-year steps is the most expensive mistake that can be made on the timeline.</li>
</ol>""")
    )


# -------------------------------------------------------------- what-if page --
def page_what_if() -> str:
    """Link-driven what-if: each case is one row and every row is reachable from the list at the top."""
    paths = {x["inherit_year"]: x for x in MODEL["paths"]}
    p45 = paths[2045]
    sens = MODEL["sensitivity"]
    regs = MODEL["regimes"]
    KEYS = ["sell_equities", "sell_treasury", "live_in", "live_then_rent", "rent_out"]

    def lever_row(s, anchor):
        best = s["best"]
        cells = "".join(
            (f"<td class='best'>{m(s[k])}</td>" if k == best else f"<td>{m(s[k])}</td>")
            for k in ["sell_equities", "sell_treasury", "live_in", "rent_out"])
        return (f"<td><a id='{anchor}'></a>{pc(s['house_growth'], 1)}</td><td>{pc(s['equity_return'], 1)}</td>"
                + cells + f"<td><strong>{esc(PATH_LABELS[best])}</strong></td>"
                + method_cell("#method", "Model output", sources=["fred_casthpi", "fred_gs10", "damodaran_histret"]))

    lever_hdr = ["House growth", "Equity return", "Sell, equities", "Sell, Treasuries",
                 "Live in it", "Let it out", "Best path", "Basis"]

    by_house = [s for s in sens if s["equity_return"] == 7.0]
    by_house.sort(key=lambda s: s["house_growth"])
    by_equity = [s for s in sens if s["house_growth"] == 4.0]
    by_equity.sort(key=lambda s: s["equity_return"])
    lever1 = table(
        "Lever 1: change house growth, hold the equity return at 7.0%",
        lever_hdr, [lever_row(s, f"house-{s['house_growth']}") for s in by_house],
        note="Each row is one case. The case with 4.0% house growth is the 2045 baseline used on the decision page.")
    lever2 = table(
        "Lever 2: change the equity return, hold house growth at 4.0%",
        lever_hdr, [lever_row(s, f"equity-{s['equity_return']}") for s in by_equity],
        note="Each row is one case. Lever 1 and lever 2 share the baseline row.")

    reg_rows = []
    for i, r in enumerate(regs):
        t = r["run"]["terminal"]
        best = r["run"]["best"]
        cells = "".join(
            (f"<td class='best'>{m(t[k])}</td>" if k == best else f"<td>{m(t[k])}</td>")
            for k in ["sell_equities", "sell_treasury", "live_in", "rent_out"])
        reg_rows.append(
            f"<td><a id='regime-{i}'></a>{esc(r['name'])}</td><td>{pc(r['cpi'], 1)}</td>"
            f"<td>{pc(r['house'], 1)}</td><td>{pc(r['treasury'], 1)}</td>"
            + cells + f"<td><strong>{esc(PATH_LABELS[best])}</strong></td>"
            + method_cell("black-swan.html", "Stress regime", sources=["fred_casthpi", "fred_tb3ms", "fred_nasdaq"]))
    reg_table = table(
        "Stress regimes: each one is a case",
        ["Regime", "Inflation a year", "House prices a year", "Treasury yield",
         "Sell, equities", "Sell, Treasuries", "Live in it", "Let it out", "Best path", "Basis"],
        reg_rows,
        note="Figures are the terminal value at 2045 after thirty years in the regime. The regime's own "
             "analogue is described on the black swan page.")

    yr_rows = []
    for y in (2040, 2045, 2050):
        pr = paths[y]["paths"]
        best = max(pr, key=lambda k: pr[k]["terminal"])
        cells = "".join(
            (f"<td class='best'>{m(pr[k]['terminal'])}</td>" if k == best else f"<td>{m(pr[k]['terminal'])}</td>")
            for k in ["sell_equities", "sell_treasury", "live_in", "live_then_rent", "rent_out"])
        yr_rows.append(f"<td><a id='year-{y}'></a>{y}</td>" + cells
                       + f"<td><strong>{esc(PATH_LABELS[best])}</strong></td>"
                       + method_cell("#method", "Model output", sources=["fred_nasdaq", "fred_tb3ms", "fred_cpiaucns"]))
    yr_table = table(
        "Inheritance year: each one is a case",
        ["Inherited", "Sell, equities", "Sell, Treasuries", "Live in it", "Live in it, then let it",
         "Let it out", "Best path", "Basis"], yr_rows,
        note="Terminal values after thirty years, in nominal dollars of that future year. Live in it, then let it is a mixed path: "
             "the heir occupies the house for a period and then lets it out.")

    be_rows = [
        ("<a id='threshold-growth'></a>House growth needed to make keeping the home match selling (2045)",
         f"{pc(p45['breakeven_house_growth'])} a year for thirty years"),
        ("<a id='threshold-rent'></a>Monthly rent needed to make letting match selling (2045)",
         f"{m(p45['breakeven_rent_monthly'])} a month, in 2045 dollars"),
        ("<a id='threshold-return'></a>Return on the sale proceeds at which living matches selling (2045)",
         f"{ret_cell(p45['breakeven_return_vs_live'])}"),
    ]
    be_table = table(
        "Break-even thresholds, 2045 inheritance",
        ["Threshold", "Value"],
        [f"<td>{a}</td><td>{b}</td>" + method_cell("#method", "Model output", sources=["fred_casthpi", "fred_gs10"]) for a, b in be_rows],
        note="A negative return means selling still matches living even if the sale proceeds lose that much a year.")

    # ---------------------------------------------------------------- imputed rent --
    # This session's absolute stated-level cases. The share-of-market-rent ladder
    # and the solved break-even live on the decision page and the pre-commit
    # register; this lever answers the same question in absolute monthly dollars
    # and adds the return the sale proceeds would then need.
    imr = MODEL["imputed_rent_levels"]
    im_rows = []
    for r in imr["rows"]:
        im_rows.append(
            f"<td><a id='imputed-{r['monthly']}'></a>{m(r['monthly'])}</td>"
            f"<td>{m(r['annual'])}</td>"
            f"<td>{m(r['uplift'])}</td>"
            f"<td>{m(r['live_terminal'])}</td>"
            f"<td>{m(r['sell_terminal'])}</td>"
            + ret_cell(r["return_required"])
            + f"<td><strong>{esc(PATH_LABELS[r['best']])}</strong></td>"
            + method_cell("#method", "Model output", sources=["fred_casthpi", "fred_gs10"]))
    im_table = table(
        "Lever 3: imputed rent credited to the living path (2045 inheritance)",
        ["Imputed rent a month (stated)", "A year", "Added to the living path",
         "Living path terminal", "Sell and invest terminal",
         "Return the proceeds must earn to match living", "Winner", "Basis"],
        im_rows,
        note="The levels are stated scenarios, not estimates: no market rent or rent opinion for Property A "
             "has been supplied, so the real input in the data file is empty and the published baseline is "
             "the zero row. Each level is credited to the living path over the whole thirty years, grown at "
             "the modelled inflation rate and accumulated at the after-tax equity return, the same "
             "convention as the letting path's rent, and it is not taxable income because it is never "
             "received as cash. The gap only closes near the housing value the decision page reports as "
             "needed; below that, selling still wins.")


    # ---------------------------------------------------------------- cost levers --
    # Levers 4 and 5 price the two owner-side cost uncertainties the brief asked to
    # see as ranges rather than round numbers: the insurance premium on Property A,
    # and the debt service that would exist if either building turns out to be
    # encumbered. Both re-run the same engine; neither invents a figure for the
    # household. The official rung is published at the figure the Department prints.
    cc = MODEL.get("cost_cases") or {}
    ins_rows = []
    for i, r in enumerate(cc.get("rows", [])):
        t = r["terminals"]
        anchor = f"insurance-{r['annual']}"
        ins_rows.append(
            f"<td><a id='{anchor}'></a>{esc(_rung(r))}</td>"
            f"<td>${r['annual']:,}</td>"
            f"<td>{m(t['sell_equities'])}</td><td>{m(t['sell_treasury'])}</td>"
            f"<td>{m(t['live_in'])}</td><td>{m(t['rent_out'])}</td>"
            f"<td>{m(r['live_gap'])}</td>"
            f"<td><strong>{esc(PATH_LABELS[r['best']])}</strong></td>"
            + (src_cell([r["kind"]], "Published figure") if r.get("kind") in SOURCES
               else method_cell("review.html#register", "Owner figure or stated scenario", sources=[])))
    ins_table = table(
        "Lever 4: the insurance premium on Property A, across the whole band (2045 inheritance)",
        ["Rung", "A year", "Sell, equities", "Sell, Treasuries", "Live in it", "Let it out",
         "Change to the living path", "Best path", "Basis"],
        ins_rows,
        note=f"The floor rung is the published statewide average written premium for the owner-occupied "
             f"homeowners form in experience year {cc.get('band', {}).get('official_floor_year', 2017)}, "
             f"which is the newest year of that series and is quoted as published, not rounded. The middle "
             f"is the owner's estimate, which is what the rest of this site runs. The top is a stated "
             f"scenario, not an estimate. Across the whole band the living path moves by "
             f"{m(cc.get('band', {}).get('effect_on_live', 0))} of terminal value against a "
             f"{m(cc.get('gap_live_at_baseline', 0))} selling-versus-living gap, which is "
             f"{cc.get('band_share_of_gap', 0)}% of it: insurance changes the size of the bill, not the "
             f"ranking, because a house sold in the year of inheritance pays no premium afterwards.")

    debt_rows2 = []
    for r in cc.get("debt_rows", []):
        t = r["terminals"]
        debt_rows2.append(
            f"<td><a id='debt-{r['monthly']}'></a>{m(r['monthly'])} a month</td>"
            f"<td>{m(r['annual'])}</td><td>{m(t['sell_equities'])}</td>"
            f"<td>{m(t['live_in'])}</td><td>{m(t['rent_out'])}</td>"
            f"<td>{m(r['live_delta'])}</td>"
            f"<td><strong>{esc(PATH_LABELS[r['best']])}</strong></td>"
            + method_cell("#method", "Model output", sources=["fred_casthpi", "fred_gs10"]))
    debt_table = table(
        "Lever 5: a debt service added to the keeping paths, if either building is encumbered (2045 inheritance)",
        ["Stated payment", "A year", "Sell, equities", "Live in it", "Let it out",
         "Change to the living path", "Best path", "Basis"],
        debt_rows2,
        note="The zero row is the published baseline: nothing in the record says whether either building "
             "carries a mortgage, deed of trust or lien, so the model runs both free and clear and says so. "
             "Each further row adds that payment to the paths that keep the house and leaves the sale paths "
             "alone, which is the effect on the ranking rather than on the balance sheet, because a sale pays "
             "the balance off out of the proceeds and a holder pays it off over time with interest on top. "
             "The ranking does not move at any of these levels.")

    # Lever 6: the keep-and-borrow case. The estate liquidity page runs both complete
    # routes - borrow the band's tax against the kept house, or sell it and pay from
    # the proceeds - band by band; this lever carries the same rows onto the what-if
    # page so every way the ranking can move sits on one page.
    kb = MODEL.get("mortgage_case") or {}
    kb_rows6 = kb.get("rows", [])
    kb_rows_whatif = []
    for r in kb_rows6:
        kb_rows_whatif.append(
            f"<td><a id='borrow-{r['tax']}'></a>{m(r['tax'])}</td>"
            f"<td>{m(r['monthly_payment'])}</td>"
            f"<td>{m(r['route_keep_live'])}</td><td>{m(r['route_keep_rent'])}</td>"
            f"<td>{m(r['route_sell_pay'])}</td>"
            f"<td><strong>{esc(r['best_route'])}</strong></td>"
            + method_cell("liquidity.html", "Keep-and-borrow case",
                          sources=["fred_mortgage", "fred_casthpi", "fred_gs10"]))
    kb_table = table(
        "Lever 6: borrow the estate's tax against the kept house instead of selling (2045 inheritance, band by band)",
        ["Tax to raise", "Monthly payment on a 30-year fixed loan", "Keep it, live in it, borrow",
         "Keep it, let it out, borrow", "Sell it and pay from the proceeds",
         "Better route at this band", "Basis"],
        kb_rows_whatif,
        note=f"The principal is never an estate size: each row is the tax on one anonymous band of the amount "
             f"above the exclusion, the same bands the estate liquidity page publishes. The loan amortises at "
             f"{pcf(kb['rate'], 2)}, the published 30-year fixed average, with no deduction assumed for the "
             f"interest. Borrowing does not become the better route at any published band, but the largest "
             f"band is the one the sale proceeds cannot self-fund, which is a liquidity question to settle "
             f"before the nine-month date. Full method, loan-to-value arithmetic and limits: the "
             f"<a href=\"liquidity.html\">estate liquidity page</a>.")

    jump = ("<ul class='card-list'>"
            "<li><a href='#house-2.5'>House growth at 2.5%</a></li>"
            "<li><a href='#house-5.5'>House growth at 5.5%</a></li>"
            "<li><a href='#equity-5.0'>Equity return at 5.0%</a></li>"
            "<li><a href='#equity-9.0'>Equity return at 9.0%</a></li>"
            "<li><a href='#regime-0'>Great Inflation repeat</a></li>"
            "<li><a href='#regime-2'>A financial crisis crash</a></li>"
            "<li><a href='#year-2040'>Inherit in 2040</a></li>"
            "<li><a href='#year-2050'>Inherit in 2050</a></li>"
            "<li><a href='#threshold-growth'>House growth needed</a></li>"
            "<li><a href='#threshold-rent'>Rent needed</a></li>"
            f"<li><a href='#imputed-{imr['rows'][0]['monthly']}'>Imputed rent at zero (the baseline)</a></li>"
            f"<li><a href='#imputed-{imr['rows'][-1]['monthly']}'>Imputed rent at "
            f"{m(imr['rows'][-1]['monthly'])} a month</a></li>"
            + ("".join(f"<li><a href='#insurance-{r['annual']}'>Insurance at ${r['annual']:,} a year</a></li>"
                       for r in (cc.get("rows") or []))
               + "".join(f"<li><a href='#debt-{r['monthly']}'>Debt service at {m(r['monthly'])} a month</a></li>"
                         for r in (cc.get("debt_rows") or [])))
            + "".join(f"<li><a href='#borrow-{r['tax']}'>Borrow against the house: tax of {m(r['tax'])}</a></li>"
                      for r in (kb_rows6 or []))
            + "</ul>")
    return (
        callout("method", "How to use this page", f"""
<p>There are no sliders, because this site runs no script. Each case below is a link target. Choose one from the list,
or read the tables in order. Change one lever at a time, and the other stays at the baseline. Every figure is rounded
to the nearest $10 and comes from the same model that builds the rest of the site.</p>
{jump}""")
        + lever1 + lever2 + im_table + ins_table + debt_table + kb_table + reg_table + yr_table + be_table
        + callout("flag", "What the cases do not show", """
<p>No case here credits the letting paths with a market rent, because none has been supplied. Read every letting row as
the path at zero rent, which is a floor. Lever 3 credits the <em>living</em> path instead, at stated levels that are
scenarios rather than estimates; the input that would hold a real imputed rent is empty, so the published baseline
stays the zero row. Levers 4 and 5 change a <em>cost</em> rather than a return, and they are there to show what does
<em>not</em> move the answer: neither the insurance band nor any debt service tested here puts keeping the house
ahead of selling it. Lever 6 runs the keep-and-borrow case end to end, and it does not move the answer either:
borrowing against the kept house is dearer than selling and paying at every published band, and the largest band
is the one the sale proceeds cannot self-fund, which makes the lender conversation a pre-death task rather than a
nine-month scramble. The model also does not change the Proposition 19 eligibility question; if
that answer is no, the reassessment is full and every case here moves toward selling.</p>""")
    )


def page_decision_rules() -> str:
    """Rules written before the figures arrive: gates, pre-committed paths, a draft investment policy.

    Nothing here is adopted. The sign-off and decision fields are blank on purpose: the owner and the
    household complete them, with a date, before any figure is relied on.
    """
    p45 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2045)
    blank = '<span class="blank">pending, owner to complete</span>'

    def row(cells, src):
        return "".join(f"<td>{c}</td>" for c in cells) + src

    gates = table(
        "Gates, applied in order. A gate is met only on written evidence.",
        ["#", "Gate", "Evidence needed", "If met", "If not met", "Model figure it is tested against", "Source"],
        [
            row(["G1", "Is the transfer between a parent and a child, or between a grandparent and a grandchild whose parent has died?",
                 "The trust instrument and the recorded deed.",
                 "The exclusion may apply. Keep the Proposition 19 steps on the timeline.",
                 "No exclusion. Property A is reassessed to full value, every shelter figure on the site falls away, and the case for selling strengthens.",
                 "The model assumes this gate is met.",
                 ], src_cell(["rtc63_2_eligibility"], "Revenue and Taxation Code 63.2")),
            row(["G2", "Will the heir occupy Property A as the principal residence and claim the exclusion in time?",
                 "A written occupancy plan. The rules: occupy within one year of the transfer, claim within three years.",
                 "The living path is an option.",
                 "The living path is removed. The exclusion is not claimed.",
                 "The living paths assume occupancy.",
                 ], src_cell(["boe_prop19"], "BOE, Proposition 19")),
            row(["G3", f"Is an independent written value at the date of death within 10% of the owner's estimate of {m(A['estimated_market_value_2026'])}?",
                 "A written valuation as of the date of death.",
                 "No change to the model.",
                 "Re-run the model before deciding. The 10% band is a proposal for the owner to adopt or change.",
                 "The model starts from the owner's estimate, unverified.",
                 ], method_cell("decision.html", "Model input, unverified", sources=[])),
            row(["G4", "Does a documented rent opinion for comparable housing, where the heir would otherwise live, exceed the imputed-rent break-even for the year of inheritance?",
                 "A written rent opinion for comparable housing in the place the heir would live, and the inheritance year.",
                 "The living path beats selling and investing on the model's assumptions.",
                 "Selling and investing (section 2, rule R2).",
                 f"2045: about {m(p45['imputed_rent_breakeven_monthly'])} a month, in 2045 dollars, rising with inflation.",
                 ], method_cell("decision.html", "Model output", sources=[])),
            row(["G5", "Does a documented market rent for Property A exceed the letting break-even?",
                 "An independent rent opinion for Property A.",
                 "Letting becomes a candidate to compare with selling.",
                 "Letting stays a floor, not a comparison. The site credits no rent today.",
                 f"2045: about {m(p45['breakeven_rent_monthly'])} a month, in 2045 dollars.",
                 ], method_cell("decision.html", "Model output", sources=[])),
            row(["G6", "Does the best independent forecast of house growth over thirty years exceed the growth needed for keeping the home to match selling?",
                 "A forecast with a stated source and a stated range.",
                 "Keeping the home is a candidate.",
                 "Sell.",
                 f"2045: {pc(p45['breakeven_house_growth'])} a year. The model baseline is {pcf(ASM['house_growth']['baseline'], 1)}.",
                 ], method_cell("decision.html", "Model output", sources=["fred_casthpi"])),
            row(["G7", "Does the gross estate, with adjusted taxable gifts, exceed the federal basic exclusion?",
                 "An estate inventory, a record of prior taxable gifts and the portability decision.",
                 "An estate liquidity plan and a review of the federal return are needed before the sale.",
                 "The standard path applies.",
                 f"Basic exclusion: {m(V['federal_basic_exclusion_2026']['value'])} for 2026; {m(V['federal_basic_exclusion_2027']['value'])} for 2027.",
                 ], src_cell(["irs_estate"], "IRS, Estate tax")),
            row(["G8", "Does the household want to reduce the chance of investing just before a crash?",
                 "The household's stated preference, written before the proceeds arrive.",
                 "Adopt the phased entry in the investment policy (section 3).",
                 "Invest in one step.",
                 "The black-swan page tests both on four real crashes and on synthetic sequences.",
                 ], src_cell(["fred_djia_1929"], "FRED, Dow Jones 1929 episode")),
            row(["G9", "Are the November 2026 results certified, for the state measure and for the local parcel tax?",
                 "Certified results from the Secretary of State and the city elections office.",
                 "Keep the rates in the model.",
                 "Re-run the model without the affected rule.",
                 "Top California rate, including the 1% surcharge: 13.3% (ledger ftb_540es_2026).",
                 ], src_cell(["sos_results"], "Secretary of State, unofficial results")),
        ],
        note="G9 changes a rule, not a path. A measure that is not certified is not modelled as law.")

    paths = table(
        "Pre-committed paths. Each row states what will be chosen if its findings occur, and why.",
        ["Rule", "If the findings are", "Path chosen", "Why", "Decision and date", "Source"],
        [
            row(["R1", "G1 met, G2 met and G4 met",
                 "Live in Property A and claim the exclusion. Review each year.",
                 "Living beats selling only when the rent avoided exceeds the break-even. The comparable-rent opinion is the test.",
                 blank], src_cell([], "Logged on the register")),
            row(["R2", "G1 met, and G2 or G4 not met",
                 "Sell soon after inheritance. Invest the proceeds under the policy in section 3.",
                 "Selling leads in the baseline run of the path table, and it does not depend on occupancy or on finding a tenant. The sensitivity and regime runs are on the what-if and black-swan pages.",
                 blank], method_cell("decision.html", "Model output", sources=["fred_casthpi", "fred_gs10"])),
            row(["R3", "G1 not met",
                 "Sell (no exclusion). Re-run the sale and tax figures with the attorney and the CPA.",
                 "Without the exclusion the reassessment is to full value, which favours a sale.",
                 blank], src_cell(["rtc63_2_eligibility"], "Revenue and Taxation Code 63.2")),
            row(["R4", "G5 met",
                 "Letting becomes a candidate. Compare it with selling on the rent opinion, not on the model's zero rent.",
                 "The letting paths are a floor until a documented rent exists.",
                 blank], method_cell("decision.html", "Model output", sources=[])),
            row(["R5", "G3 not met",
                 "Re-run the model on the independent value. Re-test G4 and G6 before deciding.",
                 "Every reassessment and sale figure scales with the value at death.",
                 blank], src_cell([], "Logged on the register")),
            row(["R6", "A mixed path is wanted (for example, part of the proceeds invested at once and the rest phased)",
                 "Write the split as a percentage before the proceeds arrive. The black-swan page models the phased half and the immediate half separately.",
                 "A mixed path is not a fourth answer. It is a way of spreading the entry risk, and it has to be written down to be tested.",
                 blank], method_cell("black-swan.html", "Model output", sources=["fred_tb3ms"])),
        ],
        note="Rules R1 to R6 are proposals. They take effect only when the owner and the household sign section 5.")

    pi = ASM["treasury_short_yield_nominal"]["baseline"]
    policy = table(
        "Investment policy for the sale proceeds (draft; choices left to the owner are marked)",
        ["Item", "Draft rule", "Basis in this model", "Owner decision and date", "Source"],
        [
            row(["P1", "Purpose. Preserve the net proceeds first, then grow them for the household's stated goals. The goals are the owner's to state.",
                 "No model input. The owner states the goals.", blank], src_cell([], "Owner statement")),
            row(["P2", f"Entry method, chosen before the proceeds arrive: (a) invest in one step, or (b) park the net proceeds in short-term Treasuries for 24 to 36 months, then buy equities in equal monthly steps over {ASM['phased_equity_phase_months']['value']} months. The base case in the model parks for {ASM['phased_park_months']['value']} months.",
                 "The black-swan page: four real crashes (1929, 2000, 2008, 2020) and the 24-, 30- and 36-month windows, with the synthetic stress table alongside.", blank],
                 method_cell("black-swan.html", "Model output", sources=["fred_tb3ms", "treasury_cmt"])),
            row([f"P3", f"Parking yield. Short-term Treasuries from three months to two years. The model uses {pc(pi*100, 1)} nominal, within a band of {pc(ASM['treasury_short_yield_nominal']['low']*100, 1)} to {pc(ASM['treasury_short_yield_nominal']['high']*100, 1)}.",
                 "A stated scenario, not an official forecast. No agency publishes a forward short-term yield for 2040 to 2050.", blank],
                 src_cell(["fred_gs10"], "FRED, Treasury yields")),
            row(["P4", f"Equity allocation. The owner sets the mix. The model uses one equity return ({pc(ASM['equity_return_nominal_gross']['baseline']*100, 1)} gross, less {pc(ASM['equity_tax_drag']['baseline']*100, 1)} a year for tax drag). It recommends no allocation.",
                 f"Equity return and drag, from the inputs. The 7.0% is a stated scenario.", blank],
                 src_cell(["ftb_cg"], "FTB, Capital gains")),
            row(["P5", "Market moves during the phase-in. Keep the schedule. Do not stop buying after a fall, and do not speed up after a rise. Market timing is not part of the policy.",
                 "The phased engine buys on a fixed schedule. Market timing is not modelled.", blank], src_cell([], "Model design")),
            row(["P6", "Rebalancing. The owner chooses the frequency and the bands before the proceeds arrive.",
                 "No model input.", blank], src_cell([], "Owner decision")),
            row(["P7", "Cash reserve. The owner sets the months of spending held outside the portfolio.",
                 "No model input.", blank], src_cell([], "Owner decision")),
            row(["P8", "Tax. The account type decides the tax. A taxable account pays federal and California tax on dividends, interest and gains. A CPA advises on lot selection and on any harvesting.",
                 f"The model deducts {pc(ASM['equity_tax_drag']['baseline']*100, 1)} a year for dividend and turnover tax in a taxable account. California taxes gains as ordinary income.",
                 blank], src_cell(["ftb_cg"], "FTB, Capital gains")),
            row(["P9", "Review. Once a year, and after any change on the law watch. Re-run the model from the inputs each time.",
                 "The model rebuilds from its inputs and reports whether the recommendation moved.", blank],
                 method_cell("#method", "Model output", sources=[])),
            row(["P10", "Records. Keep dated copies of this page, the gate decisions and the model version used.",
                 "This page and the build version are the record.", blank], src_cell([], "Owner decision")),
        ],
        note="A policy written before the money arrives is the protection against deciding the rules after seeing the figures.")

    open_items = table(
        "Still open: items that need an outside party before a decision",
        ["Item", "Why it matters", "Who can supply it", "Status", "Source"],
        [
            row(["Trust instrument and the relationship between the transferor and the heir (G1)",
                 "It decides whether any exclusion applies at all.", "An estate attorney", "Open"],
                src_cell(["rtc63_2_eligibility"], "Revenue and Taxation Code 63.2")),
            row(["Written valuation of Property A at the date of death (G3)",
                 "Every reassessment and sale figure scales with it.", "An independent appraiser", "Open"],
                src_cell(["boe_pub29"], "BOE, Publication 29")),
            row(["Documented market rent for Property A, and for comparable housing (G4, G5)",
                 "It is the one missing input that could change the recommendation.", "A rent opinion from an independent appraiser or broker", "Open"],
                src_cell(["hud_fmr"], "HUD, Fair Market Rents")),
            row(["Comparable sales for Property A",
                 "The owner's value estimate has not been checked against sales.", "A licensed broker or appraiser", "Open"],
                src_cell([], "No official source applies")),
            row(["Insurance quotes: a primary-residence policy for Property A, a rental policy for Property B",
                 "The figure used is an owner estimate, and no quote exists.", "An insurer or broker", "Open"],
                src_cell(["cdi_tips"], "CDI, shopping tips")),
            row(["Finished living area of Property B's building (local parcel tax, G9)",
                 "Each square foot above 5,000 adds $0.195 a year to the tax.", "The owner, from the plans or the assessor's record", "Open"],
                src_cell([], "Official text withheld for privacy")),
            row(["Rent-control status and base-rent dates for Property B's units",
                 "Decides whether up to half of the parcel tax can be passed to tenants.", "The owner, from the leases and rent records", "Open"],
                src_cell([], "Official text withheld for privacy")),
            row(["Five-year maintenance and capital plan for both buildings",
                 "The maintenance figures are assumptions, and nothing has been supplied.", "The owner and a licensed contractor", "Open"],
                src_cell([], "No official source applies")),
            row(["Estate inventory, prior taxable gifts and the portability decision (G7)",
                 "Decides whether a federal return and a liquidity plan are needed.", "An estate attorney and a CPA", "Open"],
                src_cell(["irs_estate"], "IRS, Estate tax")),
            row(["Certification of the November 2026 results (Proposition 3 and the local parcel tax)",
                 "A result that is not certified is not law. Proposition 3 is due for certification on 11 December 2026.",
                 "The Secretary of State and the city elections office", "Due 11 December 2026"],
                src_cell(["sos_results"], "Secretary of State, unofficial results")),
            row(["Pre-rounding figures and place names in the public repository's earlier commits",
                 "The site is clean; the history is not. Removing it needs a rewrite of main and a force-push.",
                 "The repository owner, under the procedure on the review page", "Not performed in this session"],
                src_cell([], "Logged on the register")),
        ])

    signoff = callout(
        "flag", "Sign-off (blank until completed)",
        "<p>These rules are not in force until the owner and the household sign them. Fill the lines below before any "
        "figure is used to choose a path, and record the date.</p>"
        "<p>Adopted by: <span class=\"blank\">pending, owner to complete</span> &nbsp; "
        "Date: <span class=\"blank\">pending</span></p>"
        "<p>Any change is a new, dated version of this page. The model is rebuilt from its inputs after each change, "
        "and the recommendation is checked for movement.</p>")

    return (
        callout("note", "Status: draft, unsigned",
                "<p>Written so that the outcome is not reverse-engineered from one projection. Each rule names the evidence "
                "that triggers it, the path it selects, and the model figure it is measured against. Blank fields are for the "
                "owner and household to complete with a date. Nothing here is a recommendation to a specific person, and nothing "
                "here is legal, tax or investment advice.</p>")
        + '<h2 id="gates">1. Gates</h2>' + gates
        + '<h2 id="paths">2. Pre-committed paths</h2>' + paths
        + '<h2 id="policy">3. Investment policy for the sale proceeds</h2>' + policy
        + '<h2 id="open">4. Still open</h2>' + open_items
        + '<h2 id="signoff">5. Sign-off</h2>' + signoff
    )


PAGE_BUILDERS = {
    "index.html": (page_index, "Two California properties, one decision. Every figure rounded to the nearest $10."),
    "precommit.html": (page_precommit, "The household's rules, written before the figures are read."),
    "executive-summary.html": (page_executive_summary,
                               "The important details, the recommendation, and what would change it."),
    "decision-rules.html": (page_decision_rules, "Gates, pre-committed paths, an investment policy draft and what is still open. Unsigned."),
    "decision.html": (page_decision, "Five paths, priced, with the break-even numbers and the sensitivity."),
    "briefing.html": (page_briefing, "A printable one-page attorney and CPA discussion sheet."),
    "property-a.html": (page_property_a, "The home being inherited through a trust, planned 2040 to 2050."),
    "property-b.html": (page_property_b, "The three-unit building the heir already owns and rents out."),
    "ownership-distinction.html": (page_distinction, "Why inherited and already-owned are not interchangeable."),
    "costs.html": (page_costs, "Water, power, insurance, maintenance and tax, now and projected."),
    "projections.html": (page_projections, "Year by year to 2076 for value, assessed value and tax."),
    "taxes.html": (page_taxes, "Basis step-up, capital gains, the 121 exclusion, recapture."),
    "inheritance.html": (page_inheritance, "The trust transfer, phase by phase, with deadlines."),
    "timeline.html": (page_timeline, "Every legal and tax clock in order, from death and from transfer, with its official source."),
    "what-if.html": (page_what_if, "Change one lever at a time. Each case is a link; no script is used."),
    "estate.html": (page_estate, "Federal thresholds, California's position, scenario bands."),
    "liquidity.html": (page_liquidity, "What the estate tax costs, when it is due, and how it can be paid without a forced sale."),
    "keep-and-borrow.html": (page_keep_and_borrow,
                                  "Take the cash out of the house without selling it, and what the loan costs for the privilege."),
    "laws.html": (page_laws, "Enacted, dead and proposed rules that could move the answer."),
    "black-swan.html": (page_black_swan, "Regimes where the answer changes, and by how much."),
    "economy.html": (page_economy, "Fifty years of verified inflation, house price and yield data."),
    "questions.html": (page_questions, "What is known, what is missing, and how to find it."),
    "suggestions.html": (page_suggestions, "A review queue of proposals, with a decision and date column for each one."),
    "review.html": (page_review, "Unverified figures, modelling caveats and the repository audit."),
    "glossary.html": (page_glossary, "Plain-language definitions of the terms used on this site."),
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
      "trust; **Property B** is the three-unit building the heir already owns. No name, street address, postal "
      "parcel number, postal code, county or city name, trust term or utility account appears here or on the "
      "site; the county and city are deliberately withheld because they identify the properties.")
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
    a("## Mixed paths, and what moving out costs")
    a("")
    a("| Path | Terminal value | Selling at the inheritance leaves this much more |")
    a("|---|---|---|")
    for r in MIXED["paths"]:
        if r["occupy_years"] == 0 and r["mode"] == "sell":
            continue
        a(f"| {r['label']} | {cash(r['asset_terminal'])} | {cash(r['gap_vs_sell_now'])} |")
    a("")
    a(f"The closest mixed path is a short occupancy followed by a sale, and it still ends behind selling at "
      f"the inheritance. Moving out after claiming the Proposition 19 exclusion costs about "
      f"{cash(MIXED['clawback']['difference'])} of extra property tax over thirty years on the "
      "live-then-let path, against the reading in which the low assessment survives; both readings are published.")
    a("")
    a("## How often the answer holds")
    a("")
    for s in MIXED["distribution"]["shares"]:
        a(f"- {s['key']}: **{s['value']*100:.1f}%** of {MIXED['distribution']['draws']} resampled histories.")
    a("")
    a("The draws are ten-year blocks of the verified California house price index and consumer price index, "
      "drawn together so house and inflation history move as they did. The equity return is held at the "
      "published scenario, because no official series of forward equity returns exists.")
    a("")
    a("## Read this before the numbers")
    a("")
    a("The pre-commitment register on `precommit.html` states, in advance, the condition under which the "
      "household would choose each path, and the household's own priorities. It is meant to be filled in "
      "before any projection is read, so the answer cannot be reverse-engineered from one scenario.")
    a("")
    a("## Corrections in this edition")
    a("")
    a(f"- The combined depreciation recapture rate is corrected from 41.1% to **42.1%**. Its own stated "
      f"components are 25% federal, 13.3% California and 3.8% net investment income tax, which sum to 42.1. "
      f"Every figure that depends on recapture was rebuilt.")
    a("- The transfer tax and recording fees on the sell path are itemised: about "
      f"{cash(MIXED['fees_example']['published_total'])} on a {cash(MIXED['fees_example']['price'])} sale, "
      f"about {MIXED['fees_example']['published_share_of_modelled']}% of the modelled 5.5% selling cost. "
      "The $75 instrument fee does **not** apply, because Government Code section 27388.1(a)(2)(A) exempts "
      "an instrument recorded in connection with a transfer subject to the documentary transfer tax.")
    a("- The initiative to repeal most of Proposition 19 **failed to qualify** for the November 2026 ballot "
      "(Secretary of State memorandum, 18 May 2026), so the shelter arithmetic is current law rather than "
      "law about to change. It is recorded as dead on the law page.")
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
    hpi = {int(y): float(v) for y, v in SERIES["hpi_a"]["values"].items()}
    hpi_first, hpi_last = min(hpi), max(hpi)
    hpi_fifty = ((hpi[hpi_last] / hpi[hpi_first]) ** (1 / (hpi_last - hpi_first)) - 1) * 100
    hpi_twenty_start = hpi_last - 20
    hpi_twenty = ((hpi[hpi_last] / hpi[hpi_twenty_start]) ** (1 / 20) - 1) * 100
    hpi_annual = [(hpi[y] / hpi[y - 1] - 1) * 100 for y in range(hpi_first + 1, hpi_last + 1)]
    cpi = {int(y): float(v) for y, v in SERIES["cpi"]["values"].items()}
    cpi_years = sorted(cpi)
    cpi_annual = [(cpi[y] / cpi[y - 1] - 1) * 100 for y in cpi_years[1:]]
    a(f"- **The break-even.** Keeping the home beats selling only if it appreciates "
      f"{pc(p45['breakeven_house_growth'])} a year for thirty years. The verified California state house-price "
      f"index compounded at {hpi_fifty:.1f}% a year from {hpi_first} to {hpi_last} and "
      f"{hpi_twenty:.1f}% a year over the latest twenty years in the record "
      f"([FRED CASTHPI]({SERIES['hpi_a']['src']})).")
    a(f"- **The break-even rent.** Letting would need about {cash(p45['breakeven_rent_monthly'])} a month, "
      f"{cash(p45['breakeven_rent_annual'])} a year, in 2045, to match selling and investing.")
    a("")
    a("## The black swans, and what they do to the answer")
    a("")
    a("Real economies do not grow at a constant rate. In the verified record used here, annual consumer price "
      f"inflation ranged from {min(cpi_annual):.1f}% to {max(cpi_annual):.1f}%, and annual house-price growth "
      f"in the California state-level index ranged from {min(hpi_annual):.1f}% to {max(hpi_annual):.1f}% "
      f"([FRED CASTHPI]({SERIES['hpi_a']['src']})). CPI figures use [FRED CPIAUCSL]({SOURCES['fred_cpi']['url']}). "
      "The regimes below replay the worst stretches of that record against a 2045 inheritance over thirty years.")
    a("")
    a("| Regime | Inflation | House growth | Treasury | Best path |")
    a("|---|---|---|---|---|")
    for r in regs:
        a(f"| {r['name']} | {r['cpi']}% | {r['house']}% | {r['treasury']}% | "
          f"{PATH_LABELS[r['run']['best']]} |")
    a("")
    a(f"Sold into equities or Treasuries wins {RF['sell']} of the {RF['n']} regimes. Keeping the house wins only in: "
      f"{RF['keep_names']}. These are scenario results, not forecasts for a particular neighborhood.")
    a("")
    a("### Entry timing, replayed against the real record")
    a("")
    a("The stress regimes above are 30-year averages. The owner also asked what happens if the sale proceeds "
      "arrive just before a crash. The table below replays the same capital through the published monthly prices "
      "of the actual 1929, 2000, 2008 and 2020 episodes, held for the episode's own horizon and restated in "
      "October 2026 purchasing power.")
    a("")
    a("| Episode | Window | Invest on day one | Park 30 months, then phase in | Phasing ahead by |")
    a("|---|---|---|---|---|")
    for e in EPI["episodes"]:
        s = e["strategies"]
        a(f"| {e['name']} | {e['entry']} to {e['exit']} | {cash(s['lump']['real_today'])} | "
          f"{cash(s['phase']['real_today'])} | {cash(s['phase']['vs_lump'])} |")
    a("")
    a(f"Waiting beat day-one investing in {len(EPI['phase_better_than_lump'])} of the {len(EPI['episodes'])} "
      "episodes. It lost in the 2020 episode, where the crash was over before a 24-month parking period ended. "
      "It is insurance against one specific bad luck, paid for in the years when that luck does not happen. "
      "The full method, the 24-month and 36-month results, and the case where the crash arrives three years "
      "after the inheritance are on the black swan page.")
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
    a("### If the estate does exceed the exclusion, the tax is due in cash on a fixed date")
    a("")
    a(f"- Federal estate tax is {pcf(LIQ['clock']['estate_tax_rate'], 0)} of the amount above the exclusion and is "
      f"due {LIQ['clock']['due_months_after_death']} months after the date of death. A six-month extension of time "
      f"to file the return is not an extension of time to pay.")
    a(f"- Interest on anything unpaid runs from the original due date at the federal short-term rate plus three "
      f"percentage points, compounded daily. That rate was {pcf(LIQ['clock']['underpayment_rate'], 0)} in the fourth "
      f"quarter of 2026 and has ranged from {pcf(LIQ['clock']['underpayment_low'], 0)} to "
      f"{pcf(LIQ['clock']['underpayment_high'], 0)} across 2022 to 2026.")
    a(f"- On the {cash(LIQ['excess_bands'][2]['excess'])} band, deferring five years costs "
      f"{cash(next(x for x in LIQ['excess_bands'][2]['terms'] if x['years'] == 5)['instalment_interest'])} in "
      f"interest against {cash(next(x for x in LIQ['excess_bands'][2]['terms'] if x['years'] == 5)['return_given_up'])} "
      f"of return the same cash would have earned, so deferral is close to break-even at five years and only "
      f"clearly worthwhile at ten.")
    a(f"- The two-person case changes the estate side, not the recommendation: two exclusions with portability "
      f"would shelter {cash(LIQ['estate_exclusions'][1]['two_exclusions'])} in 2045 against "
      f"{cash(LIQ['estate_exclusions'][1]['one_exclusion'])} for one person. The joint section 121 exclusion is "
      f"worth {cash(JOINT_121_MAX_SAVING)} at most, and nothing at all on a sale soon after inheritance.")
    a(f"- Full bands, the five routes to raising the cash, the cost of borrowing instead of selling, and the "
      f"keep-and-borrow case run end to end - for each band, a fully amortising 30-year fixed loan charged to "
      f"the keeping paths against the sell route that pays the same band's tax out of the proceeds, with the "
      f"loan-to-value arithmetic: the estate liquidity page. Borrowing is dearer than selling and paying at "
      f"every published band, and the largest band is beyond what one property's sale can self-fund. Whether "
      f"the section 6166 instalment election is available is a question for the "
      f"attorney; this site does not assume it, because a home occupied as a personal residence is not an "
      f"interest in a closely held business on the face of the statute.")
    a("")
    a("## What is still open")
    a("")
    a("These sit on the flagged-for-review page, each with the publisher that holds the record:")
    a("")
    a("- The owner's market values, the property-tax and assessment histories, the rent and the utility and "
      "insurance estimates are the owner's own records, not checked against a county roll or a quote.")
    a("- Property A's tax rate area and its published ad valorem rate. 1.18% is assumed and flagged.")
    a("- A property-specific insurance premium for either building. The Department of Insurance publishes a "
      "statewide average written premium for each policy form - the newest year read gives $1,074 for an "
      "owner-occupied homeowners form and $519 for a rental dwelling or landlord form on up to four units - and "
      "an online premium survey, not an average for a postal area. Both buildings are now carried as bands "
      "bounded by those figures instead of one shared estimate, and the whole band moves the thirty-year living "
      "figure by under 1% of the gap to selling, so it is a bill to be sized rather than a decision to be made.")
    a("- Whether either building carries a mortgage, deed of trust or lien at the transfer. Nothing in the "
      "record says either way, so both are modelled free and clear and the decision page states that as an "
      "assumption and prices each stated payment level. An encumbrance changes the size of every keeping path's "
      "bill and never the ranking, because a holder pays the interest as well as the principal. A separate "
      "question follows from it, and it is a legal one rather than a financial one: whether the instrument "
      "holding title permits the beneficiary to grant a lien over the property at all, which is what the "
      "keep-and-borrow path assumes.")
    a("- A market rent for Property A, and the seller's actual selling costs.")
    a("- Whether the trust actually holds title, and whether the transfer is between a parent and a child.")
    a("")
    a(f"**Two opened in this pass, both worked and both published.** The living path is credited with no "
      f"housing at all, so it is charged every cost of owning and credited with the value of nothing; credited "
      f"at the market rent it would otherwise cost, living and selling come level at about "
      f"{100 * (next((r['share'] for r in MODEL['imputed_rent']['rows'] if r['living_wins']), 1.0)):.0f}% of that "
      f"rent. And the fixed charges inside Property B's tax bill are "
      f"{MODEL['roll_audit']['property_b']['fixed_share_latest_pct']}% of the bill and grew "
      f"{MODEL['roll_audit']['property_b']['fixed_growth_full_pct']}% a year over its roll, against a "
      f"{ASM['fixed_charge_growth']['baseline'] * 100:.1f}% assumption, so the 2% cap cannot bound that bill "
      f"the way the tables imply.")
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
    a("- `suggestions.html` — the review queue; every item needs a decision, recorded in its own decision and date columns")
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
