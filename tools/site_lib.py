#!/usr/bin/env python3
"""site_lib.py — shared shell, helpers and navigation for the static site."""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PAGES = os.path.join(ROOT, "pages")

with open(os.path.join(DATA, "model.json")) as f:
    M = json.load(f)

NAV = [
    ("index.html", "Dashboard"),
    ("pages/executive-summary.html", "Executive summary"),
    ("pages/inheritance-process.html", "Inheritance process"),
    ("pages/taxes.html", "Taxes &amp; law"),
    ("pages/cupertino.html", "Cupertino"),
    ("pages/san-francisco.html", "San Francisco"),
    ("pages/operating-costs.html", "Operating costs"),
    ("pages/projections.html", "Projections"),
    ("pages/decision-analysis.html", "Decision analysis"),
    ("pages/risks.html", "Risks &amp; law changes"),
    ("pages/sources.html", "Sources"),
    ("pages/flagged.html", "Flagged for review"),
]

CONFIDENTIALITY = (
    "Internal working document &middot; anonymised &middot; no personal identifying "
    "information is published on this site"
)


def money(x, dash="&mdash;", exact=False):
    """Round to the nearest $10 (the reporting convention for this project).

    exact=True keeps a verbatim statutory or cited amount unrounded - used for
    figures such as the $1,044,586 Prop 19 allowance, where rounding would
    misstate the law.
    """
    if x is None:
        return dash
    if x == 0:
        return "$0"
    neg = x < 0
    v = abs(x)
    v = int(round(v)) if exact else int(round(v / 10.0) * 10)
    return ("&minus;$" if neg else "$") + f"{v:,}"


def plain(x):
    if x is None:
        return "&mdash;"
    return f"{int(round(x)):,}"


def pct(x, dp=2):
    return f"{x * 100:.{dp}f}%"


_REL = {"v": "../"}


def set_rel(rel):
    """Called by the page builder so that source chips resolve from any depth."""
    _REL["v"] = rel


def src(sid, note=""):
    """A compact source chip linking to the register entry."""
    label = sid if not note else f"{sid} {note}"
    base = "pages/sources.html" if _REL["v"] == "" else "sources.html"
    return (f'<a class="srclink" href="{base}#{sid}" '
            f'title="Source {sid} — see the source register">{label}</a>')


def badge(text, kind="ok"):
    return f'<span class="badge b-{kind}">{text}</span>'


VERIFIED = badge("verified", "ok")
REPORTED = badge("reported", "rep")
ASSUMED = badge("assumption", "as")
UNVERIFIED = badge("unverified", "unv")


def table(headers, rows, caption="", cls="", foot=None, aligns=None):
    """rows: list of lists of cell HTML; a cell may be (html, css_class)."""
    out = ['<div class="tablewrap"><table class="%s">' % cls]
    if caption:
        out.append(f"<caption>{caption}</caption>")
    out.append("<thead><tr>")
    for i, h in enumerate(headers):
        a = ""
        if aligns and i < len(aligns):
            a = f' class="{aligns[i]}"'
        out.append(f"<th{a}>{h}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        rcls = ""
        if isinstance(r, tuple):
            r, rcls = r
        out.append(f'<tr class="{rcls}">' if rcls else "<tr>")
        for cell in r:
            if isinstance(cell, tuple):
                out.append(f'<td class="{cell[1]}">{cell[0]}</td>')
            else:
                out.append(f"<td>{cell}</td>")
        out.append("</tr>")
    out.append("</tbody>")
    if foot:
        out.append("<tfoot><tr>")
        for cell in foot:
            if isinstance(cell, tuple):
                out.append(f'<td class="{cell[1]}">{cell[0]}</td>')
            else:
                out.append(f"<td>{cell}</td>")
        out.append("</tr></tfoot>")
    out.append("</table></div>")
    return "".join(out)


def page(title, description, body, rel="", current=""):
    """Render a full HTML document.

    rel = "" for a root-level page, "../" for a page inside pages/.
    current = the page's path from the repository root (used for nav state).
    """
    nav = []
    for href, label in NAV:
        if rel == "":
            h = href
        elif href == "index.html":
            h = "../index.html"
        elif href.startswith("pages/"):
            h = href[len("pages/"):]
        else:
            h = href
        cur = ' aria-current="page"' if href == current else ""
        nav.append(f'<a href="{h}"{cur}>{label}</a>')
    navhtml = "".join(nav)
    set_rel(rel)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &middot; Inheritance Decision Dashboard</title>
<meta name="description" content="{description}">
<link rel="stylesheet" href="{rel}assets/style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='7' fill='%2314507a'/><path d='M8 21l6-9 4 6 3-4 3 7z' fill='%23fff'/></svg>">
</head>
<body>
<div class="confbar"><div class="wrap"><strong>Internal use only</strong><span>{CONFIDENTIALITY}</span></div></div>
<header class="masthead"><div class="wrap">
<p class="eyebrow">Cupertino 95014 &middot; San Francisco 94122 &middot; inheritance planning 2040&ndash;2050</p>
<h1>{title}</h1>
<p class="sub">{description}</p>
</div></header>
<nav class="main" aria-label="Sections"><div class="wrap">{navhtml}</div></nav>
<main><div class="wrap">
{body}
</div></main>
<footer class="site"><div class="wrap">
<div><strong>Inheritance Decision Dashboard</strong><br>
Model v{M['meta']['model_version']} &middot; built {M['meta']['build_date']} &middot; all figures rounded to the nearest $10</div>
<div>Not legal, tax or investment advice. Confirm every figure against your own documents and a licensed California attorney or CPA.<br>
<a href="{rel}pages/flagged.html">Flagged for review</a> &middot; <a href="{rel}pages/sources.html">Source register</a> &middot; <a href="{rel}pages/executive-summary.html">Executive summary</a></div>
</div></footer>
</body>
</html>
"""


def write(rel_path, html):
    path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(html)
    return path


def pager(rel, prev_href, prev_label, next_href, next_label):
    a = f'<span>&larr; <a href="{prev_href}">{prev_label}</a></span>' if prev_href else "<span></span>"
    b = f'<span><a href="{next_href}">{next_label}</a> &rarr;</span>' if next_href else "<span></span>"
    return f'<div class="pager">{a}{b}</div>'
