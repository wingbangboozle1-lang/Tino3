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
MIXED = json.loads((DATA / "mixed.json").read_text(encoding="utf-8"))
PRECOMMIT = INPUTS.get("precommit", {"rules": [], "household_goals": [], "review_gates": [], "meta": {}})

A = INPUTS["property_a"]
B = INPUTS["property_b"]
V = INPUTS["verified_parameters"]
ASM = INPUTS["assumptions"]
BUILD_DATE = "15 November 2026"

# The phased-investing figures are computed by the model's one monthly engine, so the
# stress table on the black-swan page and the dashboard path cannot drift apart again.
import model as model_mod  # noqa: E402

NAV_GROUPS = [
    ("Start here", ["index.html", "precommit.html", "executive-summary.html", "decision.html",
                    "what-if.html", "briefing.html"]),
    ("The two properties", ["property-a.html", "property-b.html", "ownership-distinction.html"]),
    ("Money over time", ["costs.html", "projections.html", "taxes.html"]),
    ("Rules and the estate", ["inheritance.html", "timeline.html", "estate.html", "laws.html"]),
    ("Black swan economics", ["black-swan.html", "economy.html"]),
    ("Review before deciding", ["questions.html", "suggestions.html", "review.html"]),
    ("Evidence", ["glossary.html", "sources.html"]),
]
PAGE_TITLES = {
    "index.html": "Dashboard",
    "precommit.html": "Decide before you read the numbers",
    "what-if.html": "What-if cases",
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
    <p class="page-footer">Built {esc(BUILD_DATE)}. Sources were last checked between 13 and 15 November 2026;
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


def page_index() -> str:
    p45 = next(p for p in MODEL["paths"] if p["inherit_year"] == 2045)
    best = p45["best_path"]
    # What staging costs when no crash arrives: the phased terminal against immediate
    # investment, both computed by the one monthly engine.
    phase_cost = (p45["paths"]["sell_equities"]["terminal"]
                  - p45["paths"]["sell_then_phase"]["terminal"])
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
</ol>""")
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
<li><strong>Do not act yet.</strong> The <a href="questions.html">questions page</a> lists what is still unknown and how to find it out. The <a href="suggestions.html">suggestions page</a> is a review queue: nothing there has been implemented.</li>
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
    "inheritance.html": "The trust transfer, phase by phase, with deadlines.",
    "what-if.html": "One lever at a time, with each case linked.",
    "estate.html": "Federal thresholds, California's position, scenario bands.",
    "laws.html": "Enacted, dead and proposed rules that could move the answer.",
    "black-swan.html": "Regimes where the answer changes, and by how much.",
    "economy.html": "Fifty years of verified inflation, house price and yield data.",
    "questions.html": "What is known, what is missing, and how to find it.",
    "suggestions.html": "A review queue of proposals. Nothing implemented yet.",
    "review.html": "Unverified figures, modelling caveats and the repository audit.",
    "glossary.html": "Plain-language terms with official citations.",
    "timeline.html": "The deadlines and key dates that shape the inheritance decision.",
    "sources.html": "Every official source used, with what it supports.",
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
                + method_cell("decision.html#method", "Model output"))
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
        ("Why moving in only half-helps", f"The Proposition 19 exclusion shelters the old assessed value plus an indexed {m(V['prop19_value_cap_2025_2027']['value'])}. Everything above that is reassessed. In 2045 the sheltered slice is about {m(p45['prop19_cap'])} against a market value of {m(p45['value_at_death'])}."),
        ("The tax-free sale window", "Property acquired from a decedent takes a basis equal to its value at death, so a sale soon after the inheritance pays close to zero capital gains tax. Holding it for thirty years turns the appreciation into a gain taxed at roughly 37% combined federal and California."),
        ("The equity comparison", f"To match selling and investing at 7%, the home must appreciate {pc(p45['breakeven_house_growth'])} a year for thirty years. The verified California state index compounded at 6.4% over fifty years and 2.6% over the last twenty."),
        ("The rental comparison", f"Letting the home out would need about {m(p45['breakeven_rent_monthly'])} a month in 2045 to match selling and investing. That is over 5% of the property's value per year in gross rent."),
        ("The estate position", f"California has had no estate tax since 2005. Federally, the 2026 exclusion is {m(V['federal_basic_exclusion_2026']['value'])} per person and {m(V['federal_basic_exclusion_2027']['value'])} for 2027. Portability lets a surviving spouse use a deceased spouse's unused exclusion."),
        ("The biggest unknown", "Whether the heir wants to live in this specific house. That is a preference, not a number, and it is worth more than any gap in this analysis."),
        ("Mixed paths", f"Living there for a while and then selling is the closest of the mixed paths, and it still ends behind an immediate sale: five years of occupancy followed by a sale leaves {m(next(x for x in MIXED['paths'] if x['occupy_years'] == 5 and x['mode'] == 'sell')['gap_vs_sell_now'])} less than selling at the inheritance. The table is on the <a href=\"decision.html\">decision page</a>."),
        ("The clawback nobody models", f"Moving out after claiming the Proposition 19 exclusion is not free. On the live-then-let path the exclusion is removed and the change-of-ownership base year value is enrolled, which costs about {m(MIXED['clawback']['difference'])} of extra property tax over thirty years against the reading in which the low assessment survives. Both readings are now published."),
        ("How often it holds", f"Over {MIXED['distribution']['draws']} resampled histories of the verified record, selling beats living in the house in {next(s['value'] for s in MIXED['distribution']['shares'] if s['key'].startswith('Selling beats living in it for thirty'))*100:.1f}% of them, and beats living there ten years and then selling in {next(s['value'] for s in MIXED['distribution']['shares'] if s['key'].startswith('Selling beats living in it ten years'))*100:.1f}%. The distribution is on the <a href=\"index.html#distribution\">dashboard</a> and the <a href=\"projections.html#fan\">projections page</a>."),
        ("What a sale actually costs the state", f"The transfer tax and recording fees the brief asked to have priced come to {m(MIXED['fees_example']['published_total'])} on a {m(MIXED['fees_example']['price'])} sale, about {MIXED['fees_example']['published_share_of_modelled']}% of the modelled 5.5% selling cost. The other {MIXED['fees_example']['private_share_of_modelled']}% is commission, escrow and title, which are private quotes rather than statutes. The itemisation is on the <a href=\"taxes.html\">taxes page</a>."),
        ("The repeal that did not happen", "The initiative that would have undone most of Proposition 19 failed to qualify for the November 2026 ballot, so the shelter arithmetic above is current law rather than law about to change. A replacement measure can be filed at any time; the Secretary of State's qualification dashboard is the official page that would show it."),
        ("The pre-commitment rule", "Before reading any projection, the household should write down what would make it choose each path. That register, with its decision columns empty, is on the <a href=\"precommit.html\">pre-commitment page</a>. Without it a single projection can be made to justify any path."),
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
<p>The counter-case is real and it is on the <a href="black-swan.html">black swan page</a>: keeping the house wins in {len(RF['keep'])} of the {RF['n']} stress regimes, namely {esc(RF['keep_names'])}. That is a bet on one neighbourhood, not a plan.</p>
""")
        + ftab
        + term
        + exec_episode_table()
        + callout("risk", "Five things that could change the answer", """
<ol>
<li><strong>The heir wants to live there.</strong> That is worth the whole gap if it is true. It also has to be true for the whole time: moving out removes the Proposition 19 exclusion.</li>
<li><strong>Law changes.</strong> On unofficial results as of 14 November 2026 (5:16 p.m.; counting continues), California voters approved Proposition 3, which makes the high-income tax rates permanent (60.7% yes), and rejected Proposition 40, the one-time billionaire tax (52.2% no). Certification is due by 11 December 2026. Both are on the <a href="laws.html">law page</a>. A future measure could cut the other way.</li>
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
                        + method_cell("#method", "Model output"))
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
            + method_cell("#method", "Model output"))
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
             "the sale proceeds can match it.")

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
             + method_cell("#method", "Model output"))

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
        + mixed_section()
        + reinvestment_section()
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
<li><strong>Mortgages, 1031 exchanges, instalment sales, gifting and trust restructuring.</strong> None are modelled. Each is on the <a href="questions.html">questions page</a>.</li>
<li><strong>Transaction costs of moving house, and the cost of capital gains tax on any other asset that would have to be sold.</strong> Not modelled.</li>
</ul>""")
    )


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
                    + method_cell("black-swan.html", "Model output"))
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
            + method_cell("precommit.html#method", "Model output"))
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
                 + method_cell("review.html#register", "Model output, condition unverified")
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
            + method_cell("review.html#register", "Household rule, not a figure"))
    rule_table = table(
        "The pre-commitment register: what decides each path, written before the figures",
        ["Rule", "Path", "The household chooses this path if...", "...but this would override it",
         "Decided on", "Decided by", "Where the figure is"],
        rule_rows,
        note="The two decision columns are deliberately empty. No path has been chosen. Fill them in "
             "by hand when the household decides, with the date, and keep the rule beside the decision "
             "so a future reader can see whether the rule was followed or changed.")

    goal_rows = []
    for g in goals:
        goal_rows.append(
            f"<td><strong>{esc(g['id'])}</strong></td><td><strong>{esc(g['goal'])}</strong></td>"
            f"<td>{esc(g['definition'])}</td>"
            f"<td>{g['priority']}</td>"
            f'<td><span class="blank">not yet agreed</span></td>'
            + method_cell("review.html#register", "Household objective, not a figure"))
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
            + method_cell("review.html#register", "Procedure, not a figure"))
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
                         + method_cell("#method", "Scenario, not a quote"))
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
            + method_cell("review.html#register", "Model output, rent unverified"))
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
        + src_cell([], "Owner estimate, unverified"),
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
        f"<td>Insurance, rental policy</td><td>{m(B['annual_costs']['insurance']['low'])}</td><td>{m(B['annual_costs']['insurance']['mid'])}</td>"
        f'<td><span class="badge unverified">owner estimate</span></td>' + src_cell(["cdi_tips"], "Where to get a quote"),
        f"<td>Maintenance and repair</td><td>not supplied</td><td>{m(MODEL['costs_b_now']['maintenance'])}</td>"
        f'<td><span class="badge assumption">assumption</span></td>' + src_cell([], "No official source"),
        f"<td>Property tax, today</td><td>&mdash;</td><td>{m(MODEL['costs_b_now']['property_tax'])}</td>"
        f'<td><span class="badge derived">derived</span></td>' + src_cell([], "Local rate withheld for privacy"),
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
                        + method_cell("#method", "Assumption, no quote"))
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
            + method_cell("#method", "Assumption, no quote"),
            "<td>Exterior paint and siding</td><td>7 to 10 years</td><td>No quote</td>"
            "<td>Predictable and deferrable, which is what makes it the usual casualty of a tight year.</td>"
            + method_cell("#method", "Assumption, no quote"),
            "<td>Water heater</td><td>10 to 15 years</td><td>No quote</td>"
            "<td>Emergency replacement; cannot be deferred and does not improve value.</td>"
            + method_cell("#method", "Assumption, no quote"),
            "<td>Furnace and ductwork</td><td>15 to 25 years</td><td>No quote</td>"
            "<td>An efficiency-driven replacement is larger than a like-for-like repair.</td>"
            + method_cell("#method", "Assumption, no quote"),
            "<td>Solar inverter and monitoring</td><td>10 to 15 years</td><td>No quote</td>"
            "<td>Property A has solar. The panels outlast the inverter, so an inverter replacement is likely "
            "inside a long hold and the net electricity benefit in the projection does not include it.</td>"
            + method_cell("#method", "Assumption, no quote"),
            "<td>Windows and doors</td><td>20 to 30 years</td><td>No quote</td>"
            "<td>Usually deferred to sale, which means a buyer discounts for it instead of the owner paying for it.</td>"
            + method_cell("#method", "Assumption, no quote"),
            "<td>Unit turnover: paint, flooring, appliances (Property B only)</td><td>On vacancy</td><td>No quote</td>"
            "<td>This is why a rental carries a higher rate than an owner-occupied home. It is also the item "
            "the letting path is most sensitive to, because it arrives when the tenant leaves, not on a schedule.</td>"
            + method_cell("#method", "Assumption, no quote"),
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
            + method_cell("#method", "Model output"))
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
<p>Two official series exist. The <strong>NAIC Homeowners Insurance Report</strong> (2023 data, published July
2026) is the state-level statistical series regulators use: average premium is written premium divided by written
exposures in house-years, as reported to statistical agents, for the dwelling fire and homeowners policy forms
separately. {slink('naic_hmr_2023')} The California Department of Insurance publishes its own statewide average
written premium from its Residential Property Insurance Report: about <strong>$1,070</strong> for an owner-occupied
homeowners policy in experience year 2017, which is the newest figure in that series read for this site.
{slink('cdi_homeowners_avg')} Both properties here are carried at {m(MODEL['costs_a_now']['insurance'])} a year,
which is an <strong>owner estimate</strong> and is flagged unverified.</p>
<p>Neither series is a premium for either building and neither must be read as one: a three-unit rental in the
city is written on a dwelling fire form and a single-family home in the county on a homeowners form, at entirely
different amounts of insurance. The NAIC report itself warns that average premium rises with the amount of
insurance and that dwelling fire premiums are generally lower than homeowners package premiums because the
coverage is more limited. A statewide average therefore <strong>understates</strong> a high-value home. The
report's own by-state averages sit in Table 4 (page 30 onward) and Table 5 (page 135); those pages were not
machine-readable in this build, so no average-premium figure from them is published here, under the rule that
nothing is inferred or copied second-hand. A property-specific premium remains blank until it is quoted.</p>
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
                    "<td>About $1,070 a year</td>" + src_cell(["cdi_homeowners_avg"], "Department of Insurance report"),
                ],
                note="These are market-wide published figures, not quotes and not estimates for either building. "
                     "The owner estimate used in the model is flagged unverified and should be replaced with quotes.")
        + table("Property B net income today",
                ["Item", "Amount", "Source"],
                [
                    f"<td>Rent received, two units</td><td>{m(net['rent'])}</td>" + src_cell([], "Owner statement, unverified"),
                    f"<td>Less water</td><td>{m(-net['water'])}</td>" + src_cell([], "Owner estimate; city schedule withheld for privacy"),
                    f"<td>Less electricity</td><td>{m(-net['electricity'])}</td>" + src_cell([], "Owner estimate, unverified"),
                    f"<td>Less insurance</td><td>{m(-net['insurance'])}</td>" + src_cell([], "Owner estimate, unverified"),
                    f"<td>Less maintenance at the assumed rate</td><td>{m(-net['maintenance'])}</td>" + src_cell([], "Assumption"),
                    f"<td>Less property tax</td><td>{m(-net['property_tax'])}</td>" + src_cell([], "Local rate withheld for privacy"),
                    f"<td><strong>Net, before income tax and vacancy</strong></td><td><strong>{m(net_now)}</strong></td>" + method_cell("#method", "Model output"),
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
        + capital_plan_section()
        + callout("flag", "Three cost numbers that need replacing", """
<ol>
<li><strong>Insurance on both properties.</strong> The state-level benchmark is the NAIC Homeowners Insurance
Report: the by-state averages for the correct policy form sit in its Table 4 (dwelling fire for Property B,
owner-occupied homeowners for Property A), but no average is a premium for either building, and neither the
Department nor the NAIC publishes an average for this postal area. Get three quotes for each building,
one of which should be a rental policy. See <a href="suggestions.html">suggestion S-01</a>.</li>
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
        + fan_section()
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
                else method_cell("review.html#register", "Private cost or deliberate omission"))
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
         "Proposition 3 is approved on unofficial results (60.7% yes as of 14 November 2026, 5:16 p.m.). It makes permanent the voter-approved rates on individuals earning over $371,000, adjusted for inflation, that would otherwise expire in 2031.",
         "Removes a scheduled state tax cut. A large gain on a California property sale will be taxed at the top state rate for the foreseeable future.",
         ["sos_results", "voterguide_p3"]),
        ("One-time tax on certain taxpayers rejected",
         "Proposition 40 failed on unofficial results (52.2% no as of 14 November 2026, 5:16 p.m.).",
         "No state wealth tax. Recorded because a later version could return.",
         ["sos_results", "voterguide_p40"]),
        ("Countermeasure to Proposition 40 rejected",
         "Proposition 41 failed on unofficial results (55.2% no as of 14 November 2026, 5:16 p.m.). It would have prohibited new state taxes that exclude revenues from the state spending limit.",
         "Its failure removes one of the two measures that could have voided the one-time tax if both had passed.",
         ["sos_results", "voterguide_p40"]),
        ("New state personal property taxes barred",
         "Proposition 42 is ahead on unofficial results (51.3% yes as of 14 November 2026, 5:16 p.m.). The margin is close and counting continues, so the outcome is not final.",
         "Narrows one route for a future state tax, but does not touch real property tax.",
         ["sos_results"]),
        ("Local revenue vote threshold rejected",
         "Proposition 43 failed on unofficial results (57.6% no as of 14 November 2026, 5:16 p.m.).",
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
of State with all 23,860 precincts partially reporting as of 14 November 2026, 5:16 p.m. Vote-by-mail,
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
                 + src_cell(d, "Official source") for a, b, c, d in enacted])
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

    # Status per proposal. The owner asked for a section where suggestions can be
    # reviewed and chosen before anything is implemented; this map is the record of
    # what the 15 November 2026 build actually did, so a reader can see which items
    # are still open rather than assuming the whole list is untouched.
    improve_status = {
        "Add a distribution chart to the projections": ("done", "Implemented: decile fan charts on the dashboard and the projections page, a histogram of the sell-minus-keep gap on the dashboard and the decision page, and the same distributions behind every headline share."),
        "Add a real rental opinion for Property A": ("open", "Still open. The site now publishes the rent at which occupying and letting each match selling, which is the closest substitute available without a rent opinion."),
        "Add a real rental opinion for Property A (imputed rent)": ("done", "Implemented as a range of rent scenarios plus a solved break-even, because no rent opinion exists yet."),
        "Add the itemised tax bills": ("open", "Still open: needs the parcel's own bill, which is not on the site."),
        "Add a liquidity model for the estate": ("open", "Still open: the scenario bands on the estate page are the current substitute."),
        "Add a two-person household case": ("open", "Still open."),
        "Add a mortgage case": ("open", "Still open."),
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
                   "Write the rules down before reading any projection": [],
                   "Put the answer and what would change it on the first screen": [],
                   "Price the transfer tax and recording fees into the sell path": ["rtc11911", "gov27388_1"],
                   "Distinguish enacted changes from proposals": ["sos_initiative_status"],
                   "Add per-unit detail for Property B": [],
                   "Add a real rental opinion for Property A": [],
                   "Add a maintenance and capital schedule": [],
                   "Add the itemised tax bills": [],
                   "Add a liquidity model for the estate": ["irs_estate", "irs_i706"],
                   "Add a two-person household case": ["irs_tc409", "irs_estate"],
                   "Add a mortgage case": [],
                   "Add a distribution chart to the projections": []}
    def improve_badge(a: str) -> str:
        state = improve_status.get(a, ("proposed", ""))
        return (f'<span class="badge verified">done</span>'
                f'<br><span class="small">{esc(state[1])}</span>'
                if state[0] == "done" else
                f'<span class="badge proposed">open</span>'
                + (f'<br><span class="small">{esc(state[1])}</span>' if state[1] else ""))

    improve_rows = [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td><td>{esc(c)}</td>"
                    f"<td>{improve_badge(a)}</td>"
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
                        ("Add a real rental opinion for Property A (imputed rent)", "Prints the market rent at which living there, and at which letting it out, match selling at the inheritance.", "Without it the housing value of living there is a preference rather than a number."),
                        ("Model mixed paths, not only the three pure choices", "Live for a period and then sell, or live and then let, with the Proposition 19 clawback priced.", "The pure paths overstate how bad a short occupancy is and understate what moving out costs."),
                        ("Write the rules down before reading any projection", "The household's own test for each path and its priorities, recorded before the figures are read.", "Without it a single projection can be made to justify any path."),
                        ("Put the answer and what would change it on the first screen", "A decision strip with the answer, a confidence label, the build date and the three checks that would move it.", "Readers arrive at the recommendation without knowing how conditional it is."),
                        ("Price the transfer tax and recording fees into the sell path", "The statutory charges itemised, with the published and private parts separated.", "The 5.5% selling cost is mistaken for a tax figure when most of it is a private quote."),
                        ("Distinguish enacted changes from proposals", "A stated rule and an annual recheck gate for the law page, with the failed Proposition 19 repeal recorded as dead.", "A proposal gets treated as law, or a dead measure keeps distorting the arithmetic."),
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
        ("Postal code of either property", "66", "0",
         "Present in superseded file versions and in the archive directory, which is never published."),
        ("Place name, or the county or city name", "917", "0",
         "Superseded file versions and archive material, plus every early version written before the county and "
         "city names were withdrawn. None of it is in the deployable artifact."),
        ("Dollar amount that is not a multiple of ten", "143", "0",
         "Superseded versions only. Every amount in the current tree is a multiple of ten or a verbatim "
         "published official amount."),
        ("Email address", "1", "0 published",
         "One internal working note carries a publisher's contact address in a quotation. The note is excluded "
         "from the deployable artifact, so no published file contains an email address."),
    ]
    body = [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(d)}</td>"
            + f'<td><a href="review.html#register">Logged in the register</a></td>' for a, b, c, d in rows]
    return (
        '<h2 id="history-audit">Privacy audit of this repository\'s own history</h2>'
        + callout("privacy", "What the history audit found, and what it did not do", """
<p>The published site is scanned on every build for names, street addresses, postal codes, parcel numbers,
telephone numbers, email addresses and property-level place names, and for any dollar figure that is not a
multiple of ten. That scan covers the deployable artifact, not the Git history behind it.</p>
<p>A separate read-only audit therefore walks every commit reachable in this repository and counts how many file
versions carry the <em>shape</em> of each identifier. It reports counts only. It does not print a matching value,
because publishing the value in order to disclose it would recreate exactly the exposure being disclosed.</p>
<p><strong>The result is that the current published tree is clean on every class, and the history is not clean on
three of them.</strong> No street address, parcel number or telephone number has ever been
committed. Postal codes and property-level place names did appear in superseded file versions and in archive
material, none of which is part of the published artifact. The full counts are below.</p>
<p>Cleaning the history is a different operation from cleaning the site: it needs a rewrite and a force-push of a
public branch, which invalidates every clone, every open pull request and every fork, and cannot recall copies
already downloaded. That is the owner's decision, it is recorded as an open item, and the procedure and its costs
are written up for the owner. Until that decision is taken, this page states the exposure rather than claiming it
has been removed.</p>""")
        + table("File versions whose content matches each identifier class",
                ["Identifier class", "File versions in history", "Matches in the published tree",
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
<li>The amount class is evaluated the way the live gate evaluates it: the formatted amount is parsed and its value
tested, so a rounded figure is never counted and a pre-rounding figure always is. Official statutory amounts are
exempted exactly as the gate exempts them.</li>
<li>The audit knows its own limits. It cannot see pull-request diffs, forks, or copies outside this repository, and
it cannot certify that a deleted object is unreachable on the hosting service.</li>
</ul>
</section>"""
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
        ("Insurance on both properties", m(A["annual_costs"]["insurance"]["mid"]) + " a year each",
         "Owner estimate. The state and industry benchmarks are statewide and across all amounts of insurance, not an average for this postal area, so the figure can be compared against published averages but not verified as the premium for this building. The NAIC by-state averages (Table 4 of the Homeowners Insurance Report) were not machine-readable in this build and are left blank on the costs page, not inferred.",
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
        ("Proposition H: not located, not modelled",
         "No figure on this site depends on it",
         "The brief asked for a measure it called Prop H to be modelled on its official terms. No measure "
         "by that name was found that applies to either property: the statewide November 2026 ballot is "
         "numbered 1 to 5 and 37 to 45 on the Secretary of State's own returns page, and no municipal or "
         "county measure could be searched by letter without naming the jurisdiction, which the privacy "
         "boundary forbids. The site therefore models none of it, and says so here rather than inventing "
         "terms for a measure it could not read.",
         "Ask the owner which measure the brief meant, and which jurisdiction's ballot it was on. If it is "
         "a local measure, supply its official text privately and it can be added without naming the "
         "jurisdiction."),
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
        "Insurance on both properties": ["cdi_homeowners_avg", "naic_hmr_2023"],
        "Maintenance on both properties": [],
        "Property B rent": [],
        "The inherited cash amount": [],
        "City transfer tax reduction proposal": [],
        "City documentary transfer tax on a sale of Property A": ["rtc11911"],
        "Commission, escrow and title as a share of the sale price": [],
        "Property A market rent, and therefore the imputed-rent credit": ["hud_fmr"],
        "Proposition H: not located, not modelled": ["sos_initiative_status"],
        "The Proposition 19 clawback on the live-then-let path": ["rtc63_2_eligibility", "boe_lta26026"],
        "Combined recapture rate, corrected from 41.1% to 42.1%": ["irs_tc409", "irs_tc559", "ftb_cg", "ftb_rates"],
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
         "They are published with all precincts partially reporting and are not certified until 11 December 2026. Proposition 3 is treated as approved (60.7% yes on unofficial results as of 14 November 2026, 5:16 p.m.) because it changes the tax rate on a sale, but the result must be confirmed at certification."),
        ("Combined tax rates are added, not interacted",
         "State and federal rates are added and no federal deduction is taken for state tax paid. That overstates the tax on a sale and therefore understates the case for selling, which is the conservative direction."),
        ("The housing value of living in the home is priced, not added",
         f"The living and letting paths bear their property tax and running costs in the terminal-value tables, "
         f"but are not credited with the housing they provide, and the sell paths are not charged for housing elsewhere. "
         f"The housing-value row prices the difference instead: on the 2045 baseline it is about "
         f"{m(next(p for p in MODEL['paths'] if p['inherit_year'] == 2045)['housing_value_needed'])} a year, a level "
         f"nominal amount. An earlier edition printed a figure about six times larger, because it used the "
         f"present-value form of the annuity on a future-value gap; that is corrected."),
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
        "No mortgage, no 1031 exchange, no instalment sale, no gifting": [],
        "The inheritance year is a range, not a date": [],
        "The property tax lesser-of rule is modelled only under the drawn inflation paths": ["rtc51", "boe_pub29", "fred_cpi"],
        "The Proposition 19 shelter path after 2027 is a projection": ["boe_lta25009"],
        "A sheltered base is assumed to survive a later move-out": ["rtc63_2_eligibility", "boe_prop19"],
        "Every reassessment figure is conditional on the parent-and-child relationship": ["rtc63_2_eligibility"],
        "The dated equity-entry backtest uses an academic return series": ["damodaran_histret", "fedhist_1929", "fedhist_greatrecession"],
        "Both properties are projected with the same state-level house price index": ["fred_casthpi", "fred_casthpi"],
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
         "The publishing route should be confirmed live after every change. The exclusion list is the control that keeps the rest of the repository out of the site."),
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
        ("The one-page brief has not been print-checked in a browser",
         "No browser is available in the build environment. The print rules were corrected on 15 November 2026 - the page-size rules had been conflicting (a later global margin overrode the general print margins) and are now a single default page plus a named page for the brief - but the printed pagination was not seen.",
         "Open the brief in a browser and print it to PDF before handing it to an adviser."),
        ("A personal e-mail address appears in commit metadata",
         "Git stores an author address with every commit. Earlier commits (83 of them) carry a personal e-mail address rather than the GitHub no-reply address now in use. It is not on any published page.",
         "Removing it from history needs a rewrite, which is the owner's decision. The runbook at scripts/history_scrub.sh covers the rewrite steps, including an author-address rewrite. For new commits, the account setting that keeps the address private is the owner's to change."),
        ("Pre-rounding history scrub is prepared as a runbook, not run",
         "scripts/history_scrub.sh audits the whole history for the identifier classes the privacy scanner guards and for candidate unrounded figures (found outside the repository, never written to the tree), and can run a git-filter-repo rewrite. The audit on 15 November 2026 found the identifier tokens still present in the visible history and one candidate figure. The scanner's own patterns were split into string fragments so the file text no longer carries any identifier.",
         "The rewrite itself rewrites every ref and needs a force-push to main, so it is the owner's to run or authorise. Until then, earlier commits, pull-request diffs and forks keep what they hold. The runbook carries the full post-rewrite checklist."),
    ]
    aud_rows = [f"<td><strong>{esc(a)}</strong></td><td>{esc(b)}</td><td>{esc(c)}</td>"
                + src_cell(rest[0] if rest else ["boe_lta25009", "irs_estate"], "Related sources")
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
        + '<h2>Modelling caveats</h2>'
        + table("Shortcuts that matter", ["Caveat", "What it means", "Source"], cav_rows)
        + '<h2>Repository audit</h2>'
        + table("What was found when the repository was reviewed",
                ["Finding", "Detail", "Residual risk", "Source"], aud_rows)
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
        ("Proposition 19", "The rule that the parent-child property-tax exclusion now applies only when the child makes the inherited home their principal residence, and shelters only value above the prior taxable value plus a biennial adjustment amount.", ["rtc63_2", "boe_prop19", "boe_lta25009"]),
        ("Proposition 19 parent-child exclusion", "A conditional California change-in-ownership exclusion, limited by statute and generally requiring the eligible transferee to use the transferred home as a principal residence and file a claim.", ["rtc63_2_eligibility", "boe_prop19"]),
        ("Reinvestment risk", "The risk that sale proceeds must be reinvested at lower returns than expected - for example, inheriting just before a stock-market crash and buying equities at the top. The phased-investing path on the black-swan page tests parking proceeds in short-term Treasuries for 24-36 months before buying stocks, with a synthetic stress and a dated backtest of the realized 1929, 2000 and 2008 returns.", ["fred_gs10", "damodaran_histret"]),
        ("Phased investing", "Selling the inherited home, holding the proceeds in 3-month to 2-year Treasury bills for 24-36 months, then buying equities in equal monthly pieces over the following 12 months. It softens the risk of entering the stock market at a 1929- or 2008-style peak; the black-swan page tests it synthetically and against realized returns.", ["fred_gs10", "damodaran_histret"]),
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
<div class="brief-toolbar"><p><strong>Print / save as PDF:</strong> use your browser's Print command. This sheet is formatted for one letter-size page.</p><p><strong>One-page printable Attorney &amp; CPA Briefing Sheet:</strong> this page is the single briefing sheet; the duplicate briefing-sheet.html was withdrawn on 15 November 2026.</p></div>
<p class="brief-confidential"><strong>Planning brief — placeholders only; no personal names, addresses, parcel IDs, trust terms or account figures.</strong></p>
<div class="brief-grid">
<section><h2>Decision in front of the family</h2>
<p>Property A is expected to pass through a trust around 2040–2050; Property B is already owned by the heir and currently has two rented units plus one available unit. Do not treat the inherited home as already owned or assume Property B rent is displaced by living there.</p>
<p>Current model direction: sell Property A soon after inheritance unless the heir genuinely wants to live in it. This is conditional—not advice—and depends on eligibility, title, tax basis, actual carrying costs, market rent and updated law. A 2045 illustration puts inherited-home value around {m(value)} and after-sale proceeds before reinvestment around {m(cash_net)}; both are model outputs, not appraisals or quotes.</p>
</section>
<section><h2>First questions for counsel and tax adviser</h2>
<ol>
<li>Does the trust actually own the property, and is the transferor-to-beneficiary relationship eligible for California's parent-child Proposition 19 exclusion? If not, full reassessment is assumed. {slink('rtc63_2_eligibility')} {slink('boe_prop19')}</li>
<li>What are the trust's distribution, sale, occupancy, debt and trustee powers? Confirm deed, trust amendments, successor-trustee process and authority to sell.</li>
<li>What is the date-of-death basis, appraisal standard and allocation between land/building? What is the cash estate, prior taxable gifts, marital portability and federal Form 706 filing position? {slink('irs_basis')} {slink('irs_estate')} {slink('irs_i706')}</li>
<li>Which home will be the heir's principal residence after transfer, and can occupancy/claim deadlines be met? Confirm eligibility and filing sequence with the assessor. {slink('boe_lta25009')}</li>
</ol>
</section>
<section><h2>Mixed paths and the clawback</h2>
<p>Living there for a period and then selling is the closest mixed path, and it still ends behind an immediate sale by {m(next(x for x in MIXED['paths'] if x['occupy_years'] == 5 and x['mode'] == 'sell')['gap_vs_sell_now'])} after five years. Moving out after claiming the Proposition 19 exclusion removes it: section 63.2(a)(1)(C) enrols the change-of-ownership base year value, costing about {m(MIXED['clawback']['difference'])} of extra property tax over thirty years on the live-then-let path. Both readings are published; ask counsel which applies.</p></section>
<section><h2>Known / unknown before choosing</h2>
<p><strong>Known from the supplied brief, not independently verified:</strong> owner-reported values, Property B rent and utilities, Property A water/solar estimate and historic tax-roll figures. <strong>Unknown:</strong> actual deed/title and trust terms, relationship eligibility, current insurance quotes, property-specific utilities, repairs/capital work, exact tax-rate areas, Property A market rent, selling costs, total taxable estate and future law.</p>
<p>Obtain certified tax bills and assessor records, title report, trust copy, date-of-death appraisal, insurer quotes for owner-occupied and rental uses, utility bills, property-condition inspection and a local rent opinion. Do not publish source documents or identifiers.</p>
</section>
<section><h2>Options and material risks</h2>
<ul><li>Live in Property A: possible reassessment shelter only if eligible and occupancy requirements are met; higher concentration and maintenance exposure.</li><li>Rent Property A: full reassessment may apply; income, vacancy, repairs, landlord rules and depreciation/recapture need a CPA-grade model.</li><li>Sell and reinvest: basis step-up may limit immediate gain, but confirm sale costs and tax. The published transfer tax and recording fees come to {m(MIXED['fees_example']['published_total'])} on a {m(MIXED['fees_example']['price'])} sale - about {MIXED['fees_example']['published_share_of_modelled']}% of the modelled 5.5% selling cost - and the $75 instrument fee does not apply to a sale that pays the transfer tax; reinvestment risk remains. The Black Swan page models 24/36-month Treasury parking and phased equity entry through one canonical monthly path: a synthetic stress test and a dated backtest of the realized 1929, 2000 and 2008 returns. Reinvestment yield may decline at maturity.</li><li>Property B remains an independent owned asset: include its net operating costs, insurance, rent/legal rules and available unit in household liquidity planning.</li></ul>
</section>
<section><h2>Timing / action sequence</h2>
<p>Before transfer: verify trust/deed, relationship eligibility, estate liquidity and insurance. At death/transfer: secure property, contact trustee/assessor/insurer, obtain date-of-death valuation, inventory expenses and confirm tax filing calendar. After title transfer: have counsel/CPA calendar assessor claim deadlines, income/estate returns, insurance endorsements and rental notices; model live/rent/sell choices with actual quotes before signing or distributing proceeds. Exact dates depend on transfer and filing facts.</p>
</section>
<section class="brief-glossary"><h2>Glossary</h2>
<p><strong>Basis step-up</strong>: generally resets inherited property tax basis to date-of-death value, subject to exceptions. <strong>Prop 19 exclusion</strong>: conditional California parent-child reassessment exclusion subject to statutory value and occupancy rules. <strong>Estate tax</strong>: federal tax on taxable estate, not a California inheritance tax. <strong>Reinvestment risk</strong>: future short-term Treasury proceeds may earn lower yields at maturity.</p>
</section>
</div>
<p class="brief-footer">For attorney / CPA discussion only. Laws and projections may change before 2040–2050. Sources and full assumptions: <a href="sources.html">source ledger</a>, <a href="questions.html">question register</a>, <a href="review.html">unverified items</a>, <a href="black-swan.html">phased-investing stress test</a>. No legal, tax or investment advice.</p>
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
                    + method_cell("precommit.html", "Household rule, not a figure"))
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
<strong>10 December 2026</strong> to avoid penalties. That is the only dated item on this page that falls in the
next year. Everything else is measured from the date of death or the date of transfer.</p>""")
        + '<p class="lede">Read in order. Each row is a legal or tax clock, and each names the official text it comes from.</p>'
        + tl
        + callout("answer", "Which deadlines can move the answer",
"""<p>The three deadlines that can change the recommendation are: (1) whether the parent-child relationship is in place before the transfer, because without it the Proposition 19 shelter disappears; (2) the one-year homeowners' exemption and three-year exclusion-claim windows, because missing them costs the shelter; and (3) the nine-month estate-tax return, because portability is normally lost when no timely return is filed - although an estate not otherwise required to file can use the simplified late election of Rev. Proc. 2022-32 within five years of death. The estate page works entirely in anonymous scenario bands because the inherited cash amount is not published.</p>""")
        + policy_section()
        + callout("method", "Why the order matters", """
<ol>
<li>The trust notice (60 days) and the change-in-ownership statement (150 days) are the first two clocks after death.</li>
<li>The federal return, if one is needed, comes at nine months, and Form 4768 is the only automatic way to extend it.</li>
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
                + method_cell("#method", "Model output"))

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
            + method_cell("black-swan.html", "Stress regime"))
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
                       + method_cell("#method", "Model output"))
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
        [f"<td>{a}</td><td>{b}</td>" + method_cell("#method", "Model output") for a, b in be_rows],
        note="A negative return means selling still matches living even if the sale proceeds lose that much a year.")

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
            "</ul>")
    return (
        callout("method", "How to use this page", f"""
<p>There are no sliders, because this site runs no script. Each case below is a link target. Choose one from the list,
or read the tables in order. Change one lever at a time, and the other stays at the baseline. Every figure is rounded
to the nearest $10 and comes from the same model that builds the rest of the site.</p>
{jump}""")
        + lever1 + lever2 + reg_table + yr_table + be_table
        + callout("flag", "What the cases do not show", """
<p>No case here credits the letting paths with a market rent, because none has been supplied. Read every letting row as
the path at zero rent, which is a floor. The model also does not change the Proposition 19 eligibility question; if
that answer is no, the reassessment is full and every case here moves toward selling.</p>""")
    )


PAGE_BUILDERS = {
    "index.html": (page_index, "Two California properties, one decision. Every figure rounded to the nearest $10."),
    "precommit.html": (page_precommit, "The household's rules, written before the figures are read."),
    "executive-summary.html": (page_executive_summary,
                               "The important details, the recommendation, and what would change it."),
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
    "laws.html": (page_laws, "Enacted, dead and proposed rules that could move the answer."),
    "black-swan.html": (page_black_swan, "Regimes where the answer changes, and by how much."),
    "economy.html": (page_economy, "Fifty years of verified inflation, house price and yield data."),
    "questions.html": (page_questions, "What is known, what is missing, and how to find it."),
    "suggestions.html": (page_suggestions, "A review queue of proposals. Nothing implemented yet."),
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
    a(f"Sold into equities or Treasuries wins {RF['sell']} of the {RF['n']} regimes. Keeping the house wins only in: "
      f"{RF['keep_names']}. That is a bet on one neighbourhood repeating its best decades, not a plan.")
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
