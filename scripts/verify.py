"""Rebuild, audit and package the privacy-safe public edition using the standard library."""
from __future__ import annotations

import json
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from build import PAGES
from package_site import ASSETS, NOJEKYLL, SITE
from privacy_boundary import FORBIDDEN, verify as verify_privacy_boundary

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PAGE_COUNT = 15
OFFICIAL_HOSTS = {
    "irs.gov", "www.irs.gov", "ftb.ca.gov", "www.ftb.ca.gov", "sco.ca.gov", "www.sco.ca.gov",
    "leginfo.legislature.ca.gov", "boe.ca.gov", "www.boe.ca.gov", "cpuc.ca.gov", "www.cpuc.ca.gov",
    "insurance.ca.gov", "www.insurance.ca.gov", "federalreservehistory.org",
    "www.federalreservehistory.org", "libertystreeteconomics.newyorkfed.org",
    "bls.gov", "www.bls.gov", "congress.gov", "www.congress.gov", "govinfo.gov", "www.govinfo.gov",
}
FORBIDDEN_TAGS = {"script", "iframe", "form", "input", "textarea", "object", "embed"}
# Every decision-facing data row must carry an official source or validation anchor.
# Header rows and source-library rows are handled separately; worksheet/proposal rows are
# included because an evidence checklist still needs a published rule or agency anchor.
DATA_ROW_CLASSES = {"fact-row", "worksheet-row", "framework-row", "choice-row", "proposal-row", "flag-row"}


