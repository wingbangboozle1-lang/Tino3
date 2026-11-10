"""Static site builder: shell, helpers, page registry, build loop."""
from __future__ import annotations
import html as _html
import json
import shutil
from pathlib import Path

from sources import SOURCES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT
DATA = json.loads((ROOT / "data" / "model_outputs.json").read_text())

NAV = [
    ("index.html", "Dashboard", "Overview and recommendation"),
    ("executive-summary.html", "Executive summary", "The whole case on one page"),
    ("properties.html", "Properties", "Facts, roll history, reconciliation"),
    ("property-tax.html", "Property tax", "Prop 13 / Prop 19 and forward values"),
    ("operating-costs.html", "Running costs", "Insurance, water, power, repairs"),
    ("taxes-estate.html", "Taxes & estate", "Federal, state, local, step-up"),
    ("projections.html", "Projections", "2026-2055 year by year"),
    ("decision-analysis.html", "Decision analysis", "Live vs rent vs sell, after tax"),
    ("inheritance-process.html", "Inheritance process", "Step by step with deadlines"),
    ("laws-watch.html", "Laws & watch list", "Enacted, scheduled, proposed"),
    ("flagged-for-review.html", "Flagged for review", "Unverified values and gaps"),
    ("sources.html", "Source library", "Every link used, with scope"),
    ("privacy.html", "Privacy", "What is published and what is not"),
]

SHORT = {
    "IRS-ESTATE": "IRS estate tax",
    "IRS-2027": "IRS IR-2026-133",
    "IRS-BASIS": "IRS basis FAQ",
    "IRS-T409": "IRS Topic 409",
    "IRS-T701": "IRS Topic 701",
    "IRS-P527": "IRS Pub 527",
    "BOE-P19": "BOE Prop 19",
    "BOE-CAP": "BOE NR 25-02",
    "SCC-ASSESSOR": "SCC Assessor 2026",
    "SF-TTC": "SF Tax Collector",
    "SF-PARCEL": "SF parcel taxes",
    "SF-RENT": "SF Rent Board",
    "SFPUC": "SFPUC rates",
    "CPUC-NEM": "CPUC NEM/NBT",
    "CDI-SIS": "CDI market snapshot",
    "CDI-2026": "CDI 2026 alert",
    "RTC-13301": "RTC 13301",
    "RTC-51": "RTC 51",
    "RTC-480": "RTC 480",
    "PROB-16061": "Prob. Code 16061.7",
    "FTB-RATES": "FTB rate schedules",
    "TREASURY": "U.S. Treasury",
    "BLS-CPI": "BLS CPI",
    "FHFA-HPI": "FHFA/FRED HPI",
}


def esc(s) -> str:
    return _html.escape(str(s), quote=False)


INTERNAL = {"OWNER", "COMPUTED"}


def link(src_id: str, label: str | None = None) -> str:
    s = SOURCES[src_id]
    text = label or SHORT.get(src_id, src_id)
    if src_id in INTERNAL:
        return f'<a href="{s["url"]}" class="internal">{esc(text)}</a>'
    return (f'<a href="{s["url"]}" target="_blank" rel="noopener noreferrer">{esc(text)}'
            f'<span class="ext" aria-hidden="true">\u2197</span></a>')


def links(*ids: str) -> str:
    return " ".join(link(i) for i in ids)


def money(x, dash="--") -> str:
    """Every computed amount is displayed rounded to the nearest $10."""
    if x is None or x == "":
        return dash
    try:
        v = float(x)
    except (TypeError, ValueError):
        return esc(x)
    r = round(v / 10.0) * 10
    return ("\u2212$" if r < 0 else "$") + f"{abs(r):,.0f}"


def exact(x, prefix="") -> str:
    """Verbatim display for statutory or officially published amounts."""
    return f"{prefix}${float(x):,.0f}" if float(x) == int(float(x)) else f"{prefix}${x}"


def pct(x, places: int = 2) -> str:
    if x is None or x == "":
        return "--"
    return f"{float(x) * 100:.{places}f}%"


def table(headers, rows, *, cls="", note=None, caption=None) -> str:
    """rows: list of (cells..., sources). sources may be a str id, list of ids, or HTML."""
    out = [f'<div class="tw"><table class="{cls}">']
    if caption:
        out.append(f"<caption>{caption}</caption>")
    out.append("<thead><tr>" + "".join(f'<th scope="col">{esc(h)}</th>' for h in headers) + "</tr></thead>")
    out.append("<tbody>")
    for row in rows:
        cells = list(row)
        src = cells.pop() if cells else ""
        if isinstance(src, str) and src.strip().startswith("<a "):
            srchtml = src
        elif isinstance(src, str) and src in SOURCES:
            srchtml = link(src)
        elif isinstance(src, (list, tuple)):
            srchtml = links(*src)
        else:
            srchtml = esc(src)
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells)
                   + f'<td class="src">{srchtml}</td></tr>')
    out.append("</tbody></table></div>")
    if note:
        out.append(f'<p class="tnote">{note}</p>')
    return "\n".join(out)


def section(title, body, *, sub=None, sid=None) -> str:
    idattr = f' id="{sid}"' if sid else ""
    subhtml = f'<p class="sub">{sub}</p>' if sub else ""
    return f'<section{idattr}><h2>{title}</h2>{subhtml}{body}</section>'


def callout(kind, title, body) -> str:
    return (f'<div class="callout {kind}"><p class="ctitle">{title}</p>{body}</div>')


def page(filename, title, body, *, active, description, crumbs=None) -> str:
    nav = []
    for i, (href, label, hint) in enumerate(NAV, start=1):
        cur = ' aria-current="page"' if href == active else ""
        nav.append(f'<a href="{href}"{cur}><span class="n">{i:02d}</span>'
                   f'<span><b>{esc(label)}</b><small>{esc(hint)}</small></span></a>')
    crumb = ""
    if crumbs:
        crumb = '<nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">Dashboard</a> / ' + \
                " / ".join(crumbs) + "</nav>"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} \u00b7 Inheritance Decision Atlas</title>
<meta name="description" content="{esc(description)}">
<meta name="referrer" content="no-referrer">
<meta name="robots" content="index,follow">
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar">
  <a class="brand" href="index.html"><span class="mark">IDA</span>
    <span class="bt">Inheritance<br>Decision Atlas</span></a>
  <button class="navtoggle" aria-expanded="false" aria-controls="nav">Menu</button>
  <nav id="nav" class="nav" aria-label="Sections">
    {''.join(nav)}
  </nav>
</header>
<main id="main">
{crumb}
{body}
<footer class="foot">
  <p><b>Inheritance Decision Atlas</b> \u00b7 planning model reviewed 10 November 2026 \u00b7 all amounts rounded to the nearest $10.</p>
  <p>General information for planning, not legal, tax, investment or fiduciary advice. Values marked
  <span class="tag unv">UNVERIFIED</span> come from the property owner and are not checked against a public record.
  See <a href="flagged-for-review.html">Flagged for review</a> and <a href="privacy.html">Privacy</a>.</p>
</footer>
</main>
<script src="assets/site.js"></script>
</body>
</html>
"""


def write(filename, html_text):
    (OUT / filename).write_text(html_text, encoding="utf-8")


def build():
    import pages_core, pages_money, pages_decide
    pages = []
    pages += pages_core.PAGES
    pages += pages_money.PAGES
    pages += pages_decide.PAGES
    for fn, title, body, active, desc in pages:
        write(fn, page(fn, title, body, active=active, description=desc))
    print(f"site: built {len(pages)} pages")


if __name__ == "__main__":
    build()
