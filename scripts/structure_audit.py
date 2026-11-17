"""Independent structural audit of the published pages.

scripts/verify.py proves the things a decision reader depends on: one title, one main,
one h1, a source link on every table row, approved hosts, resolvable internal links.
It does not look at document structure, and structure is what assistive technology and
a skim reader use to navigate a twenty-five page analysis.

This script is advisory on purpose. It prints what it found and exits 0, so it can run
beside the publication gate without ever blocking a build; `--strict` is available for a
local check that is meant to fail. Every check below is one the generated pages either
pass today or are reported as a finding, and no finding is repaired here: the pages are
produced by scripts/build.py, which this script never edits.

Checks
  * every page declares a document language, one <title>, one <main> and one <h1>
  * heading levels never skip downwards (an h2 section must exist before its h3)
  * no duplicate id on a page (a duplicate silently breaks a fragment link)
  * every <th> carries a scope, every <table> a caption or an aria-label
  * the navigation marks the current page exactly once
  * a skip link to the main landmark is present
  * no script, frame or form element reaches a published page
  * every page links the stylesheet, and the printable one-page brief still carries its
    print rules in assets/style.css (the page is the export, so the rules are part of it)

Usage:
    python3 scripts/structure_audit.py
    python3 scripts/structure_audit.py --strict
    python3 scripts/structure_audit.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLESHEET = ROOT / "assets" / "style.css"
FORBIDDEN_ELEMENTS = {"script", "iframe", "form", "input", "textarea", "object", "embed"}


class PageAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang: str | None = None
        self.titles = 0
        self.mains = 0
        self.h1s = 0
        self.headings: list[int] = []
        self.ids: list[str] = []
        self.tables = 0
        self.captions = 0
        self.th_total = 0
        self.th_scoped = 0
        self.active = 0
        self.skip_links = 0
        self.stylesheet_links = 0
        self.forbidden: list[str] = []
        self.body_classes: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attr = {k: (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = attr.get("lang")
        elif tag == "title":
            self.titles += 1
        elif tag == "main":
            self.mains += 1
        elif tag == "body":
            self.body_classes = attr.get("class", "").split()
        elif re.fullmatch(r"h[1-6]", tag):
            level = int(tag[1])
            self.headings.append(level)
            if level == 1:
                self.h1s += 1
        elif tag == "table":
            self.tables += 1
        elif tag == "caption":
            self.captions += 1
        elif tag == "th":
            self.th_total += 1
            if "scope" in attr:
                self.th_scoped += 1
        elif tag == "a":
            if attr.get("class", "").split().count("active"):
                self.active += 1
            classes = attr.get("class", "").split()
            if "skip" in classes:
                self.skip_links += 1
            if attr.get("href", "").endswith("style.css"):
                self.stylesheet_links += 1
        elif tag == "link" and attr.get("href", "").endswith("style.css"):
            self.stylesheet_links += 1
        if "id" in attr:
            self.ids.append(attr["id"])
        if tag in FORBIDDEN_ELEMENTS:
            self.forbidden.append(tag)

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        self.handle_starttag(tag, attrs)


def heading_findings(levels: list[int]) -> list[str]:
    findings: list[str] = []
    previous = 0
    for level in levels:
        if previous and level > previous + 1:
            findings.append(f"heading level skips from h{previous} to h{level}")
        previous = level
    return findings


def audit_pages(pages: list[Path]) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    findings: list[str] = []
    for path in pages:
        text = path.read_text(encoding="utf-8")
        parser = PageAudit()
        parser.feed(text)
        page_issues: list[str] = []
        if parser.lang != "en":
            page_issues.append(f"document language is {parser.lang!r}, expected 'en'")
        if parser.titles != 1:
            page_issues.append(f"{parser.titles} <title> elements")
        if parser.mains != 1:
            page_issues.append(f"{parser.mains} <main> landmarks")
        if parser.h1s != 1:
            page_issues.append(f"{parser.h1s} <h1> elements")
        page_issues.extend(heading_findings(parser.headings))
        duplicates = [i for i, c in Counter(parser.ids).items() if c > 1]
        if duplicates:
            page_issues.append(
                f"{len(duplicates)} duplicate id(s): {', '.join(sorted(duplicates))}")
        if parser.th_total and parser.th_scoped != parser.th_total:
            page_issues.append(
                f"{parser.th_total - parser.th_scoped} of {parser.th_total} <th> without scope")
        if parser.tables and parser.captions == 0 and "aria-label" not in text:
            page_issues.append(f"{parser.tables} table(s) with no caption and no aria-label")
        if parser.active != 1:
            page_issues.append(f"{parser.active} navigation markers class=\"active\"")
        if parser.skip_links != 1:
            page_issues.append(f"{parser.skip_links} skip links")
        if parser.stylesheet_links < 1:
            page_issues.append("no link to the stylesheet")
        if parser.forbidden:
            page_issues.append(
                "forbidden elements: " + ", ".join(sorted(set(parser.forbidden))))
        rows.append({
            "page": path.name,
            "headings": len(parser.headings),
            "tables": parser.tables,
            "ids": len(parser.ids),
            "findings": page_issues,
        })
        findings.extend(f"{path.name}: {issue}" for issue in page_issues)
    return rows, findings


def stylesheet_findings(pages: list[Path]) -> list[str]:
    findings: list[str] = []
    if not STYLESHEET.is_file():
        return ["assets/style.css is missing"]
    css = STYLESHEET.read_text(encoding="utf-8")
    if "@media print" not in css:
        findings.append("assets/style.css has no print block at all")
    if "page: brief" not in css and "@page brief" not in css:
        findings.append("assets/style.css has no named print page for the one-page brief")
    brief = ROOT / "briefing.html"
    if brief in pages:
        text = brief.read_text(encoding="utf-8")
        if "print-brief-page" not in text:
            findings.append("briefing.html no longer carries the print-brief-page body class")
        if "brief-grid" not in text:
            findings.append("briefing.html no longer carries the brief-grid layout")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 when any finding is reported")
    parser.add_argument("--json", default="", help="also write the findings as JSON")
    args = parser.parse_args()

    pages = sorted(ROOT.glob("*.html"))
    rows, findings = audit_pages(pages)
    findings.extend(stylesheet_findings(pages))

    print("# Structural audit of the published pages")
    print("")
    print(f"- Pages scanned: {len(pages)}")
    print(f"- Findings: {len(findings)}")
    print("")
    print("| Page | Headings | Tables | Ids | Findings |")
    print("|---|---|---|---|---|")
    for row in rows:
        print(f"| {row['page']} | {row['headings']} | {row['tables']} | {row['ids']} | "
              f"{len(row['findings'])} |")
    print("")
    if findings:
        print("## Findings")
        print("")
        for item in findings:
            print(f"- {item}")
        print("")
        print("Every page is generated by scripts/build.py; this audit repairs nothing. "
              "A finding is logged for the session that owns the generator.")
    else:
        print("No structural findings.")
    print("")
    print("Advisory by design: exit status is 0 unless --strict is given.")

    if args.json:
        Path(args.json).write_text(
            json.dumps({"pages": rows, "findings": findings}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
    if args.strict and findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
