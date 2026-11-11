#!/usr/bin/env python3
"""Render the requirements-traceability edition from the JSON ledgers.

Every table row ends with a Basis badge and at least one link to an official publisher.
Values that could not be confirmed from an official source are left blank and flagged.
"""
from __future__ import annotations
import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
e = html.escape

SOURCES = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
SRC = SOURCES["sources"]
REQS = json.loads((DATA / "requirements.json").read_text(encoding="utf-8"))
SUMMARY = json.loads((DATA / "summary.json").read_text(encoding="utf-8"))["summary"]
FLAGS = json.loads((DATA / "flags.json").read_text(encoding="utf-8"))["flags"]
CATS = json.loads((DATA / "categories.json").read_text(encoding="utf-8"))["categories"]
PUB = json.loads((DATA / "publication.json").read_text(encoding="utf-8"))

SHORT = {
    "Internal Revenue Service": "IRS",
    "California State Board of Equalization": "BOE",
    "California Legislative Information": "CA code",
    "California Franchise Tax Board": "FTB",
    "California State Controller": "CA Controller",
    "California Public Utilities Commission": "CPUC",
    "California Department of Insurance": "CDI",
    "California Legislative Analyst's Office": "LAO",
    "California Secretary of State": "CA SOS",
    "City B Treasurer and Tax Collector": "City B Treasurer",
    "City B Rent Board": "City B Rent Board",
    "County A Controller-Treasurer": "County A",
    "U.S. Government Publishing Office (GovInfo)": "US Code (GPO)",
    "Board of Governors of the Federal Reserve System": "Federal Reserve",
    "Social Security Administration": "SSA",
    "Congressional Budget Office": "CBO",
    "Bureau of Labor Statistics": "BLS",
    "Federal Reserve History": "Fed History",
    "Federal Reserve Bank of St. Louis (data: Federal Housing Finance Agency)": "FHFA index",
    "Federal Retirement Thrift Investment Board": "TSP",
    "U.S. Department of the Treasury": "US Treasury",
    "U.S. Department of Housing and Urban Development": "HUD",
    "GitHub Docs": "GitHub Docs",
}

NAV = [("index.html", "Requirements map"), ("executive-summary.html", "Executive summary"),
       ("findings.html", "Official-source findings"), ("flagged.html", "Flagged for review")]

LABELS = {
    "../index.html": "Root dashboard", "../executive-summary.html": "Root executive summary",
    "../decision.html": "Decision analysis", "../projections.html": "Year-by-year projections",
    "../black-swans.html": "Black-swan conditions", "../stress.html": "Black-swan stress tests",
    "../property-a.html": "Property A", "../property-b.html": "Property B",
    "../taxes.html": "Tax, thresholds, law watch", "../inheritance.html": "Inheritance steps",
    "../review.html": "Root flagged review", "../audit.html": "Independent verification",
    "../sources.html": "Root source library", "../plan/index.html": "Cross-check edition",
    "../analysis/index.html": "50-year suite", "../analysis/projections.html": "50-year projections",
    "../analysis/ownership-distinction.html": "Ownership distinction",
    "../analysis/black-swan.html": "50-year black-swan regimes",
    "../analysis/decision.html": "50-year decision matrix",
    "index.html": "Requirements map", "executive-summary.html": "Executive summary",
    "findings.html": "Official-source findings", "flagged.html": "Flagged for review",
}


def s_link(sid: str) -> str:
    s = SRC[sid]
    pub = SHORT.get(s["publisher"], s["publisher"])
    return f'<a href="{e(s["url"])}" target="_blank" rel="noopener noreferrer">{e(pub)} &middot; {e(s["title"])}</a>'


def i_link(path: str, label: str | None = None) -> str:
    return f'<a href="{e(path)}">{e(label or LABELS.get(path, path))}</a>'


def page_links(paths: list[str]) -> str:
    return " ".join(i_link(p) for p in paths)


def badge(basis: str) -> tuple[str, str]:
    b = basis.lower()
    if "verified" in b:
        return "b-v", basis
    if "owner" in b:
        return "b-o", basis
    if "assum" in b or "scenario" in b:
        return "b-a", basis
    if "comput" in b:
        return "b-c", basis
    if "unverified" in b or "pending" in b or "needs review" in b:
        return "b-u", basis
    return "b-c", basis


def table(caption: str, headers: list[str], rows: list[dict]) -> str:
    hd = "".join(f'<th scope="col">{e(h)}</th>' for h in headers + ["Basis", "Official source"])
    body = []
    for row in rows:
        assert row["sources"], f"row without an official source: {row}"
        cells = row["cells"]
        if len(cells) != len(headers):
            raise AssertionError(f"cell count mismatch in {caption}: {cells}")
        tds = "".join(f"<td>{c}</td>" for c in cells)
        cls, text = badge(row["basis"])
        tds += f'<td><span class="b {cls}">{e(text)}</span></td>'
        tds += f'<td>{"".join(s_link(s) for s in row["sources"])}</td>'
        body.append(f"<tr>{tds}</tr>")
    return ('<div class="table-wrap"><table><caption>' + e(caption) + '</caption><thead><tr>' + hd +
            '</tr></thead><tbody>' + "".join(body) + '</tbody></table></div>')


