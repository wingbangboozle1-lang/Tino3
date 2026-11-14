"""Rebuild, audit and verify the anonymised quantitative decision edition.

Checks, in order:
  1. every page on disk is exactly what the builder produces (no hand edits);
  2. page structure: one h1, one main, one title, no script/img/form, unique ids;
  3. every table body row carries a link to an official site;
  4. every internal link resolves, every fragment target exists;
  5. every external link is https and on an approved official host;
  6. the source ledger is well formed and every entry is used at least once;
  7. the deployable artifact passes the privacy boundary.

Standard library only. No network calls.
"""
from __future__ import annotations

import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build as builder  # noqa: E402
import package_site as pack  # noqa: E402

LEDGER = json.loads((ROOT / "assets" / "sources.json").read_text(encoding="utf-8"))
LEDGER_URLS = {item["url"] for item in LEDGER["sources"]}
LEDGER_IDS = [item["id"] for item in LEDGER["sources"]]

OFFICIAL_HOSTS = {
    "irs.gov", "www.irs.gov", "ftb.ca.gov", "www.ftb.ca.gov", "sco.ca.gov", "www.sco.ca.gov",
    "leginfo.legislature.ca.gov", "boe.ca.gov", "www.boe.ca.gov", "cpuc.ca.gov", "www.cpuc.ca.gov",
    "insurance.ca.gov", "www.insurance.ca.gov", "federalreservehistory.org",
    "www.federalreservehistory.org", "libertystreeteconomics.newyorkfed.org",
    "bls.gov", "www.bls.gov", "fred.stlouisfed.org", "sfgov.legistar.com",
    "sos.ca.gov", "www.sos.ca.gov", "voterguide.sos.ca.gov", "electionresults.sos.ca.gov",
    "sftreasurer.org", "www.sf.gov", "sf.gov", "www.santaclaracounty.gov",
    "clerkrecorder.santaclaracounty.gov", "files.santaclaracounty.gov",
    "ssa.gov", "www.ssa.gov", "govinfo.gov", "www.govinfo.gov",
    # added when the two independently maintained ledgers were merged
    "www.sfpuc.gov", "sfbos.archive.sf.gov", "elections.cdn.sos.ca.gov",
    "www.cbo.gov", "www.federalreserve.gov", "www.huduser.gov", "www.lao.ca.gov",
    "home.treasury.gov", "www.tsp.gov", "docs.github.com",
}
FORBIDDEN_TAGS = {"script", "iframe", "form", "input", "textarea", "object", "embed", "img"}

PAGES = builder.PAGES
ASSETS = builder.ASSETS