class PageAudit(HTMLParser):
    """Collect page structure, links, identifiers and source-backed table rows."""

    def __init__(self, path: Path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.errors: list[str] = []
        self.ids: set[str] = set()
        self.links: list[tuple[str, str, dict[str, str]]] = []
        self.main_count = 0
        self.title_count = 0
        self.h1_count = 0
        self.current_count = 0
        self.rows: list[dict[str, object]] = []
        self.fact_rows: list[dict[str, object]] = []
        self.sourced_rows: list[dict[str, object]] = []
        self.row: dict[str, object] | None = None
        self.cell_open = False

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
            identifier = attr["id"]
            if identifier in self.ids:
                self.errors.append(f"duplicate id #{identifier}")
            self.ids.add(identifier)
        if tag == "tr":
            if self.row is not None:
                self.errors.append("nested table row")
            classes = set(attr.get("class", "").split())
            self.row = {"classes": classes, "hrefs": [], "cells": 0, "header": False}
        if tag in {"td", "th"}:
            if self.cell_open:
                self.errors.append("nested table cell")
            self.cell_open = True
            if self.row is not None:
                self.row["cells"] = int(self.row["cells"]) + 1
                if tag == "th":
                    self.row["header"] = True
                    if attr.get("scope") != "col":
                        self.errors.append("table heading without scope=col")
        if tag in {"a", "link"} and attr.get("href"):
            self.links.append((tag, attr["href"], attr))
            if self.row is not None:
                hrefs = self.row["hrefs"]
                assert isinstance(hrefs, list)
                hrefs.append(attr["href"])
        if tag == "img" or "src" in attr:
            self.errors.append("remote or embedded asset is not allowed")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"}:
            if not self.cell_open:
                self.errors.append(f"closing table cell without an open cell: </{tag}>")
            self.cell_open = False
        if tag == "tr":
            if self.row is None:
                self.errors.append("closing table row without an open row")
                return
            if self.cell_open:
                self.errors.append("table row closes with an open cell")
                self.cell_open = False
            classes = self.row["classes"]
            if isinstance(classes, set) and "fact-row" in classes:
                self.fact_rows.append(self.row)
            if isinstance(classes, set) and classes.intersection(DATA_ROW_CLASSES):
                self.sourced_rows.append(self.row)
                hrefs = self.row["hrefs"]
                if not isinstance(hrefs, list) or not any(urlsplit(href).scheme == "https" for href in hrefs):
                    self.errors.append("decision data row lacks an HTTPS official-source link")
            self.rows.append(self.row)
            self.row = None


def read_ledger() -> tuple[list[dict[str, str]], set[str]]:
    path = ROOT / "assets" / "sources.json"
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read official source ledger: {exc}") from exc
    if ledger.get("as_of") != "2026-11-12":
        raise SystemExit("Source ledger as-of date is not the reviewed publication date")
    sources = ledger.get("sources")
    if not isinstance(sources, list) or not sources:
        raise SystemExit("Source ledger must contain a non-empty list")
    ids: set[str] = set()
    urls: set[str] = set()
    for item in sources:
        required = ("id", "publisher", "title", "url", "checked", "supports", "limits")
        if not isinstance(item, dict) or any(not item.get(key) for key in required):
            raise SystemExit("Each ledger entry must include id, publisher, title, URL, check method, support and limits")
        if item["id"] in ids:
            raise SystemExit(f"Duplicate source id: {item['id']}")
        ids.add(item["id"])
        parsed = urlsplit(item["url"])
        if parsed.scheme != "https" or parsed.hostname not in OFFICIAL_HOSTS:
            raise SystemExit(f"Source is not an HTTPS link to an approved official publisher: {item['id']}")
        urls.add(item["url"])
    return sources, urls


def audit_page(path: Path, ledger_urls: set[str]) -> tuple[list[str], PageAudit]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [f"cannot read page: {exc}"], PageAudit(path)
    parser = PageAudit(path)
    parser.feed(text)
    parser.close()
    errors = list(parser.errors)
    if parser.main_count != 1:
        errors.append(f"expected one main element, got {parser.main_count}")
    if parser.title_count != 1:
        errors.append(f"expected one title element, got {parser.title_count}")
    if parser.h1_count != 1:
        errors.append(f"expected one h1 element, got {parser.h1_count}")
    if parser.current_count != 1:
        errors.append(f"expected one current-navigation link, got {parser.current_count}")

    for tag, href, attr in parser.links:
        parsed = urlsplit(href)
        if parsed.scheme or parsed.netloc:
            if parsed.scheme != "https" or parsed.hostname not in OFFICIAL_HOSTS:
                errors.append(f"link is not HTTPS to an approved official host: {href}")
            if attr.get("target") == "_blank":
                rel = set(attr.get("rel", "").lower().split())
                if not {"noopener", "noreferrer"}.issubset(rel):
                    errors.append(f"new-tab link lacks noopener/noreferrer: {href}")
        else:
            if parsed.path.startswith("/"):
                errors.append(f"root-absolute local URL is not supported: {href}")
                continue
            relative = unquote(parsed.path)
            target = (path.parent / relative).resolve() if relative else path.resolve()
            try:
                target.relative_to(SITE.resolve())
            except ValueError:
                errors.append(f"local URL escapes the artifact: {href}")
                continue
            if not target.is_file():
                errors.append(f"broken local URL: {href}")
                continue
            if parsed.fragment and target.suffix == ".html":
                target_parser = PageAudit(target)
                target_parser.feed(target.read_text(encoding="utf-8"))
                if unquote(parsed.fragment) not in target_parser.ids:
                    errors.append(f"broken local fragment: {href}")

    for row in parser.sourced_rows:
        hrefs = row["hrefs"]
        assert isinstance(hrefs, list)
        external = [href for href in hrefs if urlsplit(href).scheme]
        source_links = [href for href in external if href in ledger_urls]
        unlisted = [href for href in external if href not in ledger_urls]
        if not source_links:
            errors.append("decision data row lacks a source-ledger URL")
        if unlisted:
            errors.append(f"decision data row has external links outside the source ledger: {unlisted}")

    # Scan only the actual public page. The artifact path allowlist prevents private models/data
    # from being copied; these patterns catch the common direct identifiers and location clues.
    for label, pattern in FORBIDDEN.items():
        match = pattern.search(text)
        if match:
            errors.append(f"possible {label} in page")
    return errors, parser


def run(command: list[str], label: str) -> None:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        detail = (result.stdout + result.stderr).strip().splitlines()
        raise SystemExit(f"{label} failed: " + (detail[-1] if detail else "no diagnostic output"))


def main() -> int:
    if len(PAGES) != EXPECTED_PAGE_COUNT:
        raise SystemExit(f"Expected {EXPECTED_PAGE_COUNT} public pages, found {len(PAGES)}")

    generated = PAGES + ASSETS
    before = {name: (ROOT / name).read_bytes() for name in generated}
    run([sys.executable, "scripts/build.py"], "public page build")
    after = {name: (ROOT / name).read_bytes() for name in generated}
    stale = [name for name in generated if before[name] != after[name]]
    if stale:
        raise SystemExit(f"Generated files were stale; rebuild and review: {stale}")

    sources, ledger_urls = read_ledger()
    run([sys.executable, "scripts/package_site.py"], "site packaging")
    try:
        verify_privacy_boundary()
    except SystemExit as exc:
        raise SystemExit(f"Privacy boundary failed: {exc}") from exc

    failures: list[str] = []
    total_rows = 0
    factual_rows = 0
    sourced_rows = 0
    for name in PAGES:
        page_errors, parser = audit_page(SITE / name, ledger_urls)
        failures.extend(f"{name}: {error}" for error in page_errors)
        total_rows += len(parser.rows)
        factual_rows += len(parser.fact_rows)
        sourced_rows += len(parser.sourced_rows)

    if failures:
        print("FAIL")
        for failure in dict.fromkeys(failures):
            print("  -", failure)
        return 1

    print(
        f"PASS: {len(PAGES)} reproducible public pages; {total_rows} table rows, "
        f"{sourced_rows} source-linked decision rows ({factual_rows} factual); {len(sources)} official-source ledger entries; " 
        "local links/fragments, official hosts, privacy scan, allowlisted package and withdrawal notices clean."
    )
    print(
        "Scope: structural and privacy checks only. They do not establish legal completeness, "
        "a property-specific value, an insurance quote or a future outcome."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