def page(name: str, title: str, eyebrow: str, h1: str, lead: str, body: str) -> str:
    nav = []
    for i, (path, label) in enumerate(NAV, 1):
        cur = ' aria-current="page"' if path == name else ""
        nav.append(f'<a href="{path}"{cur}><span>{i:02d}</span> {e(label)}</a>')
    nav_html = "".join(nav)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} &middot; Inheritance decision dashboard</title>
<link rel="stylesheet" href="../assets/style.css"></head>
<body><a class="skip" href="#main">Skip to content</a>
<aside><a class="brand" href="../index.html">Inheritance decision dashboard<small>Property A and Property B</small></a>
<div class="nav-label">PAGES</div><nav>{nav_html}</nav>
<div class="nav-label">MORE</div><nav><a href="../index.html">Root dashboard</a><a href="../sources.html">Root sources</a><a href="../review.html">Root flags</a></nav>
<div class="aside-note">Anonymised. Dollar figures rounded to $10. Reviewed 11 November 2026.</div></aside>
<main id="main"><div class="top"><span>{e(eyebrow)}</span><span>Reviewed 11 Nov 2026</span></div>
<div class="hero"><div class="eyebrow">{e(eyebrow)}</div><h1>{e(h1)}</h1><p>{e(lead)}</p></div>
{body}
<footer><span>Requirements traceability &middot; {e(PUB["session"])}</span>
<span>{i_link("../index.html")} &middot; {i_link("../plan/index.html", "Cross-check")} &middot; {i_link("../analysis/index.html", "50-year suite")}</span></footer>
</main></body></html>
'''


LEGEND = ('<p class="legend"><span class="b b-v">Verified</span> read on the publisher\'s own domain. '
          '<span class="b b-o">Owner-supplied</span> household record, not independently checked. '
          '<span class="b b-a">Assumption</span> or scenario input. <span class="b b-c">Computed</span> arithmetic on published rows. '
          '<span class="b b-u">Unverified</span> no official confirmation, so the value is blank. '
          'A link on an owner-supplied, assumed or computed row points to the official rule or series the row rests on; it does not confirm the value.</p>')

PRIV = ('<div class="privacy"><strong>Privacy.</strong> ' + e(PUB["privacy"]) + '</div>')


# --------------------------------------------------------------------------------------------- landing page
cat_cards = "".join(
    f'<div class="card"><div class="k">{e(c["label"])}</div><p>{e(c["description"])}<br>{i_link(c["page"], "Open")}</p></div>'
    for c in CATS)
req_rows = []
for r in REQS["requirements"]:
    req_rows.append({
        "cells": [e(r["id"]), e(r["category"]), e(r["text"]), page_links(r["pages"]), e(r["value"]), e(r["status"])],
        "basis": r["basis"], "sources": r["sources"],
    })
body = f'''
<div class="answer"><p><strong>Best plan on these numbers: sell Property A soon after inheriting, reinvest the proceeds, and keep Property B.</strong></p>
<p>This section is an index and a check, not a fourth financial model. It maps every numbered brief item to the page that answers it, records the official source opened for it, and leaves unverified values blank.</p></div>
<div class="cards">{cat_cards}</div>
<section><h2>Requirements traceability</h2>
<p>One row per item in the owner's brief. "Answer page" opens the published page; "Official source" opens the publisher's own domain for manual review.</p>
{table("Full requirements matrix", ["ID", "Category", "Brief item", "Answer page", "Value on site", "Status"], req_rows)}
{LEGEND}</section>
<section><h2>What this section checks</h2>
<p>{e(PUB["verification"])}</p>
<p>{e(PUB["coordination"])} The publication path is described by {s_link("github_pages")} and the integration method by {s_link("github_pr")}.</p>
{PRIV}</section>
'''
PAGES = {"index.html": page("index.html", "Requirements map", "Requirements & verification",
                           "Every requirement, one row",
                           "A privacy-safe traceability matrix, an independent official-source log, and a flagged-review page for the inheritance decision dashboard.", body)}

# --------------------------------------------------------------------------------------------- executive summary
sum_rows = [{
    "cells": [e(r["topic"]), e(r["finding"]), e(r["value"]), e(r["note"])],
    "basis": r["basis"], "sources": r["sources"],
} for r in SUMMARY]
body = f'''
<div class="answer"><p><strong>Sell Property A after inheriting, reinvest, and keep Property B.</strong> The figures below are $10-rounded scenario arithmetic, not appraisals or forecasts.</p></div>
{table("Important details", ["Topic", "Finding", "Value", "Note"], sum_rows)}
{LEGEND}
<section><h2>Limits</h2><p>Insurance premiums, property-specific water and electricity use, the deed, the trust instrument, the estate's cash balance and future thresholds are not verifiable from public sources today. They are left blank on {i_link("../review.html", "the root flagged page")} and {i_link("flagged.html", "here")}.</p>{PRIV}</section>
'''
PAGES["executive-summary.html"] = page("executive-summary.html", "Executive summary", "Requirements & verification",
                                       "What matters, in one table",
                                       "The decision, the numbers behind it, and the official rule or series behind each row.", body)

# --------------------------------------------------------------------------------------------- official-source findings
find_rows = []
for sid, s in SRC.items():
    find_rows.append({
        "cells": [e(sid), e(s["publisher"]), e(s["title"]), e(s["quote"]), e(s["supports"]), e(s["checked"]), e(s["status"])],
        "basis": s["status"], "sources": [sid],
    })
body = f'''
<div class="note"><strong>Independent verification.</strong> {len(SRC)} official sources were opened on the publisher's own domain on 11 November 2026. The exact words relied on and how each document was checked are recorded below. No search snippet, secondary source or insurer quote is treated as verified.</div>
{table("Official-source verification ledger", ["ID", "Publisher", "Document", "Exact words relied on", "What it supports", "How it was checked", "Status"], find_rows)}
{LEGEND}
<section><h2>Method</h2><p>{e(SOURCES["method"])}</p>{PRIV}</section>
'''
PAGES["findings.html"] = page("findings.html", "Official-source findings", "Requirements & verification",
                              "Every source, and how it was checked",
                              "Open any publisher link to check the wording yourself. This is the independent ledger for the requirements matrix.", body)

# --------------------------------------------------------------------------------------------- flagged for review
flag_rows = [{
    "cells": [e(f["id"]), e(f["item"]), e(f["status"]), e(f["value"]), e(f["settles"]), e(f["note"])],
    "basis": f["status"], "sources": f["sources"],
} for f in FLAGS]
body = f'''
<div class="answer"><p><strong>Nothing on this page blocks the plan or the merge.</strong> Each value that could not be confirmed from an official source is left blank rather than estimated.</p></div>
{table("Flagged for review", ["ID", "Item", "Status", "Value", "What settles it", "Note"], flag_rows)}
{LEGEND}
<section><h2>Owner decisions</h2><ul>
<li>Whether to rewrite repository history or make the repository private ({s_link("github_pages")}).</li>
<li>Whether to keep the local official links that identify jurisdictions, at the cost of weaker privacy ({s_link("cityb_rate")}, {s_link("cnty_a_rates")}).</li>
<li>Whether assessed values and bills should return to $10 precision, as the brief asks ({s_link("boe_lta26002")}).</li>
<li>Whether to obtain two written insurance quotes at replacement cost ({s_link("cdi_compare")}).</li>
<li>Whether to wait for the certified 3 November 2026 election result ({s_link("sos_results")}).</li>
</ul>{PRIV}</section>
'''
PAGES["flagged.html"] = page("flagged.html", "Flagged for review", "Requirements & verification",
                             "Unverified, unknown or irregular",
                             "Values left blank, irregularities, and the decisions only the owner can settle, each with an official source link.", body)

# --------------------------------------------------------------------------------------------- reproducible outputs
for name, text in PAGES.items():
    (ROOT / name).write_text(text, encoding="utf-8")


def write_csv(name: str, headers: list[str], rows: list[list[str]]) -> None:
    with (DATA / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(headers)
        w.writerows(rows)


write_csv("requirements.csv", ["id", "category", "brief_item", "answer_pages", "value", "status", "basis", "official_sources", "note"],
          [[r["id"], r["category"], r["text"], "|".join(r["pages"]), r["value"], r["status"], r["basis"],
            "|".join(SRC[s]["url"] for s in r["sources"]), r["note"]] for r in REQS["requirements"]])
write_csv("summary.csv", ["topic", "finding", "value", "basis", "official_sources", "note"],
          [[r["topic"], r["finding"], r["value"], r["basis"], "|".join(SRC[s]["url"] for s in r["sources"]), r["note"]] for r in SUMMARY])
write_csv("findings.csv", ["id", "publisher", "document", "url", "quote", "supports", "checked", "status", "category"],
          [[sid, s["publisher"], s["title"], s["url"], s["quote"], s["supports"], s["checked"], s["status"], s["category"]]
           for sid, s in SRC.items()])
write_csv("flagged.csv", ["id", "item", "status", "value", "settles", "basis", "official_sources", "note"],
          [[f["id"], f["item"], f["status"], f["value"], f["settles"], f["status"],
            "|".join(SRC[s]["url"] for s in f["sources"]), f["note"]] for f in FLAGS])

print(f"built {len(PAGES)} pages; {len(REQS['requirements'])} requirements; {len(SRC)} sources; {len(SUMMARY)} summary rows; {len(FLAGS)} flags")
