#!/usr/bin/env python3
"""Fail-closed verification for the published edition.

 1. Reproducible build: re-running the model, the renderer and the packager changes no byte.
 2. Structure: one title, one main, one h1, exactly one aria-current, no scripts or forms.
 3. Links: every internal target and fragment exists inside the artifact; every external link is
    HTTPS to an official publisher and carries no jurisdiction marker.
 4. Citations: every factual table row links to a URL in the official source ledger.
 5. Privacy: no name, postal code, parcel number, street address, e-mail address or local
    jurisdiction appears in a page, a data file, a path or a link.
 6. Rounding: every dollar amount displayed is a multiple of $10.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from package_site import ASSETS, SITE, PAGES as PAGE_LIST
from privacy_boundary import FORBIDDEN, FORBIDDEN_URL_MARKERS, is_official, verify as verify_privacy

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PAGE_COUNT = 16
FORBIDDEN_TAGS = {"script", "iframe", "form", "input", "textarea", "object", "embed"}
# Officially published averages and thresholds are quoted verbatim and must never be altered to
# fit the rounding rule. Each one is a state or national figure, not a property figure. No
# property, cost, projection or tax-bill amount may be added to this set.
ALLOWED_VERBATIM = {"$1,571", "$1,512"}

DOLLAR = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})+|\d+)(?!\d)(\s*(?:million|billion|trillion)\b)?", re.I)
DECIMAL_AMOUNT = re.compile(r"\$\s?[1-9][\d,]*\.\d{1,2}(?![\d])")


class PageAudit(HTMLParser):
    """Collect page structure, links and per-row citations."""

    def __init__(self, path: Path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.errors: list[str] = []
        self.ids: set[str] = set()
        self.links: list[tuple[str, dict[str, str]]] = []
        self.main_count = self.title_count = self.h1_count = self.current_count = 0
        self.rows: list[dict[str, object]] = []
        self.fact_rows: list[dict[str, object]] = []
        self.sourced_rows: list[dict[str, object]] = []
        self.row: dict[str, object] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        if tag in FORBIDDEN_TAGS:
            self.errors.append(f"forbidden element <{tag}>")
        if tag == "main":
            self.main_count += 1
        elif tag == "title":
            self.title_count += 1
        elif tag == "h1":
            self.h1_count += 1
        if attr.get("aria-current") == "page":
            self.current_count += 1
        if attr.get("id"):
            if attr["id"] in self.ids:
                self.errors.append(f"duplicate id #{attr['id']}")
            self.ids.add(attr["id"])
        if attr.get("src"):
            self.errors.append(f"embedded asset is not allowed: {attr['src']}")
        if tag == "tr":
            if self.row is not None:
                self.errors.append("nested table row")
            self.row = {"classes": set(attr.get("class", "").split()), "hrefs": [], "header": False}
        if tag in {"td", "th"} and self.row is not None and tag == "th":
            self.row["header"] = True
            if attr.get("scope") != "col":
                self.errors.append("table heading without scope=col")
        if tag in {"a", "link"} and attr.get("href"):
            self.links.append((attr["href"], attr))
            if self.row is not None:
                assert isinstance(self.row["hrefs"], list)
                self.row["hrefs"].append(attr["href"])

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.row is not None:
            if not self.row["header"]:
                hrefs = self.row["hrefs"]
                assert isinstance(hrefs, list)
                if not hrefs:
                    self.errors.append("table row without any link")
                if any(urlsplit(href).scheme for href in hrefs):
                    self.fact_rows.append(self.row)
            self.rows.append(self.row)
            self.row = None


def read_ledger() -> tuple[dict[str, dict[str, object]], set[str]]:
    ledger = json.loads((ROOT / "assets" / "sources.json").read_text(encoding="utf-8"))
    sources = ledger["sources"]
    if not sources:
        raise SystemExit("source ledger is empty")
    urls = set()
    for sid, source in sources.items():
        for field in ("publisher", "title", "url", "checked"):
            if not source.get(field):
                raise SystemExit(f"ledger entry {sid} is missing {field}")
        if not source["url"].startswith("https://") or not is_official(source["url"]):
            raise SystemExit(f"ledger entry {sid} is not an official HTTPS publisher")
        if FORBIDDEN_URL_MARKERS.search(source["url"]):
            raise SystemExit(f"ledger entry {sid} links a jurisdiction-identifying address")
        urls.add(source["url"])
    return sources, urls


def audit_page(path: Path, ledger_urls: set[str]) -> tuple[list[str], PageAudit]:
    text = path.read_text(encoding="utf-8")
    parser = PageAudit(path)
    parser.feed(text)
    parser.close()
    errors = list(parser.errors)
    if parser.main_count != 1:
        errors.append(f"expected 1 main element, found {parser.main_count}")
    if parser.title_count != 1:
        errors.append(f"expected 1 title, found {parser.title_count}")
    if parser.h1_count != 1:
        errors.append(f"expected 1 h1, found {parser.h1_count}")
    if parser.current_count != 1:
        errors.append(f"expected 1 aria-current link, found {parser.current_count}")

    for href, attr in parser.links:
        parsed = urlsplit(href)
        if parsed.scheme or parsed.netloc:
            if parsed.scheme != "https":
                errors.append(f"external link is not HTTPS: {href}")
            elif not is_official(href):
                errors.append(f"external link is not an official publisher: {href}")
            if attr.get("target") == "_blank" and not {"noopener", "noreferrer"}.issubset(
                    set(attr.get("rel", "").lower().split())):
                errors.append(f"new-tab link lacks noopener/noreferrer: {href}")
            continue
        if parsed.path.startswith("/"):
            errors.append(f"root-absolute local URL is not supported: {href}")
            continue
        target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path.resolve()
        try:
            target.relative_to(SITE.resolve())
        except ValueError:
            errors.append(f"local URL escapes the artifact: {href}")
            continue
        if not target.is_file():
            errors.append(f"broken local URL: {href}")
            continue
        if parsed.fragment and target.suffix == ".html":
            other = PageAudit(target)
            other.feed(target.read_text(encoding="utf-8"))
            if unquote(parsed.fragment) not in other.ids:
                errors.append(f"broken local fragment: {href}")

    for row in parser.fact_rows:
        hrefs = [href for href in row["hrefs"] if urlsplit(href).scheme]
        if not any(href in ledger_urls for href in hrefs):
            errors.append(f"factual row cites nothing in the source ledger: {hrefs[:2]}")

    for label, pattern in FORBIDDEN.items():
        if pattern.search(text):
            errors.append(f"possible {label} in page text")
    for amount in DECIMAL_AMOUNT.findall(text):
        errors.append(f"amount shown with cents: ${amount}")
    for raw, scale in DOLLAR.findall(text):
        if scale:
            # "about $69 trillion" is an aggregate published by the source, not a property
            # figure, and is reported in whole units of the scale word.
            continue
        if f"${raw}" in ALLOWED_VERBATIM:
            continue
        value = int(raw.replace(",", ""))
        if value % 10:
            errors.append(f"amount not rounded to $10: ${raw}")
    return errors, parser


def main() -> int:
    if len(PAGE_LIST) != EXPECTED_PAGE_COUNT:
        raise SystemExit(f"expected {EXPECTED_PAGE_COUNT} published pages, found {len(PAGE_LIST)}")

    generated = PAGE_LIST + ASSETS
    before = {name: (ROOT / name).read_bytes() for name in generated}
    for script in ("scripts/model.py", "scripts/economy.py", "scripts/build.py"):
        run([sys.executable, script])
    after = {name: (ROOT / name).read_bytes() for name in generated}
    stale = [name for name in generated if before[name] != after[name]]
    if stale:
        raise SystemExit(f"generated output was stale; rebuild and review: {stale}")

    sources, ledger_urls = read_ledger()
    run([sys.executable, "scripts/package_site.py"])
    if verify_privacy() != 0:
        raise SystemExit("privacy boundary failed")

    failures: list[str] = []
    rows = facts = 0
    for name in PAGE_LIST:
        page_errors, parser = audit_page(SITE / name, ledger_urls)
        failures.extend(f"{name}: {error}" for error in page_errors)
        rows += len(parser.rows)
        facts += len(parser.fact_rows)

    if failures:
        print("FAIL")
        for failure in dict.fromkeys(failures):
            print("  -", failure)
        return 1
    print(
        f"PASS: {len(PAGE_LIST)} reproducible pages; {rows} table rows, {facts} of them citing an "
        f"official ledger URL; {len(sources)} ledger sources; links, fragments, official hosts, "
        f"identifier scan and $10 rounding all clean."
    )
    print("Scope: structural, citation and privacy checks only. They do not prove legal "
          "completeness and cannot verify an insurance quote, an appraisal or a future statute.")
    return 0


def run(command: list[str]) -> None:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        detail = (result.stdout + result.stderr).strip().splitlines()
        raise SystemExit(f"{' '.join(command)} failed: " + (detail[-1] if detail else "no output"))


if __name__ == "__main__":
    raise SystemExit(main())