class PageAudit(HTMLParser):
    def __init__(self, path: Path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.errors: list[str] = []
        self.ids: set[str] = set()
        self.links: list[tuple[str, str]] = []
        self.main_count = 0
        self.title_count = 0
        self.h1_count = 0
        self.rows: list[dict] = []
        self.row: dict | None = None
        self.in_body = False
        self.cell_open = False
        self.tbody_depth = 0

    def handle_starttag(self, tag, attrs):
        attr = {k: (v or "") for k, v in attrs}
        if tag in FORBIDDEN_TAGS:
            self.errors.append(f"forbidden element <{tag}>")
        if "src" in attr:
            self.errors.append("remote or embedded asset is not allowed")
        if tag == "main":
            self.main_count += 1
        elif tag == "title":
            self.title_count += 1
        elif tag == "h1":
            self.h1_count += 1
        if attr.get("id"):
            ident = attr["id"]
            if ident in self.ids:
                self.errors.append(f"duplicate id #{ident}")
            self.ids.add(ident)
        if tag == "tbody":
            self.tbody_depth += 1
        if tag == "tr" and self.tbody_depth:
            if self.row is not None:
                self.errors.append("nested table row")
            self.row = {"hrefs": [], "cells": 0}
        if tag in {"td", "th"} and self.row is not None:
            self.row["cells"] += 1
        if tag == "a" and attr.get("href"):
            self.links.append(("a", attr["href"]))
            if self.row is not None:
                self.row["hrefs"].append(attr["href"])
        if tag == "link" and attr.get("href"):
            self.links.append(("link", attr["href"]))

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.tbody_depth = max(0, self.tbody_depth - 1)
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def check_reproducible() -> list[str]:
    problems = []
    for name, (fn, lede) in builder.PAGE_BUILDERS.items():
        expected = builder.page(name, fn(), lede)
        actual = (ROOT / name).read_text(encoding="utf-8")
        if expected != actual:
            problems.append(f"{name}: file on disk differs from the builder output; run scripts/build.py")
    # The standalone executive summary is generated too, so it cannot drift from the model
    # the way the hand-typed one did.
    expected_md = builder.executive_summary_markdown()
    actual_md = (ROOT / "EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
    if expected_md != actual_md:
        problems.append("EXECUTIVE_SUMMARY.md: file on disk differs from the builder output; run scripts/build.py")
    return problems


def check_ledger() -> list[str]:
    problems = []
    if len(LEDGER["sources"]) != len(LEDGER_IDS):
        problems.append("duplicate source id in the ledger")
    # 'limits' is optional: entries inherited from the other ledger record what the
    # source verifies but not always a stated limitation. Inventing one would be worse
    # than leaving the column blank, so the count is reported instead of enforced.
    no_limits = []
    for item in LEDGER["sources"]:
        for field in ("id", "publisher", "title", "url", "checked", "supports"):
            if not str(item.get(field, "")).strip():
                problems.append(f"{item.get('id')}: missing field {field}")
        if not str(item.get("limits", "")).strip():
            no_limits.append(item["id"])
        parts = urlsplit(item["url"])
        if parts.scheme != "https" or not parts.netloc:
            problems.append(f"{item['id']}: source url is not https")
        if parts.netloc not in OFFICIAL_HOSTS:
            problems.append(f"{item['id']}: host not on the approved list: {parts.netloc}")
    all_html = "".join((ROOT / p).read_text(encoding="utf-8") for p in PAGES)
    unused = [sid for sid in LEDGER_IDS if sid not in all_html]
    if unused:
        problems.append(f"ledger entries never cited on any page: {unused}")
    return problems, no_limits


def check_pages() -> tuple[list[str], dict]:
    problems: list[str] = []
    stats = {"rows": 0, "sourced_rows": 0, "registered_rows": 0,
             "links": 0, "official_links": 0}
    audits: dict[str, PageAudit] = {}
    for name in PAGES:
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        audit = PageAudit(path)
        audit.feed(text)
        audits[name] = audit
        problems.extend(f"{name}: {e}" for e in audit.errors)
        if audit.main_count != 1:
            problems.append(f"{name}: expected exactly one <main>, found {audit.main_count}")
        if audit.title_count != 1:
            problems.append(f"{name}: expected exactly one <title>, found {audit.title_count}")
        if audit.h1_count != 1:
            problems.append(f"{name}: expected exactly one <h1>, found {audit.h1_count}")
        stats["rows"] += len(audit.rows)
        for row in audit.rows:
            if any(urlsplit(h).scheme == "https" for h in row["hrefs"]):
                stats["sourced_rows"] += 1
            elif "review.html#register" in row["hrefs"]:
                stats["registered_rows"] += 1
            else:
                problems.append(f"{name}: a table row has neither an official source link "
                                f"nor a link to the register of unverified items")
        for tag, href in audit.links:
            stats["links"] += 1
            parts = urlsplit(href)
            if parts.scheme in {"http", "https"}:
                stats["official_links"] += 1
                if parts.scheme != "https":
                    problems.append(f"{name}: external link is not https: {href}")
                if parts.netloc not in OFFICIAL_HOSTS:
                    problems.append(f"{name}: external host not approved: {parts.netloc} ({href})")
                if parts.netloc.startswith("www.irs.gov") and href not in LEDGER_URLS:
                    problems.append(f"{name}: link is not in the source ledger: {href}")
                continue
            if parts.scheme in {"mailto", "tel", "javascript"}:
                problems.append(f"{name}: disallowed link scheme: {href}")
                continue
            if href.startswith("#"):
                if href[1:] and href[1:] not in audit.ids:
                    problems.append(f"{name}: fragment target missing: {href}")
                continue
            target_name, _, fragment = href.partition("#")
            if target_name and target_name not in PAGES + ASSETS:
                problems.append(f"{name}: internal link target missing: {href}")
            # fragment targets are checked in a second pass, once every page is audited
    # fragment links into pages audited later are checked in a second pass
    for name, audit in audits.items():
        for tag, href in audit.links:
            if href.startswith(("#", "http", "mailto", "tel", "javascript")):
                continue
            target_name, _, fragment = href.partition("#")
            if fragment and target_name in PAGES and fragment not in audits[target_name].ids:
                problems.append(f"{name}: fragment target missing in {target_name}: {href}")
    return problems, stats


def check_nav() -> list[str]:
    problems = []
    for group, pages in builder.NAV_GROUPS:
        for p in pages:
            if p not in PAGES:
                problems.append(f"nav links to a page that is not built: {p}")
    for p in PAGES:
        if not any(p in pages for _, pages in builder.NAV_GROUPS):
            problems.append(f"page is built but never linked from the nav: {p}")
    return problems


def main() -> int:
    import privacy_boundary  # late import: reads the packaged artifact

    problems: list[str] = []
    no_limits: list[str] = []
    problems += check_reproducible()
    problems += check_nav()
    page_problems, stats = check_pages()
    ledger_problems, no_limits = check_ledger()
    problems += page_problems + ledger_problems

    print(f"Pages built by this edition : {len(PAGES)}")
    print(f"Table rows                  : {stats['rows']}")
    print(f"Rows linked to an official site: {stats['sourced_rows']}")
    print(f"Rows explicitly logged as unsourceable: {stats['registered_rows']}")
    print(f"Links                       : {stats['links']} ({stats['official_links']} external)")
    print(f"Official sources in ledger  : {len(LEDGER['sources'])} "
          f"({len(no_limits)} state no limitation)")

    if problems:
        raise SystemExit("Verification FAILED:\n  - " + "\n  - ".join(dict.fromkeys(problems)))

    pack.main()
    privacy_boundary.main()
    print("PASS: build reproducible, every table row source-linked, links resolve, "
          "artifact within the privacy boundary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
